"""Frozen tactical-literacy audit: verify/dry-run offline; run requires --live."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.observation import build_observation, OBSERVATION_VERSION
from aig.arena.ai.prompts import PROMPT_VERSION
from aig.arena.snapshots import digest, from_snapshot
from aig.arena.mechanics_oracle import ORACLE_VERSION, evaluate, score

SUITE_VERSION='arena-tactical-literacy-v1'
ROOT=Path(__file__).resolve().parents[3]
SUITE=Path(__file__).parent/'benchmark_artifacts'/f'{SUITE_VERSION}.json'
REPETITIONS=3
CEILING=140


def hashes():
    paths=list((ROOT/'backend/aig/arena').rglob('*.py'))
    paths += [ROOT/p for p in ('backend/aig/state.py','backend/aig/movement.py','backend/aig/settings.py',
        'backend/aig/versions.py','backend/aig/ai/model_profiles.py','backend/aig/ai/openai.py','backend/aig/ai/plan_schema.py')]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def write(path, data):
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def freeze():
    from aig.arena.tactical_literacy_fixtures import build_probes
    from aig.ai.model_profiles import resolve_model_profile
    if SUITE.exists(): raise ValueError('frozen suite already exists; new version required')
    probes=build_probes()
    for probe in probes:
        probe['observation_hash']=build_observation(from_snapshot(probe['initial_state'])).hash
        probe['acceptable_reference_first_actions']=[seq[0] for seq in probe['acceptable_reference_sequences'] if seq]
    profile,configuration=resolve_model_profile('openai','luna-config-v1')
    payload=dict(version=SUITE_VERSION,oracle_version=ORACLE_VERSION,fixture_version='arena-literacy-fixtures-v1',
        prompt_version=PROMPT_VERSION,observation_version=OBSERVATION_VERSION,plan_schema=PLAN_SCHEMA_VERSION,
        rules_version=probes[0]['initial_state']['config']['rules_version'],
        scenario_version=probes[0]['initial_state']['config']['scenario_version'],
        model_profile=profile,configuration=configuration,source_hashes=hashes(),
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_worktree='dirty; source_hashes are authoritative',repetitions=REPETITIONS,request_ceiling=CEILING,
        schedule='repetition then frozen probe order; one full-turn decision each; no preflight',probes=probes)
    write(SUITE,dict(payload=payload,sha256=digest(payload)))


def verify(path=SUITE):
    wrapper=json.loads(Path(path).read_text(encoding='utf-8-sig')); suite=wrapper['payload']
    if digest(suite)!=wrapper['sha256']:raise ValueError('suite integrity mismatch')
    if suite['version']!=SUITE_VERSION or suite['source_hashes']!=hashes():raise ValueError('frozen source/version drift')
    for p in suite['probes']:
        if digest(p['initial_state'])!=p['initial_state_hash']:raise ValueError('fixture hash mismatch')
        if build_observation(from_snapshot(p['initial_state'])).hash!=p['observation_hash']:
            raise ValueError('observation drift')
        if evaluate(p['initial_state'],p['reference_sequence'])!=p['expected_mechanics']:
            raise ValueError('frozen mechanics drift: '+p['id'])
    return suite


def summarize(rows, scheduled, reservations):
    categories=defaultdict(Counter)
    objectives=defaultdict(Counter)
    for row in rows:
        categories[row['category']][row['classification']]+=1
        if row.get('scorable_opportunity'):
            objectives[row['category']]['denominator']+=1
            objectives[row['category']]['satisfied']+=int(row['objective_satisfied'] is True)
    return dict(scheduled=scheduled,completed=len(rows),unstarted=scheduled-len(rows),
        provider_requests=reservations,by_category={k:dict(v) for k,v in categories.items()},
        objective_rates={k:dict(v, rate=v['satisfied']/v['denominator']) for k,v in objectives.items()},
        no_composite_score=True)


def run(output, *, live=False, provider=None, repeats=None):
    suite=verify()
    repeats=suite['repetitions'] if repeats is None else repeats
    if live and repeats!=suite['repetitions']:raise ValueError('live schedule is frozen')
    if repeats<1:raise ValueError('repeats must be positive')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    write(output/'suite.json',json.loads(SUITE.read_text(encoding='utf-8')))
    write(output/'manifest.json',dict(suite_hash=digest(suite),mode='live' if live else 'offline-scripted',
        repetitions=repeats,request_ceiling=suite['request_ceiling'],configuration=suite['configuration']))
    rows=[];reservations=[]
    if live and provider is None:
        from aig.settings import load_settings
        from aig.ai.model_profiles import apply_model_profile
        from aig.arena.ai.openai import OpenAIArenaTurnProvider
        settings=apply_model_profile(load_settings(),'openai',suite['model_profile'])
        provider=OpenAIArenaTurnProvider(settings.openai,prompt_version=suite['prompt_version'])
    if provider is not None:
        if provider.name!='openai' or provider.configuration()!=suite['configuration'] or provider.prompt_version!=suite['prompt_version']:
            raise ValueError('provider contract mismatch')
        def reserve():
            verify_sources=suite['source_hashes']==hashes()
            if not verify_sources:raise RuntimeError('source drift before transport')
            if provider.configuration()!=suite['configuration'] or provider.prompt_version!=suite['prompt_version']:
                raise RuntimeError('provider contract drift before transport')
            if len(reservations)>=suite['request_ceiling']:
                raise RuntimeError('hard request ceiling reached')
            reservations.append(dict(number=len(reservations)+1,trial=current_trial))
            write(output/'request-ledger.json',reservations)
        provider.before_request=reserve
    try:
        for repetition in range(1,repeats+1):
            for p in suite['probes']:
                current_trial=f'{repetition:02}-{p["id"]}'
                directory=output/current_trial;directory.mkdir()
                observation=build_observation(from_snapshot(p['initial_state']))
                write(directory/'starting-state.json',p['initial_state'])
                write(directory/'observation.json',observation.to_dict())
                if provider is None:
                    actions=p['reference_sequence']; telemetry=dict(offline_scripted=True,provider_requests=0)
                    evaluation=score(p,actions)
                else:
                    from aig.arena.benchmark_provider import checked_plan
                    before=len(reservations)
                    plan,telemetry=checked_plan(provider,'openai',observation)
                    write(directory/'telemetry.json',telemetry)
                    # Retain only schema-shaped actions from each attempt, never arbitrary prose.
                    from aig.arena.ai.contracts import ArenaTurnPlan
                    outputs=[]
                    for attempt in (provider.last_trace or {}).get('attempts',[]):
                        try:
                            parsed=ArenaTurnPlan.from_dict(json.loads(attempt.get('raw_content') or 'null')).to_dict()
                        except (ValueError, TypeError, KeyError):
                            parsed=None
                        outputs.append(dict(parsed_output=parsed,error_category=attempt.get('error_category')))
                    write(directory/'attempt-outputs.json',outputs)
                    if telemetry['provider_requests']!=len(reservations)-before:
                        raise RuntimeError('request accounting mismatch')
                    actions=plan.to_dict()['actions'] if plan else None
                    if plan is None:
                        static={'malformed_json','schema_validation','ap_budget','invalid_reference','invalid_ability','repair_failed'}
                        evaluation=dict(classification='static invalidity' if telemetry['error_category'] in static else 'provider failure',
                            objective_satisfied=None,information_class=p['information_class'])
                    else:evaluation=score(p,actions)
                write(directory/'provider-output.json',dict(actions=actions,retention='parsed actions only; no prose or hidden reasoning'))
                write(directory/'parsed-plan.json',dict(schema_version=PLAN_SCHEMA_VERSION,actions=actions))
                write(directory/'telemetry.json',telemetry)
                write(directory/'evaluation.json',evaluation)
                if 'execution' in evaluation:
                    write(directory/'execution.json',evaluation['execution'])
                    write(directory/'replay-verification.json',dict(verified=evaluation['execution']['replay_verified']))
                rows.append(dict(probe=p['id'],category=p['category'],repetition=repetition,
                    classification=evaluation['classification'],objective_satisfied=evaluation['objective_satisfied'],
                    scorable_opportunity=bool(p['acceptable_reference_sequences'])))
                write(output/'results.json',rows)
                write(output/'summary.json',summarize(rows,len(suite['probes'])*repeats,len(reservations)))
                if provider is not None and telemetry['error_category'] in ('provider_mismatch','provider_exception','authentication_failure','configuration_failure'):
                    raise RuntimeError('integrity or unclassified provider failure; stop schedule')
        verify()
    except BaseException as error:
        write(output/'stopped.json',dict(error_type=type(error).__name__,completed=len(rows),requests=len(reservations)))
        raise
    finally:
        write(output/'summary.json',summarize(rows,len(suite['probes'])*repeats,len(reservations)))
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['freeze','verify','dry-run','run'])
    parser.add_argument('--suite',default=SUITE_VERSION,choices=[SUITE_VERSION])
    parser.add_argument('--provider',default='openai',choices=['openai'])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if args.command=='run' and not args.live:parser.error('run requires explicit --live authorization')
    if args.command!='run' and args.live:parser.error('--live only applies to run')
    if args.command=='freeze':freeze()
    elif args.command=='verify':print(json.dumps(dict(probes=len(verify()['probes']),verified=True)))
    else:
        if not args.output:parser.error('--output required')
        run(args.output,live=args.command=='run')

if __name__=='__main__':main()
