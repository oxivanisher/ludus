import json
import time
import uuid

from .config import settings
from .plugin_loader import get_game
from .redis_client import get_redis

SESSION_PREFIX = "session:"
PLAYER_PREFIX = "player:"
PUBLIC_KEY = "public:sessions"
STAT_ACTIVE = "stats:active_games"
STAT_TOTAL = "stats:total_games"
STAT_WAITING = "stats:waiting_sessions"


async def get_stats() -> dict:
    r = await get_redis()
    active, total, waiting = await r.mget(STAT_ACTIVE, STAT_TOTAL, STAT_WAITING)
    return {
        "active_games": max(0, int(active or 0)),
        "total_games": int(total or 0),
        "waiting_games": max(0, int(waiting or 0)),
    }


async def create_session(game_slug: str, username: str, player_token: str, public: bool = False) -> dict:
    game = get_game(game_slug)
    if game is None:
        raise ValueError(f"Unknown game: {game_slug}")

    r = await get_redis()
    waiting, active = await r.mget(STAT_WAITING, STAT_ACTIVE)
    total_sessions = max(0, int(waiting or 0)) + max(0, int(active or 0))
    if total_sessions >= settings.max_active_sessions:
        raise ValueError("Server is at capacity. Please try again later.")

    if public:
        public_count = await r.scard(PUBLIC_KEY)
        if public_count >= settings.max_public_sessions:
            raise ValueError("Too many open public games right now. Please wait for one to start or create a private game.")

    session_id = str(uuid.uuid4())
    now = time.time()
    session = {
        "uuid": session_id,
        "game_slug": game_slug,
        "status": "waiting",
        "public": public,
        "players": [{"username": username, "token": player_token}],
        "current_turn": None,
        "state": {},
        "winner": None,
        "created_at": now,
        "last_action_at": now,
    }

    pipe = r.pipeline()
    pipe.set(f"{SESSION_PREFIX}{session_id}", json.dumps(session), ex=settings.session_ttl)
    pipe.sadd(f"{PLAYER_PREFIX}{player_token}:sessions", session_id)
    pipe.expire(f"{PLAYER_PREFIX}{player_token}:sessions", settings.session_ttl)
    pipe.incr(STAT_WAITING)
    if public:
        pipe.sadd(PUBLIC_KEY, session_id)
    await pipe.execute()

    return session


