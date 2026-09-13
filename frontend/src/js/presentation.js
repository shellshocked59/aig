// Presentation only: atlas locations and stable faction identities, never rules.
export const terrainSprites = Object.freeze({
  grassland: 'sprite-grassland', plains: 'sprite-plains', forest: 'sprite-forest',
  hills: 'sprite-hills', mountains: 'sprite-mountains', water: 'sprite-water',
});
export const unitSprites = Object.freeze({
  settler: 'sprite-settler', warrior: 'sprite-warrior', scout: 'sprite-scout',
  archer: 'sprite-archer', spearman: 'sprite-spearman',
});
// Original compact vector icons, independent of terrain/unit atlas coordinates.
export const resourceSprites = Object.freeze({
  wheat: '<path d="M12 22V5M12 15L6 10M12 11L18 6"/><path d="M6 10L4 5L9 7ZM18 6L20 2L15 4Z" fill="#eac45b"/>',
  cattle: '<path d="M4 7L2 3M20 7L22 3"/><path d="M4 7H20L18 20H6Z" fill="#e6c8a3"/><path d="M7 10H10V14H7Z" fill="#544338"/><circle cx="15" cy="11" r="1"/>',
  iron: '<path d="M3 18L6 8L14 3L21 11L19 20Z" fill="#a4acb7"/><path d="M6 8L13 12L14 3M13 12L19 20"/>',
  gems: '<path d="M3 8L8 3H17L22 8L12 22Z" fill="#bc80eb"/><path d="M3 8H22M8 3L8 8L12 22L17 8L17 3"/>',
  spices: '<path d="M9 5Q16 3 20 8Q21 18 5 21Q13 16 9 5Z" fill="#e46b42"/><path d="M13 5Q11 1 16 2"/>',
});
export const campSprite = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 21L12 3L22 21Z" fill="#ae6942" stroke="#39251f"/><path d="M8 21L12 12L16 21" fill="#39251f"/><path d="M12 3V1M12 4H20L17 7H12" fill="#bf3d37" stroke="#39251f"/></svg>';
const factions = {
  barbarians: { name: 'Barbarians', className: 'faction-barbarian' },
  A: { name: 'Amber League', className: 'faction-a' },
  B: { name: 'Azure Union', className: 'faction-b' },
  C: { name: 'Jade Assembly', className: 'faction-c' },
  D: { name: 'Violet Dominion', className: 'faction-d' },
};
export function faction(id) {
  return factions[id] || { name: id || 'Unclaimed', className: 'faction-neutral' };
}
export function label(value) {
  return value ? value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()) : 'None';
}
export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}
