"""OpenAI adapter and integration tests: fake clients only, never live inference."""

from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
import traceback

import httpx
import openai
from fastapi.testclient import TestClient
from openai.types.responses import Response

from aig.ai import AiController, OpenAIStrategyProvider, StrategyProviderError
from aig.ai.benchmark import benchmark, main as benchmark_main, make_provider
from aig.ai.ollama import OllamaStrategyProvider, PROMPT_VERSION, SYSTEM_PROMPT
from aig.ai.openai import OPENAI_SCHEMA_VERSION, openai_plan_json_schema, public_configuration
from aig.ai.openai_smoke import main as smoke_main
from aig.ai.plan_schema import PLAN_SCHEMA_VERSION, canonical_json, plan_json_schema
from aig.ai.strategy import HeuristicStrategyProvider, Posture, StrategicPlan, StrategicStateBuilder
from aig.api import create_app
from aig.commands import EndActivation, FoundCity, apply_command
from aig.scenarios import human_vs_ai_demo_setup
from aig.settings import AiSettings, OpenAISettings, Settings, load_settings
from aig.setup import create_game, start_game
from aig.snapshots import SCHEMA_VERSION, to_snapshot

KEY = "sk-FAKE-openai-adapter-secret-canary"


def response(raw=None):
    """Use the actual SDK response model, including its output_text helper."""
    return Response.model_validate(dict(
        id="resp_offline", created_at=0, model="configured-model-2026-09-10", object="response",
        status="completed", error=None, incomplete_details=None, instructions=None,
        metadata={}, parallel_tool_calls=False, temperature=None, tool_choice="auto", tools=[], top_p=None,
        output=[dict(type="reasoning", id="reasoning_offline", summary=[]),
                dict(type="message", id="msg_offline", role="assistant", status="completed",
                     content=[dict(type="output_text", text=raw if raw is not None else
                                   canonical_json(StrategicPlan(Posture.EXPAND).to_dict()), annotations=[])])],
        usage=dict(input_tokens=100, input_tokens_details=dict(cached_tokens=30, cache_write_tokens=0),
                   output_tokens=40, output_tokens_details=dict(reasoning_tokens=5), total_tokens=140),
    ))


