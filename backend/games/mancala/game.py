import copy

from ..base import BaseGame, GameMeta

# Board indices:
#   Player 0 pits: 0-5   Player 0 store: 6
#   Player 1 pits: 7-12  Player 1 store: 13
#
# Physical layout (Player 0's perspective):
#   [13] | 12  11  10   9   8   7 | [6]
#   [13] |  0   1   2   3   4   5 | [6]
#
# Stones always travel 0→1→…→5→6→7→…→12→13→0→…
# Each player skips the opponent's store when sowing.
# Opposite pit of i (for captures): 12 - i  (works for all pits 0–12)

INITIAL_STONES = 4
STORE_0 = 6
STORE_1 = 13
P0_PITS = list(range(0, 6))
P1_PITS = list(range(7, 13))


def _distribute(pits: list, pit: int, player_idx: int) -> tuple[list, int]:
    """
    Sow all stones from pit counter-clockwise (skipping opponent's store).
    Apply capture rule if the last stone lands in an own empty pit.
    Returns (new_pits, last_pos).
    """
    p = pits[:]
    opp_store = STORE_1 if player_idx == 0 else STORE_0
    own_store = STORE_0 if player_idx == 0 else STORE_1
    own_pits = P0_PITS if player_idx == 0 else P1_PITS

    stones = p[pit]
    p[pit] = 0
    pos = pit
    while stones:
        pos = (pos + 1) % 14
        if pos == opp_store:
            continue
        p[pos] += 1
        stones -= 1

    # Capture: last stone lands in own empty pit AND opposite has stones
    if pos in own_pits and p[pos] == 1 and p[12 - pos] > 0:
        p[own_store] += p[12 - pos] + 1
        p[12 - pos] = 0
        p[pos] = 0

    return p, pos


def _sweep(pits: list) -> list:
    """Collect all remaining stones to each player's store (called at game end)."""
    p = pits[:]
    for i in P0_PITS:
        p[STORE_0] += p[i]
        p[i] = 0
    for i in P1_PITS:
        p[STORE_1] += p[i]
        p[i] = 0
    return p


class Mancala(BaseGame):
    meta = GameMeta(
        slug="mancala",
        name="Mancala",
        description="Sow stones around the board. Capture and collect — most in your store wins.",
        min_players=2,
        max_players=2,
        supports_solo=True,
    )

    def initial_state(self, players: list[str]) -> dict:
        pits = [INITIAL_STONES] * 14
        pits[STORE_0] = 0
        pits[STORE_1] = 0
        return {
            "pits": pits,
            "current_turn": players[0],
            "players": players,
            "extra_turn": False,
            "last_move": None,
        }

    def _player_idx(self, state: dict, player: str) -> int:
        return 0 if player == state["players"][0] else 1

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state.get("current_turn") != player:
            return False
        if action.get("type") != "pick":
            return False
        pit = action.get("pit")
        if not isinstance(pit, int):
            return False
        own_pits = P0_PITS if self._player_idx(state, player) == 0 else P1_PITS
        return pit in own_pits and state["pits"][pit] > 0

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        player_idx = self._player_idx(state, player)
        own_store = STORE_0 if player_idx == 0 else STORE_1
        opp = state["players"][1] if player_idx == 0 else state["players"][0]

        new_pits, last = _distribute(state["pits"], action["pit"], player_idx)
        state["pits"] = new_pits
        state["last_move"] = action["pit"]

        if last == own_store:
            state["extra_turn"] = True
            # current_turn unchanged — same player goes again
        else:
            state["extra_turn"] = False
            state["current_turn"] = opp

        # End-of-game sweep: if either side is fully empty, collect all remaining stones
        if all(state["pits"][i] == 0 for i in P0_PITS) or \
           all(state["pits"][i] == 0 for i in P1_PITS):
            state["pits"] = _sweep(state["pits"])

        return state

    def is_game_over(self, state: dict) -> bool:
        return (all(state["pits"][i] == 0 for i in P0_PITS) and
                all(state["pits"][i] == 0 for i in P1_PITS))

    def get_winner(self, state: dict) -> str | None:
        p = state["players"]
        s0, s1 = state["pits"][STORE_0], state["pits"][STORE_1]
        if s0 > s1:
            return p[0]
        if s1 > s0:
            return p[1]
        return None

    def get_computer_action(self, state: dict, player: str) -> dict | None:
        if state.get("current_turn") != player:
            return None
        player_idx = self._player_idx(state, player)
        own_store = STORE_0 if player_idx == 0 else STORE_1
        opp_store = STORE_1 if player_idx == 0 else STORE_0
        own_pits = P0_PITS if player_idx == 0 else P1_PITS

        valid = [p for p in own_pits if state["pits"][p] > 0]
        if not valid:
            return None

        def score(pit: int) -> int:
            new_pits, last = _distribute(state["pits"], pit, player_idx)
            s = new_pits[own_store] - new_pits[opp_store]
            if last == own_store:
                s += 4  # bonus turn is valuable
            return s

        return {"type": "pick", "pit": max(valid, key=score)}
