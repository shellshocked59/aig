"""Offline artifact preservation, selection, provenance and hash regressions."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from aig.ai.benchmark import benchmark, initial_state, main, run_trial, terminal_summary
from aig.ai.experiments import experiment_manifest, source_provenance
from aig.ai.model_profiles import (LUNA_CONFIGS, QWEN_CONFIGS, apply_model_profile,
                                   inference_configuration, public_ollama_configuration, resolve_model_profile)
from aig.ai.ollama import OllamaStrategyProvider, SYSTEM_PROMPT
from aig.ai.openai import OpenAIStrategyProvider, openai_plan_json_schema
from aig.ai.plan_schema import canonical_json, plan_json_schema
from aig.ai.prompts import PROMPTS, resolve_prompt
from aig.ai.strategy import HeuristicStrategyProvider, StrategicStateBuilder
from aig.application import GameSession
from aig.scenarios import human_vs_ai_demo_setup, scenario_setup
from aig.settings import AiSettings, OpenAISettings, Settings, load_settings
from aig.snapshots import SCHEMA_VERSION, to_snapshot
from aig.versions import ENVIRONMENTS, resolve_version
from test_openai import response


class ArtifactVersionTests(unittest.TestCase):
    def test_resolution_defaults_and_explicit_identifiers(self):
        self.assertEqual(resolve_version(available=ENVIRONMENTS, latest="environment-v1"), "environment-v1")
        for selected in (None, "", "latest", "v1", "environment-v1"):
            with self.subTest(selected=selected):
                self.assertEqual(resolve_version(selected, available=ENVIRONMENTS,
                                                 latest="environment-v1"), "environment-v1")

    def test_unknown_and_wrong_domain_fail(self):
        for selected in ("garbage", "v99", "scenario-v1", 1, []):
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, "unknown environment version"):
                resolve_version(selected, available=ENVIRONMENTS, latest="environment-v1")
        with self.assertRaisesRegex(ValueError, "not registered"):
            resolve_version(None, available=ENVIRONMENTS, latest="environment-v99")

    def test_moving_latest_does_not_change_explicit_history(self):
        registry = {"environment-v1": "old", "environment-v2": "new"}
        for selected in (None, "", "latest", "v2"):
            self.assertEqual(resolve_version(selected, available=registry, latest="environment-v2"), "environment-v2")
        self.assertEqual(resolve_version("v1", available=registry, latest="environment-v2"), "environment-v1")
        short_registry = {"v1": "old", "v2": "new"}
        self.assertEqual(resolve_version(None, available=short_registry, latest="v2"), "v2")
        self.assertEqual(resolve_version("v1", available=short_registry, latest="v2"), "v1")

    def test_prompt_exact_original_bytes(self):
        for selected in (None, "", "latest", "v1", "strategy-prompt-v1"):
            version, prompt = resolve_prompt(selected)
            self.assertEqual(version, "strategy-prompt-v1")
            self.assertEqual(prompt, SYSTEM_PROMPT)
            self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(),
                             "1af8d0e613b1661f59e84b6dce118d31afd45fce0bef5cae97ecd9b6994cc598")
        with self.assertRaises(TypeError):
            PROMPTS["strategy-prompt-v1"] = "changed"

    def test_schema_frozen_detached_and_independent_of_snapshot(self):
        self.assertEqual(SCHEMA_VERSION, 12)
        for selected in (None, "latest", "v1", "strategic-plan-schema-v1"):
            schema = plan_json_schema(selected)
            self.assertEqual(hashlib.sha256(canonical_json(schema).encode()).hexdigest(),
                             "9511dd479590df1e34605b408ade5f7649ddbccb5f341ef56efcdc90a6d38071")
            schema["properties"]["posture"]["enum"].append("invented")
        self.assertNotIn("invented", plan_json_schema()["properties"]["posture"]["enum"])
        adapted = openai_plan_json_schema("v1")
        self.assertNotIn("uniqueItems", adapted["properties"]["production_priority"])
        self.assertTrue(plan_json_schema("v1")["properties"]["production_priority"]["uniqueItems"])

    def test_scenario_exact_original_initial_snapshot(self):
        for selected in ("v1", "scenario-v1"):
            self.assertEqual(scenario_setup(selected), scenario_setup("v1"))
            snapshot = to_snapshot(initial_state(selected))
            # Compare scenario data to its frozen V1 projection, not V2 knowledge/schema.
            snapshot.pop("result")
            for player in snapshot["players"]: player.pop("has_ever_owned_city")
            snapshot.pop("camps")
            for unit in snapshot["units"]: unit.pop("home_camp_id")
            for player in snapshot["players"]: player.pop("kind")
            snapshot["schema_version"] = 8
            for tile in snapshot["tiles"]:
                self.assertIsNone(tile.pop("resource"))
            for player in snapshot["players"]:
                player.pop("knowledge")
            self.assertEqual(hashlib.sha256(canonical_json(snapshot).encode()).hexdigest(),
                             "00d35be14e9e6dce68f58d5dc018909c34ca7f2ada901dfd0fa1b15e56ef59b9")

    def test_profiles_exact_baseline_values_and_detached(self):
        expected = {
            "ollama": dict(model="hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M", context_size=4096,
                           temperature=0.0, seed=42, max_output_tokens=256, think=False, stream=False),
            "openai": dict(model="gpt-5.6-luna", reasoning_effort="none", max_output_tokens=512,
                           store=False, max_retries=0),
        }
        for provider, values in expected.items():
            for selected in (None, "", "latest", "v1"):
                version, profile = resolve_model_profile(provider, selected)
                self.assertEqual(version, "qwen-config-v1" if provider == "ollama" else "luna-config-v1")
                self.assertEqual(profile, values)
                self.assertEqual(profile, inference_configuration(provider, Settings()))
                profile["model"] = "mutation"
        for registry in (QWEN_CONFIGS, LUNA_CONFIGS):
            with self.assertRaises(TypeError):
                next(iter(registry.values()))["model"] = "mutation"

    def test_both_provider_traces_use_selected_frozen_artifacts(self):
        game = initial_state("v1")
        state = StrategicStateBuilder().build(game, "A")
        raw = canonical_json(HeuristicStrategyProvider().create_plan(state).to_dict())
        requester = Mock(return_value=canonical_json(dict(done=True, message=dict(content=raw))))
        client = Mock()
        client.responses.create.return_value = response(raw)
        providers = (OllamaStrategyProvider(Settings().ollama, requester=requester, prompt_version="v1",
                                            plan_schema_version="v1"),
                     OpenAIStrategyProvider(OpenAISettings(api_key="test-canary"), client=client,
                                            prompt_version="v1", plan_schema_version="v1"))
        for provider in providers:
            provider.create_plan(state)
            self.assertEqual(provider.last_trace["prompt_version"], "strategy-prompt-v1")
            self.assertEqual(provider.last_trace["schema_version"], "strategic-plan-schema-v1")
            self.assertEqual(provider.last_trace["system_content"], SYSTEM_PROMPT)
        self.assertEqual(client.responses.create.call_args.kwargs["instructions"],
                         json.loads(requester.call_args.args[1])["messages"][0]["content"])

    def test_invalid_provider_versions_fail_before_inference(self):
        for argument in ("prompt_version", "plan_schema_version"):
            client = Mock()
            with self.assertRaises(ValueError):
                OpenAIStrategyProvider(OpenAISettings(api_key="test-canary"), client=client, **{argument: "v99"})
            client.responses.create.assert_not_called()
            requester = Mock()
            with self.assertRaises(ValueError):
                OllamaStrategyProvider(Settings().ollama, requester=requester, **{argument: "v99"})
            requester.assert_not_called()

    def test_v2_reaches_both_transports_without_changing_schema_or_default(self):
        version, prompt = resolve_prompt("v2")
        self.assertEqual(version, "strategy-prompt-v2")
        self.assertEqual(resolve_prompt()[0], "strategy-prompt-v1")
        state = StrategicStateBuilder().build(initial_state("v3"), "A")
        raw = canonical_json(HeuristicStrategyProvider().create_plan(state).to_dict())
        requester = Mock(return_value=canonical_json(dict(done=True, message=dict(content=raw))))
        client = Mock()
        client.responses.create.return_value = response(raw)
        providers = (
            OllamaStrategyProvider(Settings().ollama, requester=requester, prompt_version="v2"),
            OpenAIStrategyProvider(OpenAISettings(api_key="test-canary"), client=client,
                                   prompt_version="v2"),
        )
        for provider in providers:
            provider.create_plan(state)
            self.assertEqual(provider.last_trace["prompt_version"], version)
            self.assertEqual(provider.last_trace["schema_version"], "strategic-plan-schema-v1")
        self.assertEqual(client.responses.create.call_args.kwargs["instructions"], prompt)
        self.assertEqual(json.loads(requester.call_args.args[1])["messages"][0]["content"], prompt)


class ManifestTests(unittest.TestCase):
    def manifest(self, provider="heuristic", settings=None, **versions):
        return experiment_manifest(provider=provider, settings=settings or Settings(),
                                   source=dict(sourceRevision="abc123", sourceDirty=True), **versions)

    def test_manifest_concrete_allowlisted_and_canonical(self):
        settings = replace(Settings(), openai=OpenAISettings(api_key="manifest-secret-canary"))
        for provider in ("heuristic", "ollama", "openai"):
            manifest = self.manifest(provider, settings, environment_version="latest", scenario_version="latest",
                                     prompt_version="latest", plan_schema_version="latest")
            expected = dict(environmentVersion="environment-v5", scenarioVersion="scenario-v4",
                            strategyPromptVersion="strategy-prompt-v1", strategicPlanSchemaVersion="strategic-plan-schema-v1",
                            benchmarkVersion="benchmark-v1", sourceRevision="abc123", sourceDirty=True, provider=provider)
            for field, value in expected.items():
                self.assertEqual(manifest[field], value)
            raw = canonical_json(manifest)
            self.assertEqual(raw, canonical_json(dict(reversed(list(manifest.items())))))
            for private in ("manifest-secret-canary", "api_key", "Authorization", "latest", "base_url", "timestamp"):
                self.assertNotIn(private, raw)
            self.assertEqual(manifest["modelConfigVersion"],
                             {"heuristic": None, "ollama": "qwen-config-v1", "openai": "luna-config-v1"}[provider])
            self.assertEqual(manifest["model"], None if provider == "heuristic" else
                             getattr(settings, provider).model)

    def test_runtime_overrides_are_custom_and_explicit_profile_restores_baseline(self):
        for provider in ("ollama", "openai"):
            settings = Settings()
            modified = replace(getattr(settings, provider), model="custom-model", timeout_seconds=39)
            if provider == "openai":
                modified = replace(modified, api_key="keep-credential-canary")
            else:
                modified = replace(modified, base_url="http://runtime-host:11434", keep_alive="2m")
            settings = replace(settings, **{provider: modified})
            self.assertIsNone(self.manifest(provider, settings)["modelConfigVersion"])
            self.assertEqual(self.manifest(provider, settings)["modelConfiguration"]["model"], "custom-model")
            pinned = apply_model_profile(settings, provider, "v1")
            self.assertIsNotNone(self.manifest(provider, pinned)["modelConfigVersion"])
            self.assertEqual(getattr(pinned, provider).timeout_seconds, 39)
            if provider == "openai":
                self.assertEqual(pinned.openai.api_key, "keep-credential-canary")
            else:
                self.assertEqual(pinned.ollama.base_url, "http://runtime-host:11434")
                self.assertEqual(pinned.ollama.keep_alive, "2m")

    def test_every_tunable_inference_override_is_detected(self):
        overrides = dict(ollama=dict(model="custom", context_size=8192, temperature=0.1, seed=7,
                                     max_output_tokens=300, think=True, stream=True),
                         openai=dict(model="custom", reasoning_effort="low", max_output_tokens=1024))
        for provider, values in overrides.items():
            for key, value in values.items():
                with self.subTest(provider=provider, field=key):
                    settings = Settings()
                    settings = replace(settings, **{provider: replace(getattr(settings, provider), **{key: value})})
                    self.assertIsNone(self.manifest(provider, settings)["modelConfigVersion"])

    def test_endpoint_credentials_are_excluded_from_runtime_metadata(self):
        settings = replace(Settings().ollama,
                           base_url="http://user:password-canary@[::1]:11434/prefix?token=query-canary#fragment")
        public = public_ollama_configuration(settings)
        self.assertEqual(public["base_url"], "http://[::1]:11434/prefix")
        self.assertNotIn("canary", canonical_json(public))
        self.assertEqual(settings.base_url, "http://user:password-canary@[::1]:11434/prefix?token=query-canary#fragment")

    def test_domains_can_evolve_independently(self):
        with patch("aig.ai.experiments.ENVIRONMENTS", {"environment-v1": "old", "environment-v2": "new"}), \
                patch("aig.ai.experiments.LATEST_ENVIRONMENT_VERSION", "environment-v2"):
            manifest = self.manifest(scenario_version="v1", prompt_version="v1")
            self.assertEqual(manifest["environmentVersion"], "environment-v2")
            self.assertEqual(manifest["scenarioVersion"], "scenario-v1")
            self.assertEqual(manifest["strategyPromptVersion"], "strategy-prompt-v1")
            self.assertEqual(self.manifest(environment_version="v1")["environmentVersion"], "environment-v1")


class GitProvenanceTests(unittest.TestCase):
    def test_unavailable_git_returns_unknown(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("git", 5),
                      subprocess.CalledProcessError(128, "git")):
            with patch("aig.ai.experiments.subprocess.run", side_effect=error):
                self.assertEqual(source_provenance(), dict(sourceRevision=None, sourceDirty=None))

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_real_checkout_clean_dirty_and_non_checkout(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.run(["git", "-C", folder, *args], check=True,
                                      capture_output=True, text=True).stdout.strip()
            self.assertEqual(source_provenance(root), dict(sourceRevision=None, sourceDirty=None))
            git("init")
            (root / "tracked.txt").write_text("original")
            git("add", "tracked.txt")
            git("-c", "user.name=Offline Test", "-c", "user.email=offline@example.test",
                "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
            sha = git("rev-parse", "HEAD")
            self.assertEqual(source_provenance(root), dict(sourceRevision=sha, sourceDirty=False))
            (root / "tracked.txt").write_text("modified")
            self.assertEqual(source_provenance(root), dict(sourceRevision=sha, sourceDirty=True))
            (root / "tracked.txt").write_text("original")
            (root / "untracked.txt").write_text("new")
            self.assertTrue(source_provenance(root)["sourceDirty"])
            nested = root / "installed-package"
            nested.mkdir()
            self.assertIsNone(source_provenance(nested)["sourceRevision"])


class BenchmarkVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_environment_v2_100_turn_hashes_repeat(self):
        report = benchmark(output=self.root / "hashes", turns=100, settings=Settings())
        self.assertEqual(report["runs"][0]["hashes"], report["runs"][1]["hashes"])
        self.assertEqual(json.loads((self.root / "hashes/summary.json").read_text()), report)


    def test_cli_default_latest_empty_and_explicit(self):
        for index, selection in enumerate((None, "", "latest", "v1")):
            output = self.root / str(index)
            args = ["--turns", "1", "--output", str(output)]
            if selection is not None:
                for flag in ("environment-version", "scenario-version", "prompt-version", "plan-schema-version"):
                    args += [f"--{flag}", "v5" if flag == "environment-version" and selection == "v1" else selection]
            with patch("aig.ai.benchmark.load_settings", return_value=Settings()), patch("builtins.print"):
                main(args)
            report = json.loads((output / "summary.json").read_text())
            self.assertNotIn('"latest"', canonical_json(report))
            self.assertEqual(report["runs"][0]["experiment"]["strategyPromptVersion"], "strategy-prompt-v1")

    def test_cli_unknown_versions_fail_before_creating_output_or_provider(self):
        for flag in ("environment-version", "scenario-version", "prompt-version", "plan-schema-version",
                     "qwen-config-version", "luna-config-version"):
            with patch("aig.ai.benchmark.load_settings", return_value=Settings()), \
                    patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                main([f"--{flag}", "v99", "--output", str(self.root / "bad")])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse((self.root / "bad").exists())

    def test_explicit_profile_benchmark_pins_factory_settings(self):
        settings = replace(Settings(), openai=OpenAISettings(model="custom", api_key="keep-secret-canary"))
        seen = []
        def factory(name, effective):
            seen.append(effective)
            provider = HeuristicStrategyProvider()
            provider.name = name  # Offline named fake; no real provider requests.
            return provider
        for selection in ("", "latest", "v1"):
            report = benchmark(output=self.root / (selection or "empty"), turns=1, settings=settings,
                               provider_b="openai", luna_config_version=selection, provider_factory=factory)
            self.assertEqual(seen[-1].openai.model, "gpt-5.6-luna")
            self.assertEqual(report["runs"][1]["experiment"]["modelConfigVersion"], "luna-config-v1")
            self.assertNotIn("keep-secret-canary", canonical_json(report))

    def test_injected_provider_configuration_mismatch_is_rejected(self):
        requester = Mock()
        def factory(name, settings):
            return OllamaStrategyProvider(replace(settings.ollama, model="custom"), requester=requester)
        with self.assertRaisesRegex(ValueError, "inference settings do not match"):
            benchmark(output=self.root / "mismatch", provider_a="ollama", turns=1,
                      settings=Settings(), provider_factory=factory)
        requester.assert_not_called()

    def test_direct_trial_records_actual_injected_provider_configuration(self):
        provider = OllamaStrategyProvider(replace(Settings().ollama, model="custom"),
                                           requester=Mock(side_effect=TimeoutError()))
        report = run_trial(provider, provider_name="ollama", turns=1, settings=Settings(),
                           directory=self.root / "direct")
        self.assertIsNone(report["experiment"]["modelConfigVersion"])
        self.assertEqual(report["experiment"]["model"], "custom")

    def test_benchmark_without_git_still_completes(self):
        with patch("aig.ai.experiments.subprocess.run", side_effect=FileNotFoundError()):
            report = benchmark(output=self.root / "nogit", turns=1, settings=Settings())
        self.assertIsNone(report["runs"][0]["experiment"]["sourceRevision"])
        self.assertIn("Revision: unknown (unknown)", terminal_summary(report))

    def test_settings_precedence_empty_local_and_provider_resolution(self):
        local = self.root / ".env"
        for selection in ("", "latest", "v1", "strategy-prompt-v1"):
            local.write_text(f"AIG_STRATEGY_PROMPT_VERSION={selection}\n")
            settings = load_settings(local_file=local, environ={"AIG_STRATEGY_PROMPT_VERSION": ""})
            self.assertEqual(resolve_prompt(settings.ai.strategy_prompt_version)[0], "strategy-prompt-v1")
        settings = load_settings(local_file=local, environ={"AIG_STRATEGY_PROMPT_VERSION": "v99"})
        with self.assertRaisesRegex(ValueError, "unknown strategy-prompt"):
            GameSession(settings.ai).demo(versus_ai=True, provider="ollama")
        with patch("aig.application.OllamaStrategyProvider") as constructor:
            GameSession(AiSettings(strategy_prompt_version="v1")).demo(versus_ai=True, provider="ollama")
        self.assertEqual(constructor.call_args.kwargs["prompt_version"], "v1")
