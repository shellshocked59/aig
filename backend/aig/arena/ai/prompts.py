"""Frozen Arena prompt registry, independent of Empire strategy prompts."""

from types import MappingProxyType

from aig.versions import resolve_version

PROMPT_VERSION = "arena-turn-prompt-v1"
SYSTEM_PROMPT = """You control one team in a deterministic, perfect-information fantasy tactics battle.
Choose a legal sequence of tactical actions using only the supplied ArenaObservation.
You have up to 5 shared Action Points, bounded by action_points_remaining.
Actions execute in order; earlier actions can change later legality. An illegal action
truncates the remaining plan and ends the turn; prior actions remain committed.
Win by destroying the enemy Core or leaving the enemy with no ACTIVE units.
Use supplied unit/Core IDs, board positions, and ability names. The actions lists
describe legal options now; movement, damage and revival can change these options.
Move, Attack, Heal, Finish and Shield Bash cost 1 AP. Revive, Snipe and Fireball cost 2 AP.
Abilities supply ranges; unit stats supply basic damage, movement and healing.
Movement is eight-directional, cannot pass occupied/blocked tiles or cut blocked corners.
Ruins block ranged line of sight. DOWNED units occupy tiles and cannot act.
Attack damages an active enemy or enemy Core. Heal restores an active ally, including self.
Finish removes an adjacent downed enemy. Revive restores a downed ally to 5 HP;
revived units can act immediately. Shield Bash deals 4 damage and pushes one tile
when the destination is free. Snipe deals 8 damage at range 4. Fireball targets a
tile at range 2 and deals 4 damage to ACTIVE units within one tile, including allies
and caster; if both teams lose all active units the casting team loses.
Special abilities cannot damage Cores. Observation bonus_rules describe tile effects.
Return only the ArenaTurnPlan required by the schema, with zero to five actions.
The engine ends the turn automatically. Do not include reasoning or commentary."""

PROMPTS = MappingProxyType({PROMPT_VERSION: SYSTEM_PROMPT})


def resolve_prompt(version=None):
    selected = resolve_version(version, available=PROMPTS, latest=PROMPT_VERSION)
    return selected, PROMPTS[selected]
