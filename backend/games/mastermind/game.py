import copy
from collections import Counter

from ..base import BaseGame, GameMeta

COLORS = ["red", "orange", "yellow", "green", "blue", "purple"]
CODE_LENGTH = 4
MAX_GUESSES = 10


def _score(secret: list, guess: list) -> tuple[int, int]:
    blacks = sum(s == g for s, g in zip(secret, guess))
    s_unmatched = Counter(s for s, g in zip(secret, guess) if s != g)
    g_unmatched = Counter(g for s, g in zip(secret, guess) if s != g)
    whites = sum(min(s_unmatched[c], g_unmatched[c]) for c in s_unmatched)
    return blacks, whites


class Mastermind(BaseGame):
    meta = GameMeta(
        slug="mastermind",
        name="Mastermind",
        description="Set a secret color code or crack it before guesses run out.",
        min_players=2,
        max_players=2,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {
            "phase": "setting",
            "code_maker": players[0],
            "code_breaker": players[1],
            "secret_code": None,
            "guesses": [],
            "current_turn": players[0],
        }

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        action_type = action.get("type")

        if action_type == "set_code":
            if state["phase"] != "setting":
                return False
            if player != state["code_maker"]:
                return False
            colors = action.get("colors", [])
            return len(colors) == CODE_LENGTH and all(c in COLORS for c in colors)

        if action_type == "guess":
            if state["phase"] != "guessing":
                return False
            if player != state["code_breaker"]:
                return False
            if len(state["guesses"]) >= MAX_GUESSES:
                return False
            colors = action.get("colors", [])
            return len(colors) == CODE_LENGTH and all(c in COLORS for c in colors)

        return False

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        state = copy.deepcopy(state)

        if action["type"] == "set_code":
            state["secret_code"] = action["colors"]
            state["phase"] = "guessing"
            state["current_turn"] = state["code_breaker"]

        elif action["type"] == "guess":
            blacks, whites = _score(state["secret_code"], action["colors"])
            state["guesses"].append({
                "colors": action["colors"],
                "blacks": blacks,
                "whites": whites,
            })
            # current_turn stays with code_breaker unless game over

        return state

    def is_game_over(self, state: dict) -> bool:
        if state["phase"] != "guessing" or not state["guesses"]:
            return False
        last = state["guesses"][-1]
        return last["blacks"] == CODE_LENGTH or len(state["guesses"]) >= MAX_GUESSES

    def get_winner(self, state: dict) -> str | None:
        if not state["guesses"]:
            return None
        last = state["guesses"][-1]
        if last["blacks"] == CODE_LENGTH:
            return state["code_breaker"]
        return state["code_maker"]

    def render_state_for_player(self, state: dict, player: str) -> dict:
        game_over = self.is_game_over(state)
        is_code_maker = player == state["code_maker"]
        return {
            "phase": state["phase"],
            "current_turn": state.get("current_turn"),
            "code_maker": state["code_maker"],
            "code_breaker": state["code_breaker"],
            "secret_code": state["secret_code"] if (is_code_maker or game_over) else None,
            "guesses": state["guesses"],
            "guesses_remaining": MAX_GUESSES - len(state["guesses"]),
            "max_guesses": MAX_GUESSES,
            "code_length": CODE_LENGTH,
            "colors": COLORS,
        }
