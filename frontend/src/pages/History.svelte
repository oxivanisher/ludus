<script>
  import { onMount } from "svelte";
  import { _ } from "svelte-i18n";
  import { api } from "../lib/api.js";

  let { onBack, onJoinGame } = $props();

  let sessions = $state([]);
  let loading = $state(true);
  let error = $state(null);

  onMount(async () => {
    try {
      const all = await api.mySessions();
      sessions = all.filter((s) => s.status === "finished");
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  function elapsed(session) {
    const h = Math.round((Date.now() / 1000 - session.last_action_at) / 3600);
    if (h < 1) return $_('game_card.just_now');
    if (h < 24) return $_('game_card.hours_ago', { values: { n: h } });
    return $_('game_card.days_ago', { values: { n: Math.round(h / 24) } });
  }

  function result(session) {
    if (!session.my_username) return null;
    if (session.winner === null) return 'draw';
    return session.winner === session.my_username ? 'won' : 'lost';
  }

  function opponents(session) {
    return session.players
      .filter(p => p.username !== session.my_username)
      .map(p => p.username)
      .join(', ') || '—';
  }
</script>

<button
  class="inline-flex items-center gap-1 text-sm px-3 py-1.5 mb-6 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
  onclick={onBack}
>
  {$_('history.back')}
</button>

<h1 class="text-2xl font-bold mb-6">{$_('history.title')}</h1>

{#if error}
  <p class="text-red-500 mb-4">{error}</p>
{/if}

{#if loading}
  <p class="text-gray-500 dark:text-gray-400">{$_('history.loading')}</p>
{:else if sessions.length === 0}
  <p class="text-gray-500 dark:text-gray-400">{$_('history.empty')}</p>
{:else}
  <table class="w-full text-sm">
    <thead>
      <tr class="text-left text-xs text-gray-400 dark:text-gray-600 uppercase tracking-wide border-b border-gray-100 dark:border-gray-800">
        <th class="pb-2 font-medium">{$_('history.col_game')}</th>
        <th class="pb-2 font-medium">{$_('history.col_opponent')}</th>
        <th class="pb-2 font-medium">{$_('history.col_result')}</th>
        <th class="pb-2 font-medium text-right">{$_('history.col_when')}</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
      {#each sessions as session (session.uuid)}
        {@const r = result(session)}
        <tr
          class="hover:bg-gray-50 dark:hover:bg-gray-800/40 cursor-pointer"
          onclick={() => onJoinGame(session.uuid)}
        >
          <td class="py-2.5 pr-4">{$_(`games.${session.game_slug}.name`, { default: session.game_slug })}</td>
          <td class="py-2.5 pr-4 text-gray-500 dark:text-gray-400">{opponents(session)}</td>
          <td class="py-2.5 pr-4">
            {#if r === 'won'}
              <span class="text-green-600 dark:text-green-400 font-medium">{$_('history.won')}</span>
            {:else if r === 'lost'}
              <span class="text-red-500 dark:text-red-400">{$_('history.lost')}</span>
            {:else if r === 'draw'}
              <span class="text-gray-500 dark:text-gray-400">{$_('history.draw')}</span>
            {:else}
              <span class="text-gray-400 dark:text-gray-600">—</span>
            {/if}
          </td>
          <td class="py-2.5 text-right text-gray-400 dark:text-gray-500 whitespace-nowrap">{elapsed(session)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}
