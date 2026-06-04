<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const state        = $derived(session.state ?? {});
  const cards        = $derived(state.cards ?? []);
  const faceUp       = $derived(state.face_up ?? []);
  const matched      = $derived(state.matched ?? []);
  const firstPick    = $derived(state.first_pick ?? null);
  const scores       = $derived(state.scores ?? {});
  const players      = $derived(state.players ?? []);
  const curTurn      = $derived(state.current_turn);
  const gridCols     = $derived(state.grid_cols ?? 4);
  const numCards     = $derived(state.num_cards ?? 16);
  const numPairs     = $derived(numCards / 2);
  const isMyTurn     = $derived(curTurn === myUsername && session.status === 'playing');
  const opponent     = $derived(players.find(p => p !== myUsername) ?? '');
  const pairsLeft    = $derived(numPairs - players.reduce((s, p) => s + (scores[p] ?? 0), 0));

  // Briefly reveal mismatched cards after they flip back down
  let showingMismatch = $state(null); // [i, j] | null

  $effect(() => {
    const lm = state.last_mismatch;
    const id = state.mismatch_id ?? 0;
    if (!lm) { showingMismatch = null; return; }
    showingMismatch = lm;
    const t = setTimeout(() => { showingMismatch = null; }, 1300);
    return () => clearTimeout(t);
  });

  const mismatchValues = $derived(state.last_mismatch_values ?? null);

  // A card is visually face-up if matched, currently face_up, or in the mismatch reveal window
  function isVisible(i) {
    return matched[i] || faceUp[i] || (showingMismatch !== null && showingMismatch.includes(i));
  }

  // Returns the emoji to display, including during the mismatch reveal window
  function cardValue(i) {
    if (matched[i] || faceUp[i]) return cards[i];
    if (showingMismatch !== null && mismatchValues !== null) {
      const idx = showingMismatch.indexOf(i);
      if (idx !== -1) return mismatchValues[idx];
    }
    return null;
  }

  // Clicks are allowed when it's my turn, the card is hidden, and we're not mid-mismatch animation
  function canClick(i) {
    if (!isMyTurn || showingMismatch !== null) return false;
    if (matched[i] || faceUp[i]) return false;
    if (firstPick !== null && firstPick === i) return false; // can't re-flip same card
    return true;
  }

  function handleClick(i) {
    if (!canClick(i)) return;
    onAction({ type: 'flip', pos: i });
  }

  const hint = $derived((() => {
    if (session.status !== 'playing') return null;
    if (isMyTurn) {
      return firstPick === null
        ? $_('games.memory.hint_first')
        : $_('games.memory.hint_second');
    }
    return firstPick !== null
      ? $_('games.memory.hint_wait_second', { values: { player: curTurn } })
      : $_('games.memory.hint_wait_first',  { values: { player: curTurn } });
  })());
</script>

<div class="select-none flex flex-col gap-4 max-w-sm mx-auto w-full">

  <!-- Hint / status -->
  {#if hint}
    <p class="text-sm text-center font-medium
              {isMyTurn
                ? 'text-indigo-700 dark:text-indigo-300'
                : 'text-gray-400 dark:text-gray-500'}">
      {hint}
    </p>
  {/if}

  <!-- Card grid -->
  <div
    class="grid gap-2"
    style="grid-template-columns: repeat({gridCols}, minmax(0, 1fr));"
  >
    {#each { length: numCards } as _, i}
      {@const visible = isVisible(i)}
      {@const isMatch = matched[i]}
      {@const isFirst = firstPick === i}
      {@const clickable = canClick(i)}
      {@const mismatchFlash = showingMismatch !== null && showingMismatch.includes(i) && !faceUp[i]}

      <button
        class="aspect-square rounded-xl text-3xl flex items-center justify-center
               shadow transition-all duration-150
               {visible
                 ? 'bg-white dark:bg-gray-100 text-gray-900'
                 : 'bg-indigo-600 dark:bg-indigo-700'}
               {isMatch
                 ? 'opacity-50 ring-2 ring-green-400 dark:ring-green-500'
                 : ''}
               {isFirst
                 ? 'ring-2 ring-yellow-400'
                 : ''}
               {mismatchFlash
                 ? 'ring-2 ring-red-400'
                 : ''}
               {clickable
                 ? 'cursor-pointer hover:scale-105 active:scale-95'
                 : 'cursor-default'}"
        onclick={() => handleClick(i)}
        aria-label={visible ? cards[i] : 'hidden card'}
      >
        {#if visible}
          {cardValue(i)}
        {:else}
          <span class="text-indigo-300 dark:text-indigo-400 font-bold text-xl">✦</span>
        {/if}
      </button>
    {/each}
  </div>

  <!-- Scores + pairs remaining -->
  <div class="flex justify-between items-center text-sm px-1">
    <div class="flex gap-4">
      {#each players as p}
        <span class="{p === myUsername ? 'font-semibold' : 'text-gray-500 dark:text-gray-400'}">
          {p}{p === myUsername ? ' (you)' : ''}:
          <span class="tabular-nums font-bold">
            {$_('games.memory.pair', { values: { n: scores[p] ?? 0 } })}
          </span>
        </span>
      {/each}
    </div>
    <span class="text-gray-400 text-xs tabular-nums">
      {$_('games.memory.pairs_remaining', { values: { n: pairsLeft } })}
    </span>
  </div>

</div>
