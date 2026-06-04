import copy

from ..base import BaseGame, GameMeta

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _opp(color: str) -> str:
    return "light" if color == "dark" else "dark"


def _flips(board: list, row: int, col: int, color: str) -> list:
    """Return (r, c) positions that would be flipped by placing color at (row, col)."""
    opp = _opp(color)
    result = []
    for dr, dc in DIRS:
        r, c = row + dr, col + dc
        line = []
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opp:
            line.append((r, c))
            r += dr
            c += dc
        if line and 0 <= r < 8 and 0 <= c < 8 and board[r][c] == color:
            result.extend(line)
    return result


def _valid_moves(board: list, color: str) -> list:
    return [
        [r, c]
        for r in range(8)
        for c in range(8)
        if board[r][c] is None and _flips(board, r, c, color)
    ]


def _count(board: list, color: str) -> int:
    return sum(cell == color for row in board for cell in row)


class Reversi(BaseGame):
    meta = GameMeta(
        slug="reversi",
        name="Reversi",
        description="Flip your opponent's pieces to claim the board. Most pieces when the board fills wins.",
        min_players=2,
        max_players=2,
        supports_solo=False,
    )

    def initial_state(self, players: list[str]) -> dict:
        board = [[None] * 8 for _ in range(8)]
        board[3][3] = "light"
        board[3][4] = "dark"
        board[4][3] = "dark"
        board[4][4] = "light"
        dark_player, light_player = players[0], players[1]
        return {
            "board": board,
            "current_turn": dark_player,
            "players": players,
            "dark": dark_player,
            "light": light_player,
            "counts": {dark_player: 2, light_player: 2},
            "valid_moves": _valid_moves(board, "dark"),
            "skipped": False,
        }

    def _color(self, state: dict, player: str) -> str:
        return "dark" if player == state["players"][0] else "light"

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state.get("current_turn") != player:
            return False
        if action.get("type") != "place":
            return False
        r, c = action.get("row"), action.get("col")
        if not (isinstance(r, int) and isinstance(c, int)):
            return False
        if not (0 <= r < 8 and 0 <= c < 8):
            return False
        board = state["board"]
        if board[r][c] is not None:
            return False
        return bool(_flips(board, r, c, self._color(state, player)))

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        players = state["players"]
        color = self._color(state, player)
        opp_player = players[1] if player == players[0] else players[0]
        opp_color = _opp(color)
        board = state["board"]

        r, c = action["row"], action["col"]
        board[r][c] = color
        for fr, fc in _flips(board, r, c, color):
            board[fr][fc] = color

        state["counts"] = {
            players[0]: _count(board, "dark"),
            players[1]: _count(board, "light"),
        }

        opp_moves = _valid_moves(board, opp_color)
        my_moves = _valid_moves(board, color)

        if opp_moves:
            state["current_turn"] = opp_player
            state["valid_moves"] = opp_moves
            state["skipped"] = False
        elif my_moves:
            # Opponent has no valid move — they are skipped
            state["current_turn"] = player
            state["valid_moves"] = my_moves
            state["skipped"] = True
        else:
            # Neither can move — game over
            state["current_turn"] = opp_player
            state["valid_moves"] = []
            state["skipped"] = False

        return state

    def is_game_over(self, state: dict) -> bool:
        board = state["board"]
        if all(cell is not None for row in board for cell in row):
            return True
        return not _valid_moves(board, "dark") and not _valid_moves(board, "light")

    def get_winner(self, state: dict) -> str | None:
        players = state["players"]
        counts = state["counts"]
        d, l = counts[players[0]], counts[players[1]]
        if d > l:
            return players[0]
        if l > d:
            return players[1]
        return None
