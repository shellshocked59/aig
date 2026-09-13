"""Exercise the real SDK with an in-memory HTTP transport; never live inference."""

import json
import traceback
import unittest
from unittest.mock import Mock

import httpx
from openai import OpenAI

from aig.ai.controller import AiController
from aig.ai.openai import OpenAIStrategyProvider
from aig.ai.strategy import HeuristicStrategyProvider, StrategicStateBuilder, StrategyProviderError
from aig.scenarios import human_vs_ai_demo_setup
from aig.settings import OpenAISettings
from aig.setup import create_game, start_game


KEY = "sk-FAKE-transport-secret-canary"


class OpenAITransportTests(unittest.TestCase):
    def setUp(self):
        self.game = create_game(human_vs_ai_demo_setup())
        start_game(self.game)
        self.state = StrategicStateBuilder().build(self.game, "B")
        self.plan = HeuristicStrategyProvider().create_plan(self.state)

    def provider(self, reply):
        handler = Mock(return_value=reply)
        client = OpenAI(api_key=KEY, max_retries=0,
                        http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        self.addCleanup(client.close)
        return OpenAIStrategyProvider(OpenAISettings(api_key=KEY), client=client), handler

    def envelope(self):
        return dict(id="resp_offline", status="completed", error=None,
                    output=[dict(type="message", id="msg_offline", role="assistant", status="completed",
                                 content=[dict(type="output_text", text=json.dumps(self.plan.to_dict()),
                                               annotations=[])])])

    def test_sdk_serializes_request_and_extracts_plan_without_network(self):
        provider, handler = self.provider(httpx.Response(200, json=self.envelope(),
                                                        headers={"x-request-id": "req_offline"}))
        self.assertEqual(provider.create_plan(self.state), self.plan)
        handler.assert_called_once()
        request = handler.call_args.args[0]
        self.assertEqual(request.url.path, "/v1/responses")
        payload = json.loads(request.content)
        self.assertFalse(payload["store"])
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(provider.last_trace["attempts"][0]["request_id"], "req_offline")

    def test_unreadable_http_json_is_sanitized_and_reaches_controller_fallback(self):
        for body in (b"not-json", b"\xff", b"[" * 2000, ("{" + KEY).encode()):
            with self.subTest(body_length=len(body)):
                provider, handler = self.provider(httpx.Response(
                    200, content=body, headers={"content-type": "application/json"}))
                controller = AiController(provider)
                self.assertEqual(controller.plan_for(self.game, "B"), self.plan)
                handler.assert_called_once()
                self.assertEqual(controller.summary["requestedProvider"], "openai")
                self.assertEqual(controller.summary["actualProvider"], "heuristic")
                self.assertTrue(controller.summary["fallbackUsed"])
                attempt = controller.last_trace["attempts"][0]
                self.assertEqual(attempt["error_category"], "malformed_openai_response")
                self.assertGreaterEqual(attempt["wall_clock_seconds"], 0)
                self.assertNotIn(KEY, json.dumps(controller.last_trace))

    def test_malformed_message_cannot_be_hidden_by_valid_plan_text(self):
        for changes in (dict(status="incomplete"), dict(status=None), dict(role="user"),
                        dict(content=[dict(type="unexpected", text=KEY)])):
            with self.subTest(changes=list(changes)):
                envelope = self.envelope()
                message = {**envelope["output"][0], "content": [], **changes}
                # Even with a second valid message, reject malformed/incomplete content.
                envelope["output"].insert(0, message)
                provider, handler = self.provider(httpx.Response(200, json=envelope))
                with self.assertRaises(StrategyProviderError):
                    provider.create_plan(self.state)
                handler.assert_called_once()
                expected = "incomplete_response" if changes.get("status") == "incomplete" else "malformed_openai_response"
                self.assertEqual(provider.last_trace["attempts"][0]["error_category"], expected)
                self.assertNotIn(KEY, json.dumps(provider.last_trace))

    def test_real_sdk_http_errors_have_no_hidden_retries_or_secret_exception_chain(self):
        for status, category in ((401, "authentication_failure"), (403, "permission_denied"),
                                 (404, "model_not_available"), (429, "rate_limit"), (500, "api_error")):
            with self.subTest(status=status):
                provider, handler = self.provider(httpx.Response(
                    status, json={"error": {"message": KEY}}, headers={"x-request-id": "req_failure"}))
                try:
                    provider.create_plan(self.state)
                except StrategyProviderError:
                    rendered = traceback.format_exc()
                else:
                    self.fail("Expected controlled provider failure")
                handler.assert_called_once()
                attempt = provider.last_trace["attempts"][0]
                self.assertEqual(attempt["error_category"], category)
                self.assertEqual(attempt["http_status"], status)
                self.assertEqual(attempt["request_id"], "req_failure")
                self.assertNotIn(KEY, rendered + json.dumps(provider.last_trace))


if __name__ == "__main__":
    unittest.main()
