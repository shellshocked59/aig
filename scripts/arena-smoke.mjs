/** Real local HTTP + browser DOM smoke. Requires an isolated running API.
 * Usage: node scripts/arena-smoke.mjs http://127.0.0.1:8011
 * Resets only the Arena demo on that API. No AI/provider calls.
 */
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { mountEnvironments } from '../frontend/src/js/environments.js';
import { createGameApi } from '../frontend/src/js/api/game.js';
import { createArenaApi } from '../frontend/src/js/api/arena.js';

const origin = process.argv[2] || 'http://127.0.0.1:8011';
const dom = new JSDOM('<main id="app"></main>');
const root = dom.window.document.querySelector('#app');
const app = mountEnvironments(root, createGameApi(undefined, origin), createArenaApi(undefined, origin));
const tile = (x, y) => `[data-arena="tile"][data-x="${x}"][data-y="${y}"]`;
async function click(selector) {
  const button = root.querySelector(selector);
  assert.ok(button, `Missing ${selector}`);
  assert.equal(button.disabled, false, `Disabled ${selector}`);
  button.click();
  await app.arena.whenIdle();
  assert.equal(root.querySelector('[data-view="arena"] [role="alert"]'), null, root.textContent);
}
async function act(kind, x, y) {
  await click(`[data-mode="${kind}"]`);
  await click(tile(x, y));
}
const end = () => click('[data-arena="end"]');
try {
  await app.empire.whenIdle();
  root.querySelector('[data-environment="arena"]').click();
  await app.arena.whenIdle();
  await click('[data-arena="demo"]');
  assert.equal(root.querySelectorAll('.arena-tile').length, 45);
  // Red advances a Ranger and injures Blue's Cleric; Blue heals itself.
  await end();
  await click(tile(7, 0));
  await act('move', 6, 3);
  await act('move', 4, 4);
  await act('attack', 1, 4);
  assert.match(root.querySelector(tile(1, 4)).textContent, /4\/11 HP/);
  await end();
  await click(tile(1, 4));
  await act('heal', 1, 4);
  assert.match(root.querySelector(tile(1, 4)).textContent, /9\/11 HP/);
  // Blue's Ranger then wins by attacking from SIEGE across two turns.
  await click(tile(1, 0));
  await act('move', 4, 0);
  await act('move', 5, 2);
  await act('attack', 8, 2);
  await act('attack', 8, 2);
  assert.match(root.querySelector('.arena-status').textContent, /0 \/ 5 AP/);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
  await end();
  await end();
  await click(tile(5, 2));
  await act('attack', 8, 2);
  await act('attack', 8, 2);
  assert.match(root.querySelector('.arena-status').textContent, /Blue Team wins!/);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
  const trace = await (await fetch(`${origin}/api/arena/trace`)).json();
  console.log(JSON.stringify({ result: 'passed', commands: trace.entries.length,
    finalHash: trace.entries.at(-1).after_hash,
    checks: ['environment selection', '45 tiles', 'move', 'unit attack', 'self-heal', 'Core attack', '0 AP inspection', 'End Turn', 'victory'] }, null, 2));
} finally {
  app.destroy();
  dom.window.close();
}
