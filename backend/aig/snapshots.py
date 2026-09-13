"""Version 12 JSON persistence contract, including historical ownership and victory.

Explicit conversion keeps wire formats independent of the domain dataclasses.
Future audience-specific snapshots can have their own types and converters here.
"""

from typing import NotRequired, TypedDict

from aig.state import (
    CityState,
    ControllerType,
    GameConfig,
    GameMap,
    GameState, GameResult, VictoryType,
    PlayerState,
    PlayerKnowledge,
    KnownCity,
    KnownCamp, BarbarianCamp, FactionKind,
    Position,
    TileState,
    ResourceType,
    Terrain,
    Technology,
    UnitState,
    UnitType,
)

SCHEMA_VERSION = 12

JSONValue = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


class PositionData(TypedDict):
    x: int
    y: int


class ConfigData(TypedDict):
    seed: int
    debug_mode: bool


class PlayerData(TypedDict):
    id: str
    controller: str
    kind: str
    eliminated: bool
    has_ever_owned_city: bool
    gold: int
    science_stored: int
    research_target: str | None
    researched_technologies: list[str]
    knowledge: dict


class TileData(TypedDict):
    position: PositionData
    terrain: str
    resource: str | None
    owner_id: str | None


class MapData(TypedDict):
    width: int
    height: int
    origin: PositionData


class OwnedEntityData(TypedDict):
    id: str
    owner_id: str
    position: PositionData


class CityData(OwnedEntityData):
    name: str
    population: int
    food_stored: int
    production_stored: int
    production_target: str | None


class UnitData(OwnedEntityData):
    unit_type: str
    moves_remaining: int
    hp: int
    home_camp_id: str | None


class Snapshot(TypedDict):
    schema_version: int
    config: ConfigData
    turn: int
    turn_order: list[str]
    active_player_id: str | None
    players: list[PlayerData]
    tiles: list[TileData]
    cities: list[CityData]
    units: list[UnitData]
    game_map: MapData
    next_unit_id: int
    camps: list[dict]
    result: dict | None


class SnapshotEnvelope(TypedDict):
    """Optional observations travel beside, and are never restored into, state."""

    snapshot: Snapshot
    observer_data: NotRequired[dict[str, JSONValue]]


def _position_data(position: Position) -> PositionData:
    return {"x": position.x, "y": position.y}


def _owned_data(entity: CityState | UnitState) -> OwnedEntityData:
    return {
        "id": entity.id,
        "owner_id": entity.owner_id,
        "position": _position_data(entity.position),
    }


def to_snapshot(state: GameState) -> Snapshot:
    """Return detached JSON-compatible data; reject structurally invalid state."""
    state.validate()
    return {
        "schema_version": SCHEMA_VERSION,
        "config": {"seed": state.config.seed, "debug_mode": state.config.debug_mode},
        "turn": state.turn,
        "turn_order": list(state.turn_order),
        "active_player_id": state.active_player_id,
        "result": (dict(winner_player_id=state.result.winner_player_id,
                        victory_type=state.result.victory_type.value) if state.result else None),
        "players": [
            {"id": player.id, "controller": player.controller.value, "kind": player.kind.value,
             "eliminated": player.eliminated, "gold": player.gold,
             "has_ever_owned_city": player.has_ever_owned_city,
             "science_stored": player.science_stored,
             "research_target": (player.research_target.value
                                 if player.research_target is not None else None),
             "researched_technologies": sorted(tech.value for tech in player.researched_technologies),
             "knowledge": {
                 "discovered_camps": [dict(id=c.id, position=_position_data(c.position), last_seen_turn=c.last_seen_turn)
                     for c in sorted(player.knowledge.discovered_camps.values(), key=lambda c:c.id)],
                 "explored_positions": [_position_data(p) for p in sorted(
                     player.knowledge.explored_positions, key=lambda p: (p.y, p.x))],
                 "discovered_cities": [dict(city_id=c.city_id, owner_id=c.owner_id,
                                            position=_position_data(c.position))
                                       for c in sorted(player.knowledge.discovered_cities.values(), key=lambda c: c.id)],
             }}
            for player in sorted(state.players.values(), key=lambda player: player.id)
        ],
        "tiles": [
            {"position": _position_data(tile.position), "terrain": tile.terrain.value,
             "owner_id": tile.owner_id, "resource": tile.resource.value if tile.resource else None}
            for tile in sorted(state.tiles.values(), key=lambda tile: (tile.position.y, tile.position.x))
        ],
        "cities": [
            {**_owned_data(city), "name": city.name, "population": city.population,
             "food_stored": city.food_stored, "production_stored": city.production_stored,
             "production_target": (city.production_target.value
                                   if city.production_target is not None else None)}
            for city in sorted(state.cities.values(), key=lambda city: city.id)
        ],
        "units": [
            {**_owned_data(unit), "unit_type": unit.unit_type.value,
             "moves_remaining": unit.moves_remaining, "hp": unit.hp, "home_camp_id": unit.home_camp_id}
            for unit in sorted(state.units.values(), key=lambda unit: unit.id)
        ],
        "game_map": {
            "width": state.game_map.width, "height": state.game_map.height,
            "origin": _position_data(state.game_map.origin),
        },
        "next_unit_id": state.next_unit_id,
        "camps": [dict(id=c.id, position=_position_data(c.position)) for c in sorted(state.camps.values(), key=lambda c:c.id)],
    }


