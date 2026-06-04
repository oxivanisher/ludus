<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  // Board coordinate for each of the 24 positions (viewBox 0 0 420 420, center 210,210).
  // Three nested squares: outer 30–390, middle 90–330, inner 150–270.
  const POSITIONS = [
    [30, 30],   // 0  outer TL
    [210, 30],  // 1  outer T
    [390, 30],  // 2  outer TR
    [90, 90],   // 3  middle TL
    [210, 90],  // 4  middle T
    [330, 90],  // 5  middle TR
    [150, 150], // 6  inner TL
    [210, 150], // 7  inner T
    [270, 150], // 8  inner TR
    [30, 210],  // 9  outer L
    [90, 210],  // 10 middle L
    [150, 210], // 11 inner L
    [270, 210], // 12 inner R
    [330, 210], // 13 middle R
    [390, 210], // 14 outer R
    [150, 270], // 15 inner BL
    [210, 270], // 16 inner B
    [270, 270], // 17 inner BR
    [90, 330],  // 18 middle BL
    [210, 330], // 19 middle B
    [330, 330], // 20 middle BR
    [30, 390],  // 21 outer BL
    [210, 390], // 22 outer B
    [390, 390], // 23 outer BR
  ];

  const ADJACENCY = [
    [1, 9],           // 0
    [0, 2, 4],        // 1
    [1, 14],          // 2
    [4, 10],          // 3
    [1, 3, 5, 7],     // 4
    [4, 13],          // 5
    [7, 11],          // 6
    [4, 6, 8],        // 7
    [7, 12],          // 8
    [0, 10, 21],      // 9
    [3, 9, 11, 18],   // 10
    [6, 10, 15],      // 11
    [8, 13, 17],      // 12
    [5, 12, 14, 20],  // 13
    [2, 13, 23],      // 14
    [11, 16],         // 15
    [15, 17, 19],     // 16
    [12, 16],         // 17
    [10, 19],         // 18
    [16, 18, 20, 22], // 19
    [13, 19],         // 20
    [9, 22],          // 21
    [19, 21, 23],     // 22
    [14, 22],         // 23
  ];

  const MILLS_LIST = [
    [0, 1, 2], [2, 14, 23], [21, 22, 23], [0, 9, 21],
    [3, 4, 5], [5, 13, 20], [18, 19, 20], [3, 10, 18],
    [6, 7, 8], [8, 12, 17], [15, 16, 17], [6, 11, 15],
    [1, 4, 7], [9, 10, 11], [12, 13, 14], [16, 19, 22],
  ];

  const state     = $derived(session.state ?? {});
  const board     = $derived(state.board ?? Array(24).fill(null));
  const phase     = $derived(state.phase ?? 'placing');
  const curTurn   = $derived(state.current_turn);
  const players   = $derived(state.players ?? []);
  const toPlace   = $derived(state.to_place ?? {});
  const counts    = $derived(state.counts ?? {});
  const isMyTurn  = $derived(curTurn === myUsername && session.status === 'playing');
  const opponent  = $derived(players.find(p => p !== myUsername) ?? '');
  const isFlying  = $derived(phase === 'moving' && counts[myUsername] === 3);
  const oppFlying = $derived(phase === 'moving' && counts[opponent] === 3);

  // Player 0 = amber, player 1 = indigo
  const myColorIdx = $derived(players.indexOf(myUsername));

  let selected = $state(null);
  $effect(() => { phase; curTurn; selected = null; });

  function inMillOf(b, pos, player) {
    return MILLS_LIST.some(m => m.includes(pos) && m.every(p => b[p] === player));
  }

  function allInMills(b, player) {
    return Array.from({ length: 24 }, (_, i) => i)
      .filter(i => b[i] === player)
      .every(i => inMillOf(b, i, player));
  }

  // Positions that are part of any completed mill right now
  const milledPositions = $derived((() => {
    const s = new Set();
    MILLS_LIST.forEach(mill => {
      const owner = board[mill[0]];
      if (owner && mill.every(p => board[p] === owner)) {
        mill.forEach(p => s.add(p));
      }
    });
    return s;
  })());

  // Empty positions reachable from `selected` (or all empty if flying)
  const validTargets = $derived((() => {
    const s = new Set();
    if (!isMyTurn) return s;
    if (phase === 'placing') {
      board.forEach((v, i) => { if (v === null) s.add(i); });
    } else if (phase === 'moving' && selected !== null) {
      if (isFlying) {
        board.forEach((v, i) => { if (v === null) s.add(i); });
      } else {
        ADJACENCY[selected].forEach(i => { if (board[i] === null) s.add(i); });
      }
    } else if (phase === 'removing') {
      const oppAll = allInMills(board, opponent);
      board.forEach((v, i) => {
        if (v !== opponent) return;
        if (inMillOf(board, i, opponent) && !oppAll) return;
        s.add(i);
      });
    }
    return s;
  })());

  // My pieces that have at least one legal move (for highlighting in moving phase)
  const movablePieces = $derived((() => {
    const s = new Set();
    if (!isMyTurn || phase !== 'moving' || selected !== null) return s;
    board.forEach((v, i) => {
      if (v !== myUsername) return;
      if (isFlying || ADJACENCY[i].some(adj => board[adj] === null)) s.add(i);
    });
    return s;
  })());

  function handleClick(pos) {
    if (!isMyTurn) return;
    if (phase === 'placing') {
      if (board[pos] === null) onAction({ type: 'place', pos });
    } else if (phase === 'moving') {
      if (selected === null) {
        if (board[pos] === myUsername) selected = pos;
      } else if (pos === selected) {
        selected = null;
      } else if (board[pos] === myUsername) {
        selected = pos;
      } else if (validTargets.has(pos)) {
        onAction({ type: 'move', from: selected, to: pos });
      }
    } else if (phase === 'removing') {
      if (validTargets.has(pos)) onAction({ type: 'remove', pos });
    }
  }

  // Determine visual role of each position for SVG rendering
  function posRole(pos) {
    const v = board[pos];
    if (phase === 'removing' && isMyTurn && validTargets.has(pos)) return 'removable';
    if (pos === selected) return 'selected';
    if (phase === 'moving' && isMyTurn && v === myUsername && movablePieces.has(pos)) return 'movable';
    if (validTargets.has(pos) && v === null) return 'target';
    return 'normal';
  }

  // Circle fill color by owner
  function pieceFill(pos) {
    const v = board[pos];
    if (!v) return null;
    return players.indexOf(v) === 0 ? 'amber' : 'indigo';
  }

  // Status / hint message
  const hint = $derived((() => {
    if (session.status === 'finished') return null;
    const n = toPlace[myUsername] ?? 0;
    const on = toPlace[opponent] ?? 0;
    if (phase === 'placing') {
      return isMyTurn
        ? $_('games.mill.hint_place_my', { values: { n } })
        : $_('games.mill.hint_place_opp', { values: { player: curTurn, n: on } });
    }
    if (phase === 'moving') {
      if (!isMyTurn) return $_('games.mill.hint_select').replace('Your turn — ', '') + ` — waiting for ${curTurn}…`;
      return selected === null
        ? $_('games.mill.hint_select')
        : $_('games.mill.hint_move');
    }
    if (phase === 'removing') {
      return isMyTurn
        ? $_('games.mill.hint_remove_my', { values: { opponent } })
        : $_('games.mill.hint_remove_opp', { values: { player: curTurn } });
    }
    return null;
  })());
