"""Deterministic candidate contracts; network is forbidden throughout this module."""
import json
from pathlib import Path
import unittest
from dataclasses import replace
from types import SimpleNamespace as NS
from unittest.mock import patch

from aig.arena import ArenaSimulation, replay
from aig.arena.ai.benchmark_candidate import (
    CandidatePlan as Plan, EndTurnAction as Stop, candidate_observation, base_observation,
    parse_candidate, candidate_schema, OpenAICandidateProvider, OllamaCandidateProvider,
    PROMPTS, POLICY_CORE, TURN_PROMPT_VERSION, STEP_PROMPT_VERSION, SCHEMA_VERSION,
)
from aig.arena.ai.candidate_control import CandidateController, aggregate_candidate_turns
from aig.arena.ai.contracts import AttackAction as Attack, MoveAction as Move, ArenaPosition as Pos, SnipeAction as Snipe
from aig.arena.ai.observation import build_observation, OBSERVATION_V2, observation_facts
from aig.arena.ai.probes import create_probe
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.snapshots import canonical_json
from aig.settings import OpenAISettings, OllamaSettings


class Scripted:
    def __init__(self, *plans):
        self.plans, self.observations = iter(plans), []

    def create_turn_plan(self, observation):
        self.observations.append(observation)
        plan = next(self.plans)
        if isinstance(plan, Exception):
            raise plan
        return plan


class FakeTransport(OpenAICandidateProvider):
    def __init__(self, *responses, step=False):
        super().__init__(OpenAISettings(), step=step, client=object())
        self.responses = iter(responses)

    def request(self, messages, record):
        record['metrics'] = dict(input_tokens=10, output_tokens=5, total_tokens=15)
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, str) else canonical_json(value.to_dict())


