<script>
  import { onMount, onDestroy } from "svelte";
  import { _ } from 'svelte-i18n';
  import { api } from "../lib/api.js";
  import { getSavedUsername, saveUsername } from "../lib/username.js";
  import { installState, isIOS, isInstalled, hasPlayedGame, triggerInstall } from "../lib/install.svelte.js";
  import GameCard from "../components/GameCard.svelte";
  import GameThumbnail from "../components/GameThumbnail.svelte";

  let { onJoinGame, onHistory } = $props();

  let sessions = $state([]);
  let games = $state([]);
  let stats = $state(null);
  let publicSessions = $state([]);
  let loading = $state(true);
  let error = $state(null);

  let showNewGame = $state(false);
  let selectedSlug = $state("");
  let username = $state(getSavedUsername());
  let vsComputer = $state(false);

  function getPublicPref() {
    const stored = localStorage.getItem('ludus_public_game');
    return stored === null ? true : stored === 'true';
  }
  let creating = $state(false);

  const selectedGame = $derived(games.find(g => g.slug === selectedSlug) ?? null);

  let activeSessions = $derived(sessions.filter((s) => s.status !== "finished"));
  let hasFinished = $derived(sessions.some((s) => s.status === "finished"));

  // Public sessions where the viewer is not already a participant
  let joinableSessions = $derived(publicSessions.filter((s) => s.my_username === null));

  async function refreshPublic() {
    if (document.hidden) return;
    try {
      [publicSessions, stats] = await Promise.all([api.publicSessions(), api.stats()]);
    } catch {}
  }

  let pollTimer;

  onMount(async () => {
    try {
      [sessions, games, stats, publicSessions] = await Promise.all([
        api.mySessions(),
        api.games(),
        api.stats(),
        api.publicSessions(),
      ]);
      if (sessions.every((s) => s.status === "finished")) {
        showNewGame = true;
      }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }

    pollTimer = setInterval(refreshPublic, 5000);
    document.addEventListener("visibilitychange", refreshPublic);
  });

  onDestroy(() => {
    clearInterval(pollTimer);
    document.removeEventListener("visibilitychange", refreshPublic);
  });

  async function createGame() {
    if (!selectedSlug || !username.trim()) return;
    creating = true;
    try {
      const trimmed = username.trim();
      saveUsername(trimmed);
      const session = await api.createSession(selectedSlug, trimmed, vsComputer ? false : getPublicPref(), vsComputer);
      onJoinGame(session.uuid);
    } catch (e) {
      error = e.message;
    } finally {
      creating = false;
    }
  }
</script>

<h1 class="text-2xl font-bold mb-6">{$_('lobby.title')}</h1>

{#if error}
  <p class="text-red-500 mb-4">{error}</p>
{/if}

{#if loading}
  <p class="text-gray-500 dark:text-gray-400">{$_('lobby.loading')}</p>
{:else}
  {#if activeSessions.length === 0}
    <p class="text-gray-500 dark:text-gray-400 mb-6">{$_('lobby.no_active')}</p>
  {:else}
    <div class="space-y-3 mb-8">
      {#each activeSessions as session (session.uuid)}
        <GameCard {session} onClick={() => onJoinGame(session.uuid)} />
      {/each}
    </div>
  {/if}

  {#if !showNewGame}
    <button
      class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
      onclick={() => { showNewGame = true; }}
    >
      {$_('lobby.new_game')}
    </button>
  {/if}

  {#if showNewGame}
    <div class="mt-4 p-4 border rounded-lg space-y-3
                bg-gray-50 border-gray-200
                dark:bg-gray-800 dark:border-gray-700">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">{$_('lobby.create.title')}</h2>
        <button
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-xl leading-none"
          onclick={() => { showNewGame = false; }}
        >×</button>
      </div>

      <div>
        <label for="new-game-username" class="block text-sm text-gray-600 dark:text-gray-400 mb-1">
          {$_('lobby.create.username_label')}
        </label>
        <input
          id="new-game-username"
          class="w-full border rounded px-3 py-2
                 border-gray-300 bg-white text-gray-900 placeholder-gray-400
                 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
          placeholder={$_('lobby.create.username_placeholder')}
          bind:value={username}
        />
      </div>

      <div>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">{$_('lobby.create.choose_game')}</p>
        <div class="grid grid-cols-2 gap-2">
          {#each games as game}
            <button
              class="p-3 border rounded text-left transition-colors flex flex-col justify-start
                     border-gray-200 hover:border-indigo-400
                     dark:border-gray-600 dark:hover:border-indigo-500
                     {selectedSlug === game.slug
                       ? 'border-indigo-600 bg-indigo-50 dark:border-indigo-500 dark:bg-indigo-900/30'
                       : ''}"
              onclick={() => { selectedSlug = game.slug; vsComputer = false; }}
            >
              <div class="flex items-center gap-2 mb-1.5">
                <div class="w-8 h-8 shrink-0">
                  <GameThumbnail slug={game.slug} />
                </div>
                <div class="font-medium leading-tight">{$_(`games.${game.slug}.name`, { default: game.name })}</div>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{$_(`games.${game.slug}.description`, { default: game.description })}</div>
            </button>
          {/each}
        </div>
      </div>

      {#if selectedGame?.supports_solo}
        <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer select-none">
          <input type="checkbox" class="rounded" bind:checked={vsComputer} />
          {$_('lobby.create.vs_computer')}
        </label>
      {/if}

      <button
        class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        disabled={creating || !selectedSlug || !username.trim()}
        onclick={createGame}
      >
        {creating ? $_('lobby.create.submitting') : $_('lobby.create.submit')}
      </button>
    </div>
  {/if}

  {#if joinableSessions.length > 0}
    <div class="mt-10">
      <h2 class="text-sm font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
        {$_('lobby.open_games')}
      </h2>
      <div class="space-y-3">
        {#each joinableSessions as session (session.uuid)}
          <GameCard {session} onClick={() => onJoinGame(session.uuid)} />
        {/each}
      </div>
    </div>
  {/if}

  {#if hasFinished}
    <div class="mt-8">
      <button
        class="inline-flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
        onclick={onHistory}
      >
        {$_('lobby.past_games_link')}
      </button>
    </div>
  {/if}

  {#if !isInstalled() && (installState.prompt || isIOS())}
    <div class="mt-4">
      <button
        class="inline-flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
        onclick={() => isIOS() ? (installState.iosHintOpen = true) : triggerInstall()}
      >
        <span>📱</span>
        <span>{$_('install.button')}</span>
      </button>
    </div>
  {/if}
{/if}

{#if stats}
  <div class="mt-10 pt-4 border-t border-gray-100 dark:border-gray-800 flex items-center gap-2 text-xs text-gray-300 dark:text-gray-700">
    <span class="inline-flex items-center gap-1.5">
      <span class="relative flex h-1.5 w-1.5">
        {#if stats.active_games > 0}
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        {/if}
        <span class="relative inline-flex rounded-full h-1.5 w-1.5 {stats.active_games > 0 ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}"></span>
      </span>
      {$_('lobby.stats_in_progress', { values: { count: stats.active_games } })}
    </span>
    <span>·</span>
    <span>{$_('lobby.stats_total', { values: { count: stats.total_games } })}</span>
    {#if stats.git_commit}
      <span class="ml-auto font-mono">{stats.git_commit.slice(0, 7)}</span>
    {/if}
  </div>
{/if}
