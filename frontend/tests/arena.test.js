import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import { mountArena } from '../src/js/arena.js';
import { mountEnvironments } from '../src/js/environments.js';
import { createArenaApi } from '../src/js/api/arena.js';
import { ApiError } from '../src/js/api/game.js';
import { arenaIcon } from '../src/js/arena-icons.js';

function fixture() {
  const stats = { knight: [18, 6, 1, 2], ranger: [10, 5, 3, 3], mage: [9, 6, 2, 2], cleric: [11, 3, 2, 2] };
  return {
    environment: 'arena', turn: 0, active_player_id: 'blue', action_points_remaining: 5, winner_player_id: null,
    players: [{ id: 'blue', name: 'Blue Team' }, { id: 'red', name: 'Red Team' }],
    board: { width: 9, height: 5, tiles: Array.from({ length: 45 }, (_, i) => ({
      x: i % 9, y: Math.floor(i / 9), terrain: [12, 14, 30, 32].includes(i) ? 'blocked' : 'floor',
      bonus: ({ 4: 'power', 40: 'power', 20: 'ward', 24: 'ward', 21: 'siege', 23: 'siege' })[i] || null,
    })) },
    units: ['blue', 'red'].flatMap((owner_id) => Object.entries(stats).map(([unit_type, [hp, damage, attack_range, move_range]], i) => ({
      id: `${owner_id}-${unit_type}`, owner_id, unit_type, hp, max_hp: hp, status: 'active',
      abilities: Object.fromEntries(['move', 'attack', ...({knight:['shield_bash'], ranger:['snipe'], mage:['fireball'], cleric:['heal','revive']}[unit_type]), 'finish'].map((a) => [a, {ap_cost: ['snipe','fireball','revive'].includes(a) ? 2 : 1}])),
      x: owner_id === 'blue' ? 1 : 7, y: [1, 0, 3, 4][i],
      stats: { hp, damage, attack_range, move_range, heal_amount: unit_type === 'cleric' ? 5 : 0, heal_range: 2 },
      actions: { move: owner_id === 'blue' ? [{ x: 2, y: 1 }] : [], attack: [], heal: [], finish: [], revive: [], shield_bash: [], snipe: [], fireball: [] },
    }))),
    cores: ['blue', 'red'].map((owner_id) => ({ id: `${owner_id}-core`, owner_id, x: owner_id === 'blue' ? 0 : 8, y: 2, hp: 30, max_hp: 30 })),
  };
}

async function setup(t, { state = fixture(), overrides = {} } = {}) {
  const dom = new JSDOM('<main id="app"></main>');
  t.after(() => dom.window.close());
  const root = dom.window.document.querySelector('#app');
  const calls = [];
  const api = {
    getGame: async () => structuredClone(state),
    createDemo: async () => structuredClone(state),
    createAiDemo: async () => structuredClone(state),
    command: async (...args) => { calls.push(args); return structuredClone(state); },
    ...overrides,
  };
  const game = mountArena(root, api);
  t.after(() => game.destroy());
  await game.whenIdle();
  async function click(selector) {
    const target = root.querySelector(selector);
    assert.ok(target, `Missing ${selector}`);
    target.click();
    await game.whenIdle();
  }
  return { root, game, calls, click, dom };
}

const tile = (x, y) => `[data-arena="tile"][data-x="${x}"][data-y="${y}"]`;
const mode = (name) => `[data-mode="${name}"]`;

test('ability information works for an unavailable Bash without selecting or executing an action', async (t) => {
  const { root, click, calls, dom } = await setup(t);
  await click(tile(1, 1));
  assert.equal(root.querySelector(mode('shield_bash')).disabled, true);
  const help = root.querySelector('[aria-label="About Shield Bash"]');
  assert.equal(help.disabled, false);
  help.click();
  assert.equal(help.getAttribute('aria-expanded'), 'true');
  assert.match(root.querySelector('#arena-help-shield_bash').textContent, /4 base damage.*adjacent.*one tile.*blocked.*Cannot target Cores/s);
  assert.equal(root.querySelector('[data-mode][aria-pressed="true"]'), null);
  assert.equal(calls.length, 0);
  help.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  assert.equal(help.getAttribute('aria-expanded'), 'false');
  help.click(); help.click();
  assert.equal(help.getAttribute('aria-expanded'), 'false');
});

