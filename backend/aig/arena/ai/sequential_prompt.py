"""Opt-in V1 descendant; historical prompt registries and controls stay frozen."""
from hashlib import sha256
from types import MappingProxyType

from aig.arena.ai.prompts import SYSTEM_PROMPT, PROMPT_VERSION as DEFAULT_VERSION
from aig.arena.ai.friendly_fire_prompt import BEHAVIOR_PROMPTS
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController

PROMPT_VERSION = 'arena-turn-prompt-v4'
AP_GUIDANCE = """The observation's action_points_remaining is the complete AP budget for this plan.
The total cost of your returned actions MUST NOT exceed it. Keep a running remaining
budget: confirm an action is affordable and subtract its cost before adding another."""
SEQUENCE_GUIDANCE = """Start from the current authoritative observation, including on a partial turn.
Treat the plan as a sequence of state transitions, not independent starting options.
For each action in order: check actor, ability and target legality in the current
imagined state; check and subtract AP; apply the supplied mechanical consequences
to HP, status, occupancy and positions; only then choose the next action.
The first action must appear in its actor's current legal-action list. Later
actions use the updated state, where options may disappear or become available.
If damage DOWNs a unit, it is no longer an ACTIVE target: later Attack, Snipe or
Shield Bash cannot target that enemy unit. DOWNED units cannot act. Finish may
target a DOWNED enemy when legal; it is optional. Once removed by Finish, a unit
cannot be a later actor or target, and its tile is no longer occupied by it.
Revive changes a DOWNED ally to ACTIVE; the revived unit may act later this turn.
Movement and a surviving Shield Bash target's push change positions. Reassess
range, adjacency, target availability and required LOS from the updated board
at each action, not from the original positions. Range uses Chebyshev distance.
Ranged LOS checks the center-to-center supercover excluding endpoints; blocked
terrain blocks it, including both side tiles at an exact corner crossing.
Units and Cores do not block LOS.
If an action ends the game, stop the sequence there; append no later actions.
Use AP productively when a coherent legal continuation exists. You need not spend
every AP: stop with a shorter legal plan when later legality is uncertain.
Derive consequences from the supplied mechanics, not memorized action combinations.
"""
PROMPT = SYSTEM_PROMPT.replace(
    'You have up to 5 shared Action Points, bounded by action_points_remaining.', AP_GUIDANCE
).replace('Return only the ArenaTurnPlan', SEQUENCE_GUIDANCE + 'Return only the ArenaTurnPlan')
PROMPTS = MappingProxyType({**BEHAVIOR_PROMPTS, PROMPT_VERSION: PROMPT})
PROMPT_HASHES = MappingProxyType({v: sha256(p.encode()).hexdigest() for v, p in PROMPTS.items()})


def resolve_prompt(version=None):
    version = DEFAULT_VERSION if version in (None, 'latest') else version
    if version not in PROMPTS:
        raise ValueError('unknown experimental Arena prompt')
    return version, PROMPTS[version]


class OpenAISequentialProvider(OpenAIArenaTurnProvider):
    resolve_prompt = staticmethod(resolve_prompt)


class OllamaSequentialProvider(OllamaArenaTurnProvider):
    resolve_prompt = staticmethod(resolve_prompt)


class ExperimentalBoundedReplanController(ArenaBoundedReplanController):
    """Explicit prompt binding only; inherit the frozen run_turn method verbatim."""
    def __init__(self, provider, *, fallback=False):
        resolve_prompt(provider.prompt_version)
        self.provider = provider
        self.fallback = fallback
