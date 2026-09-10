"""Terrain governor, owner-end economy, spacing and exact detached persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest
from unittest.mock import patch

from aig.commands import EliminatePlayer, EndActivation, FoundCity, apply_command
from aig.economy import (
    Yields, city_center_yields, city_yields, growth_cost, resolve_player_economy,
    terrain_yields, workable_positions, worked_positions,
)
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    CityState, ControllerType, GameConfig, GameMap, GameState, PlayerState,
    Position, Terrain, TileState, UnitType,
)


def economy_state(*, center=Position(1, 1), terrain=Terrain.GRASSLAND, population=1):
    state = GameState(
        GameConfig(42), players={p: PlayerState(p, ControllerType.HUMAN) for p in "ABC"},
        turn_order=list("ABC"), active_player_id="A", game_map=GameMap(8, 5),
        tiles={Position(x, y): TileState(Position(x, y), terrain)
               for y in range(5) for x in range(8)},
    )
    state.tiles[center].terrain = Terrain.GRASSLAND
    state.add_city(CityState("a", "A", center, name="Alpha", population=population))
    return state


class YieldQueryTests(unittest.TestCase):
    def test_terrain_table_and_repeated_queries(self):
        expected = {
            Terrain.GRASSLAND: Yields(2, 0, 0), Terrain.PLAINS: Yields(1, 1, 0),
            Terrain.FOREST: Yields(1, 2, 0), Terrain.HILLS: Yields(0, 2, 0),
            Terrain.MOUNTAINS: Yields(), Terrain.WATER: Yields(1, 0, 1),
        }
        for terrain, yields in expected.items():
            with self.subTest(terrain=terrain):
                self.assertEqual(terrain_yields(terrain), yields)
                self.assertEqual(terrain_yields(terrain), terrain_yields(terrain))
        for invalid in ("grassland", None, True, []):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                terrain_yields(invalid)

    def test_yields_are_immutable_strict_nonnegative_integers(self):
        for field in ("food", "production", "gold"):
            with self.assertRaises(FrozenInstanceError):
                setattr(Yields(), field, 1)
            for invalid in (-1, True, False, 1.0, "1", None, []):
                with self.subTest(field=field, value=invalid), self.assertRaises(ValueError):
                    Yields(**{field: invalid})
        self.assertEqual(Yields(10**50).food, 10**50)

    def test_component_addition_and_summing(self):
        self.assertEqual(Yields(2, 1, 3) + Yields(1, 4, 2), Yields(3, 5, 5))
        self.assertEqual(sum([Yields(2), Yields(1, 2), Yields(0, 0, 1)]), Yields(3, 2, 1))
        self.assertEqual(sum([], Yields()), Yields())
        for invalid in (1, True, 0.0, None):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                invalid + Yields()

    def test_center_minimums_preserve_terrain_and_state(self):
        for terrain, expected in (
            (Terrain.GRASSLAND, Yields(2, 1)), (Terrain.PLAINS, Yields(2, 1)),
            (Terrain.FOREST, Yields(2, 2)), (Terrain.HILLS, Yields(2, 2)),
        ):
            state = economy_state()
            city = state.cities["a"]
            state.tiles[city.position].terrain = terrain
            before = deepcopy(state)
            with self.subTest(terrain=terrain):
                self.assertEqual(city_center_yields(state, city), expected)
                self.assertEqual(state, before)

    def test_interior_has_eight_surroundings_and_free_center(self):
        state = economy_state()
        city = state.cities["a"]
        expected = [Position(x, y) for y in range(3) for x in range(3)
                    if (x, y) != (1, 1)]
        self.assertEqual(workable_positions(state, city), expected)
        self.assertEqual(worked_positions(state, city), [Position(0, 0)])
        self.assertEqual(city_yields(state, city), Yields(4, 1))

    def test_bounds_corners_edges_and_negative_map_origin(self):
        for center, count in ((Position(0, 0), 3), (Position(7, 4), 3),
                              (Position(0, 2), 5), (Position(7, 2), 5),
                              (Position(2, 0), 5), (Position(2, 4), 5)):
            state = economy_state(center=center)
            positions = workable_positions(state, state.cities["a"])
            with self.subTest(center=center):
                self.assertEqual(len(positions), count)
                self.assertTrue(all(state.game_map.contains(p) for p in positions))
        state = economy_state()
        offset = Position(-5, -7)
        state.game_map = GameMap(8, 5, offset)
        state.tiles = {Position(p.x + offset.x, p.y + offset.y):
                       TileState(Position(p.x + offset.x, p.y + offset.y), tile.terrain)
                       for p, tile in state.tiles.items()}
        state.cities["a"].position = offset
        self.assertEqual(workable_positions(state, state.cities["a"]),
                         [Position(-4, -7), Position(-5, -6), Position(-4, -6)])

    def test_missing_and_mountain_tiles_excluded_water_included(self):
        state = economy_state()
        state.tiles[Position(0, 0)].terrain = Terrain.MOUNTAINS
        state.tiles[Position(1, 0)].terrain = Terrain.WATER
        del state.tiles[Position(2, 0)]
        positions = workable_positions(state, state.cities["a"])
        self.assertEqual(len(positions), 6)
        self.assertNotIn(Position(0, 0), positions)
        self.assertNotIn(Position(2, 0), positions)
        self.assertIn(Position(1, 0), positions)

    def test_population_slots_capped_by_available_tiles(self):
        state = economy_state()
        city = state.cities["a"]
        for population, count in ((1, 1), (2, 2), (3, 3), (8, 8), (100, 8)):
            city.population = population
            with self.subTest(population=population):
                self.assertEqual(len(worked_positions(state, city)), count)
                self.assertNotIn(city.position, worked_positions(state, city))
        for position in workable_positions(state, city):
            state.tiles[position].terrain = Terrain.MOUNTAINS
        self.assertEqual(worked_positions(state, city), [])
        self.assertEqual(city_yields(state, city), Yields(2, 1))

    def test_food_then_production_then_gold_priorities(self):
        # Best tile is later in coordinate order to ensure yields decide.
        for worse, better in ((Terrain.FOREST, Terrain.GRASSLAND),
                              (Terrain.PLAINS, Terrain.FOREST),
                              (Terrain.HILLS, Terrain.WATER)):
            state = economy_state(terrain=Terrain.MOUNTAINS)
            state.tiles[Position(0, 0)].terrain = worse
            state.tiles[Position(2, 2)].terrain = better
            with self.subTest(worse=worse, better=better):
                self.assertEqual(worked_positions(state, state.cities["a"]), [Position(2, 2)])
        # No two current terrains tie in food/production but differ in gold.
        # Isolate the governor's gold key without adding a terrain variant.
        state = economy_state(terrain=Terrain.MOUNTAINS)
        state.tiles[Position(0, 0)].terrain = Terrain.PLAINS
        state.tiles[Position(2, 2)].terrain = Terrain.WATER
        actual = terrain_yields
        with patch("aig.economy.terrain_yields", side_effect=lambda t:
                   Yields(1, 0, 0) if t is Terrain.PLAINS else actual(t)):
            self.assertEqual(worked_positions(state, state.cities["a"]), [Position(2, 2)])

    def test_y_then_x_ties_repeated_queries_and_insertion_independence(self):
        state = economy_state(population=3)
        state.tiles = dict(reversed(list(state.tiles.items())))
        before = deepcopy(state)
        for _ in range(3):
            positions = worked_positions(state, state.cities["a"])
            self.assertEqual(positions, [Position(0, 0), Position(1, 0), Position(2, 0)])
            positions.clear()  # No cached mutable assignments.
        self.assertEqual(state, before)

    def test_working_ignores_ownership_and_units_and_does_not_claim(self):
        state = economy_state()
        state.tiles[Position(0, 0)].owner_id = "B"
        state.add_unit("B", UnitType.WARRIOR, Position(0, 0))
        before = deepcopy(state.tiles)
        self.assertEqual(worked_positions(state, state.cities["a"]), [Position(0, 0)])
        resolve_player_economy(state, "A")
        self.assertEqual(state.tiles, before)

    def test_queries_reject_detached_cities_and_invalid_state(self):
        for query in (city_center_yields, workable_positions, worked_positions, city_yields):
            state = economy_state()
            with self.subTest(query=query), self.assertRaises(ValueError):
                query(state, deepcopy(state.cities["a"]))
            state.cities["a"].food_stored = -1
            with self.assertRaises(ValueError):
                query(state, state.cities["a"])


class CitySpacingTests(unittest.TestCase):
    def test_founding_distances_for_same_and_other_factions(self):
        for owner in ("A", "B"):
            for position, allowed in (
                (Position(2, 1), False), (Position(3, 1), False),
                (Position(2, 2), False), (Position(3, 3), False),
                (Position(4, 1), True), (Position(4, 4), True),
            ):
                with self.subTest(owner=owner, position=position):
                    state = economy_state()
                    state.cities["a"].owner_id = owner
                    settler = state.add_unit("A", UnitType.SETTLER, position)
                    before = deepcopy(state)
                    command = FoundCity("A", settler.id, "new", "New")
                    if allowed:
                        apply_command(state, command)
                        state.validate()
                        self.assertEqual(len(state.cities), 2)
                        self.assertTrue(set(workable_positions(state, state.cities["a"])).isdisjoint(
                            workable_positions(state, state.cities["new"])))
                    else:
                        with self.assertRaisesRegex(ValueError, "distance 3"):
                            apply_command(state, command)
                        self.assertEqual(state, before)

    def test_setup_direct_state_and_snapshots_enforce_spacing(self):
        for position in (Position(2, 1), Position(3, 1), Position(3, 3)):
            for owner in ("A", "B"):
                with self.subTest(position=position, owner=owner):
                    state = economy_state()
                    candidate = CityState("b", owner, position, name="Beta")
                    before = deepcopy(state)
                    with self.assertRaisesRegex(ValueError, "distance 3"):
                        state.add_city(candidate)
                    self.assertEqual(state, before)
                    state.cities["b"] = candidate
                    for check in (state.validate, lambda: to_snapshot(state),
                                  lambda: GameState(**vars(state))):
                        with self.assertRaisesRegex(ValueError, "distance 3"):
                            check()
                    snapshot = to_snapshot(before)
                    row = deepcopy(snapshot["cities"][0])
                    row.update(id="b", owner_id=owner, position={"x": position.x, "y": position.y})
                    snapshot["cities"].append(row)
                    with self.assertRaisesRegex(ValueError, "distance 3"):
                        from_snapshot(snapshot)


class EconomyResolutionTests(unittest.TestCase):
    def test_food_surplus_zero_deficit_and_floor_without_starvation(self):
        for terrain, population, stored, expected in (
            (Terrain.GRASSLAND, 1, 0, 2), (Terrain.HILLS, 1, 7, 7),
            (Terrain.HILLS, 2, 7, 5), (Terrain.HILLS, 2, 1, 0),
            (Terrain.HILLS, 3, 0, 0),
        ):
            state = economy_state(terrain=terrain, population=population)
            city = state.cities["a"]
            city.food_stored = stored
            with self.subTest(terrain=terrain, population=population, stored=stored):
                resolve_player_economy(state, "A")
                self.assertEqual(city.food_stored, expected)
                self.assertEqual(city.population, population)

    def test_growth_cost_strict_and_uncapped(self):
        for population, cost in ((1, 15), (2, 20), (3, 25), (10**30, 10 + 5 * 10**30)):
            self.assertEqual(growth_cost(population), cost)
        for invalid in (0, -1, True, False, 1.0, "1", None):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                growth_cost(invalid)

    def test_growth_exact_threshold_carry_and_multiple_growth(self):
        for stored, population, remaining in ((12, 1, 14), (13, 2, 0),
                                               (14, 2, 1), (60, 4, 2)):
            state = economy_state()
            city = state.cities["a"]
            city.food_stored = stored
            resolve_player_economy(state, "A")
            with self.subTest(stored=stored):
                self.assertEqual((city.population, city.food_stored), (population, remaining))

    def test_growth_after_deficit_uses_food_after_consumption(self):
        state = economy_state(terrain=Terrain.HILLS, population=2)
        city = state.cities["a"]
        city.food_stored = 21
        resolve_player_economy(state, "A")
        self.assertEqual((city.population, city.food_stored), (2, 19))

    def test_new_population_only_works_on_next_resolution(self):
        state = economy_state(terrain=Terrain.MOUNTAINS)
        city = state.cities["a"]
        state.tiles[Position(0, 0)].terrain = Terrain.GRASSLAND
        state.tiles[Position(1, 0)].terrain = Terrain.FOREST
        city.food_stored = 13
        resolve_player_economy(state, "A")
        self.assertEqual((city.population, city.food_stored, city.production_stored), (2, 0, 1))
        resolve_player_economy(state, "A")
        self.assertEqual((city.population, city.food_stored, city.production_stored), (2, 1, 4))

    def test_production_and_gold_accumulate_without_spending_or_unit_creation(self):
        state = economy_state(terrain=Terrain.WATER)
        city = state.cities["a"]
        state.tiles[city.position].terrain = Terrain.FOREST
        city.production_stored = 10**30
        state.players["A"].gold = 10**30
        before_units, counter = deepcopy(state.units), state.next_unit_id
        for _ in range(3):
            resolve_player_economy(state, "A")
        self.assertEqual(city.production_stored, 10**30 + 6)
        self.assertEqual(state.players["A"].gold, 10**30 + 3)
        self.assertEqual((state.units, state.next_unit_id), (before_units, counter))

    def test_multiple_cities_aggregate_by_id_independent_of_insertion_order(self):
        source = economy_state(terrain=Terrain.WATER)
        for city_id, owner, position in (("z", "A", Position(4, 1)), ("b", "B", Position(7, 1))):
            source.tiles[position].terrain = Terrain.GRASSLAND
            source.add_city(CityState(city_id, owner, position, name=city_id))
        for reverse in (False, True):
            state = deepcopy(source)
            if reverse:
                for field in ("players", "cities", "tiles"):
                    setattr(state, field, dict(reversed(list(getattr(state, field).items()))))
            with patch("aig.economy.city_yields", wraps=city_yields) as query:
                resolve_player_economy(state, "A")
                self.assertEqual([call.args[1].id for call in query.call_args_list], ["a", "z"])
            self.assertEqual(state.players["A"].gold, 2)
            self.assertEqual(state.players["B"], source.players["B"])
            self.assertEqual(state.cities["b"], source.cities["b"])
            if not reverse:
                expected = to_snapshot(state)
            else:
                self.assertEqual(to_snapshot(state), expected)

    def test_no_cities_is_noop_and_rules_do_not_advance_or_refresh(self):
        state = economy_state()
        unit = state.add_unit("A", UnitType.SCOUT, Position(1, 1))
        unit.moves_remaining = 0
        before = deepcopy(state)
        resolve_player_economy(state, "B")
        self.assertEqual(state, before)
        resolve_player_economy(state, "A")
        self.assertEqual((state.active_player_id, state.turn, state.turn_order), ("A", 0, list("ABC")))
        self.assertEqual(state.units, before.units)

    def test_invalid_owner_or_later_city_prevents_any_mutation(self):
        for player_id in ("missing", "", None, [], "C"):
            state = economy_state()
            state.eliminate_player("C")
            before = deepcopy(state)
            with self.subTest(player_id=player_id), self.assertRaises(ValueError):
                resolve_player_economy(state, player_id)
            self.assertEqual(state, before)
        state = economy_state()
        state.add_city(CityState("z", "A", Position(4, 1), name="Last"))
        state.cities["z"].production_stored = -1
        before = deepcopy(state)
        with self.assertRaises(ValueError):
            resolve_player_economy(state, "A")
        self.assertEqual(state, before)

    def test_all_results_are_computed_before_commit(self):
        state = economy_state()
        state.add_city(CityState("z", "A", Position(4, 1), name="Last"))
        before = deepcopy(state)
        with patch("aig.economy.city_yields", side_effect=[Yields(4, 1, 2), ValueError("query failure")]):
            with self.assertRaisesRegex(ValueError, "query failure"):
                resolve_player_economy(state, "A")
        self.assertEqual(state, before)


class EconomyActivationTests(unittest.TestCase):
    def test_end_resolves_outgoing_before_one_advance_and_incoming_refresh(self):
        state = economy_state(terrain=Terrain.WATER)
        state.tiles[Position(4, 1)].terrain = Terrain.GRASSLAND
        other = state.add_city(CityState("b", "B", Position(4, 1), name="Beta"))
        units = [state.add_unit(owner, UnitType.SCOUT, position)
                 for owner, position in (("A", Position(1, 1)), ("B", Position(4, 1)))]
        for unit in units:
            unit.moves_remaining, unit.hp = 0, 42
        finish = state.finish_activation

        def check_then_advance():
            self.assertEqual((state.active_player_id, state.players["A"].gold), ("A", 1))
            self.assertEqual(state.cities["a"].production_stored, 1)
            self.assertEqual(units[1].moves_remaining, 0)
            finish()

        with patch.object(state, "finish_activation", side_effect=check_then_advance) as advance:
            self.assertIsNone(apply_command(state, EndActivation("A")))
            advance.assert_called_once_with()
        self.assertEqual((state.active_player_id, state.turn), ("B", 0))
        self.assertEqual((units[0].moves_remaining, units[1].moves_remaining), (0, 2))
        self.assertEqual([u.hp for u in units], [42, 42])
        self.assertEqual((other.food_stored, other.production_stored, state.players["B"].gold), (0, 0, 0))

    def test_round_wrap_collects_once_for_each_owner(self):
        state = economy_state(terrain=Terrain.WATER)
        state.cities["a"].owner_id = "C"
        for owner in "ABC":
            apply_command(state, EndActivation(owner))
        self.assertEqual((state.turn, state.active_player_id, state.players["C"].gold), (1, "A", 1))
        self.assertEqual(state.cities["a"].production_stored, 1)

    def test_invalid_end_activation_has_no_economic_mutation(self):
        for case in ("inactive", "unknown", "eliminated", "pregame", "terminal", "invalid_state"):
            state = economy_state(terrain=Terrain.WATER)
            actor = "A"
            if case == "inactive":
                actor = "B"
            elif case == "unknown":
                actor = "missing"
            elif case == "eliminated":
                state.eliminate_player("C")
                actor = "C"
            elif case == "pregame":
                state.active_player_id = None
            elif case == "terminal":
                state.eliminate_player("B")
                state.eliminate_player("C")
            else:
                state.players["B"].gold = -1
            before = deepcopy(state)
            with self.subTest(case=case), self.assertRaises(ValueError):
                apply_command(state, EndActivation(actor))
            self.assertEqual(state, before)

    def test_elimination_aborts_economy_including_wrap_and_terminal(self):
        for active, successor, turn in (("A", "B", 0), ("C", "A", 1), ("A", None, 0)):
            state = economy_state(terrain=Terrain.WATER)
            state.cities["a"].owner_id = active
            state.active_player_id = active
            city = state.cities["a"]
            city.food_stored = 14
            before_city = deepcopy(city)
            state.players[active].gold = 7
            if successor is None:
                state.eliminate_player("C")
            else:
                position = Position(4, 1)
                state.tiles[position].terrain = Terrain.GRASSLAND
                incoming = state.add_city(CityState("b", successor, position, name="Beta"))
                unit = state.add_unit(successor, UnitType.SCOUT, position)
                unit.moves_remaining = 0
            with self.subTest(active=active, successor=successor):
                apply_command(state, EliminatePlayer(active, active))
                self.assertEqual((state.active_player_id, state.turn), (successor, turn))
                self.assertNotIn("a", state.cities)
                self.assertEqual(city, before_city)
                self.assertEqual(state.players[active].gold, 7)
                if successor is not None:
                    self.assertEqual(unit.moves_remaining, 2)
                    self.assertEqual(incoming.production_stored, 0)
                    self.assertEqual(state.players[successor].gold, 0)

    def test_low_level_advance_and_inactive_elimination_do_not_collect(self):
        state = economy_state(terrain=Terrain.WATER)
        before_city, before_player = deepcopy(state.cities["a"]), deepcopy(state.players["A"])
        apply_command(state, EliminatePlayer("A", "C"))
        state.finish_activation()
        self.assertEqual(state.cities["a"], before_city)
        self.assertEqual(state.players["A"], before_player)

    def test_founded_city_participates_in_same_activation_economy(self):
        state = economy_state()
        state.remove_city("a")
        settler = state.add_unit("A", UnitType.SETTLER, Position(1, 1))
        apply_command(state, FoundCity("A", settler.id, "new", "New"))
        city = state.cities["new"]
        self.assertEqual((city.population, city.food_stored, city.production_stored), (1, 0, 0))
        apply_command(state, EndActivation("A"))
        self.assertEqual((city.population, city.food_stored, city.production_stored), (1, 2, 1))
        self.assertEqual(state.next_unit_id, 2)


class EconomyPersistenceTests(unittest.TestCase):
    def test_defaults_and_strict_validation_at_every_boundary(self):
        state = economy_state()
        self.assertEqual(state.players["A"].gold, 0)
        self.assertEqual((state.cities["a"].food_stored, state.cities["a"].production_stored), (0, 0))
        for collection, field in (("players", "gold"), ("cities", "food_stored"),
                                  ("cities", "production_stored")):
            for invalid in (-1, True, False, 1.5, "1", None, []):
                with self.subTest(collection=collection, field=field, value=invalid):
                    with self.assertRaises(ValueError):
                        if collection == "players":
                            PlayerState("A", ControllerType.HUMAN, gold=invalid)
                        else:
                            CityState("a", "A", Position(1, 1), name="Alpha", **{field: invalid})
                    state = economy_state()
                    snapshot = to_snapshot(state)
                    snapshot[collection][0][field] = invalid
                    before_wire = deepcopy(snapshot)
                    with self.assertRaises(ValueError):
                        from_snapshot(snapshot)
                    self.assertEqual(snapshot, before_wire)
                    entity = state.players["A"] if collection == "players" else state.cities["a"]
                    setattr(entity, field, invalid)
                    before = deepcopy(state)
                    for check in (state.validate, lambda: to_snapshot(state),
                                  lambda: apply_command(state, EndActivation("A"))):
                        with self.assertRaises(ValueError):
                            check()
                        self.assertEqual(state, before)

    def test_exact_midactivation_restore_does_not_resolve_or_refresh(self):
        state = economy_state(terrain=Terrain.WATER, population=2)
        city = state.cities["a"]
        city.food_stored, city.production_stored = 100, 12345
        state.players["A"].gold = 765
        state.players["C"].gold = 8
        state.eliminate_player("C")
        unit = state.add_unit("A", UnitType.SCOUT, city.position)
        unit.moves_remaining, unit.hp = 0, 37
        state.turn = 9
        before = deepcopy(state)
        snapshot = to_snapshot(state)
        self.assertEqual(snapshot["schema_version"], 8)
        restored = from_snapshot(json.loads(json.dumps(snapshot)))
        self.assertEqual(restored, before)
        self.assertEqual(state, before)
        self.assertEqual(json.dumps(to_snapshot(restored)), json.dumps(snapshot))
        apply_command(restored, EndActivation("A"))
        apply_command(state, EndActivation("A"))
        self.assertEqual(restored, state)

    def test_fields_required_and_derived_data_rejected(self):
        snapshot = to_snapshot(economy_state())
        self.assertEqual(set(snapshot["players"][0]), {"id", "controller", "eliminated", "gold",
                     "science_stored", "research_target", "researched_technologies"})
        self.assertEqual(set(snapshot["cities"][0]),
                         {"id", "owner_id", "position", "name", "population", "food_stored", "production_stored", "production_target"})
        for collection, fields in (("players", ("gold",)),
                                   ("cities", ("food_stored", "production_stored"))):
            for field in fields:
                malformed = deepcopy(snapshot)
                del malformed[collection][0][field]
                with self.assertRaises(ValueError):
                    from_snapshot(malformed)
        for field in ("worked_positions", "yields", "growth_cost", "center_yields"):
            malformed = deepcopy(snapshot)
            malformed["cities"][0][field] = []
            with self.assertRaises(ValueError):
                from_snapshot(malformed)

    def test_economy_copies_and_wire_data_are_independent(self):
        source = economy_state(terrain=Terrain.WATER)
        source.cities["a"].food_stored = 14
        snapshot = to_snapshot(source)
        copies = [deepcopy(source), from_snapshot(snapshot), from_snapshot(snapshot)]
        for state in copies[:2]:
            apply_command(state, EndActivation("A"))
            self.assertEqual((state.cities["a"].population, state.cities["a"].food_stored,
                              state.cities["a"].production_stored, state.players["A"].gold), (2, 0, 1, 1))
            self.assertEqual(copies[2], source)
            self.assertEqual(to_snapshot(source), snapshot)
        self.assertEqual(copies[0], copies[1])
        snapshot["players"][0]["gold"] = 99
        for field in ("food_stored", "production_stored", "population"):
            snapshot["cities"][0][field] = 99
        self.assertEqual(copies[2], source)


if __name__ == "__main__":
    unittest.main()