test('three public modes are available and New Match preserves the current provider', async (t) => {
  const state = fixture();
  state.controllers = { blue: 'human', red: 'heuristic-v2_ai' };
  const providers = [];
  const { root, click } = await setup(t, { state, overrides: {
    createAiDemo: async (provider) => { providers.push(provider); return { ...structuredClone(state), controllers: { blue: 'human', red: `${provider}_ai` } }; },
  } });
  assert.deepEqual([...root.querySelectorAll('[data-arena^="demo"]')].map(b => b.dataset.arena), ['demo-ai-v2', 'demo-openai', 'demo-observer']);
  assert.doesNotMatch(root.textContent, /usage charges|External provider required|Experimental AI|Local Qwen|Configured AI/);
  await click('[data-arena="reset"]');
  assert.match(root.querySelector('.arena-mode').textContent, /Human vs Heuristic/);
  await click('[data-arena="demo-openai"]');
  assert.deepEqual(providers, ['heuristic-v2', 'openai']);
});

test('each class exposes only its server-described abilities and AP costs', async (t) => {
  for (const [y, actions] of [[1, ['move', 'attack', 'shield_bash', 'finish']],
    [0, ['move', 'attack', 'snipe', 'finish']], [3, ['move', 'attack', 'fireball', 'finish']],
    [4, ['move', 'attack', 'heal', 'revive', 'finish']]]) {
    const { root, click } = await setup(t);
    await click(tile(1, y));
    assert.deepEqual([...root.querySelectorAll('[data-mode]')].map((b) => b.dataset.mode), actions);
    for (const action of actions) {
      assert.match(root.querySelector(mode(action)).textContent,
        new RegExp(`${['snipe', 'fireball', 'revive'].includes(action) ? 2 : 1} AP`));
    }
  }
});

for (const [action, actorIndex, targetId, cost] of [
  ['shield_bash', 0, 'red-knight', 1], ['snipe', 1, 'red-knight', 2],
  ['revive', 3, 'blue-mage', 2], ['finish', 0, 'red-mage', 1],
]) {
  test(`${action} uses explicit left-click target and renders authoritative result`, async (t) => {
    const state = fixture();
    const actor = state.units[actorIndex];
    const target = state.units.find((u) => u.id === targetId);
    actor.actions[action] = [targetId];
    if (['revive', 'finish'].includes(action)) { target.hp = 0; target.status = 'downed'; }
    const updated = structuredClone(state);
    const after = updated.units.find((u) => u.id === targetId);
    if (action === 'revive') { after.hp = 5; after.status = 'active'; }
    if (action === 'finish') updated.units = updated.units.filter((u) => u.id !== targetId);
    if (action === 'shield_bash') { after.x = 8; after.hp -= 4; }
    if (action === 'snipe') after.hp -= 8;
    updated.action_points_remaining -= cost;
    let received;
    const { root, click } = await setup(t, { state, overrides: {
      command: (...args) => { received = args; return updated; },
    } });
    if (target.status === 'downed') assert.match(root.querySelector(tile(target.x, target.y)).textContent, /DOWNED/);
    await click(tile(actor.x, actor.y));
    await click(mode(action));
    await click(tile(target.x, target.y));
    assert.deepEqual(received, [action, 'blue', { unit_id: actor.id, target_id: targetId }]);
    assert.match(root.querySelector('.arena-status').textContent, new RegExp(`${5 - cost} / 5 AP`));
    if (action === 'revive') {
      assert.match(root.querySelector(tile(target.x, target.y)).textContent, /5\/9 HP/);
      assert.doesNotMatch(root.querySelector(tile(target.x, target.y)).textContent, /DOWNED/);
    }
    if (action === 'finish') assert.doesNotMatch(root.querySelector(tile(target.x, target.y)).textContent, /mage/);
    if (action === 'shield_bash') assert.match(root.querySelector(tile(8, 1)).textContent, /knight/);
  });
}

test('Fireball selects empty impact tile, shows friendly-fire guidance and returned downed caster', async (t) => {
  const state = fixture();
  state.units[2].actions.fireball = [{ x: 2, y: 3 }];
  const updated = structuredClone(state);
  updated.units[2].hp = 0;
  updated.units[2].status = 'downed';
  Object.keys(updated.units[2].actions).forEach((key) => { updated.units[2].actions[key] = []; });
  updated.action_points_remaining = 3;
  let received;
  const { root, click } = await setup(t, { state, overrides: {
    command: (...args) => { received = args; return updated; },
  } });
  await click(tile(1, 3));
  assert.match(root.textContent, /including allies and the caster/);
  await click(mode('fireball'));
  assert.equal(root.querySelectorAll('.arena-legal').length, 1);
  await click(tile(2, 3));
  assert.deepEqual(received, ['fireball', 'blue', { unit_id: 'blue-mage', target_position: { x: 2, y: 3 } }]);
  assert.match(root.querySelector(tile(1, 3)).getAttribute('aria-label'), /DOWNED/);
  assert.match(root.querySelector('.arena-selected-summary').textContent, /DOWNED/);
  assert.ok([...root.querySelectorAll('[data-mode]')].every((b) => b.disabled));
  assert.match(root.querySelector('.arena-status').textContent, /3 \/ 5 AP/);
});

