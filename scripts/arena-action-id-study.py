"""Offline Phase 9A catalog proof and request-size study. No network operations."""
import argparse
from copy import deepcopy
import json
from math import ceil
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from aig.ai.benchmark import write_json
from aig.arena.ai.action_id import (OllamaArenaActionIdProvider, OpenAIArenaActionIdProvider,
    catalog_hash, choice_for_action, resolve_action, ArenaActionIdDecision, decision_schema)
from aig.arena.ai.observation import (ArenaObservation, OBSERVATION_V2, OBSERVATION_V3,
    build_observation, simulation_state, observation_facts)
from aig.arena.ai.stepwise import OllamaArenaStepProvider, OpenAIArenaStepProvider
from aig.arena.ai.contracts import action_from_dict, action_command, ArenaTurnPlan, turn_plan_schema
from aig.arena.ai.validation import openai_turn_plan_schema
from aig.arena.benchmark_versions import frozen_probe, probe_set
from aig.arena.commands import apply_command, ACTION_COSTS
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json, to_snapshot
from aig.settings import Settings, OpenAISettings

HISTORY = ('arena-phase7f-stepwise-reliability-20260913-01',
           'arena-phase8c-qwen-fullmatch-repair-v1-01','arena-phase8c-qwen-fullmatch-repair-v2-01')


def catalog_proof(state):
    v2,v3=[build_observation(state,version=v) for v in (OBSERVATION_V2,OBSERVATION_V3)]
    entries=v3.to_dict()['legal_actions']
    actions=[e['action'] for e in entries]
    assert actions==v2.to_dict()['legal_actions']
    assert len({e['id'] for e in entries})==len(entries)==len({canonical_json(a) for a in actions})
    assert observation_facts(v2)==observation_facts(v3)
    assert to_snapshot(simulation_state(v3))==to_snapshot(state)
    assert ArenaObservation.from_dict(v3.to_dict())==v3
    for e in entries:
        detached=deepcopy(state)
        action=resolve_action(ArenaActionIdDecision(e['id']),v3)
        apply_command(detached,action_command(action,state.active_player_id))
        assert state.action_points_remaining-detached.action_points_remaining==ACTION_COSTS[action.type]
    return dict(v2_hash=v2.hash,v3_hash=v3.hash,catalog_hash=catalog_hash(v3),
                legal_actions=len(entries),first_action_execution_checks=len(entries),equivalent=True)


def captured_request(observation,kind,action_id):
    captured=[]
    if kind=='ollama':
        def request(url,body,timeout):
            captured.append(json.loads(body))
            return canonical_json(dict(done=True,message=dict(content='{}')))
        provider=(OllamaArenaActionIdProvider if action_id else OllamaArenaStepProvider)(Settings().ollama,requester=request)
    else:
        def request(**kwargs):
            captured.append(kwargs)
            return NS(status='completed',error=None,id=None,_request_id=None,usage=None,
                output=[NS(type='message',role='assistant',status='completed',content=[NS(type='output_text',text='{}')])])
        provider=(OpenAIArenaActionIdProvider if action_id else OpenAIArenaStepProvider)(
            OpenAISettings(api_key='offline-placeholder'),client=NS(responses=NS(create=request)))
    provider.request([dict(role='user',content='ArenaObservation:\n'+observation.canonical)],dict(metrics={}))
    return captured[0]


def measure(state,label,anchor=None):
    v2,v3=[build_observation(state,version=v) for v in (OBSERVATION_V2,OBSERVATION_V3)]
    size=lambda data:len(canonical_json(data).encode('utf-8'))
    row=dict(label=label,v2_bytes=len(v2.canonical.encode()),v3_bytes=len(v3.canonical.encode()),
             catalog_size=len(v3.to_dict()['legal_actions']),v2_hash=v2.hash,v3_hash=v3.hash)
    row['growth_percent']=round(100*(row['v3_bytes']/row['v2_bytes']-1),2)
    row['requests']={kind:{'structured_bytes':size(captured_request(v2,kind,False)),
                           'action_id_bytes':size(captured_request(v3,kind,True))} for kind in ('ollama','openai')}
    s=Settings().ollama
    request=row['requests']['ollama']
    estimate=sorted(ceil(request['action_id_bytes']/d) for d in (3,4))
    row['unanchored_qwen_input_token_estimate']=estimate
    row['context_after_reserved_output']=[s.context_size-s.max_output_tokens-estimate[1],s.context_size-s.max_output_tokens-estimate[0]]
    if anchor is not None:
        delta=size(captured_request(v3,'ollama',True)['messages'])-size(captured_request(v2,'ollama',False)['messages'])
        estimated=sorted(ceil(anchor+delta/d) for d in (3,4))
        row['historical_structured_input_tokens']=anchor
        row['anchored_qwen_input_token_estimate']=estimated
        row['anchored_context_after_reserved_output']=[s.context_size-s.max_output_tokens-estimated[1],s.context_size-s.max_output_tokens-estimated[0]]
    entries=v3.to_dict()['legal_actions']
    if entries:
        action=action_from_dict(entries[0]['action'])
        row['representative_output']=dict(action=action.to_dict(),structured_bytes=size(ArenaTurnPlan((action,)).to_dict()),
            action_id_bytes=size(choice_for_action(action,v3).to_dict()))
    return row


