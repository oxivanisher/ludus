<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const STORE_0 = 6;
  const STORE_1 = 13;
  const P0_PITS = [0, 1, 2, 3, 4, 5];
  const P1_PITS = [12, 11, 10, 9, 8, 7]; // reversed for display (left→right from P0 view)

  const state      = $derived(session.state ?? {});
  const pits       = $derived(state.pits ?? Array(14).fill(0));
  const curTurn    = $derived(state.current_turn);
  const players    = $derived(state.players ?? []);
  const extraTurn  = $derived(state.extra_turn ?? false);
  const lastMove   = $derived(state.last_move ?? null);
  const isMyTurn   = $derived(curTurn === myUsername && session.status === 'playing');
  const myIdx      = $derived(players.indexOf(myUsername));
  const myPits     = $derived(myIdx === 0 ? P0_PITS : P1_PITS);
  const myStore    = $derived(myIdx === 0 ? STORE_0 : STORE_1);
  const opponent   = $derived(players.find(p => p !== myUsername) ?? '');
  const isComputer = $derived(curTurn === 'Computer' && session.status === 'playing');

  function canPick(pitIdx) {
    if (!isMyTurn) return false;
    const ownPits = myIdx === 0 ? P0_PITS : [7, 8, 9, 10, 11, 12];
    return ownPits.includes(pitIdx) && pits[pitIdx] > 0;
  }

  function pick(pitIdx) {
    if (!canPick(pitIdx)) return;
    onAction({ type: 'pick', pit: pitIdx });
  }

  const hint = $derived((() => {
    if (session.status !== 'playing') return null;
    if (isComputer) return $_('games.mancala.hint_computer');
    if (!isMyTurn)  return $_('games.mancala.hint_wait', { values: { player: curTurn } });
    if (extraTurn)  return $_('games.mancala.hint_extra');
    return $_('games.mancala.hint_pick');
  })());

  // Row 0 = top (P1's pits shown left→right: indices 12,11,10,9,8,7)
  // Row 1 = bottom (P0's pits shown left→right: indices 0,1,2,3,4,5)
  const topPits    = P1_PITS;   // [12,11,10,9,8,7]
  const bottomPits = P0_PITS;   // [0,1,2,3,4,5]

  const p0name = $derived(players[0] ?? '');
  const p1name = $derived(players[1] ?? '');
</script>

<div class="select-none flex flex-col gap-3 max-w-sm mx-auto w-full">

  <!-- Hint / status banner -->
  {#if hint}
    <p class="text-sm text-center font-medium transition-colors
              {isMyTurn && !isComputer
                ? 'text-indigo-700 dark:text-indigo-300'
                : 'text-gray-400 dark:text-gray-500'}">
      {hint}
    </p>
  {/if}

  <!-- Board -->
  <div class="flex items-stretch gap-2 p-3 rounded-xl
              bg-amber-100 dark:bg-amber-950 shadow-inner">

    <!-- Player 1 store (left side) -->
    <div class="w-12 shrink-0 rounded-xl flex flex-col items-center justify-center gap-1
                bg-amber-200 dark:bg-amber-800 py-3 px-1
                {curTurn === p1name && session.status === 'playing'
                  ? 'ring-2 ring-amber-500 dark:ring-amber-400' : ''}">
      <span class="text-2xl font-bold tabular-nums leading-none">{pits[STORE_1]}</span>
      <span class="text-[10px] font-medium text-amber-700 dark:text-amber-300 text-center leading-tight">
        {$_('games.mancala.store')}
      </span>
      <span class="text-[9px] text-amber-600 dark:text-amber-400 text-center leading-tight truncate w-full px-0.5">
        {p1name}
      </span>
    </div>

    <!-- Pit grid: 6 × 2 -->
    <div class="flex-1 flex flex-col gap-2">

      <!-- Top row: P1's pits (display order 12→7) -->
      <div class="grid grid-cols-6 gap-1">
        {#each topPits as i}
          {@const active = curTurn === p1name && isMyTurn && canPick(i)}
          {@const isLast = lastMove === i}
          <button
            class="aspect-square rounded-full flex items-center justify-center
                   text-sm font-bold tabular-nums transition-all
                   bg-amber-200 dark:bg-amber-800
                   {pits[i] === 0 ? 'opacity-35' : ''}
                   {active ? 'ring-2 ring-amber-500 cursor-pointer hover:bg-amber-300 dark:hover:bg-amber-700 active:scale-95' : 'cursor-default'}
                   {isLast ? 'ring-2 ring-yellow-400' : ''}"
            onclick={() => pick(i)}
            disabled={!active}
          >
            {pits[i]}
          </button>
        {/each}
      </div>

      <!-- Bottom row: P0's pits (display order 0→5) -->
      <div class="grid grid-cols-6 gap-1">
        {#each bottomPits as i}
          {@const active = canPick(i)}
          {@const isLast = lastMove === i}
          <button
            class="aspect-square rounded-full flex items-center justify-center
                   text-sm font-bold tabular-nums transition-all
                   bg-amber-200 dark:bg-amber-800
                   {pits[i] === 0 ? 'opacity-35' : ''}
                   {active ? 'ring-2 ring-indigo-500 cursor-pointer hover:bg-amber-300 dark:hover:bg-amber-700 active:scale-95' : 'cursor-default'}
                   {isLast ? 'ring-2 ring-yellow-400' : ''}"
            onclick={() => pick(i)}
            disabled={!active}
          >
            {pits[i]}
          </button>
        {/each}
      </div>

    </div>

    <!-- Player 0 store (right side) -->
    <div class="w-12 shrink-0 rounded-xl flex flex-col items-center justify-center gap-1
                bg-amber-200 dark:bg-amber-800 py-3 px-1
                {curTurn === p0name && session.status === 'playing'
                  ? 'ring-2 ring-indigo-500 dark:ring-indigo-400' : ''}">
      <span class="text-2xl font-bold tabular-nums leading-none">{pits[STORE_0]}</span>
      <span class="text-[10px] font-medium text-amber-700 dark:text-amber-300 text-center leading-tight">
        {$_('games.mancala.store')}
      </span>
      <span class="text-[9px] text-amber-600 dark:text-amber-400 text-center leading-tight truncate w-full px-0.5">
        {p0name}
      </span>
    </div>

  </div>

  <!-- Player labels below the board -->
  <div class="flex justify-between text-xs px-1 text-gray-500 dark:text-gray-400">
    <span>↑ {p1name}{p1name === myUsername ? ' (you)' : ''}</span>
    <span>↓ {p0name}{p0name === myUsername ? ' (you)' : ''}</span>
  </div>

</div>
