"""Versioned independent-trial Fireball audit. No live requests at preparation."""
import argparse
import hashlib
import json
from pathlib import Path

from aig.arena.friendly_fire_experiment import (ROOT, sources, write, OLD_PROMPT, PROMPT_VERSION,
    LunaBehaviorProvider, Settings, inference_configuration, resolve_model_profile,
    build_observation, openai_turn_plan_schema, PLAN_SCHEMA_VERSION, OBSERVATION_VERSION,
    BEHAVIOR_PROMPTS, CASES, FIXTURE_VERSION, ArenaSimulation, from_snapshot, to_snapshot,
    digest, checked_plan, execute_arena_turn, analyze_fireball, ArenaFireball, ArenaProviderError)
from aig.arena.commands import ACTION_COSTS
from aig.arena.replay import replay
from aig.arena.benchmark_metrics import inference_metrics

VERSION = 'arena-fireball-methodology-v2'
ARMS = (OLD_PROMPT, PROMPT_VERSION)
STATIC_ERRORS = {'malformed_json', 'schema_validation', 'ap_budget', 'invalid_reference', 'invalid_ability'}
RUNNER = 'backend/aig/arena/friendly_fire_experiment.py'
MODULE = 'backend/aig/arena/friendly_fire_methodology.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare_methodology(plan_path, output):
    saved = json.loads(Path(plan_path).read_text())
    current = sources()
    changed = {p for p in set(current) | set(saved['source_files'])
               if current.get(p) != saved['source_files'].get(p)}
    if not changed <= {RUNNER, MODULE}:
        raise ValueError('unexpected protected source change')
    data = dict(version=VERSION, plan_sha256=sha(plan_path), source_files=current,
                changed_sources=sorted(changed), decisions_per_arm=24,
                request_ceiling_per_arm=48, combined_request_ceiling=96,
                excluded_evidence='ABORTED-METHODOLOGY PILOT EVIDENCE',
                policy='independent trials; execution truncation and failed static repair continue')
    output = Path(output)
    if output.exists():
        raise ValueError('methodology artifact exists')
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, data)
    return data


def validate(plan_path, methodology_path):
    m = json.loads(Path(methodology_path).read_text())
    s = json.loads(Path(plan_path).read_text())
    if (m['version'] != VERSION or m['plan_sha256'] != sha(plan_path)
            or m['source_files'] != sources()
            or (m['decisions_per_arm'], m['request_ceiling_per_arm'], m['combined_request_ceiling']) != (24,48,96)):
        raise ValueError('methodology/source/artifact mismatch')
    if (s['version'] != 'arena-luna-fireball-experiment-v1'
            or s['fixture_hash'] != digest(s['fixtures']) or s['fixture_version'] != FIXTURE_VERSION
            or s['observation_version'] != OBSERVATION_VERSION or s['schema_version'] != PLAN_SCHEMA_VERSION
            or s['schema_hash'] != digest(openai_turn_plan_schema())
            or s['control_version'] != 'arena-control-full-turn-v1'
            or s['model_profile'] != resolve_model_profile('openai')[0]
            or s['model_configuration'] != resolve_model_profile('openai')[1]
            or s['repair'] is not True or s['trials_per_fixture'] != 4
            or s['decisions_per_arm'] != 24 or s['request_ceiling_per_arm'] != 48
            or [r['name'] for r in s['fixtures']] != list(CASES)
            or any(s['prompt_hashes'][v] != hashlib.sha256(BEHAVIOR_PROMPTS[v].encode()).hexdigest() for v in ARMS)):
        raise ValueError('frozen contract mismatch')
    return s, m


def classify(effect):
    enemies, friends = bool(effect['enemy_ids']), bool(effect['friendly_ids'])
    return 'MIXED' if enemies and friends else 'ENEMY_ONLY' if enemies else 'FRIENDLY_ONLY' if friends else 'EMPTY'


