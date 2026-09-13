"""Arena's independent, fully visible state. No Empire lifecycle or AI rules."""

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from aig.state import Position

RULES_VERSION = "arena-rules-v1"
SCENARIO_VERSION = "arena-scenario-v1"
TURN_AP = 5
CORE_HP = 30


def integer(value, name, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"invalid {name}")


def identifier(value, name="id"):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid {name}")


class Terrain(StrEnum):
    FLOOR = "floor"
    BLOCKED = "blocked"


class Bonus(StrEnum):
    POWER = "power"
    WARD = "ward"
    SIEGE = "siege"


class UnitType(StrEnum):
    KNIGHT = "knight"
    RANGER = "ranger"
    MAGE = "mage"
    CLERIC = "cleric"


@dataclass(frozen=True)
class UnitStats:
    hp: int
    damage: int
    attack_range: int
    move_range: int
    heal_amount: int = 0
    heal_range: int = 0


STATS = MappingProxyType({
    UnitType.KNIGHT: UnitStats(18, 6, 1, 2),
    UnitType.RANGER: UnitStats(10, 5, 3, 3),
    UnitType.MAGE: UnitStats(9, 6, 2, 2),
    UnitType.CLERIC: UnitStats(11, 3, 2, 2, 5, 2),
})


@dataclass(frozen=True)
class ArenaConfig:
    rules_version: str = RULES_VERSION
    scenario_version: str = SCENARIO_VERSION

    def __post_init__(self):
        if self.rules_version != RULES_VERSION or self.scenario_version != SCENARIO_VERSION:
            raise ValueError("unsupported Arena rules/scenario version")


@dataclass(frozen=True)
class Tile:
    terrain: Terrain = Terrain.FLOOR
    bonus: Bonus | None = None

    def __post_init__(self):
        if not isinstance(self.terrain, Terrain) or (self.bonus is not None and not isinstance(self.bonus, Bonus)):
            raise ValueError("invalid Arena tile")
        if self.terrain is Terrain.BLOCKED and self.bonus is not None:
            raise ValueError("blocked tiles cannot have bonuses")


@dataclass(frozen=True)
class Board:
    """Complete row-major immutable board; origin (0, 0), y increases south."""

    tiles: tuple[Tile, ...]
    width: int = 9
    height: int = 5

    def __post_init__(self):
        integer(self.width, "width", 9, 9)
        integer(self.height, "height", 5, 5)
        if type(self.tiles) is not tuple or len(self.tiles) != 45 or not all(isinstance(t, Tile) for t in self.tiles):
            raise ValueError("Arena requires exactly 45 tiles")

    def contains(self, position):
        return isinstance(position, Position) and 0 <= position.x < self.width and 0 <= position.y < self.height

    def at(self, position):
        if not self.contains(position):
            raise ValueError("position outside Arena board")
        return self.tiles[position.y * self.width + position.x]


@dataclass(frozen=True)
class ArenaPlayer:
    id: str
    name: str

    def __post_init__(self):
        identifier(self.id)
        identifier(self.name, "player name")


@dataclass
class ArenaUnit:
    id: str
    owner_id: str
    unit_type: UnitType
    position: Position
    hp: int

    @property
    def stats(self):
        return STATS[self.unit_type]

    @property
    def max_hp(self):
        return self.stats.hp


@dataclass
class ArenaCore:
    id: str
    owner_id: str
    position: Position
    hp: int = CORE_HP


@dataclass
class ArenaState:
    board: Board
    players: tuple[ArenaPlayer, ...]
    units: dict[str, ArenaUnit]
    cores: dict[str, ArenaCore]
    active_player_id: str | None
    config: ArenaConfig = field(default_factory=ArenaConfig)
    turn: int = 0
    action_points_remaining: int = TURN_AP
    winner_player_id: str | None = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not isinstance(self.board, Board) or not isinstance(self.config, ArenaConfig):
            raise ValueError("invalid Arena board/config")
        if type(self.players) is not tuple or len(self.players) != 2 or not all(isinstance(p, ArenaPlayer) for p in self.players):
            raise ValueError("Arena requires exactly two players")
        ids = [p.id for p in self.players]
        if len(set(ids)) != 2:
            raise ValueError("duplicate players")
        if type(self.units) is not dict or type(self.cores) is not dict or len(self.cores) != 2:
            raise ValueError("invalid units/cores")
        integer(self.turn, "turn")
        integer(self.action_points_remaining, "AP", 0, TURN_AP)
        occupied = set()
        entity_ids = set(ids)
        for entities, cls in ((self.units, ArenaUnit), (self.cores, ArenaCore)):
            for key, entity in entities.items():
                if not isinstance(entity, cls):
                    raise ValueError("invalid entity type")
                identifier(entity.id)
                identifier(entity.owner_id, "owner")
                if key != entity.id or entity.id in entity_ids or entity.owner_id not in ids:
                    raise ValueError("invalid or duplicate entity identity/owner")
                entity_ids.add(entity.id)
                if not self.board.contains(entity.position) or self.board.at(entity.position).terrain is Terrain.BLOCKED:
                    raise ValueError("entity must be on an in-bounds floor tile")
                if entity.position in occupied:
                    raise ValueError("units and Cores cannot share tiles")
                occupied.add(entity.position)
                if cls is ArenaUnit:
                    if not isinstance(entity.unit_type, UnitType):
                        raise ValueError("invalid unit type")
                    integer(entity.hp, "unit HP", 1, entity.max_hp)
                else:
                    integer(entity.hp, "Core HP", 0, CORE_HP)
        if sorted(c.owner_id for c in self.cores.values()) != sorted(ids):
            raise ValueError("each player requires one Core")
        defeated = {p for p in ids if not any(u.owner_id == p for u in self.units.values())
                    or any(c.owner_id == p and c.hp == 0 for c in self.cores.values())}
        if self.winner_player_id is None:
            if self.active_player_id not in ids or defeated:
                raise ValueError("nonterminal battle requires an active player and two living teams")
        elif (self.winner_player_id not in ids or self.active_player_id is not None
              or defeated != set(ids) - {self.winner_player_id}):
            raise ValueError("inconsistent terminal winner")

    def unit_at(self, position):
        return next((u for u in self.units.values() if u.position == position), None)

    def core_at(self, position):
        return next((c for c in self.cores.values() if c.position == position), None)

    def can_enter(self, position):
        return (self.board.contains(position) and self.board.at(position).terrain is Terrain.FLOOR
                and self.unit_at(position) is None and self.core_at(position) is None)
