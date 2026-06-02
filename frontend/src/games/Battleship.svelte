<script>
  import { _ } from 'svelte-i18n';

  let { session, myUsername, onAction } = $props();

  const SHIP_DEFS = [
    { type: 'battleship', size: 4, count: 1 },
    { type: 'cruiser',    size: 3, count: 2 },
    { type: 'destroyer',  size: 2, count: 3 },
    { type: 'submarine',  size: 1, count: 4 },
  ];

  const SHIP_COLORS = {
    battleship: 'bg-violet-600',
    cruiser:    'bg-teal-500',
    destroyer:  'bg-amber-500',
    submarine:  'bg-emerald-500',
  };

  const state = $derived(session.state ?? {});
  const phase = $derived(state.phase ?? 'placement');
  const iAmReady = $derived(state.i_am_ready ?? false);
  const isMyTurn = $derived(
    state.current_turn === myUsername && phase === 'battle' && session.status === 'playing'
  );

  const myShips = $derived(state.my_ships ?? []);
  const placedCounts = $derived.by(() => {
    const counts = {};
    for (const ship of myShips) counts[ship.type] = (counts[ship.type] ?? 0) + 1;
    return counts;
  });
  const remainingShips = $derived(SHIP_DEFS.filter(s => (placedCounts[s.type] ?? 0) < s.count));

  let selectedType = $state(null);
  const selectedDef = $derived(
    remainingShips.find(s => s.type === selectedType) ?? remainingShips[0] ?? null
  );

  let horizontal = $state(true);
  let hoverCell = $state(null);

  // --- error feedback ---
  let placementError = $state(null);
  let errorTimer = null;
  function showError(key) {
    placementError = key;
    clearTimeout(errorTimer);
    errorTimer = setTimeout(() => { placementError = null; }, 2500);
  }

  // --- cell maps ---
  const myShipCellMap = $derived.by(() => {
    const map = {};
    for (const ship of myShips)
      for (const [r, c] of ship.cells) map[`${r},${c}`] = ship;
    return map;
  });

  const myShotMap = $derived.by(() => {
    const map = {};
    for (const s of state.my_shots ?? []) map[`${s.row},${s.col}`] = s.hit;
    return map;
  });

  const incomingMap = $derived.by(() => {
    const map = {};
    for (const s of state.incoming ?? []) map[`${s.row},${s.col}`] = s.hit;
    return map;
  });

  const opponentShipCellMap = $derived.by(() => {
    const map = {};
    for (const ship of state.opponent_ships ?? [])
      for (const [r, c] of ship.cells) map[`${r},${c}`] = ship.type;
    return map;
  });

  // --- placement helpers ---
  function shipBufferZone(ships) {
    const buf = new Set();
    for (const ship of ships)
      for (const [r, c] of ship.cells)
        for (let dr = -1; dr <= 1; dr++)
          for (let dc = -1; dc <= 1; dc++)
            if (dr !== 0 || dc !== 0) buf.add(`${r + dr},${c + dc}`);
    return buf;
  }

  // Which ship (all its cells) is the cursor hovering over, for removal highlight
  const hoveredShipCells = $derived.by(() => {
    if (!hoverCell) return new Set();
    const key = `${hoverCell[0]},${hoverCell[1]}`;
    const ship = myShipCellMap[key];
    if (!ship) return new Set();
    return new Set(ship.cells.map(([r, c]) => `${r},${c}`));
  });

  const isHoverOnShip = $derived(hoveredShipCells.size > 0);

  const previewCells = $derived.by(() => {
    if (!hoverCell || !selectedDef || iAmReady || isHoverOnShip) return [];
    const [row, col] = hoverCell;
    return Array.from({ length: selectedDef.size }, (_, i) =>
      horizontal ? [row, col + i] : [row + i, col]
    );
  });

  const previewValid = $derived.by(() => {
    if (!previewCells.length) return false;
    const occupied = new Set(myShips.flatMap(s => s.cells.map(([r, c]) => `${r},${c}`)));
    const buffer = shipBufferZone(myShips);
    return previewCells.every(([r, c]) =>
      r >= 0 && r < 10 && c >= 0 && c < 10 && !occupied.has(`${r},${c}`) && !buffer.has(`${r},${c}`)
    );
  });

  // Pre-compute all 100 cells for placement grid
  const placementCells = $derived.by(() => {
    const previewSet = new Set(previewCells.map(([r, c]) => `${r},${c}`));
    return Array.from({ length: 100 }, (_, i) => {
      const row = Math.floor(i / 10), col = i % 10;
      const key = `${row},${col}`;
      const ship = myShipCellMap[key];
      const inPreview = previewSet.has(key);
      const inHoveredShip = hoveredShipCells.has(key);
      let cls;
      if (inHoveredShip) {
        cls = 'bg-red-400 dark:bg-red-700 cursor-pointer';
      } else if (inPreview) {
        cls = previewValid ? 'bg-green-300 dark:bg-green-700' : 'bg-red-300 dark:bg-red-800';
      } else if (ship) {
        cls = SHIP_COLORS[ship.type] + ' cursor-pointer';
      } else {
        cls = 'bg-sky-100 dark:bg-sky-900/40';
      }
      return { row, col, key, cls };
    });
  });

  const myGridCells = $derived.by(() => {
    return Array.from({ length: 100 }, (_, i) => {
      const row = Math.floor(i / 10), col = i % 10;
      const key = `${row},${col}`;
      const incomingResult = incomingMap[key];
      const ship = myShipCellMap[key];
      let cls, hitMarker = false, missMarker = false;
      if (ship !== undefined) {
        if (incomingResult === true) { cls = 'bg-red-500'; hitMarker = true; }
        else { cls = SHIP_COLORS[ship.type] + ' opacity-80'; }
      } else if (incomingResult === false) {
        cls = 'bg-sky-200 dark:bg-sky-800/60'; missMarker = true;
      } else {
        cls = 'bg-sky-100 dark:bg-sky-900/40';
      }
      return { row, col, key, cls, hitMarker, missMarker };
    });
  });

  const targetCells = $derived.by(() => {
    return Array.from({ length: 100 }, (_, i) => {
      const row = Math.floor(i / 10), col = i % 10;
      const key = `${row},${col}`;
      const shotResult = myShotMap[key];
      const opponentShip = opponentShipCellMap[key];
      let cls, hitMarker = false, missMarker = false, canFire = false;
      if (shotResult === true) {
        cls = 'bg-red-500'; hitMarker = true;
      } else if (shotResult === false) {
        cls = 'bg-sky-200 dark:bg-sky-800/60'; missMarker = true;
      } else if (opponentShip) {
        cls = SHIP_COLORS[opponentShip] + ' opacity-50';
      } else if (isMyTurn) {
        cls = 'bg-sky-100 dark:bg-sky-900/40 hover:bg-indigo-200 dark:hover:bg-indigo-800/50 cursor-crosshair';
        canFire = true;
      } else {
        cls = 'bg-sky-100 dark:bg-sky-900/40';
      }
      return { row, col, key, cls, hitMarker, missMarker, canFire };
    });
  });

  function handlePlacementClick(row, col) {
    if (iAmReady) return;

    // Click on a placed ship → remove it
    if (myShipCellMap[`${row},${col}`]) {
      onAction({ type: 'remove', row, col });
      placementError = null;
      return;
    }

    if (!selectedDef) return;

    const cells = Array.from({ length: selectedDef.size }, (_, i) =>
      horizontal ? [row, col + i] : [row + i, col]
    );

    if (!cells.every(([r, c]) => r >= 0 && r < 10 && c >= 0 && c < 10)) {
      showError('games.battleship.error_out_of_bounds');
      return;
    }

    const occupied = new Set(myShips.flatMap(s => s.cells.map(([r, c]) => `${r},${c}`)));
    const buffer = shipBufferZone(myShips);

    if (cells.some(([r, c]) => occupied.has(`${r},${c}`) || buffer.has(`${r},${c}`))) {
      showError('games.battleship.error_touching');
      return;
    }

    onAction({ type: 'place', ship: selectedDef.type, row, col, horizontal });
  }

  function handleFireClick(row, col) {
    if (!isMyTurn || myShotMap[`${row},${col}`] !== undefined) return;
    onAction({ type: 'fire', row, col });
  }

  // Pointer-event handlers for the placement grid.
  // onpointerenter fires for mouse hover and initial touch contact.
  // onpointermove + elementFromPoint tracks the finger as it drags across cells.
  // onpointerup fires on release for both mouse click and touch lift — no ghost
  // click possible because we never use onclick for placement.

  function cellFromPoint(x, y) {
    const el = document.elementFromPoint(x, y);
    const r = el?.dataset.row, c = el?.dataset.col;
    return r !== undefined && c !== undefined ? [+r, +c] : null;
  }

  function handleGridPointerMove(e) {
    if (e.pointerType === 'mouse') return; // mouse hover handled by onpointerenter
    const cell = cellFromPoint(e.clientX, e.clientY);
    if (cell) hoverCell = cell;
  }

  function handleGridPointerUp(e) {
    if (e.button !== 0) return; // ignore right- / middle-click
    if (hoverCell) handlePlacementClick(hoverCell[0], hoverCell[1]);
  }
