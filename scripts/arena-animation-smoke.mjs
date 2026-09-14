/** Phase 3 interruption/resize acceptance against the real offline game. */
import assert from 'node:assert/strict';
import {writeFile,mkdir} from 'node:fs/promises';
import {chromium} from '../.local/arena-ui-tools/node_modules/playwright/index.mjs';
const origin=process.argv[2]||'http://127.0.0.1:5173';
if(!['localhost','127.0.0.1'].includes(new URL(origin).hostname))throw new Error('Local origin required');
const output='.local/arena-ui-phase3';await mkdir(output,{recursive:true});
const browser=await chromium.launch({channel:process.env.ARENA_BROWSER||'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080}}),errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error'&&m.text().includes('Arena presentation'))errors.push(m.text());});
await page.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
const tile=(x,y)=>`[data-arena="tile"][data-x="${x}"][data-y="${y}"]`;
const idle=()=>page.locator('[data-arena="end"]:enabled').waitFor();
const effect=selector=>page.waitForFunction(s=>!!document.querySelector(s),selector,{polling:'raf'});
async function act(kind,x,y,wait=true){await page.locator(`[data-mode="${kind}"]`).click();await page.locator(tile(x,y)).click();if(wait)await idle();}
async function snapshot(){return page.locator('.arena-board').evaluate(n=>n.innerHTML);}
async function resetDuring(selector,label){
 await effect(selector);
 // Same delegated UI click, performed immediately while the effect is present.
 await page.locator('[data-arena="reset"]').evaluate(n=>n.click());await idle();
 const fresh=await snapshot();await page.waitForTimeout(1000);assert.equal(await snapshot(),fresh);
 assert.equal(await page.locator('.arena-effect,.arena-movement-ghost,.arena-turn-banner').count(),0);
 assert.equal(await page.evaluate(()=>document.getAnimations().length),0);checks.push(label);
}
try{
 await page.goto(`${origin}/arena`);await page.locator('[data-arena="demo"]').click();await idle();
 await page.locator(tile(1,0)).click();await act('move',4,0,false);await resetDuring('.arena-movement-ghost','New Match during Move');
 await page.locator(tile(1,0)).click();await act('move',4,0);await act('attack',7,0,false);await resetDuring('.arena-tracer','New Match during Attack');
 await page.locator(tile(1,3)).click();await act('move',2,2);await act('fireball',3,2,false);await resetDuring('.arena-area','New Match during Fireball');
 await page.locator('[data-arena="demo-ai"]').click();await idle();
 await page.locator('[data-arena="end"]').click();await resetDuring('.arena-movement-ghost','New Match during heuristic queue');
 // Resize while a real entity is travelling; subsequent actions remeasure cells.
 await page.locator(tile(1,0)).click();await act('move',4,0,false);await effect('.arena-movement-ghost');
 await page.setViewportSize({width:1100,height:900});await idle();
 assert.equal(await page.locator(`${tile(4,0)} [data-unit-id="blue-ranger"]`).count(),1);
 assert.equal(await page.locator('.arena-movement-ghost').count(),0);checks.push('Resize during movement');
 // The shared environment switch explicitly cancels; resume reconciles server state.
 await act('move',4,2,false);await effect('.arena-movement-ghost');
 await page.locator('[data-environment="empire"]').evaluate(n=>n.click());
 assert.equal(await page.locator('.arena-movement-ghost,.arena-effect').count(),0);
 await page.locator('[data-environment="arena"]').click();await idle();checks.push('Environment switch cancels and resumes');
 await page.locator('[data-arena="end"]').click();await effect('.arena-movement-ghost');
 await page.goto(`${origin}/arena/presentation-lab`);
 await page.locator('[data-effect="Revive"]').click();await effect('.arena-float');
 await page.locator('a[href="/arena"]').click();await idle();
 assert.equal(await page.locator('.arena-effect,.arena-movement-ghost').count(),0);checks.push('Arena to lab and back during playback');
 assert.deepEqual(errors,[]);
 await writeFile(`${output}/interruption-review.json`,JSON.stringify({result:'passed',checks,errors},null,2));
 console.log(JSON.stringify({result:'passed',checks,errors},null,2));
}finally{await browser.close();}
