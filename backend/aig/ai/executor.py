"""Basic tactical choices; every gameplay mutation goes through apply_command."""

from collections.abc import Callable
from dataclasses import asdict, dataclass

from aig.ai.strategy import ExpansionPriority, Posture, StrategicPlan
from aig.cities import can_found_city_at
from aig.combat import preview_attack
from aig.commands import (
    AttackUnit, Command, EndActivation, FoundCity, MoveUnit,
    SetCityProduction, SetResearch, apply_command,
)
from aig.economy import terrain_yields
from aig.movement import find_path
from aig.research import available_technologies, unit_is_unlocked
from aig.state import ControllerType, GameState, Position, UnitState, UnitType, _integer


def _distance(a: Position, b: Position) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


@dataclass(frozen=True)
class AiActivationResult:
    player_id: str
    plan: StrategicPlan
    commands_executed: tuple[Command, ...]

    def to_dict(self) -> dict:
        return {"player_id": self.player_id, "plan": self.plan.to_dict(),
                "commands_executed": [dict(type=type(c).__name__, **asdict(c))
                                      for c in self.commands_executed]}


class AiActionLimitError(RuntimeError):
    """A controller bug or undersized configured budget must never hang a turn."""


class AiExecutor:
    def __init__(self, max_actions: int = 256, *,
                 observer: Callable[[str, GameState, Command], None] | None = None):
        _integer(max_actions, "max_actions", minimum=1)
        self.max_actions = max_actions
        # Optional read-only instrumentation; never part of command selection.
        self.observer = observer

    def execute(self, state: GameState, plan: StrategicPlan) -> AiActivationResult:
        state.validate()
        if state.active_controller is not ControllerType.AI:
            raise ValueError("AI execution requires an active AI player")
        if not isinstance(plan, StrategicPlan):
            raise ValueError("AI execution requires a StrategicPlan")
        actor = state.active_player_id
        executed: list[Command] = []

        def issue(command: Command) -> None:
            if len(executed) >= self.max_actions:
                raise AiActionLimitError(f"AI {actor} exceeded {self.max_actions} actions on turn {state.turn}")
            if self.observer is not None:
                self.observer("before", state, command)
            apply_command(state, command)
            executed.append(command)
            if self.observer is not None:
                self.observer("after", state, command)

        player = state.players[actor]
        available = available_technologies(player)
        research = next((t for t in plan.research_priority if t in available), None)
        if research is not None and research != player.research_target:
            issue(SetResearch(actor, research))
        self._production(state, actor, plan, issue)

        # Snapshot IDs, never live dictionary iteration across mutations.
        settlers = sorted(u.id for u in state.units.values()
                          if u.owner_id == actor and u.unit_type is UnitType.SETTLER)
        for unit_id in settlers:
            unit = state.units[unit_id]
            while unit.moves_remaining:
                if can_found_city_at(state, actor, unit.position):
                    base = f"ai-city-{unit.id}"
                    city_id, suffix = base, 1
                    while city_id in state.cities:
                        city_id = f"{base}-{suffix}"
                        suffix += 1
                    number = 1 + sum(c.owner_id == actor for c in state.cities.values())
                    issue(FoundCity(actor, unit.id, city_id, f"{actor} Settlement {number}"))
                    break
                path = self._settlement_path(state, unit)
                if path is None:
                    break
                issue(MoveUnit(actor, unit.id, path[min(unit.moves_remaining, len(path) - 1)]))

        # New cities need a target before this activation's economy.
        self._production(state, actor, plan, issue)
        military = sorted(u.id for u in state.units.values()
                          if u.owner_id == actor and u.unit_type is not UnitType.SETTLER)
        for unit_id in military:
            while unit_id in state.units and state.units[unit_id].moves_remaining:
                unit = state.units[unit_id]
                targets = []
                for enemy in sorted(state.units.values(), key=lambda u: u.id):
                    if enemy.owner_id == actor:
                        continue
                    try:
                        preview = preview_attack(state, unit.id, enemy.id)
                    except ValueError:
                        continue
                    targets.append((enemy.hp > preview.target_damage, enemy.hp, enemy.id))
                if targets:
                    issue(AttackUnit(actor, unit.id, min(targets)[2]))
                    continue
                path = self._military_path(state, unit, plan)
                if path is None or len(path) < 2:
                    break
                issue(MoveUnit(actor, unit.id, path[min(unit.moves_remaining, len(path) - 1)]))

        issue(EndActivation(actor))
        return AiActivationResult(actor, plan, tuple(executed))

    @staticmethod
    def _production(state: GameState, actor: str, plan: StrategicPlan,
                    issue: Callable[[Command], None]) -> None:
        cities = sorted((c for c in state.cities.values() if c.owner_id == actor), key=lambda c: c.id)
        units = [u for u in state.units.values() if u.owner_id == actor]
        military_needed = sum(u.unit_type is not UnitType.SETTLER for u in units) < 2
        settler_committed = any(u.unit_type is UnitType.SETTLER for u in units) or any(
            c.production_target is UnitType.SETTLER for c in cities)
        for city in cities:
            # Finish existing orders, except civilian construction during a military shortage.
            if city.production_target is not None and not (
                    military_needed and city.production_target is UnitType.SETTLER):
                continue
            choices = list(plan.production_priority)
            if military_needed:
                choices = [t for t in choices if t is not UnitType.SETTLER]
                choices += [t for t in (UnitType.WARRIOR, UnitType.ARCHER, UnitType.SPEARMAN) if t not in choices]
            allow_settler = (not military_needed and not settler_committed and len(cities) < 2
                             and plan.expansion_priority is ExpansionPriority.HIGH
                             and any(can_found_city_at(state, actor, p) for p in sorted(
                                 state.tiles, key=lambda p: (p.y, p.x))))
            target = next((t for t in choices if unit_is_unlocked(state.players[actor], t)
                           and (t is not UnitType.SETTLER or allow_settler)), None)
            if target is not None and target != city.production_target:
                issue(SetCityProduction(actor, city.id, target))
                if target is UnitType.SETTLER:
                    settler_committed = True

    @staticmethod
    def _settlement_path(state: GameState, unit: UnitState) -> list[Position] | None:
        def priority(position: Position):
            yields = [terrain_yields(t.terrain) for p, t in state.tiles.items()
                      if _distance(p, position) <= 1]
            return (_distance(unit.position, position), -sum(y.food for y in yields),
                    -sum(y.production for y in yields), position.y, position.x)

        candidates = [p for p in state.tiles if can_found_city_at(state, unit.owner_id, p)]
        for position in sorted(candidates, key=priority):
            path = find_path(state, unit, position)
            if path is not None and len(path) > 1:
                return path
        return None

    @staticmethod
    def _military_path(state: GameState, unit: UnitState, plan: StrategicPlan) -> list[Position] | None:
        own_cities = [c for c in state.cities.values() if c.owner_id == unit.owner_id]
        enemies = [u for u in state.units.values() if u.owner_id != unit.owner_id]
        goal = None
        if plan.posture is Posture.DEFEND or plan.posture is Posture.EXPAND:
            city = min(own_cities, key=lambda c: (_distance(unit.position, c.position), c.id), default=None)
            if city is not None:
                threats = [e for e in enemies if _distance(e.position, city.position) <= 3]
                if threats:
                    goal = min(threats, key=lambda e: (_distance(unit.position, e.position), e.id)).position
                elif _distance(unit.position, city.position) > 1:
                    goal = city.position
                else:
                    return None
        if goal is None:
            target = state.cities.get(plan.target_city_id)
            if target is not None and target.owner_id != unit.owner_id:
                goal = target.position
            else:
                enemy = min(enemies, key=lambda e: (
                    e.owner_id != plan.primary_enemy_id, _distance(unit.position, e.position), e.id), default=None)
                if enemy is not None:
                    goal = enemy.position
        if goal is None:
            return None
        # Approach a firing/holding position; never issue a move onto the enemy city.
        radius = unit.unit_type.attack_range
        if _distance(unit.position, goal) <= radius:
            return None
        candidates = sorted((p for p in state.tiles if 1 <= _distance(p, goal) <= radius),
                            key=lambda p: (_distance(unit.position, p), _distance(p, goal), p.y, p.x))
        for position in candidates:
            path = find_path(state, unit, position)
            if path is not None:
                return path
        return None
