"""Offline descriptive audit of saved structured decisions and frozen diagnostics."""
import json
from collections import Counter
from pathlib import Path
from aig.arena.case_study_contract import read,sha

root=Path(__file__).parent
arms=('strict','bounded','stepwise')
stats={str(b):{a:Counter() for a in arms} for b in (1,2,3,4)}
cases=[]

def attempt_evidence(a,w):
    e=a.get('rejected_decision') or {};d=e.get('diagnostics',[]);v=e.get('validation',{})
    plan=e.get('rejected_plan');actions=(plan or {}).get('actions',[])
    categories=[]
    if e.get('over_budget_by',0)>0 or a.get('error_category')=='ap_budget':categories.append('AP_VIOLATION')
    for item in d:
        msg=item.get('message','').lower();code=item.get('code','');field=item.get('field','')
        if code=='ap_budget':tag='AP_VIOLATION'
        elif 'occupied, blocked, unchanged, or beyond move range' in msg:tag='OTHER_CURRENT_ACTION_VALIDATION'
        elif code in ('range','los') or 'range' in msg or 'line of sight' in msg:tag='STATIC_RANGE_OR_LOS'
        elif code=='actor_reference_or_status' or field=='unit_id' or 'unit is not owned' in msg:tag='INVALID_ACTOR_REFERENCE_OR_STATUS'
        elif code=='target_status' or field=='target_id' or 'target ownership' in msg:tag='INVALID_TARGET_REFERENCE_OR_STATUS'
        elif code=='invalid_ability':tag='ILLEGAL_ACTION_REFERENCE'
        elif code=='current_action_invalid':tag='OTHER_CURRENT_ACTION_VALIDATION'
        else:tag='OTHER_VALIDATION_FAILURE'
        if tag not in categories:categories.append(tag)
    if not categories:
        field=v.get('field_path') or ''
        if 'unit_id' in field:categories=['INVALID_ACTOR_REFERENCE_OR_STATUS']
        elif 'target_id' in field:categories=['INVALID_TARGET_REFERENCE_OR_STATUS']
        elif a.get('error_category')=='invalid_ability':categories=['ILLEGAL_ACTION_REFERENCE']
        elif a.get('error_category') in ('schema_validation','malformed_json'):categories=['SCHEMA_OR_TYPE_VIOLATION']
        else:categories=['OTHER_VALIDATION_FAILURE']
    ix=v.get('action_index')
    if ix is None and d:ix=d[0].get('action_index')
    action=actions[ix] if isinstance(ix,int) and 0<=ix<len(actions) else None
    if action is None and d:action=d[0].get('action')
    receipt_path=root/'requests'/f"{a['ledger_id']:06d}"/'receipt.json'
    receipt=read(receipt_path)
    own={x['id']:x for x in w['observation']['own_team']['units']}
    all_units={x['id']:x for side in ('own_team','enemy_team') for x in w['observation'][side]['units']}
    actor=(action or {}).get('unit_id');target=(action or {}).get('target_id')
    return dict(ledger_id=a['ledger_id'],error_category=a.get('error_category'),classifications=categories,
        classification_basis='Saved validator/repair diagnostics; descriptive mapping, never a change to frozen categories.',
        validation=v,diagnostics=d,available_ap=e.get('available_ap',w['ap_available']),planned_ap=e.get('planned_ap'),over_budget_by=e.get('over_budget_by'),
        action_index=ix,identified_action=action,actor_reference=actor,target_reference=target,
        target_position=(action or {}).get('target_position'),destination=(action or {}).get('destination'),
        actor_owned=actor in own if actor is not None else None,actor_status=own.get(actor,{}).get('status'),target_status=all_units.get(target,{}).get('status'),
        structured_plan=plan,request_payload_present=(receipt_path.parent/'payload.json').exists(),response_receipt_present=True,
        receipt_status=receipt['status'],response_id=a.get('response_id'),provider_request_id=a.get('request_id'),response_sha256=receipt.get('response_sha256'),
        transport_completed=receipt['status']=='returned',receipt_file_sha256=sha(receipt_path),
        reference_redaction_note='Unknown reference strings remain redacted as recorded; absent structured fields are not reconstructed.')

for result_file in sorted(root.glob('matches/*/result.json')):
    if not (result_file.parent/'seal.json').exists():continue
    r=read(result_file);s=stats[str(r['batch'])][r['arm']];s['matches']+=1
    for f in sorted((result_file.parent/'turns').glob('*.json')):
        bundle=read(f);t=bundle['turn']
        if t['player_id']!=r['luna_side']:continue
        for w in t['waves']:
            attempts=w['inference'].get('attempts',[])
            if attempts:
                s['first_responses']+=1;s['first_response_invalid_decisions']+=bool(attempts[0].get('error_category'))
            if len(attempts)>1:
                s['repairs_attempted']+=len(attempts)-1
                s['repairs_succeeded']+=sum(not a.get('error_category') for a in attempts[1:])
                s['repairs_failed']+=sum(bool(a.get('error_category')) for a in attempts[1:])
            if w['error_category']!='repair_failed':continue
            s['repairs_exhausted']+=1
            forfeit=r['terminal_cause']=='PROVIDER_FORFEIT'
            s['repair_exhaustion_forfeits']+=forfeit
            assert len(attempts)==2
            cases.append(dict(batch=r['batch'],match_id=r['match_id'],control=r['arm'],luna_side=r['luna_side'],
                player_turn_ordinal=bundle['ordinal'],engine_round_index=t['turn'],round_number=t['turn']+1,
                wave_index=w['wave_index'],replacement=r['arm']=='bounded' and w['wave_index']==1,
                ap_at_wave=w['ap_available'],ap_remaining=t['ap_remaining'],
                initial=attempt_evidence(attempts[0],w),repair=attempt_evidence(attempts[1],w),
                forfeit=forfeit,terminal_cause=r['terminal_cause'],engine_winner=r['engine_winner'],
                turn_bundle=str(f.relative_to(root)),turn_bundle_sha256=sha(f)))
