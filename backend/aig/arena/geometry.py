"""Integer-only Arena geometry. Entities never obstruct line of sight."""

from aig.state import Position
from aig.arena.state import Terrain


def distance(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))


def arena_line_of_sight(board, start, end):
    """Center-to-center supercover, excluding endpoints.

    At an exact grid-corner crossing both side cells are touched and checked.
    Integer cross products make the result symmetric and platform-independent.
    A blocked impact tile is allowed; out-of-board endpoints are not.
    """
    if not board.contains(start) or not board.contains(end):
        return False
    x, y = start.x, start.y
    nx, ny = abs(end.x - x), abs(end.y - y)
    sx, sy = (1 if end.x > x else -1), (1 if end.y > y else -1)
    ix = iy = 0

    def clear(px, py):
        p = Position(px, py)
        return p in (start, end) or board.at(p).terrain is not Terrain.BLOCKED

    while ix < nx or iy < ny:
        cross = (1 + 2 * ix) * ny - (1 + 2 * iy) * nx
        if cross == 0:
            if not clear(x + sx, y) or not clear(x, y + sy):
                return False
            x, y, ix, iy = x + sx, y + sy, ix + 1, iy + 1
        elif cross < 0:
            x, ix = x + sx, ix + 1
        else:
            y, iy = y + sy, iy + 1
        if not clear(x, y):
            return False
    return True


def can_step(state, start, end):
    if distance(start, end) != 1 or not state.can_enter(end):
        return False
    if start.x != end.x and start.y != end.y:
        return all(state.board.at(p).terrain is not Terrain.BLOCKED for p in
                   (Position(start.x, end.y), Position(end.x, start.y)))
    return True
