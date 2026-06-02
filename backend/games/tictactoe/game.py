import copy

from ..base import BaseGame, GameMeta

_WINNING_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


class TicTacToe(BaseGame):
    meta = GameMeta(
        slug="tictactoe",
        name="Tic-Tac-Toe",
        description="Classic 3×3 grid. Get three in a row to win.",
        min_players=2,
        max_players=2,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "board": [None] * 9,          # index 0-8, None = empty, else username
            "marks": {players[0]: "X", players[1]: "O"},
            "current_turn": players[0],
        }

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state["current_turn"] != player:
            return False
        cell = action.get("cell")
        if not isinstance(cell, int) or not (0 <= cell <= 8):
            return False
        return state["board"][cell] is None

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        cell = action["cell"]
        state["board"][cell] = player
        players = list(state["marks"].keys())
        state["current_turn"] = players[1] if player == players[0] else players[0]
        return state

    def get_winner(self, state: dict) -> str | None:
        board = state["board"]
        for a, b, c in _WINNING_LINES:
            if board[a] is not None and board[a] == board[b] == board[c]:
                return board[a]
        return None

    def is_game_over(self, state: dict) -> bool:
        return self.get_winner(state) is not None or all(
            cell is not None for cell in state["board"]
        )
