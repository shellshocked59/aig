import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import { mountGame } from '../src/js/game.js';
import { terrainSprites, unitSprites, resourceSprites, faction } from '../src/js/presentation.js';
import { ApiError } from '../src/js/api/game.js';
import { gameFixture } from './fixtures.js';

test('known camp has original icon in explored fog and no hidden camp icon', async (t) => {
  const state = gameFixture();
  const [known, hidden] = state.map.tiles;
  Object.assign(known, { explored: true, visible: false });
  Object.assign(hidden, { explored: false, visible: false });
  state.barbarianCamps = [
    { id: 'known', x: known.x, y: known.y, currently_visible: false, live_exists: null },
    { id: 'hidden', x: hidden.x, y: hidden.y, live_exists: true },
  ];
  const { root } = await setup(t, { state });
  assert.equal(root.querySelectorAll('.camp-icon').length, 1);
  assert.ok(root.querySelector('.fogged .camp-icon svg'));
  assert.match(root.querySelector('.camp-icon').title, /current status unknown/);
});

test('visible barbarian uses Warrior sprite and disappears after sight is lost', async (t) => {
  const state = gameFixture();
  Object.assign(state.units[2], { ownerId: 'barbarians', type: 'warrior', barbarian: true });
  const hidden = structuredClone(state);
  hidden.units = hidden.units.filter((u) => !u.barbarian);
  let reads = 0;
  const { root, click } = await setup(t, { state, overrides: {
    getGame: () => structuredClone(reads++ ? hidden : state),
  } });
  assert.ok(root.querySelector('.faction-barbarian .sprite-warrior'));
  assert.equal(faction('barbarians').name, 'Barbarians');
  await click('[data-action="refresh"]');
  assert.equal(root.querySelector('.piece.faction-barbarian'), null);
});

test('confirmed absent camps have no icon', async (t) => {
  const state = gameFixture();
  state.barbarianCamps = [{ id: 'gone', x: 0, y: 0, live_exists: false }];
  const { root } = await setup(t, { state });
  assert.equal(root.querySelector('.camp-icon'), null);
});

test('all five original resource icons render only on explored tiles', async (t) => {
  assert.deepEqual(Object.keys(resourceSprites), ['wheat', 'cattle', 'iron', 'gems', 'spices']);
  const state = gameFixture();
  Object.keys(resourceSprites).forEach((resource, index) => {
    Object.assign(state.map.tiles[index], { resource, explored: true, visible: false });
  });
  const { root } = await setup(t, { state });
  assert.equal(root.querySelectorAll('.fogged .resource-icon svg').length, 5);
  for (const name of ['Wheat', 'Cattle', 'Iron', 'Gems', 'Spices']) {
    assert.ok(root.querySelector(`.resource-icon[aria-label="${name}"]`));
  }
});

test('unexplored resource is excluded from DOM even in malformed fixture', async (t) => {
  const state = gameFixture();
  Object.assign(state.map.tiles[4], { resource: 'gems', terrain: null, explored: false, visible: false });
  const { root } = await setup(t, { state });
  assert.equal(root.querySelectorAll('.resource-icon').length, 0);
  assert.doesNotMatch(root.innerHTML, /Gems|gems|bc80eb/);
});

test('fog flags render unknown terrain and dim explored terrain', async (t) => {
  const state = gameFixture();
  state.map.tiles[4] = { ...state.map.tiles[4], terrain: null, explored: false, visible: false };
  state.map.tiles[5] = { ...state.map.tiles[5], explored: true, visible: false };
  const { root, click } = await setup(t, { state });
  assert.ok(root.querySelector('.unexplored .unknown-terrain'));
  assert.ok(root.querySelector('.fogged .sprite-water'));
  assert.match(root.querySelector('#tile-1-1').getAttribute('aria-label'), /Unexplored/);
  await click('#tile-1-1');
  assert.doesNotMatch(root.textContent, /undefined/);
});

test('remembered city renders without current population or production', async (t) => {
  const state = gameFixture();
  state.cities.push({ id: 'remembered', ownerId: 'B', x: 2, y: 1, currentlyVisible: false, liveExists: null });
  const { root, click } = await setup(t, { state });
  await click('[data-action="city"][data-id="remembered"]');
  const panel = root.querySelector('[aria-label="Selected city"]');
  assert.match(panel.textContent, /Current details unknown/);
  assert.doesNotMatch(panel.textContent, /Population|Building|undefined/);
});

