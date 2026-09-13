"""Compressed JSON planning contract and the first, entirely local provider."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import NotRequired, Protocol, TypedDict

from aig.knowledge import known_enemy_cities, known_resources, visible_positions, military_strength, known_camps
from aig.research import available_technologies, unit_is_unlocked
from aig.state import GameState, Technology, UnitType, _identifier


class StrategicCity(TypedDict):
    id: str
    owner_id: str
    x: int
    y: int
    population: NotRequired[int]
    production: NotRequired[str | None]
    currently_visible: NotRequired[bool]
    live_exists: NotRequired[bool | None]
    food_stored: NotRequired[int]
    production_stored: NotRequired[int]
    name: NotRequired[str]


class StrategicUnit(TypedDict):
    id: str
    owner_id: str
    type: str
    x: int
    y: int
    hp: int
    moves_remaining: int
    strength: int


class StrategicState(TypedDict):
    terminal: bool
    remaining_civilization_count: int
    own_city_count: int
    victory: dict | None
    player_id: str
    turn: int
    gold: int
    science_stored: int
    science_per_activation: int
    research_target: str | None
    known_technologies: list[str]
    own_cities: list[StrategicCity]
    own_units: list[StrategicUnit]
    enemy_cities: list[StrategicCity]
    enemy_units: list[StrategicUnit]
    own_military_strength: int
    enemy_military_strength: int
    visible_enemy_military_strength: int
    nearest_visible_enemy_unit_distance: int | None
    civilizations: list[dict]
    explored_terrain: list[dict]
    known_resources: list[dict]
    known_barbarian_camps: list[dict]
    visible_barbarian_units: list[StrategicUnit]
    available_production: list[str]
    available_research: list[str]


def distance(a: dict, b: dict) -> int:
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


class StrategicStateBuilder:
    def build(self, state: GameState, player_id: str) -> StrategicState:
        state.validate()
        if player_id not in state.players or state.players[player_id].eliminated:
            raise ValueError("strategic state requires a live player")
        if state.is_barbarian(player_id):
            raise ValueError("system faction cannot request strategic state")
        player = state.players[player_id]
        visible = visible_positions(state, player_id)
        cities: list[StrategicCity] = [
            dict(id=c.id, owner_id=c.owner_id, x=c.position.x, y=c.position.y,
                 population=c.population, food_stored=c.food_stored, production_stored=c.production_stored, name=c.name,
                 production=c.production_target.value if c.production_target else None)
            for c in sorted(state.cities.values(), key=lambda c: c.id) if c.owner_id == player_id
        ]
        units: list[StrategicUnit] = [
            dict(id=u.id, owner_id=u.owner_id, type=u.unit_type.value,
                 x=u.position.x, y=u.position.y, hp=u.hp, moves_remaining=u.moves_remaining,
                 strength=max(u.unit_type.combat_strength, u.unit_type.ranged_strength or 0) * u.hp // 100)
            for u in sorted(state.units.values(), key=lambda u: u.id)
            if u.owner_id == player_id or u.position in visible
        ]
        own_cities = [c for c in cities if c["owner_id"] == player_id]
        own_units = [u for u in units if u["owner_id"] == player_id]
        enemy_units = [u for u in units if u["owner_id"] != player_id and not state.is_barbarian(u["owner_id"])]
        return StrategicState(
            terminal=state.result is not None,
            remaining_civilization_count=len(state.civilization_ids),
            own_city_count=len(own_cities),
            victory=asdict(state.result) if state.result else None,
            player_id=player_id, turn=state.turn, gold=player.gold,
            science_stored=player.science_stored,
            science_per_activation=sum(c["population"] for c in own_cities),
            research_target=player.research_target.value if player.research_target else None,
            known_technologies=sorted(t.value for t in player.researched_technologies),
            own_cities=own_cities, own_units=own_units,
            enemy_cities=known_enemy_cities(state, player_id),
            enemy_units=enemy_units,
            own_military_strength=sum(u["strength"] for u in own_units),
            enemy_military_strength=military_strength(u for u in state.units.values() if u.owner_id != player_id and not state.is_barbarian(u.owner_id)),
            visible_enemy_military_strength=sum(u["strength"] for u in enemy_units),
            nearest_visible_enemy_unit_distance=min((distance(u, a) for u in enemy_units
                if u["type"] != "settler" for a in own_cities + own_units), default=None),
            civilizations=[dict(id=p.id, eliminated=p.eliminated, hostile=p.id != player_id,
                global_military_strength=military_strength(u for u in state.units.values() if u.owner_id == p.id),
                researched_technologies=sorted(t.value for t in p.researched_technologies))
                for p in sorted(state.players.values(), key=lambda p: p.id) if not state.is_barbarian(p.id)],
            explored_terrain=[dict(x=p.x, y=p.y, terrain=state.tiles[p].terrain.value)
                for p in sorted(player.knowledge.explored_positions, key=lambda p: (p.y, p.x)) if p in state.tiles],
            known_resources=known_resources(state, player_id),
            known_barbarian_camps=known_camps(state, player_id),
            visible_barbarian_units=[u for u in units if state.is_barbarian(u["owner_id"])],
            available_production=sorted(t.value for t in UnitType if unit_is_unlocked(player, t)),
            available_research=sorted(t.value for t in available_technologies(player)),
        )


class Posture(StrEnum):
    EXPAND = "expand"
    DEFEND = "defend"
    ATTACK = "attack"


class ExpansionPriority(StrEnum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True)
class StrategicPlan:
    posture: Posture
    primary_enemy_id: str | None = None
    target_city_id: str | None = None
    expansion_priority: ExpansionPriority = ExpansionPriority.LOW
    production_priority: tuple[UnitType, ...] = (
        UnitType.ARCHER, UnitType.SPEARMAN, UnitType.WARRIOR,
    )
    research_priority: tuple[Technology, ...] = (
        Technology.ARCHERY, Technology.BRONZE_WORKING, Technology.AGRICULTURE,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.posture, Posture) or not isinstance(self.expansion_priority, ExpansionPriority):
            raise ValueError("plan posture and expansion priority must be enum values")
        for name in ("primary_enemy_id", "target_city_id"):
            if getattr(self, name) is not None:
                _identifier(getattr(self, name), name)
        for name, kind in (("production_priority", UnitType), ("research_priority", Technology)):
            values = getattr(self, name)
            if (not isinstance(values, tuple) or not values
                    or any(not isinstance(v, kind) for v in values) or len(set(values)) != len(values)):
                raise ValueError(f"{name} must be a nonempty tuple of unique {kind.__name__} values")

    def to_dict(self) -> dict:
        return {**asdict(self), "posture": self.posture.value,
                "expansion_priority": self.expansion_priority.value,
                "production_priority": [t.value for t in self.production_priority],
                "research_priority": [t.value for t in self.research_priority]}


class StrategyProvider(Protocol):
    """Previous context is a currently reference-valid plan or None.

    The controller clears known-invalid plans before primary/fallback invocation.
    Expiry and significant events may preserve valid continuity.
    """

    def create_plan(self, state: StrategicState,
                    previous_plan: StrategicPlan | None = None) -> StrategicPlan: ...


class StrategyProviderError(RuntimeError):
    """Expected planning failure; orchestration may use a fallback provider."""


class HeuristicStrategyProvider:
    name = "heuristic"

    def create_plan(self, state: StrategicState,
                    previous_plan: StrategicPlan | None = None) -> StrategicPlan:
        own = state["own_units"]
        cities = state["own_cities"]
        military = [u for u in own if u["type"] != UnitType.SETTLER.value]
        anchors = cities or own
        dead = {c['id'] for c in state.get('civilizations', []) if c['eliminated']}
        target = min((c for c in state["enemy_cities"] if c.get("live_exists") is not False
                      and c['owner_id'] not in dead), key=lambda c: (
            min((distance(c, a) for a in anchors), default=0), c["id"]), default=None)
        local_enemies = [u for u in state["enemy_units"] + state.get("visible_barbarian_units", [])
                         if any(distance(u, a) <= 3 for a in anchors)]
        local_own = [u for u in military
                     if any(distance(u, enemy) <= 3 for enemy in local_enemies)]
        threatened = sum(u["strength"] for u in local_enemies) > 2 * sum(u["strength"] for u in local_own)
        if not cities and any(u["type"] == "settler" for u in own):
            posture = Posture.EXPAND
        elif threatened:
            posture = Posture.DEFEND
        elif target and len(military) >= 2:
            posture = Posture.ATTACK
        else:
            posture = Posture.EXPAND
        expansion = len(cities) < 2 and posture is not Posture.DEFEND
        if len(military) < 2:
            production = (UnitType.WARRIOR, UnitType.ARCHER, UnitType.SPEARMAN)
        elif expansion:
            production = (UnitType.SETTLER, UnitType.ARCHER, UnitType.SPEARMAN, UnitType.WARRIOR)
        else:
            production = (UnitType.ARCHER, UnitType.SPEARMAN, UnitType.WARRIOR)
        enemy = target["owner_id"] if target else (
            min(state["enemy_units"], key=lambda u: (
                min((distance(u, a) for a in anchors), default=0), u["id"]), default={}).get("owner_id"))
        return StrategicPlan(
            posture, enemy, target["id"] if target else None,
            ExpansionPriority.HIGH if expansion else ExpansionPriority.LOW,
            production,
        )
