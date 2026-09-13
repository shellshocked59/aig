"""Human/heuristic orchestration through the actual HTTP routes."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from aig.api import create_app
from aig.settings import load_settings
from aig.arena import ArenaSimulation, ArenaEndTurn, replay, state_hash
from aig.arena.ai.probes import create_probe
from aig.arena.ai.controller import controller_setup
from aig.arena.snapshots import command_to_dict


class ArenaAiApiTests(unittest.TestCase):
    def setUp(self):
        with patch("aig.api.load_settings", return_value=load_settings(local_file=None, environ={})):
            self.app = create_app()
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def end_turn(self, player="blue"):
        return self.client.post("/api/arena/commands", json=command_to_dict(ArenaEndTurn(player)))

    def test_ai_demo_same_layout_snapshot_and_explicit_controllers(self):
        manual = self.client.post("/api/arena/demo").json()
        snapshot = self.client.get("/api/arena/trace").json()["initial_snapshot"]
        ai = self.client.post("/api/arena/demo-ai").json()
        self.assertEqual(ai["controllers"], dict(blue="human", red="heuristic_ai"))
        self.assertEqual(ai["board"], manual["board"])
        self.assertEqual(ai["units"], manual["units"])
        self.assertEqual(self.client.get("/api/arena/trace").json()["initial_snapshot"], snapshot)
        self.assertEqual(ai["ai_turns"], [])

    def test_human_end_turn_runs_one_ai_turn_and_replays(self):
        self.client.post("/api/arena/demo-ai")
        response = self.end_turn()
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertEqual(state["active_player_id"], "blue")
        self.assertEqual(state["turn"], 1)
        self.assertEqual(state["action_points_remaining"], 5)
        self.assertEqual(len(state["ai_turns"]), 1)
        trace = state["ai_turns"][0]
        self.assertEqual(trace["player_id"], "red")
        self.assertEqual(trace["provider_type"], "arena-heuristic-v1")
        self.assertIsNone(trace["invalid_action"])
        commands = self.client.get("/api/arena/trace").json()
        self.assertEqual(state_hash(replay(commands).state), commands["entries"][-1]["after_hash"])

    def test_manual_demo_reset_preserves_manual_end_turn(self):
        self.client.post("/api/arena/demo-ai")
        self.end_turn()
        manual = self.client.post("/api/arena/demo").json()
        self.assertEqual(manual["controllers"], dict(blue="human", red="human"))
        self.assertEqual(manual["ai_turns"], [])
        self.assertEqual(self.end_turn().json()["active_player_id"], "red")
        self.assertEqual(len(self.client.get("/api/arena/trace").json()["entries"]), 1)

    def test_terminal_ai_stops_without_end_turn(self):
        state = create_probe("winning_core_line")
        state.active_player_id = "red"
        sim = ArenaSimulation(state)
        session = self.app.state.arena_session
        session._simulation = sim
        session._controllers = controller_setup(state, "manual")
        from aig.arena.ai.controller import ArenaControllerType
        session._controllers["blue"] = ArenaControllerType.HEURISTIC_AI
        response = self.end_turn("red")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["winner_player_id"], "blue")
        self.assertIsNone(response.json()["active_player_id"])
        self.assertEqual([e["command"]["type"] for e in sim.trace()["entries"]], ["arena_end_turn", "arena_attack"])

    def test_manual_cannot_issue_commands_for_ai(self):
        self.client.post("/api/arena/demo-ai")
        session = self.app.state.arena_session
        session._simulation.execute(ArenaEndTurn("blue"))
        before = session.trace()
        self.assertEqual(self.end_turn("red").status_code, 422)
        self.assertEqual(session.trace(), before)

    def test_complete_human_pass_vs_ai_battle_and_empire_isolation(self):
        empire = self.client.post("/api/game/demo").json()
        self.client.post("/api/arena/demo-ai")
        for _ in range(20):
            response = self.end_turn()
            self.assertEqual(response.status_code, 200)
            if response.json()["winner_player_id"]:
                break
        self.assertEqual(response.json()["winner_player_id"], "red")
        self.assertEqual(self.end_turn().status_code, 422)
        self.assertEqual(self.client.get("/api/game").json(), empire)
        trace = self.client.get("/api/arena/trace").json()
        self.assertEqual(replay(trace).trace(), trace)


if __name__ == "__main__":
    unittest.main()
