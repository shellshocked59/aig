"""Immutable requests and atomic deterministic Arena rules."""

from collections import deque
from dataclasses import dataclass
from types import MappingProxyType

from aig.movement import NEIGHBOR_OFFSETS
from aig.state import Position
from aig.arena.state import ArenaState, Bonus, TURN_AP, UnitType, UnitStatus, identifier, arena_team_has_active_units
from aig.arena.geometry import distance, can_step, arena_line_of_sight


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


@dataclass(frozen=True)
class ArenaFinish(ArenaAttack):
    pass


@dataclass(frozen=True)
class ArenaRevive(ArenaAttack):
    pass


@dataclass(frozen=True)
class ArenaShieldBash(ArenaAttack):
    pass


@dataclass(frozen=True)
class ArenaSnipe(ArenaAttack):
    pass


@dataclass(frozen=True)
class ArenaFireball:
    actor_id: str
    unit_id: str
    target_position: Position

    def __post_init__(self):
        identifier(self.actor_id, "actor_id")
        identifier(self.unit_id, "unit_id")
        if not isinstance(self.target_position, Position):
            raise ValueError("target_position must be a Position")


ArenaCommand = ArenaMove | ArenaAttack | ArenaHeal | ArenaEndTurn | ArenaFinish | ArenaRevive | ArenaShieldBash | ArenaSnipe | ArenaFireball
COMMAND_KINDS = {ArenaMove: "move", ArenaAttack: "attack", ArenaHeal: "heal", ArenaEndTurn: "end_turn",
                 ArenaFinish: "finish", ArenaRevive: "revive", ArenaShieldBash: "shield_bash",
                 ArenaSnipe: "snipe", ArenaFireball: "fireball"}
COMMAND_TYPES = tuple(COMMAND_KINDS)
ACTION_COSTS = MappingProxyType(dict(move=1, attack=1, heal=1, end_turn=0, finish=1,
                                    revive=2, shield_bash=1, snipe=2, fireball=2))
SPECIALS = MappingProxyType({UnitType.KNIGHT: ("shield_bash",), UnitType.RANGER: ("snipe",),
                            UnitType.MAGE: ("fireball",), UnitType.CLERIC: ("heal", "revive")})
ACTION_RANGES = MappingProxyType(dict(finish=1, revive=2, shield_bash=1, snipe=4, fireball=2))


def arena_action_cost(command):
    """Accept a domain command or action name; reject foreign command types."""
    kind = command if isinstance(command, str) else COMMAND_KINDS.get(type(command))
    if kind not in ACTION_COSTS:
        raise ValueError("unknown Arena action")
    return ACTION_COSTS[kind]


def find_path(state, unit_id, destination):
    """BFS, endpoints included; N, NE, E, SE, S, SW, W, NW tie order.

    All units (including downed) and Cores block transit. Diagonal steps require
    both orthogonal terrain cells open. Queries ignore AP/ownership.
    """
    state.validate()
    if unit_id not in state.units or not isinstance(destination, Position):
        raise ValueError("path requires a present unit and Position")
    unit = state.units[unit_id]
    if unit.status is UnitStatus.DOWNED:
        return None
    start = unit.position
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
            if neighbor not in previous and can_step(state, current, neighbor):
                previous[neighbor] = current
                frontier.append(neighbor)
    return None


def attack_damage(state, attacker, target, base_damage=None):
    """Integer damage before HP clamping. Specials never receive SIEGE."""
    bonus = state.board.at(attacker.position).bonus
    damage = (attacker.stats.damage if base_damage is None else base_damage) + (2 if bonus is Bonus.POWER else 0)
    if target.id in state.cores:
        return damage + (4 if base_damage is None and bonus is Bonus.SIEGE else 0)
    return max(1, damage - (2 if state.board.at(target.position).bonus is Bonus.WARD else 0))


def arena_fireball_affected_units(state, impact):
    """Stable IDs, including the caster/friendlies, excluding bodies and Cores."""
    return sorted(u.id for u in state.units.values()
                  if u.status is UnitStatus.ACTIVE and distance(u.position, impact) <= 1)


