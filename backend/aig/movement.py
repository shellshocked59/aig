"""Deterministic land movement; reusable execution infrastructure, not strategy."""

from collections import deque

from aig.state import GameState, Position, UnitState, _identifier


# y increases southward. This tuple alone determines shortest-path tie breaks.
NEIGHBOR_OFFSETS = (
    (0, -1), (1, -1), (1, 0), (1, 1),
    (0, 1), (-1, 1), (-1, 0), (-1, -1),
)


def find_path(state: GameState, unit: UnitState, destination: Position) -> list[Position] | None:
    """Return a shortest path including both endpoints, or None if unreachable.

    BFS considers all eight neighbors in N, NE, E, SE, S, SW, W, NW order.
    Diagonals cost one and may pass between blocked orthogonal neighbors.
    Missing tiles, impassable terrain, enemy units and enemy cities block travel;
    same-owner units and cities do not.
    Movement budgets and active faction are deliberately ignored. Invalid state,
    non-live units and malformed destinations raise ValueError. No state changes.
    """
    state.validate()
    if not isinstance(unit, UnitState) or state.units.get(unit.id) is not unit:
        raise ValueError("pathfinding requires a live unit from this state")
    if not isinstance(destination, Position):
        raise ValueError("destination must be a Position")
    if not state.can_enter(unit.owner_id, destination):
        return None
    frontier = deque([unit.position])
    previous: dict[Position, Position | None] = {unit.position: None}
    while frontier:
        current = frontier.popleft()
        if current == destination:
            path: list[Position] = []
            step: Position | None = current
            while step is not None:
                path.append(step)
                step = previous[step]
            return list(reversed(path))
        for dx, dy in NEIGHBOR_OFFSETS:
            neighbor = Position(current.x + dx, current.y + dy)
            if neighbor not in previous and state.can_enter(unit.owner_id, neighbor):
                previous[neighbor] = current
                frontier.append(neighbor)
    return None


def move_unit(state: GameState, unit_id: str, destination: Position) -> None:
    """Resolve and validate the entire move before committing position/budget.

    Actor authorization belongs to apply_command; internal rules can use this
    executor independently. Staying on the current tile is rejected as no move.
    """
    state.validate()
    _identifier(unit_id, "unit_id")
    if unit_id not in state.units:
        raise ValueError(f"unknown unit: {unit_id!r}")
    if not isinstance(destination, Position):
        raise ValueError("destination must be a Position")
    unit = state.units[unit_id]
    if not state.game_map.contains(destination):
        raise ValueError("destination is outside map bounds")
    if not state.can_enter(unit.owner_id, destination):
        raise ValueError("destination is impassable or enemy-occupied")
    if destination == unit.position:
        raise ValueError("destination is the unit's current position")
    if unit.moves_remaining == 0:
        raise ValueError("unit has no movement remaining")
    path = find_path(state, unit, destination)
    if path is None:
        raise ValueError("destination is unreachable")
    cost = len(path) - 1
    if cost > unit.moves_remaining:
        raise ValueError("insufficient movement remaining")
    # BFS validated every step; no intermediate events exist in this slice.
    unit.position = destination
    unit.moves_remaining -= cost
