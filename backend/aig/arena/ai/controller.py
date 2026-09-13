"""One observation and one provider call per turn; configuration stays outside state."""

from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import ArenaObservation, build_observation
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.replay import metrics
from aig.arena.snapshots import digest
from aig.arena.state import integer

AI_TRACE_VERSION = "arena-ai-trace-v1"


class ArenaTurnProvider(Protocol):
    def create_turn_plan(self, observation: ArenaObservation) -> ArenaTurnPlan: ...


class ArenaControllerType(StrEnum):
    HUMAN = "human"
    HEURISTIC_AI = "heuristic_ai"
    OLLAMA_AI = "ollama_ai"
    OPENAI_AI = "openai_ai"


@dataclass(frozen=True)
class ArenaAiTurnTrace:
    data: dict

    def to_dict(self):
        return deepcopy(self.data)


class ArenaAiController:
    def __init__(self, provider: ArenaTurnProvider | None = None):
        self.provider = provider if provider is not None else HeuristicArenaTurnProvider()

    def run_turn(self, simulation):
        observation = build_observation(simulation.state)
        turn = simulation.state.turn
        failure = None
        actual = self.provider
        try:
            plan = self.provider.create_turn_plan(observation)
        except ArenaProviderError as error:
            failure = error.category
            actual = HeuristicArenaTurnProvider()
            plan = actual.create_turn_plan(observation)
        result = execute_arena_turn(simulation.state, plan, execute_command=simulation.execute)
        data = result.to_dict()
        data.update(schema_version=AI_TRACE_VERSION, turn=turn, observation_hash=observation.hash,
                    provider_type=getattr(actual, "name", type(actual).__name__),
                    plan_hash=digest(plan.to_dict()), actions_executed=sum(a["executed"] for a in result.actions_attempted),
                    resulting_players=metrics(simulation.state)["players"],
                    resulting_units=[dict(id=u.id, owner_id=u.owner_id, status=u.status.value, hp=u.hp,
                                          x=u.position.x, y=u.position.y)
                                     for u in sorted(simulation.state.units.values(), key=lambda u: u.id)])
        # Preserve byte-identical Phase 3 heuristic diagnostics and hashes.
        if isinstance(self.provider, ModelArenaTurnProvider) or failure:
            inference = self.provider.last_trace if isinstance(self.provider, ModelArenaTurnProvider) else {}
            inference.update(requested_provider=self.provider.name,
                             actual_provider="heuristic" if failure else self.provider.name,
                             fallback_used=failure is not None, error_category=failure,
                             resulting_plan=plan.to_dict())
            data["inference"] = inference
        return ArenaAiTurnTrace(data)


def controller_setup(state, mode="manual"):
    if mode not in ("manual", "human_vs_heuristic", "heuristic_vs_heuristic", "human_vs_ollama", "human_vs_openai"):
        raise ValueError("unknown Arena controller mode")
    ai = ArenaControllerType(mode.removeprefix("human_vs_") + "_ai") if mode.startswith("human_vs_") else ArenaControllerType.HEURISTIC_AI
    return {p.id: ai if mode == "heuristic_vs_heuristic"
            or mode.startswith("human_vs_") and index == 1 else ArenaControllerType.HUMAN
            for index, p in enumerate(state.players)}


def advance_until_human(simulation, controllers, *, controller=None, max_ai_turns=200):
    """Consecutive AI turns, with an orchestration safety bound (never a game draw)."""
    integer(max_ai_turns, "max_ai_turns", 1)
    if set(controllers) != {p.id for p in simulation.state.players} or any(
            not isinstance(c, ArenaControllerType) for c in controllers.values()):
        raise ValueError("explicit Arena controller identity required for each player")
    if controller is None and any(c in (ArenaControllerType.OLLAMA_AI, ArenaControllerType.OPENAI_AI) for c in controllers.values()):
        raise ValueError("model controllers require an explicitly constructed provider")
    runner = controller if controller is not None else ArenaAiController()
    traces = []
    while simulation.state.active_player_id is not None and controllers[simulation.state.active_player_id] is not ArenaControllerType.HUMAN:
        if len(traces) == max_ai_turns:
            break
        traces.append(runner.run_turn(simulation))
    return tuple(traces)
