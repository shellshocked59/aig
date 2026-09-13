"""Authoritative mutable state with validation and faction activation transitions."""

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from collections.abc import Iterable


MAX_UNIT_HP = 100


class _DefaultMovement(Enum):
    ALLOWANCE = "allowance"


def _integer(value: object, name: str, *, minimum: int | None = None) -> None:
    # bool is an int subclass, but is not a valid coordinate, seed, or counter.
    if type(value) is not int or (minimum is not None and value < minimum):
        suffix = f" >= {minimum}" if minimum is not None else ""
        raise ValueError(f"{name} must be an integer{suffix}")


def _identifier(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


class ControllerType(StrEnum):
    HUMAN = "human"
    AI = "ai"


class FactionKind(StrEnum):
    CIVILIZATION = "civilization"
    BARBARIAN = "barbarian"


class VictoryType(StrEnum):
    CONQUEST = "conquest"


@dataclass(frozen=True)
class GameResult:
    winner_player_id: str
    victory_type: VictoryType = VictoryType.CONQUEST

    def __post_init__(self):
        _identifier(self.winner_player_id, "winner_player_id")
        if not isinstance(self.victory_type, VictoryType):
            raise ValueError("victory_type must be a VictoryType")


def are_hostile(a: "PlayerState", b: "PlayerState") -> bool:
    """Permanent total war; the barbarian system is one friendly faction."""
    return a.id != b.id and not (a.kind is b.kind is FactionKind.BARBARIAN)


BARBARIAN_ID = "barbarians"


class Terrain(StrEnum):
    GRASSLAND = "grassland"
    PLAINS = "plains"
    FOREST = "forest"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    WATER = "water"

    @property
    def land_passable(self) -> bool:
        return self not in (Terrain.MOUNTAINS, Terrain.WATER)


class ResourceType(StrEnum):
    WHEAT = "wheat"
    CATTLE = "cattle"
    IRON = "iron"
    GEMS = "gems"
    SPICES = "spices"


class UnitType(StrEnum):
    SETTLER = "settler"
    SCOUT = "scout"
    WARRIOR = "warrior"
    ARCHER = "archer"
    SPEARMAN = "spearman"

    @property
    def production_cost(self) -> int:
        return {
            UnitType.WARRIOR: 20,
            UnitType.SCOUT: 20,
            UnitType.ARCHER: 30,
            UnitType.SPEARMAN: 30,
            UnitType.SETTLER: 40,
        }[self]

    @property
    def movement_allowance(self) -> int:
        return 2 if self in (UnitType.SETTLER, UnitType.SCOUT) else 1

    @property
    def combat_strength(self) -> int:
        return {
            UnitType.SETTLER: 0,
            UnitType.SCOUT: 10,
            UnitType.WARRIOR: 20,
            UnitType.SPEARMAN: 25,
            UnitType.ARCHER: 10,
        }[self]

    @property
    def ranged_strength(self) -> int | None:
        return 20 if self is UnitType.ARCHER else None

    @property
    def can_capture(self) -> bool:
        return self.combat_strength > 0 and self.ranged_strength is None

    @property
    def attack_range(self) -> int:
        if self is UnitType.SETTLER:
            return 0
        return 2 if self is UnitType.ARCHER else 1


class Technology(StrEnum):
    AGRICULTURE = "agriculture"
    ARCHERY = "archery"
    BRONZE_WORKING = "bronze_working"

    @property
    def science_cost(self) -> int:
        return {Technology.AGRICULTURE: 0, Technology.ARCHERY: 15,
                Technology.BRONZE_WORKING: 20}[self]

    @property
    def prerequisites(self) -> frozenset["Technology"]:
        return (frozenset() if self is Technology.AGRICULTURE
                else frozenset({Technology.AGRICULTURE}))


@dataclass(frozen=True)
class Position:
    """Integer tile coordinates; no bounds or grid topology are assumed."""

    x: int
    y: int

    def __post_init__(self) -> None:
        _integer(self.x, "position.x")
        _integer(self.y, "position.y")


def _validate_city_spacing(position: Position, others: Iterable[Position]) -> None:
    for other in others:
        if position == other:
            raise ValueError("only one city may occupy a tile")
        if max(abs(position.x - other.x), abs(position.y - other.y)) < 3:
            raise ValueError("city centers must be at least Chebyshev distance 3 apart")


@dataclass(frozen=True)
class GameMap:
    """Finite square-grid bounds; tile data stays in GameState.tiles.

    An explicit origin supports existing negative coordinates. Empty bounds are
    useful for roster-only setup. Missing tiles inside bounds are not traversable.
    """

    width: int = 0
    height: int = 0
    origin: Position = Position(0, 0)

    def __post_init__(self) -> None:
        _integer(self.width, "map.width", minimum=0)
        _integer(self.height, "map.height", minimum=0)
        if (self.width == 0) != (self.height == 0):
            raise ValueError("empty map must have both dimensions zero")
        if not isinstance(self.origin, Position):
            raise ValueError("map.origin must be a Position")

    def contains(self, position: Position) -> bool:
        return (
            self.origin.x <= position.x < self.origin.x + self.width
            and self.origin.y <= position.y < self.origin.y + self.height
        )


@dataclass(frozen=True)
class GameConfig:
    """Per-game configuration, separate from mutable state and static definitions."""

    seed: int
    debug_mode: bool = False

    def __post_init__(self) -> None:
        _integer(self.seed, "config.seed")
        if type(self.debug_mode) is not bool:
            raise ValueError("config.debug_mode must be a boolean")


@dataclass(frozen=True)
class KnownCity:
    city_id: str
    owner_id: str
    position: Position

    def __post_init__(self) -> None:
        _identifier(self.city_id, "known city.id")
        _identifier(self.owner_id, "known city.owner_id")
        if not isinstance(self.position, Position):
            raise ValueError("known city.position must be a Position")

    @property
    def id(self) -> str:
        return self.city_id


@dataclass(frozen=True)
class BarbarianCamp:
    id: str
    position: Position

    def __post_init__(self):
        self.validate()

    def validate(self):
        _identifier(self.id, "camp.id")
        if not isinstance(self.position, Position):
            raise ValueError("camp.position must be a Position")


@dataclass(frozen=True)
class KnownCamp:
    id: str
    position: Position
    last_seen_turn: int

    def __post_init__(self):
        BarbarianCamp(self.id, self.position)
        _integer(self.last_seen_turn, "camp.last_seen_turn", minimum=0)


@dataclass
class PlayerKnowledge:
    explored_positions: set[Position] = field(default_factory=set)
    discovered_cities: dict[str, KnownCity] = field(default_factory=dict)
    discovered_camps: dict[str, "KnownCamp"] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.discovered_camps, dict):
            raise ValueError("discovered_camps must be a dictionary")
        for key, camp in self.discovered_camps.items():
            if not isinstance(camp, KnownCamp) or key != camp.id:
                raise ValueError("discovered_camps must map IDs to KnownCamp")
        if not isinstance(self.explored_positions, set) or any(
                not isinstance(p, Position) for p in self.explored_positions):
            raise ValueError("explored_positions must be a set of Position")
        if not isinstance(self.discovered_cities, dict) or any(
                not isinstance(c, KnownCity) or key != c.city_id
                for key, c in self.discovered_cities.items()):
            raise ValueError("discovered_cities must map IDs to KnownCity")


