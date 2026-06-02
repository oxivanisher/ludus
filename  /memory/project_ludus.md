---
name: Ludus project
description: Open-source self-hostable multiplayer gaming platform — current state, stack, and what's done
type: project
originSessionId: b547f013-9955-4e98-900a-00f920e4b12d
---
Building "Ludus" — an open-source, self-hostable, privacy-first multiplayer gaming platform for simple turn-based games.

**Why:** Child-safe design (no accounts, no chat, no data retention). Simple games (tic-tac-toe, battleship, mastermind, etc.).

**Location:** `/home/oxi/dev/PycharmProjects/PyWebGames/ludus/`

**Stack:**
- Backend: Python 3.12 / FastAPI + WebSockets + Redis (no SQL — sessions are ephemeral with TTL)
- Frontend: Svelte 5 + Vite 8 + Tailwind CSS 3 (dark mode: `media` strategy, auto from OS)
- Infrastructure: Docker Compose + Traefik (user already has Traefik; port 8000 also exposed for local dev)
- Push notifications: Web Push / VAPID via `pywebpush` (optional, disabled if VAPID keys not set)
- Build: multi-stage Dockerfile — Node builds frontend inside container, Python serves it. No Node on host.

## What is fully implemented

- **Core platform**: session lifecycle, WebSocket real-time sync, player token system (localStorage UUID)
- **Token export/import**: QR code encodes `/?import_token=…` URL; scanning auto-imports on other device
- **Push notifications**: opt-in per game; suppressed when player has active WebSocket (already watching)
- **Tic-Tac-Toe**: fully working reference game — Python plugin + Svelte board
- **Play Again / rematch**: either player triggers it; new session auto-created with turn order reversed; other player's tab updates via WS broadcast without refresh
- **Platform stats**: `stats:active_games` and `stats:total_games` Redis counters shown on lobby with pulsing green dot
- **Dark mode**: automatic from OS preference, all components styled
- **SPA routing**: catch-all `/{full_path:path}` route serves `index.html` for all non-API paths (fixes 404 on direct `/game/{uuid}` navigation)
- **WS token via query param**: `?token=…` on WS URL so `my_username` is correct on first push (fixes identity loss on reload)
- **`{#key sessionId}` in App.svelte**: forces GameRoom remount on session change (fixes "Go to Rematch" doing nothing)

## Key architectural decisions

- Player identity = random UUID token in `localStorage`; sent as `X-Player-Token` header on REST, `?token=` on WebSocket
- `SessionResponse.my_username` tells each viewer who they are — tokens never exposed to other clients
- `render_state_for_player()` on `BaseGame` for hidden-information games (Battleship, Mastermind)
- `core/connections.py`: in-memory WS registry; push checks this before dispatching
- Redis AOF (`--appendonly yes`) + named volume `ludus_redis_data` = sessions survive reboots
- Stats counters have no TTL — `total_games` accumulates forever; `active_games` may drift ±1 if session expires mid-game (acceptable for display purposes)

## Running the stack

```bash
cd /home/oxi/dev/PycharmProjects/PyWebGames/ludus
docker compose up -d --build   # builds frontend inside container
```
App at http://localhost:8000. API docs at http://localhost:8000/docs.

Backend venv (for local testing without Docker): `backend/.venv` — activate and run from `backend/` dir.

## Next games to implement (priority order)

See `docs/games.md` for full details.
1. **Connect Four** — gravity mechanic, near-zero new concepts
2. **Battleship** — reference implementation for hidden state (`render_state_for_player`)
3. **Mastermind** — asymmetric roles (codemaker / codebreaker)
4. **Dots and Boxes** — bonus-turn mechanic, multi-point scoring
5. **Memory / Pairs** — ephemeral hidden state (flip-and-hide)

## Adding a game — checklist

- `backend/games/<slug>/__init__.py` (empty)
- `backend/games/<slug>/game.py` — subclass `BaseGame`, set `meta: GameMeta`
- `frontend/src/games/MyGame.svelte` — props: `session`, `myUsername`, `onAction`
- Register in `frontend/src/pages/GameRoom.svelte` `GAME_COMPONENTS` map
