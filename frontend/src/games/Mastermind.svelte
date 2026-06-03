<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const COLOR_BG = {
    red:    'bg-red-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-400',
    green:  'bg-green-500',
    blue:   'bg-blue-500',
    purple: 'bg-purple-500',
  };

  const COLOR_LABEL = {
    red:    'Red',
    orange: 'Orange',
    yellow: 'Yellow',
    green:  'Green',
    blue:   'Blue',
    purple: 'Purple',
  };

  const state = $derived(session.state ?? {});
  const phase = $derived(state.phase ?? 'setting');
  const amCodeMaker = $derived(state.code_maker === myUsername);
  const amCodeBreaker = $derived(state.code_breaker === myUsername);
  const isMyTurn = $derived(state.current_turn === myUsername && session.status === 'playing');
  const colors = $derived(state.colors ?? ['red', 'orange', 'yellow', 'green', 'blue', 'purple']);
  const codeLength = $derived(state.code_length ?? 4);
  const guessesRemaining = $derived(state.guesses_remaining ?? 10);

  // Current draft (setting or guessing)
  let draft = $state([]);

  // Reset draft when phase or turn changes
  $effect(() => {
    phase; // track
    isMyTurn;
    draft = Array(codeLength).fill(null);
  });

  function cycleColor(index) {
    const current = draft[index];
    const idx = current === null ? 0 : (colors.indexOf(current) + 1) % colors.length;
    draft = draft.map((c, i) => i === index ? colors[idx] : c);
  }

  function clearSlot(index) {
    draft = draft.map((c, i) => i === index ? null : c);
  }

  const draftComplete = $derived(draft.length === codeLength && draft.every(c => c !== null));

  function submitCode() {
    if (!draftComplete) return;
    onAction({ type: 'set_code', colors: draft });
  }

  function submitGuess() {
    if (!draftComplete) return;
    onAction({ type: 'guess', colors: draft });
  }

  function pegClass(g) {
    if (g === 'black') return 'bg-gray-900 dark:bg-gray-100';
    if (g === 'white') return 'bg-white border border-gray-400 dark:border-gray-500';
    return 'bg-gray-300 dark:bg-gray-600';
  }

  function buildPegs(blacks, whites) {
    const pegs = [];
    for (let i = 0; i < blacks; i++) pegs.push('black');
    for (let i = 0; i < whites; i++) pegs.push('white');
    while (pegs.length < codeLength) pegs.push('empty');
    return pegs;
  }
</script>

