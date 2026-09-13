"""Explicit setup/start, fixed demo, and the first playable activation cycle."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from aig.commands import (
    AttackUnit, EndActivation, FoundCity, MoveUnit, SetCityProduction,
    SetResearch, apply_command,
)
from aig.economy import city_yields
from aig.movement import find_path
from aig.scenarios import scenario_setup

# Preserve pre-barbarian setup regressions against the explicit V2 scenario.
def demo_game_setup():
    setup = scenario_setup('v2')
    return replace(setup, players=tuple(replace(p, controller=ControllerType.HUMAN) for p in setup.players))

from aig.settings import load_settings
from aig.setup import GameSetup, PlayerSetup, create_game, start_game
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    CityState, ControllerType, GameConfig, GameMap, GameState, Position,
    Technology, Terrain, UnitType,
)


class SetupTests(unittest.TestCase):
    def test_valid_fresh_state_and_all_player_defaults(self):
        setup = demo_game_setup()
        state = create_game(setup)
        self.assertIsNone(state.active_player_id)
        self.assertEqual(state.turn, 0)
        self.assertEqual(state.turn_order, ["A", "B"])
        self.assertEqual(state.cities, {})
        self.assertTrue(all(tile.owner_id is None for tile in state.tiles.values()))
        for player in state.players.values():
            self.assertFalse(player.eliminated)
            self.assertEqual((player.gold, player.science_stored, player.research_target), (0, 0, None))
            self.assertEqual(player.researched_technologies, frozenset({Technology.AGRICULTURE}))
            self.assertIs(player.controller, ControllerType.HUMAN)
        state.validate()

    def test_starting_units_and_allocation_follow_turn_order_settler_first(self):
        setup = replace(demo_game_setup(), turn_order=("B", "A"))
        state = create_game(setup)
        starts = {p.id: p.starting_position for p in setup.players}
        self.assertEqual(
            [(u.id, u.owner_id, u.unit_type, u.position) for u in state.units.values()],
            [("unit-1", "B", UnitType.SETTLER, starts["B"]),
             ("unit-2", "B", UnitType.WARRIOR, starts["B"]),
             ("unit-3", "A", UnitType.SETTLER, starts["A"]),
             ("unit-4", "A", UnitType.WARRIOR, starts["A"])],
        )
        self.assertEqual(state.next_unit_id, 5)
        for unit in state.units.values():
            self.assertEqual((unit.hp, unit.moves_remaining), (100, unit.unit_type.movement_allowance))
        self.assertEqual(state.add_unit("A", UnitType.SCOUT, starts["A"]).id, "unit-5")

    def test_identical_and_reordered_input_create_identical_snapshots(self):
        setup = demo_game_setup()
        baseline = to_snapshot(create_game(setup))
        self.assertEqual(to_snapshot(create_game(demo_game_setup())), baseline)
        reordered = replace(setup, players=tuple(reversed(setup.players)), tiles=tuple(reversed(setup.tiles)))
        self.assertEqual(to_snapshot(create_game(reordered)), baseline)

    def test_new_states_and_setup_share_no_mutable_data(self):
        setup = demo_game_setup()
        first, second = create_game(setup), create_game(setup)
        baseline = deepcopy(second)
        first.tiles[Position(0, 0)].terrain = Terrain.WATER
        first.players["A"].science_stored = 10
        first.units["unit-1"].moves_remaining = 0
        first.turn_order.reverse()
        self.assertEqual(second, baseline)
        self.assertEqual(create_game(setup), baseline)

    def test_setup_models_are_immutable(self):
        setup = demo_game_setup()
        with self.assertRaises(FrozenInstanceError):
            setup.turn_order = ("B", "A")
        with self.assertRaises(FrozenInstanceError):
            setup.players[0].starting_position = Position(0, 0)
        self.assertEqual(deepcopy(setup), setup)

    def test_at_least_two_and_unique_players(self):
        setup = demo_game_setup()
        for players in ((), setup.players[:1], (setup.players[0], setup.players[0])):
            with self.subTest(players=players), self.assertRaises(ValueError):
                replace(setup, players=players)

    def test_turn_order_must_contain_every_player_exactly_once(self):
        setup = demo_game_setup()
        for order in ((), ("A",), ("A", "A"), ("A", "missing"), ("A", "B", "B"),
                      ("A", "B", "missing"), ([], "B"), ["A", "B"]):
            with self.subTest(order=order), self.assertRaises(ValueError):
                replace(setup, turn_order=order)

    def test_missing_out_of_bounds_and_impassable_starts(self):
        setup = demo_game_setup()
        for position in (Position(-1, 0), Position(12, 0), Position(0, 10),
                         Position(6, 2), Position(8, 5)):
            with self.subTest(position=position), self.assertRaises(ValueError):
                replace(setup, players=(replace(setup.players[0], starting_position=position), setup.players[1]))
        missing = tuple(pair for pair in setup.tiles if pair[0] != setup.players[0].starting_position)
        with self.assertRaises(ValueError):
            replace(setup, tiles=missing)

    def test_spacing_uses_chebyshev_including_diagonals(self):
        setup = demo_game_setup()
        tiles = tuple((p, Terrain.GRASSLAND) for p, _ in setup.tiles)
        for dx, dy, accepted in ((0, 0, False), (1, 0, False), (2, 0, False),
                                  (2, 2, False), (3, 0, True), (0, 3, True), (3, 3, True)):
            players = (PlayerSetup("A", ControllerType.HUMAN, Position(1, 1)),
                       PlayerSetup("B", ControllerType.HUMAN, Position(1 + dx, 1 + dy)))
            with self.subTest(dx=dx, dy=dy):
                if accepted:
                    create_game(replace(setup, tiles=tiles, players=players)).validate()
                else:
                    with self.assertRaises(ValueError):
                        replace(setup, tiles=tiles, players=players)

    def test_all_passable_land_terrains_allow_starts(self):
        setup = demo_game_setup()
        start = setup.players[0].starting_position
        for terrain in (Terrain.GRASSLAND, Terrain.PLAINS, Terrain.FOREST, Terrain.HILLS):
            tiles = tuple((p, terrain if p == start else t) for p, t in setup.tiles)
            create_game(replace(setup, tiles=tiles)).validate()

    def test_malformed_player_setup_rejected(self):
        for identifier, controller, position in (("", ControllerType.HUMAN, Position(0, 0)),
                                                 ("A", "human", Position(0, 0)),
                                                 ("A", ControllerType.HUMAN, (0, 0))):
            with self.assertRaises(ValueError):
                PlayerSetup(identifier, controller, position)

    def test_invalid_map_tiles_and_mutable_collections_rejected(self):
        setup = demo_game_setup()
        for changes in ({"config": None}, {"game_map": None}, {"players": list(setup.players)},
                        {"players": (None, None)}, {"tiles": list(setup.tiles)},
                        {"tiles": ((Position(0, 0), "grassland"),)},
                        {"tiles": setup.tiles + (setup.tiles[0],)},
                        {"tiles": setup.tiles + ((Position(12, 10), Terrain.GRASSLAND),)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(setup, **changes)
        with self.assertRaises(ValueError):
            create_game(None)

    def test_explicit_negative_origin_and_sparse_map_supported(self):
        starts = (Position(-3, -3), Position(0, 0))
        setup = GameSetup(GameConfig(1), GameMap(4, 4, starts[0]),
                          tuple((p, Terrain.PLAINS) for p in starts),
                          tuple(PlayerSetup(name, ControllerType.HUMAN, p)
                                for name, p in zip("AB", starts)), ("B", "A"))
        state = create_game(setup)
        start_game(state)
        self.assertEqual((state.active_player_id, state.turn), ("B", 0))


class StartGameTests(unittest.TestCase):
    def test_start_only_refreshes_first_owner_and_leaves_turn_zero(self):
        state = create_game(replace(demo_game_setup(), turn_order=("B", "A")))
        for unit in state.units.values():
            unit.moves_remaining, unit.hp = 0, 50
        for player in state.players.values():
            player.science_stored, player.research_target = 100, Technology.ARCHERY
            player.gold = 7
        state.add_city(CityState("b", "B", Position(9, 7), name="Beta", food_stored=100,
                                 production_stored=100, production_target=UnitType.WARRIOR))
        expected = deepcopy(state)
        from aig.knowledge import update_knowledge
        update_knowledge(expected)
        expected.active_player_id = "B"
        for unit in expected.units.values():
            if unit.owner_id == "B":
                unit.moves_remaining = unit.unit_type.movement_allowance
        self.assertIsNone(start_game(state))
        self.assertEqual(state, expected)

    def test_double_start_rejected_without_mutation(self):
        state = create_game(demo_game_setup())
        start_game(state)
        before = deepcopy(state)
        with self.assertRaises(ValueError):
            start_game(state)
        self.assertEqual(state, before)

    def test_invalid_pregame_and_terminal_states_rejected_atomically(self):
        states = [GameState(GameConfig(0))]
        terminal = create_game(demo_game_setup())
        terminal.eliminate_player("B")
        states.append(terminal)
        for field, value in (("turn", 1), ("turn_order", []), ("turn_order", ["A", "A"]),
                             ("turn_order", ["A", "missing"]), ("next_unit_id", 0)):
            state = create_game(demo_game_setup())
            setattr(state, field, value)
            states.append(state)
        for state in states:
            before = deepcopy(state)
            with self.assertRaises(ValueError):
                start_game(state)
            self.assertEqual(state, before)

    def test_all_gameplay_commands_reject_pregame(self):
        state = create_game(demo_game_setup())
        for command in (MoveUnit("A", "unit-1", Position(3, 2)),
                        AttackUnit("A", "unit-2", "unit-4"),
                        FoundCity("A", "unit-1", "a", "Alpha"),
                        SetCityProduction("A", "a", UnitType.WARRIOR),
                        SetResearch("A", Technology.ARCHERY), EndActivation("A")):
            before = deepcopy(state)
            with self.subTest(command=command), self.assertRaisesRegex(ValueError, "no active activation"):
                apply_command(state, command)
            self.assertEqual(state, before)

    def test_post_start_movement_and_combat_are_usable(self):
        state = create_game(demo_game_setup())
        enemy = state.add_unit("B", UnitType.WARRIOR, Position(3, 2))
        start_game(state)
        apply_command(state, MoveUnit("A", "unit-1", Position(2, 3)))
        apply_command(state, AttackUnit("A", "unit-2", enemy.id))
        self.assertEqual(enemy.hp, 70)
        self.assertEqual(state.players["A"].science_stored, 0)

    def test_pregame_and_started_snapshot_restore_without_start_or_refresh(self):
        for started in (False, True):
            state = create_game(demo_game_setup())
            if started:
                start_game(state)
            state.units["unit-1"].moves_remaining = 0
            state.players["A"].science_stored = 100
            state.players["A"].research_target = Technology.ARCHERY
            restored = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
            self.assertEqual(restored, state)
            self.assertEqual(restored.next_unit_id, 5)
            if not started:
                start_game(restored)
                self.assertEqual(restored.units["unit-1"].moves_remaining, 2)
            self.assertEqual(restored.add_unit("A", UnitType.SCOUT, Position(2, 2)).id, "unit-5")


class DemoIntegrationTests(unittest.TestCase):
    def test_demo_dimensions_terrain_variety_and_route_around_obstacles(self):
        setup = demo_game_setup()
        self.assertEqual((setup.game_map.width, setup.game_map.height), (12, 10))
        self.assertEqual(len(setup.tiles), 120)
        self.assertEqual({terrain for _, terrain in setup.tiles}, set(Terrain))
        state = create_game(setup)
        path = find_path(state, state.units["unit-1"], Position(9, 6))
        self.assertIsNotNone(path)
        self.assertTrue(all(state.tiles[p].terrain.land_passable for p in path))
        self.assertEqual(path, find_path(state, state.units["unit-1"], Position(9, 6)))

    def play_cycle(self):
        state = create_game(demo_game_setup())
        start_game(state)
        for actor, settler, warrior, position in (("A", "unit-1", "unit-2", Position(2, 3)),
                                                   ("B", "unit-3", "unit-4", Position(9, 8))):
            self.assertEqual(state.active_player_id, actor)
            apply_command(state, MoveUnit(actor, warrior, position))
            apply_command(state, FoundCity(actor, settler, actor.lower(), actor))
            city = state.cities[actor.lower()]
            yields = city_yields(state, city)
            apply_command(state, SetCityProduction(actor, city.id, UnitType.WARRIOR))
            apply_command(state, SetResearch(actor, Technology.ARCHERY))
            apply_command(state, EndActivation(actor))
            self.assertEqual((city.food_stored, city.production_stored),
                             (max(0, yields.food - 2), yields.production))
            self.assertEqual(state.players[actor].gold, yields.gold)
            self.assertEqual(state.players[actor].science_stored, 1)
            self.assertIs(state.players[actor].research_target, Technology.ARCHERY)
        self.assertEqual((state.active_player_id, state.turn), ("A", 1))
        self.assertEqual(state.units["unit-2"].moves_remaining, 1)
        self.assertEqual(state.units["unit-4"].moves_remaining, 0)
        state.validate()
        return state

    def test_actual_first_playable_cycle_is_deterministic(self):
        self.assertEqual(to_snapshot(self.play_cycle()), to_snapshot(self.play_cycle()))

    def test_demo_can_complete_research_and_build_unlocked_units(self):
        state = self.play_cycle()
        for _ in range(40):
            if all(Technology.ARCHERY in p.researched_technologies for p in state.players.values()):
                break
            apply_command(state, EndActivation(state.active_player_id))
        self.assertTrue(all(Technology.ARCHERY in p.researched_technologies for p in state.players.values()))
        for actor in tuple(state.turn_order):
            while state.active_player_id != actor:
                apply_command(state, EndActivation(state.active_player_id))
            apply_command(state, SetCityProduction(actor, actor.lower(), UnitType.ARCHER))
        for _ in range(80):
            if all(c.production_target is None for c in state.cities.values()):
                break
            apply_command(state, EndActivation(state.active_player_id))
        self.assertEqual({u.owner_id for u in state.units.values() if u.unit_type is UnitType.ARCHER}, {"A", "B"})
        state.validate()

    def test_all_readme_python_examples_execute_in_document_order(self):
        readme = Path(__file__).resolve().parents[1] / "README.md"
        blocks = re.findall(r"```python\n(.*?)```", readme.read_text(encoding="utf-8"), re.DOTALL)
        self.assertGreater(len(blocks), 0)
        namespace = {"__name__": "__readme__"}
        # The startup example must not load the developer's local credentials.
        with patch("aig.settings.load_settings", return_value=load_settings(local_file=None, environ={})):
            for index, block in enumerate(blocks, 1):
                exec(compile(block, f"README.md:python-example-{index}", "exec"), namespace)


if __name__ == "__main__":
    unittest.main()
