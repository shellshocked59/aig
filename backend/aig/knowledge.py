"""Authoritative sight and persistent discovery; queries never reveal or mutate."""

from aig.state import GameMap, GameState, KnownCity, KnownCamp, Position, UnitType


def vision_range(unit_type: UnitType) -> int:
    return 3 if unit_type is UnitType.SCOUT else 2


def vision_positions(game_map: GameMap, center: Position, radius: int) -> set[Position]:
    return {Position(x, y)
            for y in range(max(game_map.origin.y, center.y - radius),
                           min(game_map.origin.y + game_map.height, center.y + radius + 1))
            for x in range(max(game_map.origin.x, center.x - radius),
                           min(game_map.origin.x + game_map.width, center.x + radius + 1))}


def visible_positions(state: GameState, player_id: str) -> set[Position]:
    if state.players[player_id].eliminated:
        return set()
    sources = [(u.position, vision_range(u.unit_type)) for u in state.units.values()
               if u.owner_id == player_id]
    sources += [(c.position, 2) for c in state.cities.values() if c.owner_id == player_id]
    if state.is_barbarian(player_id):
        sources += [(c.position, 2) for c in state.camps.values()]
    return set().union(*(vision_positions(state.game_map, p, r) for p, r in sources))


def is_visible(state: GameState, player_id: str, position: Position) -> bool:
    return position in visible_positions(state, player_id)


def is_explored(state: GameState, player_id: str, position: Position) -> bool:
    return position in state.players[player_id].knowledge.explored_positions


def visible_enemy_units(state: GameState, player_id: str):
    visible = visible_positions(state, player_id)
    return sorted((u for u in state.units.values()
                   if u.owner_id != player_id and u.position in visible), key=lambda u: u.id)


def known_enemy_cities(state: GameState, player_id: str) -> list[dict]:
    """Hidden existence is unknown, including removal: live_exists is null.

    Once the remembered location is visible, an empty site returns false.
    Historical records remain intact and never dereference a missing live ID.
    """
    visible = visible_positions(state, player_id)
    known = dict(state.players[player_id].knowledge.discovered_cities)
    for city in state.cities.values():
        if city.owner_id != player_id and city.position in visible:
            known[city.id] = KnownCity(city.id, city.owner_id, city.position)
    result = []
    for city in sorted(known.values(), key=lambda c: c.id):
        seen = city.position in visible
        live = state.cities.get(city.id) if seen else None
        if live is not None and live.owner_id == player_id:
            continue
        row = dict(id=city.id, owner_id=city.owner_id, x=city.position.x, y=city.position.y,
                   currently_visible=seen, live_exists=(live is not None) if seen else None)
        if live is not None:
            row.update(owner_id=live.owner_id, population=live.population,
                       production=live.production_target.value if live.production_target else None)
        result.append(row)
    return result


def update_knowledge(state: GameState) -> None:
    """After domain mutations, all factions observe their resulting sight."""
    for player_id, player in state.players.items():
        visible = visible_positions(state, player_id)
        player.knowledge.explored_positions.update(visible)
        for camp in list(player.knowledge.discovered_camps.values()):
            if camp.position in visible and camp.id not in state.camps:
                del player.knowledge.discovered_camps[camp.id]
        for camp in state.camps.values():
            if camp.position in visible:
                player.knowledge.discovered_camps[camp.id] = KnownCamp(camp.id, camp.position, state.turn)
        for city in state.cities.values():
            if city.owner_id == player_id:
                player.knowledge.discovered_cities.pop(city.id, None)
            if city.owner_id != player_id and city.position in visible:
                player.knowledge.discovered_cities[city.id] = KnownCity(city.id, city.owner_id, city.position)


def known_camps(state: GameState, player_id: str) -> list[dict]:
    """Remembered presence is historical; hidden current existence is unknown."""
    visible = visible_positions(state, player_id) if state.active_player_id is not None else set()
    return [dict(id=c.id, x=c.position.x, y=c.position.y, last_seen_turn=c.last_seen_turn,
                 currently_visible=c.position in visible,
                 live_exists=(c.id in state.camps) if c.position in visible else None)
            for c in sorted(state.players[player_id].knowledge.discovered_camps.values(), key=lambda c: c.id)]


def known_resources(state: GameState, player_id: str) -> list[dict]:
    """Static discoveries, with ownership only where independently valid knowledge."""
    from dataclasses import asdict
    from aig.economy import resource_yields
    visible = visible_positions(state, player_id)
    cities = [c for c in state.cities.values() if c.owner_id == player_id]
    return [dict(type=t.resource.value, position=dict(x=p.x, y=p.y),
                 bonus_yields=asdict(resource_yields(t.resource)),
                 ownerId=t.owner_id if p in visible or t.owner_id == player_id else None,
                 inside_own_city_radius=any(max(abs(p.x-c.position.x), abs(p.y-c.position.y)) <= 1
                                            for c in cities))
            for p in sorted(state.players[player_id].knowledge.explored_positions, key=lambda p: (p.y, p.x))
            if (t := state.tiles.get(p)) is not None and t.resource is not None]


def military_strength(units) -> int:
    return sum(max(u.unit_type.combat_strength, u.unit_type.ranged_strength or 0) * u.hp // 100
               for u in units)