test('refresh removes enemy units that left vision', async (t) => {
  const state = gameFixture();
  const hidden = structuredClone(state);
  hidden.units = hidden.units.filter((u) => u.ownerId === 'A');
  const { root, click } = await setup(t, { state, overrides: { getGame: (() => {
    let count = 0;
    return () => structuredClone(count++ ? hidden : state);
  })() } });
  assert.ok(root.querySelector('[data-id="unit-3"]'));
  await click('[data-action="refresh"]');
  assert.equal(root.querySelector('[data-id="unit-3"]'), null);
});

async function setup(t, { state = gameFixture(), overrides = {} } = {}) {
  const dom = new JSDOM('<main id="app"></main>', { url: 'http://localhost:5173' });
  const root = dom.window.document.querySelector('#app');
  const calls = [];
  const api = Object.fromEntries(['getGame', 'createDemoGame', 'createAiDemoGame', 'createLlmDemoGame', 'createOpenAiDemoGame', 'createConfiguredAiDemoGame', 'startGame', 'moveUnit', 'attackUnit', 'foundCity', 'setProduction', 'setResearch', 'endActivation'].map((name) => [name, async (...args) => {
    calls.push([name, ...args]);
    return overrides[name] ? overrides[name](...args) : structuredClone(state);
  }]));
  const view = mountGame(root, api);
  await view.ready;
  t.after(() => { view.destroy(); dom.window.close(); });
  const click = async (selector) => { assert.ok(root.querySelector(selector), selector); root.querySelector(selector).click(); await view.whenIdle(); };
  const change = async (selector, value) => {
    const control = root.querySelector(selector);
    control.value = value;
    control.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
    await view.whenIdle();
  };
  return { root, dom, view, calls, click, change };
}

test('public HUD and terrain render using all six local sprite mappings', async (t) => {
  const { root } = await setup(t);
  assert.match(root.querySelector('.hud').textContent, /Amber League/);
  assert.match(root.querySelector('.hud').textContent, /12 gold/);
  assert.equal(root.querySelectorAll('button.tile').length, 6);
  for (const sprite of Object.values(terrainSprites)) assert.ok(root.querySelector(`.tile.${sprite}`));
  assert.equal(new Set(Object.values(unitSprites)).size, 5);
  assert.notEqual(faction('A').className, faction('B').className);
  assert.equal(root.querySelectorAll('button button').length, 0);
});

test('no-game screen creates demo, then requires explicit start', async (t) => {
  const pregame = gameFixture();
  pregame.game = { turn: 0, activePlayerId: null, status: 'pre_game' };
  const { root, click, calls } = await setup(t, { overrides: {
    getGame: () => { throw new ApiError('no_game', 'Create a game', 404); },
    createDemoGame: () => pregame,
  } });
  assert.match(root.textContent, /New Demo Game/);
  await click('[data-action="demo"]');
  assert.ok(root.querySelector('[data-action="start"]'));
  assert.equal(root.querySelector('[data-action="end"]'), null);
  assert.equal(root.querySelector('#research'), null);
  await click('[data-action="unit"][data-id="unit-1"]');
  assert.equal(root.querySelector('#found-city-form'), null);
  await click('#tile-2-0');
  assert.equal(calls.filter(([name]) => name === 'moveUnit').length, 0);
  await click('[data-action="start"]');
  assert.ok(root.querySelector('[data-action="end"]'));
});

test('unit selection is visible and displays server movement allowance', async (t) => {
  const { root, click } = await setup(t);
  await click('[data-action="unit"][data-id="unit-1"]');
  assert.ok(root.querySelector('.selected-piece[data-id="unit-1"]'));
  assert.match(root.querySelector('[aria-label="Selected unit"]').textContent, /2 \/ 7/);
  assert.equal(root.querySelector('#tile-0-0').getAttribute('aria-pressed'), 'true');
  assert.ok(root.querySelector('#found-city-form'));
});

test('tile selection without an owned unit never sends movement', async (t) => {
  const { root, click, calls } = await setup(t);
  await click('#tile-2-0');
  assert.equal(root.querySelector('#tile-2-0').getAttribute('aria-pressed'), 'true');
  assert.deepEqual(calls, [['getGame']]);
  await click('[data-action="unit"][data-id="unit-3"]');
  await click('#tile-0-1');
  assert.deepEqual(calls, [['getGame']]);
});

