"""No-network tests of the full-match experiment boundary."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.observation import ArenaObservation
from aig.arena.ai.stepwise import OllamaArenaStepProvider, HeuristicArenaStepProvider, STEP_PROMPT_VERSION, CONTROL_VERSION
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_versions import artifact
from aig.arena.fullmatch_benchmark import RequestBudget, run_match, verify_match, pilot, SCHEDULE
from aig.ai.model_profiles import inference_configuration
from aig.arena.snapshots import canonical_json
from aig.settings import Settings


class FakeModel(OllamaArenaStepProvider):
    def __init__(self, outputs=()):
        super().__init__(Settings().ollama)
        self.outputs = list(outputs)
        self.calls = 0

    def request(self, messages, record):
        self.calls += 1
        record['metrics'] = dict(prompt_eval_count=100, eval_count=10)
        if self.outputs:
            return self.outputs.pop(0)
        obs = ArenaObservation(messages[0]['content'].removeprefix('ArenaObservation:\n'))
        return canonical_json(HeuristicArenaStepProvider().create_step(obs).to_dict())


class FullMatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exp = dict(benchmarkVersion='arena-benchmark-v3', controlVersion=CONTROL_VERSION,
                        observationVersion='arena-observation-v2', promptVersion=STEP_PROMPT_VERSION)
        for target in ('urllib.request.OpenerDirector.open', 'httpx.Client.send'):
            p = patch(target, side_effect=AssertionError('network forbidden'))
            p.start()
            self.addCleanup(p.stop)

    def run_one(self, provider, limit=400, **kwargs):
        budget = RequestBudget(limit)
        provider.before_request = budget.take
        result = run_match(self.root/'match', dict(blue='ollama', red='heuristic'),
                           dict(ollama=provider), self.exp, **kwargs)
        return result, budget

    def test_budget_denies_repair_without_counting_denial(self):
        p = FakeModel(['{}'])
        r, b = self.run_one(p, limit=1)
        self.assertEqual((p.calls, b.used), (1, 1))
        self.assertEqual(r['status'], 'request_ceiling')
        self.assertTrue(r['verification']['success'])
        self.assertEqual(r['turns'][0]['provider_requests'], 1)
        self.assertEqual(r['turns'][0]['repair_requests'], 0)
        self.assertEqual(r['turns'][0]['ap_unused'], 5)
        trace = json.loads((self.root/'match/command-trace.json').read_text())
        self.assertEqual(trace['entries'], [])

    def test_midturn_budget_preserves_prefix_and_exact_replay(self):
        p = FakeModel()
        r, b = self.run_one(p, limit=2)
        self.assertEqual(r['status'], 'request_ceiling')
        self.assertEqual(p.calls, 2)
        self.assertTrue(r['verification']['success'])
        self.assertEqual(r['turns'][0]['actions_executed'], 2)
        self.assertFalse(r['turns'][0]['explicit_early_end'])

    def test_full_offline_match_and_tampered_observation(self):
        r, b = self.run_one(FakeModel(), limit=1000)
        self.assertEqual(r['status'], 'completed')
        self.assertTrue(r['verification']['success'])
        self.assertGreater(r['player_turns'], 2)
        path = self.root/'match/turns/turn-0001/turn.json'
        row = json.loads(path.read_text())
        row['steps'][0]['observation_hash'] = 'tampered'
        path.write_text(json.dumps(row))
        self.assertFalse(verify_match(self.root/'match')['success'])

    def test_bound_and_provider_failure_are_results(self):
        r, _ = self.run_one(FakeModel(), turns=1)
        self.assertEqual(r['status'], 'turn_limit')
        self.assertEqual(r['global_turns'], 1)
        self.assertTrue(r['verification']['success'])

    def test_failed_repair_partial_match(self):
        r, _ = self.run_one(FakeModel(['{}', '{}']))
        self.assertEqual(r['error_category'], 'repair_failed')
        self.assertEqual(r['status'], 'failed')
        self.assertTrue(r['verification']['success'])

    def test_source_guard_before_transport(self):
        b = RequestBudget(400, lambda: (_ for _ in ()).throw(ArenaProviderError('source_mutation')))
        with self.assertRaises(ArenaProviderError):
            b.take()
        self.assertEqual(b.used, 0)

    def test_frozen_contracts_remain_distinct(self):
        self.assertEqual(artifact('arena-benchmark-v3')['default_turns'], 100)
        self.assertEqual(artifact('arena-benchmark-v2')['scope'], 'rest of one player turn from a frozen probe state')

    def scheduled(self, errors):
        def factory(settings, name):
            return SimpleNamespace(name=name, configuration=lambda: inference_configuration(name, settings),
                                   prompt_version=STEP_PROMPT_VERSION, schema_version='arena-turn-plan-schema-v1')
        def preflight(provider, name, observation, **kwargs):
            provider.before_request()
            return None, dict(success=True, actual_provider=name, fallback_used=False, provider_requests=1)
        def match(*args, **kwargs):
            category = errors.pop(0) if errors else None
            return dict(status='failed' if category else 'completed', error_category=category)
        with patch('aig.arena.fullmatch_benchmark.checked_step', side_effect=preflight), \
             patch('aig.arena.fullmatch_benchmark.run_match', side_effect=match) as mocked:
            report = pilot(self.root/'pilot', provider_factory=factory)
        return report, mocked

    def test_independent_failures_continue_all_eight_no_retries(self):
        report, mocked = self.scheduled(['repair_failed'])
        self.assertEqual(mocked.call_count, 8)
        self.assertEqual(len(report['matches']), 8)
        self.assertEqual(report['requests'], dict(ollama=1, openai=1))
        assignments = [c.args[1] for c in mocked.call_args_list]
        self.assertEqual(assignments, [dict(blue=b, red=r) for _,b,r in SCHEDULE])

    def test_integrity_failure_stops_stage_b_and_other_provider(self):
        report, mocked = self.scheduled(['catalog_execution_defect'])
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(report['status'], 'hard_stop')
        self.assertEqual(sum(m['status']=='not_started' for m in report['matches']), 7)
        self.assertEqual(report['requests'], dict(ollama=1, openai=0))

    def test_ceiling_disables_only_affected_provider(self):
        report, mocked = self.scheduled(['request_ceiling'])
        self.assertEqual(mocked.call_count, 5)
        self.assertEqual(report['disabled'], dict(ollama='request_ceiling'))

    def test_cli_loads_effective_settings_without_inference(self):
        from aig.arena.fullmatch_benchmark import main
        from contextlib import redirect_stdout
        from io import StringIO
        settings = Settings()
        with patch('aig.arena.fullmatch_benchmark.load_settings', return_value=settings), \
             patch('aig.arena.fullmatch_benchmark.pilot', return_value=dict(status='complete', requests={})) as run, \
             redirect_stdout(StringIO()):
            self.assertEqual(main(['--output', str(self.root/'cli')]), 0)
        self.assertIs(run.call_args.kwargs['settings'], settings)


if __name__ == '__main__':
    unittest.main()
