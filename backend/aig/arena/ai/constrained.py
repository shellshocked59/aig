"""Opt-in exact current-action wire constraints; frozen stepwise semantics reused."""

from copy import deepcopy

from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION, action_from_dict
from aig.arena.ai.observation import ArenaObservation, OBSERVATION_V2
from aig.arena.ai.repair import REPAIR_V1
from aig.arena.ai.stepwise import (ArenaStepController, HeuristicArenaStepProvider,
    OllamaArenaStepProvider, OpenAIArenaStepProvider)
from aig.arena.snapshots import canonical_json, digest

CONTROL_VERSION = "arena-control-stepwise-constrained-structured-v1"
WIRE_SCHEMA_VERSION = "arena-step-legal-action-wire-schema-v1"
CONTROL_MODE = "stepwise-constrained-structured"


def resolve_control_version(version=CONTROL_VERSION):
    if version != CONTROL_VERSION:
        raise ValueError("unknown constrained control version")
    return version


def resolve_wire_schema_version(version=WIRE_SCHEMA_VERSION):
    if version != WIRE_SCHEMA_VERSION:
        raise ValueError("unknown legal-action wire schema version")
    return version


def _exact(value):
    if type(value) is dict:
        return dict(type="object", additionalProperties=False, required=list(value),
                    properties={k: _exact(v) for k, v in value.items()})
    if type(value) not in (str, int):
        raise ValueError("unsupported action field")
    return dict(type="string" if type(value) is str else "integer", enum=[value])


def build_arena_step_legal_wire_schema(observation, provider_kind="ollama"):
    """Exact disjoint action branches, in unchanged catalog order.

    Both adapters use the existing OpenAI-compatible typed singleton-enum subset.
    EndTurn is the unique empty array (zero items, conceptually before branches).
    No titles/descriptions, field cross products, null padding, or tactical ranking.
    """
    if provider_kind not in ("ollama", "openai"):
        raise ValueError("unsupported constrained schema provider")
    if observation.version != OBSERVATION_V2:
        raise ValueError("constrained structured requires Observation V2")
    actions = observation.to_dict()["legal_actions"]
    keys = [canonical_json(a) for a in actions]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate current legal action")
    for action in actions:
        action_from_dict(action)  # Reject malformed catalogs, without normalizing them.
    items = {"anyOf": [_exact(a) for a in actions]} if actions else {"type": "string"}
    return dict(type="object", additionalProperties=False,
        required=["schema_version", "actions"], properties=dict(
            schema_version=_exact(PLAN_SCHEMA_VERSION),
            actions=dict(type="array", maxItems=1 if actions else 0, items=items)))


def wire_metadata(observation, provider_kind="ollama"):
    schema = build_arena_step_legal_wire_schema(observation, provider_kind)
    return dict(control_mode=CONTROL_MODE, control_version=CONTROL_VERSION,
                logical_schema_version=PLAN_SCHEMA_VERSION, wire_schema_version=WIRE_SCHEMA_VERSION,
                wire_schema_hash=digest(schema), provider_wire_schema_hash=digest(schema),
                wire_schema_bytes=len(canonical_json(schema).encode("utf-8")),
                legal_action_count=len(observation.to_dict()["legal_actions"]))


class _ConstrainedContract:
    control_version = CONTROL_VERSION
    wire_schema_version = WIRE_SCHEMA_VERSION

    def __init__(self, *args, repair_version=REPAIR_V1, **kwargs):
        if repair_version != REPAIR_V1:
            raise ValueError("constrained v1 requires Repair V1")
        self._current_wire_schema = None
        super().__init__(*args, repair_version=repair_version, **kwargs)

    def output_schema(self):
        if self._current_wire_schema is None:
            raise ValueError("wire schema requires a current create_step boundary")
        return deepcopy(self._current_wire_schema)

    def create_step(self, observation):
        schema = build_arena_step_legal_wire_schema(observation, self.name)
        self._current_wire_schema = schema
        try:
            return super().create_step(observation)
        finally:
            if self._last_trace is not None:
                self._last_trace.update(wire_metadata(observation, self.name))
            # No stale schema can be used outside this decision/its bounded repair.
            self._current_wire_schema = None


class OllamaArenaConstrainedStepProvider(_ConstrainedContract, OllamaArenaStepProvider):
    pass


class OpenAIArenaConstrainedStepProvider(_ConstrainedContract, OpenAIArenaStepProvider):
    pass


class HeuristicArenaConstrainedStepProvider(HeuristicArenaStepProvider):
    control_version = CONTROL_VERSION
    wire_schema_version = WIRE_SCHEMA_VERSION
    repair_version = REPAIR_V1

    def create_step(self, observation):
        build_arena_step_legal_wire_schema(observation)
        return super().create_step(observation)


def create_constrained_step_provider(settings, name, **kwargs):
    if name == "heuristic":
        if kwargs:
            raise ValueError("heuristic constrained provider takes no overrides")
        return HeuristicArenaConstrainedStepProvider()
    kinds = {"ollama": OllamaArenaConstrainedStepProvider, "openai": OpenAIArenaConstrainedStepProvider}
    if name not in kinds:
        raise ValueError("unknown constrained provider")
    return kinds[name](getattr(settings, name), secrets=(settings.openai.api_key,), **kwargs)


class ArenaConstrainedStepController(ArenaStepController):
    """Same command loop and failure policy, with separately versioned provenance."""
    def __init__(self, provider, name=None):
        if (getattr(provider, "control_version", None) != CONTROL_VERSION
                or getattr(provider, "wire_schema_version", None) != WIRE_SCHEMA_VERSION
                or getattr(provider, "repair_version", None) != REPAIR_V1):
            raise ValueError("constrained controller requires an explicit constrained provider")
        super().__init__(provider, name)

    def run_turn(self, simulation, *, trial=None):
        turn = super().run_turn(simulation, trial=trial)
        turn.update(control_mode=CONTROL_MODE, control_version=CONTROL_VERSION,
                    wire_schema_version=WIRE_SCHEMA_VERSION, repair_version=REPAIR_V1)
        for row in turn["steps"]:
            observation = ArenaObservation(canonical_json(row["observation"]))
            row.update(wire_metadata(observation, self.name if self.name != "heuristic" else "ollama"))
            row["repair_version"] = REPAIR_V1
            ci = row["command_index"]
            row["command_result"] = deepcopy(simulation.trace()["entries"][ci]) if ci is not None else None
        return turn
