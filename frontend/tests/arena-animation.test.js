import assert from 'node:assert/strict';
import { test } from 'node:test';
import { JSDOM } from 'jsdom';
import fixtures from '../src/js/arena-lab-fixtures.json' with { type: 'json' };
import { ArenaAnimationDriver, ARENA_TIMINGS, createArenaRegistry, genericPresentation, revivePresentation, snipePresentation } from '../src/js/arena-animation.js';
import { ArenaPresentationEngine, applyPresentationEvent, visualSignature } from '../src/js/arena-presentation.js';
import { mountArena } from '../src/js/arena.js';
const gate = () => { let resolve; const promise = new Promise((r) => { resolve = r; }); return { promise, resolve }; };
const tick = async () => { for (let i=0;i<30;i++) await Promise.resolve(); };
function recorded(name) {
  const fixture = structuredClone(fixtures[name]), calls = [], checkpoints = [];
  let state = fixture.start;
  const driver = Object.fromEntries(['pulse','tracer','lunge','hp','flash','hit','float','status','move','destruction','fade','area','turn','delay'].map((method) =>
    [method, async (...args) => { calls.push([method, ...args]); }]));
  driver.cue = (...args) => { calls.push(['cue', ...args]); return () => calls.push(['cleanup']); };
  const engine = new ArenaPresentationEngine({ registry:createArenaRegistry(), driver, getState:()=>state,
    setState:(s, phase) => { state=s; if (phase) checkpoints.push(phase.effects); }, report:(...args)=>assert.fail(args.join(' ')) });
  return { fixture, calls, driver, engine, checkpoints, get state(){return state;} };
}
for (const name of Object.keys(fixtures)) test(`real default handler: ${name} preserves resolved effects`, async () => {
  const s=recorded(name); await s.engine.play(s.fixture.batch,s.fixture.final);
  assert.equal(visualSignature(s.state),visualSignature(s.fixture.final));
  const expected=s.fixture.batch.events.flatMap(e=>e.effects).filter(e=>['damage','core_damage','heal'].includes(e.type));
  assert.deepEqual(s.calls.filter(c=>c[0]==='hp').map(c=>c[1]),expected);
  for (const e of expected) assert.ok(s.calls.some(c=>c[0]==='float' && c[2]===`${e.type==='heal'?'+':'-'}${e.amount}`));
});
test('registered Snipe and Revive overrides are real handlers, distinct from fallback', async()=>{
  const registry=createArenaRegistry();
  assert.equal(registry.resolve({type:'snipe'}),snipePresentation);
  assert.equal(registry.resolve({type:'revive'}),revivePresentation);
  assert.equal(registry.resolve({type:'unknown'}),genericPresentation);
  const s=recorded('Snipe'); await s.engine.play(s.fixture.batch,s.fixture.final);
  assert.equal(s.calls.find(c=>c[0]==='pulse')[3],'snipeWindup');
  assert.equal(s.calls.find(c=>c[0]==='tracer')[4],true);
  const r=recorded('Revive'); await r.engine.play(r.fixture.batch,r.fixture.final);
  assert.equal(r.calls.find(c=>c[0]==='cue')[3],'arena-restorative arena-revive');
  assert.equal(r.calls.find(c=>c[0]==='pulse')[3],'reviveWindup');
  assert.equal(r.calls.find(c=>c[0]==='status')[1].type,'revived');
});
test('attack connects actor to target before committing HP; HP commits during feedback',async()=>{
  const s=recorded('Attack'), travel=gate(), impact=gate();
  s.driver.tracer=async()=>{s.calls.push(['travel']);await travel.promise;};
  s.driver.float=async()=>{s.calls.push(['float']);await impact.promise;};
  const playing=s.engine.play(s.fixture.batch,s.fixture.final); await tick();
  assert.equal(s.state.units.find(u=>u.id==='red-knight').hp,18);
  assert.deepEqual(s.calls.slice(0,3).map(c=>c[0]),['cue','pulse','travel']);
  travel.resolve();await tick();
  assert.equal(s.state.units.find(u=>u.id==='red-knight').hp,12);
  assert.equal(s.calls.at(-1)[0],'float');
  impact.resolve();await playing;
});
test('move commits only after the continuous path animation completes',async()=>{
  const s=recorded('Move'), moving=gate();let path;
  s.driver.move=async(...args)=>{path=args[4];await moving.promise;};
  const p=s.engine.play(s.fixture.batch,s.fixture.final);await tick();
  assert.equal(s.state.units.find(u=>u.id==='blue-knight').x,3);
  assert.deepEqual(path,s.fixture.batch.events[0].path);
  moving.resolve();await p;assert.equal(s.state.units.find(u=>u.id==='blue-knight').x,2);
});
test('Finish retains the body until fade completes',async()=>{
  const s=recorded('Finish'), fade=gate();s.driver.fade=()=>fade.promise;
  const p=s.engine.play(s.fixture.batch,s.fixture.final);await tick();
  assert.ok(s.state.units.some(u=>u.id==='red-knight'));
  fade.resolve();await p;assert.equal(s.state.units.some(u=>u.id==='red-knight'),false);
});
test('Bash damage completes before push; absent push never creates motion',async()=>{
  const s=recorded('Shield Bash'), damage=gate();s.driver.float=()=>damage.promise;
  const p=s.engine.play(s.fixture.batch,s.fixture.final);await tick();
  assert.equal(s.state.units.find(u=>u.id==='red-knight').hp,14);
  assert.equal(s.calls.some(c=>c[0]==='move'),false);
  damage.resolve();await p;assert.ok(s.calls.some(c=>c[0]==='move' && c[6]===true));
  s.calls.length=0;
  const e=structuredClone(s.fixture.batch.events[0]);e.effects=e.effects.filter(e=>e.type!=='push');
  await genericPresentation(e,s.driver,new AbortController().signal);
  assert.equal(s.calls.some(c=>c[0]==='move'),false);
});
test('Fireball commits victims in event order and includes allies; Core destruction precedes victory',async()=>{
  const s=recorded('Fireball');await s.engine.play(s.fixture.batch,s.fixture.final);
  assert.ok(s.calls.some(c=>c[0]==='area'));
  assert.deepEqual(s.checkpoints[0],s.fixture.batch.events[0].effects);
  assert.ok(s.calls.some(c=>c[0]==='hp' && c[1].owner_id==='blue'));
  const v=recorded('Victory'), destroyed=gate();v.driver.destruction=()=>destroyed.promise;
  const p=v.engine.play(v.fixture.batch,v.fixture.final);await tick();
  assert.equal(v.state.cores.find(c=>c.id==='red-core').hp,0);assert.equal(v.state.winner_player_id,null);
  assert.equal(v.calls.some(c=>c[0]==='delay'&&c[1]==='victoryDelay'),false);
  destroyed.resolve();await p;assert.equal(v.state.winner_player_id,'blue');
});
test('reset invalidates checkpoint closures as well as final event commits',async()=>{
  const s=recorded('Attack'), pending=gate();let checkpoint;
  s.engine.registry.register('attack',async(_e,_d,_s,{commit})=>{checkpoint=commit;await pending.promise;commit(s.fixture.batch.events[0].effects);}, 'knight');
  const p=s.engine.play(s.fixture.batch,s.fixture.final);s.engine.cancel();
  checkpoint(s.fixture.batch.events[0].effects);pending.resolve();await p;
  assert.equal(s.state.units.find(u=>u.id==='red-knight').hp,18);
});
async function domDriver(name='Attack', options={}) {
  const dom=new JSDOM('<main></main>'),root=dom.window.document.querySelector('main');
  const driver=new ArenaAnimationDriver(root,options);
  const game=mountArena(root,{getGame:async()=>structuredClone(fixtures[name].start)},{driver});await game.whenIdle();
  root.querySelector('.arena-overlay').getBoundingClientRect=()=>({left:0,top:0});
  for(const cell of root.querySelectorAll('.arena-tile'))cell.getBoundingClientRect=()=>({left:+cell.dataset.x*100,top:+cell.dataset.y*130,width:95,height:125});
  return {dom,root,driver,close(){game.destroy();dom.window.close();}};
}
test('movement uses one ghost, measured path frames, capped duration, and restores source on abort',async()=>{
  const s=await domDriver('Move'),controller=new AbortController(),pending=gate();let frames,duration;
  s.driver.animate=async(_n,f,t)=>{frames=f;duration=t;await pending.promise;};
  try{
    const p=s.driver.move('blue-knight',{x:3,y:2},{x:1,y:1},controller.signal,[{x:3,y:2},{x:2,y:2},{x:2,y:1},{x:1,y:1}]);
    assert.equal(s.root.querySelectorAll('.arena-movement-ghost').length,1);
    assert.equal(s.driver.entity('blue-knight').style.visibility,'hidden');assert.equal(frames.length,4);
    assert.match(frames[2].transform,/-100px.*-130px/);assert.equal(duration,330);
    controller.abort();s.driver.clear();assert.equal(s.driver.entity('blue-knight').style.visibility,'');
    assert.equal(s.driver.nodes.size,0);pending.resolve();await p;
  }finally{s.close();}
});
test('WAAPI speed and instant mode scale the actual clock and clean transient nodes',async()=>{
  const s=await domDriver('Attack',{speed:2}),signal=new AbortController().signal;let options;
  const node=s.driver.entity('blue-knight');node.animate=(_f,o)=>{options=o;return{finished:Promise.resolve(),cancel(){}};};
  try{
    await s.driver.pulse('blue-knight',signal);assert.equal(options.duration,ARENA_TIMINGS.attackWindup/2);
    s.driver.instant=true;await s.driver.flash({x:4,y:2},signal);await s.driver.float({x:4,y:2},'-6',signal);
    assert.equal(s.driver.duration('moveDuration'),0);assert.equal(s.driver.nodes.size,0);assert.equal(s.driver.animations.size,0);
  }finally{s.close();}
});
test('HP primitive updates numeric/accessible HP and animates resolved bar endpoints',async()=>{
  const s=await domDriver();let frames;
  s.driver.animate=async(_n,f)=>{frames=f;};
  try{
    s.driver.entity('red-knight').closest('button').click();
    await s.driver.hp(fixtures.Attack.batch.events[0].effects[0],new AbortController().signal);
    const entity=s.driver.entity('red-knight');assert.equal(entity.querySelector('meter').value,12);
    assert.equal(entity.querySelector('[data-hp-label]').textContent,'12/18 HP');
    assert.equal(s.root.querySelector('[data-selected-hp]').textContent,'12/18 HP');assert.match(entity.parentElement.getAttribute('aria-label'),/HP 12\/18/);
    assert.equal(frames[0].width,'100%');assert.ok(parseFloat(frames[1].width)<67);
  }finally{s.close();}
});
test('reduced motion omits travel/rotation but retains damage, revive and exact Fireball cells',async()=>{
  const s=await domDriver('Revive',{reducedMotion:true}),signal=new AbortController().signal,calls=[];
  s.driver.animate=async(n,f)=>{calls.push({node:n,frames:f});};
  try{
    await revivePresentation(fixtures.Revive.batch.events[0],s.driver,signal);
    assert.ok(calls.some(c=>c.node?.textContent==='REVIVE'));
    assert.ok(calls.some(c=>c.node?.textContent==='+5'));
    assert.equal(calls.some(c=>c.node?.classList.contains('arena-tracer')),false);
    assert.equal(calls.some(c=>c.frames.some(f=>f.transform?.includes('rotate'))),false);
    await s.driver.area({x:0,y:0},signal);
    assert.equal(calls.filter(c=>c.node?.classList.contains('arena-area')).length,4);
    assert.equal(s.driver.nodes.size,0);
  }finally{s.close();}
});

