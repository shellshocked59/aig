/** Measured overlay and accessibility review for the shared Phase 6 board. */
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {chromium} from '../.local/arena-ui-tools/node_modules/playwright/index.mjs';
import fixtures from '../frontend/src/js/arena-lab-fixtures.json' with {type:'json'};
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage(), checks=[];
const output='artifacts/arena-ui-phase6';
const idle=()=>page.locator('[data-lab-game] [data-arena="end"]:enabled').waitFor({state:'attached'});
try {
 await page.goto('http://127.0.0.1:5173/arena/presentation-lab');await idle();
 await page.locator('[data-speed]').selectOption('0.5');
 for(const width of [1920,1440,1080,900]) {
  await page.setViewportSize({width,height:1080});
  for(const name of ['Ranger Attack','Fireball','Heal']) {
   await page.locator(`[data-effect="${name}"]`).click();
   const effect=name==='Fireball'?'.arena-area':'.arena-target';
   await page.waitForFunction(s=>!!document.querySelector(s),effect,{polling:'raf'});
   const event=fixtures[name].batch.events.find(e=>e.origin && e.target);
   const geometry=await page.evaluate(({origin,target,effect})=>{
    const center=n=>{const r=n.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2,width:r.width,height:r.height};};
    const cell=p=>center(document.querySelector(`[data-arena="tile"][data-x="${p.x}"][data-y="${p.y}"]`));
    const source=center(document.querySelector('.arena-source'));
    const targetMark=center(document.querySelector('.arena-target'));
    const areas=[...document.querySelectorAll('.arena-area')].map(n=>({actual:center(n),closest:Math.min(...[...document.querySelectorAll('.arena-board .arena-tile')].map(t=>{const c=center(t),a=center(n);return Math.hypot(c.x-a.x,c.y-a.y);})),cellWidth:cell(target).width,cellHeight:cell(target).height}));
    return {source,targetMark,origin:cell(origin),target:cell(target),areas};
   },{origin:event.origin,target:event.target,effect});
   assert.ok(Math.hypot(geometry.source.x-geometry.origin.x,geometry.source.y-geometry.origin.y)<1);
   assert.ok(Math.hypot(geometry.targetMark.x-geometry.target.x,geometry.targetMark.y-geometry.target.y)<1);
   for(const a of geometry.areas){assert.ok(a.closest<1);assert.ok(Math.abs(a.actual.width-a.cellWidth)<1);assert.ok(Math.abs(a.actual.height-a.cellHeight)<1);}
   checks.push({width,name,geometry});await idle();
  }
 }
 await page.locator('[data-effect="Move"]').click();await page.waitForFunction(()=>!!document.querySelector('.arena-movement-ghost'));
 await page.setViewportSize({width:1280,height:900});await idle();
 assert.equal(await page.locator('.arena-effect,.arena-movement-ghost').count(),0);
 const move=fixtures.Move.batch.events[0];
 assert.equal(await page.locator(`[data-x="${move.destination?.x ?? move.target.x}"][data-y="${move.destination?.y ?? move.target.y}"] [data-unit-id="${move.actor_id}"]`).count(),1);
 await page.goto('http://127.0.0.1:5173/arena');await page.locator('[data-arena="end"]:enabled').waitFor();
 await page.locator('[data-unit-id="blue-mage"]').click();
 const contrast=await page.locator('.arena-view').evaluate(n=>{
  const s=getComputedStyle(n),pairs=[['--arena-fg','--arena-panel'],['--arena-muted','--arena-panel'],['--arena-disabled','--arena-panel-raised'],['--arena-tile-power','--arena-bg'],['--arena-tile-ward','--arena-bg'],['--arena-tile-siege','--arena-bg']];
  const lum=hex=>{const c=hex.trim().match(/[a-f0-9]{2}/gi).map(h=>parseInt(h,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722;};
  return pairs.map(([fg,bg])=>{const a=lum(s.getPropertyValue(fg)),b=lum(s.getPropertyValue(bg));return{fg,bg,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};});
 });
 assert.ok(contrast.every(p=>p.ratio>=4.5));
 await page.keyboard.press('Tab');
 await page.locator('[data-mode="move"]').focus();
 assert.equal(await page.locator('[data-mode="move"]').evaluate(n=>getComputedStyle(n).outlineStyle),'solid');
 await page.keyboard.press('Enter');assert.ok(await page.locator('.arena-legal').count());
 await page.locator('[data-arena="cancel"]').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('.arena-legal').count(),0);
 await writeFile(`${output}/geometry-accessibility.json`,JSON.stringify({result:'passed',checks,resizeReconciled:true,contrast,keyboard:true},null,2));
 console.log('Overlay source/target centers and Fireball cells align at four widths; resize reconciles; text contrast and keyboard controls pass.');
} finally {await browser.close();}
