import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import fixtures from '../src/js/arena-ai-playback-fixtures.json' with { type: 'json' };
import effects from '../src/js/arena-lab-fixtures.json' with { type: 'json' };
import { actionGroups, ArenaPresentationEngine, PresentationRegistry, visualSignature } from '../src/js/arena-presentation.js';
import { ArenaAnimationDriver, ARENA_TIMINGS } from '../src/js/arena-animation.js';
import { mountArena } from '../src/js/arena.js';
import { mountPresentationLab } from '../src/js/arena-presentation-lab.js';

const tick = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
const gate = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };

for (const [provider, count] of [['heuristic', 5], ['heuristic-v2', 4]]) {
  test(`${provider}: executed commands define counters; effects and two-AP Snipe do not add actions`, () => {
    const f = fixtures[provider], groups = actionGroups(f.batch.events, f.final.controllers).filter(g => g.ai);
    assert.equal(groups.length, count);
    assert.deepEqual(groups.map(g => [g.index, g.total]), Array.from({ length: count }, (_, i) => [i + 1, count]));
    assert.equal(groups.reduce((ap, g) => ap + g.events[0].ap_before - g.events[0].ap_after, 0), 5);
  });

  test(`${provider}: real response stays behind each handler, including AP, turn, log, focus and input lock`, async () => {
    const f = structuredClone(fixtures[provider]), dom = new JSDOM('<main></main>');
    const root = dom.window.document.querySelector('main'), started = [], gates = f.batch.events.map(gate);
    const game = mountArena(root, { getGame: async () => f.start, command: async () => ({ ...f.final, presentation: f.batch }) }, {
      driver: {}, registry: new PresentationRegistry(event => { started.push(event); return gates[started.length - 1].promise; }),
    });
    try {
      await game.whenIdle();
      root.querySelector('[data-unit-id="blue-ranger"]').closest('button').click();
      root.querySelector('[data-arena="end"]').click(); await tick();
      assert.equal(started.length, 1);
      assert.equal(game.state.state_hash, f.start.state_hash);
      assert.equal(game.authoritative.state_hash, f.final.state_hash);
      for (let i = 0; i < f.batch.events.length; i++) {
        const event = f.batch.events[i];
        assert.equal(started.length, i + 1);
        assert.equal(game.state.action_points_remaining, event.ap_before);
        assert.equal(game.state.active_player_id, event.acting_player);
        assert.equal(game.state.battle_log.length, i + 1);
        assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
        assert.equal(root.querySelector('.arena-selected [data-unit-id]').dataset.unitId, 'blue-ranger');
        if (event.actor_id) {
          assert.equal(root.querySelector('.arena-acting [data-unit-id]').dataset.unitId, event.actor_id);
          assert.match(root.querySelector('.arena-playback-status').textContent, new RegExp(`Action ${i} / ${count}`));
        }
        gates[i].resolve(); await tick();
      }
      await game.whenIdle();
      assert.equal(visualSignature(game.state), visualSignature(f.final));
      assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
      assert.equal(root.querySelector('.arena-acting'), null);
    } finally { game.destroy(); dom.window.close(); }
  });
}

for (const cancelAt of ['handler', 'minimum', 'pause']) test(`cancellation in action 2 ${cancelAt} prevents actions 3–5`, async () => {
  const f = fixtures.heuristic, blocker = gate(), reached = gate();
  let state = structuredClone(f.start), index = 0, commits = 0;
  const started = [];
  const block = () => { reached.resolve(); return blocker.promise; };
  const engine = new ArenaPresentationEngine({
    getState: () => state, setState: s => { state = s; commits++; },
    onGroup: g => { index = g?.index || 0; },
    registry: new PresentationRegistry(e => { started.push(e); if (index === 2 && cancelAt === 'handler') return block(); }),
    driver: { duration: () => 1000,
      wait: () => index === 2 && cancelAt === 'minimum' ? block() : Promise.resolve(),
      delay: () => index === 2 && cancelAt === 'pause' ? block() : Promise.resolve() },
  });
  const playing = engine.play(f.batch, f.final);
  await reached.promise; engine.cancel(); const before = commits;
  blocker.resolve(); await playing;
  assert.equal(commits, before);
  assert.equal(started.filter(e => e.actor_id).length, 2);
});

