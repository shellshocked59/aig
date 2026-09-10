"""Small offline benchmark tests; real inference is never required."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from aig.ai.benchmark import (
    BENCHMARK_VERSION, JsonlTrace, benchmark, canonical_hash, compare_runs, initial_state,
    main, run_trial, terminal_summary,
)
from aig.ai.benchmark_metrics import RunMetrics, inference_metrics, statistics
from aig.ai.controller import AiController
from aig.ai.ollama import OllamaStrategyProvider
from aig.ai.plan_schema import canonical_json
from aig.ai.simulate import simulate
from aig.ai.strategy import HeuristicStrategyProvider, Posture, StrategicPlan
from aig.commands import AttackUnit, EndActivation, FoundCity, SetCityProduction, apply_command
from aig.settings import AiSettings, Settings
from aig.snapshots import to_snapshot
from aig.state import Position, UnitType


def envelope(content=None, **metrics):
    return canonical_json(dict(done=True, message=dict(
        content=content if content is not None else canonical_json(StrategicPlan(Posture.EXPAND).to_dict()),
        thinking="HIDDEN REASONING MUST NOT BE STORED"), **metrics))


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = Settings()
        network = patch("aig.ai.ollama.urlopen", side_effect=AssertionError("live network forbidden in tests"))
        network.start()
        self.addCleanup(network.stop)

    def trial(self, provider=None, name="heuristic", turns=2, folder="trial"):
        return run_trial(provider or HeuristicStrategyProvider(), provider_name=name, turns=turns,
                         settings=self.settings, directory=self.root / folder)

    def test_canonical_hash_and_trace_bytes(self):
        self.assertEqual(canonical_hash({"b": 2, "a": [1, "é"]}), canonical_hash({"a": [1, "é"], "b": 2}))
        self.assertNotEqual(canonical_hash([1, 2]), canonical_hash([2, 1]))
        with self.assertRaises(ValueError):
            canonical_hash(float("nan"))
        with JsonlTrace(self.root / "trace.jsonl") as trace:
            trace.write({"b": 2, "a": "é"})
        data = (self.root / "trace.jsonl").read_bytes()
        self.assertEqual(data, '{"a":"é","b":2}\n'.encode())
        self.assertEqual(hashlib.sha256(data).hexdigest(), trace.hash.hexdigest())

    def test_fresh_independent_equal_states(self):
        a, b = initial_state(), initial_state()
        self.assertEqual(to_snapshot(a), to_snapshot(b))
        a.players["A"].gold = 42
        self.assertEqual(b.players["A"].gold, 0)

    def test_paired_repeatability_output_and_offline_defaults(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            report = benchmark(output=self.root / "report", games=2, turns=2, settings=self.settings)
        self.assertEqual(report["benchmarkVersion"], BENCHMARK_VERSION)
        self.assertEqual(json.loads((self.root / "report/summary.json").read_text()), report)
        self.assertEqual(len(report["runs"]), 4)
        for comparison in report["comparison"]:
            self.assertTrue(comparison["initialStatesEqual"])
            self.assertTrue(all(comparison["hashesEqual"].values()))
            self.assertEqual(comparison["deltas"]["final_city_count"], 0)
            self.assertEqual(comparison["equivalentStateReplans"], dict(matched=2, identicalPlans=2, differentPlans=0))
        self.assertTrue(all(report["repeatability"]["a"]["hashesIdentical"].values()))
        self.assertIn("hashes identical", terminal_summary(report))
        self.assertIsNone(report["runs"][0]["inference"]["tokens"]["eval_count"]["mean"])
        self.assertEqual(report["runs"][0]["inference"]["requests"], 0)

    def test_instrumented_execution_matches_existing_simulation(self):
        trial = self.trial(turns=3)
        existing = simulate(3)
        snapshot = json.loads((self.root / "trial/final-state.json").read_text())
        self.assertEqual(hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest(),
                         existing["snapshot_sha256"])
        commands = [json.loads(line) for line in (self.root / "trial/commands.jsonl").read_text().splitlines()]
        activations = [json.loads(line) for line in (self.root / "trial/activations.jsonl").read_text().splitlines()]
        legacy_trace = hashlib.sha256()
        for activation in activations:
            result = dict(player_id=activation["player_id"], plan=activation["plan"],
                          commands_executed=[c["command"] for c in commands if c["activation"] == activation["activation"]])
            legacy_trace.update(json.dumps(result, sort_keys=True).encode())
        self.assertEqual(legacy_trace.hexdigest(), existing["trace_sha256"])
        self.assertEqual(trial["metrics"]["activations_completed"], 6)

    def test_plan_trace_and_reuse(self):
        trial = self.trial(turns=6)
        plans = [json.loads(line) for line in (self.root / "trial/plans.jsonl").read_text().splitlines()]
        self.assertEqual(len(plans), 4)
        self.assertEqual([p["turn"] for p in plans], [0, 0, 5, 5])
        self.assertEqual([p["plan_age_turns"] for p in plans], [None, None, 5, 5])
        self.assertEqual(plans[2]["previous_plan"], plans[0]["new_plan"])
        self.assertEqual(plans[2]["replan_reason"], "expired")
        self.assertEqual(canonical_hash(plans[0]["strategic_state"]), plans[0]["strategic_state_sha256"])
        self.assertEqual(trial["metrics"]["plans_reused"], 8)
        self.assertEqual(trial["metrics"]["plan_age_turns"]["mean"], 20 / 12)

    def test_comparison_delta_direction(self):
        a = self.trial(folder="a")
        b = deepcopy(a)
        b["metrics"]["final_city_count"] += 3
        b["players"]["A"]["final_city_count"] += 3
        b["inference"]["request_wall_clock_total_seconds"] = 2
        b["pureProviderRun"] = False
        b["fallbackCount"] = 1
        comparison = compare_runs(a, b)
        self.assertEqual(comparison["deltas"]["final_city_count"], 3)
        self.assertEqual(comparison["playerDeltas"]["A"]["final_city_count"], 3)
        self.assertEqual(comparison["deltas"]["inference_time_seconds"], 2)
        self.assertFalse(comparison["pureProviderRuns"])

    def test_failure_fallback_and_inference_trace(self):
        requester = Mock(side_effect=TimeoutError("timeout"))
        trial = self.trial(OllamaStrategyProvider(self.settings.ollama, requester=requester), name="ollama")
        self.assertFalse(trial["pureProviderRun"])
        self.assertEqual(trial["fallbackCount"], 2)
        self.assertEqual(trial["inference"]["failures"]["timeout"], 2)
        self.assertEqual(trial["inference"]["failures"]["heuristic_fallback"], 2)
        self.assertEqual(trial["inference"]["requests"], 2)
        self.assertEqual(trial["inference"]["retries"], 0)
        baseline = self.trial(folder="baseline")
        self.assertEqual(trial["hashes"]["final_state"], baseline["hashes"]["final_state"])
        self.assertEqual(trial["hashes"]["commands"], baseline["hashes"]["commands"])
        self.assertEqual(len((self.root / "trial/inference.jsonl").read_text().splitlines()), 2)

    def test_successful_fake_ollama_counts_and_no_hidden_reasoning(self):
        requester = Mock(return_value=envelope(prompt_eval_count=512, eval_count=80, total_duration=2_000_000_000))
        trial = self.trial(OllamaStrategyProvider(self.settings.ollama, requester=requester), name="ollama")
        self.assertTrue(trial["pureProviderRun"])
        self.assertEqual(trial["inference"]["maximum_prompt_context_percent"], 12.5)
        self.assertEqual(trial["inference"]["timings"]["ollama_total_seconds"]["mean"], 2)
        raw = (self.root / "trial/inference.jsonl").read_text()
        self.assertNotIn("HIDDEN REASONING", raw)
        self.assertNotIn('"messages"', raw)
        self.assertIn('"raw_content"', raw)

    def test_fake_ollama_repeated_differences_are_reported(self):
        responses = iter((Posture.EXPAND, Posture.DEFEND))

        def factory(name, settings):
            if name == "heuristic":
                return HeuristicStrategyProvider()
            plan = StrategicPlan(next(responses))
            return OllamaStrategyProvider(settings.ollama, requester=Mock(
                return_value=envelope(canonical_json(plan.to_dict()))))

        report = benchmark(output=self.root / "different", games=2, turns=1,
                           provider_b="ollama", settings=self.settings, provider_factory=factory)
        self.assertFalse(report["repeatability"]["b"]["hashesIdentical"]["plans"])
        self.assertTrue(report["repeatability"]["b"]["allPureProviderRuns"])
        self.assertGreater(report["comparison"][1]["equivalentStateReplans"]["differentPlans"], 0)

    def test_fallback_reuse_does_not_inflate_failure_counts(self):
        provider = OllamaStrategyProvider(self.settings.ollama, requester=Mock(side_effect=TimeoutError()))
        trial = self.trial(provider, name="ollama", turns=4)
        self.assertEqual(trial["fallbackCount"], 2)
        self.assertEqual(trial["metrics"]["plans_reused"], 6)
        rows = [json.loads(line) for line in (self.root / "trial/activations.jsonl").read_text().splitlines()]
        self.assertTrue(all(row["fallback_used"] for row in rows))
        self.assertTrue(all(row["actual_provider"] == "heuristic" for row in rows))

    def test_every_replan_is_saved_beyond_runtime_ring_buffer(self):
        self.settings = replace(self.settings, ai=AiSettings(replan_interval=1))
        trial = self.trial(turns=33)
        self.assertEqual(trial["metrics"]["plans_created"], 66)
        self.assertEqual(len((self.root / "trial/plans.jsonl").read_text().splitlines()), 66)

    def test_output_and_cli_validation(self):
        for arguments in ({"games": 0}, {"turns": 0}, {"scenario": "fake"}, {"provider_a": "fake"}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                benchmark(output=self.root / "bad", settings=self.settings, **arguments)
        occupied = self.root / "keep.txt"
        occupied.write_text("keep")
        with self.assertRaisesRegex(ValueError, "new or empty"):
            benchmark(output=self.root, settings=self.settings)
        self.assertEqual(occupied.read_text(), "keep")
        with patch("builtins.print") as printer, patch("aig.ai.benchmark.load_settings", return_value=self.settings):
            main(["--turns", "1", "--output", str(self.root / "cli")])
        self.assertIn("Benchmark complete", printer.call_args_list[0].args[0])


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.state = initial_state()
        self.writer = Mock()
        self.controller = AiController(HeuristicStrategyProvider())
        self.controller.previous_plan = StrategicPlan(Posture.EXPAND)
        self.metrics = RunMetrics(self.state, {"A": self.controller, "B": self.controller}, self.writer)

    def issue(self, command):
        self.metrics.observe("before", self.state, command)
        apply_command(self.state, command)
        self.metrics.observe("after", self.state, command)

    def test_founding_is_not_a_loss_and_records_zero_based_time(self):
        self.issue(FoundCity("A", "unit-1", "capital", "Capital"))
        totals, players = self.metrics.finish(self.state)
        self.assertEqual(totals["unit_losses"], 0)
        self.assertEqual(totals["cities_founded"], 1)
        self.assertEqual(totals["cities_founded_at"], [dict(turn=0, activation=0, player_activation=0,
                                                          player_id="A", city_id="capital")])
        self.assertEqual(players["B"]["unused_settlers"], 1)

    def test_pre_economy_target_and_idle_measurement(self):
        self.issue(FoundCity("A", "unit-1", "capital", "Capital"))
        self.state.cities["capital"].production_stored = 20
        self.issue(SetCityProduction("A", "capital", UnitType.WARRIOR))
        self.issue(EndActivation("A"))
        totals, _ = self.metrics.finish(self.state)
        self.assertEqual(totals["units_produced_by_type"], {"warrior": 1})
        self.assertIsNone(self.state.cities["capital"].production_target)
        self.assertEqual(totals["activations_with_no_production_target"], 0)
        self.assertEqual(totals["idle_movable_combat_units"], 1)
        self.assertEqual(totals["activations_without_research_target_with_choices"], 1)

    def test_unset_production_accumulates_without_waste(self):
        self.issue(FoundCity("A", "unit-1", "capital", "Capital"))
        self.issue(EndActivation("A"))
        totals, _ = self.metrics.finish(self.state)
        self.assertEqual(totals["city_activations_without_target_with_production"], 1)
        self.assertEqual(totals["production_generated_without_target"], totals["final_production_stored"])
        self.assertGreater(totals["final_production_stored"], 0)

    def test_produced_settlers_and_target_distance_samples(self):
        self.issue(FoundCity("A", "unit-1", "capital", "Capital"))
        self.state.cities["capital"].production_stored = 40
        self.issue(SetCityProduction("A", "capital", UnitType.SETTLER))
        self.issue(EndActivation("A"))
        self.issue(FoundCity("B", "unit-3", "enemy", "Enemy"))
        self.controller.previous_plan = StrategicPlan(Posture.ATTACK, "A", "capital")
        self.metrics.activation = 1
        self.issue(EndActivation("B"))
        totals, players = self.metrics.finish(self.state)
        self.assertEqual(totals["settlers_produced"], 1)
        self.assertEqual(players["A"]["unused_settlers"], 1)
        self.assertEqual(players["B"]["combat_distance_to_target_tiles"],
                         dict(samples=1, min=7, max=7, mean=7, median=7))

    def test_combat_kills_and_actual_damage_including_retaliation(self):
        self.state.units["unit-4"].position = Position(3, 2)
        self.issue(AttackUnit("A", "unit-2", "unit-4"))
        totals, players = self.metrics.finish(self.state)
        self.assertGreater(players["A"]["damage_dealt"], 0)
        self.assertGreater(players["B"]["damage_dealt"], 0)
        self.assertEqual(totals["kills"], 0)
        self.state.units["unit-2"].moves_remaining = 1
        self.state.units["unit-4"].hp = 1
        self.issue(AttackUnit("A", "unit-2", "unit-4"))
        totals, players = self.metrics.finish(self.state)
        self.assertEqual(players["A"]["kills"], 1)
        self.assertEqual(players["B"]["unit_losses"], 1)
        self.assertEqual(self.writer.write.call_args.args[0]["outcome"]["damage"][1]["hp_lost"], 1)

    def test_churn_and_invalidated_plan_counts(self):
        old = StrategicPlan(Posture.EXPAND).to_dict()
        new = StrategicPlan(Posture.ATTACK, "B", "target").to_dict()
        controller = SimpleNamespace(last_trace=dict(previous_plan=old, resulting_plan=new,
                                    replan_reason="invalid_target", fallback_used=False),
                                     summary={"planAgeTurns": 0}, previous_plan=StrategicPlan(Posture.ATTACK))
        self.metrics.record_plan("A", controller)
        self.assertEqual(self.metrics.players["A"]["plan_changes"], 1)
        self.assertEqual(self.metrics.players["A"]["target_changes"], 1)
        self.assertEqual(self.metrics.players["A"]["posture_changes"], 1)
        self.assertEqual(self.metrics.players["A"]["invalidated_plans"], 1)


class InferenceAccountingTests(unittest.TestCase):
    def test_empty_and_token_timing_statistics(self):
        self.assertEqual(statistics([]), dict(samples=0, min=None, max=None, mean=None, median=None))
        traces = [dict(fallback_used=False, retry_count=1, attempts=[
            dict(error_category="schema_validation", wall_clock_seconds=2,
                 metrics=dict(prompt_eval_count=100, eval_count=10, total_duration=1_000_000_000,
                              prompt_eval_duration=200_000_000, eval_duration=800_000_000)),
            dict(wall_clock_seconds=4, metrics=dict(prompt_eval_count=200, eval_count=20,
                                                  total_duration=3_000_000_000))])]
        result = inference_metrics(traces, 4096)
        self.assertEqual(result["tokens"]["prompt_eval_count"], dict(samples=2, min=100, max=200, mean=150, median=150))
        self.assertEqual(result["timings"]["request_wall_clock_seconds"]["mean"], 3)
        self.assertEqual(result["timings"]["ollama_total_seconds"]["mean"], 2)
        self.assertEqual(result["timings"]["prompt_eval_seconds"]["samples"], 1)
        self.assertEqual(result["repair_success_count"], 1)
        self.assertEqual(result["failures"]["schema_validation"], 1)

    def test_categorized_real_provider_failures_and_repairs(self):
        invalid_reference = StrategicPlan(Posture.ATTACK, "missing").to_dict()
        cases = [
            (TimeoutError(), "timeout", 1),
            (URLError(TimeoutError()), "timeout", 1),
            (URLError("connection refused"), "transport_failure", 1),
            (HTTPError("http://test.invalid", 503, "unavailable", {}, None), "non_2xx", 1),
            ("not an envelope", "malformed_ollama_envelope", 2),
            (envelope("{"), "malformed_json_content", 2),
            (envelope("{}"), "schema_validation", 2),
            (envelope(canonical_json(invalid_reference)), "invalid_strategic_references", 2),
        ]
        for response, category, count in cases:
            with self.subTest(category=category, response=response):
                requester = Mock(side_effect=response) if isinstance(response, Exception) else Mock(return_value=response)
                controller = AiController(OllamaStrategyProvider(Settings().ollama, requester=requester))
                controller.plan_for(initial_state(), "A")
                result = inference_metrics([controller.last_trace], 4096)
                self.assertEqual(result["failures"][category], count)
                self.assertEqual(result["requests"], count)
                self.assertEqual(result["fallback_count"], 1)
                self.assertEqual(result["failures"]["repair_failed"], count - 1)

    def test_actual_repair_success(self):
        requester = Mock(side_effect=[envelope("{}"), envelope()])
        controller = AiController(OllamaStrategyProvider(Settings().ollama, requester=requester))
        controller.plan_for(initial_state(), "A")
        result = inference_metrics([controller.last_trace], 4096)
        self.assertEqual(result["repair_success_count"], 1)
        self.assertEqual(result["fallback_count"], 0)
        self.assertEqual(result["failures"]["repair_failed"], 0)

    def test_reported_metrics_survive_malformed_envelope(self):
        requester = Mock(side_effect=[canonical_json(dict(prompt_eval_count=100, total_duration=1_000_000_000)),
                                      envelope()])
        controller = AiController(OllamaStrategyProvider(Settings().ollama, requester=requester))
        controller.plan_for(initial_state(), "A")
        result = inference_metrics([controller.last_trace], 4096)
        self.assertEqual(result["maximum_prompt_tokens"], 100)
        self.assertEqual(result["timings"]["ollama_total_seconds"]["mean"], 1)
        self.assertEqual(result["failures"]["malformed_ollama_envelope"], 1)


if __name__ == "__main__":
    unittest.main()
