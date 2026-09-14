import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aig.arena import bounded_replan_comparison as bench
from aig.arena.ai.contracts import ArenaTurnPlan, AttackAction, SnipeAction, MoveAction, ArenaPosition
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_versions import frozen_probe
from aig.arena.snapshots import digest, to_snapshot
from aig.arena.ai.observation import build_observation
from tests.test_arena_bounded_replan import TransportSequence, blocked


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = bench.historical_audit()
        cls.cases = bench.select_cases(cls.audit)

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        guard = patch('socket.socket.connect', side_effect=AssertionError('live forbidden'))
        guard.start(); self.addCleanup(guard.stop)

    def plan(self, count=1, probe='snipe_vs_basic', ceilings=None):
        state = frozen_probe(probe)
        cases = [dict(pair_id=f'pair-{i:03d}', snapshot=to_snapshot(state), initial_state_hash=bench.state_hash(state),
            initial_observation_hash=build_observation(state).hash, player_id=state.active_player_id,
            initial_ap=state.action_points_remaining, category='test') for i in range(1, count+1)]
        profile, config = bench.resolve_model_profile('openai', 'luna-config-v1')
        data = dict(version=bench.VERSION, recipe=bench.recipe(), recipe_hash=digest(bench.recipe()),
            source_files=bench.inventory(), cases=cases, fixture_hash=digest(cases), provider='openai',
            model_profile=profile, model_configuration=config, intended_turns=count*2,
            prompt_hash=bench.hashlib.sha256(bench.resolve_prompt('arena-turn-prompt-v1')[1].encode()).hexdigest(),
            wire_schema_hash=digest(bench.openai_turn_plan_schema()), evidence_sha256={},
            transport=dict(timeout_seconds=bench.Settings().openai.timeout_seconds),
            ceilings=ceilings or dict(full_turn=count*2, bounded_replan=count*4, total=count*6))
        bench.write(self.root/'plan.json', bench.seal(data))
        return self.root/'plan.json'

    def run_fake(self, strict, bounded, **kwargs):
        plan = self.plan(**kwargs)
        result = bench.run(plan, self.root/'run', offline=True,
            provider_factory=lambda settings, case, arm: TransportSequence(*(strict if arm == 'full_turn' else bounded)))
        return result

    def test_historical_complete_selection_and_identity(self):
        self.assertEqual(len(self.audit['cases']), 184)
        self.assertEqual(self.cases, bench.select_cases(self.audit))
        self.assertEqual(len({r['initial_state_hash'] for r in self.cases}), 42)
        self.assertEqual(sum(r.get('replan_eligible', False) for r in self.cases[:14]), 9)
        for row in self.audit['cases']:
            if row['invalid_reason']:
                self.assertFalse(row['terminal_before_invalidity'])
                self.assertEqual(row['stale_suffix_length'], len(row['historical_plan']['actions'])-row['invalid_index'])

    def test_clean_short_plan_and_pair_identity(self):
        result = self.run_fake([ArenaTurnPlan()], [ArenaTurnPlan()])
        self.assertEqual(result['status'], 'complete')
        a, b = result['runs']
        for key in ('initial_state_hash', 'player_id', 'ap', 'pair_id'):
            self.assertEqual(a[key], b[key])
        for row in (a, b):
            self.assertEqual(row['actual_attempts'], 1)
            self.assertEqual(row['metrics']['short_plan_unused_AP'], 5)
            self.assertFalse(row['metrics']['replan_triggered'])
            self.assertTrue(row['replay_verified'])

    def test_recovery_metrics_and_freshness(self):
        replacement = ArenaTurnPlan((AttackAction('actor', 'enemy2'),)*3)
        result = self.run_fake([blocked()], [blocked(), replacement])
        a, b = (r['metrics'] for r in result['runs'])
        self.assertEqual((a['ap_executed'], a['ap_unused'], b['ap_executed'], b['ap_recovered']), (2, 3, 5, 3))
        self.assertNotEqual(b['initial']['observation_hash'], b['replacement']['observation_hash'])
        self.assertEqual(b['ap_at_replan'], 3)
        self.assertEqual(b['total_tokens'], 30)
        self.assertAlmostEqual(b['provider_latency_seconds'], sum(w['inference']['attempts'][0]['wall_clock_seconds'] for w in result['runs'][1]['waves']))
        self.assertTrue(all(r['replay_verified'] for r in result['runs']))

    def test_second_invalid_no_third_wave(self):
        replacement = ArenaTurnPlan((SnipeAction('actor', 'enemy'),))
        result = self.run_fake([blocked()], [blocked(), replacement])
        b = result['runs'][1]['metrics']
        self.assertEqual(result['status'], 'complete')
        self.assertTrue(b['second_execution_invalidity'])
        self.assertEqual((b['provider_attempts'], b['ap_recovered']), (2, 0))

    def test_static_repairs_independent(self):
        result = self.run_fake(['{', blocked()], ['{', blocked(), '{', ArenaTurnPlan()])
        b = result['runs'][1]['metrics']
        self.assertEqual((b['provider_attempts'], b['static_repair_attempts'], b['static_repair_successes']), (4, 2, 2))
        self.assertTrue(b['initial']['static_invalid']); self.assertTrue(b['replacement']['static_invalid'])
        self.assertFalse(b['initial']['first_response_valid'])

    def test_provider_failures_continue_and_partial_replay(self):
        result = self.run_fake([ArenaProviderError('transport_failure')],
            [blocked(), ArenaProviderError('timeout')], count=2)
        self.assertEqual(result['status'], 'complete_with_provider_failures')
        self.assertEqual(len(result['runs']), 4)
        for row in result['runs']:
            self.assertTrue(row['replay_verified'])
            self.assertFalse(row['metrics']['completed_turn'])
        b = result['runs'][1]
        self.assertEqual(b['metrics']['ap_executed'], 2)
        self.assertEqual(b['metrics']['ap_unused'], 3)
        snapshot = json.loads((self.root/'run/bounded/pair-001/final-snapshot.json').read_text())
        self.assertEqual(snapshot['active_player_id'], 'blue')

    def test_repair_exhaustion_continues(self):
        result = self.run_fake(['{', '{'], [ArenaTurnPlan()], count=2)
        self.assertEqual(len(result['runs']), 4)
        self.assertEqual(result['runs'][0]['metrics']['provider_failure'], 'repair_failed')

    def test_arm_and_total_ceiling_before_transport(self):
        for ceilings in (dict(full_turn=2, bounded_replan=1, total=10),
                         dict(full_turn=2, bounded_replan=4, total=2)):
            with self.subTest(ceilings=ceilings):
                root = self.root / str(ceilings['total']); root.mkdir()
                previous = self.root; self.root = root
                result = self.run_fake([blocked()], [blocked(), ArenaTurnPlan()], ceilings=ceilings)
                self.root = previous
                self.assertEqual(result['status'], 'ceiling_stop')
                for arm in (*bench.ARMS, 'total'):
                    self.assertLessEqual(result['requests'][arm], ceilings[arm])
                self.assertEqual(result['runs'][-1]['metrics']['ap_executed'], 2)

    def test_source_freeze_before_any_transport(self):
        plan = self.plan()
        with patch.object(bench, 'inventory', return_value={}):
            with self.assertRaisesRegex(bench.IntegrityError, 'source drift'):
                bench.run(plan, self.root/'bad', offline=True, provider_factory=lambda *a: self.fail('constructed provider'))

    def test_source_drift_mid_turn_preserves_trace(self):
        plan = self.plan()
        class Drift(TransportSequence):
            def request(inner, messages, record):
                result = super(Drift, inner).request(messages, record)
                patcher = patch.object(bench, 'inventory', return_value={})
                patcher.start(); self.addCleanup(patcher.stop)
                return result
        result = bench.run(plan, self.root/'run', offline=True, provider_factory=lambda *args: Drift(ArenaTurnPlan()))
        self.assertEqual(result['status'], 'hard_stop')
        self.assertEqual(len(result['runs']), 1)

    def test_wrong_provider_and_accounting_hard_stop(self):
        plan = self.plan()
        class Wrong(TransportSequence):
            name = 'ollama'
        result = bench.run(plan, self.root/'wrong', offline=True, provider_factory=lambda *a: Wrong())
        self.assertEqual(result['status'], 'hard_stop')
        class Corrupt(TransportSequence):
            @property
            def last_trace(self):
                trace = super().last_trace
                trace['attempts'] = []
                return trace
        result = bench.run(plan, self.root/'corrupt', offline=True, provider_factory=lambda *a: Corrupt(ArenaTurnPlan()))
        self.assertEqual(result['status'], 'hard_stop')
        self.assertEqual(len(result['runs']), 1)

    def test_replay_mismatch_hard_stop(self):
        plan = self.plan()
        with patch.object(bench, 'replay', side_effect=ValueError('replay mismatch')):
            result = bench.run(plan, self.root/'run', offline=True, provider_factory=lambda *a: TransportSequence(ArenaTurnPlan()))
        self.assertEqual(result['status'], 'hard_stop')
        self.assertEqual(len(result['runs']), 1)

    def test_terminal_initial_no_replan(self):
        win = ArenaTurnPlan((AttackAction('actor', 'red-core'),)*3)
        result = self.run_fake([win], [win], probe='winning_core_line')
        self.assertEqual(result['status'], 'complete')
        for row in result['runs']:
            self.assertIsNotNone(row['metrics']['terminal_result'])
            self.assertFalse(row['metrics']['replan_triggered'])
            self.assertTrue(row['replay_verified'])

    def test_terminal_replacement(self):
        bad = ArenaTurnPlan((MoveAction('actor', ArenaPosition(0, 2)),))
        win = ArenaTurnPlan((AttackAction('actor', 'red-core'),)*2)
        result = self.run_fake([bad], [bad, win], probe='winning_core_line')
        self.assertEqual(result['status'], 'complete')
        row = result['runs'][1]
        self.assertTrue(row['metrics']['terminal_replacement'])
        self.assertEqual(row['metrics']['ap_recovered'], 1)
        self.assertTrue(row['replay_verified'])

    def test_unknown_tokens_remain_unset(self):
        result = self.run_fake([ArenaTurnPlan()], [ArenaTurnPlan()])
        self.assertIsNone(result['runs'][0]['metrics']['cached_input_tokens'])
        comparison = bench.summarize(result)
        self.assertEqual(comparison['headlines']['full_turn']['mean_provider_attempts'], 1)
        self.assertEqual(comparison['pairs'][0]['delta']['ap_executed'], 0)
        self.assertIsNone(comparison['pricing'])


if __name__ == '__main__':
    unittest.main()
