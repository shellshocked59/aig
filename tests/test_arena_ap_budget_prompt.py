"""Deterministic contracts/mechanics, never assertions about model competence."""
from dataclasses import replace
import json
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from aig.arena.ai import ap_budget_prompt as prompt
from aig.arena import ap_budget_literacy as study
from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION, action_from_dict
from aig.arena.ai.observation import build_observation, ArenaObservation
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController
from aig.arena.ai.prompts import resolve_prompt as historical_prompt
from aig.arena.ai.stepwise import STEP_PROMPT_VERSION
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.ap_budget_prompt import OpenAIAPBudgetProvider, OllamaAPBudgetProvider
from aig.arena.tactical_literacy_fixtures import fixture, action, tile
from aig.arena.mechanics_oracle import evaluate
from aig.arena.snapshots import to_snapshot, from_snapshot, state_hash
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.state import UnitType as U
from aig.ai.model_profiles import apply_model_profile
from aig.settings import Settings


def encoded(actions):
    return json.dumps(dict(schema_version=PLAN_SCHEMA_VERSION, actions=actions))


class APBudgetTests(unittest.TestCase):
    def setUp(self):
        guard = patch.object(socket.socket, 'connect', side_effect=AssertionError('live forbidden'))
        guard.start()
        self.addCleanup(guard.stop)
        from arena_candidate_scope import CANDIDATE_ADDITIONS
        original_hashes = study.frozen.hashes
        scope = patch.object(study.frozen, 'hashes', side_effect=lambda: {
            p: h for p, h in original_hashes().items() if p not in CANDIDATE_ADDITIONS})
        scope.start()
        self.addCleanup(scope.stop)
        self.suite = study.verify_suite()
        self.probes = {p['id']: p for p in self.suite['probes']}
        self.settings = apply_model_profile(Settings(), 'openai', 'luna-config-v1')

    def provider(self, replies):
        provider = OpenAIAPBudgetProvider(replace(self.settings.openai, api_key='offline'),
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
                    provider = OpenAIAPBudgetProvider(replace(self.settings.openai, api_key='offline'),
                        client=NS(responses=NS(create=send)), prompt_version=version)
                else:
                    def send(url, payload, timeout):
                        calls.append(json.loads(payload))
                        return json.dumps(dict(message=dict(content=next(outputs)), done=True))
                    provider = OllamaAPBudgetProvider(Settings().ollama, requester=send, prompt_version=version)
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
        result = prompt.APBudgetBoundedReplanController(provider).run_turn(sim).to_dict()
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


    def test_exact_ancestry_snapshot_hashes_and_exclusions(self):
        from aig.arena.ai.prompts import SYSTEM_PROMPT
        from aig.arena.ai.sequential_prompt import PROMPT_HASHES as old
        self.assertEqual(prompt.PROMPT.replace(prompt.AP_GUIDANCE, prompt.ORIGINAL_AP), SYSTEM_PROMPT)
        self.assertEqual({v: prompt.PROMPT_HASHES[v] for v in old}, dict(old))
        self.assertEqual(prompt.PROMPT_HASHES[prompt.PROMPT_VERSION], '6b86be79d29a9287768ef447f8c3d817a583f959e62430e9cdf4a059bf111b81')
        self.assertEqual(prompt.PROMPT, (study.ROOT / 'tests/fixtures/arena-turn-prompt-v5.txt').read_text())
        for phrase in ('action_points_remaining is the complete AP budget', 'running total of action costs',
                       'Before adding each action', 'MUST NOT\nexceed this budget',
                       'shorter plan if no worthwhile legal action\nfits the remaining AP'):
            self.assertIn(phrase, prompt.AP_GUIDANCE)
        for phrase in ('state', 'Shield Bash', 'DOWNED', 'LOS', 'target', 'Fireball', 'damage', 'uncertain'):
            self.assertNotIn(phrase, prompt.AP_GUIDANCE)

    def test_defaults_schema_repair_and_control_identity(self):
        for value in (None, 'latest'):
            self.assertEqual(prompt.resolve_prompt(value), historical_prompt(value))
        for name in ('openai', 'ollama'):
            self.assertEqual(create_arena_turn_provider(Settings(), name).prompt_version, 'arena-turn-prompt-v1')
        self.assertEqual(STEP_PROMPT_VERSION, 'arena-step-prompt-v1')
        self.assertIs(OpenAIAPBudgetProvider.parse_plan, ModelArenaTurnProvider.parse_plan)
        self.assertIs(OpenAIAPBudgetProvider.repair_feedback, ModelArenaTurnProvider.repair_feedback)
        self.assertIs(prompt.APBudgetBoundedReplanController.run_turn, ArenaBoundedReplanController.run_turn)
        with self.assertRaises(ValueError):
            prompt.resolve_prompt('arena-turn-prompt-v99')

    def test_strict_and_bounded_all_partial_ap(self):
        for ap in range(1, 6):
            for bounded in (False, True):
                sim = ArenaSimulation(fixture(ap=ap, actor=(2, 2), enemy=(3, 2)))
                provider = self.provider([encoded([action('attack')])])
                observed = []
                original = provider.create_turn_plan
                def capture(obs):
                    observed.append(obs.to_dict()['action_points_remaining'])
                    return original(obs)
                provider.create_turn_plan = capture
                if bounded:
                    controller = prompt.APBudgetBoundedReplanController(provider)
                    self.assertEqual(controller.control_version, 'arena-control-full-turn-bounded-replan-v1')
                    result = controller.run_turn(sim)
                else:
                    plan, t = study.checked_plan(provider, 'openai', build_observation(sim.state))
                    self.assertTrue(t['success'])
                    result = execute_arena_turn(sim.state, plan, execute_command=sim.execute)
                self.assertEqual(observed, [ap])
                self.assertEqual(state_hash(replay(sim.trace()).state), state_hash(sim.state))
            obs = build_observation(fixture(ap=ap))
            self.assertEqual(parse_turn_plan(encoded([]), obs), ArenaTurnPlan())
            with self.assertRaises(ArenaProviderError) as caught:
                parse_turn_plan(encoded([action('attack')] * (ap + 1)), obs)
            self.assertEqual(caught.exception.category, 'ap_budget' if ap < 5 else 'schema_validation')

    def test_three_way_scripted_and_historical_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / 'run'
            out = Path(tmp) / 'analysis'
            study.run(run)
            pair = study.compare(run, out, scripted=True)
            result = study.read(out / 'three-way.json')
            self.assertTrue(result['diagnostic_only'])
            self.assertEqual(pair['matched_intended_decisions'], 122)
            self.assertEqual(result['arms']['V1']['counts']['truncation_unused_ap'], 21)
            self.assertEqual(result['arms']['V4']['counts']['truncation_unused_ap'], 27)
            self.assertEqual(result['arms']['V4']['counts']['exhausted_repairs'], 1)
            self.assertEqual(result['arms']['V4']['counts']['shield_bash_range_failures'], 4)
            for arm in ('V1', 'V4'):
                self.assertEqual(result['arms'][arm]['counts']['all_later_action_failures'], 15)
            self.assertEqual(result['arms']['V5']['counts']['requests'], 0)
            self.assertIn('| Metric | V1 | V4 | V5 |', (out / 'three-way.md').read_text())
            with self.assertRaises(ValueError):
                study.compare(run, Path(tmp) / 'denied')
            manifest = study.read(run / 'manifest.json')
            manifest['prompt_version'] = 'arena-turn-prompt-v4'
            study.frozen.write(run / 'manifest.json', manifest)
            with self.assertRaises(ValueError):
                study.compare(run, Path(tmp) / 'tampered', scripted=True)

    def test_historical_analysis_reproduced_and_cohort_tamper_rejected(self):
        binding, suite = study.verify()
        preserved = study.read(study.V4_ANALYSIS / 'comparison.json')
        for name, root in (('baseline', study.BASELINE), ('candidate', study.V4_RUN)):
            actual = study.analyze_arm(root, binding['cohort'], suite)
            for section in ('counts', 'rates', 'first_response_errors', 'categories'):
                for key, value in preserved[name][section].items():
                    self.assertEqual(actual[section][key], value, (name, section, key))
        wrapper = study.read(study.BINDING)
        wrapper['payload']['cohort'] = wrapper['payload']['cohort'][:-1]
        wrapper['sha256'] = study.digest(wrapper['payload'])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'binding.json'
            study.frozen.write(path, wrapper)
            with self.assertRaisesRegex(ValueError, 'matched cohort/protocol drift'):
                study.verify(path)
