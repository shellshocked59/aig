"""Deterministic city yields and economy, independent of activation advancement."""

from dataclasses import dataclass
from types import MappingProxyType

from aig.production import production_cost
from aig.research import technology_cost
from aig.state import CityState, GameState, Position, Terrain, _identifier, _integer


@dataclass(frozen=True)
class Yields:
    food: int = 0
    production: int = 0
    gold: int = 0

    def __post_init__(self) -> None:
        for name in ("food", "production", "gold"):
            _integer(getattr(self, name), f"yields.{name}", minimum=0)

    def __add__(self, other: object) -> "Yields":
        if not isinstance(other, Yields):
            return NotImplemented
        return Yields(self.food + other.food, self.production + other.production,
                      self.gold + other.gold)

    def __radd__(self, other: object) -> "Yields":
        # Support sum(yields), including its integer-zero starting value.
        if type(other) is int and other == 0:
            return self
        return NotImplemented


_TERRAIN_YIELDS = MappingProxyType({
    Terrain.GRASSLAND: Yields(food=2),
    Terrain.PLAINS: Yields(food=1, production=1),
    Terrain.FOREST: Yields(food=1, production=2),
    Terrain.HILLS: Yields(production=2),
    Terrain.MOUNTAINS: Yields(),
    Terrain.WATER: Yields(food=1, gold=1),
})


def terrain_yields(terrain: Terrain) -> Yields:
    """Return immutable static yields; tiles never store calculated yields."""
    if not isinstance(terrain, Terrain):
        raise ValueError("terrain must be a Terrain")
    return _TERRAIN_YIELDS[terrain]


def _validate_city(state: GameState, city: CityState) -> None:
    state.validate()
    if not isinstance(city, CityState) or state.cities.get(city.id) is not city:
        raise ValueError("economy queries require a live city from this state")


def city_center_yields(state: GameState, city: CityState) -> Yields:
    """The free center has at least 2 food and 1 production, without terraforming."""
    _validate_city(state, city)
    base = terrain_yields(state.tiles[city.position].terrain)
    return Yields(max(base.food, 2), max(base.production, 1), base.gold)


def workable_positions(state: GameState, city: CityState) -> list[Position]:
    """Surrounding radius-1 tiles in (y, x) order; excludes center and mountains.

    Missing/out-of-bounds tiles are unavailable. Water, ownership and unit
    occupancy do not restrict working. Queries neither claim nor modify tiles.
    """
    _validate_city(state, city)
    positions = []
    for y in range(city.position.y - 1, city.position.y + 2):
        for x in range(city.position.x - 1, city.position.x + 2):
            position = Position(x, y)
            tile = state.tiles.get(position)
            if (position != city.position and state.game_map.contains(position)
                    and tile is not None and tile.terrain is not Terrain.MOUNTAINS):
                positions.append(position)
    return positions


def worked_positions(state: GameState, city: CityState) -> list[Position]:
    """One surrounding tile per citizen, by descending F/P/G then ascending y/x.

    The free center is not included. Assignments are derived on every query.
    """
    def priority(position: Position) -> tuple[int, int, int, int, int]:
        yields = terrain_yields(state.tiles[position].terrain)
        return (-yields.food, -yields.production, -yields.gold, position.y, position.x)

    return sorted(workable_positions(state, city), key=priority)[:city.population]


def city_yields(state: GameState, city: CityState) -> Yields:
    """Total free center plus selected surroundings, using current population."""
    return sum((terrain_yields(state.tiles[p].terrain) for p in worked_positions(state, city)),
               city_center_yields(state, city))


def growth_cost(population: int) -> int:
    _integer(population, "population", minimum=1)
    return 10 + 5 * population


def resolve_player_economy(state: GameState, player_id: str) -> None:
    """Resolve a live owner's cities in city-ID ascending order, in place.

    Validate and compute all results before committing assignments. Yields and
    consumption and science use each city's starting population; growth works
    next activation. Research completes after all city results are prepared.
    Actor authorization belongs to apply_command. This rules API never advances
    activation or refreshes movement, and is not called by elimination or loading.
    """
    state.validate()
    _identifier(player_id, "player_id")
    if player_id not in state.players or state.players[player_id].eliminated:
        raise ValueError("economy owner must be a live player")
    player = state.players[player_id]
    gold = player.gold
    science = player.science_stored
    results = []
    produced_units = []
    next_unit_id = state.next_unit_id
    for city in sorted(state.cities.values(), key=lambda city: city.id):
        if city.owner_id != player_id:
            continue
        yields = city_yields(state, city)
        population = city.population
        science += population
        food = max(0, city.food_stored + yields.food - 2 * population)
        while food >= growth_cost(population):
            food -= growth_cost(population)
            population += 1
        production = city.production_stored + yields.production
        target = city.production_target
        if target is not None and production >= production_cost(target):
            # Prepare all spawns before any city's economy is committed. The
            # same allocator as setup validates placement without spending IDs.
            unit, next_unit_id = state._prepare_unit(
                city.owner_id, target, city.position,
                next_unit_id=next_unit_id, moves_remaining=0,
            )
            produced_units.append(unit)
            production -= production_cost(target)
            target = None
        results.append((city, food, population, production, target))
        gold += yields.gold

    research_target = player.research_target
    technologies = player.researched_technologies
    if research_target is not None and science >= technology_cost(research_target):
        science -= technology_cost(research_target)
        technologies = technologies | {research_target}
        research_target = None

    for city, food, population, production, target in results:
        city.food_stored = food
        city.population = population
        city.production_stored = production
        city.production_target = target
    for unit in produced_units:
        state.units[unit.id] = unit
    state.next_unit_id = next_unit_id
    player.gold = gold
    player.science_stored = science
    player.researched_technologies = technologies
    player.research_target = research_target