test('transient geometry is set as real CSS properties and an aborted WAAPI clock cleans up',async()=>{
  const s=await domDriver(),controller=new AbortController();let cancelled=0;
  try{
    const original=s.dom.window.HTMLElement.prototype.animate;
    s.dom.window.HTMLElement.prototype.animate=function(){let reject;const finished=new Promise((_r,j)=>{reject=j;});return{finished,cancel(){cancelled++;reject(new Error('cancelled'));}};}; 
    const p=s.driver.flash({x:4,y:2},controller.signal);
    const node=s.root.querySelector('.arena-impact');
    assert.equal(node.style.getPropertyValue('--cell-width'),'95px');
    assert.equal(node.style.getPropertyValue('--cell-height'),'125px');
    controller.abort();await p;
    assert.ok(cancelled>0);assert.equal(s.driver.animations.size,0);assert.equal(s.driver.nodes.size,0);
    s.dom.window.HTMLElement.prototype.animate=original;
  }finally{s.close();}
});
for(const unitClass of ['knight','ranger','mage','cleric'])test(`movement is independent of ${unitClass} glyph`,async()=>{
  const s=await domDriver('Move'),pending=gate(),signal=new AbortController().signal;
  s.driver.animate=()=>pending.promise;
  try{
    const entity=s.driver.entity(`blue-${unitClass}`),cell=entity.parentElement;
    const from={x:+cell.dataset.x,y:+cell.dataset.y};
    const p=s.driver.move(`blue-${unitClass}`,from,{x:2,y:0},signal);
    assert.equal(s.root.querySelectorAll('.arena-movement-ghost').length,1);
    assert.equal(entity.style.visibility,'hidden');pending.resolve();await p;
    assert.equal(entity.style.visibility,'');assert.equal(s.driver.nodes.size,0);
  }finally{s.close();}
});
