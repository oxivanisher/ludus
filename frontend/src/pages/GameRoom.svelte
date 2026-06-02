<script>
  import { onMount, onDestroy } from "svelte";
  import { _ } from 'svelte-i18n';
  import { api } from "../lib/api.js";
  import { createGameSocket } from "../lib/ws.js";
  import { subscribeToPush, unsubscribeFromPush, isPushSupported } from "../lib/push.js";
  import { getSavedUsername, saveUsername } from "../lib/username.js";
  import TicTacToe from "../games/TicTacToe.svelte";
  import ConnectFour from "../games/ConnectFour.svelte";
  import Battleship from "../games/Battleship.svelte";

  const GAME_COMPONENTS = {
    tictactoe: TicTacToe,
    connect_four: ConnectFour,
    battleship: Battleship,
  };

  let { sessionId, onBack, onJoinGame } = $props();

  let session = $state(null);
  let error = $state(null);
  let socket = null;

  let joinUsername = $state(getSavedUsername());
  let joining = $state(false);

  let isParticipant = $derived(session?.my_username !== null && session?.my_username !== undefined);

  let inviteCopied = $state(false);
  let inviteUrl = $derived(session ? `${location.origin}/game/${session.uuid}` : "");

  let pushSupported = isPushSupported();
  let pushPermission = $state(Notification.permission ?? "default");

  async function togglePush() {
    if (pushPermission === "granted") {
      await unsubscribeFromPush();
      pushPermission = "default";
    } else {
      const result = await subscribeToPush();
      pushPermission = result === "granted" ? "granted" : Notification.permission;
    }
  }

  onMount(async () => {
    try {
      session = await api.getSession(sessionId);
    } catch (e) {
      error = e.message;
      return;
    }

    socket = createGameSocket(sessionId, {
      onState: (s) => { session = s; },
      onError: (msg) => { error = msg; },
      onCancelled: () => { onBack(); },
    });
  });

  onDestroy(() => socket?.close());

  function sendAction(action) {
    socket?.sendAction(action);
  }

  async function joinGame() {
    if (!joinUsername.trim()) return;
    joining = true;
    try {
      const trimmed = joinUsername.trim();
      saveUsername(trimmed);
      session = await api.joinSession(sessionId, trimmed);
    } catch (e) {
      error = e.message;
    } finally {
      joining = false;
    }
  }

  async function copyInvite() {
    await navigator.clipboard.writeText(inviteUrl);
    inviteCopied = true;
    setTimeout(() => { inviteCopied = false; }, 2000);
  }

  let GameComponent = $derived(session ? GAME_COMPONENTS[session.game_slug] : null);
  let myUsername = $derived(session?.my_username ?? null);

  let isOwner = $derived(session?.players[0]?.username === myUsername);

  let cancelling = $state(false);

  async function cancelGame() {
    cancelling = true;
    try {
      await api.cancelSession(sessionId);
      onBack();
    } catch (e) {
      error = e.message;
      cancelling = false;
    }
  }

  let rematching = $state(false);

  async function requestRematch() {
    rematching = true;
    try {
      const newSession = await api.rematch(sessionId);
      onJoinGame(newSession.uuid);
    } catch (e) {
      error = e.message;
    } finally {
      rematching = false;
    }
  }

  function goToRematch() {
    onJoinGame(session.rematch_session_id);
  }
</script>

<button class="text-sm text-indigo-600 dark:text-indigo-400 mb-4 hover:underline" onclick={onBack}>
  {$_('game_room.back')}
</button>

