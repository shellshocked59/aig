"""Explicit deterministic match creation and the one pre-game start transition."""

from dataclasses import dataclass

from aig.state import (
    ControllerType, GameConfig, GameMap, GameState, PlayerState, Position,
    Terrain, ResourceType, TileState, UnitType, _identifier, _validate_city_spacing,
    BarbarianCamp, FactionKind, BARBARIAN_ID,
)


@dataclass(frozen=True)
class PlayerSetup:
    id: str
    controller: ControllerType
    starting_position: Position

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _identifier(self.id, "player setup.id")
        if not isinstance(self.controller, ControllerType):
            raise ValueError("player setup.controller must be a ControllerType")
        if not isinstance(self.starting_position, Position):
            raise ValueError("starting_position must be a Position")


@dataclass(frozen=True)
class GameSetup:
    """Immutable inputs; terrain pairs become independent, unowned live tiles.

    Bounds and tiles are separate, matching GameState. Missing tiles are allowed
    inside bounds, but every starting position must have a passable land tile.
    """

    config: GameConfig
    game_map: GameMap
    tiles: tuple[tuple[Position, Terrain], ...]
    players: tuple[PlayerSetup, ...]
    turn_order: tuple[str, ...]
    resources: tuple[tuple[Position, ResourceType], ...] = ()
    camps: tuple[BarbarianCamp, ...] = ()

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.config, GameConfig) or not isinstance(self.game_map, GameMap):
            raise ValueError("setup requires GameConfig and GameMap")
        if not isinstance(self.players, tuple) or len(self.players) < 2:
            raise ValueError("setup.players must be a tuple of at least two players")
        for player in self.players:
            if not isinstance(player, PlayerSetup):
                raise ValueError("setup.players must contain PlayerSetup values")
            player.validate()
        ids = [player.id for player in self.players]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate setup player ID")
        if not isinstance(self.turn_order, tuple):
            raise ValueError("setup.turn_order must be a tuple")
        for player_id in self.turn_order:
            _identifier(player_id, "setup.turn_order player ID")
        if len(self.turn_order) != len(ids) or set(self.turn_order) != set(ids):
            raise ValueError("turn_order must contain every setup player exactly once")
        if not isinstance(self.tiles, tuple):
            raise ValueError("setup.tiles must be a tuple of (Position, Terrain) pairs")
        terrain_by_position = {}
        for pair in self.tiles:
            if (not isinstance(pair, tuple) or len(pair) != 2
                    or not isinstance(pair[0], Position) or not isinstance(pair[1], Terrain)):
                raise ValueError("setup tile must be a (Position, Terrain) tuple")
            position, terrain = pair
            if not self.game_map.contains(position):
                raise ValueError("setup tile is outside map bounds")
            if position in terrain_by_position:
                raise ValueError("duplicate setup tile position")
            terrain_by_position[position] = terrain
        if not isinstance(self.resources, tuple):
            raise ValueError("setup.resources must be a tuple")
        resources = set()
        for pair in self.resources:
            if (not isinstance(pair, tuple) or len(pair) != 2
                    or not isinstance(pair[0], Position) or not isinstance(pair[1], ResourceType)):
                raise ValueError("setup resource must be a (Position, ResourceType) tuple")
            position, resource = pair
            if position in resources or position not in terrain_by_position:
                raise ValueError("duplicate or missing resource tile")
            TileState(position, terrain_by_position[position], resource=resource)
            resources.add(position)
        starts = []
        for player in self.players:
            position = player.starting_position
            terrain = terrain_by_position.get(position)
            if not self.game_map.contains(position) or terrain is None or not terrain.land_passable:
                raise ValueError("starting position must exist on passable land within map bounds")
            _validate_city_spacing(position, starts)
            starts.append(position)
        if not isinstance(self.camps, tuple):
            raise ValueError("setup.camps must be a tuple")
        ids, positions = set(), set()
        for camp in self.camps:
            if not isinstance(camp, BarbarianCamp):
                raise ValueError("setup camp must be BarbarianCamp")
            terrain = terrain_by_position.get(camp.position)
            if (camp.id in ids or camp.position in positions or camp.position in starts
                    or terrain is None or not terrain.land_passable):
                raise ValueError("duplicate or illegal camp placement")
            ids.add(camp.id)
            positions.add(camp.position)
        if any(p.id == BARBARIAN_ID for p in self.players):
            raise ValueError("reserved system faction ID")


def create_game(setup: GameSetup) -> GameState:
    """Build a detached pre-game state without resolving or starting anything."""
    if not isinstance(setup, GameSetup):
        raise ValueError("setup must be a GameSetup")
    setup.validate()
    state = GameState(
        config=setup.config, game_map=setup.game_map,
        players={p.id: PlayerState(p.id, p.controller) for p in setup.players},
        tiles={position: TileState(position, terrain) for position, terrain in setup.tiles},
        turn_order=list(setup.turn_order),
    )
    for position, resource in setup.resources:
        state.tiles[position].resource = resource
    players = {p.id: p for p in setup.players}
    for player_id in setup.turn_order:
        for unit_type in (UnitType.SETTLER, UnitType.WARRIOR):
            state.add_unit(player_id, unit_type, players[player_id].starting_position)
    if setup.camps:
        state.players[BARBARIAN_ID] = PlayerState(
            BARBARIAN_ID, ControllerType.AI, kind=FactionKind.BARBARIAN,
            researched_technologies=frozenset())
        state.turn_order.append(BARBARIAN_ID)
        state.camps = {c.id: c for c in setup.camps}
        for camp in sorted(setup.camps, key=lambda c: c.id):
            state.add_unit(BARBARIAN_ID, UnitType.WARRIOR, camp.position).home_camp_id = camp.id
    return state


def start_game(state: GameState) -> None:
    """Begin the first activation at turn zero, refreshing only incoming movement."""
    if not isinstance(state, GameState):
        raise ValueError("state must be a GameState")
    state.validate()
    if state.turn != 0 or state.active_player_id is not None:
        raise ValueError("start_game requires a pre-game state at turn zero")
    if len(state.civilization_ids) < 2:
        raise ValueError("start_game requires at least two live factions")
    from aig.knowledge import update_knowledge
    update_knowledge(state)
    state._begin_activation(state.turn_order[0])
