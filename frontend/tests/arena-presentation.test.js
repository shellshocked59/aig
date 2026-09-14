import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import fixtures from '../src/js/arena-lab-fixtures.json' with { type: 'json' };
import { ArenaPresentationEngine, PresentationRegistry, applyPresentationEvent, visualSignature } from '../src/js/arena-presentation.js';
import { ArenaAnimationDriver, createArenaRegistry, genericPresentation } from '../src/js/arena-animation.js';
import { mountArena } from '../src/js/arena.js';
import { mountPresentationLab } from '../src/js/arena-presentation-lab.js';

const clone = structuredClone;
const deferred = () => { let resolve; const promise = new Promise((r) => { resolve = r; }); return { promise, resolve }; };
const tick = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
function setup(name = 'Attack', handler = async () => {}) {
  const f = clone(fixtures[name]); let state = f.start;
  const logs = [], locks = [], warnings = [], commits = [];
  const engine = new ArenaPresentationEngine({ registry: new PresentationRegistry(handler), driver: {},
    getState: () => state, setState: (s) => { state = s; commits.push(s); }, onEvent: (e) => logs.push(e.type),
    onBusy: (b) => locks.push(b), report: (...args) => warnings.push(args) });
  return { f, engine, logs, locks, warnings, commits, get state() { return state; }, set state(s) { state = s; } };
}

for (const name of Object.keys(fixtures)) test(`resolved ${name} effects reproduce authoritative visual state`, () => {
  const f = fixtures[name];
  const actual = f.batch.events.reduce(applyPresentationEvent, f.start);
  assert.equal(visualSignature(actual), visualSignature(f.final));
  assert.deepEqual(f.start, fixtures[name].start);
});

test('registry selects class override, action fallback, then safe unknown fallback', () => {
  const fallback = () => {}, action = () => {}, specific = () => {};
  const r = new PresentationRegistry(fallback).register('attack', action).register('attack', specific, 'ranger');
  assert.equal(r.resolve({ type: 'attack', actor_class: 'ranger' }), specific);
  assert.equal(r.resolve({ type: 'attack', actor_class: 'knight' }), action);
  assert.equal(r.resolve({ type: 'future_event' }), fallback);
});

test('queue waits for each handler; logs start one at a time; victory and promise wait for damage', async () => {
  const gates = [deferred(), deferred()], started = [];
  const s = setup('Victory', (e) => { started.push(e.type); return gates[started.length-1].promise; });
  let done = false;
  const playback = s.engine.play(s.f.batch, s.f.final).then(() => { done = true; });
  assert.deepEqual(started, ['attack']); assert.deepEqual(s.logs, ['attack']);
  assert.equal(s.state.cores.find((c) => c.id === 'red-core').hp, 1);
  assert.equal(s.locks.at(-1), true);
  gates[0].resolve(); await tick();
  assert.deepEqual(started, ['attack', 'victory']);
  assert.equal(s.state.winner_player_id, null); assert.equal(done, false);
  gates[1].resolve(); await playback;
  assert.equal(s.state.winner_player_id, 'blue'); assert.equal(s.locks.at(-1), false);
  assert.equal(done, true); assert.deepEqual(s.warnings, []);
});

test('cancel prevents stale handler completion from mutating a new fixture', async () => {
  const gate = deferred(), s = setup('Move', () => gate.promise);
  const old = s.engine.play(s.f.batch, s.f.final);
  s.engine.cancel(); s.state = clone(fixtures.Revive.start);
  gate.resolve(); await old;
  assert.deepEqual(s.state, fixtures.Revive.start); assert.equal(s.commits.length, 0);
});

test('new playback supersedes an older queue', async () => {
  const gate = deferred(), s = setup('Move', () => gate.promise);
  const old = s.engine.play(s.f.batch, s.f.final);
  s.engine.registry = new PresentationRegistry();
  await s.engine.play(s.f.batch, s.f.final);
  const count = s.commits.length;
  gate.resolve(); await old; assert.equal(s.commits.length, count);
});

test('handler error still applies authoritative effects and completes', async () => {
  const s = setup('Attack', () => { throw new Error('cosmetic failure'); });
  await s.engine.play(s.f.batch, s.f.final);
  assert.deepEqual(s.state, s.f.final); assert.equal(s.warnings.length, 1);
});

test('mismatch reports clearly and snaps; unknown event remains safe', async () => {
  const s = setup(); s.f.batch.events = [{ type: 'future_action', effects: [] }];
  await s.engine.play(s.f.batch, s.f.final);
  assert.deepEqual(s.state, s.f.final); assert.match(s.warnings[0][0], /final-state mismatch/);
});

