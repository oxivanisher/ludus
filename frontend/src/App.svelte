<script>
  import { onMount, onDestroy } from "svelte";
  import { _, locale } from 'svelte-i18n';
  import { setupI18n } from './lib/i18n.js';
  import { handleImportFromUrl, importToken } from "./lib/token.js";
  import { installState } from "./lib/install.svelte.js";
  import { api } from "./lib/api.js";
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
  let versionPoller;

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

  onDestroy(() => clearInterval(versionPoller));

  onMount(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      installState.prompt = e;
    });

    // Register SW unconditionally for install prompt + update detection
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        if (navigator.serviceWorker.controller) {
          reg.addEventListener('updatefound', () => {
            const sw = reg.installing;
            sw?.addEventListener('statechange', () => {
              if (sw.state === 'activated') window.location.reload();
            });
          });
        }
      });
    }

    // Poll git_commit every 60s — catches deploys where sw.js itself didn't change
    let initialCommit = null;
    api.stats().then((s) => {
      if (s?.git_commit && s.git_commit !== 'dev') initialCommit = s.git_commit;
    }).catch(() => {});

    versionPoller = setInterval(async () => {
      try {
        const { git_commit } = await api.stats();
        if (!git_commit || git_commit === 'dev') return;
        if (initialCommit && git_commit !== initialCommit) { window.location.reload(); return; }
        if (!initialCommit) initialCommit = git_commit;
      } catch {}
    }, 60_000);

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

{#if installState.iosHintOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-50 bg-black/50 flex items-end justify-center p-4"
       onclick={() => { installState.iosHintOpen = false; }}>
    <div class="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-sm space-y-4"
         onclick={(e) => e.stopPropagation()}>
      <h2 class="font-semibold text-lg">{$_('install.ios_title')}</h2>
      <ol class="space-y-3 text-sm text-gray-700 dark:text-gray-300">
        <li class="flex gap-3"><span class="font-semibold text-indigo-600 dark:text-indigo-400 shrink-0">1.</span><span>{$_('install.ios_step1')}</span></li>
        <li class="flex gap-3"><span class="font-semibold text-indigo-600 dark:text-indigo-400 shrink-0">2.</span><span>{$_('install.ios_step2')}</span></li>
        <li class="flex gap-3"><span class="font-semibold text-indigo-600 dark:text-indigo-400 shrink-0">3.</span><span>{$_('install.ios_step3')}</span></li>
      </ol>
      <button
        class="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        onclick={() => { installState.iosHintOpen = false; }}
      >{$_('install.close')}</button>
    </div>
  </div>
{/if}
