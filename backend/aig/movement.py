"""Deterministic land movement; reusable execution infrastructure, not strategy."""

from collections import deque

from aig.state import GameState, KnownCity, Position, UnitState, UnitType, _identifier


# y increases southward. This tuple alone determines shortest-path tie breaks.
NEIGHBOR_OFFSETS = (
    (0, -1), (1, -1), (1, 0), (1, 1),
    (0, 1), (-1, 1), (-1, 0), (-1, -1),
)


def find_path(state: GameState, unit: UnitState, destination: Position) -> list[Position] | None:
    """Return a shortest path including both endpoints, or None if unreachable.

    BFS considers all eight neighbors in N, NE, E, SE, S, SW, W, NW order.
    Diagonals cost one and may pass between blocked orthogonal neighbors.
    Missing tiles, impassable terrain and enemy units block travel. Undefended
    hostile cities are destinations for capture-capable civilization units only;
    they cannot be intermediate steps. Friendly units and cities do not block.
    Movement budgets and active faction are deliberately ignored. Invalid state,
    non-live units and malformed destinations raise ValueError. No state changes.
    """
    state.validate()
    if not isinstance(unit, UnitState) or state.units.get(unit.id) is not unit:
        raise ValueError("pathfinding requires a live unit from this state")
    if not isinstance(destination, Position):
        raise ValueError("destination must be a Position")
    if not state.can_enter(unit.owner_id, destination, capture_unit_type=unit.unit_type):
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
            # A capture is an entry event, never an invisible intermediate hop.
            if neighbor not in previous and state.can_enter(
                    unit.owner_id, neighbor,
                    capture_unit_type=unit.unit_type if neighbor == destination else None):
                previous[neighbor] = current
                frontier.append(neighbor)
    return None


def move_unit(state: GameState, unit_id: str, destination: Position) -> None:
    """Resolve and validate the entire move before committing position/budget.

    Actor authorization belongs to apply_command; internal rules can use this
    executor independently. Staying on the current tile is rejected as no move.
    """
    state.validate()
    if state.result is not None:
        raise ValueError("game has ended")
    _identifier(unit_id, "unit_id")
    if unit_id not in state.units:
        raise ValueError(f"unknown unit: {unit_id!r}")
    if not isinstance(destination, Position):
        raise ValueError("destination must be a Position")
    unit = state.units[unit_id]
    if not state.game_map.contains(destination):
        raise ValueError("destination is outside map bounds")
    if not state.can_enter(unit.owner_id, destination, capture_unit_type=unit.unit_type):
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
    city = state.city_at(destination)
    from aig.knowledge import visible_positions
    witnesses = ([p for p in state.players if destination in visible_positions(state, p)]
                 if city is not None and city.owner_id != unit.owner_id else [])
    # BFS validated every step; hostile-city entry can only be the destination.
    unit.position = destination
    unit.moves_remaining -= cost
    former_owner = None
    if city is not None and city.owner_id != unit.owner_id:
        former_owner = city.owner_id
        city.owner_id = unit.owner_id
        state.players[unit.owner_id].has_ever_owned_city = True
        state.tiles[destination].owner_id = unit.owner_id
        city.population = max(1, city.population - 1)
        city.food_stored = city.production_stored = 0
        city.production_target = None
        # Factions witnessing the entry learn ownership even if losing this city
        # immediately removes their last sight source at the location.
        for player_id in witnesses:
            if player_id != unit.owner_id:
                knowledge = state.players[player_id].knowledge
                knowledge.explored_positions.add(destination)
                knowledge.discovered_cities[city.id] = KnownCity(city.id, unit.owner_id, destination)
    if not state.is_barbarian(unit.owner_id) and unit.unit_type.combat_strength > 0:
        # Every traversed tile counts as entry; validation above precedes all rewards.
        cleared = [c.id for c in state.camps.values() if c.position in path[1:]]
        for camp_id in cleared:
            del state.camps[camp_id]
        state.players[unit.owner_id].gold += 25 * len(cleared)
    from aig.knowledge import update_knowledge
    update_knowledge(state)
    if former_owner is not None:
        state._eliminate_if_cityless(former_owner)
        update_knowledge(state)
