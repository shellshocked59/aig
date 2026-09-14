import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from aig.arena.ai.bounded_replan import ArenaBoundedReplanController
from aig.arena.ai.contracts import ArenaTurnPlan, AttackAction, action_command
from aig.arena.ai.observation import build_observation
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.benchmark_versions import frozen_probe
from aig.arena.bounded_replan_recovery_smoke import (
    ScriptedFirstWaveThenDelegateProvider, expected_boundary, scripted_plan, prepare, run, verify)
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json
from aig.settings import Settings


class FakeLuna(OpenAIArenaTurnProvider):
    def __init__(self, *responses):
        super().__init__(Settings().openai, client=object())
        self.responses = iter(responses)
        self.messages = []

    def request(self, messages, record):
        self.messages.append(deepcopy(messages))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result if isinstance(result, str) else canonical_json(result.to_dict())


def replacement(count=3):
    return ArenaTurnPlan((AttackAction('actor', 'enemy2'),)*count)


class RecoverySmokeTests(unittest.TestCase):
    def setUp(self):
        # Fail closed on any accidental network use, including non-OpenAI transports.
        guard = patch('socket.socket.connect', side_effect=AssertionError('network forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def case(self, *responses, state=None):
        delegate = FakeLuna(*responses)
        provider = ScriptedFirstWaveThenDelegateProvider(delegate)
        sim = ArenaSimulation(state or frozen_probe('snipe_vs_basic'))
        turn = ArenaBoundedReplanController(provider, fallback=False).run_turn(sim).to_dict()
        self.assertEqual(replay(sim.trace()).trace(), sim.trace())
        return sim, turn, provider, delegate

    def test_script_is_static_and_individually_legal_at_start(self):
        initial, execution, fresh, sim = expected_boundary()
        self.assertEqual(parse_turn_plan(canonical_json(scripted_plan().to_dict()), initial), scripted_plan())
        for action in scripted_plan().actions:
            isolated = ArenaSimulation(frozen_probe('snipe_vs_basic'))
            isolated.execute(action_command(action, 'blue'))
        self.assertEqual((execution['actions_executed'], execution['ap_spent'], execution['ap_unused']), (1, 2, 3))
        self.assertEqual(execution['invalid_action']['index'], 1)
        self.assertEqual(execution['stale_suffix_count'], 2)
        self.assertNotEqual(initial.hash, fresh.hash)
        self.assertEqual(fresh.to_dict()['action_points_remaining'], 3)
        before = initial.to_dict()['enemy_team']['units'][0]
        after = fresh.to_dict()['enemy_team']['units'][0]
        self.assertEqual((before['id'], before['hp'], before['status']), ('enemy', 8, 'active'))
        self.assertEqual((after['id'], after['hp'], after['status'], after['x'], after['y']), ('enemy', 0, 'downed', 5, 2))
        actor = fresh.to_dict()['own_team']['units'][0]
        self.assertEqual((actor['x'], actor['y']), (1, 2))
        self.assertIn('enemy', initial.to_dict()['own_team']['units'][0]['actions']['snipe'])
        self.assertNotIn('enemy', actor['actions']['snipe'])
        self.assertNotIn('enemy', actor['actions']['attack'])
        self.assertNotIn('enemy', actor['actions']['finish'])

    def test_fresh_delegate_and_clean_replay(self):
        sim, turn, provider, delegate = self.case(replacement())
        self.assertTrue(verify(sim, turn, provider)['passed'])
        self.assertEqual((provider.calls, provider.attempts, len(delegate.messages)), (2, 1, 1))
        self.assertEqual(delegate.messages[0][0]['content'], 'ArenaObservation:\n'+expected_boundary()[2].canonical)
        self.assertEqual(turn['waves'][1]['command_start'], 1)
        self.assertEqual(turn['commands_executed'][-1]['type'], 'arena_end_turn')
        self.assertFalse(hasattr(delegate, 'before_request'))

    def test_partial_budget_and_normal_static_repair(self):
        obs = expected_boundary()[2]
        self.assertEqual(parse_turn_plan(canonical_json(replacement().to_dict()), obs), replacement())
        with self.assertRaises(ArenaProviderError) as error:
            parse_turn_plan(canonical_json(replacement(4).to_dict()), obs)
        self.assertEqual(error.exception.category, 'ap_budget')
        sim, turn, provider, delegate = self.case(replacement(4), replacement())
        self.assertTrue(verify(sim, turn, provider)['passed'])
        self.assertEqual((turn['static_repairs'], turn['provider_requests'], turn['planning_waves']), (1, 2, 2))
        self.assertEqual(delegate.messages[0][0], delegate.messages[1][0])

    def test_exhausted_repair_and_transport_failure_no_fallback(self):
        for responses, attempts in ((('{', '{'), 2), ((ArenaProviderError('transport_failure'),), 1)):
            sim, turn, provider, delegate = self.case(*responses)
            self.assertEqual(provider.attempts, attempts)
            self.assertFalse(turn['fallback_used'])
            self.assertFalse(verify(sim, turn, provider)['passed'])
            self.assertEqual(len(sim.trace()['entries']), 1)

    def test_second_execution_invalidity_ends_turn_no_third_wave(self):
        plan = ArenaTurnPlan((AttackAction('actor', 'enemy2'), AttackAction('actor', 'enemy')))
        sim, turn, provider, delegate = self.case(plan)
        self.assertIsNotNone(turn['waves'][1]['invalid_action'])
        self.assertTrue(verify(sim, turn, provider)['passed'])
        self.assertEqual((provider.calls, provider.attempts, len(delegate.messages)), (2, 1, 1))
        self.assertEqual(turn['commands_executed'][-1]['type'], 'arena_end_turn')

    def test_terminal_replacement_no_end_turn(self):
        state = frozen_probe('snipe_vs_basic')
        state.units['enemy2'].hp = 1  # Offline terminal edge case only; live fixture stays frozen.
        sim, turn, provider, _ = self.case(replacement(1), state=state)
        self.assertEqual(turn['terminal_result'], 'blue')
        self.assertFalse(any(c['type'] == 'arena_end_turn' for c in turn['commands_executed']))
        self.assertEqual(provider.attempts, 1)

    def test_hard_ceiling_denies_third_reservation(self):
        class OverRequester(FakeLuna):
            def create_turn_plan(self, observation):
                for _ in range(3):
                    self.before_request()
                raise AssertionError('third request escaped')
        provider = ScriptedFirstWaveThenDelegateProvider(OverRequester())
        turn = ArenaBoundedReplanController(provider, fallback=False).run_turn(
            ArenaSimulation(frozen_probe('snipe_vs_basic'))).to_dict()
        self.assertEqual((provider.attempts, turn['provider_requests'], turn['error_category']), (2, 2, 'request_ceiling'))

    def test_artifacts_offline_and_no_rerun(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)/'evidence'
            manifest = prepare(root)
            self.assertEqual(manifest['request_ceiling'], 2)
            report = run(root, settings=Settings(), provider_factory=lambda *args: FakeLuna(replacement()))
            self.assertEqual(report['status'], 'pass')
            self.assertTrue(report['stronger_pass'])
            self.assertEqual(replay(json.loads((root/'commands.json').read_text())).trace(),
                             json.loads((root/'commands.json').read_text()))
            for name in ('manifest.json', 'initial-state.json', 'scripted-plan.json', 'initial-execution.json',
                         'replan-observation.json', 'luna-inference.jsonl', 'replacement-plan.json',
                         'command-trace.jsonl', 'final-state.json', 'offline-verification.json', 'report.json'):
                self.assertTrue((root/name).is_file(), name)
            with self.assertRaises(FileExistsError):
                run(root, settings=Settings(), provider_factory=lambda *args: self.fail('rerun forbidden'))


if __name__ == '__main__':
    unittest.main()
