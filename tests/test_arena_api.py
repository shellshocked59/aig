"""Real API command routing and independent sessions, with no live providers."""

from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from aig.api import create_app
from aig.arena import ArenaEndTurn, ArenaSimulation, replay
from aig.arena.snapshots import command_to_dict, state_hash
from aig.settings import load_settings
from test_arena import core_win_commands, duel
from aig.arena.state import UnitType
from aig.arena import ArenaAttack, ArenaHeal


class ArenaApiTests(unittest.TestCase):
    def setUp(self):
        with patch("aig.api.load_settings", return_value=load_settings(local_file=None, environ={})):
            self.app = create_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)

    def command(self, command):
        return self.client.post("/api/arena/commands", json=command_to_dict(command))

    def test_environment_registry_and_missing_arena(self):
        self.assertEqual([e["id"] for e in self.client.get("/api/environments").json()], ["empire", "arena"])
        self.assertEqual(self.client.get("/api/arena").status_code, 404)
        self.assertEqual(self.client.get("/api/arena/trace").status_code, 404)
        self.assertEqual(self.command(ArenaEndTurn("blue")).status_code, 404)

    def test_demo_public_state_and_end_turn(self):
        response = self.client.post("/api/arena/demo")
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertEqual(state["environment"], "arena")
        self.assertEqual((state["active_player_id"], state["action_points_remaining"]), ("blue", 5))
        self.assertEqual(len(state["board"]["tiles"]), 45)
        self.assertEqual(len(state["units"]), 8)
        self.assertNotIn("aiProviders", state)
        self.assertEqual(self.command(ArenaEndTurn("blue")).json()["active_player_id"], "red")

    def test_complete_manual_match_via_http_and_trace_replay(self):
        self.client.post("/api/arena/demo")
        for command in core_win_commands():
            response = self.command(command)
            self.assertEqual(response.status_code, 200, response.text)
        state = response.json()
        self.assertEqual(state["winner_player_id"], "blue")
        self.assertIsNone(state["active_player_id"])
        self.assertEqual(state["turn"], 1)
        self.assertEqual(self.command(ArenaEndTurn("blue")).status_code, 422)
        trace = self.client.get("/api/arena/trace").json()
        self.assertEqual(state_hash(replay(trace).state), trace["entries"][-1]["after_hash"])

    def test_heal_and_attack_routes_use_engine(self):
        s = duel(UnitType.CLERIC)
        s.units["actor"].hp = 1
        self.app.state.arena_session._simulation = ArenaSimulation(s)
        response = self.command(ArenaHeal("blue", "actor", "actor"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["units"][0]["hp"], 6)
        response = self.command(ArenaAttack("blue", "actor", "target"))
        self.assertEqual(response.json()["units"][1]["hp"], 15)
        self.assertEqual(response.json()["action_points_remaining"], 3)

    def test_foreign_payloads_and_resets_cannot_cross_environments(self):
        empire = self.client.post("/api/game/demo").json()
        arena = self.client.post("/api/arena/demo").json()
        self.assertEqual(self.client.post("/api/arena/commands", json={"type": "end_activation"}).status_code, 422)
        self.assertEqual(self.client.post("/api/game/commands", json=command_to_dict(ArenaEndTurn("blue"))).status_code, 422)
        self.assertEqual(self.client.get("/api/game").json(), empire)
        self.assertEqual(self.client.get("/api/arena").json(), arena)
        self.client.post("/api/game/start")
        self.client.post("/api/game/commands", json={"type": "end_activation"})
        self.assertEqual(self.client.get("/api/arena").json(), arena)
        empire = self.client.get("/api/game").json()
        self.command(ArenaEndTurn("blue"))
        self.client.post("/api/arena/demo")
        self.assertEqual(self.client.get("/api/game").json(), empire)

    def test_invalid_requests_leave_state_and_trace_unchanged(self):
        initial = self.client.post("/api/arena/demo").json()
        for payload in ([], {"schema_version": "arena-command-v1", "type": "arena_end_turn", "actor_id": "red"},
                        {**command_to_dict(ArenaEndTurn("blue")), "extra": True},
                        {"schema_version": "arena-command-v1", "type": "arena_move", "actor_id": "blue",
                         "unit_id": "blue-knight", "destination": {"x": True, "y": 0}}):
            response = self.client.post("/api/arena/commands", json=payload)
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(self.client.get("/api/arena").json(), initial)
            self.assertEqual(self.client.get("/api/arena/trace").json()["entries"], [])

    def test_concurrent_same_actor_end_turn_serializes(self):
        self.client.post("/api/arena/demo")
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.command(ArenaEndTurn("blue")), range(2)))
        self.assertEqual(sorted(r.status_code for r in responses), [200, 422])
        self.assertEqual(len(self.client.get("/api/arena/trace").json()["entries"]), 1)