test('one AP preserves basic actions but server disables a two AP ability', async (t) => {
  const state = fixture();
  state.action_points_remaining = 1;
  const { root, click } = await setup(t, { state });
  await click(tile(1, 0));
  assert.equal(root.querySelector(mode('move')).disabled, false);
  assert.equal(root.querySelector(mode('snipe')).disabled, true);
});

test('Fireball unlisted impact never sends a request', async (t) => {
  const state = fixture();
  state.units[2].actions.fireball = [{ x: 2, y: 3 }];
  const { root, calls, click } = await setup(t, { state });
  await click(tile(1, 3));
  await click(mode('fireball'));
  await click(tile(4, 4));
  assert.equal(calls.length, 0);
  assert.match(root.querySelector('[role="alert"]').textContent, /legal target/);
});

test('Arena demo creation renders all tiles, classes, Cores, bonuses, HP and active player', async (t) => {
  const { root, click } = await setup(t, { overrides: {
    getGame: () => { throw new ApiError('no_game', 'Create demo', 404); },
  } });
  assert.equal(root.querySelector('[data-arena="demo-openai"]').textContent, 'Human vs OpenAI Luna');
  await click('[data-arena="demo-openai"]');
  assert.equal(root.querySelectorAll('.arena-tile').length, 45);
  assert.equal(root.querySelectorAll('.arena-blocked').length, 4);
  assert.equal(root.querySelectorAll('.arena-bonus').length, 6);
  assert.equal(root.querySelectorAll('.arena-tile.arena-team-blue').length, 5);
  assert.equal(root.querySelectorAll('.arena-tile.arena-team-red').length, 5);
  assert.match(root.textContent, /Blue Team turn5 \/ 5 AP/);
  for (const name of ['knight', 'ranger', 'mage', 'cleric', 'core', 'power', 'ward', 'siege']) {
    assert.match(root.textContent, new RegExp(name));
  }
  assert.match(root.querySelector(tile(0, 2)).textContent, /30\/30 HP/);
});

test('all original placeholder shapes are distinct inline SVGs', () => {
  const icons = ['knight', 'ranger', 'mage', 'cleric', 'core', 'power', 'ward', 'siege', 'blocked'].map(arenaIcon);
  assert.equal(new Set(icons).size, 9);
  assert.ok(icons.every((icon) => icon.startsWith('<svg') && !icon.includes('http')));
});

test('select unit, choose Move, click destination uses server command and returned AP', async (t) => {
  const state = fixture();
  const updated = structuredClone(state);
  updated.units[0].x = 2;
  updated.action_points_remaining = 4;
  let received;
  const { root, click } = await setup(t, { state, overrides: {
    command: (...args) => { received = args; return updated; },
  } });
  await click(tile(1, 1));
  assert.match(root.querySelector('.arena-selected-summary').textContent, /knight/);
  await click(mode('move'));
  assert.equal(root.querySelectorAll('.arena-legal').length, 1);
  await click(tile(2, 1));
  assert.deepEqual(received, ['move', 'blue', { unit_id: 'blue-knight', destination: { x: 2, y: 1 } }]);
  assert.match(root.querySelector('.arena-status').textContent, /4 \/ 5 AP/);
  assert.ok(root.querySelector(`${tile(2, 1)}.arena-selected`));
});

test('Attack targets enemy unit and accepts authoritative damage/removal', async (t) => {
  const state = fixture();
  state.units[0].actions.attack = ['red-knight'];
  const updated = structuredClone(state);
  updated.units = updated.units.filter((u) => u.id !== 'red-knight');
  updated.action_points_remaining = 4;
  let received;
  const { root, click } = await setup(t, { state, overrides: { command: (...args) => { received = args; return updated; } } });
  await click(tile(1, 1));
  await click(mode('attack'));
  await click(tile(7, 1));
  assert.deepEqual(received, ['attack', 'blue', { unit_id: 'blue-knight', target_id: 'red-knight' }]);
  assert.doesNotMatch(root.querySelector(tile(7, 1)).textContent, /knight/);
});

