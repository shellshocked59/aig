/** Semantic state projection: resolved values only, never legality or damage rules. */
export const PRESENTATION_VERSION = 'arena-presentation-events-v1';
/** V1 already emits one event per executed command; victory belongs to its cause. */
export function actionGroups(events, controllers = {}) {
  const groups = [];
  for (const event of events) {
    if (event.type === 'victory' && groups.length) {
      groups.at(-1).events.push(event);
      break; // No action can follow terminal feedback.
    }
    const ai = event.type !== 'turn_end' && event.type !== 'victory' &&
      Boolean(controllers[event.acting_player] && controllers[event.acting_player] !== 'human');
    groups.push({ events: [event], ai, actorId: event.actor_id, player: event.acting_player, turn: event.turn });
  }
  for (const group of groups.filter(g => g.ai)) {
    const turn = groups.filter(g => g.ai && g.player === group.player && g.turn === group.turn);
    group.index = turn.indexOf(group) + 1;
    group.total = turn.length;
  }
  return groups;
}
export function applyPresentationEvent(state, event) {
  const next = structuredClone(state);
  for (const effect of event.effects || []) {
    const key = effect.entity_kind === 'core' ? 'cores' : 'units';
    const entity = next[key].find((u) => u.id === effect.entity_id);
    if (effect.type === 'removed') next[key] = next[key].filter((u) => u.id !== effect.entity_id);
    else if (entity) {
      if (effect.hp_after !== undefined) entity.hp = effect.hp_after;
      if (effect.status_after !== undefined) entity.status = effect.status_after;
      if (effect.destination) Object.assign(entity, effect.destination);
    }
  }
  Object.assign(next, event.transition || {});
  if (event.type === 'victory') {
    next.winner_player_id = event.winner_player_id;
    next.terminal_reason = event.terminal_reason;
  }
  if (event.after_hash) next.state_hash = event.after_hash;
  return next;
}

export function visualSignature(state) {
  const pieces = (items) => items.map(({ id, owner_id, x, y, hp, status }) =>
    ({ id, owner_id, x, y, hp, status })).sort((a, b) => a.id.localeCompare(b.id));
  return JSON.stringify({ units: pieces(state.units), cores: pieces(state.cores), turn: state.turn,
    active_player_id: state.active_player_id, action_points_remaining: state.action_points_remaining,
    winner_player_id: state.winner_player_id, terminal_reason: state.terminal_reason || null });
}

export class PresentationRegistry {
  constructor(fallback = async () => {}) { this.handlers = new Map(); this.fallback = fallback; }
  register(eventType, handler, actorClass) {
    this.handlers.set(actorClass ? `${eventType}:${actorClass}` : eventType, handler);
    return this;
  }
  resolve(event) {
    return this.handlers.get(`${event.type}:${event.actor_class}`) || this.handlers.get(event.type) || this.fallback;
  }
}

/** One cancellable owner for all presentation work. A new play supersedes the old queue. */
export class ArenaPresentationEngine {
  constructor({ registry, driver, getState, setState, onEvent = () => {}, onGroup = () => {}, onBusy = () => {}, report = console.error }) {
    Object.assign(this, { registry, driver, getState, setState, onEvent, onGroup, onBusy, report });
    this.generation = 0;
  }
  cancel() {
    this.generation++;
    this.controller?.abort();
    this.driver.clear?.();
    this.onGroup(null);
    this.onBusy(false);
  }
  async play(batch, authoritative) {
    this.cancel();
    const generation = this.generation;
    const controller = this.controller = new AbortController();
    const current = () => generation === this.generation && !controller.signal.aborted;
    this.onBusy(true);
    try {
      if (batch.version !== PRESENTATION_VERSION ||
          (this.getState().state_hash && this.getState().state_hash !== batch.start_state_hash)) {
        this.report('Arena presentation version/start-state mismatch; synchronizing.');
        this.setState(structuredClone(authoritative));
        return;
      }
      for (const group of actionGroups(batch.events, authoritative.controllers)) {
        if (!current()) return;
        this.onGroup(group.ai ? group : null);
        const started = performance.now();
        for (const event of group.events) {
          if (!current()) return;
          this.onEvent(event);
          // Optional semantic checkpoints let HP commit at impact without replacing
          // the board DOM underneath live animations. Final application is idempotent.
          const commit = (effects) => {
            if (current()) this.setState(applyPresentationEvent(this.getState(), { effects }), { effects });
          };
          try { await this.registry.resolve(event)(event, this.driver, controller.signal, { commit }); }
          catch (error) { if (current()) this.report('Arena presentation handler failed; applying resolved event.', error); }
          if (!current()) return;
          this.setState(applyPresentationEvent(this.getState(), event));
        }
        if (group.ai) {
          // Animation time contributes to the minimum readable action duration.
          const remaining = Math.max(0, (this.driver.duration?.('aiActionMinDuration') || 0) - (performance.now() - started));
          await this.driver.wait?.(remaining, controller.signal);
          if (!current()) return;
          await this.driver.delay?.('aiBetweenActionPause', controller.signal);
        } else await this.driver.delay?.('betweenActionDelay', controller.signal);
      }
      if (!current()) return;
      if (visualSignature(this.getState()) !== visualSignature(authoritative)) {
        this.report('Arena presentation final-state mismatch; synchronizing to authoritative state.');
      }
      this.setState(structuredClone(authoritative));
    } finally { if (current()) { this.driver.clear?.(); this.onGroup(null); this.onBusy(false); } }
  }
}
