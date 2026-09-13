"""Small deterministic tactical fixtures for provider comparisons, not scenarios."""

from aig.state import Position as P
from aig.arena.scenarios import create_scenario
from aig.arena.state import ArenaUnit, Board, Tile, Bonus, UnitType as U, UnitStatus as S, STATS

PROBE_VERSION = "arena-tactical-probes-v1"
PROBE_NAMES = ("finish_or_core", "revive_decision", "fireball_friendly_fire", "shield_bash_position",
               "snipe_vs_basic", "winning_core_line", "team_elimination")


def create_probe(name):
    if name not in PROBE_NAMES:
        raise ValueError("unknown Arena tactical probe")
    state = create_scenario()
    state.board = Board(tuple(Tile() for _ in range(45)))
    state.units = {}

    def add(uid, owner, kind, x, y, hp=None):
        hp = STATS[kind].hp if hp is None else hp
        state.units[uid] = ArenaUnit(uid, owner, kind, P(x, y), hp, S.DOWNED if hp == 0 else S.ACTIVE)

    def bonus(x, y, value):
        tiles = list(state.board.tiles)
        tiles[y * 9 + x] = Tile(bonus=value)
        state.board = Board(tuple(tiles))

    if name == "finish_or_core":
        add("actor", "blue", U.KNIGHT, 7, 2)
        add("body", "red", U.MAGE, 7, 1, 0)
        add("enemy", "red", U.CLERIC, 1, 4)
    elif name == "revive_decision":
        add("actor", "blue", U.CLERIC, 2, 2)
        add("ally", "blue", U.MAGE, 3, 2, 0)
        add("enemy", "red", U.KNIGHT, 3, 3)
    elif name == "fireball_friendly_fire":
        add("actor", "blue", U.MAGE, 2, 2)
        add("ally", "blue", U.KNIGHT, 3, 2)
        add("enemy", "red", U.KNIGHT, 4, 1)
        add("enemy2", "red", U.MAGE, 4, 2)
        bonus(3, 2, Bonus.WARD)
    elif name == "shield_bash_position":
        add("actor", "blue", U.KNIGHT, 2, 2)
        add("enemy", "red", U.KNIGHT, 3, 2)
        bonus(3, 2, Bonus.POWER)
    elif name == "snipe_vs_basic":
        add("actor", "blue", U.RANGER, 1, 2)
        add("enemy", "red", U.MAGE, 5, 2, 8)
        add("enemy2", "red", U.KNIGHT, 2, 1)
    elif name == "winning_core_line":
        add("actor", "blue", U.RANGER, 5, 2)
        add("body", "red", U.MAGE, 6, 1, 0)
        add("enemy", "red", U.KNIGHT, 7, 4)
        bonus(5, 2, Bonus.SIEGE)
        state.cores["red-core"].hp = 9
    else:
        # Finish cannot win in valid v2 state: the final ACTIVE down already wins.
        add("actor", "blue", U.KNIGHT, 2, 2)
        add("body", "red", U.MAGE, 3, 1, 0)
        add("enemy", "red", U.KNIGHT, 3, 2, 6)
    state.validate()
    return state