@dataclass
class PlayerState:
    id: str
    controller: ControllerType
    eliminated: bool = False
    has_ever_owned_city: bool = field(default=False, kw_only=True)
    kind: FactionKind = field(default=FactionKind.CIVILIZATION, kw_only=True)
    gold: int = 0
    science_stored: int = 0
    research_target: Technology | None = None
    knowledge: PlayerKnowledge = field(default_factory=PlayerKnowledge)
    researched_technologies: frozenset[Technology] = field(
        default_factory=lambda: frozenset({Technology.AGRICULTURE}),
    )

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _identifier(self.id, "player.id")
        if type(self.has_ever_owned_city) is not bool:
            raise ValueError("player.has_ever_owned_city must be a boolean")
        if not isinstance(self.kind, FactionKind):
            raise ValueError("player.kind must be a FactionKind")
        if self.id == BARBARIAN_ID and self.kind is not FactionKind.BARBARIAN:
            raise ValueError("reserved system faction ID")
        if self.kind is FactionKind.BARBARIAN and (
                self.id != BARBARIAN_ID or self.controller is not ControllerType.AI
                or self.gold or self.science_stored or self.research_target is not None
                or self.researched_technologies or self.eliminated or self.has_ever_owned_city):
            raise ValueError("barbarian system faction cannot have civilization state")
        if not isinstance(self.knowledge, PlayerKnowledge):
            raise ValueError("player.knowledge must be PlayerKnowledge")
        self.knowledge.validate()
        if not isinstance(self.controller, ControllerType):
            raise ValueError("player.controller must be a ControllerType")
        if type(self.eliminated) is not bool:
            raise ValueError("player.eliminated must be a boolean")
        _integer(self.gold, "player.gold", minimum=0)
        _integer(self.science_stored, "player.science_stored", minimum=0)
        if (not isinstance(self.researched_technologies, frozenset)
                or any(not isinstance(tech, Technology) for tech in self.researched_technologies)):
            raise ValueError("player.researched_technologies must be a frozenset of Technology")
        if self.research_target is not None:
            if not isinstance(self.research_target, Technology):
                raise ValueError("player.research_target must be a Technology or None")
            if self.research_target in self.researched_technologies:
                raise ValueError("research target is already researched")
            if not self.research_target.prerequisites <= self.researched_technologies:
                raise ValueError("research target prerequisites are not satisfied")


