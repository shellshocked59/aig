"""Ephemeral plan reuse and activation orchestration, independent of HTTP."""

from dataclasses import dataclass

from aig.ai.executor import AiActivationResult, AiExecutor
from aig.ai.strategy import (
    HeuristicStrategyProvider, StrategicPlan, StrategicStateBuilder, StrategyProvider,
)
from aig.state import ControllerType, GameState, _integer


@dataclass
class AiController:
    provider: StrategyProvider
    replan_interval: int = 5
    previous_plan: StrategicPlan | None = None
    plan_creation_turn: int | None = None

    def __post_init__(self) -> None:
        _integer(self.replan_interval, "replan_interval", minimum=1)

    def plan_for(self, state: GameState, player_id: str) -> StrategicPlan:
        plan = self.previous_plan
        invalid = False
        if plan is not None:
            enemy = state.players.get(plan.primary_enemy_id)
            city = state.cities.get(plan.target_city_id)
            invalid = ((plan.primary_enemy_id is not None and (
                enemy is None or enemy.eliminated or enemy.id == player_id))
                or (plan.target_city_id is not None and (
                    city is None or city.owner_id == player_id
                    or (plan.primary_enemy_id is not None and city.owner_id != plan.primary_enemy_id))))
        if (plan is None or invalid or self.plan_creation_turn is None
                or state.turn < self.plan_creation_turn
                or state.turn - self.plan_creation_turn >= self.replan_interval):
            plan = self.provider.create_plan(StrategicStateBuilder().build(state, player_id), plan)
            if not isinstance(plan, StrategicPlan):
                raise ValueError("strategy provider must return a StrategicPlan")
            self.previous_plan = plan
            self.plan_creation_turn = state.turn
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

    def run_active_ai_activation(self, state: GameState) -> AiActivationResult | None:
        if state.active_controller is not ControllerType.AI:
            return None
        player_id = state.active_player_id
        controller = self.controllers.setdefault(player_id, AiController(self.provider, self.replan_interval))
        result = self.executor.execute(state, controller.plan_for(state, player_id))
        self.latest_results = (result,)
        return result

    def advance_until_human(self, state: GameState) -> tuple[AiActivationResult, ...]:
        if state.active_player_id is not None and not any(
                not p.eliminated and p.controller is ControllerType.HUMAN for p in state.players.values()):
            raise ValueError("advance_until_human requires a live human; use single activations for AI-only games")
        results = []
        # At most one pass through the live roster before reaching a human.
        for _ in range(len(state.turn_order)):
            result = self.run_active_ai_activation(state)
            if result is None:
                break
            results.append(result)
        if state.active_controller is ControllerType.AI:
            raise RuntimeError("AI orchestration failed to reach a human within the roster")
        if results:
            self.latest_results = tuple(results)
        return tuple(results)