test('Core attack displays winner and disables gameplay without End Turn', async (t) => {
  const state = fixture();
  state.units[0].actions.attack = ['red-core'];
  const updated = structuredClone(state);
  updated.active_player_id = null;
  updated.winner_player_id = 'blue';
  updated.cores[1].hp = 0;
  const calls = [];
  const { root, click } = await setup(t, { state, overrides: { command: (...args) => { calls.push(args); return updated; } } });
  await click(tile(1, 1));
  await click(mode('attack'));
  await click(tile(8, 2));
  assert.equal(calls.length, 1);
  assert.equal(calls[0][2].target_id, 'red-core');
  assert.match(root.textContent, /Blue Team wins!/);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
  assert.ok([...root.querySelectorAll('.arena-tile')].every((b) => b.disabled));
});

test('Heal friendly and self are explicit left-click actions', async (t) => {
  for (const [target, x, y] of [['blue-knight', 1, 1], ['blue-cleric', 1, 4]]) {
    const state = fixture();
    state.units[3].actions.heal = [target];
    const { root, calls, click } = await setup(t, { state });
    await click(tile(1, 4));
    assert.equal(root.querySelector(mode('heal')).disabled, false);
    await click(mode('heal'));
    await click(tile(x, y));
    assert.deepEqual(calls, [['heal', 'blue', { unit_id: 'blue-cleric', target_id: target }]]);
  }
});

test('End Turn uses explicit actor, restores returned AP and clears selection', async (t) => {
  const state = fixture();
  const updated = structuredClone(state);
  updated.active_player_id = 'red';
  const calls = [];
  const { root, click } = await setup(t, { state, overrides: { command: (...args) => { calls.push(args); return updated; } } });
  await click(tile(1, 1));
  await click('[data-arena="end"]');
  assert.deepEqual(calls, [['end_turn', 'blue']]);
  assert.equal(root.querySelector('.arena-selected'), null);
  assert.match(root.textContent, /Red Team turn5 \/ 5 AP/);
});

test('zero AP leaves End Turn enabled while actions are disabled', async (t) => {
  const state = fixture();
  state.action_points_remaining = 0;
  state.units.forEach((u) => { u.actions = { move: [], attack: [], heal: [], finish: [], revive: [], shield_bash: [], snipe: [], fireball: [] }; });
  const { root, calls, click } = await setup(t, { state });
  await click(tile(1, 1));
  for (const action of ['move', 'attack', 'shield_bash', 'finish']) assert.equal(root.querySelector(mode(action)).disabled, true);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
  assert.equal(calls.length, 0);
});

test('illegal targets do not send requests; cancel allows selecting another unit', async (t) => {
  const { root, calls, click } = await setup(t);
  await click(tile(1, 1));
  await click(mode('move'));
  await click(tile(7, 1));
  assert.equal(calls.length, 0);
  assert.match(root.querySelector('[role="alert"]').textContent, /legal target/);
  await click('[data-arena="cancel"]');
  await click(tile(7, 1));
  assert.match(root.querySelector('.arena-selected-summary').textContent, /Red Team/);
  assert.equal(root.querySelector(mode('move')).disabled, true);
});

test('server rejection preserves board and AP with readable error', async (t) => {
  const { root, click } = await setup(t, { overrides: {
    command: () => { throw new ApiError('invalid_command', 'No AP remaining', 422); },
  } });
  await click(tile(1, 1));
  await click(mode('move'));
  await click(tile(2, 1));
  assert.match(root.querySelector('[role="alert"]').textContent, /No AP remaining/);
  assert.match(root.querySelector('.arena-status').textContent, /5 \/ 5 AP/);
  assert.match(root.querySelector(tile(1, 1)).textContent, /knight/);
});

test('in-flight command disables controls and prevents duplicate submissions', async (t) => {
  let resolve;
  let count = 0;
  const { root, game, click } = await setup(t, { overrides: {
    command: () => { count++; return new Promise((done) => { resolve = done; }); },
  } });
  await click(tile(1, 1));
  root.querySelector('[data-arena="end"]').click();
  root.querySelector('[data-arena="end"]').click();
  assert.equal(count, 1);
  assert.ok([...root.querySelectorAll('button')].every((b) => b.disabled));
  resolve(fixture());
  await game.whenIdle();
});

test('new Arena Demo clears selection and action even with same active player', async (t) => {
  const { root, click } = await setup(t);
  await click(tile(1, 1));
  await click(mode('move'));
  await click('[data-arena="demo-openai"]');
  assert.equal(root.querySelector('.arena-selected'), null);
  assert.equal(root.querySelector('[data-mode]'), null);
});

test('untrusted player names are escaped in labels and markup', async (t) => {
  const state = fixture();
  state.players[0].name = '<img src=x onerror=alert(1)>';
  const { root } = await setup(t, { state });
  assert.equal(root.querySelector('img'), null);
  assert.match(root.textContent, /<img src=x/);
});

