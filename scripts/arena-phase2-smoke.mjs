/** Run after: python scripts/arena-phase2-smoke.py --serve 8012
 * Executes the supplied fixture through real DOM controls and HTTP, no AI.
 */
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { JSDOM } from 'jsdom';
import { mountArena } from '../frontend/src/js/arena.js';
import { createArenaApi } from '../frontend/src/js/api/arena.js';

const origin = process.argv[2] || 'http://127.0.0.1:8012';
const directory = process.argv[3] || '.local/arena-phase2-verification';
const commands = JSON.parse(await readFile(`${directory}/commands.json`, 'utf8'));
const expected = JSON.parse(await readFile(`${directory}/trace.json`, 'utf8'));
const dom = new JSDOM('<main></main>');
const root = dom.window.document.querySelector('main');
const api = createArenaApi(undefined, origin);
const game = mountArena(root, api);
const tile = (p) => `[data-arena="tile"][data-x="${p.x}"][data-y="${p.y}"]`;
async function click(selector) {
  const button = root.querySelector(selector);
  assert.ok(button, `Missing ${selector}`);
  assert.equal(button.disabled, false, `Disabled ${selector}`);
  button.click();
  await game.whenIdle();
  assert.equal(root.querySelector('[role="alert"]'), null, root.textContent);
}
let downedSeen = false;
try {
  await game.whenIdle();
  for (const command of commands) {
    const state = await api.getGame();
    assert.equal(state.active_player_id, command.actor_id);
    if (command.type === 'arena_end_turn') {
      await click('[data-arena="end"]');
    } else {
      const unit = state.units.find((u) => u.id === command.unit_id);
      await click(tile(unit));
      const mode = command.type.slice('arena_'.length);
      const button = root.querySelector(`[data-mode="${mode}"]`);
      assert.match(button.textContent, new RegExp(`${unit.abilities[mode].ap_cost} AP`));
      await click(`[data-mode="${mode}"]`);
      const target = command.destination || command.target_position
        || [...state.units, ...state.cores].find((p) => p.id === command.target_id);
      assert.ok(root.querySelector(`${tile(target)}.arena-legal`));
      await click(tile(target));
    }
    downedSeen ||= root.querySelector('.arena-downed-badge') !== null;
  }
  assert.ok(downedSeen);
  assert.match(root.querySelector('.arena-status').textContent, /Blue Team wins!/);
  assert.equal(root.querySelector('[data-arena="end"]').disabled, true);
  const trace = await (await fetch(`${origin}/api/arena/trace`)).json();
  assert.deepEqual(trace, expected);
  await writeFile(`${directory}/http-trace.json`, `${JSON.stringify(trace, null, 2)}\n`);
  console.log(JSON.stringify({ result: 'passed', commands: trace.entries.length,
    finalHash: trace.entries.at(-1).after_hash, exactHeadlessTrace: true,
    checks: ['all nine command types', '2 AP labels', 'legal targets', 'downed badge', 'friendly fire',
      'revive then act', 'Finish removal', 'Core victory', 'exact headless trace'] }, null, 2));
} finally {
  game.destroy();
  dom.window.close();
}
