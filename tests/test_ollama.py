"""Offline Ollama contract, failure, orchestration and browser API coverage."""

from copy import deepcopy
from dataclasses import fields, replace
from http.client import RemoteDisconnected
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from fastapi.testclient import TestClient

from aig.ai import AiController, AiExecutor, AiOrchestrator, OllamaStrategyProvider, StrategyProviderError
from aig.ai.ollama import METRICS, PROMPT_VERSION, post_json
from aig.ai.plan_schema import PLAN_SCHEMA_VERSION, canonical_json, parse_plan, plan_json_schema
from aig.ai.strategy import HeuristicStrategyProvider, Posture, StrategicPlan, StrategicStateBuilder
from aig.api import create_app
from aig.application import GameSession
from aig.commands import EndActivation, FoundCity, apply_command
from aig.scenarios import human_vs_ai_demo_setup
from aig.settings import OllamaSettings, load_settings
from aig.setup import create_game, start_game
from aig.snapshots import SCHEMA_VERSION, to_snapshot


def game():
    state = create_game(human_vs_ai_demo_setup())
    start_game(state)
    apply_command(state, FoundCity("A", "unit-1", "city-A", "Amber"))
    apply_command(state, EndActivation("A"))
    return state


def response(plan=None, *, content=None, **extra):
    return json.dumps({"done": True, "message": {"content": content if content is not None else
                       canonical_json((plan or StrategicPlan(Posture.EXPAND)).to_dict()),
                       "thinking": "must never be retained"},
                       **{key: n + 10 for n, key in enumerate(METRICS)}, **extra})


