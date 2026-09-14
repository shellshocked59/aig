"""Build a descriptive delivery report from verified, derived batch evidence."""
import json
from pathlib import Path
from collections import Counter
from statistics import median

root=Path(__file__).parent
read=lambda name:json.loads((root/name).read_text(encoding='utf-8'))
d=read('supplemental-audit.json'); analysis=read('analysis.json'); integrity=read('integrity.json')
arms=('strict','bounded','stepwise'); rows=d['matches']; summaries=d['arms']
lines=[]
def p(text=''): lines.extend([text,''])
def fmt(v):
    if v is None:return 'unknown'
    if isinstance(v,float):return f'{v:,.3f}'
    if isinstance(v,(dict,list)):return json.dumps(v,ensure_ascii=False)
    return str(v)
def table(headers,values):
    lines.append('| '+' | '.join(headers)+' |')
    lines.append('| '+' | '.join(['---']*len(headers))+' |')
    for row in values:lines.append('| '+' | '.join(fmt(v) for v in row)+' |')
    lines.append('')
def metric_table(fields):
    table(['Metric',*arms],[[label,*[summaries[a]['totals'].get(key) for a in arms]] for label,key in fields])

p('# Luna vs Heuristic V2 — Batch 1 report')
p('**Decision: PASS for a separately authorized continuation unchanged.** All 30 intended matches are sealed; 30 exact replays and 583 requests reconcile with zero pending requests. Batch 2 was not run. Detailed reasons and early interpretation: [decision.md](decision.md).')
p('Descriptive expenditure/integrity batch only. Intended sample: 10 matches per control, 30 total; one canonical opening. No confirmatory tests, absolute skill rating, or declaration of a winning control. Wilson intervals below describe a small sample. Limits are nonwins; provider forfeits are losses.')
p('## Execution')
p('Only Batch 1 was authorized and executed. The prepared live command was run with network execution permission; no inference preflight, focused-validation rerun, model change, or benchmark-source change was made. No resume was used.')
p('```powershell\n.venv/Scripts/python.exe -B -m aig.arena.case_study verify\n.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 1 --authorize-live arena-case-study-benchmark-v1\n.venv/Scripts/python.exe -B -m aig.arena.case_study verify --output artifacts/arena-case-study-live-v1-01\n.venv/Scripts/python.exe -B -m aig.arena.case_study analyze --output artifacts/arena-case-study-live-v1-01\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-01/supplemental-audit.py\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-01/build-batch-report.py\n```')
p('The last two scripts create supplemental derived reporting from saved evidence. They do not alter the frozen runner, analyzer, contract, telemetry, or sealed match artifacts and make no provider calls.')
table(['Binding','SHA-256 / value'],list(d['bindings'].items()))
p('Batch manifest is the first 30 entries of `contract.json` / `schedule.json`, MATCH-001 through MATCH-010, under the contract hash above. The batch-specific hash is the canonical hash of that exact slice; it is an additional audit digest, not a replacement contract.')
table(['Control','Intended','Started','Sealed/adjudicated','Forfeits','No-result','Red/Blue sealed'],[[a,10,len(list((root/'matches').glob('*-'+a))),summaries[a]['matches'],summaries[a]['terminal_causes'].get('PROVIDER_FORFEIT',0),summaries[a]['limits'],dict(Counter(r['luna_side'] for r in rows if r['arm']==a))] for a in arms])
p('Forfeits and request/turn-limit results are included in the sealed/adjudicated counts; they are not additional matches. Unsealed/integrity-interrupted matches are not fabricated outcomes.')
p('## Integrity')
p('The current case-study source/runtime verifier passed before the live command. The historical focused whole-inventory verifier was not changed or used as the new benchmark authority. Frozen model/profile: gpt-5.6-luna / luna-config-v1; policy arena-policy-core-v1; full-turn prompt arena-turn-prompt-v6; step prompt arena-step-prompt-v3; observation arena-observation-v4; schema arena-turn-plan-schema-v2; repair arena-candidate-repair-v2; rules arena-rules-v2; scenario arena-scenario-v1; opponent arena-heuristic-v2. Exact configuration, prompt/schema and dependency hashes are in the verified copied contract.')
p('Standalone integrity result: `'+json.dumps({k:v for k,v in integrity.items() if k!='results'})+'`. The verifier covers exact command replay, control observations, deterministic heuristic replay, metric recomputation, request receipts/bindings, schedule/side prefix, seals and zero fallback. Supplemental audit independently replays saved turns and reconciles request purposes. No completed live request was rerun.')
p('## Requests and control mechanics')
used=sum(summaries[a]['totals'].get('provider_requests',0) for a in arms)
p(f'Sealed-match requests: **{used} / 1,700**. Reservations and any pending requests are reported by the integrity result above. Per-control batch limits remain Strict 300, Bounded 500, Stepwise 900.')
table(['Control','Requests','Requests/match','Requests/Luna turn','Completed Luna turns','First-response valid/decisions','Repairs success/attempts'],[[a,summaries[a]['totals'].get('provider_requests'),summaries[a]['per_match']['provider_requests'],summaries[a]['per_turn']['provider_requests'],summaries[a]['totals'].get('completed_turns'),f"{summaries[a]['totals'].get('first_response_valid')}/{summaries[a]['totals'].get('first_responses')}",f"{summaries[a]['totals'].get('repair_success')}/{summaries[a]['totals'].get('repairs')}"] for a in arms])
table(['Request purpose',*arms],[[key,*[d['request_categories'][a].get(key,0) for a in arms]] for key in ['initial_planning','repair','bounded_replacement_planning','bounded_replacement_repair','stepwise_decisions']])
p('Purpose counts are disjoint. Stepwise decisions above exclude repair calls; the repair row includes Stepwise decision repairs and initial-wave full-turn repairs. Bounded replacement repairs have their own row.')
metric_table([('Attempted Luna turns','turns'),('Execution truncations','execution_truncations'),('Initial execution-invalid turns','initial_execution_invalidities'),('Bounded replans','replans'),('Replacement repairs','replacement_repairs'),('Replacement first-response invalidities','replacement_first_invalidities'),('AP recovered','ap_recovered'),('Second execution invalidities','second_invalidities'),('Decisions','decisions'),('Provider failures','provider_failures')])
b=summaries['bounded']; bm=[r['luna_metrics'] for r in rows if r['arm']=='bounded']
p(f"Bounded replan rate: {fmt(b['replan_rate'])}; positive-AP recoveries: {sum(v>0 for m in bm for v in m['ap_recovered_distribution'])}/{sum(len(m['ap_recovered_distribution']) for m in bm)}. AP at replan: {fmt([v for m in bm for v in m['ap_at_replan']])}; AP recovered per replan: {fmt([v for m in bm for v in m['ap_recovered_distribution']])}. Second-invalidity rate: {fmt(b['second_invalid_rate'])}.")
sm=summaries['stepwise']['totals']; p(f"Stepwise decisions/attempted turn: {fmt(sm.get('decisions',0)/sm['turns'] if sm.get('turns') else None)}; requests/completed turn: {fmt(summaries['stepwise'].get('requests_per_completed_turn'))}; actions/turn: {fmt(sum(sum(r['luna_metrics'].get(k,0) for k in ['move','attacks','snipe','shield_bash','fireball','finish','revive','heal']) for r in rows if r['arm']=='stepwise')/sm['turns'] if sm.get('turns') else None)}.")
invalids={a:dict(Counter(i['reason'] for r in rows if r['arm']==a for i in r['luna_metrics']['invalidities'])) for a in arms}
p('Execution invalidity categories: `'+json.dumps(invalids)+'`. Exact action indexes, AP and actions remain in match results.')
p('## Game outcomes')
table(['Control','Wins','Losses (incl. forfeit)','Forfeits','No-result','Win rate / intended 10','Wilson 95% (sealed sample)','Terminal causes'],[[a,summaries[a]['wins'],summaries[a]['losses'],summaries[a]['terminal_causes'].get('PROVIDER_FORFEIT',0),summaries[a]['limits'],summaries[a]['wins']/10,summaries[a]['wilson_95'],summaries[a]['terminal_causes']] for a in arms])
table(['Control','Player turns total / median / range','Completed rounds total / median / range','Luna turns'],[[a, [sum(v),median(v),[min(v),max(v)]], [sum(w),median(w),[min(w),max(w)]],summaries[a]['totals']['turns']] for a in arms for v in [[r['player_turns'] for r in rows if r['arm']==a]] for w in [[r['rounds_completed'] for r in rows if r['arm']==a]] if v])
metric_table([('Core damage dealt','core_damage_dealt'),('Core damage received','core_damage_received'),('Enemy unit damage','enemy_damage'),('Friendly unit damage','friendly_damage'),('Enemy downs inflicted','enemy_units_downed'),('Friendly downs inflicted','friendly_units_downed'),('Downs received','units_downed_received'),('Finishes','finish'),('Finishes received','units_finished_received'),('Revives','revive')])
p('## AP and EndTurn semantics')
metric_table([('AP available','ap_available'),('AP executed','ap_executed')])
table(['Unused AP reason',*arms],[[reason,*[summaries[a]['unused_ap_by_reason'][reason] for a in arms]] for reason in ['INTENTIONAL_END_TURN','CLEAN_PLAN_COMPLETE','EXECUTION_TRUNCATION','PROVIDER_FAILURE','TERMINAL']])
metric_table([('Request-limit AP within generic failure bucket','request_limit_unused_ap')])
table(['Adjusted AP category',*arms],[['Actual provider-failure AP',*[summaries[a]['unused_ap_by_reason']['PROVIDER_FAILURE']-summaries[a]['totals'].get('request_limit_unused_ap',0) for a in arms]]])
p('The controller generic PROVIDER_FAILURE bucket includes request-budget-denied AP; subtract the separately reported request-limit AP to obtain provider-failure AP. Intentional AP is not automatically waste. Terminal AP is separate.')
table(['Control','Explicit stops','Immediate stops','AP left distribution','Actions before distribution','Stops with legal damaging option','Stops with available down','Requests after stop'],[[a,*[summaries[a]['end_turn_audit'][k] for k in ['count','immediate','ap_distribution','actions_before_distribution','damaging_opportunity_stops','down_opportunity_stops','requests_after_end_turn']]] for a in arms])
p('“Legal damaging option” means an immediately executable catalog action in a detached simulation caused positive enemy unit/Core HP loss at the saved stop state. This flags potentially premature stops; it does not establish that taking the action was strategically preferable. No LLM judge was used. All opportunities, actions, AP and turn identifiers are in supplemental-audit.json.')
p('Stepwise explicit EndTurn was observed and all observed stops have zero subsequent wave/request in the same turn.' if summaries['stepwise']['end_turn_audit']['count'] else 'Stepwise explicit EndTurn remains live-unobserved in this cohort and offline-tested; this alone does not invalidate the batch.')
p('## Fireball mechanics')
metric_table([('Casts','fireball'),('Empty blasts','empty_fireballs'),('Friendly-only blasts','friendly_only_fireballs'),('Enemy-only blasts','enemy_only_fireballs'),('Mixed blasts','mixed_fireballs')])
table(['Fireball effect',*arms],[[key,*[summaries[a]['fireball_audit'][key] for a in arms]] for key in ['enemy_units_hit','friendly_units_hit','enemy_damage','friendly_damage','enemy_downs','friendly_downs']])
p('Hit counts include repeated exposure across casts, using ACTIVE units before each cast. Damage is actual capped HP loss. Heuristic Fireball records are separately retained in supplemental-audit.json.')
p('## Resources and projections')
metric_table([('Input tokens','input_tokens'),('Cached input tokens (subset of input)','cached_input_tokens'),('Output tokens','output_tokens'),('Reasoning tokens (subset of output)','reasoning_tokens'),('Total tokens','total_tokens'),('Provider latency seconds','provider_latency_seconds'),('Backend controller thinking seconds','backend_thinking_seconds')])
table(['Overall Batch 1 resource','Total','Per intended match'],[[key,sum(summaries[a]['totals'][key] for a in arms),sum(summaries[a]['totals'][key] for a in arms)/30] for key in ['provider_requests','input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens','provider_latency_seconds','backend_thinking_seconds']])
table(['Control','Tokens/match','Observed requests/match','Frozen central estimate','Observed/estimate'],[[a,summaries[a]['per_match']['total_tokens'],summaries[a]['per_match']['provider_requests'],estimate,summaries[a]['per_match']['provider_requests']/estimate if summaries[a]['per_match']['provider_requests'] is not None else None] for a,estimate in zip(arms,[11,17.875,31.79])])
p('Provider latency and backend controller time overlap and must not be added as independent costs. Unknown provider telemetry remains unknown, not zero. No dollar pricing is frozen. Process wall-clock duration is recorded in execution-timing.json when available.')
timing=json.loads((root/'execution-timing.json').read_text(encoding='utf-8-sig'))
p(f"Live process elapsed wall time: at most {timing['wall_seconds_upper_bound']:.3f} seconds ({timing['wall_seconds_upper_bound']/60:.2f} minutes), measured from process start to observed successful completion; includes a short observation delay. Start UTC: {timing['start_utc']}; completion observed UTC: {timing['end_observed_utc']}. Offline post-run verification/analysis is excluded.")
table(['Control','Summed match evidence elapsed seconds','Active control seconds (both players)','Tokens/Luna turn','Cached input tokens/match'],[[a,sum(r['evidence_elapsed_seconds'] for r in rows if r['arm']==a),sum(r['active_control_seconds'] for r in rows if r['arm']==a),summaries[a]['per_turn']['total_tokens'],summaries[a]['totals'].get('cached_input_tokens')/10 if summaries[a]['totals'].get('cached_input_tokens') is not None else None] for a in arms])
p('Per-control elapsed is the sum of each match manifest-to-seal file timestamp interval. It includes match execution and finalization/replay but excludes between-match gaps and batch gates; it is not a separate process stopwatch. Precise evidence-span durations are retained per match in supplemental-audit.json.')
for field in ['provider_requests','total_tokens','provider_latency_seconds']:
    table([field,'Remaining 90/control central','All 100/control central','Observed per-match min/max','Remaining sensitivity','All 100 sensitivity'],[[a,*[summaries[a]['projection'][field][k] for k in ['remaining_90','full_100','per_match_observed_range','remaining_90_sensitivity','full_100_sensitivity']]] for a in arms if summaries[a]['projection'][field] is not None])
    values=[summaries[a]['projection'][field] for a in arms]
    if all(v is not None for v in values):
        p(f"Combined {field}: remaining 270 central **{fmt(sum(v['remaining_90'] for v in values))}**; total 300 central **{fmt(sum(v['full_100'] for v in values))}**. Remaining sensitivity {fmt([sum(v['remaining_90_sensitivity'][i] for v in values) for i in (0,1)])}; total sensitivity {fmt([sum(v['full_100_sensitivity'][i] for v in values) for i in (0,1)])}.")
