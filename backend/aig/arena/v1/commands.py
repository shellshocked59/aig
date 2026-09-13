"""Immutable requests and atomic deterministic Arena rules."""

from collections import deque
from dataclasses import dataclass

from aig.movement import NEIGHBOR_OFFSETS
from aig.state import Position
from aig.arena.v1.state import ArenaState, Bonus, TURN_AP, UnitType, identifier


@dataclass(frozen=True)
class ArenaEndTurn:
    actor_id: str

    def __post_init__(self):
        identifier(self.actor_id, "actor_id")


@dataclass(frozen=True)
class ArenaMove:
    actor_id: str
    unit_id: str
    destination: Position

    def __post_init__(self):
        identifier(self.actor_id, "actor_id")
        identifier(self.unit_id, "unit_id")
        if not isinstance(self.destination, Position):
            raise ValueError("destination must be a Position")


@dataclass(frozen=True)
class ArenaAttack:
    actor_id: str
    unit_id: str
    target_id: str

    def __post_init__(self):
        identifier(self.actor_id, "actor_id")
        identifier(self.unit_id, "unit_id")
        identifier(self.target_id, "target_id")


@dataclass(frozen=True)
class ArenaHeal:
    actor_id: str
    unit_id: str
    target_id: str

    def __post_init__(self):
        identifier(self.actor_id, "actor_id")
        identifier(self.unit_id, "unit_id")
        identifier(self.target_id, "target_id")


ArenaCommand = ArenaMove | ArenaAttack | ArenaHeal | ArenaEndTurn
COMMAND_TYPES = (ArenaMove, ArenaAttack, ArenaHeal, ArenaEndTurn)


def distance(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))


def find_path(state, unit_id, destination):
    """BFS including endpoints; N, NE, E, SE, S, SW, W, NW tie order.

    All eight steps cost one. Like Empire, diagonals may cut blocked corners.
    Unlike Empire, all units and both Cores block transit and destinations.
    Query ignores AP/ownership and never mutates state.
    """
    state.validate()
    if unit_id not in state.units or not isinstance(destination, Position):
        raise ValueError("path requires a live unit and Position")
    start = state.units[unit_id].position
    if destination == start:
        return [start]
    if not state.can_enter(destination):
        return None
    frontier = deque([start])
    previous = {start: None}
    while frontier:
        current = frontier.popleft()
        if current == destination:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return list(reversed(path))
        for dx, dy in NEIGHBOR_OFFSETS:
            neighbor = Position(current.x + dx, current.y + dy)
            if neighbor not in previous and state.can_enter(neighbor):
                previous[neighbor] = current
                frontier.append(neighbor)
    return None


def attack_damage(state, attacker, target):
    """Integer damage before HP clamping; WARD only mitigates units."""
    bonus = state.board.at(attacker.position).bonus
    damage = attacker.stats.damage + (2 if bonus is Bonus.POWER else 0)
    if target.id in state.cores:
        return damage + (4 if bonus is Bonus.SIEGE else 0)
    return max(1, damage - (2 if state.board.at(target.position).bonus is Bonus.WARD else 0))


def apply_command(state: ArenaState, command: ArenaCommand):
    """All rejection precedes mutation. Terminal actions never advance the turn."""
    if not isinstance(state, ArenaState) or type(command) not in COMMAND_TYPES:
        raise ValueError("Arena state and command required")
    state.validate()
    if state.winner_player_id is not None:
        raise ValueError("battle has ended")
    if command.actor_id != state.active_player_id:
        raise ValueError("only the active player may act")
    if isinstance(command, ArenaEndTurn):
        order = [p.id for p in state.players]
        index = order.index(command.actor_id)
        state.active_player_id = order[1 - index]
        state.action_points_remaining = TURN_AP
        state.turn += int(index == 1)
        return
    if state.action_points_remaining < 1:
        raise ValueError("no AP remaining; End Turn to continue")
    unit = state.units.get(command.unit_id)
    if unit is None or unit.owner_id != command.actor_id:
        raise ValueError("actor must own the living unit")
    if isinstance(command, ArenaMove):
        path = find_path(state, unit.id, command.destination)
        if path is None or not 1 <= len(path) - 1 <= unit.stats.move_range:
            raise ValueError("destination is occupied, blocked, unchanged, or beyond move range")
        unit.position = command.destination
    elif isinstance(command, ArenaAttack):
        target = state.units.get(command.target_id) or state.cores.get(command.target_id)
        if target is None or target.owner_id == unit.owner_id:
            raise ValueError("attack requires an enemy unit or Core")
        if distance(unit.position, target.position) > unit.stats.attack_range:
            raise ValueError("target outside attack range")
        target.hp = max(0, target.hp - attack_damage(state, unit, target))
        if target.hp == 0 and target.id in state.units:
            del state.units[target.id]
        if (any(c.hp == 0 for c in state.cores.values())
                or not any(u.owner_id == target.owner_id for u in state.units.values())):
            state.winner_player_id = unit.owner_id
            state.active_player_id = None
    elif isinstance(command, ArenaHeal):
        target = state.units.get(command.target_id)
        if unit.unit_type is not UnitType.CLERIC:
            raise ValueError("only Clerics can heal")
        if target is None or target.owner_id != unit.owner_id:
            raise ValueError("heal requires a friendly living unit, never a Core")
        if distance(unit.position, target.position) > unit.stats.heal_range:
            raise ValueError("target outside heal range")
        if target.hp == target.max_hp:
            raise ValueError("target already has full HP")
        target.hp = min(target.max_hp, target.hp + unit.stats.heal_amount)
    state.action_points_remaining -= 1
