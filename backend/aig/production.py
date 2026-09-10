"""Pure queries for single-target unit construction; no queues or presentation."""

from aig.state import CityState, UnitType


def production_cost(unit_type: UnitType) -> int:
    """Static unit cost, derived from type rather than persisted on cities."""
    if not isinstance(unit_type, UnitType):
        raise ValueError("unit_type must be a producible UnitType")
    return unit_type.production_cost


def production_remaining(city: CityState) -> int | None:
    """Return None without a target, otherwise its non-negative shortfall.

    An affordable target returns zero but only completes during owner economy.
    """
    if not isinstance(city, CityState):
        raise ValueError("city must be a CityState")
    city.validate()
    if city.production_target is None:
        return None
    return max(0, production_cost(city.production_target) - city.production_stored)
