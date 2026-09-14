"""Experimental single-action control; full-turn contracts/defaults stay separate."""

from copy import deepcopy
from typing import Protocol
from types import MappingProxyType

from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION, action_command
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import ArenaObservation, OBSERVATION_V2, build_observation
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.repair import REPAIR_V1, repair_version as resolve_repair_version, feedback, rejected_evidence
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.benchmark_provider import checked_plan
from aig.arena.commands import ArenaEndTurn
from aig.arena.snapshots import canonical_json, state_hash

CONTROL_VERSION = "arena-control-stepwise-v1"
FULL_TURN_CONTROL_VERSION = "arena-control-full-turn-v1"
STEP_PROMPT_VERSION = "arena-step-prompt-v1"
STEP_PROMPT = """You control one team in a deterministic fantasy tactics battle.
Choose the single best legal action to take NOW from the supplied ArenaObservation.
Current AP is action_points_remaining. Copy one complete action from legal_actions;
do not reconstruct a different actor/target combination. The catalog describes the
current observation, including when legal_actions_state is labeled turn_start.
The engine will execute exactly that action and, if AP remains and battle is not
terminal, give you a fresh updated observation before you choose again.
Return ArenaTurnPlan with exactly one action, or actions=[] to intentionally end
the turn now. Keep schema_version=arena-turn-plan-schema-v1.
Move, Attack, Heal, Finish, Shield Bash cost 1 AP; Revive, Snipe, Fireball cost 2 AP.
Do not plan later actions. Do not explain your reasoning or add commentary."""
STEP_PROMPTS = MappingProxyType({STEP_PROMPT_VERSION: STEP_PROMPT})


def resolve_step_prompt(version):
    if version not in STEP_PROMPTS:
        raise ValueError("stepwise requires arena-step-prompt-v1")
    return version, STEP_PROMPTS[version]


def parse_step(raw, observation):
    if observation.version != OBSERVATION_V2:
        raise ArenaProviderError("schema_validation")
    plan = parse_turn_plan(raw, observation)
    if len(plan.actions) > 1:
        raise ArenaProviderError("schema_validation", field_path="actions", message="Stepwise mode requires zero or one action.", rejected_value=len(plan.actions))
    catalog = {canonical_json(a) for a in observation.to_dict()["legal_actions"]}
    if plan.actions and canonical_json(plan.actions[0].to_dict()) not in catalog:
        raise ArenaProviderError("invalid_reference", action_index=0, field_path="actions[0]",
                                 message="Returned action does not exactly match any current legal action.",
                                 rejected_value=plan.actions[0].to_dict())
    return plan


class ArenaStepProvider(Protocol):
    def create_step(self, observation: ArenaObservation) -> ArenaTurnPlan: ...


class _StepContract:
    """Reuse transport, bounded repair and telemetry; only the task contract varies."""
    resolve_prompt = staticmethod(resolve_step_prompt)
    parse_plan = staticmethod(parse_step)

    def __init__(self, settings, *, repair_version=REPAIR_V1, **kwargs):
        self.repair_version = resolve_repair_version(repair_version)
        kwargs.setdefault("prompt_version", STEP_PROMPT_VERSION)
        super().__init__(settings, **kwargs)

    def repair_feedback(self, category):
        return feedback(REPAIR_V1, category)

    def rejection_evidence(self, raw, observation, error):
        return rejected_evidence(raw, observation, error.diagnostic, self.repair_version, self._secrets)

    def repair_messages(self, observation, error, evidence):
        return [{"role": "user", "content": "ArenaObservation:\n" + observation.canonical},
                {"role": "user", "content": feedback(self.repair_version, error.category, evidence)}]

    def create_step(self, observation):
        if observation.version != OBSERVATION_V2:
            raise ArenaProviderError("schema_validation")
        return super().create_turn_plan(observation)

    def create_turn_plan(self, observation):
        raise TypeError("step providers require create_step")


class OllamaArenaStepProvider(_StepContract, OllamaArenaTurnProvider):
    pass


class OpenAIArenaStepProvider(_StepContract, OpenAIArenaTurnProvider):
    pass


class HeuristicArenaStepProvider:
    name = "heuristic"
    prompt_version = STEP_PROMPT_VERSION
    schema_version = PLAN_SCHEMA_VERSION

    def create_step(self, observation):
        plan = HeuristicArenaTurnProvider().create_turn_plan(observation)
        return parse_step(canonical_json(ArenaTurnPlan(plan.actions[:1]).to_dict()), observation)


def create_arena_step_provider(settings, name, **kwargs):
    if name == "heuristic":
        return HeuristicArenaStepProvider()
    kinds = {"ollama": OllamaArenaStepProvider, "openai": OpenAIArenaStepProvider}
    if name not in kinds:
        raise ValueError("unknown Arena step provider")
    return kinds[name](getattr(settings, name), secrets=(settings.openai.api_key,), **kwargs)


