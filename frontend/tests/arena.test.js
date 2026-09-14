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

test('Luna is the only match entry and New Match selects OpenAI even from an existing offline match', async (t) => {
  const state = fixture();
  state.controllers = { blue: 'human', red: 'heuristic-v2_ai' };
  const providers = [];
  const { root, click } = await setup(t, { state, overrides: {
    createAiDemo: async (provider) => { providers.push(provider); return { ...structuredClone(state), controllers: { blue: 'human', red: 'openai_ai' } }; },
  } });
  assert.deepEqual([...root.querySelectorAll('[data-arena^="demo"]')].map(b => b.dataset.arena), ['demo-openai']);
  assert.doesNotMatch(root.textContent, /usage charges|External provider required|Experimental AI|Local Qwen|Configured AI/);
  await click('[data-arena="reset"]');
  assert.match(root.querySelector('.arena-mode').textContent, /OpenAI Luna/);
  await click('[data-arena="demo-openai"]');
  assert.deepEqual(providers, ['openai', 'openai']);
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
  assert.match(root.querySelector('.arena-details').textContent, /DOWNED/);
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
  assert.equal(root.querySelector('[data-arena="demo-openai"]').textContent, 'OpenAI Luna');
  await click('[data-arena="demo-openai"]');
  assert.equal(root.querySelectorAll('.arena-tile').length, 45);
  assert.equal(root.querySelectorAll('.arena-blocked').length, 4);
  assert.equal(root.querySelectorAll('.arena-bonus').length, 6);
  assert.equal(root.querySelectorAll('.arena-tile.arena-team-blue').length, 5);
  assert.equal(root.querySelectorAll('.arena-tile.arena-team-red').length, 5);
  assert.match(root.textContent, /Blue Team · Turn 0 · 5 \/ 5 AP/);
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
  assert.match(root.querySelector('.arena-details').textContent, /knight/);
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
  assert.match(root.textContent, /Red Team · Turn 0 · 5 \/ 5 AP/);
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
  assert.match(root.querySelector('.arena-details').textContent, /Red Team/);
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
  assert.match(root.querySelector('.arena-status').textContent, /Blue Team.*Turn 1/);
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
  test(`Arena ${provider} pending turn disables controls and displays fallback actions safely`, async (t) => {
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
    assert.match(root.textContent, /Heuristic fallback/);
    assert.match(root.textContent, /red-ranger attack <img src=x>/);
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
  assert.equal(root.querySelector('.arena-experimental'), null);
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

test('New Match selects Luna after refreshing an old heuristic match and clears the battle log', async (t) => {
  const state = { ...fixture(), controllers: { blue: 'human', red: 'heuristic_ai' },
    battle_log: [{ id: 1, text: 'Blue Team Knight moved to (2, 1)' }] };
  let provider = 'not called';
  const { root, click } = await setup(t, { state, overrides: {
    createAiDemo: async (name) => { provider = name; return { ...state, battle_log: [] }; },
  } });
  assert.match(root.querySelector('.arena-mode').textContent, /You are Blue/);
  assert.match(root.querySelector('.arena-battle-log').textContent, /moved to/);
  await click('[data-arena="reset"]');
  assert.equal(provider, 'openai');
  assert.doesNotMatch(root.querySelector('.arena-battle-log').textContent, /moved to/);
});

test('battle log escapes server text and winner displays reason with a reset', async (t) => {
  const state = { ...fixture(), winner_player_id: 'blue', terminal_reason: 'Core destroyed',
    battle_log: [{ id: 1, text: '<img src=x> attacked' }] };
  const { root, click } = await setup(t, { state, overrides: { createAiDemo: async () => fixture() } });
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
