import { escapeHtml as esc } from './presentation.js';
import { arenaIcon } from './arena-icons.js';

/** Manual/AI controller: all destinations, targets, HP and AP come from Python. */
export function mountArena(root, api) {
  let state = null;
  let selectedId = null;
  let mode = null;
  let busy = false;
  let aiPending = false;
  let error = '';
  let pending = Promise.resolve();
  const selected = () => state?.units.find((u) => u.id === selectedId);
  const playerName = (id) => state?.players.find((p) => p.id === id)?.name || id;
  const disabled = (condition = false) => busy || condition ? 'disabled' : '';
  const at = (piece, tile) => piece.x === tile.x && piece.y === tile.y;

  function render() {
    const unit = selected();
    const terminal = state?.winner_player_id != null;
    const cannotAct = terminal || (state?.controllers?.[state.active_player_id] && state.controllers[state.active_player_id] !== 'human');
    root.innerHTML = `<section class="arena-view" aria-label="Arena">
      <header><h1>Arena</h1><p>Perfect information fantasy tactics · manual play or AI opponent</p>
      <button data-arena="demo" ${disabled()}>${state ? 'New Arena Demo' : 'Arena Demo'}</button>
      <button data-arena="demo-ai" ${disabled()}>Arena Human vs Heuristic</button>
      <button data-arena="demo-ollama" ${disabled()}>Arena Human vs Qwen</button>
      <button data-arena="demo-openai" ${disabled()}>Arena Human vs OpenAI (Luna)</button>
      <button data-arena="demo-configured" ${disabled()}>Arena Human vs Configured AI</button>
      <button data-arena="refresh" ${disabled()}>Refresh</button></header>
      ${error ? `<p role="alert">${esc(error)}</p>` : ''}
      ${busy ? `<p role="status">${aiPending ? 'AI turn...' : 'Resolving…'}</p>` : ''}
      ${(state?.ai_turns || []).map((t) => `<div class="arena-ai-summary"><strong>${esc(t.inference?.actual_provider || t.provider_type)}: ${t.ap_spent} AP</strong>
        ${t.inference?.fallback_used ? `<p>Heuristic fallback from ${esc(t.inference.requested_provider)} (${esc(t.inference.error_category)})</p>` : ''}
        <ul>${t.actions_attempted.map((a) => `<li>${esc(a.action.unit_id)} ${esc(a.action.type)} ${esc(a.action.target_id || JSON.stringify(a.action.destination || a.action.target_position))}${a.executed ? '' : ' (invalid; turn truncated)'}</li>`).join('')}</ul></div>`).join('')}
      ${state ? `<p class="arena-status" role="status">${terminal
        ? `${esc(playerName(state.winner_player_id))} wins!`
        : `${esc(playerName(state.active_player_id))} · Turn ${state.turn} · ${state.action_points_remaining} / 5 AP`}</p>
      <button data-arena="end" ${disabled(cannotAct)}>End Turn</button>
      <div class="arena-layout"><div class="arena-scroll"><div class="arena-board" aria-label="Arena board">
      ${state.board.tiles.map((tile) => {
        const piece = state.units.find((u) => at(u, tile)) || state.cores.find((c) => at(c, tile));
        const kind = piece?.unit_type || (piece ? 'core' : tile.terrain === 'blocked' ? 'blocked' : null);
        const legal = mode && unit && ((mode === 'move' || mode === 'fireball')
          ? unit.actions[mode].some((p) => at(p, tile)) : piece && unit.actions[mode].includes(piece.id));
        const description = `${tile.x}, ${tile.y}: ${tile.terrain}${tile.bonus ? `, ${tile.bonus}` : ''}${piece ? `, ${playerName(piece.owner_id)} ${kind}, HP ${piece.hp}/${piece.max_hp}${piece.status === 'downed' ? ', DOWNED' : ''}` : ''}`;
        return `<button class="arena-tile arena-${tile.terrain} ${tile.bonus ? `arena-${tile.bonus}` : ''} ${piece ? `arena-team-${piece.owner_id === state.players[0].id ? 'blue' : 'red'}` : ''} ${piece?.status === 'downed' ? 'arena-downed' : ''} ${piece?.id === selectedId ? 'arena-selected' : ''} ${legal ? 'arena-legal' : ''}"
          data-arena="tile" data-x="${tile.x}" data-y="${tile.y}" aria-label="${esc(description)}" title="${esc(description)}" ${disabled(cannotAct)}>
          <span class="arena-coordinate">${tile.x},${tile.y}</span>
          ${tile.bonus ? `<span class="arena-bonus">${arenaIcon(tile.bonus)}${esc(tile.bonus)}</span>` : ''}
          ${kind ? arenaIcon(kind) : ''}${piece ? `<strong>${esc(kind)}</strong>${piece.status === 'downed' ? '<span class="arena-downed-badge">DOWNED</span>' : ''}<span>${piece.hp}/${piece.max_hp} HP</span>` : ''}
        </button>`;
      }).join('')}</div></div>
      <aside class="arena-details"><h2>Selected unit</h2>${unit
        ? `<p>${esc(playerName(unit.owner_id))} · <strong>${esc(unit.unit_type)}</strong><br>${unit.hp}/${unit.max_hp} HP | ${esc(unit.status.toUpperCase())}</p>
           <p>Move ${unit.stats.move_range} · Attack ${unit.stats.damage} / range ${unit.stats.attack_range}${unit.stats.heal_amount ? `<br>Heal ${unit.stats.heal_amount} / range ${unit.stats.heal_range}` : ''}</p>
           <div class="arena-actions">${Object.keys(unit.abilities).map((action) => `<button data-arena="mode" data-mode="${action}" aria-pressed="${mode === action}" ${disabled(cannotAct || !unit.actions[action].length)}>${action.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())} (${unit.abilities[action].ap_cost} AP)</button>`).join('')}
           <button data-arena="cancel" ${disabled()}>Cancel action</button></div>
           <p>${mode ? `Choose a highlighted ${(mode === 'move' || mode === 'fireball') ? 'destination' : 'target'} for ${mode}.` : 'Choose an action.'}</p>`
        : '<p>Select an active-team unit to act. Select any unit to inspect it.</p>'}
        <p>Basic actions, Bash and Finish cost 1 AP. Snipe, Fireball and Revive cost 2 AP. A unit may act repeatedly. At 0 AP, choose End Turn.</p>
        <p>Win by destroying the enemy Core or downing every enemy unit. If Fireball downs both teams, the casting team loses.</p>
        <p>POWER: +2 attack damage<br>WARD: −2 incoming unit damage (minimum 1)<br>SIEGE: +4 damage to Core</p>
        <p>Eight-direction movement. Units, Cores and ruins block movement. Ruins block ranged line of sight; movement cannot cut blocked corners. Clerics may heal themselves.</p><p>DOWNED units occupy their tiles. Finish an adjacent downed enemy to remove it; Clerics can Revive a friendly body at 5 HP within range 2. Revived units may act immediately.</p><p>Shield Bash: 4 damage and a one-tile shove. Snipe: 8 damage, range 4. Fireball: 4 damage to every active unit within one tile of impact, including allies and the caster. Select a highlighted impact tile within range 2. Specials cannot damage Cores.</p>
      </aside></div>` : '<p>Create an Arena Demo to begin. Blue moves first.</p>'}
    </section>`;
  }

  function run(action, reset = false, expectingAi = false) {
    if (busy) return pending;
    busy = true;
    aiPending = expectingAi;
    error = '';
    render();
    pending = (async () => {
      try {
        const previousActor = state?.active_player_id;
        state = await action();
        if (reset || previousActor !== state.active_player_id || !selected()) selectedId = null;
        mode = null;
      } catch (failure) {
        if (failure.code === 'no_game') { state = null; selectedId = null; mode = null; }
        else error = failure.message || 'Arena action failed.';
      } finally { busy = false; aiPending = false; render(); }
    })();
    return pending;
  }

  function onClick(event) {
    const button = event.target.closest('[data-arena]');
    if (!button || !root.contains(button) || button.disabled || busy) return;
    const action = button.dataset.arena;
    if (action === 'demo') return run(() => api.createDemo(), true);
    if (action === 'demo-ai') return run(() => api.createAiDemo(), true);
    if (['demo-ollama', 'demo-openai', 'demo-configured'].includes(action)) return run(() => api.createAiDemo(action.slice(5)), true);
    if (action === 'refresh') return run(() => api.getGame());
    if (action === 'end') return run(() => api.command('end_turn', state.active_player_id), false,
      Object.values(state.controllers || {}).some((c) => c !== 'human'));
    if (action === 'cancel') { mode = null; render(); return; }
    if (action === 'mode') { mode = button.dataset.mode; render(); return; }
    if (action !== 'tile' || !state || state.winner_player_id) return;
    const position = { x: Number(button.dataset.x), y: Number(button.dataset.y) };
    const piece = state.units.find((u) => at(u, position)) || state.cores.find((c) => at(c, position));
    const unit = selected();
    if (mode && unit) {
      const details = { unit_id: unit.id };
      const legal = (mode === 'move' || mode === 'fireball') ? unit.actions[mode].some((p) => at(p, position))
        : piece && unit.actions[mode].includes(piece.id);
      if (!legal) { error = 'Choose a highlighted legal target, or cancel the action to select another unit.'; render(); return; }
      if (mode === 'move') details.destination = position;
      else if (mode === 'fireball') details.target_position = position;
      else details.target_id = piece.id;
      return run(() => api.command(mode, state.active_player_id, details));
    }
    selectedId = piece?.unit_type ? piece.id : null;
    error = '';
    render();
  }

  root.addEventListener('click', onClick);
  run(() => api.getGame());
  return { whenIdle: () => pending, destroy: () => root.removeEventListener('click', onClick) };
}
