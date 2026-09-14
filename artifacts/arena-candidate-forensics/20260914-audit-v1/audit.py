"""Offline frozen-evidence audit. No provider construction or autonomous trials."""
import sys, socket, json, hashlib
from pathlib import Path
from copy import deepcopy
from collections import Counter

sys.dont_write_bytecode = True
def denied(*args, **kwargs):
    raise RuntimeError('Network forbidden during forensic audit')
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
sys.path.insert(0, str(Path('backend').resolve()))
from aig.arena.ai.benchmark_candidate import (CandidateObservation, candidate_observation,
    parse_candidate, candidate_schema, PROMPTS)
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.ai.contracts import action_from_dict, action_command
from aig.arena.commands import ACTION_COSTS, validate_command
from aig.arena.snapshots import canonical_json, to_snapshot
from aig.arena.replay import replay

HERE = Path(__file__).parent
BASE = Path('artifacts/arena-candidate-focused/20260914-validation-v1')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(BASE/'manifest.json')
completion=read(BASE/'completion.json')
for name, expected in completion['evidence_hashes'].items():
    assert sha(BASE/name)==expected, name
assert sha(BASE/'request-ledger.jsonl')==completion['ledger_sha256']
source_checks=[]
for name,expected in manifest['preparation']['payload']['source_hashes'].items():
    assert sha(Path(name))==expected,name
    source_checks.append(name)
assert manifest['prompts']==dict(PROMPTS)
for mode,schema in manifest['schemas'].items():
    assert schema==candidate_schema(step=mode=='stepwise',openai=True)
full=deepcopy(manifest['schemas']['strict']);step=deepcopy(manifest['schemas']['stepwise'])
step['properties']['actions']['maxItems']=6
assert full==step==manifest['schemas']['bounded']
ledger=[json.loads(x) for x in (BASE/'request-ledger.jsonl').read_text().splitlines()]
requests=[read(BASE/f'request-{i:03}.json') for i in range(1,38)]
assert [r['reservation'] for r in requests]==ledger
schedule=manifest['preparation']['payload']['schedule']
data=dict(trials=[],repairs=[],requests=[],observation_pairs=[],historical={},
          evidence_files=len(completion['evidence_hashes']),source_files=len(source_checks),
          prompts=manifest['prompts'],schemas=manifest['schemas'],network_policy='denied')
