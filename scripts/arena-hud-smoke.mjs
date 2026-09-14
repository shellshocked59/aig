/** Phase 6 real Chromium acceptance. Local Arena only; never invokes model providers. */
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium} from '../.local/arena-ui-tools/node_modules/playwright/index.mjs';
const origin=process.argv[2] || 'http://127.0.0.1:5173';
if(!['localhost','127.0.0.1'].includes(new URL(origin).hostname)) throw Error('Local origin required');
const output=process.env.ARENA_EVIDENCE_DIR || 'artifacts/arena-ui-phase6';
await mkdir(output,{recursive:true});
const browser=await chromium.launch({channel:process.env.ARENA_BROWSER || 'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080}}), errors=[], checks=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error' && m.text().includes('Arena presentation')) errors.push(m.text());});
await page.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
// Guard the harness against accidentally creating a paid/live provider match.
await page.route('**/api/arena/demo-ai/*',r=>['heuristic','heuristic-v2'].includes(r.request().url().split('/').at(-1))?r.continue():r.abort());
const tile=(x,y)=>`[data-arena="tile"][data-x="${x}"][data-y="${y}"]`;
const idle=()=>page.locator('[data-arena="end"]:enabled').waitFor();
const shot=name=>page.screenshot({path:`${output}/${name}.png`,fullPage:true});
async function local(){await page.request.post(`${origin}/api/arena/demo`);await page.locator('[data-arena="refresh"]').click();await idle();}
async function act(action,x,y){await page.locator(`[data-mode="${action}"]`).click();assert.equal(await page.locator(`${tile(x,y)}.arena-legal`).count(),1);await page.locator(tile(x,y)).click();await idle();}
async function end(){await page.locator('[data-arena="end"]').click();await idle();}
try {
 await page.goto(`${origin}/arena`);await page.locator('.arena-experimental > summary').click();await page.locator('[data-arena="demo-ai-v2"]').click();await idle();await shot('default');
 for(const [w,h] of [[2560,1440],[1920,1080],[1440,1080],[1080,900],[900,900]]) {
  await page.setViewportSize({width:w,height:h});
  await page.locator(tile(1,3)).click();
  const geometry=await page.evaluate(()=>{
   const rect=s=>document.querySelector(s).getBoundingClientRect().toJSON();
   return {board:rect('.arena-board'),deck:rect('.arena-command-deck'),overflow:document.documentElement.scrollWidth>innerWidth,
   fits:[...document.querySelectorAll('.arena-board .arena-entity')].every(n=>{const t=n.parentElement.getBoundingClientRect(),a=n.querySelector('svg').getBoundingClientRect(),hp=n.querySelector('[data-hp-label]').getBoundingClientRect();return a.left>=t.left && a.right<=t.right && a.top>=t.top && hp.bottom<=t.bottom;})};
  });
  assert.equal(geometry.overflow,false,`${w} overflow`);assert.ok(geometry.fits,`${w} art fit`);
  assert.ok(geometry.deck.y>=geometry.board.y+geometry.board.height,`${w} deck below board`);
  assert.ok(geometry.board.y+geometry.board.height<=h,`${w} board visible`);
  if(w>=1440)assert.ok(geometry.deck.y+geometry.deck.height<=h,`${w} deck visible`);
  checks.push({viewport:[w,h],...geometry}); await shot(`selected-mage-${w}`);
 }
 await page.setViewportSize({width:1440,height:1080});
 for(const [y,kind] of [[1,'knight'],[0,'ranger'],[3,'mage'],[4,'cleric']]) {await page.locator(tile(1,y)).click();await shot(`selected-${kind}`);}
 await page.locator(tile(1,0)).click();await page.locator('[data-mode="move"]').click();await shot('target-move');
 assert.ok(await page.locator('.arena-target-move.arena-legal').count());await page.locator('[data-arena="cancel"]').click();
 await act('move',4,0);await page.locator('[data-mode="attack"]').click();await shot('target-attack');await page.locator('[data-arena="cancel"]').click();
 await act('snipe',7,0);assert.ok(await page.locator('.arena-downed').count());await shot('downed');
 await page.locator('[data-arena="end"]').click();
 await page.waitForFunction(()=>/Action \d+ \/ \d+/.test(document.querySelector('.arena-playback-status')?.textContent));
 assert.ok(await page.locator('.arena-command-deck.arena-passive').count());await shot('ai-turn');await idle();
 assert.equal(await page.locator('.arena-command-deck.arena-passive').count(),0);
 // Real local commands exercise support, AOE, and victory without inference.
 await local();await page.locator(tile(1,3)).click();await page.locator('[data-mode="fireball"]').click();await shot('target-fireball');await page.locator('[data-arena="cancel"]').click();
 await end();await page.locator(tile(7,0)).click();await act('move',6,3);await act('move',4,4);await act('attack',1,4);await end();
 await page.locator(tile(1,4)).click();await page.locator('[data-mode="heal"]').click();await shot('target-heal');await page.locator(tile(1,4)).click();await idle();
 await page.locator(tile(1,0)).click();await act('move',4,0);await act('move',5,2);await act('attack',8,2);await act('attack',8,2);await end();await end();
 await page.locator(tile(5,2)).click();await act('attack',8,2);
 await page.locator('[data-mode="attack"]').click();await page.locator(tile(8,2)).click();await page.locator('.arena-winner').waitFor();await page.locator('.arena-command-deck[aria-busy="false"]').waitFor();await shot('victory');
 assert.match(await page.locator('.arena-status').innerText(),/Blue Team wins/);
 await page.locator('[data-arena="reset"]').click();await idle();
 assert.equal(await page.locator('[data-arena="coordinates"]').count(),0);
 assert.equal(await page.locator('.arena-details details').count(),0);
 await page.locator('.arena-view > .arena-rules summary').first().click();
 assert.equal(await page.locator('.arena-view > .arena-rules[open]').count(),1);
 // Restore a useful default offline game for the user.
 await page.locator('.arena-experimental > summary').click();await page.locator('[data-arena="demo-ai-v2"]').click();await idle();
 assert.deepEqual(errors,[]);
 await writeFile(`${output}/browser-review.json`,JSON.stringify({result:'passed',errors,checks},null,2));
 console.log('Phase 6: five viewport sizes, four classes, four targeting modes, downed, victory, AI playback, reset and rules accordion passed.');
} finally {await browser.close();}
