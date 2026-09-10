"""Application selection is independent of explicit demos and benchmark choices."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from aig.ai.benchmark import main as benchmark_main
from aig.ai.ollama import OllamaStrategyProvider
from aig.ai.strategy import HeuristicStrategyProvider, Posture, StrategicPlan
from aig.api import create_app
from aig.application import ApplicationError, GameSession
from aig.commands import EndActivation
from aig.settings import AiSettings, load_settings
from aig.snapshots import to_snapshot


def envelope(content=None):
    return json.dumps({'done': True, 'message': {'content': content if content is not None
                      else json.dumps(StrategicPlan(Posture.EXPAND).to_dict())}})


class ProviderSelectionTests(unittest.TestCase):
    def setUp(self):
        network = patch('aig.ai.ollama.urlopen', side_effect=AssertionError('Live network forbidden'))
        network.start()
        self.addCleanup(network.stop)

    def app(self, provider):
        settings = load_settings(local_file=None, environ={
            'AIG_STRATEGY_PROVIDER': provider,
            'OPENAI_API_KEY': 'sk-FAKE-selector-secret-canary',
            'AIG_OLLAMA_BASE_URL': 'http://private-ollama.example.test:11434',
            'AIG_AI_REPLAN_INTERVAL': '3', 'AIG_AI_MAX_ACTIONS': '100',
        })
        with patch('aig.api.load_settings', return_value=settings):
            return create_app()

    def test_configured_heuristic_matches_explicit_baseline_and_keeps_injection(self):
        configured = GameSession(AiSettings(strategy_provider='heuristic'))
        baseline = GameSession()
        self.assertEqual(configured.demo(versus_ai=True),
                         baseline.demo(versus_ai=True, provider='heuristic'))
        self.assertIsInstance(configured.ai.provider, HeuristicStrategyProvider)
        self.assertEqual(configured.start(), baseline.start())
        for _ in range(12):
            self.assertEqual(configured.execute(EndActivation), baseline.execute(EndActivation))
        self.assertEqual(to_snapshot(configured._state), to_snapshot(baseline._state))
        injected = HeuristicStrategyProvider()
        session = GameSession(strategy_provider=injected)
        session.demo(versus_ai=True)
        self.assertIs(session.ai.provider, injected)

    def test_configured_api_constructs_existing_provider_and_preserves_ollama_behavior(self):
        for selected in ('heuristic', 'ollama'):
            for failure in (False, True):
                with self.subTest(selected=selected, failure=failure):
                    app = self.app(selected)
                    requester = Mock(side_effect=TimeoutError() if failure else
                                     [envelope('invalid json'), envelope()])
                    def construct(settings):
                        return OllamaStrategyProvider(settings, requester=requester)
                    with patch('aig.application.OllamaStrategyProvider', side_effect=construct) as factory, \
                            TestClient(app) as client:
                        response = client.post('/api/game/demo/configured')
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.json()['aiProviders'], {'B': selected})
                        requester.assert_not_called()
                        ai = app.state.session.ai
                        self.assertEqual(ai.replan_interval, 3)
                        self.assertEqual(ai.executor.max_actions, 100)
                        if selected == 'ollama':
                            factory.assert_called_once_with(app.state.settings.ollama)
                            self.assertIsInstance(ai.provider, OllamaStrategyProvider)
                        else:
                            factory.assert_not_called()
                            self.assertIsInstance(ai.provider, HeuristicStrategyProvider)
                        client.post('/api/game/start').raise_for_status()
                        results = []
                        for _ in range(2):
                            result = client.post('/api/game/commands', json={'type': 'end_activation'})
                            result.raise_for_status()
                            results.append(result.json())
                        first, reused = [result['aiActivations'][0] for result in results]
                        self.assertEqual(first['requestedProvider'], selected)
                        fallback = selected == 'ollama' and failure
                        self.assertEqual(first['fallbackUsed'], fallback)
                        self.assertEqual(first['actualProvider'], 'heuristic' if fallback else selected)
                        self.assertEqual(first['retryCount'], int(selected == 'ollama' and not failure))
                        self.assertTrue(reused['planReused'])
                        self.assertEqual(reused['retryCount'], 0)
                        self.assertEqual(requester.call_count, (1 if failure else 2) if selected == 'ollama' else 0)
                        public = json.dumps(results)
                        for private in ('sk-FAKE-selector-secret-canary', 'private-ollama.example.test',
                                        'OPENAI_API_KEY', 'AIG_STRATEGY_PROVIDER'):
                            self.assertNotIn(private, public)
                        self.assertNotIn('sk-FAKE-selector-secret-canary', json.dumps(ai.inference_traces))
                        self.assertNotIn('sk-FAKE-selector-secret-canary',
                                         json.dumps(to_snapshot(app.state.session._state)))

    def test_openai_missing_key_is_controlled_atomic_and_startup_does_not_require_key(self):
        settings = load_settings(local_file=None, environ={'AIG_STRATEGY_PROVIDER': 'openai'})
        self.assertIsNone(settings.openai.api_key)
        with patch('aig.api.load_settings', return_value=settings):
            app = create_app()
        with TestClient(app) as client:
            self.assertEqual(client.get('/api/health').status_code, 200)
            response = client.post('/api/game/demo/configured')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json(), {
                'error': 'provider_not_available',
                'message': 'OpenAI requires OPENAI_API_KEY when selected.',
            })
            self.assertEqual(client.get('/api/game').status_code, 404)
            client.post('/api/game/demo/ai').raise_for_status()
            client.post('/api/game/start').raise_for_status()
            client.post('/api/game/commands', json={'type': 'end_activation'}).raise_for_status()
            before = client.get('/api/game').json()
            ai = app.state.session.ai
            with self.assertRaises(ApplicationError) as caught:
                app.state.session.demo(versus_ai=True)
            self.assertEqual(caught.exception.code, 'provider_not_available')
            self.assertEqual(client.post('/api/game/demo/configured').status_code, 503)
            self.assertIs(app.state.session.ai, ai)
            self.assertEqual(client.get('/api/game').json(), before)

    def test_explicit_demos_ignore_configured_selection(self):
        for selected in ('heuristic', 'ollama', 'openai'):
            app = self.app(selected)
            requester = Mock(return_value=envelope())
            injected = OllamaStrategyProvider(app.state.settings.ollama, requester=requester)
            app.state.session._ollama_provider = injected
            with TestClient(app) as client:
                for path, provider in (('', None), ('/ai', 'heuristic'), ('/llm', 'ollama')):
                    with self.subTest(selected=selected, path=path):
                        result = client.post('/api/game/demo' + path)
                        result.raise_for_status()
                        self.assertEqual(result.json().get('aiProviders', {}).get('B'), provider)
                        client.post('/api/game/start').raise_for_status()
                        result = client.post('/api/game/commands', json={'type': 'end_activation'})
                        result.raise_for_status()
                        if provider:
                            self.assertEqual(result.json()['aiActivations'][0]['requestedProvider'], provider)
                self.assertIs(app.state.session.ai.provider, injected)
                requester.assert_called_once()

    def test_benchmark_cli_provider_arguments_ignore_application_selection(self):
        for selected in ('heuristic', 'ollama', 'openai'):
            settings = load_settings(local_file=None, environ={'AIG_STRATEGY_PROVIDER': selected})
            requester = Mock(return_value=envelope())
            def construct(config):
                return OllamaStrategyProvider(config, requester=requester)
            with TemporaryDirectory() as directory, \
                    patch('aig.ai.benchmark.load_settings', return_value=settings), \
                    patch('aig.ai.benchmark.OllamaStrategyProvider', side_effect=construct) as factory, \
                    patch('builtins.print'):
                benchmark_main(['--provider-a', 'heuristic', '--provider-b', 'ollama',
                                '--games', '1', '--turns', '1', '--output', directory])
                report = json.loads((Path(directory) / 'summary.json').read_text())
                self.assertEqual(report['configuration']['providers'], {'a': 'heuristic', 'b': 'ollama'})
                self.assertEqual([run['provider'] for run in report['runs']], ['heuristic', 'ollama'])
                self.assertTrue(all(run['pureProviderRun'] for run in report['runs']))
                factory.assert_called_once_with(settings.ollama)
                self.assertEqual(requester.call_count, 2)


if __name__ == '__main__':
    unittest.main()
