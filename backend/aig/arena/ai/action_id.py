"""Experimental current-catalog selection; frozen structured stepwise stays separate."""
from dataclasses import dataclass
from typing import Protocol
import re

from aig.ai.plan_schema import strict_json
from aig.arena.ai.contracts import ArenaTurnPlan, action_from_dict, action_command
from aig.arena.ai.observation import (ArenaObservation, OBSERVATION_V2, OBSERVATION_V3,
                                      build_observation, simulation_state)
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.stepwise import HeuristicArenaStepProvider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.ai.repair import MAX_REJECTED_BYTES, REDACTED
from aig.arena.benchmark_provider import checked_plan
from aig.arena.snapshots import canonical_json, digest, state_hash
from aig.arena.commands import ArenaEndTurn

CONTROL_VERSION = "arena-control-stepwise-action-id-v1"
STEP_PROMPT_VERSION = "arena-step-prompt-v2"
SCHEMA_VERSION = "arena-step-action-id-schema-v1"
REPAIR_VERSION = "arena-action-id-repair-v1"
STEP_PROMPT = """You control one team in a deterministic tactical battle.
Choose the single action to take NOW. Every currently legal action is listed in
legal_actions with a deterministic action ID and its complete action semantics.
Return the action_id of exactly one listed action. Do not create or modify IDs.
Do not reconstruct unit IDs, target IDs, coordinates, or action fields.
To intentionally end the turn, return {"action_id":null}.
After your action executes, if AP remains and battle is not terminal, you receive
a fresh observation and a new catalog. IDs apply only to the CURRENT observation.
Return only the required schema. Do not explain your reasoning."""


def resolve_prompt(version):
    if version != STEP_PROMPT_VERSION:
        raise ValueError("action-ID control requires arena-step-prompt-v2")
    return version, STEP_PROMPT


def decision_schema():
    # Common strict wire subset for both adapters; membership is application-side.
    return dict(type="object", additionalProperties=False, required=["action_id"],
                properties=dict(action_id=dict(type=["string", "null"])))


@dataclass(frozen=True)
class ArenaActionIdDecision:
    action_id: str | None

    def __post_init__(self):
        if self.action_id is not None and type(self.action_id) is not str:
            raise ValueError("action_id must be a string or null")

    def to_dict(self):
        return dict(action_id=self.action_id)


def catalog_hash(observation):
    require_v3(observation)
    return digest([[e["id"], e["action"]] for e in observation.to_dict()["legal_actions"]])


def require_v3(observation):
    if observation.version != OBSERVATION_V3:
        raise ArenaProviderError("schema_validation")


def resolve_action(decision, observation):
    require_v3(observation)
    if decision.action_id is None:
        return None
    for entry in observation.to_dict()["legal_actions"]:
        if entry["id"] == decision.action_id:
            return action_from_dict(entry["action"])
    raise ArenaProviderError("invalid_action_id", field_path="action_id",
        message="Returned action_id is not in the CURRENT legal_actions catalog.", rejected_value=decision.action_id)


def parse_choice(raw, observation):
    require_v3(observation)
    try:
        data = strict_json(raw)
    except (ValueError, TypeError, RecursionError):
        raise ArenaProviderError("malformed_json") from None
    if (type(data) is not dict or set(data) != {"action_id"}
            or (data["action_id"] is not None and type(data["action_id"]) is not str)):
        raise ArenaProviderError("schema_validation")
    choice = ArenaActionIdDecision(data["action_id"])
    resolve_action(choice, observation)
    return choice


class ArenaActionIdStepProvider(Protocol):
    def create_step_choice(self, observation: ArenaObservation) -> ArenaActionIdDecision: ...