@dataclass
class TileState:
    position: Position
    terrain: Terrain = Terrain.GRASSLAND
    owner_id: str | None = None
    resource: ResourceType | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.position, Position):
            raise ValueError("tile.position must be a Position")
        if not isinstance(self.terrain, Terrain):
            raise ValueError("tile.terrain must be a Terrain")
        if self.resource is not None:
            if not isinstance(self.resource, ResourceType):
                raise ValueError("tile.resource must be a ResourceType or None")
            if not self.terrain.land_passable:
                raise ValueError("resources require workable land terrain")
        if self.owner_id is not None:
            _identifier(self.owner_id, "tile.owner_id")


@dataclass
class CityState:
    id: str
    owner_id: str
    position: Position
    name: str = field(kw_only=True)
    population: int = field(default=1, kw_only=True)
    food_stored: int = field(default=0, kw_only=True)
    production_stored: int = field(default=0, kw_only=True)
    production_target: UnitType | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        _identifier(self.id, "city.id")
        _identifier(self.owner_id, "city.owner_id")
        _identifier(self.name, "city.name")
        _integer(self.population, "city.population", minimum=1)
        _integer(self.food_stored, "city.food_stored", minimum=0)
        _integer(self.production_stored, "city.production_stored", minimum=0)
        if self.production_target is not None and not isinstance(self.production_target, UnitType):
            raise ValueError("city.production_target must be a UnitType or None")
        if not isinstance(self.position, Position):
            raise ValueError("city.position must be a Position")


@dataclass(init=False)
class UnitState:
    id: str
    owner_id: str
    position: Position
    unit_type: UnitType = UnitType.WARRIOR
    moves_remaining: int = field(kw_only=True)
    hp: int = field(default=MAX_UNIT_HP, kw_only=True)
    home_camp_id: str | None = field(default=None, kw_only=True)

    def __init__(
        self, id: str, owner_id: str, position: Position,
        unit_type: UnitType = UnitType.WARRIOR, *,
        moves_remaining: int | _DefaultMovement = _DefaultMovement.ALLOWANCE,
        hp: int = MAX_UNIT_HP,
        home_camp_id: str | None = None,
    ) -> None:
        self.id = id
        self.owner_id = owner_id
        self.position = position
        self.unit_type = unit_type
        self.hp = hp
        self.home_camp_id = home_camp_id
        if not isinstance(unit_type, UnitType):
            raise ValueError("unit.unit_type must be a UnitType")
        self.moves_remaining = (
            unit_type.movement_allowance
            if moves_remaining is _DefaultMovement.ALLOWANCE else moves_remaining
        )
        self.validate()

    def validate(self) -> None:
        _identifier(self.id, "unit.id")
        if self.home_camp_id is not None:
            _identifier(self.home_camp_id, "unit.home_camp_id")
        _identifier(self.owner_id, "unit.owner_id")
        if not isinstance(self.position, Position):
            raise ValueError("unit.position must be a Position")
        if not isinstance(self.unit_type, UnitType):
            raise ValueError("unit.unit_type must be a UnitType")
        _integer(self.moves_remaining, "unit.moves_remaining", minimum=0)
        if self.moves_remaining > self.unit_type.movement_allowance:
            raise ValueError("unit.moves_remaining exceeds movement allowance")
        _integer(self.hp, "unit.hp", minimum=1)
        if self.hp > MAX_UNIT_HP:
            raise ValueError("unit.hp exceeds maximum HP")


