<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const CELL = 50; // px per cell in the 400×400 viewBox

  const state       = $derived(session.state ?? {});
  const board       = $derived(state.board ?? Array.from({ length: 8 }, () => Array(8).fill(null)));
  const curTurn     = $derived(state.current_turn);
  const players     = $derived(state.players ?? []);
  const counts      = $derived(state.counts ?? {});
  const skipped     = $derived(state.skipped ?? false);
  const rawMoves    = $derived(state.valid_moves ?? []);
  const isMyTurn    = $derived(curTurn === myUsername && session.status === 'playing');
  const myColor     = $derived(players.indexOf(myUsername) === 0 ? 'dark' : 'light');
  const opponent    = $derived(players.find(p => p !== myUsername) ?? '');

  // Set of "r,c" strings for O(1) valid-move lookup
  const validSet = $derived(new Set(rawMoves.map(([r, c]) => `${r},${c}`)));

  function handleClick(row, col) {
    if (!isMyTurn) return;
    if (!validSet.has(`${row},${col}`)) return;
    onAction({ type: 'place', row, col });
  }

  // Piece fill / stroke colours
  const DARK_FILL   = '#1a1a1a';
  const DARK_STROKE = '#555';
  const LIGHT_FILL  = '#f5f5f5';
  const LIGHT_STROKE = '#aaa';

  // Board background colours (classic Reversi green)
  const BG       = '#2d7a2d';
  const BG_DARK  = '#1e5a1e';
  const LINE_CLR = '#1a5c1a';
</script>

<div class="select-none flex flex-col gap-3 max-w-sm mx-auto w-full">

  <!-- Role badge -->
  <p class="text-xs font-semibold uppercase tracking-wide text-center
            {myColor === 'dark' ? 'text-gray-700 dark:text-gray-300' : 'text-indigo-600 dark:text-indigo-400'}">
    {myColor === 'dark' ? $_('games.reversi.you_are_dark') : $_('games.reversi.you_are_light')}
  </p>

  <!-- Skipped notice -->
  {#if skipped && session.status === 'playing'}
    <p class="text-xs text-center px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-medium">
      {isMyTurn
        ? $_('games.reversi.skipped_opps', { values: { player: opponent } })
        : $_('games.reversi.skipped_yours')}
    </p>
  {/if}

  <!-- Hint -->
  {#if session.status === 'playing'}
    <p class="text-sm text-center font-medium
              {isMyTurn
                ? 'text-indigo-700 dark:text-indigo-300'
                : 'text-gray-400 dark:text-gray-500'}">
      {isMyTurn
        ? $_('games.reversi.hint_place')
        : $_('games.reversi.hint_wait', { values: { player: curTurn } })}
    </p>
  {/if}

  <!-- Board -->
  <svg
    viewBox="0 0 400 400"
    class="w-full rounded-lg shadow-lg"
    style="touch-action: manipulation; background: {BG};"
  >
    <!-- Grid lines -->
    <g stroke={LINE_CLR} stroke-width="1">
      {#each Array(7) as _, i}
        <line x1={(i + 1) * CELL} y1="0" x2={(i + 1) * CELL} y2="400"/>
        <line x1="0" y1={(i + 1) * CELL} x2="400" y2={(i + 1) * CELL}/>
      {/each}
    </g>

    <!-- Corner dots (traditional Reversi board markers) -->
    {#each [2, 6] as dr}
      {#each [2, 6] as dc}
        <circle cx={dc * CELL} cy={dr * CELL} r="4" fill={LINE_CLR}/>
      {/each}
    {/each}

    <!-- Cells -->
    {#each { length: 8 } as _, row}
      {#each { length: 8 } as _, col}
        {@const piece  = board[row]?.[col]}
        {@const valid  = validSet.has(`${row},${col}`)}
        {@const cx     = col * CELL + CELL / 2}
        {@const cy     = row * CELL + CELL / 2}

        <!-- Hit area -->
        <rect
          x={col * CELL} y={row * CELL}
          width={CELL} height={CELL}
          fill="transparent"
          class={valid && isMyTurn ? 'cursor-pointer' : ''}
          onclick={() => handleClick(row, col)}
        />

        {#if piece}
          <circle
            cx={cx} cy={cy} r="21"
            fill={piece === 'dark' ? DARK_FILL : LIGHT_FILL}
            stroke={piece === 'dark' ? DARK_STROKE : LIGHT_STROKE}
            stroke-width="1.5"
            pointer-events="none"
          />
        {:else if valid && isMyTurn}
          <!-- Valid move indicator -->
          <circle
            cx={cx} cy={cy} r="9"
            fill="rgba(255,255,255,0.28)"
            pointer-events="none"
          />
        {/if}
      {/each}
    {/each}
  </svg>

  <!-- Piece counts -->
  <div class="flex justify-between text-sm px-1">
    {#each players as p, idx}
      {@const color = idx === 0 ? 'dark' : 'light'}
      {@const isMe  = p === myUsername}
      <div class="flex items-center gap-2">
        <span class="inline-block w-4 h-4 rounded-full border
          {color === 'dark'
            ? 'bg-gray-900 border-gray-600'
            : 'bg-gray-100 border-gray-400 dark:bg-gray-200'}">
        </span>
        <span class="{isMe ? 'font-semibold' : 'text-gray-500 dark:text-gray-400'}">
          {p}{isMe ? ' (you)' : ''}
        </span>
        <span class="text-gray-400 tabular-nums">
          {counts[p] ?? 0}
        </span>
      </div>
    {/each}
  </div>

</div>
