"""Deterministic unit combat rules, reusable by command-driven executors."""

from dataclasses import dataclass

from aig.state import GameState, UnitType, _identifier


def calculate_damage(attacking_strength: int, defending_strength: int) -> int:
    """Base damage with integer caps; no RNG, HP scaling or hidden modifiers."""
    return max(10, min(50, 30 + attacking_strength - defending_strength))


@dataclass(frozen=True)
class AttackPreview:
    target_damage: int
    retaliation: int


def preview_attack(state: GameState, attacker_unit_id: str, target_unit_id: str) -> AttackPreview:
    """Read-only legality and damage query, shared by combat and controllers.

    Illegal attacks raise ValueError. Actor authorization remains in commands.
    """
    state.validate()
    _identifier(attacker_unit_id, "attacker_unit_id")
    _identifier(target_unit_id, "target_unit_id")
    if attacker_unit_id not in state.units:
        raise ValueError(f"unknown attacker unit: {attacker_unit_id!r}")
    if target_unit_id not in state.units:
        raise ValueError(f"unknown target unit: {target_unit_id!r}")
    attacker = state.units[attacker_unit_id]
    target = state.units[target_unit_id]
    if attacker.owner_id == target.owner_id:
        raise ValueError("cannot attack a friendly unit or self")
    if attacker.unit_type.attack_range == 0:
        raise ValueError("unit cannot attack")
    if attacker.moves_remaining == 0:
        raise ValueError("unit has no movement remaining")
    distance = max(
        abs(attacker.position.x - target.position.x),
        abs(attacker.position.y - target.position.y),
    )
    if not 1 <= distance <= attacker.unit_type.attack_range:
        raise ValueError("target is outside attack range")

    ranged_strength = attacker.unit_type.ranged_strength
    is_ranged = ranged_strength is not None
    strength = ranged_strength if is_ranged else attacker.unit_type.combat_strength
    civilian = target.unit_type is UnitType.SETTLER
    target_damage = target.hp if civilian else calculate_damage(strength, target.unit_type.combat_strength)
    retaliation = (
        0 if is_ranged or civilian
        else calculate_damage(target.unit_type.combat_strength, attacker.unit_type.combat_strength)
    )
    return AttackPreview(target_damage, retaliation)


def attack_unit(state: GameState, attacker_unit_id: str, target_unit_id: str) -> None:
    """Resolve through the shared preview, then commit damage, deaths and advance."""
    preview = preview_attack(state, attacker_unit_id, target_unit_id)
    attacker = state.units[attacker_unit_id]
    target = state.units[target_unit_id]
    target_damage, retaliation = preview.target_damage, preview.retaliation
    is_ranged = attacker.unit_type.ranged_strength is not None
    attacker_hp = attacker.hp - retaliation
    target_hp = target.hp - target_damage
    remaining_moves = attacker.moves_remaining - 1
    attacker_position = attacker.position
    if not is_ranged and attacker_hp > 0 and target_hp <= 0:
        if state.can_enter(attacker.owner_id, target.position, excluding_unit_id=target.id):
            attacker_position = target.position

    # All legality, damage, deaths, cost and advance are now resolved from the
    # pre-combat state. Commit only; no fallible rules or callbacks follow.
    if target_hp <= 0:
        del state.units[target.id]
    else:
        target.hp = target_hp
    if attacker_hp <= 0:
        del state.units[attacker.id]
    else:
        attacker.hp = attacker_hp
        attacker.moves_remaining = remaining_moves
        attacker.position = attacker_position
