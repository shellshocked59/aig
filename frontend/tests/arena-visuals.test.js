import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import { unitVisualRegistry, unitVisual, renderArenaPiece } from '../src/js/arena-unit-visuals.js';
import { mountArena } from '../src/js/arena.js';
import { mountPresentationLab } from '../src/js/arena-presentation-lab.js';
import { actionIcon } from '../src/js/arena-action-icons.js';
import { createArenaRegistry, ArenaAnimationDriver, genericPresentation } from '../src/js/arena-animation.js';
import fixtures from '../src/js/arena-lab-fixtures.json' with { type:'json' };

for (const kind of ['knight','ranger','mage','cleric','core']) test(`${kind}: original art, ownership and downed identity survive composition`, () => {
  const dom = new JSDOM(`<main>${['blue','red'].map(owner_id => renderArenaPiece({id:owner_id,owner_id,unit_type:kind === 'core' ? undefined : kind,status:'downed',hp:0,max_hp:18})).join('')}</main>`);
  const root = dom.window.document;
  assert.equal(root.querySelectorAll(`[data-class-art="${kind}"]`).length,2);
  for (const team of ['blue','red']) {
    const entity = root.querySelector(`.arena-team-${team}`);
    assert.match(entity.querySelector('.arena-owner').textContent,new RegExp(team,'i'));
    assert.ok(entity.querySelector('.arena-token-base'));
    assert.equal(entity.querySelector('meter').value,0);
    assert.equal(entity.querySelector('svg').getAttribute('aria-hidden'),'true');
    assert.ok(entity.querySelector('.arena-downed-badge'));
  }
  dom.window.close();
});
test('registry has distinct class silhouettes and safe unknown fallback', () => {
  assert.equal(new Set(['knight','ranger','mage','cleric'].map(k=>unitVisualRegistry[k])).size,4);
  assert.match(unitVisual('<unknown>'),/data-class-art="unknown"/);
  assert.doesNotMatch(unitVisual('<unknown>'),/<unknown>/);
});
for (const name of ['move','attack','heal','finish','revive','shield_bash','snipe','fireball']) test(`${name}: decorative original action icon`, () => {
  assert.match(actionIcon(name),new RegExp(`data-action-icon="${name}"`));
  assert.match(actionIcon(name),/aria-hidden="true"/);
});
test('selection reuses artwork, action labels/AP and disabled legality remain authoritative; debug toggle persists',async()=>{
  const dom=new JSDOM('<main></main>'),root=dom.window.document.querySelector('main');
  const game=mountArena(root,{getGame:async()=>structuredClone(fixtures.Attack.start)});
  try {
    await game.whenIdle();root.querySelector('[data-unit-id="blue-knight"]').closest('button').click();
    assert.ok(root.querySelector('.arena-selected [data-class-art="knight"]'));
    assert.ok(root.querySelector('.arena-selected-art [data-class-art="knight"]'));
    for(const b of root.querySelectorAll('[data-mode]')) {
      const cost=fixtures.Attack.start.units.find(u=>u.id==='blue-knight').abilities[b.dataset.mode].ap_cost;
      assert.ok(b.querySelector(`[data-action-icon="${b.dataset.mode}"]`));
      assert.ok(b.textContent.includes(`${cost} AP`));assert.equal(b.disabled,true);
    }
    assert.equal(root.querySelector('.arena-show-coordinates'),null);
    root.querySelector('[data-arena="coordinates"]').click();assert.ok(root.querySelector('.arena-show-coordinates'));
    root.querySelector('[data-unit-id="blue-mage"]').closest('button').click();assert.ok(root.querySelector('.arena-show-coordinates'));
  } finally {game.destroy();dom.window.close();}
});
const cases=[['Knight Attack','arena-physical'],['Ranger Attack','arena-precision'],['Mage Attack','arena-arcane'],['Cleric Attack','arena-radiant'],['Snipe','arena-precision'],['Shield Bash','arena-bash'],['Heal','arena-restorative'],['Revive','arena-revive'],['Fireball','arena-fire']];
for(const [name,motif] of cases) test(`${name}: real specialized handler retains motif and resolved feedback with reduced motion`,async()=>{
  const dom=new JSDOM('<main></main>'),root=dom.window.document.querySelector('main');
  const driver=new ArenaAnimationDriver(root,{reducedMotion:true});
  const game=mountArena(root,{getGame:async()=>structuredClone(fixtures[name].start)},{driver});
  try{
    await game.whenIdle();
    root.querySelector('.arena-overlay').getBoundingClientRect=()=>({left:0,top:0});
    for(const cell of root.querySelectorAll('.arena-tile'))cell.getBoundingClientRect=()=>({left:+cell.dataset.x*100,top:+cell.dataset.y*130,width:95,height:125});
    const calls=[];driver.animate=async(node,frames)=>{calls.push({node,frames});};
    const event=fixtures[name].batch.events[0],handler=createArenaRegistry().resolve(event);
    assert.notEqual(handler,genericPresentation);
    await handler(event,driver,new AbortController().signal);
    assert.ok(calls.some(c=>c.node?.classList.contains(motif)));
    assert.ok(calls.some(c=>c.node?.classList.contains('arena-float')));
    assert.equal(calls.some(c=>c.node?.classList.contains('arena-tracer')),false);
    assert.equal(calls.some(c=>c.frames.some(f=>f.transform?.includes('rotate'))),false);
    assert.equal(driver.nodes.size,0);
  }finally{game.destroy();dom.window.close();}
});
test('gallery exposes all 16 actual-renderer variants with selected active states and nine ability fixtures',async()=>{
  const dom=new JSDOM('<main></main>'),root=dom.window.document.querySelector('main'),lab=mountPresentationLab(root);
  try{
    await lab.whenIdle();
    assert.equal(root.querySelectorAll('.arena-gallery .arena-entity').length,16);
    assert.equal(root.querySelectorAll('.arena-gallery .arena-downed').length,8);
    assert.equal(root.querySelectorAll('.arena-gallery .arena-selected').length,8);
    for(const [name] of cases)assert.ok(root.querySelector(`[data-effect="${name}"]`));
  }finally{lab.destroy();dom.window.close();}
});
