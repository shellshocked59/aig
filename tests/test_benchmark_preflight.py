"""Provider purity tests. All provider traffic uses injected transports."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import httpx
import openai
from aig.ai.benchmark import benchmark, initial_state, main, run_trial, verify_replay
from aig.ai.benchmark_preflight import preflight
from aig.ai.experiments import experiment_manifest
from aig.ai.ollama import OllamaStrategyProvider
from aig.ai.openai import OpenAIStrategyProvider
from aig.ai.plan_schema import canonical_json
from aig.ai.strategy import HeuristicStrategyProvider, StrategicPlan, StrategicStateBuilder, Posture
from aig.settings import Settings
from test_openai import response


def envelope(plan=None):
    return canonical_json(dict(done=True, message=dict(content=canonical_json(
        (plan or StrategicPlan(Posture.EXPAND)).to_dict())), prompt_eval_count=17, eval_count=4))


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = Settings()
        self.settings = replace(self.settings, openai=replace(self.settings.openai, api_key="secret-canary"))
        self.state = StrategicStateBuilder().build(initial_state("v3"), "A")
        self.calls = []
        self.responses = {}
        self.providers = {}
        self.addCleanup(patch.stopall)
        patch("aig.ai.ollama.urlopen", side_effect=AssertionError("network forbidden")).start()
        patch("aig.ai.openai.OpenAI", side_effect=AssertionError("network forbidden")).start()

    def factory(self, name, settings):
        if name == "heuristic":
            return HeuristicStrategyProvider()
        def request(*args, **kwargs):
            self.calls.append(name)
            value = self.responses.get(name)
            if isinstance(value, list):
                value = value.pop(0)
            if isinstance(value, Exception):
                raise value
            return value if value is not None else (envelope() if name == "ollama" else response())
        if name == "ollama":
            provider = OllamaStrategyProvider(settings.ollama, requester=request)
        else:
            client = Mock()
            client.responses.create.side_effect = request
            provider = OpenAIStrategyProvider(settings.openai, client=client)
        self.providers[name] = provider
        return provider

    def bench(self, **kwargs):
        return benchmark(scenario_version="v3", output=self.root / "report", settings=self.settings, turns=1,
                         provider_factory=self.factory, **kwargs)

    def test_heuristic_no_preflight_and_valid_trials(self):
        report = self.bench()
        self.assertEqual(self.calls, [])
        self.assertEqual(report["preflight"], [])
        self.assertEqual(report["validModelTrials"], 2)
        self.assertEqual(report["trialsStarted"], 2)
        self.assertEqual(report["pureProviderRuns"], 2)
        self.assertTrue(all(r["replay"]["success"] for r in report["runs"]))

    def test_distinct_providers_one_preflight_each(self):
        for names in (("ollama", "ollama"), ("openai", "openai"), ("ollama", "openai")):
            with self.subTest(names=names), TemporaryDirectory() as folder:
                self.calls.clear()
                report = benchmark(scenario_version="v3", output=Path(folder), settings=self.settings, provider_a=names[0],
                                   provider_b=names[1], provider_factory=self.factory, preflight_only=True)
                self.assertEqual(self.calls, list(dict.fromkeys(names)))
                self.assertEqual(report["trialsStarted"], 0)
                self.assertEqual(report["status"], "preflight_passed")
                self.assertFalse((Path(folder) / "runs").exists())
                for check in report["preflight"]:
                    self.assertTrue(check["success"] and check["plan_valid"])
                    self.assertEqual(check["requested_provider"], check["actual_provider"])
                    self.assertEqual(check["requests"], 1)
                    self.assertFalse(check["fallback_used"])
                    self.assertTrue(check["usage"])

    def test_both_preflight_before_any_trial(self):
        original = run_trial
        def trial(*args, **kwargs):
            self.assertEqual(self.calls[:2], ["ollama", "openai"])
            return original(*args, **kwargs)
        with patch("aig.ai.benchmark.run_trial", side_effect=trial):
            report = self.bench(provider_a="ollama", provider_b="openai")
        self.assertEqual(report["requestAccounting"]["preflightRequests"], {"ollama": 1, "openai": 1})
        self.assertEqual(report["requestAccounting"]["trialProviderRequests"], {"ollama": 2, "openai": 2})
        self.assertEqual(report["validModelTrials"], 2)

    def test_failed_preflight_aborts_every_side_and_all_trials(self):
        self.responses["openai"] = RuntimeError("Authorization: Bearer secret-canary")
        with patch("aig.ai.benchmark.run_trial") as trial:
            report = self.bench(provider_a="ollama", provider_b="openai", games=3)
        trial.assert_not_called()
        self.assertEqual(self.calls, ["ollama", "openai"])
        self.assertEqual(report["status"], "preflight_failed")
        self.assertEqual(report["trialsStarted"], 0)
        self.assertEqual(report["validModelTrials"], 0)
        self.assertEqual(report["invalidModelTrials"], 0)
        self.assertEqual(report["runs"], [])
        self.assertEqual(report["comparison"], [])
        self.assertEqual(report["requestAccounting"]["trialProviderRequests"], {"ollama": 0, "openai": 0})
        self.assertEqual(report["experiments"]["openai"]["environmentVersion"], "environment-v5")
        self.assertNotIn("secret-canary", canonical_json(report))
        self.assertFalse((self.root / "report/runs").exists())

    def test_failed_first_provider_still_preflights_second(self):
        self.responses["ollama"] = TimeoutError()
        report = self.bench(provider_a="ollama", provider_b="openai")
        self.assertEqual(self.calls, ["ollama", "openai"])
        self.assertTrue(report["preflight"][1]["success"])
        self.assertEqual(report["trialsStarted"], 0)

    def test_preflight_invalid_response_never_repairs(self):
        for name in ("ollama", "openai"):
            with self.subTest(name=name):
                self.responses[name] = "{}" if name == "ollama" else response("{}")
                provider = self.factory(name, self.settings)
                check = preflight(provider, name, self.state, experiment_manifest(provider=name, settings=self.settings))
                self.assertFalse(check["success"])
                self.assertEqual(check["requests"], 1)
                self.assertEqual(check["retry_count"], 0)
                self.assertTrue(provider._repair)

    def test_preflight_fallback_and_invalid_plan_and_exception(self):
        for behavior, expected in (("fallback", "provider_mismatch"), ("invalid", "schema_validation"),
                                   ("reference", "invalid_strategic_references"), ("exception", "provider_exception")):
            with self.subTest(behavior=behavior):
                provider = Mock(spec=["name", "last_trace", "create_plan"])
                provider.name = "ollama"
                provider.last_trace = {}
                if behavior == "fallback":
                    provider.create_plan.return_value = StrategicPlan(Posture.EXPAND)
                    provider.last_trace = dict(actual_provider="heuristic", fallback_used=True)
                elif behavior == "invalid":
                    provider.create_plan.return_value = {}
                elif behavior == "reference":
                    provider.create_plan.return_value = StrategicPlan(Posture.ATTACK, "missing")
                else:
                    provider.create_plan.side_effect = RuntimeError("secret-canary")
                result = preflight(provider, "ollama", self.state,
                                   experiment_manifest(provider="ollama", settings=self.settings))
                self.assertFalse(result["success"])
                self.assertEqual(result["error_category"], expected)
                self.assertNotIn("secret-canary", canonical_json(result))

    def test_strict_failure_stops_before_fallback_commands_preserves_prefix(self):
        self.responses["ollama"] = [envelope(), envelope(), TimeoutError("secret-canary")]
        report = self.bench(provider_a="ollama", provider_b="openai", games=3)
        self.assertEqual(report["status"], "trial_failed")
        self.assertEqual(report["trialsStarted"], 1)
        self.assertEqual(report["invalidModelTrials"], 1)
        self.assertEqual(report["validModelTrials"], 0)
        self.assertEqual(report["pureProviderRuns"], 0)
        run = report["runs"][0]
        self.assertFalse(run["pureProviderRun"])
        self.assertEqual(run["metrics"]["activations_completed"], 1)
        self.assertEqual(run["fallbackCount"], 1)
        folder = self.root / "report" / run["directory"]
        rows = [json.loads(row) for row in (folder / "inference.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["error_category"], "timeout")
        acts = [json.loads(row) for row in (folder / "activations.jsonl").read_text().splitlines()]
        self.assertEqual(acts[-1]["commands_executed"], 0)
        self.assertTrue(run["replay"]["success"])
        self.assertNotIn("secret-canary", (folder / "inference.jsonl").read_text())
        self.assertEqual(report["comparison"], [])

    def test_explicit_fallback_continues_but_is_invalid(self):
        self.responses["ollama"] = [envelope(), TimeoutError(), TimeoutError()]
        report = self.bench(provider_a="ollama", allow_provider_fallback=True)
        self.assertEqual(report["status"], "fallback_contaminated")
        self.assertEqual(report["trialsStarted"], 2)
        self.assertEqual(report["invalidModelTrials"], 1)
        self.assertEqual(report["runs"][0]["metrics"]["activations_completed"], 2)
        self.assertEqual(report["requestAccounting"]["fallbackPlans"]["ollama"], 2)
        self.assertFalse(report["comparison"][0]["pureProviderRuns"])

    def test_trial_repair_accounted_separately(self):
        self.responses["ollama"] = [envelope(), "{}", envelope(), envelope()]
        report = self.bench(provider_a="ollama")
        accounting = report["requestAccounting"]
        self.assertEqual(accounting["preflightRequests"]["ollama"], 1)
        self.assertEqual(accounting["trialProviderRequests"]["ollama"], 3)
        self.assertEqual(accounting["repairRequests"]["trials"]["ollama"], 1)
        self.assertEqual(accounting["repairRequests"]["preflight"]["ollama"], 0)
        self.assertEqual(report["validModelTrials"], 2)

    def test_ollama_diagnostic_categories(self):
        cases = [(TimeoutError(), "timeout"), (ConnectionRefusedError(), "connection_failure"),
                 (URLError(socket.gaierror()), "dns_failure"),
                 ("{}", "malformed_ollama_envelope"),
                 (envelope(StrategicPlan(Posture.ATTACK, "missing")), "invalid_strategic_references")]
        cases += [(HTTPError("http://secret:password@host", code, "secret-canary", {}, None), category)
                  for code, category in ((401, "authentication_failure"), (403, "permission_denied"),
                    (404, "model_not_available"), (429, "rate_limit"), (503, "non_2xx"))]
        for value, category in cases:
            with self.subTest(category=category):
                self.responses["ollama"] = value
                result = preflight(self.factory("ollama", self.settings), "ollama", self.state,
                                   experiment_manifest(provider="ollama", settings=self.settings))
                self.assertEqual(result["error_category"], category)
                self.assertNotIn("password", canonical_json(result))
                self.assertNotIn("secret-canary", canonical_json(result))

    def test_cli_preflight_status_and_separate_provider_output(self):
        for failed in (False, True):
            with self.subTest(failed=failed), TemporaryDirectory() as folder:
                self.calls.clear()
                self.responses["ollama"] = TimeoutError() if failed else None
                # Patch provider classes, keeping the normal benchmark factory path.
                ollama = self.factory("ollama", self.settings)
                openai = self.factory("openai", self.settings)
                with patch("aig.ai.benchmark.OllamaStrategyProvider", return_value=ollama), \
                     patch("aig.ai.benchmark.OpenAIStrategyProvider", return_value=openai), \
                     patch("aig.ai.benchmark.load_settings", return_value=self.settings), patch("builtins.print") as printer:
                    code = main(["--provider-a", "ollama", "--provider-b", "openai", "--preflight-only", "--output", folder])
                self.assertEqual(code, int(failed))
                self.assertEqual(self.calls, ["ollama", "openai"])
                output = printer.call_args_list[0].args[0]
                self.assertIn("Preflight ollama:", output)
                self.assertIn("Preflight openai: PASS", output)
                self.assertIn("Trials started: 0", output)

    def test_openai_categories_survive_preflight(self):
        request = httpx.Request("POST", "https://test.invalid")
        cases = [(openai.APIConnectionError(request=request), "connection_failure"),
                 (openai.APITimeoutError(request=request), "timeout")]
        for cls, code, category in ((openai.AuthenticationError, 401, "authentication_failure"),
                (openai.PermissionDeniedError, 403, "permission_denied"),
                (openai.NotFoundError, 404, "model_not_available"),
                (openai.RateLimitError, 429, "rate_limit"),
                (openai.InternalServerError, 500, "api_error")):
            cases.append((cls("secret-canary", response=httpx.Response(code, request=request),
                              body={"secret": "secret-canary"}), category))
        cases += [(response("{"), "malformed_json_content"), (response("{}"), "schema_validation"),
                  (response(canonical_json(StrategicPlan(Posture.ATTACK, "missing").to_dict())),
                   "invalid_strategic_references")]
        for error, category in cases:
            with self.subTest(category=category):
                self.responses["openai"] = error
                result = preflight(self.factory("openai", self.settings), "openai", self.state,
                                   experiment_manifest(provider="openai", settings=self.settings))
                self.assertEqual(result["error_category"], category)
                self.assertEqual(result["requests"], 1)
                self.assertNotIn("secret-canary", canonical_json(result))

    def test_missing_credentials_produces_zero_request_diagnostic(self):
        settings = replace(self.settings, openai=replace(self.settings.openai, api_key=None))
        report = benchmark(scenario_version="v3", output=self.root / "missing", settings=settings, provider_b="openai")
        self.assertEqual(report["status"], "preflight_failed")
        self.assertEqual(report["preflight"][0]["error_category"], "configuration_failure")
        self.assertEqual(report["preflight"][0]["requests"], 0)
        self.assertEqual(report["trialsStarted"], 0)

    def test_normal_cli_failure_returns_nonzero_without_trials(self):
        self.responses["ollama"] = TimeoutError()
        provider = self.factory("ollama", self.settings)
        with patch("aig.ai.benchmark.OllamaStrategyProvider", return_value=provider), \
             patch("aig.ai.benchmark.load_settings", return_value=self.settings), patch("builtins.print"):
            self.assertEqual(main(["--provider-a", "ollama", "--output", str(self.root / "cli")]), 1)
        self.assertEqual(self.calls, ["ollama"])
        report = json.loads((self.root / "cli/summary.json").read_text())
        self.assertEqual(report["trialsStarted"], 0)

    def test_repair_failure_stops_immediately_and_is_countable(self):
        self.responses["ollama"] = [envelope(), "{}", "{}"]
        report = self.bench(provider_a="ollama", games=3)
        run = report["runs"][0]
        self.assertEqual(run["metrics"]["activations_completed"], 0)
        self.assertEqual(run["inference"]["failures"]["repair_failed"], 1)
        self.assertEqual(run["inference"]["requests"], 2)
        self.assertEqual(report["requestAccounting"]["repairRequests"]["trials"]["ollama"], 1)
        self.assertEqual(report["trialsStarted"], 1)
        self.assertEqual(run["hashes"]["initial_state"], run["hashes"]["final_state"])

    def test_trial_provider_returning_fallback_is_rejected(self):
        provider = Mock(spec=["name", "last_trace", "create_plan"])
        provider.name = "ollama"
        provider.last_trace = dict(actual_provider="heuristic", fallback_used=True)
        provider.create_plan.return_value = StrategicPlan(Posture.EXPAND)
        run = run_trial(provider, provider_name="ollama", turns=100, settings=self.settings,
                        directory=self.root / "fallback")
        self.assertFalse(run["validModelTrial"])
        self.assertFalse(run["pureProviderRun"])
        self.assertEqual(run["metrics"]["activations_completed"], 0)
        self.assertEqual(run["fallbackCount"], 1)
        provider.create_plan.assert_called_once()

    def test_preflight_wire_uses_resolved_normal_state_and_artifacts(self):
        requester = Mock(return_value=envelope())
        provider = OllamaStrategyProvider(self.settings.ollama, requester=requester,
                                          prompt_version="v1", plan_schema_version="v1")
        result = preflight(provider, "ollama", self.state,
                           experiment_manifest(provider="ollama", settings=self.settings))
        self.assertTrue(result["success"])
        payload = json.loads(requester.call_args.args[1])
        self.assertEqual(payload["messages"][0]["content"], provider.system_prompt)
        self.assertIn(canonical_json(self.state), payload["messages"][1]["content"])
        self.assertEqual(payload["model"], self.settings.ollama.model)
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])

    def test_replay_rejects_changed_final_state(self):
        path = self.root / "commands.jsonl"
        path.write_text("")
        from aig.snapshots import to_snapshot
        initial = to_snapshot(initial_state("v3"))
        final = dict(initial, turn=123)
        with self.assertRaises(AssertionError):
            verify_replay(initial, final, path)


class PreservationTests(unittest.TestCase):
    def test_saved_v1_v2_files_and_archives_unchanged_when_present(self):
        root = Path(__file__).resolve().parents[1]
        fixture = json.loads((root / "tests/fixtures/preflight-preserved-artifacts.json").read_text())
        checked = 0
        for relative, expected in fixture.items():
            path = root / relative
            if path.is_file():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)
                checked += 1
        if not checked:
            self.skipTest("local baseline archives are intentionally not committed")

    def test_baseline_documentation_keeps_v2_llms_unmeasured(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs/baselines.md").read_text(encoding="utf-8")
        self.assertIn("| V1 | measured | measured | measured |", text)
        self.assertIn("| V2 | measured | **UNMEASURED** | **UNMEASURED** |", text)
        self.assertIn("trials: **0**", text)

    def test_saved_v2_control_hashes_remain_frozen(self):
        root = Path(__file__).resolve().parents[1]
        summary = root / ".local/benchmark-environment-v2/heuristic/summary.json"
        if not summary.exists():
            self.skipTest("local V2 heuristic control is intentionally not committed")
        # V3 is a new ruleset, not runtime emulation of V2. Check the archive
        # against the pre-change digest rather than comparing new gameplay to it.
        fixture = json.loads((root / "tests/fixtures/preflight-preserved-artifacts.json").read_text())
        relative = summary.relative_to(root).as_posix()
        self.assertEqual(hashlib.sha256(summary.read_bytes()).hexdigest(), fixture[relative])
        runs = json.loads(summary.read_text())["runs"]
        self.assertTrue(all(run["hashes"] == runs[0]["hashes"] for run in runs))
