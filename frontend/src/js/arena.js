import { abilityHelp, rulesHelp } from './arena-help.js';
import { escapeHtml as esc } from './presentation.js';
import { renderArenaPiece, unitVisual } from './arena-unit-visuals.js';
import { actionIcon } from './arena-action-icons.js';
import { arenaIcon } from './arena-icons.js';
import { ArenaPresentationEngine } from './arena-presentation.js';
import { ArenaAnimationDriver, createArenaRegistry } from './arena-animation.js';

/** Manual/AI controller: all destinations, targets, HP and AP come from Python. */
export function mountArena(root, api, options = {}) {
  let state = null;
  let authoritative = null;
  let playing = false;
  let generation = 0;
  let destroyed = false;
  let actionGroup = null;
  const driver = options.driver || new ArenaAnimationDriver(root, options);
  const engine = new ArenaPresentationEngine({ registry: options.registry || createArenaRegistry(), driver,
    getState: () => state,
    setState: (value, { effects } = {}) => { state = value; if (!effects) render(); },
    onBusy: (value) => { playing = value; },
    onGroup: (value) => { actionGroup = value; },
    onEvent: (event) => {
      state = { ...state, battle_log: [...(state.battle_log || []), ...(event.log ? [event.log] : [])].slice(-60) };
      render();
    }, report: (...args) => {
      error = 'Playback could not be completed. Refresh the page; if this persists, restart npm run dev.';
      (options.report || console.error)(...args);
    } });
  let selectedId = null;
  let coordinates = options.coordinates ?? false;
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
    if (destroyed) return;
    const unit = selected();
    const terminal = state?.winner_player_id != null;
    const controllers = Object.values(state?.controllers || {});
    const offlineAi = controllers.some((c) => ['heuristic_ai', 'heuristic-v2_ai'].includes(c));
    const hasAi = controllers.some((c) => c !== 'human');
    const matchLabel = hasAi ? (offlineAi ? (controllers.includes('heuristic-v2_ai') ? 'Human vs Heuristic V2 \u00b7 You are Blue' : 'Human vs Heuristic \u00b7 You are Blue') : controllers.includes('openai_ai') ? 'OpenAI Luna \u00b7 You are Blue' : 'AI match \u00b7 You are Blue') : 'Local Match \u00b7 Control both teams';
    const cannotAct = terminal || (state?.controllers?.[state.active_player_id] && state.controllers[state.active_player_id] !== 'human');
    root.innerHTML = `<section class="arena-view" aria-label="Arena">
      <header class="arena-header"><div><p class="arena-eyebrow">Agent Strategy / Arena</p><h1>Arena</h1>
      <p>Break their Core. Protect your team.</p></div>
      <div class="arena-match-controls">
      <button data-arena="demo-openai" ${disabled()}>OpenAI Luna</button>
      ${state ? `<button data-arena="reset" ${busy && !playing ? 'disabled' : ''}>New Match</button>` : ''}
      <button data-arena="refresh" ${busy && !playing ? 'disabled' : ''}>Refresh</button></div></header>
      ${error ? `<p role="alert">${esc(error)}</p>` : ''}
      <p class="arena-playback-status" role="status">${busy ? (playing ? (actionGroup ? `AI acting · Action ${actionGroup.index} / ${actionGroup.total} · ${esc(actionGroup.events[0].actor_label)} · ${esc(actionGroup.events[0].type.replaceAll('_', ' '))}` : aiPending ? 'AI acting\u2026' : 'Playing action\u2026') : aiPending ? 'AI thinking\u2026' : 'Resolving\u2026') : '&nbsp;'}</p>
      ${state ? `<div class="arena-turnbar"><div><p class="arena-mode">${esc(matchLabel)}</p><p class="arena-status" role="status">${terminal
        ? `${esc(playerName(state.winner_player_id))} wins!`
        : `${esc(playerName(state.active_player_id))} · Turn ${state.turn} · ${state.action_points_remaining} / 5 AP`}</p>
      ${terminal ? `<p class="arena-winner">${esc(state.terminal_reason || 'Battle complete')}</p>` : `<p>${aiPending ? 'AI is taking its turn. Controls will return shortly.' : hasAi && cannotAct ? 'AI controls this turn. Refresh to check the state.' : 'Select a unit → choose an action → click a highlighted tile.'}</p>`}</div>
      <button class="arena-end" data-arena="end" ${disabled(cannotAct)}>End Turn</button></div>
      <div class="arena-layout"><div class="arena-scroll"><div class="arena-board ${coordinates ? 'arena-show-coordinates' : ''}" aria-label="Arena board"><div class="arena-overlay" aria-hidden="true"></div>
      ${state.board.tiles.map((tile) => {
        const piece = state.units.find((u) => at(u, tile)) || state.cores.find((c) => at(c, tile));
        const kind = piece?.unit_type || (piece ? 'core' : tile.terrain === 'blocked' ? 'blocked' : null);
        const legal = mode && unit && ((mode === 'move' || mode === 'fireball')
          ? unit.actions[mode].some((p) => at(p, tile)) : piece && unit.actions[mode].includes(piece.id));
        const description = `${tile.x}, ${tile.y}: ${tile.terrain}${tile.bonus ? `, ${tile.bonus}` : ''}${piece ? `, ${playerName(piece.owner_id)} ${kind}, HP ${piece.hp}/${piece.max_hp}${piece.status === 'downed' ? ', DOWNED' : ''}` : ''}`;
        return `<button class="arena-tile arena-${tile.terrain} ${tile.bonus ? `arena-${tile.bonus}` : ''} ${piece ? `arena-team-${piece.owner_id === state.players[0].id ? 'blue' : 'red'}` : ''} ${piece?.status === 'downed' ? 'arena-downed' : ''} ${piece && !piece.unit_type && piece.hp === 0 ? 'arena-core-destroyed' : ''} ${piece?.id === selectedId ? 'arena-selected' : ''} ${actionGroup?.actorId === piece?.id && piece ? 'arena-acting' : ''} ${legal ? 'arena-legal' : ''}"
          data-arena="tile" data-x="${tile.x}" data-y="${tile.y}" aria-pressed="${piece?.id === selectedId}" aria-label="${esc(description + (legal ? ', legal ' + mode + ' target' : ''))}" title="${esc(description + (legal ? ', legal ' + mode + ' target' : ''))}" ${disabled(cannotAct)}>
          <span class="arena-coordinate">${tile.x},${tile.y}</span>
          ${tile.bonus ? `<span class="arena-bonus">${arenaIcon(tile.bonus)}${esc(tile.bonus)}</span>` : ''}
          ${piece ? renderArenaPiece(piece, state.players[0].id) : kind ? arenaIcon(kind) : ''}
        </button>`;
      }).join('')}</div></div>
      <aside class="arena-details"><section class="arena-panel"><h2>Selected unit</h2>${unit
        ? `<div class="arena-selected-art arena-team-${unit.owner_id === state.players[0].id ? 'blue' : 'red'} ${unit.status === 'downed' ? 'arena-downed' : ''}">${unitVisual(unit.unit_type)}</div><p>${esc(playerName(unit.owner_id))} · <strong>${esc(unit.unit_type)}</strong><br><span data-selected-hp="${esc(unit.id)}">${unit.hp}/${unit.max_hp} HP</span> | <span data-selected-status="${esc(unit.id)}">${esc(unit.status.toUpperCase())}</span></p>
           <p>Move ${unit.stats.move_range} · Attack ${unit.stats.damage} / range ${unit.stats.attack_range}${unit.stats.heal_amount ? `<br>Heal ${unit.stats.heal_amount} / range ${unit.stats.heal_range}` : ''}</p>
           <div class="arena-actions">${Object.keys(unit.abilities).map((action) => `<div class="arena-action-option"><button data-arena="mode" data-mode="${action}" aria-pressed="${mode === action}" ${disabled(cannotAct || unit.owner_id !== state.active_player_id || unit.status !== 'active' || !unit.actions[action].length)}>${actionIcon(action)}<span>${action.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())} <small>(${unit.abilities[action].ap_cost} AP)</small></span></button>${abilityHelp(action, busy)}</div>`).join('')}
           <button data-arena="cancel" ${disabled()}>Cancel action</button></div>
           <p>${mode ? `Choose a highlighted ${(mode === 'move' || mode === 'fireball') ? 'destination' : 'target'} for ${mode}.` : 'Choose an action.'}</p>`
        : '<p>Select an active-team unit to act. Select any unit to inspect it.</p>'}
        </section><section class="arena-panel arena-legend"><h2>Board guide</h2>
        <p><b>POWER</b> +2 attack damage</p><p><b>WARD</b> −2 incoming unit damage (min 1)</p><p><b>SIEGE</b> +4 Core damage</p><p><b>Ruins</b> Impassable · block line of sight</p>
        <p><b>White outline</b> Selected unit<br><b>Gold outline</b> Legal target</p></section>
        <section class="arena-panel"><h2>Battle log</h2><ol class="arena-battle-log" aria-label="Battle log" aria-live="polite">${(state.battle_log || []).slice().reverse().map((entry) => `<li>${esc(entry.text)}</li>`).join('') || '<li>No actions yet. Blue moves first.</li>'}</ol></section>
        ${rulesHelp()}<details class="arena-panel"><summary>Development info</summary><label><input type="checkbox" data-arena="coordinates" ${coordinates ? 'checked' : ''}> Show coordinates</label><a href="/arena/presentation-lab">Presentation lab</a><p>${esc(state.rules_version || '')}<br>${esc(state.scenario_version || '')}<br>Selected: ${esc(selectedId || 'none')}</p></details>
        ${(state?.ai_turns || []).map((t) => `<details class="arena-panel arena-ai-summary"><summary>AI turn details · ${t.ap_spent} AP</summary><strong>${esc(t.inference?.actual_provider || t.provider_type)}</strong>
        ${t.inference?.fallback_used ? `<p>Heuristic fallback from ${esc(t.inference.requested_provider)} (${esc(t.inference.error_category)})</p>` : ''}
        <ul>${t.actions_attempted.map((a) => `<li>${esc(a.action.unit_id)} ${esc(a.action.type)} ${esc(a.action.target_id || JSON.stringify(a.action.destination || a.action.target_position))}${a.executed ? '' : ' (invalid; turn truncated)'}</li>`).join('')}</ul></details>`).join('')}
      </aside></div>` : '<div class="arena-welcome arena-panel"><h2>Your first skirmish</h2><p>Choose <strong>OpenAI Luna</strong> to play Blue against Luna.</p><p>Each team has four units, a Core, and 5 AP per turn. Select a unit, choose an action, then click a gold target.</p></div>'}
    </section>`;
  }

  function run(action, reset = false, expectingAi = false) {
    if (busy && !reset) return pending;
    const requestGeneration = ++generation;
    engine.cancel();
    busy = true;
    aiPending = expectingAi;
    mode = null;
    error = '';
    render();
    pending = (async () => {
      try {
        const previousActor = state?.active_player_id;
        const response = await action();
        if (destroyed || generation !== requestGeneration) return;
        const { presentation, ...finalState } = response;
        authoritative = finalState;
        if (!reset && state && presentation) await engine.play(presentation, authoritative);
        else {
          if (!reset && state && !presentation) {
            error = 'This server returned no animation sequence. Restart npm run dev and refresh the page.';
          }
          state = authoritative;
        }
        if (destroyed || generation !== requestGeneration) return;
        if (reset || previousActor !== state.active_player_id || !selected()) selectedId = null;
      } catch (failure) {
        if (destroyed || generation !== requestGeneration) return;
        if (failure.code === 'no_game') { state = null; selectedId = null; mode = null; }
        else error = failure.message || 'Arena action failed.';
      } finally {
        if (!destroyed && generation === requestGeneration) { busy = false; aiPending = false; render(); }
      }
    })();
    return pending;
  }

  function onClick(event) {
    const button = event.target.closest('[data-arena]');
    if (!button || !root.contains(button) || button.disabled || (busy && !['reset', 'refresh'].includes(button.dataset.arena))) return;
    const action = button.dataset.arena;
    if (action === 'ability-help') {
      const expanded = button.getAttribute('aria-expanded') === 'true';
      root.querySelectorAll('[data-arena="ability-help"]').forEach(b => b.setAttribute('aria-expanded', 'false'));
      button.setAttribute('aria-expanded', String(!expanded));
      button.parentElement.toggleAttribute('data-help-dismissed', expanded);
      return;
    }
    if (action === 'coordinates') { coordinates = button.checked; render(); return; }
    if (action === 'reset' || action === 'demo-openai') return run(() => api.createAiDemo('openai'), true);
    if (action === 'refresh') return run(() => api.getGame(), true);
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
      if (!legal && piece?.unit_type && piece.owner_id === state.active_player_id && piece.status === 'active' && piece.id !== selectedId) {
        selectedId = piece.id; mode = null; error = ''; render(); return;
      }
      if (!legal) { error = 'Choose a highlighted legal target, or cancel the action to select another unit.'; render(); return; }
      if (mode === 'move') details.destination = position;
      else if (mode === 'fireball') details.target_position = position;
      else details.target_id = piece.id;
      const actionMode = mode;
      return run(() => api.command(actionMode, state.active_player_id, details));
    }
    selectedId = piece?.unit_type ? piece.id : null;
    error = '';
    render();
  }

  function onHelpKey(event) {
    if (event.key !== 'Escape') return;
    root.querySelectorAll('[data-arena="ability-help"]').forEach(button => {
      button.setAttribute('aria-expanded', 'false');
      button.parentElement.setAttribute('data-help-dismissed', '');
    });
  }
  function onHelpEnter(event) {
    const help = event.target.closest?.('.arena-ability-help');
    if (help && !help.contains(event.relatedTarget)) help.removeAttribute('data-help-dismissed');
  }
  root.addEventListener('keydown', onHelpKey);
  root.addEventListener('pointerover', onHelpEnter);
  root.addEventListener('focusin', onHelpEnter);
  root.addEventListener('click', onClick);
  run(() => api.getGame(), true);
  return { whenIdle: () => pending,
    resume: () => { const previous = pending; return run(async () => { await previous; return api.getGame(); }, true); },
    get state() { return state; }, get authoritative() { return authoritative; },
    cancel: () => { generation++; engine.cancel(); busy = false; aiPending = false; if (authoritative) state = authoritative; render(); },
    destroy: () => { destroyed = true; generation++; engine.cancel(); root.removeEventListener('click', onClick);
      root.removeEventListener('keydown', onHelpKey); root.removeEventListener('pointerover', onHelpEnter); root.removeEventListener('focusin', onHelpEnter); } };
}