def evaluate(state, plan):
    sim = ArenaSimulation(state)
    row = dict(planned_fireballs=[], executed_fireballs=[], planned_but_unreached=[],
               unexecuted_fireballs=[], execution=None, execution_truncated=False,
               invalid_action_index=None, invalid_action_type=None, invalid_reason=None,
               planned_ap=None, executed_ap=0, ap_before_truncation=None,
               fireballs_before_truncation=0)
    if plan is not None:
        row['planned_ap'] = sum(ACTION_COSTS[a.type] for a in plan.actions)
        row['planned_fireballs'] = [dict(action_index=i, action=a.to_dict(), impact=a.to_dict()['target_position'])
                                    for i,a in enumerate(plan.actions) if a.type == 'fireball']
        def execute(command):
            index = len(sim.trace()['entries'])
            effect = analyze_fireball(sim.state, command) if type(command) is ArenaFireball else None
            sim.execute(command)
            if effect is not None:
                row['executed_fireballs'].append(dict(effect, action_index=index,
                    category=classify(effect), zero_enemy=not bool(effect['enemy_ids'])))
        result = execute_arena_turn(sim.state, plan, execute_command=execute).to_dict()
        row['execution'] = result
        row['executed_ap'] = result['ap_spent']
        invalid = result['invalid_action']
        if invalid:
            row.update(execution_truncated=True, invalid_action_index=invalid['index'],
                       invalid_action_type=invalid['action']['type'], invalid_reason=invalid['reason'],
                       ap_before_truncation=result['ap_spent'],
                       fireballs_before_truncation=len(row['executed_fireballs']))
        reached = {b['action_index'] for b in row['executed_fireballs']}
        for b in row['planned_fireballs']:
            if b['action_index'] not in reached:
                reason = ('planned_but_unreached' if invalid and b['action_index'] > invalid['index']
                          else 'rejected_at_execution' if invalid and b['action_index'] == invalid['index']
                          else 'unreached_after_terminal')
                item = dict(b, status=reason)
                row['unexecuted_fireballs'].append(item)
                if reason == 'planned_but_unreached':
                    row['planned_but_unreached'].append(item)
    sim.state.validate()
    row.update(command_trace=sim.trace(), final_snapshot=to_snapshot(sim.state),
               terminal_result=sim.state.winner_player_id)
    try:
        row['replay_matches'] = to_snapshot(replay(row['command_trace']).state) == row['final_snapshot']
    except Exception as error:
        row['replay_matches'] = False
        row['replay_error_type'] = type(error).__name__
    return row


def aggregate(rows):
    balls = [b for r in rows for b in r.get('executed_fireballs', [])]
    return dict(plans_containing_fireball=sum(bool(r.get('planned_fireballs')) for r in rows),
        planned_fireballs=sum(len(r.get('planned_fireballs', [])) for r in rows),
        planned_action_indices=[dict(fixture=r['fixture'],trial=r['trial'],indices=[b['action_index'] for b in r.get('planned_fireballs',[])]) for r in rows],
        executed_fireballs=len(balls),
        planned_but_unreached=sum(len(r.get('planned_but_unreached',[])) for r in rows),
        execution_truncations=sum(r.get('execution_truncated',False) for r in rows),
        failed_provider_trials=sum(r.get('trial_status')=='provider_failed' for r in rows),
        first_response_valid=sum(r.get('first_response_valid',False) for r in rows),
        intended_trials_started=len(rows),
        categories={c:sum(b['category']==c for b in balls) for c in ('EMPTY','FRIENDLY_ONLY','ENEMY_ONLY','MIXED')},
        zero_enemy=sum(b['zero_enemy'] for b in balls),
        enemy_damage=sum(b['enemy_damage'] for b in balls), friendly_damage=sum(b['friendly_damage'] for b in balls),
        enemy_downs=sum(len(b['enemy_downs']) for b in balls), friendly_downs=sum(len(b['friendly_downs']) for b in balls),
        immediate_win_fireballs=sum(b['immediate_win'] for b in balls))


def run_corrected(plan_path, methodology_path, prompt, output, *, settings=None, provider_factory=LunaBehaviorProvider):
    saved, method = validate(plan_path, methodology_path)
    if prompt not in ARMS:
        raise ValueError('unknown arm')
    settings = settings or Settings()
    if inference_configuration('openai',settings) != saved['model_configuration']:
        raise ValueError('profile mismatch')
    root = Path(output)
    root.mkdir(parents=True,exist_ok=True)
    # Exclusive lock spans an entire arm; never run concurrent arms against the ledger.
    lock = root/'batch.lock'
    with lock.open('x'):
        pass
    try:
        return _run_locked(saved,method,plan_path,methodology_path,prompt,root,settings,provider_factory)
    finally:
        lock.unlink()


