"""Prompt-only ablation: fake transports, unchanged rules/schema/repair/settings."""

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from aig.arena.ai.contracts import ArenaTurnPlan, AttackAction, SnipeAction
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.observation import build_observation
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.prompts import PROMPTS, PROMPT_VERSION, resolve_prompt
from aig.arena.benchmark import benchmark, main, read_rows
from aig.arena.benchmark_versions import manifest, frozen_probe, artifact
from aig.arena.prompt_metrics import starting_legality
from aig.arena.snapshots import canonical_json
from aig.settings import Settings, OllamaSettings, OpenAISettings

V1 = "arena-turn-prompt-v1"
V2 = "arena-turn-prompt-v2"


class PromptV2Tests(unittest.TestCase):
    def setUp(self):
        for target in ("urllib.request.OpenerDirector.open", "httpx.Client.send",
                       "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("Live network forbidden"))
            guard.start()
            self.addCleanup(guard.stop)
        self.obs = build_observation(frozen_probe("snipe_vs_basic"))

    def provider(self, name, version, *, repair=False):
        raw = canonical_json(ArenaTurnPlan().to_dict())
        outputs = ["invalid", raw] if repair else [raw]
        if name == "ollama":
            mock = Mock(side_effect=[canonical_json(dict(done=True, message=dict(content=r))) for r in outputs])
            provider = OllamaArenaTurnProvider(OllamaSettings(), requester=mock, prompt_version=version)
        else:
            mock = Mock(side_effect=[NS(status="completed", error=None, output=[NS(type="message",
                role="assistant", status="completed", content=[NS(type="output_text", text=r)])]) for r in outputs])
            provider = OpenAIArenaTurnProvider(OpenAISettings(api_key="offline-key"),
                client=NS(responses=NS(create=mock)), prompt_version=version)
        return provider, mock

    def test_registry_defaults_aliases_unknown_and_frozen_hashes(self):
        self.assertEqual(PROMPT_VERSION, V1)
        for alias in (None, "latest", "v1", V1):
            self.assertEqual(resolve_prompt(alias), (V1, PROMPTS[V1]))
        self.assertEqual(resolve_prompt("v2"), (V2, PROMPTS[V2]))
        with self.assertRaises(ValueError):
            resolve_prompt("arena-turn-prompt-v99")
        for version, expected in ((V1, "5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7"),
                                  (V2, "5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29")):
            self.assertEqual(hashlib.sha256(PROMPTS[version].encode()).hexdigest(), expected)
        with self.assertRaises(TypeError):
            PROMPTS[V2] = "changed"

    def test_v2_contract_markers_and_neutrality(self):
        prompt = PROMPTS[V2]
        for marker in ("grouped under each unit", "unit_id must equal the id", "first action must be currently legal",
                       "START of the turn", "state changes caused by actions 1..N", "options may become legal",
                       "1 AP: Move, Attack, Heal, Finish, Shield Bash", "2 AP: Revive, Snipe, Fireball",
                       "useful legal action", "Leaving AP unused", "No explanation, reasoning, prose",
                       "Victory stops", "DOWNED friendlies", "ACTIVE enemy or enemy Core"):
            self.assertIn(marker, prompt)
        for phrase in ("attack core first", "focus cleric", "focus the cleric", "finish before revive",
                       "use fireball on two", "use siege", "prioritize lethal", "prefer core wins",
                       "conserve units", "always use all", "blue-ranger", "red-cleric"):
            self.assertNotIn(phrase, prompt.lower())

    def test_both_provider_payloads_change_only_base_prompt_including_repair(self):
        for name in ("ollama", "openai"):
            payloads = []
            for version in (V1, V2):
                provider, mock = self.provider(name, version, repair=True)
                self.assertEqual(provider.create_turn_plan(self.obs), ArenaTurnPlan())
                self.assertEqual(mock.call_count, 2)
                trace = provider.last_trace
                self.assertEqual(trace["prompt_version"], version)
                self.assertEqual(trace["schema_version"], "arena-turn-plan-schema-v1")
                self.assertEqual(trace["model_config_version"], "qwen-config-v1" if name == "ollama" else "luna-config-v1")
                self.assertEqual(trace["observation_hash"], self.obs.hash)
                calls = []
                for call in mock.call_args_list:
                    data = json.loads(call.args[1]) if name == "ollama" else dict(call.kwargs)
                    actual = data["messages"].pop(0)["content"] if name == "ollama" else data.pop("instructions")
                    self.assertEqual(actual, PROMPTS[version])
                    calls.append(data)
                payloads.append(calls)
            self.assertEqual(*payloads)  # Observation, schema, settings and repair feedback identical.

    def test_factory_default_and_override(self):
        for name in ("ollama", "openai"):
            self.assertEqual(create_arena_turn_provider(Settings(), name).prompt_version, V1)
            self.assertEqual(create_arena_turn_provider(Settings(), name, prompt_version=V2).prompt_version, V2)
            with self.assertRaises(ValueError):
                create_arena_turn_provider(Settings(), name, prompt_version="unknown")

    def test_manifest_records_recipe_and_concrete_override(self):
        for version in (V1, V2):
            value = manifest(["ollama", "openai"], Settings(),
                             dict(sourceRevision="offline", sourceDirty=True), prompt_version=version)
            self.assertEqual(value["promptVersion"], version)
            self.assertEqual(value["baseRecipePromptVersion"], V1)
            self.assertEqual(value["experimentOverrides"], {} if version == V1 else {"promptVersion": V2})
            self.assertEqual(value["benchmarkVersion"], "arena-benchmark-v1")
            self.assertEqual(value["probeSetVersion"], "arena-probes-v1")
            self.assertEqual(value["planSchemaVersion"], "arena-turn-plan-schema-v1")
            self.assertEqual(value["environmentVersion"], "arena-rules-v2")
            self.assertEqual(value["scenarioVersion"], "arena-scenario-v1")
            self.assertTrue(value["sourceDirty"])
        self.assertEqual(artifact("arena-benchmark-v1")["prompt"], V1)

    def test_cli_override_propagates_to_saved_trial_and_preflight(self):
        with TemporaryDirectory() as temp:
            for version in (V1, V2):
                made = []
                def factory(settings, name, **kwargs):
                    provider, mock = self.provider(name, kwargs.get("prompt_version", V1))
                    mock.side_effect = None
                    mock.return_value = canonical_json(dict(done=True, message=dict(content=canonical_json(ArenaTurnPlan().to_dict()))))
                    made.append(provider)
                    return provider
                output = Path(temp) / version
                with redirect_stdout(StringIO()):
                    code = main(["--mode", "probes", "--blue-provider", "ollama", "--prompt-version", version,
                        "--probe", "snipe_vs_basic", "--probe-trials", "1", "--output", str(output)], provider_factory=factory)
                self.assertEqual(code, 0)
                self.assertEqual(made[0].prompt_version, version)
                report = json.loads((output / "summary.json").read_text())
                self.assertEqual(report["experiment"]["promptVersion"], version)
                self.assertEqual(report["preflight"][0]["prompt_version"], version)
                trial = Path(report["runs"][0]["directory"])
                self.assertEqual(json.loads((trial / "manifest.json").read_text())["promptVersion"], version)
                for filename in ("plans.jsonl", "inference.jsonl"):
                    self.assertEqual(read_rows(trial / filename)[0]["prompt_version"], version)

    def test_unknown_version_fails_before_factory_or_output(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "new"
            factory = Mock()
            with self.assertRaises(ValueError):
                benchmark(output=output, prompt_version="unknown", provider_factory=factory)
            factory.assert_not_called()
            self.assertFalse(output.exists())
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(["--prompt-version", "unknown", "--output", str(output)], provider_factory=factory)
            factory.assert_not_called()

    def test_mismatched_v2_provider_stops_before_request(self):
        provider, mock = self.provider("ollama", V1)
        with TemporaryDirectory() as temp:
            report = benchmark(output=Path(temp), mode="probes", blue_provider="ollama",
                               prompt_version=V2, provider_factory=lambda *a, **k: provider)
        self.assertEqual(report["status"], "preflight_failed")
        self.assertEqual(report["trialsStarted"], 0)
        mock.assert_not_called()

    def test_starting_membership_is_actor_specific_and_not_execution_validity(self):
        plan = ArenaTurnPlan((SnipeAction("actor", "enemy"), SnipeAction("actor", "enemy")))
        self.assertEqual(starting_legality(self.obs, plan), dict(first_action_starting_legal=True,
            starting_legal_prefix_length=2, starting_action_membership=[True, True]))
        # First Snipe downs the enemy; the second is starting-legal but dynamically invalid.
        from aig.arena.ai.executor import execute_arena_turn
        result = execute_arena_turn(frozen_probe("snipe_vs_basic"), plan).to_dict()
        self.assertEqual(result["invalid_action"]["index"], 1)
        wrong = ArenaTurnPlan((SnipeAction("enemy", "enemy"),))
        self.assertFalse(starting_legality(self.obs, wrong)["first_action_starting_legal"])
        mixed = ArenaTurnPlan((AttackAction("actor", "enemy"), SnipeAction("actor", "enemy")))
        self.assertEqual(starting_legality(self.obs, mixed)["starting_legal_prefix_length"], 0)

    def test_empty_and_newly_legal_actions_have_explicit_membership(self):
        self.assertEqual(starting_legality(self.obs, ArenaTurnPlan()), dict(first_action_starting_legal=None,
            starting_legal_prefix_length=0, starting_action_membership=[]))
        from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
        obs = build_observation(frozen_probe("revive_decision"))
        plan = HeuristicArenaTurnProvider().create_turn_plan(obs)
        metrics = starting_legality(obs, plan)
        self.assertTrue(metrics["first_action_starting_legal"])
        self.assertLess(metrics["starting_legal_prefix_length"], len(plan.actions))


if __name__ == "__main__":
    unittest.main()
