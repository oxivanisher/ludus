<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  // Board layout: 15×15 grid, 20px per cell, 20px margin → viewBox 320×320
  const MARGIN = 20;
  const CELL   = 20;
  const N      = 15;
  const STONE_R = 9;

  // Star points (hoshi) on a standard 15×15 board
  const STAR_POINTS = [
    [3,3],[3,7],[3,11],
    [7,3],[7,7],[7,11],
    [11,3],[11,7],[11,11],
  ];

  const state     = $derived(session.state ?? {});
  const board     = $derived(state.board ?? Array.from({ length: N }, () => Array(N).fill(null)));
  const curTurn   = $derived(state.current_turn);
  const players   = $derived(state.players ?? []);
  const lastMove  = $derived(state.last_move ?? null);
  const isMyTurn  = $derived(curTurn === myUsername && session.status === 'playing');
  const myColor   = $derived(players.indexOf(myUsername) === 0 ? 'black' : 'white');

  let hover = $state(null); // [row, col] | null

  function intersectionXY(row, col) {
    return [MARGIN + col * CELL, MARGIN + row * CELL];
  }

  function svgToIntersection(event) {
    const rect = event.currentTarget.getBoundingClientRect();
    const scale = (N - 1) * CELL / (rect.width - MARGIN * 2 * (rect.width / 320));
    const svgX = (event.clientX - rect.left) * (320 / rect.width);
    const svgY = (event.clientY - rect.top)  * (320 / rect.height);
    const col = Math.round((svgX - MARGIN) / CELL);
    const row = Math.round((svgY - MARGIN) / CELL);
    if (col < 0 || col >= N || row < 0 || row >= N) return null;
    return [row, col];
  }

  function handleClick(event) {
    if (!isMyTurn) return;
    const pos = svgToIntersection(event);
    if (!pos) return;
    const [row, col] = pos;
    if (board[row]?.[col] !== null) return;
    onAction({ type: 'place', row, col });
    hover = null;
  }

  function handleMouseMove(event) {
    if (!isMyTurn) { hover = null; return; }
    const pos = svgToIntersection(event);
    if (!pos) { hover = null; return; }
    const [row, col] = pos;
    hover = board[row]?.[col] === null ? [row, col] : null;
  }

  function handleMouseLeave() { hover = null; }
</script>

<div class="select-none flex flex-col gap-3 max-w-sm mx-auto w-full">

  <!-- Role badge -->
  <p class="text-xs font-semibold uppercase tracking-wide text-center
            {myColor === 'black' ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400 dark:text-gray-500'}">
    {myColor === 'black' ? $_('games.gomoku.you_are_black') : $_('games.gomoku.you_are_white')}
  </p>

  <!-- Hint -->
  {#if session.status === 'playing'}
    <p class="text-sm text-center font-medium
              {isMyTurn ? 'text-indigo-700 dark:text-indigo-300' : 'text-gray-400 dark:text-gray-500'}">
      {isMyTurn
        ? $_('games.gomoku.hint_place')
        : $_('games.gomoku.hint_wait', { values: { player: curTurn } })}
    </p>
  {/if}

  <!-- Board -->
  <svg
    viewBox="0 0 320 320"
    class="w-full rounded-lg shadow {isMyTurn ? 'cursor-crosshair' : ''}"
    onclick={handleClick}
    onmousemove={handleMouseMove}
    onmouseleave={handleMouseLeave}
    style="touch-action: manipulation;"
  >
    <!-- Wooden background -->
    <rect width="320" height="320" fill="#DCB167" rx="6"/>

    <!-- Grid lines -->
    <g stroke="#8B6425" stroke-width="0.75">
      {#each { length: N } as _, i}
        <line x1={MARGIN + i * CELL} y1={MARGIN}          x2={MARGIN + i * CELL} y2={MARGIN + (N-1)*CELL}/>
        <line x1={MARGIN}            y1={MARGIN + i * CELL} x2={MARGIN + (N-1)*CELL} y2={MARGIN + i * CELL}/>
      {/each}
    </g>

    <!-- Star points -->
    {#each STAR_POINTS as [r, c]}
      <circle cx={MARGIN + c * CELL} cy={MARGIN + r * CELL} r="2.5" fill="#8B6425"/>
    {/each}

    <!-- Stones and hover ghost -->
    {#each { length: N } as _, r}
      {#each { length: N } as _, c}
        {@const piece    = board[r]?.[c]}
        {@const cx       = MARGIN + c * CELL}
        {@const cy       = MARGIN + r * CELL}
        {@const isLast   = lastMove && lastMove[0] === r && lastMove[1] === c}
        {@const isHover  = hover && hover[0] === r && hover[1] === c}

        {#if piece}
          <circle {cx} {cy} r={STONE_R}
            fill={piece === 'black' ? '#111' : '#f5f5f5'}
            stroke={piece === 'black' ? '#444' : '#aaa'}
            stroke-width="0.75"
            pointer-events="none"
          />
          {#if isLast}
            <!-- Dot marks the last-placed stone -->
            <circle {cx} {cy} r="3"
              fill={piece === 'black' ? '#fff' : '#333'}
              pointer-events="none"
            />
          {/if}
        {:else if isHover}
          <circle {cx} {cy} r={STONE_R}
            fill={myColor === 'black' ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.5)'}
            stroke={myColor === 'black' ? '#444' : '#aaa'}
            stroke-width="0.75"
            pointer-events="none"
          />
        {/if}
      {/each}
    {/each}
  </svg>

  <!-- Player labels with stone previews -->
  <div class="flex justify-between text-sm px-1">
    {#each players as p, idx}
      {@const color = idx === 0 ? 'black' : 'white'}
      {@const isMe  = p === myUsername}
      <div class="flex items-center gap-2">
        <span class="inline-block w-4 h-4 rounded-full border
          {color === 'black'
            ? 'bg-gray-900 border-gray-600'
            : 'bg-gray-100 border-gray-400 dark:bg-gray-200'}">
        </span>
        <span class="{isMe ? 'font-semibold' : 'text-gray-500 dark:text-gray-400'}">
          {p}{isMe ? ' (you)' : ''}
        </span>
      </div>
    {/each}
  </div>

</div>
