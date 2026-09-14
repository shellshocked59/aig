"""Offline supplementary mechanical review of the completed focused validation."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import statistics

from aig.arena.ai.benchmark_candidate import candidate_observation, candidate_schema, parse_candidate, CandidateObservation
from aig.arena.commands import ACTION_COSTS
from aig.arena.replay import replay
from aig.arena.snapshots import canonical_json, digest, to_snapshot
from aig.arena.candidate_validation import verify_preparation
from aig.arena.ai.validation import ArenaProviderError


def main(output):
    a = json.loads((output/'analysis.json').read_text())
    prepared = verify_preparation()
    completion = json.loads((output/'completion.json').read_text())
    for name, expected in completion['evidence_hashes'].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest() == expected
    rows = a['per_trial']
    data = dict(controls={}, first_decisions={}, stops=[], bounded=[], stepwise=[],
                refresh_observations_verified=0, accepted_plans_reparsed=0,
                schema_only_cardinality_differs=False, preservation={})
    full = candidate_schema(openai=True)
    step = candidate_schema(step=True, openai=True)
    step['properties']['actions']['maxItems'] = full['properties']['actions']['maxItems']
    assert full == step
    data['schema_only_cardinality_differs'] = True
    for mode in ('strict','bounded','stepwise'):
        chosen = [r for r in rows if r['trial']['control_mode'] == mode]
        waves = [w for r in chosen for w in r['turn']['waves']]
        raw_costs, invalid, first_invalid, repair_groups = [], [], [], Counter()
        first_valid_by_ap = {}
        for r in chosen:
            t = r['turn']
            for wi,w in enumerate(t['waves']):
                before = deepcopy(r['command_trace'])
                before['entries'] = before['entries'][:w['command_start']]
                state = replay(before).state
                actual_observation = candidate_observation(state)
                assert actual_observation.to_dict() == w['observation']
                assert actual_observation.hash == w['observation_hash']
                data['refresh_observations_verified'] += 1
                if w['plan']:
                    parsed = parse_candidate(canonical_json(w['plan']), actual_observation, step=mode=='stepwise')
                    assert parsed.to_dict() == w['plan']
                    data['accepted_plans_reparsed'] += 1
                if w['provider_requests'] == 2:
                    group = 'bounded_replacement' if mode=='bounded' and wi else 'stepwise' if mode=='stepwise' else 'initial'
                    repair_groups[group] += 1
                for ai,attempt in enumerate(w['inference']['attempts']):
                    raw = json.loads(attempt['raw_content']) if attempt['raw_content'] else None
                    cost = sum(ACTION_COSTS[x['type']] for x in raw['actions']) if raw else None
                    overbudget = cost is not None and cost > w['ap_available']
                    record = dict(trial=r['trial']['trial'], wave=wi, attempt=ai, ap_available=w['ap_available'],
                        planned_ap=cost, overbudget=overbudget, category=attempt.get('error_category'), raw=raw)
                    raw_costs.append(record)
                    if attempt.get('error_category'):
                        invalid.append(record)
                        if ai == 0:
                            first_invalid.append(record)
                    if ai == 0:
                        bucket = first_valid_by_ap.setdefault(w['ap_available'], dict(decisions=0, valid=0, ap_overbudget=0))
                        bucket['decisions'] += 1
                        bucket['valid'] += not bool(attempt.get('error_category'))
                        bucket['ap_overbudget'] += overbudget
            if t['explicit_end_turn']:
                pre_stop = deepcopy(r['command_trace'])
                assert pre_stop['entries'][-1]['command']['type'] == 'arena_end_turn'
                pre_stop['entries'].pop()
                state = replay(pre_stop).state
                legal = candidate_observation(state).to_dict()['legal_actions']
                data['stops'].append(dict(trial=r['trial']['trial'], control=mode, ap_available=t['ap_available'],
                    ap_executed=t['ap_executed'], ap_remaining=t['ap_remaining'], actions_before=t['actions_before_intentional_stop'],
                    requests=t['provider_requests'], first_response_repaired=t['waves'][0]['provider_requests']==2,
                    legal_nonstop_counts=dict(Counter(x['type'] for x in legal if x['type']!='end_turn')),
                    legal_nonmove_actions=[x for x in legal if x['type'] not in ('end_turn','move')],
                    state_before_stop=to_snapshot(state)))
            if mode=='bounded':
                first=t['waves'][0]
                replacement=t['waves'][1] if len(t['waves'])>1 else None
                data['bounded'].append(dict(trial=r['trial']['trial'], initial_plan=first['plan'],
                    initial_planned_end=first['planned_end_turn'], initial_reached_end=first['explicit_end_turn'],
                    invalidity=first['invalid_action'], stale_suffix=first['stale_suffix_count'],
                    ap_at_replan=t['ap_at_replan'], replan=t['replan_used'], replacement_plan=replacement['plan'] if replacement else None,
                    replacement_attempts=replacement['inference']['attempts'] if replacement else [],
                    replacement_end=t['replacement_explicit_end_turn'], second_invalidity=t['second_invalidity'],
                    recovered_ap=t['ap_recovered'], stop=t['stop_reason'], requests=t['provider_requests']))
            if mode=='stepwise':
                data['stepwise'].append(dict(trial=r['trial']['trial'], accepted_actions=[x['action'] for w in t['waves'] for x in w['actions_attempted']],
                    requests=t['provider_requests'], explicit=t['explicit_end_turn'], remaining=t['ap_remaining'],
                    executed_actions_legal=all(x['executed'] for w in t['waves'] for x in w['actions_attempted']),
                    rejected_outputs=[at['raw_content'] for w in t['waves'] for at in w['inference']['attempts'] if at.get('error_category')],
                    stop=t['stop_reason']))
        accepted_initial=[r['turn']['waves'][0] for r in chosen if r['turn']['waves'][0]['plan']]
        counts=[sum(x['type']!='end_turn' for x in w['plan']['actions']) for w in accepted_initial]
        data['controls'][mode]=dict(first_valid_by_ap=first_valid_by_ap, raw_attempts=raw_costs, static_invalid=invalid,
            first_static_invalid=first_invalid, repair_groups=dict(repair_groups),
            first_ap_overbudget=sum(x['overbudget'] and x['attempt']==0 for x in raw_costs),
            all_ap_overbudget=sum(x['overbudget'] for x in raw_costs),
            accepted_initial_plans=len(counts), initial_gameplay_counts=counts,
            one_action_plans=sum(n==1 for n in counts), multi_action_plans=sum(n>=2 for n in counts),
            mean_initial_actions=statistics.mean(counts), initial_planned_ap=[w['planned_ap'] for w in accepted_initial],
            mean_initial_planned_ap=statistics.mean(w['planned_ap'] for w in accepted_initial),
            short_initial_plans=sum(w['planned_ap']<w['ap_available'] for w in accepted_initial),
            full_budget_initial_plans=sum(w['planned_ap']==w['ap_available'] for w in accepted_initial),
            initial_end_placements=[dict(trial=r['trial']['trial'], index=i, reached=r['turn']['waves'][0]['explicit_end_turn'])
                for r in chosen if r['turn']['waves'][0]['plan'] for i,x in enumerate(r['turn']['waves'][0]['plan']['actions']) if x['type']=='end_turn'])
    for probe in prepared['probes']:
        matched = [r for r in rows if r['trial']['probe']==probe['id']]
        decisions={}
        for r in matched:
            wave=r['turn']['waves'][0]
            raw=json.loads(wave['inference']['attempts'][0]['raw_content'])
            action=raw['actions'][0] if raw['actions'] else None
            accepted=wave['plan']['actions'][0] if wave['plan'] and wave['plan']['actions'] else None
            kind=action['type'] if action else None
            objective=('core_damage' if action and action.get('target_id')=='red-core' else
                       'unit_damage_and_push' if kind=='shield_bash' else 'unit_damage' if kind in ('attack','snipe','fireball') else
                       'positioning' if kind=='move' else 'intentional_stop' if kind=='end_turn' else kind)
            decisions[r['trial']['control_mode']]=dict(first_raw_action=action, first_accepted_action=accepted,
                first_response_valid=not bool(wave['inference']['attempts'][0].get('error_category')),
                objective_class=objective, ap_cost=ACTION_COSTS[kind] if kind else None)
        data['first_decisions'][probe['id']]=decisions
    baseline=json.loads((output.parent/'preservation-before-20260914.json').read_text())
    changed=[name for name,value in baseline.items() if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest()!=value]
    assert not changed
    data['preservation']=dict(files_checked=len(baseline), changed_or_missing=changed,
        frozen_preparation_verified=True, evidence_files_verified=len(completion['evidence_hashes']))
    with (output/'review-data.json').open('x',encoding='utf-8') as f:
        json.dump(data,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in data.items() if k not in ('controls','bounded','stepwise','stops')},indent=2))
    for mode,s in data['controls'].items():
        print(mode,json.dumps({k:v for k,v in s.items() if k not in ('raw_attempts','static_invalid','first_static_invalid')}))
    for s in data['stops']:
        print('STOP',json.dumps({k:v for k,v in s.items() if k!='state_before_stop'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
