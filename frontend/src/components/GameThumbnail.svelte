<script>
  let { slug } = $props();
</script>

<!--
  Fills its parent container — wrap with a sized div to control dimensions.
  SVG thumbnails use viewBox so they scale perfectly at any size.
-->

{#if slug === 'tictactoe'}
  <svg viewBox="0 0 48 48" class="w-full h-full rounded-lg" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#f1f5f9" rx="6"/>
    <g stroke="#94a3b8" stroke-width="1.5">
      <line x1="16" y1="3"  x2="16" y2="45"/>
      <line x1="32" y1="3"  x2="32" y2="45"/>
      <line x1="3"  y1="16" x2="45" y2="16"/>
      <line x1="3"  y1="32" x2="45" y2="32"/>
    </g>
    <!-- X indigo – top-left, center, bottom-right -->
    <g stroke="#4f46e5" stroke-width="2.5" stroke-linecap="round">
      <line x1="4"  y1="4"  x2="12" y2="12"/>
      <line x1="12" y1="4"  x2="4"  y2="12"/>
      <line x1="20" y1="20" x2="28" y2="28"/>
      <line x1="28" y1="20" x2="20" y2="28"/>
      <line x1="36" y1="36" x2="44" y2="44"/>
      <line x1="44" y1="36" x2="36" y2="44"/>
    </g>
    <!-- O rose – top-right, bottom-left -->
    <circle cx="40" cy="8"  r="4" fill="none" stroke="#e11d48" stroke-width="2.5"/>
    <circle cx="8"  cy="40" r="4" fill="none" stroke="#e11d48" stroke-width="2.5"/>
  </svg>

{:else if slug === 'connect_four'}
  <svg viewBox="0 0 48 48" class="w-full h-full rounded-lg" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#1d4ed8" rx="6"/>
    <!-- 4 cols × 3 rows, r=5. Col x: 6 18 30 42. Row y: 8 24 40 -->
    <!-- bottom: Y R Y R -->
    <circle cx="6"  cy="40" r="5" fill="#eab308"/>
    <circle cx="18" cy="40" r="5" fill="#ef4444"/>
    <circle cx="30" cy="40" r="5" fill="#eab308"/>
    <circle cx="42" cy="40" r="5" fill="#ef4444"/>
    <!-- middle: R Y Y _ -->
    <circle cx="6"  cy="24" r="5" fill="#ef4444"/>
    <circle cx="18" cy="24" r="5" fill="#eab308"/>
    <circle cx="30" cy="24" r="5" fill="#eab308"/>
    <circle cx="42" cy="24" r="5" fill="#1e3a8a"/>
    <!-- top: _ Y _ _ -->
    <circle cx="6"  cy="8"  r="5" fill="#1e3a8a"/>
    <circle cx="18" cy="8"  r="5" fill="#eab308"/>
    <circle cx="30" cy="8"  r="5" fill="#1e3a8a"/>
    <circle cx="42" cy="8"  r="5" fill="#1e3a8a"/>
  </svg>

{:else if slug === 'battleship'}
  <div class="w-full h-full rounded-lg bg-sky-600 flex items-center justify-center text-3xl leading-none select-none">
    🚢
  </div>

{:else if slug === 'mastermind'}
  <svg viewBox="0 0 48 48" class="w-full h-full rounded-lg" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#fafaf9" rx="6"/>
    <!-- Guess row: 4 coloured pegs -->
    <circle cx="7"  cy="14" r="6" fill="#ef4444"/>
    <circle cx="19" cy="14" r="6" fill="#3b82f6"/>
    <circle cx="31" cy="14" r="6" fill="#eab308"/>
    <circle cx="43" cy="14" r="6" fill="#22c55e"/>
    <!-- Divider -->
    <line x1="3" y1="25" x2="45" y2="25" stroke="#e2e8f0" stroke-width="1"/>
    <!-- Feedback pegs: 2 black hits, 1 white near-miss, 1 empty -->
    <circle cx="10" cy="36" r="5" fill="#111"/>
    <circle cx="24" cy="36" r="5" fill="#111"/>
    <circle cx="38" cy="36" r="5" fill="none" stroke="#cbd5e1" stroke-width="1.5"/>
  </svg>

{:else if slug === 'mill'}
  <svg viewBox="0 0 48 48" class="w-full h-full rounded-lg" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#f8fafc" rx="6"/>
    <!-- Three nested squares: outer 2–46, middle 11–37, inner 20–28 -->
    <rect x="2"  y="2"  width="44" height="44" fill="none" stroke="#64748b" stroke-width="1.5" rx="1"/>
    <rect x="11" y="11" width="26" height="26" fill="none" stroke="#64748b" stroke-width="1.5" rx="1"/>
    <rect x="20" y="20" width="8"  height="8"  fill="none" stroke="#64748b" stroke-width="1.5" rx="1"/>
    <!-- Cross-connections -->
    <line x1="24" y1="2"  x2="24" y2="20" stroke="#64748b" stroke-width="1.5"/>
    <line x1="24" y1="28" x2="24" y2="46" stroke="#64748b" stroke-width="1.5"/>
    <line x1="2"  y1="24" x2="20" y2="24" stroke="#64748b" stroke-width="1.5"/>
    <line x1="28" y1="24" x2="46" y2="24" stroke="#64748b" stroke-width="1.5"/>
    <!-- Amber pieces: outer TL, outer T-mid, middle L-mid -->
    <circle cx="2"  cy="2"  r="3.5" fill="#f59e0b"/>
    <circle cx="24" cy="2"  r="3.5" fill="#f59e0b"/>
    <circle cx="11" cy="24" r="3.5" fill="#f59e0b"/>
    <!-- Indigo pieces: outer TR, middle TL -->
    <circle cx="46" cy="2"  r="3.5" fill="#6366f1"/>
    <circle cx="11" cy="11" r="3.5" fill="#6366f1"/>
  </svg>

{:else if slug === 'reversi'}
  <svg viewBox="0 0 48 48" class="w-full h-full rounded-lg" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#15803d" rx="6"/>
    <!-- Subtle grid lines (3×3 cells, 16px each) -->
    <g stroke="#166534" stroke-width="0.75">
      <line x1="16" y1="0" x2="16" y2="48"/>
      <line x1="32" y1="0" x2="32" y2="48"/>
      <line x1="0"  y1="16" x2="48" y2="16"/>
      <line x1="0"  y1="32" x2="48" y2="32"/>
    </g>
    <!-- Starting 4 pieces centred at (24,24) ± 6 -->
    <circle cx="18" cy="18" r="7" fill="#f5f5f5"/>
    <circle cx="30" cy="18" r="7" fill="#1a1a1a"/>
    <circle cx="18" cy="30" r="7" fill="#1a1a1a"/>
    <circle cx="30" cy="30" r="7" fill="#f5f5f5"/>
    <!-- Two extra pieces showing a game in progress -->
    <circle cx="18" cy="6"  r="5" fill="#1a1a1a"/>
    <circle cx="42" cy="30" r="5" fill="#f5f5f5"/>
  </svg>

{:else if slug === 'memory'}
  <!-- 3×2 grid: face-down (indigo) and face-up (white + emoji) cards -->
  <div class="w-full h-full rounded-lg bg-slate-200 grid grid-cols-3 gap-[3px] p-[4px]">
    <div class="rounded bg-indigo-600"></div>
    <div class="rounded bg-white border border-slate-200 flex items-center justify-center text-[10px]">🐶</div>
    <div class="rounded bg-indigo-600"></div>
    <div class="rounded bg-white border border-slate-200 flex items-center justify-center text-[10px]">🐶</div>
    <div class="rounded bg-indigo-600"></div>
    <div class="rounded bg-indigo-600"></div>
  </div>

{:else if slug === 'gomoku'}
  <svg viewBox="0 0 48 48" class="w-full h-full rounded-lg" xmlns="http://www.w3.org/2000/svg">
    <rect width="48" height="48" fill="#DCB167" rx="6"/>
    <!-- 5×5 mini grid, margin 4, cell 10 -->
    <g stroke="#8B6425" stroke-width="0.75">
      {#each [4, 14, 24, 34, 44] as p}
        <line x1={p} y1="4" x2={p} y2="44"/>
        <line x1="4" y1={p} x2="44" y2={p}/>
      {/each}
    </g>
    <!-- Star point at center -->
    <circle cx="24" cy="24" r="1.5" fill="#8B6425"/>
    <!-- Black stones -->
    <circle cx="14" cy="14" r="5" fill="#111" stroke="#444" stroke-width="0.5"/>
    <circle cx="24" cy="24" r="5" fill="#111" stroke="#444" stroke-width="0.5"/>
    <circle cx="34" cy="34" r="5" fill="#111" stroke="#444" stroke-width="0.5"/>
    <!-- White stones -->
    <circle cx="24" cy="14" r="5" fill="#f5f5f5" stroke="#aaa" stroke-width="0.5"/>
    <circle cx="14" cy="24" r="5" fill="#f5f5f5" stroke="#aaa" stroke-width="0.5"/>
    <circle cx="34" cy="24" r="5" fill="#f5f5f5" stroke="#aaa" stroke-width="0.5"/>
  </svg>

{:else}
  <div class="w-full h-full rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-2xl select-none">
    🎮
  </div>
{/if}
