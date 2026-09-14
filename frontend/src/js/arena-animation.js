import { PresentationRegistry } from './arena-presentation.js';

export const ARENA_TIMINGS = Object.freeze({
  movePerTile: 110, moveMin: 220, moveMax: 480, moveDuration: 320,
  attackWindup: 110, snipeWindup: 220, reviveWindup: 180, projectileDuration: 150,
  impactDuration: 180, hpDuration: 240, floatTextDuration: 360, healFloatDuration: 420,
  statusTransition: 360, pushDuration: 210, fireballWindup: 180, fireballImpact: 360,
  betweenActionDelay: 55, turnTransition: 300, victoryDelay: 260,
  aiActionMinDuration: 1000, aiBetweenActionPause: 250,
});

/** All DOM geometry, transient ownership and clocks belong to this driver. */
export class ArenaAnimationDriver {
  constructor(root, { speed = 1, instant = false, reducedMotion, timings = ARENA_TIMINGS } = {}) {
    Object.assign(this, { root, speed: speed > 0 ? speed : 1, instant, timings: { ...ARENA_TIMINGS, ...timings } });
    this.reducedMotion = reducedMotion ?? root.ownerDocument.defaultView.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    this.animations = new Set(); this.nodes = new Set(); this.cleanups = new Set();
  }
  duration(key) { return this.instant ? 0 : (typeof key === 'number' ? key : this.timings[key]) / this.speed; }
  async animate(node, frames, key, signal, easing = 'ease-out') {
    if (!node || signal.aborted || !node.animate || !this.duration(key)) return;
    const animation = node.animate(frames, { duration: this.duration(key), easing, fill: 'forwards' });
    this.animations.add(animation);
    const cancel = () => animation.cancel();
    signal.addEventListener('abort', cancel, { once: true });
    try { await animation.finished; } catch (error) { if (!signal.aborted) throw error; }
    finally { signal.removeEventListener('abort', cancel); animation.cancel(); this.animations.delete(animation); }
  }
  // Playback clocks must survive absent Web Animations support and DOM replacement.
  wait(milliseconds, signal) {
    if (signal.aborted || !milliseconds) return Promise.resolve();
    return new Promise(resolve => {
      let timer;
      const done = () => { clearTimeout(timer); signal.removeEventListener('abort', done); this.cleanups.delete(done); resolve(); };
      this.cleanups.add(done);
      signal.addEventListener('abort', done, { once: true });
      timer = setTimeout(done, milliseconds);
    });
  }
  delay(key, signal) { return this.wait(this.duration(key), signal); }
  cell(position) { return position && this.root.querySelector(`[data-arena="tile"][data-x="${position.x}"][data-y="${position.y}"]`); }
  entity(id) { return [...this.root.querySelectorAll('[data-unit-id], [data-core-id]')]
    .find((node) => node.dataset.unitId === id || node.dataset.coreId === id); }
  point(position) {
    const cell = this.cell(position)?.getBoundingClientRect(), board = this.root.querySelector('.arena-overlay')?.getBoundingClientRect();
    return cell && board ? { x: cell.left - board.left + cell.width / 2, y: cell.top - board.top + cell.height / 2,
      width: cell.width, height: cell.height } : null;
  }
  own(node) { this.root.querySelector('.arena-overlay')?.append(node); this.nodes.add(node); return node; }
  release(node) { node.remove(); this.nodes.delete(node); }
  create(position, className, text = '') {
    const p = this.point(position);
    if (!p || !this.root.querySelector('.arena-overlay')) return null;
    const node = this.root.ownerDocument.createElement('span');
    node.className = `arena-effect ${className}`; node.textContent = text;
    Object.assign(node.style, { left: `${p.x}px`, top: `${p.y}px` });
    node.style.setProperty('--cell-width', `${p.width}px`);
    node.style.setProperty('--cell-height', `${p.height}px`);
    return this.own(node);
  }
  async overlay(position, className, text, frames, timing, signal) {
    if (signal.aborted || this.instant) return;
    const node = this.create(position, className, text);
    if (!node) return;
    try { await this.animate(node, frames, timing, signal); } finally { this.release(node); }
  }
  /** Retain actor/target rings through impact, not just a momentary brightness blink. */
  cue(event, signal, tone = '') {
    if (signal.aborted || this.instant) return () => {};
    const nodes = [this.create(event.origin, `arena-source ${tone}`, event.type.replaceAll('_', ' ').toUpperCase()),
      this.create(event.target, `arena-target ${tone}`)].filter(Boolean);
    const cleanup = () => { nodes.forEach((n) => this.release(n)); this.cleanups.delete(cleanup); signal.removeEventListener('abort', cleanup); };
    this.cleanups.add(cleanup); signal.addEventListener('abort', cleanup, { once: true }); return cleanup;
  }
  pulse(id, signal, timing = 'attackWindup') {
    return this.animate(this.entity(id), [{ filter: 'brightness(1)' }, { filter: 'brightness(2.5)' }, { filter: 'brightness(1)' }], timing, signal);
  }
  flash(position, signal, area = false, tone = '') {
    if (area) return this.area(position, signal);
    return this.overlay(position, `arena-impact ${tone}`, '',
      [{ opacity: .95, transform: 'translate(-50%,-50%) scale(.8)' },
        { opacity: 0, transform: `translate(-50%,${!this.reducedMotion && tone.includes('arena-revive') ? '-75%' : '-50%'}) scale(${this.reducedMotion ? 1 : 1.25})` }], 'impactDuration', signal);
  }
  area(position, signal) {
    // Measure each actual cell: rectangular tiles and clipped board edges remain exact.
    const pulses = [];
    for (let y = position.y - 1; y <= position.y + 1; y++) for (let x = position.x - 1; x <= position.x + 1; x++) {
      pulses.push(this.overlay({ x, y }, 'arena-area', '', [{ opacity: .9 }, { opacity: .45, offset: .65 }, { opacity: 0 }], 'fireballImpact', signal));
    }
    return Promise.all(pulses);
  }
  float(position, text, signal, tone = '') {
    return this.overlay(position, `arena-float ${tone}`, text,
      [{ opacity: 1, transform: 'translate(-50%,-100%)' }, { opacity: 1, offset: .8 },
        { opacity: 0, transform: `translate(-50%,${this.reducedMotion ? '-100%' : '-180%'})` }],
      tone === 'arena-restorative' ? 'healFloatDuration' : 'floatTextDuration', signal);
  }
  async move(id, from, to, signal, path = [from, to], push = false) {
    if (this.instant || signal.aborted) return;
    if (this.reducedMotion) { await this.pulse(id, signal); return; }
    const points = path.map((p) => this.point(p)), entity = this.entity(id);
    if (points.length < 2 || points.some((p) => !p) || !entity) return;
    const a = points[0], ghost = entity.cloneNode(true);
    ghost.removeAttribute('data-unit-id'); ghost.removeAttribute('data-core-id');
    ghost.classList.add('arena-movement-ghost');
    ghost.dataset.movingId = id;
    ghost.classList.add(entity.closest('.arena-team-blue') ? 'arena-team-blue' : 'arena-team-red');
    Object.assign(ghost.style, { left: `${a.x}px`, top: `${a.y}px`, width: `${a.width - 8}px` });
    this.own(ghost);
    const visibility = entity.style.visibility;
    entity.style.visibility = 'hidden';
    const cleanup = () => { entity.style.visibility = visibility; this.release(ghost); this.cleanups.delete(cleanup); };
    this.cleanups.add(cleanup);
    const timing = push ? this.timings.pushDuration : Math.min(this.timings.moveMax,
      Math.max(this.timings.moveMin, (points.length - 1) * this.timings.movePerTile));
    try { await this.animate(ghost, points.map((p, i) => ({ offset: i / (points.length - 1),
      transform: `translate(calc(-50% + ${p.x-a.x}px),calc(-50% + ${p.y-a.y}px))`,
      filter: 'drop-shadow(0 5px 5px #0008)' })), timing, signal, 'linear'); }
    finally { cleanup(); }
  }
  async tracer(from, to, signal, snipe = false, tone = '') {
    if (this.reducedMotion) { await Promise.all([this.flash(from, signal, false, tone), this.flash(to, signal, false, tone)]); return; }
    const a = this.point(from), b = this.point(to);
    if (!a || !b) return;
    const angle = Math.atan2(b.y-a.y, b.x-a.x), length = Math.hypot(b.x-a.x, b.y-a.y);
    await this.overlay(from, `arena-tracer ${snipe ? 'arena-snipe' : ''} ${tone}`, '',
      [{ width: '0px', transform: `rotate(${angle}rad)`, opacity: 1 },
        { width: `${length}px`, transform: `rotate(${angle}rad)`, opacity: 1 }], 'projectileDuration', signal);
  }
  lunge(event, signal) {
    if (this.reducedMotion) return this.pulse(event.actor_id, signal);
    const a = this.point(event.origin), b = this.point(event.target);
    if (!a || !b) return Promise.resolve();
    const length = Math.hypot(b.x-a.x, b.y-a.y) || 1;
    const dx = (b.x-a.x) / length * a.width * .25, dy = (b.y-a.y) / length * a.width * .25;
    return this.animate(this.entity(event.actor_id), [{ transform: 'translate(0,0)' },
      { transform: `translate(${dx}px,${dy}px)`, offset: .65 }, { transform: 'translate(0,0)' }], 'projectileDuration', signal);
  }
  hit(id, signal) {
    return this.animate(this.entity(id), [{ filter: 'brightness(3)', transform: 'translateX(0)' },
      { filter: 'brightness(1.6)', transform: `translateX(${this.reducedMotion ? 0 : -4}px)`, offset: .3 },
      { transform: `translateX(${this.reducedMotion ? 0 : 4}px)`, offset: .6 },
      { filter: 'brightness(1)', transform: 'translateX(0)' }], 'impactDuration', signal);
  }
  hp(effect, signal) {
    if (signal.aborted) return Promise.resolve();
    const entity = this.entity(effect.entity_id), meter = entity?.querySelector('meter'), fill = entity?.querySelector('.arena-hp-fill');
    if (!meter) return Promise.resolve();
    meter.value = effect.hp_after;
    const label = entity.querySelector('[data-hp-label]');
    if (label) label.textContent = `${effect.hp_after}/${meter.max} HP`;
    for (const selected of this.root.querySelectorAll('[data-selected-hp]')) {
      if (selected.dataset.selectedHp === effect.entity_id) selected.textContent = `${effect.hp_after}/${meter.max} HP`;
    }
    const tile = entity.closest('.arena-tile');
    for (const attribute of ['aria-label', 'title']) if (tile?.hasAttribute(attribute)) {
      tile.setAttribute(attribute, tile.getAttribute(attribute).replace(/HP \d+\/\d+/, `HP ${effect.hp_after}/${meter.max}`));
    }
    if (fill) fill.style.width = `${100 * effect.hp_after / meter.max}%`;
    return this.animate(fill, [{ width: `${100 * effect.hp_before / meter.max}%` },
      { width: `${100 * effect.hp_after / meter.max}%` }], 'hpDuration', signal);
  }
  async status(effect, signal) {
    const revive = effect.type === 'revived', entity = this.entity(effect.entity_id);
    const icon = entity?.querySelector('.arena-icon');
    const motion = (frames) => this.reducedMotion ? frames.map(({ transform, ...frame }) => frame) : frames;
    await Promise.all([
      this.float(effect.position, revive ? 'REVIVE' : 'DOWNED', signal, revive ? 'arena-restorative arena-revive arena-status-float' : 'arena-status-float'),
      this.animate(icon, motion(revive ? [{ opacity: .4, filter: 'grayscale(1)', transform: 'rotate(70deg)' },
        { opacity: 1, filter: 'brightness(2)', transform: 'rotate(0deg)' }] :
        [{ opacity: 1, transform: 'rotate(0deg)' }, { opacity: .4, filter: 'grayscale(1)', transform: 'rotate(70deg)' }]), 'statusTransition', signal),
      revive ? this.flash(effect.position, signal, false, 'arena-restorative arena-revive') : Promise.resolve(),
    ]);
    if (signal.aborted || !entity) return;
    entity.closest('.arena-tile')?.classList.toggle('arena-downed', !revive);
    for (const selected of this.root.querySelectorAll('[data-selected-status]')) {
      if (selected.dataset.selectedStatus === effect.entity_id) selected.textContent = effect.status_after.toUpperCase();
    }
    const badge = entity.querySelector('.arena-downed-badge');
    if (revive) badge?.remove();
    else if (!badge) { const label = this.root.ownerDocument.createElement('span'); label.className = 'arena-downed-badge'; label.textContent = 'DOWNED'; entity.append(label); }
  }
  fade(id, signal, core = false) { return this.animate(this.entity(id), [{ opacity: 1, filter: 'brightness(3)' },
    { opacity: core ? .2 : 0, filter: 'grayscale(1)', transform: this.reducedMotion ? 'none' : `scale(${core ? .75 : .15})` }], 'statusTransition', signal); }
  async destruction(effect, signal) {
    await Promise.all([this.float(effect.position, 'CORE DESTROYED', signal, 'arena-status-float'),
      this.flash(effect.position, signal), this.fade(effect.entity_id, signal, true)]);
    if (!signal.aborted) this.entity(effect.entity_id)?.closest('.arena-tile')?.classList.add('arena-core-destroyed');
  }
  async turn(event, signal) {
    if (signal.aborted || this.instant) return;
    const layer = this.root.querySelector('.arena-overlay');
    if (!layer) return;
    const node = this.root.ownerDocument.createElement('span'); node.className = 'arena-turn-banner';
    node.textContent = `${(event.transition.active_player_id || '').toUpperCase()} TURN`;
    this.own(node);
    try { await this.animate(node, [{ opacity: 0 }, { opacity: 1, offset: .2 }, { opacity: 1, offset: .8 }, { opacity: 0 }], 'turnTransition', signal); }
    finally { this.release(node); }
  }
  clear() {
    for (const animation of this.animations) animation.cancel();
    for (const cleanup of [...this.cleanups]) cleanup();
    for (const node of this.nodes) node.remove();
    this.animations.clear(); this.nodes.clear();
  }
}

