"""Independent deterministic behavior fixtures and evaluation-only consequences."""
from copy import deepcopy
from aig.state import Position
from aig.arena.scenarios import create_scenario
from aig.arena.state import ArenaUnit, Board, Tile, UnitType, UnitStatus, STATS
from aig.arena.commands import ArenaFireball, validate_command, arena_fireball_affected_units, apply_command

FIXTURE_VERSION = "arena-fireball-behavior-fixtures-v1"
CASES = ("empty_blast", "friendly_only", "clean_cluster", "mixed_blast", "bad_trade", "winning_trade")


def fixture(name):
    if name not in CASES:
        raise ValueError("unknown Fireball fixture")
    state = create_scenario()
    state.board = Board(tuple(Tile() for _ in range(45)))
    state.units = {}
    def add(uid, owner, kind, x, y, hp=None):
        hp = STATS[kind].hp if hp is None else hp
        state.units[uid] = ArenaUnit(uid, owner, kind, Position(x, y), hp,
                                    UnitStatus.ACTIVE if hp else UnitStatus.DOWNED)
    add("mage", "blue", UnitType.MAGE, 2, 2)
    add("enemy", "red", UnitType.KNIGHT, 4, 2,
        4 if name == "winning_trade" else None)
    impact = Position(4, 2)
    if name == "empty_blast":
        impact = Position(2, 0)
    elif name == "friendly_only":
        add("ally", "blue", UnitType.KNIGHT, 2, 0)
        impact = Position(2, 0)
    else:
        if name != "bad_trade":
            add("enemy2", "red", UnitType.MAGE, 4, 3, 4 if name == "winning_trade" else None)
        if name != "clean_cluster":
            add("ally", "blue", UnitType.KNIGHT, 3, 1, 2 if name == "bad_trade" else None)
    state.validate()
    command = ArenaFireball("blue", "mage", impact)
    validate_command(state, command)
    return state, command


def analyze_fireball(state, command):
    """Pure: execute on a copy so damage, bonuses, downs and victory stay authoritative.

    Damage means actual HP removed (clamped), not nominal pre-clamp damage.
    """
    if type(command) is not ArenaFireball:
        raise ValueError("Fireball command required")
    validate_command(state, command)
    affected = arena_fireball_affected_units(state, command.target_position)
    after = deepcopy(state)
    apply_command(after, command)
    result = dict(impact=dict(x=command.target_position.x, y=command.target_position.y),
                  terminal_result=after.winner_player_id,
                  immediate_win=after.winner_player_id == command.actor_id)
    for side, friendly in (("enemy", False), ("friendly", True)):
        ids = [uid for uid in affected if (state.units[uid].owner_id == command.actor_id) == friendly]
        result[side + "_ids"] = ids
        result[side + "_damage"] = sum(state.units[uid].hp-after.units[uid].hp for uid in ids)
        result[side + "_downs"] = [uid for uid in ids if after.units[uid].status is UnitStatus.DOWNED]
    return result