test('selected own unit sends destination without frontend pathfinding', async (t) => {
  const { click, calls } = await setup(t);
  await click('[data-action="unit"][data-id="unit-2"]');
  // Even impassable water is submitted for authoritative backend validation.
  await click('#tile-2-1');
  assert.deepEqual(calls.at(-1), ['moveUnit', 'unit-2', 2, 1]);
  assert.equal(calls.filter(([name]) => name === 'getGame').length, 1);
});

test('enemy stack reveals all explicit targets and attacks only selected target', async (t) => {
  const { root, click, calls } = await setup(t);
  await click('[data-action="unit"][data-id="unit-2"]');
  await click('[data-action="unit"][data-id="unit-3"]');
  assert.equal(root.querySelectorAll('[data-action="attack"]').length, 2);
  assert.equal(calls.length, 1);
  await click('[data-action="attack"][data-id="unit-4"]');
  assert.deepEqual(calls.at(-1), ['attackUnit', 'unit-2', 'unit-4']);
});

test('enemy tile click presents attack chooser without sending a move', async (t) => {
  const { root, click, calls } = await setup(t);
  await click('[data-action="unit"][data-id="unit-2"]');
  await click('#tile-1-0');
  assert.equal(root.querySelectorAll('[data-action="attack"]').length, 2);
  assert.deepEqual(calls, [['getGame']]);
});

test('large friendly stacks remain individually selectable from tile details', async (t) => {
  const state = gameFixture();
  state.units.push({ ...state.units[1], id: 'unit-5', type: 'archer' });
  const { root, click } = await setup(t, { state });
  await click('.stack-count');
  assert.equal(root.querySelectorAll('.tile-details [data-action="unit"]').length, 3);
  await click('.tile-details [data-id="unit-5"]');
  assert.match(root.querySelector('[aria-label="Selected unit"]').textContent, /Archer/);
});

test('city selection exposes server costs and production set/clear commands', async (t) => {
  const { root, click, change, calls } = await setup(t);
  await click('[data-action="city"][data-id="city-1"]');
  assert.match(root.querySelector('[aria-label="Selected city"]').textContent, /New Hope/);
  assert.match(root.querySelector('#production').textContent, /53 production/);
  assert.equal(root.querySelector('#production option[value="archer"]'), null);
  await change('#production', 'scout');
  assert.deepEqual(calls.at(-1), ['setProduction', 'city-1', 'scout']);
  await change('#production', '');
  assert.deepEqual(calls.at(-1), ['setProduction', 'city-1', null]);
});

test('research uses API choices, costs, switching and clearing', async (t) => {
  const { root, change, calls } = await setup(t);
  assert.match(root.querySelector('#research').textContent, /37 science/);
  await change('#research', 'bronze_working');
  assert.deepEqual(calls.at(-1), ['setResearch', 'bronze_working']);
  await change('#research', '');
  assert.deepEqual(calls.at(-1), ['setResearch', null]);
});

test('enemy city inspection does not expose production controls', async (t) => {
  const state = gameFixture();
  state.cities[0].ownerId = 'B';
  const { root, click } = await setup(t, { state });
  await click('[data-action="city"]');
  assert.ok(root.querySelector('[aria-label="Selected city"]'));
  assert.equal(root.querySelector('#production'), null);
});

test('founding submits in-page city name and selects the returned city', async (t) => {
  const state = gameFixture();
  state.cities = [];
  const founded = gameFixture();
  founded.units = founded.units.filter((u) => u.id !== 'unit-1');
  founded.cities[0].name = 'Oak & Iron';
  const { root, click, dom, view, calls } = await setup(t, { state, overrides: { foundCity: () => founded } });
  await click('[data-action="unit"][data-id="unit-1"]');
  root.querySelector('#city-name').value = 'Oak & Iron';
  root.querySelector('#city-name').dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  root.querySelector('#found-city-form').dispatchEvent(new dom.window.Event('submit', { bubbles: true, cancelable: true }));
  await view.whenIdle();
  assert.deepEqual(calls.at(-1), ['foundCity', 'unit-1', 'Oak & Iron']);
  assert.match(root.querySelector('[aria-label="Selected city"]').textContent, /Oak & Iron/);
  assert.equal(root.querySelector('[data-action="unit"][data-id="unit-1"]'), null);
});