test('terminal feedback belongs to its command and excludes later actions', async () => {
  const f = structuredClone(effects.Victory);
  f.final.controllers = { blue: 'heuristic_ai', red: 'human' };
  f.batch.events.push(effects.Move.batch.events[0]);
  const groups = actionGroups(f.batch.events, f.final.controllers);
  assert.equal(groups.length, 1); assert.equal(groups[0].total, 1);
  assert.deepEqual(groups[0].events.map(e => e.type), ['attack', 'victory']);
  let state = f.start;
  const gates = [gate(), gate()], started = [];
  const engine = new ArenaPresentationEngine({ getState: () => state, setState: s => { state = s; }, driver: {},
    registry: new PresentationRegistry(e => { started.push(e.type); return gates[started.length - 1].promise; }) });
  const playback = engine.play(f.batch, f.final);
  assert.equal(state.winner_player_id, null);
  gates[0].resolve(); await tick(); assert.equal(state.winner_player_id, null);
  gates[1].resolve(); await playback;
  assert.deepEqual(started, ['attack', 'victory']); assert.equal(state.winner_player_id, 'blue');
});

for (const reducedMotion of [false, true]) test(`clock remains readable without Web Animations, reduced motion ${reducedMotion}`, async () => {
  const dom = new JSDOM('<main></main>');
  try {
    const driver = new ArenaAnimationDriver(dom.window.document.querySelector('main'), { reducedMotion });
    assert.equal(driver.duration('aiActionMinDuration'), 1000);
    let finished = false;
    const controller = new AbortController();
    const waiting = driver.delay('aiBetweenActionPause', controller.signal).then(() => { finished = true; });
    await tick(); assert.equal(finished, false);
    controller.abort(); await waiting; assert.equal(finished, true); assert.equal(driver.cleanups.size, 0);
    driver.speed = 2; assert.equal(driver.duration('aiBetweenActionPause'), 125);
    driver.instant = true; assert.equal(driver.duration('aiActionMinDuration'), 0);
    await driver.delay('aiActionMinDuration', new AbortController().signal);
  } finally { dom.window.close(); }
});

test('sample AI turn uses shared controller and instant speed reaches its final checkpoint', async () => {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main');
  const lab = mountPresentationLab(root);
  try {
    await lab.whenIdle(); root.querySelector('[data-instant]').checked = true;
    root.querySelector('[data-effect="Play sample AI turn"]').click(); await lab.whenIdle();
    assert.match(root.querySelector('.arena-status').textContent, /Blue Team.*5 \/ 5 AP/);
    assert.equal(root.querySelectorAll('.arena-battle-log li').length, 7);
    assert.equal(root.querySelector('[data-unit-id="blue-mage"]').closest('button').classList.contains('arena-downed'), true);
  } finally { lab.destroy(); dom.window.close(); }
});

test('normal AI pacing targets 1.25 seconds per short action without changing human animation timings', () => {
  assert.equal(ARENA_TIMINGS.aiActionMinDuration + ARENA_TIMINGS.aiBetweenActionPause, 1250);
  assert.equal(ARENA_TIMINGS.betweenActionDelay, 55);
  assert.equal(ARENA_TIMINGS.movePerTile, 110);
});

test('missing presentation from an old server is visible instead of silently snapping', async () => {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main');
  const f = fixtures.heuristic;
  const game = mountArena(root, { getGame: async () => f.start, command: async () => f.final });
  try {
    await game.whenIdle(); root.querySelector('[data-arena="end"]').click(); await game.whenIdle();
    assert.match(root.querySelector('[role="alert"]').textContent, /no animation sequence/);
    assert.equal(game.state.state_hash, f.final.state_hash);
  } finally { game.destroy(); dom.window.close(); }
});