<div class="select-none flex flex-col gap-5 max-w-sm">

  <!-- Role badge -->
  <p class="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400">
    {amCodeMaker ? $_('games.mastermind.you_are_code_maker') : $_('games.mastermind.you_are_code_breaker')}
  </p>

  <!-- ── SETTING PHASE ── -->
  {#if phase === 'setting'}
    {#if amCodeMaker}
      <div class="flex flex-col gap-4">
        <div>
          <h2 class="font-semibold">{$_('games.mastermind.set_your_code')}</h2>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{$_('games.mastermind.set_code_hint')}</p>
        </div>

        <!-- Draft slots -->
        <div class="flex gap-2">
          {#each draft as color, i}
            <button
              class="w-10 h-10 rounded-full border-2 transition-colors
                     {color ? COLOR_BG[color] + ' border-transparent' : 'bg-gray-200 dark:bg-gray-700 border-gray-400 dark:border-gray-500'}
                     hover:scale-110 active:scale-95"
              aria-label="Slot {i + 1}: {color ?? 'empty'}"
              onclick={() => color ? clearSlot(i) : cycleColor(i)}
            ></button>
          {/each}
        </div>

        <!-- Color palette -->
        <div class="flex flex-wrap gap-2">
          {#each colors as c}
            <button
              class="w-8 h-8 rounded-full {COLOR_BG[c]} hover:scale-110 active:scale-95 transition-transform shadow"
              aria-label={COLOR_LABEL[c]}
              onclick={() => {
                const empty = draft.findIndex(x => x === null);
                if (empty !== -1) draft = draft.map((x, i) => i === empty ? c : x);
              }}
            ></button>
          {/each}
        </div>

        <button
          class="px-4 py-2 rounded bg-indigo-600 text-white text-sm font-medium disabled:opacity-40 w-fit"
          disabled={!draftComplete}
          onclick={submitCode}
        >{$_('games.mastermind.set_code_btn')}</button>
      </div>

    {:else}
      <p class="text-sm text-gray-500 dark:text-gray-400">
        {$_('games.mastermind.waiting_for_code', { values: { maker: state.code_maker } })}
      </p>
    {/if}

  <!-- ── GUESSING PHASE ── -->
  {:else if phase === 'guessing'}
    <!-- Secret code (visible to code maker only) -->
    {#if amCodeMaker && state.secret_code}
      <div class="flex items-center gap-3">
        <span class="text-xs text-gray-500 dark:text-gray-400">{$_('games.mastermind.your_code_is')}</span>
        <div class="flex gap-1.5">
          {#each state.secret_code as c}
            <div class="w-7 h-7 rounded-full {COLOR_BG[c]} shadow"></div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Guess history -->
    {#if state.guesses?.length > 0}
      <div class="flex flex-col gap-1.5">
        {#each state.guesses as g, idx}
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400 w-5 text-right">{idx + 1}.</span>
            <!-- Colors -->
            <div class="flex gap-1.5">
              {#each g.colors as c}
                <div class="w-7 h-7 rounded-full {COLOR_BG[c]} shadow-sm"></div>
              {/each}
            </div>
            <!-- Pegs -->
            <div class="grid grid-cols-2 gap-[3px]">
              {#each buildPegs(g.blacks, g.whites) as peg}
                <div class="w-3 h-3 rounded-full {pegClass(peg)}"></div>
              {/each}
            </div>
            <!-- Score text -->
            <span class="text-xs text-gray-400">
              {g.blacks}B {g.whites}W
            </span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Active input (code breaker's turn) -->
    {#if amCodeBreaker && isMyTurn}
      <div class="flex flex-col gap-3 pt-1 border-t border-gray-200 dark:border-gray-700">
        <p class="text-sm font-medium text-indigo-700 dark:text-indigo-400">{$_('games.mastermind.guess_prompt')}</p>

        <!-- Draft slots -->
        <div class="flex gap-2">
          {#each draft as color, i}
            <button
              class="w-10 h-10 rounded-full border-2 transition-all
                     {color ? COLOR_BG[color] + ' border-transparent' : 'bg-gray-200 dark:bg-gray-700 border-gray-400 dark:border-gray-500'}
                     hover:scale-110 active:scale-95"
              aria-label="Slot {i + 1}: {color ?? 'empty'}"
              onclick={() => color ? clearSlot(i) : cycleColor(i)}
            ></button>
          {/each}
        </div>

        <!-- Color palette -->
        <div class="flex flex-wrap gap-2">
          {#each colors as c}
            <button
              class="w-8 h-8 rounded-full {COLOR_BG[c]} hover:scale-110 active:scale-95 transition-transform shadow"
              aria-label={COLOR_LABEL[c]}
              onclick={() => {
                const empty = draft.findIndex(x => x === null);
                if (empty !== -1) draft = draft.map((x, i) => i === empty ? c : x);
              }}
            ></button>
          {/each}
        </div>

        <div class="flex items-center gap-4">
          <button
            class="px-4 py-2 rounded bg-indigo-600 text-white text-sm font-medium disabled:opacity-40"
            disabled={!draftComplete}
            onclick={submitGuess}
          >{$_('games.mastermind.guess_btn')}</button>
          <span class="text-xs text-gray-400">
            {guessesRemaining === 1
              ? $_('games.mastermind.guesses_remaining', { values: { n: guessesRemaining } })
              : $_('games.mastermind.guesses_remaining_plural', { values: { n: guessesRemaining } })}
          </span>
        </div>
      </div>

    {:else if amCodeBreaker}
      <!-- Waiting (shouldn't normally appear, but just in case) -->
      <p class="text-sm text-gray-500 dark:text-gray-400 pt-1 border-t border-gray-200 dark:border-gray-700">
        {$_('games.mastermind.guess_prompt')}
      </p>

    {:else}
      <!-- Code maker waiting -->
      <p class="text-sm text-gray-500 dark:text-gray-400 pt-1 border-t border-gray-200 dark:border-gray-700">
        {$_('games.mastermind.waiting_for_guess', { values: { breaker: state.code_breaker } })}
      </p>
      <span class="text-xs text-gray-400">
        {guessesRemaining === 1
          ? $_('games.mastermind.guesses_remaining', { values: { n: guessesRemaining } })
          : $_('games.mastermind.guesses_remaining_plural', { values: { n: guessesRemaining } })}
      </span>
    {/if}

  <!-- ── FINISHED ── -->
  {:else if phase === 'finished' || session.status === 'finished'}
    {@const breackerWon = state.guesses?.at(-1)?.blacks === codeLength}

    <p class="font-semibold text-lg">
      {breackerWon
        ? $_('games.mastermind.code_cracked', { values: { breaker: state.code_breaker } })
        : $_('games.mastermind.code_safe',    { values: { maker:   state.code_maker   } })}
    </p>

    <!-- Final guess history -->
    {#if state.guesses?.length > 0}
      <div class="flex flex-col gap-1.5">
        {#each state.guesses as g, idx}
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400 w-5 text-right">{idx + 1}.</span>
            <div class="flex gap-1.5">
              {#each g.colors as c}
                <div class="w-7 h-7 rounded-full {COLOR_BG[c]} shadow-sm"></div>
              {/each}
            </div>
            <div class="grid grid-cols-2 gap-[3px]">
              {#each buildPegs(g.blacks, g.whites) as peg}
                <div class="w-3 h-3 rounded-full {pegClass(peg)}"></div>
              {/each}
            </div>
            <span class="text-xs text-gray-400">{g.blacks}B {g.whites}W</span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Reveal the code -->
    {#if state.secret_code}
      <div class="flex items-center gap-3">
        <span class="text-xs text-gray-500 dark:text-gray-400">{$_('games.mastermind.the_code_was')}</span>
        <div class="flex gap-1.5">
          {#each state.secret_code as c}
            <div class="w-7 h-7 rounded-full {COLOR_BG[c]} shadow"></div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>
