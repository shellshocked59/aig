"""Filtered command-choice inputs. No hidden state is retained by this view.

Known terrain only is traversable for planning. Frontiers approach unseen space
from known tiles; every issued step is adjacent, so sight precedes entry. The
engine pathfinder remains unchanged and validates the actual command separately.
"""

from dataclasses import dataclass, replace

from aig.knowledge import known_enemy_cities, known_camps, visible_positions, vision_positions, vision_range
from aig.movement import find_path
from aig.state import GameState, KnownCity, Position, PlayerState


@dataclass
class PlanningView:
    game_map: object
    players: dict
    tiles: dict
    cities: dict
    units: dict
    explored: frozenset
    camps: dict

    # These pure rule queries read only the filtered collections above.
    can_enter = GameState.can_enter
    _validate_city_placement = GameState._validate_city_placement

    def validate(self):
        # The source is validated at the executor boundary. Remembered cities
        # are intentionally historical records, not live simulation entities.
        pass


def planning_view(state: GameState, actor: str) -> PlanningView:
    visible = visible_positions(state, actor)
    explored = frozenset(state.players[actor].knowledge.explored_positions | visible)
    cities = {c.id: c for c in state.cities.values() if c.owner_id == actor or c.position in visible}
    for row in known_enemy_cities(state, actor):
        if row['id'] not in cities and row['live_exists'] is not False:
            cities[row['id']] = KnownCity(row['id'], row['owner_id'], Position(row['x'], row['y']))
    return PlanningView(
        state.game_map, {p: player if p == actor else PlayerState(
            p, player.controller, eliminated=player.eliminated, kind=player.kind,
            researched_technologies=player.researched_technologies)
            for p, player in state.players.items()},
        {p: replace(t, owner_id=t.owner_id if p in visible or t.owner_id == actor else None)
         for p, t in state.tiles.items() if p in explored},
        cities, {u.id: u if u.owner_id == actor else replace(u, home_camp_id=None)
                 for u in state.units.values() if u.owner_id == actor or u.position in visible},
        explored,
        {c.id: c for c in state.players[actor].knowledge.discovered_camps.values()},
    )


def exploration_path(view: PlanningView, unit) -> list[Position] | None:
    """Prefer expected reveal, then travel distance and stable coordinates.

    Estimate only bounded coordinate geometry, never unknown terrain values.
    Candidates have a known route; no failed authoritative query ranks them.
    """
    candidates = []
    radius = vision_range(unit.unit_type)
    for position in view.tiles:
        if position == unit.position:
            continue
        reveal = len(vision_positions(view.game_map, position, radius) - view.explored)
        if reveal and view.can_enter(unit.owner_id, position):
            candidates.append((-reveal, position.y, position.x, position))
    # Try highest reveal groups first; rank reachable ties by path length.
    best = None
    for negative_reveal, y, x, position in sorted(candidates):
        if best is not None and negative_reveal > best[0][0]:
            break
        path = find_path(view, unit, position)
        if path is not None:
            rank = (negative_reveal, len(path), y, x)
            if best is None or rank < best[0]:
                best = rank, path
    return best[1] if best else None