test('End Turn updates faction and clears stale selection', async (t) => {
  const next = gameFixture();
  next.game.activePlayerId = 'B';
  const { root, click, calls } = await setup(t, { overrides: { endActivation: () => next } });
  await click('[data-action="unit"][data-id="unit-2"]');
  await click('[data-action="end"]');
  assert.deepEqual(calls.at(-1), ['endActivation']);
  assert.match(root.querySelector('.hud').textContent, /Azure Union/);
  assert.equal(root.querySelector('[aria-label="Selected unit"]'), null);
  await click('[data-action="unit"][data-id="unit-3"]');
  await click('#tile-2-0');
  assert.deepEqual(calls.at(-1), ['moveUnit', 'unit-3', 2, 0]);
});

test('backend errors show unobtrusively and leave pieces unchanged', async (t) => {
  const { root, click } = await setup(t, { overrides: { moveUnit: () => { throw new ApiError('invalid_command', 'Not enough movement remaining.', 422); } } });
  await click('[data-action="unit"][data-id="unit-2"]');
  await click('#tile-2-1');
  assert.match(root.querySelector('[role="alert"]').textContent, /Not enough movement remaining/);
  assert.match(root.querySelector('[aria-label="Selected unit"]').textContent, /0, 0/);
  assert.equal(root.querySelector('[data-action="end"]').disabled, false);
});

test('pending commands disable controls and never optimistically move pieces or double submit', async (t) => {
  let resolve;
  const waiting = new Promise((done) => { resolve = done; });
  const { root, click, view, calls } = await setup(t, { overrides: { moveUnit: () => waiting } });
  await click('[data-action="unit"][data-id="unit-2"]');
  root.querySelector('#tile-2-0').click();
  assert.equal(root.querySelector('[data-action="end"]').disabled, true);
  assert.match(root.querySelector('[aria-label="Selected unit"]').textContent, /0, 0/);
  root.querySelector('#tile-2-0').click();
  assert.equal(calls.filter(([name]) => name === 'moveUnit').length, 1);
  resolve(gameFixture());
  await view.whenIdle();
  assert.equal(root.querySelector('[data-action="end"]').disabled, false);
});

test('city names render as text, including HTML-looking names', async (t) => {
  const state = gameFixture();
  state.cities[0].name = '<img src=x onerror="alert(1)">';
  const { root, click } = await setup(t, { state });
  await click('[data-action="city"]');
  assert.match(root.querySelector('[aria-label="Selected city"]').textContent, /<img src=x/);
  assert.equal(root.querySelector('img'), null);
});

test('reset returns pregame and clears selections; Escape clears local selection', async (t) => {
  const pregame = gameFixture();
  pregame.game = { turn: 0, activePlayerId: null, status: 'pre_game' };
  const { root, click, dom } = await setup(t, { overrides: { createDemoGame: () => pregame } });
  await click('[data-action="city"]');
  root.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  assert.equal(root.querySelector('[aria-label="Selected city"]'), null);
  await click('[data-action="unit"][data-id="unit-1"]');
  await click('[data-action="demo"]');
  assert.equal(root.querySelector('[aria-label="Selected unit"]'), null);
  assert.ok(root.querySelector('[data-action="start"]'));
});

test('all scenarios are available from the welcome screen and AI demo requires start', async (t) => {
  const pregame = gameFixture();
  pregame.players[1].controller = 'ai';
  pregame.game = { turn: 0, activePlayerId: null, status: 'pre_game' };
  const { root, click, calls } = await setup(t, { overrides: {
    getGame: () => { throw new ApiError('no_game', 'Create a game', 404); },
    createAiDemoGame: () => pregame,
  } });
  assert.match(root.querySelector('[data-action="demo"]').textContent, /Hot-seat/);
  assert.match(root.querySelector('[data-action="demo-ai"]').textContent, /Human vs Heuristic AI/);
  assert.match(root.querySelector('[data-action="demo-llm"]').textContent, /Human vs LLM/);
  await click('[data-action="demo-ai"]');
  assert.deepEqual(calls.at(-1), ['createAiDemoGame']);
  assert.match(root.querySelector('.edition').textContent, /Human vs Heuristic AI/);
  assert.ok(root.querySelector('[data-action="start"]'));
});

