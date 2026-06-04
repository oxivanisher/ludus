import copy
import random

from ..base import BaseGame, GameMeta

EMOJIS = ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼"]
NUM_PAIRS = len(EMOJIS)   # 8
NUM_CARDS = NUM_PAIRS * 2  # 16
GRID_COLS = 4


class Memory(BaseGame):
    meta = GameMeta(
        slug="memory",
        name="Memory",
        description="Flip cards to find matching pairs. The player with the most pairs wins.",
        min_players=2,
        max_players=2,
        supports_solo=False,
    )

    def initial_state(self, players: list[str]) -> dict:
        deck = EMOJIS * 2
        random.shuffle(deck)
        return {
            "cards": deck,
            "face_up": [False] * NUM_CARDS,
            "matched": [False] * NUM_CARDS,
            "first_pick": None,
            "last_mismatch": None,
            "last_mismatch_values": None,
            "mismatch_id": 0,
            "scores": {players[0]: 0, players[1]: 0},
            "current_turn": players[0],
            "players": players,
            "num_cards": NUM_CARDS,
            "grid_cols": GRID_COLS,
        }

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        if state.get("current_turn") != player:
            return False
        if action.get("type") != "flip":
            return False
        pos = action.get("pos")
        if not isinstance(pos, int) or not (0 <= pos < NUM_CARDS):
            return False
        # Can't flip an already face-up or matched card
        if state["face_up"][pos] or state["matched"][pos]:
            return False
        # Can't flip the same card as the first pick
        if state["first_pick"] == pos:
            return False
        return True

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)
        pos = action["pos"]
        players = state["players"]
        opponent = players[1] if player == players[0] else players[0]

        if state["first_pick"] is None:
            # First flip of the turn
            state["face_up"][pos] = True
            state["first_pick"] = pos
            state["last_mismatch"] = None
        else:
            # Second flip — resolve the pair
            first = state["first_pick"]
            state["face_up"][pos] = True

            if state["cards"][first] == state["cards"][pos]:
                # Match — mark both permanently and award a point
                state["matched"][first] = True
                state["matched"][pos] = True
                state["scores"][player] += 1
                state["face_up"][first] = True
                state["face_up"][pos] = True
                state["last_mismatch"] = None
                state["last_mismatch_values"] = None
                # Same player goes again (turn does NOT change)
            else:
                # Mismatch — flip both back down, pass turn.
                # Keep the values in last_mismatch_values so the frontend can
                # briefly display them even though face_up is already False.
                state["last_mismatch_values"] = [state["cards"][first], state["cards"][pos]]
                state["face_up"][first] = False
                state["face_up"][pos] = False
                state["last_mismatch"] = [first, pos]
                state["mismatch_id"] = state.get("mismatch_id", 0) + 1
                state["current_turn"] = opponent

            state["first_pick"] = None

        return state

    def is_game_over(self, state: dict) -> bool:
        return all(state["matched"])

    def get_winner(self, state: dict) -> str | None:
        players = state["players"]
        s = state["scores"]
        if s[players[0]] > s[players[1]]:
            return players[0]
        if s[players[1]] > s[players[0]]:
            return players[1]
        return None  # draw

    def render_state_for_player(self, state: dict, player: str) -> dict:
        """Mask unrevealed card values so clients cannot read them from the API."""
        if not state.get("cards"):
            return state
        result = {**state}
        result["cards"] = [
            state["cards"][i] if state["face_up"][i] or state["matched"][i] else None
            for i in range(NUM_CARDS)
        ]
        return result
