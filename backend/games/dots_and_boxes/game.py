import copy
import random

from ..base import BaseGame, GameMeta

# 5×5 dots → 4×4 boxes → 40 total lines
GRID = 5   # dots per side
N = GRID - 1   # boxes / line-segments per side = 4
MAX_LINES = GRID * N * 2   # 5*4 horizontal + 4*5 vertical = 40


def _box_complete(h: list, v: list, br: int, bc: int) -> bool:
    return (h[br][bc] is not None and h[br + 1][bc] is not None and
            v[br][bc] is not None and v[br][bc + 1] is not None)


def _sides(h: list, v: list, br: int, bc: int) -> int:
    return sum([
        h[br][bc] is not None,
        h[br + 1][bc] is not None,
        v[br][bc] is not None,
        v[br][bc + 1] is not None,
    ])


def _adjacent_boxes(orientation: str, r: int, c: int) -> list:
    """Boxes that share the given line segment."""
    adj = []
    if orientation == "h":
        if r > 0:     adj.append((r - 1, c))
        if r < N:     adj.append((r, c))
    else:
        if c > 0:     adj.append((r, c - 1))
        if c < N:     adj.append((r, c))
    return adj


class DotsAndBoxes(BaseGame):
    meta = GameMeta(
        slug="dots_and_boxes",
        name="Dots & Boxes",
        description="Draw lines to complete boxes. Complete a box to score a point and go again.",
        min_players=2,
        max_players=2,
        supports_solo=True,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "h_lines": [[None] * N    for _ in range(GRID)],  # GRID rows × N cols  [0-4][0-3]
            "v_lines": [[None] * GRID for _ in range(N)],   # N rows    × GRID cols [0-3][0-4]
            "boxes":   [[None] * N for _ in range(N)],       # [row 0-3][col 0-3]
            "scores":  {players[0]: 0, players[1]: 0},
            "current_turn": players[0],
            "players": players,
            "lines_drawn": 0,
            "last_line": None,
            "extra_turn": False,
        }

    def _player_idx(self, state: dict, player: str) -> int:
        return 0 if player == state["players"][0] else 1

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state.get("current_turn") != player:
            return False
        if action.get("type") != "line":
            return False
        o = action.get("orientation")
        r, c = action.get("row"), action.get("col")
        if o not in ("h", "v") or not isinstance(r, int) or not isinstance(c, int):
            return False
        if o == "h":
            if not (0 <= r < GRID and 0 <= c < N):
                return False
            return state["h_lines"][r][c] is None
        else:
            if not (0 <= r < N and 0 <= c < GRID):
                return False
            return state["v_lines"][r][c] is None

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        o, r, c = action["orientation"], action["row"], action["col"]
        player_idx = self._player_idx(state, player)
        opp = state["players"][1] if player_idx == 0 else state["players"][0]
        h, v, boxes = state["h_lines"], state["v_lines"], state["boxes"]

        if o == "h":
            h[r][c] = player_idx
        else:
            v[r][c] = player_idx

        state["lines_drawn"] += 1
        state["last_line"] = action

        # Check adjacent boxes for completion
        claimed = 0
        for br, bc in _adjacent_boxes(o, r, c):
            if boxes[br][bc] is None and _box_complete(h, v, br, bc):
                boxes[br][bc] = player
                state["scores"][player] += 1
                claimed += 1

        if claimed:
            state["extra_turn"] = True
            # current_turn unchanged — same player goes again
        else:
            state["extra_turn"] = False
            state["current_turn"] = opp

        # extra_turn has no meaning once all lines are drawn
        if state["lines_drawn"] >= MAX_LINES:
            state["extra_turn"] = False

        return state

    def is_game_over(self, state: dict) -> bool:
        return state["lines_drawn"] >= MAX_LINES

    def get_winner(self, state: dict) -> str | None:
        p = state["players"]
        s0, s1 = state["scores"][p[0]], state["scores"][p[1]]
        if s0 > s1: return p[0]
        if s1 > s0: return p[1]
        return None

    def get_computer_action(self, state: dict, player: str) -> dict | None:
        if state.get("current_turn") != player:
            return None
        player_idx = self._player_idx(state, player)
        h, v = state["h_lines"], state["v_lines"]

        # Collect all valid moves
        all_moves = []
        for r in range(GRID):
            for c in range(N):
                if h[r][c] is None:
                    all_moves.append({"type": "line", "orientation": "h", "row": r, "col": c})
        for r in range(N):
            for c in range(GRID):
                if v[r][c] is None:
                    all_moves.append({"type": "line", "orientation": "v", "row": r, "col": c})

        if not all_moves:
            return None

        def completes(move) -> int:
            """Number of boxes this move completes."""
            return sum(
                1 for br, bc in _adjacent_boxes(move["orientation"], move["row"], move["col"])
                if _sides(h, v, br, bc) == 3
            )

        def opens(move) -> int:
            """Number of 3-sided boxes this move would create (danger = gift to opponent)."""
            return sum(
                1 for br, bc in _adjacent_boxes(move["orientation"], move["row"], move["col"])
                if _sides(h, v, br, bc) == 2
            )

        # 1. Complete any available boxes (greedy — most first)
        scoring = [m for m in all_moves if completes(m) > 0]
        if scoring:
            return max(scoring, key=completes)

        # 2. Safe moves: don't create any 3-sided box
        safe = [m for m in all_moves if opens(m) == 0]
        if safe:
            return random.choice(safe)

        # 3. Forced sacrifice: open as few boxes as possible
        return min(all_moves, key=opens)
