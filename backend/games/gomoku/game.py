import copy

from ..base import BaseGame, GameMeta

SIZE = 15
DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]  # right, down, diagonal ↘, anti-diagonal ↙


def _check_win(board: list, row: int, col: int, color: str) -> bool:
    for dr, dc in DIRS:
        count = 1
        for sign in (1, -1):
            r, c = row + dr * sign, col + dc * sign
            while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == color:
                count += 1
                r += dr * sign
                c += dc * sign
        if count >= 5:
            return True
    return False


class Gomoku(BaseGame):
    meta = GameMeta(
        slug="gomoku",
        name="Gomoku",
        description="Place stones to get five in a row. First to connect five wins.",
        min_players=2,
        max_players=2,
        supports_solo=False,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "board": [[None] * SIZE for _ in range(SIZE)],
            "current_turn": players[0],
            "players": players,
            "black": players[0],
            "white": players[1],
            "last_move": None,
            "winner": None,
            "move_count": 0,
        }

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state.get("current_turn") != player:
            return False
        if action.get("type") != "place":
            return False
        r, c = action.get("row"), action.get("col")
        if not (isinstance(r, int) and isinstance(c, int)):
            return False
        if not (0 <= r < SIZE and 0 <= c < SIZE):
            return False
        return state["board"][r][c] is None

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        r, c = action["row"], action["col"]
        color = "black" if player == state["players"][0] else "white"
        state["board"][r][c] = color
        state["last_move"] = [r, c]
        state["move_count"] += 1

        if _check_win(state["board"], r, c, color):
            state["winner"] = player
        else:
            opp = state["players"][1] if player == state["players"][0] else state["players"][0]
            state["current_turn"] = opp

        return state

    def is_game_over(self, state: dict) -> bool:
        return bool(state.get("winner")) or state.get("move_count", 0) >= SIZE * SIZE

    def get_winner(self, state: dict) -> str | None:
        return state.get("winner")