class _ActionIdContract:
    schema_version = SCHEMA_VERSION
    repair_version = REPAIR_VERSION
    output_schema_name = "arena_step_action_id"
    output_schema = staticmethod(decision_schema)
    resolve_prompt = staticmethod(resolve_prompt)
    parse_plan = staticmethod(parse_choice)

    def __init__(self, settings, **kwargs):
        kwargs.setdefault("prompt_version", STEP_PROMPT_VERSION)
        super().__init__(settings, **kwargs)

    def create_step_choice(self, observation):
        require_v3(observation)
        return super().create_turn_plan(observation)

    def create_turn_plan(self, observation):
        raise TypeError("action-ID providers require create_step_choice")

    def rejection_evidence(self, raw, observation, error):
        # Only short ID-shaped text can survive. No arbitrary provider text/fields.
        value = error.diagnostic.rejected_value
        safe = (value if isinstance(value, str) and re.fullmatch(r"A[0-9]{2,8}", value)
                and not any(s in value for s in self._secrets) else REDACTED)
        result = dict(raw_content=None, rejected_action_id=safe if value is not None else None,
                      validation_category=error.category, current_id_member=False if error.category == "invalid_action_id" else None,
                      repair_version=REPAIR_VERSION,
                      repair_result="pending")
        assert len(canonical_json(result).encode()) <= MAX_REJECTED_BYTES
        return result

    def repair_feedback(self, category):
        return (f"Previous output failed static validation ({category}). Return exactly one action_id "
                "copied from the CURRENT legal_actions catalog, or {\"action_id\":null} to end the turn. "
                "Do not create or modify an action ID. Return only the required schema.")

    def repair_messages(self, observation, error, evidence):
        return [{"role": "user", "content": "ArenaObservation:\n" + observation.canonical},
                {"role": "user", "content": self.repair_feedback(error.category) +
                 "\nSanitized rejected decision: " + canonical_json(evidence)}]


class OllamaArenaActionIdProvider(_ActionIdContract, OllamaArenaTurnProvider):
    pass


class OpenAIArenaActionIdProvider(_ActionIdContract, OpenAIArenaTurnProvider):
    pass


class HeuristicArenaActionIdProvider:
    name = "heuristic"
    prompt_version = STEP_PROMPT_VERSION
    schema_version = SCHEMA_VERSION
    repair_version = REPAIR_VERSION

    def create_step_choice(self, observation):
        require_v3(observation)
        v2 = build_observation(simulation_state(observation), version=OBSERVATION_V2)
        plan = HeuristicArenaStepProvider().create_step(v2)
        if not plan.actions:
            return ArenaActionIdDecision(None)
        return choice_for_action(plan.actions[0], observation)


def choice_for_action(action, observation):
    require_v3(observation)
    for entry in observation.to_dict()["legal_actions"]:
        if entry["action"] == action.to_dict():
            return ArenaActionIdDecision(entry["id"])
    raise ValueError("selected complete action absent from current catalog")


def create_action_id_provider(settings, name, **kwargs):
    if name == "heuristic":
        return HeuristicArenaActionIdProvider()
    kinds = dict(ollama=OllamaArenaActionIdProvider, openai=OpenAIArenaActionIdProvider)
    if name not in kinds:
        raise ValueError("unknown Arena action-ID provider")
    return kinds[name](getattr(settings, name), secrets=(settings.openai.api_key,), **kwargs)


class _ChoiceBridge:
    """Resolve at the existing provenance/telemetry and planned-command boundary."""
    def __init__(self, provider):
        self.provider, self.choice, self.error = provider, None, None

    def __getattr__(self, name):
        return getattr(self.provider, name)

    def create_turn_plan(self, observation):
        try:
            candidate = self.provider.create_step_choice(observation)
            if type(candidate) is not ArenaActionIdDecision:
                raise ArenaProviderError("schema_validation")
            self.choice = parse_choice(canonical_json(candidate.to_dict()), observation)
            action = resolve_action(self.choice, observation)
            return ArenaTurnPlan((action,) if action else ())
        except ArenaProviderError as error:
            self.error = error.category
            raise


