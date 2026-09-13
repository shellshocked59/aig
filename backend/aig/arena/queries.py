"""Pure legal action queries using the same validator as command execution."""

from aig.state import Position
from aig.arena.commands import (ACTION_COSTS, ACTION_RANGES, COMMAND_KINDS, SPECIALS,
                                ArenaEndTurn, ArenaFireball, ArenaMove, validate_command)
from aig.arena.geometry import arena_line_of_sight
from aig.arena.commands import arena_action_cost, arena_fireball_affected_units
from aig.arena.state import UnitStatus, arena_team_has_active_units


def legal_actions(state, unit):
    """Positions and entity IDs, independent of wire/browser formatting."""
    result = {kind: [] for kind in ACTION_COSTS if kind != "end_turn"}
    if (state.winner_player_id is not None or state.active_player_id != unit.owner_id
            or unit.status is not UnitStatus.ACTIVE):
        return result
    for cls, kind in COMMAND_KINDS.items():
        if cls is ArenaEndTurn or state.action_points_remaining < ACTION_COSTS[kind]:
            continue
        if kind not in ("move", "attack", "finish") and kind not in SPECIALS[unit.unit_type]:
            continue
        if cls in (ArenaMove, ArenaFireball):
            candidates = [Position(x, y) for y in range(state.board.height) for x in range(state.board.width)]
        else:
            candidates = sorted([*state.units, *state.cores])
        for target in candidates:
            command = cls(unit.owner_id, unit.id, target)
            try:
                validate_command(state, command)
            except ValueError:
                continue
            result[kind].append(target)
    return result


def abilities(unit):
    """Derived class metadata, including unavailable abilities for discovery."""
    return {kind: dict(ap_cost=ACTION_COSTS[kind], range=(unit.stats.move_range if kind == "move"
                      else unit.stats.attack_range if kind == "attack" else 2 if kind == "heal"
                      else ACTION_RANGES[kind]))
            for kind in ("move", "attack", *SPECIALS[unit.unit_type], "finish")}


def arena_legal_moves(state, unit_id):
    return legal_actions(state, state.units[unit_id])["move"]


def arena_attackable_targets(state, unit_id):
    return legal_actions(state, state.units[unit_id])["attack"]


def arena_finishable_targets(state, unit_id):
    return legal_actions(state, state.units[unit_id])["finish"]


def arena_revivable_targets(state, unit_id):
    return legal_actions(state, state.units[unit_id])["revive"]


def arena_fireball_targets(state, unit_id):
    return legal_actions(state, state.units[unit_id])["fireball"]
