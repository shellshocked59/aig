import unittest
from copy import deepcopy
from unittest.mock import patch

from aig.arena import ArenaSimulation, replay, state_hash
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController, aggregate_turns
from aig.arena.ai.contracts import ArenaTurnPlan, AttackAction, SnipeAction, MoveAction, ArenaPosition, FinishAction
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.probes import create_probe
from aig.arena.ai.observation import build_observation
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.snapshots import canonical_json
from aig.settings import OpenAISettings, Settings


class SequenceProvider:
    name = 'fake'

    def __init__(self, *plans):
        self.plans = iter(plans)
        self.observations = []

    def create_turn_plan(self, observation):
        self.observations.append(observation)
        plan = next(self.plans)
        if isinstance(plan, Exception):
            raise plan
        return plan


class TransportSequence(OpenAIArenaTurnProvider):
    def __init__(self, *responses):
        super().__init__(OpenAISettings(), client=object())
        self.responses = iter(responses)
        self.messages = []

    def request(self, messages, record):
        self.messages.append(deepcopy(messages))
        record['metrics'] = dict(input_tokens=10, output_tokens=5, total_tokens=15)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, str) else canonical_json(value.to_dict())


def blocked():
    return ArenaTurnPlan((SnipeAction('actor', 'enemy'), SnipeAction('actor', 'enemy'), AttackAction('actor', 'enemy2')))