def validate_command(state, command):
    """Pure authoritative validation shared by execution and legal-action queries."""
    if not isinstance(state, ArenaState) or type(command) not in COMMAND_TYPES:
        raise ValueError("Arena state and command required")
    state.validate()
    if state.winner_player_id is not None:
        raise ValueError("battle has ended")
    if command.actor_id != state.active_player_id:
        raise ValueError("only the active player may act")
    if type(command) is ArenaEndTurn:
        return
    if state.action_points_remaining < arena_action_cost(command):
        raise ValueError("insufficient AP; End Turn to continue")
    unit = state.units.get(command.unit_id)
    if unit is None or unit.owner_id != command.actor_id or unit.status is not UnitStatus.ACTIVE:
        raise ValueError("actor must own an ACTIVE unit")
    kind = COMMAND_KINDS[type(command)]
    if kind not in ("move", "attack", "finish") and kind not in SPECIALS[unit.unit_type]:
        raise ValueError("unit class cannot use this ability")
    if type(command) is ArenaMove:
        path = find_path(state, unit.id, command.destination)
        if path is None or not 1 <= len(path) - 1 <= unit.stats.move_range:
            raise ValueError("destination is occupied, blocked, unchanged, or beyond move range")
        return
    if type(command) is ArenaFireball:
        position = command.target_position
        if not state.board.contains(position) or distance(unit.position, position) > 2:
            raise ValueError("impact outside Fireball range/board")
    else:
        target = state.units.get(command.target_id)
        if type(command) is ArenaAttack:
            target = target or state.cores.get(command.target_id)
        friendly = type(command) in (ArenaHeal, ArenaRevive)
        downed = type(command) in (ArenaFinish, ArenaRevive)
        if target is None or (target.owner_id == unit.owner_id) != friendly:
            raise ValueError("invalid target ownership or entity type")
        if target.id in state.units and (target.status is UnitStatus.DOWNED) != downed:
            raise ValueError("invalid target ACTIVE/DOWNED status")
        reach = unit.stats.attack_range if type(command) is ArenaAttack else (2 if type(command) is ArenaHeal else ACTION_RANGES[kind])
        position = target.position
        if distance(unit.position, position) > reach:
            raise ValueError("target outside action range")
        if type(command) is ArenaHeal and target.hp == target.max_hp:
            raise ValueError("target already has full HP")
    needs_los = (type(command) in (ArenaHeal, ArenaRevive, ArenaSnipe, ArenaFireball)
                 or type(command) is ArenaAttack and unit.unit_type is not UnitType.KNIGHT)
    if needs_los and not arena_line_of_sight(state.board, unit.position, position):
        raise ValueError("blocked line of sight")


def resolve_victory(state, actor_id):
    defeated = {p.id for p in state.players if not arena_team_has_active_units(state, p.id)
                or any(c.owner_id == p.id and c.hp == 0 for c in state.cores.values())}
    if defeated:
        # Friendly fire can eliminate both teams: the casting team loses ties.
        state.winner_player_id = (next(p.id for p in state.players if p.id != actor_id)
                                  if actor_id in defeated else actor_id)
        state.active_player_id = None


def apply_command(state: ArenaState, command: ArenaCommand):
    """Reject before mutation; compute AoE from pre-action state; resolve once."""
    validate_command(state, command)
    kind = type(command)
    if kind is ArenaEndTurn:
        order = [p.id for p in state.players]
        index = order.index(command.actor_id)
        state.active_player_id = order[1 - index]
        state.action_points_remaining = TURN_AP
        state.turn += int(index == 1)
        return
    unit = state.units[command.unit_id]
    if kind is ArenaMove:
        unit.position = command.destination
    elif kind is ArenaFinish:
        del state.units[command.target_id]
    elif kind in (ArenaHeal, ArenaRevive):
        target = state.units[command.target_id]
        if kind is ArenaRevive:
            target.status, target.hp = UnitStatus.ACTIVE, 5
        else:
            target.hp = min(target.max_hp, target.hp + 5)
    else:
        if kind is ArenaFireball:
            targets = [state.units[uid] for uid in arena_fireball_affected_units(state, command.target_position)]
            base = 4
        else:
            targets = [state.units.get(command.target_id) or state.cores[command.target_id]]
            base = {ArenaAttack: None, ArenaShieldBash: 4, ArenaSnipe: 8}[kind]
        damage = [(target, attack_damage(state, unit, target, base)) for target in targets]
        for target, amount in damage:
            target.hp = max(0, target.hp - amount)
            if target.id in state.units and target.hp == 0:
                target.status = UnitStatus.DOWNED
        if kind is ArenaShieldBash:
            target = targets[0]
            dest = Position(2 * target.position.x - unit.position.x, 2 * target.position.y - unit.position.y)
            if target.status is UnitStatus.ACTIVE and state.can_enter(dest):
                target.position = dest
    state.action_points_remaining -= arena_action_cost(command)
    resolve_victory(state, command.actor_id)
