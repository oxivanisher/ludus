from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GameMeta:
    slug: str
    name: str
    description: str
    min_players: int
    max_players: int


class BaseGame(ABC):
    """
    Base class for all Ludus game plugins.

    Implement this class to add a new game. Place your module anywhere under
    backend/games/<your_slug>/ and it will be auto-discovered at startup.
    """

    meta: GameMeta  # set as a class attribute in every subclass

    @abstractmethod
    def initial_state(self, players: list[str]) -> dict:
        """Return the starting game state for the given ordered list of usernames."""
        ...

    @abstractmethod
    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        """Return True if `action` is legal for `player` in the current `state`."""
        ...

    @abstractmethod
    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        """
        Apply `action` and return the new state.
        Only called after validate_action returned True.
        Must not mutate the input state dict — return a new one.
        """
        ...

    @abstractmethod
    def get_winner(self, state: dict) -> str | None:
        """Return the winning username, or None if the game is not yet won."""
        ...

    @abstractmethod
    def is_game_over(self, state: dict) -> bool:
        """Return True if the game has ended (win or draw)."""
        ...

    def render_state_for_player(self, state: dict, player: str) -> dict:
        """
        Return a player-specific view of the state.
        Override for games with hidden information (Battleship, Mastermind, …).
        Default implementation returns the full state unchanged.
        """
        return state
