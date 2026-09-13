"""Deterministic elimination and activation transitions."""

from copy import deepcopy
import json
import unittest

from aig.snapshots import from_snapshot, to_snapshot
from aig.state import ControllerType, GameConfig, GameState, PlayerState
from test_state import example_state


def activation_state(*, active: str | None = "B", turn: int = 7) -> GameState:
    return GameState(
        config=GameConfig(42),
        turn=turn,
        turn_order=["A", "B", "C", "D"],
        active_player_id=active,
        # Deliberately different from activation order.
        players={name: PlayerState(name, ControllerType.AI) for name in "DCBA"},
    )


class ActivationTests(unittest.TestCase):
    def test_normal_advancement_and_wrap_across_two_cycles(self):
        state = activation_state(active="A", turn=0)
        for expected_turn, expected_active in (
            (0, "B"), (0, "C"), (0, "D"), (1, "A"),
            (1, "B"), (1, "C"), (1, "D"), (2, "A"),
        ):
            state.finish_activation()
            self.assertEqual((state.turn, state.active_player_id), (expected_turn, expected_active))
            state.validate()

    def test_elimination_around_active_player_does_not_skip_survivors(self):
        cases = [
            (("C",), ["A", "B", "D"], 7, "D"),
            (("C", "D"), ["A", "B"], 8, "A"),
            (("A",), ["B", "C", "D"], 7, "C"),
            (("D",), ["A", "B", "C"], 7, "C"),
            (("A", "C"), ["B", "D"], 7, "D"),
        ]
        for eliminated, order, next_turn, next_active in cases:
            with self.subTest(eliminated=eliminated):
                state = activation_state()
                for player_id in eliminated:
                    state.eliminate_player(player_id)
                    self.assertEqual((state.turn, state.active_player_id), (7, "B"))
                    state.validate()
                self.assertEqual(state.turn_order, order)
                state.finish_activation()
                self.assertEqual((state.turn, state.active_player_id), (next_turn, next_active))
                state.validate()

    def test_eliminating_last_player_makes_previous_player_wrap(self):
        state = activation_state(active="C")
        state.eliminate_player("D")
        state.finish_activation()
        self.assertEqual((state.turn, state.active_player_id), (8, "A"))

    def test_eliminating_active_player_ends_activation(self):
        for active, successor, turn in (("A", "B", 7), ("B", "C", 7), ("D", "A", 8)):
            with self.subTest(active=active):
                state = activation_state(active=active)
                state.eliminate_player(active)
                self.assertEqual((state.turn, state.active_player_id), (turn, successor))
                self.assertNotIn(active, state.turn_order)
                self.assertTrue(state.players[active].eliminated)
                state.validate()

    def test_elimination_retains_player_and_other_players_cities_but_removes_live_units(self):
        state = example_state()
        player = state.players["player-b"]
        cities = deepcopy(state.cities)
        state.eliminate_player("player-b")
        self.assertIs(state.players["player-b"], player)
        self.assertTrue(player.eliminated)
        self.assertEqual(state.turn_order, ["player-a"])
        self.assertEqual(state.units, {})
        self.assertEqual(state.cities, cities)
        state.validate()

    def test_repeated_elimination_is_idempotent(self):
        # Include active-player wrap and terminal transitions.
        for player_id in ("A", "B", "D"):
            with self.subTest(player=player_id):
                state = activation_state(active="D")
                state.eliminate_player(player_id)
                expected = deepcopy(state)
                state.eliminate_player(player_id)
                self.assertEqual(state, expected)
        state = example_state()
        state.eliminate_player("player-b")
        expected = deepcopy(state)
        state.eliminate_player("player-b")
        self.assertEqual(state, expected)

    def test_unknown_or_malformed_elimination_rejected_without_mutation(self):
        state = activation_state()
        expected = deepcopy(state)
        for player_id in ("missing", "", None, []):
            with self.subTest(player=player_id), self.assertRaises(ValueError):
                state.eliminate_player(player_id)
            self.assertEqual(state, expected)

    def test_one_survivor_is_terminal_without_advancement(self):
        for eliminated in ("player-a", "player-b"):
            with self.subTest(eliminated=eliminated):
                state = example_state()
                state.eliminate_player(eliminated)
                self.assertEqual(len(state.turn_order), 1)
                self.assertIsNone(state.active_player_id)
                self.assertIsNone(state.active_controller)
                self.assertEqual(state.turn, 3)
                state.validate()
                expected = deepcopy(state)
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError, "no active activation"):
                        state.finish_activation()
                    self.assertEqual(state, expected)

    def test_zero_survivors_is_terminal_and_keeps_history(self):
        state = example_state()
        state.eliminate_player("player-a")
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "game has ended"):
            state.eliminate_player("player-b")
        self.assertEqual(state, before)
        self.assertEqual(state.result.winner_player_id, "player-b")
        # Zero survivors remain representable in a pre-game setup.
        empty = type(state)(state.config)
        self.assertEqual(from_snapshot(to_snapshot(empty)), empty)

    def test_pre_game_elimination_does_not_start_activation(self):
        state = activation_state(active=None, turn=0)
        for player_id in "ABCD":
            state.eliminate_player(player_id)
            self.assertIsNone(state.active_player_id)
            self.assertEqual(state.turn, 0)
            state.validate()
        with self.assertRaisesRegex(ValueError, "no active activation"):
            state.finish_activation()

    def test_finish_pre_game_rejected_without_mutation(self):
        state = activation_state(active=None, turn=0)
        expected = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "no active activation"):
            state.finish_activation()
        self.assertEqual(state, expected)

    def test_operations_reject_invalid_state_before_mutating(self):
        for operation in (lambda s: s.eliminate_player("C"), lambda s: s.finish_activation()):
            state = activation_state()
            state.turn_order.remove("A")
            expected = deepcopy(state)
            with self.assertRaises(ValueError):
                operation(state)
            self.assertEqual(state, expected)

    def test_deepcopy_and_restored_copies_advance_independently(self):
        source = activation_state()
        snapshot = to_snapshot(source)
        expected = deepcopy(source)
        copies = [deepcopy(source), from_snapshot(snapshot), from_snapshot(snapshot)]
        copies[0].eliminate_player("C")
        copies[0].finish_activation()
        self.assertEqual((copies[0].turn, copies[0].active_player_id), (7, "D"))
        copies[1].eliminate_player("D")
        copies[1].finish_activation()
        copies[1].finish_activation()
        self.assertEqual((copies[1].turn, copies[1].active_player_id), (8, "A"))
        self.assertEqual(copies[2], expected)
        self.assertEqual(source, expected)
        self.assertEqual(snapshot, to_snapshot(expected))


