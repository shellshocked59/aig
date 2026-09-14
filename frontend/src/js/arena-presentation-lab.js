import { renderArenaPiece } from './arena-unit-visuals.js';
import { mountArena } from './arena.js';
import effectFixtures from './arena-lab-fixtures.json' with { type: 'json' };
import aiFixtures from './arena-ai-playback-fixtures.json' with { type: 'json' };
const fixtures = { ...effectFixtures, 'Play sample AI turn': aiFixtures.heuristic };

/** A local API-shaped fixture source feeds the actual Arena controller and engine. */
export function mountPresentationLab(root) {
  root.innerHTML = `<section class="arena-view"><h1>Arena presentation lab</h1>
    <p>Local authoritative examples. Choose an effect to reset its fixture and replay it.</p>
    <a href="/arena">Back to Arena</a><div class="arena-lab-controls">
    ${Object.keys(fixtures).map((name) => `<button data-effect="${name}">${name}</button>`).join('')}
    <button data-lab-reset>Reset fixture</button>
    <label>Speed <select data-speed><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select></label>
    <label><input type="checkbox" data-instant> Instant</label></div>
    <details><summary>Class gallery  /  Blue / Red  /  Active / Downed</summary>${classGallery()}</details>
    <details><summary>Event JSON</summary><pre data-event-json></pre></details></section><div data-lab-game></div>`;
  const gameRoot = root.querySelector('[data-lab-game]');
  let game, selected = 'Attack', generation = 0, pending;
  async function show(name, play = true) {
    selected = name;
    const current = ++generation;
    game?.destroy();
    const fixture = fixtures[name];
    game = mountArena(gameRoot, {
      getGame: async () => structuredClone(fixture.start),
      createDemo: async () => structuredClone(fixture.start),
      createAiDemo: async () => structuredClone(fixture.start),
      command: async () => ({ ...structuredClone(fixture.final), presentation: structuredClone(fixture.batch) }),
    }, { coordinates: true, instant: root.querySelector('[data-instant]').checked, speed: Number(root.querySelector('[data-speed]').value) });
    root.querySelector('[data-event-json]').textContent = JSON.stringify(fixture.batch, null, 2);
    await game.whenIdle();
    if (generation !== current) return;
    if (play) gameRoot.querySelector('[data-arena="end"]').click();
    await game.whenIdle();
  }
  function click(event) {
    if (event.target.dataset.effect) pending = show(event.target.dataset.effect);
    if (event.target.hasAttribute('data-lab-reset')) pending = show(selected, false);
  }
  root.addEventListener('click', click);
  pending = show(selected, false);
  return { whenIdle: () => pending, destroy() { generation++; game?.destroy(); root.removeEventListener('click', click); } };
}

function classGallery() {
  return `<p class="arena-gallery-note">Original miniatures at board scale. White outlines show selection. Round Blue bases and angular Red bases retain ownership when downed.</p><div class="arena-gallery">${['knight','ranger','mage','cleric'].map(kind => `<section><h3>${kind}</h3><div class="arena-gallery-variants">${['blue','red'].flatMap(team => ['active','downed'].map(status => `<div class="arena-tile arena-team-${team} ${status === 'downed' ? 'arena-downed' : 'arena-selected'}" role="img" aria-label="${team} ${kind} ${status}${status === 'active' ? ' selected' : ''}">${renderArenaPiece({id:`gallery-${team}-${kind}-${status}`,unit_type:kind,owner_id:team,status,hp:status === 'downed' ? 0 : 10,max_hp:10})}</div>`)).join('')}</div></section>`).join('')}</div>`;
}
