"""Controller command validation and deterministic state transitions."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest

from aig.commands import EliminatePlayer, EndActivation, apply_command
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import ControllerType, GameConfig, GameState
from test_activations import activation_state
from test_state import example_state


class CommandTests(unittest.TestCase):
    def assert_rejected(self, state, command, error):
        expected = deepcopy(state)
        with self.assertRaisesRegex(ValueError, error):
            apply_command(state, command)
        self.assertEqual(state, expected)

    def test_active_player_can_end_activation(self):
        for controller in ControllerType:
            with self.subTest(controller=controller):
                state = activation_state()
                state.players["B"].controller = controller
                self.assertIsNone(apply_command(state, EndActivation("B")))
                self.assertEqual((state.turn, state.active_player_id), (7, "C"))
                state.validate()

    def test_end_activation_wraps_once(self):
        state = activation_state(active="D")
        apply_command(state, EndActivation("D"))
        self.assertEqual((state.turn, state.active_player_id), (8, "A"))

    def test_inactive_actor_cannot_issue_either_command(self):
        for command in (EndActivation("A"), EliminatePlayer("A", "C")):
            with self.subTest(command=command):
                self.assert_rejected(activation_state(), command, "only the active player")

    def test_unknown_actor_cannot_issue_either_command(self):
        for command in (EndActivation("missing"), EliminatePlayer("missing", "C")):
            with self.subTest(command=command):
                self.assert_rejected(activation_state(), command, "unknown command actor")

    def test_eliminated_actor_cannot_issue_either_command(self):
        state = activation_state()
        apply_command(state, EliminatePlayer("B", "C"))
        for command in (EndActivation("C"), EliminatePlayer("C", "A")):
            with self.subTest(command=command):
                self.assert_rejected(state, command, "eliminated player cannot issue")

    def test_elimination_retains_history_and_removes_target_from_live_order(self):
        state = activation_state()
        target = state.players["C"]
        self.assertIsNone(apply_command(state, EliminatePlayer("B", "C")))
        self.assertIs(state.players["C"], target)
        self.assertTrue(target.eliminated)
        self.assertEqual(set(state.players), set("ABCD"))
        self.assertEqual(state.turn_order, ["A", "B", "D"])
        state.validate()

    def test_eliminating_another_player_does_not_advance_activation(self):
        for target in ("A", "C", "D"):
            with self.subTest(target=target):
                state = activation_state()
                apply_command(state, EliminatePlayer("B", target))
                self.assertEqual((state.turn, state.active_player_id), (7, "B"))
                apply_command(state, EndActivation("B"))
                self.assertEqual(state.active_player_id, "D" if target == "C" else "C")
                self.assertEqual(state.turn, 7)

    def test_repeated_target_elimination_is_idempotent(self):
        state = activation_state()
        command = EliminatePlayer("B", "C")
        apply_command(state, command)
        expected = deepcopy(state)
        self.assertIsNone(apply_command(state, command))
        self.assertEqual(state, expected)

    def test_self_elimination_advances_exactly_once(self):
        state = activation_state()
        apply_command(state, EliminatePlayer("B", "B"))
        self.assertEqual((state.turn, state.active_player_id), (7, "C"))
        self.assertEqual(state.turn_order, ["A", "C", "D"])
        self.assertTrue(state.players["B"].eliminated)
        state.validate()

    def test_self_elimination_at_cycle_end_wraps_exactly_once(self):
        state = activation_state(active="D")
        apply_command(state, EliminatePlayer("D", "D"))
        self.assertEqual((state.turn, state.active_player_id), (8, "A"))
        self.assertEqual(state.turn_order, ["A", "B", "C"])
        state.validate()

    def test_successor_can_repeat_elimination_but_eliminated_actor_cannot(self):
        state = activation_state()
        command = EliminatePlayer("B", "B")
        apply_command(state, command)
        self.assert_rejected(state, command, "eliminated player cannot issue")
        expected = deepcopy(state)
        apply_command(state, EliminatePlayer("C", "B"))
        self.assertEqual(state, expected)

    def test_elimination_to_one_survivor_clears_activation_without_turn_increment(self):
        for target in ("player-a", "player-b"):
            with self.subTest(target=target):
                state = example_state()
                apply_command(state, EliminatePlayer("player-b", target))
                self.assertEqual(len(state.turn_order), 1)
                self.assertIsNone(state.active_player_id)
                self.assertIsNone(state.active_controller)
                self.assertEqual(state.turn, 3)
                state.validate()

    def test_terminal_survivor_cannot_issue_commands_even_for_eliminated_target(self):
        state = example_state()
        apply_command(state, EliminatePlayer("player-b", "player-a"))
        for command in (
            EndActivation("player-b"),
            EliminatePlayer("player-b", "player-a"),
            EliminatePlayer("player-b", "player-b"),
        ):
            with self.subTest(command=command):
                self.assert_rejected(state, command, "no active activation")

    def test_zero_survivor_and_empty_states_reject_commands(self):
        state = example_state()
        state.eliminate_player("player-a")
        state.eliminate_player("player-b")
        for command in (EndActivation("player-b"), EliminatePlayer("player-b", "player-a")):
            with self.subTest(command=command):
                self.assert_rejected(state, command, "eliminated player cannot issue")
                self.assert_rejected(GameState(GameConfig(42)), command, "unknown command actor")

    def test_pre_game_commands_rejected(self):
        for command in (EndActivation("B"), EliminatePlayer("B", "C")):
            with self.subTest(command=command):
                self.assert_rejected(
                    activation_state(active=None, turn=0), command, "no active activation"
                )

    def test_unknown_target_rejected(self):
        self.assert_rejected(
            activation_state(), EliminatePlayer("B", "missing"), "cannot eliminate unknown player"
        )

    def test_unsupported_commands_rejected(self):
        for command in (None, object(), "EndActivation", {"actor_id": "B"}):
            with self.subTest(command=command):
                self.assert_rejected(activation_state(), command, "unsupported command type")

    def test_invalid_state_rejected_before_mutation(self):
        for command in (EndActivation("B"), EliminatePlayer("B", "C")):
            with self.subTest(command=command):
                state = activation_state()
                state.turn_order.remove("A")
                self.assert_rejected(state, command, "every player")

    def test_command_identifiers_require_non_empty_strings(self):
        for value in (None, True, 1, [], "", " \t"):
            for construct in (
                lambda: EndActivation(value),
                lambda: EliminatePlayer(value, "C"),
                lambda: EliminatePlayer("B", value),
            ):
                with self.subTest(value=value, construct=construct):
                    with self.assertRaisesRegex(ValueError, "must be a non-empty string"):
                        construct()

    def test_command_objects_are_immutable(self):
        for command, field in (
            (EndActivation("B"), "actor_id"),
            (EliminatePlayer("B", "C"), "actor_id"),
            (EliminatePlayer("B", "C"), "target_player_id"),
        ):
            with self.subTest(command=command, field=field):
                with self.assertRaises(FrozenInstanceError):
                    setattr(command, field, "A")

    def test_commands_round_trip_through_v6_snapshots(self):
        cases = (
            (activation_state(), EndActivation("B")),
            (activation_state(), EliminatePlayer("B", "C")),
            (activation_state(active="D"), EliminatePlayer("D", "D")),
            (example_state(), EliminatePlayer("player-b", "player-b")),
        )
        for state, command in cases:
            with self.subTest(command=command):
                apply_command(state, command)
                snapshot = to_snapshot(state)
                self.assertEqual(snapshot["schema_version"], 8)
                restored = from_snapshot(json.loads(json.dumps(snapshot, allow_nan=False)))
                self.assertEqual(restored, state)
                if state.active_player_id is not None:
                    next_command = EndActivation(state.active_player_id)
                    apply_command(state, next_command)
                    apply_command(restored, next_command)
                    self.assertEqual(restored, state)

    def test_copied_states_execute_independently_and_deterministically(self):
        for command in (EndActivation("B"), EliminatePlayer("B", "C"), EliminatePlayer("B", "B")):
            with self.subTest(command=command):
                source = activation_state()
                snapshot = to_snapshot(source)
                first = deepcopy(source)
                second = from_snapshot(snapshot)
                apply_command(first, command)
                self.assertEqual(second, source)
                self.assertEqual(to_snapshot(source), snapshot)
                apply_command(second, command)
                self.assertEqual(first, second)
                self.assertEqual(to_snapshot(first), to_snapshot(second))
                self.assertEqual(to_snapshot(source), snapshot)


if __name__ == "__main__":
    unittest.main()
