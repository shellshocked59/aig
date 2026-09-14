"""Supplemental descriptive tables over frozen analysis and audited command evidence."""
import json
from pathlib import Path
from collections import Counter
from statistics import median
from aig.arena.case_study_contract import read, sha, digest
from aig.arena.case_study_analysis import summarize, paired

root=Path(__file__).parent
audit=read(root/'supplemental-audit.json'); contract=read(root/'contract.json'); pre=read(root/'batch-3-preflight.json')
integrity=read(root/'integrity.json'); post=read(root/'postprocess-verification.json')
rows=[read(root/'matches'/r['match_id']/'result.json') for r in audit['matches']]
arms=('strict','bounded','stepwise')
timing=json.loads((root/'execution-timing.json').read_text(encoding='utf-8-sig'))
timings={b:json.loads((Path(f'artifacts/arena-case-study-live-v1-{b:02d}')/'execution-timing.json').read_text(encoding='utf-8-sig')) for b in (1,2,3)}
audit_by_id={r['match_id']:r for r in audit['matches']}
purposes={}; extra={}
for r in rows:
    c=Counter(); turnrows=[]
    for f in sorted((root/'matches'/r['match_id']/'turns').glob('*.json')):
        t=read(f)['turn']
        if t['player_id']!=r['luna_side']:continue
        turnrows.append(t)
        for i,w in enumerate(t['waves']):
            attempts=w['inference'].get('attempts',[])
            label='stepwise_decisions' if r['arm']=='stepwise' else 'bounded_replacement_planning' if i else 'initial_planning'
            repair='bounded_replacement_repair' if r['arm']=='bounded' and i else 'repair'
            c[label]+=bool(attempts);c[repair]+=max(0,len(attempts)-1)
    assert sum(c.values())==r['requests']
    purposes[r['match_id']]=dict(c)
    extra[r['match_id']]=dict(actions=sum(t['actions_executed'] for t in turnrows),
        replacement_explicit_end_turns=sum(t['replacement_explicit_end_turn'] for t in turnrows))

def cohort(selected,label):
    ids={r['match_id'] for r in selected}; out=dict(label=label,matches=len(selected),arms={})
    for arm in arms:
        rr=[r for r in selected if r['arm']==arm]; s=summarize(rr); mm=[r['metrics'][r['luna_side']] for r in rr]
        stops=[s for s in audit['end_turns'] if s['match_id'] in ids and s['arm']==arm]
        casts=[c for c in audit['fireballs'] if c['match_id'] in ids and c['arm']==arm and c['agent']=='luna']
        abilities={kind:[c for c in audit['ability_effects'] if c['match_id'] in ids and c['arm']==arm and c['agent']=='luna' and c['kind']==kind] for kind in ('arena_snipe','arena_shield_bash')}
        recovered=[v for m in mm for v in m['ap_recovered_distribution']]
        capped=[r for r in rr if r['terminal_cause']=='REQUEST_LIMIT']
        requests=s['totals'].get('provider_requests',0); turns=s['totals'].get('turns',0)
        s.update(heuristic=summarize(rr,True),sides={side:dict(luna=summarize([r for r in rr if r['luna_side']==side]),heuristic=summarize([r for r in rr if r['luna_side']==side],True)) for side in ('red','blue')},
            request_purposes=dict(sum((Counter(purposes[r['match_id']]) for r in rr),Counter())),
            recovery=dict(replans=len(recovered),positive=sum(v>0 for v in recovered),positive_fraction=sum(v>0 for v in recovered)/len(recovered) if recovered else None,
                ap_total=sum(recovered),mean_ap_per_replan=sum(recovered)/len(recovered) if recovered else None,
                ap_at_replan=[v for m in mm for v in m['ap_at_replan']],ap_recovered=recovered),
            caps=dict(count=len(capped),fraction=len(capped)/len(rr) if rr else None,requests=sum(r['requests'] for r in capped),
                request_share=sum(r['requests'] for r in capped)/requests if requests else None,match_ids=[r['match_id'] for r in capped]),
            end_turn=dict(count=len(stops),immediate=sum(s['actions_before']==0 for s in stops),ap_distribution=dict(Counter(s['ap_remaining'] for s in stops)),
                actions_before_distribution=dict(Counter(s['actions_before'] for s in stops)),damaging_opportunity_stops=sum(bool(s['legal_damaging_opportunities']) for s in stops),
                down_opportunity_stops=sum(any(o['enemy_downs'] for o in s['legal_damaging_opportunities']) for s in stops),requests_after_end_turn=0,
                replacement_stops=sum(extra[r['match_id']]['replacement_explicit_end_turns'] for r in rr)),
            fireball={k:sum(c[k] for c in casts) for k in ('enemy_units_hit','friendly_units_hit','enemy_damage','friendly_damage','enemy_downs','friendly_downs')},
            ability_effects={kind:{k:sum(c[k] for c in effects) for k in ('enemy_damage','friendly_damage','enemy_downs','friendly_downs','enemy_displacements')} for kind,effects in abilities.items()},
            invalidity_categories=dict(Counter(i['reason'] for m in mm for i in m['invalidities'])),
            player_turns=[r['player_turns'] for r in rr],rounds_completed=[r['rounds_completed'] for r in rr],
            actions_per_turn=sum(extra[r['match_id']]['actions'] for r in rr)/turns if turns else None,
            evidence_elapsed_seconds=sum(audit_by_id[r['match_id']]['evidence_elapsed_seconds'] for r in rr))
        out['arms'][arm]=s
    out['paired']=[paired(selected,a,b,inference=False) for a,b in [('bounded','strict'),('stepwise','bounded')]]
    indexed={(r['slot'],r['arm']):r for r in selected};triplets=[]
    for slot in sorted({r['slot'] for r in selected}):
        if not all((slot,a) in indexed for a in arms):continue
        tri=[indexed[slot,a] for a in arms]
        triplets.append(dict(slot=slot,luna_side=tri[0]['luna_side'],outcomes=[r['luna_outcome'] for r in tri],
            requests=[r['requests'] for r in tri],player_turns=[r['player_turns'] for r in tri],
            bounded_minus_strict_requests=tri[1]['requests']-tri[0]['requests'],stepwise_minus_bounded_requests=tri[2]['requests']-tri[1]['requests'],
            bounded_minus_strict_turns=tri[1]['player_turns']-tri[0]['player_turns'],stepwise_minus_bounded_turns=tri[2]['player_turns']-tri[1]['player_turns']))
    out['triplets']=triplets;out['triplet_patterns']=dict(Counter('/'.join(t['outcomes']) for t in triplets))
    out['all_three_same_outcome']=sum(len(set(t['outcomes']))==1 for t in triplets)
    return out

