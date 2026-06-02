import importlib
import pkgutil
from pathlib import Path

from games.base import BaseGame

_registry: dict[str, BaseGame] = {}


def load_plugins() -> None:
    """
    Walk the games/ package and register every concrete BaseGame subclass found.
    Add a new game by dropping a module into games/<slug>/ — no changes needed here.
    """
    games_path = Path(__file__).parent.parent / "games"
    for finder, name, _ in pkgutil.walk_packages(
        path=[str(games_path)], prefix="games.", onerror=lambda e: None
    ):
        if name == "games.base":
            continue
        importlib.import_module(name)

    for cls in _all_subclasses(BaseGame):
        if hasattr(cls, "meta"):
            _registry[cls.meta.slug] = cls()


def _all_subclasses(cls: type) -> list[type]:
    result = []
    for sub in cls.__subclasses__():
        result.append(sub)
        result.extend(_all_subclasses(sub))
    return result


def get_game(slug: str) -> BaseGame | None:
    return _registry.get(slug)


def list_games() -> list[BaseGame]:
    return list(_registry.values())
