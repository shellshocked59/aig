"""Single-target construction, atomic owner economy and deterministic persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest
from unittest.mock import patch

from aig.commands import (
    EliminatePlayer, EndActivation, FoundCity, SetCityProduction, apply_command,
)
from aig.economy import Yields, city_yields, resolve_player_economy
from aig.production import production_cost, production_remaining
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    CityState, ControllerType, GameConfig, GameMap, GameState, PlayerState,
    Position, Technology, Terrain, TileState, UnitState, UnitType,
)


def production_state():
    state = GameState(
        # Production fixtures intentionally know every unit unlock.
        GameConfig(42), players={p: PlayerState(p, ControllerType.HUMAN,
            researched_technologies=frozenset(Technology)) for p in "ABC"},
        turn_order=list("ABC"), active_player_id="A", game_map=GameMap(8, 5),
        tiles={Position(x, y): TileState(Position(x, y))
               for y in range(5) for x in range(8)},
    )
    state.add_city(CityState("a", "A", Position(1, 1), name="Alpha"))
    return state


def ready_city(state, city_id="a", unit_type=UnitType.WARRIOR, stored=19):
    city = state.cities[city_id]
    city.production_target = unit_type
    city.production_stored = stored
    return city


class ProductionQueryTests(unittest.TestCase):
    def test_costs_and_deterministic_lookup(self):
        for unit_type, cost in ((UnitType.WARRIOR, 20), (UnitType.SCOUT, 20),
                                (UnitType.ARCHER, 30), (UnitType.SPEARMAN, 30),
                                (UnitType.SETTLER, 40)):
            with self.subTest(unit_type=unit_type):
                self.assertEqual(unit_type.production_cost, cost)
                self.assertEqual([production_cost(unit_type) for _ in range(3)], [cost] * 3)

    def test_cost_rejects_non_unit_types(self):
        for value in (None, "warrior", "building", 20, True, [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                production_cost(value)

    def test_city_defaults_and_existing_stockpile(self):
        for stored in (0, 17, 10**30):
            city = CityState("a", "A", Position(0, 0), name="Alpha", production_stored=stored)
            self.assertIsNone(city.production_target)
            self.assertEqual(city.production_stored, stored)
            self.assertIsNone(production_remaining(city))

    def test_city_accepts_every_target_and_copy_preserves_it(self):
        for target in UnitType:
            with self.subTest(target=target):
                city = CityState("a", "A", Position(0, 0), name="Alpha",
                                 production_target=target, production_stored=17)
                copied = deepcopy(city)
                self.assertEqual(copied, city)
                copied.production_target = None
                self.assertIs(city.production_target, target)

    def test_invalid_city_targets_rejected_at_construction_and_validation(self):
        for value in ("warrior", "WARRIOR", "building", "", 0, True, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    CityState("a", "A", Position(0, 0), name="Alpha", production_target=value)
                state = production_state()
                state.cities["a"].production_target = value
                before = deepcopy(state)
                for validate in (state.validate, lambda: to_snapshot(state)):
                    with self.assertRaises(ValueError):
                        validate()
                    self.assertEqual(state, before)

    def test_remaining_is_pure_and_floors_at_zero(self):
        state = production_state()
        city = ready_city(state, unit_type=UnitType.ARCHER)
        for stored, remaining in ((0, 30), (17, 13), (29, 1), (30, 0), (10**30, 0)):
            city.production_stored = stored
            before = deepcopy(state)
            self.assertEqual(production_remaining(city), remaining)
            self.assertEqual(state, before)
        city.production_target = None
        self.assertIsNone(production_remaining(city))

    def test_remaining_validates_city_and_storage(self):
        with self.assertRaises(ValueError):
            production_remaining(None)
        for stored in (-1, True, 1.5, "20"):
            state = production_state()
            city = ready_city(state)
            city.production_stored = stored
            with self.subTest(stored=stored), self.assertRaises(ValueError):
                production_remaining(city)


class ProductionCommandTests(unittest.TestCase):
    def assert_rejected(self, state, command):
        before = deepcopy(state)
        with self.assertRaises(ValueError):
            apply_command(state, command)
        self.assertEqual(state, before)

    def test_command_is_frozen_and_validates_fields(self):
        command = SetCityProduction("A", "a", UnitType.WARRIOR)
        with self.assertRaises(FrozenInstanceError):
            command.unit_type = None
        for actor, city, target in (("", "a", None), ("A", "", None),
                                   ("A", "a", "warrior"), ("A", "a", [])):
            with self.subTest(actor=actor, city=city, target=target), self.assertRaises(ValueError):
                SetCityProduction(actor, city, target)

    def test_active_actor_can_set_every_type_without_other_changes(self):
        for target in UnitType:
            with self.subTest(target=target):
                state = production_state()
                unit = state.add_unit("A", UnitType.SCOUT, Position(1, 1))
                unit.moves_remaining = 1
                state.cities["a"].production_stored = 1000
                expected = deepcopy(state)
                expected.cities["a"].production_target = target
                self.assertIsNone(apply_command(state, SetCityProduction("A", "a", target)))
                self.assertEqual(state, expected)

    def test_switch_and_clear_preserve_generic_stockpile_and_activation(self):
        state = production_state()
        city = ready_city(state, stored=17)
        for target in (UnitType.ARCHER, UnitType.ARCHER, None, None, UnitType.SCOUT):
            with self.subTest(target=target):
                expected = deepcopy(state)
                expected.cities["a"].production_target = target
                apply_command(state, SetCityProduction("A", "a", target))
                self.assertEqual(state, expected)
                self.assertEqual(city.production_stored, 17)

    def test_inactive_unknown_and_eliminated_actors_rejected(self):
        for actor in ("B", "missing", "C"):
            state = production_state()
            state.eliminate_player("C")
            with self.subTest(actor=actor):
                self.assert_rejected(state, SetCityProduction(actor, "a", UnitType.WARRIOR))

    def test_pregame_and_terminal_rejected(self):
        for terminal in (False, True):
            state = production_state()
            if terminal:
                state.eliminate_player("B")
                state.eliminate_player("C")
            else:
                state.active_player_id = None
            with self.subTest(terminal=terminal):
                self.assert_rejected(state, SetCityProduction("A", "a", UnitType.WARRIOR))

    def test_unknown_enemy_city_and_enemy_clear_rejected(self):
        state = production_state()
        state.add_city(CityState("b", "B", Position(4, 1), name="Beta"))
        for city_id in ("missing", "b"):
            for target in (UnitType.WARRIOR, None):
                with self.subTest(city_id=city_id, target=target):
                    self.assert_rejected(state, SetCityProduction("A", city_id, target))

    def test_runtime_invalid_target_revalidated_before_mutation(self):
        state = production_state()
        for target in ("archer", "building", True, 30, [], {}):
            command = SetCityProduction("A", "a", None)
            object.__setattr__(command, "unit_type", target)
            with self.subTest(target=target):
                self.assert_rejected(state, command)

    def test_invalid_state_rejected_without_repair(self):
        state = production_state()
        state.cities["a"].production_stored = -1
        self.assert_rejected(state, SetCityProduction("A", "a", UnitType.WARRIOR))


class ProductionCompletionTests(unittest.TestCase):
    def test_below_cost_accumulates_and_keeps_target(self):
        state = production_state()
        city = ready_city(state, stored=18)
        apply_command(state, EndActivation("A"))
        self.assertEqual(city.production_stored, 19)
        self.assertIs(city.production_target, UnitType.WARRIOR)
        self.assertEqual(state.units, {})
        self.assertEqual(state.next_unit_id, 1)

    def test_every_unit_exact_cost_owner_position_hp_and_zero_movement(self):
        for target in UnitType:
            with self.subTest(target=target):
                state = production_state()
                city = ready_city(state, unit_type=target, stored=production_cost(target) - 1)
                apply_command(state, EndActivation("A"))
                self.assertEqual(city.production_stored, 0)
                self.assertIsNone(city.production_target)
                self.assertEqual(list(state.units), ["unit-1"])
                unit = state.units["unit-1"]
                self.assertEqual((unit.owner_id, unit.position, unit.unit_type, unit.hp,
                                  unit.moves_remaining), ("A", city.position, target, 100, 0))
                self.assertEqual(unit.unit_type.combat_strength, target.combat_strength)
                self.assertEqual((state.active_player_id, state.turn), ("B", 0))
                state.validate()

    def test_new_production_pushes_over_threshold_retaining_overflow(self):
        state = production_state()
        city = ready_city(state, unit_type=UnitType.ARCHER, stored=27)
        city.population = 3
        for tile in state.tiles.values():
            tile.terrain = Terrain.FOREST
        self.assertEqual(city_yields(state, city).production, 8)
        apply_command(state, EndActivation("A"))
        self.assertEqual(city.production_stored, 5)
        self.assertIsNone(city.production_target)
        self.assertIs(state.units["unit-1"].unit_type, UnitType.ARCHER)

    def test_large_stockpile_completes_once_without_repeat(self):
        state = production_state()
        city = ready_city(state, stored=10**30)
        apply_command(state, EndActivation("A"))
        self.assertEqual(city.production_stored, 10**30 - 19)
        for actor in "BCA":
            apply_command(state, EndActivation(actor))
        self.assertEqual(len(state.units), 1)
        self.assertEqual(state.next_unit_id, 2)
        self.assertIsNone(city.production_target)
        self.assertEqual(city.production_stored, 10**30 - 18)

    def test_cleared_target_does_not_complete_even_when_affordable(self):
        state = production_state()
        city = ready_city(state, stored=1000)
        apply_command(state, SetCityProduction("A", "a", None))
        apply_command(state, EndActivation("A"))
        self.assertEqual((city.production_stored, state.next_unit_id), (1001, 1))
        self.assertEqual(state.units, {})

    def test_next_owner_activation_refreshes_all_produced_types(self):
        for target in UnitType:
            with self.subTest(target=target):
                state = production_state()
                ready_city(state, unit_type=target, stored=100)
                apply_command(state, EndActivation("A"))
                unit = state.units["unit-1"]
                apply_command(state, EndActivation("B"))
                self.assertEqual(unit.moves_remaining, 0)
                apply_command(state, EndActivation("C"))
                self.assertEqual(unit.moves_remaining, target.movement_allowance)
                self.assertEqual(unit.hp, 100)
                self.assertEqual((state.active_player_id, state.turn), ("A", 1))

    def test_setup_units_still_start_with_full_movement(self):
        state = production_state()
        for target in UnitType:
            with self.subTest(target=target):
                unit = state.add_unit("A", target, Position(1, 1))
                self.assertEqual((unit.moves_remaining, unit.hp), (target.movement_allowance, 100))

    def test_production_stacks_with_multiple_friends_without_changing_them(self):
        state = production_state()
        city = ready_city(state)
        for target in (UnitType.SCOUT, UnitType.SETTLER, UnitType.WARRIOR):
            unit = state.add_unit("A", target, city.position)
            unit.moves_remaining = 0
            unit.hp = 50
        friends = deepcopy(state.units)
        apply_command(state, EndActivation("A"))
        self.assertEqual(len(state.units), 4)
        for unit_id, friend in friends.items():
            self.assertEqual(state.units[unit_id], friend)
        self.assertEqual(state.units["unit-4"].position, city.position)
        state.validate()

    def test_food_growth_gold_and_only_outgoing_city_production(self):
        state = production_state()
        city = ready_city(state)
        for tile in state.tiles.values():
            if tile.position != city.position:
                tile.terrain = Terrain.WATER
        city.food_stored = 14
        state.players["A"].gold = 7
        state.tiles[Position(4, 1)].terrain = Terrain.GRASSLAND
        enemy = state.add_city(CityState("b", "B", Position(4, 1), name="Beta",
                                        production_stored=100, production_target=UnitType.SCOUT))
        before_enemy = deepcopy(enemy)
        self.assertEqual(city_yields(state, city), Yields(3, 1, 1))
        apply_command(state, EndActivation("A"))
        self.assertEqual((city.population, city.food_stored, city.production_stored), (2, 0, 0))
        self.assertEqual(state.players["A"].gold, 8)
        self.assertEqual(state.players["B"].gold, 0)
        self.assertEqual(enemy, before_enemy)
        self.assertEqual([u.owner_id for u in state.units.values()], ["A"])

    def test_invalid_end_activation_never_produces(self):
        for actor in ("B", "missing", "C"):
            state = production_state()
            ready_city(state, stored=100)
            state.eliminate_player("C")
            before = deepcopy(state)
            with self.subTest(actor=actor), self.assertRaises(ValueError):
                apply_command(state, EndActivation(actor))
            self.assertEqual(state, before)

    def test_hostile_center_rejected_before_any_economy_changes(self):
        state = production_state()
        ready_city(state)
        state.add_city(CityState("z", "A", Position(4, 1), name="Zulu",
                                 production_stored=19, production_target=UnitType.WARRIOR))
        state.units["hostile"] = UnitState("hostile", "B", Position(4, 1))
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "hostile city and unit"):
            apply_command(state, EndActivation("A"))
        self.assertEqual(state, before)

    def test_later_spawn_failure_rolls_back_all_city_economy_and_allocator(self):
        state = production_state()
        city = ready_city(state)
        city.food_stored = 14
        state.add_city(CityState("z", "A", Position(4, 1), name="Zulu",
                                 production_stored=19, production_target=UnitType.WARRIOR))
        before = deepcopy(state)
        original = GameState.can_enter

        def reject_second(game, owner_id, position, **kwargs):
            return position != Position(4, 1) and original(game, owner_id, position, **kwargs)

        # Exercise a future placement restriction after the first spawn has
        # already been prepared, without making the input state invalid.
        with patch.object(GameState, "can_enter", reject_second):
            with self.assertRaisesRegex(ValueError, "unit position"):
                apply_command(state, EndActivation("A"))
        self.assertEqual(state, before)
        apply_command(state, EndActivation("A"))
        self.assertEqual(list(state.units), ["unit-1", "unit-2"])


class ProductionAllocatorTests(unittest.TestCase):
    def test_first_and_subsequent_ids_and_no_reuse_after_removal(self):
        state = production_state()
        ready_city(state)
        apply_command(state, EndActivation("A"))
        self.assertEqual(list(state.units), ["unit-1"])
        del state.units["unit-1"]
        for actor in "BC":
            apply_command(state, EndActivation(actor))
        state.cities["a"].production_stored = 19
        apply_command(state, SetCityProduction("A", "a", UnitType.SCOUT))
        apply_command(state, EndActivation("A"))
        self.assertEqual(list(state.units), ["unit-2"])
        self.assertEqual(state.next_unit_id, 3)
        self.assertEqual(state.add_unit("B", UnitType.ARCHER, Position(7, 4)).id, "unit-3")

    def test_explicit_id_collisions_are_skipped_without_overwrites(self):
        state = production_state()
        ready_city(state)
        for unit_id in ("unit-1", "unit-2", "unit-4", "custom"):
            state.units[unit_id] = UnitState(unit_id, "A", Position(1, 1))
        before = deepcopy(state.units)
        apply_command(state, EndActivation("A"))
        self.assertEqual(state.next_unit_id, 4)
        self.assertIn("unit-3", state.units)
        for unit_id, unit in before.items():
            self.assertEqual(state.units[unit_id], unit)
        self.assertEqual(state.add_unit("A", UnitType.SCOUT, Position(1, 1)).id, "unit-5")

    def test_multi_city_ids_use_lexical_city_order_independent_of_insertion(self):
        source = production_state()
        del source.cities["a"]
        source.players["A"].has_ever_owned_city = False
        for city_id, position, target in (("city-2", Position(1, 1), UnitType.SCOUT),
                                          ("city-10", Position(4, 1), UnitType.ARCHER)):
            source.add_city(CityState(city_id, "A", position, name=city_id,
                                     production_target=target, production_stored=100))
        source.units["unit-2"] = UnitState("unit-2", "B", Position(7, 4))
        first, second = deepcopy(source), from_snapshot(to_snapshot(source))
        second.cities = dict(reversed(list(source.cities.items())))
        second.cities = deepcopy(second.cities)
        apply_command(first, EndActivation("A"))
        self.assertEqual(source.next_unit_id, 1)
        self.assertEqual(second.next_unit_id, 1)
        apply_command(second, EndActivation("A"))
        self.assertEqual(first, second)
        self.assertEqual(to_snapshot(first), to_snapshot(second))
        self.assertEqual(first.units["unit-1"].position, Position(4, 1))
        self.assertIs(first.units["unit-1"].unit_type, UnitType.ARCHER)
        self.assertEqual(first.units["unit-3"].position, Position(1, 1))
        self.assertIs(first.units["unit-3"].unit_type, UnitType.SCOUT)
        self.assertEqual(first.next_unit_id, 4)


class FoundingAndEliminationProductionTests(unittest.TestCase):
    def test_found_set_target_and_resolve_during_same_activation(self):
        state = production_state()
        del state.cities["a"]
        state.players["A"].has_ever_owned_city = False
        settler = state.add_unit("A", UnitType.SETTLER, Position(1, 1))
        apply_command(state, FoundCity("A", settler.id, "a", "Alpha"))
        city = state.cities["a"]
        self.assertEqual((city.production_stored, city.production_target), (0, None))
        apply_command(state, SetCityProduction("A", "a", UnitType.WARRIOR))
        apply_command(state, EndActivation("A"))
        self.assertEqual((city.food_stored, city.production_stored), (2, 1))
        self.assertIs(city.production_target, UnitType.WARRIOR)
        self.assertEqual(state.units, {})

    def test_new_city_can_complete_if_first_yields_are_sufficient(self):
        state = production_state()
        del state.cities["a"]
        state.players["A"].has_ever_owned_city = False
        settler = state.add_unit("A", UnitType.SETTLER, Position(1, 1))
        apply_command(state, FoundCity("A", settler.id, "a", "Alpha"))
        apply_command(state, SetCityProduction("A", "a", UnitType.WARRIOR))
        # Current population-1 terrain yields cannot reach cost 20. Isolate
        # sufficient yields to verify that founding adds no completion delay.
        with patch("aig.economy.city_yields", return_value=Yields(4, 20, 1)):
            apply_command(state, EndActivation("A"))
        city = state.cities["a"]
        self.assertEqual((city.food_stored, city.production_stored, city.production_target), (2, 0, None))
        self.assertEqual(state.units["unit-2"].moves_remaining, 0)

    def test_active_elimination_skips_production_and_advances_once(self):
        for active, expected_turn, expected_order in (("A", 0, ["B", "C"]),
                                                     ("C", 1, ["A", "B"])):
            state = production_state()
            city = ready_city(state, stored=100)
            city.owner_id = active
            for p in state.players.values():
                p.has_ever_owned_city = any(c.owner_id == p.id for c in state.cities.values())
            state.active_player_id = active
            state.add_unit(active, UnitType.SCOUT, city.position)
            state.players[active].gold = 7
            before_city, next_id = deepcopy(city), state.next_unit_id
            apply_command(state, EliminatePlayer(active, active))
            self.assertEqual(state.cities, {})
            self.assertEqual(state.units, {})
            self.assertEqual(city, before_city)
            self.assertEqual(state.players[active].gold, 7)
            self.assertEqual(state.next_unit_id, next_id)
            self.assertEqual((state.active_player_id, state.turn, state.turn_order),
                             (expected_order[0], expected_turn, expected_order))
            before = deepcopy(state)
            for operation in (lambda: apply_command(state, EndActivation(active)),
                              lambda: resolve_player_economy(state, active)):
                with self.assertRaises(ValueError):
                    operation()
                self.assertEqual(state, before)

    def test_terminal_self_elimination_never_completes_survivor_target(self):
        state = production_state()
        state.eliminate_player("C")
        ready_city(state, stored=100)
        survivor = state.add_city(CityState("b", "B", Position(4, 1), name="Beta",
                                           production_target=UnitType.SCOUT, production_stored=100))
        before = deepcopy(survivor)
        apply_command(state, EliminatePlayer("A", "A"))
        self.assertIsNone(state.active_player_id)
        self.assertEqual(state.turn, 0)
        self.assertEqual(state.units, {})
        self.assertEqual(state.next_unit_id, 1)
        self.assertEqual(survivor, before)

    def test_removed_city_spawns_nothing(self):
        state = production_state()
        ready_city(state, stored=100)
        state.remove_city("a")
        with self.assertRaises(ValueError):
            apply_command(state, EndActivation("A"))
        self.assertEqual(state.units, {})
        self.assertEqual(state.next_unit_id, 1)


class ProductionSnapshotTests(unittest.TestCase):
    def test_all_targets_json_round_trip_with_no_load_side_effects(self):
        for target in (*UnitType, None):
            for stored in (29, 100):
                with self.subTest(target=target, stored=stored):
                    state = production_state()
                    ready_city(state, unit_type=target, stored=stored)
                    state.next_unit_id = 23
                    before = deepcopy(state)
                    snapshot = json.loads(json.dumps(to_snapshot(state)))
                    wire_before = deepcopy(snapshot)
                    restored = from_snapshot(snapshot)
                    self.assertEqual(restored, before)
                    self.assertEqual(state, before)
                    self.assertEqual(snapshot, wire_before)
                    self.assertEqual(restored.units, {})
                    self.assertEqual(snapshot["cities"][0]["production_target"],
                                     target.value if target is not None else None)

    def test_midbuild_then_produced_unit_and_allocator_round_trip(self):
        state = production_state()
        ready_city(state, unit_type=UnitType.ARCHER, stored=29)
        state.next_unit_id = 8
        saved = from_snapshot(to_snapshot(state))
        self.assertEqual(saved.cities["a"].production_stored, 29)
        apply_command(saved, EndActivation("A"))
        self.assertEqual(state.next_unit_id, 8)
        self.assertEqual(state.units, {})
        restored = from_snapshot(json.loads(json.dumps(to_snapshot(saved))))
        self.assertEqual(restored, saved)
        self.assertEqual(restored.units["unit-8"].moves_remaining, 0)
        self.assertIsNone(restored.cities["a"].production_target)
        self.assertEqual(restored.next_unit_id, 9)
        self.assertEqual(restored.add_unit("B", UnitType.WARRIOR, Position(7, 4)).id, "unit-9")
        self.assertEqual(saved.next_unit_id, 9)

    def test_strict_v9_shape_and_no_derived_fields(self):
        snapshot = to_snapshot(production_state())
        self.assertEqual(snapshot["schema_version"], 12)
        self.assertEqual(set(snapshot["cities"][0]), {
            "id", "owner_id", "position", "name", "population", "food_stored",
            "production_stored", "production_target",
        })
        missing = deepcopy(snapshot)
        del missing["cities"][0]["production_target"]
        with self.assertRaises(ValueError):
            from_snapshot(missing)
        for field in ("production_cost", "production_remaining", "production_queue"):
            malformed = deepcopy(snapshot)
            malformed["cities"][0][field] = 20
            with self.subTest(field=field), self.assertRaises(ValueError):
                from_snapshot(malformed)

    def test_invalid_serialized_targets_rejected_without_repair(self):
        baseline = to_snapshot(production_state())
        for value in ("WARRIOR", "building", "", " archer ", 0, True, 30.0, [], {}):
            snapshot = deepcopy(baseline)
            snapshot["cities"][0]["production_target"] = value
            before = deepcopy(snapshot)
            with self.subTest(value=value), self.assertRaises(ValueError):
                from_snapshot(snapshot)
            self.assertEqual(snapshot, before)

    def test_all_previous_versions_rejected_including_actual_v6_shape(self):
        for version in range(1, 8):
            snapshot = to_snapshot(production_state())
            snapshot["schema_version"] = version
            del snapshot["cities"][0]["production_target"]
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "unsupported schema_version"):
                from_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