data={name:cohort([r for r in rows if r['batch'] in batches],name) for name,batches in [('batch_1',[1]),('batch_2',[2]),('batch_3',[3]),('cumulative',[1,2,3])]}
projection={}
for arm in arms:
    rr=[r for r in rows if r['arm']==arm];n=len(rr);remain=100-n;projection[arm]={}
    for key in ('provider_requests','total_tokens','provider_latency_seconds'):
        values=[r['metrics'][r['luna_side']][key] for r in rr]
        projection[arm][key]=None if not values or any(v is None for v in values) else dict(
            observed=sum(values),per_match=sum(values)/n,remaining_matches=remain,remaining_central=sum(values)/n*remain,total_100_central=sum(values)/n*100,
            observed_min_max=[min(values),max(values)],remaining_sensitivity=[min(values)*remain,max(values)*remain],
            total_100_sensitivity=[sum(values)+min(values)*remain,sum(values)+max(values)*remain])
data['projection']=projection;data['batch_3_manifest_sha256']=pre['batch_schedule_sha256']
(root/'interim-metrics.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def fmt(v):
    if v is None:return 'unknown / not applicable'
    if isinstance(v,float):return f'{v:,.4f}'
    if isinstance(v,(dict,list)):return json.dumps(v)
    return str(v)

forensics=read(root/'repair-forensics.json')
cap_details=[]
from aig.arena.snapshots import from_snapshot
for r in rows:
    if r['arm']!='stepwise' or r['terminal_cause']!='REQUEST_LIMIT':continue
    state=from_snapshot(read(root/'matches'/r['match_id']/'final-state.json'));m=r['metrics'][r['luna_side']]
    cap_details.append(dict(match_id=r['match_id'],batch=r['batch'],luna_side=r['luna_side'],player_turns=r['player_turns'],rounds_completed=r['rounds_completed'],
        luna_turns=m['turns'],ap_executed=m['ap_executed'],actions_executed=extra[r['match_id']]['actions'],requests=r['requests'],repairs=m['repairs'],explicit_end_turns=m['explicit_end_turn_decisions'],
        engine_winner=state.winner_player_id,core_hp={c.id:c.hp for c in state.cores.values()},units=[dict(id=u.id,owner=u.owner_id,hp=u.hp,status=u.status.value,x=u.position.x,y=u.position.y) for u in state.units.values()],
        final_state_path=f"matches/{r['match_id']}/final-state.json",final_state_hash=audit_by_id[r['match_id']]['final_state_hash']))
(root/'cap-details.json').write_text(json.dumps(cap_details,indent=2)+'\n',encoding='utf-8')

def render_report(cohort_name,filename,n):
    co=data[cohort_name];aa=co['arms'];selected=[r for r in rows if cohort_name=='cumulative' or r['batch']==3];lines=[]
    def p(v=''):lines.extend([v,''])
    def table(head,values):
        lines.append('| '+' | '.join(head)+' |');lines.append('| '+' | '.join(['---']*len(head))+' |')
        for row in values:lines.append('| '+' | '.join(fmt(v) for v in row)+' |')
        lines.append('')
    def metrics(fields):table(['Metric',*arms],[[k,*[aa[a]['totals'].get(k) for a in arms]] for k in fields])
    p('# '+('Batch 3 standalone' if cohort_name=='batch_3' else 'Cumulative Batches 1–3')+' — INTERIM')
    p(f'**n={n}/control, {len(selected)} sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).')
    p('## Execution and frozen integrity')
    p('Only Batch 3 was newly executed. Original Batch 1 and Batch 2 roots are preserved byte-for-byte. The verified 60-match prefix was copied to arena-case-study-live-v1-03 so cumulative aggregate updates do not overwrite old reports. Frozen resume continued at MATCH-021 Stepwise (Red), request 1031. No earlier match/request was rerun; no within-Batch-3 interruption recovery was needed. Scope ended at --through-batch 3. Batch 4 was not started.')
    p('```powershell\n.venv/Scripts/python.exe -B -m aig.arena.case_study verify\n.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-03 --through-batch 3 --authorize-live arena-case-study-benchmark-v1\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/postprocess.py\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/supplemental-audit.py\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/repair-forensics.py\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/interim-report.py\n```')
    p('postprocess.py calls the unchanged frozen source verifier, full-prefix integrity/replay verifier and analyzer for the cumulative prefix and batch==3 subset. Other scripts are separate offline derived audits, without provider calls or changes to frozen metrics/analysis.')
    table(['Binding','Value'],[['Benchmark',contract['payload']['id']],['Contract payload SHA-256',contract['sha256']],['Contract file SHA-256',sha(root/'contract.json')],['Batch 3 schedule SHA-256',pre['batch_schedule_sha256']],['Full schedule SHA-256',contract['payload']['schedule_hash']],['Source manifest SHA-256',pre['source_manifest_sha256']],['Source-bound files',len(contract['payload']['source_hashes'])]])
    p('Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.')
    p('Batch 3 is schedule entries 61–90, MATCH-021–030, five Red/five Blue matches per control. Budget: 1,700 new requests; per-control batch 300/500/900; per-match 50/80/140; global 15,000. One bounded replan maximum. Every request reserves ledger capacity before transport. Limits produce no winner; provider exhaustion is a forfeit with no fallback. Termination bounds remain 200 started player turns / 100 completed rounds.')
    p('Final frozen verifier: `'+json.dumps(integrity)+'`. Previous roots verified: `'+json.dumps(post['previous_roots_files_verified'])+'`; copied immutable prefix files verified: '+str(post['copied_immutable_prefix_files_verified'])+'. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.')
    table(['Control','Intended','Started/sealed','Side counts','Terminal causes'],[[a,n,aa[a]['matches'],dict(Counter(r['luna_side'] for r in selected if r['arm']==a)),aa[a]['terminal_causes']] for a in arms])
    p('## Outcomes and heuristic baseline')
    table(['Agent/matchup','Wins','Losses incl. forfeit','No-result','Win rate','Wilson 95%','Requests/turn'],[[a+' Luna' if who=='luna' else 'Heuristic vs '+a,s['wins'],s['losses'],s['limits'],s['win_rate'],s['wilson_95'],s['per_turn']['provider_requests']] for a in arms for who in ('luna','heuristic') for s in [aa[a] if who=='luna' else aa[a]['heuristic']]])
    table(['Control','Luna side','W/L/no-result','Wilson 95%'],[[a,side,[s['wins'],s['losses'],s['limits']],s['wilson_95']] for a in arms for side in ('red','blue') for s in [aa[a]['sides'][side]['luna']]])
    table(['Control','Forfeits','Request limits','Turn limits','Other no-results','Player turns total/median/range','Rounds total/median/range'],[[a,aa[a]['terminal_causes'].get('PROVIDER_FORFEIT',0),aa[a]['terminal_causes'].get('REQUEST_LIMIT',0),aa[a]['terminal_causes'].get('TURN_LIMIT',0),aa[a]['limits']-aa[a]['terminal_causes'].get('REQUEST_LIMIT',0)-aa[a]['terminal_causes'].get('TURN_LIMIT',0),[sum(aa[a]['player_turns']),median(aa[a]['player_turns']),[min(aa[a]['player_turns']),max(aa[a]['player_turns'])]],[sum(aa[a]['rounds_completed']),median(aa[a]['rounds_completed']),[min(aa[a]['rounds_completed']),max(aa[a]['rounds_completed'])]]] for a in arms])
    p('## Repair reliability — all batches')
    table(['Cohort','Control','First invalid/first responses','Repairs attempted','Succeeded','Exhausted','Success rate','Repair-exhaustion forfeits'],[[b,a,f"{s['first_response_invalid_decisions']}/{s['first_responses']}",s['repairs_attempted'],s['repairs_succeeded'],s['repairs_exhausted'],s['repair_success_rate'],s['repair_exhaustion_forfeits']] for b in ('1','2','3','cumulative') for a in arms for s in [forensics['reliability'][b][a]]])
    p('Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).')
    for b in ('1','2','3','cumulative'):p('Batch/cohort '+b+' patterns: `'+json.dumps(forensics['patterns'][b])+'`. Tags may overlap.')
    p('## Requests and bounded recovery')
    metrics(('provider_requests','turns','completed_turns','repairs','repair_success','repair_failure','execution_truncations','initial_execution_invalidities','replans','ap_recovered','replacement_repairs','replacement_invalidities','second_invalidities','decisions'))
    table(['Request purpose',*arms],[[k,*[aa[a]['request_purposes'].get(k,0) for a in arms]] for k in ('initial_planning','repair','bounded_replacement_planning','bounded_replacement_repair','stepwise_decisions')])
    table(['Control','Requests/match','Requests/Luna turn','Requests/completed turn','Actions/Luna turn','Execution invalidity categories'],[[a,aa[a]['per_match']['provider_requests'],aa[a]['per_turn']['provider_requests'],aa[a]['requests_per_completed_turn'],aa[a]['actions_per_turn'],aa[a]['invalidity_categories']] for a in arms])
    p('Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.')
    b=aa['bounded'];s=aa['strict'];w=aa['stepwise'];rec=b['recovery'];extra_req=b['totals']['provider_requests']-s['totals']['provider_requests']
    table(['Bounded metric','Observed'],list(rec.items())+[['Replan rate',b['replan_rate']],['Second invalidity rate',b['second_invalid_rate']],['Replacement explicit EndTurns',b['end_turn']['replacement_stops']],['Replacement failures',sum(c['replacement'] and c['match_id'] in {r['match_id'] for r in selected} for c in forensics['exhaustions'])],['Extra requests vs Strict',extra_req],['Request premium vs Strict (%)',100*extra_req/s['totals']['provider_requests']],['Extra provider seconds vs Strict',b['totals']['provider_latency_seconds']-s['totals']['provider_latency_seconds']],['Extra tokens vs Strict',b['totals']['total_tokens']-s['totals']['total_tokens']],['Extra requests / recovered AP (descriptive)',extra_req/rec['ap_total'] if rec['ap_total'] else None],['Strict minus Bounded final truncations',s['totals']['execution_truncations']-b['totals']['execution_truncations']],['Bounded minus Strict wins',b['wins']-s['wins']]])
    p('Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.')
    p('## Stepwise caps and Bounded comparison')
    table(['Stepwise cap metric','Observed'],list(w['caps'].items()))
    table(['Metric','Bounded','Stepwise'],[[key,b['totals'][key],w['totals'][key]] for key in ('provider_requests','total_tokens','provider_latency_seconds')]+[[key+'/match',b['per_match'][key],w['per_match'][key]] for key in ('provider_requests','total_tokens')]+[[key+'/turn',b['per_turn'][key],w['per_turn'][key]] for key in ('provider_requests','total_tokens','provider_latency_seconds')]+[['W/L/no-result',[b['wins'],b['losses'],b['limits']],[w['wins'],w['losses'],w['limits']]]])
    table(['Capped match','Side','Player turns/rounds/Luna turns','AP/actions','Requests/repairs/EndTurns','Core HP','Engine winner'],[[c['match_id'],c['luna_side'],[c['player_turns'],c['rounds_completed'],c['luna_turns']],[c['ap_executed'],c['actions_executed']],[c['requests'],c['repairs'],c['explicit_end_turns']],c['core_hp'],c['engine_winner']] for c in cap_details if cohort_name=='cumulative' or c['batch']==3])
    p('Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.')
    p('## AP and EndTurn semantics')
    metrics(('ap_available','ap_executed'))
    table(['Unused AP category',*arms],[[k,*[aa[a]['unused_ap_by_reason'][k] for a in arms]] for k in ('INTENTIONAL_END_TURN','CLEAN_PLAN_COMPLETE','EXECUTION_TRUNCATION','PROVIDER_FAILURE','TERMINAL')]+[['Budget-denied AP within generic failure bucket',*[aa[a]['totals']['request_limit_unused_ap'] for a in arms]],['Actual provider-failure AP',*[aa[a]['unused_ap_by_reason']['PROVIDER_FAILURE']-aa[a]['totals']['request_limit_unused_ap'] for a in arms]]])
    p('The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”')
    table(['Control','Explicit stops','Immediate','AP left distribution','Actions before stop','Damaging option left','Down option left','Requests after stop'],[[a,*[aa[a]['end_turn'][k] for k in ('count','immediate','ap_distribution','actions_before_distribution','damaging_opportunity_stops','down_opportunity_stops','requests_after_end_turn')]] for a in arms])
    p('A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.')
    p('## Gameplay and combat')
    metrics(('core_damage_dealt','core_damage_received','enemy_damage','friendly_damage','enemy_units_downed','friendly_units_downed','units_downed_received','finish','revive','heal','snipe','shield_bash','shield_bash_pushes','fireball','empty_fireballs','friendly_only_fireballs','enemy_only_fireballs','mixed_fireballs','enemy_fireball_damage','friendly_fireball_damage'))
    table(['Fireball effect',*arms],[[key,*[aa[a]['fireball'][key] for a in arms]] for key in ('enemy_units_hit','friendly_units_hit','enemy_damage','friendly_damage','enemy_downs','friendly_downs')])
    terminal_fire=[c for c in audit['fireballs'] if c.get('winner_after_action') and (cohort_name=='cumulative' or c['match_id'] in {r['match_id'] for r in selected})]
    p('Fireballs immediately producing an engine winner: `'+json.dumps(terminal_fire)+'`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.')
    table(['Ability effect',*arms],[[kind+' '+key,*[aa[a]['ability_effects'][kind][key] for a in arms]] for kind in ('arena_snipe','arena_shield_bash') for key in ('enemy_damage','friendly_damage','enemy_downs','enemy_displacements')])
    table(['Heuristic mechanics by matchup',*arms],[[k,*[aa[a]['heuristic']['totals'].get(k) for a in arms]] for k in ('core_damage_dealt','core_damage_received','enemy_units_downed','finish','revive','ap_executed','provider_requests','total_tokens','provider_latency_seconds','heuristic_compute_seconds')])
    p('Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.')
    p('## Resources and calibration')
    fields=('provider_requests','input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens','provider_latency_seconds','backend_thinking_seconds')
    metrics(fields)
    table(['Resource','Batch 1','Batch 2','Batch 3','Cumulative'],[[k,*[sum(data[co]['arms'][a]['totals'][k] for a in arms) for co in ('batch_1','batch_2','batch_3','cumulative')]] for k in fields])
    table(['Control','Requests/match','Tokens/match','Requests/turn','Tokens/turn','Provider sec/turn','Backend sec/turn','Evidence elapsed sec'],[[a,aa[a]['per_match']['provider_requests'],aa[a]['per_match']['total_tokens'],*[aa[a]['per_turn'][k] for k in ('provider_requests','total_tokens','provider_latency_seconds','backend_thinking_seconds')],aa[a]['evidence_elapsed_seconds']] for a in arms])
    table(['Batch','Observed process wall seconds upper bound','Start UTC','Completion observed UTC'],[[b,t['wall_seconds_upper_bound'],t['start_utc'],t['end_observed_utc']] for b,t in timings.items()])
    p('Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.')
    p('## Updated projection from cumulative rates')
    for key in ('provider_requests','total_tokens','provider_latency_seconds'):
        table([key,'Observed','Mean/match','Remaining 70/control','All 100/control','Observed match min/max','Remaining sensitivity','All 100 sensitivity'],[[a,*[projection[a][key][k] for k in ('observed','per_match','remaining_central','total_100_central','observed_min_max','remaining_sensitivity','total_100_sensitivity')]] for a in arms])
        vals=[projection[a][key] for a in arms];rem=sum(v['remaining_central'] for v in vals);full=sum(v['total_100_central'] for v in vals)
        p(f'Combined {key}: remaining 210 central **{rem:,.3f}**; full 300 central **{full:,.3f}**. Full-study sensitivity {[sum(v["total_100_sensitivity"][i] for v in vals) for i in (0,1)]}.')
        if key=='provider_latency_seconds':p(f'Provider hours: remaining **{rem/3600:.4f}**, full **{full/3600:.4f}**.')
    p('Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.')
    walls=[t['wall_seconds_upper_bound'] for t in timings.values()];p(f'If future batch workloads resemble the three observed batches, seven remaining batches span {7*min(walls)/3600:.3f}–{7*max(walls)/3600:.3f} wall hours; full study {(sum(walls)+7*min(walls))/3600:.3f}–{(sum(walls)+7*max(walls))/3600:.3f} hours. This is a workload illustration, not a guaranteed bound: larger-prefix verification, provider conditions, caps and post-run analysis can add time.')
    p('## Matched triplet patterns and differences')
    p('Order is Strict / Bounded / Stepwise. Outcome patterns: `'+json.dumps(co['triplet_patterns'])+'`; all-three-same outcome triplets: '+str(co['all_three_same_outcome'])+'.')
    for pair in co['paired']:p('`'+json.dumps(pair)+'`')
    table(['Slot','Luna side','Outcomes S/B/W','Requests S/B/W','Player turns S/B/W','Request difference B-S/W-B','Turn difference B-S/W-B'],[[t['slot'],t['luna_side'],t['outcomes'],t['requests'],t['player_turns'],[t['bounded_minus_strict_requests'],t['stepwise_minus_bounded_requests']],[t['bounded_minus_strict_turns'],t['stepwise_minus_bounded_turns']]] for t in co['triplets']])
    p('## Per-match evidence')
    table(['Match','Side','Outcome/cause','Turns/rounds','Requests/Luna turns','AP executed; I/C/X/P/T unused','Core damage dealt/received','Enemy downs/Finish/Revive','Final state hash'],[[r['match_id'],r['luna_side'],r['luna_outcome']+'/'+r['terminal_cause'],[r['player_turns'],r['rounds_completed']],[r['requests'],r['metrics'][r['luna_side']]['turns']],[r['metrics'][r['luna_side']]['ap_executed'],*[r['metrics'][r['luna_side']]['unused_ap_by_reason'][k] for k in ('INTENTIONAL_END_TURN','CLEAN_PLAN_COMPLETE','EXECUTION_TRUNCATION','PROVIDER_FAILURE','TERMINAL')]],[r['metrics'][r['luna_side']]['core_damage_dealt'],r['metrics'][r['luna_side']]['core_damage_received']],[r['metrics'][r['luna_side']]['enemy_units_downed'],r['metrics'][r['luna_side']]['finish'],r['metrics'][r['luna_side']]['revive']],audit_by_id[r['match_id']]['final_state_hash']] for r in selected])
    p('## Decision and limitations')
    p('See [decision.md](decision.md) for PASS/PAUSE, all ten research-question answers and next authorization scope. Results remain interim at n=30/control. Frozen confirmatory analysis waits for 100/control. No tuning, replacement of failed/capped games, or next-batch execution occurred. Figures: [figures.md](figures.md); machine-readable metrics: interim-metrics.json; command audits: supplemental-audit.json; repair evidence: repair-forensics.json.')
    (root/filename).write_text('\n'.join(lines),encoding='utf-8')

render_report('batch_3','batch-3-report.md',10)
render_report('cumulative','cumulative-batches-1-3-report.md',30)
print(json.dumps(dict(batch_3=data['batch_3']['matches'],cumulative=data['cumulative']['matches'],reports_written=True)))

