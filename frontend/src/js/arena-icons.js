import { unitVisual, unitVisualRegistry } from './arena-unit-visuals.js';
/** Original terrain marks; class artwork resolves through the shared registry, following the existing inline icon convention. */
const drawings = {
  power: '<path d="M18 2 6 18h9l-2 12 13-18h-9z" fill="currentColor"/>',
  ward: '<path d="m16 3 12 5-3 13-9 8-9-8L4 8z" fill="none" stroke="currentColor" stroke-width="3"/>',
  siege: '<path d="M4 25 16 5l12 20zM4 25h24M16 12v15" fill="none" stroke="currentColor" stroke-width="3"/>',
  blocked: '<path d="m2 27 3-13 8-3 4 16zm14 0 1-20 8-4 5 24z" fill="currentColor"/>',
};

export function arenaIcon(kind) {
  if (Object.hasOwn(unitVisualRegistry, kind)) return unitVisual(kind);
  return `<svg class="arena-icon" viewBox="0 0 32 32" aria-hidden="true">${drawings[kind] || ''}</svg>`;
}