class OllamaProviderTests(unittest.TestCase):
    def setUp(self):
        self.game = game()
        self.state = StrategicStateBuilder().build(self.game, "B")
        self.plan = HeuristicStrategyProvider().create_plan(self.state)
        self.requester = Mock(return_value=response(self.plan))
        self.settings = OllamaSettings(base_url="http://test.invalid:9999///", model="test-qwen",
                                       context_size=2048, temperature=0.2, seed=7,
                                       max_output_tokens=128, keep_alive="2m", timeout_seconds=1.5)
        self.provider = OllamaStrategyProvider(self.settings, requester=self.requester)

    def test_exact_request_and_concrete_schema(self):
        self.provider.create_plan(self.state)
        url, body, timeout = self.requester.call_args.args
        self.assertEqual(url, "http://test.invalid:9999/api/chat")
        self.assertEqual(timeout, 1.5)
        request = json.loads(body)
        self.assertEqual(set(request), {"model", "stream", "think", "keep_alive", "messages", "format", "options"})
        self.assertEqual(request["model"], "test-qwen")
        self.assertIs(request["stream"], False)
        self.assertIs(request["think"], False)
        self.assertEqual(request["keep_alive"], "2m")
        self.assertEqual(request["options"], dict(num_ctx=2048, temperature=0.2, seed=7, num_predict=128))
        self.assertEqual(request["format"], plan_json_schema())
        self.assertIs(request["format"]["additionalProperties"], False)
        self.assertEqual(set(request["format"]["required"]), {f.name for f in fields(StrategicPlan)})
        self.assertEqual(body.decode(), canonical_json(request))

    def test_valid_plan_preserves_every_field(self):
        self.assertEqual(self.provider.create_plan(self.state), self.plan)
        self.assertIsInstance(self.provider.create_plan(self.state), StrategicPlan)

    def test_compact_prompt_includes_state_options_and_null_previous(self):
        before = deepcopy(self.state)
        self.provider.create_plan(self.state)
        messages = json.loads(self.requester.call_args.args[1])["messages"]
        self.assertIn(canonical_json(self.state), messages[1]["content"])
        self.assertIn("PREVIOUS PLAN:\nnull", messages[1]["content"])
        self.assertIn("PRIORITY OPTIONS:", messages[1]["content"])
        self.assertNotIn('"tiles"', messages[1]["content"])
        self.assertEqual(self.state, before)

    def test_previous_plan_is_serialized(self):
        self.provider.create_plan(self.state, self.plan)
        self.assertIn("PREVIOUS PLAN:\n" + canonical_json(self.plan.to_dict()),
                      json.loads(self.requester.call_args.args[1])["messages"][1]["content"])
        self.assertEqual(self.provider.last_trace["previous_plan"], self.plan.to_dict())

    def test_trace_versions_metrics_raw_output_and_timing(self):
        with patch("aig.ai.ollama.perf_counter", side_effect=[10.0, 12.5]):
            self.provider.create_plan(self.state)
        trace = self.provider.last_trace
        self.assertEqual(trace["prompt_version"], PROMPT_VERSION)
        self.assertEqual(trace["schema_version"], PLAN_SCHEMA_VERSION)
        self.assertEqual(trace["wall_clock_seconds"], 2.5)
        self.assertEqual(trace["attempts"][0]["metrics"], {k: i + 10 for i, k in enumerate(METRICS)})
        self.assertEqual(trace["attempts"][0]["raw_content"], canonical_json(self.plan.to_dict()))
        self.assertEqual(trace["resulting_plan"], self.plan.to_dict())
        self.assertNotIn("must never be retained", canonical_json(trace))
        trace["attempts"].clear()
        self.assertEqual(len(self.provider.last_trace["attempts"]), 1)

    def test_identical_inputs_produce_identical_request_bytes_and_prompts(self):
        self.provider.create_plan(self.state, self.plan)
        first = self.requester.call_args.args[1]
        reordered = dict(reversed(list(self.state.items())))
        self.provider.create_plan(reordered, self.plan)
        self.assertEqual(first, self.requester.call_args.args[1])

    def test_null_targets_and_future_priorities_remain_valid(self):
        plan = StrategicPlan(Posture.DEFEND)
        self.assertEqual(parse_plan(canonical_json(plan.to_dict()), self.state), plan)
        self.state["available_research"] = []
        self.assertEqual(parse_plan(canonical_json(plan.to_dict()), self.state), plan)

    def test_invalid_outputs_repair_once_with_concise_feedback(self):
        valid = self.plan.to_dict()
        invalid = ["not json", "[]", "null", "{}", '{"posture":NaN}',
                   canonical_json({**valid, "extra": "invented"})]
        for key, value in [("posture", "conquer"), ("posture", 1),
                           ("expansion_priority", "medium"), ("primary_enemy_id", "city-A"),
                           ("primary_enemy_id", "B"), ("target_city_id", "city-99"),
                           ("target_city_id", 99), ("production_priority", ["tank"]),
                           ("production_priority", ["warrior", "warrior"]),
                           ("production_priority", [True]), ("production_priority", "warrior"),
                           ("research_priority", []), ("research_priority", ["lasers"])]:
            invalid.append(canonical_json({**valid, key: value}))
        for raw in invalid:
            with self.subTest(raw=raw):
                self.requester.reset_mock()
                self.requester.side_effect = [response(content=raw), response(self.plan)]
                self.assertEqual(self.provider.create_plan(self.state), self.plan)
                self.assertEqual(self.requester.call_count, 2)
                payload = json.loads(self.requester.call_args.args[1])
                self.assertIn("invalid", payload["messages"][-1]["content"])
                self.assertNotIn("Traceback", payload["messages"][-1]["content"])
                self.assertEqual(payload["format"], plan_json_schema())
                self.assertEqual(self.provider.last_trace["retry_count"], 1)

    def test_own_city_and_mismatched_enemy_city_are_rejected(self):
        own = dict(self.state["enemy_cities"][0], id="city-B", owner_id="B")
        self.state["own_cities"].append(own)
        for target, enemy in [("city-B", "A"), ("city-A", "C")]:
            self.state["enemy_units"].append(dict(self.state["enemy_units"][0], owner_id="C", id="other"))
            with self.subTest(target=target), self.assertRaises(ValueError):
                parse_plan(canonical_json({**self.plan.to_dict(), "target_city_id": target,
                                           "primary_enemy_id": enemy}), self.state)

    def test_duplicate_json_keys_are_rejected(self):
        raw = canonical_json(self.plan.to_dict()).replace('"posture":', '"posture":"defend","posture":')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_plan(raw, self.state)

    def test_second_invalid_output_raises_controlled_error(self):
        self.requester.return_value = response(content="broken")
        with self.assertRaises(StrategyProviderError):
            self.provider.create_plan(self.state)
        self.assertEqual(self.requester.call_count, 2)
        self.assertEqual(self.provider.last_trace["retry_count"], 1)

    def test_bad_top_level_responses_are_controlled_and_bounded(self):
        for raw in ("<html>bad gateway</html>", "[]", "{}", '{"message":null}',
                    '{"message":{"content":{}}}', response(self.plan, done=False),
                    response(self.plan, error="generation error")):
            with self.subTest(raw=raw):
                self.requester.reset_mock()
                self.requester.return_value = raw
                with self.assertRaises(StrategyProviderError):
                    self.provider.create_plan(self.state)
                self.assertEqual(self.requester.call_count, 2)

    def test_http_failures_do_not_retry(self):
        for error in (ConnectionRefusedError(), TimeoutError(), URLError("offline"),
                      HTTPError("http://test", 503, "unavailable", {}, None), RemoteDisconnected()):
            with self.subTest(error=error):
                self.requester.reset_mock()
                self.requester.side_effect = error
                with self.assertRaises(StrategyProviderError):
                    self.provider.create_plan(self.state)
                self.assertEqual(self.requester.call_count, 1)
                self.assertEqual(self.provider.last_trace["retry_count"], 0)
                self.assertIn("error", self.provider.last_trace)

    def test_http_failure_on_repair_retains_both_attempts(self):
        self.requester.side_effect = [response(content="bad"), TimeoutError()]
        with self.assertRaises(StrategyProviderError):
            self.provider.create_plan(self.state)
        self.assertEqual(len(self.provider.last_trace["attempts"]), 2)

    def test_transport_posts_json_with_timeout(self):
        http_response = Mock(status=200)
        http_response.read.return_value = b'{"ok":true}'
        with patch("aig.ai.ollama.urlopen") as opener:
            opener.return_value.__enter__.return_value = http_response
            self.assertEqual(post_json("http://test/api/chat", b"{}", 7.0), '{"ok":true}')
            request = opener.call_args.args[0]
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(request.full_url, "http://test/api/chat")
            self.assertEqual(request.get_header("Content-type"), "application/json")
            self.assertEqual(request.data, b"{}")
            self.assertEqual(opener.call_args.kwargs["timeout"], 7.0)

    def test_transport_rejects_non_success_status(self):
        with patch("aig.ai.ollama.urlopen") as opener:
            opener.return_value.__enter__.return_value.status = 503
            with self.assertRaises(StrategyProviderError):
                post_json("http://test/api/chat", b"{}", 1)

    def test_no_reasoning_or_streaming_configuration_is_accepted(self):
        for key in ("think", "stream"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                OllamaStrategyProvider(replace(self.settings, **{key: True}))


class OllamaControllerTests(unittest.TestCase):
    def setUp(self):
        self.state = game()
        self.plan = HeuristicStrategyProvider().create_plan(StrategicStateBuilder().build(self.state, "B"))
        self.requester = Mock(return_value=response(self.plan))
        self.provider = OllamaStrategyProvider(OllamaSettings(), requester=self.requester)
        self.ai = AiOrchestrator(self.provider)

    def test_success_executes_same_commands_and_state_as_heuristic_plan(self):
        expected_state = deepcopy(self.state)
        expected = AiExecutor().execute(expected_state, self.plan)
        actual = self.ai.run_active_ai_activation(self.state)
        self.assertEqual(actual, expected)
        self.assertEqual(to_snapshot(self.state), to_snapshot(expected_state))
        self.assertFalse(self.ai.latest_summaries[0]["fallbackUsed"])
        self.assertEqual(self.ai.latest_summaries[0]["actualProvider"], "ollama")

    def test_network_and_exhausted_repair_fallback_execute_normally(self):
        for result in (TimeoutError(), response(content="bad")):
            with self.subTest(result=result):
                state = game()
                requester = Mock(side_effect=result) if isinstance(result, Exception) else Mock(return_value=result)
                ai = AiOrchestrator(OllamaStrategyProvider(OllamaSettings(), requester=requester))
                actual = ai.run_active_ai_activation(state)
                self.assertEqual(actual.plan, self.plan)
                state.validate()
                self.assertEqual(state.active_player_id, "A")
                summary = ai.latest_summaries[0]
                self.assertEqual(summary["requestedProvider"], "ollama")
                self.assertEqual(summary["actualProvider"], "heuristic")
                self.assertTrue(summary["fallbackUsed"])
                self.assertEqual(ai.inference_traces[0]["resulting_plan"], self.plan.to_dict())

    def test_valid_young_plan_never_calls_ollama(self):
        controller = AiController(self.provider, previous_plan=self.plan, plan_creation_turn=0)
        self.state.turn = 4
        self.assertIs(controller.plan_for(self.state, "B"), self.plan)
        self.requester.assert_not_called()
        self.assertTrue(controller.summary["planReused"])

    def test_expired_plan_replans_once_with_previous(self):
        controller = AiController(self.provider, previous_plan=self.plan, plan_creation_turn=0)
        self.state.turn = 5
        controller.plan_for(self.state, "B")
        self.assertEqual(self.requester.call_count, 1)
        self.assertEqual(controller.last_trace["replan_reason"], "expired")
        self.assertEqual(controller.last_trace["plan_age_turns"], 5)
        self.assertEqual(controller.last_trace["previous_plan"], self.plan.to_dict())

    def test_invalid_city_triggers_immediate_replan(self):
        old = replace(self.plan, target_city_id="city-deleted")
        controller = AiController(self.provider, previous_plan=old, plan_creation_turn=0)
        controller.plan_for(self.state, "B")
        self.assertEqual(self.requester.call_count, 1)
        self.assertEqual(controller.last_trace["replan_reason"], "invalid_target")

    def test_reuse_retains_provenance_and_deterministic_execution(self):
        self.ai.run_active_ai_activation(self.state)
        apply_command(self.state, EndActivation("A"))
        expected_state = deepcopy(self.state)
        expected = AiExecutor().execute(expected_state, self.plan)
        self.assertEqual(self.ai.run_active_ai_activation(self.state), expected)
        self.assertEqual(self.requester.call_count, 1)
        self.assertEqual(to_snapshot(self.state), to_snapshot(expected_state))
        self.assertEqual(self.ai.latest_summaries[0]["actualProvider"], "ollama")
        self.assertTrue(self.ai.latest_summaries[0]["planReused"])
        self.assertEqual(self.ai.latest_summaries[0]["durationSeconds"], 0.0)

    def test_fallback_is_reused_then_ollama_is_retried_at_expiry(self):
        self.requester.side_effect = [TimeoutError(), response(self.plan)]
        controller = AiController(self.provider)
        controller.plan_for(self.state, "B")
        self.state.turn = 1
        controller.plan_for(self.state, "B")
        self.assertTrue(controller.summary["fallbackUsed"])
        self.assertEqual(controller.summary["actualProvider"], "heuristic")
        self.assertEqual(self.requester.call_count, 1)
        self.state.turn = 5
        controller.plan_for(self.state, "B")
        self.assertFalse(controller.summary["fallbackUsed"])
        self.assertEqual(self.requester.call_count, 2)

    def test_context_trace_detachment_and_unchanged_snapshot_schema(self):
        self.ai.run_active_ai_activation(self.state)
        trace = self.ai.inference_traces[0]
        self.assertEqual(trace["game_seed"], 42)
        self.assertEqual(trace["player_id"], "B")
        self.assertEqual(trace["replan_reason"], "missing_plan")
        self.assertIsNone(trace["plan_age_turns"])
        self.assertEqual(SCHEMA_VERSION, 8)
        self.assertNotIn("prompt", canonical_json(to_snapshot(self.state)))
        trace["attempts"].clear()
        self.assertEqual(len(self.ai.inference_traces[0]["attempts"]), 1)

    def test_trace_history_is_bounded(self):
        self.ai.replan_interval = 1
        for _ in range(66):
            self.ai.run_active_ai_activation(self.state)
            apply_command(self.state, EndActivation("A"))
        self.assertEqual(len(self.ai.inference_traces), 64)
        self.assertEqual(self.ai.inference_traces[-1]["turn"], 65)


class LlmApiTests(unittest.TestCase):
    def setUp(self):
        # Normal suites always inject transport and settings; no LAN access.
        with patch("aig.api.load_settings", return_value=load_settings(local_file=None, environ={})):
            self.app = create_app()
        self.requester = Mock(return_value=response())
        self.provider = OllamaStrategyProvider(OllamaSettings(), requester=self.requester)
        self.app.state.session._ollama_provider = self.provider
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def post(self, path, payload=None):
        result = self.client.post("/api/game" + path, json=payload)
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def test_all_three_modes_and_explicit_provider_identity(self):
        for path, provider in [("/demo", None), ("/demo/ai", "heuristic"), ("/demo/llm", "ollama")]:
            with self.subTest(path=path):
                state = self.post(path)
                self.assertEqual(state.get("aiProviders", {}).get("B"), provider)
                self.assertEqual(state["players"][1]["controller"], "ai" if provider else "human")
        self.requester.assert_not_called()

    def test_human_end_turn_runs_llm_and_returns_compact_debug_summary(self):
        self.post("/demo/llm")
        self.post("/start")
        state = self.post("/commands", {"type": "end_activation"})
        self.assertEqual(state["game"]["activePlayerId"], "A")
        summary = state["aiActivations"][0]
        self.assertEqual(summary["requestedProvider"], "ollama")
        self.assertEqual(summary["actualProvider"], "ollama")
        self.assertFalse(summary["fallbackUsed"])
        self.assertEqual(summary["model"], OllamaSettings().model)
        self.assertEqual(summary["retryCount"], 0)
        self.assertIsInstance(summary["durationSeconds"], float)
        self.assertTrue(summary["commands_executed"])
        self.assertIn("plan", summary)
        self.assertNotIn("CURRENT STATE", json.dumps(state))
        self.post("/commands", {"type": "end_activation"})
        self.assertEqual(self.requester.call_count, 1)

    def test_fallback_is_explicit_in_browser_response(self):
        self.requester.side_effect = TimeoutError()
        self.post("/demo/llm")
        self.post("/start")
        state = self.post("/commands", {"type": "end_activation"})
        summary = state["aiActivations"][0]
        self.assertEqual(summary["requestedProvider"], "ollama")
        self.assertEqual(summary["actualProvider"], "heuristic")
        self.assertTrue(summary["fallbackUsed"])
        self.assertEqual(state["game"]["activePlayerId"], "A")

    def test_reset_clears_runtime_traces_and_switches_provider(self):
        self.post("/demo/llm")
        self.post("/start")
        self.post("/commands", {"type": "end_activation"})
        state = self.post("/demo/ai")
        self.assertNotIn("aiActivations", state)
        self.assertEqual(self.app.state.session.ai.inference_traces, [])
        self.post("/start")
        state = self.post("/commands", {"type": "end_activation"})
        self.assertEqual(state["aiActivations"][0]["actualProvider"], "heuristic")
        self.assertEqual(self.requester.call_count, 1)

    def test_invalid_llm_configuration_preserves_existing_session(self):
        session = GameSession(ollama_settings=OllamaSettings(think=True))
        before = session.demo(versus_ai=True)
        with self.assertRaises(ValueError):
            session.demo(versus_ai=True, provider="ollama")
        self.assertEqual(session.current(), before)

    def test_frontend_source_contains_no_provider_url_or_direct_network_call(self):
        root = Path(__file__).resolve().parents[1] / "frontend/src/js"
        for path in root.rglob("*.js"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("10.0.0.250", source)
            self.assertNotIn("11434", source)
            self.assertNotIn("/api/chat", source)
            if path.name != "game.js" or path.parent.name != "api":
                self.assertNotIn("fetch(", source)


if __name__ == "__main__":
    unittest.main()
