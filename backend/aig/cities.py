"""Deterministic Settler founding; no borders or city combat."""

from aig.state import (
    CityState, GameState, Position, UnitType, _identifier, _validate_city_spacing,
)


def validate_founding_site(state: GameState, owner_id: str, position: Position,
                           *, city_id: str | None = None) -> None:
    """Read-only site rules; independent of Settler movement and proposed city ID."""
    state.validate()
    candidate = CityState("site-query", owner_id, position, name="Site query")
    state._validate_city_placement(candidate)
    tile = state.tiles[position]
    if tile.owner_id is not None and tile.owner_id != owner_id:
        raise ValueError("cannot found on another player's tile")
    if city_id is not None and city_id in state.cities:
        raise ValueError(f"duplicate city ID: {city_id!r}")
    _validate_city_spacing(position, (city.position for city in state.cities.values()))


def can_found_city_at(state: GameState, owner_id: str, position: Position) -> bool:
    """Whether this position is a legal future site, using the founding rules."""
    try:
        validate_founding_site(state, owner_id, position)
    except ValueError:
        return False
    return True


def found_city(state: GameState, settler_unit_id: str, city_id: str, city_name: str) -> None:
    """Validate completely, then consume the Settler and claim only its tile.

    Actor authorization belongs to apply_command, as with movement and combat.
    """
    state.validate()
    _identifier(settler_unit_id, "settler_unit_id")
    if settler_unit_id not in state.units:
        raise ValueError(f"unknown Settler unit: {settler_unit_id!r}")
    settler = state.units[settler_unit_id]
    if settler.unit_type is not UnitType.SETTLER:
        raise ValueError("only a Settler may found a city")
    if settler.moves_remaining < 1:
        raise ValueError("Settler has no movement remaining")
    city = CityState(city_id, settler.owner_id, settler.position, name=city_name)
    tile = state.tiles[settler.position]
    validate_founding_site(state, settler.owner_id, settler.position, city_id=city_id)
    # add_city validates terrain, IDs, live ownership, spacing and occupancy
    # before its first mutation. Only infallible assignments/removal follow.
    state.add_city(city)
    del state.units[settler.id]
    tile.owner_id = city.owner_id
