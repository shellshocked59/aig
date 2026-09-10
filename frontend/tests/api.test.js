import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ApiError, createGameApi } from '../src/js/api/game.js';

test('client sends explicit payloads to relative API routes, without actor or allocated city IDs', async () => {
  const calls = [];
  const returnedState = { game: { turn: 4 } };
  const api = createGameApi(async (path, options) => {
    calls.push({ path, options });
    return { ok: true, json: async () => returnedState };
  });
  const cases = [
    ['getGame', [], '', undefined, 'GET'],
    ['createDemoGame', [], '/demo'], ['startGame', [], '/start'],
    ['createAiDemoGame', [], '/demo/ai'],
    ['createLlmDemoGame', [], '/demo/llm'],
    ['moveUnit', ['u1', 2, 3], '/commands', { type: 'move_unit', unitId: 'u1', x: 2, y: 3 }],
    ['attackUnit', ['u1', 'u2'], '/commands', { type: 'attack_unit', attackerUnitId: 'u1', targetUnitId: 'u2' }],
    ['foundCity', ['u1', 'City'], '/commands', { type: 'found_city', settlerUnitId: 'u1', name: 'City' }],
    ['setProduction', ['c1', 'warrior'], '/commands', { type: 'set_city_production', cityId: 'c1', unitType: 'warrior' }],
    ['setProduction', ['c1', null], '/commands', { type: 'set_city_production', cityId: 'c1', unitType: null }],
    ['setResearch', ['archery'], '/commands', { type: 'set_research', technology: 'archery' }],
    ['setResearch', [null], '/commands', { type: 'set_research', technology: null }],
    ['endActivation', [], '/commands', { type: 'end_activation' }],
  ];
  for (const [name, args, suffix, payload, method = 'POST'] of cases) {
    assert.equal(await api[name](...args), returnedState);
    const { path, options } = calls.at(-1);
    assert.equal(path, `/api/game${suffix}`);
    assert.equal(options.method, method);
    assert.equal(options.cache, 'no-store');
    assert.deepEqual(options.body === undefined ? undefined : JSON.parse(options.body), payload);
  }
});

test('client preserves structured backend validation and no-game errors', async () => {
  for (const [status, error] of [[422, 'invalid_command'], [404, 'no_game'], [500, 'server_error']]) {
    const api = createGameApi(async () => ({ ok: false, status, json: async () => ({ error, message: 'Useful message' }) }));
    await assert.rejects(api.getGame, (failure) => failure instanceof ApiError && failure.code === error && failure.status === status && failure.message === 'Useful message');
  }
});

test('client sends reads and JSON commands to the configured API origin', async () => {
  const calls = [];
  const api = createGameApi(async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({}) };
  }, 'https://api.agentstrategy.online/');
  await api.getGame();
  await api.moveUnit('unit-1', 2, 3);
  assert.equal(calls[0].url, 'https://api.agentstrategy.online/api/game');
  assert.equal(calls[0].options.method, 'GET');
  assert.equal(calls[1].url, 'https://api.agentstrategy.online/api/game/commands');
  assert.equal(calls[1].options.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(calls[1].options.body), { type: 'move_unit', unitId: 'unit-1', x: 2, y: 3 });
});

test('client explains connection and non-JSON proxy failures', async () => {
  const offline = createGameApi(async () => { throw new TypeError('fetch failed'); });
  await assert.rejects(offline.getGame, { code: 'connection_error' });
  const invalid = createGameApi(async () => ({ status: 502, json: async () => { throw new SyntaxError(); } }));
  await assert.rejects(invalid.getGame, { code: 'invalid_response' });
});