for slot in schedule:
    name=slot['trial']; row=read(BASE/(name+'.json'));t=row['turn'];mode=t['control_mode']
    sim=replay(row['command_trace'])
    assert sim.trace()==row['command_trace'] and to_snapshot(sim.state)==row['final_state']
    record=dict(trial=name,source=(BASE/(name+'.json')).as_posix(),trial_binding=row['trial'],
        starting_state=row['command_trace']['initial_snapshot'],ap_available=t['ap_available'],
        ap_executed=t['ap_executed'],ap_remaining=t['ap_remaining'],stop_reason=t['stop_reason'],
        explicit_end_turn=t['explicit_end_turn'],provider_attempts=t['provider_requests'],
        execution_invalidities=t['execution_invalidities'],replay_exact=True,waves=[],
        normal_finalization=not t['explicit_end_turn'] and any(c['type']=='arena_end_turn' for c in t['commands_executed']),
        telemetry={k:t[k] for k in ['input_tokens','output_tokens','total_tokens','backend_thinking_seconds']})
    reservations=[r for r in requests if r['reservation']['trial']==name]; cursor=0
    for w in t['waves']:
        prefix=deepcopy(row['command_trace']);prefix['entries']=prefix['entries'][:w['command_start']]
        state=replay(prefix).state; obs=candidate_observation(state)
        assert obs.to_dict()==w['observation'] and obs.hash==w['observation_hash']
        wave=dict(index=w['wave_index'],ap_available=w['ap_available'],observation=w['observation'],
            attempts=[],accepted_plan=w['plan'],execution_invalidity=w['invalid_action'],
            actions_attempted=w['actions_attempted'])
        for ai,a in enumerate(w['inference']['attempts']):
            raw=json.loads(a['raw_content']);diag=None
            try:
                plan=parse_candidate(a['raw_content'],obs,step=mode=='stepwise')
                assert plan.to_dict()==w['plan']
            except ArenaProviderError as e:
                diag=e.diagnostic.to_dict()
            assert (diag['category'] if diag else None)==a.get('error_category')
            rr=reservations[cursor];cursor+=1
            assert rr['observation']==w['observation'] and rr['command_trace']==prefix
            messages=[dict(role='user',content='ArenaObservation:\n'+obs.canonical)]
            if ai:
                feedback=ModelArenaTurnProvider.repair_feedback(None,w['inference']['attempts'][0]['error_category'])
                messages.append(dict(role='user',content=feedback))
                assert rr['preceding_inference']['attempts'][0]['raw_content']==w['inference']['attempts'][0]['raw_content']
            mechanics=[]
            for action in raw['actions']:
                if action['type']=='end_turn': mechanics.append(None);continue
                try: validate_command(state,action_command(action_from_dict(action),state.active_player_id)); mechanics.append(None)
                except ValueError as e: mechanics.append(str(e))
            attempt=dict(attempt=ai,raw_content=a['raw_content'],parsed_json=raw,
                planned_ap=sum(ACTION_COSTS[x['type']] for x in raw['actions']),
                costs=[ACTION_COSTS[x['type']] for x in raw['actions']],valid=diag is None,
                reconstructed_diagnostic=diag,individual_action_errors_at_decision_state=mechanics,
                request=rr['reservation']['request'],metrics=a['metrics'],wall_seconds=a['wall_clock_seconds'])
            wave['attempts'].append(attempt)
            data['requests'].append(dict(request=attempt['request'],trial=name,wave=w['wave_index'],attempt=ai,
                instructions=manifest['prompts'][t['prompt_version']],input=messages,
                reconstruction='Frozen observation/raw traces plus hash-verified provider source; not a captured wire body.'))
        if len(wave['attempts'])==2:
            data['repairs'].append(dict(id='R'+str(len(data['repairs'])+1),trial=name,wave=w['wave_index'],
                ap_available=w['ap_available'],feedback=feedback,original=wave['attempts'][0],repaired=wave['attempts'][1],
                legal_actions=w['observation']['legal_actions']))
        record['waves'].append(wave)
    assert cursor==len(reservations)==t['provider_requests']
    record['end_turn_provenance']='none'
    if t['explicit_end_turn']:
        stop_wave=next(w for w in record['waves'] if any(a['action']['type']=='end_turn' and a['executed'] for a in w['actions_attempted']))
        record['end_turn_provenance']='repair' if len(stop_wave['attempts'])==2 else 'initial output'
        prefix=deepcopy(row['command_trace']);prefix['entries'].pop()
        record['observation_before_end_turn']=candidate_observation(replay(prefix).state).to_dict()
    elif record['normal_finalization']:record['end_turn_provenance']='controller finalization (not explicit)'
    data['trials'].append(record)
for probe in manifest['preparation']['payload']['probes']:
    rows=[r for r in data['trials'] if r['trial_binding']['probe']==probe['id']]
    assert len(rows)==3
    assert rows[0]['starting_state']==rows[1]['starting_state']==rows[2]['starting_state']
    assert rows[0]['waves'][0]['observation']==rows[1]['waves'][0]['observation']==rows[2]['waves'][0]['observation']
    data['observation_pairs'].append(dict(probe=probe['id'],equal=True,hash=rows[0]['trial_binding']['observation_hash']))
for version,dirname in [('V1','arena-luna-tactical-literacy-01'),('V4','arena-luna-tactical-literacy-prompt-v4-01'),('V5','arena-luna-tactical-literacy-prompt-v5-01')]:
    hist=[]
    for p in (Path('.local')/dirname).glob('*/telemetry.json'):
        d=read(p)
        attempts=d.get('attempts',[])
        if len(attempts)>1:hist.append(dict(path=p.as_posix(),attempts=attempts,resulting_plan=d.get('resulting_plan'),error=d.get('error_category')))
    data['historical'][version]=dict(repairs=len(hist),successes=sum(x['resulting_plan'] is not None for x in hist),episodes=hist)
data['counts']=dict(trials=len(data['trials']),waves=sum(len(r['waves']) for r in data['trials']),requests=len(data['requests']),
    repairs=len(data['repairs']),successful_repairs=sum(r['repaired']['valid'] for r in data['repairs']),
    stops=dict(Counter(r['stop_reason'] for r in data['trials'])))
(HERE/'forensics.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data['counts'],indent=2))
print('historical', {k:(v['repairs'],v['successes']) for k,v in data['historical'].items()})
print('sources',len(source_checks),'evidence',data['evidence_files'])