test('environment selector preserves both roots and refreshes Arena when returning', async (t) => {
  const dom = new JSDOM('<main></main>');
  t.after(() => dom.window.close());
  const root = dom.window.document.querySelector('main');
  let empireReads = 0;
  let arenaReads = 0;
  const app = mountEnvironments(root, {
    getGame: () => { empireReads++; throw new ApiError('no_game', 'Create demo', 404); },
  }, { getGame: () => { arenaReads++; return fixture(); } });
  t.after(() => app.destroy());
  await app.empire.whenIdle();
  await app.arena.whenIdle();
  assert.equal(root.querySelector('[data-view="arena"]').hidden, false);
  assert.equal(root.querySelector('[data-view="empire"]').hidden, true);
  assert.equal(root.querySelector('[data-environment]').dataset.environment, 'arena');
  assert.equal(root.querySelector('[data-environment="arena"]').getAttribute('aria-pressed'), 'true');
  assert.equal(root.querySelector('[data-environment="arena"]').textContent, 'Arena');
  assert.equal(root.querySelector('[data-environment="empire"]').textContent, 'Empire');
  assert.match(root.textContent, /New Demo Game/);
  root.querySelector('[data-environment="arena"]').click();
  await app.arena.whenIdle();
  root.querySelector(tile(1, 1)).click();
  root.querySelector('[data-environment="empire"]').click();
  assert.equal(root.querySelector('[data-view="empire"]').hidden, false);
  root.querySelector('[data-environment="arena"]').click();
  assert.ok(root.querySelector('.arena-selected'));
  assert.equal(empireReads, 1);
  await app.arena.whenIdle();
  assert.equal(arenaReads, 3); // Initial load, explicit Arena selection, and return from Empire.
  assert.equal(root.querySelectorAll('.arena-tile').length, 45);
  assert.equal(root.querySelector('.arena-selected'), null); // Resync clears stale selection.
});

test('Arena API routes include explicit version and actor, respect public origin', async () => {
  const calls = [];
  const api = createArenaApi(async (...args) => { calls.push(args); return { ok: true, json: async () => ({ environment: 'arena' }) }; }, 'https://api.example.test/');
  await api.getGame();
  await api.createDemo();
  await api.command('move', 'blue', { unit_id: 'blue-ranger', destination: { x: 4, y: 0 } });
  assert.deepEqual(calls.map(([url]) => url), ['https://api.example.test/api/arena', 'https://api.example.test/api/arena/demo', 'https://api.example.test/api/arena/commands']);
  assert.equal(calls[0][1].method, 'GET');
  assert.deepEqual(JSON.parse(calls[2][1].body), { schema_version: 'arena-command-v2', type: 'arena_move', actor_id: 'blue', unit_id: 'blue-ranger', destination: { x: 4, y: 0 } });
});

test('Arena API reports HTTP, transport and unreadable response failures', async () => {
  for (const [fetcher, code] of [
    [async () => { throw new Error('offline'); }, 'connection_error'],
    [async () => ({ ok: false, status: 422, json: async () => ({ error: 'invalid_command', message: 'blocked' }) }), 'invalid_command'],
    [async () => ({ status: 502, json: async () => { throw new Error('html'); } }), 'invalid_response'],
  ]) await assert.rejects(createArenaApi(fetcher).getGame(), (error) => error.code === code);
});


test('Arena AI pending turn disables all controls then renders returned human state', async (t) => {
  const state = { ...fixture(), controllers: { blue: 'human', red: 'heuristic_ai' } };
  let finish;
  let requests = 0;
  const { root, game } = await setup(t, { state, overrides: {
    command: () => { requests++; return new Promise((resolve) => { finish = resolve; }); },
  } });
  root.querySelector('[data-arena="end"]').click();
  assert.match(root.textContent, /AI thinking/);
  assert.ok([...root.querySelectorAll('button')].every((b) => b.disabled));
  root.querySelector('[data-arena="end"]').click();
  assert.equal(requests, 1);
  finish({ ...state, turn: 1, units: state.units.map((u) => ({ ...u, hp: u.hp - 1 })) });
  await game.whenIdle();
  assert.doesNotMatch(root.textContent, /AI thinking/);
  assert.match(root.querySelector('.arena-status').textContent, /Blue Team/);
  assert.match(root.querySelector('.arena-mode').textContent, /Turn 1/);
  assert.match(root.querySelector(tile(1, 1)).textContent, /17\/18 HP/);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
});

