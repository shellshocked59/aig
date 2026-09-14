"""Phase 8C offline preparation, fake transport, integrity and metrics tests."""
from copy import deepcopy
import inspect
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.observation import ArenaObservation
from aig.arena.ai.repair import REPAIR_V1, REPAIR_V2
from aig.arena.ai.stepwise import OllamaArenaStepProvider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_versions import source_manifest
from aig.arena.fullmatch_benchmark import RequestBudget, pilot, run_match, verify_match
from aig.arena.repair_fullmatch_experiment import prepare, run_arm, load_plan, slots, contracts, compare
from aig.arena.repair_fullmatch_metrics import match_metrics, aggregate, read
from aig.arena.repair_benchmark import challenge_set
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json, from_snapshot, digest
from aig.settings import Settings

EMPTY = canonical_json(ArenaTurnPlan().to_dict())


class Fake(OllamaArenaStepProvider):
    def __init__(self, version=REPAIR_V1, outputs=()):
        super().__init__(Settings().ollama, repair_version=version)
        self.outputs = list(outputs)
        self.calls = []

    def request(self, messages, record):
        self.calls.append(deepcopy(messages))
        record["metrics"] = dict(prompt_eval_count=100, eval_count=10)
        item = self.outputs.pop(0) if self.outputs else EMPTY
        obs = ArenaObservation(messages[0]["content"].removeprefix("ArenaObservation:\n"))
        if item == "action":
            return canonical_json(dict(schema_version="arena-turn-plan-schema-v1", actions=obs.to_dict()["legal_actions"][:1]))
        if isinstance(item, Exception):
            raise item
        return item


class RepairFullMatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for target in ("socket.socket.connect", "socket.getaddrinfo", "urllib.request.OpenerDirector.open",
                       "httpx.Client.send", "openai.resources.responses.Responses.create"):
            mock = patch(target, side_effect=AssertionError("network forbidden"))
            mock.start()
            self.addCleanup(mock.stop)
        self.source = source_manifest()
        mock = patch("aig.arena.repair_fullmatch_experiment.source_manifest", return_value=self.source)
        mock.start()
        self.addCleanup(mock.stop)

    def plan(self, ceiling=30):
        return prepare(self.root/"prep", settings=Settings(), v1_output=self.root/"v1",
                       v2_output=self.root/"v2", comparison_output=self.root/"comparison", request_ceiling=ceiling)

    def one(self, outputs, *, version=REPAIR_V2, limit=20, turns=1):
        exp = dict(contracts(Settings(), self.source), repairVersion=version, **slots()[0])
        provider = Fake(version, outputs)
        budget = RequestBudget(limit)
        provider.before_request = budget.take
        result = run_match(self.root/"match", exp["assignments"], {"ollama": provider}, exp, turns=turns)
        return result, match_metrics(self.root/"match"), provider

    def test_pairing_manifest_and_defaults(self):
        plan = self.plan()
        arms = plan["arms"]
        for version in (REPAIR_V1, REPAIR_V2):
            matches = arms[version]["matches"]
            self.assertEqual(len(matches), 6)
            self.assertEqual([m["qwenSide"] for m in matches], ["blue", "red"]*3)
            self.assertEqual([m["pair_id"] for m in matches], [f"pair-{i:02d}" for i in range(1,7)])
            self.assertEqual({m["repairVersion"] for m in matches}, {version})
            self.assertEqual({m["benchmarkVersion"] for m in matches}, {"arena-benchmark-v2"})
        for a,b in zip(arms[REPAIR_V1]["matches"], arms[REPAIR_V2]["matches"]):
            self.assertEqual({k for k in a if a[k] != b[k]}, {"repairVersion", "experimentOverrides"})
        self.assertEqual(Fake().repair_version, REPAIR_V1)
        self.assertEqual(inspect.signature(pilot).parameters["repair_version"].default, REPAIR_V1)
        self.assertEqual(load_plan(self.root/"prep/plan.json", Settings()), plan)
        self.assertFalse((self.root/"v1").exists())

    def test_repaired_endturn_and_initial_invalid_retained(self):
        r, m, p = self.one(["{}", EMPTY])
        self.assertTrue(r["verification"]["success"])
        self.assertEqual((m["first_response_invalid"], m["eventual_decision_success"]), (1,1))
        event = m["repair_events"][0]
        self.assertTrue(event["repaired_endturn"])
        self.assertEqual(event["ap_abandoned"], 5)
        self.assertGreater(event["legal_action_count"], 0)
        self.assertIn("nonmove_legal_action_count", event)
        self.assertIn("core", event["teams"]["own_team"])
        self.assertEqual(event["rejected"][0]["repair_result"], "succeeded")
        a = aggregate([m], total_requests=2)
        self.assertEqual(a["REPAIR_ENDTURN_AP_ABANDONED"], 5)
        self.assertEqual(a["normal_endturn_rate"], 0)
        self.assertEqual(a["repaired_endturn_rate"], 1)
        self.assertEqual(a["repair_telemetry"]["context_occupancy"]["max"], 110/4096)
        self.assertEqual(len(p.calls), 2)

    def test_successful_repaired_nonempty_action(self):
        r, m, _ = self.one(["{}", "action", EMPTY])
        e = m["repair_events"][0]
        self.assertTrue(e["exact_catalog_membership"])
        self.assertTrue(e["authoritative_execution_succeeded"])
        self.assertEqual(e["ap_cost"], 1)
        self.assertEqual(e["resulting_ap"], 4)
        self.assertEqual(aggregate([m], total_requests=3)["repaired_action_count"], 1)
        self.assertEqual(len(e["resulting_state_hash"]), 64)

    def test_endturn_abandons_available_nonmove_actions(self):
        snapshot = next(c["snapshot"] for c in challenge_set()["challenges"] if c["id"] == "midgame")
        def scenario(state=None):
            return ArenaSimulation(from_snapshot(snapshot) if state is None else state)
        with patch("aig.arena.fullmatch_benchmark.ArenaSimulation", side_effect=scenario):
            result, metrics, _ = self.one(["{}", EMPTY], turns=snapshot["turn"]+1)
        self.assertTrue(result["verification"]["success"])
        event = metrics["repair_events"][0]
        self.assertGreater(event["nonmove_legal_action_count"], 0)
        self.assertEqual(event["ap_abandoned"], snapshot["action_points_remaining"])
        self.assertEqual(aggregate([metrics], total_requests=metrics["requests"])["REPAIR_ENDTURN_WITH_NONMOVE_ACTIONS_AVAILABLE"], 1)

    def test_failed_repair_stops_with_exact_partial_replay(self):
        r, m, p = self.one(["action", "{}", "{}"])
        self.assertEqual(r["error_category"], "repair_failed")
        self.assertTrue(r["verification"]["success"])
        self.assertEqual(m["repairs_failed"], 1)
        self.assertEqual(m["decisions_before_first_invalid"], 1)
        self.assertEqual(m["fatal_boundary"]["ap"], 4)
        trace = read(self.root/"match/command-trace.json")
        self.assertEqual(m["fatal_boundary"]["state_hash"], trace["entries"][0]["after_hash"])
        self.assertNotEqual(m["fatal_boundary"]["state_hash"], m["stopping_state_hash"])
        self.assertEqual(len(p.calls), 3)

    def test_ceiling_preserves_prefix_no_repair_request_overflow(self):
        r, m, p = self.one(["action", "{}"], limit=2)
        self.assertEqual(r["status"], "request_ceiling")
        self.assertTrue(verify_match(self.root/"match")["success"])
        self.assertEqual(len(p.calls), 2)
        self.assertEqual(m["repairs_attempted"], 0)
        trace = read(self.root/"match/command-trace.json")
        self.assertEqual(len(trace["entries"]), 1)
        self.assertEqual(read(self.root/"match/final-snapshot.json")["action_points_remaining"], 4)

    def arm(self, version, provider, ceiling):
        # Real runner and controller, but a one-round offline fixture for speed.
        with patch("aig.arena.repair_fullmatch_experiment.MAX_TURNS", 1):
            return run_arm(self.root/"prep/plan.json", settings=Settings(), repair_version=version,
                           request_ceiling=ceiling, output=self.root/("v1" if version == REPAIR_V1 else "v2"),
                           provider_factory=lambda settings, name, **kw: self.factory(provider, name, kw))

    def factory(self, provider, name, kwargs):
        self.assertEqual(name, "ollama")
        self.assertEqual(kwargs, {"repair_version": provider.repair_version})
        return provider

    def short_plan(self, ceiling):
        with patch("aig.arena.repair_fullmatch_experiment.MAX_TURNS", 1):
            return self.plan(ceiling)

    def test_cumulative_arm_ceiling_and_independent_later_pairs(self):
        self.short_plan(6)
        p = Fake(REPAIR_V1, [EMPTY, "{}", "{}"])
        r = self.arm(REPAIR_V1, p, 6)
        self.assertEqual(r["requests"], 6)
        self.assertEqual(len(p.calls), 6)
        self.assertEqual(r["matches"][0]["status"], "failed")
        self.assertNotEqual(r["matches"][1]["status"], "not_started")
        self.assertEqual(len(r["matches"]), 6)
        self.assertEqual(r["matches"][-1]["reason"], "request_ceiling")

    def test_two_explicit_arms_and_offline_comparison(self):
        self.short_plan(20)
        a = self.arm(REPAIR_V1, Fake(REPAIR_V1), 20)
        b = self.arm(REPAIR_V2, Fake(REPAIR_V2), 20)
        self.assertEqual((a["requests"], b["requests"]), (7,7))
        self.assertEqual(a["status"], "complete")
        with patch("aig.arena.repair_fullmatch_experiment.MAX_TURNS", 1):
            c = compare(self.root/"prep/plan.json", settings=Settings())
        self.assertEqual(len(c["paired_outcomes"]), 6)

    def test_wrong_version_and_source_change_stop_before_transport(self):
        self.short_plan(20)
        p = Fake(REPAIR_V2)
        with patch.object(self, "factory", return_value=p):
            report = self.arm(REPAIR_V1, p, 20)
        self.assertEqual(report["status"], "hard_stop")
        self.assertEqual(len(p.calls), 0)
        self.assertEqual(len(report["matches"]), 6)

    def test_source_guard_rejects_second_arm_before_transport(self):
        self.short_plan(20)
        self.arm(REPAIR_V1, Fake(REPAIR_V1), 20)
        with patch("aig.arena.repair_fullmatch_experiment.frozen_guard", return_value=lambda: (_ for _ in ()).throw(ArenaProviderError("source_mutation"))):
            with self.assertRaisesRegex(ArenaProviderError, "source_mutation"):
                self.arm(REPAIR_V2, Fake(REPAIR_V2), 20)
        self.assertFalse((self.root/"v2").exists())

    def test_corrupt_control_blocks_second_arm(self):
        self.short_plan(20)
        self.arm(REPAIR_V1, Fake(REPAIR_V1), 20)
        path = self.root/"v1/pair-01/final-snapshot.json"
        path.write_text("{}")
        with self.assertRaises(ArenaProviderError):
            self.arm(REPAIR_V2, Fake(REPAIR_V2), 20)
        self.assertFalse((self.root/"v2").exists())

    def test_preflight_failure_is_one_request_no_repair_or_matches(self):
        self.short_plan(20)
        p = Fake(REPAIR_V1, ["{}"])
        report = self.arm(REPAIR_V1, p, 20)
        self.assertEqual(report["status"], "stopped")
        self.assertEqual(report["requests"], 1)
        self.assertEqual(len(p.calls), 1)
        self.assertTrue(all(m["status"] == "not_started" for m in report["matches"]))

    def test_accounting_defect_hard_stops_without_extra_requests(self):
        self.short_plan(20)
        p = Fake(REPAIR_V1)
        from aig.arena.ai.stepwise import checked_step
        def broken(*args, **kwargs):
            plan, call = checked_step(*args, **kwargs)
            call["provider_requests"] += 1
            return plan, call
        with patch("aig.arena.repair_fullmatch_experiment.checked_step", side_effect=broken):
            with self.assertRaises(ArenaProviderError):
                self.arm(REPAIR_V1, p, 20)
        self.assertEqual(len(p.calls), 1)
        report = read(self.root/"v1/summary.json")
        self.assertEqual(report["hard_stop"], "request_accounting_defect")

    def test_v2_cannot_run_before_control(self):
        self.short_plan(20)
        with self.assertRaises(FileNotFoundError):
            self.arm(REPAIR_V2, Fake(REPAIR_V2), 20)
        self.assertFalse((self.root/"v2").exists())


if __name__ == "__main__":
    unittest.main()
