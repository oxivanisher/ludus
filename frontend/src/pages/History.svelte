<script>
  import { onMount } from "svelte";
  import { _ } from "svelte-i18n";
  import { api } from "../lib/api.js";
  import GameCard from "../components/GameCard.svelte";

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
</script>

<button class="text-sm text-indigo-600 dark:text-indigo-400 mb-6 hover:underline" onclick={onBack}>
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
  <div class="space-y-3">
    {#each sessions as session (session.uuid)}
      <GameCard {session} onClick={() => onJoinGame(session.uuid)} />
    {/each}
  </div>
{/if}