/** Reused by every attack/ability. Commit resolved HP at impact in event order. */
export async function presentEffects(event, driver, signal, { commit = () => {} } = {}, motif = '') {
  const effects = event.effects || [];
  const hp = effects.filter((e) => ['damage', 'core_damage', 'heal'].includes(e.type));
  if (signal.aborted) return;
  commit(hp);
  await Promise.all(hp.map((effect) => {
    const heal = effect.type === 'heal', tone = heal ? 'arena-restorative' : 'arena-damage';
    return Promise.all([driver.hp(effect, signal), driver.flash(effect.position, signal, false, motif || tone),
      heal ? driver.pulse(effect.entity_id, signal) : driver.hit(effect.entity_id, signal),
      driver.float(effect.position, `${heal ? '+' : '-'}${effect.amount}`, signal, tone)]);
  }));
  // Status and displacement checkpoints preserve the original semantic order.
  for (const effect of effects) {
    if (signal.aborted) return;
    if (['downed', 'revived'].includes(effect.type)) { await driver.status(effect, signal); commit([effect]); }
    else if (effect.type === 'removed') {
      await Promise.all([driver.float(effect.position, 'FINISHED', signal, 'arena-status-float'), driver.fade(effect.entity_id, signal)]);
      commit([effect]);
    } else if (effect.type === 'push') {
      await driver.move(effect.entity_id, effect.position, effect.destination, signal, undefined, true); commit([effect]);
    } else if (effect.type === 'core_damage' && effect.hp_after === 0) await driver.destruction(effect, signal);
  }
}

