"""Offline repair-boundary regressions and frozen one-request-per-arm accounting."""
import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aig.arena.ai.benchmark_candidate import CandidateObservation, SCHEMA_VERSION, parse_candidate
from aig.arena.ai.candidate_repair import (OLD, NEW, POLICY, context, compare, repair_messages,
    OpenAIRepairCandidateProvider, OllamaRepairCandidateProvider)
from aig.arena.ai.candidate_control import CandidateController
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.observation import simulation_state
from aig.arena.ai.benchmark_candidate import base_observation
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json
from aig.arena.repair_contract_comparison import challenges, prepare, verify, run, analyze
from aig.settings import OpenAISettings, Settings


def plan(actions):
    return canonical_json(dict(schema_version=SCHEMA_VERSION, actions=actions))


class Fake(OpenAIRepairCandidateProvider):
    def __init__(self, responses, *, step=False, version=NEW):
        super().__init__(OpenAISettings(),step=step,repair_version=version,client=object())
        self.responses=iter(responses)
        self.messages=[]

    def request(self,messages,record):
        self.messages.append(deepcopy(messages))
        record['metrics']=dict(input_tokens=10,output_tokens=5,total_tokens=15)
        return next(self.responses)


class RepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=challenges()

    def setUp(self):
        for target in ('socket.socket.connect','socket.socket.connect_ex','socket.create_connection',
                       'openai.resources.responses.responses.Responses.create'):
            guard=patch(target,side_effect=AssertionError('NO LIVE INFERENCE'))
            guard.start(); self.addCleanup(guard.stop)

    def obs(self,c):
        return CandidateObservation(canonical_json(c['observation']))

    def evidence(self,raw,obs,step=False):
        try:
            parse_candidate(raw,obs,step=step)
        except ArenaProviderError as e:
            return context(raw,obs,e,step=step)
        self.fail('expected invalid input')

    def correction(self,c):
        if c['id'] in ('R2','R3'):
            return plan([dict(type='move',unit_id='actor',destination=dict(x=3,y=2)),
                         dict(type='snipe',unit_id='actor',target_id='enemy')])
        return plan([next(a for a in c['observation']['legal_actions'] if a['type']=='move')])

    def test_six_forensic_payloads_and_fake_corrections(self):
        for c in self.cases:
            with self.subTest(case=c['id']):
                p=Fake([c['raw'],self.correction(c)],step=c['step'])
                obs=self.obs(c)
                corrected=p.create_turn_plan(obs)
                self.assertEqual(len(p.messages),2)
                self.assertEqual(p.messages[1],c['payloads'][NEW]['input'])
                self.assertEqual(c['evidence']['rejected_plan'],json.loads(c['raw']))
                self.assertTrue(p.last_trace['repair_comparison']['valid'])
                self.assertEqual(corrected.to_dict(),json.loads(self.correction(c)))
                self.assertIn('range',[d['code'] for d in c['evidence']['diagnostics']])
                if c['id'] in ('R2','R3'):
                    self.assertEqual([c['evidence'][k] for k in ('available_ap','planned_ap','over_budget_by')],[3,4,1])
                    self.assertEqual(c['evidence']['diagnostics'][-1]['actual_distance'],5)

    def test_old_payload_exact(self):
        for c in self.cases:
            p=Fake([c['raw'],self.correction(c)],step=c['step'],version=OLD)
            p.create_turn_plan(self.obs(c))
            self.assertEqual(p.messages[1],c['payloads'][OLD]['input'])
            self.assertEqual(p.messages[1][1]['content'],ModelArenaTurnProvider.repair_feedback(None,c['evidence']['validation']['category']))
            self.assertNotIn('rejected_plan',p.messages[1][1]['content'])

    def test_repeated_range_and_ap_failures(self):
        for c in self.cases:
            p=Fake([c['raw'],c['raw']],step=c['step'])
            with self.assertRaises(ArenaProviderError): p.create_turn_plan(self.obs(c))
            self.assertEqual(p.last_trace['repair_comparison']['category'],'REPEATED_SAME_ERROR')
            self.assertEqual(len(p.messages),2)

    def test_endturn_escape_still_legal(self):
        c=self.cases[3]
        p=Fake([c['raw'],plan([dict(type='end_turn')])],step=True)
        p.create_turn_plan(self.obs(c))
        self.assertEqual(p.last_trace['repair_comparison']['category'],'ENDTURN_ESCAPE')
        self.assertTrue(p.last_trace['repair_comparison']['valid'])

    def test_original_endturn_wrapper_error(self):
        obs=self.obs(self.cases[3])
        raw=json.dumps(dict(schema_version='wrong',actions=[dict(type='end_turn')]))
        e=self.evidence(raw,obs,True)
        result=compare(e,plan([dict(type='end_turn')]),obs,step=True)
        self.assertEqual(result['category'],'EXACT_VALIDATION_FIX')
        self.assertTrue(result['original_end_turn_preserved'])
        self.assertFalse(result['potential_endturn_escape'])

    def test_suffix_trim(self):
        c=self.cases[1]; obs=self.obs(c)
        actions=json.loads(self.correction(c))['actions']
        raw=plan(actions+[dict(type='attack',unit_id='actor',target_id='enemy')])
        e=self.evidence(raw,obs)
        self.assertEqual(e['planned_ap'],4)
        self.assertEqual(compare(e,plan(actions),obs)['category'],'VALID_SUFFIX_TRIM')
        self.assertEqual(e['diagnostics'],[dict(code='ap_budget',available_ap=3,planned_ap=4,over_budget_by=1)])

    def test_malformed(self):
        obs=self.obs(self.cases[0])
        for raw in ('broken SECRET','[', 'x'*40000):
            e=self.evidence(raw,obs)
            self.assertIsNone(e['rejected_plan'])
            self.assertNotIn('SECRET',canonical_json(e))
            p=Fake([raw,plan([dict(type='end_turn')])])
            p.create_turn_plan(obs)
            self.assertEqual(len(p.messages),2)

    def test_failed_malformed_repair_telemetry(self):
        c=self.cases[0]; p=Fake([c['raw'],'bad output'])
        with self.assertRaises(ArenaProviderError): p.create_turn_plan(self.obs(c))
        self.assertEqual(p.last_trace['repair_comparison']['category'],'MALFORMED')

    def test_partial_ap(self):
        for ap in range(1,5):
            facts=deepcopy(self.cases[1]['observation']); facts['action_points_remaining']=ap
            obs=CandidateObservation(canonical_json(facts))
            e=self.evidence(plan([dict(type='snipe',unit_id='actor',target_id='enemy')]*3),obs)
            self.assertEqual((e['available_ap'],e['planned_ap'],e['over_budget_by']),(ap,6,6-ap))

    def test_unknown_reference_redaction(self):
        obs=self.obs(self.cases[0]); raw=plan([dict(type='attack',unit_id='actor',target_id='SECRET')])
        e=self.evidence(raw,obs)
        self.assertNotIn('SECRET',canonical_json(e))
        self.assertIn('invalid_reference',[d['code'] for d in e['diagnostics']])

    def test_status_and_los(self):
        facts=deepcopy(self.cases[0]['observation'])
        facts['enemy_team']['units'][0]['status']='downed'
        facts['enemy_team']['units'][0]['hp']=0
        obs=CandidateObservation(canonical_json(facts))
        e=self.evidence(self.cases[0]['raw'],obs)
        d=next(d for d in e['diagnostics'] if d['code']=='target_status')
        self.assertEqual((d['expected_status'],d['actual_status']),('active','downed'))
        facts=deepcopy(self.cases[1]['observation'])
        facts['own_team']['units'][0]['x']=2
        facts['board']['blocked_tiles'].append(dict(x=4,y=2))
        obs=CandidateObservation(canonical_json(facts))
        e=self.evidence(plan([dict(type='snipe',unit_id='actor',target_id='enemy')]),obs)
        self.assertTrue(any(d['code']=='los' and d['los_clear'] is False for d in e['diagnostics']))

    def test_single_action_cardinality(self):
        c=self.cases[3]; obs=self.obs(c)
        with self.assertRaises(ArenaProviderError):
            parse_candidate(self.correction(self.cases[1]),obs,step=True)

    def test_controls_and_replacement(self):
        data=json.loads(Path('artifacts/arena-candidate-forensics/20260914-audit-v1/forensics.json').read_text())
        for c in self.cases:
            t=next(t for t in data['trials'] if t['trial']==c['trial'])
            initial=ArenaSimulation(__import__('aig.arena.snapshots',fromlist=['from_snapshot']).from_snapshot(t['starting_state']))
            responses=[w['attempts'][0]['raw_content'] for w in t['waves'][:c['wave']]]
            responses += [c['raw'],self.correction(c)]
            # Any refreshed step after the correction cleanly completes without another repair.
            responses += [plan([])]*5
            p=Fake(responses,step=c['step'])
            trace=CandidateController(p,mode=t['trial_binding']['control_mode']).run_turn(initial)
            self.assertNotEqual(trace['stop_reason'],'PROVIDER_FAILURE')
            self.assertEqual(replay(initial.trace()).trace(),initial.trace())
            self.assertEqual(trace['static_repairs'],1)
            self.assertEqual(trace['waves'][c['wave']]['inference']['repair_comparison']['valid'],True)
            if c['id'] in ('R1','R5'): self.assertTrue(trace['replan_used'])

    def test_no_state_mutation_or_later_geometry_check(self):
        c=self.cases[1]; obs=self.obs(c); before=obs.canonical
        e=self.evidence(plan(json.loads(self.correction(c))['actions']+[dict(type='attack',unit_id='actor',target_id='enemy')]),obs)
        self.assertEqual(obs.canonical,before)
        self.assertNotIn('range',[d['code'] for d in e['diagnostics']])

    def test_ollama_binding_shared(self):
        from aig.settings import OllamaSettings
        p=OllamaRepairCandidateProvider(OllamaSettings(),repair_version=NEW)
        c=self.cases[0]; obs=self.obs(c)
        error=ArenaProviderError('invalid_reference')
        self.assertEqual(p.repair_messages(obs,error,c['evidence']),repair_messages(obs,error,c['evidence'],NEW))

    def test_live_gate_and_frozen_runner(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'frozen'
            m=prepare(out)
            self.assertEqual((m['pairs'],m['intended_requests'],m['synthetic_challenges']),(18,36,0))
            verify(out)
            with self.assertRaises(ValueError): run(out)
            calls=[]
            class Single(Fake):
                def __init__(self,settings,step=False,repair=False):
                    super().__init__([plan([dict(type='end_turn')])]*36,step=step)
                def request(self,messages,record):
                    calls.append(messages)
                    return super().request(messages,record)
            with patch('aig.settings.load_settings',return_value=Settings()):
                self.assertEqual(run(out,live=True,provider_factory=Single)['reserved_requests'],36)
                with self.assertRaises(FileExistsError): run(out,live=True,provider_factory=Single)
            self.assertEqual(len(calls),36)
            report=analyze(out)
            self.assertEqual(report['requests'],36)
            self.assertEqual(len(report['pairs']),18)
            with (out/'challenges.json').open('a') as f: f.write(' ')
            with self.assertRaises(ValueError): verify(out)

    def test_provider_failure_stops_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'frozen'; prepare(out)
            class Broken(Fake):
                def __init__(self,settings,step=False,repair=False): super().__init__([],step=step)
                def request(self,messages,record): raise ArenaProviderError('transport_failure')
            with patch('aig.settings.load_settings',return_value=Settings()):
                result=run(out,live=True,provider_factory=Broken)
            self.assertEqual(result['reserved_requests'],1)
            self.assertEqual(analyze(out)['status'],'stopped')


if __name__=='__main__': unittest.main()
