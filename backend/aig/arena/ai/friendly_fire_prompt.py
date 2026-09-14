"""Opt-in behavior registry; historical registry and defaults remain frozen."""
from types import MappingProxyType

from aig.arena.ai.prompts import PROMPTS, SYSTEM_PROMPT
from aig.arena.ai.openai import OpenAIArenaTurnProvider

PROMPT_VERSION = "arena-turn-prompt-v3"
GUIDANCE = """Before selecting an action, evaluate its resolved effect on the current board,
not merely whether it is legal. For area damage, account for every affected
friendly and enemy. Use the current legal-action catalog for movement and targets;
when sequencing later actions, account for changes caused by earlier actions.
FIREBALL HAS FRIENDLY FIRE. Before choosing an impact, examine the target tile
and all 8 adjacent tiles: a 3x3 area (Chebyshev radius 1). Identify every ACTIVE
friendly and enemy there. Fireball damages ALL of them, including allies and
the caster. DOWNED units and Cores are not damaged by Fireball.
A selectable impact is not necessarily useful. Avoid an area with no ACTIVE
enemies unless the actual state supplies a concrete tactical reason; avoid
damaging only your own team. Compare friendly damage and possible downs with
Attack, Snipe, movement or another legal action. Friendly fire can be acceptable
when its actual consequences justify the tradeoff; it is not categorically
forbidden. If both teams lose all ACTIVE units, the casting team loses.
"""
PROMPT = SYSTEM_PROMPT.replace("Return only the ArenaTurnPlan", GUIDANCE + "Return only the ArenaTurnPlan")
BEHAVIOR_PROMPTS = MappingProxyType({**PROMPTS, PROMPT_VERSION: PROMPT})


def resolve_behavior_prompt(version):
    if version not in BEHAVIOR_PROMPTS:
        raise ValueError("unknown Arena behavior prompt")
    return version, BEHAVIOR_PROMPTS[version]


class LunaBehaviorProvider(OpenAIArenaTurnProvider):
    """Explicit selection only; transport, schema, repair and profile are inherited."""
    resolve_prompt = staticmethod(resolve_behavior_prompt)
