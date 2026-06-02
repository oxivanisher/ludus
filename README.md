# Ludus

A self-hostable, privacy-first multiplayer gaming platform for simple turn-based games.

Play Tic-Tac-Toe, Battleship, Connect Four, and more — with anyone, on any device, with no accounts, no tracking, and no chat.

---

## Games

| Game | Players | Description |
|---|---|---|
| Tic-Tac-Toe | 2 | Classic 3×3 grid — get three in a row to win |
| Connect Four | 2 | Drop pieces into a 7×6 grid — connect four to win |
| Battleship | 2 | Place your fleet and sink all 10 enemy ships |

---

## Why Ludus?

Most online gaming platforms require accounts, collect data, and expose players to chat. Ludus is designed with the opposite priorities:

- **No accounts.** Players identify themselves with a username they type when joining a game. Nothing is stored permanently.
- **No tracking.** Sessions expire automatically. No analytics, no cookies beyond your anonymous player token.
- **No chat.** The only interaction is the game itself — safe for children.
- **Self-hostable.** One `docker compose up` and you're running your own instance.
- **Open source.** Add your own games via the plugin system.

---

## How it works

### Player identity

When you first visit Ludus, your browser generates a random anonymous token and stores it in `localStorage`. This token is your identity — it lets you see your active games across sessions without logging in.

**Moving to another device?** Go to "My Token" in the top bar, and either copy the token string or scan the QR code on your other device. The QR encodes a URL that imports your token automatically when opened.

### Starting a game

1. Click **New Game**, pick a game type, and enter a username.
2. Share the invite link with your opponent, or create a **public game** anyone on the server can join.
3. Your opponent opens the link, enters their username, and the game begins.
4. Come back whenever it is your turn — sessions wait for days.

### Turn notifications (optional)

If you allow notifications, Ludus will send a browser push notification when it becomes your turn — even if the tab is closed. You will not be notified while you are actively viewing the game. This is opt-in per game and can be disabled at any time from the game page.

---

## Self-hosting

### Quick start

```bash
git clone https://github.com/oxivanisher/ludus.git
cd ludus

cp .env.example .env
# Edit .env — set LUDUS_DOMAIN to your domain

docker compose up -d
```

Point your Traefik (or Nginx — see `docs/nginx.md`) instance at port 8000 and you are done.

### Push notifications (optional)

Generate VAPID keys and add them to `.env`:

```bash
docker compose run --rm ludus python -m core.vapid_gen
```

Add the printed values to your `.env` file, then restart: `docker compose up -d`.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379` | Redis connection string |
| `SESSION_TTL_DAYS` | `30` | Days until an inactive session expires |
| `FINISHED_SESSION_TTL_DAYS` | `3` | Days a finished session remains viewable |
| `LUDUS_DOMAIN` | `ludus.localhost` | Domain name for Traefik routing |
| `VAPID_PRIVATE_KEY` | _(empty)_ | VAPID private key — push disabled if unset |
| `VAPID_PUBLIC_KEY` | _(empty)_ | VAPID public key |
| `VAPID_CONTACT_EMAIL` | `admin@example.com` | Contact email sent with push requests |

### Updating

```bash
docker compose pull && docker compose up -d
```

---

## Adding a game

Ludus has a plugin system — drop a new game into `backend/games/` and it is discovered automatically at startup.

### 1. Implement the game logic

Create `backend/games/<slug>/game.py` and subclass `BaseGame`:

```python
from games.base import BaseGame, GameMeta

class MyGame(BaseGame):
    meta = GameMeta(
        slug="mygame",
        name="My Game",
        description="A short description.",
        min_players=2,
        max_players=2,
    )

    def initial_state(self, players: list[str]) -> dict:
        return {"board": [], "current_turn": players[0]}

    def validate_action(self, state: dict, player: str, action: dict) -> bool:
        ...

    def apply_action(self, state: dict, player: str, action: dict) -> dict:
        # Return the new state — do not mutate the input
        ...

    def get_winner(self, state: dict) -> str | None:
        # Return the winning username, or None
        ...

    def is_game_over(self, state: dict) -> bool:
        ...

    def render_state_for_player(self, state: dict, player: str) -> dict:
        # Optional: filter hidden information (e.g. opponent's ships in Battleship)
        return state
```

Also create an empty `backend/games/<slug>/__init__.py`.

### 2. Create the frontend component

Create `frontend/src/games/MyGame.svelte`. It receives three props:

```svelte
<script>
  let { session, myUsername, onAction } = $props();
  // session.state contains your game-specific state (already filtered for this player)
  // call onAction({ ...your action... }) when the player makes a move
</script>
```

Optionally add translation files at `frontend/src/games/<slug>/i18n/en.json` (and `de.json`, etc.) — they are loaded automatically.

### 3. Register the component

In `frontend/src/pages/GameRoom.svelte`, import your component and add it to `GAME_COMPONENTS`:

```js
import MyGame from "../games/MyGame.svelte";

const GAME_COMPONENTS = {
  tictactoe: TicTacToe,
  mygame: MyGame,
};
```

That is all. The backend auto-discovers your `MyGame` class; the frontend routes to your component by `game_slug`.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, WebSockets |
| State | Redis (no SQL database — sessions are ephemeral) |
| Frontend | Svelte 5, Vite, Tailwind CSS, svelte-i18n |
| Push | Web Push / VAPID (`pywebpush`) |
| Infrastructure | Docker Compose, GitHub Container Registry |

---

## Contributing

Pull requests are welcome. When adding a game, please include:
- The Python plugin in `backend/games/<slug>/`
- The Svelte component in `frontend/src/games/`
- Translation files for at least English (`en.json`)
- A row in the Games table in this README

Please do not add: accounts, user tracking, chat, or features that would compromise the privacy-first design.

---

## License

MIT
