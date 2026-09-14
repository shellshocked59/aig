import { mountGame } from './game.js';
import { mountPresentationLab } from './arena-presentation-lab.js';
import { mountArena } from './arena.js';

/** Independent roots preserve each view/session when switching environments. */
export function mountEnvironments(root, empireApi, arenaApi) {
  if (root.ownerDocument.defaultView.location.pathname === '/arena/presentation-lab') return mountPresentationLab(root);
  root.innerHTML = `<nav class="environment-picker" aria-label="Environment">
    <button data-environment="arena" aria-pressed="false">Arena</button>
    <button data-environment="empire" aria-pressed="true">Empire</button>
    </nav><div data-view="empire"></div><div data-view="arena" hidden></div>`;
  const empireRoot = root.querySelector('[data-view="empire"]');
  const arenaRoot = root.querySelector('[data-view="arena"]');
  const empire = mountGame(empireRoot, empireApi);
  let arena = null;
  function select(event) {
    const button = event.target.closest('[data-environment]');
    if (!button) return;
    const isArena = button.dataset.environment === 'arena';
    empireRoot.hidden = isArena;
    arenaRoot.hidden = !isArena;
    if (!isArena) arena?.cancel?.();
    root.querySelectorAll('[data-environment]').forEach((b) => b.setAttribute('aria-pressed', String(b === button)));
    if (isArena && !arena) arena = mountArena(arenaRoot, arenaApi);
    else if (isArena) arena.resume();
  }
  root.addEventListener('click', select);
  if (!/^\/empire\/?$/.test(root.ownerDocument.defaultView.location.pathname)) {
    root.querySelector('[data-environment="arena"]').click();
  }
  return { empire, get arena() { return arena; }, destroy() {
    root.removeEventListener('click', select); empire.destroy(); arena?.destroy();
  } };
}