for (const problem of ['version', 'start_state_hash']) test(`${problem} mismatch skips playback and synchronizes`, async () => {
  const s = setup(); s.f.batch[problem] = 'wrong';
  await s.engine.play(s.f.batch, s.f.final);
  assert.equal(s.logs.length, 0); assert.equal(s.warnings.length, 1); assert.deepEqual(s.state, s.f.final);
});

for (const reducedMotion of [false, true]) test(`instant driver preserves information, reduced motion ${reducedMotion}`, async () => {
  const dom = new JSDOM('<main></main>');
  try {
    const root = dom.window.document.querySelector('main');
    const driver = new ArenaAnimationDriver(root, { instant: true, reducedMotion });
    const seen = []; driver.float = async (_p, text) => seen.push(text);
    for (const name of ['Revive', 'Down', 'Fireball', 'Heal']) {
      await genericPresentation(fixtures[name].batch.events[0], driver, new AbortController().signal);
    }
    assert.ok(seen.includes('REVIVE')); assert.ok(seen.includes('DOWNED')); assert.ok(seen.includes('+5'));
    assert.equal(driver.duration('moveDuration'), 0);
  } finally { dom.window.close(); }
});

test('controller separates authoritative state, locks input, streams logs, and New Match cancels playback', async () => {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main');
  const gate = deferred(), f = clone(fixtures.Attack), next = clone(fixtures.Move.start);
  const game = mountArena(root, { getGame: async () => f.start, createAiDemo: async () => next,
    command: async () => ({ ...f.final, presentation: f.batch }) },
  { registry: new PresentationRegistry(() => gate.promise), driver: {} });
  try {
    await game.whenIdle(); root.querySelector('[data-arena="end"]').click(); await tick();
    assert.equal(game.authoritative.units.find((u) => u.id === 'red-knight').hp, 12);
    assert.equal(game.state.units.find((u) => u.id === 'red-knight').hp, 18);
    assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
    assert.equal(root.querySelector('[data-arena="reset"]').disabled, false);
    assert.match(root.querySelector('.arena-battle-log').textContent, /damage/);
    const old = game.whenIdle(); root.querySelector('[data-arena="reset"]').click(); await game.whenIdle();
    gate.resolve(); await old;
    assert.equal(visualSignature(game.state), visualSignature(next));
    assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
  } finally { game.destroy(); dom.window.close(); }
});

test('destroy during pending API request cannot render into another route', async () => {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main'), gate = deferred();
  const game = mountArena(root, { getGame: () => gate.promise });
  game.destroy(); root.innerHTML = 'Other route'; gate.resolve(fixtures.Move.start);
  await game.whenIdle(); assert.equal(root.textContent, 'Other route'); dom.window.close();
});

test('lab loads locally, invokes shared handler, and resets fixture', async () => {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main');
  const lab = mountPresentationLab(root);
  try {
    await lab.whenIdle(); await tick();
    root.querySelector('[data-instant]').checked = true;
    for (const name of Object.keys(fixtures)) {
      root.querySelector(`[data-effect="${name}"]`).click(); await tick(); await lab.whenIdle();
      assert.match(root.querySelector('[data-event-json]').textContent, /arena-presentation-events-v1/);
      assert.equal(root.querySelectorAll('[data-lab-game] .arena-tile').length, 45);
    }
    root.querySelector('[data-effect="Revive"]').click(); await tick(); await lab.whenIdle();
    assert.equal(root.querySelector('[data-unit-id="blue-mage"]').textContent.includes('DOWNED'), false);
    root.querySelector('[data-lab-reset]').click(); await tick(); await lab.whenIdle();
    assert.equal(root.querySelector('[data-unit-id="blue-mage"]').textContent.includes('DOWNED'), true);
  } finally { lab.destroy(); dom.window.close(); }
});

test('resume waits for an abandoned server command then refreshes authoritative state', async () => {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main');
  const gate = deferred(), f = clone(fixtures.Attack); let server = f.start, reads = 0;
  const game = mountArena(root, {
    getGame: async () => { reads++; return clone(server); },
    command: async () => { await gate.promise; server = f.final; return { ...f.final, presentation: f.batch }; },
  }, { instant: true });
  try {
    await game.whenIdle(); root.querySelector('[data-arena="end"]').click();
    game.cancel(); const resumed = game.resume(); await tick();
    assert.equal(reads, 1);
    gate.resolve(); await resumed;
    assert.equal(reads, 2); assert.equal(visualSignature(game.state), visualSignature(f.final));
    assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
  } finally { game.destroy(); dom.window.close(); }
});