class EliminationValidationTests(unittest.TestCase):
    def test_eliminated_must_be_boolean(self):
        self.assertFalse(PlayerState("A", ControllerType.AI).eliminated)
        for value in (0, 1, None, "false", []):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "eliminated must be a boolean"):
                    PlayerState("A", ControllerType.AI, eliminated=value)
                state = activation_state()
                state.players["A"].eliminated = value
                with self.assertRaisesRegex(ValueError, "eliminated must be a boolean"):
                    to_snapshot(state)

    def test_eliminated_player_in_live_order_rejected(self):
        state = activation_state()
        state.players["C"].eliminated = True
        with self.assertRaisesRegex(ValueError, "turn_order contains an eliminated player"):
            state.validate()
        with self.assertRaises(ValueError):
            to_snapshot(state)

    def test_eliminated_active_player_rejected(self):
        state = activation_state()
        state.players["B"].eliminated = True
        state.turn_order.remove("B")
        with self.assertRaisesRegex(ValueError, "active_player_id cannot be an eliminated player"):
            state.validate()

    def test_one_player_construction_requires_no_active_player(self):
        for turn in (0, 4):
            with self.subTest(turn=turn):
                state = GameState(
                    GameConfig(42), turn=turn, turn_order=["A"],
                    players={"A": PlayerState("A", ControllerType.AI)},
                )
                self.assertEqual(from_snapshot(to_snapshot(state)), state)
                with self.assertRaisesRegex(ValueError, "fewer than two"):
                    GameState(
                        GameConfig(42), turn=turn, turn_order=["A"],
                        players=state.players, active_player_id="A",
                    )


class EliminationSnapshotTests(unittest.TestCase):
    def test_round_trip_elimination_and_continued_advancement(self):
        state = activation_state()
        state.eliminate_player("C")
        snapshot = to_snapshot(state)
        wire = json.dumps(snapshot, allow_nan=False)
        self.assertEqual(json.dumps(to_snapshot(state), allow_nan=False), wire)
        restored = from_snapshot(json.loads(wire))
        self.assertEqual(restored, state)
        self.assertTrue(restored.players["C"].eliminated)
        self.assertEqual(restored.turn_order, ["A", "B", "D"])
        self.assertEqual((restored.turn, restored.active_player_id), (7, "B"))
        self.assertEqual(json.dumps(to_snapshot(restored), allow_nan=False), wire)
        restored.finish_activation()
        self.assertEqual((restored.turn, restored.active_player_id), (7, "D"))
        restored.finish_activation()
        self.assertEqual((restored.turn, restored.active_player_id), (8, "A"))

    def test_terminal_snapshots_round_trip(self):
        state = example_state()
        for player_id in ("player-a", "player-b"):
            state = example_state()
            state.eliminate_player(player_id)
            restored = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
            self.assertEqual(restored, state)
            self.assertIsNone(restored.active_player_id)
            self.assertEqual(restored.turn, 3)

    def test_missing_or_invalid_elimination_field_rejected(self):
        snapshot = to_snapshot(activation_state())
        del snapshot["players"][0]["eliminated"]
        with self.assertRaisesRegex(ValueError, "exactly these fields"):
            from_snapshot(snapshot)
        for value in (None, 0, 1, "false", [], True):
            with self.subTest(value=value):
                snapshot = to_snapshot(activation_state())
                snapshot["players"][0]["eliminated"] = value
                # True is also invalid here: this player remains in turn_order.
                with self.assertRaises(ValueError):
                    from_snapshot(snapshot)

    def test_v1_snapshots_rejected_without_migration_or_repair(self):
        snapshot = to_snapshot(example_state())
        snapshot["schema_version"] = 1
        for player in snapshot["players"]:
            del player["eliminated"]
        for order in (["player-a", "player-b"], ["player-b"], []):
            with self.subTest(order=order):
                snapshot["turn_order"] = order
                with self.assertRaisesRegex(ValueError, "unsupported schema_version"):
                    from_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
