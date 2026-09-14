/** Phase 4 visual workbench and scale review; local Chromium, no providers. */
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '../.local/arena-ui-tools/node_modules/playwright/index.mjs';
const origin=process.argv[2] || 'http://127.0.0.1:5173';
if(!['localhost','127.0.0.1'].includes(new URL(origin).hostname))throw new Error('Local origin required');
const output='.local/arena-ui-phase4';await mkdir(output,{recursive:true});
const browser=await chromium.launch({channel:process.env.ARENA_BROWSER || 'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080}}),errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error' && m.text().includes('Arena presentation'))errors.push(m.text());});
await page.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
const idle=()=>page.locator('[data-lab-game] [data-arena="end"]:enabled').waitFor({state:'attached'});
try {
  await page.goto(`${origin}/arena/presentation-lab`);await idle();
  await page.getByText('Class gallery / Blue / Red / Active / Downed',{exact:true}).click();
  await page.locator('.arena-gallery').screenshot({path:`${output}/class-design-sheet.png`});
  assert.equal(await page.locator('.arena-gallery .arena-unit-art').count(),16);
  await page.getByText('Class gallery / Blue / Red / Active / Downed',{exact:true}).click();
  for(const width of [1280,1440,1920,900]) {
    await page.setViewportSize({width,height:1080});
    const geometry=await page.locator('.arena-board .arena-entity').evaluateAll(nodes=>nodes.map(n=>{
      const tile=n.parentElement.getBoundingClientRect(),art=n.querySelector('svg').getBoundingClientRect(),hp=n.querySelector('[data-hp-label]').getBoundingClientRect();
      return {id:n.dataset.unitId || n.dataset.coreId,tile:tile.toJSON(),art:art.toJSON(),fits:art.left>=tile.left && art.right<=tile.right && art.top>=tile.top && hp.bottom<=tile.bottom};
    }));
    assert.ok(geometry.every(g=>g.fits),`tile fit at ${width}`);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:`${output}/lab-${width}.png`,fullPage:true});
    checks.push({width,geometry});
  }
  await page.setViewportSize({width:1440,height:1080});
  for(const kind of ['knight','ranger','mage','cleric']) {
    await page.locator(`.arena-board [data-unit-id="blue-${kind}"]`).click();
    await page.screenshot({path:`${output}/selected-${kind}.png`,fullPage:true});
    assert.equal(await page.locator(`.arena-selected-art [data-class-art="${kind}"]`).count(),1);
  }
  await page.locator('[data-speed]').selectOption('0.5');
  for(const [name,selector] of [
    ['Knight Attack','.arena-impact.arena-physical'],['Shield Bash','.arena-impact.arena-bash'],
    ['Ranger Attack','.arena-tracer.arena-precision'],['Snipe','.arena-tracer.arena-snipe'],
    ['Mage Attack','.arena-tracer.arena-arcane'],['Fireball','.arena-area'],
    ['Cleric Attack','.arena-tracer.arena-radiant'],['Heal','.arena-impact.arena-restorative'],['Revive','.arena-status-float']]) {
    await page.locator(`[data-effect="${name}"]`).click();
    await page.waitForFunction(s=>!!document.querySelector(s),selector,{polling:'raf'});
    if(selector.includes('arena-tracer')) await page.waitForFunction(s=>{
      const tracer=document.querySelector(s),source=document.querySelector('.arena-source')?.getBoundingClientRect(),target=document.querySelector('.arena-target')?.getBoundingClientRect();
      return tracer && source && target && parseFloat(getComputedStyle(tracer).width)>=Math.hypot(target.x-source.x,target.y-source.y)*.45;
    },selector,{polling:'raf'});
    await page.screenshot({path:`${output}/effect-${name.toLowerCase().replaceAll(' ','-')}.png`,fullPage:true});
    await idle();assert.equal(await page.locator('.arena-effect').count(),0);
    assert.equal(await page.evaluate(()=>document.getAnimations().length),0);
  }
  await page.locator('[data-lab-reset]').click();await idle();
  await page.locator('.arena-board').screenshot({path:`${output}/downed-mage.png`});
  assert.equal(await page.locator('.arena-board .arena-downed [data-class-art="mage"]').count(),1);
  await page.emulateMedia({reducedMotion:'reduce'});
  for(const name of ['Knight Attack','Ranger Attack','Mage Attack','Cleric Attack','Snipe','Shield Bash','Fireball','Heal','Revive']) {
    await page.locator(`[data-effect="${name}"]`).click();
    await page.waitForFunction(()=>!!document.querySelector('.arena-float'),null,{polling:'raf'});
    assert.equal(await page.locator('.arena-tracer,.arena-movement-ghost').count(),0);
    await idle();
  }
  assert.deepEqual(errors,[]);
  await writeFile(`${output}/visual-identity-review.json`,JSON.stringify({result:'passed',errors,checks,reducedMotion:true},null,2));
  console.log('Phase 4 class gallery, four viewport sizes, selected art, nine effects and reduced motion passed.');
} finally {await browser.close();}
