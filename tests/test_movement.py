"""Movement legality, deterministic routing, activation budgets and persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest

from aig.commands import EliminatePlayer, EndActivation, MoveUnit, apply_command
from aig.movement import find_path
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    ControllerType, GameConfig, GameMap, GameState, PlayerState, Position,
    Terrain, TileState, UnitState, UnitType,
)


def movement_state(unit_type=UnitType.SCOUT, *, width=5, height=5):
    state = GameState(
        GameConfig(42), turn_order=list("ABC"), active_player_id="A",
        players={p: PlayerState(p, ControllerType.HUMAN) for p in "ABC"},
        game_map=GameMap(width, height),
        tiles={Position(x, y): TileState(Position(x, y))
               for y in range(height) for x in range(width)},
    )
    state.add_unit("A", unit_type, Position(0, 0))
    return state


class MovementTests(unittest.TestCase):
    def assert_rejected(self, state, command, error):
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, error):
            apply_command(state, command)
        self.assertEqual(state, before)

    def check_direction(self, dx, dy):
        state = movement_state(UnitType.WARRIOR)
        unit = state.units["unit-1"]
        unit.position = Position(2, 2)
        destination = Position(2 + dx, 2 + dy)
        self.assertIsNone(apply_command(state, MoveUnit("A", unit.id, destination)))
        self.assertEqual(unit.position, destination)
        self.assertEqual(unit.moves_remaining, 0)
        self.assertEqual((state.active_player_id, state.turn), ("A", 0))

    def test_north(self):
        self.check_direction(0, -1)

    def test_northeast(self):
        self.check_direction(1, -1)

    def test_east(self):
        self.check_direction(1, 0)

    def test_southeast(self):
        self.check_direction(1, 1)

    def test_south(self):
        self.check_direction(0, 1)

    def test_southwest(self):
        self.check_direction(-1, 1)

    def test_west(self):
        self.check_direction(-1, 0)

    def test_northwest(self):
        self.check_direction(-1, -1)

    def test_each_map_edge_is_closed(self):
        for destination in (Position(-1, 0), Position(0, -1), Position(5, 0), Position(0, 5)):
            with self.subTest(destination=destination):
                state = movement_state()
                self.assert_rejected(state, MoveUnit("A", "unit-1", destination), "outside map")
                self.assertIsNone(find_path(state, state.units["unit-1"], destination))

    def test_water_destination_rejected(self):
        state = movement_state()
        state.tiles[Position(1, 0)].terrain = Terrain.WATER
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(1, 0)), "impassable")

    def test_mountain_destination_rejected(self):
        state = movement_state()
        state.tiles[Position(1, 0)].terrain = Terrain.MOUNTAINS
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(1, 0)), "impassable")

    def test_all_land_types_passable_for_all_unit_types(self):
        for terrain in (Terrain.GRASSLAND, Terrain.PLAINS, Terrain.FOREST, Terrain.HILLS):
            for unit_type in UnitType:
                with self.subTest(terrain=terrain, unit_type=unit_type):
                    state = movement_state(unit_type)
                    state.tiles[Position(1, 0)].terrain = terrain
                    apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
                    self.assertEqual(state.units["unit-1"].moves_remaining, unit_type.movement_allowance - 1)

    def test_inactive_actor_rejected(self):
        state = movement_state()
        unit = state.add_unit("B", UnitType.SCOUT, Position(4, 4))
        self.assert_rejected(state, MoveUnit("B", unit.id, Position(3, 4)), "only the active")

    def test_other_players_unit_rejected(self):
        state = movement_state()
        unit = state.add_unit("B", UnitType.SCOUT, Position(4, 4))
        self.assert_rejected(state, MoveUnit("A", unit.id, Position(3, 4)), "does not belong")

    def test_unknown_unit_rejected(self):
        self.assert_rejected(movement_state(), MoveUnit("A", "unknown", Position(1, 0)), "unknown unit")

    def test_unknown_actor_rejected(self):
        self.assert_rejected(movement_state(), MoveUnit("missing", "unit-1", Position(1, 0)), "unknown command actor")

    def test_eliminated_actor_rejected(self):
        state = movement_state()
        state.eliminate_player("B")
        self.assert_rejected(state, MoveUnit("B", "unit-1", Position(1, 0)), "eliminated player")

    def test_pre_game_and_terminal_commands_rejected(self):
        for terminal in (False, True):
            with self.subTest(terminal=terminal):
                state = movement_state()
                if terminal:
                    state.eliminate_player("B")
                    state.eliminate_player("C")
                else:
                    state.active_player_id = None
                self.assert_rejected(state, MoveUnit("A", "unit-1", Position(1, 0)), "no active activation")

    def test_warrior_cannot_move_two_tiles(self):
        state = movement_state(UnitType.WARRIOR)
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(2, 0)), "insufficient movement")

    def test_scout_can_move_two_tiles_atomically(self):
        state = movement_state()
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state.units["unit-1"].position, Position(2, 0))
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)
        self.assertEqual(state.active_player_id, "A")

    def test_successive_moves_deduct_budget_and_zero_rejects(self):
        state = movement_state()
        for x, remaining in ((1, 1), (2, 0)):
            apply_command(state, MoveUnit("A", "unit-1", Position(x, 0)))
            self.assertEqual(state.units["unit-1"].moves_remaining, remaining)
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(3, 0)), "no movement")

    def test_over_budget_leaves_every_unit_and_state_field_unchanged(self):
        state = movement_state()
        state.add_unit("A", UnitType.WARRIOR, Position(0, 0))
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(3, 0)), "insufficient movement")

    def test_move_onto_friendly_stack(self):
        state = movement_state()
        for _ in range(2):
            state.add_unit("A", UnitType.WARRIOR, Position(1, 0))
        apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
        self.assertTrue(all(u.position == Position(1, 0) for u in state.units.values()))
        state.validate()

    def test_path_through_friendly_stack(self):
        state = movement_state(width=3, height=1)
        friend = state.add_unit("A", UnitType.WARRIOR, Position(1, 0))
        path = find_path(state, state.units["unit-1"], Position(2, 0))
        self.assertEqual(path, [Position(0, 0), Position(1, 0), Position(2, 0)])
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(friend.position, Position(1, 0))
        self.assertEqual(friend.moves_remaining, 1)

    def test_enemy_destination_rejected(self):
        state = movement_state()
        state.add_unit("B", UnitType.WARRIOR, Position(1, 0))
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(1, 0)), "enemy-occupied")
        self.assertIsNone(find_path(state, state.units["unit-1"], Position(1, 0)))

    def test_current_position_command_rejected(self):
        state = movement_state()
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(0, 0)), "current position")

    def test_command_is_immutable_and_strictly_typed(self):
        command = MoveUnit("A", "unit-1", Position(1, 0))
        for field in ("actor_id", "unit_id", "destination"):
            with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
                setattr(command, field, None)
        for value in (None, [], True, 1, "", " "):
            for args in ((value, "u", Position(0, 0)), ("A", value, Position(0, 0))):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    MoveUnit(*args)
        for destination in (None, (1, 0), {"x": 1, "y": 0}):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                MoveUnit("A", "u", destination)

    def test_invalid_state_rejected_without_repair(self):
        state = movement_state()
        state.units["unit-1"].moves_remaining = 3
        self.assert_rejected(state, MoveUnit("A", "unit-1", Position(1, 0)), "exceeds")


class PathfindingTests(unittest.TestCase):
    def test_routes_around_impassable_terrain(self):
        state = movement_state(width=3, height=3)
        state.tiles[Position(1, 0)].terrain = Terrain.MOUNTAINS
        self.assertEqual(find_path(state, state.units["unit-1"], Position(2, 0)),
                         [Position(0, 0), Position(1, 1), Position(2, 0)])
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)

    def test_routes_around_enemy_unit(self):
        state = movement_state(width=3, height=3)
        enemy = state.add_unit("B", UnitType.SCOUT, Position(1, 0))
        self.assertEqual(find_path(state, state.units["unit-1"], Position(2, 0)),
                         [Position(0, 0), Position(1, 1), Position(2, 0)])
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(enemy.position, Position(1, 0))
        self.assertEqual(enemy.moves_remaining, 2)

    def test_no_path_through_enemy_or_terrain_barrier(self):
        for blocker in (Terrain.WATER, Terrain.MOUNTAINS, "enemy"):
            with self.subTest(blocker=blocker):
                state = movement_state(width=3, height=3)
                for y in range(3):
                    if blocker == "enemy":
                        state.add_unit("B", UnitType.WARRIOR, Position(1, y))
                    else:
                        state.tiles[Position(1, y)].terrain = blocker
                self.assertIsNone(find_path(state, state.units["unit-1"], Position(2, 0)))
                before = deepcopy(state)
                with self.assertRaisesRegex(ValueError, "unreachable"):
                    apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
                self.assertEqual(state, before)

    def test_detour_cost_counts_steps_not_coordinate_distance(self):
        state = movement_state(width=3, height=4)
        for y in range(3):
            state.tiles[Position(1, y)].terrain = Terrain.WATER
        path = find_path(state, state.units["unit-1"], Position(2, 0))
        self.assertEqual(len(path) - 1, 6)
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "insufficient movement"):
            apply_command(state, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(state, before)

    def test_missing_tiles_are_not_traversable(self):
        state = movement_state(width=3, height=1)
        del state.tiles[Position(1, 0)]
        self.assertIsNone(find_path(state, state.units["unit-1"], Position(1, 0)))
        self.assertIsNone(find_path(state, state.units["unit-1"], Position(2, 0)))

    def test_diagonal_can_pass_between_orthogonal_blockers(self):
        state = movement_state(width=2, height=2)
        state.tiles[Position(1, 0)].terrain = Terrain.WATER
        state.tiles[Position(0, 1)].terrain = Terrain.MOUNTAINS
        self.assertEqual(find_path(state, state.units["unit-1"], Position(1, 1)),
                         [Position(0, 0), Position(1, 1)])

    def test_neighbor_order_breaks_ties_in_all_directions(self):
        state = movement_state(width=7, height=7)
        unit = state.units["unit-1"]
        unit.position = Position(3, 3)
        # Each pair has multiple two-step routes; the first intermediate wins.
        for destination, intermediate in (
            (Position(4, 1), Position(3, 2)),
            (Position(5, 2), Position(4, 2)),
            (Position(5, 4), Position(4, 3)),
            (Position(4, 5), Position(4, 4)),
            (Position(2, 5), Position(3, 4)),
            (Position(1, 4), Position(2, 4)),
            (Position(1, 2), Position(2, 3)),
            (Position(2, 1), Position(3, 2)),
        ):
            with self.subTest(destination=destination):
                self.assertEqual(find_path(state, unit, destination), [unit.position, intermediate, destination])

    def test_path_does_not_depend_on_dictionary_insertion_order(self):
        state = movement_state()
        state.add_unit("A", UnitType.WARRIOR, Position(1, 1))
        state.add_unit("B", UnitType.WARRIOR, Position(3, 3))
        other = deepcopy(state)
        for field in ("players", "tiles", "units"):
            setattr(other, field, dict(reversed(list(getattr(other, field).items()))))
        before = deepcopy(state)
        expected = [Position(0, 0), Position(1, 0), Position(2, 0)]
        for _ in range(3):
            for candidate in (state, other, from_snapshot(to_snapshot(state))):
                self.assertEqual(find_path(candidate, candidate.units["unit-1"], Position(2, 0)), expected)
        self.assertEqual(state, before)

    def test_pathfinder_ignores_activation_and_budget(self):
        state = movement_state(UnitType.WARRIOR)
        state.units["unit-1"].moves_remaining = 0
        state.active_player_id = "B"
        path = find_path(state, state.units["unit-1"], Position(4, 4))
        self.assertEqual(len(path), 5)
        self.assertEqual(state.units["unit-1"].moves_remaining, 0)

    def test_path_to_origin_contains_only_origin(self):
        state = movement_state()
        self.assertEqual(find_path(state, state.units["unit-1"], Position(0, 0)), [Position(0, 0)])

    def test_pathfinder_rejects_malformed_destination_and_non_live_unit(self):
        state = movement_state()
        for unit, destination in ((deepcopy(state.units["unit-1"]), Position(1, 0)),
                                  (None, Position(1, 0)), (state.units["unit-1"], (1, 0))):
            with self.subTest(unit=unit, destination=destination), self.assertRaises(ValueError):
                find_path(state, unit, destination)


class MovementActivationTests(unittest.TestCase):
    def spent_state(self):
        state = movement_state()
        state.add_unit("A", UnitType.WARRIOR, Position(0, 0))
        state.add_unit("B", UnitType.SCOUT, Position(4, 4))
        state.add_unit("B", UnitType.ARCHER, Position(4, 4))
        state.add_unit("C", UnitType.SETTLER, Position(3, 3))
        for unit in state.units.values():
            unit.moves_remaining = 0
        return state

    def assert_only_refreshed(self, state, owner):
        for unit in state.units.values():
            self.assertEqual(unit.moves_remaining, unit.unit_type.movement_allowance if unit.owner_id == owner else 0)

    def test_finish_refreshes_all_next_players_units_only(self):
        state = self.spent_state()
        apply_command(state, EndActivation("A"))
        self.assertEqual((state.active_player_id, state.turn), ("B", 0))
        self.assert_only_refreshed(state, "B")

    def test_wrap_increments_turn_and_refreshes_first_player(self):
        state = self.spent_state()
        state.active_player_id = "C"
        state.finish_activation()
        self.assertEqual((state.active_player_id, state.turn), ("A", 1))
        self.assert_only_refreshed(state, "A")

    def test_active_elimination_refreshes_successor_exactly_once(self):
        for active, successor, turn in (("A", "B", 0), ("B", "C", 0), ("C", "A", 1)):
            with self.subTest(active=active):
                state = self.spent_state()
                state.active_player_id = active
                apply_command(state, EliminatePlayer(active, active))
                self.assertEqual((state.active_player_id, state.turn), (successor, turn))
                self.assert_only_refreshed(state, successor)
                self.assertFalse(any(u.owner_id == active for u in state.units.values()))
                for unit in state.units.values():
                    unit.moves_remaining = 0
                apply_command(state, EliminatePlayer(successor, active))
                self.assertTrue(all(u.moves_remaining == 0 for u in state.units.values()))

    def test_inactive_elimination_does_not_refresh_current_player(self):
        state = self.spent_state()
        apply_command(state, EliminatePlayer("A", "B"))
        self.assertEqual(state.active_player_id, "A")
        self.assertTrue(all(u.moves_remaining == 0 for u in state.units.values()))

    def test_terminal_elimination_does_not_refill_survivor(self):
        for active_target in (False, True):
            with self.subTest(active_target=active_target):
                state = self.spent_state()
                state.eliminate_player("C")
                apply_command(state, EliminatePlayer("A", "A" if active_target else "B"))
                self.assertIsNone(state.active_player_id)
                self.assertEqual(state.turn, 0)
                self.assertTrue(all(u.moves_remaining == 0 for u in state.units.values()))
                before = deepcopy(state)
                with self.assertRaisesRegex(ValueError, "game has ended"):
                    state.eliminate_player(state.turn_order[0])
                self.assertEqual(state, before)

    def test_pregame_elimination_does_not_refresh(self):
        state = self.spent_state()
        state.active_player_id = None
        state.eliminate_player("A")
        self.assertIsNone(state.active_player_id)
        self.assertTrue(all(u.moves_remaining == 0 for u in state.units.values()))


class MovementSnapshotTests(unittest.TestCase):
    def test_mid_activation_round_trip_preserves_spent_budget_and_continuation(self):
        state = movement_state()
        apply_command(state, MoveUnit("A", "unit-1", Position(1, 0)))
        restored = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
        self.assertEqual(restored, state)
        self.assertEqual(restored.units["unit-1"].moves_remaining, 1)
        for candidate in (state, restored):
            apply_command(candidate, MoveUnit("A", "unit-1", Position(2, 0)))
        self.assertEqual(restored, state)
        self.assertEqual(from_snapshot(to_snapshot(state)).units["unit-1"].moves_remaining, 0)

    def test_deepcopy_and_restored_positions_and_budgets_are_independent(self):
        source = movement_state()
        snapshot = to_snapshot(source)
        for copied in (deepcopy(source), from_snapshot(snapshot)):
            apply_command(copied, MoveUnit("A", "unit-1", Position(2, 0)))
            self.assertEqual(copied.units["unit-1"].moves_remaining, 0)
            self.assertEqual(source.units["unit-1"].position, Position(0, 0))
            self.assertEqual(source.units["unit-1"].moves_remaining, 2)
            self.assertEqual(to_snapshot(source), snapshot)

    def test_serialization_is_canonical_across_entity_insertion_order(self):
        state = movement_state()
        state.add_unit("B", UnitType.WARRIOR, Position(4, 4))
        copied = deepcopy(state)
        for field in ("players", "tiles", "units"):
            setattr(copied, field, dict(reversed(list(getattr(copied, field).items()))))
        self.assertEqual(json.dumps(to_snapshot(state)), json.dumps(to_snapshot(copied)))

    def test_invalid_movement_rejected_on_construction_export_and_restore(self):
        for unit_type in UnitType:
            for value in (-1, unit_type.movement_allowance + 1, True, 1.0, None, "1"):
                with self.subTest(unit_type=unit_type, value=value):
                    with self.assertRaises(ValueError):
                        UnitState("u", "A", Position(0, 0), unit_type, moves_remaining=value)
                    state = movement_state(unit_type)
                    snapshot = to_snapshot(state)
                    snapshot["units"][0]["moves_remaining"] = value
                    with self.assertRaises(ValueError):
                        from_snapshot(snapshot)
                    state.units["unit-1"].moves_remaining = value
                    with self.assertRaises(ValueError):
                        to_snapshot(state)

    def test_unit_fields_are_required_and_unknown_fields_rejected(self):
        for field in ("unit_type", "moves_remaining"):
            snapshot = to_snapshot(movement_state())
            del snapshot["units"][0][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                from_snapshot(snapshot)
        snapshot = to_snapshot(movement_state())
        snapshot["units"][0]["base_movement"] = 2
        with self.assertRaises(ValueError):
            from_snapshot(snapshot)

    def test_v1_and_v2_rejected_before_new_fields_are_required(self):
        for version in (1, 2):
            snapshot = to_snapshot(movement_state())
            snapshot["schema_version"] = version
            del snapshot["game_map"]
            del snapshot["next_unit_id"]
            del snapshot["units"][0]["moves_remaining"]
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "unsupported schema_version"):
                from_snapshot(snapshot)


class PlacementPrerequisiteTests(unittest.TestCase):
    def test_base_allowances_and_default_budgets(self):
        for unit_type, allowance in ((UnitType.SETTLER, 2), (UnitType.SCOUT, 2),
                                     (UnitType.WARRIOR, 1), (UnitType.ARCHER, 1), (UnitType.SPEARMAN, 1)):
            with self.subTest(unit_type=unit_type):
                self.assertEqual(unit_type.movement_allowance, allowance)
                self.assertEqual(UnitState("u", "A", Position(0, 0), unit_type).moves_remaining, allowance)
                state = movement_state(unit_type)
                self.assertEqual(state.units["unit-1"].moves_remaining, allowance)

    def test_generated_ids_survive_restoration_and_are_not_reused_after_elimination(self):
        state = movement_state()
        self.assertEqual(state.add_unit("B", UnitType.SCOUT, Position(4, 4)).id, "unit-2")
        state.eliminate_player("B")
        restored = from_snapshot(to_snapshot(state))
        for candidate in (state, restored):
            self.assertEqual(candidate.add_unit("A", UnitType.SCOUT, Position(0, 0)).id, "unit-3")
        self.assertEqual(state, restored)

    def test_id_collision_with_caller_supplied_id_is_skipped(self):
        state = movement_state()
        state.units["unit-2"] = UnitState("unit-2", "A", Position(0, 0))
        self.assertEqual(state.add_unit("A", UnitType.WARRIOR, Position(0, 0)).id, "unit-3")

    def test_invalid_placement_is_atomic(self):
        state = movement_state()
        state.eliminate_player("C")
        state.tiles[Position(1, 0)].terrain = Terrain.WATER
        state.tiles[Position(1, 1)].terrain = Terrain.MOUNTAINS
        state.add_unit("B", UnitType.WARRIOR, Position(2, 0))
        for owner, unit_type, position in (
            ("missing", UnitType.SCOUT, Position(0, 0)), ("C", UnitType.SCOUT, Position(0, 0)),
            ("A", "scout", Position(0, 0)), ("A", UnitType.SCOUT, (0, 0)),
            ("A", UnitType.SCOUT, Position(-1, 0)), ("A", UnitType.SCOUT, Position(1, 0)),
            ("A", UnitType.SCOUT, Position(1, 1)), ("A", UnitType.SCOUT, Position(2, 0)),
        ):
            with self.subTest(owner=owner, position=position):
                before = deepcopy(state)
                with self.assertRaises(ValueError):
                    state.add_unit(owner, unit_type, position)
                self.assertEqual(state, before)

    def test_invalid_terrain_owner_and_hostile_colocation_rejected(self):
        for mutation in ("water", "mountain", "owner", "eliminated", "hostile"):
            with self.subTest(mutation=mutation):
                snapshot = to_snapshot(movement_state())
                if mutation in ("water", "mountain"):
                    snapshot["tiles"][0]["terrain"] = "water" if mutation == "water" else "mountains"
                elif mutation == "owner":
                    snapshot["units"][0]["owner_id"] = "unknown"
                elif mutation == "eliminated":
                    snapshot["players"][1]["eliminated"] = True
                    snapshot["turn_order"].remove("B")
                    snapshot["units"][0]["owner_id"] = "B"
                else:
                    enemy = dict(snapshot["units"][0], id="enemy", owner_id="B")
                    snapshot["units"].append(enemy)
                with self.assertRaises(ValueError):
                    from_snapshot(snapshot)

    def test_map_and_new_snapshot_fields_are_strict(self):
        for args in ((-1, 2), (True, 2), (1.5, 2), (2, 0), (0, 2), (2, 2, (0, 0))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                GameMap(*args)
        for path, value in (
            (("game_map", "width"), -1), (("game_map", "height"), True),
            (("game_map", "origin", "x"), "0"), (("game_map", "width"), 1),
            (("tiles", 0, "terrain"), "lava"), (("tiles", 0, "terrain"), []),
            (("units", 0, "unit_type"), "dragon"), (("units", 0, "unit_type"), []),
            (("next_unit_id",), 0), (("next_unit_id",), True),
        ):
            snapshot = to_snapshot(movement_state())
            target = snapshot
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path, value=value), self.assertRaises(ValueError):
                from_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
