"""Configuration-only cloud foundation: public boundaries and offline providers."""

import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from aig.ai.ollama import OllamaStrategyProvider
from aig.ai.strategy import Posture, StrategicPlan
from aig.api import create_app
from aig.settings import load_settings
from aig.snapshots import to_snapshot


class OpenAIConfigurationBoundaryTests(unittest.TestCase):
    def test_existing_api_modes_with_and_without_key_keep_public_outputs_secret_free(self):
        fake_key = "sk-FAKE-openai-public-output-canary"
        for key in (None, fake_key):
            for mode, provider_name in (("", None), ("/ai", "heuristic"), ("/llm", "ollama")):
                with self.subTest(key_present=key is not None, mode=mode):
                    settings = load_settings(local_file=None, environ={} if key is None else
                                             {"OPENAI_API_KEY": key})
                    requester = Mock(return_value=json.dumps({
                        "done": True,
                        "message": {"content": json.dumps(StrategicPlan(Posture.EXPAND).to_dict())},
                    }))
                    # The genuine Ollama adapter runs with an in-memory transport.
                    ollama = OllamaStrategyProvider(settings.ollama, requester=requester)
                    with patch("aig.api.load_settings", return_value=settings), \
                            patch("socket.create_connection", side_effect=AssertionError("Network forbidden")):
                        app = create_app()
                        app.state.session._ollama_provider = ollama
                        with TestClient(app) as client:
                            responses = [client.get("/api/health"), client.post("/api/game/demo" + mode),
                                         client.post("/api/game/start"),
                                         client.post("/api/game/commands", json={"type": "end_activation"}),
                                         client.get("/api/game")]
                        for response in responses:
                            self.assertEqual(response.status_code, 200, response.text)
                            self.assertNotIn(fake_key, response.text)
                            self.assertNotIn("api_key", response.text.lower())
                        result = responses[-1].json()
                        if provider_name:
                            self.assertEqual(result["aiProviders"], {"B": provider_name})
                            self.assertTrue(result["aiActivations"])
                        else:
                            self.assertNotIn("aiProviders", result)
                        snapshot = json.dumps(to_snapshot(app.state.session._state))
                        self.assertNotIn(fake_key, snapshot)
                        self.assertNotIn("api_key", snapshot.lower())
                        self.assertNotIn(fake_key, repr(app.state.settings))
                        if provider_name == "ollama":
                            requester.assert_called_once()
                            self.assertNotIn(fake_key, json.dumps(ollama.last_trace))
                            self.assertNotIn(fake_key, repr(requester.call_args))
                        else:
                            requester.assert_not_called()

    @unittest.skipUnless((Path(__file__).resolve().parents[1] / "compose.yaml").exists(),
                         "Compose wiring is checked in the checkout, not the API image")
    def test_compose_cloud_variables_are_api_runtime_only(self):
        root = Path(__file__).resolve().parents[1]
        names = ("AIG_STRATEGY_PROVIDER", "OPENAI_API_KEY", "AIG_OPENAI_MODEL", "AIG_OPENAI_TIMEOUT_SECONDS",
                 "AIG_OPENAI_MAX_OUTPUT_TOKENS", "AIG_OPENAI_REASONING_EFFORT")
        # Inspect the committed block boundary without resolving developer secrets.
        for filename in ("compose.yaml", "compose.prod.yaml"):
            service = section = None
            found = set()
            for line in (root / filename).read_text().splitlines():
                indentation = len(line) - len(line.lstrip())
                if indentation == 2 and line.endswith(":"):
                    service = line.strip()[:-1]
                elif indentation == 4 and line.endswith(":"):
                    section = line.strip()[:-1]
                for name in names:
                    if line.strip().startswith(name + ":"):
                        self.assertEqual((service, section), ("api", "environment"))
                        self.assertEqual(line.strip(), f"{name}: ${{{name}:-}}")
                        found.add(name)
            self.assertEqual(found, set(names), filename)
        dockerfile = (root / "Dockerfile").read_text()
        for name in names:
            self.assertNotIn(name, dockerfile)
        for filename in (".gitignore", ".dockerignore"):
            lines = (root / filename).read_text().splitlines()
            self.assertIn(".env", lines)
            self.assertIn(".env.*", lines)
            self.assertEqual([line for line in lines if line.startswith("!")], ["!.env.example"])
        deployment = (root / "scripts/deploy-remote.sh").read_text()
        self.assertIn('--env-file "$repo_root/.env.production"', deployment)


if __name__ == "__main__":
    unittest.main()
