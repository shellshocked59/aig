// Presentation only: atlas locations and stable faction identities, never rules.
export const terrainSprites = Object.freeze({
  grassland: 'sprite-grassland', plains: 'sprite-plains', forest: 'sprite-forest',
  hills: 'sprite-hills', mountains: 'sprite-mountains', water: 'sprite-water',
});
export const unitSprites = Object.freeze({
  settler: 'sprite-settler', warrior: 'sprite-warrior', scout: 'sprite-scout',
  archer: 'sprite-archer', spearman: 'sprite-spearman',
});
const factions = {
  A: { name: 'Amber League', className: 'faction-a' },
  B: { name: 'Azure Union', className: 'faction-b' },
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