test('LLM demo uses explicit provider metadata and keeps AI loading until Python returns', async (t) => {
  const state = gameFixture();
  state.players[1].controller = 'ai';
  state.aiProviders = { B: 'ollama' };
  let resolve;
  const waiting = new Promise((done) => { resolve = done; });
  const { root, click, calls, view } = await setup(t, { state, overrides: {
    createLlmDemoGame: () => state, endActivation: () => waiting,
  } });
  await click('[data-action="demo-llm"]');
  assert.deepEqual(calls.at(-1), ['createLlmDemoGame']);
  assert.match(root.querySelector('.edition').textContent, /Human vs LLM/);
  root.querySelector('[data-action="end"]').click();
  assert.match(root.querySelector('[role="status"]').textContent, /AI turn\.\.\./);
  for (const control of root.querySelectorAll('button, input, select')) assert.equal(control.disabled, true);
  const returned = structuredClone(state);
  returned.game.turn += 1;
  returned.aiActivations = [{ requestedProvider: 'ollama', actualProvider: 'heuristic', fallbackUsed: true }];
  resolve(returned);
  await view.whenIdle();
  assert.equal(root.querySelector('[data-action="end"]').disabled, false);
  assert.match(root.querySelector('.edition').textContent, /Human vs LLM/);
  await click('[data-action="demo"]');
  assert.deepEqual(calls.at(-1), ['createDemoGame']);
});

test('configured AI uses its API route and displays the resolved provider after refresh', async (t) => {
  for (const provider of ['heuristic', 'ollama', 'openai']) {
    const state = gameFixture();
    state.players[1].controller = 'ai';
    state.aiProviders = { B: provider };
    state.game = { turn: 0, activePlayerId: null, status: 'pre_game' };
    let created = false;
    const { root, click, calls } = await setup(t, { state, overrides: {
      getGame: () => {
        if (!created) throw new ApiError('no_game', 'Create a game', 404);
        return state;
      },
      createConfiguredAiDemoGame: () => { created = true; return state; },
    } });
    assert.match(root.querySelector('[data-action="demo-configured"]').textContent, /Human vs Configured AI/);
    await click('[data-action="demo-configured"]');
    assert.deepEqual(calls.at(-1), ['createConfiguredAiDemoGame']);
    assert.ok(root.querySelector('[data-action="start"]'));
    const label = provider === 'openai' ? /Human vs OpenAI/ : provider === 'ollama' ? /Human vs LLM/ : /Human vs Heuristic AI/;
    assert.match(root.querySelector('.edition').textContent, label);
    await click('[data-action="refresh"]');
    assert.match(root.querySelector('.edition').textContent, label);
  }
});

test('unavailable configured AI shows the backend error and preserves the current game', async (t) => {
  const message = 'OpenAI requires OPENAI_API_KEY when selected.';
  for (const hasGame of [false, true]) {
    const { root, click } = await setup(t, { overrides: {
      getGame: () => {
        if (!hasGame) throw new ApiError('no_game', 'Create a game', 404);
        return gameFixture();
      },
      createConfiguredAiDemoGame: () => { throw new ApiError('provider_not_available', message, 503); },
    } });
    const before = root.querySelector('.hud')?.textContent;
    await click('[data-action="demo-configured"]');
    assert.equal(root.querySelector('[role="alert"]').textContent, message);
    assert.equal(root.querySelector('.hud')?.textContent, before);
    assert.equal(root.querySelector('[data-action="demo-ai"]').disabled, false);
    assert.equal(root.querySelector('[data-action="demo"]').disabled, false);
  }
});

test('AI turn loading disables every control, renders final human turn, and clears selection', async (t) => {
  const state = gameFixture();
  state.players[1].controller = 'ai';
  let resolve;
  const waiting = new Promise((done) => { resolve = done; });
  const { root, click, view, calls } = await setup(t, { state, overrides: { endActivation: () => waiting } });
  await click('[data-action="unit"][data-id="unit-2"]');
  root.querySelector('[data-action="end"]').click();
  assert.match(root.querySelector('[role="status"]').textContent, /AI turn\.\.\./);
  for (const control of root.querySelectorAll('button, input, select')) assert.equal(control.disabled, true);
  root.querySelector('[data-action="end"]').click();
  assert.equal(calls.filter(([name]) => name === 'endActivation').length, 1);
  const returned = structuredClone(state);
  returned.game.turn += 1;
  returned.units = returned.units.filter((u) => u.id !== 'unit-3');
  returned.players[0].gold = 37;
  resolve(returned);
  await view.whenIdle();
  assert.equal(root.querySelector('[data-action="end"]').disabled, false);
  assert.equal(root.querySelector('[aria-label="Selected unit"]'), null);
  assert.equal(root.querySelector('[data-action="unit"][data-id="unit-3"]'), null);
  assert.match(root.querySelector('.hud').textContent, /37 gold/);
  assert.match(root.querySelector('[role="status"]').textContent, /Your next activation is ready/);
  assert.equal(calls.filter(([name]) => name === 'getGame').length, 1);
});