@dataclass
class GameState:
    """Sequential faction activation state; no activation executor is provided.

    turn is the global game turn, initially zero. It increments only after the
    final live faction (the system phase, when present) completes its activation.
    With fewer than two civilization survivors, active_player_id must be None. Pre-game
    states also allow no active player at turn zero.
    """

    config: GameConfig
    turn: int = 0
    turn_order: list[str] = field(default_factory=list)
    active_player_id: str | None = None
    players: dict[str, PlayerState] = field(default_factory=dict)
    tiles: dict[Position, TileState] = field(default_factory=dict)
    cities: dict[str, CityState] = field(default_factory=dict)
    units: dict[str, UnitState] = field(default_factory=dict)
    game_map: GameMap = field(default_factory=GameMap)
    next_unit_id: int = 1
    camps: dict[str, BarbarianCamp] = field(default_factory=dict)
    result: GameResult | None = None

    @property
    def civilization_ids(self) -> list[str]:
        return [p for p in self.turn_order if self.players[p].kind is FactionKind.CIVILIZATION]

    def is_barbarian(self, player_id: str) -> bool:
        return self.players[player_id].kind is FactionKind.BARBARIAN

    def __post_init__(self) -> None:
        self.validate()

    @property
    def active_controller(self) -> ControllerType | None:
        """Derived from the active player, never a second authoritative value."""
        if self.active_player_id is None:
            return None
        return self.players[self.active_player_id].controller

    def finish_activation(self) -> None:
        """Advance once without economy; reject states with no activation."""
        self.validate()
        if self.active_player_id is None:
            raise ValueError("no active activation to finish")
        next_index = self.turn_order.index(self.active_player_id) + 1
        if next_index == len(self.turn_order):
            self.turn += 1
            next_index = 0
        self._begin_activation(self.turn_order[next_index])

    def _begin_activation(self, player_id: str) -> None:
        """Called only for an actual transition, never construction or restore."""
        self.active_player_id = player_id
        for unit in self.units.values():
            if unit.owner_id == player_id:
                unit.moves_remaining = unit.unit_type.movement_allowance
        if self.is_barbarian(player_id):
            from aig.barbarians import spawn_replacements
            spawn_replacements(self)

    def add_unit(self, owner_id: str, unit_type: UnitType, position: Position) -> UnitState:
        """Place a fresh live unit during setup/rules, with a deterministic ID."""
        self.validate()
        if self.result is not None:
            raise ValueError("game has ended")
        unit, next_unit_id = self._prepare_unit(
            owner_id, unit_type, position, next_unit_id=self.next_unit_id,
        )
        self.units[unit.id] = unit
        self.next_unit_id = next_unit_id
        if self.active_player_id is not None:
            from aig.knowledge import update_knowledge
            update_knowledge(self)
        return unit

    def _prepare_unit(
        self, owner_id: str, unit_type: UnitType, position: Position, *,
        next_unit_id: int,
        moves_remaining: int | _DefaultMovement = _DefaultMovement.ALLOWANCE,
    ) -> tuple[UnitState, int]:
        """Validate placement and allocate without mutation in an already valid state.

        Setup and economy share this allocator. A batch passes the returned
        counter into its next preparation, then commits units and counter only
        after all preparations succeed.
        """
        _integer(next_unit_id, "next_unit_id", minimum=1)
        _identifier(owner_id, "owner_id")
        if owner_id not in self.players or self.players[owner_id].eliminated:
            raise ValueError("unit owner must be a live player")
        if not isinstance(unit_type, UnitType):
            raise ValueError("unit_type must be a UnitType")
        if self.is_barbarian(owner_id) and unit_type is not UnitType.WARRIOR:
            raise ValueError("barbarians use Warriors only")
        if not isinstance(position, Position):
            raise ValueError("unit.position must be a Position")
        if not self.can_enter(owner_id, position):
            raise ValueError("unit position is out of bounds, impassable, or enemy-occupied")
        number = next_unit_id
        while f"unit-{number}" in self.units:
            number += 1
        unit = UnitState(
            f"unit-{number}", owner_id, position, unit_type,
            moves_remaining=moves_remaining,
        )
        return unit, number + 1

    def get_city(self, city_id: str) -> CityState:
        """Look up a live city; malformed or unknown IDs raise ValueError."""
        _identifier(city_id, "city_id")
        if city_id not in self.cities:
            raise ValueError(f"unknown city: {city_id!r}")
        return self.cities[city_id]

    def city_at(self, position: Position) -> CityState | None:
        """Return the live city at a position, or None."""
        if not isinstance(position, Position):
            raise ValueError("city.position must be a Position")
        return next((c for c in self.cities.values() if c.position == position), None)

    def _validate_city_placement(self, city: CityState) -> None:
        """Shared setup/state checks; tile ownership is separate persistent state."""
        city.validate()
        if city.owner_id not in self.players or self.players[city.owner_id].eliminated:
            raise ValueError("city owner must be a live player")
        if self.players[city.owner_id].kind is FactionKind.BARBARIAN:
            raise ValueError("barbarians cannot own cities")
        if any(c.position == city.position for c in self.camps.values()):
            raise ValueError("city cannot occupy a camp")
        if not self.game_map.contains(city.position):
            raise ValueError("city position is outside map bounds")
        tile = self.tiles.get(city.position)
        if tile is None:
            raise ValueError("city position references an unknown tile")
        if not tile.terrain.land_passable:
            raise ValueError("city position has illegal terrain")
        if any(u.position == city.position and u.owner_id != city.owner_id for u in self.units.values()):
            raise ValueError("hostile city and unit cannot share a tile")

    def add_city(self, city: CityState) -> CityState:
        """Add a caller-supplied live city during setup/rules; do not claim tiles."""
        self.validate()
        if self.result is not None:
            raise ValueError("game has ended")
        if not isinstance(city, CityState):
            raise ValueError("city must be a CityState")
        self._validate_city_placement(city)
        if city.id in self.cities:
            raise ValueError(f"duplicate city ID: {city.id!r}")
        _validate_city_spacing(city.position, (c.position for c in self.cities.values()))
        self.cities[city.id] = city
        self.players[city.owner_id].has_ever_owned_city = True
        if self.active_player_id is not None:
            from aig.knowledge import update_knowledge
            update_knowledge(self)
        return city

    def remove_city(self, city_id: str) -> None:
        """Remove a live city, retaining tiles and evaluating zero-city elimination.

        Unknown IDs raise ValueError, including repeated removal.
        """
        self.validate()
        if self.result is not None:
            raise ValueError("game has ended")
        city = self.get_city(city_id)
        del self.cities[city.id]
        self._eliminate_if_cityless(city.owner_id)

    def can_enter(
        self, owner_id: str, position: Position, *, excluding_unit_id: str | None = None,
        capture_unit_type: UnitType | None = None,
    ) -> bool:
        """Shared placement/movement legality for all current land unit types.

        Combat may exclude its lethally damaged target to resolve advance before
        mutation. Cities are never excluded.
        """
        tile = self.tiles.get(position)
        return (
            self.game_map.contains(position)
            and tile is not None
            and tile.terrain.land_passable
            and not any(c.position == position and c.owner_id != owner_id
                        and not (capture_unit_type is not None and capture_unit_type.can_capture
                                 and self.players[owner_id].kind is FactionKind.CIVILIZATION
                                 and not self.players[owner_id].eliminated
                                 and self.players[c.owner_id].kind is FactionKind.CIVILIZATION
                                 and not self.players[c.owner_id].eliminated)
                        for c in self.cities.values())
            and not any(
                u.id != excluding_unit_id and u.position == position and u.owner_id != owner_id
                for u in self.units.values()
            )
        )

    def eliminate_player(self, player_id: str) -> None:
        """Retain history, remove a live faction, and end its activation if active.

        Repeated elimination is a no-op. Eliminating the active faction selects
        its next survivor, wrapping the turn only if at least two remain.
        Becoming terminal clears the activation without incrementing the turn.
        """
        self.validate()
        _identifier(player_id, "player_id")
        if player_id not in self.players:
            raise ValueError(f"cannot eliminate unknown player: {player_id!r}")
        player = self.players[player_id]
        if self.is_barbarian(player_id):
            raise ValueError("system faction cannot be eliminated")
        if player.eliminated:
            return
        if self.result is not None:
            raise ValueError("game has ended")
        self._eliminate_player(player_id)

    def _eliminate_if_cityless(self, player_id: str) -> None:
        if (self.players[player_id].has_ever_owned_city
                and not any(c.owner_id == player_id for c in self.cities.values())):
            self._eliminate_player(player_id)

    def _eliminate_player(self, player_id: str) -> None:
        """Commit cleanup in an already validated ownership transition."""
        player = self.players[player_id]
        started = self.active_player_id is not None
        removed_index = self.turn_order.index(player_id)
        player.eliminated = True
        self.turn_order.pop(removed_index)
        for unit_id in [u.id for u in self.units.values() if u.owner_id == player_id]:
            del self.units[unit_id]
        for city_id in [c.id for c in self.cities.values() if c.owner_id == player_id]:
            del self.cities[city_id]
        if len(self.civilization_ids) < 2:
            self.active_player_id = None
            if started and len(self.civilization_ids) == 1:
                self.result = GameResult(self.civilization_ids[0])
        elif self.active_player_id == player_id:
            if removed_index == len(self.turn_order):
                self.turn += 1
                removed_index = 0
            self._begin_activation(self.turn_order[removed_index])

    def validate(self) -> None:
        """Check types and references, including after direct state mutations."""
        if not isinstance(self.config, GameConfig):
            raise ValueError("config must be a GameConfig")
        _integer(self.turn, "turn", minimum=0)
        if not isinstance(self.game_map, GameMap):
            raise ValueError("game_map must be a GameMap")
        _integer(self.next_unit_id, "next_unit_id", minimum=1)
        for name, entities, entity_type in (
            ("players", self.players, PlayerState),
            ("cities", self.cities, CityState),
            ("units", self.units, UnitState),
            ("camps", self.camps, BarbarianCamp),
        ):
            if not isinstance(entities, dict):
                raise ValueError(f"{name} must be a dictionary keyed by ID")
            for key, entity in entities.items():
                if not isinstance(entity, entity_type):
                    raise ValueError(f"{name} contains an invalid entity")
                entity.validate()
                if key != entity.id:
                    raise ValueError(f"{name} key {key!r} does not match entity ID")
        if not isinstance(self.tiles, dict):
            raise ValueError("tiles must be a dictionary keyed by Position")
        for key, tile in self.tiles.items():
            if not isinstance(tile, TileState):
                raise ValueError("tiles contains an invalid entity")
            tile.validate()
            if key != tile.position:
                raise ValueError("tiles key does not match tile position")
            if not self.game_map.contains(tile.position):
                raise ValueError("tile position is outside map bounds")
            if tile.owner_id is not None and tile.owner_id not in self.players:
                raise ValueError("tile.owner_id references an unknown player")
        if not isinstance(self.turn_order, list):
            raise ValueError("turn_order must be a list of player IDs")
        ordered_ids: set[str] = set()
        for player_id in self.turn_order:
            _identifier(player_id, "turn_order player ID")
            if player_id in ordered_ids:
                raise ValueError(f"duplicate player ID in turn_order: {player_id!r}")
            if player_id not in self.players:
                raise ValueError(f"turn_order references an unknown player: {player_id!r}")
            if self.players[player_id].eliminated:
                raise ValueError(f"turn_order contains an eliminated player: {player_id!r}")
            ordered_ids.add(player_id)
        if self.active_player_id is not None:
            _identifier(self.active_player_id, "active_player_id")
            if self.active_player_id not in self.players:
                raise ValueError("active_player_id references an unknown player")
            if self.players[self.active_player_id].eliminated:
                raise ValueError("active_player_id cannot be an eliminated player")
            if self.active_player_id not in ordered_ids:
                raise ValueError("active_player_id must appear in turn_order")
        live_ids = {player.id for player in self.players.values() if not player.eliminated}
        if self.result is not None:
            if (not isinstance(self.result, GameResult)
                    or not isinstance(self.result.victory_type, VictoryType)
                    or self.civilization_ids != [self.result.winner_player_id]
                    or self.active_player_id is not None):
                raise ValueError("invalid conquest result")
        if ordered_ids != live_ids:
            raise ValueError("every player that is not eliminated must appear exactly once in turn_order")
        system_ids = [p.id for p in self.players.values() if p.kind is FactionKind.BARBARIAN]
        if system_ids and self.turn_order[-1:] != system_ids:
            raise ValueError("system faction must be the final activation")
        if len(self.civilization_ids) < 2:
            if self.active_player_id is not None:
                raise ValueError("active_player_id must be None with fewer than two surviving players")
        elif self.active_player_id is None and self.turn != 0:
            raise ValueError("active_player_id may be None only in a pre-game or terminal state")
        for entity in (*self.cities.values(), *self.units.values()):
            if entity.owner_id not in self.players:
                raise ValueError(f"{entity.id!r} owner_id references an unknown player")
            if entity.position not in self.tiles:
                raise ValueError(f"{entity.id!r} position references an unknown tile")
        for player in self.players.values():
            owns_city = any(c.owner_id == player.id for c in self.cities.values())
            if owns_city and not player.has_ever_owned_city:
                raise ValueError("city owner must have has_ever_owned_city true")
            if ((self.active_player_id is not None or self.turn > 0 or self.result is not None)
                    and not player.eliminated
                    and player.has_ever_owned_city and not owns_city):
                raise ValueError("live historical city owner without cities must be eliminated")
            if any(not self.game_map.contains(p) for p in player.knowledge.explored_positions):
                raise ValueError("explored position outside map")
            for camp in player.knowledge.discovered_camps.values():
                if camp.position not in player.knowledge.explored_positions or camp.last_seen_turn > self.turn:
                    raise ValueError("known camp must reference explored position and past turn")
            for city in player.knowledge.discovered_cities.values():
                if (city.owner_id not in self.players or city.owner_id == player.id
                        or city.position not in player.knowledge.explored_positions):
                    raise ValueError("known city must reference another faction and explored position")
        city_positions: set[Position] = set()
        for city in self.cities.values():
            self._validate_city_placement(city)
            _validate_city_spacing(city.position, city_positions)
            city_positions.add(city.position)
        occupants: dict[Position, str] = {}
        camp_positions = set()
        for camp in self.camps.values():
            tile = self.tiles.get(camp.position)
            if (not system_ids or tile is None or not tile.terrain.land_passable
                    or camp.position in city_positions or camp.position in camp_positions):
                raise ValueError("camp requires unique passable land, no city, and system faction")
            camp_positions.add(camp.position)
        for unit in self.units.values():
            if self.is_barbarian(unit.owner_id):
                if unit.unit_type is not UnitType.WARRIOR:
                    raise ValueError("barbarians use Warriors only")
            elif unit.home_camp_id is not None:
                raise ValueError("civilization unit cannot have home camp")
            if self.players[unit.owner_id].eliminated:
                raise ValueError("live unit cannot belong to an eliminated player")
            if not self.tiles[unit.position].terrain.land_passable:
                raise ValueError("unit position has impassable terrain")
            if unit.position in occupants and occupants[unit.position] != unit.owner_id:
                raise ValueError("hostile units cannot share a tile")
            occupants[unit.position] = unit.owner_id
