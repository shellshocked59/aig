import { escapeHtml as esc } from './presentation.js';
import { actionIcon } from './arena-action-icons.js';

const abilities = {
  move: ['Move', 'Move to a highlighted tile within this unit’s movement range. Units, Cores and ruins block the path.'],
  attack: ['Attack', 'Attack an enemy unit or Core within this unit’s attack range. Damage and range depend on the unit; terrain bonuses can change damage.'],
  shield_bash: ['Shield Bash', 'Knight ability: deal 4 base damage to an adjacent enemy unit. If the target survives, push it one tile directly away from the Knight. No push if that tile is blocked or off the board. Cannot target Cores.'],
  snipe: ['Snipe', 'Ranger ability: deal 8 base damage to an enemy unit within range 4. Ruins block line of sight. Cannot target Cores.'],
  fireball: ['Fireball', 'Mage ability: choose an impact tile within range 2. Deal 4 base damage to every active unit within one tile of impact, including allies and the caster. Cannot damage Cores.'],
  heal: ['Heal', 'Cleric ability: restore 5 HP to an active friendly unit within range 2, up to its maximum HP. The Cleric can heal itself.'],
  revive: ['Revive', 'Cleric ability: restore a downed friendly unit within range 2 to active status with 5 HP. It can act immediately.'],
  finish: ['Finish', 'Remove an adjacent downed enemy unit from the board, freeing its tile and preventing it from being revived.'],
};

export const actionName = action => abilities[action]?.[0] || action.replaceAll('_', ' ');

export function abilityHelp(action, busy = false) {
  const name = esc(actionName(action));
  const id = esc(action);
  return `<span class="arena-ability-help"><button type="button" data-arena="ability-help" ${busy ? 'disabled' : ''} aria-describedby="arena-help-${id}" aria-label="About ${name}" aria-expanded="false" aria-controls="arena-help-${id}">i</button><span class="arena-ability-tip" id="arena-help-${id}" role="tooltip"><strong>${name}</strong>${abilities[action]?.[1] || 'Choose a highlighted legal target.'}</span></span>`;
}

export function rulesHelp() {
  const section = (icon, title, body) => `<section class="arena-rule-section"><h3>${actionIcon(icon)}${title}</h3>${body}</section>`;
  return `<details class="arena-panel arena-rules"><summary>Rules & abilities</summary>
    ${section('attack', 'Win the battle', '<p>Destroy the enemy Core or down every enemy unit. If Fireball downs both teams, the casting team loses.</p>')}
    ${section('move', 'Your turn · 5 AP', '<p>Spend AP on actions. A unit can act repeatedly. At 0 AP, choose <strong>End Turn</strong>.</p><p><strong>1 AP</strong> · Move, Attack, Heal, Shield Bash, Finish<br><strong>2 AP</strong> · Snipe, Fireball, Revive</p>')}
    ${section('move', 'Movement & cover', '<p>Move in eight directions. Units, Cores and ruins block movement; you cannot cut blocked corners. Ruins also block ranged line of sight.</p><dl class="arena-terrain-help"><dt>POWER</dt><dd>+2 attack damage</dd><dt>WARD</dt><dd>−2 incoming unit damage (minimum 1)</dd><dt>SIEGE</dt><dd>+4 damage to Cores</dd></dl>')}
    ${section('revive', 'Downed units', '<p>A downed unit stays on its tile and cannot act. <strong>Revive</strong> brings an ally back; <strong>Finish</strong> removes a downed enemy.</p>')}
    <section class="arena-rule-section"><h3>${actionIcon('shield_bash')}Ability reference</h3><div class="arena-ability-reference">${Object.entries(abilities).map(([action, [name, description]]) => `<details><summary>${actionIcon(action)}${name}</summary><p>${description}</p></details>`).join('')}</div><p>Damage values are base damage; terrain bonuses apply.</p></section>
  </details>`;
}
