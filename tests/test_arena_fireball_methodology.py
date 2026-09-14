import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from aig.arena import friendly_fire_methodology as m
from aig.arena.ai.contracts import ArenaTurnPlan, action_from_dict
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.friendly_fire_fixtures import fixture
from aig.arena.snapshots import canonical_json, digest

PLAN=m.ROOT/'artifacts/arena-luna-friendly-fire/plan-v1.json'

def plan(*actions):
    return ArenaTurnPlan(tuple(action_from_dict(a) for a in actions))

def attack(uid='mage'):
    return dict(type='attack',unit_id=uid,target_id='enemy')

def fireball():
    return dict(type='fireball',unit_id='mage',target_position=dict(x=4,y=2))

class Fake(m.LunaBehaviorProvider):
    calls=0
    def request(self,messages,record):
        type(self).calls+=1
        record['metrics']=dict(input_tokens=10,output_tokens=5)
        return canonical_json(ArenaTurnPlan().to_dict())

class MethodologyTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.method=self.root/'method.json'
        m.prepare_methodology(PLAN,self.method)
        self.batch=self.root/'batch'
        # Any accidental transport usage fails this offline suite.
        guard=patch('openai.resources.responses.responses.Responses.create',side_effect=AssertionError('live forbidden'))
        guard.start()
        self.addCleanup(guard.stop)

    def run_arm(self,kind=Fake,prompt=m.OLD_PROMPT):
        return m.run_corrected(PLAN,self.method,prompt,self.batch,provider_factory=kind)

    def test_preservation(self):
        frozen=json.loads((m.ROOT/'tests/fixtures/arena-fireball-methodology-preservation.json').read_text())
        for p,h in frozen.items():
            self.assertEqual(m.sha(m.ROOT/p),h,p)

    def test_truncation_continues_without_retry(self):
        class Truncate(Fake):
            calls=0
            def request(self,messages,record):
                type(self).calls+=1
                # The second fixture has ally; it is deliberately out of attack range.
                if type(self).calls==2:
                    return canonical_json(plan(attack(),attack('ally'),attack()).to_dict())
                return canonical_json(ArenaTurnPlan().to_dict())
        r=self.run_arm(Truncate)
        self.assertEqual(r['status'],'complete')
        self.assertEqual(Truncate.calls,24)
        self.assertEqual(r['runs'][1]['invalid_action_index'],1)
        self.assertEqual(r['runs'][1]['executed_ap'],1)
        self.assertEqual(r['runs'][1]['planned_ap'],3)
        self.assertEqual(r['runs'][2]['fixture'],'clean_cluster')
        self.assertTrue(all(x['replay_matches'] for x in r['runs']))

    def test_fireball_before_truncation(self):
        state,_=fixture('friendly_only')
        r=m.evaluate(state,plan(fireball(),attack('ally')))
        self.assertEqual(len(r['executed_fireballs']),1)
        self.assertEqual(r['executed_fireballs'][0]['category'],'ENEMY_ONLY')
        self.assertEqual(r['executed_fireballs'][0]['enemy_damage'],4)
        self.assertTrue(r['execution_truncated'])
        self.assertEqual(r['ap_before_truncation'],2)
        self.assertEqual(r['fireballs_before_truncation'],1)
        self.assertTrue(r['replay_matches'])

    def test_fireball_after_truncation(self):
        state,_=fixture('friendly_only')
        r=m.evaluate(state,plan(attack('ally'),fireball()))
        self.assertEqual(len(r['planned_but_unreached']),1)
        self.assertEqual(r['planned_but_unreached'][0]['action_index'],1)
        self.assertNotIn('enemy_damage',r['planned_but_unreached'][0])
        self.assertEqual(r['executed_fireballs'],[])
        self.assertEqual(r['executed_ap'],0)

    def test_no_fireball_and_terminal(self):
        state,_=fixture('empty_blast')
        r=m.evaluate(state,plan(attack(),attack(),attack(),fireball()))
        self.assertEqual(r['executed_fireballs'],[])
        self.assertEqual(r['planned_but_unreached'],[])
        self.assertEqual(r['unexecuted_fireballs'][0]['status'],'unreached_after_terminal')
        self.assertEqual(r['terminal_result'],'blue')
        self.assertTrue(r['replay_matches'])

    def test_categories(self):
        for name,expected in [('empty_blast','EMPTY'),('friendly_only','FRIENDLY_ONLY'),('clean_cluster','ENEMY_ONLY'),('mixed_blast','MIXED')]:
            state,cmd=fixture(name)
            self.assertEqual(m.classify(m.analyze_fireball(state,cmd)),expected)

    def test_no_fireball_counts(self):
        state,_=fixture('empty_blast')
        row=m.evaluate(state,plan(attack()))|dict(fixture='empty_blast',trial=1)
        result=m.aggregate([row])
        self.assertEqual(result['planned_fireballs'],0)
        self.assertEqual(result['executed_fireballs'],0)
        self.assertEqual(result['zero_enemy'],0)

    def test_authoritative_inconsistency_hard_stop(self):
        with patch.object(m,'evaluate',side_effect=ValueError('inconsistent state')):
            r=self.run_arm()
        self.assertEqual(r['hard_stop'],'authoritative_or_artifact_failure')
        self.assertEqual(len(r['unstarted_trials']),23)

    def test_failed_repairs_continue_and_combined_ceiling(self):
        class Invalid(Fake):
            calls=0
            def request(self,messages,record):
                type(self).calls+=1
                return 'invalid'
        old=self.run_arm(Invalid)
        new=self.run_arm(Invalid,m.PROMPT_VERSION)
        self.assertEqual(old['status'],'complete')
        self.assertEqual(new['status'],'complete')
        self.assertEqual(Invalid.calls,96)
        self.assertEqual(new['combined_requests'],96)
        self.assertEqual(old['aggregate']['failed_provider_trials'],24)
        self.assertTrue(all(r['replay_matches'] for r in old['runs']))
        with self.assertRaises(FileExistsError):
            self.run_arm(Invalid)
        self.assertEqual(Invalid.calls,96)

    def test_replay_hard_stop(self):
        original=m.evaluate
        def bad(*args):
            return original(*args)|dict(replay_matches=False)
        with patch.object(m,'evaluate',side_effect=bad):
            r=self.run_arm()
        self.assertEqual(r['hard_stop'],'replay_mismatch')
        self.assertEqual(len(r['unstarted_trials']),23)
        with self.assertRaises(ValueError):
            self.run_arm(prompt=m.PROMPT_VERSION)

    def test_replay_exception_preserves_trace(self):
        state,_=fixture('friendly_only')
        with patch.object(m,'replay',side_effect=ValueError('bad replay')):
            r=m.evaluate(state,plan(fireball(),attack('ally')))
        self.assertFalse(r['replay_matches'])
        self.assertTrue(r['command_trace']['entries'])
        self.assertEqual(len(r['executed_fireballs']),1)

    def test_source_drift_boundary(self):
        actual=m.sources()
        with patch.object(m,'sources',side_effect=[actual,{}]):
            r=self.run_arm()
        self.assertEqual(r['hard_stop'],'source_drift')
        self.assertEqual(r['requests'],0)

    def test_wrong_provider(self):
        class Wrong(Fake):
            name='ollama'
        r=self.run_arm(Wrong)
        self.assertEqual(r['hard_stop'],'provider_contract_mismatch')
        self.assertEqual(r['requests'],0)

    def test_fallback_hard_stop(self):
        class Fallback(Fake):
            @property
            def last_trace(self):
                t=super().last_trace
                if t:
                    t['fallback_used']=True
                return t
        r=self.run_arm(Fallback)
        self.assertEqual(r['hard_stop'],'provider_or_fallback')

    def test_request_accounting_hard_stop(self):
        class Corrupt(Fake):
            @property
            def last_trace(self):
                t=super().last_trace
                if t:
                    t['attempts']=[]
                return t
        r=self.run_arm(Corrupt)
        self.assertEqual(r['hard_stop'],'request_accounting')
        self.assertEqual(len(r['unstarted_trials']),23)

    def test_infrastructure_stops(self):
        class Down(Fake):
            def request(self,messages,record):
                raise ArenaProviderError('connection_failure')
        r=self.run_arm(Down)
        self.assertEqual(r['hard_stop'],'connection_failure')
        self.assertEqual(r['requests'],1)
        self.assertTrue(r['runs'][0]['replay_matches'])

    def test_corrupt_plan_before_request(self):
        p=self.root/'bad-plan.json'
        p.write_text(PLAN.read_text()+' ')
        with self.assertRaises(ValueError):
            m.run_corrected(p,self.method,m.OLD_PROMPT,self.batch,provider_factory=Fake)

    def test_ledger_corruption(self):
        self.run_arm()
        path=self.batch/'request-ledger.json'
        data=json.loads(path.read_text())
        data['total']+=1
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.run_arm(prompt=m.PROMPT_VERSION)

    def test_ceiling_unstarted(self):
        self.batch.mkdir()
        ledger=dict(identity=dict(methodology_sha256=m.sha(self.method),plan_sha256=m.sha(PLAN)),
                    arms={m.OLD_PROMPT:48,m.PROMPT_VERSION:48},total=96)
        ledger['checksum']=digest(ledger)
        m.write(self.batch/'request-ledger.json',ledger)
        r=self.run_arm()
        self.assertEqual(r['hard_stop'],'request_ceiling')
        self.assertEqual(len(r['unstarted_trials']),24)
        self.assertEqual(r['runs'],[])
