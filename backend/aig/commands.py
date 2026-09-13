"""Deterministic controller requests; state rules own the actual mutations."""

from dataclasses import dataclass

from aig.cities import found_city
from aig.combat import attack_unit
from aig.economy import resolve_player_economy
from aig.movement import move_unit
from aig.production import production_cost
from aig.research import available_technologies, technology_cost, unit_is_unlocked
from aig.state import GameState, Position, Technology, UnitType, _identifier


@dataclass(frozen=True)
class EndActivation:
    """Request completion of the actor's current activation."""

    actor_id: str

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")


@dataclass(frozen=True)
class EliminatePlayer:
    """Infrastructure command to exercise elimination, not a combat rule."""

    actor_id: str
    target_player_id: str

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        _identifier(self.target_player_id, "target_player_id")


@dataclass(frozen=True)
class MoveUnit:
    """Request a destination; deterministic rules choose the complete route."""

    actor_id: str
    unit_id: str
    destination: Position

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        _identifier(self.unit_id, "unit_id")
        if not isinstance(self.destination, Position):
            raise ValueError("destination must be a Position")


@dataclass(frozen=True)
class AttackUnit:
    """Request an attack against one explicit enemy unit, including in stacks."""

    actor_id: str
    attacker_unit_id: str
    target_unit_id: str

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        _identifier(self.attacker_unit_id, "attacker_unit_id")
        _identifier(self.target_unit_id, "target_unit_id")


@dataclass(frozen=True)
class FoundCity:
    """Found a named city at the actor's Settler, consuming that unit."""

    actor_id: str
    settler_unit_id: str
    city_id: str
    city_name: str

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        _identifier(self.settler_unit_id, "settler_unit_id")
        _identifier(self.city_id, "city_id")
        _identifier(self.city_name, "city_name")


@dataclass(frozen=True)
class SetCityProduction:
    """Choose or clear one target, retaining the city's generic stockpile."""

    actor_id: str
    city_id: str
    unit_type: UnitType | None

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        _identifier(self.city_id, "city_id")
        if self.unit_type is not None:
            production_cost(self.unit_type)


@dataclass(frozen=True)
class SetResearch:
    """Choose or clear research, retaining the player's generic science."""

    actor_id: str
    technology: Technology | None

    def __post_init__(self) -> None:
        _identifier(self.actor_id, "actor_id")
        if self.technology is not None:
            technology_cost(self.technology)


Command = (EndActivation | EliminatePlayer | MoveUnit | AttackUnit | FoundCity
           | SetCityProduction | SetResearch)


def apply_command(state: GameState, command: Command) -> None:
    """Validate and execute one request in place, returning None on success.

    Invalid state, unsupported commands, and illegal requests raise ValueError
    before mutation. All commands require a known, live, active actor; none
    is valid before play or in a terminal game. Commands do not implicitly end
    activations.
    """
    state.validate()
    if not isinstance(command, (EndActivation, EliminatePlayer, MoveUnit, AttackUnit,
                                FoundCity, SetCityProduction, SetResearch)):
        raise ValueError(f"unsupported command type: {type(command).__name__}")
    if command.actor_id not in state.players:
        raise ValueError(f"unknown command actor: {command.actor_id!r}")
    if state.players[command.actor_id].eliminated:
        raise ValueError(f"eliminated player cannot issue commands: {command.actor_id!r}")
    if state.active_player_id is None:
        raise ValueError("no active activation: commands require a game in progress")
    if command.actor_id != state.active_player_id:
        raise ValueError("only the active player may issue commands")
    system = state.is_barbarian(command.actor_id)
    if system and not isinstance(command, (MoveUnit, AttackUnit, EndActivation)):
        raise ValueError("system faction may only move, attack, or end activation")

    if isinstance(command, EndActivation):
        if not system:
            resolve_player_economy(state, command.actor_id)
        state.finish_activation()
    elif isinstance(command, EliminatePlayer):
        # Self-elimination already ends the activation within the state rules.
        state.eliminate_player(command.target_player_id)
    elif isinstance(command, SetResearch):
        player = state.players[command.actor_id]
        if command.technology is not None:
            technology_cost(command.technology)
            if command.technology not in available_technologies(player):
                raise ValueError("technology is already researched or prerequisites are not satisfied")
        player.research_target = command.technology
    elif isinstance(command, SetCityProduction):
        city = state.get_city(command.city_id)
        if city.owner_id != command.actor_id:
            raise ValueError("city does not belong to command actor")
        if command.unit_type is not None:
            production_cost(command.unit_type)
            if not unit_is_unlocked(state.players[command.actor_id], command.unit_type):
                raise ValueError("unit type is not unlocked by the player's technologies")
        city.production_target = command.unit_type
    elif isinstance(command, FoundCity):
        if command.settler_unit_id not in state.units:
            raise ValueError(f"unknown Settler unit: {command.settler_unit_id!r}")
        if state.units[command.settler_unit_id].owner_id != command.actor_id:
            raise ValueError("Settler unit does not belong to command actor")
        found_city(state, command.settler_unit_id, command.city_id, command.city_name)
    elif isinstance(command, AttackUnit):
        if command.attacker_unit_id not in state.units:
            raise ValueError(f"unknown attacker unit: {command.attacker_unit_id!r}")
        if state.units[command.attacker_unit_id].owner_id != command.actor_id:
            raise ValueError("attacker unit does not belong to command actor")
        attack_unit(state, command.attacker_unit_id, command.target_unit_id)
    else:
        if command.unit_id not in state.units:
            raise ValueError(f"unknown unit: {command.unit_id!r}")
        if state.units[command.unit_id].owner_id != command.actor_id:
            raise ValueError("unit does not belong to command actor")
        move_unit(state, command.unit_id, command.destination)
