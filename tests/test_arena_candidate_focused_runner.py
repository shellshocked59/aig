import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('candidate_focused_runner', Path(__file__).parents[1]/'scripts/arena-candidate-focused.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class FakeProvider(runner.OpenAICandidateProvider):
    def request(self, messages, record):
        record['metrics'] = dict(input_tokens=10, cached_input_tokens=0, output_tokens=5, reasoning_tokens=0, total_tokens=15)
        return json.dumps(dict(schema_version='arena-turn-plan-schema-v2', actions=[dict(type='end_turn')]))


class RunnerTests(unittest.TestCase):
    def test_budget_and_corruption_deny_before_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = runner.Ledger(Path(tmp)/'ledger', 86)
            trial = dict(trial='test', control_mode='strict', request_ceiling=86)
            for i in range(86):
                ledger.reserve(trial, 'hash', i)
            with self.assertRaisesRegex(runner.IntegrityError, 'global request ceiling'):
                ledger.reserve(trial, 'hash', 86)
            self.assertEqual(len(ledger.rows), 86)
            ledger.path.write_text('')
            with self.assertRaisesRegex(runner.IntegrityError, 'accounting corruption'):
                ledger.reserve(trial, 'hash', 86)

    def test_trial_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = runner.Ledger(Path(tmp)/'ledger', 86)
            trial = dict(trial='test', control_mode='strict', request_ceiling=2)
            ledger.reserve(trial, 'hash', 0)
            ledger.reserve(trial, 'hash', 1)
            with self.assertRaisesRegex(runner.IntegrityError, 'trial request ceiling'):
                ledger.reserve(trial, 'hash', 2)

    def test_schedule_persistence_replay_analysis_and_no_overwrite(self):
        from aig.settings import Settings
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner, 'load_settings', return_value=Settings()), patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
            output = Path(tmp)/'run'
            runner.run(output, factory=lambda settings, trial: FakeProvider(settings, client=object(), step=trial['control_mode']=='stepwise'))
            runner.analyze(output)
            report = json.loads((output/'analysis.json').read_text())
            self.assertEqual((report['trials'], report['requests']), (24,24))
            for control in report['controls'].values():
                self.assertEqual(control['stop_counts']['INTENTIONAL_END_TURN'],8)
                self.assertEqual(control['replans'],0)
            with self.assertRaises(FileExistsError):
                runner.run(output, factory=lambda *args: None)
            (output/'AP-001-strict.json').write_text('{}')
            with self.assertRaisesRegex(runner.IntegrityError, 'evidence corruption'):
                runner.analyze(output)


if __name__ == '__main__':
    unittest.main()
