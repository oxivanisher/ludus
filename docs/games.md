# Game roadmap

Games are grouped by implementation effort and what new concept each one introduces to the plugin system.

## Implemented

| Game | Players | Notes |
|---|---|---|
| Tic-Tac-Toe | 2 | Reference implementation |
| Connect Four | 2 | Gravity mechanic (column-drop) |
| Battleship | 2 | Hidden state per player; Russian fleet rules; hits grant extra shots |

## Tier 1 — straightforward, each teaches one new concept

| Game | Players | New concept |
|---|---|---|
| Gomoku (Five in a Row) | 2 | Almost identical to Tic-Tac-Toe on 15×15 — reusable logic |
| Dots and Boxes | 2+ | Multi-point scoring; extra-turn mechanic (player keeps turn after completing a box) |
| Hangman | 2 | Asymmetric roles + `render_state_for_player` (guesser hides full word) |
| Memory / Pairs | 2+ | Ephemeral hidden state: unmatched flipped cards must be hidden between turns |

## Tier 2 — moderate complexity, high value

| Game | Players | New concept |
|---|---|---|
| Mastermind | 2 | Asymmetric roles (codemaker vs codebreaker); feedback encoding (black/white pegs) |
| Reversi / Othello | 2 | Valid-move highlighting; disc-flipping chains; edge-case game-over (no moves for either player) |
| Checkers | 2 | Multi-jump chains; forced captures; piece promotion |
| Ultimate Tic-Tac-Toe | 2 | Meta-board directing where opponent must play; can reuse Tic-Tac-Toe sub-board logic |

## Tier 3 — ambitious, worth it when the platform is mature

| Game | Players | Notes |
|---|---|---|
| Chess | 2 | Full move generation, check/checkmate/stalemate, special moves (castling, en passant, promotion) |
| Go Fish | 2–4 | First natural multi-player card game; hidden hands per player |
| Crazy Eights | 2–4 | Uno-like without trademark issues; hidden hands, draw pile, suit/rank matching |

## Suggested implementation order

1. **Mastermind** — asymmetric roles, different UI pattern from grid games
2. **Dots and Boxes** — multi-point scoring and bonus-turn logic
3. **Memory / Pairs** — ephemeral hidden state (flip-and-hide)
4. **Checkers** — first game with genuinely complex move validation
5. **Chess** — once the platform is stable and well-tested