{#if error}
  <p class="text-red-500 mb-4">{error}</p>
{/if}

{#if !session}
  <p class="text-gray-500 dark:text-gray-400">{$_('game_room.loading')}</p>
{:else}
  <div class="flex items-center justify-between mb-4">
    <h1 class="text-xl font-bold">{$_(`games.${session.game_slug}.name`, { default: session.game_slug })}</h1>
    <div class="flex items-center gap-2">
      {#if pushSupported && isParticipant && session.status !== "finished"}
        <button
          class="text-xs px-2 py-1 rounded border transition-colors
                 {pushPermission === 'granted'
                   ? 'bg-indigo-50 border-indigo-300 text-indigo-700 dark:bg-indigo-900/30 dark:border-indigo-600 dark:text-indigo-300'
                   : 'bg-gray-50 border-gray-300 text-gray-500 hover:border-indigo-300 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400'}"
          onclick={togglePush}
          title={pushPermission === 'granted' ? $_('game_room.push_on_title') : $_('game_room.push_off_title')}
        >
          {pushPermission === "granted" ? $_('game_room.push_on') : $_('game_room.push_off')}
        </button>
      {/if}
      <span class="text-sm px-2 py-1 rounded bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
        {#if session.status === "waiting"}
          {$_('game_room.status_waiting')}
        {:else if session.status === "playing"}
          {$_('game_room.status_playing')}
        {:else if session.status === "finished"}
          {$_('game_room.status_finished')}
        {:else}
          {session.status}
        {/if}
      </span>
    </div>
  </div>

  <!-- Players -->
  <div class="flex gap-3 mb-4 text-sm flex-wrap">
    {#each session.players as p}
      <span class="px-2 py-1 bg-indigo-100 rounded dark:bg-indigo-900/40 dark:text-indigo-200">
        {p.username}{p.username === myUsername ? ' ' + $_('game_card.you') : ""}
      </span>
    {/each}
  </div>

  <!-- Waiting: invite link + optional join form -->
  {#if session.status === "waiting"}
    <div class="p-4 rounded-lg mb-4 space-y-3
                bg-yellow-50 border border-yellow-200
                dark:bg-yellow-900/20 dark:border-yellow-700">
      <p class="text-sm text-yellow-800 dark:text-yellow-300">{$_('game_room.waiting_title')}</p>

      {#if isParticipant}
      <div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">{$_('game_room.invite_link')}</p>
        <div class="flex gap-2">
          <input
            class="flex-1 border rounded px-2 py-1 text-sm font-mono bg-white
                   dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
            readonly
            value={inviteUrl}
          />
          <button
            class="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
            onclick={copyInvite}
          >
            {inviteCopied ? $_('game_room.copied') : $_('game_room.copy')}
          </button>
        </div>
      </div>
      {/if}

      {#if !isParticipant}
        <div class="flex gap-2 pt-1 flex-wrap">
          <input
            class="border rounded px-3 py-1 text-sm
                   dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
            placeholder={$_('game_room.join_placeholder')}
            bind:value={joinUsername}
          />
          <button
            class="px-3 py-1 bg-green-600 text-white rounded text-sm disabled:opacity-50 hover:bg-green-700"
            disabled={joining || !joinUsername.trim()}
            onclick={joinGame}
          >
            {joining ? $_('game_room.joining') : $_('game_room.join')}
          </button>
        </div>
      {/if}

      {#if isOwner}
        <div class="pt-1">
          <button
            class="px-3 py-1 bg-red-600 text-white rounded text-sm disabled:opacity-50 hover:bg-red-700"
            disabled={cancelling}
            onclick={cancelGame}
          >
            {cancelling ? $_('game_room.cancelling') : $_('game_room.cancel_game')}
          </button>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Finished banner -->
  {#if session.status === "finished"}
    <div class="p-4 mb-4 rounded-lg text-sm space-y-3
                bg-green-50 border border-green-200
                dark:bg-green-900/20 dark:border-green-700">
      <p class="font-medium">
        {#if session.winner}
          {session.winner === myUsername ? $_('game_room.you_win') : $_('game_room.winner_wins', { values: { winner: session.winner } })}
        {:else}
          {$_('game_room.draw')}
        {/if}
      </p>

      {#if session.rematch_session_id}
        <!-- Rematch already created — both players can jump in -->
        <button
          class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm"
          onclick={goToRematch}
        >
          {$_('game_room.go_to_rematch')}
        </button>
      {:else if isParticipant}
        <!-- Either participant can trigger the rematch -->
        <button
          class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 text-sm disabled:opacity-50"
          disabled={rematching}
          onclick={requestRematch}
        >
          {rematching ? $_('game_room.starting_rematch') : $_('game_room.play_again')}
        </button>
      {/if}
    </div>
  {/if}

  <!-- Turn indicator -->
  {#if session.status === "playing" && !('phase' in (session.state ?? {}))}
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
      {#if session.current_turn === myUsername}
        <span class="font-semibold text-indigo-700 dark:text-indigo-400">{$_('game_room.your_turn')}</span>
      {:else}
        {$_('game_room.their_turn', { values: { player: session.current_turn } })}
      {/if}
    </p>
  {/if}

  <!-- How to play -->
  <details class="mb-4 group">
    <summary class="cursor-pointer text-sm text-indigo-600 dark:text-indigo-400 hover:underline list-none flex items-center gap-1">
      <span class="text-xs">▶</span>
      <span class="group-open:hidden">{$_('game_room.how_to_play')}</span>
      <span class="hidden group-open:inline">{$_('game_room.how_to_play')}</span>
    </summary>
    <ul class="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
      {#each $_(`games.${session.game_slug}.how_to_play`).split('\n') as rule}
        <li>{rule}</li>
      {/each}
    </ul>
  </details>

  <!-- Game board -->
  {#if GameComponent}
    <GameComponent {session} {myUsername} onAction={sendAction} />
  {:else}
    <p class="text-gray-500 dark:text-gray-400 text-sm">{$_('game_room.no_ui', { values: { slug: session.game_slug } })}</p>
  {/if}
{/if}
