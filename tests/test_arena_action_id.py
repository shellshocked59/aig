"""Offline action-ID contract, transport, execution, replay and preservation tests."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from aig.arena.ai.action_id import *
from aig.arena.ai.observation import (action_id_catalog, observation_facts, resolve_observation_version,
                                      OBSERVATION_VERSION)
from aig.arena.ai.contracts import *
from aig.arena.ai.stepwise import ArenaStepController, HeuristicArenaStepProvider
from aig.arena.action_id_benchmark import benchmark_action_id, verify_action_id_trial, BENCHMARK_VERSION
from aig.arena.benchmark_versions import frozen_probe, probe_set, artifact
from aig.arena.commands import ACTION_COSTS, apply_command
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import to_snapshot
from aig.settings import Settings, OpenAISettings
from aig.state import Position


def raw(value):
    return canonical_json(dict(action_id=value))


class Scripted:
    name = "heuristic"
    def __init__(self, *choices):
        self.choices = list(choices)
        self.observations = []

    def create_step_choice(self, observation):
        self.observations.append(observation)
        value = self.choices.pop(0) if self.choices else ArenaActionIdDecision(None)
        return value(observation) if callable(value) else value


def select(action):
    return lambda obs: choice_for_action(action, obs)


class ActionIdTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for target in ("urllib.request.OpenerDirector.open", "httpx.Client.send", "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("live inference forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def obs(self, probe="snipe_vs_basic"):
        return build_observation(frozen_probe(probe), version=OBSERVATION_V3)

    def test_explicit_version_default_and_roundtrip(self):
        self.assertEqual(resolve_observation_version(), OBSERVATION_VERSION)
        self.assertEqual(resolve_observation_version(OBSERVATION_V3), OBSERVATION_V3)
        for name in probe_set()["probes"]:
            state = frozen_probe(name)
            v1 = build_observation(state)
            v2 = build_observation(state, version=OBSERVATION_V2)
            v3 = build_observation(state, version=OBSERVATION_V3)
            self.assertEqual(observation_facts(v3), v1.to_dict())
            self.assertEqual(observation_facts(v3), observation_facts(v2))
            self.assertEqual(ArenaObservation.from_dict(v3.to_dict()), v3)
            self.assertEqual(to_snapshot(simulation_state(v3)), to_snapshot(state))
            self.assertEqual(v3, build_observation(deepcopy(state), version=OBSERVATION_V3))
            self.assertEqual(v3.hash, build_observation(state, version=OBSERVATION_V3).hash)
            expected = v2.to_dict()
            actual = v3.to_dict()
            actual["schema_version"] = OBSERVATION_V2
            actual["legal_actions"] = [e["action"] for e in actual["legal_actions"]]
            self.assertEqual(expected, actual)

    def test_every_catalog_entry_unique_ordered_legal_ap(self):
        for name in probe_set()["probes"]:
            obs = self.obs(name)
            entries = obs.to_dict()["legal_actions"]
            self.assertEqual(len(entries), len({e["id"] for e in entries}))
            self.assertEqual(len(entries), len({canonical_json(e["action"]) for e in entries}))
            v2 = build_observation(frozen_probe(name), version=OBSERVATION_V2)
            self.assertEqual(entries, action_id_catalog(v2.to_dict()["legal_actions"]))
            self.assertEqual(catalog_hash(obs), digest([[e["id"],e["action"]] for e in entries]))
            for entry in entries:
                choice = parse_choice(raw(entry["id"]), obs)
                action = resolve_action(choice,obs)
                self.assertEqual(action.to_dict(),entry["action"])
                state = simulation_state(obs)
                before = state.action_points_remaining
                apply_command(state,action_command(action,state.active_player_id))
                self.assertEqual(before-state.action_points_remaining,ACTION_COSTS[action.type])

    def test_namespace_capacity(self):
        for count in (0,1,99,100,999,1000,10001):
            entries=action_id_catalog([{}]*count)
            self.assertEqual(len({e["id"] for e in entries}),count)
            if count:
                self.assertEqual(entries[-1]["id"],f'A{count:0{max(2,len(str(count)))}d}')

    def test_forged_catalog_rejected(self):
        data=self.obs().to_dict()
        data['legal_actions'][0]['id']='A99'
        with self.assertRaises(ValueError): ArenaObservation.from_dict(data)

    def test_schema_and_errors(self):
        obs=self.obs()
        self.assertEqual(parse_choice(raw(None),obs),ArenaActionIdDecision(None))
        for value,category in [('not json','malformed_json'), ('{"action_id":null,"action_id":null}','malformed_json'),
            ('{}','schema_validation'), ('{"action_id":3}','schema_validation'),
            ('{"action_id":false}','schema_validation'), ('{"action_id":null,"extra":1}','schema_validation'),
            ('{"type":"end_turn"}','schema_validation'), (raw('A999999'),'invalid_action_id'),
            (raw('end_turn'),'invalid_action_id'), (raw(''),'invalid_action_id')]:
            with self.subTest(value=value),self.assertRaises(ArenaProviderError) as caught:
                parse_choice(value,obs)
            self.assertEqual(caught.exception.category,category)
        self.assertEqual(decision_schema()['properties']['action_id']['type'],['string','null'])
        self.assertFalse(decision_schema()['additionalProperties'])

    def fake(self,kind,outputs,repair=True):
        captured=[]
        def content():
            value=outputs.pop(0)
            if isinstance(value,Exception): raise value
            return value
        if kind=='ollama':
            def request(url,body,timeout):
                captured.append(json.loads(body))
                return canonical_json(dict(done=True,message=dict(content=content()),prompt_eval_count=100,eval_count=5))
            provider=OllamaArenaActionIdProvider(Settings().ollama,requester=request,repair=repair,secrets=('secret-canary',))
        else:
            def request(**kwargs):
                captured.append(kwargs)
                return NS(status='completed',error=None,id='response',_request_id='request',
                    output=[NS(type='message',role='assistant',status='completed',content=[NS(type='output_text',text=content())])],
                    usage=NS(input_tokens=100,output_tokens=5,total_tokens=105,
                             input_tokens_details=NS(cached_tokens=0),output_tokens_details=NS(reasoning_tokens=0)))
            provider=OpenAIArenaActionIdProvider(OpenAISettings(api_key='secret-canary'),client=NS(responses=NS(create=request)),repair=repair)
        return provider,captured

    def test_both_transports_schema_success_end_and_repairs(self):
        obs=self.obs()
        legal=obs.to_dict()['legal_actions'][0]['id']
        for kind in ('ollama','openai'):
            for outputs,expected,count in [([raw(legal)],legal,1),([raw(None)],None,1),
                ([raw('A999'),raw(legal)],legal,2),([raw('A999'),raw(None)],None,2)]:
                with self.subTest(kind=kind,outputs=outputs):
                    p,captured=self.fake(kind,list(outputs))
                    choice,call=checked_choice(p,kind,obs)
                    self.assertTrue(call['success'])
                    self.assertEqual(choice.action_id,expected)
                    self.assertEqual(call['provider_requests'],count)
                    schema=captured[0]['format'] if kind=='ollama' else captured[0]['text']['format']['schema']
                    self.assertEqual(schema,decision_schema())
                    if count==2:
                        self.assertEqual(call['attempts'][0]['error_category'],'invalid_action_id')
                        self.assertEqual(call['attempts'][0]['rejected_decision']['repair_result'],'succeeded')
                        messages=captured[-1]['messages'] if kind=='ollama' else captured[-1]['input']
                        self.assertIn('CURRENT',messages[-1]['content'])
                        self.assertIn('A999',messages[-1]['content'])
                        self.assertIn(obs.canonical,canonical_json(messages).replace('\\"','"'))
                    self.assertNotIn('secret-canary',canonical_json(call))

    def test_both_failed_repairs_and_disabled_repair(self):
        for kind in ('ollama','openai'):
            for enabled,count,category in ((True,2,'repair_failed'),(False,1,'invalid_action_id')):
                p,captured=self.fake(kind,[raw('A999')]*3,repair=enabled)
                sim=ArenaSimulation(frozen_probe('snipe_vs_basic'))
                turn=ArenaActionIdController(p).run_turn(sim)
                self.assertEqual(turn['error_category'],category)
                self.assertEqual(len(captured),count)
                self.assertEqual(sim.trace()['entries'],[])
                self.assertFalse(turn['explicit_early_end'])
                self.assertEqual(turn['steps'][0]['attempts'][0]['error_category'],'invalid_action_id')

    def test_sanitized_rejections_no_raw_text(self):
        for value in ('secret-canary','A01 secret-canary','A'+'9'*1000):
            p,_=self.fake('ollama',[raw(value)],repair=False)
            _,call=checked_choice(p,'ollama',self.obs())
            self.assertNotIn(value,canonical_json(call))
            self.assertIn(REDACTED,canonical_json(call))
            self.assertIsNone(p.last_trace['attempts'][0]['raw_content'])

    def test_wrong_observation_no_request(self):
        for kind in ('ollama','openai'):
            p,captured=self.fake(kind,[raw(None)])
            for version in (OBSERVATION_VERSION,OBSERVATION_V2):
                with self.assertRaises(ArenaProviderError):
                    p.create_step_choice(build_observation(frozen_probe('snipe_vs_basic'),version=version))
            self.assertEqual(captured,[])
            with self.assertRaises(TypeError):p.create_turn_plan(self.obs())

    def test_provider_mismatch_and_transport_failure(self):
        p,_=self.fake('ollama',[raw(None)])
        _,call=checked_choice(p,'openai',self.obs())
        self.assertEqual(call['error_category'],'provider_mismatch')
        p,_=self.fake('ollama',[OSError('secret-canary')])
        _,call=checked_choice(p,'ollama',self.obs())
        self.assertFalse(call['success'])
        self.assertEqual(call['provider_requests'],1)
        self.assertNotIn('secret-canary',canonical_json(call))

    def test_attack_finish_refresh(self):
        state=frozen_probe('fireball_friendly_fire');state.units['enemy2'].hp=1
        state.units['actor'].position=Position(3,3)
        attack,finish=AttackAction('actor','enemy2'),FinishAction('actor','enemy2')
        def after(obs):
            self.assertNotIn(attack.to_dict(),[e['action'] for e in obs.to_dict()['legal_actions']])
            return choice_for_action(finish,obs)
        p=Scripted(select(attack),after)
        sim=ArenaSimulation(state)
        turn=ArenaActionIdController(p).run_turn(sim)
        self.assertIsNone(turn['error_category'])
        self.assertNotIn('enemy2',sim.state.units)
        self.assertFalse(any(e['action'].get('target_id')=='enemy2' for e in p.observations[-1].to_dict()['legal_actions']))
        self.assertEqual([o.to_dict()['action_points_remaining'] for o in p.observations],[5,4,3])

    def test_revive_refresh(self):
        action=ReviveAction('actor','ally')
        def after(obs):
            self.assertEqual(obs.to_dict()['action_points_remaining'],3)
            entries=obs.to_dict()['legal_actions']
            self.assertNotIn(action.to_dict(),[e['action'] for e in entries])
            self.assertTrue(any(e['action']['unit_id']=='ally' for e in entries))
            return ArenaActionIdDecision(None)
        turn=ArenaActionIdController(Scripted(select(action),after)).run_turn(ArenaSimulation(frozen_probe('revive_decision')))
        self.assertEqual(turn['ap_executed'],2)

    def test_bash_refresh(self):
        def after(obs):
            enemy=next(u for u in obs.to_dict()['enemy_team']['units'] if u['id']=='enemy')
            self.assertEqual((enemy['x'],enemy['y']),(4,2))
            self.assertNotIn(AttackAction('actor','enemy').to_dict(),[e['action'] for e in obs.to_dict()['legal_actions']])
            return ArenaActionIdDecision(None)
        turn=ArenaActionIdController(Scripted(select(ShieldBashAction('actor','enemy')),after)).run_turn(ArenaSimulation(frozen_probe('shield_bash_position')))
        self.assertEqual(turn['ap_executed'],1)

    def test_fireball_refresh(self):
        state=frozen_probe('fireball_friendly_fire');state.units['enemy2'].hp=4
        def after(obs):
            enemy=next(u for u in obs.to_dict()['enemy_team']['units'] if u['id']=='enemy2')
            self.assertEqual(enemy['status'],'downed')
            return ArenaActionIdDecision(None)
        turn=ArenaActionIdController(Scripted(select(FireballAction('actor',ArenaPosition(4,1))),after)).run_turn(ArenaSimulation(state))
        self.assertEqual(turn['ap_executed'],2)

    def test_local_stale_id_resolves_current_action(self):
        # Find an actual action that changes the meaning of an overlapping catalog ID.
        found=False
        for name in probe_set()['probes']:
            before=self.obs(name)
            for entry in before.to_dict()['legal_actions']:
                sim=ArenaSimulation(simulation_state(before))
                action=action_from_dict(entry['action'])
                sim.execute(action_command(action,sim.state.active_player_id))
                if sim.state.winner_player_id or not sim.state.action_points_remaining:continue
                after=build_observation(sim.state,version=OBSERVATION_V3)
                old={e['id']:e['action'] for e in before.to_dict()['legal_actions']}
                changed=next((e for e in after.to_dict()['legal_actions'] if e['id'] in old and e['action']!=old[e['id']]),None)
                if changed:
                    provider=Scripted(ArenaActionIdDecision(entry['id']),ArenaActionIdDecision(changed['id']))
                    turn=ArenaActionIdController(provider).run_turn(ArenaSimulation(simulation_state(before)))
                    self.assertEqual(turn['steps'][1]['resolved_action'],changed['action'])
                    self.assertNotEqual(turn['steps'][1]['resolved_action'],old[changed['id']])
                    found=True;break
            if found:break
        self.assertTrue(found)

    def test_ap_limits_end_and_five(self):
        for ap in (0,1,2,5):
            state=frozen_probe('finish_or_core');state.action_points_remaining=ap
            turn=ArenaActionIdController(HeuristicArenaActionIdProvider()).run_turn(ArenaSimulation(state))
            self.assertEqual(turn['ap_executed'],ap)
            self.assertLessEqual(turn['steps_requested'],5)
        turn=ArenaActionIdController(Scripted()).run_turn(ArenaSimulation(frozen_probe('finish_or_core')))
        self.assertTrue(turn['explicit_early_end']);self.assertEqual(turn['ap_executed'],0)

    def test_execution_defect_stops_without_end(self):
        sim=ArenaSimulation(frozen_probe('team_elimination'))
        with patch.object(sim,'execute',side_effect=ValueError('defect')):
            turn=ArenaActionIdController(HeuristicArenaActionIdProvider()).run_turn(sim)
        self.assertEqual(turn['error_category'],'catalog_execution_defect')
        self.assertEqual(sim.trace()['entries'],[])

    def test_heuristic_commands_identical_and_replay(self):
        for name in probe_set()['probes']:
            a,b=ArenaSimulation(frozen_probe(name)),ArenaSimulation(frozen_probe(name))
            ta=ArenaActionIdController(HeuristicArenaActionIdProvider()).run_turn(a)
            tb=ArenaStepController(HeuristicArenaStepProvider()).run_turn(b)
            self.assertEqual(a.trace(),b.trace())
            self.assertEqual(ta['action_sequence'],tb['action_sequence'])
            self.assertEqual(replay(a.trace()).trace(),a.trace())

    def test_benchmark_and_replay_tampering(self):
        report=benchmark_action_id(output=self.root/'baseline')
        self.assertEqual((report['validTrials'],report['providerRequests']),(7,0))
        self.assertEqual(report['experiment']['benchmarkVersion'],BENCHMARK_VERSION)
        self.assertEqual(artifact('arena-benchmark-v3')['control_version'],'arena-control-stepwise-v1')
        directory=Path(report['runs'][0]['directory'])
        original=json.loads((directory/'turn.json').read_text())
        for key,value in [('action_catalog_hash','bad'),('selected_action_id','A999'),('resolved_action',None),
                          ('ap_after',99),('observation_hash','bad'),('command_index',99),('selected_current_legal',False)]:
            data=deepcopy(original);data['steps'][0][key]=value
            (directory/'turn.json').write_text(json.dumps(data))
            self.assertFalse(verify_action_id_trial(directory)['success'],key)
        with self.assertRaises(FileExistsError):benchmark_action_id(output=self.root/'baseline')

    def test_benchmark_ceiling_precedes_provider_creation(self):
        factory=Mock(side_effect=AssertionError('no provider'))
        with self.assertRaises(ValueError):
            benchmark_action_id(output=self.root/'bad',provider='ollama',request_ceiling=-1,provider_factory=factory)
        factory.assert_not_called()

    def test_fake_model_benchmark_no_preflight_accounted(self):
        def factory(settings,name):
            p,_=self.fake(name,[raw(None)]*7)
            return p
        report=benchmark_action_id(output=self.root/'fake',provider='ollama',provider_factory=factory)
        self.assertEqual((report['validTrials'],report['providerRequests']),(7,7))
        self.assertEqual(report['experiment']['providers']['ollama']['modelConfigVersion'],'qwen-config-v1')
        self.assertEqual(report['experiment']['preflightRequests'],0)

    def test_fake_model_failed_prefix_replays(self):
        def factory(settings,name):
            return self.fake(name,[raw('A999'),raw('A999')])[0]
        report=benchmark_action_id(output=self.root/'failure',provider='ollama',probe='revive_decision',provider_factory=factory)
        self.assertEqual(report['status'],'completed_with_failures')
        self.assertEqual(report['providerRequests'],2)
        self.assertEqual(report['trialsStarted'],1)
        self.assertTrue(report['runs'][0]['verification']['success'])


    def test_request_ceiling_denies_repair_preserves_prefix(self):
        from aig.arena.fullmatch_benchmark import RequestBudget
        p,captured=self.fake('ollama',[raw('A999'),raw(None)])
        budget=RequestBudget(1)
        p.before_request=budget.take
        sim=ArenaSimulation(frozen_probe('snipe_vs_basic'))
        turn=ArenaActionIdController(p).run_turn(sim)
        self.assertEqual(turn['error_category'],'request_ceiling')
        self.assertEqual((budget.used,len(captured),turn['provider_requests']),(1,1,1))
        self.assertEqual(sim.trace()['entries'],[])
        self.assertEqual(turn['steps'][0]['attempts'][0]['rejected_decision']['repair_result'],'not_attempted')

    def test_schema_invalid_repair_success_and_no_raw_persistence(self):
        for kind in ('ollama','openai'):
            for invalid,category in [('secret-canary','malformed_json'),('{"action_id":null,"reason":"secret-canary"}','schema_validation')]:
                p,captured=self.fake(kind,[invalid,raw(None)])
                choice,call=checked_choice(p,kind,self.obs())
                self.assertEqual(choice,ArenaActionIdDecision(None))
                self.assertEqual(call['attempts'][0]['error_category'],category)
                self.assertEqual(call['attempts'][0]['rejected_decision']['repair_result'],'succeeded')
                self.assertNotIn('secret-canary',canonical_json(call))
                messages=captured[-1]['messages'] if kind=='ollama' else captured[-1]['input']
                self.assertNotIn('secret-canary',canonical_json(messages))

    def test_removed_local_id_unknown_after_ap_change(self):
        state=frozen_probe('fireball_friendly_fire')
        before=build_observation(state,version=OBSERVATION_V3)
        state.action_points_remaining=1
        after=build_observation(state,version=OBSERVATION_V3)
        old={e['id'] for e in before.to_dict()['legal_actions']}
        new={e['id'] for e in after.to_dict()['legal_actions']}
        self.assertTrue(old-new)
        with self.assertRaises(ArenaProviderError) as caught:
            parse_choice(raw(sorted(old-new)[-1]),after)
        self.assertEqual(caught.exception.category,'invalid_action_id')

    def test_benchmark_invalid_id_rates_include_failed_attempts(self):
        def factory(settings,name):
            return self.fake(name,[raw('A999'),raw('A999')])[0]
        report=benchmark_action_id(output=self.root/'rates',provider='ollama',probe='revive_decision',provider_factory=factory)
        self.assertEqual(report['firstResponseValidRate'],0)
        self.assertEqual(report['firstResponseSchemaValidRate'],1)
        self.assertEqual(report['validActionIdRate'],0)
        self.assertEqual(report['invalidActionIdAttempts'],2)
        self.assertEqual(report['inferenceAllAttempts']['statically_invalid_initial_outputs'],1)

    def test_expanded_schedule_below_theoretical_ceiling(self):
        def factory(settings,name):
            return self.fake(name,[raw(None)]*28)[0]
        report=benchmark_action_id(output=self.root/'expanded',provider='ollama',probe_trials=4,
                                  request_ceiling=180,provider_factory=factory)
        self.assertEqual((report['status'],report['validTrials'],report['providerRequests']),('complete',28,28))

    def test_failure_consumes_trial_and_continues(self):
        def factory(settings,name):
            return self.fake(name,[raw('A999'),raw('A999'),raw(None)])[0]
        report=benchmark_action_id(output=self.root/'continue',provider='ollama',probe='revive_decision',
                                  probe_trials=2,request_ceiling=3,provider_factory=factory)
        self.assertEqual((report['trialsStarted'],report['validTrials'],report['providerRequests']),(2,1,3))
        self.assertTrue(all(r['verification']['success'] for r in report['runs']))

    def test_benchmark_cap_during_repair_and_between_trials(self):
        for outputs,limit in (([raw('A999'),raw(None)],1),([raw(None)]*3,2)):
            def factory(settings,name):
                return self.fake(name,list(outputs))[0]
            report=benchmark_action_id(output=self.root/f'cap-{limit}',provider='ollama',probe='revive_decision',
                                      probe_trials=4,request_ceiling=limit,provider_factory=factory)
            self.assertEqual(report['status'],'request_ceiling')
            self.assertEqual(report['providerRequests'],limit)
            self.assertEqual(report['recordedProviderRequests'],limit)
            self.assertTrue(all(r['verification']['success'] for r in report['runs']))

    def test_benchmark_integrity_failure_stops_schedule(self):
        for category in ('source_mutation','replay_mismatch','provider_mismatch','accounting_failed'):
            def factory(settings,name):
                return self.fake(name,[raw(None)]*4)[0]
            if category=='source_mutation':
                guard=patch('aig.arena.action_id_benchmark.frozen_guard',return_value=Mock(side_effect=ArenaProviderError(category)))
            elif category=='replay_mismatch':
                guard=patch('aig.arena.action_id_benchmark.verify_action_id_trial',return_value={'success':False})
            elif category=='accounting_failed':
                guard=patch('aig.arena.fullmatch_benchmark.RequestBudget.take')
            else:
                original=checked_choice
                def mismatch(*args):
                    choice,call=original(*args)
                    call['fallback_used']=True
                    return choice,call
                guard=patch('aig.arena.ai.action_id.checked_choice',side_effect=mismatch)
            with guard:
                report=benchmark_action_id(output=self.root/category,provider='ollama',probe_trials=4,
                                          request_ceiling=180,provider_factory=factory)
            self.assertEqual(report['trialsStarted'],1)
            self.assertEqual(report['status'],category)

    def test_v2_historical_golden_hashes_unchanged(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/arena-action-id-golden.json').read_text())
        for name,record in fixture['probes'].items():
            state=frozen_probe(name)
            self.assertEqual(build_observation(state,version=OBSERVATION_V2).hash,record['v2_hash'])
            obs=build_observation(state,version=OBSERVATION_V3)
            self.assertEqual(obs.hash,record['v3_hash'])
            self.assertEqual(catalog_hash(obs),record['catalog_hash'])


if __name__=='__main__':unittest.main()
