"""Supplemental descriptive tables over frozen analysis and audited command evidence."""
import json
from pathlib import Path
from collections import Counter
from statistics import median
from aig.arena.case_study_contract import read, sha, digest
from aig.arena.case_study_analysis import summarize, paired

root=Path(__file__).parent
audit=read(root/'supplemental-audit.json'); contract=read(root/'contract.json'); pre=read(root/'batch-2-preflight.json')
integrity=read(root/'integrity.json'); post=read(root/'postprocess-verification.json')
rows=[read(root/'matches'/r['match_id']/'result.json') for r in audit['matches']]
arms=('strict','bounded','stepwise')
timing=json.loads((root/'execution-timing.json').read_text(encoding='utf-8-sig'))
b1timing=json.loads((Path(pre['original_root'])/'execution-timing.json').read_text(encoding='utf-8-sig'))
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

data={name:cohort([r for r in rows if r['batch'] in batches],name) for name,batches in [('batch_1',[1]),('batch_2',[2]),('cumulative',[1,2])]}
projection={}
for arm in arms:
    rr=[r for r in rows if r['arm']==arm];n=len(rr);remain=100-n;projection[arm]={}
    for key in ('provider_requests','total_tokens','provider_latency_seconds'):
        values=[r['metrics'][r['luna_side']][key] for r in rr]
        projection[arm][key]=None if not values or any(v is None for v in values) else dict(
            observed=sum(values),per_match=sum(values)/n,remaining_matches=remain,remaining_central=sum(values)/n*remain,total_100_central=sum(values)/n*100,
            observed_min_max=[min(values),max(values)],remaining_sensitivity=[min(values)*remain,max(values)*remain],
            total_100_sensitivity=[sum(values)+min(values)*remain,sum(values)+max(values)*remain])