test('Arena AI request errors clear pending state and allow refresh', async (t) => {
  const state = { ...fixture(), controllers: { blue: 'human', red: 'heuristic_ai' } };
  const { root, click } = await setup(t, { state, overrides: {
    command: async () => { throw new Error('Request failed'); },
  } });
  await click('[data-arena="end"]');
  assert.match(root.querySelector('[role="alert"]').textContent, /Request failed/);
  assert.doesNotMatch(root.textContent, /AI thinking/);
  assert.equal(root.querySelector('[data-arena="refresh"]').disabled, false);
});

test('Arena explicitly AI-controlled active player cannot issue human commands', async (t) => {
  const state = { ...fixture(), controllers: { blue: 'heuristic_ai', red: 'human' } };
  const { root } = await setup(t, { state });
  assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
  assert.ok([...root.querySelectorAll('.arena-tile')].every((b) => b.disabled));
  assert.equal(root.querySelector('[data-arena="demo-openai"]').disabled, false);
});

test('Arena client creates AI game without model/provider arguments', async () => {
  let request;
  const api = createArenaApi(async (...args) => { request = args; return { ok: true, json: async () => fixture() }; });
  await api.createAiDemo();
  assert.equal(request[0], '/api/arena/demo-ai');
  assert.equal(request[1].method, 'POST');
  assert.equal(request[1].body, undefined);
});

for (const provider of ['ollama', 'openai', 'configured']) {
  test(`Arena ${provider} API retains its explicit provider route`, async (t) => {
    let requested;
    const { click } = await setup(t, { overrides: {
      createAiDemo: async (name) => { requested = name; return fixture(); },
    } });
    if (provider === 'openai') {
      await click(`[data-arena="demo-${provider}"]`);
      assert.equal(requested, provider);
    }
    const calls = [];
    const api = createArenaApi(async (...args) => { calls.push(args); return { ok: true, json: async () => fixture() }; });
    await api.createAiDemo(provider);
    assert.equal(calls[0][0], `/api/arena/demo-ai/${provider}`);
  });
}

for (const provider of ['ollama', 'openai']) {
  test(`Arena ${provider} pending turn locks controls and retains fallback data without development UI`, async (t) => {
    const state = { ...fixture(), controllers: { blue: 'human', red: `${provider}_ai` } };
    let finish;
    const { root, game } = await setup(t, { state, overrides: {
      command: () => new Promise((resolve) => { finish = resolve; }),
    } });
    root.querySelector('[data-arena="end"]').click();
    assert.match(root.textContent, /AI thinking/);
    assert.ok([...root.querySelectorAll('button')].every((b) => b.disabled));
    finish({ ...state, turn: 1, ai_turns: [{ ap_spent: 1, provider_type: 'arena-heuristic-v1',
      inference: { actual_provider: 'heuristic', requested_provider: provider, fallback_used: true, error_category: 'timeout' },
      actions_attempted: [{ executed: true, action: { type: 'attack', unit_id: 'red-ranger', target_id: '<img src=x>' } }],
    }] });
    await game.whenIdle();
    assert.equal(game.state.ai_turns[0].inference.fallback_used, true);
    assert.equal(game.state.ai_turns[0].actions_attempted[0].action.target_id, '<img src=x>');
    assert.doesNotMatch(root.textContent, /Heuristic fallback|AI turn details/);
    assert.equal(root.querySelector('img'), null);
    assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
  });
}

test('Arena URL opens Arena directly without creating a match or contacting a provider', async (t) => {
  const dom = new JSDOM('<main></main>', { url: 'http://localhost/arena' });
  t.after(() => dom.window.close());
  const root = dom.window.document.querySelector('main');
  let creates = 0;
  const app = mountEnvironments(root, { getGame: async () => { throw new ApiError('no_game', '', 404); } }, {
    getGame: async () => fixture(), createAiDemo: () => { creates++; },
  });
  t.after(() => app.destroy());
  await app.arena.whenIdle();
  assert.equal(root.querySelector('[data-view="arena"]').hidden, false);
  assert.equal(root.querySelectorAll('.arena-tile').length, 45);
  assert.equal(creates, 0);
  assert.equal(root.querySelector('.arena-experimental').open, false);
});

test('changing owned selection during Move clears old targets without a command', async (t) => {
  const { root, click, calls } = await setup(t);
  await click(tile(1, 1));
  await click(mode('move'));
  await click(tile(1, 0));
  assert.ok(root.querySelector(`${tile(1, 0)}.arena-selected`));
  assert.equal(root.querySelectorAll('.arena-legal').length, 0);
  assert.equal(calls.length, 0);
});

for (const action of ['attack', 'heal', 'revive']) {
  test(`${action} highlights exactly the backend targets with accessible labels`, async (t) => {
    const state = fixture();
    state.units[3].actions[action] = [action === 'attack' ? 'red-knight' : 'blue-knight'];
    const { root, click } = await setup(t, { state });
    await click(tile(1, 4));
    await click(mode(action));
    const targets = [...root.querySelectorAll('.arena-legal')];
    assert.equal(targets.length, 1);
    assert.match(targets[0].getAttribute('aria-label'), new RegExp(`legal ${action} target`));
  });
}