stats['cumulative']={a:sum((stats[str(b)][a] for b in (1,2,3,4)),Counter()) for a in arms}
for group in stats.values():
    for row in group.values():
        for key in ('matches','first_responses','first_response_invalid_decisions','repairs_attempted','repairs_succeeded','repairs_failed','repairs_exhausted','repair_exhaustion_forfeits'):row.setdefault(key,0)
        row['repair_success_rate']=row['repairs_succeeded']/row['repairs_attempted'] if row['repairs_attempted'] else None
        row['forfeit_rate_per_match']=row['repair_exhaustion_forfeits']/row['matches'] if row['matches'] else None
patterns={}
for b in ('1','2','3','4','cumulative'):
    selected=[c for c in cases if b=='cumulative' or str(c['batch'])==b]
    patterns[b]=dict(initial_categories=dict(Counter(c['initial']['error_category'] for c in selected)),
        repair_categories=dict(Counter(c['repair']['error_category'] for c in selected)),
        repair_classifications=dict(Counter(tag for c in selected for tag in c['repair']['classifications'])),
        repair_identified_action_types=dict(Counter((c['repair']['identified_action'] or {}).get('type','unavailable') for c in selected)),
        initial_to_repair_categories=dict(Counter(str(c['initial']['error_category'])+' -> '+str(c['repair']['error_category']) for c in selected)))
out=dict(reliability=stats,exhaustions=cases,patterns=patterns,
    caveat='invalid_reference is broad: first-action catalog failures can be range/LOS or status errors with valid IDs. Classification tags may overlap. Schema-invalid outputs may lack retained actions; no raw prose or hidden reasoning is used.')
(root/'repair-forensics.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
lines=['# Repair-exhaustion forensics — interim Batches 1–3','',out['caveat'],'',
       'This is a descriptive audit of saved structured outputs and repository-owned diagnostics. It does not modify validation, replay, telemetry or the benchmark contract. No chain-of-thought or raw prose is included.','',
       '| Batch | Control | Matches | First invalid/decisions | Repairs attempted | Succeeded | Exhausted | Success rate | Forfeits |',
       '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for b in ('1','2','3','4','cumulative'):
    for a in arms:
        s=stats[b][a];rate=f"{s['repair_success_rate']:.3%}" if s['repair_success_rate'] is not None else 'N/A'
        lines.append(f"| {b} | {a} | {s['matches']} | {s['first_response_invalid_decisions']}/{s['first_responses']} | {s['repairs_attempted']} | {s['repairs_succeeded']} | {s['repairs_exhausted']} | {rate} | {s['repair_exhaustion_forfeits']} |")
lines += ['', '## Category and action patterns','']
for b,p in patterns.items():lines += [f'Batch/cohort {b}: `{json.dumps(p)}`','']
lines += ['## Every Batch 4 exhausted repair','']
for c in cases:
    if c['batch']!=4:continue
    lines += [f"### {c['match_id']} — {c['luna_side']}",'',
        f"Player-turn ordinal {c['player_turn_ordinal']}; engine round index {c['engine_round_index']} (round number {c['round_number']}); wave {c['wave_index']}; replacement={c['replacement']}; AP at wave {c['ap_at_wave']}, AP left {c['ap_remaining']}. Result: {c['terminal_cause']}, forfeit={c['forfeit']}. Engine winner remains {c['engine_winner']}.",'',
        f"Evidence: [{c['turn_bundle']}]({c['turn_bundle']}); SHA-256 `{c['turn_bundle_sha256']}`.",'']
    for name in ('initial','repair'):
        a=c[name];lines += [f"**{name.title()} response** — request {a['ledger_id']}; category `{a['error_category']}`; descriptive tags `{a['classifications']}`.",'',
            f"Action index {a['action_index']}; action `{json.dumps(a['identified_action'])}`. Actor `{a['actor_reference']}` (owned={a['actor_owned']}, status={a['actor_status']}); target `{a['target_reference']}` (status={a['target_status']}). Available AP {a['available_ap']}; planned AP {a['planned_ap']}; over budget {a['over_budget_by']}.",'',
            f"Validator: `{json.dumps(a['validation'])}`. Diagnostics: `{json.dumps(a['diagnostics'])}`.",'',
            f"Retained structured plan: `{json.dumps(a['structured_plan'])}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.",'',
            f"Payload present={a['request_payload_present']}; receipt present={a['response_receipt_present']}; receipt status={a['receipt_status']}; transport completed={a['transport_completed']}; response ID `{a['response_id']}`; provider request ID `{a['provider_request_id']}`. Structured response SHA-256 `{a['response_sha256']}`.",'']
lines += ['Full initial and repair structured plans, detailed diagnostics, and earlier-batch cases are in [repair-forensics.json](repair-forensics.json). A field absent from sanitized evidence is unavailable, not evidence that the model omitted it.','']
(root/'repair-forensics.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(dict(exhausted_repairs=len(cases),batch_4=sum(c['batch']==4 for c in cases),success=True)))
