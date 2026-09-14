const paths = {
  move: 'M4 18h6V7m-4 4 4-4 4 4m-4 7h10m-4-4 4 4-4 4',
  attack: 'm5 20 14-15 2-2-1 6L8 21m-4-8 7 7',
  heal: 'M4 16q8 9 16 0M7 11a5 5 0 1 1 10 0M12 3v3m-9 4 3 1m15-1-3 1',
  finish: 'm5 5 14 14M19 5 5 19M8 3H3v5m13 13h5v-5',
  revive: 'M4 18q8 8 16 0M12 18V4m-5 6 5-6 5 6M4 12V8m16 4V8',
  shield_bash: 'm4 4 6-2 6 2v9l-6 7-6-7zm14 3 4 4-4 4',
  snipe: 'M6 3q17 9 0 18M6 3v18M3 12h19m-4-4 4 4-4 4',
  fireball: 'M13 2q2 7 6 9 6 11-6 11Q0 22 5 12l3 4q-2-8 5-14z',
};
export function actionIcon(action) {
  return `<svg class="arena-action-icon" data-action-icon="${Object.hasOwn(paths, action) ? action : 'unknown'}" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[action] || 'M5 12h14'}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}
