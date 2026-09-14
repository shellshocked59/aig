"""Phase 8A offline repair contract, safety, transport, and one-call tests."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.observation import ArenaObservation
from aig.arena.ai.repair import REPAIR_V1, REPAIR_V2, MAX_REJECTED_BYTES, feedback, repair_version
from aig.arena.ai.stepwise import OllamaArenaStepProvider, OpenAIArenaStepProvider, STEP_PROMPT, checked_step, parse_step
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.repair_benchmark import benchmark, challenge_set, validate_challenge, run_trial
from aig.arena.snapshots import canonical_json
from aig.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


class Fake(OllamaArenaStepProvider):
    def __init__(self, version=REPAIR_V1, outputs=(), secrets=()):
        super().__init__(Settings().ollama, repair_version=version, secrets=secrets)
        self.outputs = list(outputs)
        self.messages = []

    def request(self, messages, record):
        self.messages.append(deepcopy(messages))
        record["metrics"] = dict(prompt_eval_count=100, eval_count=10)
        if self.outputs:
            output = self.outputs.pop(0)
            if isinstance(output, Exception):
                raise output
            return output
        obs = ArenaObservation(messages[0]["content"].removeprefix("ArenaObservation:\n"))
        return canonical_json(dict(schema_version="arena-turn-plan-schema-v1", actions=obs.to_dict()["legal_actions"][:1]))


class RepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.challenges = challenge_set()["challenges"]

    def setUp(self):
        for target in ("socket.socket.connect", "socket.getaddrinfo", "urllib.request.OpenerDirector.open",
                       "httpx.Client.send", "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("live inference forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def test_frozen_v1_and_defaults(self):
        fixture = json.loads((ROOT/"tests/fixtures/arena-step-repair-v1.json").read_text())
        self.assertEqual(feedback(REPAIR_V1, "invalid_reference"), fixture["feedback"])
        self.assertEqual(hashlib.sha256(fixture["feedback"].encode()).hexdigest(), fixture["feedback_sha256"])
        self.assertEqual(hashlib.sha256(STEP_PROMPT.encode()).hexdigest(), fixture["step_prompt_sha256"])
        self.assertEqual(repair_version(), REPAIR_V1)
        self.assertEqual(Fake().repair_version, REPAIR_V1)
        with self.assertRaises(ValueError):
            Fake("v3")

    def test_frozen_source_and_artifacts(self):
        hashes = json.loads((ROOT/"tests/fixtures/arena-phase8a-preservation.json").read_text())
        # Phase 9A adds V3 dispatch and schema hooks. Reverse only those exact
        # additions before checking the unchanged Phase 8A source hashes.
        extensions = json.loads((ROOT/"tests/fixtures/arena-phase9a-source-extensions.json").read_text())
        for path, expected in hashes.items():
            with self.subTest(path=path):
                source = (ROOT/path).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
                for current, previous in extensions.get(path, []):
                    self.assertEqual(source.count(current), 1)
                    source = source.replace(current, previous)
                self.assertEqual(hashlib.sha256(source.encode("utf-8")).hexdigest(), expected)

    def test_every_challenge_both_versions_valid_and_invalid(self):
        for challenge in self.challenges:
            obs, error = validate_challenge(challenge)
            for version in (REPAIR_V1, REPAIR_V2):
                with self.subTest(challenge=challenge["id"], version=version):
                    provider = Fake(version)
                    result = run_trial(provider, challenge, 1)
                    self.assertEqual(result["repair_request_count"], 1)
                    self.assertEqual(len(provider.messages), 1)
                    self.assertTrue(result["repair_success"])
                    self.assertTrue(result["execution_success"])
                    self.assertIn(result["repaired_action"], obs.to_dict()["legal_actions"])
                    messages = provider.messages[0]
                    self.assertEqual(messages[0], dict(role="user", content="ArenaObservation:\n"+obs.canonical))
                    evidence = provider.rejection_evidence(canonical_json(challenge["invalid_decision"]), obs, error)
                    if version == REPAIR_V1:
                        self.assertEqual(messages[1]["content"], feedback(REPAIR_V1, "invalid_reference"))
                    else:
                        text = messages[1]["content"]
                        self.assertIn(canonical_json(evidence), text)
                        self.assertIsNotNone(evidence["parsed_decision"])
                        self.assertEqual(evidence["validation"]["message"], error.diagnostic.message)
                        self.assertEqual(evidence["validation"]["field_path"], error.diagnostic.field_path)
                        guidance = text.split("\nReturn zero actions", 1)[1]
                        for tactical in ("Core", "Finish", "Revive", "Snipe", "damage", "winning", "AP", "prefer", "closest"):
                            self.assertNotIn(tactical, guidance)
                    invalid = Fake(version, [canonical_json(challenge["invalid_decision"])])
                    result = run_trial(invalid, challenge, 1)
                    self.assertFalse(result["repair_success"])
                    self.assertTrue(result["parse_status"])
                    self.assertTrue(result["schema_status"])
                    self.assertFalse(result["current_catalog_status"])
                    self.assertEqual(len(invalid.messages), 1)
                    self.assertEqual(len(result["rejected_decisions"]), 2)

    def test_end_turn_and_failure_stages(self):
        challenge = self.challenges[0]
        for raw, parse, schema in [("not JSON", False, None), ('{"actions":[]}', True, False)]:
            row = run_trial(Fake(REPAIR_V2, [raw]), challenge, 1)
            self.assertEqual((row["parse_status"], row["schema_status"]), (parse, schema))
            self.assertFalse(row["repair_success"])
        row = run_trial(Fake(REPAIR_V2, [canonical_json(ArenaTurnPlan().to_dict())]), challenge, 1)
        self.assertTrue(row["end_turn"])
        self.assertTrue(row["execution_success"])
        self.assertEqual(row["ap_cost"], 0)

    def test_rejected_trace_and_secret_canaries(self):
        challenge = self.challenges[0]
        obs, error = validate_challenge(challenge)
        canaries = ["OPENAI_API_KEY=sk-secret-canary", "Authorization: Bearer secret-canary",
                    "Settings(api_key=secret-canary)", "provider client configuration secret-canary",
                    "environment-secret-canary", "private-reasoning-canary", "shortsecret"]
        for canary in canaries:
            bad = deepcopy(challenge["invalid_decision"])
            bad["actions"][0]["unit_id"] = canary
            for raw in (canary, canonical_json(bad), '{"reasoning":"'+canary+'"}', canary*40000):
                provider = Fake(REPAIR_V2, [raw, raw])
                _, call = checked_step(provider, "ollama", obs)
                serialized = canonical_json(call)
                self.assertNotIn(canary, serialized)
                self.assertNotIn(canary, canonical_json(provider.messages[1:]))
                self.assertFalse(call["success"])
                for attempt in call["attempts"]:
                    evidence = attempt["rejected_decision"]
                    self.assertIsNone(evidence["raw_content"])
                    self.assertEqual(evidence["repair_result"], "failed")
                    self.assertLessEqual(len(canonical_json(evidence).encode()), MAX_REJECTED_BYTES)
        provider = Fake(outputs=[canonical_json(challenge["invalid_decision"])])
        _, call = checked_step(provider, "ollama", obs)
        self.assertTrue(call["success"])
        self.assertEqual(call["attempts"][0]["rejected_decision"]["repair_result"], "succeeded")
        self.assertIsNotNone(provider.last_trace["attempts"][1]["raw_content"])

    def test_exact_catalog_no_approximation_and_diagnostics(self):
        for challenge in self.challenges:
            obs, _ = validate_challenge(challenge)
            for action in obs.to_dict()["legal_actions"]:
                valid = dict(schema_version="arena-turn-plan-schema-v1", actions=[action])
                self.assertEqual(parse_step(canonical_json(valid), obs).actions[0].to_dict(), action)
            for action in obs.to_dict()["legal_actions"]:
                bad = deepcopy(action)
                bad["unit_id"] = "missing-unit"
                with self.assertRaises(ArenaProviderError) as caught:
                    parse_step(canonical_json(dict(schema_version="arena-turn-plan-schema-v1", actions=[bad])), obs)
                self.assertEqual(caught.exception.diagnostic.field_path, "actions[0].unit_id")

    def test_real_adapter_wire_shapes_with_fake_transports(self):
        challenge = self.challenges[0]
        for version in (REPAIR_V1, REPAIR_V2):
            local_calls, cloud_calls = [], []
            raw = canonical_json(ArenaTurnPlan().to_dict())

            def requester(url, payload, timeout):
                local_calls.append(json.loads(payload))
                return canonical_json(dict(done=True, message=dict(content=raw)))

            def create(**kwargs):
                cloud_calls.append(kwargs)
                return NS(status="completed", error=None, usage=None,
                          output=[NS(type="message", role="assistant", status="completed",
                                     content=[NS(type="output_text", text=raw)])])

            local = OllamaArenaStepProvider(Settings().ollama, requester=requester, repair_version=version)
            cloud = OpenAIArenaStepProvider(replace(Settings().openai, api_key="test-canary"),
                client=NS(responses=NS(create=create)), repair_version=version)
            for provider in (local, cloud):
                self.assertTrue(run_trial(provider, challenge, 1)["repair_success"])
            self.assertEqual(len(local_calls), 1)
            self.assertEqual(len(cloud_calls), 1)
            self.assertEqual(local_calls[0]["messages"][1:], cloud_calls[0]["input"])
            self.assertEqual(local_calls[0]["messages"][0]["content"], STEP_PROMPT)
            self.assertEqual(cloud_calls[0]["instructions"], STEP_PROMPT)

    def test_controlled_schedule_and_no_second_repair(self):
        for version in (REPAIR_V1, REPAIR_V2):
            with TemporaryDirectory() as temp:
                provider = Fake(version)
                with patch("aig.arena.repair_benchmark.source_manifest", return_value=dict(sourceManifestHash="fixed")):
                    report = benchmark(output=Path(temp)/"run", repair_version=version,
                        provider_factory=lambda *args, **kwargs: provider)
                self.assertEqual(report["repairRequests"], 24)
                self.assertEqual(report["repairSuccesses"], 24)
                self.assertEqual(len(provider.messages), 24)
                saved = json.loads((Path(temp)/"run/manifest.json").read_text())
                self.assertEqual(saved["repairVersion"], version)
                self.assertEqual(saved["preflightRequests"], 0)
                self.assertEqual(saved["initialInferenceRequests"], 0)
        with TemporaryDirectory() as temp:
            bad = Fake(outputs=["not JSON"]*24)
            with patch("aig.arena.repair_benchmark.source_manifest", return_value=dict(sourceManifestHash="fixed")):
                report = benchmark(output=Path(temp)/"invalid", provider_factory=lambda *args, **kwargs: bad)
            self.assertEqual(report["repairRequests"], 24)
            self.assertEqual(report["repairSuccesses"], 0)
            self.assertEqual(report["status"], "complete")

    def test_transport_failure_stops_and_ceiling_rejected_before_requests(self):
        with TemporaryDirectory() as temp:
            provider = Fake(outputs=[ArenaProviderError("transport_failure")])
            with patch("aig.arena.repair_benchmark.source_manifest", return_value=dict(sourceManifestHash="fixed")):
                report = benchmark(output=Path(temp)/"run", provider_factory=lambda *args, **kwargs: provider)
            self.assertEqual(report["repairRequests"], 1)
            self.assertEqual(report["status"], "stopped")
            with self.assertRaises(ValueError):
                benchmark(output=Path(temp)/"too-many", trials=5)
            self.assertFalse((Path(temp)/"too-many").exists())


if __name__ == "__main__":
    unittest.main()
