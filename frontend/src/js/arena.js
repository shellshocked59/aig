import { actionName, abilityHelp, rulesHelp } from './arena-help.js';
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
  const coordinates = options.coordinates ?? false;
  let mode = null;
  let busy = false;
  let aiPending = false;
  let error = '';
  let pending = Promise.resolve();
  const selected = () => state?.units.find((u) => u.id === selectedId);
  const playerName = (id) => state?.players.find((p) => p.id === id)?.name || id || 'Team';
  const disabled = (condition = false) => busy || condition ? 'disabled' : '';
  const at = (piece, tile) => piece.x === tile.x && piece.y === tile.y;

  function render() {
    if (destroyed) return;
    const unit = selected();
    const terminal = state?.winner_player_id != null;
    const controllers = Object.values(state?.controllers || {});
    const observer = controllers.length > 0 && controllers.every(c => c !== 'human');
    const offlineAi = controllers.some((c) => ['heuristic_ai', 'heuristic-v2_ai'].includes(c));
    const hasAi = controllers.some((c) => c !== 'human');
    const matchLabel = observer ? 'OpenAI Luna vs OpenAI Luna · Observer mode' : hasAi ? (offlineAi ? 'Human vs Heuristic · You are Blue' : 'Human vs OpenAI Luna · You are Blue') : 'Existing local match';
    const cannotAct = terminal || (state?.controllers?.[state.active_player_id] && state.controllers[state.active_player_id] !== 'human');
    const passive = aiPending || cannotAct;
    const targetKind = mode === 'move' ? 'move' : ['heal', 'revive'].includes(mode) ? 'support' : mode === 'fireball' ? 'fire' : 'hostile';
    const instruction = { move: 'Choose a highlighted destination.', fireball: 'Choose an impact tile. Nearby allies can be hit.', heal: 'Choose a highlighted active ally.', revive: 'Choose a DOWNED ally.' }[mode] || 'Choose a highlighted enemy.';
    root.innerHTML = `<section class="arena-view" aria-label="Arena">
      <header class="arena-header"><div><h1>Arena</h1><p>Break their Core. Protect your team.</p></div>
      <div class="arena-match-controls"><span class="arena-mode-label">Play mode</span>
      <details class="arena-experimental"><summary>${state ? esc(matchLabel.split(' · ')[0]) : 'Choose mode'}</summary><div>
      <button data-arena="demo-ai-v2" ${disabled()}>Human vs Heuristic</button>
      <button data-arena="demo-openai" ${disabled()}>Human vs OpenAI Luna</button>
      <button data-arena="demo-observer" ${disabled()}>OpenAI Luna vs OpenAI Luna</button></div></details>
      ${state ? `<button data-arena="reset" ${busy && !playing ? 'disabled' : ''}>New Match</button>` : ''}
      <button data-arena="refresh" ${busy && !playing ? 'disabled' : ''}>Refresh</button></div></header>
      ${error ? `<p role="alert">${esc(error)}</p>` : ''}
      ${state ? `<div class="arena-turnbar arena-team-${(state.winner_player_id ?? state.active_player_id) === state.players[0].id ? 'blue' : 'red'}"><div>
      <p class="arena-status" role="status">${terminal
        ? `${esc(playerName(state.winner_player_id))} wins!`
        : `<span>${esc(playerName(state.active_player_id))} turn</span><span class="arena-ap">${state.action_points_remaining} / 5 <small>AP</small></span>`}</p>
      <p class="arena-mode">${esc(matchLabel)} · Turn ${state.turn}</p>
      ${terminal ? `<p class="arena-winner">${esc(state.terminal_reason || 'Battle complete')}</p>` : ''}</div>
      <p class="arena-playback-status" role="status">${busy ? (playing ? (actionGroup ? `AI acting · Action ${actionGroup.index} / ${actionGroup.total}<span>${esc(actionGroup.events[0].actor_label)} · ${esc(actionName(actionGroup.events[0].type))}</span>` : aiPending ? 'AI acting…' : 'Playing action…') : aiPending ? 'AI thinking…' : 'Resolving…') : terminal ? 'Battle complete' : 'Ready'}</p>
      ${observer ? `<button class="arena-end" data-arena="observer-turn" ${disabled(terminal)}>Next AI turn</button>` : `<button class="arena-end" data-arena="end" ${disabled(cannotAct)}>End Turn</button>`}</div>
      <div class="arena-layout"><div class="arena-scroll"><div class="arena-board ${coordinates ? 'arena-show-coordinates' : ''}" aria-label="Arena board"><div class="arena-overlay" aria-hidden="true"></div>
      ${state.board.tiles.map((tile) => {
        const piece = state.units.find((u) => at(u, tile)) || state.cores.find((c) => at(c, tile));
        const kind = piece?.unit_type || (piece ? 'core' : tile.terrain === 'blocked' ? 'blocked' : null);
        const legal = mode && unit && ((mode === 'move' || mode === 'fireball')
          ? unit.actions[mode].some((p) => at(p, tile)) : piece && unit.actions[mode].includes(piece.id));
        const description = `${tile.x}, ${tile.y}: ${tile.terrain}${tile.bonus ? `, ${tile.bonus}` : ''}${piece ? `, ${playerName(piece.owner_id)} ${kind}, HP ${piece.hp}/${piece.max_hp}${piece.status === 'downed' ? ', DOWNED' : ''}` : ''}`;
        return `<button class="arena-tile arena-${tile.terrain} ${tile.bonus ? `arena-${tile.bonus}` : ''} ${piece ? `arena-team-${piece.owner_id === state.players[0].id ? 'blue' : 'red'}` : ''} ${piece?.status === 'downed' ? 'arena-downed' : ''} ${piece && !piece.unit_type && piece.hp === 0 ? 'arena-core-destroyed' : ''} ${piece?.id === selectedId ? 'arena-selected' : ''} ${actionGroup?.actorId === piece?.id && piece ? 'arena-acting' : ''} ${legal ? `arena-legal arena-target-${targetKind}` : ''}"
          data-arena="tile" data-x="${tile.x}" data-y="${tile.y}" aria-pressed="${piece?.id === selectedId}" aria-label="${esc(description + (legal ? ', legal ' + mode + ' target' : ''))}" title="${esc(description + (legal ? ', legal ' + mode + ' target' : ''))}" ${disabled(cannotAct)}>
          <span class="arena-coordinate">${tile.x},${tile.y}</span>
          ${tile.bonus ? `<span class="arena-bonus">${arenaIcon(tile.bonus)}${esc(tile.bonus)}</span>` : ''}
          ${piece ? renderArenaPiece(piece, state.players[0].id) : kind ? arenaIcon(kind) : ''}
        </button>`;
      }).join('')}</div></div>
      <aside class="arena-details" aria-label="Battle information">
        <section class="arena-panel arena-log-panel"><h2>Battle log</h2><ol class="arena-battle-log" aria-label="Battle log" aria-live="polite">${(state.battle_log || []).slice().reverse().map((entry) => `<li>${esc(entry.text)}</li>`).join('') || '<li>No actions yet. Blue moves first.</li>'}</ol></section>
      </aside>
      <section class="arena-command-deck ${passive ? 'arena-passive' : ''}" aria-label="Command deck" aria-busy="${busy}">
        <div class="arena-selected-summary" aria-label="Selected unit">${unit
          ? `<div role="img" aria-label="${esc(playerName(unit.owner_id))} ${esc(unit.unit_type)} artwork" class="arena-selected-art arena-team-${unit.owner_id === state.players[0].id ? 'blue' : 'red'} ${unit.status === 'downed' ? 'arena-downed' : ''}">${unitVisual(unit.unit_type)}</div>
            <div><p class="arena-unit-team">${esc(playerName(unit.owner_id))} · <span data-selected-status="${esc(unit.id)}">${esc(unit.status.toUpperCase())}</span></p>
            <h2>${esc(unit.unit_type)}</h2><p class="arena-unit-hp" data-selected-hp="${esc(unit.id)}">${unit.hp}/${unit.max_hp} HP</p>
            <p class="arena-unit-stats"><span>Move ${unit.stats.move_range}</span> · <span>Damage ${unit.stats.damage}</span> · <span>Range ${unit.stats.attack_range}</span>${unit.stats.heal_amount ? `<br>Heal ${unit.stats.heal_amount} · Range ${unit.stats.heal_range}` : ''}</p></div>`
          : `<div class="arena-empty-art">${arenaIcon('knight')}</div><div><h2>${terminal ? 'Battle complete' : observer ? 'Observer mode' : passive ? 'Opponent turn' : 'Select a ' + esc(playerName(state.active_player_id).replace(' Team', '')) + ' unit'}</h2><p>${terminal ? 'Start a new match when ready.' : observer ? 'Watch Blue and Red take turns.' : passive ? 'Watch the opposing team act.' : 'Inspect a unit, then choose an ability.'}</p></div>`}</div>
        <div class="arena-ability-tray" aria-label="Abilities">${unit ? `<div class="arena-actions">${Object.keys(unit.abilities).map((action) => `<div class="arena-action-option arena-ability-${action}"><button data-arena="mode" data-mode="${action}" aria-pressed="${mode === action}" ${disabled(cannotAct || unit.owner_id !== state.active_player_id || unit.status !== 'active' || !unit.actions[action].length)}>${actionIcon(action)}<span>${esc(actionName(action))}<small>${unit.abilities[action].ap_cost} AP</small></span></button>${abilityHelp(action, busy)}</div>`).join('')}</div>` : observer && !terminal ? '<p class="arena-tray-empty">AI vs AI<span>Luna controls both teams.</span></p>' : terminal ? '<p class="arena-tray-empty">Battle complete<span>New Match keeps your current play mode.</span></p>' : '<p class="arena-tray-empty">Move · Attack · Class ability · Finish<span>Every turn gives your team 5 AP.</span></p>'}</div>
        <div class="arena-context arena-target-${targetKind}" aria-label="Action context" role="status">
          <h2>${terminal ? 'Victory' : observer ? 'Observer mode' : passive ? 'Opponent turn' : busy ? 'Resolving action' : mode ? `${esc(actionName(mode))} · ${unit.abilities[mode].ap_cost} AP` : 'Your command'}</h2>
          <p>${terminal ? 'Start a new match to play again.' : observer ? busy ? 'Watching the current AI turn.' : 'Choose Next AI turn to watch Luna play.' : passive ? 'Controls return after playback.' : busy ? 'Wait for the action to finish.' : mode ? instruction : unit ? unit.status === 'downed' ? 'This unit is DOWNED.' : unit.owner_id !== state.active_player_id ? 'Inspecting the opposing team.' : 'Choose an action, then a highlighted tile.' : 'Select an active-team unit to act. Select any unit to inspect it.'}</p>
          ${mode ? `<button data-arena="cancel" ${disabled()}>Cancel action</button>` : ''}
        </div>
      </section></div>${rulesHelp()}` : '<div class="arena-welcome arena-panel"><h2>Your first skirmish</h2><p>Choose a mode to play or watch an AI match. Each team has four units, a Core, and 5 AP per turn.</p><p>Select a unit, choose an action, then click a highlighted tile. Observer mode advances one AI turn at a time.</p></div>'}
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
    if (action === 'demo-ai-v2') return run(() => api.createAiDemo('heuristic-v2'), true);
    if (action === 'demo-openai') return run(() => api.createAiDemo('openai'), true);
    if (action === 'demo-observer') return run(() => api.createObserverDemo(), true);
    if (action === 'observer-turn') return run(() => api.observerTurn(), false, true);
    if (action === 'reset') {
      if (Object.values(state?.controllers || {}).length && Object.values(state.controllers).every(c => c !== 'human')) return run(() => api.createObserverDemo(), true);
      const controller = Object.values(state?.controllers || {}).find(c => c !== 'human');
      return run(() => controller ? api.createAiDemo(controller.replace(/_ai$/, '')) : api.createDemo(), true);
    }
    if (action === 'refresh') return run(() => api.getGame(), true);
    if (action === 'end') return run(() => api.command('end_turn', state.active_player_id), false,
      Object.values(state.controllers || {}).some((c) => c !== 'human'));
    if (action === 'cancel') { const previousMode = mode; mode = null; render(); root.querySelector(`[data-mode="${previousMode}"]`)?.focus({ preventScroll: true }); return; }
    if (action === 'mode') { mode = button.dataset.mode; render(); root.querySelector(`[data-mode="${mode}"]`)?.focus({ preventScroll: true }); return; }
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
    root.querySelector(`[data-arena="tile"][data-x="${position.x}"][data-y="${position.y}"]`)?.focus({ preventScroll: true });
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