test('New Match preserves an old heuristic match and clears the battle log', async (t) => {
  const state = { ...fixture(), controllers: { blue: 'human', red: 'heuristic_ai' },
    battle_log: [{ id: 1, text: 'Blue Team Knight moved to (2, 1)' }] };
  let provider = 'not called';
  const { root, click } = await setup(t, { state, overrides: {
    createAiDemo: async (name) => { provider = name; return { ...state, battle_log: [] }; },
  } });
  assert.match(root.querySelector('.arena-mode').textContent, /You are Blue/);
  assert.match(root.querySelector('.arena-battle-log').textContent, /moved to/);
  await click('[data-arena="reset"]');
  assert.equal(provider, 'heuristic');
  assert.doesNotMatch(root.querySelector('.arena-battle-log').textContent, /moved to/);
});

test('battle log escapes server text and winner displays reason with a reset', async (t) => {
  const state = { ...fixture(), winner_player_id: 'blue', terminal_reason: 'Core destroyed',
    battle_log: [{ id: 1, text: '<img src=x> attacked' }] };
  const { root, click } = await setup(t, { state, overrides: { createDemo: async () => fixture() } });
  assert.equal(root.querySelector('img'), null);
  assert.match(root.querySelector('.arena-winner').textContent, /Core destroyed/);
  await click('[data-arena="reset"]');
  assert.equal(root.querySelector('.arena-winner'), null);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
});

test('session creation failure is visible and can be retried', async (t) => {
  const { root, click } = await setup(t, { overrides: {
    getGame: async () => { throw new ApiError('no_game', '', 404); },
    createAiDemo: async () => { throw new Error('Could not create Arena. Retry.'); },
  } });
  await click('[data-arena="demo-openai"]');
  assert.match(root.querySelector('[role="alert"]').textContent, /Could not create Arena/);
  assert.equal(root.querySelector('[data-arena="demo-openai"]').disabled, false);
});

test('board-first HUD keeps unit and abilities in a full-width deck, with rules below and a log-only rail', async (t) => {
  const { root, click } = await setup(t);
  const deck = root.querySelector('.arena-command-deck');
  assert.ok(root.querySelector('.arena-board').compareDocumentPosition(deck) & 4);
  assert.match(deck.textContent, /Select a Blue unit/);
  assert.ok(root.querySelector('.arena-details .arena-battle-log'));
  assert.equal(root.querySelector('.arena-details .arena-selected-summary'), null);
  assert.equal(root.querySelector('.arena-legend'), null);
  assert.equal(root.querySelectorAll('.arena-details > *').length, 1);
  assert.equal(root.querySelector('.arena-details details'), null);
  const rules = root.querySelector('.arena-view > .arena-rules');
  assert.equal(rules.open, false);
  assert.ok(deck.compareDocumentPosition(rules) & 4);
  assert.equal(root.querySelector('[data-arena="coordinates"]'), null);
  assert.doesNotMatch(root.textContent, /Development info|AI turn details/);
  for (const [y, kind, hp] of [[1,'knight',18],[0,'ranger',10],[3,'mage',9],[4,'cleric',11]]) {
    await click(tile(1,y));
    const summary = root.querySelector('.arena-command-deck .arena-selected-summary');
    assert.ok(summary.querySelector(`[data-class-art="${kind}"]`));
    assert.match(summary.textContent, new RegExp(`${hp}/${hp} HP`));
    assert.match(summary.textContent, /Move.*Damage.*Range/);
    assert.ok(root.querySelectorAll('.arena-command-deck [data-mode]').length >= 4);
    assert.equal(root.querySelectorAll('.arena-details [data-mode]').length, 0);
    assert.ok(root.querySelector('.arena-selected-art[role="img"]').getAttribute('aria-label').includes(kind));
  }
});

for (const [action, category, instruction] of [
  ['move','move',/highlighted destination/], ['attack','hostile',/highlighted enemy/],
  ['heal','support',/active ally/], ['revive','support',/DOWNED ally/], ['fireball','fire',/impact tile/],
]) test(`${action} exposes semantic targeting and context without changing legal targets`, async (t) => {
  const state = fixture(), unit = state.units[action === 'fireball' ? 2 : 3];
  unit.actions[action] = ['move','fireball'].includes(action) ? [{x:2,y:2}] : [action === 'attack' ? 'red-knight' : 'blue-knight'];
  const { root, click } = await setup(t, { state });
  await click(tile(unit.x,unit.y)); await click(mode(action));
  assert.equal(root.querySelectorAll(`.arena-legal.arena-target-${category}`).length,1);
  assert.match(root.querySelector('.arena-context').textContent,instruction);
  assert.match(root.querySelector('.arena-context h2').textContent,/AP/);
  await click('[data-arena="cancel"]');
  assert.equal(root.querySelectorAll('.arena-legal').length,0);
  assert.equal(root.querySelector('[data-arena="cancel"]'),null);
});

