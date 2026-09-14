"""Offline full-match safety tests; real parser/repair/controller, fake transport."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aig.arena.case_study import (JournalProvider,Ledger,run_match,run,integrity,read,write_new,
    IntegrityError,BudgetStop,no_network,verify_match,heuristic_plan)
from aig.arena.case_study_contract import freeze,ARMS,LIMITS,schedule
from aig.arena.case_study_analysis import wilson,exact_mcnemar,paired,summarize
from aig.arena.case_study_metrics import mechanical
from aig.arena.ai.benchmark_candidate import SCHEMA_VERSION
from aig.arena.ai.probes import create_probe
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json,digest,to_snapshot
from aig.settings import OpenAISettings


def raw(*actions):
    return canonical_json(dict(schema_version=SCHEMA_VERSION,actions=list(actions)))


STOP=raw(dict(type='end_turn'))


class CaseStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            cls.contract=freeze(Path(folder)/'contract.json')

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'run'
        network=no_network();network.__enter__();self.addCleanup(network.__exit__,None,None,None)

    def fixture(self,arm='strict',probe='finish_or_core',turns=1,**limits):
        c=deepcopy(self.contract);p=c['payload']
        p['initial_state']=to_snapshot(create_probe(probe))
        p['limits'].update(player_turns=turns,**limits)
        slot=dict(p['schedule'][0],arm=arm,luna_side='blue',heuristic_side='red',
            match_id='MATCH-001-'+arm,initial_state_hash=digest(p['initial_state']))
        p['schedule']=[slot];c['sha256']=digest(p)
        write_new(self.root/'benchmark-manifest.json',dict(mode='fake'))
        return c,slot,Ledger(self.root,p['limits'])

    def factory(self,*responses):
        sequence=iter(responses)
        def policy(obs,step):
            item=next(sequence)
            if isinstance(item,BaseException):raise item
            return item
        return lambda slot,book:JournalProvider(OpenAISettings(),slot=slot,ledger=book,fake=True,fake_policy=policy)

    def test_schedule_300_balance_matched_latin_order(self):
        p=self.contract['payload'];self.assertEqual(len(p['slots']),100);self.assertEqual(len(p['schedule']),300)
        self.assertEqual(sum(s['luna_side']=='red' for s in p['slots']),50)
        for i in range(100):
            triplet=p['schedule'][i*3:(i+1)*3]
            self.assertEqual({r['arm'] for r in triplet},set(ARMS))
            self.assertEqual(len({(r['initial_state_hash'],r['luna_side']) for r in triplet}),1)
        for batch in range(1,11):
            self.assertEqual(sum(s['batch']==batch for s in p['schedule']),30)

    def test_strict_explicit_stop_turn_limit(self):
        c,s,b=self.fixture();r=run_match(self.root,s,c,b,self.factory(STOP))
        self.assertEqual(r['terminal_cause'],'TURN_LIMIT');self.assertIsNone(r['winner'])
        self.assertEqual(r['metrics']['blue']['unused_ap_by_reason']['INTENTIONAL_END_TURN'],5)
        self.assertTrue(verify_match(self.root/'matches'/s['match_id'],contract=c)['success'])

    def test_static_repair_and_failure_forfeit(self):
        c,s,b=self.fixture();r=run_match(self.root,s,c,b,self.factory('{','{'))
        self.assertEqual((r['terminal_cause'],r['winner'],r['engine_winner'],r['requests']),('PROVIDER_FORFEIT','red',None,2))
        self.assertEqual(r['metrics']['blue']['repair_failure'],1)
        self.assertEqual(r['metrics']['red']['provider_requests'],0)

    def test_repair_success_preserves_intent_and_receipts(self):
        c,s,b=self.fixture();r=run_match(self.root,s,c,b,self.factory('{',STOP))
        self.assertEqual((r['requests'],r['metrics']['blue']['repair_success']),(2,1))
        self.assertEqual(len(list((self.root/'requests').glob('*/receipt.json'))),2)

    def test_transport_failure_no_retry(self):
        c,s,b=self.fixture();r=run_match(self.root,s,c,b,self.factory(ArenaProviderError('timeout')))
        self.assertEqual((r['terminal_cause'],r['requests']),('PROVIDER_FORFEIT',1))
        self.assertTrue(verify_match(self.root/'matches'/s['match_id'],contract=c)['success'])

    def test_core_victory(self):
        c,s,b=self.fixture(probe='winning_core_line')
        r=run_match(self.root,s,c,b,self.factory(raw(dict(type='attack',unit_id='actor',target_id='red-core'))))
        self.assertEqual((r['terminal_cause'],r['winner']),('CORE_DESTRUCTION','blue'))

    def test_team_elimination(self):
        c,s,b=self.fixture(probe='team_elimination')
        r=run_match(self.root,s,c,b,self.factory(raw(dict(type='attack',unit_id='actor',target_id='enemy'))))
        self.assertEqual((r['terminal_cause'],r['winner']),('TEAM_ELIMINATION','blue'))

    def test_bounded_replan_repair_and_second_invalidity(self):
        c,s,b=self.fixture(arm='bounded',probe='snipe_vs_basic')
        initial=raw(dict(type='snipe',unit_id='actor',target_id='enemy'),dict(type='attack',unit_id='actor',target_id='enemy'))
        replacement=raw(dict(type='move',unit_id='actor',destination=dict(x=2,y=2)),dict(type='attack',unit_id='actor',target_id='enemy'))
        r=run_match(self.root,s,c,b,self.factory('{',initial,'{',replacement))
        m=r['metrics']['blue'];self.assertEqual((r['requests'],m['replans'],m['ap_recovered'],m['second_invalidities']),(4,1,1,1))
        self.assertEqual(m['replacement_repairs'],1)

    def test_strict_truncates_without_replan(self):
        c,s,b=self.fixture(probe='snipe_vs_basic')
        plan=raw(dict(type='snipe',unit_id='actor',target_id='enemy'),dict(type='attack',unit_id='actor',target_id='enemy'))
        r=run_match(self.root,s,c,b,self.factory(plan));self.assertEqual(r['metrics']['blue']['execution_truncations'],1)
        self.assertEqual(r['requests'],1)

    def test_stepwise_refresh_and_end_turn(self):
        c,s,b=self.fixture(arm='stepwise')
        r=run_match(self.root,s,c,b,self.factory(raw(dict(type='attack',unit_id='actor',target_id='red-core')),STOP))
        self.assertEqual((r['requests'],r['metrics']['blue']['explicit_end_turn_decisions']),(2,1))
        turn=read(self.root/'matches'/s['match_id']/'turns/0001.json')['turn']
        self.assertNotEqual(turn['waves'][0]['observation_hash'],turn['waves'][1]['observation_hash'])

    def test_per_match_request_ceiling_before_transport(self):
        c,s,b=self.fixture(per_match=dict(strict=1,bounded=1,stepwise=1))
        r=run_match(self.root,s,c,b,self.factory('{',STOP))
        self.assertEqual((r['terminal_cause'],r['requests'],r['winner']),('REQUEST_LIMIT',1,None))
        self.assertEqual(r['metrics']['blue']['provider_failures'],0)
        self.assertEqual(r['metrics']['blue']['request_limit_decisions'],1)
        self.assertEqual(r['metrics']['blue']['failure_derived_unused_ap'],0)

    def test_cumulative_limits_stop_before_reserve(self):
        for key,value in [('global_requests',0),('batch_requests',0),('per_control',dict.fromkeys(ARMS,0)),
                          ('per_batch_control',dict.fromkeys(ARMS,0))]:
            with self.subTest(key=key):
                limits=deepcopy(LIMITS);limits[key]=value
                ledger=Ledger(self.root/ key,limits)
                with self.assertRaises(BudgetStop):ledger.reserve(self.contract['payload']['schedule'][0],1)
                self.assertEqual(ledger.rows,[])

    def test_zero_sent_requests_have_zero_tokens(self):
        c,s,b=self.fixture(per_match=dict.fromkeys(ARMS,0))
        r=run_match(self.root,s,c,b,self.factory())
        self.assertEqual(r['requests'],0)
        self.assertEqual(r['metrics']['blue']['total_tokens'],0)
        self.assertEqual(r['metrics']['blue']['provider_failures'],0)

    def test_interrupted_turn_durable_resume_no_duplicate(self):
        c,s,b=self.fixture(turns=1)
        with self.assertRaises(InterruptedError):
            run_match(self.root,s,c,b,self.factory(STOP),stop_after_turn=1)
        r=run_match(self.root,s,c,Ledger(self.root,c['payload']['limits']),self.factory())
        self.assertEqual(r['requests'],1)
        self.assertEqual(len(Ledger(self.root).rows),1)

    def test_uncommitted_reservation_blocks_resume(self):
        c,s,b=self.fixture();b.reserve(s,1)
        with self.assertRaisesRegex(IntegrityError,'uncommitted'):
            run_match(self.root,s,c,b,self.factory(STOP))
        self.assertEqual(len(b.rows),1)

    def test_request_and_artifact_tamper(self):
        c,s,b=self.fixture();run_match(self.root,s,c,b,self.factory(STOP))
        (self.root/'requests/000001/payload.json').write_text('{}')
        with self.assertRaisesRegex(IntegrityError,'request evidence mutation'):
            verify_match(self.root/'matches'/s['match_id'],contract=c)

    def test_heuristic_exception_is_integrity_stop(self):
        c,s,b=self.fixture(turns=2)
        with patch('aig.arena.case_study.heuristic_turn',side_effect=RuntimeError('defect')):
            with self.assertRaises(RuntimeError):run_match(self.root,s,c,b,self.factory(STOP))
        self.assertFalse((self.root/'matches'/s['match_id']/'seal.json').exists())

    def test_completed_resume_and_batch_gate(self):
        c=deepcopy(self.contract);p=c['payload'];p['limits']['player_turns']=1
        # Keep the full canonical schedule; first batch is 30 offline bounded matches.
        c['sha256']=digest(p)
        policy=lambda slot,book:JournalProvider(OpenAISettings(),slot=slot,ledger=book,fake=True,fake_policy=lambda o,s:STOP)
        result=run(self.root,c,through_batch=1,provider_factory=policy,stop_after_matches=13)
        count=result['reserved_requests'];self.assertEqual(result['completed_matches'],13)
        result=run(self.root,c,through_batch=1,provider_factory=policy)
        self.assertEqual(result['completed_matches'],30);self.assertTrue((self.root/'gates/batch-01.json').exists())
        before=deepcopy(Ledger(self.root).rows)
        result=run(self.root,c,through_batch=1,provider_factory=self.factory())
        self.assertEqual(Ledger(self.root).rows,before)
        gate=self.root/'gates/batch-01.json';value=read(gate);value['requests']+=1
        import json
        gate.write_text(json.dumps(value))
        with self.assertRaisesRegex(IntegrityError,'batch gate requests'):
            run(self.root,c,through_batch=2,provider_factory=self.factory())

    def test_source_guard_failure_before_requests(self):
        def guard():raise IntegrityError('source drift')
        with self.assertRaises(IntegrityError):run(self.root,self.contract,through_batch=1,guard=guard)
        self.assertFalse((self.root/'requests').exists())

    def test_statistics(self):
        low,high=wilson(50,100)
        self.assertAlmostEqual(low,.4038315303659956);self.assertAlmostEqual(high,.5961684696340044)
        self.assertEqual(exact_mcnemar(0,0),1);self.assertEqual(exact_mcnemar(6,0),.03125)
        self.assertIsNone(wilson(0,0))

    def test_fireball_objective_categories_and_damage(self):
        from aig.arena.friendly_fire_fixtures import fixture,analyze_fireball
        for name,kind in [('empty_blast','empty'),('friendly_only','friendly_only'),
                          ('clean_cluster','enemy_only'),('mixed_blast','mixed')]:
            with self.subTest(name=name):
                state,command=fixture(name);expected=analyze_fireball(state,command)
                sim=ArenaSimulation(state);sim.execute(command);m=mechanical(sim.trace())['blue']
                self.assertEqual(m[kind+'_fireballs'],1)
                self.assertEqual(m['friendly_fireball_damage'],expected['friendly_damage'])
                self.assertEqual(m['enemy_fireball_damage'],expected['enemy_damage'])

    def test_wrong_provider_and_replay_corruption_stop(self):
        c,s,b=self.fixture();run_match(self.root,s,c,b,self.factory(STOP))
        folder=self.root/'matches'/s['match_id']
        (folder/'command-trace.json').write_text('{}')
        with self.assertRaisesRegex(IntegrityError,'artifact mutation'):verify_match(folder,contract=c)

    def test_analysis_pairing_limits_and_heuristic_record(self):
        c,s,b=self.fixture();r=run_match(self.root,s,c,b,self.factory(ArenaProviderError('timeout')))
        r2=deepcopy(r);r2.update(arm='bounded',winner='blue',luna_outcome='win',terminal_cause='CORE_DESTRUCTION')
        comparison=paired([r,r2],'bounded','strict',inference=False)
        self.assertEqual((comparison['win_rate_difference'],comparison['win_gains']),(1,1))
        self.assertIsNone(comparison['exact_mcnemar_p'])
        self.assertEqual(summarize([r],True)['wins'],1)
        self.assertEqual(summarize([r],True)['per_turn']['provider_requests'],None) # no heuristic turn before forfeit

    def test_wrong_provider_blocked_before_request(self):
        c,s,b=self.fixture()
        def factory(slot,book):
            p=JournalProvider(OpenAISettings(),slot=slot,ledger=book,fake=True)
            p.name='ollama';return p
        with self.assertRaisesRegex(IntegrityError,'provider/control binding'):
            run_match(self.root,s,c,b,factory)
        self.assertEqual(b.rows,[])


if __name__=='__main__':unittest.main()
