"""Detached, explicit perfect-information browser DTO and legal action queries."""

from dataclasses import asdict

from aig.state import Position
from aig.arena.v1.commands import distance, find_path
from aig.arena.v1.state import UnitType


def legal_actions(state, unit):
    result = dict(move=[], attack=[], heal=[])
    if state.active_player_id != unit.owner_id or state.action_points_remaining == 0:
        return result
    for y in range(state.board.height):
        for x in range(state.board.width):
            destination = Position(x, y)
            if destination == unit.position or distance(unit.position, destination) > unit.stats.move_range:
                continue
            path = find_path(state, unit.id, destination)
            if path is not None and len(path) - 1 <= unit.stats.move_range:
                result["move"].append(dict(x=x, y=y))
    result["attack"] = sorted(t.id for t in (*state.units.values(), *state.cores.values())
                              if t.owner_id != unit.owner_id and distance(unit.position, t.position) <= unit.stats.attack_range)
    if unit.unit_type is UnitType.CLERIC:
        result["heal"] = sorted(t.id for t in state.units.values() if t.owner_id == unit.owner_id
                                and t.hp < t.max_hp and distance(unit.position, t.position) <= unit.stats.heal_range)
    return result


def public_state(state):
    state.validate()
    def piece(e):
        return dict(id=e.id, owner_id=e.owner_id, x=e.position.x, y=e.position.y, hp=e.hp)
    return dict(
        environment="arena", rules_version=state.config.rules_version, scenario_version=state.config.scenario_version,
        turn=state.turn, active_player_id=state.active_player_id,
        action_points_remaining=state.action_points_remaining, winner_player_id=state.winner_player_id,
        players=[dict(id=p.id, name=p.name) for p in state.players],
        board=dict(width=state.board.width, height=state.board.height,
                   tiles=[dict(x=x, y=y, terrain=t.terrain.value, bonus=t.bonus.value if t.bonus else None)
                          for y in range(state.board.height) for x in range(state.board.width)
                          for t in [state.board.at(Position(x, y))]]),
        units=[dict(**piece(u), unit_type=u.unit_type.value, max_hp=u.max_hp,
                    stats=asdict(u.stats), actions=legal_actions(state, u))
               for u in sorted(state.units.values(), key=lambda u: u.id)],
        cores=[dict(**piece(c), max_hp=30) for c in sorted(state.cores.values(), key=lambda c: c.id)],
    )