test('observer mode creates both AI seats without advancing and steps only on request', async (t) => {
  const observer = {...fixture(), controllers:{blue:'openai_ai',red:'openai_ai'}};
  let creates=0, turns=0, finish;
  const {root,game,click} = await setup(t,{overrides:{
    createObserverDemo:async()=>{creates++;return structuredClone(observer);},
    observerTurn:()=>{turns++;return new Promise(resolve=>{finish=resolve;});},
  }});
  await click('[data-arena="demo-observer"]');
  assert.equal(creates,1);assert.equal(turns,0);
  assert.match(root.querySelector('.arena-mode').textContent,/Observer mode/);
  assert.equal(root.querySelector('[data-arena="end"]'),null);
  assert.ok([...root.querySelectorAll('.arena-tile')].every(b=>b.disabled));
  root.querySelector('[data-arena="observer-turn"]').click();
  assert.equal(turns,1);assert.equal(root.querySelector('[data-arena="observer-turn"]').disabled,true);
  finish({...observer,active_player_id:'red'});await game.whenIdle();
  assert.equal(root.querySelector('[data-arena="observer-turn"]').disabled,false);
  assert.equal(turns,1);
  await click('[data-arena="reset"]');assert.equal(creates,2);
});

test('ability selection and Cancel retain keyboard focus in the deck', async (t) => {
  const { root, click, dom } = await setup(t);
  await click(tile(1,1));
  assert.equal(dom.window.document.activeElement,root.querySelector(tile(1,1)));
  await click(mode('move'));
  assert.equal(dom.window.document.activeElement,root.querySelector(mode('move')));
  await click('[data-arena="cancel"]');
  assert.equal(dom.window.document.activeElement,root.querySelector(mode('move')));
});

test('missing observer route gives a restart instruction instead of a generic failure', async () => {
  const api=createArenaApi(async()=>({ok:false,status:404,json:async()=>({detail:'Not Found'})}));
  for(const request of [()=>api.createObserverDemo(),()=>api.observerTurn()]) {
    await assert.rejects(request,error=>error.code==='observer_unavailable' && /docker compose restart api/.test(error.message) && /restart npm run dev/.test(error.message));
  }
});


test('Adaptive selector is idle, configures new sessions and New Match retains authoritative control', async (t) => {
  const calls = [];
  const state = fixture();
  state.controllers = {blue: 'human', red: 'openai_ai'};
  state.control_mode = 'full_turn';
  const ui = await setup(t, {state, overrides: {
    createAiDemo: async (provider, control) => {
      calls.push([provider, control]);
      return {...structuredClone(state), control_mode: control};
    },
  }});
  assert.equal(calls.length, 0);
  const select = ui.root.querySelector('[data-arena-control]');
  assert.equal(select.value, 'full_turn');
  assert.deepEqual([...select.options].map(o => o.value), ['full_turn', 'bounded_replan', 'stepwise']);
  select.value = 'bounded_replan';
  select.dispatchEvent(new ui.dom.window.Event('change', {bubbles: true}));
  assert.equal(calls.length, 0);
  await ui.click('[data-arena="demo-openai"]');
  assert.deepEqual(calls[0], ['openai', 'bounded_replan']);
  await ui.click('[data-arena="reset"]');
  assert.deepEqual(calls[1], ['openai', 'bounded_replan']);
});

test('Arena API passes explicit control mode in one creation request', async () => {
  const urls = [];
  const api = createArenaApi(async (url) => { urls.push(url); return {ok: true, json: async () => ({control_mode: url.split('control_mode=')[1]})}; });
  await api.createAiDemo('openai', 'bounded_replan');
  await api.createObserverDemo('stepwise');
  assert.deepEqual(urls, ['/api/arena/demo-ai/openai?control_mode=bounded_replan', '/api/arena/observer/demo?control_mode=stepwise']);
});

test('an old host cannot silently accept Adaptive while running strict control', async () => {
  const api = createArenaApi(async () => ({ok: true, json: async () => ({})}));
  await assert.rejects(api.createAiDemo('openai', 'bounded_replan'), error => error.code === 'control_unavailable');
});
