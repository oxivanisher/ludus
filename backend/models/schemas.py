from pydantic import BaseModel


class StatsResponse(BaseModel):
    active_games: int
    total_games: int
    waiting_games: int = 0
    git_commit: str = "dev"


class GameInfo(BaseModel):
    slug: str
    name: str
    description: str
    min_players: int
    max_players: int
    supports_solo: bool = False


class CreateSessionRequest(BaseModel):
    game_slug: str
    username: str
    public: bool = False
    vs_computer: bool = False


class JoinSessionRequest(BaseModel):
    username: str


class ActionRequest(BaseModel):
    action: dict


class PlayerView(BaseModel):
    username: str


class SessionResponse(BaseModel):
    uuid: str
    game_slug: str
    status: str
    players: list[PlayerView]
    current_turn: str | None
    winner: str | None
    created_at: float
    last_action_at: float
    state: dict  # game-specific; may be filtered per player
    public: bool = False
    my_username: str | None = None  # set when the viewer is a participant
    rematch_session_id: str | None = None

    @classmethod
    def from_session(cls, session: dict, viewer_token: str | None = None) -> "SessionResponse":
        from core.plugin_loader import get_game

        player_entry = next(
            (p for p in session["players"] if p["token"] == viewer_token), None
        ) if viewer_token else None

        my_username = player_entry["username"] if player_entry else None

        state: dict = {}
        if player_entry:
            game = get_game(session["game_slug"])
            if game:
                state = game.render_state_for_player(session["state"], my_username)

        return cls(
            uuid=session["uuid"],
            game_slug=session["game_slug"],
            status=session["status"],
            players=[PlayerView(username=p["username"]) for p in session["players"]],
            current_turn=session["current_turn"],
            winner=session["winner"],
            created_at=session["created_at"],
            last_action_at=session["last_action_at"],
            state=state,
            public=session.get("public", False),
            my_username=my_username,
            rematch_session_id=session.get("rematch_session_id"),
        )