class OpenAIProviderTests(unittest.TestCase):
    def setUp(self):
        network = patch("httpx.Client.send", side_effect=AssertionError("Live network forbidden"))
        network.start()
        self.addCleanup(network.stop)
        self.game = create_game(human_vs_ai_demo_setup())
        start_game(self.game)
        apply_command(self.game, FoundCity("A", "unit-1", "city-A", "Amber"))
        apply_command(self.game, EndActivation("A"))
        self.state = StrategicStateBuilder().build(self.game, "B")
        self.plan = HeuristicStrategyProvider().create_plan(self.state)
        self.settings = OpenAISettings(api_key=KEY, model="configured-model", timeout_seconds=2.5,
                                       max_output_tokens=333, reasoning_effort="low")
        self.client = Mock()
        self.client.responses.create.return_value = response(canonical_json(self.plan.to_dict()))
        self.provider = OpenAIStrategyProvider(self.settings, client=self.client)

    def test_client_has_explicit_resolved_key_timeout_and_zero_sdk_retries(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "wrong-environment-key"}), \
                patch("aig.ai.openai.OpenAI", return_value=self.client) as constructor:
            provider = OpenAIStrategyProvider(self.settings)
        constructor.assert_called_once_with(api_key=KEY, timeout=2.5, max_retries=0)
        provider.create_plan(self.state)
        self.client.responses.create.assert_called_once()
        with openai.OpenAI(api_key=KEY, timeout=2.5, max_retries=0) as client:
            self.assertEqual(client.timeout, 2.5)
            self.assertEqual(client.max_retries, 0)

    def test_key_required_only_at_provider_construction_no_environment_discovery(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": KEY}), patch("aig.ai.openai.OpenAI") as constructor:
            with self.assertRaisesRegex(StrategyProviderError, "requires OPENAI_API_KEY"):
                OpenAIStrategyProvider(OpenAISettings())
        constructor.assert_not_called()
        self.assertIsNone(load_settings(local_file=None, environ={}).openai.api_key)

    def test_request_and_schema_use_settings_without_persistence_or_extra_parameters(self):
        self.assertEqual(self.provider.create_plan(self.state), self.plan)
        call = self.client.responses.create.call_args.kwargs
        self.assertEqual(set(call), {"model", "instructions", "input", "reasoning", "max_output_tokens", "text", "store"})
        self.assertEqual(call["model"], self.settings.model)
        self.assertEqual(call["reasoning"], {"effort": "low"})
        self.assertEqual(call["max_output_tokens"], 333)
        self.assertIs(call["store"], False)
        self.assertEqual(call["instructions"], SYSTEM_PROMPT)
        self.assertEqual(call["text"]["format"], dict(type="json_schema", name="strategic_plan", strict=True,
                                                      schema=openai_plan_json_schema()))
        expected = plan_json_schema()
        for rule in expected["properties"].values():
            rule.pop("uniqueItems", None)
            rule.pop("minLength", None)
        self.assertEqual(openai_plan_json_schema(), expected)
        self.assertTrue(plan_json_schema()["properties"]["production_priority"]["uniqueItems"])
        self.assertEqual(expected["required"], list(self.plan.to_dict()))

    def test_identical_prompt_semantics_and_no_state_mutation(self):
        before = deepcopy(self.state)
        snapshot = to_snapshot(self.game)
        requester = Mock(return_value=canonical_json(dict(done=True, message=dict(content=canonical_json(self.plan.to_dict())))))
        ollama = OllamaStrategyProvider(Settings().ollama, requester=requester)
        for previous in (None, self.plan):
            self.provider.create_plan(self.state, previous)
            ollama.create_plan(self.state, previous)
            ollama_messages = json.loads(requester.call_args.args[1])["messages"]
            request = self.client.responses.create.call_args.kwargs
            self.assertEqual(request["input"], ollama_messages[1:])
            self.assertEqual(request["instructions"], ollama_messages[0]["content"])
            self.assertIn(canonical_json(self.state), request["input"][0]["content"])
            self.assertIn("PREVIOUS PLAN:\n" + canonical_json(previous.to_dict() if previous else None),
                          request["input"][0]["content"])
        self.assertEqual(self.state, before)
        self.assertEqual(to_snapshot(self.game), snapshot)

    def test_trace_records_usage_versions_ids_timing_and_is_detached(self):
        self.client.responses.create.return_value._request_id = "req_offline"
        with patch("aig.ai.openai.perf_counter", side_effect=[10.0, 12.5]):
            self.provider.create_plan(self.state, self.plan)
        trace = self.provider.last_trace
        self.assertEqual(trace["model_configuration"], public_configuration(self.settings))
        self.assertEqual(trace["prompt_version"], PROMPT_VERSION)
        self.assertEqual(trace["schema_version"], PLAN_SCHEMA_VERSION)
        self.assertEqual(trace["provider_schema_version"], OPENAI_SCHEMA_VERSION)
        self.assertEqual(trace["wall_clock_seconds"], 2.5)
        self.assertEqual(trace["retry_count"], 0)
        self.assertEqual(trace["actual_provider"], "openai")
        self.assertFalse(trace["fallback_used"])
        attempt = trace["attempts"][0]
        self.assertEqual(attempt["metrics"], dict(input_tokens=100, cached_input_tokens=30,
                                                 output_tokens=40, reasoning_tokens=5, total_tokens=140))
        self.assertEqual(attempt["response_id"], "resp_offline")
        self.assertEqual(attempt["request_id"], "req_offline")
        self.assertEqual(attempt["model"], "configured-model-2026-09-10")
        self.assertEqual(attempt["raw_content"], canonical_json(self.plan.to_dict()))
        self.assertEqual(trace["resulting_plan"], self.plan.to_dict())
        self.assertNotIn(KEY, canonical_json(trace))
        self.assertNotIn(KEY, repr(self.provider))
        self.assertNotIn(KEY, repr(self.settings))
        trace["attempts"].clear()
        self.assertEqual(len(self.provider.last_trace["attempts"]), 1)

    def test_application_validation_repair_and_second_failure(self):
        valid = self.plan.to_dict()
        cases = ["invalid json", "[]", canonical_json({**valid, "extra": True}),
                 canonical_json({**valid, "production_priority": ["warrior", "warrior"]}),
                 canonical_json({**valid, "research_priority": []}),
                 canonical_json({**valid, "primary_enemy_id": "B"}),
                 canonical_json({**valid, "target_city_id": "invented"}),
                 canonical_json({**valid, "target_city_id": " "}),
                 '{"posture":"expand","posture":"attack"}', "NaN"]
        for raw in cases:
            for succeeds in (True, False):
                with self.subTest(raw=raw, succeeds=succeeds):
                    self.client.reset_mock()
                    self.client.responses.create.side_effect = [response(raw), response() if succeeds else response(raw)]
                    if succeeds:
                        self.assertEqual(self.provider.create_plan(self.state), StrategicPlan(Posture.EXPAND))
                    else:
                        with self.assertRaises(StrategyProviderError):
                            self.provider.create_plan(self.state)
                    self.assertEqual(self.client.responses.create.call_count, 2)
                    self.assertEqual(self.provider.last_trace["retry_count"], 1)
                    repair = self.client.responses.create.call_args.kwargs["input"][-1]["content"]
                    self.assertIn("Return a corrected StrategicPlan", repair)
                    self.assertLess(len(repair), 500)

    def test_refusal_incomplete_empty_and_malformed_responses_do_not_retry(self):
        incomplete = response()
        incomplete.status = "incomplete"
        refusal = response()
        refusal.output[-1].content = [NS(type="refusal", refusal=KEY)]
        failed = response()
        failed.status = "failed"
        cases = [(refusal, "refusal"), (incomplete, "incomplete_response"), (failed, "malformed_openai_response"),
                 (response(""), "empty_output"), (response("  "), "empty_output"),
                 (None, "malformed_openai_response"),
                 (NS(status="completed", output=None), "malformed_openai_response"),
                 (NS(status="completed", output=[], output_text=123), "malformed_openai_response"),
                 (NS(status="completed", output=[NS(type="message", content=None)]), "malformed_openai_response")]
        for value, category in cases:
            with self.subTest(category=category, response_type=type(value)):
                self.client.reset_mock()
                self.client.responses.create.return_value = value
                with self.assertRaises(StrategyProviderError) as caught:
                    self.provider.create_plan(self.state)
                self.client.responses.create.assert_called_once()
                self.assertEqual(self.provider.last_trace["attempts"][0]["error_category"], category)
                self.assertNotIn(KEY, str(caught.exception) + canonical_json(self.provider.last_trace))

    def test_sdk_failures_are_categorized_sanitized_and_not_retried(self):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses", headers={"Authorization": "Bearer " + KEY})
        cases = [(openai.AuthenticationError, 401, "authentication_failure"),
                 (openai.PermissionDeniedError, 403, "permission_denied"),
                 (openai.NotFoundError, 404, "model_not_available"),
                 (openai.RateLimitError, 429, "rate_limit"),
                 (openai.BadRequestError, 400, "api_error"),
                 (openai.InternalServerError, 500, "api_error")]
        errors = [(kind(KEY, response=httpx.Response(status, request=request, headers={"x-request-id": "req_error"}),
                        body={"error": KEY}), category) for kind, status, category in cases]
        errors.extend([(openai.APITimeoutError(request), "timeout"),
                       (openai.APIConnectionError(message=KEY, request=request), "connection_failure"),
                       (openai.APIError(KEY, request, body={"secret": KEY}), "api_error"),
                       (openai.APIResponseValidationError(response=httpx.Response(200, request=request),
                                                          body=KEY), "malformed_openai_response")])
        for error, category in errors:
            with self.subTest(category=category):
                self.client.reset_mock()
                self.client.responses.create.side_effect = error
                try:
                    self.provider.create_plan(self.state)
                except StrategyProviderError:
                    rendered = traceback.format_exc()
                else:
                    self.fail("Expected controlled failure")
                self.client.responses.create.assert_called_once()
                self.assertEqual(self.provider.last_trace["attempts"][0]["error_category"], category)
                self.assertNotIn(KEY, rendered + canonical_json(self.provider.last_trace))
                self.assertNotIn("Authorization", rendered)

    def test_raw_diagnostics_redact_accidental_echoes_and_bound_output(self):
        self.client.responses.create.side_effect = [response(KEY * 5000), response()]
        self.provider.create_plan(self.state)
        trace = self.provider.last_trace
        self.assertNotIn(KEY, canonical_json(trace))
        self.assertLessEqual(len(trace["attempts"][0]["raw_content"]), 32768)

    def test_absent_usage_is_not_fabricated_and_malformed_counters_are_ignored(self):
        for usage, expected in ((None, {}),
                                (NS(input_tokens=-1, output_tokens=True, total_tokens=4,
                                    input_tokens_details=None), {"total_tokens": 4})):
            value = response()
            value.usage = usage
            self.client.responses.create.return_value = value
            self.provider.create_plan(self.state)
            self.assertEqual(self.provider.last_trace["attempts"][0]["metrics"], expected)

    def test_controller_fallback_and_success_provenance_and_reuse(self):
        for fails in (False, True):
            self.client.reset_mock()
            self.client.responses.create.side_effect = [response("invalid"), response("invalid")] if fails else None
            controller = AiController(self.provider)
            result = controller.plan_for(self.game, "B")
            self.assertEqual(result, self.plan)
            self.assertEqual(controller.summary["requestedProvider"], "openai")
            self.assertEqual(controller.summary["actualProvider"], "heuristic" if fails else "openai")
            self.assertEqual(controller.summary["fallbackUsed"], fails)
            self.assertEqual(controller.last_trace["fallback_used"], fails)
            count = self.client.responses.create.call_count
            controller.plan_for(self.game, "B")
            self.assertEqual(self.client.responses.create.call_count, count)
            self.assertTrue(controller.summary["planReused"])

    def test_api_selected_and_explicit_modes_use_provider_and_keep_boundaries_secret_free(self):
        self.client.responses.create.return_value = response()
        for selected, route in (("openai", "configured"), ("heuristic", "openai"), ("ollama", "openai")):
            settings = Settings(ai=AiSettings(strategy_provider=selected), openai=self.settings)
            with patch("aig.api.load_settings", return_value=settings), \
                    patch("aig.ai.openai.OpenAI", return_value=self.client) as constructor:
                app = create_app()
                constructor.assert_not_called()
                with TestClient(app) as client:
                    client.post("/api/game/demo/" + route).raise_for_status()
                    self.assertIsInstance(app.state.session.ai.provider, OpenAIStrategyProvider)
                    constructor.assert_called_once_with(api_key=KEY, timeout=2.5, max_retries=0)
                    client.post("/api/game/start").raise_for_status()
                    result = client.post("/api/game/commands", json={"type": "end_activation"})
                    result.raise_for_status()
                    dto = result.json()
                    self.assertEqual(dto["aiProviders"], {"B": "openai"})
                    self.assertEqual(dto["aiActivations"][0]["actualProvider"], "openai")
                    self.assertFalse(dto["aiActivations"][0]["fallbackUsed"])
                self.assertNotIn(KEY, canonical_json(dto))
                self.assertNotIn(KEY, canonical_json(app.state.session.ai.inference_traces))
                self.assertNotIn(KEY, canonical_json(to_snapshot(app.state.session._state)))
                self.assertEqual(SCHEMA_VERSION, 8)

    def test_benchmark_explicit_selection_telemetry_and_fallback_contamination(self):
        settings = Settings(ai=AiSettings(strategy_provider="ollama"), openai=self.settings)
        with patch("aig.ai.openai.OpenAI", return_value=self.client):
            self.assertIsInstance(make_provider("openai", settings), OpenAIStrategyProvider)
        for fails in (False, True):
            self.client.responses.create.side_effect = None
            self.client.responses.create.return_value = response("invalid") if fails else response()
            with TemporaryDirectory() as directory:
                report = benchmark(output=Path(directory), games=1, turns=1, provider_b="openai", settings=settings,
                                   provider_factory=lambda name, _: self.provider if name == "openai" else HeuristicStrategyProvider())
                run = report["runs"][1]
                self.assertEqual(run["pureProviderRun"], not fails)
                self.assertEqual(run["fallbackCount"], 2 if fails else 0)
                self.assertEqual(report["comparison"][0]["pureProviderRuns"], not fails)
                usage = run["inference"]["openai_usage"]
                self.assertEqual(usage["input_tokens"]["total"], 400 if fails else 200)
                self.assertEqual(usage["cached_input_tokens"]["total"], 120 if fails else 60)
                self.assertEqual(usage["reasoning_tokens"]["total"], 20 if fails else 10)
                for path in Path(directory).rglob("*.json*"):
                    self.assertNotIn(KEY, path.read_text(encoding="utf-8"))
        self.client.responses.create.return_value = response()
        with TemporaryDirectory() as directory, patch("aig.ai.benchmark.load_settings", return_value=settings), \
                patch("aig.ai.openai.OpenAI", return_value=self.client), patch("builtins.print"):
            benchmark_main(["--provider-a", "openai", "--provider-b", "heuristic", "--turns", "1", "--output", directory])
            report = json.loads((Path(directory) / "summary.json").read_text())
            self.assertEqual(report["configuration"]["providers"], dict(a="openai", b="heuristic"))

    def test_smoke_is_exactly_one_request_with_no_repair_or_fallback(self):
        for invalid in (False, True):
            self.client.reset_mock()
            self.client.responses.create.return_value = response("invalid") if invalid else response()
            with patch("aig.ai.openai_smoke.load_settings", return_value=Settings(openai=self.settings)), \
                    patch("aig.ai.openai.OpenAI", return_value=self.client), patch("sys.stdout", new_callable=io.StringIO) as output:
                code = smoke_main([])
            self.assertEqual(code, 1 if invalid else 0)
            self.client.responses.create.assert_called_once()
            result = json.loads(output.getvalue())
            self.assertFalse(result["fallback_used"])
            self.assertEqual(result["requests"], 1)
            self.assertEqual(result["usage"][0]["input_tokens"], 100)
            self.assertNotIn(KEY, output.getvalue())
        with patch("aig.ai.openai_smoke.load_settings", return_value=Settings()), \
                patch("aig.ai.openai.OpenAI") as constructor, patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(smoke_main([]), 1)
            constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
