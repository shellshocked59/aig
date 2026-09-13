"""Original left/right mirrored setup; stable IDs, no random draws."""

from aig.state import Position
from aig.arena.v1.state import (ArenaCore, ArenaPlayer, ArenaState, ArenaUnit, Board,
                             Bonus, SCENARIO_VERSION, STATS, Terrain, Tile, UnitType)


def create_scenario(version=SCENARIO_VERSION):
    if version != SCENARIO_VERSION:
        raise ValueError("unknown Arena scenario")
    blocked = {(3, 1), (5, 1), (3, 3), (5, 3)}
    bonuses = {(4, 0): Bonus.POWER, (4, 4): Bonus.POWER,
               (2, 2): Bonus.WARD, (6, 2): Bonus.WARD,
               (3, 2): Bonus.SIEGE, (5, 2): Bonus.SIEGE}
    board = Board(tuple(Tile(Terrain.BLOCKED if (x, y) in blocked else Terrain.FLOOR,
                             bonuses.get((x, y))) for y in range(5) for x in range(9)))
    players = (ArenaPlayer("blue", "Blue Team"), ArenaPlayer("red", "Red Team"))
    units = {}
    for player, x in (("blue", 1), ("red", 7)):
        for kind, y in zip(UnitType, (1, 0, 3, 4)):
            uid = f"{player}-{kind.value}"
            units[uid] = ArenaUnit(uid, player, kind, Position(x, y), STATS[kind].hp)
    cores = {f"{p}-core": ArenaCore(f"{p}-core", p, Position(x, 2))
             for p, x in (("blue", 0), ("red", 8))}
    return ArenaState(board, players, units, cores, "blue")