data['projection']=projection;data['batch_2_manifest_sha256']=pre['batch_schedule_sha256']
(root/'interim-metrics.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def fmt(v):
    if v is None:return 'unknown / not applicable'
    if isinstance(v,float):return f'{v:,.4f}'
    if isinstance(v,(dict,list)):return json.dumps(v)
    return str(v)

def report(name,filename,n):
    cc=data[name]; aa=cc['arms']; selected=[r for r in rows if r['batch']==2] if name=='batch_2' else rows
    lines=[]
    def p(s=''):lines.extend([s,''])
    def table(head,values):
        lines.append('| '+' | '.join(head)+' |');lines.append('| '+' | '.join(['---']*len(head))+' |')
        for row in values:lines.append('| '+' | '.join(fmt(v) for v in row)+' |')
        lines.append('')
    def metrics(fields):table(['Metric',*arms],[[title,*[aa[a]['totals'].get(key) for a in arms]] for title,key in fields])
    p('# '+('Batch 2 standalone' if name=='batch_2' else 'Cumulative Batches 1–2')+' — interim case-study report')
    p(f'**Preliminary n={n}/control; {len(selected)} sealed matches.** One canonical opening and nondeterministic Luna trajectories. No confirmatory tests, composite score, superiority or equivalence claim. [Decision and interpretation](decision.md).')
    p('## Execution and integrity')
    p('Only Batch 2 was newly run. The original Batch 1 directory was preserved byte-for-byte; the verified prefix was copied to arena-case-study-live-v1-02 because frozen resume refreshes cumulative aggregate views. Resume continued at MATCH-011 Bounded, request 584. No Batch 1 request/match was repeated. No interruption recovery was needed during Batch 2. The command stops at --through-batch 2; Batch 3 was not started.')
    p('```powershell\n.venv/Scripts/python.exe -B -m aig.arena.case_study verify\n.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-02 --through-batch 2 --authorize-live arena-case-study-benchmark-v1\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-02/postprocess.py\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-02/supplemental-audit.py\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-02/interim-report.py\n```')
    p('postprocess.py invokes the unchanged case_study_contract.verify and case_study.integrity, then the unchanged case_study_analysis.analyze on the verified cumulative prefix and the batch==2 subset. Supplemental scripts only derive reporting from sealed evidence and never call providers.')
    table(['Binding','Value'],[['Benchmark',contract['payload']['id']],['Contract payload SHA-256',contract['sha256']],['Contract file SHA-256',sha(root/'contract.json')],['Full schedule SHA-256',contract['payload']['schedule_hash']],['Batch 2 schedule SHA-256',pre['batch_schedule_sha256']],['Source manifest SHA-256',pre['source_manifest_sha256']],['Frozen source files',len(contract['payload']['source_hashes'])]])
    p('Frozen bindings: gpt-5.6-luna / luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 / arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2; arena-scenario-v1. Full immutable hashes/configuration are in contract.json. No frozen source or analyzer was modified.')
    p('Final frozen verification: `'+json.dumps(integrity)+'`. It verifies source/runtime, exact schedule/side prefix, all command replays, observations/control bindings, deterministic heuristic actions, metrics, request ledger/receipts/seals and zero fallback. Original Batch 1 files checked: '+str(post['original_batch_1_files_verified'])+'; copied immutable prefix files checked: '+str(post['copied_immutable_prefix_files_verified'])+'.')
    p('Batch 2 manifest is schedule.json entries 31–60, MATCH-011–020, 30 intended matches and five Red/five Blue per control. The authoritative pre-send ledger enforces 1,700 Batch 2 requests, per-control 300/500/900 and per-match 50/80/140. Study ceiling remains 15,000. No extra retries or fallback. Provider repair exhaustion is a forfeit; limits receive no winner. Turn bounds remain 200 player turns / 100 completed rounds.')
    table(['Control','Intended','Started in cohort','Sealed','Red/Blue','Natural endings','Forfeits','No-result'],[[a,n,len([r for r in selected if r['arm']==a]),aa[a]['matches'],dict(Counter(r['luna_side'] for r in selected if r['arm']==a)),sum(aa[a]['terminal_causes'].get(k,0) for k in ('CORE_DESTRUCTION','TEAM_ELIMINATION')),aa[a]['terminal_causes'].get('PROVIDER_FORFEIT',0),aa[a]['limits']] for a in arms])
    p('## Outcomes and heuristic baseline')
    table(['Agent / matchup','Wins','Losses incl. forfeits','No-result','Win rate','Wilson 95%','Requests/turn'],[[a+' Luna' if who=='luna' else 'Heuristic vs '+a,s['wins'],s['losses'],s['limits'],s['win_rate'],s['wilson_95'],s['per_turn']['provider_requests']] for a in arms for who in ('luna','heuristic') for s in [aa[a] if who=='luna' else aa[a]['heuristic']]])
    table(['Control','Luna side','Wins','Losses','Limits','Wilson 95%'],[[a,side,s['wins'],s['losses'],s['limits'],s['wilson_95']] for a in arms for side in ('red','blue') for s in [aa[a]['sides'][side]['luna']]])
    table(['Control','Terminal causes','Player turns total/median/min/max','Rounds total/median/min/max'],[[a,aa[a]['terminal_causes'],[sum(aa[a]['player_turns']),median(aa[a]['player_turns']),min(aa[a]['player_turns']),max(aa[a]['player_turns'])],[sum(aa[a]['rounds_completed']),median(aa[a]['rounds_completed']),min(aa[a]['rounds_completed']),max(aa[a]['rounds_completed'])]] for a in arms if aa[a]['matches']])
    p('## Requests and controls')
    metrics([('Provider requests','provider_requests'),('Attempted Luna turns','turns'),('Completed Luna turns','completed_turns'),('First responses','first_responses'),('First valid responses','first_response_valid'),('Repairs','repairs'),('Successful repairs','repair_success'),('Failed repairs','repair_failure'),('Provider failures excluding budget denial','provider_failures'),('Execution truncations','execution_truncations'),('Initial execution invalidities','initial_execution_invalidities'),('Bounded replans','replans'),('Replacement repairs','replacement_repairs'),('Replacement invalidities','replacement_invalidities'),('Second execution invalidities','second_invalidities'),('AP recovered','ap_recovered'),('Decisions including denied budgets','decisions')])
    table(['Control','Requests/match','Requests/Luna turn','Requests/completed turn','Actions/Luna turn','Invalidity categories'],[[a,aa[a]['per_match']['provider_requests'],aa[a]['per_turn']['provider_requests'],aa[a]['requests_per_completed_turn'],aa[a]['actions_per_turn'],aa[a]['invalidity_categories']] for a in arms])
    table(['Disjoint request purpose',*arms],[[key,*[aa[a]['request_purposes'].get(key,0) for a in arms]] for key in ('initial_planning','repair','bounded_replacement_planning','bounded_replacement_repair','stepwise_decisions')])
    p('Stepwise decisions in the request-purpose table exclude repair and budget-denied decisions. Repair includes initial-wave and Stepwise repairs; replacement repairs are separate. Requests/turn use attempted Luna turns. Truncations are execution-ending stops, not every invalidity that Bounded subsequently recovered.')
    b=aa['bounded']; rec=b['recovery']; st=aa['strict'];sw=aa['stepwise']
    table(['Bounded question','Observed'],[['Replans',rec['replans']],['Positive-AP recoveries',rec['positive']],['Positive recovery fraction',rec['positive_fraction']],['Total AP recovered',rec['ap_total']],['Mean AP/replan',rec['mean_ap_per_replan']],['Second-invalidity rate',b['second_invalid_rate']],['Requests/turn',b['per_turn']['provider_requests']],['Extra total requests vs Strict',b['totals'].get('provider_requests',0)-st['totals'].get('provider_requests',0)],['Bounded/Strict total request ratio',b['totals']['provider_requests']/st['totals']['provider_requests'] if st['totals'].get('provider_requests') else None],['Bounded/Strict requests-per-turn ratio',b['per_turn']['provider_requests']/st['per_turn']['provider_requests'] if st['per_turn'].get('provider_requests') else None],['AP at each replan',rec['ap_at_replan']],['AP recovered per replan',rec['ap_recovered']]])
    table(['Stepwise question','Observed'],list(sw['caps'].items())+[['Requests/Luna turn',sw['per_turn']['provider_requests']],['Decisions/Luna turn',sw['totals']['decisions']/sw['totals']['turns']],['Requests after explicit EndTurn',sw['end_turn']['requests_after_end_turn']]])
    p('## AP and EndTurn')
    metrics([('AP available','ap_available'),('AP executed','ap_executed')])
    table(['AP reason',*arms],[[reason,*[aa[a]['unused_ap_by_reason'][reason] for a in arms]] for reason in ('INTENTIONAL_END_TURN','CLEAN_PLAN_COMPLETE','EXECUTION_TRUNCATION','PROVIDER_FAILURE','TERMINAL')]+[['Budget-denied AP within generic failure bucket',*[aa[a]['totals'].get('request_limit_unused_ap',0) for a in arms]],['Actual provider-failure AP',*[aa[a]['unused_ap_by_reason']['PROVIDER_FAILURE']-aa[a]['totals'].get('request_limit_unused_ap',0) for a in arms]]])
    p('Generic PROVIDER_FAILURE includes budget denial in frozen controller telemetry; actual provider-failure AP is adjusted in the last row. Intentional, clean, truncation, provider, budget and terminal AP are not a composite quality score.')
    table(['Control','Explicit stops','Immediate','AP remaining distribution','Actions before stop','Damaging option left','Down option left','Replacement stops','Requests after EndTurn'],[[a,*[aa[a]['end_turn'][k] for k in ('count','immediate','ap_distribution','actions_before_distribution','damaging_opportunity_stops','down_opportunity_stops','replacement_stops','requests_after_end_turn')]] for a in arms])
    p('Damaging/down opportunities are legal single actions simulated from the authoritative pre-EndTurn state. They flag potentially premature stops without claiming an action was strategically preferable. Exact stop records/opportunities are in supplemental-audit.json. No model judge or live counterfactual inference was used.')
    p('## Combat and tactics')
    metrics([('Core damage dealt','core_damage_dealt'),('Core damage received','core_damage_received'),('Enemy unit damage','enemy_damage'),('Friendly unit damage','friendly_damage'),('Enemy downs','enemy_units_downed'),('Friendly downs','friendly_units_downed'),('Downs received','units_downed_received'),('Finishes','finish'),('Revives','revive'),('Snipe uses','snipe'),('Shield Bash uses','shield_bash'),('Shield Bash pushes','shield_bash_pushes'),('Fireball uses','fireball'),('Enemy Fireball damage','enemy_fireball_damage'),('Friendly Fireball damage','friendly_fireball_damage'),('Empty Fireballs','empty_fireballs'),('Friendly-only Fireballs','friendly_only_fireballs'),('Enemy-only Fireballs','enemy_only_fireballs'),('Mixed Fireballs','mixed_fireballs'),('Basic attacks','attacks'),('Core attacks','core_attacks'),('Moves','move'),('Heals','heal')])
    table(['Fireball effect',*arms],[[key,*[aa[a]['fireball'][key] for a in arms]] for key in ('enemy_units_hit','friendly_units_hit','enemy_damage','friendly_damage','enemy_downs','friendly_downs')])
    table(['Ability effect',*arms],[[kind+' '+key,*[aa[a]['ability_effects'][kind][key] for a in arms]] for kind in ('arena_snipe','arena_shield_bash') for key in ('enemy_damage','friendly_damage','enemy_downs','friendly_downs','enemy_displacements')])
    table(['Heuristic mechanical total by matchup',*arms],[[key,*[aa[a]['heuristic']['totals'].get(key) for a in arms]] for key in ('core_damage_dealt','core_damage_received','enemy_units_downed','finish','revive','ap_executed','provider_requests','total_tokens','provider_latency_seconds','heuristic_compute_seconds')])
    p('Counts are exposure-dependent and can include repeated downs/revivals of the same unit. Heuristic inference is zero; measured heuristic computation is separate. Heuristic matchup strata are not pooled. Per-match engine command traces preserve all action effects.')
    p('## Resources and calibration')
    fields=('provider_requests','input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens','provider_latency_seconds','backend_thinking_seconds')
    metrics([(k,k) for k in fields])
    table(['Resource','Batch 1','Batch 2','Cumulative'],[[k,*[sum(data[co]['arms'][a]['totals'][k] for a in arms) for co in ('batch_1','batch_2','cumulative')]] for k in fields])
    table(['Control','Requests/match','Tokens/match','Requests/turn','Tokens/turn','Provider sec/turn','Backend sec/turn','Evidence elapsed sec'],[[a,aa[a]['per_match']['provider_requests'],aa[a]['per_match']['total_tokens'],*[aa[a]['per_turn'][k] for k in ('provider_requests','total_tokens','provider_latency_seconds','backend_thinking_seconds')],aa[a]['evidence_elapsed_seconds']] for a in arms])
    p(f"Batch 1 observed process wall upper bound: {b1timing['wall_seconds_upper_bound']:.3f} s. Batch 2 process wall upper bound: {timing['wall_seconds_upper_bound']:.3f} s. Sum: {b1timing['wall_seconds_upper_bound']+timing['wall_seconds_upper_bound']:.3f} s. Timing begins at process start and ends at observed successful exit, including short observation delay and Batch 2 initial offline prefix verification. Post-run analysis time is excluded. Provider and backend times overlap, so do not add them. Match evidence elapsed is manifest-to-seal duration; it excludes between-match gates. Cached input is a subset of input, and reasoning a subset of output.")
    p('## Updated projection from cumulative observations')
    for key in ('provider_requests','total_tokens','provider_latency_seconds'):
        table([key,'Observed cumulative','Per-match mean','Remaining 80/control','All 100/control','Observed match min/max','Remaining sensitivity','All 100 sensitivity'],[[a,*[projection[a][key][k] for k in ('observed','per_match','remaining_central','total_100_central','observed_min_max','remaining_sensitivity','total_100_sensitivity')]] for a in arms if projection[a][key] is not None])
        vals=[projection[a][key] for a in arms]
        if all(v is not None for v in vals):
            rem=sum(v['remaining_central'] for v in vals);full=sum(v['total_100_central'] for v in vals)
            p(f'Combined {key}: remaining 240 central **{rem:,.3f}**, full 300 central **{full:,.3f}**. Remaining observed-extreme sensitivity: {[sum(v["remaining_sensitivity"][i] for v in vals) for i in (0,1)]}; full-study sensitivity: {[sum(v["total_100_sensitivity"][i] for v in vals) for i in (0,1)]}.')
            if key=='provider_latency_seconds':p(f'Provider hours: remaining **{rem/3600:.4f}**, full study **{full/3600:.4f}**.')
    p('Central projection uses each control’s cumulative mean. The extreme sensitivity assigns every remaining game that control’s observed minimum or maximum and holds collected results fixed; it is not a confidence interval. It can exceed frozen limits, in which case guards stop the study. Request-limited games are censored outcomes, and early forfeits can lower observed costs. No dollar pricing is inferred.')
    b1=b1timing['wall_seconds_upper_bound'];b2=timing['wall_seconds_upper_bound'];p(f'Wall-clock planning sensitivity, if future batches resemble either observed batch: remaining eight batches {8*min(b1,b2)/3600:.3f}–{8*max(b1,b2)/3600:.3f} hours; full study {(b1+b2+8*min(b1,b2))/3600:.3f}–{(b1+b2+8*max(b1,b2))/3600:.3f} hours. This excludes future standalone analysis and is only a two-batch workload illustration. Longer cumulative prefix verification, provider conditions and cap frequency can move wall time outside it.')
    p('## Paired triplets')
    p('Order in each list: Strict / Bounded / Stepwise. Frozen analysis is descriptive at this interim sample; McNemar p-values and bootstrap inferential intervals remain absent until the prespecified complete cohort.')
    p('Outcome patterns: `'+json.dumps(cc['triplet_patterns'])+'`; all-three-same outcome triplets: '+str(cc['all_three_same_outcome'])+'.')
    for comparison in cc['paired']:p('`'+json.dumps(comparison)+'`')
    table(['Slot','Side','Outcomes S/B/W','Requests S/B/W','Player turns S/B/W','Request difference B-S/W-B','Turn difference B-S/W-B'],[[t['slot'],t['luna_side'],t['outcomes'],t['requests'],t['player_turns'],[t['bounded_minus_strict_requests'],t['stepwise_minus_bounded_requests']],[t['bounded_minus_strict_turns'],t['stepwise_minus_bounded_turns']]] for t in cc['triplets']])
    p('## Per-match evidence')
    table(['Match','Side','Outcome/cause','Turns/rounds','Requests/Luna turns','AP executed; I/C/X/P/T unused','Core damage dealt/received','Enemy downs/Finish/Revive','Final state hash'],[[r['match_id'],r['luna_side'],r['luna_outcome']+'/'+r['terminal_cause'],[r['player_turns'],r['rounds_completed']],[r['requests'],r['metrics'][r['luna_side']]['turns']],[r['metrics'][r['luna_side']]['ap_executed'],*[r['metrics'][r['luna_side']]['unused_ap_by_reason'][k] for k in ('INTENTIONAL_END_TURN','CLEAN_PLAN_COMPLETE','EXECUTION_TRUNCATION','PROVIDER_FAILURE','TERMINAL')]],[r['metrics'][r['luna_side']]['core_damage_dealt'],r['metrics'][r['luna_side']]['core_damage_received']],[r['metrics'][r['luna_side']]['enemy_units_downed'],r['metrics'][r['luna_side']]['finish'],r['metrics'][r['luna_side']]['revive']],audit_by_id[r['match_id']]['final_state_hash']] for r in selected])
    p('## Decision and limitations')
    p('See [decision.md](decision.md) for the final PASS/PAUSE recommendation, comparisons and next authorization scope. Tactical weakness alone is not an infrastructure blocker. This sample remains interim; spending AP or recovering AP does not prove better game quality. Do not change prompts, controls, caps, opponent or analysis after observing these results. Batch 3 was not run.')
    p('Prepared figures: standalone in batch-2-analysis/plots/; cumulative in plots/. Each view contains 11 PNG and 11 SVG outputs from the unchanged frozen analyzer. See [figures.md](figures.md) for small-sample and AP-bucket captions. Full metrics and audit details: interim-metrics.json, supplemental-audit.json, analysis.json and batch-2-analysis/analysis.json.')
    (root/filename).write_text('\n'.join(lines),encoding='utf-8')

report('batch_2','batch-2-report.md',10)
report('cumulative','cumulative-batches-1-2-report.md',20)
print(json.dumps(dict(batch_2=data['batch_2']['matches'],cumulative=data['cumulative']['matches'],reports_written=True)))
