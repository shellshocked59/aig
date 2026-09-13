/** Real loopback HTTP and DOM integration. Resets only Arena on an isolated API.
 * node scripts/arena-ai-smoke.mjs http://127.0.0.1:8013
 */
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { JSDOM } from 'jsdom';
import { mountArena } from '../frontend/src/js/arena.js';
import { createArenaApi } from '../frontend/src/js/api/arena.js';

const origin = process.argv[2] || 'http://127.0.0.1:8013';
const dom = new JSDOM('<main></main>');
const root = dom.window.document.querySelector('main');
const api = createArenaApi(undefined, origin);
const app = mountArena(root, api);
async function click(selector, ai = false) {
  const button = root.querySelector(selector);
  assert.ok(button);
  assert.equal(button.disabled, false);
  button.click();
  if (ai) {
    assert.match(root.textContent, /AI turn\.\.\./);
    assert.ok([...root.querySelectorAll('button')].every((b) => b.disabled));
  }
  await app.whenIdle();
  assert.equal(root.querySelector('[role="alert"]'), null, root.textContent);
}
try {
  await app.whenIdle();
  await click('[data-arena="demo-ai"]');
  let state = await api.getGame();
  assert.equal(state.controllers.red, 'heuristic_ai');
  // A human who passes eventually loses; every actual AI turn runs server-side.
  for (let turn = 0; turn < 20 && !state.winner_player_id; turn++) {
    await click('[data-arena="end"]', true);
    state = await api.getGame();
    assert.equal(state.ai_turns.length, 1);
    assert.equal(state.ai_turns[0].invalid_action, null);
    if (!state.winner_player_id) assert.equal(state.active_player_id, 'blue');
  }
  assert.equal(state.winner_player_id, 'red');
  assert.match(root.querySelector('.arena-status').textContent, /Red Team wins!/);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
  const trace = await (await fetch(`${origin}/api/arena/trace`)).json();
  mkdirSync('.local/arena-phase3-verification', { recursive: true });
  writeFileSync('.local/arena-phase3-verification/http-trace.json', JSON.stringify(trace, null, 2) + '\n');
  console.log(JSON.stringify({ result: 'passed', winner: state.winner_player_id, turn: state.turn,
    commands: trace.entries.length, finalHash: trace.entries.at(-1).after_hash }, null, 2));
  await click('[data-arena="demo"]');
  await click('[data-arena="end"]');
  assert.equal((await api.getGame()).active_player_id, 'red');
} finally {
  app.destroy();
  dom.window.close();
}
