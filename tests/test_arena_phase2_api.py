"""Phase 2 complete HTTP match and strict environment/command isolation."""

from copy import deepcopy
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from aig.api import create_app
from aig.settings import load_settings
from aig.arena import ArenaSimulation, replay, to_snapshot, state_hash
from aig.arena.snapshots import command_to_dict, digest

FIXTURE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/arena-phase2-smoke.py"))


class Phase2ApiTests(unittest.TestCase):
    def setUp(self):
        with patch("aig.api.load_settings", return_value=load_settings(local_file=None, environ={})):
            self.app = create_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        self.app.state.arena_session._simulation = ArenaSimulation(FIXTURE["initial_state"]())

    def test_all_actions_through_http_match_offline_trace_exactly(self):
        expected = FIXTURE["run_match"]()
        empire = self.client.post("/api/game/demo").json()
        for command in FIXTURE["commands"]():
            response = self.client.post("/api/arena/commands", json=command_to_dict(command))
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(self.client.get("/api/game").json(), empire)
        self.assertEqual(response.json()["winner_player_id"], "blue")
        trace = self.client.get("/api/arena/trace").json()
        self.assertEqual(trace, expected.trace())
        self.assertEqual(to_snapshot(replay(trace).state), to_snapshot(expected.state))
        self.assertEqual(state_hash(expected.state), "dfa08c98197375a6231ef3a8013aaf84afdfdfc47913b669c12974fe4fdf64ec")
        self.assertEqual(digest(trace), "42585d1fe45943cf0aa127e3f37b312fa297a2974a1fd61a32d88273360c70b7")
        values = expected.metrics()["players"]["blue"]
        self.assertEqual([values[k] for k in ("units_downed", "units_revived", "units_finished",
                                              "friendly_fire_damage", "core_damage", "shield_bash_pushes",
                                              "fireball_targets_hit")], [3, 1, 1, 3, 30, 1, 4])
        self.assertEqual(sum(values["ap_spent_by_action"].values()), values["ap_used"])

    def test_every_special_invalid_and_foreign_request_is_atomic(self):
        empire = self.client.post("/api/game/demo").json()
        before = self.client.get("/api/arena").json()
        before_trace = self.client.get("/api/arena/trace").json()
        kinds = {"arena_finish", "arena_revive", "arena_shield_bash", "arena_snipe", "arena_fireball"}
        for command in FIXTURE["commands"]():
            payload = command_to_dict(command)
            if payload["type"] not in kinds:
                continue
            self.assertEqual(self.client.post("/api/game/commands", json=payload).status_code, 422)
            for mutation in (dict(unit_id="missing"), dict(actor_id="unknown"), dict(extra=True),
                             dict(schema_version="arena-command-v1")):
                response = self.client.post("/api/arena/commands", json={**payload, **mutation})
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(self.client.get("/api/arena").json(), before)
                self.assertEqual(self.client.get("/api/arena/trace").json(), before_trace)
                self.assertEqual(self.client.get("/api/game").json(), empire)

    def test_fireball_wire_position_is_strict(self):
        payload = next(command_to_dict(c) for c in FIXTURE["commands"]() if type(c).__name__ == "ArenaFireball")
        before = self.client.get("/api/arena/trace").json()
        for position in (None, [], {}, {"x": True, "y": 2}, {"x": 2.5, "y": 2},
                         {"x": 2, "y": 2, "z": 0}, {"x": 9, "y": 2}):
            response = self.client.post("/api/arena/commands", json={**payload, "target_position": position})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(self.client.get("/api/arena/trace").json(), before)

    def test_public_status_and_abilities_are_derived_not_persisted(self):
        for command in FIXTURE["commands"]()[:3]:
            self.assertEqual(self.client.post("/api/arena/commands", json=command_to_dict(command)).status_code, 200)
        dto = self.client.get("/api/arena").json()
        body = next(u for u in dto["units"] if u["id"] == "red-mage")
        self.assertEqual((body["status"], body["hp"]), ("downed", 0))
        self.assertFalse(any(body["actions"].values()))
        ranger = next(u for u in dto["units"] if u["id"] == "blue-ranger")
        self.assertEqual(ranger["abilities"]["snipe"], dict(ap_cost=2, range=4))
        self.assertFalse(ranger["actions"]["snipe"])  # one AP remains
        snapshot = self.client.get("/api/arena/trace").json()["initial_snapshot"]
        self.assertFalse({"abilities", "stats", "actions", "los"} & set(snapshot["units"][0]))

    def test_new_trace_counters_are_verified_against_reexecution(self):
        sim = FIXTURE["run_match"]()
        for key in ("units_downed", "units_revived", "units_finished", "friendly_fire_damage",
                    "core_damage", "bonus_tile_attacks", "shield_bash_pushes", "fireball_targets_hit"):
            trace = deepcopy(sim.trace())
            trace["entries"][0][key] += 1
            with self.assertRaises(ValueError):
                replay(trace)
