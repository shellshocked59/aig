"""Local deterministic system activation using the ordinary command/rules engine."""

from dataclasses import asdict, dataclass, replace

from aig.commands import AttackUnit, EndActivation, MoveUnit, apply_command
from aig.combat import preview_attack
from aig.knowledge import vision_positions, update_knowledge
from aig.movement import find_path
from aig.state import BARBARIAN_ID, UnitType

SPAWN_INTERVAL = 8
MAX_CAMP_WARRIORS = 2
PURSUIT_RANGE = 5
GUARD_RADIUS = 2


def distance(a, b):
    return max(abs(a.x-b.x), abs(a.y-b.y))


def spawn_replacements(state):
    """Entry hook, once per actual phase transition; restore never calls this.

    Turn zero has no replacements. At phase entry on turns 8,16,... each camp
    attempts one spawn, on its tile only. Same-owner stacking remains legal.
    """
    if state.result is not None or state.turn == 0 or state.turn % SPAWN_INTERVAL:
        return
    for camp in sorted(state.camps.values(), key=lambda c: c.id):
        count = sum(u.owner_id == BARBARIAN_ID and u.home_camp_id == camp.id
                    for u in state.units.values())
        if count < MAX_CAMP_WARRIORS and state.can_enter(BARBARIAN_ID, camp.position):
            state.add_unit(BARBARIAN_ID, UnitType.WARRIOR, camp.position).home_camp_id = camp.id
    update_knowledge(state)


@dataclass(frozen=True)
class BarbarianActivationResult:
    player_id: str
    commands_executed: tuple

    def to_dict(self):
        return dict(player_id=self.player_id, system_phase=True,
                    commands_executed=[dict(type=type(c).__name__, **asdict(c)) for c in self.commands_executed])


class BarbarianController:
    def execute(self, state, *, observer=None):
        if state.active_player_id != BARBARIAN_ID or not state.is_barbarian(BARBARIAN_ID):
            raise ValueError("barbarian controller requires active system faction")
        commands = []

        def issue(command):
            if observer:
                observer("before", state, command)
            apply_command(state, command)
            commands.append(command)
            if observer:
                observer("after", state, command)

        for unit_id in sorted(u.id for u in state.units.values() if u.owner_id == BARBARIAN_ID):
            unit = state.units.get(unit_id)
            if unit is None or not unit.moves_remaining:
                continue
            camp = state.camps.get(unit.home_camp_id)
            visible = vision_positions(state.game_map, unit.position, 2)
            if camp:
                visible |= vision_positions(state.game_map, camp.position, 2)
            enemies = [u for u in state.units.values()
                       if u.owner_id != BARBARIAN_ID and u.position in visible]
            targets = []
            for enemy in enemies:
                try:
                    preview = preview_attack(state, unit.id, enemy.id)
                except ValueError:
                    continue
                targets.append((enemy.hp > preview.target_damage, enemy.unit_type is not UnitType.SETTLER,
                                enemy.hp, distance(unit.position, enemy.position), enemy.id))
            if targets:
                issue(AttackUnit(BARBARIAN_ID, unit.id, min(targets)[-1]))
                continue
            target = min((u for u in enemies if distance(unit.position, u.position) <= PURSUIT_RANGE
                          and (camp is None or distance(camp.position, u.position) <= PURSUIT_RANGE)),
                         key=lambda u: (distance(unit.position, u.position), u.id), default=None)
            goal = target.position if target else (camp.position if camp else None)
            if goal is None or (target is None and distance(unit.position, goal) <= GUARD_RADIUS):
                continue
            # Keep only this unit/home-camp's current sight. Other camps/warriors
            # cannot disclose targets or route blockers across the map.
            from aig.ai.knowledge_planning import PlanningView
            view = PlanningView(state.game_map, {BARBARIAN_ID: state.players[BARBARIAN_ID]},
                                {p: replace(t) for p, t in state.tiles.items() if p in visible},
                                {c.id: c for c in state.cities.values() if c.position in visible},
                                {u.id: u for u in state.units.values() if u.position in visible},
                                frozenset(visible), {})
            candidates = sorted((p for p in view.tiles if distance(p, goal) <= (1 if target else GUARD_RADIUS)),
                                key=lambda p: (distance(unit.position, p), distance(p, goal), p.y, p.x))
            for position in candidates:
                path = find_path(view, unit, position)
                if path and len(path) > 1:
                    issue(MoveUnit(BARBARIAN_ID, unit.id, path[1]))
                    break
        issue(EndActivation(BARBARIAN_ID))
        return BarbarianActivationResult(BARBARIAN_ID, tuple(commands))
