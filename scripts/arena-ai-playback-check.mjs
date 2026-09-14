/** Live local HTTP + real frontend/clock, without a browser animation implementation.
 * Resets only Arena; uses offline V1 and V2. This is not a visual browser review.
 */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { JSDOM } from 'jsdom';
import { createArenaApi } from '../frontend/src/js/api/arena.js';
import { mountArena } from '../frontend/src/js/arena.js';

const origin = process.argv[2] || 'http://127.0.0.1:5173';
if (!['127.0.0.1', 'localhost'].includes(new URL(origin).hostname)) throw new Error('Local origin required');
const output = 'artifacts/arena-phase5';
await mkdir(output, { recursive: true });
const reports = [];
for (const provider of ['heuristic', 'heuristic-v2']) {
  const dom = new JSDOM('<main></main>'), root = dom.window.document.querySelector('main');
  const api = createArenaApi(fetch, origin), errors = [], frames = [];
  const start = await api.createAiDemo(provider);
  let response, responseAt, last = '';
  const game = mountArena(root, { ...api, command: async (...args) => {
    response = await api.command(...args); responseAt = performance.now(); return response;
  } }, { report: (...args) => errors.push(args.map(String)) });
  const observer = new dom.window.MutationObserver(() => {
    const status = root.querySelector('.arena-playback-status')?.textContent || '';
    const turn = root.querySelector('.arena-status')?.textContent || '';
    const key = status + turn;
    if (key === last || !responseAt) return;
    last = key;
    frames.push({ ms: Math.round(performance.now() - responseAt), status, turn,
      locked: root.querySelector('[data-arena="end"]')?.disabled,
      actor: root.querySelector('.arena-acting [data-unit-id]')?.dataset.unitId,
      logCount: root.querySelectorAll('.arena-battle-log li').length });
  });
  try {
    await game.whenIdle(); observer.observe(root, { childList: true, subtree: true });
    root.querySelector('[data-arena="end"]').click(); await game.whenIdle();
    const elapsed = Math.round(performance.now() - responseAt);
    const actions = response.presentation.events.filter(e => e.actor_id);
    const seen = new Set(frames.map(f => f.status.match(/Action (\d+) \/ (\d+)/)?.[1]).filter(Boolean));
    assert.equal(seen.size, actions.length);
    assert.deepEqual(errors, []);
    assert.equal(game.state.state_hash, response.state_hash);
    for (const frame of frames.filter(f => /Action \d/.test(f.status))) {
      assert.match(frame.turn, /Red Team/); assert.equal(frame.locked, true); assert.ok(frame.actor);
    }
    assert.equal(root.querySelector('[data-arena="end"]').disabled, false);
    reports.push({ provider, elapsedMs: elapsed, actionCount: actions.length,
      actions: actions.map(e => ({ type: e.type, actor: e.actor_id, apAfter: e.ap_after })), frames, errors });
    await writeFile(`${output}/${provider}-live.json`, JSON.stringify({ start, response }, null, 2));
    console.log(`${provider}: ${actions.length} actions, ${elapsed} ms, ordered and locked, no playback warnings`);
  } finally { observer.disconnect(); game.destroy(); dom.window.close(); }
}
await writeFile(`${output}/timing-review.json`, JSON.stringify(reports, null, 2));
