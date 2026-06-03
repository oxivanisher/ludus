<script>
  import { onMount } from "svelte";
  import { _, locale } from 'svelte-i18n';
  import { setupI18n } from './lib/i18n.js';
  import { handleImportFromUrl, importToken } from "./lib/token.js";
  import Lobby from "./pages/Lobby.svelte";
  import GameRoom from "./pages/GameRoom.svelte";
  import History from "./pages/History.svelte";
  import About from "./pages/About.svelte";
  import TokenManager from "./components/TokenManager.svelte";

  setupI18n();

  let page = $state("lobby");
  let sessionId = $state(null);
  let showTokenManager = $state(false);
  let pendingImportToken = $state(null);

  function navigate(to, id = null) {
    sessionId = id;
    page = to;
    const url = to === "game" ? `/game/${id}` : to === "history" ? "/history" : to === "about" ? "/about" : "/";
    window.history.pushState({}, "", url);
  }

  function setLocale(lang) {
    locale.set(lang);
    localStorage.setItem('ludus_locale', lang);
  }

  onMount(() => {
    const incoming = handleImportFromUrl();
    if (incoming) pendingImportToken = incoming;

    const path = window.location.pathname;
    const match = path.match(/^\/game\/([^/]+)/);
    if (match) {
      page = "game";
      sessionId = match[1];
    } else if (path === "/history") {
      page = "history";
    } else if (path === "/about") {
      page = "about";
    }

    window.addEventListener("popstate", () => {
      const p = window.location.pathname;
      const m = p.match(/^\/game\/([^/]+)/);
      if (m) { page = "game"; sessionId = m[1]; }
      else if (p === "/history") { page = "history"; sessionId = null; }
      else if (p === "/about") { page = "about"; sessionId = null; }
      else { page = "lobby"; sessionId = null; }
    });
  });
</script>

<!-- Token import confirmation banner -->
{#if pendingImportToken}
  <div class="fixed inset-x-0 top-0 z-50 bg-yellow-100 border-b border-yellow-300 p-4 flex items-center justify-between gap-4
              dark:bg-yellow-900/60 dark:border-yellow-700">
    <p class="text-sm text-yellow-900 dark:text-yellow-200">
      {$_('token_import.prompt', { values: { token: pendingImportToken.slice(0, 8) + '…' } })}
    </p>
    <div class="flex gap-2 shrink-0">
      <button
        class="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
        onclick={() => { importToken(pendingImportToken); }}
      >{$_('token_import.confirm')}</button>
      <button
        class="px-3 py-1 bg-white border border-yellow-400 rounded text-sm dark:bg-gray-800 dark:border-yellow-600 dark:text-gray-200"
        onclick={() => { pendingImportToken = null; }}
      >{$_('token_import.cancel')}</button>
    </div>
  </div>
{/if}

<!-- Top bar -->
<header class="bg-indigo-700 text-white px-4 py-3 flex items-center justify-between dark:bg-indigo-900">
  <button class="text-xl font-bold tracking-wide" onclick={() => navigate("lobby")}>
    Ludus
  </button>
  <div class="flex items-center gap-3">
    <div class="flex gap-1 text-xs">
      <button
        class="px-2 py-0.5 rounded transition-colors {$locale === 'en' || $locale?.startsWith('en-') ? 'bg-white/20 font-semibold' : 'opacity-70 hover:opacity-100'}"
        onclick={() => setLocale('en')}
      >EN</button>
      <button
        class="px-2 py-0.5 rounded transition-colors {$locale === 'de' || $locale?.startsWith('de-') ? 'bg-white/20 font-semibold' : 'opacity-70 hover:opacity-100'}"
        onclick={() => setLocale('de')}
      >DE</button>
    </div>
    <button
      class="text-sm underline opacity-80 hover:opacity-100"
      onclick={() => navigate("about")}
    >
      {$_('nav.about')}
    </button>
    <button
      class="text-sm underline opacity-80 hover:opacity-100"
      onclick={() => { showTokenManager = true; }}
    >
      {$_('nav.my_token')}
    </button>
  </div>
</header>

<!-- Page content -->
<main class="max-w-2xl mx-auto px-4 py-6">
  {#if page === "lobby"}
    <Lobby onJoinGame={(id) => navigate("game", id)} onHistory={() => navigate("history")} />
  {:else if page === "game"}
    {#key sessionId}
      <GameRoom {sessionId} onBack={() => navigate("lobby")} onJoinGame={(id) => navigate("game", id)} />
    {/key}
  {:else if page === "history"}
    <History onBack={() => navigate("lobby")} onJoinGame={(id) => navigate("game", id)} />
  {:else if page === "about"}
    <About onBack={() => navigate("lobby")} />
  {/if}
</main>

{#if showTokenManager}
  <TokenManager onClose={() => { showTokenManager = false; }} />
{/if}
