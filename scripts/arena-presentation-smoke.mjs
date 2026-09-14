/** Real Chromium + local HTTP; manual/heuristic only. Resets Arena on the supplied origin.
 * Setup: npm install --prefix .local/arena-ui-tools --no-save playwright
 * Run after npm run dev: node scripts/arena-ui-smoke.mjs
 */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '../.local/arena-ui-tools/node_modules/playwright/index.mjs';

const origin = process.argv[2] || 'http://127.0.0.1:5173';
if (!['localhost', '127.0.0.1'].includes(new URL(origin).hostname)) throw new Error('Local test origin required');
const output = process.env.ARENA_EVIDENCE_DIR || '.local/arena-ui-phase3';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: process.env.ARENA_BROWSER || 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1080 } });
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
page.on('console', (message) => { if (message.type() === 'error' && message.text().includes('Arena presentation')) errors.push(message.text()); });
await page.route('**/*', (route) => new URL(route.request().url()).origin === origin
  ? route.continue() : route.abort());
const tile = (x, y) => `[data-arena="tile"][data-x="${x}"][data-y="${y}"]`;
async function click(selector, request = false) {
  const response = request ? page.waitForResponse((r) => r.url().includes('/api/arena') && r.request().method() === 'POST') : null;
  await page.locator(selector).click();
  if (response) assert.equal((await response).status(), 200);
  await page.locator('[data-arena="demo"]:enabled').waitFor();
  assert.equal(await page.locator('[data-view="arena"] [role="alert"]').count(), 0);
}
async function act(kind, x, y) {
  await click(`[data-mode="${kind}"]`);
  assert.ok(await page.locator(`${tile(x, y)}.arena-legal`).count());
  await click(tile(x, y), true);
}
const end = () => click('[data-arena="end"]', true);
try {
  await page.goto(`${origin}/arena`);
  await click('[data-arena="demo"]', true);
  assert.equal(await page.locator('.arena-tile').count(), 45);
  await click(tile(1, 0));
  await click('[data-mode="move"]');
  await page.screenshot({ path: `${output}/arena-desktop.png`, fullPage: true });
  await click('[data-arena="cancel"]');
  // Real initial scenario: injure a Cleric, heal, then destroy the enemy Core.
  await end();
  await click(tile(7, 0));
  await act('move', 6, 3);
  await act('move', 4, 4);
  await act('attack', 1, 4);
  await end();
  await click(tile(1, 4));
  await act('heal', 1, 4);
  assert.match(await page.locator(tile(1, 4)).innerText(), /9\/11 HP/);
  await click(tile(1, 0));
  await act('move', 4, 0);
  await act('move', 5, 2);
  await act('attack', 8, 2);
  await act('attack', 8, 2);
  await end(); await end();
  await click(tile(5, 2));
  await act('attack', 8, 2);
  await act('attack', 8, 2);
  assert.match(await page.locator('.arena-status').innerText(), /Blue Team wins!/i);
  assert.match(await page.locator('.arena-winner').innerText(), /Core destroyed/);
  await page.screenshot({ path: `${output}/arena-winner.png`, fullPage: true });
  await click('[data-arena="reset"]', true);
  await click('[data-arena="demo-ai"]', true);
  await click(tile(1, 0));
  await act('move', 4, 0);
  await act('snipe', 7, 0);
  assert.match(await page.locator(tile(7, 0)).innerText(), /DOWNED/);
  await page.screenshot({ path: `${output}/arena-downed.png`, fullPage: true });
  // Delay delivery of the real response briefly so the transient state is observable.
  await page.route('**/api/arena/commands', async (route) => {
    const response = await route.fetch();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await route.fulfill({ response });
  });
  await page.evaluate(() => {
    window.turnSamples=[];window.recordTurn=true;
    const sample=()=>{
      window.turnSamples.push({t:performance.now(),status:document.querySelector('.arena-playback-status')?.textContent,
        latest:document.querySelector('.arena-battle-log li')?.textContent,
        source:document.querySelector('.arena-source')?.textContent,
        sourcePosition:document.querySelector('.arena-source')?.getBoundingClientRect().toJSON(),
        targetPosition:document.querySelector('.arena-target')?.getBoundingClientRect().toJSON(),
        ghost:document.querySelector('.arena-movement-ghost')?.getBoundingClientRect().toJSON(),
        float:[...document.querySelectorAll('.arena-float')].map(n=>n.textContent),
        hp:[...document.querySelectorAll('.arena-tile > .arena-entity')].map(n=>({id:n.dataset.unitId||n.dataset.coreId,hp:n.querySelector('meter').value})),
        locked:document.querySelector('[data-arena="end"]')?.disabled});
      if(window.recordTurn)requestAnimationFrame(sample);
    };requestAnimationFrame(sample);
  });
  const response = page.waitForResponse((r) => r.url().endsWith('/commands'));
  await page.locator('[data-arena="end"]').click();
  assert.match(await page.locator('.arena-view').innerText(), /AI thinking/);
  assert.ok(await page.locator('[data-arena="end"]').isDisabled());
  const finalResponse = await (await response).json();
  await page.getByText('AI acting', { exact: false }).first().waitFor();
  const currentLines = await page.locator('.arena-battle-log li').allTextContents();
  assert.ok(currentLines.length < finalResponse.battle_log.length, 'AI log streams instead of dumping final batch');
  await page.screenshot({ path: `${output}/arena-ai-acting.png`, fullPage: true });
  for(const kind of ['REVIVE','HEAL','ATTACK']) {
    await page.waitForFunction(kind=>document.querySelector('.arena-source')?.textContent===kind &&
      !!document.querySelector('.arena-float'),kind,{polling:'raf'});
    if (kind === 'ATTACK') assert.equal(await page.locator('[data-selected-hp]').innerText(), '5/10 HP');
    await page.screenshot({path:`${output}/arena-ai-${kind.toLowerCase()}.png`,fullPage:true});
  }
  await page.locator('[data-arena="end"]:enabled').waitFor();
  const turnSamples=await page.evaluate(()=>{window.recordTurn=false;return window.turnSamples;});
  await writeFile(`${output}/heuristic-turn-frames.json`,JSON.stringify({events:finalResponse.presentation.events,samples:turnSamples},null,2));
  const acting=turnSamples.filter(s=>s.status?.includes('AI acting'));
  assert.ok(acting.every(s=>s.locked));
  const actionStarts=[];
  for(const s of acting)if(s.latest!==actionStarts.at(-1)?.text)actionStarts.push({text:s.latest,t:s.t});
  console.log('Heuristic playback',JSON.stringify({durationMs:acting.at(-1).t-acting[0].t,actions:actionStarts}));
  assert.deepEqual((await page.locator('.arena-battle-log li').allTextContents()).reverse(), finalResponse.battle_log.map((e) => e.text));
  assert.match(await page.locator('.arena-status').innerText(), /Blue Team/);
  assert.match(await page.locator('.arena-battle-log').innerText(), /Red Team/);
  await page.screenshot({ path: `${output}/arena-heuristic.png`, fullPage: true });
  await click('[data-arena="reset"]', true);
  assert.match(await page.locator('.arena-mode').innerText(), /Human vs Heuristic/);
  const board = await page.locator('.arena-board').boundingBox();
  assert.ok(board.x >= 0 && board.x + board.width <= 1440);
  await page.setViewportSize({ width: 900, height: 900 });
  await page.screenshot({ path: `${output}/arena-narrow.png`, fullPage: true });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.setViewportSize({ width: 1440, height: 1080 });
  assert.deepEqual(errors, []);
  const report = { result: 'passed', browser: 'Chromium', boardCells: 45,
    checks: ['direct Arena route', 'manual match', 'selection', 'legal targets', 'move', 'attack', 'heal',
      'snipe', 'Core victory', 'winner reason', 'reset preserves mode', 'heuristic turn',
      'AI loading disables controls', 'battle log', '900px no document overflow'], errors };
  await writeFile(`${output}/browser-smoke.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
} finally { await browser.close(); }

