"""Live cities, atomic founding, occupancy, elimination and strict persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest

from aig.cities import found_city
from aig.commands import AttackUnit, EliminatePlayer, EndActivation, FoundCity, MoveUnit, apply_command
from aig.movement import find_path
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import CityState, GameState, Position, Terrain, TileState, UnitState, UnitType
from test_combat import combat_state
from test_movement import movement_state


def city(city_id="city-1", owner="A", position=Position(0, 0), *, name="New Hope", population=1):
    return CityState(city_id, owner, position, name=name, population=population)


def founding_state():
    return movement_state(UnitType.SETTLER)


def founding_command(**overrides):
    return FoundCity(**dict(
        {"actor_id": "A", "settler_unit_id": "unit-1", "city_id": "city-1", "city_name": "New Hope"},
        **overrides,
    ))


class CityModelTests(unittest.TestCase):
    def assert_add_rejected(self, state, candidate, error):
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, error):
            state.add_city(candidate)
        self.assertEqual(state, before)

    def test_construction_and_default_population(self):
        candidate = CityState("explicit-id", "A", Position(1, 2), name="New Hope")
        self.assertEqual((candidate.id, candidate.owner_id, candidate.position, candidate.name,
                          candidate.population), ("explicit-id", "A", Position(1, 2), "New Hope", 1))

    def test_zero_population_rejected(self):
        with self.assertRaisesRegex(ValueError, "population"):
            city(population=0)

    def test_negative_population_rejected(self):
        with self.assertRaisesRegex(ValueError, "population"):
            city(population=-1)

    def test_population_requires_integer_without_upper_bound(self):
        for value in (True, False, 1.0, "1", None, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                city(population=value)
        self.assertEqual(city(population=10**30).population, 10**30)

    def test_name_requires_nonblank_string(self):
        for value in ("", " \t\n", None, [], True, 7):
            with self.subTest(value=value), self.assertRaises(ValueError):
                city(name=value)

    def test_name_preserves_supplied_spelling_and_whitespace(self):
        self.assertEqual(city(name="  São Paulo  ").name, "  São Paulo  ")

    def test_ids_owner_and_position_strictly_validated(self):
        for value in ("", " \t", None, [], 1, True):
            for field in ("city_id", "owner"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    city(**{field: value})
        with self.assertRaises(ValueError):
            city(position=(0, 0))

    def test_add_and_lookup_return_live_city_without_claiming_tile(self):
        state = founding_state()
        candidate = city()
        self.assertIs(state.add_city(candidate), candidate)
        self.assertIs(state.get_city(candidate.id), candidate)
        self.assertIs(state.city_at(candidate.position), candidate)
        self.assertIsNone(state.city_at(Position(1, 0)))
        self.assertIsNone(state.tiles[candidate.position].owner_id)
        state.validate()

    def test_lookup_and_removal_reject_unknown_or_malformed_ids(self):
        state = founding_state()
        before = deepcopy(state)
        for value in ("missing", "", [], None, True):
            for operation in (state.get_city, state.remove_city):
                with self.subTest(value=value, operation=operation), self.assertRaises(ValueError):
                    operation(value)
                self.assertEqual(state, before)
        with self.assertRaises(ValueError):
            state.city_at((0, 0))

    def test_add_rejects_wrong_entity_type(self):
        self.assert_add_rejected(founding_state(), None, "CityState")

    def test_duplicate_city_id_rejected(self):
        state = founding_state()
        state.add_city(city())
        self.assert_add_rejected(state, city(position=Position(1, 0)), "duplicate city ID")

    def test_two_cities_on_same_tile_rejected(self):
        state = founding_state()
        state.add_city(city())
        self.assert_add_rejected(state, city("city-2"), "one city")

    def test_duplicate_names_at_legal_spacing_allowed(self):
        state = founding_state()
        state.add_city(city())
        state.add_city(city("city-2", position=Position(3, 0)))
        self.assertEqual(len(state.cities), 2)
        state.validate()

    def test_unknown_owner_rejected(self):
        self.assert_add_rejected(founding_state(), city(owner="missing"), "live player")

    def test_eliminated_owner_rejected(self):
        state = founding_state()
        state.eliminate_player("B")
        self.assert_add_rejected(state, city(owner="B"), "live player")

    def test_all_legal_terrains_preserved(self):
        for terrain in (Terrain.GRASSLAND, Terrain.PLAINS, Terrain.FOREST, Terrain.HILLS):
            with self.subTest(terrain=terrain):
                state = founding_state()
                state.tiles[Position(1, 0)].terrain = terrain
                state.add_city(city(position=Position(1, 0)))
                self.assertIs(state.tiles[Position(1, 0)].terrain, terrain)
                state.validate()

    def test_mountains_and_water_rejected(self):
        for terrain in (Terrain.MOUNTAINS, Terrain.WATER):
            with self.subTest(terrain=terrain):
                state = founding_state()
                state.tiles[Position(1, 0)].terrain = terrain
                self.assert_add_rejected(state, city(position=Position(1, 0)), "illegal terrain")

    def test_out_of_bounds_rejected(self):
        for position in (Position(-1, 0), Position(0, -1), Position(5, 0), Position(0, 5)):
            with self.subTest(position=position):
                self.assert_add_rejected(founding_state(), city(position=position), "outside map")

    def test_missing_tile_rejected(self):
        state = founding_state()
        del state.tiles[Position(1, 0)]
        self.assert_add_rejected(state, city(position=Position(1, 0)), "unknown tile")

    def test_hostile_city_unit_colocation_rejected_on_add(self):
        self.assert_add_rejected(founding_state(), city(owner="B"), "hostile city and unit")

    def test_direct_invalid_city_state_rejected_without_repair(self):
        mutations = (
            lambda s: setattr(s.cities["city-1"], "id", "wrong-key"),
            lambda s: setattr(s.cities["city-1"], "owner_id", "unknown"),
            lambda s: setattr(s.cities["city-1"], "owner_id", "C"),
            lambda s: setattr(s.cities["city-1"], "owner_id", "B"),
            lambda s: setattr(s.cities["city-1"], "name", " "),
            lambda s: setattr(s.cities["city-1"], "population", 0),
            lambda s: setattr(s.cities["city-1"], "position", Position(8, 8)),
            lambda s: setattr(s.cities["city-1"], "position", Position(2, 0)),
            lambda s: setattr(s.tiles[Position(0, 0)], "terrain", Terrain.WATER),
            lambda s: s.cities.update({"city-2": city("city-2")}),
            lambda s: s.units.update({"enemy": UnitState("enemy", "B", Position(0, 0))}),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                state = founding_state()
                state.add_city(city())
                state.eliminate_player("C")
                del state.tiles[Position(2, 0)]
                mutate(state)
                before = deepcopy(state)
                for validate in (state.validate, lambda: to_snapshot(state),
                                 lambda: GameState(**vars(state))):
                    with self.assertRaises(ValueError):
                        validate()
                    self.assertEqual(state, before)

    def test_tile_ownership_strict_types_and_known_player(self):
        for owner in ("", " ", [], True, 1):
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                TileState(Position(0, 0), owner_id=owner)
        state = founding_state()
        state.tiles[Position(0, 0)].owner_id = "unknown"
        with self.assertRaises(ValueError):
            state.validate()


class FoundCityTests(unittest.TestCase):
    def assert_rejected(self, state, command, error):
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, error):
            apply_command(state, command)
        self.assertEqual(state, before)

    def test_active_actor_founds_with_supplied_identity_at_settler_position(self):
        state = founding_state()
        apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
        self.assertEqual(state.units["unit-1"].moves_remaining, 1)
        self.assertIsNone(apply_command(state, founding_command(city_id="chosen", city_name="São Paulo")))
        self.assertEqual(state.cities, {"chosen": city("chosen", position=Position(1, 0), name="São Paulo")})
        self.assertNotIn("unit-1", state.units)
        self.assertEqual(state.tiles[Position(1, 0)].owner_id, "A")
        self.assertEqual(state.next_unit_id, 2)
        state.validate()

    def test_inactive_actor_rejected(self):
        self.assert_rejected(founding_state(), founding_command(actor_id="B"), "only the active")

    def test_unknown_actor_rejected(self):
        self.assert_rejected(founding_state(), founding_command(actor_id="unknown"), "unknown command actor")

    def test_eliminated_actor_rejected(self):
        state = founding_state()
        state.eliminate_player("B")
        self.assert_rejected(state, founding_command(actor_id="B"), "eliminated player")

    def test_pregame_and_terminal_rejected(self):
        for terminal in (False, True):
            with self.subTest(terminal=terminal):
                state = founding_state()
                if terminal:
                    state.eliminate_player("B")
                    state.eliminate_player("C")
                else:
                    state.active_player_id = None
                self.assert_rejected(state, founding_command(), "no active activation")

    def test_unknown_settler_rejected(self):
        self.assert_rejected(founding_state(), founding_command(settler_unit_id="missing"), "unknown Settler")

    def test_another_players_settler_rejected(self):
        state = founding_state()
        settler = state.add_unit("B", UnitType.SETTLER, Position(1, 0))
        self.assert_rejected(state, founding_command(settler_unit_id=settler.id), "does not belong")

    def test_all_non_settler_types_rejected(self):
        for unit_type in (UnitType.WARRIOR, UnitType.ARCHER, UnitType.SCOUT, UnitType.SPEARMAN):
            with self.subTest(unit_type=unit_type):
                self.assert_rejected(movement_state(unit_type), founding_command(), "only a Settler")

    def test_spent_settler_must_wait_for_next_activation(self):
        state = founding_state()
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assert_rejected(state, founding_command(), "no movement")
        for player in "ABC":
            apply_command(state, EndActivation(player))
        apply_command(state, founding_command())
        self.assertEqual(state.cities["city-1"].position, Position(2, 0))

    def test_duplicate_requested_city_id_rejected(self):
        state = founding_state()
        state.add_city(city(position=Position(1, 0)))
        self.assert_rejected(state, founding_command(), "duplicate city ID")

    def test_city_already_on_settler_tile_rejected(self):
        state = founding_state()
        state.add_city(city("existing"))
        self.assert_rejected(state, founding_command(), "one city")

    def test_enemy_owned_tile_rejected_including_historical_owner(self):
        for eliminated in (False, True):
            with self.subTest(eliminated=eliminated):
                state = founding_state()
                state.tiles[Position(0, 0)].owner_id = "B"
                if eliminated:
                    state.eliminate_player("B")
                self.assert_rejected(state, founding_command(), "another player's tile")

    def test_unowned_and_own_owned_tiles_allowed(self):
        for owner in (None, "A"):
            with self.subTest(owner=owner):
                state = founding_state()
                state.tiles[Position(0, 0)].owner_id = owner
                apply_command(state, founding_command())
                self.assertEqual(state.tiles[Position(0, 0)].owner_id, "A")

    def test_all_legal_terrain_founding_preserves_terrain(self):
        for terrain in (Terrain.GRASSLAND, Terrain.PLAINS, Terrain.FOREST, Terrain.HILLS):
            with self.subTest(terrain=terrain):
                state = founding_state()
                state.tiles[Position(0, 0)].terrain = terrain
                apply_command(state, founding_command())
                self.assertIs(state.tiles[Position(0, 0)].terrain, terrain)

    def test_invalid_settler_terrain_rejected_without_mutation(self):
        for terrain in (Terrain.MOUNTAINS, Terrain.WATER):
            with self.subTest(terrain=terrain):
                state = founding_state()
                state.tiles[Position(0, 0)].terrain = terrain
                self.assert_rejected(state, founding_command(), "impassable terrain")

    def test_founding_removes_only_settler_and_preserves_activation_and_units(self):
        state = founding_state()
        state.turn = 7
        escort = state.add_unit("A", UnitType.WARRIOR, Position(0, 0))
        escort.hp, escort.moves_remaining = 42, 0
        other = state.add_unit("A", UnitType.SCOUT, Position(0, 0))
        enemy = state.add_unit("B", UnitType.SCOUT, Position(4, 4))
        enemy.moves_remaining = 0
        before_units = deepcopy({u.id: u for u in (escort, other, enemy)})
        apply_command(state, founding_command())
        self.assertEqual(state.units, before_units)
        self.assertEqual((state.turn, state.active_player_id, state.turn_order), (7, "A", list("ABC")))
        apply_command(state, MoveUnit("A", other.id, Position(1, 0)))
        state.validate()

    def test_founding_claims_only_center_and_preserves_unrelated_ownership(self):
        state = founding_state()
        state.tiles[Position(1, 0)].owner_id = "B"
        state.tiles[Position(3, 3)].owner_id = "A"
        before = deepcopy(state.tiles)
        apply_command(state, founding_command())
        before[Position(0, 0)].owner_id = "A"
        self.assertEqual(state.tiles, before)

    def test_cities_at_distance_three_with_identical_names_can_be_founded(self):
        state = founding_state()
        second = state.add_unit("A", UnitType.SETTLER, Position(3, 0))
        apply_command(state, founding_command())
        apply_command(state, founding_command(settler_unit_id=second.id, city_id="city-2"))
        self.assertEqual(len(state.cities), 2)
        self.assertFalse(state.units)
        self.assertFalse(state.players["A"].eliminated)

    def test_invalid_hostile_colocation_cannot_be_hidden_by_consuming_settler(self):
        state = founding_state()
        state.units["enemy"] = UnitState("enemy", "B", Position(0, 0))
        self.assert_rejected(state, founding_command(), "hostile units")

    def test_command_is_immutable_and_fields_require_nonblank_strings(self):
        command = founding_command()
        state = founding_state()
        before = deepcopy(state)
        for field in ("actor_id", "settler_unit_id", "city_id", "city_name"):
            with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
                setattr(command, field, "replacement")
            for value in ("", " \t", None, True, 1, []):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    apply_command(state, founding_command(**{field: value}))
                self.assertEqual(state, before)

    def test_internal_executor_validates_names_and_ids_before_mutation(self):
        for city_id, name in (("", "valid"), ([], "valid"), ("valid", " "), ("valid", None)):
            state = founding_state()
            before = deepcopy(state)
            with self.subTest(city_id=city_id, name=name), self.assertRaises(ValueError):
                found_city(state, "unit-1", city_id, name)
            self.assertEqual(state, before)

    def test_founding_deterministic_across_copies_and_insertion_orders(self):
        source = founding_state()
        source.add_city(city("z", "B", Position(4, 4)))
        source.add_city(city("a", "C", Position(0, 3)))
        first = deepcopy(source)
        second = from_snapshot(to_snapshot(source))
        for field in ("players", "cities", "tiles", "units"):
            setattr(second, field, dict(reversed(list(getattr(second, field).items()))))
        for state in (first, second):
            apply_command(state, founding_command())
        self.assertEqual(first, second)
        self.assertEqual(to_snapshot(first), to_snapshot(second))


class CityOccupancyTests(unittest.TestCase):
    def test_own_city_can_be_entered_and_traversed_with_friendly_stack(self):
        state = movement_state(width=3, height=1)
        state.add_city(city(position=Position(1, 0)))
        for _ in range(3):
            state.add_unit("A", UnitType.WARRIOR, Position(1, 0))
        self.assertEqual(find_path(state, state.units["unit-1"], Position(2, 0)),
                         [Position(0, 0), Position(1, 0), Position(2, 0)])
        apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        state.validate()

    def test_enemy_city_entry_depends_on_capture_capability(self):
        for unit_type in UnitType:
            for owner in "BC":
                with self.subTest(unit_type=unit_type, owner=owner):
                    state = movement_state(unit_type)
                    state.add_city(city(owner=owner, position=Position(1, 0)))
                    before = deepcopy(state)
                    self.assertFalse(state.can_enter("A", Position(1, 0)))
                    with self.assertRaises(ValueError):
                        state.add_unit("A", unit_type, Position(1, 0))
                    self.assertEqual(state, before)
                    if unit_type.can_capture:
                        self.assertIsNotNone(find_path(state, state.units["unit-1"], Position(1, 0)))
                        apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
                        self.assertEqual(state.cities["city-1"].owner_id, "A")
                    else:
                        self.assertIsNone(find_path(state, state.units["unit-1"], Position(1, 0)))
                        with self.assertRaises(ValueError):
                            apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
                        self.assertEqual(state, before)

    def test_pathfinder_routes_around_enemy_city_deterministically(self):
        state = movement_state(width=3, height=3)
        state.add_city(city(owner="B", position=Position(1, 0)))
        self.assertEqual(find_path(state, state.units["unit-1"], Position(2, 0)),
                         [Position(0, 0), Position(1, 1), Position(2, 0)])
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)

    def test_no_path_when_city_blocks_only_route(self):
        state = movement_state(width=3, height=1)
        state.add_city(city(owner="B", position=Position(1, 0)))
        before = deepcopy(state)
        self.assertIsNone(find_path(state, state.units["unit-1"], Position(2, 0)))
        with self.assertRaisesRegex(ValueError, "unreachable"):
            apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state, before)

    def test_historical_tile_ownership_alone_does_not_block_movement(self):
        state = movement_state(width=3, height=1)
        state.tiles[Position(1, 0)].owner_id = "B"
        state.eliminate_player("B")
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state.units["unit-1"].position, Position(2, 0))

    def test_attack_unit_cannot_target_city(self):
        state = movement_state(UnitType.WARRIOR)
        state.add_city(city(owner="B", position=Position(1, 0)))
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "unknown target unit"):
            apply_command(state, AttackUnit("A", "unit-1", "city-1"))
        self.assertEqual(state, before)

    def test_defender_on_own_city_takes_normal_melee_damage(self):
        state = combat_state()
        state.add_city(city(owner="B", position=Position(1, 0)))
        before_city = deepcopy(state.cities["city-1"])
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual((state.units["unit-1"].hp, state.units["unit-2"].hp), (70, 70))
        self.assertEqual(state.cities["city-1"], before_city)

    def test_melee_kill_on_enemy_city_preserves_city_and_prevents_advance(self):
        for target_type in UnitType:
            with self.subTest(target_type=target_type):
                state = combat_state(target_type=target_type)
                state.units["unit-2"].hp = 1
                state.add_city(city(owner="B", position=Position(1, 0)))
                state.tiles[Position(1, 0)].owner_id = "B"
                before_city = deepcopy(state.cities["city-1"])
                apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                self.assertNotIn("unit-2", state.units)
                self.assertEqual(state.cities["city-1"], before_city)
                self.assertEqual(state.units["unit-1"].position, Position(0, 0))
                self.assertEqual(state.units["unit-1"].moves_remaining, 0)
                self.assertEqual(state.tiles[Position(1, 0)].owner_id, "B")
                self.assertFalse(state.players["B"].eliminated)
                state.validate()

    def test_removing_last_defender_in_stack_still_prevents_advance(self):
        state = combat_state(UnitType.SCOUT, UnitType.SETTLER)
        escort = state.add_unit("B", UnitType.SETTLER, Position(1, 0))
        state.add_city(city(owner="B", position=Position(1, 0)))
        for target_id in ("unit-2", escort.id):
            apply_command(state, AttackUnit("A", "unit-1", target_id))
            self.assertEqual(state.units["unit-1"].position, Position(0, 0))
            self.assertIn("city-1", state.cities)
        state.validate()

    def test_ranged_damage_and_kills_unchanged_on_city(self):
        for distance in (1, 2):
            for target_hp in (100, 1):
                with self.subTest(distance=distance, target_hp=target_hp):
                    state = combat_state(UnitType.ARCHER, distance=distance)
                    state.units["unit-2"].hp = target_hp
                    state.add_city(city(owner="B", position=Position(distance, 0)))
                    before_city = deepcopy(state.cities["city-1"])
                    apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
                    self.assertEqual((state.units["unit-1"].hp, state.units["unit-1"].moves_remaining), (100, 0))
                    self.assertEqual(state.units["unit-1"].position, Position(0, 0))
                    if target_hp == 1:
                        self.assertNotIn("unit-2", state.units)
                    else:
                        self.assertEqual(state.units["unit-2"].hp, 70)
                    self.assertEqual(state.cities["city-1"], before_city)
                    state.validate()

    def test_ranged_attack_can_fire_over_enemy_city(self):
        state = combat_state(UnitType.ARCHER, distance=2)
        state.add_city(city(owner="B", position=Position(1, 0)))
        apply_command(state, AttackUnit("A", "unit-1", "unit-2"))
        self.assertEqual(state.units["unit-2"].hp, 70)


class CityEliminationTests(unittest.TestCase):
    def test_explicit_elimination_removes_all_owned_cities_and_units_retains_history(self):
        state = founding_state()
        apply_command(state, founding_command())
        state.add_unit("A", UnitType.WARRIOR, Position(0, 0))
        state.add_city(city("second", position=Position(3, 0)))
        state.tiles[Position(3, 0)].owner_id = "A"
        other_city = state.add_city(city("other", "B", Position(3, 3)))
        other_unit = state.add_unit("B", UnitType.WARRIOR, Position(3, 3))
        before_tiles = deepcopy(state.tiles)
        player = state.players["A"]
        state.active_player_id = "B"
        apply_command(state, EliminatePlayer("B", "A"))
        self.assertEqual(state.cities, {other_city.id: other_city})
        self.assertEqual(state.units, {other_unit.id: other_unit})
        self.assertIs(state.players["A"], player)
        self.assertTrue(player.eliminated)
        self.assertEqual(state.tiles, before_tiles)
        self.assertEqual((state.active_player_id, state.turn), ("B", 0))
        self.assertEqual(from_snapshot(to_snapshot(state)), state)

    def test_active_elimination_with_cities_advances_and_refreshes_once(self):
        for active, successor, turn in (("A", "B", 0), ("B", "C", 0), ("C", "A", 1)):
            with self.subTest(active=active):
                state = founding_state()
                for owner, position in zip("ABC", (Position(0, 0), Position(3, 0), Position(0, 3))):
                    state.add_city(city(owner, owner, position))
                    state.add_unit(owner, UnitType.SCOUT, position)
                for unit in state.units.values():
                    unit.moves_remaining = 0
                state.active_player_id = active
                apply_command(state, EliminatePlayer(active, active))
                self.assertEqual((state.active_player_id, state.turn), (successor, turn))
                self.assertNotIn(active, state.cities)
                self.assertFalse(any(u.owner_id == active for u in state.units.values()))
                for unit in state.units.values():
                    self.assertEqual(unit.moves_remaining, 2 if unit.owner_id == successor else 0)
                    unit.moves_remaining = 0
                before = deepcopy(state)
                apply_command(state, EliminatePlayer(successor, active))
                self.assertEqual(state, before)

    def test_terminal_elimination_cleans_cities_without_turn_increment(self):
        state = founding_state()
        apply_command(state, founding_command())
        state.eliminate_player("B")
        state.eliminate_player("A")
        self.assertEqual(state.cities, {})
        self.assertEqual(state.units, {})
        self.assertIsNone(state.active_player_id)
        self.assertEqual(state.turn, 0)
        self.assertEqual(state.tiles[Position(0, 0)].owner_id, "A")
        state.validate()

    def test_removing_final_city_eliminates_owner_and_preserves_tiles(self):
        state = founding_state()
        apply_command(state, founding_command())
        state.add_unit("A", UnitType.SCOUT, Position(0, 0))
        tiles = deepcopy(state.tiles)
        self.assertIsNone(state.remove_city("city-1"))
        self.assertTrue(state.players["A"].eliminated)
        self.assertFalse(any(u.owner_id == "A" for u in state.units.values()))
        self.assertEqual(state.active_player_id, "B")
        self.assertEqual(state.tiles, tiles)
        expected = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "unknown city"):
            state.remove_city("city-1")
        self.assertEqual(state, expected)

    def test_removing_enemy_city_reopens_route_but_retains_ownership(self):
        state = movement_state(width=3, height=1)
        state.add_city(city(owner="B", position=Position(1, 0)))
        state.tiles[Position(1, 0)].owner_id = "B"
        state.remove_city("city-1")
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state.tiles[Position(1, 0)].owner_id, "B")

    def test_invalid_state_prevents_city_removal_or_addition(self):
        state = founding_state()
        state.add_city(city())
        state.cities["city-1"].population = 0
        before = deepcopy(state)
        for operation in (lambda: state.remove_city("city-1"),
                          lambda: state.add_city(city("second", position=Position(1, 0)))):
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual(state, before)


class CitySnapshotTests(unittest.TestCase):
    def populated_state(self):
        state = founding_state()
        apply_command(state, founding_command())
        state.cities["city-1"].population = 12  # Restore exactly, without resolving economy.
        state.cities["city-1"].name = "  São Paulo  "
        state.add_city(city("z-city", "B", Position(3, 0), population=3))
        state.add_city(city("a-city", "B", Position(0, 3)))
        unit = state.add_unit("A", UnitType.SCOUT, Position(0, 0))
        unit.hp, unit.moves_remaining = 17, 0
        enemy = state.add_unit("B", UnitType.ARCHER, Position(3, 0))
        enemy.hp, enemy.moves_remaining = 53, 0
        state.tiles[Position(4, 4)].owner_id = "C"
        state.eliminate_player("C")
        state.turn = 7
        return state

    def test_midturn_round_trip_preserves_all_state_without_gameplay_side_effects(self):
        state = self.populated_state()
        before = deepcopy(state)
        snapshot = to_snapshot(state)
        self.assertEqual(snapshot["schema_version"], 12)
        restored = from_snapshot(json.loads(json.dumps(snapshot, allow_nan=False)))
        self.assertEqual(restored, before)
        self.assertEqual(state, before)
        self.assertEqual(restored.cities["city-1"],
                         city(name="  São Paulo  ", population=12))
        self.assertEqual(restored.tiles[Position(0, 0)].owner_id, "A")
        self.assertEqual(restored.tiles[Position(4, 4)].owner_id, "C")
        self.assertTrue(restored.players["C"].eliminated)
        self.assertEqual((restored.turn, restored.active_player_id), (7, "A"))
        self.assertTrue(all(u.moves_remaining == 0 for u in restored.units.values()))

    def test_canonical_city_order_is_id_ascending(self):
        state = self.populated_state()
        snapshot = to_snapshot(state)
        self.assertEqual([c["id"] for c in snapshot["cities"]], ["a-city", "city-1", "z-city"])
        state.cities = dict(reversed(list(state.cities.items())))
        self.assertEqual(json.dumps(to_snapshot(state)), json.dumps(snapshot))
        snapshot["cities"].reverse()
        self.assertEqual(to_snapshot(from_snapshot(snapshot)), to_snapshot(state))

    def test_city_and_tile_serialized_fields_are_exact_and_required(self):
        baseline = to_snapshot(self.populated_state())
        self.assertEqual(set(baseline["cities"][0]),
                         {"id", "owner_id", "name", "population", "position",
                          "food_stored", "production_stored", "production_target"})
        self.assertEqual(set(baseline["tiles"][0]), {"position", "terrain", "owner_id", "resource"})
        for collection in ("cities", "tiles"):
            for field in baseline[collection][0]:
                with self.subTest(collection=collection, missing=field):
                    snapshot = deepcopy(baseline)
                    del snapshot[collection][0][field]
                    with self.assertRaises(ValueError):
                        from_snapshot(snapshot)
            snapshot = deepcopy(baseline)
            snapshot[collection][0]["future_state"] = 1
            with self.assertRaises(ValueError):
                from_snapshot(snapshot)

    def test_malformed_city_snapshots_rejected_without_repair(self):
        baseline = to_snapshot(self.populated_state())
        for field, values in (
            ("id", ("", " ", [], True)),
            ("name", ("", " \n", None, [], 1)),
            ("population", (0, -1, True, 1.0, "1", None)),
            ("owner_id", ("unknown", "C", "A", None, [])),
            ("position", ({"x": 99, "y": 0}, {"x": 0, "y": 0}, {"x": True, "y": 0}, None)),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    snapshot = deepcopy(baseline)
                    # z-city contains a B unit, so owner A is hostile.
                    snapshot["cities"][2][field] = value
                    before = deepcopy(snapshot)
                    with self.assertRaises(ValueError):
                        from_snapshot(snapshot)
                    self.assertEqual(snapshot, before)

    def test_duplicate_city_ids_or_positions_rejected_on_load(self):
        for duplicate_id in (True, False):
            snapshot = to_snapshot(self.populated_state())
            duplicate = deepcopy(snapshot["cities"][0])
            if not duplicate_id:
                duplicate["id"] = "different-id"
            snapshot["cities"].append(duplicate)
            with self.subTest(duplicate_id=duplicate_id), self.assertRaises(ValueError):
                from_snapshot(snapshot)

    def test_invalid_city_terrain_and_missing_tile_rejected_on_load(self):
        for terrain in (Terrain.MOUNTAINS.value, Terrain.WATER.value, "missing"):
            with self.subTest(terrain=terrain):
                snapshot = to_snapshot(self.populated_state())
                center_index = next(i for i, tile in enumerate(snapshot["tiles"])
                                    if tile["position"] == snapshot["cities"][0]["position"])
                if terrain == "missing":
                    del snapshot["tiles"][center_index]
                else:
                    snapshot["tiles"][center_index]["terrain"] = terrain
                with self.assertRaises(ValueError):
                    from_snapshot(snapshot)

    def test_invalid_tile_owners_rejected_on_load(self):
        for owner in ("unknown", "", True, [], 1):
            snapshot = to_snapshot(self.populated_state())
            snapshot["tiles"][0]["owner_id"] = owner
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                from_snapshot(snapshot)

    def test_v1_through_v5_rejected_without_migration(self):
        for version in (1, 2, 3, 4, 5):
            snapshot = to_snapshot(self.populated_state())
            snapshot["schema_version"] = version
            for row in snapshot["cities"]:
                del row["name"]
                del row["population"]
            for row in snapshot["tiles"]:
                del row["owner_id"]
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "unsupported schema_version"):
                from_snapshot(snapshot)

    def test_city_mutation_independent_between_deep_and_snapshot_copies(self):
        source = self.populated_state()
        baseline = to_snapshot(source)
        copies = (deepcopy(source), from_snapshot(baseline), from_snapshot(baseline))
        for state in copies[:2]:
            state.cities["city-1"].name = "Changed"
            state.cities["city-1"].population = 21
            state.cities["city-1"].position = Position(3, 3)
            state.cities["city-1"].owner_id = "B"
            state.players["B"].has_ever_owned_city = True
            state._eliminate_if_cityless("A")
            state.tiles[Position(3, 3)].owner_id = "B"
            state.tiles[Position(3, 3)].terrain = Terrain.FOREST
            self.assertNotIn("unit-2", state.units)
            state.validate()
        self.assertEqual(copies[0], copies[1])
        self.assertEqual(copies[2], source)
        self.assertEqual(to_snapshot(source), baseline)
        baseline["cities"][1]["name"] = "Wire mutation"
        baseline["cities"][1]["population"] = 99
        baseline["cities"][1]["position"]["x"] = 999
        self.assertEqual(copies[2], source)

    def test_founding_independent_between_copies(self):
        source = founding_state()
        snapshot = to_snapshot(source)
        first, second = deepcopy(source), from_snapshot(snapshot)
        apply_command(first, founding_command())
        self.assertEqual(second, source)
        self.assertEqual(to_snapshot(source), snapshot)
        apply_command(second, founding_command())
        self.assertEqual(first, second)
        self.assertIn("unit-1", source.units)
        self.assertIsNone(source.tiles[Position(0, 0)].owner_id)

    def test_city_removal_independent_between_copies(self):
        source = self.populated_state()
        snapshot = to_snapshot(source)
        first, second = deepcopy(source), from_snapshot(snapshot)
        first.remove_city("city-1")
        self.assertEqual(second, source)
        self.assertEqual(to_snapshot(source), snapshot)
        second.remove_city("city-1")
        self.assertEqual(first, second)
        self.assertIn("city-1", source.cities)


if __name__ == "__main__":
    unittest.main()
