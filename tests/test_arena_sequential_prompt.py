"""Deterministic contracts/mechanics, never assertions about model competence."""
from dataclasses import replace
import json
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from aig.arena.ai import sequential_prompt as prompt
from aig.arena import sequential_literacy as study
from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION, action_from_dict
from aig.arena.ai.observation import build_observation, ArenaObservation
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController
from aig.arena.ai.prompts import resolve_prompt as historical_prompt
from aig.arena.ai.stepwise import STEP_PROMPT_VERSION
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.sequential_prompt import OpenAISequentialProvider, OllamaSequentialProvider
from aig.arena.tactical_literacy_fixtures import fixture, action, tile
from aig.arena.mechanics_oracle import evaluate
from aig.arena.snapshots import to_snapshot, from_snapshot, state_hash
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.state import UnitType as U
from aig.ai.model_profiles import apply_model_profile
from aig.settings import Settings


def encoded(actions):
    return json.dumps(dict(schema_version=PLAN_SCHEMA_VERSION, actions=actions))


class SequentialTests(unittest.TestCase):
    def setUp(self):
        guard = patch.object(socket.socket, 'connect', side_effect=AssertionError('live forbidden'))
        guard.start()
        self.addCleanup(guard.stop)
        from aig.arena.ap_budget_literacy import NEW_ADDITIONS
        from arena_candidate_scope import CANDIDATE_ADDITIONS
        original_hashes = study.frozen.hashes
        scope = patch.object(study.frozen, 'hashes', side_effect=lambda: {
            p: h for p, h in original_hashes().items() if p not in NEW_ADDITIONS and p not in CANDIDATE_ADDITIONS})
        scope.start()
        self.addCleanup(scope.stop)
        self.suite = study.verify_suite()
        self.probes = {p['id']: p for p in self.suite['probes']}
        self.settings = apply_model_profile(Settings(), 'openai', 'luna-config-v1')

    def provider(self, replies):
        provider = OpenAISequentialProvider(replace(self.settings.openai, api_key='offline'),
            client=object(), prompt_version=prompt.PROMPT_VERSION)
        replies = iter(replies)
        def request(messages, record):
            record['metrics'] = dict(input_tokens=10, output_tokens=5, total_tokens=15, cached_input_tokens=0)
            value = next(replies)
            if isinstance(value, Exception):
                raise value
            return value
        provider.request = request
        return provider

    def test_immutable_snapshot_and_ancestry(self):
        self.assertEqual(dict(prompt.PROMPT_HASHES), {
            'arena-turn-prompt-v1': '5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7',
            'arena-turn-prompt-v2': '5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29',
            'arena-turn-prompt-v3': '5a517164a8f799b2f5e9b2f9a56103fb61e4ef690d2b7e6efd53412b08dce182',
            'arena-turn-prompt-v4': 'ede7f2defc81aa099fd8d1e2e4acbdd948389790101afc3d4b75c05342b16b35'})
        from aig.arena.ai.prompts import SYSTEM_PROMPT
        restored = prompt.PROMPT.replace(prompt.SEQUENCE_GUIDANCE, '').replace(prompt.AP_GUIDANCE,
            'You have up to 5 shared Action Points, bounded by action_points_remaining.')
        self.assertEqual(restored, SYSTEM_PROMPT)
        self.assertNotIn('FIREBALL HAS FRIENDLY FIRE', prompt.PROMPT)
        self.assertEqual(prompt.PROMPT, (study.ROOT / 'tests/fixtures/arena-turn-prompt-v4.txt').read_text())

    def test_defaults_contract_and_repair_unchanged(self):
        for version in (None, 'latest'):
            self.assertEqual(prompt.resolve_prompt(version)[0], 'arena-turn-prompt-v1')
            self.assertEqual(historical_prompt(version)[0], 'arena-turn-prompt-v1')
        for name in ('openai', 'ollama'):
            self.assertEqual(create_arena_turn_provider(Settings(), name).prompt_version, 'arena-turn-prompt-v1')
        self.assertEqual(STEP_PROMPT_VERSION, 'arena-step-prompt-v1')
        self.assertIs(OpenAISequentialProvider.parse_plan, ModelArenaTurnProvider.parse_plan)
        self.assertIs(OpenAISequentialProvider.repair_feedback, ModelArenaTurnProvider.repair_feedback)
        self.assertIs(prompt.ExperimentalBoundedReplanController.run_turn, ArenaBoundedReplanController.run_turn)
        with self.assertRaises(ValueError):
            ArenaBoundedReplanController(self.provider([]))
        with self.assertRaises(ValueError):
            prompt.resolve_prompt('arena-turn-prompt-v99')

    def test_provider_wire_changes_only_prompt_including_repair(self):
        observation = build_observation(fixture(ap=3))
        for kind in ('openai', 'ollama'):
            captured = []
            for version in ('arena-turn-prompt-v1', prompt.PROMPT_VERSION):
                calls = []
                outputs = iter(['bad', encoded([])])
                if kind == 'openai':
                    def send(**kwargs):
                        calls.append(kwargs)
                        return NS(status='completed', error=None, usage=None, output=[NS(type='message',
                            role='assistant', status='completed', content=[NS(type='output_text', text=next(outputs))])])
                    provider = OpenAISequentialProvider(replace(self.settings.openai, api_key='offline'),
                        client=NS(responses=NS(create=send)), prompt_version=version)
                else:
                    def send(url, payload, timeout):
                        calls.append(json.loads(payload))
                        return json.dumps(dict(message=dict(content=next(outputs)), done=True))
                    provider = OllamaSequentialProvider(Settings().ollama, requester=send, prompt_version=version)
                self.assertEqual(provider.create_turn_plan(observation), ArenaTurnPlan())
                self.assertEqual(len(calls), 2)
                for call in calls:
                    if kind == 'openai':
                        self.assertEqual(call.pop('instructions'), prompt.PROMPTS[version])
                    else:
                        self.assertEqual(call['messages'][0]['content'], prompt.PROMPTS[version])
                        call['messages'] = call['messages'][1:]
                captured.append(calls)
            self.assertEqual(captured[0], captured[1])

    def test_partial_ap_and_short_plan(self):
        self.assertIn('complete AP budget', prompt.PROMPT)
        self.assertIn('subtract its cost before adding another', prompt.PROMPT)
        self.assertIn('You need not spend', prompt.PROMPT)
        for ap in (1, 2, 3, 4):
            obs = build_observation(fixture(ap=ap, enemy=(3, 2)))
            self.assertEqual(ArenaObservation.from_dict(obs.to_dict()), obs)
            self.assertEqual(parse_turn_plan(encoded([]), obs), ArenaTurnPlan())
            self.assertEqual(parse_turn_plan(encoded([action('attack')]), obs).ap_cost, 1)
        obs = build_observation(fixture(ap=3))
        with self.assertRaises(ArenaProviderError) as caught:
            parse_turn_plan(encoded([action('snipe')] * 2), obs)
        self.assertEqual(caught.exception.category, 'ap_budget')

    def test_down_finish_revive_transitions(self):
        self.assertIn('no longer an ACTIVE target', prompt.PROMPT)
        self.assertIn('cannot be a later actor or target', prompt.PROMPT)
        self.assertIn('revived unit may act later this turn', prompt.PROMPT)
        p = self.probes['MULTI-004']
        state = from_snapshot(p['initial_state'])
        state.action_points_remaining = 3
        for later in ('attack', 'snipe'):
            result = evaluate(to_snapshot(state), [action('attack'), action(later)])
            self.assertEqual(result['failure']['index'], 1)
            self.assertTrue(result['steps'][0]['affected'][0]['guaranteed_down'])
        p = self.probes['DOWNED-002']
        state = from_snapshot(p['initial_state'])
        state.action_points_remaining = 2
        result = evaluate(to_snapshot(state), [action('finish'), action('attack')])
        self.assertEqual(result['steps'][0]['affected'][0]['status_after'], 'removed')
        self.assertEqual(result['failure']['index'], 1)
        p = self.probes['REVIVE-002']
        result = evaluate(p['initial_state'], p['reference_sequence'])
        self.assertIsNone(result['failure'])
        self.assertEqual(result['steps'][0]['affected'][0]['status_after'], 'active')
        self.assertEqual(len(result['steps']), 2)

    def test_position_push_los_terminal(self):
        self.assertIn('from the updated board', prompt.PROMPT)
        self.assertIn('append no later actions', prompt.PROMPT)
        p = self.probes['POSITION-002']
        self.assertIsNotNone(evaluate(p['initial_state'], [action('snipe')])['failure'])
        self.assertIsNone(evaluate(p['initial_state'], p['reference_sequence'])['failure'])
        s = fixture(U.KNIGHT, hp=18, ap=2, actor=(2, 2), enemy=(3, 2))
        result = evaluate(to_snapshot(s), [action('shield_bash'), action('attack')])
        self.assertEqual(result['steps'][0]['affected'][0]['position_after'], dict(x=4, y=2))
        self.assertEqual(result['failure']['index'], 1)
        s = fixture(ap=3, actor=(1, 1), enemy=(5, 1))
        tile(s, (3, 2), blocked=True)
        self.assertIsNone(evaluate(to_snapshot(s), [action('snipe')])['failure'])
        result = evaluate(to_snapshot(s), [action('move', position=(2, 3)), action('snipe')])
        self.assertEqual(result['failure']['index'], 1)
        self.assertIn('line of sight', result['failure']['reason'].lower())
        p = self.probes['CORE-002']
        result = evaluate(p['initial_state'], p['reference_sequence'] * 2)
        self.assertTrue(result['terminal'])
        self.assertEqual(result['ignored_terminal_suffix'], 1)

    def test_strict_and_bounded_with_partial_recovery_replay(self):
        p = self.probes['MULTI-004']
        provider = self.provider([encoded(p['reference_sequence'])])
        sim = ArenaSimulation(from_snapshot(p['initial_state']))
        plan, telemetry = study.checked_plan(provider, 'openai', build_observation(sim.state))
        self.assertTrue(telemetry['success'])
        result = execute_arena_turn(sim.state, plan, execute_command=sim.execute)
        self.assertIsNotNone(result.invalid_action)
        provider = self.provider([encoded(p['reference_sequence']), encoded([])])
        sim = ArenaSimulation(from_snapshot(p['initial_state']))
        result = prompt.ExperimentalBoundedReplanController(provider).run_turn(sim).to_dict()
        self.assertTrue(result['replan_used'])
        self.assertEqual(result['ap_before_replan'], 1)
        self.assertFalse(result['fallback_used'])
        self.assertEqual(state_hash(replay(sim.trace()).state), state_hash(sim.state))

    def test_binding_baseline_analysis(self):
        binding, suite = study.verify()
        self.assertEqual(len(binding['cohort']), 122)
        self.assertEqual(binding['excluded_slots'], ['03-POSITION-002', '03-POSITION-003', '03-POSITION-004', '03-REVIVE-004'])
        result = study.analyze_arm(study.BASELINE, binding['cohort'], suite)
        self.assertEqual(result['first_response_errors'], {'ap_budget': 18})
        self.assertEqual(result['counts']['stale_downed_plans'], 15)
        self.assertEqual(result['counts']['blocked_los_plans'], 2)
        self.assertEqual(result['counts']['requests'], 140)

    def test_independent_failures_repair_and_accounting(self):
        b, suite = study.verify()
        b = dict(b, cohort=b['cohort'][:3])
        provider = self.provider(['bad', 'bad', ArenaProviderError('timeout'), encoded([])])
        with tempfile.TemporaryDirectory() as tmp, patch.object(study, 'verify', return_value=(b, suite)):
            out = Path(tmp) / 'run'
            rows = study.run(out, provider=provider)
            self.assertEqual(len(rows), 3)
            self.assertEqual([r['classification'] for r in rows][:2], ['static invalidity', 'provider failure'])
            self.assertEqual(study.read(out / 'summary.json')['provider_requests'], 4)
            with self.assertRaises(FileExistsError):
                study.run(out, provider=provider)

    def test_source_drift_denied_before_transport(self):
        b, suite = study.verify()
        provider = self.provider([])
        with tempfile.TemporaryDirectory() as tmp, patch.object(study, 'verify', return_value=(b, suite)):
            with patch.object(study.frozen, 'hashes', return_value={}):
                out = Path(tmp) / 'run'
                with self.assertRaises(RuntimeError):
                    study.run(out, provider=provider)
                self.assertEqual(study.read(out / 'request-ledger.json'), [])

    def test_ceiling_denies_repair_without_extra_transport(self):
        b, suite = study.verify()
        provider = self.provider(['bad'])
        with tempfile.TemporaryDirectory() as tmp, patch.object(study, 'verify', return_value=(b, suite)):
            with patch.object(study, 'CEILING', 1):
                out = Path(tmp) / 'run'
                with self.assertRaises(RuntimeError):
                    study.run(out, provider=provider)
                self.assertEqual(len(study.read(out / 'request-ledger.json')), 1)
                self.assertEqual(study.read(out / 'stopped.json')['reason'], 'hard request ceiling reached')
                self.assertEqual(len(study.read(out / b['cohort'][0] / 'attempt-outputs.json')), 1)

    def test_binding_corruption_rejected(self):
        wrapper = study.read(study.BINDING)
        wrapper['payload']['cohort'] = []
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'corrupt.json'
            study.frozen.write(path, wrapper)
            with self.assertRaisesRegex(ValueError, 'binding/source/contract drift'):
                study.verify(path)

    def test_offline_fake_transport_cannot_be_live_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'candidate'
            candidate.mkdir()
            study.frozen.write(candidate / 'binding.json', study.read(study.BINDING))
            study.frozen.write(candidate / 'manifest.json', dict(mode='offline-scripted'))
            with self.assertRaisesRegex(ValueError, 'offline run cannot be live'):
                study.compare(candidate, Path(tmp) / 'analysis')


if __name__ == '__main__':
    unittest.main()
