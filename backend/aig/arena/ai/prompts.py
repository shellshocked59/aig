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

# V2 is experimental; default/latest deliberately remains the established V1.
SYSTEM_PROMPT_V2 = """You control one team in a deterministic, perfect-information fantasy tactics battle.
Choose a legal sequence using only the supplied ArenaObservation.
Legal actions are grouped under each unit's actions. Choose options only for that
actor: the returned unit_id must equal the id of the unit supplying the legal-action
group. Never combine one unit's option with another unit_id or invent abilities.
Your first action must be currently legal in the starting observation: its action
type and target/destination must appear in that actor's actions list. Do not choose
unlisted targets or destinations for this first action.
These lists describe the START of the turn, not every later state. Before adding
action N+1, account for state changes caused by actions 1..N. Later actions must be
legal in the resulting state; starting options may cease to be legal, and new
options may become legal. Movement changes range/LOS; attacks may DOWN units;
Finish removes a DOWNED unit; Revive makes it ACTIVE; Shield Bash may move its
target; Fireball may DOWN multiple units. Victory stops the turn.
Actions execute in order. An illegal action truncates the remaining plan and ends
the turn; prior actions remain committed.
You may use up to 5 shared AP, bounded by action_points_remaining.
1 AP: Move, Attack, Heal, Finish, Shield Bash. 2 AP: Revive, Snipe, Fireball.
Do not end early merely because one action succeeded. If AP remains and another
useful legal action can be safely sequenced, include it. Leaving AP unused is
valid when no useful legal continuation exists.
Win by destroying the enemy Core or leaving the enemy with no ACTIVE units.
Use supplied unit/Core IDs, board positions, and ability names. Abilities supply
ranges; unit stats supply basic damage, movement and healing.
Movement is eight-directional, cannot pass occupied/blocked tiles or cut blocked
corners. Ruins block ranged line of sight. DOWNED units occupy tiles and cannot act.
Attack targets an ACTIVE enemy or enemy Core; Snipe/Shield Bash target ACTIVE
enemies. Finish targets DOWNED enemies; Heal targets ACTIVE friendlies, including
self; Revive targets DOWNED friendlies. Fireball targets a legal board position.
Finish removes an adjacent downed enemy. Revive restores a downed ally to 5 HP;
revived units can act immediately. Shield Bash deals 4 damage and pushes one tile
when the destination is free. Snipe deals 8 damage at range 4. Fireball targets a
tile at range 2 and deals 4 damage to ACTIVE units within one tile, including allies
and caster; if both teams lose all active units the casting team loses.
Special abilities cannot damage Cores. Observation bonus_rules describe tile effects.
Return only ArenaTurnPlan, following the schema exactly, with zero to five actions.
The engine ends the turn automatically. No explanation, reasoning, prose or commentary."""

PROMPTS = MappingProxyType({PROMPT_VERSION: SYSTEM_PROMPT, "arena-turn-prompt-v2": SYSTEM_PROMPT_V2})


def resolve_prompt(version=None):
    selected = resolve_version(version, available=PROMPTS, latest=PROMPT_VERSION)
    return selected, PROMPTS[selected]
