"""Deterministic combat, command authorization, atomicity and HP persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest

from aig.combat import attack_unit, calculate_damage
from aig.commands import AttackUnit, EliminatePlayer, EndActivation, MoveUnit, apply_command
from aig.movement import find_path
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import ControllerType, GameState, GameConfig, Position, Terrain, UnitState, UnitType
from test_movement import movement_state


def combat_state(attacker_type=UnitType.WARRIOR, target_type=UnitType.WARRIOR, *, distance=1):
    state = movement_state(attacker_type)
    state.add_unit("B", target_type, Position(distance, 0))
    return state


class DamageTests(unittest.TestCase):
    def test_equal_strength(self):
        self.assertEqual(calculate_damage(20, 20), 30)

    def test_stronger_attacker(self):
        self.assertEqual(calculate_damage(25, 20), 35)

    def test_weaker_attacker(self):
        self.assertEqual(calculate_damage(10, 20), 20)

    def test_minimum_cap(self):
        self.assertEqual(calculate_damage(10, 40), 10)
        self.assertEqual(calculate_damage(10, 30), 10)

    def test_maximum_cap(self):
        self.assertEqual(calculate_damage(40, 10), 50)
        self.assertEqual(calculate_damage(30, 10), 50)

    def test_repeated_calculations_are_deterministic(self):
        for _ in range(20):
            self.assertEqual(calculate_damage(25, 20), 35)
            self.assertEqual(calculate_damage(20, 25), 25)


class CombatModelTests(unittest.TestCase):
    def test_stats_derived_from_unit_type(self):
        for kind, combat, ranged, attack_range in (
            (UnitType.SETTLER, 0, None, 0),
            (UnitType.SCOUT, 10, None, 1),
            (UnitType.WARRIOR, 20, None, 1),
            (UnitType.SPEARMAN, 25, None, 1),
            (UnitType.ARCHER, 10, 20, 2),
        ):
            with self.subTest(kind=kind):
                self.assertEqual((kind.combat_strength, kind.ranged_strength, kind.attack_range),
                                 (combat, ranged, attack_range))
                unit = UnitState("u", "A", Position(0, 0), kind)
                self.assertTrue({"combat_strength", "ranged_strength", "attack_range"}.isdisjoint(vars(unit)))

    def test_new_units_start_at_100_hp(self):
        for kind in UnitType:
            with self.subTest(kind=kind):
                self.assertEqual(UnitState("u", "A", Position(0, 0), kind).hp, 100)
                self.assertEqual(movement_state(kind).units["unit-1"].hp, 100)

    def test_live_hp_boundaries(self):
        for hp in (1, 100):
            with self.subTest(hp=hp):
                unit = UnitState("u", "A", Position(0, 0), hp=hp)
                self.assertEqual(unit.hp, hp)

    def test_invalid_hp_rejected_on_construction_validation_export_and_load(self):
        for kind in UnitType:
            for hp in (0, -1, 101, True, False, 1.0, "50", None, []):
                with self.subTest(kind=kind, hp=hp):
                    with self.assertRaises(ValueError):
                        UnitState("u", "A", Position(0, 0), kind, hp=hp)
                    state = movement_state(kind)
                    snapshot = to_snapshot(state)
                    snapshot["units"][0]["hp"] = hp
                    with self.assertRaises(ValueError):
                        from_snapshot(snapshot)
                    state.units["unit-1"].hp = hp
                    with self.assertRaises(ValueError):
                        state.validate()
                    with self.assertRaises(ValueError):
                        to_snapshot(state)


class CombatCommandTests(unittest.TestCase):
    def assert_rejected(self, state, command, error):
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, error):
            apply_command(state, command)
        self.assertEqual(state, before)

    def test_command_is_immutable(self):
        command = AttackUnit("A", "unit-1", "unit-2")
        for field in ("actor_id", "attacker_unit_id", "target_unit_id"):
            with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
                setattr(command, field, "changed")

    def test_command_identifiers_are_strict(self):
        for value in (None, True, 1, [], "", " \t"):
            for index in range(3):
                args = ["A", "unit-1", "unit-2"]
                args[index] = value
                with self.subTest(args=args), self.assertRaises(ValueError):
                    AttackUnit(*args)

    def test_active_human_or_ai_can_attack(self):
        for controller in ControllerType:
            with self.subTest(controller=controller):
                state = combat_state()
                state.players["A"].controller = controller
                self.assertIsNone(apply_command(state, AttackUnit("A", "unit-1", "unit-2")))
                self.assertEqual(state.units["unit-2"].hp, 70)
                state.validate()

    def test_inactive_actor_rejected(self):
        self.assert_rejected(combat_state(), AttackUnit("B", "unit-2", "unit-1"), "only the active")

    def test_unknown_actor_rejected(self):
        self.assert_rejected(combat_state(), AttackUnit("missing", "unit-1", "unit-2"), "unknown command actor")

    def test_unknown_attacker_rejected(self):
        self.assert_rejected(combat_state(), AttackUnit("A", "missing", "unit-2"), "unknown attacker")

    def test_unknown_target_rejected(self):
        self.assert_rejected(combat_state(), AttackUnit("A", "unit-1", "missing"), "unknown target")

    def test_cannot_command_other_factions_unit(self):
        self.assert_rejected(combat_state(), AttackUnit("A", "unit-2", "unit-1"), "does not belong")

    def test_friendly_and_self_attacks_rejected(self):
        state = combat_state()
        friend = state.add_unit("A", UnitType.SCOUT, Position(0, 1))
        for target in ("unit-1", friend.id):
            with self.subTest(target=target):
                self.assert_rejected(state, AttackUnit("A", "unit-1", target), "friendly unit or self")

    def test_eliminated_actor_rejected(self):
        state = combat_state()
        state.eliminate_player("B")
        self.assert_rejected(state, AttackUnit("B", "unit-2", "unit-1"), "eliminated player")

    def test_pre_game_and_terminal_rejected(self):
        for terminal in (False, True):
            with self.subTest(terminal=terminal):
                state = combat_state()
                if terminal:
                    state.eliminate_player("B")
                    state.eliminate_player("C")
                else:
                    state.active_player_id = None
                self.assert_rejected(state, AttackUnit("A", "unit-1", "unit-2"), "no active activation")

    def test_empty_and_zero_survivor_states_rejected(self):
        self.assert_rejected(GameState(GameConfig(42)), AttackUnit("A", "u", "v"), "unknown command actor")
        state = combat_state()
        state.turn = 0
        state.active_player_id = None
        for player in "ABC":
            state.eliminate_player(player)
        self.assert_rejected(state, AttackUnit("A", "unit-1", "unit-2"), "eliminated player")

    def test_melee_distance_two_rejected_for_all_melee_types(self):
        for kind in (UnitType.SCOUT, UnitType.WARRIOR, UnitType.SPEARMAN):
            with self.subTest(kind=kind):
                self.assert_rejected(combat_state(kind, distance=2),
                                     AttackUnit("A", "unit-1", "unit-2"), "outside attack range")

    def test_archer_distance_three_rejected(self):
        self.assert_rejected(combat_state(UnitType.ARCHER, distance=3),
                             AttackUnit("A", "unit-1", "unit-2"), "outside attack range")

    def test_zero_movement_rejected_for_melee_and_ranged(self):
        for kind in (UnitType.SCOUT, UnitType.WARRIOR, UnitType.SPEARMAN, UnitType.ARCHER):
            with self.subTest(kind=kind):
                state = combat_state(kind)
                state.units["unit-1"].moves_remaining = 0
                self.assert_rejected(state, AttackUnit("A", "unit-1", "unit-2"), "no movement")

    def test_settler_cannot_attack(self):
        self.assert_rejected(combat_state(UnitType.SETTLER), AttackUnit("A", "unit-1", "unit-2"), "cannot attack")

    def test_invalid_state_rejected_without_repair(self):
        for field, value in (("hp", 0), ("hp", 101), ("moves_remaining", 2)):
            with self.subTest(field=field, value=value):
                state = combat_state()
                setattr(state.units["unit-2"], field, value)
                self.assert_rejected(state, AttackUnit("A", "unit-1", "unit-2"), "unit[.]")

    def test_move_unit_never_attacks(self):
        state = combat_state()
        state.units["unit-2"].hp = 1
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(1, 0)), "enemy-occupied")

    def test_internal_executor_rejects_invalid_ids_atomically(self):
        state = combat_state()
        before = deepcopy(state)
        for attacker, target in ((None, "unit-2"), ("unit-1", []), ("missing", "unit-2"),
                                 ("unit-1", "missing"), ("unit-1", "unit-1")):
            with self.subTest(attacker=attacker, target=target), self.assertRaises(ValueError):
                attack_unit(state, attacker, target)
            self.assertEqual(state, before)


class MeleeTests(unittest.TestCase):
    def test_adjacent_melee_damage_and_retaliation_by_type(self):
        for kind, attacker_hp, target_hp in ((UnitType.SCOUT, 60, 80),
                                            (UnitType.WARRIOR, 70, 70),
                                            (UnitType.SPEARMAN, 75, 65)):
            with self.subTest(kind=kind):
                state = combat_state(kind)
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units["unit-1"].hp, attacker_hp)
                self.assertEqual(state.units["unit-2"].hp, target_hp)
                self.assertEqual(state.units["unit-1"].moves_remaining, kind.movement_allowance - 1)
                self.assertEqual(state.units["unit-2"].moves_remaining, 1)
                state.validate()

    def test_melee_chebyshev_range_in_all_eight_directions(self):
        for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            with self.subTest(dx=dx, dy=dy):
                state = combat_state()
                state.units["unit-1"].position = Position(2, 2)
                state.units["unit-2"].position = Position(2 + dx, 2 + dy)
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units["unit-2"].hp, 70)

    def test_defender_survives_so_attacker_stays(self):
        state = combat_state()
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(state.units["unit-1"].position, Position(0, 0))
        self.assertEqual(state.units["unit-2"].position, Position(1, 0))

    def test_lethal_damage_still_allows_full_precombat_retaliation(self):
        state = combat_state(UnitType.SPEARMAN)
        state.units["unit-2"].hp = 1
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertNotIn("unit-2", state.units)
        self.assertEqual(state.units["unit-1"].hp, 75)
        self.assertEqual(state.units["unit-1"].position, Position(1, 0))
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)
        state.validate()

    def test_attacker_dies_but_still_deals_full_damage(self):
        state = combat_state()
        state.units["unit-1"].hp = 20
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertNotIn("unit-1", state.units)
        self.assertEqual(state.units["unit-2"].hp, 70)
        self.assertEqual(state.units["unit-2"].position, Position(1, 0))
        state.validate()

    def test_both_may_die_in_same_combat(self):
        for hp in (20, 30):
            with self.subTest(hp=hp):
                state = combat_state()
                for unit in state.units.values():
                    unit.hp = hp
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units, {})
                self.assertEqual(to_snapshot(state)["units"], [])
                self.assertEqual((state.active_player_id, state.turn, state.turn_order), ("A", 0, list("ABC")))
                self.assertTrue(all(not p.eliminated for p in state.players.values()))

    def test_one_hp_survivor_advances_at_no_extra_cost(self):
        state = combat_state(UnitType.SCOUT, UnitType.SCOUT)
        state.units["unit-1"].hp = 31
        state.units["unit-2"].hp = 30
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        attacker = state.units["unit-1"]
        self.assertEqual((attacker.hp, attacker.position, attacker.moves_remaining), (1, Position(1, 0), 1))
        self.assertNotIn("unit-2", state.units)
        state.validate()

    def test_enemy_stack_prevents_advance_and_remains_movement_blocker(self):
        state = combat_state(UnitType.SCOUT)
        other = state.add_unit("B", UnitType.SETTLER, Position(1, 0))
        before_other = deepcopy(other)
        state.units["unit-2"].hp = 1
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertNotIn("unit-2", state.units)
        self.assertEqual(other, before_other)
        self.assertEqual(state.units["unit-1"].position, Position(0, 0))
        self.assertEqual(state.units["unit-1"].moves_remaining, 1)
        self.assertIsNone(find_path(state, state.units["unit-1"], Position(1, 0)))
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "enemy-occupied"):
            apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
        self.assertEqual(state, before)
        # A second explicit attack removes the final hostile and permits advance.
        apply_command(state, AttackUnit("A", "unit-1", other.id))
        self.assertEqual(state.units["unit-1"].position, Position(1, 0))
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)
        state.validate()

    def test_two_movement_scout_can_attack_twice_without_ending_activation(self):
        state = combat_state(UnitType.SCOUT, UnitType.SCOUT)
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(state.units["unit-1"].moves_remaining, 1)
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)
        self.assertEqual((state.units["unit-1"].hp, state.units["unit-2"].hp), (40, 40))
        self.assertEqual((state.active_player_id, state.turn, state.turn_order), ("A", 0, list("ABC")))

    def test_movement_and_attack_share_budget_in_either_order(self):
        for attack_first in (False, True):
            with self.subTest(attack_first=attack_first):
                state = combat_state(UnitType.SCOUT)
                attack = AttackUnit("A", "unit-1", "unit-2")
                move = MoveUnit("A", "unit-1", Position(0, 1))
                for command in ((attack, move) if attack_first else (move, attack)):
                    apply_command(state, command)
                self.assertEqual(state.units["unit-1"].moves_remaining, 0)
                self.assertEqual(state.units["unit-1"].position, Position(0, 1))
                self.assertEqual(state.units["unit-2"].hp, 80)

    def test_archer_defends_and_retaliates_with_normal_strength(self):
        state = combat_state(UnitType.WARRIOR, UnitType.ARCHER)
        state.units["unit-2"].moves_remaining = 0
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(state.units["unit-1"].hp, 80)
        self.assertEqual(state.units["unit-2"].hp, 60)
        self.assertEqual(state.units["unit-2"].moves_remaining, 0)

    def test_melee_settler_destruction_without_retaliation(self):
        for hp in (1, 100):
            with self.subTest(hp=hp):
                state = combat_state(UnitType.SCOUT, UnitType.SETTLER)
                state.units["unit-1"].hp = 1
                state.units["unit-2"].hp = hp
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertNotIn("unit-2", state.units)
                attacker = state.units["unit-1"]
                self.assertEqual((attacker.hp, attacker.position, attacker.moves_remaining), (1, Position(1, 0), 1))
                self.assertFalse(state.players["B"].eliminated)
                state.validate()

    def test_destroying_settler_in_stack_does_not_damage_escort_or_advance(self):
        state = combat_state(UnitType.WARRIOR, UnitType.SETTLER)
        escort = state.add_unit("B", UnitType.SPEARMAN, Position(1, 0))
        before_escort = deepcopy(escort)
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertNotIn("unit-2", state.units)
        self.assertEqual(escort, before_escort)
        self.assertEqual(state.units["unit-1"].hp, 100)
        self.assertEqual(state.units["unit-1"].position, Position(0, 0))
        state.validate()

    def test_friendly_stack_on_origin_does_not_join_combat(self):
        state = combat_state()
        friend = state.add_unit("A", UnitType.SCOUT, Position(0, 0))
        before_friend = deepcopy(friend)
        state.units["unit-2"].hp = 1
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(friend, before_friend)
        self.assertEqual(state.units["unit-1"].position, Position(1, 0))
        state.validate()


class RangedTests(unittest.TestCase):
    def test_range_one_and_two_use_ranged_damage_without_retaliation(self):
        for distance in (1, 2):
            with self.subTest(distance=distance):
                state = combat_state(UnitType.ARCHER, distance=distance)
                state.units["unit-1"].hp = 1
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units["unit-2"].hp, 70)
                self.assertEqual(state.units["unit-2"].moves_remaining, 1)
                self.assertEqual(state.units["unit-1"].hp, 1)
                self.assertEqual(state.units["unit-1"].position, Position(0, 0))
                self.assertEqual(state.units["unit-1"].moves_remaining, 0)
                self.assertEqual((state.active_player_id, state.turn), ("A", 0))

    def test_diagonal_range_two_in_each_quadrant(self):
        for dx, dy in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
            with self.subTest(dx=dx, dy=dy):
                state = combat_state(UnitType.ARCHER)
                state.units["unit-1"].position = Position(2, 2)
                state.units["unit-2"].position = Position(2 + dx, 2 + dy)
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units["unit-2"].hp, 70)

    def test_ranged_kill_never_advances(self):
        for distance in (1, 2):
            with self.subTest(distance=distance):
                state = combat_state(UnitType.ARCHER, distance=distance)
                state.units["unit-2"].hp = 30
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertNotIn("unit-2", state.units)
                self.assertEqual(state.units["unit-1"].position, Position(0, 0))
                self.assertEqual(state.units["unit-1"].hp, 100)
                self.assertEqual(state.units["unit-1"].moves_remaining, 0)
                state.validate()

    def test_ranged_destroys_settler_without_moving(self):
        state = combat_state(UnitType.ARCHER, UnitType.SETTLER, distance=2)
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertNotIn("unit-2", state.units)
        self.assertEqual(state.units["unit-1"].position, Position(0, 0))
        self.assertEqual(state.units["unit-1"].hp, 100)
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)

    def test_only_selected_stack_member_is_damaged_or_killed(self):
        for hp in (1, 100):
            with self.subTest(hp=hp):
                state = combat_state(UnitType.ARCHER, distance=2)
                chosen = state.add_unit("B", UnitType.SCOUT, Position(2, 0))
                chosen.hp = hp
                unchosen = deepcopy(state.units["unit-2"])
                apply_command(state, AttackUnit("A", "unit-1", chosen.id))
                self.assertEqual(state.units["unit-2"], unchosen)
                if hp == 1:
                    self.assertNotIn(chosen.id, state.units)
                else:
                    self.assertEqual(chosen.hp, 60)
                self.assertEqual(state.units["unit-1"].position, Position(0, 0))
                state.validate()

    def test_no_line_of_sight_over_terrain(self):
        for terrain in Terrain:
            with self.subTest(terrain=terrain):
                state = combat_state(UnitType.ARCHER, distance=2)
                state.tiles[Position(1, 0)].terrain = terrain
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units["unit-2"].hp, 70)

    def test_no_line_of_sight_over_units(self):
        for owner in "AB":
            with self.subTest(owner=owner):
                state = combat_state(UnitType.ARCHER, distance=2)
                blocker = state.add_unit(owner, UnitType.SPEARMAN, Position(1, 0))
                before_blocker = deepcopy(blocker)
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(blocker, before_blocker)
                self.assertEqual(state.units["unit-2"].hp, 70)

    def test_target_terrain_has_no_defense_modifier(self):
        for terrain in (Terrain.GRASSLAND, Terrain.PLAINS, Terrain.FOREST, Terrain.HILLS):
            with self.subTest(terrain=terrain):
                state = combat_state(UnitType.ARCHER)
                state.tiles[Position(1, 0)].terrain = terrain
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertEqual(state.units["unit-2"].hp, 70)


class CombatPersistenceTests(unittest.TestCase):
    def test_mid_activation_round_trip_preserves_hp_movement_and_continuation(self):
        state = combat_state(UnitType.SCOUT, UnitType.SCOUT)
        command = AttackUnit("A", "unit-1", "unit-2")
        apply_command(state, command)
        snapshot = to_snapshot(state)
        self.assertEqual(snapshot["schema_version"], 12)
        restored = from_snapshot(json.loads(json.dumps(snapshot)))
        self.assertEqual(restored, state)
        self.assertEqual((restored.units["unit-1"].hp, restored.units["unit-1"].moves_remaining), (70, 1))
        self.assertEqual(restored.units["unit-2"].hp, 70)
        for candidate in (state, restored):
            apply_command(candidate, command)
        self.assertEqual(restored, state)
        loaded = from_snapshot(to_snapshot(restored))
        self.assertEqual((loaded.units["unit-1"].hp, loaded.units["unit-1"].moves_remaining), (40, 0))

    def test_snapshot_requires_hp_and_rejects_derived_stats(self):
        baseline = to_snapshot(combat_state())
        self.assertEqual(set(baseline["units"][0]),
                         {"id", "owner_id", "unit_type", "position", "moves_remaining", "hp", "home_camp_id"})
        missing = deepcopy(baseline)
        del missing["units"][0]["hp"]
        with self.assertRaisesRegex(ValueError, "exactly these fields"):
            from_snapshot(missing)
        for field in ("combat_strength", "ranged_strength", "attack_range", "max_hp"):
            snapshot = deepcopy(baseline)
            snapshot["units"][0][field] = 100
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "exactly these fields"):
                from_snapshot(snapshot)

    def test_old_schemas_rejected_without_supplying_hp(self):
        for version in (1, 2, 3):
            snapshot = to_snapshot(combat_state())
            snapshot["schema_version"] = version
            for row in snapshot["units"]:
                del row["hp"]
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "unsupported schema_version"):
                from_snapshot(snapshot)

    def test_copies_have_independent_hp_and_combat(self):
        source = combat_state()
        source.units["unit-1"].hp = 80
        snapshot = to_snapshot(source)
        first, second = deepcopy(source), from_snapshot(snapshot)
        apply_command(first, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(second, source)
        self.assertEqual(to_snapshot(source), snapshot)
        apply_command(second, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(first, second)
        first.units["unit-1"].hp = 1
        snapshot["units"][0]["hp"] = 2
        self.assertEqual(second.units["unit-1"].hp, 50)
        self.assertEqual(source.units["unit-1"].hp, 80)

    def test_dead_units_absent_after_round_trip_and_ids_not_reused(self):
        state = combat_state()
        state.units["unit-2"].hp = 1
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        restored = from_snapshot(to_snapshot(state))
        self.assertEqual(set(restored.units), {"unit-1"})
        self.assertEqual(restored.units["unit-1"].hp, 70)
        self.assertEqual(restored.add_unit("B", UnitType.SCOUT, Position(4, 4)).id, "unit-3")

    def test_activation_refreshes_movement_but_never_heals(self):
        state = combat_state()
        state.units["unit-2"].moves_remaining = 0
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        for player in "ABC":
            apply_command(state, EndActivation(player))
            self.assertEqual(state.units["unit-1"].hp, 70)
            self.assertEqual(state.units["unit-2"].hp, 70)
        self.assertEqual((state.turn, state.active_player_id), (1, "A"))
        self.assertEqual(state.units["unit-1"].moves_remaining, 1)
        self.assertEqual(state.units["unit-2"].moves_remaining, 1)

    def test_explicit_elimination_still_removes_remaining_damaged_units(self):
        state = combat_state()
        state.add_unit("B", UnitType.SCOUT, Position(2, 0))
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        apply_command(state, EliminatePlayer("A", "B"))
        self.assertEqual(set(state.units), {"unit-1"})
        self.assertTrue(state.players["B"].eliminated)
        self.assertEqual(state.turn_order, ["A", "C"])
        self.assertEqual((state.active_player_id, state.turn), ("A", 0))
        self.assertEqual((state.units["unit-1"].hp, state.units["unit-1"].moves_remaining), (70, 0))
        state.validate()

    def test_combat_independent_of_seed_and_dictionary_insertion_order(self):
        source = combat_state(UnitType.SCOUT)
        source.add_unit("B", UnitType.SCOUT, Position(1, 0))
        source.units["unit-2"].hp = 1
        for seed in (0, 42, -17):
            for reverse in (False, True):
                with self.subTest(seed=seed, reverse=reverse):
                    state = deepcopy(source)
                    state.config = GameConfig(seed)
                    if reverse:
                        for field in ("players", "units", "tiles"):
                            setattr(state, field, dict(reversed(list(getattr(state, field).items()))))
                    apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                    snapshot = to_snapshot(state)
                    snapshot["config"]["seed"] = 42
                    if seed == 0 and not reverse:
                        expected = snapshot
                    self.assertEqual(snapshot, expected)


if __name__ == "__main__":
    unittest.main()