def _record(value: object, fields: set[str], name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    if value.keys() != fields:
        raise ValueError(f"{name} must contain exactly these fields: {', '.join(sorted(fields))}")
    return value


def _records(value: object, fields: set[str], name: str) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    return [_record(item, fields, f"{name}[{index}]") for index, item in enumerate(value)]


def _position(value: object) -> Position:
    data = _record(value, {"x", "y"}, "position")
    return Position(x=data["x"], y=data["y"])


def _knowledge(value: object) -> PlayerKnowledge:
    data = _record(value, {"explored_positions", "discovered_cities", "discovered_camps"}, "knowledge")
    positions = [_position(p) for p in _records(data["explored_positions"], {"x", "y"}, "explored_positions")]
    if len(set(positions)) != len(positions):
        raise ValueError("duplicate explored position")
    cities = {}
    for row in _records(data["discovered_cities"], {"city_id", "owner_id", "position"}, "discovered_cities"):
        city = KnownCity(row["city_id"], row["owner_id"], _position(row["position"]))
        if city.id in cities:
            raise ValueError("duplicate known city")
        cities[city.id] = city
    camps = {}
    for row in _records(data["discovered_camps"], {"id", "position", "last_seen_turn"}, "discovered_camps"):
        camp = KnownCamp(row["id"], _position(row["position"]), row["last_seen_turn"])
        if camp.id in camps:
            raise ValueError("duplicate known camp")
        camps[camp.id] = camp
    return PlayerKnowledge(set(positions), cities, camps)


def from_snapshot(data: object) -> GameState:
    """Restore v12 data, raising ValueError for malformed or unsupported snapshots.

    State invariants are validated; no coercion, migration, ID generation, or
    economy resolution, movement refresh, or activation advancement is performed.
    Unknown fields are rejected to avoid silently losing saved data.
    """
    # Identify old versions before checking the new root shape.
    if not isinstance(data, dict):
        raise ValueError("snapshot must be an object")
    if "schema_version" not in data:
        raise ValueError("snapshot must contain schema_version")
    root = data
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version: {root['schema_version']!r}")
    root = _record(root, set(Snapshot.__required_keys__), "snapshot")
    config = _record(root["config"], {"seed", "debug_mode"}, "config")
    game_config = GameConfig(seed=config["seed"], debug_mode=config["debug_mode"])
    if not isinstance(root["turn_order"], list):
        raise ValueError("turn_order must be an array of player IDs")

    players: dict[str, PlayerState] = {}
    for row in _records(root["players"], set(PlayerData.__required_keys__), "players"):
        if not isinstance(row["controller"], str):
            raise ValueError("player.controller must be 'human' or 'ai'")
        target = row["research_target"]
        if target is not None and not isinstance(target, str):
            raise ValueError("player.research_target must be a technology string or null")
        technologies = row["researched_technologies"]
        if not isinstance(technologies, list) or any(not isinstance(t, str) for t in technologies):
            raise ValueError("player.researched_technologies must be an array of technology strings")
        if len(set(technologies)) != len(technologies):
            raise ValueError("duplicate researched technology")
        knowledge = _knowledge(row["knowledge"])
        player = PlayerState(
            knowledge=knowledge, id=row["id"], controller=ControllerType(row["controller"]), kind=FactionKind(row["kind"]),
            eliminated=row["eliminated"], gold=row["gold"],
            has_ever_owned_city=row["has_ever_owned_city"],
            science_stored=row["science_stored"],
            research_target=Technology(target) if target is not None else None,
            researched_technologies=frozenset(Technology(t) for t in technologies),
        )
        if player.id in players:
            raise ValueError(f"duplicate player ID: {player.id!r}")
        players[player.id] = player

    tiles: dict[Position, TileState] = {}
    for row in _records(root["tiles"], set(TileData.__required_keys__), "tiles"):
        if not isinstance(row["terrain"], str):
            raise ValueError("tile.terrain must be a terrain string")
        tile = TileState(
            position=_position(row["position"]), terrain=Terrain(row["terrain"]),
            owner_id=row["owner_id"],
            resource=ResourceType(row["resource"]) if row["resource"] is not None else None,
        )
        if tile.position in tiles:
            raise ValueError(f"duplicate tile position: {tile.position!r}")
        tiles[tile.position] = tile

    cities: dict[str, CityState] = {}
    for row in _records(root["cities"], set(CityData.__required_keys__), "cities"):
        target = row["production_target"]
        if target is not None and not isinstance(target, str):
            raise ValueError("city.production_target must be a unit type string or null")
        city = CityState(
            id=row["id"], owner_id=row["owner_id"], position=_position(row["position"]),
            name=row["name"], population=row["population"],
            food_stored=row["food_stored"], production_stored=row["production_stored"],
            production_target=UnitType(target) if target is not None else None,
        )
        if city.id in cities:
            raise ValueError(f"duplicate city ID: {city.id!r}")
        cities[city.id] = city

    units: dict[str, UnitState] = {}
    for row in _records(root["units"], set(UnitData.__required_keys__), "units"):
        if not isinstance(row["unit_type"], str):
            raise ValueError("unit.unit_type must be a unit type string")
        unit = UnitState(
            id=row["id"], owner_id=row["owner_id"], position=_position(row["position"]),
            unit_type=UnitType(row["unit_type"]), moves_remaining=row["moves_remaining"], hp=row["hp"],
            home_camp_id=row["home_camp_id"],
        )
        if unit.id in units:
            raise ValueError(f"duplicate unit ID: {unit.id!r}")
        units[unit.id] = unit

    camps = {}
    for row in _records(root["camps"], {"id", "position"}, "camps"):
        camp = BarbarianCamp(row["id"], _position(row["position"]))
        if camp.id in camps:
            raise ValueError("duplicate camp ID")
        camps[camp.id] = camp
    map_data = _record(root["game_map"], {"width", "height", "origin"}, "game_map")
    result = root["result"]
    if result is not None:
        result = _record(result, {"winner_player_id", "victory_type"}, "result")
        result = GameResult(result["winner_player_id"], VictoryType(result["victory_type"]))
    return GameState(
        config=game_config,
        turn=root["turn"],
        turn_order=list(root["turn_order"]),
        active_player_id=root["active_player_id"],
        players=players,
        tiles=tiles,
        cities=cities,
        units=units,
        game_map=GameMap(map_data["width"], map_data["height"], _position(map_data["origin"])),
        next_unit_id=root["next_unit_id"],
        camps=camps,
        result=result,
    )