async function combatPresentation(event, driver, signal, context, { snipe = false, restorative = false, revive = false, motif = '' } = {}) {
  const tone = restorative ? `arena-restorative${revive ? ' arena-revive' : ''}` : motif;
  const cleanup = driver.cue(event, signal, tone);
  try {
    await Promise.all([
      driver.pulse(event.actor_id, signal, snipe ? 'snipeWindup' : revive ? 'reviveWindup' : event.type === 'fireball' ? 'fireballWindup' : 'attackWindup'),
      revive || snipe ? driver.flash(event.target, signal, false, tone) : Promise.resolve(),
    ]);
    if (signal.aborted) return;
    if (event.origin && event.target) {
      await Promise.all([driver.tracer(event.origin, event.target, signal, snipe, tone),
        event.actor_class === 'knight' && !restorative ? driver.lunge(event, signal) : Promise.resolve()]);
    }
    if (signal.aborted) return;
    await Promise.all([event.type === 'fireball' ? driver.area(event.target, signal) : Promise.resolve(),
      presentEffects(event, driver, signal, context, tone)]);
  } finally { cleanup(); }
}
export async function genericPresentation(event, driver, signal, context = {}) {
  if (event.type === 'victory') { await driver.delay('victoryDelay', signal); return; }
  if (event.type === 'turn_end') { await driver.turn(event, signal); return; }
  if (event.type === 'move') {
    const path = event.path?.length > 1 ? event.path : [event.origin, event.destination];
    await driver.move(event.actor_id, event.origin, event.destination, signal, path); return;
  }
  await combatPresentation(event, driver, signal, context, { restorative: ['heal', 'revive'].includes(event.type) });
}
export const snipePresentation = (event, driver, signal, context) => combatPresentation(event, driver, signal, context, { snipe: true, motif: 'arena-precision arena-aim' });
export const revivePresentation = (event, driver, signal, context) => combatPresentation(event, driver, signal, context, { restorative: true, revive: true });
export const knightAttack = (e,d,s,c) => combatPresentation(e,d,s,c,{ motif:'arena-physical' });
export const rangerAttack = (e,d,s,c) => combatPresentation(e,d,s,c,{ motif:'arena-precision' });
export const mageAttack = (e,d,s,c) => combatPresentation(e,d,s,c,{ motif:'arena-arcane' });
export const clericAttack = (e,d,s,c) => combatPresentation(e,d,s,c,{ motif:'arena-radiant' });
export const shieldBashPresentation = (e,d,s,c) => combatPresentation(e,d,s,c,{ motif:'arena-physical arena-bash' });
export const fireballPresentation = (e,d,s,c) => combatPresentation(e,d,s,c,{ motif:'arena-arcane arena-fire' });
export const healPresentation = (e,d,s,c) => combatPresentation(e,d,s,c,{ restorative:true });
export const createArenaRegistry = () => new PresentationRegistry(genericPresentation)
  .register('attack', knightAttack, 'knight').register('attack', rangerAttack, 'ranger')
  .register('attack', mageAttack, 'mage').register('attack', clericAttack, 'cleric')
  .register('snipe', snipePresentation).register('revive', revivePresentation)
  .register('heal', healPresentation).register('shield_bash', shieldBashPresentation)
  .register('fireball', fireballPresentation);
