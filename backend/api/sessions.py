import json

from fastapi import APIRouter, Header, HTTPException

from core import connections, session as session_store
from core.config import settings
from core.plugin_loader import get_game, list_games
from models.schemas import (
    ActionRequest,
    CreateSessionRequest,
    GameInfo,
    JoinSessionRequest,
    SessionResponse,
    StatsResponse,
)

router = APIRouter(prefix="/api")


def _require_token(x_player_token: str | None) -> str:
    if not x_player_token:
        raise HTTPException(status_code=401, detail="X-Player-Token header required")
    return x_player_token


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    stats = await session_store.get_stats()
    stats["git_commit"] = settings.git_commit
    return stats


@router.get("/sessions/public", response_model=list[SessionResponse])
async def get_public_sessions(x_player_token: str | None = Header(default=None)):
    sessions = await session_store.get_public_sessions()
    return [SessionResponse.from_session(s, x_player_token) for s in sessions]


@router.get("/games", response_model=list[GameInfo])
async def list_available_games():
    return [
        GameInfo(
            slug=g.meta.slug,
            name=g.meta.name,
            description=g.meta.description,
            min_players=g.meta.min_players,
            max_players=g.meta.max_players,
            supports_solo=g.meta.supports_solo,
        )
        for g in list_games()
    ]


@router.get("/sessions", response_model=list[SessionResponse])
async def get_my_sessions(x_player_token: str | None = Header(default=None)):
    token = _require_token(x_player_token)
    sessions = await session_store.get_player_sessions(token)
    return [SessionResponse.from_session(s, token) for s in sessions]


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    try:
        session = await session_store.create_session(body.game_slug, body.username, token, body.public, body.vs_computer)
        if body.vs_computer:
            game = get_game(body.game_slug)
            if not game or not game.meta.supports_solo:
                raise ValueError("This game does not support playing against the computer.")
            session = await session_store.join_session(
                session["uuid"], session_store.COMPUTER_USERNAME, session_store.COMPUTER_TOKEN
            )
            computer_action = game.get_computer_action(session["state"], session_store.COMPUTER_USERNAME)
            if computer_action:
                session = await session_store.apply_action(
                    session["uuid"], session_store.COMPUTER_TOKEN, computer_action
                )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SessionResponse.from_session(session, token)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    x_player_token: str | None = Header(default=None),
):
    session = await session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.from_session(session, x_player_token)


@router.post("/sessions/{session_id}/join", response_model=SessionResponse)
async def join_session(
    session_id: str,
    body: JoinSessionRequest,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    try:
        session = await session_store.join_session(session_id, body.username, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Notify the creator (and any other watchers) that a player has joined.
    for tok, ws in connections.get_sockets(session_id).items():
        viewer = SessionResponse.from_session(session, tok)
        try:
            await ws.send_text(json.dumps({"type": "state", "session": viewer.model_dump()}))
        except Exception:
            pass

    return SessionResponse.from_session(session, token)


@router.delete("/sessions/{session_id}", status_code=204)
async def cancel_session(
    session_id: str,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    try:
        await session_store.cancel_session(session_id, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    for tok, ws in connections.get_sockets(session_id).items():
        try:
            await ws.send_text(json.dumps({"type": "cancelled"}))
        except Exception:
            pass


@router.post("/sessions/{session_id}/action", response_model=SessionResponse)
async def perform_action(
    session_id: str,
    body: ActionRequest,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    try:
        session = await session_store.apply_action(session_id, token, body.action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SessionResponse.from_session(session, token)


@router.post("/sessions/{session_id}/forfeit", response_model=SessionResponse)
async def forfeit_session(
    session_id: str,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    try:
        session = await session_store.forfeit_session(session_id, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    for tok, ws in connections.get_sockets(session_id).items():
        viewer = SessionResponse.from_session(session, tok)
        try:
            await ws.send_text(json.dumps({"type": "state", "session": viewer.model_dump()}))
        except Exception:
            pass

    return SessionResponse.from_session(session, token)


@router.post("/sessions/{session_id}/rematch", response_model=SessionResponse, status_code=201)
async def rematch(
    session_id: str,
    x_player_token: str | None = Header(default=None),
):
    token = _require_token(x_player_token)
    try:
        old_session, new_session = await session_store.create_rematch(session_id, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Broadcast the updated old session (now carrying rematch_session_id) to
    # any players still watching the finished game, so they see the button appear.
    for tok, ws in connections.get_sockets(session_id).items():
        viewer = SessionResponse.from_session(old_session, tok)
        try:
            await ws.send_text(json.dumps({"type": "state", "session": viewer.model_dump()}))
        except Exception:
            pass

    return SessionResponse.from_session(new_session, token)