class CandidateTests(unittest.TestCase):
    def setUp(self):
        for target in ('socket.socket.connect', 'socket.create_connection',
                       'openai.resources.responses.responses.Responses.create'):
            guard = patch(target, side_effect=AssertionError('live inference forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def run_case(self, *plans, mode='strict', probe='finish_or_core', ap=5, provider=None):
        state = create_probe(probe)
        state.action_points_remaining = ap
        sim = ArenaSimulation(state)
        provider = provider or Scripted(*plans)
        trace = CandidateController(provider, mode=mode).run_turn(sim)
        self.assertEqual(replay(sim.trace()).trace(), sim.trace())
        self.assertEqual(trace['ap_executed']+trace['ap_remaining'], ap)
        self.assertEqual(sum(w['ap_executed'] for w in trace['waves']), trace['ap_executed'])
        return trace, provider, sim

    def test_strict_explicit_stop(self):
        t, _, sim = self.run_case(Plan((Attack('actor','red-core'), Move('actor',Pos(6,2)), Stop())))
        self.assertEqual((t['ap_executed'],t['ap_remaining'],t['stop_reason']), (2,3,'INTENTIONAL_END_TURN'))
        self.assertEqual((t['actions_executed'],t['provider_requests'],t['replan_used']), (2,1,False))
        self.assertEqual(sim.state.active_player_id, 'red')
        self.assertEqual(len(t['commands_executed']), 3)

    def test_bounded_explicit_stop(self):
        t, _, _ = self.run_case(Plan((Attack('actor','red-core'), Move('actor',Pos(6,2)), Stop())), mode='bounded')
        self.assertEqual((t['ap_executed'],t['ap_remaining'],t['replan_used']), (2,3,False))
        self.assertTrue(t['first_plan_explicit_end_turn'])

    def test_clean_short_and_empty_distinct(self):
        for mode in ('strict','bounded','stepwise'):
            for plan in (Plan(), Plan((Attack('actor','red-core'),))):
                plans = (plan,Plan()) if mode == 'stepwise' and plan.actions else (plan,)
                t, _, _ = self.run_case(*plans, mode=mode)
                self.assertEqual(t['stop_reason'], 'CLEAN_PLAN_COMPLETE')
                self.assertTrue(t['clean_short_plan'])
                self.assertFalse(t['explicit_end_turn'])
                self.assertFalse(t['replan_used'])

    def test_ordering_and_extra_fields(self):
        obs = candidate_observation(create_probe('finish_or_core'))
        for actions in ([{'type':'end_turn'}, Attack('actor','red-core').to_dict()],
                        [{'type':'end_turn'},{'type':'end_turn'}],
                        [{'type':'end_turn','reason':'good position'}]):
            with self.assertRaises(ArenaProviderError):
                parse_candidate(canonical_json(dict(schema_version=SCHEMA_VERSION,actions=actions)),obs)

    def test_terminal_suppresses_stop_and_suffix(self):
        for mode in ('strict','bounded'):
            t, _, _ = self.run_case(Plan((Attack('actor','red-core'), Attack('actor','red-core'), Stop())),
                                   mode=mode, probe='winning_core_line')
            self.assertEqual(t['stop_reason'],'TERMINAL')
            self.assertFalse(t['explicit_end_turn'])
            self.assertFalse(any(c['type']=='arena_end_turn' for c in t['commands_executed']))

    def test_bounded_replacement_explicit(self):
        t, p, _ = self.run_case(Plan((Snipe('actor','enemy'), Attack('actor','enemy'))),
            Plan((Move('actor',Pos(2,2)),Stop())), mode='bounded',probe='snipe_vs_basic')
        self.assertEqual((t['ap_executed'],t['ap_remaining'],t['ap_at_replan'],t['ap_recovered']), (3,2,3,1))
        self.assertEqual(t['stop_reason'],'INTENTIONAL_END_TURN')
        self.assertEqual(len(p.observations),2)
        self.assertTrue(t['replacement_explicit_end_turn'])
        self.assertTrue(t['invalidity_triggered_replan'])
        self.assertNotEqual(p.observations[0].hash,p.observations[1].hash)

    def test_unreached_stop_is_not_intent(self):
        t, _, _ = self.run_case(Plan((Snipe('actor','enemy'), Attack('actor','enemy'),Stop())),probe='snipe_vs_basic')
        self.assertEqual(t['stop_reason'],'EXECUTION_TRUNCATION')
        self.assertFalse(t['explicit_end_turn'])
        self.assertTrue(t['first_plan_planned_end_turn'])

    def test_second_invalidity_no_third_request(self):
        bad = Plan((Snipe('actor','enemy'),Attack('actor','enemy')))
        replacement = Plan((Move('actor',Pos(2,2)),Attack('actor','enemy')))
        t, p, _ = self.run_case(bad,replacement,mode='bounded',probe='snipe_vs_basic')
        self.assertTrue(t['second_invalidity'])
        self.assertEqual(len(p.observations),2)
        self.assertEqual(t['stop_reason'],'EXECUTION_TRUNCATION')

    def test_replacement_clean_short(self):
        t, _, _ = self.run_case(Plan((Snipe('actor','enemy'),Attack('actor','enemy'))),
            Plan((Move('actor',Pos(2,2)),)),mode='bounded',probe='snipe_vs_basic')
        self.assertTrue(t['replacement_clean_short_plan'])
        self.assertEqual(t['stop_reason'],'CLEAN_PLAN_COMPLETE')

    def test_stepwise_stop(self):
        t, p, _ = self.run_case(Plan((Attack('actor','red-core'),)),Plan((Stop(),)),mode='stepwise')
        self.assertEqual((len(p.observations),t['actions_before_intentional_stop'],t['ap_remaining']), (2,1,4))
        self.assertEqual(t['explicit_end_turn_decisions'],1)

    def test_stepwise_full_budget_bounded_requests(self):
        plans=[Plan((Attack('actor','red-core'),))]*4+[Plan((Move('actor',Pos(6,2)),))]
        t, p, _ = self.run_case(*plans,mode='stepwise')
        self.assertEqual((t['ap_executed'],len(p.observations)),(5,5))
        self.assertEqual([o.to_dict()['action_points_remaining'] for o in p.observations],[5,4,3,2,1])

    def test_stepwise_terminal_no_more_decisions(self):
        t, p, _ = self.run_case(Plan((Attack('actor','red-core'),)),Plan((Attack('actor','red-core'),)),
                               mode='stepwise',probe='winning_core_line')
        self.assertEqual(t['stop_reason'],'TERMINAL')
        self.assertEqual(len(p.observations),1)

    def test_stop_only_all_modes(self):
        for mode in ('strict','bounded','stepwise'):
            t, _, _ = self.run_case(Plan((Stop(),)),mode=mode)
            self.assertEqual((t['ap_executed'],t['ap_remaining'],t['provider_requests']), (0,5,1))

    def test_zero_ap_no_request(self):
        for mode in ('strict','bounded','stepwise'):
            t, _, _ = self.run_case(mode=mode,ap=0)
            self.assertEqual(t['provider_requests'],0)
            self.assertEqual(t['stop_reason'],'CLEAN_PLAN_COMPLETE')

    def test_six_entries_full_ap_then_stop(self):
        plan = Plan((Attack('actor','red-core'),)*4+(Move('actor',Pos(6,2)),Stop()))
        t, _, _ = self.run_case(plan)
        self.assertEqual((t['ap_executed'],t['ap_remaining'],t['stop_reason']), (5,0,'INTENTIONAL_END_TURN'))

    def test_partial_ap_rejected(self):
        t, _, _ = self.run_case(Plan((Attack('actor','red-core'),)*3),ap=2)
        self.assertEqual((t['stop_reason'],t['error_category'],t['ap_executed']), ('PROVIDER_FAILURE','ap_budget',0))

    def test_provider_failure_preserves_prefix(self):
        for mode in ('strict','bounded','stepwise'):
            t, _, sim = self.run_case(ArenaProviderError('transport_failure'),mode=mode)
            self.assertEqual(t['stop_reason'],'PROVIDER_FAILURE')
            self.assertEqual(sim.state.active_player_id,'blue')

    def test_four_requests_two_repairs(self):
        p = FakeTransport('{',Plan((Snipe('actor','enemy'),Attack('actor','enemy'))),'{',Plan((Stop(),)))
        t, _, _ = self.run_case(provider=p,mode='bounded',probe='snipe_vs_basic')
        self.assertEqual((t['provider_requests'],t['static_repairs'],t['total_tokens']), (4,2,60))
        self.assertFalse(hasattr(p,'before_request'))

    def test_repair_exhaustion(self):
        t, _, _ = self.run_case(provider=FakeTransport('{','{'))
        self.assertEqual((t['provider_requests'],t['error_category']), (2,'repair_failed'))

    def test_global_budget_hook_restored(self):
        p = FakeTransport(Plan((Stop(),)))
        def deny():
            raise ArenaProviderError('request_ceiling')
        p.before_request = deny
        t, _, _ = self.run_case(provider=p)
        self.assertIs(p.before_request,deny)
        self.assertEqual(t['provider_requests'],0)

    def test_all_controls_same_starting_observation(self):
        observations=[]
        for mode in ('strict','bounded','stepwise'):
            _, p, _ = self.run_case(Plan((Stop(),)),mode=mode)
            observations.append(p.observations[0])
        self.assertEqual(observations[0],observations[1])
        self.assertEqual(observations[0],observations[2])
        original=build_observation(create_probe('finish_or_core'),version=OBSERVATION_V2)
        self.assertEqual(base_observation(observations[0]),original)
        self.assertEqual(observation_facts(original),build_observation(create_probe('finish_or_core')).to_dict())

    def test_step_cardinality_and_common_first_legality(self):
        obs=candidate_observation(create_probe('snipe_vs_basic'))
        for step in (True,False):
            with self.assertRaises(ArenaProviderError):
                parse_candidate(canonical_json(Plan((Attack('actor','enemy'),)).to_dict()),obs,step=step)
        with self.assertRaises(ArenaProviderError):
            parse_candidate(canonical_json(Plan((Snipe('actor','enemy'),Stop())).to_dict()),obs,step=True)

    def test_prompt_core_and_wire(self):
        from aig.arena.ai.action_id import STEP_PROMPT_VERSION as ACTION_ID_PROMPT
        from aig.arena.ai.stepwise import STEP_PROMPT_VERSION as HISTORICAL_STEP_PROMPT
        self.assertNotIn(STEP_PROMPT_VERSION,(ACTION_ID_PROMPT,HISTORICAL_STEP_PROMPT))
        self.assertTrue(all(p.startswith(POLICY_CORE) for p in PROMPTS.values()))
        for step in (True,False):
            schema=candidate_schema(step=step,openai=True)
            self.assertEqual(schema['properties']['actions']['maxItems'],1 if step else 6)
            self.assertNotIn('reason',canonical_json(schema))
            p=OpenAICandidateProvider(OpenAISettings(),client=object(),step=step)
            q=OllamaCandidateProvider(OllamaSettings(),requester=lambda *a: self.fail('unexpected request'),step=step)
            self.assertEqual(p.system_prompt,q.system_prompt)
            self.assertEqual(p.prompt_version,STEP_PROMPT_VERSION if step else TURN_PROMPT_VERSION)

    def test_fake_transport_wire_and_repairs(self):
        for step in (False,True):
            for kind in ('openai','ollama'):
                calls=[]
                responses=iter(['{',canonical_json(Plan((Stop(),)).to_dict())])
                if kind == 'openai':
                    def send(**kwargs):
                        calls.append(kwargs)
                        return NS(status='completed',error=None,usage=None,output=[NS(type='message',
                            role='assistant',status='completed',content=[NS(type='output_text',text=next(responses))])])
                    provider=OpenAICandidateProvider(replace(OpenAISettings(),api_key='offline'),
                        client=NS(responses=NS(create=send)),step=step)
                else:
                    def send(url,payload,timeout):
                        calls.append(json.loads(payload))
                        return json.dumps(dict(done=True,message=dict(content=next(responses)),
                                               prompt_eval_count=10,eval_count=5))
                    provider=OllamaCandidateProvider(OllamaSettings(),requester=send,step=step)
                t, _, _=self.run_case(provider=provider,mode='stepwise' if step else 'strict')
                self.assertEqual((len(calls),t['static_repairs'],t['ap_remaining']),(2,1,5))
                for call in calls:
                    schema=call['format'] if kind=='ollama' else call['text']['format']['schema']
                    self.assertEqual(schema,candidate_schema(step=step,openai=kind=='openai'))
                if kind=='ollama':
                    self.assertEqual(t['total_tokens'],30)

    def test_aggregate_partition(self):
        rows=[self.run_case(p)[0] for p in (Plan(),Plan((Stop(),)),ArenaProviderError('transport_failure'))]
        a=aggregate_candidate_turns(rows)
        self.assertEqual(sum(a['unused_ap_by_reason'].values()),a['ap_remaining'])
        self.assertEqual(a['failure_derived_unused_ap'],5)
        self.assertEqual(a['unused_ap_by_reason']['INTENTIONAL_END_TURN'],5)

    def test_response_fixtures(self):
        fixture=json.loads(Path('tests/fixtures/arena-candidate-responses-v1.json').read_text())
        for row in fixture['fixtures']:
            state=create_probe(row['probe'])
            state.action_points_remaining=row['ap']
            plan=parse_candidate(canonical_json(row['response']),candidate_observation(state),step=row['step'])
            self.assertLessEqual(plan.ap_cost,row['ap'])

    def test_focused_preparation_and_outcome_evaluator(self):
        from aig.arena.candidate_validation import verify_preparation, evaluate_candidate_trace
        from aig.arena.snapshots import from_snapshot
        suite=verify_preparation()
        self.assertEqual((suite['trial_count'],suite['hard_request_ceiling']),(24,86))
        probe=suite['probes'][0]
        sim=ArenaSimulation(from_snapshot(probe['initial_state']))
        trace=CandidateController(Scripted(Plan((Stop(),))),mode='strict').run_turn(sim)
        result=evaluate_candidate_trace(probe,trace)
        self.assertEqual(result['gameplay_actions_executed'],0)
        self.assertEqual(result['stop_reason'],'INTENTIONAL_END_TURN')


if __name__ == '__main__':
    unittest.main()
