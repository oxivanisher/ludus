<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  // Board: 5×5 dots, 4×4 boxes. viewBox 220×220, margin 20, cell 45.
  const MARGIN = 20;
  const CELL   = 45;
  const GRID   = 5;   // dots per side
  const N      = 4;   // boxes / segments per side
  const DOT_R  = 4;
  const HIT    = 9;   // half-width of click target around each line

  // Player colours
  const P_LINE = ['#f59e0b', '#6366f1'];   // amber, indigo
  const P_FILL = ['rgba(245,158,11,0.18)', 'rgba(99,102,241,0.18)'];

  const state     = $derived(session.state ?? {});
  const hLines    = $derived(state.h_lines ?? Array.from({length: GRID}, () => Array(N).fill(null)));
  const vLines    = $derived(state.v_lines ?? Array.from({length: N},    () => Array(GRID).fill(null)));
  const boxes     = $derived(state.boxes   ?? Array.from({length: N},    () => Array(N).fill(null)));
  const scores    = $derived(state.scores  ?? {});
  const curTurn   = $derived(state.current_turn);
  const players   = $derived(state.players ?? []);
  const extraTurn = $derived(state.extra_turn ?? false);
  const isMyTurn  = $derived(curTurn === myUsername && session.status === 'playing');
  const myIdx     = $derived(players.indexOf(myUsername));
  const isComputer = $derived(curTurn === 'Computer' && session.status === 'playing');

  let hover = $state(null); // {o, r, c} | null

  function dot(r, c) {
    return [MARGIN + c * CELL, MARGIN + r * CELL];
  }

  function drawLine(o, r, c) {
    if (!isMyTurn) return;
    onAction({ type: 'line', orientation: o, row: r, col: c });
    hover = null;
  }

  const hint = $derived((() => {
    if (session.status !== 'playing') return null;
    if (isComputer)    return $_('games.dots_and_boxes.hint_computer');
    if (!isMyTurn)     return $_('games.dots_and_boxes.hint_wait', { values: { player: curTurn } });
    if (extraTurn)     return $_('games.dots_and_boxes.hint_extra');
    return $_('games.dots_and_boxes.hint_draw');
  })());

  function lineColor(owner) {
    return owner !== null ? P_LINE[owner] : null;
  }
  function boxFill(owner) {
    if (!owner) return null;
    return P_FILL[players.indexOf(owner)];
  }
  function boxStroke(owner) {
    if (!owner) return null;
    return P_LINE[players.indexOf(owner)];
  }
  function hoverColor() {
    return myIdx === 0 ? 'rgba(245,158,11,0.4)' : 'rgba(99,102,241,0.4)';
  }
</script>

