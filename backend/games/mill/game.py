import copy

from ..base import BaseGame, GameMeta

PIECES_PER_PLAYER = 9

# Board has 24 positions arranged as three nested squares with four connecting lines.
#
# Visual layout (positions 0-23):
#
#  0 --------- 1 --------- 2
#  |           |           |
#  |  3 ------ 4 ------ 5  |
#  |  |        |        |  |
#  |  |  6 --- 7 --- 8  |  |
#  |  |  |           |  |  |
#  9 -10 -11       12 -13 -14
#  |  |  |           |  |  |
#  |  |  15 -- 16 -- 17 |  |
#  |  |        |        |  |
#  |  18 ----- 19 ----- 20 |
#  |           |           |
#  21 -------- 22 -------- 23

ADJACENCY = [
    [1, 9],            # 0  outer top-left
    [0, 2, 4],         # 1  outer top-mid
    [1, 14],           # 2  outer top-right
    [4, 10],           # 3  middle top-left
    [1, 3, 5, 7],      # 4  middle top-mid
    [4, 13],           # 5  middle top-right
    [7, 11],           # 6  inner top-left
    [4, 6, 8],         # 7  inner top-mid
    [7, 12],           # 8  inner top-right
    [0, 10, 21],       # 9  outer left-mid
    [3, 9, 11, 18],    # 10 middle left-mid
    [6, 10, 15],       # 11 inner left-mid
    [8, 13, 17],       # 12 inner right-mid
    [5, 12, 14, 20],   # 13 middle right-mid
    [2, 13, 23],       # 14 outer right-mid
    [11, 16],          # 15 inner bottom-left
    [15, 17, 19],      # 16 inner bottom-mid
    [12, 16],          # 17 inner bottom-right
    [10, 19],          # 18 middle bottom-left
    [16, 18, 20, 22],  # 19 middle bottom-mid
    [13, 19],          # 20 middle bottom-right
    [9, 22],           # 21 outer bottom-left
    [19, 21, 23],      # 22 outer bottom-mid
    [14, 22],          # 23 outer bottom-right
]

MILLS = [
    # Outer square sides
    [0, 1, 2], [2, 14, 23], [21, 22, 23], [0, 9, 21],
    # Middle square sides
    [3, 4, 5], [5, 13, 20], [18, 19, 20], [3, 10, 18],
    # Inner square sides
    [6, 7, 8], [8, 12, 17], [15, 16, 17], [6, 11, 15],
    # Cross-connections (outer–middle–inner at each side midpoint)
    [1, 4, 7], [9, 10, 11], [12, 13, 14], [16, 19, 22],
]


def _forms_mill(board: list, pos: int, player: str) -> bool:
    return any(
        pos in mill and all(board[p] == player for p in mill)
        for mill in MILLS
    )


def _all_in_mills(board: list, player: str) -> bool:
    for i, v in enumerate(board):
        if v == player:
            in_any = any(
                i in mill and all(board[p] == player for p in mill)
                for mill in MILLS
            )
            if not in_any:
                return False
    return True


def _can_move(board: list, player: str, flying: bool) -> bool:
    if flying:
        return any(v is None for v in board)
    for i, v in enumerate(board):
        if v == player and any(board[adj] is None for adj in ADJACENCY[i]):
            return True
    return False


class Mill(BaseGame):
    meta = GameMeta(
        slug="mill",
        name="Mill",
        description="Place and move pieces to form mills of three. Remove opponent pieces — last one standing wins.",
        min_players=2,
        max_players=2,
        supports_solo=False,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "board": [None] * 24,
            "phase": "placing",
            "current_turn": players[0],
            "players": players,
            "to_place": {players[0]: PIECES_PER_PLAYER, players[1]: PIECES_PER_PLAYER},
            "counts": {players[0]: 0, players[1]: 0},
        }

    def _opponent(self, state: dict, player: str) -> str:
        players = state["players"]
        return players[1] if player == players[0] else players[0]

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state.get("current_turn") != player:
            return False

        atype = action.get("type")
        board = state["board"]
        opponent = self._opponent(state, player)

        if state["phase"] == "placing":
            if atype != "place":
                return False
            pos = action.get("pos")
            return isinstance(pos, int) and 0 <= pos < 24 and board[pos] is None

        if state["phase"] == "moving":
            if atype != "move":
                return False
            from_pos = action.get("from")
            to_pos = action.get("to")
            if not (isinstance(from_pos, int) and isinstance(to_pos, int)):
                return False
            if not (0 <= from_pos < 24 and 0 <= to_pos < 24):
                return False
            if board[from_pos] != player or board[to_pos] is not None:
                return False
            flying = state["counts"][player] == 3
            return flying or to_pos in ADJACENCY[from_pos]

        if state["phase"] == "removing":
            if atype != "remove":
                return False
            pos = action.get("pos")
            if not (isinstance(pos, int) and 0 <= pos < 24):
                return False
            if board[pos] != opponent:
                return False
            in_mill = any(
                pos in mill and all(board[p] == opponent for p in mill)
                for mill in MILLS
            )
            # Can only remove a milled piece if every opponent piece is in a mill
            return not in_mill or _all_in_mills(board, opponent)

        return False

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        board = state["board"]
        opponent = self._opponent(state, player)
        atype = action["type"]

        if atype == "place":
            pos = action["pos"]
            board[pos] = player
            state["to_place"][player] -= 1
            state["counts"][player] += 1

            if _forms_mill(board, pos, player):
                state["phase"] = "removing"
            else:
                all_placed = sum(state["to_place"].values()) == 0
                state["phase"] = "moving" if all_placed else "placing"
                state["current_turn"] = opponent

        elif atype == "move":
            board[action["from"]] = None
            board[action["to"]] = player

            if _forms_mill(board, action["to"], player):
                state["phase"] = "removing"
            else:
                state["current_turn"] = opponent

        elif atype == "remove":
            board[action["pos"]] = None
            state["counts"][opponent] -= 1

            all_placed = sum(state["to_place"].values()) == 0
            state["phase"] = "moving" if all_placed else "placing"
            state["current_turn"] = opponent

        return state

    def is_game_over(self, state: dict) -> bool:
        # Never end mid-removal sub-turn
        if state["phase"] == "removing":
            return False
        # Don't end while pieces remain to be placed
        if sum(state["to_place"].values()) > 0:
            return False

        board = state["board"]
        counts = state["counts"]
        for p in state["players"]:
            if counts[p] < 3:
                return True
            if not _can_move(board, p, counts[p] == 3):
                return True

        return False

    def get_winner(self, state: dict) -> str | None:
        board = state["board"]
        counts = state["counts"]
        for p in state["players"]:
            opponent = self._opponent(state, p)
            if counts[opponent] < 3:
                return p
            if not _can_move(board, opponent, counts[opponent] == 3):
                return p
        return None
