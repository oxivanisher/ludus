<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const marks = $derived(session.state.marks ?? {});
  const board = $derived(session.state.board ?? Array(9).fill(null));
  const isMyTurn = $derived(session.current_turn === myUsername && session.status === "playing");

  function cellLabel(cell) {
    if (!cell) return "";
    return marks[cell] ?? "?";
  }

  function handleClick(index) {
    if (!isMyTurn || board[index] !== null) return;
    onAction({ cell: index });
  }
</script>

<div class="flex flex-col items-center gap-4">
  <div class="grid grid-cols-3 gap-2 w-full max-w-[240px]">
    {#each board as cell, i}
      <button
        class="aspect-square text-3xl font-bold rounded-lg border-2 transition-colors
               {cell
                 ? 'cursor-default border-gray-200 bg-gray-50 dark:border-gray-600 dark:bg-gray-700'
                 : isMyTurn
                   ? 'cursor-pointer border-gray-200 bg-white hover:bg-indigo-50 hover:border-indigo-400 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-indigo-900/30 dark:hover:border-indigo-500'
                   : 'cursor-default border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'}"
        disabled={!!cell || !isMyTurn}
        onclick={() => handleClick(i)}
      >
        <span class="{cellLabel(cell) === 'X' ? 'text-indigo-600 dark:text-indigo-400' : 'text-rose-500 dark:text-rose-400'}">
          {cellLabel(cell)}
        </span>
      </button>
    {/each}
  </div>

  <div class="text-xs text-gray-400 dark:text-gray-500 text-center">
    {#each Object.entries(marks) as [name, mark]}
      <span class="mr-3">{$_('games.tictactoe.legend_label', { values: { name, mark } })}</span>
    {/each}
  </div>
</div>
