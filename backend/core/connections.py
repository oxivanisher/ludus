"""
In-memory registry of active WebSocket connections per session.
Used by both the WebSocket handler and the push notification module
to decide whether a player is currently watching a game.

Note: this is per-process. In a multi-instance deployment you would
replace is_connected() with a Redis presence check instead.
"""

from __future__ import annotations
from typing import Any

# session_id → { player_token → WebSocket }
_registry: dict[str, dict[str, Any]] = {}


def register(session_id: str, player_token: str, ws: Any) -> None:
    _registry.setdefault(session_id, {})[player_token] = ws


def unregister(session_id: str, player_token: str) -> None:
    session_sockets = _registry.get(session_id, {})
    session_sockets.pop(player_token, None)
    if not session_sockets:
        _registry.pop(session_id, None)


def is_connected(session_id: str, player_token: str) -> bool:
    return player_token in _registry.get(session_id, {})


def get_sockets(session_id: str) -> dict[str, Any]:
    return dict(_registry.get(session_id, {}))
