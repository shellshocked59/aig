"""Controlled Arena benchmarks: all model paths use fake inference only."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aig.arena.ai.contracts import ArenaTurnPlan, SnipeAction
from aig.arena.ai.controller import ArenaAiController
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import ArenaObservation, build_observation
from aig.arena.ai.probes import PROBE_NAMES, create_probe
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark import benchmark, main, read_rows, verify_trial
from aig.arena.benchmark_metrics import distribution, inference_metrics
from aig.arena.benchmark_provider import checked_plan
from aig.arena.benchmark_versions import artifact, frozen_probe, probe_set, manifest
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json, digest, to_snapshot
from aig.ai.model_profiles import inference_configuration
from aig.settings import Settings


class FakeModel(ModelArenaTurnProvider):
    def __init__(self, settings, name="ollama", outputs=()):
        self.name = name
        self.whole_settings = settings
        self.outputs = list(outputs)
        self.calls = 0
        self.observations = []
        super().__init__(getattr(settings, name))

    def configuration(self):
        return inference_configuration(self.name, self.whole_settings)

    def request(self, messages, record):
        self.calls += 1
        observation = ArenaObservation(messages[0]["content"].removeprefix("ArenaObservation:\n"))
        self.observations.append(observation.hash)
        record["metrics"] = dict(prompt_eval_count=100, eval_count=10, total_duration=123,
                                 prompt_eval_duration=80, eval_duration=43) if self.name == "ollama" else dict(
                                 input_tokens=100, cached_input_tokens=20, output_tokens=10,
                                 reasoning_tokens=0, total_tokens=110)
        if self.outputs:
            value = self.outputs.pop(0)
            if isinstance(value, Exception):
                raise value
            if value is not None:
                return value
        return canonical_json(HeuristicArenaTurnProvider().create_turn_plan(observation).to_dict())


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "results"
        # Any accidental live path is a test failure; fake models bypass transports.
        for target in ("urllib.request.urlopen", "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("external request forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def run_benchmark(self, **kwargs):
        return benchmark(output=self.output, games=1, probe_trials=1, **kwargs)

    def test_matches_repeat_and_preserve_phase3_hashes(self):
        report = benchmark(output=self.output, games=4)
        self.assertEqual(report["preflight"], [])
        self.assertEqual(report["trialsStarted"], 4)
        expected = dict(plans="5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c",
                        commands="88328e37527ddb68abf63b091613f7c1282a4581ebe72da394511838b3e6f0ae",
                        final_state="01720d448acca31206574e16fa3182ffc5c2a40e033e89d5043d56fb21939f2a",
                        command_trace="6b7c60fbb3d8dcd8451e0692bd764135a5c1b31c5abd35dbcc1101042b6f4f5d")
        for run in report["runs"]:
            self.assertTrue(run["valid"])
            self.assertEqual(run["hashes"], report["runs"][0]["hashes"])
            self.assertEqual({k: run["hashes"][k] for k in expected}, expected)
            self.assertEqual((run["metrics"]["winner"], run["metrics"]["loser"]), ("red", "blue"))
            self.assertEqual((run["metrics"]["player_turns"], run["metrics"]["global_turns"]), (10, 4))
            blue, red = (run["metrics"]["players"][p] for p in ("blue", "red"))
            self.assertEqual((blue["ap_available"], blue["ap_planned"], blue["ap_executed"], blue["ap_unused"]), (25,25,25,0))
            self.assertEqual((red["ap_available"], red["ap_planned"], red["ap_executed"], red["ap_unused"]), (25,23,23,2))
            self.assertEqual((blue["damage_dealt"], red["damage_dealt"], red["healing_done"]), (50,48,35))
            self.assertEqual((red["units_revived"], blue["units_finished"], red["units_finished"]), (2,1,1))
            self.assertEqual((red["total_hp"], blue["total_hp"], blue["removed_units"]), (33,0,1))
            self.assertTrue(all(sum(p["actions_by_type"][kind] for p in (blue,red)) > 0 for kind in blue["actions_by_type"]))

    def test_frozen_probes_exactly_match_phase3_and_are_detached(self):
        self.assertEqual(set(probe_set()["probes"]), set(PROBE_NAMES))
        for name in PROBE_NAMES:
            with self.subTest(name=name):
                state = frozen_probe(name)
                self.assertEqual(to_snapshot(state), to_snapshot(create_probe(name)))
                self.assertEqual(build_observation(state).hash, probe_set()["probes"][name]["observation_hash"])
                state.units.clear()
                self.assertTrue(frozen_probe(name).units)

    def test_all_probes_outcomes_repeat_and_replay(self):
        report = benchmark(output=self.output, mode="probes", probe_trials=2)
        self.assertEqual(report["trialsStarted"], 14)
        by_name = {}
        for row in report["runs"]:
            self.assertTrue(row["verification"]["success"])
            frozen = artifact("arena-heuristic-probes-v1")["probes"][row["probe"]]
            self.assertEqual(row["hashes"], frozen["hashes"])
            self.assertEqual(row["metrics"], frozen["metrics"])
            self.assertEqual(row["probe_outcome"], frozen["outcome"])
            if row["probe"] in by_name:
                self.assertEqual(row["hashes"], by_name[row["probe"]]["hashes"])
            by_name[row["probe"]] = row
        for name in ("winning_core_line", "team_elimination", "revive_decision"):
            self.assertTrue(by_name[name]["probe_outcome"]["objective_achieved"])
        fire = by_name["fireball_friendly_fire"]["metrics"]["players"]["blue"]
        self.assertGreater(fire["friendly_fire_damage"], 0)
        self.assertGreater(fire["fireball_friendly_targets_hit"], 0)
        self.assertGreater(by_name["finish_or_core"]["metrics"]["players"]["blue"]["units_finished"], 0)

    def test_all_mode_provider_comparison_and_side_swap(self):
        made = {}
        def factory(settings, name):
            made[name] = FakeModel(settings, name)
            return made[name]
        report = self.run_benchmark(mode="all", turns=1, blue_provider="ollama", red_provider="openai",
                                    side_swap=True, probe="winning_core_line", provider_factory=factory)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(len(report["preflight"]), 2)
        self.assertEqual(report["trialsStarted"], 4)
        a,b,c,d = report["runs"]
        self.assertEqual(a["assignments"], dict(blue="ollama", red="openai"))
        self.assertEqual(b["assignments"], dict(blue="openai", red="ollama"))
        self.assertEqual(a["hashes"]["initial_state"], b["hashes"]["initial_state"])
        self.assertEqual(c["hashes"]["observations"], d["hashes"]["observations"])
        self.assertEqual(a["outcome"], "turn_limit")
        self.assertEqual(a["metrics"]["player_turns"], 2)
        self.assertEqual(report["inference"]["ollama"]["provider_requests"], 3)
        self.assertEqual(report["inferenceByMode"]["matches"]["ollama"]["provider_requests"], 2)

    def test_preflight_once_per_distinct_provider_and_no_trials(self):
        made = []
        def factory(settings, name):
            made.append(FakeModel(settings, name))
            return made[-1]
        report = self.run_benchmark(blue_provider="ollama", red_provider="ollama", preflight_only=True,
                                    provider_factory=factory)
        self.assertEqual(len(made), 1)
        self.assertEqual(made[0].calls, 1)
        self.assertEqual(report["trialsStarted"], 0)
        self.assertEqual(report["preflight"][0]["provider_requests"], 1)
        self.assertTrue(made[0].repair)

    def test_preflight_repair_disabled_and_zero_trials(self):
        model = FakeModel(Settings(), outputs=["garbage", None])
        report = self.run_benchmark(mode="all", blue_provider="ollama", red_provider="ollama",
                                    provider_factory=lambda *_: model)
        self.assertEqual((report["status"], report["trialsStarted"], model.calls), ("preflight_failed",0,1))
        self.assertTrue(model.repair)
        self.assertFalse((self.output / "runs").exists())
        self.assertTrue((self.output / "summary.json").exists())

    def test_midmatch_failure_preserves_prefix_and_aborts(self):
        model = FakeModel(Settings(), outputs=[None, None, ArenaProviderError("timeout")])
        report = benchmark(output=self.output, games=4, blue_provider="ollama", red_provider="ollama",
                           provider_factory=lambda *_: model)
        self.assertEqual((report["status"], report["trialsStarted"]), ("trial_failed",1))
        row = report["runs"][0]
        self.assertFalse(row["valid"])
        self.assertTrue(row["verification"]["success"])
        self.assertEqual(row["metrics"]["player_turns"], 1)
        self.assertEqual(len(read_rows(Path(row["directory"]) / "inference.jsonl")), 2)
        self.assertGreater(len(read_rows(Path(row["directory"]) / "commands.jsonl")), 0)
        self.assertEqual(report["inference"]["ollama"]["provider_requests"], 0)

    def test_fallback_preflight_and_trial_are_rejected_before_execution(self):
        class Contaminated(FakeModel):
            def create_turn_plan(self, observation):
                plan = super().create_turn_plan(observation)
                if self.calls >= self.contaminate_at:
                    self._last_trace.update(actual_provider="heuristic", fallback_used=True)
                return plan
        for point in (1,2):
            with self.subTest(point=point):
                model = Contaminated(Settings())
                model.contaminate_at = point
                r = benchmark(output=self.root / str(point), games=2, blue_provider="ollama",red_provider="ollama",
                              provider_factory=lambda *_: model)
                self.assertEqual(r["trialsStarted"], point-1)
                if point == 2:
                    self.assertEqual(r["runs"][0]["fallbackCount"],1)
                    self.assertEqual(read_rows(Path(r["runs"][0]["directory"])/"commands.jsonl"),[])

    def test_interactive_fallback_unchanged(self):
        model = FakeModel(Settings(), outputs=[ArenaProviderError("timeout")])
        trace = ArenaAiController(model).run_turn(ArenaSimulation()).to_dict()
        self.assertTrue(trace["inference"]["fallback_used"])
        self.assertEqual(trace["inference"]["actual_provider"], "heuristic")

    def test_repairs_count_and_execution_truncation(self):
        plan = ArenaTurnPlan((SnipeAction("actor", "enemy"), SnipeAction("actor", "enemy")))
        model = FakeModel(Settings(), outputs=[None, "invalid", canonical_json(plan.to_dict())])
        r = self.run_benchmark(mode="probes", blue_provider="ollama", probe="snipe_vs_basic", provider_factory=lambda *_: model)
        row = r["runs"][0]
        self.assertTrue(row["valid"])
        self.assertEqual((row["repairRequests"], row["providerRequests"]), (1,2))
        p = row["metrics"]["players"]["blue"]
        self.assertEqual((p["ap_planned"], p["ap_executed"],p["ap_unused"]), (4,2,3))
        self.assertEqual(p["truncation_indices"], [1])
        self.assertEqual(row["inference"]["ollama"]["statically_invalid_initial_outputs"],1)
        self.assertEqual(row["inference"]["ollama"]["repaired_plans"],1)

    def test_empty_plan_metrics(self):
        model = FakeModel(Settings(), outputs=[None, canonical_json(ArenaTurnPlan().to_dict())])
        r = self.run_benchmark(mode="probes", blue_provider="ollama", probe="revive_decision", provider_factory=lambda *_: model)
        p = r["runs"][0]["metrics"]["players"]["blue"]
        self.assertEqual((p["zero_action_turns"],p["ap_unused"],p["ap_planned"]), (1,5,0))

    def test_replay_rejects_tampered_commands_plans_snapshot(self):
        r = self.run_benchmark(mode="probes", probe="winning_core_line")
        path = Path(r["runs"][0]["directory"])
        for file in ("commands.jsonl","plans.jsonl","final-snapshot.json"):
            with self.subTest(file=file):
                target=path/file
                original=target.read_text()
                target.write_text("{}\n")
                self.assertFalse(verify_trial(path)["success"])
                target.write_text(original)
                self.assertTrue(verify_trial(path)["success"])

    def test_output_never_overwrites_artifacts(self):
        self.output.mkdir()
        (self.output/"keep.txt").write_text("evidence")
        with self.assertRaises(ValueError):
            self.run_benchmark()
        self.assertEqual((self.output/"keep.txt").read_text(),"evidence")

    def test_cli_rejects_invalid_options_and_counts(self):
        for args in (["--mode","wrong"],["--blue-provider","qwen"],["--games","0"],
                     ["--turns","-1"],["--probe-trials","0"],["--mode","probes","--red-provider","ollama"]):
            with self.subTest(args=args), redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                main(["--output",str(self.output),*args])
            self.assertEqual(error.exception.code,2)

    def test_cli_nonzero_preflight_failure(self):
        model=FakeModel(Settings(),outputs=[ArenaProviderError("timeout")])
        with redirect_stdout(StringIO()):
            code=main(["--output",str(self.output),"--blue-provider","ollama","--preflight-only"],
                      provider_factory=lambda s,n: model if n=="ollama" else HeuristicArenaTurnProvider())
        self.assertEqual(code,1)

    def test_cli_offline_modes(self):
        for mode in ("matches","probes","all"):
            with self.subTest(mode=mode), redirect_stdout(StringIO()):
                self.assertEqual(main(["--output",str(self.root/mode),"--mode",mode,"--games","1",
                                       "--turns","1","--probe","winning_core_line","--probe-trials","1"]),0)

    def test_concrete_versions_and_profiles_no_secrets(self):
        s=Settings()
        s=replace(s,openai=replace(s.openai,api_key="CANARY-SECRET"))
        m=manifest(["heuristic","ollama","openai"],s,dict(sourceRevision="revision",sourceDirty=True))
        self.assertEqual(m["benchmarkVersion"],"arena-benchmark-v1")
        self.assertEqual(m["probeSetVersion"],"arena-probes-v1")
        self.assertEqual(m["environmentVersion"],"arena-rules-v2")
        self.assertEqual(m["scenarioVersion"],"arena-scenario-v1")
        self.assertEqual(m["providers"]["ollama"]["modelConfigVersion"],"qwen-config-v1")
        self.assertEqual(m["providers"]["openai"]["modelConfigVersion"],"luna-config-v1")
        self.assertNotIn("latest",canonical_json(m))
        self.assertNotIn("CANARY-SECRET",canonical_json(m))
        changed=replace(s,ollama=replace(s.ollama,max_output_tokens=300))
        self.assertTrue(manifest(["ollama"],changed,{})["providers"]["ollama"]["modelConfigVersion"].startswith("arena-model-config-sha256-"))

    def test_behavioral_hashes_ignore_timing_and_tokens(self):
        hashes=[]
        for number in (1,2):
            model=FakeModel(Settings())
            with patch("aig.arena.ai.provider.perf_counter",side_effect=lambda: number*99), patch(
                    "aig.arena.benchmark_provider.perf_counter",side_effect=lambda: number*199):
                r=benchmark(output=self.root/str(number),mode="probes",blue_provider="ollama",probe="winning_core_line",
                            probe_trials=1,provider_factory=lambda *_: model)
            hashes.append(r["runs"][0]["hashes"])
        self.assertEqual(*hashes)

    def test_configuration_failure_is_saved(self):
        def fail(*_):
            raise RuntimeError("CANARY-SECRET")
        r=self.run_benchmark(blue_provider="openai",red_provider="openai",provider_factory=fail)
        self.assertEqual(r["status"],"preflight_failed")
        self.assertEqual(r["trialsStarted"],0)
        self.assertNotIn("CANARY-SECRET",canonical_json(r))

    def test_invalid_return_type_is_not_executed(self):
        class Invalid:
            name="heuristic"
            def create_turn_plan(self, _): return {}
        r=self.run_benchmark(provider_factory=lambda *_: Invalid())
        self.assertEqual(r["status"],"trial_failed")
        self.assertEqual(r["runs"][0]["metrics"]["player_turns"],0)

    def test_preflight_latency_excluded_from_trial_mean(self):
        model=FakeModel(Settings())
        with patch("aig.arena.ai.provider.perf_counter",side_effect=[0,100,0,2]), patch(
                "aig.arena.benchmark_provider.perf_counter",side_effect=[0,100,0,2]):
            r=self.run_benchmark(mode="probes",blue_provider="ollama",probe="winning_core_line",provider_factory=lambda *_: model)
        self.assertEqual(r["preflight"][0]["wall_clock_seconds"],100)
        self.assertEqual(r["inference"]["ollama"]["latency_seconds"]["mean"],2)
        self.assertEqual(r["inference"]["ollama"]["provider_requests"],1)

    def test_replay_failure_invalidates_and_aborts(self):
        with patch("aig.arena.benchmark.verify_trial",return_value=dict(success=False,error_category="replay_mismatch")):
            r=self.run_benchmark(mode="probes",probe="winning_core_line")
        self.assertEqual(r["status"],"trial_failed")
        self.assertFalse(r["runs"][0]["valid"])
        self.assertEqual(r["validTrials"],0)

    def test_provider_version_mismatch_starts_no_requests(self):
        model=FakeModel(Settings())
        model.prompt_version="wrong"
        r=self.run_benchmark(blue_provider="ollama",red_provider="ollama",provider_factory=lambda *_: model)
        self.assertEqual(r["status"],"preflight_failed")
        self.assertEqual(model.calls,0)

    def test_missing_model_provenance_rejected(self):
        class NoTrace:
            name="ollama"
            def create_turn_plan(self, observation): return ArenaTurnPlan()
        plan, diagnostic=checked_plan(NoTrace(),"ollama",build_observation(create_probe("winning_core_line")),preflight=True)
        self.assertIsNone(plan)
        self.assertEqual(diagnostic["error_category"],"provider_mismatch")


class TelemetryTests(unittest.TestCase):
    def test_distribution_missing_and_p95(self):
        self.assertIsNone(distribution([])["mean"])
        self.assertIsNone(distribution([1,2])["p95"])
        self.assertEqual(distribution(range(1,21))["p95"],19)
        self.assertEqual(distribution([1,None,3])["median"],2)

    def test_ollama_and_openai_aggregation(self):
        rows=[dict(attempts=[dict(metrics=dict(prompt_eval_count=100,eval_count=20,input_tokens=100,
                  output_tokens=20,cached_input_tokens=30,reasoning_tokens=4,total_tokens=120),wall_clock_seconds=2,
                  error_category="malformed_json"),dict(metrics={},wall_clock_seconds=4,error_category=None)],
                  repair_requests=1,fallback_used=False,success=True,wall_clock_seconds=6)]
        m=inference_metrics(rows,4096)
        self.assertEqual((m["provider_requests"],m["trial_inference_requests"],m["repair_requests"]),(2,1,1))
        self.assertEqual(m["latency_seconds"]["mean"],3)
        self.assertEqual(m["max_context_occupancy"],120/4096)
        self.assertEqual(m["tokens_and_durations"]["cached_input_tokens"]["total"],30)
        self.assertEqual(m["tokens_and_durations"]["total_duration"]["samples"],0)

    def test_secret_error_and_raw_content_not_retained(self):
        class Echo(FakeModel):
            def request(self,messages,record):
                record["request_id"]="id-CANARY-SECRET"
                return "CANARY-SECRET"
        settings=Settings()
        settings=replace(settings,openai=replace(settings.openai,api_key="CANARY-SECRET"))
        model=Echo(settings,"openai")
        _,trace=checked_plan(model,"openai",build_observation(create_probe("winning_core_line")),preflight=True)
        self.assertNotIn("CANARY-SECRET",canonical_json(trace))
        self.assertNotIn("raw_content",canonical_json(trace))


if __name__ == "__main__":
    unittest.main()