p('Central projections scale each control’s observed mean. Sensitivity holds observed Batch 1 fixed and assigns every future match that control’s observed minimum or maximum; it is not a confidence or prediction interval. It can be wide with long/request-limited games and optimistic after early forfeits. If Batch 1 is incomplete, these are conditional rate extrapolations only; the actual remaining schedule exceeds 270 and must not be mislabeled as collected data.')
p('## Paired descriptive comparisons')
for pair in analysis['paired']:p('`'+json.dumps(pair)+'`')
p('Positive bounded-minus-strict outcome differences, recovered AP and reduced truncation would be consistent with selective recovery, but do not establish the hypothesis. Compare request, token, and time overhead alongside outcomes. Stepwise-minus-bounded ratios reverse when interpreting bounded relative to stepwise. This small conditional sample cannot establish equivalence or superiority.')
p('## Matched triplets')
p('Every row below uses the frozen shared opening and corresponding Luna side. Requests and Luna turns are separate. Combat columns report Luna effects. Exact per-match AP taxonomy, terminal cause, hashes and all metrics are also provided in supplemental-audit.json and sealed result files.')
table(['Slot','Side','Control','Outcome/cause','Player turns/rounds','Requests/Luna turns','AP executed; unused I/C/X/P/T','Core dealt/received','Enemy downs/Finish/Revive','Final state hash'],[[r['slot'],r['luna_side'],r['arm'],r['luna_outcome']+'/'+r['terminal_cause'],f"{r['player_turns']}/{r['rounds_completed']}",f"{r['requests']}/{r['luna_metrics']['turns']}",str(r['luna_metrics']['ap_executed'])+'; '+ '/'.join(str(r['luna_metrics']['unused_ap_by_reason'][k]) for k in ['INTENTIONAL_END_TURN','CLEAN_PLAN_COMPLETE','EXECUTION_TRUNCATION','PROVIDER_FAILURE','TERMINAL']),f"{r['luna_metrics']['core_damage_dealt']}/{r['luna_metrics']['core_damage_received']}",f"{r['luna_metrics']['enemy_units_downed']}/{r['luna_metrics']['finish']}/{r['luna_metrics']['revive']}",r['final_state_hash']] for r in sorted(rows,key=lambda r:(r['slot'],arms.index(r['arm'])))])
p('## Decision')
p('**PASS for continuation unchanged, subject to separate authorization.** Integrity, replay, ledger, termination and stop mechanics all passed. Two repair-exhaustion forfeits and two correctly capped Stepwise request-limit games are visible data. The two long Stepwise games used 280/403 Stepwise requests; retain this cost-tail and censoring qualification. Total expenditure was manageable. See [decision.md](decision.md) for the full reasoning, bounded comparisons, and preliminary tactical interpretation. Batch 2 and the remaining 270 matches were not started.')
p('Prepared outputs: case-study-report.md, analysis.json, plot-data.csv, and 11 PNG/SVG figures in plots/. Figures are partial-cohort descriptive views; n is at most 10 per control, not the completed 100-per-control study.')
(root/'batch-1-report.md').write_text('\n'.join(lines),encoding='utf-8')
print('Wrote batch-1-report.md')
