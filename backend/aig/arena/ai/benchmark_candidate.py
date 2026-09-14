"""Opt-in benchmark contracts. Historical registries and browser defaults are untouched."""
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType

from aig.ai.plan_schema import strict_json
from aig.arena.ai.contracts import ArenaTurnPlan, action_from_dict, turn_plan_schema
from aig.arena.ai.observation import build_observation, ArenaObservation, OBSERVATION_V2
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.commands import ACTION_COSTS
from aig.arena.snapshots import canonical_json, fields

POLICY_VERSION = 'arena-policy-core-v1'
TURN_PROMPT_VERSION = 'arena-turn-prompt-v6'
STEP_PROMPT_VERSION = 'arena-step-prompt-v3'
SCHEMA_VERSION = 'arena-turn-plan-schema-v2'
OBSERVATION_VERSION = 'arena-observation-v4'
POLICY_CORE = """You control one team in a perfect-information fantasy tactics battle.
Use the authoritative observation, rule facts, and legal actions. Win by destroying
the enemy Core or leaving the enemy with no ACTIVE units. Use supplied IDs,
positions, and ability names. Legal actions describe the current observation;
actions execute in order and earlier actions can change later legality.
action_points_remaining is the complete AP budget for this decision/plan.
Keep a running total of action costs. Before adding each action, ensure its cost
fits within the AP still remaining. Total planned cost MUST NOT exceed this budget.
Use the supplied costs, ranges, damage, status, movement, and bonus rules.
Movement is eight-directional and cannot pass occupied/blocked tiles or cut blocked
corners. Ruins block ranged line of sight. DOWNED units occupy tiles and cannot act.
Attack targets an ACTIVE enemy or enemy Core; special abilities cannot damage Cores.
Heal targets ACTIVE allies, including self; Finish removes an adjacent DOWNED enemy;
Revive restores a DOWNED ally, which can act immediately. Shield Bash can push its
target if the destination is free. Fireball affects ACTIVE units in its area,
including allies and caster; if both teams lose all ACTIVE units, the caster loses.
Choose useful legal actions for the current tactical situation; several actions
may be worthwhile. You may explicitly end_turn with AP remaining when you judge
no further action worthwhile. Do not add meaningless or speculative actions merely
to consume AP. end_turn costs 0 AP and must be last; victory stops execution before
any later action. An empty or short plan without end_turn is plan completion,
not an explicit intentional stop. Output only the required structured plan.
No reasoning, explanation, or commentary."""
TURN_WRAPPER = """Return ArenaTurnPlan with zero to five gameplay actions for the remaining turn,
optionally followed by end_turn. Follow schema_version=arena-turn-plan-schema-v2.
Execution commits valid actions until completion, end_turn, victory, or invalidity."""
STEP_WRAPPER = """Return ArenaTurnPlan with the single next action or end_turn (at most one action).
Follow schema_version=arena-turn-plan-schema-v2. After a successful gameplay action,
if AP remains, you receive a fresh authoritative observation for the next decision."""
PROMPTS = MappingProxyType({TURN_PROMPT_VERSION: POLICY_CORE+'\n'+TURN_WRAPPER,
                           STEP_PROMPT_VERSION: POLICY_CORE+'\n'+STEP_WRAPPER})
PROMPT_HASHES = MappingProxyType({k: sha256(v.encode()).hexdigest() for k,v in PROMPTS.items()})


@dataclass(frozen=True)
class EndTurnAction:
    type = 'end_turn'

    def to_dict(self):
        return dict(type=self.type)


@dataclass(frozen=True)
class CandidatePlan:
    actions: tuple = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        if self.schema_version != SCHEMA_VERSION or type(self.actions) is not tuple:
            raise ValueError('invalid candidate plan')
        stops = [i for i,a in enumerate(self.actions) if type(a) is EndTurnAction]
        if stops and stops != [len(self.actions)-1]:
            raise ValueError('end_turn must occur once, last')
        ArenaTurnPlan(self.gameplay_actions)

    @property
    def gameplay_actions(self):
        return tuple(a for a in self.actions if type(a) is not EndTurnAction)

    @property
    def ap_cost(self):
        return sum(ACTION_COSTS[a.type] for a in self.actions)

    def to_dict(self):
        return dict(schema_version=self.schema_version, actions=[a.to_dict() for a in self.actions])