class BoundedTests(unittest.TestCase):
    def setUp(self):
        guard = patch('openai.resources.responses.responses.Responses.create', side_effect=AssertionError('live forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def run_case(self, *plans, probe='snipe_vs_basic', fallback=True, state=None):
        provider = SequenceProvider(*plans)
        sim = ArenaSimulation(state or create_probe(probe))
        trace = ArenaBoundedReplanController(provider, fallback=fallback).run_turn(sim).to_dict()
        self.assertEqual(replay(sim.trace()).trace(), sim.trace())
        self.assertEqual(trace['ap_spent'], sum(w.get('ap_spent', 0) for w in trace['waves']))
        return sim, trace, provider

    def test_full_plan_strict_parity(self):
        plan = ArenaTurnPlan((AttackAction('actor', 'red-core'),)*4+(FinishAction('actor', 'body'),))
        sim, t, p = self.run_case(plan, probe='finish_or_core')
        strict = ArenaSimulation(create_probe('finish_or_core'))
        execute_arena_turn(strict.state, plan, execute_command=strict.execute)
        self.assertEqual(sim.trace(), strict.trace())
        self.assertEqual((t['ap_spent'], t['planning_waves'], t['replan_used']), (5, 1, False))

    def test_mid_invalid_freshness_and_suffix(self):
        initial = ArenaTurnPlan((MoveAction('actor', ArenaPosition(2, 2)), SnipeAction('actor', 'enemy'), AttackAction('actor', 'enemy'), AttackAction('actor', 'enemy2')))
        replacement = ArenaTurnPlan((AttackAction('actor', 'enemy2'),)*2)
        sim, t, p = self.run_case(initial, replacement)
        self.assertEqual((t['ap_spent'], t['ap_recovered'], t['ap_before_replan']), (5, 2, 2))
        w = t['waves'][0]
        self.assertEqual((w['actions_executed'], w['invalid_action']['index'], w['stale_suffix_count']), (2, 2, 2))
        obs = p.observations[1].to_dict()
        actor = obs['own_team']['units'][0]
        enemy = next(u for u in obs['enemy_team']['units'] if u['id'] == 'enemy')
        self.assertEqual(({'x': actor['x'], 'y': actor['y']}, enemy['hp'], enemy['status']), ({'x': 2, 'y': 2}, 0, 'downed'))
        self.assertNotEqual(p.observations[0].hash, p.observations[1].hash)
        self.assertEqual(len(t['commands_executed']), 5)

    def test_first_invalid_full_replacement_budget(self):
        invalid = ArenaTurnPlan((AttackAction('actor', 'enemy'),))
        replacement = ArenaTurnPlan((AttackAction('actor', 'enemy2'),)*3)
        _, t, p = self.run_case(invalid, replacement)
        self.assertEqual(t['waves'][0]['ap_spent'], 0)
        self.assertEqual(p.observations[0].hash, p.observations[1].hash)
        self.assertEqual(t['ap_recovered'], 3)

    def test_second_failure_no_third_wave(self):
        replacement = ArenaTurnPlan((AttackAction('actor', 'enemy2'), AttackAction('actor', 'enemy')))
        _, t, p = self.run_case(blocked(), replacement)
        self.assertEqual((len(p.observations), t['ap_spent'], t['ap_unused']), (2, 3, 2))
        self.assertEqual(t['waves'][1]['invalid_action']['index'], 1)

    def test_empty_short_initial_and_replacement(self):
        for replacement in (ArenaTurnPlan(), ArenaTurnPlan((AttackAction('actor', 'enemy2'),))):
            for plans in ((replacement,), (blocked(), replacement)):
                with self.subTest(plans=plans):
                    sim, t, p = self.run_case(*plans)
                    self.assertEqual(len(p.observations), len(plans))
                    self.assertEqual(sim.state.active_player_id, 'red')
                    self.assertEqual(t['ap_unused'], 5-t['ap_spent'])

    def test_terminal_initial_and_replacement_core_and_elimination(self):
        for probe, target in (('winning_core_line', 'red-core'), ('team_elimination', 'enemy')):
            good = ArenaTurnPlan((AttackAction('actor', target),)*2)
            bad = ArenaTurnPlan((MoveAction('actor', ArenaPosition(0, 2)),))
            for plans in ((good,), (bad, good)):
                sim, t, p = self.run_case(*plans, probe=probe)
                self.assertIsNotNone(t['terminal_result'])
                self.assertFalse(any(c['type'] == 'arena_end_turn' for c in t['commands_executed']))
                with self.assertRaises(ValueError):
                    ArenaBoundedReplanController(p).run_turn(sim)

    def test_zero_ap_no_request(self):
        state = create_probe('snipe_vs_basic'); state.action_points_remaining = 0
        sim, t, p = self.run_case(state=state)
        self.assertEqual(len(p.observations), 0)
        self.assertEqual(sim.state.active_player_id, 'red')

    def test_partial_ap_static_validation(self):
        for ap in range(1, 6):
            state = create_probe('finish_or_core'); state.action_points_remaining = ap
            obs = build_observation(state)
            plan = ArenaTurnPlan((AttackAction('actor', 'red-core'),)*ap)
            self.assertEqual(parse_turn_plan(canonical_json(plan.to_dict()), obs), plan)
            if ap < 5:
                with self.assertRaises(ArenaProviderError) as ctx:
                    parse_turn_plan(canonical_json(ArenaTurnPlan(plan.actions+(plan.actions[0],)).to_dict()), obs)
                self.assertEqual(ctx.exception.category, 'ap_budget')

    def test_four_attempts_repairs_independent_and_fresh_messages(self):
        p = TransportSequence('{', blocked(), '{', ArenaTurnPlan((AttackAction('actor', 'enemy2'),)))
        sim = ArenaSimulation(create_probe('snipe_vs_basic'))
        t = ArenaBoundedReplanController(p).run_turn(sim).to_dict()
        self.assertEqual((t['provider_requests'], t['static_repairs'], t['planning_waves']), (4, 2, 2))
        self.assertEqual([len(m) for m in p.messages], [1, 2, 1, 2])
        self.assertNotEqual(p.messages[0][0], p.messages[2][0])
        self.assertFalse(hasattr(p, 'before_request'))
        metrics = aggregate_turns([t])
        self.assertEqual((metrics['provider_requests_per_turn'], metrics['ap_recovered'], metrics['total_tokens']), (4, 1, 60))

    def test_failed_provider_fallback_and_strict(self):
        for prefix in ((), (blocked(),)):
            for error in ('transport_failure', 'repair_failed'):
                for fallback in (False, True):
                    sim, t, p = self.run_case(*prefix, ArenaProviderError(error), fallback=fallback)
                    self.assertEqual(t['fallback_used'], fallback)
                    self.assertEqual(len(p.observations), len(prefix)+1)
                    self.assertEqual(sim.state.active_player_id, 'red' if fallback else 'blue')

    def test_actual_static_repair_exhaustion(self):
        for prefix in ((), (blocked(),)):
            p = TransportSequence(*prefix, '{', '{')
            t = ArenaBoundedReplanController(p).run_turn(ArenaSimulation(create_probe('snipe_vs_basic'))).to_dict()
            self.assertEqual(t['error_category'], 'repair_failed')
            self.assertTrue(t['fallback_used'])
            self.assertLessEqual(t['provider_requests'], 4)

    def test_determinism(self):
        a = self.run_case(blocked(), ArenaTurnPlan())
        b = self.run_case(blocked(), ArenaTurnPlan())
        self.assertEqual(a[0].trace(), b[0].trace())
        self.assertEqual(a[1], b[1])

    def test_session_selection_no_inference_and_public_trace(self):
        from aig.control_web import ArenaControlWebSession, public_trace
        from aig.arena.control_settings import ArenaControlSettings, load_control_settings
        session = ArenaControlWebSession(Settings(), control_settings=ArenaControlSettings())
        for mode in ('full_turn', 'bounded_replan', 'stepwise'):
            state = session.demo(versus_ai=True, provider='openai', control_mode=mode)
            self.assertEqual(state['control_mode'], mode)
            self.assertFalse(state['ai_turns'])
            self.assertEqual(session.observer_demo(mode)['control_mode'], mode)
        self.assertEqual(session.demo(versus_ai=True, provider='openai')['control_mode'], 'full_turn')
        self.assertEqual(load_control_settings(environ={'AIG_ARENA_CONTROL_MODE': 'bounded_replan'}).mode, 'bounded_replan')
        with self.assertRaises(ValueError):
            load_control_settings(environ={'AIG_ARENA_CONTROL_MODE': 'bad'})
        self.assertEqual(public_trace({'waves': [{'inference': {'attempts': [{'raw_content': 'secret'}]}}]}),
                         {'waves': [{'inference': {}}]})

    def test_web_routes_single_ordered_batch(self):
        from fastapi.testclient import TestClient
        from aig.control_web import create_app
        from aig.arena.presentation import PresentationSimulation
        with patch('aig.api.load_settings', return_value=Settings()):
            app = create_app()
        p = SequenceProvider(blocked(), ArenaTurnPlan((AttackAction('actor', 'enemy2'),)*3))
        with TestClient(app) as client, patch('aig.arena.application.create_arena_turn_provider', return_value=p):
            response = client.post('/api/arena/observer/demo?control_mode=bounded_replan')
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['control_mode'], 'bounded_replan')
            self.assertEqual(p.observations, [])
            session = app.state.arena_session
            session._simulation = PresentationSimulation(ArenaSimulation(create_probe('snipe_vs_basic')))
            response = client.post('/api/arena/observer/turn')
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()
            self.assertEqual(len(result['ai_turns']), 1)
            self.assertEqual(result['ai_turns'][0]['ap_recovered'], 3)
            self.assertEqual(result['presentation']['final_state_hash'], result['state_hash'])
            self.assertEqual(state_hash(replay(session.trace()).state), result['state_hash'])
            self.assertGreater(len(result['presentation']['events']), 4)
            self.assertEqual(client.post('/api/arena/demo-ai/openai?control_mode=unknown').status_code, 422)

    def test_request_guard_denies_fifth_before_transport(self):
        class OverRequester(TransportSequence):
            def create_turn_plan(self, observation):
                for _ in range(5):
                    self.before_request()
                raise AssertionError('fifth reservation should fail')
        p = OverRequester()
        t = ArenaBoundedReplanController(p).run_turn(ArenaSimulation(create_probe('snipe_vs_basic'))).to_dict()
        self.assertEqual(t['provider_requests'], 4)
        self.assertEqual(t['error_category'], 'request_ceiling')
        self.assertFalse(t['fallback_used'])

    def test_benchmark_prepare_run_and_abort_offline(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from aig.arena.bounded_replan_benchmark import prepare, run, demo
        with TemporaryDirectory() as temp:
            root = Path(temp)
            plan = prepare(root/'plan.json', arms=('full_turn', 'bounded_replan'))
            self.assertEqual(plan['request_ceiling'], 6)
            p = TransportSequence(blocked(), blocked(), ArenaTurnPlan())
            result = run(root/'plan.json', root/'ok', provider_factory=lambda *args: p)
            self.assertEqual((result['status'], result['requests'], len(result['runs'])), ('complete', 3, 2))
            p = TransportSequence(ArenaProviderError('transport_failure'))
            result = run(root/'plan.json', root/'fail', provider_factory=lambda *args: p)
            self.assertEqual((result['status'], result['unstarted_turns']), ('failed', 1))
            self.assertEqual(demo()['trace']['ap_recovered'], 3)


if __name__ == '__main__':
    unittest.main()