</script>

<div class="select-none flex flex-col gap-4 max-w-lg mx-auto w-full">

  <!-- Status / hint banner -->
  {#if hint}
    <p class="text-sm text-center font-medium px-3 py-2 rounded-lg
              {isMyTurn
                ? 'bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300'
                : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400'}">
      {hint}
      {#if isFlying && isMyTurn}
        <span class="ml-1 text-xs font-semibold text-amber-600 dark:text-amber-400">
          · {$_('games.mill.flying')}
        </span>
      {/if}
    </p>
  {/if}

  <!-- Board SVG -->
  <svg
    viewBox="0 0 420 420"
    class="w-full max-w-md mx-auto"
    style="touch-action: manipulation;"
  >
    <!-- Board lines -->
    <g class="stroke-gray-500 dark:stroke-gray-400" stroke-width="2" fill="none">
      <!-- Three nested squares -->
      <rect x="30"  y="30"  width="360" height="360" rx="2"/>
      <rect x="90"  y="90"  width="240" height="240" rx="2"/>
      <rect x="150" y="150" width="120" height="120" rx="2"/>
      <!-- Connecting lines: outer midpoint → inner midpoint at each side -->
      <line x1="210" y1="30"  x2="210" y2="150"/>
      <line x1="210" y1="270" x2="210" y2="390"/>
      <line x1="30"  y1="210" x2="150" y2="210"/>
      <line x1="270" y1="210" x2="390" y2="210"/>
    </g>

    <!-- Positions -->
    {#each POSITIONS as [cx, cy], i}
      {@const fill = pieceFill(i)}
      {@const role = posRole(i)}
      {@const occupied = board[i] !== null}
      {@const milled = milledPositions.has(i)}

      <!-- Large invisible hit area for easy tapping -->
      <circle
        cx={cx} cy={cy} r="20"
        fill="transparent"
        class={(isMyTurn && (phase === 'placing' && !occupied) ||
                (phase === 'moving' && (board[i] === myUsername || (selected !== null && validTargets.has(i)))) ||
                (phase === 'removing' && validTargets.has(i))) ? 'cursor-pointer' : ''}
        onclick={() => handleClick(i)}
      />

      {#if occupied}
        <!-- Piece -->
        <circle
          cx={cx} cy={cy}
          r={role === 'selected' ? 17 : 14}
          fill={fill === 'amber' ? '#F59E0B' : '#6366F1'}
          stroke={role === 'selected'   ? '#FACC15' :
                  role === 'removable'  ? '#EF4444' :
                  role === 'movable'    ? '#34D399' :
                  milled                ? '#FCD34D' : 'white'}
          stroke-width={role === 'selected' || role === 'removable' ? 4 :
                        role === 'movable' || milled                ? 2 : 1}
          class={(role === 'removable' || role === 'movable') ? 'cursor-pointer' : ''}
          onclick={() => handleClick(i)}
        />
        <!-- Inner highlight dot for milled pieces -->
        {#if milled}
          <circle cx={cx} cy={cy} r="5" fill="rgba(255,255,255,0.35)" pointer-events="none"/>
        {/if}
      {:else}
        <!-- Empty intersection dot -->
        <circle
          cx={cx} cy={cy}
          r={role === 'target' ? 9 : 4}
          fill={role === 'target' ? '#34D399' : '#9CA3AF'}
          opacity={role === 'target' ? 0.85 : 0.6}
          class={role === 'target' ? 'cursor-pointer' : ''}
          onclick={() => handleClick(i)}
        />
      {/if}
    {/each}
  </svg>

  <!-- Piece counters -->
  <div class="flex justify-between text-xs px-1">
    {#each players as p, idx}
      {@const color = idx === 0 ? 'amber' : 'indigo'}
      {@const isMe = p === myUsername}
      {@const flying = phase === 'moving' && counts[p] === 3}
      <div class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-full
          {color === 'amber' ? 'bg-amber-400' : 'bg-indigo-500'}"></span>
        <span class="font-medium {isMe ? '' : 'text-gray-500 dark:text-gray-400'}">
          {p}{isMe ? ' (you)' : ''}
        </span>
        <span class="text-gray-400">
          {counts[p] ?? 0} on board
          {#if (toPlace[p] ?? 0) > 0}
            · {$_('games.mill.to_place', { values: { n: toPlace[p] } })}
          {/if}
          {#if flying}
            · {$_('games.mill.flying')}
          {/if}
        </span>
      </div>
    {/each}
  </div>

</div>