def _run_locked(saved,method,plan_path,methodology_path,prompt,root,settings,provider_factory):
    if (root/'halted.json').exists():
        raise ValueError('batch previously hard-stopped; review required')
    identity = dict(methodology_sha256=sha(methodology_path), plan_sha256=sha(plan_path))
    ledger_path = root/'request-ledger.json'
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
        if (ledger.get('identity') != identity or set(ledger.get('arms',{})) != set(ARMS)
                or any(type(n) is not int or not 0 <= n <= 48 for n in ledger['arms'].values())
                or ledger.get('total') != sum(ledger['arms'].values()) or ledger['total'] > 96
                or ledger.get('checksum') != digest({k:v for k,v in ledger.items() if k!='checksum'})):
            raise ValueError('request-accounting corruption')
    else:
        if any(root.iterdir()) and set(p.name for p in root.iterdir()) != {'batch.lock'}:
            raise ValueError('missing request ledger in nonempty batch')
        ledger = dict(identity=identity,arms={v:0 for v in ARMS},total=0)
    def save_ledger():
        ledger['checksum'] = digest({k:v for k,v in ledger.items() if k!='checksum'})
        write(ledger_path,ledger)
    save_ledger()
    directory = root/prompt
    directory.mkdir(exist_ok=False)
    write(directory/'manifest.json',dict(methodology=method,plan=saved,selected_prompt=prompt))
    report = dict(version=VERSION,status='complete',prompt_version=prompt,runs=[],hard_stop=None)
    schedule = [dict(fixture=e['name'],trial=t) for t in range(1,5) for e in saved['fixtures']]
    entries = {e['name']:e for e in saved['fixtures']}
    def persist():
        report.update(aggregate=aggregate(report['runs']),requests=ledger['arms'][prompt],combined_requests=ledger['total'],
                      unstarted_trials=schedule[len(report['runs']):])
        calls=[r['inference'] for r in report['runs'] if 'inference' in r]
        report['inference_metrics']=inference_metrics(calls,None)
        write(directory/'summary.json',report)
    def stop(reason):
        report.update(status='integrity_stopped',hard_stop=reason)
        if report['runs'] and report['runs'][-1]['trial_status']=='started':
            report['runs'][-1]['trial_status']='integrity_failed'
        write(root/'halted.json',dict(reason=reason,arm=prompt))
        persist()
        return report
    provider = provider_factory(settings.openai,prompt_version=prompt,repair=True)
    def provider_ok():
        return (provider.name=='openai' and provider.prompt_version==prompt
            and provider.system_prompt==BEHAVIOR_PROMPTS[prompt] and provider.schema_version==PLAN_SCHEMA_VERSION
            and provider.output_schema()==openai_turn_plan_schema() and provider.repair is True
            and provider.configuration()==saved['model_configuration'])
    if not provider_ok():
        return stop('provider_contract_mismatch')
    boundary_error=None
    def boundary():
        nonlocal boundary_error
        reason=None
        if sources()!=method['source_files']:
            reason='source_drift'
        elif sha(plan_path)!=identity['plan_sha256'] or sha(methodology_path)!=identity['methodology_sha256']:
            reason='artifact_drift'
        elif json.loads(ledger_path.read_text())!=ledger:
            reason='request_accounting'
        elif not provider_ok():
            reason='provider_contract_mismatch'
        elif ledger['total']>=96 or ledger['arms'][prompt]>=48:
            reason='request_ceiling'
        if reason:
            boundary_error=reason
            raise ArenaProviderError(reason)
        ledger['total']+=1
        ledger['arms'][prompt]+=1
        save_ledger()  # Reserve before transport; crash never refunds a request.
    provider.before_request=boundary
    persist()
    for item in schedule:
        if ledger['total']>=96 or ledger['arms'][prompt]>=48:
            return stop('request_ceiling')
        row=dict(item,trial_status='started')
        report['runs'].append(row)
        before=ledger['total']
        try:
            state=from_snapshot(entries[item['fixture']]['snapshot'])
            obs=build_observation(state)
            if obs.hash!=entries[item['fixture']]['observation_hash']:
                return stop('observation_mismatch')
            plan,call=checked_plan(provider,'openai',obs)
            row.update(inference=call,first_response_valid=bool(call['attempts'] and not call['attempts'][0]['error_category']))
            # Do not let a static error mask provenance or transport corruption.
            raw=provider.last_trace or {}
            if boundary_error:
                return stop(boundary_error)
            if sources()!=method['source_files']:
                return stop('source_drift')
            if sha(plan_path)!=identity['plan_sha256'] or sha(methodology_path)!=identity['methodology_sha256']:
                return stop('artifact_drift')
            if (ledger['total']-before != len(call['attempts']) or call['provider_requests']!=len(call['attempts'])
                    or not 1 <= len(call['attempts']) <= 2 or json.loads(ledger_path.read_text())!=ledger):
                return stop('request_accounting')
            if (not provider_ok() or raw.get('requested_provider')!='openai' or raw.get('fallback_used')
                    or raw.get('actual_provider') not in (None,'openai') or (plan is not None and raw.get('actual_provider')!='openai')):
                return stop('provider_or_fallback')
            static_failed=(plan is None and call['error_category']=='repair_failed' and len(call['attempts'])==2
                           and all(a['error_category'] in STATIC_ERRORS for a in call['attempts']))
            row.update(evaluate(state,plan))
            if not row['replay_matches']:
                return stop('replay_mismatch')
            if plan is None and not static_failed:
                return stop(call['error_category'] or 'provider_failure')
            row['trial_status']='provider_failed' if plan is None else 'execution_truncated' if row['execution_truncated'] else 'completed'
            persist()
        except Exception as error:
            # Save available evidence, never serialize arbitrary secret-bearing exceptions.
            row['exception_type']=type(error).__name__
            return stop('authoritative_or_artifact_failure')
    persist()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Offline corrected methodology preparation only')
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--prepare',type=Path,required=True)
    args=parser.parse_args()
    prepare_methodology(args.plan,args.prepare)
