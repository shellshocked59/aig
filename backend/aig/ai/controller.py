"""Ephemeral plan reuse and activation orchestration, independent of HTTP."""

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field

from aig.ai.executor import AiActivationResult, AiExecutor
from aig.ai.strategy import (
    HeuristicStrategyProvider, StrategicPlan, StrategicStateBuilder, StrategyProvider, StrategyProviderError,
)
from aig.knowledge import known_enemy_cities, visible_enemy_units
from aig.knowledge import known_camps
from aig.state import ControllerType, GameState, _integer
from aig.barbarians import BarbarianActivationResult


@dataclass
class AiController:
    provider: StrategyProvider
    replan_interval: int = 5
    previous_plan: StrategicPlan | None = None
    plan_creation_turn: int | None = None
    last_trace: dict | None = field(default=None, init=False)
    summary: dict = field(default_factory=dict, init=False)

    _seen_city: bool = field(default=False, init=False)
    _seen_military: bool = field(default=False, init=False)
    _seen_camp: bool = field(default=False, init=False)
    _seen_barbarian: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        _integer(self.replan_interval, "replan_interval", minimum=1)

    def plan_for(self, state: GameState, player_id: str) -> StrategicPlan:
        cities = {c["id"]: c for c in known_enemy_cities(state, player_id)}
        if state.is_barbarian(player_id):
            raise ValueError("system faction cannot use a StrategyProvider")
        enemies = visible_enemy_units(state, player_id)
        contact = any(u.unit_type.combat_strength > 0 and not state.is_barbarian(u.owner_id) for u in enemies)
        barbarian = any(state.is_barbarian(u.owner_id) for u in enemies)
        camps = bool(known_camps(state, player_id))
        discovery = ("first_enemy_city_discovered" if cities and not self._seen_city else
                     "first_enemy_military_contact" if contact and not self._seen_military else
                     "first_barbarian_contact" if barbarian and not self._seen_barbarian else
                     "first_camp_discovered" if camps and not self._seen_camp else None)
        self._seen_city |= bool(cities)
        self._seen_military |= contact
        self._seen_camp |= camps
        self._seen_barbarian |= barbarian
        plan = self.previous_plan
        invalid = False
        if plan is not None:
            enemy = state.players.get(plan.primary_enemy_id)
            city = cities.get(plan.target_city_id)
            invalid = ((plan.primary_enemy_id is not None and (
                enemy is None or enemy.eliminated or enemy.id == player_id))
                or (plan.target_city_id is not None and (
                    city is None or city["live_exists"] is False or city["owner_id"] == player_id
                    or state.players[city['owner_id']].eliminated
                    or (plan.primary_enemy_id is not None and city["owner_id"] != plan.primary_enemy_id))))
        age = None if self.plan_creation_turn is None else state.turn - self.plan_creation_turn
        reason = ("missing_plan" if plan is None else "invalid_target" if invalid else
                  discovery if discovery is not None else
                  "missing_creation_turn" if age is None else "turn_rewound" if age < 0 else
                  "expired" if age >= self.replan_interval else None)
        self.last_trace = None
        if reason is not None:
            strategic_state = StrategicStateBuilder().build(state, player_id)
            requested = getattr(self.provider, "name", type(self.provider).__name__)
            actual, fallback, failure = requested, False, None
            # Invalidated targets are diagnostics, never provider continuity.
            invalidated_previous = plan if invalid else None
            previous = None if invalid else plan
            try:
                plan = self.provider.create_plan(strategic_state, previous)
            except StrategyProviderError as error:
                failure = str(error)
                plan = HeuristicStrategyProvider().create_plan(strategic_state, previous)
                actual, fallback = "heuristic", True
            if not isinstance(plan, StrategicPlan):
                raise ValueError("strategy provider must return a StrategicPlan")
            trace = deepcopy(getattr(self.provider, "last_trace", None)) or {}
            trace.update(game_seed=state.config.seed, turn=state.turn, player_id=player_id,
                         strategic_state=deepcopy(strategic_state),
                         previous_plan=previous.to_dict() if previous else None,
                         resulting_plan=plan.to_dict(), requested_provider=requested,
                         actual_provider=actual, fallback_used=fallback,
                         replan_reason=reason, plan_age_turns=age)
            if invalidated_previous is not None:
                trace["invalidated_previous_plan"] = invalidated_previous.to_dict()
            if failure:
                trace["error"] = failure
            self.last_trace = trace
            self.summary = dict(requestedProvider=requested, actualProvider=actual,
                                fallbackUsed=fallback, model=trace.get("model"),
                                durationSeconds=trace.get("wall_clock_seconds"),
                                retryCount=trace.get("retry_count", 0))
            self.previous_plan = plan
            self.plan_creation_turn = state.turn
        self.summary.update(planReused=reason is None, replanReason=reason,
                            planAgeTurns=state.turn - self.plan_creation_turn)
        # Inference timing/retries describe this activation; provenance persists on reuse.
        if reason is None:
            self.summary.update(durationSeconds=0.0, retryCount=0)
        return plan


class AiOrchestrator:
    def __init__(self, provider: StrategyProvider | None = None, *,
                 replan_interval: int = 5, max_actions: int = 256):
        _integer(replan_interval, "replan_interval", minimum=1)
        self.provider = provider if provider is not None else HeuristicStrategyProvider()
        self.replan_interval = replan_interval
        self.executor = AiExecutor(max_actions)
        self.controllers: dict[str, AiController] = {}
        self.latest_results: tuple[AiActivationResult, ...] = ()
        self.latest_summaries: tuple[dict, ...] = ()
        self._inference_traces: deque[dict] = deque(maxlen=64)

    @property
    def inference_traces(self) -> list[dict]:
        """Detached backend debugging records; bounded and never part of snapshots."""
        return deepcopy(list(self._inference_traces))

    def run_active_ai_activation(self, state: GameState) -> AiActivationResult | BarbarianActivationResult | None:
        if state.active_controller is not ControllerType.AI:
            return None
        player_id = state.active_player_id
        if state.is_barbarian(player_id):
            from aig.barbarians import BarbarianController
            result = BarbarianController().execute(state, observer=self.executor.observer)
            self.latest_results = ()
            self.latest_summaries = ({"actualProvider": "system"},)
            return result
        controller = self.controllers.setdefault(player_id, AiController(self.provider, self.replan_interval))
        plan = controller.plan_for(state, player_id)
        if controller.last_trace is not None:
            self._inference_traces.append(deepcopy(controller.last_trace))
        result = self.executor.execute(state, plan)
        self.latest_results = (result,)
        self.latest_summaries = (deepcopy(controller.summary),)
        return result

    def advance_until_human(self, state: GameState) -> tuple[AiActivationResult, ...]:
        if state.active_player_id is not None and not any(
                not p.eliminated and p.controller is ControllerType.HUMAN for p in state.players.values()):
            raise ValueError("advance_until_human requires a live human; use single activations for AI-only games")
        results = []
        summaries = []
        # At most one pass through the live roster before reaching a human.
        for _ in range(len(state.turn_order)):
            result = self.run_active_ai_activation(state)
            if result is None:
                break
            if not state.is_barbarian(result.player_id):
                results.append(result)
                summaries.append(self.latest_summaries[0])
        if state.active_controller is ControllerType.AI:
            raise RuntimeError("AI orchestration failed to reach a human within the roster")
        if results:
            self.latest_results = tuple(results)
            self.latest_summaries = tuple(summaries)
        return tuple(results)
