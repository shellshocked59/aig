"""State contract tests using only the Python standard library."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest

from aig.snapshots import SCHEMA_VERSION, SnapshotEnvelope, from_snapshot, to_snapshot
from aig.state import (
    CityState,
    ControllerType,
    GameConfig,
    GameMap,
    GameState,
    PlayerState,
    Position,
    TileState,
    UnitState,
)


def example_state(*, debug_mode: bool = False) -> GameState:
    origin = Position(0, 0)
    neighbor = Position(-1, 2)
    return GameState(
        config=GameConfig(seed=42, debug_mode=debug_mode),
        turn=3,
        turn_order=["player-a", "player-b"],
        active_player_id="player-b",
        players={
            "player-a": PlayerState("player-a", ControllerType.HUMAN, has_ever_owned_city=True),
            "player-b": PlayerState("player-b", ControllerType.AI),
        },
        tiles={origin: TileState(origin), neighbor: TileState(neighbor)},
        cities={"city-7": CityState("city-7", "player-a", origin, name="First City")},
        units={"unit-9": UnitState("unit-9", "player-b", neighbor)},
        game_map=GameMap(2, 3, Position(-1, 0)),
    )


class StateTests(unittest.TestCase):
    def test_empty_state_and_independent_defaults(self):
        first = GameState(GameConfig(seed=0))
        second = GameState(GameConfig(seed=0))
        self.assertEqual(first.turn, 0)
        self.assertIsNone(first.active_player_id)
        self.assertIsNone(first.active_controller)
        self.assertFalse(first.config.debug_mode)
        first.players["p"] = PlayerState("p", ControllerType.AI)
        first.turn_order.append("p")
        first.validate()
        self.assertEqual(second.players, {})
        self.assertEqual(second.turn_order, [])
        self.assertEqual(from_snapshot(to_snapshot(second)), second)

    def test_ids_resolve_without_object_references(self):
        state = example_state()
        city = state.cities["city-7"]
        unit = state.units["unit-9"]
        self.assertEqual(state.players[city.owner_id].id, "player-a")
        self.assertEqual(state.players[unit.owner_id].id, "player-b")
        self.assertEqual(state.tiles[city.position].position, Position(0, 0))
        replacement = PlayerState("player-b", ControllerType.HUMAN)
        state.players["player-b"] = replacement
        state.validate()
        self.assertIs(state.players[unit.owner_id], replacement)
        self.assertEqual(state.active_controller, ControllerType.HUMAN)

    def test_ai_only_game(self):
        state = example_state()
        for player in state.players.values():
            player.controller = ControllerType.AI
        restored = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
        self.assertEqual(restored, state)
        self.assertTrue(all(p.controller is ControllerType.AI for p in restored.players.values()))
        self.assertEqual(restored.active_controller, ControllerType.AI)
        self.assertEqual(restored.turn_order, ["player-a", "player-b"])

    def test_pre_game_players_do_not_require_an_active_player(self):
        state = example_state()
        state.turn = 0
        state.active_player_id = None
        self.assertEqual(from_snapshot(to_snapshot(state)), state)

    def test_turn_order_is_explicit_and_independent_of_player_insertion_order(self):
        state = GameState(
            config=GameConfig(42),
            turn=12,
            turn_order=["player-b", "player-a"],
            active_player_id="player-a",
            players={
                "player-a": PlayerState("player-a", ControllerType.HUMAN),
                "player-b": PlayerState("player-b", ControllerType.AI),
            },
        )
        self.assertEqual(state.turn_order, ["player-b", "player-a"])
        self.assertEqual(state.turn_order.index(state.active_player_id), 1)
        self.assertEqual(state.active_controller, ControllerType.HUMAN)
        self.assertEqual(state.turn, 12)

    def test_invalid_turn_order_construction(self):
        cases = [
            (["player-a", "player-b", "player-a"], "player-b", "duplicate"),
            (["player-b"], "player-b", "every player"),
            (["player-a", "player-b", "unknown"], "player-b", "unknown player"),
            (["player-a"], "player-b", "active_player_id must appear"),
            ([], "player-b", "active_player_id must appear"),
            (["player-a", "player-b"], "unknown", "unknown player"),
            ([], None, "every player"),
            (None, None, "must be a list"),
            (("player-a", "player-b"), "player-b", "must be a list"),
            (["player-a", []], "player-a", "non-empty string"),
        ]
        for order, active_player_id, error in cases:
            with self.subTest(order=order, active=active_player_id):
                with self.assertRaisesRegex(ValueError, error):
                    GameState(
                        config=GameConfig(42),
                        players=example_state().players,
                        turn_order=order,
                        active_player_id=active_player_id,
                    )

    def test_missing_active_player_is_only_valid_before_play_or_when_terminal(self):
        for players, order in (({}, []), (example_state().players, ["player-a", "player-b"])):
            with self.subTest(players=list(players)):
                if len(order) < 2:
                    state = GameState(GameConfig(42), turn=1, players=players, turn_order=order)
                    self.assertIsNone(state.active_player_id)
                    self.assertEqual(from_snapshot(to_snapshot(state)), state)
                else:
                    with self.assertRaisesRegex(ValueError, "pre-game"):
                        GameState(GameConfig(42), turn=1, players=players, turn_order=order)

    def test_mutated_turn_order_is_revalidated_on_export(self):
        state = example_state()
        state.turn_order.remove("player-b")
        with self.assertRaisesRegex(ValueError, "active_player_id must appear"):
            to_snapshot(state)

    def test_config_and_coordinates_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            GameConfig(42).debug_mode = True
        with self.assertRaises(FrozenInstanceError):
            Position(1, 2).x = 3

    def test_invalid_model_construction(self):
        cases = [
            lambda: Position(True, 0),
            lambda: Position(0, 1.5),
            lambda: GameConfig("42"),
            lambda: GameConfig(42, debug_mode=1),
            lambda: PlayerState("", ControllerType.AI),
            lambda: PlayerState("p", "ai"),
            lambda: CityState("c", " ", Position(0, 0), name="City"),
            lambda: UnitState("u", "p", (0, 0)),
            lambda: TileState((0, 0)),
            lambda: GameState(GameConfig(42), turn=-1),
            lambda: GameState(GameConfig(42), active_player_id="missing"),
            lambda: GameState(GameConfig(42), players={"wrong": PlayerState("p", ControllerType.AI)}),
            lambda: GameState(GameConfig(42), units={"u": UnitState("u", "missing", Position(0, 0))}),
        ]
        for index, construct in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(ValueError):
                construct()

    def test_serialization_revalidates_mutable_state(self):
        def wrong_player_key(state):
            state.players["player-a"].id = "renamed"

        def missing_owner(state):
            del state.players["player-a"]

        def missing_tile(state):
            del state.tiles[Position(-1, 2)]

        def invalid_controller(state):
            state.players["player-a"].controller = "robot"

        def mismatched_tile_key(state):
            state.tiles[Position(0, 0)].position = Position(5, 5)

        for mutate in (wrong_player_key, missing_owner, missing_tile, invalid_controller, mismatched_tile_key):
            with self.subTest(mutation=mutate.__name__):
                state = example_state()
                mutate(state)
                with self.assertRaises(ValueError):
                    to_snapshot(state)


class SnapshotTests(unittest.TestCase):
    def test_v9_json_contract_and_round_trip(self):
        state = example_state()
        snapshot = to_snapshot(state)
        self.assertEqual(snapshot, {
            "schema_version": 12,
            "result": None,
            "camps": [],
            "config": {"seed": 42, "debug_mode": False},
            "turn": 3,
            "turn_order": ["player-a", "player-b"],
            "active_player_id": "player-b",
            "players": [
                {"id": "player-a", "controller": "human", "kind": "civilization", "has_ever_owned_city": True, "eliminated": False, "gold": 0,
                 "science_stored": 0, "research_target": None,
                 "researched_technologies": ["agriculture"],
                 "knowledge": {"explored_positions": [], "discovered_cities": [], "discovered_camps": []}},
                {"id": "player-b", "controller": "ai", "kind": "civilization", "has_ever_owned_city": False, "eliminated": False, "gold": 0,
                 "science_stored": 0, "research_target": None,
                 "researched_technologies": ["agriculture"],
                 "knowledge": {"explored_positions": [], "discovered_cities": [], "discovered_camps": []}},
            ],
            "tiles": [
                {"position": {"x": 0, "y": 0}, "terrain": "grassland", "owner_id": None, "resource": None},
                {"position": {"x": -1, "y": 2}, "terrain": "grassland", "owner_id": None, "resource": None},
            ],
            "cities": [{"id": "city-7", "owner_id": "player-a", "position": {"x": 0, "y": 0},
                        "name": "First City", "population": 1,
                        "food_stored": 0, "production_stored": 0, "production_target": None}],
            "units": [{"id": "unit-9", "owner_id": "player-b", "position": {"x": -1, "y": 2},
                       "unit_type": "warrior", "moves_remaining": 1, "hp": 100, "home_camp_id": None}],
            "game_map": {"width": 2, "height": 3, "origin": {"x": -1, "y": 0}},
            "next_unit_id": 1,
        })
        self.assertEqual(snapshot["schema_version"], SCHEMA_VERSION)
        restored = from_snapshot(json.loads(json.dumps(snapshot, allow_nan=False)))
        self.assertEqual(restored, state)
        self.assertIsNot(restored.players["player-a"], state.players["player-a"])

    def test_mid_turn_snapshot_preserves_current_activation_and_order(self):
        state = example_state()
        state.players["player-c"] = PlayerState("player-c", ControllerType.AI)
        state.turn = 12
        state.turn_order = ["player-c", "player-b", "player-a"]
        snapshot = to_snapshot(state)
        # Entity array order does not determine faction activation order.
        snapshot["players"].reverse()
        restored = from_snapshot(json.loads(json.dumps(snapshot)))
        self.assertEqual(restored.turn, 12)
        self.assertEqual(restored.turn_order, ["player-c", "player-b", "player-a"])
        self.assertEqual(restored.active_player_id, "player-b")
        self.assertEqual(restored.turn_order.index(restored.active_player_id), 1)
        self.assertEqual(restored, state)

    def test_turn_order_does_not_alias_snapshot_or_source_state(self):
        state = example_state()
        snapshot = to_snapshot(state)
        restored = from_snapshot(snapshot)
        snapshot["turn_order"].reverse()
        self.assertEqual(state.turn_order, ["player-a", "player-b"])
        self.assertEqual(restored.turn_order, ["player-a", "player-b"])
        restored.turn_order.append("new-player")
        self.assertEqual(state.turn_order, ["player-a", "player-b"])
        self.assertEqual(snapshot["turn_order"], ["player-b", "player-a"])

    def test_snapshot_and_restored_state_are_detached(self):
        state = example_state()
        snapshot = to_snapshot(state)
        restored = from_snapshot(snapshot)
        snapshot["players"][0]["controller"] = "ai"
        snapshot["cities"][0]["position"]["x"] = 999
        snapshot["config"]["debug_mode"] = True
        restored.units["unit-9"].owner_id = "player-a"
        self.assertEqual(state.players["player-a"].controller, ControllerType.HUMAN)
        self.assertEqual(restored.players["player-a"].controller, ControllerType.HUMAN)
        self.assertEqual(state.cities["city-7"].position, Position(0, 0))
        self.assertEqual(restored.cities["city-7"].position, Position(0, 0))
        self.assertFalse(restored.config.debug_mode)
        self.assertEqual(state.units["unit-9"].owner_id, "player-b")

    def test_debug_mode_round_trip(self):
        for enabled in (False, True):
            with self.subTest(debug_mode=enabled):
                state = example_state(debug_mode=enabled)
                snapshot = to_snapshot(state)
                self.assertIs(snapshot["config"]["debug_mode"], enabled)
                self.assertEqual(from_snapshot(json.loads(json.dumps(snapshot))), state)

    def test_observations_stay_outside_authoritative_state(self):
        state = example_state(debug_mode=True)
        envelope: SnapshotEnvelope = {
            "snapshot": to_snapshot(state),
            "observer_data": {"example": "non-authoritative annotation"},
        }
        decoded = json.loads(json.dumps(envelope))
        self.assertEqual(from_snapshot(decoded["snapshot"]), state)
        self.assertNotIn("observer_data", to_snapshot(state))
        with self.assertRaises(ValueError):
            from_snapshot(decoded)

    def test_malformed_snapshot_values(self):
        # Paths cover container types, scalar types, references and unknown fields.
        cases = [
            (("schema_version",), SCHEMA_VERSION + 1),
            (("schema_version",), True),
            (("schema_version",), 1.0),
            (("schema_version",), "1"),
            (("config",), None),
            (("config", "seed"), False),
            (("config", "seed"), 1.5),
            (("config", "debug_mode"), "false"),
            (("turn",), -1),
            (("turn",), True),
            (("turn_order",), None),
            (("turn_order",), {}),
            (("turn_order",), "player-a"),
            (("turn_order",), ("player-a", "player-b")),
            (("turn_order",), []),
            (("turn_order",), ["player-a", "player-b", "player-a"]),
            (("turn_order",), ["player-b"]),
            (("turn_order",), ["player-a"]),
            (("turn_order",), ["player-a", "player-b", "unknown"]),
            (("turn_order", 0), []),
            (("turn_order", 0), " "),
            (("turn_order", 0), True),
            (("active_player_id",), "missing"),
            (("active_player_id",), []),
            (("active_player_id",), None),
            (("active_controller",), "ai"),
            (("active_controller",), "human"),
            (("active_controller",), None),
            (("players",), {}),
            (("players", 0), None),
            (("players", 0, "id"), []),
            (("players", 0, "id"), " "),
            (("players", 0, "controller"), "robot"),
            (("players", 0, "controller"), []),
            (("tiles", 0, "position"), [0, 0]),
            (("tiles", 0, "position", "x"), True),
            (("tiles", 0, "position", "y"), "0"),
            (("cities", 0, "owner_id"), "missing"),
            (("units", 0, "owner_id"), "missing"),
            (("cities", 0, "position", "x"), 999),
            (("units", 0, "position", "x"), 999),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                snapshot = to_snapshot(example_state())
                target = snapshot
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValueError):
                    from_snapshot(snapshot)

    def test_missing_and_unknown_fields(self):
        baseline = to_snapshot(example_state())
        for key in baseline:
            with self.subTest(missing=key):
                snapshot = deepcopy(baseline)
                del snapshot[key]
                with self.assertRaises(ValueError):
                    from_snapshot(snapshot)
        for path in ((), ("config",), ("players", 0), ("tiles", 0, "position")):
            with self.subTest(extra_field_at=path):
                snapshot = deepcopy(baseline)
                target = snapshot
                for key in path:
                    target = target[key]
                target["unexpected"] = "must not be silently discarded"
                with self.assertRaises(ValueError):
                    from_snapshot(snapshot)

    def test_duplicate_ids_and_coordinates_are_rejected(self):
        for collection in ("players", "tiles", "cities", "units"):
            with self.subTest(collection=collection):
                snapshot = to_snapshot(example_state())
                snapshot[collection].append(deepcopy(snapshot[collection][0]))
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    from_snapshot(snapshot)

    def test_root_must_be_an_object(self):
        for malformed in (None, [], "{}", 1):
            with self.subTest(value=malformed), self.assertRaises(ValueError):
                from_snapshot(malformed)


if __name__ == "__main__":
    unittest.main()
