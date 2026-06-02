import copy

from ..base import BaseGame, GameMeta

ROWS = 6
COLS = 7


def _has_four(board: list[list], player: str) -> bool:
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # Diagonal ↘
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # Diagonal ↙
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            if all(board[r + i][c - i] == player for i in range(4)):
                return True
    return False


class ConnectFour(BaseGame):
    meta = GameMeta(
        slug="connect_four",
        name="Connect Four",
        description="Drop pieces into the grid. First to connect four wins.",
        min_players=2,
        max_players=2,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "board": [[None] * COLS for _ in range(ROWS)],
            "marks": {players[0]: "R", players[1]: "Y"},
            "current_turn": players[0],
        }

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state["current_turn"] != player:
            return False
        col = action.get("col")
        if not isinstance(col, int) or not (0 <= col < COLS):
            return False
        return state["board"][0][col] is None  # top row empty → column not full

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        col = action["col"]
        for row in range(ROWS - 1, -1, -1):
            if state["board"][row][col] is None:
                state["board"][row][col] = player
                break
        players = list(state["marks"].keys())
        state["current_turn"] = players[1] if player == players[0] else players[0]
        return state

    def get_winner(self, state: dict) -> str | None:
        for player in state["marks"]:
            if _has_four(state["board"], player):
                return player
        return None

    def is_game_over(self, state: dict) -> bool:
        if self.get_winner(state) is not None:
            return True
        return all(state["board"][0][c] is not None for c in range(COLS))
