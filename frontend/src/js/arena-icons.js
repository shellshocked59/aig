/** Original hand-drawn vector placeholders, following the existing inline icon convention. */
const drawings = {
  knight: '<path d="M9 5h14v13l-7 9-7-9z" fill="currentColor"/><path d="M16 8v14M12 13h8" stroke="#fff"/>',
  ranger: '<path d="M10 4q22 12 0 24M10 4v24M5 16h22m-5-4 5 4-5 4" fill="none" stroke="currentColor" stroke-width="2.5"/>',
  mage: '<path d="m16 3 9 21H7zM4 26h24" fill="currentColor"/><path d="m16 10 1 3 3 1-3 1-1 3-1-3-3-1 3-1z" fill="#fff"/>',
  cleric: '<path d="M13 4h6v9h9v6h-9v9h-6v-9H4v-6h9z" fill="currentColor"/>',
  core: '<path d="m16 2 11 12-11 16L5 14z" fill="currentColor"/><path d="m16 2-4 12 4 16 4-16zM5 14h22" fill="none" stroke="#fff"/>',
  power: '<path d="M18 2 6 18h9l-2 12 13-18h-9z" fill="currentColor"/>',
  ward: '<path d="m16 3 12 5-3 13-9 8-9-8L4 8z" fill="none" stroke="currentColor" stroke-width="3"/>',
  siege: '<path d="M4 25 16 5l12 20zM4 25h24M16 12v15" fill="none" stroke="currentColor" stroke-width="3"/>',
  blocked: '<path d="m2 27 3-13 8-3 4 16zm14 0 1-20 8-4 5 24z" fill="currentColor"/>',
};

export function arenaIcon(kind) {
  return `<svg class="arena-icon" viewBox="0 0 32 32" aria-hidden="true">${drawings[kind] || ''}</svg>`;
}
