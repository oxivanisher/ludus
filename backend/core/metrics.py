"""
Prometheus metrics for Ludus.

All metrics are pure aggregates — no per-player, per-session, or per-IP data.
The metrics HTTP server runs on a dedicated port (METRICS_PORT) so it can be
firewalled independently from the main application port.
"""

import threading

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import start_http_server as _prom_start

from .config import settings

# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

sessions_created = Counter(
    "ludus_sessions_created_total",
    "Sessions created",
    ["game", "visibility"],  # visibility: public | private | vs_computer
)

sessions_started = Counter(
    "ludus_sessions_started_total",
    "Sessions that reached playing state (all players joined)",
    ["game"],
)

sessions_finished = Counter(
    "ludus_sessions_finished_total",
    "Sessions that finished",
    ["game", "outcome"],  # outcome: win | draw | forfeit
)

sessions_cancelled = Counter(
    "ludus_sessions_cancelled_total",
    "Sessions cancelled before starting",
)

sessions_rematched = Counter(
    "ludus_sessions_rematched_total",
    "Rematch sessions created",
    ["game"],
)

sessions_active = Gauge(
    "ludus_sessions_active",
    "Sessions currently in playing state (resets to 0 on server restart)",
)

sessions_waiting = Gauge(
    "ludus_sessions_waiting",
    "Sessions currently waiting for players (resets to 0 on server restart)",
)

session_duration_seconds = Histogram(
    "ludus_session_duration_seconds",
    "Duration of a game session from start (all players joined) to finish",
    ["game"],
    buckets=[30, 60, 120, 300, 600, 1200, 1800, 3600, 7200],
)

# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

actions_processed = Counter(
    "ludus_actions_total",
    "Game actions processed successfully",
    ["game"],
)

# ---------------------------------------------------------------------------
# WebSocket connections
# ---------------------------------------------------------------------------

websocket_connections = Gauge(
    "ludus_websocket_connections",
    "Currently active WebSocket connections",
)

websocket_connections_total = Counter(
    "ludus_websocket_connections_total",
    "Total WebSocket connections established",
)

# ---------------------------------------------------------------------------
# Push notifications
# ---------------------------------------------------------------------------

push_sent = Counter(
    "ludus_push_sent_total",
    "Push notifications dispatched",
)

push_skipped_online = Counter(
    "ludus_push_skipped_online_total",
    "Push notifications skipped because the player had an active WebSocket",
)

push_stale_removed = Counter(
    "ludus_push_stale_removed_total",
    "Stale push subscriptions removed (browser unsubscribed or expired)",
)

# ---------------------------------------------------------------------------
# Server start
# ---------------------------------------------------------------------------

_started = False
_lock = threading.Lock()


def start_metrics_server() -> None:
    global _started
    if not settings.metrics_enabled:
        return
    with _lock:
        if _started:
            return
        _prom_start(settings.metrics_port)
        _started = True