test('AI request failure clears loading and allows refresh', async (t) => {
  const state = gameFixture();
  state.players[1].controller = 'ai';
  const { root, click } = await setup(t, { state, overrides: {
    endActivation: () => { throw new ApiError('server_error', 'Refresh to inspect state', 500); },
  } });
  await click('[data-action="end"]');
  assert.match(root.querySelector('[role="alert"]').textContent, /Refresh to inspect state/);
  assert.equal(root.querySelector('[data-action="refresh"]').disabled, false);
  assert.equal(root.querySelector('[data-action="end"]').disabled, false);
});

test('scenario reset from an existing match uses the selected scenario', async (t) => {
  const { click, calls } = await setup(t);
  await click('[data-action="demo-ai"]');
  assert.deepEqual(calls.at(-1), ['createAiDemoGame']);
  await click('[data-action="demo-configured"]');
  assert.deepEqual(calls.at(-1), ['createConfiguredAiDemoGame']);
  await click('[data-action="demo"]');
  assert.deepEqual(calls.at(-1), ['createDemoGame']);
});

test('terminal game cannot start or issue gameplay commands', async (t) => {
  const state = gameFixture();
  state.game = { turn: 10, activePlayerId: null, status: 'terminal', terminal: true,
    winnerPlayerId: 'A', victoryType: 'conquest' };
  const { root } = await setup(t, { state });
  assert.equal(root.querySelector('[data-action="start"]').disabled, true);
  assert.match(root.querySelector('[data-action="start"]').textContent, /Game ended/);
  assert.match(root.querySelector('.active-faction').textContent, /wins \u2014 Conquest/);
  assert.equal(root.querySelector('#research'), null);
});

test('AI active state exposes inspection but no manual research or unit orders', async (t) => {
  const state = gameFixture();
  state.players[0].controller = 'ai';
  const { root, click, calls } = await setup(t, { state });
  await click('[data-action="unit"][data-id="unit-1"]');
  assert.equal(root.querySelector('#found-city-form'), null);
  assert.equal(root.querySelector('#research'), null);
  await click('#tile-2-0');
  assert.deepEqual(calls, [['getGame']]);
});


test('explicit OpenAI demo and reset preserve the mode label and existing choices', async (t) => {
  const state = gameFixture();
  state.players[1].controller = 'ai';
  state.aiProviders = { B: 'openai' };
  state.game = { turn: 0, activePlayerId: null, status: 'pre_game' };
  const { root, click, calls } = await setup(t, { state, overrides: {
    getGame: () => { throw new ApiError('no_game', 'Create a game', 404); },
  } });
  await click('[data-action="demo-openai"]');
  assert.deepEqual(calls.at(-1), ['createOpenAiDemoGame']);
  assert.match(root.querySelector('.edition').textContent, /Human vs OpenAI/);
  assert.ok(root.querySelector('[data-action="start"]'));
  for (const mode of ['demo', 'demo-ai', 'demo-llm', 'demo-configured', 'demo-openai']) {
    assert.ok(root.querySelector(`[data-action="${mode}"]`));
  }
  await click('[data-action="demo-openai"]');
  assert.deepEqual(calls.at(-1), ['createOpenAiDemoGame']);
});

test('four civilizations have distinct stable identities and render C/D ownership and turns', async (t) => {
  assert.equal(new Set(['A', 'B', 'C', 'D'].map((id) => faction(id).className)).size, 4);
  const state = gameFixture();
  const template = state.players[0];
  state.players.push({ ...structuredClone(template), id: 'C' }, { ...structuredClone(template), id: 'D' });
  state.game.activePlayerId = 'D';
  state.units[0].ownerId = 'D';
  state.cities[0].ownerId = 'C';
  const { root } = await setup(t, { state });
  assert.match(root.textContent, /Violet Dominion/);
  assert.match(root.textContent, /Jade Assembly/);
  assert.ok(root.querySelector('.faction-c'));
  assert.ok(root.querySelector('.faction-d'));
});

test('four-player conquest displays either new faction as winner', async (t) => {
  for (const id of ['C', 'D']) {
    const state = gameFixture();
    state.game.status = 'terminal';
    state.game.terminal = true;
    state.game.winnerPlayerId = id;
    state.game.activePlayerId = null;
    const { root } = await setup(t, { state });
    assert.ok(root.textContent.includes(`${faction(id).name} wins`));
    assert.ok(root.querySelector('[data-action="start"]').disabled);
  }
});