<div class="select-none flex flex-col gap-3 max-w-sm mx-auto w-full">

  <!-- Hint -->
  {#if hint}
    <p class="text-sm text-center font-medium
              {isMyTurn && !isComputer
                ? 'text-indigo-700 dark:text-indigo-300'
                : 'text-gray-400 dark:text-gray-500'}">
      {hint}
    </p>
  {/if}

  <!-- Board SVG -->
  <svg
    viewBox="0 0 220 220"
    class="w-full rounded-lg bg-gray-50 dark:bg-gray-900 shadow"
    style="touch-action: manipulation;"
  >
    <!-- Claimed box fills -->
    {#each {length: N} as _, br}
      {#each {length: N} as _, bc}
        {#if boxes[br]?.[bc]}
          {@const [x, y] = dot(br, bc)}
          <rect
            x={x + DOT_R} y={y + DOT_R}
            width={CELL - 2 * DOT_R} height={CELL - 2 * DOT_R}
            fill={boxFill(boxes[br][bc])}
            stroke={boxStroke(boxes[br][bc])}
            stroke-width="0.5"
          />
        {/if}
      {/each}
    {/each}

    <!-- Horizontal lines + hit areas -->
    {#each {length: GRID} as _, r}
      {#each {length: N} as _, c}
        {@const [x1, y] = dot(r, c)}
        {@const x2 = x1 + CELL}
        {@const drawn = hLines[r]?.[c]}
        {@const isHover = hover?.o === 'h' && hover.r === r && hover.c === c}

        {#if drawn !== null}
          <line {x1} y1={y} {x2} y2={y}
            stroke={lineColor(drawn)} stroke-width="4" stroke-linecap="round"
            pointer-events="none"/>
        {:else}
          <!-- Hit area -->
          {#if isMyTurn}
            <!-- Inset by HIT on each side so horizontal and vertical hit areas never overlap at dot intersections -->
            <rect x={x1 + HIT} y={y - HIT} width={CELL - 2 * HIT} height={HIT * 2}
              fill="transparent" class="cursor-pointer"
              onclick={() => drawLine('h', r, c)}
              onmouseenter={() => { hover = {o:'h', r, c}; }}
              onmouseleave={() => { hover = null; }}
            />
          {/if}
          <!-- Hover preview -->
          {#if isHover}
            <line {x1} y1={y} {x2} y2={y}
              stroke={hoverColor()} stroke-width="4" stroke-linecap="round"
              pointer-events="none"/>
          {:else}
            <!-- Faint guide dot -->
            <line {x1} y1={y} {x2} y2={y}
              stroke="#d1d5db" stroke-width="1" stroke-dasharray="3 4"
              pointer-events="none"/>
          {/if}
        {/if}
      {/each}
    {/each}

    <!-- Vertical lines + hit areas -->
    {#each {length: N} as _, r}
      {#each {length: GRID} as _, c}
        {@const [x, y1] = dot(r, c)}
        {@const y2 = y1 + CELL}
        {@const drawn = vLines[r]?.[c]}
        {@const isHover = hover?.o === 'v' && hover.r === r && hover.c === c}

        {#if drawn !== null}
          <line x1={x} {y1} x2={x} {y2}
            stroke={lineColor(drawn)} stroke-width="4" stroke-linecap="round"
            pointer-events="none"/>
        {:else}
          {#if isMyTurn}
            <!-- Inset by HIT on each side so vertical and horizontal hit areas never overlap at dot intersections -->
            <rect x={x - HIT} y={y1 + HIT} width={HIT * 2} height={CELL - 2 * HIT}
              fill="transparent" class="cursor-pointer"
              onclick={() => drawLine('v', r, c)}
              onmouseenter={() => { hover = {o:'v', r, c}; }}
              onmouseleave={() => { hover = null; }}
            />
          {/if}
          {#if isHover}
            <line x1={x} {y1} x2={x} {y2}
              stroke={hoverColor()} stroke-width="4" stroke-linecap="round"
              pointer-events="none"/>
          {:else}
            <line x1={x} {y1} x2={x} {y2}
              stroke="#d1d5db" stroke-width="1" stroke-dasharray="3 4"
              pointer-events="none"/>
          {/if}
        {/if}
      {/each}
    {/each}

    <!-- Dots (rendered last so they sit on top of lines) -->
    {#each {length: GRID} as _, r}
      {#each {length: GRID} as _, c}
        {@const [cx, cy] = dot(r, c)}
        <circle {cx} {cy} r={DOT_R}
          fill="#374151" class="dark:fill-gray-300"
          pointer-events="none"/>
      {/each}
    {/each}
  </svg>

  <!-- Score row -->
  <div class="flex justify-between text-sm px-1">
    {#each players as p, idx}
      <div class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-sm"
          style="background:{P_LINE[idx]};"></span>
        <span class="{p === myUsername ? 'font-semibold' : 'text-gray-500 dark:text-gray-400'}">
          {p}{p === myUsername ? ' (you)' : ''}
        </span>
        <span class="font-bold tabular-nums" style="color:{P_LINE[idx]}">
          {$_('games.dots_and_boxes.score', { values: { n: scores[p] ?? 0 } })}
        </span>
      </div>
    {/each}
  </div>

</div>
