import { escapeHtml as esc, faction, label, terrainSprites, unitSprites } from './presentation.js';

/** Small DOM view/controller. No simulation, pathfinding or optimistic mutation. */
export function mountGame(root, api) {
  let state = null;
  let selectedTile = null;
  let selectedUnitId = null;
  let selectedCityId = null;
  let busy = false;
  let busyMessage = '';
  let error = '';
  let notice = '';
  let cityName = '';
  let pending = Promise.resolve();

  const unit = () => state?.units.find((u) => u.id === selectedUnitId);
  const city = () => state?.cities.find((c) => c.id === selectedCityId);
  const active = () => state?.players.find((p) => p.id === state.game.activePlayerId);
  const playing = () => state?.game.status === 'started' && active()?.controller !== 'ai';
  const versusAi = () => state?.players.some((p) => p.controller === 'ai');
  const modeLabel = () => Object.values(state?.aiProviders || {}).includes('ollama')
    ? 'Human vs LLM' : versusAi() ? 'Human vs Heuristic AI' : 'Hot-seat';
  const at = (piece, tile) => tile && piece.x === tile.x && piece.y === tile.y;
  const disabled = (condition = false) => busy || condition ? 'disabled' : '';
  const sprite = (className) => `<span aria-hidden="true" class="sprite ${className}"></span>`;

  function clearSelection() {
    selectedUnitId = null;
    selectedCityId = null;
    selectedTile = null;
    cityName = '';
  }

  function reconcile() {
    if (!unit()) selectedUnitId = null;
    if (!city()) selectedCityId = null;
    if (unit()) selectedTile = { x: unit().x, y: unit().y };
  }

  function run(action, success = '', loading = 'Resolving…') {
    if (busy) return pending;
    busy = true;
    busyMessage = loading;
    error = '';
    render();
    pending = (async () => {
      try {
        const previousActor = state?.game.activePlayerId;
        const previousTurn = state?.game.turn;
        state = await action();
        if (state.game.activePlayerId !== previousActor || state.game.turn !== previousTurn) clearSelection();
        reconcile();
        notice = success;
      } catch (failure) {
        if (failure.code === 'no_game') {
          state = null;
          clearSelection();
        } else {
          error = failure.message || 'The action failed. Please retry.';
        }
      } finally {
        busy = false;
        render();
      }
    })();
    return pending;
  }

  function pieceButton(piece, kind, compact = false) {
    const selected = kind === 'unit' ? piece.id === selectedUnitId : piece.id === selectedCityId;
    const name = kind === 'unit' ? label(piece.type) : piece.name;
    return `<button type="button" class="piece ${kind} ${compact ? 'compact' : ''} ${faction(piece.ownerId).className} ${selected ? 'selected-piece' : ''}"
      data-action="${kind}" data-id="${esc(piece.id)}" aria-pressed="${selected}"
      aria-label="${esc(name)} ${esc(piece.id)}, ${esc(faction(piece.ownerId).name)}, at ${piece.x}, ${piece.y}"
      title="${esc(name)} · ${esc(faction(piece.ownerId).name)} · ${esc(piece.id)}" ${disabled()}>
      ${sprite(kind === 'unit' ? unitSprites[piece.type] : 'sprite-city')}
      ${kind === 'city' ? `<span class="city-label">${esc(piece.name)} <b>${piece.population}</b></span>` : `<span class="faction-badge">${esc(piece.ownerId)}</span>`}
    </button>`;
  }

  function renderMap() {
    return `<div class="map-scroll"><div class="map" aria-label="World map" style="--columns:${state.map.width};--rows:${state.map.height}">
      ${state.map.tiles.map((tile) => {
        const units = state.units.filter((u) => at(u, tile));
        const town = state.cities.find((c) => at(c, tile));
        const selected = Boolean(at(tile, selectedTile));
        return `<div class="map-cell ${faction(tile.ownerId).className} ${tile.ownerId ? 'owned' : ''} ${selected ? 'selected-tile' : ''}"
          style="grid-column:${tile.x - state.map.origin.x + 1};grid-row:${tile.y - state.map.origin.y + 1}">
          <button type="button" id="tile-${tile.x}-${tile.y}" class="tile sprite ${terrainSprites[tile.terrain]}" data-action="tile" data-x="${tile.x}" data-y="${tile.y}"
            aria-label="${label(tile.terrain)} at ${tile.x}, ${tile.y}${tile.ownerId ? `, ${esc(faction(tile.ownerId).name)}` : ''}" aria-pressed="${selected}" ${disabled()}></button>
          ${town ? pieceButton(town, 'city') : ''}
          <div class="map-units ${town ? 'with-city' : ''}">${units.slice(0, 2).map((u) => pieceButton(u, 'unit', units.length > 1 || Boolean(town))).join('')}</div>
          ${units.length > 2 ? `<button class="stack-count" data-action="inspect" data-x="${tile.x}" data-y="${tile.y}" aria-label="Inspect all ${units.length} units at ${tile.x}, ${tile.y}" ${disabled()}>+${units.length - 2}</button>` : ''}
        </div>`;
      }).join('')}
    </div></div>`;
  }

  function renderUnit() {
    const selected = unit();
    if (!selected) return '';
    const owned = selected.ownerId === active()?.id;
    const targets = state.units.filter((u) => at(u, selectedTile) && u.ownerId !== selected.ownerId);
    return `<section class="panel ${faction(selected.ownerId).className}" aria-label="Selected unit">
      <p class="eyebrow">${esc(faction(selected.ownerId).name)} · ${esc(selected.id)}</p>
      <h2>${sprite(unitSprites[selected.type])}${label(selected.type)}</h2>
      <dl class="stats"><div><dt>Health</dt><dd>${selected.hp} HP</dd></div><div><dt>Movement</dt><dd>${selected.movesRemaining} / ${selected.maxMovement}</dd></div><div><dt>Position</dt><dd>${selected.x}, ${selected.y}</dd></div></dl>
      ${owned && playing() ? `<p class="hint">Click terrain to move. Click an enemy to choose an attack target.</p>
        ${selected.attackRange > 0 ? `<p class="hint">Attack range: ${selected.attackRange} tile${selected.attackRange === 1 ? '' : 's'}.</p>` : ''}
        ${targets.length ? `<div class="targets"><h3>Enemy targets at ${selectedTile.x}, ${selectedTile.y}</h3>${targets.map((target) => `<button data-action="attack" data-id="${esc(target.id)}" ${disabled(selected.movesRemaining === 0 || selected.attackRange === 0)}>Attack ${label(target.type)} · ${esc(target.id)} · ${target.hp} HP</button>`).join('')}</div>` : ''}
        ${selected.type === 'settler' ? `<form id="found-city-form"><label for="city-name">City name</label><div class="form-row"><input id="city-name" name="cityName" maxlength="80" required value="${esc(cityName)}" placeholder="Name your settlement" ${disabled(selected.movesRemaining === 0)}><button type="submit" ${disabled(selected.movesRemaining === 0)}>Found City</button></div></form>` : ''}
      ` : '<p class="hint">Inspecting this faction. Its units can act during its activation.</p>'}
    </section>`;
  }

  function renderCity() {
    const selected = city();
    if (!selected) return '';
    const owned = selected.ownerId === active()?.id;
    return `<section class="panel ${faction(selected.ownerId).className}" aria-label="Selected city">
      <p class="eyebrow">${esc(faction(selected.ownerId).name)} · ${esc(selected.id)}</p>
      <h2>${sprite('sprite-city')}${esc(selected.name)}</h2>
      <dl class="stats"><div><dt>Population</dt><dd>${selected.population}</dd></div><div><dt>Food stored</dt><dd>${selected.foodStored}</dd></div><div><dt>Production</dt><dd>${selected.productionStored}</dd></div></dl>
      <p>Building: <strong>${label(selected.productionTarget)}</strong>${selected.productionRemaining === null ? '' : ` · ${selected.productionRemaining} remaining / ${selected.productionCost} cost`}</p>
      ${owned && playing() ? `<label for="production">City production</label><select id="production" ${disabled()}><option value="">No production target</option>${selected.availableProduction.map((choice) => `<option value="${choice.unitType}" ${selected.productionTarget === choice.unitType ? 'selected' : ''}>${label(choice.unitType)} · ${choice.cost} production</option>`).join('')}</select><p class="hint">Choose or clear a target. Construction resolves when you end your turn; choose again after completion.</p>` : ''}
    </section>`;
  }

  function renderTile() {
    if (!selectedTile) return '<section class="panel"><h2>Explore the world</h2><p class="hint">Select a unit, a city, or a tile. Your two starting pieces share a tile; both are selectable.</p></section>';
    const tile = state.map.tiles.find((t) => at(t, selectedTile));
    const units = state.units.filter((u) => at(u, selectedTile));
    const town = state.cities.find((c) => at(c, selectedTile));
    return `<section class="panel tile-details"><h3>${label(tile?.terrain)} · ${selectedTile.x}, ${selectedTile.y}</h3><p class="hint">${esc(faction(tile?.ownerId).name)}</p>
      ${town ? `<button data-action="city" data-id="${esc(town.id)}" ${disabled()}>Inspect ${esc(town.name)} · population ${town.population}</button>` : ''}
      ${units.map((u) => `<button class="roster-button ${faction(u.ownerId).className}" data-action="unit" data-id="${esc(u.id)}" ${disabled()}>${sprite(unitSprites[u.type])}<span>${label(u.type)} · ${esc(u.id)}<small>${esc(faction(u.ownerId).name)} · ${u.hp} HP</small></span></button>`).join('')}
      <button class="quiet" data-action="deselect" ${disabled()}>Clear selection</button>
    </section>`;
  }

  function renderResearch() {
    const player = active();
    if (!player || !playing()) return '';
    return `<section class="panel" aria-label="Research"><p class="eyebrow">Council of knowledge</p><h2>Research <span class="number">${player.scienceStored}</span></h2>
      <p>${label(player.researchTarget)}${player.researchRemaining === null ? '' : ` · ${player.researchRemaining} science remaining / ${player.researchCost} cost`}</p>
      <label for="research">Research target</label><select id="research" ${disabled()}><option value="">No research target</option>${player.availableResearch.map((choice) => `<option value="${choice.technology}" ${player.researchTarget === choice.technology ? 'selected' : ''}>${label(choice.technology)} · ${choice.cost} science</option>`).join('')}</select>
      <p class="hint">Known: ${player.researchedTechnologies.map(label).join(', ')}. Stored science is kept when switching or clearing.</p>
    </section>`;
  }

  function render() {
    const focusId = root.contains(root.ownerDocument.activeElement) ? root.ownerDocument.activeElement?.id : null;
    const player = active();
    root.innerHTML = `<header class="masthead"><div><p class="eyebrow">A small world. An unwritten history.</p><h1>Aether, Iron <span>&amp;</span> Glory</h1></div><span class="edition">Deterministic demo · ${modeLabel()}</span></header>
      <div class="message-bar"><p role="${error ? 'alert' : 'status'}" class="${error ? 'error' : ''}">${esc(error || (busy ? busyMessage : notice || 'Two factions. One shared world.'))}</p><button class="quiet" data-action="refresh" ${disabled()}>Refresh</button></div>
      ${!state ? `<section class="welcome"><div class="crest">AIG</div><p class="eyebrow">The first expedition</p><h2>A world ready to settle</h2><p>Lead two rival factions across a fixed world.<br>Found cities, raise armies, and take turns shaping their history.</p><button class="primary" data-action="demo" ${disabled()}>New Demo Game · Hot-seat</button><button class="primary" data-action="demo-ai" ${disabled()}>Human vs Heuristic AI</button><button class="quiet" data-action="demo-llm" ${disabled()}>Human vs LLM</button><p class="hint">Play hot-seat with two people, command both sides, or face heuristic or LLM strategy.</p></section>` : `
      <section class="hud ${faction(player?.id).className}" aria-label="Game status"><div class="turn"><small>Turn</small><strong>${state.game.turn}</strong></div><div class="active-faction"><small>${state.game.status === 'started' ? 'Active faction' : state.game.status === 'terminal' ? 'Game ended' : 'Awaiting your command'}</small><strong>${player ? esc(faction(player.id).name) : 'Demo ready'}</strong></div><div><small>Treasury</small><strong>${player?.gold ?? '—'} <span>gold</span></strong></div><div><small>Science · ${label(player?.researchTarget)}</small><strong>${player?.scienceStored ?? '—'}</strong></div><button class="primary" data-action="${playing() ? 'end' : 'start'}" ${disabled(state.game.status === 'terminal' || active()?.controller === 'ai')}>${state.game.status === 'terminal' ? 'Game ended' : active()?.controller === 'ai' ? 'AI turn...' : playing() ? 'End Turn' : 'Start Game'}</button></section>
      <div class="game-layout"><section class="world-frame" aria-label="Game board"><div class="world-heading"><h2>The known world</h2><span>${state.map.width} × ${state.map.height} · square grid</span></div>${renderMap()}<div class="world-footer"><span class="faction-a">A · Amber League</span><span class="faction-b">B · Azure Union</span><span>Click pieces to inspect · Esc clears</span></div></section>
      <aside aria-label="Orders and details">${state.game.status === 'pre_game' ? '<section class="panel"><h2>Prepare the expedition</h2><p>Amber acts first. Press Start Game to begin. Each faction starts with a Settler and a Warrior.</p></section>' : ''}${renderUnit()}${renderCity()}${renderResearch()}${renderTile()}</aside></div>
      <section class="forces" aria-label="Active faction forces"><h2>${player ? `${esc(faction(player.id).name)} · forces` : 'Expedition roster'}</h2><div>${state.units.filter((u) => !player || u.ownerId === player.id).map((u) => `<button class="roster-button ${faction(u.ownerId).className}" data-action="unit" data-id="${esc(u.id)}" aria-pressed="${u.id === selectedUnitId}" ${disabled()}>${sprite(unitSprites[u.type])}<span>${label(u.type)} <small>${esc(u.id)} · ${u.movesRemaining}/${u.maxMovement} moves · ${u.x}, ${u.y}</small></span></button>`).join('') || '<p class="hint">No remaining units. Select a city to choose production.</p>'}</div></section>
      <footer class="session-footer"><span>${modeLabel()} · ${state.cities.length} cities · ${state.units.length} units</span><button class="quiet" data-action="demo" ${disabled()}>Reset Demo · Hot-seat</button><button class="quiet" data-action="demo-ai" ${disabled()}>Human vs Heuristic AI</button><button class="quiet" data-action="demo-llm" ${disabled()}>Human vs LLM</button></footer>`}`;
    if (focusId) root.ownerDocument.getElementById(focusId)?.focus({ preventScroll: true });
  }

  function selectUnit(id) {
    const clicked = state.units.find((u) => u.id === id);
    if (!clicked) return;
    // Enemy clicks keep the selected attacker and reveal every target in the stack.
    if (!(playing() && unit()?.ownerId === active()?.id && clicked.ownerId !== active()?.id)) {
      selectedUnitId = id;
      selectedCityId = null;
      cityName = '';
    }
    selectedTile = { x: clicked.x, y: clicked.y };
    render();
  }

  function click(event) {
    const button = event.target.closest('button[data-action]');
    if (!button || !root.contains(button) || button.disabled || busy) return;
    const { action, id } = button.dataset;
    if (action === 'demo') return run(async () => { const result = await api.createDemoGame(); clearSelection(); return result; }, 'A fresh expedition awaits. Press Start Game.');
    if (action === 'demo-ai') return run(async () => { const result = await api.createAiDemoGame(); clearSelection(); return result; }, 'Human vs AI ready. Press Start Game.');
    if (action === 'demo-llm') return run(async () => { const result = await api.createLlmDemoGame(); clearSelection(); return result; }, 'Human vs LLM ready. Press Start Game.');
    if (action === 'refresh') return run(api.getGame);
    if (action === 'start') return run(api.startGame, 'Amber League takes the first activation.');
    if (action === 'end') return run(api.endActivation,
      versusAi() ? 'AI turn complete. Your next activation is ready.' : 'Activation complete. Pass control to the active faction.',
      versusAi() ? 'AI turn...' : 'Resolving…');
    if (action === 'deselect') { clearSelection(); render(); return; }
    if (action === 'unit') { selectUnit(id); return; }
    if (action === 'city') {
      selectedCityId = id;
      selectedUnitId = null;
      selectedTile = { x: city().x, y: city().y };
      render();
      return;
    }
    if (action === 'attack') return run(() => api.attackUnit(selectedUnitId, id), 'Attack resolved.');
    if (action === 'tile' || action === 'inspect') {
      selectedTile = { x: Number(button.dataset.x), y: Number(button.dataset.y) };
      const selected = unit();
      if (action === 'tile' && playing() && selected?.ownerId === active()?.id && !at(selected, selectedTile)) {
        if (state.units.some((u) => at(u, selectedTile) && u.ownerId !== selected.ownerId)) { render(); return; }
        return run(() => api.moveUnit(selected.id, selectedTile.x, selectedTile.y), 'Unit moved.');
      }
      if (action === 'tile') { selectedUnitId = null; selectedCityId = null; }
      render();
    }
  }

  function change(event) {
    if (busy) return;
    // Capture values before run() replaces the controls during its loading render.
    const value = event.target.value || null;
    if (event.target.id === 'production') run(() => api.setProduction(selectedCityId, value), 'Production orders updated.');
    if (event.target.id === 'research') run(() => api.setResearch(value), 'Research orders updated.');
  }
  function input(event) {
    if (event.target.id === 'city-name') cityName = event.target.value;
  }
  function submit(event) {
    if (event.target.id !== 'found-city-form') return;
    event.preventDefault();
    const settler = unit();
    if (!settler || busy) return;
    run(async () => {
      const result = await api.foundCity(settler.id, cityName);
      selectedCityId = result.cities.find((c) => at(c, settler))?.id ?? null;
      selectedUnitId = null;
      cityName = '';
      return result;
    }, 'City founded. Choose its production.');
  }
  function keydown(event) {
    if (event.key === 'Escape' && !busy) { clearSelection(); render(); }
  }
  root.addEventListener('click', click);
  root.addEventListener('change', change);
  root.addEventListener('input', input);
  root.addEventListener('submit', submit);
  root.addEventListener('keydown', keydown);
  const ready = run(api.getGame);
  return {
    ready,
    whenIdle: () => pending,
    destroy() {
      root.removeEventListener('click', click);
      root.removeEventListener('change', change);
      root.removeEventListener('input', input);
      root.removeEventListener('submit', submit);
      root.removeEventListener('keydown', keydown);
    },
  };
}
