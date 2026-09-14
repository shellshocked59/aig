"""Offline tests: sockets forbidden, real transitions and fake provider transport."""
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from aig.arena.mechanics_oracle import Bounds, evaluate, score, satisfies
from aig.arena.tactical_literacy import verify, run, SUITE, hashes
from aig.arena.tactical_literacy_fixtures import fixture, action, tile
from aig.arena.snapshots import to_snapshot, digest
from aig.arena.state import Bonus, UnitType as U, UnitStatus as S
from aig.arena.commands import attack_damage


class LiteracyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Exercise the historical runner in its exact original source scope.
        # Runtime guards stay frozen; the new binding verifies every old hash
        # plus both explicitly added experimental modules separately.
        from aig.arena.ap_budget_literacy import ADDITIONS
        from arena_candidate_scope import CANDIDATE_ADDITIONS
        original = hashes
        scope = patch('aig.arena.tactical_literacy.hashes', side_effect=lambda: {
            p: h for p, h in original().items() if p not in ADDITIONS and p not in CANDIDATE_ADDITIONS})
        scope.start()
        cls.addClassCleanup(scope.stop)
        cls.suite=verify()
        cls.probes={p['name']:p for p in cls.suite['probes']}

    def setUp(self):
        self.socket_patch=patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden'))
        self.socket_patch.start();self.addCleanup(self.socket_patch.stop)

    def test_ranges(self):
        b=Bounds(6,9)
        self.assertEqual([b.lethal(h)['classification'] for h in (5,8,10)],['guaranteed','possible','impossible'])
        self.assertEqual(b.hp_after(8),Bounds(0,2))
        self.assertTrue(b.lethal(5)['possible'])
        with self.assertRaises(ValueError):Bounds(9,6)
        with self.assertRaises(ValueError):Bounds(-1,2)
        self.assertNotIn('probability',b.lethal(8))

    def test_all_fixed_and_replayed(self):
        for p in self.suite['probes']:
            with self.subTest(probe=p['id']):
                r=evaluate(p['initial_state'],p['reference_sequence'])
                self.assertEqual(r,p['expected_mechanics']);self.assertTrue(r['replay_verified'])
                for step in r['steps']:
                    for e in step['affected']:
                        for key in ('damage','healing'):
                            self.assertEqual(e[key]['minimum'],e[key]['maximum'])
                self.assertEqual(digest(p['initial_state']),p['initial_state_hash'])

    def test_modifiers_match_authority(self):
        for bonus,pos in [(Bonus.POWER,(2,2)),(Bonus.WARD,(3,2)),(Bonus.SIEGE,(2,2))]:
            s=fixture(U.CLERIC,18,2,enemy=(3,2),actor=(2,2));tile(s,pos,bonus)
            expected=attack_damage(s,s.units['actor'],s.units['enemy'])
            r=evaluate(to_snapshot(s),[action('attack')])
            self.assertEqual(r['steps'][0]['affected'][0]['damage']['minimum'],expected)
        s=fixture(U.CLERIC,18,2,enemy=(3,2),actor=(2,2));tile(s,(3,2),Bonus.WARD)
        self.assertEqual(attack_damage(s,s.units['actor'],s.units['enemy']),1)

    def test_core_exact_and_terminal_suffix(self):
        p=self.probes['siege-True-hp-9']
        r=evaluate(p['initial_state'],p['reference_sequence']*2)
        self.assertTrue(r['terminal']);self.assertEqual(r['winner'],'blue')
        self.assertEqual(r['ignored_terminal_suffix'],1)
        self.assertTrue(r['steps'][0]['affected'][0]['guaranteed_core_destroy'])

    def test_down_finish_and_stale_suffix(self):
        down=self.probes['down']['expected_mechanics']
        self.assertEqual(next(e for e in down['final_state']['units'] if e['id']=='enemy')['status'],'downed')
        finish=self.probes['down-finish']['expected_mechanics']
        self.assertNotIn('enemy',[e['id'] for e in finish['final_state']['units']])
        self.assertEqual(self.probes['down-stale-attack']['expected_mechanics']['failure']['index'],1)

    def test_revive_and_heal(self):
        r=self.probes['revive-act']['expected_mechanics']
        self.assertEqual(r['ap_used'],3);self.assertIsNone(r['failure'])
        ally=next(e for e in r['final_state']['units'] if e['id']=='ally')
        self.assertEqual((ally['status'],ally['hp']),('active',5))
        self.assertEqual(self.probes['heal-clamp']['expected_mechanics']['steps'][0]['affected'][0]['healing']['minimum'],2)

    def test_fireball(self):
        for name,ids in [('enemy-only',{'enemy'}),('mixed',{'actor','ally','enemy'}),('friendly-only',{'actor'}),('empty',set())]:
            r=self.probes[name]['expected_mechanics']
            self.assertIsNone(r['failure'])
            self.assertEqual({e['id'] for e in r['steps'][0]['affected']},ids)
        self.assertTrue(any(e['friendly'] and e['guaranteed_down'] for e in self.probes['friendly-down']['expected_mechanics']['steps'][0]['affected']))

    def test_team_terminal_and_tie(self):
        s=fixture(U.MAGE,4,2,enemy=(3,2),actor=(2,2));del s.units['reserve'];s.units['actor'].hp=4
        r=evaluate(to_snapshot(s),[action('fireball',position=(3,2)),action('attack')])
        self.assertEqual(r['winner'],'red');self.assertEqual(len(r['steps']),1)

    def test_ap_and_position(self):
        self.assertEqual({p['ap'] for p in self.suite['probes']},set(range(1,6)))
        for name in ['ap-short','short-down-finish','revive-short','out-of-range','blocked-los']:
            self.assertIsNotNone(self.probes[name]['expected_mechanics']['failure'])
        self.assertIsNone(self.probes['move-snipe']['expected_mechanics']['failure'])
        self.assertEqual(self.probes['5-AP-snipe+snipe+snipe']['expected_mechanics']['failure']['index'],2)

    def test_equivalent_answers_and_preferences(self):
        p=dict(self.probes['two-attacks'])
        for seq in [[action('attack'),action('attack')],[action('snipe'),action('attack')]]:
            p['initial_state']=dict(p['initial_state'],action_points_remaining=3)
            self.assertTrue(score(p,seq)['objective_satisfied'])
        self.assertEqual(score(p,[])['classification'],'legal but missed opportunity')
        self.assertFalse(score(p,[])['reasoning_failure_inferred'])

    def test_guards(self):
        with patch('aig.arena.tactical_literacy.hashes',return_value={}):
            with self.assertRaisesRegex(ValueError,'drift'):verify()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'suite.json';data=json.loads(SUITE.read_text());data['payload']['repetitions']=99
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'integrity'):verify(path)

    def test_fake_transport_and_offline_artifacts(self):
        from aig.arena.ai.openai import OpenAIArenaTurnProvider
        from aig.ai.model_profiles import apply_model_profile
        from aig.settings import Settings
        settings=apply_model_profile(Settings(),'openai','luna-config-v1')
        from dataclasses import replace
        provider=OpenAIArenaTurnProvider(replace(settings.openai,api_key='fake'),client=object())
        def request(messages,record):
            record['metrics']={'input_tokens':1,'output_tokens':1}
            return json.dumps(dict(schema_version='arena-turn-plan-schema-v1',actions=[]))
        provider.request=request
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'fake'
            rows=run(out,provider=provider,repeats=1)
            self.assertEqual(len(rows),42)
            summary=json.loads((out/'summary.json').read_text())
            self.assertEqual(summary['provider_requests'],42)
            self.assertEqual(len(json.loads((out/'request-ledger.json').read_text())),42)
            with self.assertRaises(FileExistsError):run(out,repeats=1)

    def test_repair_and_ceiling_before_transport(self):
        from copy import deepcopy
        from dataclasses import replace
        from aig.arena.ai.openai import OpenAIArenaTurnProvider
        from aig.ai.model_profiles import apply_model_profile
        from aig.settings import Settings
        settings=apply_model_profile(Settings(),'openai','luna-config-v1')
        suite=deepcopy(self.suite);suite['probes']=suite['probes'][:1]
        for ceiling, expected in [(2,2),(1,1)]:
            with self.subTest(ceiling=ceiling), tempfile.TemporaryDirectory() as tmp:
                suite['request_ceiling']=ceiling
                provider=OpenAIArenaTurnProvider(replace(settings.openai,api_key='fake'),client=object())
                calls=[]
                def request(messages,record):
                    calls.append(1)
                    return 'bad' if len(calls)==1 else json.dumps(dict(schema_version='arena-turn-plan-schema-v1',actions=[]))
                provider.request=request
                out=Path(tmp)/'run'
                with patch('aig.arena.tactical_literacy.verify',return_value=suite):
                    if ceiling==1:
                        with self.assertRaises(RuntimeError):run(out,provider=provider,repeats=1)
                        self.assertTrue((out/'stopped.json').exists())
                    else:run(out,provider=provider,repeats=1)
                self.assertEqual(len(calls),expected)
                self.assertEqual(len(json.loads((out/'request-ledger.json').read_text())),expected)
                self.assertTrue((out/'01-LETHAL-001'/'attempt-outputs.json').exists())

    def test_impossible_is_not_missed_opportunity(self):
        self.assertEqual(score(self.probes['short-down-finish'],[])['classification'],'ambiguous tactical choice')

if __name__=='__main__':unittest.main()

