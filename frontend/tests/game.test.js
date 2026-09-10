import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import { mountGame } from '../src/js/game.js';
import { terrainSprites, unitSprites, faction } from '../src/js/presentation.js';
import { ApiError } from '../src/js/api/game.js';
import { gameFixture } from './fixtures.js';

async function setup(t, { state = gameFixture(), overrides = {} } = {}) {
  const dom = new JSDOM('<main id="app"></main>', { url: 'http://localhost:5173' });
  const root = dom.window.document.querySelector('#app');
  const calls = [];
  const api = Object.fromEntries(['getGame', 'createDemoGame', 'createAiDemoGame', 'startGame', 'moveUnit', 'attackUnit', 'foundCity', 'setProduction', 'setResearch', 'endActivation'].map((name) => [name, async (...args) => {
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

test('both scenarios are available from the welcome screen and AI demo requires start', async (t) => {
  const pregame = gameFixture();
  pregame.players[1].controller = 'ai';
  pregame.game = { turn: 0, activePlayerId: null, status: 'pre_game' };
  const { root, click, calls } = await setup(t, { overrides: {
    getGame: () => { throw new ApiError('no_game', 'Create a game', 404); },
    createAiDemoGame: () => pregame,
  } });
  assert.match(root.querySelector('[data-action="demo"]').textContent, /Hot-seat/);
  assert.match(root.querySelector('[data-action="demo-ai"]').textContent, /Human vs AI/);
  await click('[data-action="demo-ai"]');
  assert.deepEqual(calls.at(-1), ['createAiDemoGame']);
  assert.match(root.querySelector('.edition').textContent, /Human vs AI/);
  assert.ok(root.querySelector('[data-action="start"]'));
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
  await click('[data-action="demo"]');
  assert.deepEqual(calls.at(-1), ['createDemoGame']);
});

test('terminal game cannot start or issue gameplay commands', async (t) => {
  const state = gameFixture();
  state.game = { turn: 10, activePlayerId: null, status: 'terminal' };
  const { root } = await setup(t, { state });
  assert.equal(root.querySelector('[data-action="start"]').disabled, true);
  assert.match(root.querySelector('[data-action="start"]').textContent, /Game ended/);
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
