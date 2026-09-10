"""Pure Ancient-era research and unit unlock queries; rules are never persisted."""

from aig.state import PlayerState, Technology, UnitType


def technology_cost(technology: Technology) -> int:
    """Agriculture has zero cost; normal factions already know it."""
    if not isinstance(technology, Technology):
        raise ValueError("technology must be a Technology")
    return technology.science_cost


def technology_prerequisites(technology: Technology) -> frozenset[Technology]:
    if not isinstance(technology, Technology):
        raise ValueError("technology must be a Technology")
    return technology.prerequisites


def _validate_player(player: PlayerState) -> None:
    if not isinstance(player, PlayerState):
        raise ValueError("player must be a PlayerState")
    player.validate()


def available_technologies(player: PlayerState) -> tuple[Technology, ...]:
    """Return unresearched options in enum declaration order."""
    _validate_player(player)
    return tuple(tech for tech in Technology
                 if tech not in player.researched_technologies
                 and technology_prerequisites(tech) <= player.researched_technologies)


def research_remaining(player: PlayerState) -> int | None:
    """Target and stored science are directly readable PlayerState fields."""
    _validate_player(player)
    if player.research_target is None:
        return None
    return max(0, technology_cost(player.research_target) - player.science_stored)


def unit_is_unlocked(player: PlayerState, unit_type: UnitType) -> bool:
    _validate_player(player)
    if not isinstance(unit_type, UnitType):
        raise ValueError("unit_type must be a UnitType")
    required = {
        UnitType.SETTLER: Technology.AGRICULTURE,
        UnitType.ARCHER: Technology.ARCHERY,
        UnitType.SPEARMAN: Technology.BRONZE_WORKING,
    }.get(unit_type)
    return required is None or required in player.researched_technologies
