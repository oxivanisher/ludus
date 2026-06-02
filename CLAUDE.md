# Ludus — Claude context

Ludus is a self-hostable, privacy-first multiplayer gaming platform for simple turn-based games. No accounts, no chat, no persistent user data.

## Project structure

```
(project root)/
├── backend/                    Python / FastAPI backend
│   ├── main.py                 App entry point, router registration, lifespan
│   ├── core/
│   │   ├── config.py           Pydantic-settings Config (reads from .env)
│   │   ├── redis_client.py     Async Redis singleton
│   │   ├── session.py          All session CRUD (create, join, apply_action)
│   │   ├── plugin_loader.py    Auto-discovers BaseGame subclasses at startup
│   │   ├── connections.py      In-memory WebSocket presence registry
│   │   ├── push.py             Web Push dispatch (skips if player is online)
│   │   └── vapid_gen.py        CLI helper to generate VAPID keys
│   ├── api/
│   │   ├── sessions.py         REST endpoints (/api/games, /api/sessions, …)
│   │   ├── push.py             Push subscribe/unsubscribe endpoints
│   │   └── websocket.py        WebSocket endpoint (/ws/{session_id})
│   ├── games/
│   │   ├── base.py             BaseGame ABC + GameMeta dataclass
│   │   └── tictactoe/game.py   Reference game plugin
│   └── models/schemas.py       Pydantic response models
├── frontend/                   Svelte 5 + Vite + Tailwind
│   ├── public/sw.js            Service worker (receives push, shows notification)
│   └── src/
│       ├── lib/
│       │   ├── token.js        localStorage player token + export/import logic
│       │   ├── api.js          Fetch wrapper (auto-attaches X-Player-Token)
│       │   ├── ws.js           WebSocket wrapper with auto-reconnect
│       │   └── push.js         Push subscription management
│       ├── pages/
│       │   ├── Lobby.svelte    My Games dashboard + new game form
│       │   └── GameRoom.svelte Join flow, invite link, turn indicator, game mount
│       ├── components/
│       │   ├── TokenManager.svelte  Token display, QR code, import
│       │   └── GameCard.svelte      Session summary card
│       └── games/
│           ├── TicTacToe.svelte
│           ├── ConnectFour.svelte
│           ├── Battleship.svelte
│           └── */i18n/          Per-game translation files (en.json, de.json, …)
├── docs/nginx.md               Nginx reverse proxy reference config
├── .github/workflows/docker.yml  CI: build + push to ghcr.io on main / tags
├── docker-compose.yml          Uses ghcr.io/oxivanisher/ludus:latest
└── .env.example                All env vars with defaults
```

## Running locally

```bash
# Backend
cd backend
uv pip install -e .
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev     # proxies /api and /ws to localhost:8000
```

The Vite dev server proxies API and WebSocket calls to the backend automatically (see `vite.config.js`).

## Key architecture decisions

### No database
All state lives in Redis with TTL. Sessions expire automatically — no cleanup jobs, no retained user data. This is intentional: simplicity and privacy.

### Player token
Each browser generates a random UUID on first visit and stores it in `localStorage`. The token is sent as `X-Player-Token` on every API request and in the WebSocket `identify` message. It is never stored in a cookie and never sent to any third party.

The server associates tokens with sessions in Redis (`player:{token}:sessions` SET). `SessionResponse.my_username` tells the frontend which player they are — tokens are never exposed to other clients.

### Push notifications
Push is entirely optional. Set `VAPID_PRIVATE_KEY` / `VAPID_PUBLIC_KEY` to enable. Push subscriptions are stored in Redis per player token (`player:{token}:push_subs`).

Before dispatching a push, `core/push.py` checks `core/connections.py` — if the player has an active WebSocket on that session, no push is sent (they are already watching). This avoids double-notifying.

### Plugin system
`core/plugin_loader.py` walks the `games/` package at startup and registers every concrete `BaseGame` subclass it finds. Adding a new game requires:
1. A Python module under `backend/games/<slug>/` with a `BaseGame` subclass
2. A Svelte component under `frontend/src/games/` registered in `GameRoom.svelte`'s `GAME_COMPONENTS` map

### WebSocket broadcast
When a player makes a move, the updated state is broadcast to all WebSocket connections on that session. Each connection receives a personalised view (`render_state_for_player`) so hidden-information games (Battleship, Mastermind) work correctly.

## Privacy invariants — do not break these

- No personally identifiable information is ever stored (no email, no IP logging, no usernames persisted beyond a session's TTL)
- Player tokens must never appear in responses visible to other clients — always use `SessionResponse.from_session(session, viewer_token)` which sets `my_username` and filters state
- No chat features
- Sessions must always have a TTL in Redis

## Adding a game — checklist

- [ ] `backend/games/<slug>/__init__.py` (empty)
- [ ] `backend/games/<slug>/game.py` — subclass `BaseGame`, set `meta: GameMeta`
- [ ] Implement all abstract methods; override `render_state_for_player` if the game has hidden information
- [ ] `frontend/src/games/MyGame.svelte` — props: `session`, `myUsername`, `onAction`
- [ ] Register in `frontend/src/pages/GameRoom.svelte` `GAME_COMPONENTS`
- [ ] Entry in README games table
