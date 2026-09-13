"""Phase 4 offline providers: fake transports/SDK, no inference network access."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
import traceback
from urllib.error import HTTPError

from fastapi.testclient import TestClient
from aig.api import create_app
from aig.settings import Settings, AiSettings, OllamaSettings, OpenAISettings, load_settings
from aig.arena import ArenaSimulation, ArenaEndTurn, replay, to_snapshot
from aig.arena.ai import ArenaTurnPlan, ArenaAiController, build_observation, HeuristicArenaTurnProvider
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION, SnipeAction, AttackAction, turn_plan_schema
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.prompts import PROMPTS, PROMPT_VERSION, SYSTEM_PROMPT, resolve_prompt
from aig.arena.ai.probes import PROBE_NAMES, create_probe
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan, openai_turn_plan_schema
from aig.arena.snapshots import canonical_json, command_to_dict
from aig.arena.simulate import simulate
from aig.arena.smoke import main as smoke

KEY = "sk-arena-SECRET-canary-4927"


def sdk_response(raw):
    return NS(status="completed", error=None, id="resp_offline", _request_id="req_offline",
              output=[NS(type="reasoning", summary=[KEY]), NS(type="message", role="assistant", status="completed",
                         content=[NS(type="output_text", text=raw)])],
              usage=NS(input_tokens=100, output_tokens=40, total_tokens=140,
                       input_tokens_details=NS(cached_tokens=20), output_tokens_details=NS(reasoning_tokens=0)))


def ollama_response(raw):
    return canonical_json(dict(done=True, message=dict(content=raw, thinking=KEY),
                               prompt_eval_count=100, eval_count=40, prompt_eval_duration=10,
                               eval_duration=20, total_duration=30))


class OfflineTests(unittest.TestCase):
    def setUp(self):
        for target in ("httpx.Client.send", "urllib.request.OpenerDirector.open"):
            guard = patch(target, side_effect=AssertionError("Live network forbidden"))
            guard.start()
            self.addCleanup(guard.stop)
        self.state = create_probe("snipe_vs_basic")
        self.obs = build_observation(self.state)
        self.plan = ArenaTurnPlan((SnipeAction("actor", "enemy"),))
        self.raw = canonical_json(self.plan.to_dict())

    def provider(self, name, raws=None, repair=True):
        raws = [self.raw] if raws is None else raws
        if name == "ollama":
            mock = Mock(side_effect=[ollama_response(r) for r in raws])
            result = OllamaArenaTurnProvider(OllamaSettings(), requester=mock, repair=repair, secrets=(KEY,))
        else:
            mock = Mock(side_effect=[sdk_response(r) for r in raws])
            result = OpenAIArenaTurnProvider(OpenAISettings(api_key=KEY), client=NS(responses=NS(create=mock)), repair=repair)
        return result, mock

    def test_frozen_prompt_registry_and_digest(self):
        self.assertEqual(resolve_prompt("v1"), (PROMPT_VERSION, SYSTEM_PROMPT))
        self.assertEqual(hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                         "5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7")
        with self.assertRaises(TypeError):
            PROMPTS[PROMPT_VERSION] = "changed"
        for phrase in ("always finish", "always revive", "focus the Cleric", "explain your strategy", "PREVIOUS PLAN"):
            self.assertNotIn(phrase, SYSTEM_PROMPT)
        for phrase in ("5 shared", "execute in order", "2 AP", "perfect-information", "DOWNED"):
            self.assertIn(phrase, SYSTEM_PROMPT)

    def test_wire_schema_keeps_disjoint_logical_v1(self):
        schema = openai_turn_plan_schema()
        self.assertEqual(schema["properties"]["schema_version"]["enum"], [PLAN_SCHEMA_VERSION])
        self.assertEqual(len(schema["properties"]["actions"]["items"]["anyOf"]), 8)
        self.assertNotIn("oneOf", canonical_json(schema))
        schema["properties"].clear()
        self.assertIn("actions", openai_turn_plan_schema()["properties"])
        self.assertIn("oneOf", turn_plan_schema()["properties"]["actions"]["items"])

    def test_ollama_request_settings_schema_and_canonical_serialization(self):
        provider, mock = self.provider("ollama")
        provider.settings = OllamaSettings(base_url="http://configured:11434/", model="custom", context_size=4096,
                                           temperature=0, seed=42, max_output_tokens=256, keep_alive="3m", timeout_seconds=3)
        self.assertEqual(provider.create_turn_plan(self.obs), self.plan)
        url, body, timeout = mock.call_args.args
        self.assertEqual((url, timeout), ("http://configured:11434/api/chat", 3))
        data = json.loads(body)
        self.assertEqual(body, canonical_json(data).encode())
        self.assertEqual(data["model"], "custom")
        self.assertFalse(data["think"])
        self.assertFalse(data["stream"])
        self.assertEqual(data["keep_alive"], "3m")
        self.assertEqual(data["options"], dict(num_ctx=4096, temperature=0, seed=42, num_predict=256))
        self.assertEqual(data["format"], turn_plan_schema())
        self.assertEqual(data["messages"][1]["content"], "ArenaObservation:\n" + self.obs.canonical)

    def test_openai_explicit_client_constructor(self):
        with patch("aig.arena.ai.openai.OpenAI") as constructor:
            OpenAIArenaTurnProvider(OpenAISettings(api_key=KEY, timeout_seconds=3))
        constructor.assert_called_once_with(api_key=KEY, timeout=3, max_retries=0)

    def test_openai_request_shape_no_persistence(self):
        provider, mock = self.provider("openai")
        self.assertEqual(provider.create_turn_plan(self.obs), self.plan)
        data = mock.call_args.kwargs
        self.assertEqual(set(data), {"model", "instructions", "input", "reasoning", "max_output_tokens", "store", "text"})
        self.assertEqual(data["model"], "gpt-5.6-luna")
        self.assertEqual(data["reasoning"], {"effort": "none"})
        self.assertEqual(data["max_output_tokens"], 512)
        self.assertFalse(data["store"])
        self.assertEqual(data["text"]["format"], dict(type="json_schema", name="arena_turn_plan", strict=True,
                                                     schema=openai_turn_plan_schema()))
        self.assertEqual(data["instructions"], SYSTEM_PROMPT)
        self.assertIn(self.obs.canonical, data["input"][0]["content"])

    def test_trace_metrics_versions_detachment_and_secret_exclusion(self):
        for name, profile in (("ollama", "qwen-config-v1"), ("openai", "luna-config-v1")):
            provider, mock = self.provider(name)
            provider.create_turn_plan(self.obs)
            trace = provider.last_trace
            self.assertEqual(trace["schema_version"], PLAN_SCHEMA_VERSION)
            self.assertEqual(trace["prompt_version"], PROMPT_VERSION)
            self.assertEqual(trace["model_config_version"], profile)
            self.assertGreaterEqual(trace["wall_clock_seconds"], 0)
            self.assertEqual(trace["observation_hash"], self.obs.hash)
            self.assertEqual(trace["resulting_plan"], self.plan.to_dict())
            self.assertTrue(trace["attempts"][0]["metrics"])
            if name == "openai":
                self.assertEqual(trace["attempts"][0]["request_id"], "req_offline")
                self.assertEqual(trace["attempts"][0]["metrics"]["cached_input_tokens"], 20)
            self.assertNotIn(KEY, repr(provider) + repr(provider.settings) + json.dumps(trace))
            trace["attempts"].clear()
            self.assertEqual(len(provider.last_trace["attempts"]), 1)

    def test_runtime_override_does_not_claim_frozen_profile(self):
        provider, _ = self.provider("ollama")
        provider.settings = replace(provider.settings, seed=1)
        provider.create_turn_plan(self.obs)
        self.assertIsNone(provider.last_trace["model_config_version"])

    def test_repair_once_for_static_invalidity_both_providers(self):
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, ['{"secret":"' + KEY + '"}', self.raw])
            self.assertEqual(provider.create_turn_plan(self.obs), self.plan)
            self.assertEqual(mock.call_count, 2)
            trace = provider.last_trace
            self.assertEqual(trace["retry_count"], 1)
            self.assertNotIn(KEY, json.dumps(trace))
            data = json.loads(mock.call_args.args[1]) if name == "ollama" else mock.call_args.kwargs
            messages = data.get("messages", data.get("input"))
            self.assertIn(self.obs.canonical, messages[-2]["content"])
            self.assertIn("schema_validation", messages[-1]["content"])
            self.assertNotIn(KEY, json.dumps(messages))
            self.assertNotIn("Traceback", json.dumps(messages))

    def test_second_invalid_fails_and_never_loops(self):
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, ["bad", "bad", self.raw])
            with self.assertRaises(ArenaProviderError) as raised:
                provider.create_turn_plan(self.obs)
            self.assertEqual(raised.exception.category, "repair_failed")
            self.assertEqual(mock.call_count, 2)

    def test_one_request_mode_disables_repair(self):
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, ["bad", self.raw], repair=False)
            with self.assertRaises(ArenaProviderError):
                provider.create_turn_plan(self.obs)
            self.assertEqual(mock.call_count, 1)

    def test_execution_invalidity_never_repairs_or_falls_back(self):
        plan = ArenaTurnPlan((SnipeAction("actor", "enemy"), SnipeAction("actor", "enemy"), AttackAction("actor", "enemy2")))
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, [canonical_json(plan.to_dict())])
            sim = ArenaSimulation(create_probe("snipe_vs_basic"))
            row = ArenaAiController(provider).run_turn(sim).to_dict()
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(row["invalid_action"]["index"], 1)
            self.assertEqual(row["ap_spent"], 2)
            self.assertFalse(row["inference"]["fallback_used"])
            self.assertEqual(sim.state.units["enemy"].hp, 0)
            self.assertEqual(sim.state.active_player_id, "red")
            self.assertEqual(replay(sim.trace()).trace(), sim.trace())

    def test_all_tactical_probe_plans_consumed_by_both_providers(self):
        for probe in PROBE_NAMES:
            obs = build_observation(create_probe(probe))
            plan = HeuristicArenaTurnProvider().create_turn_plan(obs)
            for name in ("ollama", "openai"):
                provider, mock = self.provider(name, [canonical_json(plan.to_dict())])
                self.assertEqual(provider.create_turn_plan(obs), plan)
                self.assertEqual(mock.call_count, 1)

    def test_no_previous_plan_and_terminal_prevents_request(self):
        provider, mock = self.provider("ollama", [canonical_json(ArenaTurnPlan().to_dict())] * 2)
        sim = ArenaSimulation()
        controller = ArenaAiController(provider)
        controller.run_turn(sim)
        controller.run_turn(sim)
        for call in mock.call_args_list:
            self.assertEqual(len(json.loads(call.args[1])["messages"]), 2)
        sim = ArenaSimulation(create_probe("winning_core_line"))
        ArenaAiController().run_turn(sim)
        with self.assertRaises(ValueError):
            controller.run_turn(sim)
        self.assertEqual(mock.call_count, 2)

    def test_transport_fallback_categories_sanitized_and_no_repair(self):
        cases = [(ConnectionError(KEY), "connection_failure"), (TimeoutError(KEY), "timeout"),
                 (HTTPError("http://offline", 401, KEY, {}, None), "authentication_failure"),
                 (HTTPError("http://offline", 403, KEY, {}, None), "permission_denied"),
                 (HTTPError("http://offline", 429, KEY, {}, None), "rate_limit")]
        for error, category in cases:
            provider, mock = self.provider("ollama")
            mock.side_effect = error
            sim = ArenaSimulation(self.state.clone() if hasattr(self.state, "clone") else deepcopy(self.state))
            row = ArenaAiController(provider).run_turn(sim).to_dict()
            self.assertEqual(row["inference"]["error_category"], category)
            self.assertEqual(row["inference"]["actual_provider"], "heuristic")
            self.assertEqual(row["inference"]["requested_provider"], "ollama")
            self.assertTrue(row["inference"]["fallback_used"])
            self.assertGreater(row["actions_executed"], 0)
            self.assertEqual(mock.call_count, 1)
            self.assertNotIn(KEY, json.dumps(row) + json.dumps(to_snapshot(sim.state)))

    def test_openai_sdk_error_suppresses_secret_exception_chain(self):
        import openai
        import httpx
        for cls, code, category in ((openai.AuthenticationError, 401, "authentication_failure"),
                                    (openai.PermissionDeniedError, 403, "permission_denied"),
                                    (openai.RateLimitError, 429, "rate_limit")):
            provider, mock = self.provider("openai")
            mock.side_effect = cls(KEY, response=httpx.Response(code, request=httpx.Request("POST", "https://offline")), body={"key": KEY})
            try:
                provider.create_turn_plan(self.obs)
            except ArenaProviderError as error:
                self.assertEqual(error.category, category)
                self.assertNotIn(KEY, traceback.format_exc())
            else:
                self.fail("SDK failure accepted")
            self.assertEqual(mock.call_count, 1)

    def test_openai_sdk_timeout_and_connection_fallback(self):
        import openai
        import httpx
        for cls, category in ((openai.APITimeoutError, "timeout"), (openai.APIConnectionError, "connection_failure")):
            provider, mock = self.provider("openai")
            mock.side_effect = cls(request=httpx.Request("POST", "https://offline"))
            row = ArenaAiController(provider).run_turn(ArenaSimulation(create_probe("snipe_vs_basic"))).to_dict()
            self.assertEqual(row["inference"]["error_category"], category)
            self.assertTrue(row["inference"]["fallback_used"])
            self.assertEqual(mock.call_count, 1)

    def test_real_sdk_response_model_supported(self):
        from openai.types.responses import Response
        response = Response.model_validate(dict(
            id="resp_offline", created_at=0, model="gpt-5.6-luna", object="response",
            status="completed", error=None, incomplete_details=None, instructions=None,
            metadata={}, parallel_tool_calls=False, temperature=None, tool_choice="auto", tools=[], top_p=None,
            output=[dict(type="message", id="msg_offline", role="assistant", status="completed",
                         content=[dict(type="output_text", text=self.raw, annotations=[])])]))
        provider, mock = self.provider("openai")
        mock.side_effect = None
        mock.return_value = response
        self.assertEqual(provider.create_turn_plan(self.obs), self.plan)

    def test_headless_default_ignores_configured_model_selector(self):
        report = simulate(max_turns=1, settings=Settings(ai=AiSettings(arena_turn_provider="openai")))
        self.assertTrue(report["replay_exact"])
        self.assertTrue(all("inference" not in row for row in report["ai_traces"]))

    def test_model_schema_application_rejects_extra_reasoning(self):
        data = self.plan.to_dict()
        data["reasoning"] = KEY
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, [canonical_json(data), self.raw])
            self.assertEqual(provider.create_turn_plan(self.obs), self.plan)
            self.assertEqual(mock.call_count, 2)

    def test_trace_canary_request_ids_and_model_configuration(self):
        provider, mock = self.provider("openai")
        response = sdk_response(self.raw)
        response.id = response._request_id = KEY
        mock.side_effect = None
        mock.return_value = response
        provider.settings = replace(provider.settings, model=KEY)
        provider.create_turn_plan(self.obs)
        self.assertNotIn(KEY, json.dumps(provider.last_trace))

    def test_malformed_envelopes_fail_without_repair(self):
        for envelope in ("bad", "{}", '{"done":false,"message":{"content":"{}"}}'):
            provider, mock = self.provider("ollama")
            mock.side_effect = None
            mock.return_value = envelope
            with self.assertRaisesRegex(ArenaProviderError, "malformed_envelope"):
                provider.create_turn_plan(self.obs)
            self.assertEqual(mock.call_count, 1)

    def test_openai_bad_envelopes_and_refusal_never_repair(self):
        for mutate in (lambda r: setattr(r, "status", "incomplete"), lambda r: setattr(r, "output", None),
                       lambda r: setattr(r.output[1], "role", "user"),
                       lambda r: setattr(r.output[1].content[0], "type", "refusal")):
            provider, mock = self.provider("openai")
            response = sdk_response(self.raw)
            mutate(response)
            mock.side_effect = None
            mock.return_value = response
            with self.assertRaises(ArenaProviderError):
                provider.create_turn_plan(self.obs)
            self.assertEqual(mock.call_count, 1)

    def test_large_secret_raw_trace_is_redacted_and_bounded(self):
        provider, _ = self.provider("openai", [KEY * 10000], repair=False)
        with self.assertRaises(ArenaProviderError):
            provider.create_turn_plan(self.obs)
        raw = provider.last_trace["attempts"][0]["raw_content"]
        self.assertLessEqual(len(raw), 32768)
        self.assertNotIn(KEY, raw)

    def test_static_invalid_variants_rejected_by_application(self):
        cases = ["null", "[]", "NaN", '{"actions":[],"actions":[]}',
                 canonical_json(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="unknown")])),
                 canonical_json(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="attack", unit_id="actor")])),
                 canonical_json(ArenaTurnPlan((AttackAction("unknown", "enemy"),)).to_dict()),
                 canonical_json(ArenaTurnPlan((AttackAction("actor", "unknown"),)).to_dict()),
                 canonical_json(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="move", unit_id="actor", destination=dict(x=9,y=0))])),
                 canonical_json(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="move", unit_id="actor", destination=dict(x=True,y=0))])),
                 canonical_json(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="snipe", unit_id="actor", target_id="enemy")] * 3)),
                 canonical_json(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="heal", unit_id="actor", target_id="actor")])),
                 canonical_json(ArenaTurnPlan((SnipeAction("actor", "red-core"),)).to_dict())]
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ArenaProviderError):
                parse_turn_plan(raw, self.obs)

    def test_remaining_ap_checked_before_execution(self):
        self.state.action_points_remaining = 1
        with self.assertRaisesRegex(ArenaProviderError, "ap_budget"):
            parse_turn_plan(self.raw, build_observation(self.state))

    def test_static_invalid_output_falls_back_after_two_requests(self):
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, ["bad", "bad"])
            row = ArenaAiController(provider).run_turn(ArenaSimulation(create_probe("snipe_vs_basic"))).to_dict()
            self.assertTrue(row["inference"]["fallback_used"])
            self.assertEqual(row["inference"]["error_category"], "repair_failed")
            self.assertEqual(mock.call_count, 2)

    def test_missing_key_normal_game_falls_back_without_sdk_construction(self):
        with patch("aig.arena.ai.openai.OpenAI") as constructor:
            provider = OpenAIArenaTurnProvider(OpenAISettings())
            row = ArenaAiController(provider).run_turn(ArenaSimulation()).to_dict()
        constructor.assert_not_called()
        self.assertEqual(row["inference"]["error_category"], "authentication_failure")

    def test_default_selector_independent_and_connection_does_not_select(self):
        settings = load_settings(local_file=None, environ={"AIG_STRATEGY_PROVIDER": "ollama", "OPENAI_API_KEY": KEY,
                                                          "AIG_OLLAMA_BASE_URL": "http://offline"})
        self.assertEqual(settings.ai.arena_turn_provider, "heuristic")
        self.assertIsInstance(create_arena_turn_provider(settings), HeuristicArenaTurnProvider)

    def test_local_selector_process_precedence_and_validation(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("AIG_STRATEGY_PROVIDER=ollama\nAIG_ARENA_TURN_PROVIDER=openai\n")
            self.assertEqual(load_settings(local_file=path, environ={}).ai.arena_turn_provider, "openai")
            settings = load_settings(local_file=path, environ={"AIG_ARENA_TURN_PROVIDER": "ollama"})
            self.assertEqual(settings.ai.arena_turn_provider, "ollama")
            self.assertEqual(settings.ai.strategy_provider, "ollama")
            with self.assertRaisesRegex(ValueError, "AIG_ARENA_TURN_PROVIDER"):
                load_settings(local_file=path, environ={"AIG_ARENA_TURN_PROVIDER": "llm"})

    def test_headless_fake_providers_and_exact_replay(self):
        providers = {}
        def factory(settings, name):
            provider, mock = self.provider(name, [canonical_json(ArenaTurnPlan().to_dict())])
            providers[name] = mock
            return provider
        report = simulate(max_turns=1, red_provider="ollama", blue_provider="openai", provider_factory=factory)
        self.assertTrue(report["replay_exact"])
        self.assertEqual(report["player_turns"], 2)
        self.assertTrue(all(p.call_count == 1 for p in providers.values()))

    def test_heuristic_full_match_all_five_phase3_hashes(self):
        report = simulate()
        self.assertEqual(report["hashes"], dict(
            plans="5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c",
            commands="88328e37527ddb68abf63b091613f7c1282a4581ebe72da394511838b3e6f0ae",
            final_state="01720d448acca31206574e16fa3182ffc5c2a40e033e89d5043d56fb21939f2a",
            command_trace="6b7c60fbb3d8dcd8451e0692bd764135a5c1b31c5abd35dbcc1101042b6f4f5d",
            ai_trace="9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1"))

    def test_browser_routes_model_selection_provenance_and_snapshot_exclusion(self):
        settings = Settings(ai=AiSettings(arena_turn_provider="openai"), openai=OpenAISettings(api_key=KEY))
        with patch("aig.api.load_settings", return_value=settings):
            app = create_app()
        with TestClient(app) as client:
            for name in ("ollama", "openai", "configured"):
                resolved = "openai" if name == "configured" else name
                provider, mock = self.provider(resolved, [canonical_json(ArenaTurnPlan().to_dict())])
                with patch("aig.arena.application.create_arena_turn_provider", return_value=provider) as factory:
                    response = client.post("/api/arena/demo-ai/" + name)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["controllers"]["red"], resolved + "_ai")
                factory.assert_called_once_with(settings, resolved)
                row = client.post("/api/arena/commands", json=command_to_dict(ArenaEndTurn("blue"))).json()
                self.assertEqual(row["active_player_id"], "blue")
                self.assertEqual(mock.call_count, 1)
                self.assertNotIn("attempts", row["ai_turns"][0]["inference"])
                self.assertNotIn(KEY, json.dumps(row))
                snapshot = client.get("/api/arena/trace").json()["initial_snapshot"]
                self.assertNotIn("inference", json.dumps(snapshot))
                self.assertNotIn(KEY, json.dumps(snapshot))
            self.assertEqual(client.post("/api/arena/demo-ai/invalid").status_code, 422)

    def test_smoke_one_request_plan_metrics_and_no_fallback(self):
        for name in ("ollama", "openai"):
            provider, mock = self.provider(name, repair=False)
            output = io.StringIO()
            with patch("aig.arena.smoke.load_settings", return_value=Settings()), \
                    patch("aig.arena.smoke.create_arena_turn_provider", return_value=provider) as factory, \
                    patch("sys.stdout", output):
                self.assertEqual(smoke(name, []), 0)
            self.assertEqual(mock.call_count, 1)
            self.assertFalse(factory.call_args.kwargs["repair"])
            report = json.loads(output.getvalue())
            self.assertEqual(report["ap_total"], 2)
            self.assertTrue(report["metrics"])
            self.assertNotIn(KEY, output.getvalue())

    def test_smoke_invalid_output_fails_without_repair_or_fallback(self):
        provider, mock = self.provider("openai", ["bad"], repair=False)
        output = io.StringIO()
        with patch("aig.arena.smoke.load_settings", return_value=Settings()), \
                patch("aig.arena.smoke.create_arena_turn_provider", return_value=provider), patch("sys.stdout", output):
            self.assertEqual(smoke("openai", []), 1)
        self.assertEqual(mock.call_count, 1)
        self.assertNotIn(KEY, output.getvalue())


if __name__ == "__main__":
    unittest.main()
