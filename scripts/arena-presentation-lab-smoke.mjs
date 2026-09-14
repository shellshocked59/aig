/** Temporal Chromium review of the real lab/engine. No network fixtures or inference. */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '../.local/arena-ui-tools/node_modules/playwright/index.mjs';
import fixtures from '../frontend/src/js/arena-lab-fixtures.json' with { type: 'json' };
const origin = process.argv[2] || 'http://127.0.0.1:5173';
if (!['localhost', '127.0.0.1'].includes(new URL(origin).hostname)) throw new Error('Local origin required');
const output = process.env.ARENA_EVIDENCE_DIR || '.local/arena-ui-phase3';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: process.env.ARENA_BROWSER || 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1080 } });
const errors = [], results = [];
page.on('pageerror', (error) => errors.push(error.message));
page.on('console', (message) => { if (message.type() === 'error' && message.text().includes('Arena presentation')) errors.push(message.text()); });
await page.route('**/*', (route) => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
async function effect(selector, text = '') { await page.waitForFunction(({selector,text}) => [...document.querySelectorAll(selector)].some(n => n.textContent.includes(text)), {selector,text}, {polling:'raf'}); }
async function settled() { await page.locator('[data-lab-game] [data-arena="end"]:enabled, [data-lab-game] .arena-winner').waitFor({ state: 'attached' }); }
async function inspect() {
  return page.evaluate(() => ({
    entities: [...document.querySelectorAll('.arena-board .arena-tile > .arena-entity')].map((e) => ({
      id: e.dataset.unitId || e.dataset.coreId, x: +e.parentElement.dataset.x, y: +e.parentElement.dataset.y,
      hp: +e.querySelector('meter').value, downed: !!e.querySelector('.arena-downed-badge') })).sort((a,b) => a.id.localeCompare(b.id)),
    log: document.querySelector('.arena-battle-log').textContent,
  }));
}
try {
  await page.goto(`${origin}/arena/presentation-lab`);
  await settled();
  for (const [name, f] of Object.entries(fixtures)) {
    console.log('Reviewing', name);
    await page.evaluate(() => {
      window.samples = []; window.sampling = true;
      const sample = () => {
        window.samples.push({ t: performance.now(), text: [...document.querySelectorAll('.arena-effect')].map((n) => n.textContent),
          ghost: !!document.querySelector('.arena-movement-ghost'),
          ghostPosition: document.querySelector('.arena-movement-ghost')?.getBoundingClientRect().toJSON(),
          sourceHidden: [...document.querySelectorAll('.arena-board .arena-tile > .arena-entity')].some(n => n.style.visibility === 'hidden'),
          sources: document.querySelectorAll('.arena-source').length, targets: document.querySelectorAll('.arena-target').length,
          area: document.querySelectorAll('.arena-area').length,
          areaWidth: document.querySelector('.arena-area')?.getBoundingClientRect().width,
          sourceWidth: document.querySelector('.arena-source')?.getBoundingClientRect().width,
          hp: Object.fromEntries([...document.querySelectorAll('.arena-board .arena-tile > .arena-entity')].map(n => [n.dataset.unitId || n.dataset.coreId, {value:n.querySelector('meter').value, width:n.querySelector('.arena-hp-fill')?.getBoundingClientRect().width}])),
          tracer: !!document.querySelector('.arena-tracer'),
          log: document.querySelector('.arena-battle-log')?.textContent,
          winner: !!document.querySelector('.arena-winner') });
        if (window.sampling) requestAnimationFrame(sample);
      }; requestAnimationFrame(sample);
    });
    await page.locator(`[data-effect="${name}"]`).click();
    if (name !== 'Turn') {
      const selector = name === 'Move' ? '.arena-movement-ghost' : '.arena-float';
      await effect(selector);
      if (name === 'Revive') await effect('.arena-float', 'REVIVE');
      if (name === 'Down') await effect('.arena-float', 'DOWNED');
      if (['Attack', 'Revive', 'Down', 'Fireball', 'Shield Bash', 'Move', 'Victory'].includes(name)) {
        await page.screenshot({ path: `${output}/lab-${name.toLowerCase().replaceAll(' ', '-')}-playing.png`, fullPage: true });
      }
    }
    await settled();
    const actual = await inspect();
    const expected = [...f.final.units, ...f.final.cores].map((e) => ({ id: e.id, x: e.x, y: e.y, hp: e.hp,
      downed: e.status === 'downed' })).sort((a,b) => a.id.localeCompare(b.id));
    assert.deepEqual(actual.entities, expected, name);
    for (const event of f.batch.events) assert.ok(actual.log.includes(event.log.text), name);
    const samples = await page.evaluate(() => { window.sampling = false; return window.samples; });
    if (name === 'Move') {
      const moving=samples.filter(s=>s.ghost);
      assert.ok(moving.every(s=>s.sourceHidden));
      assert.ok(new Set(moving.map(s=>Math.round(s.ghostPosition.x))).size>2,'ghost actually travels');
    }
    for(const e of f.batch.events.flatMap(e=>e.effects).filter(e=>e.hp_before!==undefined)) {
      const sign=e.type==='heal'?'+':'-';
      assert.ok(samples.some(s=>s.text.includes(`${sign}${e.amount}`)&&s.hp[e.entity_id]?.value===e.hp_after), `${name}: HP changes with amount`);
      assert.ok(samples.some(s=>s.hp[e.entity_id]?.value===e.hp_before), `${name}: before HP visible`);
    }
    if(name==='Attack'||name==='Snipe'||name==='Heal') assert.ok(samples.some(s=>s.text.length && s.sources && s.targets && s.sourceWidth>60), 'source and target remain visible at impact');
    if(name==='Fireball') assert.ok(samples.some(s=>s.area===9 && s.areaWidth>60 && s.text.filter(t=>/^-\d+$/.test(t)).length===3),'area and all victims together');
    if(name==='Attack') {
      const widths=samples.filter(s=>s.text.includes('-6')).map(s=>s.hp['red-knight'].width);
      assert.ok(new Set(widths.map(w=>Math.round(w))).size>2,'HP bar actually transitions');
    }
    if(name==='Victory') assert.ok(samples.some(s=>s.text.includes('CORE DESTROYED')&&!s.winner));
    assert.equal(await page.locator('.arena-effect, .arena-movement-ghost, .arena-turn-banner').count(),0);
    if (name === 'Attack' || name === 'Snipe') assert.ok(samples.some((s) => s.tracer));
    if (name === 'Revive') assert.ok(samples.some((s) => s.text.includes('REVIVE')));
    if (name === 'Down') assert.ok(samples.some((s) => s.text.includes('DOWNED')));
    if (name === 'Victory') assert.ok(samples.some((s) => s.text.length && !s.winner));
    results.push({ name, samples });
  }
  // Interrupt movement, travel, area and status ownership, then let all old clocks settle.
  for(const [name,selector] of [['Move','.arena-movement-ghost'],['Attack','.arena-tracer'],['Fireball','.arena-area'],['Revive','.arena-float']]) {
    await page.locator('[data-speed]').selectOption('0.5');
    await page.locator(`[data-effect="${name}"]`).click();await effect(selector);
    await page.locator('[data-lab-reset]').click();await settled();
    const reset=await inspect();await page.waitForTimeout(1000);
    assert.deepEqual(await inspect(),reset,`${name} reset resists stale completion`);
    assert.equal(await page.locator('.arena-effect, .arena-movement-ghost, .arena-turn-banner').count(),0);
    assert.equal(await page.evaluate(()=>document.getAnimations().length),0);
  }
  await page.locator('[data-speed]').selectOption('1');
  // Reset while an old queue owns an effect, then ensure no delayed mutation.
  await page.locator('[data-effect="Revive"]').click();
  await effect('.arena-float');
  await page.locator('[data-lab-reset]').click(); await settled();
  await page.waitForTimeout(1200);
  assert.equal((await inspect()).entities.find((e) => e.id === 'blue-mage').downed, true);
  assert.equal(await page.locator('.arena-effect, .arena-movement-ghost').count(), 0);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.locator('[data-effect="Revive"]').click();
  await effect('.arena-float'); await settled();
  assert.equal((await inspect()).entities.find((e) => e.id === 'blue-mage').hp, 5);
  await page.locator('[data-instant]').check();
  await page.locator('[data-effect="Fireball"]').click(); await settled();
  assert.match((await inspect()).log, /Blue Team Mage.*damage/);
  await page.screenshot({ path: `${output}/lab-overview.png`, fullPage: true });
  assert.deepEqual(errors, []);
  await writeFile(`${output}/presentation-temporal-review.json`, JSON.stringify({ result: 'passed', errors, results }, null, 2));
  console.log(JSON.stringify({ result: 'passed', effects: results.map((r) => r.name), errors, cancellation: true, reducedMotion: true, instant: true }, null, 2));
} finally { await browser.close(); }
