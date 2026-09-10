"""Explicit, detached UI read model. This is not the persistence snapshot format."""

from aig.production import production_cost, production_remaining
from aig.research import (
    available_technologies, research_remaining, technology_cost, unit_is_unlocked,
)
from aig.state import GameState, UnitType


def public_state(state: GameState) -> dict:
    return {
        "game": {
            "turn": state.turn,
            "activePlayerId": state.active_player_id,
            "status": ("started" if state.active_player_id is not None
                       else "terminal" if len(state.turn_order) < 2 else "pre_game"),
        },
        "players": [{
            "id": player.id,
            "controller": player.controller.value,
            "eliminated": player.eliminated,
            "gold": player.gold,
            "scienceStored": player.science_stored,
            "researchTarget": player.research_target,
            "researchedTechnologies": sorted(t.value for t in player.researched_technologies),
            "availableResearch": [{"technology": t.value, "cost": technology_cost(t)}
                                  for t in available_technologies(player)],
            "researchCost": (technology_cost(player.research_target)
                             if player.research_target is not None else None),
            "researchRemaining": research_remaining(player),
        } for player in sorted(state.players.values(), key=lambda p: p.id)],
        "map": {
            "width": state.game_map.width,
            "height": state.game_map.height,
            "origin": {"x": state.game_map.origin.x, "y": state.game_map.origin.y},
            "tiles": [{
                "x": tile.position.x, "y": tile.position.y,
                "terrain": tile.terrain.value, "ownerId": tile.owner_id,
            } for tile in sorted(state.tiles.values(),
                                 key=lambda t: (t.position.y, t.position.x))],
        },
        "units": [{
            "id": unit.id, "ownerId": unit.owner_id, "type": unit.unit_type.value,
            "x": unit.position.x, "y": unit.position.y,
            "hp": unit.hp, "movesRemaining": unit.moves_remaining,
            "maxMovement": unit.unit_type.movement_allowance,
            "attackRange": unit.unit_type.attack_range,
        } for unit in sorted(state.units.values(), key=lambda u: u.id)],
        "cities": [{
            "id": city.id, "ownerId": city.owner_id, "name": city.name,
            "x": city.position.x, "y": city.position.y,
            "population": city.population, "foodStored": city.food_stored,
            "productionStored": city.production_stored,
            "productionTarget": city.production_target,
            "availableProduction": [{"unitType": t.value, "cost": production_cost(t)}
                                    for t in UnitType
                                    if unit_is_unlocked(state.players[city.owner_id], t)],
            "productionCost": (production_cost(city.production_target)
                               if city.production_target is not None else None),
            "productionRemaining": production_remaining(city),
        } for city in sorted(state.cities.values(), key=lambda c: c.id)],
    }