</script>

<div class="select-none">
  {#if phase === 'placement'}
    {#if iAmReady}
      <div class="flex flex-col gap-4">
        <p class="text-sm text-gray-500 dark:text-gray-400">{$_('games.battleship.waiting_opponent_placement')}</p>
        <div class="grid grid-cols-10 gap-[2px] bg-sky-300 dark:bg-sky-700 border-2 border-sky-300 dark:border-sky-700 w-fit">
          {#each placementCells as cell}
            <div class="w-6 h-6 {cell.cls}"></div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="flex flex-col gap-4">
        <h2 class="font-semibold">{$_('games.battleship.place_your_fleet')}</h2>

        <!-- Ship selector -->
        <div class="flex flex-wrap gap-2">
          {#each SHIP_DEFS as def}
            {@const numPlaced = placedCounts[def.type] ?? 0}
            {@const fullyPlaced = numPlaced >= def.count}
            {@const remaining = def.count - numPlaced}
            <button
              class="flex items-center gap-1.5 px-2 py-1 rounded border text-sm transition-colors
                     {fullyPlaced
                       ? 'opacity-40 line-through border-gray-200 dark:border-gray-700 cursor-default'
                       : selectedDef?.type === def.type
                         ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30'
                         : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400'}"
              disabled={fullyPlaced}
              onclick={() => { if (!fullyPlaced) selectedType = def.type; }}
            >
              <span class="inline-block w-3 h-3 rounded-sm {SHIP_COLORS[def.type]}"></span>
              {$_(`games.battleship.ship_${def.type}`)} ({def.size}){#if !fullyPlaced && def.count > 1} ×{remaining}{/if}
            </button>
          {/each}
        </div>

        <!-- Orientation toggle -->
        <div class="flex gap-2 text-sm">
          <button
            class="px-3 py-1 rounded border {horizontal ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 dark:border-gray-600'}"
            onclick={() => { horizontal = true; }}
          >{$_('games.battleship.horizontal')} ↔</button>
          <button
            class="px-3 py-1 rounded border {!horizontal ? 'bg-indigo-600 text-white border-indigo-600' : 'border-gray-300 dark:border-gray-600'}"
            onclick={() => { horizontal = false; }}
          >{$_('games.battleship.vertical')} ↕</button>
        </div>

        <!-- Placement grid -->
        <div
          class="grid grid-cols-10 gap-[2px] bg-sky-300 dark:bg-sky-700 border-2 border-sky-300 dark:border-sky-700 w-fit"
          role="grid"
          aria-label={$_('games.battleship.place_your_fleet')}
          onpointerleave={() => { hoverCell = null; }}
          onpointermove={handleGridPointerMove}
          onpointerup={handleGridPointerUp}
        >
          {#each placementCells as cell}
            <button
              class="w-6 h-6 transition-colors {cell.cls}"
              aria-label="Row {cell.row + 1}, column {cell.col + 1}"
              data-row={cell.row}
              data-col={cell.col}
              onpointerenter={() => { hoverCell = [cell.row, cell.col]; }}
            ></button>
          {/each}
        </div>

        <!-- Error / hint -->
        {#if placementError}
          <p class="text-sm text-red-600 dark:text-red-400">{$_(placementError)}</p>
        {:else}
          <p class="text-xs text-gray-400 dark:text-gray-500">{$_('games.battleship.remove_hint')}</p>
        {/if}
      </div>
    {/if}
  {:else if phase === 'battle'}
    <div class="flex flex-col gap-5">
      <p class="text-sm font-medium">
        {#if isMyTurn}
          <span class="text-indigo-700 dark:text-indigo-400">{$_('games.battleship.your_turn_fire')}</span>
        {:else}
          <span class="text-gray-500 dark:text-gray-400">{$_('games.battleship.waiting_for_fire')}</span>
        {/if}
      </p>

      <div class="flex flex-col gap-6 sm:flex-row sm:gap-8">
        <!-- Enemy Waters -->
        <div>
          <h3 class="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300">{$_('games.battleship.enemy_waters')}</h3>
          <div class="grid grid-cols-10 gap-[2px] bg-sky-300 dark:bg-sky-700 border-2 border-sky-300 dark:border-sky-700 w-fit">
            {#each targetCells as cell}
              <button
                class="w-6 h-6 flex items-center justify-center transition-colors {cell.cls}"
                onclick={() => handleFireClick(cell.row, cell.col)}
                disabled={!cell.canFire}
              >
                {#if cell.hitMarker}<span class="text-white text-[10px] font-bold leading-none">✕</span>
                {:else if cell.missMarker}<span class="inline-block w-2 h-2 rounded-full bg-slate-400 dark:bg-slate-400"></span>{/if}
              </button>
            {/each}
          </div>
        </div>

        <!-- Your Fleet -->
        <div>
          <h3 class="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300">{$_('games.battleship.your_fleet')}</h3>
          <div class="grid grid-cols-10 gap-[2px] bg-sky-300 dark:bg-sky-700 border-2 border-sky-300 dark:border-sky-700 w-fit">
            {#each myGridCells as cell}
              <div class="w-6 h-6 flex items-center justify-center {cell.cls}">
                {#if cell.hitMarker}<span class="text-white text-[10px] font-bold leading-none">✕</span>
                {:else if cell.missMarker}<span class="text-sky-400 text-[10px] leading-none">·</span>{/if}
              </div>
            {/each}
          </div>
        </div>
      </div>

      {#if (state.sunk_opponent?.length ?? 0) > 0 || (state.sunk_my?.length ?? 0) > 0}
        <div class="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          {#if state.sunk_opponent?.length > 0}
            <p>{$_('games.battleship.sunk_enemy')}: {state.sunk_opponent.map(t => $_(`games.battleship.ship_${t}`)).join(', ')}</p>
          {/if}
          {#if state.sunk_my?.length > 0}
            <p>{$_('games.battleship.sunk_yours')}: {state.sunk_my.map(t => $_(`games.battleship.ship_${t}`)).join(', ')}</p>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>