def study(history):
    proofs=[dict(source='arena-probes-v1:'+n,**catalog_proof(frozen_probe(n))) for n in probe_set()['probes']]
    failures=[]; historical=[]
    for root in HISTORY:
        paths=sorted((history/root).rglob('turn.json'))
        if not paths:raise ValueError('missing historical turns: '+root)
        for path in paths:
            turn=json.loads(path.read_text())
            for index,row in enumerate(turn.get('steps',[])):
                if row.get('requested_provider')!='ollama':continue
                obs=ArenaObservation.from_dict(row['observation'])
                assert obs.hash==row['observation_hash']
                historical.append((path,index,row,obs))
                invalid=[a for a in row['attempts'] if a.get('error_category')=='invalid_reference']
                if not invalid:continue
                state=simulation_state(obs)
                proof=catalog_proof(state)
                v3=build_observation(state,version=OBSERVATION_V3)
                legal=[e['action'] for e in v3.to_dict()['legal_actions']]
                rejected=[]
                for attempt in invalid:
                    plan=attempt.get('rejected_decision',{}).get('parsed_decision')
                    if plan is not None:
                        assert plan['actions'] and any(a not in legal for a in plan['actions'])
                    rejected.append(dict(historical_action_available=plan is not None,
                                         invalid_action_absent=any(a not in legal for a in plan['actions']) if plan else None,
                                         parsed_decision=plan))
                failures.append(dict(source=path.as_posix(),step_index=index,**proof,rejections=rejected))
    mid=next(x for x in historical if x[3].to_dict()['turn']>=4)
    measurements=[measure(frozen_probe('snipe_vs_basic'),'probe:snipe_vs_basic')]
    measurements.append(measure(ArenaSimulation().state,'opening-full-match'))
    for label,item in [('historical-early',historical[0]),('midgame',mid)]:
        path,index,row,obs=item
        measurements.append(dict(source=path.as_posix(),step_index=index,
            **measure(simulation_state(obs),label,row['attempts'][0]['metrics'].get('prompt_eval_count'))))
    s=Settings().ollama
    return dict(proofs=proofs,historical_failures=failures,measurements=measurements,
        schemas={k:len(canonical_json(v).encode()) for k,v in [('ollama_structured',turn_plan_schema()),
            ('openai_structured',openai_turn_plan_schema()),('action_id_both',decision_schema())]},
        context=dict(configured=s.context_size,reserved_output=s.max_output_tokens,
            method='Offline estimates, not Qwen tokenization: canonical request UTF-8 bytes / 3..4. Anchored variants use historical prompt_eval_count plus message-byte delta / 3..4 (schema sent out of band; token effect unknown). Transport bytes are not exact rendered prompt bytes; no fit guarantee.'),
        summary=dict(probe_states=len(proofs),historical_invalid_reference_states=len(failures),
            unique_failure_states=len({r['v2_hash'] for r in failures}),
            historical_invalid_attempts=sum(len(r['rejections']) for r in failures),
            historical_rejected_outputs_available=sum(a['historical_action_available'] for r in failures for a in r['rejections']),
            first_action_execution_checks=sum(r['first_action_execution_checks'] for r in proofs+failures)),
        interpretation='Structural evidence only. Missing Phase 7F rejected objects cannot be reconstructed. Valid-ID selection and tactics require separately authorized live testing.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history',type=Path,default=Path('.local'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('output must be new')
    with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('offline only')), \
         patch('httpx.Client.send',side_effect=AssertionError('offline only')):
        result=study(args.history)
    write_json(args.output,result)
    print(canonical_json(result['summary']))


if __name__=='__main__':main()