def checked_choice(provider, name, observation):
    bridge = _ChoiceBridge(provider)
    plan, call = checked_plan(bridge, name, observation)
    raw = getattr(provider, "last_trace", None)
    extra = {"invalid_action_id", "transport_failure", "request_ceiling", "source_mutation"}
    if bridge.error in extra:
        call["error_category"] = bridge.error
    if isinstance(raw, dict):
        for saved, original in zip(call["attempts"], raw.get("attempts", [])):
            if original.get("error_category") in extra:
                saved["error_category"] = original["error_category"]
            if "rejected_decision" in original:
                saved["rejected_decision"] = original["rejected_decision"]
    call["repair_version"] = REPAIR_VERSION
    call["resulting_decision"] = bridge.choice.to_dict() if plan is not None else None
    return (bridge.choice if plan is not None else None), call


class ArenaActionIdController:
    def __init__(self, provider, name=None):
        self.provider, self.name = provider, name or provider.name

    def run_turn(self, simulation, *, trial=None):
        state = simulation.state
        state.validate()
        if state.active_player_id is None:
            raise ValueError("cannot start action-ID control after victory")
        player, turn, available = state.active_player_id, state.turn, state.action_points_remaining
        steps, actions = [], []
        failure, explicit = None, False
        start = len(simulation.trace()["entries"])
        while state.active_player_id == player and state.winner_player_id is None and state.action_points_remaining:
            if len(steps) >= 5:
                failure = "controller_safety_bound"
                break
            observation = build_observation(state, version=OBSERVATION_V3)
            choice, call = checked_choice(self.provider, self.name, observation)
            action = resolve_action(choice, observation) if choice is not None else None
            row = dict(version="arena-action-id-step-trace-v1", trial=trial, turn=turn, player_id=player,
                step_index=len(steps), ap_before=state.action_points_remaining,
                observation=observation.to_dict(), observation_hash=observation.hash,
                observation_version=OBSERVATION_V3, action_catalog_hash=catalog_hash(observation),
                legal_action_count=len(observation.to_dict()["legal_actions"]),
                prompt_version=STEP_PROMPT_VERSION, schema_version=SCHEMA_VERSION,
                decision=choice.to_dict() if choice is not None else None,
                selected_action_id=choice.action_id if choice is not None else None,
                selected_action=action.to_dict() if action else None,
                resolved_action=action.to_dict() if action else None,
                selected_current_legal=True if action else None,
                explicit_end_turn=choice is not None and choice.action_id is None,
                command_index=None, command_result=None, **call)
            row["first_response_valid"] = not bool(call["attempts"][0]["error_category"]) if call["attempts"] else None
            row["repair_succeeded"] = bool(call["repair_requests"] and call["success"])
            steps.append(row)
            if choice is None:
                failure = call["error_category"]
            elif action is None:
                explicit = True
            else:
                try:
                    index = len(simulation.trace()["entries"])
                    simulation.execute(action_command(action, player))
                    row["command_index"] = index
                    row["command_result"] = simulation.trace()["entries"][index]
                    actions.append(action.to_dict())
                except ValueError:
                    failure = "catalog_execution_defect"
            row.update(ap_after=state.action_points_remaining, resulting_state_hash=state_hash(state),
                terminal=state.winner_player_id, execution_error=failure if failure == "catalog_execution_defect" else None)
            if failure or explicit:
                break
        unused = state.action_points_remaining
        # A failed selection preserves its exact stopping state. Never EndTurn-on-failure.
        if state.winner_player_id is None and failure is None:
            simulation.execute(ArenaEndTurn(player))
        return dict(version="arena-action-id-turn-trace-v1", trial=trial, turn=turn, player_id=player,
            control_mode="stepwise-action-id", control_version=CONTROL_VERSION, steps=steps,
            steps_requested=len(steps), actions_executed=len(actions), action_sequence=actions,
            ap_available=available, ap_executed=available-unused, ap_unused=unused,
            explicit_early_end=explicit, provider_failures=sum(not r["success"] for r in steps),
            repair_requests=sum(r["repair_requests"] for r in steps),
            provider_requests=sum(r["provider_requests"] for r in steps),
            provider_latency_seconds=sum(sum(a["wall_clock_seconds"] or 0 for a in r["attempts"]) for r in steps),
            terminal=state.winner_player_id, error_category=failure,
            command_start=start, command_end=len(simulation.trace()["entries"]))