async def get_session(session_id: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(f"{SESSION_PREFIX}{session_id}")
    return json.loads(raw) if raw else None


async def save_session(session: dict) -> None:
    r = await get_redis()
    session_id = session["uuid"]
    status = session["status"]
    ttl = settings.finished_session_ttl if status == "finished" else settings.session_ttl
    await r.set(f"{SESSION_PREFIX}{session_id}", json.dumps(session), ex=ttl)


async def get_player_sessions(player_token: str) -> list[dict]:
    r = await get_redis()
    session_ids = await r.smembers(f"{PLAYER_PREFIX}{player_token}:sessions")
    sessions = []
    for sid in session_ids:
        s = await get_session(sid)
        if s is None:
            await r.srem(f"{PLAYER_PREFIX}{player_token}:sessions", sid)
        else:
            sessions.append(s)
    return sorted(sessions, key=lambda s: s["last_action_at"], reverse=True)


async def join_session(session_id: str, username: str, player_token: str) -> dict:
    session = await get_session(session_id)
    if session is None:
        raise ValueError("Session not found")
    if session["status"] != "waiting":
        raise ValueError("Session is not open for joining")

    game = get_game(session["game_slug"])
    if game is None:
        raise ValueError("Game plugin missing")

    existing_tokens = {p["token"] for p in session["players"]}
    if player_token in existing_tokens:
        return session

    if len(session["players"]) >= game.meta.max_players:
        raise ValueError("Session is full")

    session["players"].append({"username": username, "token": player_token})

    game_starting = len(session["players"]) == game.meta.min_players
    if game_starting:
        usernames = [p["username"] for p in session["players"]]
        session["state"] = game.initial_state(usernames)
        session["current_turn"] = usernames[0]
        session["status"] = "playing"

    session["last_action_at"] = time.time()
    await save_session(session)

    r = await get_redis()
    pipe = r.pipeline()
    pipe.sadd(f"{PLAYER_PREFIX}{player_token}:sessions", session_id)
    pipe.expire(f"{PLAYER_PREFIX}{player_token}:sessions", settings.session_ttl)
    if game_starting:
        pipe.decr(STAT_WAITING)
        pipe.incr(STAT_ACTIVE)
        pipe.srem(PUBLIC_KEY, session_id)
    await pipe.execute()

    return session


async def apply_action(session_id: str, player_token: str, action: dict) -> dict:
    session = await get_session(session_id)
    if session is None:
        raise ValueError("Session not found")
    if session["status"] != "playing":
        raise ValueError("Game is not in progress")

    player_entry = next((p for p in session["players"] if p["token"] == player_token), None)
    if player_entry is None:
        raise ValueError("You are not a participant in this session")

    username = player_entry["username"]
    game = get_game(session["game_slug"])

    if not game.validate_action(session["state"], username, action):
        raise ValueError("Invalid action")

    session["state"] = game.apply_action(session["state"], username, action)
    session["last_action_at"] = time.time()

    next_player_token: str | None = None
    game_over = game.is_game_over(session["state"])

    if game_over:
        session["winner"] = game.get_winner(session["state"])
        session["status"] = "finished"
        session["current_turn"] = None
    else:
        game_state_turn = session["state"].get("current_turn")
        if game_state_turn is not None:
            session["current_turn"] = game_state_turn
        else:
            players_list = [p["username"] for p in session["players"]]
            current_idx = players_list.index(username)
            session["current_turn"] = players_list[(current_idx + 1) % len(players_list)]
        next_username = session["current_turn"]
        if next_username is not None:
            next_player_token = next(
                p["token"] for p in session["players"] if p["username"] == next_username
            )

    await save_session(session)

    if game_over:
        r = await get_redis()
        pipe = r.pipeline()
        pipe.decr(STAT_ACTIVE)
        pipe.incr(STAT_TOTAL)
        await pipe.execute()

    if next_player_token:
        from .push import notify_player
        await notify_player(
            session_id=session_id,
            player_token=next_player_token,
            game_name=game.meta.name,
        )

    return session


async def cancel_session(session_id: str, player_token: str) -> None:
    session = await get_session(session_id)
    if session is None:
        raise ValueError("Session not found")
    if session["status"] != "waiting":
        raise ValueError("Only waiting sessions can be cancelled")
    if session["players"][0]["token"] != player_token:
        raise ValueError("Only the session owner can cancel it")

    r = await get_redis()
    pipe = r.pipeline()
    pipe.delete(f"{SESSION_PREFIX}{session_id}")
    pipe.srem(PUBLIC_KEY, session_id)
    pipe.decr(STAT_WAITING)
    for p in session["players"]:
        pipe.srem(f"{PLAYER_PREFIX}{p['token']}:sessions", session_id)
    await pipe.execute()


async def get_public_sessions() -> list[dict]:
    r = await get_redis()
    session_ids = await r.smembers(PUBLIC_KEY)
    sessions = []
    stale = []
    for sid in session_ids:
        s = await get_session(sid)
        if s is None or s["status"] != "waiting":
            stale.append(sid)
        else:
            sessions.append(s)
    if stale:
        await r.srem(PUBLIC_KEY, *stale)
    return sorted(sessions, key=lambda s: s["created_at"])


async def create_rematch(session_id: str, player_token: str) -> tuple[dict, dict]:
    """
    Create a rematch for a finished session.

    Both players are pre-registered in the new session so it starts immediately.
    The turn order is reversed so the player who went second now goes first.
    Returns (updated_old_session, new_session).
    """
    session = await get_session(session_id)
    if session is None:
        raise ValueError("Session not found")
    if session["status"] != "finished":
        raise ValueError("Can only rematch a finished game")
    if session.get("rematch_session_id"):
        raise ValueError("A rematch for this game already exists")
    if not any(p["token"] == player_token for p in session["players"]):
        raise ValueError("You are not a participant in this session")

    game = get_game(session["game_slug"])
    if game is None:
        raise ValueError("Game plugin missing")

    reversed_players = list(reversed(session["players"]))
    usernames = [p["username"] for p in reversed_players]

    new_session_id = str(uuid.uuid4())
    now = time.time()
    new_session = {
        "uuid": new_session_id,
        "game_slug": session["game_slug"],
        "status": "playing",
        "players": reversed_players,
        "current_turn": usernames[0],
        "state": game.initial_state(usernames),
        "winner": None,
        "created_at": now,
        "last_action_at": now,
        "rematch_session_id": None,
        "previous_session_id": session_id,
    }

    session["rematch_session_id"] = new_session_id

    r = await get_redis()
    pipe = r.pipeline()
    pipe.set(f"{SESSION_PREFIX}{new_session_id}", json.dumps(new_session), ex=settings.session_ttl)
    pipe.set(f"{SESSION_PREFIX}{session_id}", json.dumps(session), ex=settings.finished_session_ttl)
    for p in reversed_players:
        pipe.sadd(f"{PLAYER_PREFIX}{p['token']}:sessions", new_session_id)
        pipe.expire(f"{PLAYER_PREFIX}{p['token']}:sessions", settings.session_ttl)
    pipe.incr(STAT_ACTIVE)
    await pipe.execute()

    return session, new_session
