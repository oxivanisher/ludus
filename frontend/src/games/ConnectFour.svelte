<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const COLS = 7;
  const ROWS = 6;

  const marks = $derived(session.state.marks ?? {});
  const board = $derived(
    session.state.board ?? Array.from({ length: ROWS }, () => Array(COLS).fill(null))
  );
  const isMyTurn = $derived(session.current_turn === myUsername && session.status === "playing");

  let hoveredCol = $state(null);

  function colFull(col) {
    return board[0][col] !== null;
  }

  function handleColClick(col) {
    if (!isMyTurn || colFull(col)) return;
    onAction({ col });
  }

  function cellClass(cell, col) {
    if (cell !== null) {
      return marks[cell] === "R"
        ? "bg-red-500 shadow-inner"
        : "bg-yellow-400 shadow-inner";
    }
    if (isMyTurn && hoveredCol === col && !colFull(col)) {
      return "bg-white/40 dark:bg-white/20";
    }
    return "bg-indigo-900/40 dark:bg-black/30";
  }
</script>

<div class="flex flex-col items-center gap-3 select-none">
  <!-- Drop-arrow row -->
  <div class="grid grid-cols-7 gap-1 w-full max-w-sm px-[0.35rem]">
    {#each Array.from({ length: COLS }, (_, i) => i) as col}
      <div class="flex items-center justify-center h-5 text-indigo-500 dark:text-indigo-400 text-sm font-bold">
        {#if isMyTurn && hoveredCol === col && !colFull(col)}▼{/if}
      </div>
    {/each}
  </div>

  <!-- Board frame -->
  <div
    class="bg-indigo-600 dark:bg-indigo-800 p-2 rounded-xl shadow-lg w-full max-w-sm"
    onmouseleave={() => { hoveredCol = null; }}
  >
    <div class="grid grid-cols-7 gap-1">
      {#each board as row, r}
        {#each row as cell, c}
          <button
            class="aspect-square w-full rounded-full transition-colors duration-100 {cellClass(cell, c)}"
            onclick={() => handleColClick(c)}
            onmouseenter={() => { hoveredCol = c; }}
            disabled={!isMyTurn || colFull(c)}
            aria-label="Column {c + 1}"
          ></button>
        {/each}
      {/each}
    </div>
  </div>

  <!-- Legend -->
  <div class="flex gap-6 text-sm text-gray-600 dark:text-gray-400">
    {#each Object.entries(marks) as [name, mark]}
      <span class="flex items-center gap-1.5">
        <span
          class="inline-block w-4 h-4 rounded-full shadow-sm {mark === 'R' ? 'bg-red-500' : 'bg-yellow-400'}"
        ></span>
        {name}{name === myUsername ? ' ' + $_('games.connect_four.you_label') : ""}
      </span>
    {/each}
  </div>
</div>