@dataclass(frozen=True)
class CandidateObservation:
    canonical: str
    version = OBSERVATION_VERSION

    def to_dict(self):
        return strict_json(self.canonical)

    @property
    def hash(self):
        return sha256(self.canonical.encode()).hexdigest()


def candidate_observation(state):
    data = build_observation(state, version=OBSERVATION_V2).to_dict()
    data.update(schema_version=OBSERVATION_VERSION, legal_actions_state='current_observation')
    data['legal_actions'].append(EndTurnAction().to_dict())
    data['action_costs'] = dict(ACTION_COSTS)
    return CandidateObservation(canonical_json(data))


def base_observation(observation):
    if observation.version != OBSERVATION_VERSION:
        raise ArenaProviderError('schema_validation')
    data = observation.to_dict()
    data.update(schema_version=OBSERVATION_V2, legal_actions_state='turn_start')
    data.pop('action_costs')
    data['legal_actions'] = [a for a in data['legal_actions'] if a['type'] != 'end_turn']
    return ArenaObservation(canonical_json(data))


def parse_candidate(raw, observation, *, step=False):
    try:
        data = strict_json(raw)
    except (ValueError, TypeError, RecursionError):
        raise ArenaProviderError('malformed_json') from None
    try:
        fields(data, 'schema_version actions')
        if type(data['actions']) is not list:
            raise ValueError('actions must be an array')
        actions = []
        for a in data['actions']:
            if type(a) is dict and a.get('type') == 'end_turn':
                fields(a, 'type')
                actions.append(EndTurnAction())
            else:
                actions.append(action_from_dict(a))
        plan = CandidatePlan(tuple(actions), data['schema_version'])
        if step and len(plan.actions) > 1:
            raise ValueError('step requires at most one action')
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ArenaProviderError('schema_validation') from None
    parse_turn_plan(canonical_json(ArenaTurnPlan(plan.gameplay_actions).to_dict()), base_observation(observation))
    # Same first-action legality check in every arm; later state remains execution's job.
    if plan.actions and plan.actions[0].to_dict() not in observation.to_dict()['legal_actions']:
        raise ArenaProviderError('invalid_reference', action_index=0)
    return plan


def candidate_schema(*, step=False, openai=False):
    schema = turn_plan_schema()
    schema['$id'] = SCHEMA_VERSION
    schema['properties']['schema_version']['const'] = SCHEMA_VERSION
    actions = schema['properties']['actions']
    actions['maxItems'] = 1 if step else 6
    actions['items']['oneOf'].append(dict(type='object', additionalProperties=False,
        required=['type'], properties={'type': {'const': 'end_turn'}}))
    def transform(v):
        if isinstance(v, list):
            return [transform(x) for x in v]
        if not isinstance(v, dict):
            return v
        result = {('anyOf' if k == 'oneOf' else k): transform(x) for k,x in v.items()
                  if k not in ('$schema', '$id', 'minLength', 'pattern', 'const')}
        if 'const' in v:
            result.update(type='string', enum=[v['const']])
        return result
    return transform(schema) if openai else schema


class _CandidateProvider:
    schema_version = SCHEMA_VERSION

    def __init__(self, settings, *, step=False, **kwargs):
        self.step = step
        kwargs.setdefault('prompt_version', STEP_PROMPT_VERSION if step else TURN_PROMPT_VERSION)
        super().__init__(settings, **kwargs)
        if self.prompt_version != (STEP_PROMPT_VERSION if step else TURN_PROMPT_VERSION):
            raise ValueError('prompt/control mismatch')

    @staticmethod
    def resolve_prompt(version):
        if version not in PROMPTS:
            raise ValueError('explicit candidate prompt required')
        return version, PROMPTS[version]

    def parse_plan(self, raw, observation):
        return parse_candidate(raw, observation, step=self.step)

    def output_schema(self):
        return candidate_schema(step=self.step, openai=self.name == 'openai')


class OpenAICandidateProvider(_CandidateProvider, OpenAIArenaTurnProvider):
    pass


class OllamaCandidateProvider(_CandidateProvider, OllamaArenaTurnProvider):
    pass