class _CheckedStepBridge:
    """Private adapter to the existing strict provenance/telemetry boundary."""
    def __init__(self, provider):
        self.provider = provider

    def __getattr__(self, name):
        return getattr(self.provider, name)

    @property
    def repair(self):
        return getattr(self.provider, "repair", None)

    @repair.setter
    def repair(self, value):
        self.provider.repair = value

    def create_turn_plan(self, observation):
        plan = self.provider.create_step(observation)
        if type(plan) is not ArenaTurnPlan:
            raise ArenaProviderError("schema_validation")
        return parse_step(canonical_json(plan.to_dict()), observation)


def checked_step(provider, name, observation, *, preflight=False):
    plan, call = checked_plan(_CheckedStepBridge(provider), name, observation, preflight=preflight)
    # V1's historical allowlist predates this adapter category. Preserve it in V2.
    raw = getattr(provider, "last_trace", None)
    if isinstance(raw, dict) and raw.get("error_category") == "transport_failure":
        call["error_category"] = "transport_failure"
        for saved, original in zip(call["attempts"], raw.get("attempts", [])):
            if original.get("error_category") == "transport_failure":
                saved["error_category"] = "transport_failure"
    if isinstance(raw, dict) and raw.get("error_category") in ("request_ceiling", "source_mutation"):
        call["error_category"] = raw["error_category"]
    if isinstance(raw, dict) and raw.get("repair_version") in ("arena-step-repair-v1", "arena-step-repair-v2"):
        call["repair_version"] = raw["repair_version"]
        for saved, original in zip(call["attempts"], raw.get("attempts", [])):
            if "rejected_decision" in original:
                saved["rejected_decision"] = deepcopy(original["rejected_decision"])
    return plan, call


class ArenaStepController:
    """Strict single-player-turn loop. Failure ends the turn without fallback."""
    def __init__(self, provider, name=None):
        self.provider = provider
        self.name = name or provider.name

    def run_turn(self, simulation, *, trial=None):
        state = simulation.state
        state.validate()
        if state.active_player_id is None:
            raise ValueError("cannot start stepwise control after victory")
        player, turn, available = state.active_player_id, state.turn, state.action_points_remaining
        steps, actions = [], []
        failure = None
        explicit = False
        start = len(simulation.trace()["entries"])
        while state.active_player_id == player and state.winner_player_id is None and state.action_points_remaining:
            if len(steps) >= 5:
                failure = "controller_safety_bound"
                break
            observation = build_observation(state, version=OBSERVATION_V2)
            plan, call = checked_step(self.provider, self.name, observation)
            row = dict(version="arena-step-trace-v1", trial=trial, turn=turn, player_id=player,
                       step_index=len(steps), ap_before=state.action_points_remaining,
                       observation=observation.to_dict(), observation_hash=observation.hash,
                       observation_version=OBSERVATION_V2,
                       legal_action_count=len(observation.to_dict()["legal_actions"]),
                       model=getattr(getattr(self.provider, "settings", None), "model", None),
                       prompt_version=STEP_PROMPT_VERSION, schema_version=PLAN_SCHEMA_VERSION,
                       decision=plan.to_dict() if plan else None,
                       selected_action=plan.actions[0].to_dict() if plan and plan.actions else None,
                       selected_current_legal=True if plan and plan.actions else None,
                       explicit_end_turn=bool(plan is not None and not plan.actions),
                       command_index=None, **call)
            row["first_response_valid"] = not bool(call["attempts"][0]["error_category"]) if call["attempts"] else None
            row["repair_succeeded"] = bool(call["repair_requests"] and call["success"])
            steps.append(row)
            if plan is None:
                failure = call["error_category"]
            elif not plan.actions:
                explicit = True
            else:
                try:
                    index = len(simulation.trace()["entries"])
                    simulation.execute(action_command(plan.actions[0], player))
                    row["command_index"] = index
                    actions.append(plan.actions[0].to_dict())
                except ValueError:
                    failure = "catalog_execution_defect"
            row.update(ap_after=state.action_points_remaining, resulting_state_hash=state_hash(state),
                       terminal=state.winner_player_id, execution_error=failure if failure == "catalog_execution_defect" else None)
            if failure or explicit:
                break
        unused = state.action_points_remaining
        # Serious domain defects preserve the exact failing prefix for diagnosis.
        if state.winner_player_id is None and failure not in ("catalog_execution_defect", "request_ceiling", "source_mutation"):
            simulation.execute(ArenaEndTurn(player))
        return deepcopy(dict(version="arena-step-turn-trace-v1", trial=trial, turn=turn, player_id=player,
            control_mode="stepwise", control_version=CONTROL_VERSION, steps=steps,
            steps_requested=len(steps), actions_executed=len(actions), action_sequence=actions,
            ap_available=available, ap_executed=available-unused, ap_unused=unused,
            explicit_early_end=explicit, provider_failures=sum(not r["success"] for r in steps),
            repair_requests=sum(r["repair_requests"] for r in steps),
            provider_requests=sum(r["provider_requests"] for r in steps),
            provider_latency_seconds=sum(sum(a["wall_clock_seconds"] or 0 for a in r["attempts"]) for r in steps),
            terminal=state.winner_player_id, error_category=failure,
            command_start=start, command_end=len(simulation.trace()["entries"])))
