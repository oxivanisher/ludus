<script>
  import { _ } from 'svelte-i18n';
  import GameThumbnail from './GameThumbnail.svelte';

  let { session, onClick } = $props();

  let myUsername = $derived(session.my_username ?? null);
  let isMyTurn = $derived(session.current_turn === myUsername);
  let elapsed = $derived(Math.round((Date.now() / 1000 - session.last_action_at) / 3600));
  let elapsedLabel = $derived(
    elapsed < 1
      ? $_('game_card.just_now')
      : elapsed < 24
        ? $_('game_card.hours_ago', { values: { n: elapsed } })
        : $_('game_card.days_ago', { values: { n: Math.round(elapsed / 24) } })
  );
  let opponents = $derived(
    session.players.filter((p) => p.username !== myUsername).map((p) => p.username)
  );
  let isParticipant = $derived(myUsername !== null);
</script>

<button
  class="w-full text-left p-4 border rounded-lg transition-colors flex items-center gap-3
         border-gray-200 hover:border-indigo-400 hover:bg-indigo-50
         dark:border-gray-700 dark:hover:border-indigo-500 dark:hover:bg-indigo-900/20"
  onclick={onClick}
>
  <div class="w-10 h-10 shrink-0">
    <GameThumbnail slug={session.game_slug} />
  </div>

  <div class="flex-1 min-w-0">
    <div class="font-medium">{$_(`games.${session.game_slug}.name`, { default: session.game_slug })}</div>
    <div class="text-sm text-gray-500 dark:text-gray-400">
      {#if isParticipant}
        {$_('game_card.vs', { values: { opponents: opponents.length ? opponents.join(", ") : $_('game_card.waiting_for_opponent') } })}
      {:else}
        {session.players.map((p) => p.username).join(", ")}
      {/if}
    </div>
    <div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{elapsedLabel}</div>
  </div>

  <div class="shrink-0 text-sm font-medium ml-auto">
    {#if session.status === "finished"}
      <span class="text-gray-500 dark:text-gray-400">{$_('game_card.status_finished')}</span>
    {:else if session.status === "waiting"}
      <span class="text-yellow-600 dark:text-yellow-400">{$_('game_card.status_waiting')}</span>
    {:else if isMyTurn}
      <span class="text-indigo-700 dark:text-indigo-400">{$_('game_card.your_turn')}</span>
    {:else}
      <span class="text-gray-400 dark:text-gray-500">{$_('game_card.their_turn')}</span>
    {/if}
  </div>
</button>
