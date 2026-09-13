"""Explicit, detached UI read model. This is not the persistence snapshot format."""

from aig.knowledge import known_enemy_cities, military_strength, visible_positions, known_camps
from aig.state import ControllerType, Position
from aig.production import production_cost, production_remaining
from aig.research import (
    available_technologies, research_remaining, technology_cost, unit_is_unlocked,
)
from aig.state import GameState, UnitType


def observer_state(state: GameState) -> dict:
    """Explicit omniscient backend/debug DTO; never the normal HTTP response."""
    return {
        "barbarianCamps": [dict(id=c.id, x=c.position.x, y=c.position.y) for c in sorted(state.camps.values(), key=lambda c:c.id)],
        "game": {
            "terminal": state.result is not None,
            "winnerPlayerId": state.result.winner_player_id if state.result else None,
            "victoryType": state.result.victory_type.value if state.result else None,
            "turn": state.turn,
            "activePlayerId": state.active_player_id,
            "status": ("started" if state.active_player_id is not None
                       else "terminal" if len(state.civilization_ids) < 2 else "pre_game"),
        },
        "players": [{
            "id": player.id, "kind": player.kind.value,
            "controller": player.controller.value,
            "eliminated": player.eliminated,
            "hasEverOwnedCity": player.has_ever_owned_city,
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
                "resource": tile.resource.value if tile.resource else None,
            } for tile in sorted(state.tiles.values(),
                                 key=lambda t: (t.position.y, t.position.x))],
        },
        "units": [{
            "id": unit.id, "ownerId": unit.owner_id, "type": unit.unit_type.value,
            "barbarian": state.is_barbarian(unit.owner_id), "homeCampId": unit.home_camp_id,
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


def public_state(state: GameState) -> dict:
    """Active human perspective; pre-game/terminal use the first human in ID order.

    AI-only games have no browser perspective and return no spatial knowledge.
    Scoreboard research/economy remain intentionally global as in V1.
    """
    humans = sorted(p.id for p in state.players.values() if p.controller is ControllerType.HUMAN)
    actor = state.active_player_id if state.active_player_id in humans else next(iter(humans), None)
    visible = visible_positions(state, actor) if actor and state.active_player_id is not None else set()
    explored = state.players[actor].knowledge.explored_positions if actor else set()
    result = observer_state(state)
    result["viewerPlayerId"] = actor
    result["players"] = [p for p in result["players"] if not state.is_barbarian(p["id"])]
    result["barbarianCamps"] = known_camps(state, actor) if actor else []
    for unit in result["units"]:
        unit.pop("homeCampId")
    for player in result["players"]:
        player["globalMilitaryStrength"] = military_strength(u for u in state.units.values() if u.owner_id == player["id"])
    # Rectangle geometry is public; the presence of an unseen sparse-map tile is
    # not. Emit every coordinate, so hidden holes cannot reveal passability.
    tiles_by_position = {(t["x"], t["y"]): t for t in result["map"]["tiles"]}
    result["map"]["tiles"] = [tiles_by_position.get((x, y), dict(
        x=x, y=y, terrain=None, resource=None, ownerId=None))
        for y in range(state.game_map.origin.y, state.game_map.origin.y + state.game_map.height)
        for x in range(state.game_map.origin.x, state.game_map.origin.x + state.game_map.width)]
    for tile in result["map"]["tiles"]:
        position = Position(tile["x"], tile["y"])
        tile.update(explored=position in explored, visible=position in visible)
        if position not in explored:
            tile["terrain"] = None
            tile["resource"] = None
        if position not in visible and tile["ownerId"] != actor:
            tile["ownerId"] = None
    result["units"] = [u for u in result["units"] if u["ownerId"] == actor
                       or Position(u["x"], u["y"]) in visible]
    live_cities = {c["id"]: c for c in result["cities"]}
    result["cities"] = [c for c in live_cities.values() if c["ownerId"] == actor]
    if actor and state.active_player_id is not None:
        for city in known_enemy_cities(state, actor):
            if city["currently_visible"] and city["live_exists"]:
                record = live_cities[city["id"]]
            else:
                record = dict(id=city["id"], ownerId=city["owner_id"], x=city["x"], y=city["y"])
            result["cities"].append(dict(record, currentlyVisible=city["currently_visible"],
                                         liveExists=city["live_exists"]))
    elif actor:
        for city in sorted(state.players[actor].knowledge.discovered_cities.values(), key=lambda c: c.id):
            result["cities"].append(dict(id=city.id, ownerId=city.owner_id, x=city.position.x,
                                         y=city.position.y, currentlyVisible=False, liveExists=None))
    result["cities"].sort(key=lambda c: c["id"])
    return result
