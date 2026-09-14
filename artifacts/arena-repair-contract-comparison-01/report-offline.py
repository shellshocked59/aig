"""Read-only evaluation of frozen/live evidence; writes only additive report files."""
import hashlib
import json
from pathlib import Path
import socket
import statistics
from collections import Counter

def denied(*a, **k):
    raise AssertionError('No network permitted during reporting')
socket.socket.connect=denied
socket.socket.connect_ex=denied
socket.create_connection=denied

from aig.arena.repair_contract_comparison import verify, DEFAULT, read, sha, write
from aig.arena.ai.candidate_repair import OLD, NEW, compare
from aig.arena.ai.benchmark_candidate import CandidateObservation
from aig.arena.snapshots import canonical_json

p=DEFAULT
m,challenges,schedule=verify(p)
analysis=read(p/'analysis.json')
completion=read(p/'live/completion.json')
assert completion['status']=='complete' and completion['reserved_requests']==36
assert sha(p/'live/request-ledger.jsonl')==completion['ledger_sha256']
for name,h in completion['result_hashes'].items():
    assert sha(p/'live'/name)==h
rows=[read(p/'live'/name) for name in sorted(completion['result_hashes'])]
ledger=[json.loads(s) for s in (p/'live/request-ledger.jsonl').read_text().splitlines()]
assert len(rows)==len(ledger)==len(schedule)==36
assert len({r['telemetry']['request_id'] for r in rows})==36
assert len({r['telemetry']['response_id'] for r in rows})==36
assert {arm:sum(r['arm']==arm for r in rows) for arm in (OLD,NEW)}=={OLD:18,NEW:18}
for r,l,s in zip(rows,ledger,schedule):
    assert r['reservation']==l and all(r[k]==l[k]==v for k,v in s.items())
    c=next(c for c in challenges if c['id']==r['challenge'])
    assert r['observation_hash']==c['observation_hash']
    assert r['rejected_output_sha256']==c['evidence']['rejected_output_sha256']
    reproduced=compare(c['evidence'],canonical_json(r['parsed_output']),
        CandidateObservation(canonical_json(c['observation'])),step=c['step'])
    assert all(r[k]==v for k,v in reproduced.items())

baseline=read('artifacts/arena-repair-contract-v2/baseline.json')
changed=[n for n,h in baseline.items() if not Path(n).is_file() or sha(n)!=h]
assert not changed
resources={}
for arm in (OLD,NEW):
    rr=[r for r in rows if r['arm']==arm]
    resources[arm]=dict(requests=len(rr),
        **{k:sum(r['telemetry']['metrics'][k] for r in rr) for k in
           ('input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens')},
        mean_latency=statistics.mean(r['latency_seconds'] for r in rr),
        median_latency=statistics.median(r['latency_seconds'] for r in rr),
        total_latency=sum(r['latency_seconds'] for r in rr),
        mean_action_count_delta=statistics.mean(r['action_count_delta'] for r in rr),
        mean_ap_plan_delta=statistics.mean(r['ap_plan_delta'] for r in rr))
pair_counts=Counter()
for pair in analysis['pairs']:
    old,new=(pair['outcomes'][a]['valid'] for a in (OLD,NEW))
    pair_counts['both_valid' if old and new else 'new_only_valid' if new else 'old_only_valid' if old else 'both_invalid']+=1
escapes=[]
for r in rows:
    if not r['potential_endturn_escape']: continue
    c=next(c for c in challenges if c['id']==r['challenge'])
    # Witness is another observed repair for exactly this frozen episode, not an invented move.
    witness=next(x for x in rows if x['challenge']==r['challenge'] and x['valid'] and
                 x['parsed_output']['actions'] and x['parsed_output']['actions'][0]['type']=='move')
    a=witness['parsed_output']['actions'][0]
    assert a in c['observation']['legal_actions']
    original=c['evidence']['rejected_plan']['actions'][0]
    assert a['unit_id']==original['unit_id']
    units={u['id']:u for side in ('own_team','enemy_team') for u in c['observation'][side]['units']}
    actor,target=units[a['unit_id']],units[original['target_id']]
    dist=lambda x,y:max(abs(x['x']-y['x']),abs(x['y']-y['y']))
    assert dist(a['destination'],target)<dist(actor,target)
    escapes.append(dict(slot=r['slot'],pair=r['pair_id'],arm=r['arm'],witness_slot=witness['slot'],
        legal_move=a,interpretation='Same actor legal move closer to original target; coherent positioning repair, not guaranteed immediate damage.'))

extra=dict(resources=resources,paired_validity=dict(pair_counts),escape_witnesses=escapes,
    input_delta_per_request=(resources[NEW]['input_tokens']-resources[OLD]['input_tokens'])/18,
    integrity=dict(requests=36,old=18,new=18,unique_provider_request_ids=36,unique_response_ids=36,
        source_payload_schedule_and_evidence_verified=True,all_static_results_reproduced=True,
        unchanged_historical_files=len(baseline),changed_historical_files=changed,
        retries=0,fallbacks=0,additional_inference=0),
    taxonomy_caveat='OLD R2 repetitions 1/3: frozen NEW_INVALIDITY means AP category changed to range category. Range was already present in original enriched diagnostics. No genuinely new static defect was introduced in these two repairs.',
    latency_caveat='Recorded timer includes provider request and local parsing/classification; transport-only latency was not separately recorded.')
write(p/'report-data.json',extra)

def actions(r):
    result=[]
    for a in r['parsed_output']['actions']:
        if a['type']=='end_turn': result.append('E'); continue
        actor=a['unit_id']
        if a['type']=='move':
            d=a['destination']; result.append(f"M({actor},{d['x']},{d['y']})")
        else: result.append(f"{a['type']}({actor},{a['target_id']})")
    return '; '.join(result)

lines=['# Frozen Arena repair-only results', '',
    '**36/36 requests completed: OLD 18, NEW 18. NEW valid repairs 17/18 (94.4%) versus OLD 7/18 (38.9%), a 55.6 percentage-point gain.**', '',
    'All 18 pairs completed. Ten pairs changed from OLD invalid to NEW valid; none regressed from valid to invalid; seven were valid in both arms and one invalid in both. No retries, request 37, fallback, downstream planning, or match execution occurred.', '',
    'The exact authorized live command and exact prepared analysis command both completed successfully. The frozen source, challenge cohort, arm payloads, schedule, provider configuration, and validators were not modified.', '',
    '## Static repair outcomes', '',
    '| Metric | OLD | NEW |', '| --- | ---: | ---: |']
for label,key in [('Valid','valid'),('Repeated same error (frozen category)','REPEATED_SAME_ERROR'),
                  ('New invalidity (frozen category; caveat below)','NEW_INVALIDITY'),
                  ('AP-valid','ap_valid'),('First-action range-valid','range_valid'),('Reference-valid','reference_valid'),
                  ('Contains EndTurn, including invalid/suffix outputs','end_turn'),('Immediate potential EndTurn escape','potential_endturn_escape')]:
    vals=[]
    for arm in (OLD,NEW):
        a=analysis['arms'][arm]
        vals.append(a.get(key,a['categories'].get(key,0)))
    lines.append(f'| {label} | {vals[0]} | {vals[1]} |')
lines += ['', 'All AP/range/reference denominators are 18. AP rates: 83.3%/100%; range rates: 38.9%/94.4%; reference rates: 100%/100%. All responses parsed; zero malformed/schema outputs or provider failures. Range checks concern the first action only; later execution-state changes were neither simulated nor penalized. The cohort has no original bad-reference, status, or LOS failure, so it does not establish improvement on those challenge types.', '',
    '## Exact paired outcomes', '',
    'M denotes Move; E denotes EndTurn. Actor/target IDs are literal frozen IDs. Each delta is (action count, planned AP) relative to that episode’s rejected proposal; EndTurn counts as an action but costs zero. V/I denotes statically valid/invalid. Categories are the unmodified prepared classifications.', '',
    '| Pair | OLD output | OLD result | OLD delta | NEW output | NEW result | NEW delta |',
    '| --- | --- | --- | --- | --- | --- | --- |']
for cid in ('R1','R2','R3','R4','R5','R6'):
    for rep in range(1,4):
        old,new=(next(r for r in rows if r['challenge']==cid and r['repetition']==rep and r['arm']==a) for a in (OLD,NEW))
        def outcome(r): return ('V ' if r['valid'] else 'I ')+r['category']
        def delta(r): return f"({r['action_count_delta']:+d}, {r['ap_plan_delta']:+d})"
        lines.append(f"| {cid}-{rep} | {actions(old)} | {outcome(old)} | {delta(old)} | {actions(new)} | {outcome(new)} | {delta(new)} |")
lines += ['', 'Episode map: R1 DOWNED bounded replacement; R2 POSITION strict; R3 POSITION bounded initial; R4 POSITION stepwise; R5 FIREBALL bounded replacement; R6 FIREBALL stepwise.', '',
    '## Classification limits and mechanical interpretation', '',
    'The frozen classifier reports OLD 9 repeated errors and 2 new invalidities, versus NEW 1 and 0. **The two OLD NEW_INVALIDITY labels are category transitions, not newly introduced defects:** R2-1/R2-3 fix AP but retain the original out-of-range first Snipe, which the original AP rejection masked. At detailed-diagnostic level, all 11 OLD invalid repairs and the one NEW invalid repair repeat an existing range/AP defect; none demonstrates a newly introduced error class. The saved analysis is preserved unchanged.', '',
    'Intent categories: OLD 2 AMBIGUOUS, 5 ENDTURN_ESCAPE, 9 REPEATED_SAME_ERROR, 2 NEW_INVALIDITY; NEW 16 AMBIGUOUS, 1 ENDTURN_ESCAPE, 1 REPEATED_SAME_ERROR. Both arms have zero EXACT_VALIDATION_FIX, VALID_SUFFIX_TRIM, or VALID_INTENT_PRESERVED. The conservative classifier does not recognize adding a movement prerequisite as intent preservation, so the 16 AMBIGUOUS results must not be presented as 16 proven intent-preserving repairs.', '',
    'Observed structure nevertheless differs clearly: all six NEW POSITION full-plan repairs use Move(actor,4,2) followed by Snipe(actor,enemy), preserving the originally attempted first actor/target damage action and fitting 3 AP. All three NEW POSITION stepwise repairs use the same actor’s legal Move, consistent with the one-action limit. Other successful non-stop repairs move the original actor closer to the original target. These are observable structural relationships, not hidden-intent judgments or tactical-strength claims.', '',
    'OLD contains EndTurn in seven outputs: five immediate valid escapes plus two suffixes in invalid plans. NEW contains EndTurn in six outputs: one immediate escape and five valid Move/Snipe suffixes preserving an original explicit EndTurn. Suffix EndTurns were not executed in this repair-only experiment and are not escapes.', '',
    'Every flagged escape has a same-episode observed legal repair witness using the original actor and moving closer to the original target; witness slots are recorded in report-data.json. These demonstrate coherent positioning alternatives under the same cardinality/AP facts without requiring future damage. EndTurn remains valid, and the report does not infer why it was chosen.', '',
    'The remaining NEW failure is R5-3: it changes the attacking unit from mage actor to knight ally, but the Attack remains out of range (distance 2, range 1). R6-2 remains an immediate EndTurn escape in both arms. No paired validity regression occurred, but these residual failures prevent claiming the problem is solved.', '',
    '## Resources', '', '| Quantity | OLD | NEW |', '| --- | ---: | ---: |']
for k in ('requests','input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens','mean_latency','median_latency','total_latency','mean_action_count_delta','mean_ap_plan_delta'):
    a,b=resources[OLD][k],resources[NEW][k]
    fmt=lambda n: f'{n:.4f}' if isinstance(n,float) else str(n)
    lines.append(f'| {k} | {fmt(a)} | {fmt(b)} |')
lines += ['',
    'Latency values are seconds. The recorded timer includes the provider request plus local parsing/classification; transport-only latency is unavailable. Actual mean input tokens/request: OLD 2,016, NEW 2,481.667. Added input: 465.667/request (+23.10%), about 43.5 below the approximate 509.2-token preparation estimate. Total observed input was 80,958 versus the estimated 92,919; total input+output was 82,575. Cached input is a subset of input tokens, not an additional chargeable token count.', '',
    'NEW added 8,382 input tokens and 147 output tokens across its 18 requests, for 8,529 additional total tokens. Mean recorded latency rose by 0.4184 seconds (+29.97%); medians rose from 1.2900 to 1.4021 seconds. Total recorded request latency was 57.8004 seconds, versus the preparation’s 47.12-second extrapolation. No dollar price is assumed.', '',
    '## Integrity and next gate', '',
    'The ledger, 36 unique provider request IDs, 36 unique response IDs, all result seals, pair/slot/payload bindings, and all static classifications reconcile. Source and prepared artifacts verify after the run. The 16,380-file historical preservation inventory remains byte-identical. No provider/model/profile, prompt, schema, observation, game rule, control, repair wording, or default was changed. Raw output fields are sanitized semantic JSON; exact provider bytes are represented by hashes, as frozen before execution.', '',
    '**NEW clearly outperformed OLD on this frozen repair-only cohort**, primarily through improved static validity and fewer immediate EndTurn substitutions. This supports a separately authorized fresh 24-turn candidate-family validation using the new repair binding. The six repeated episodes are a small selected diagnostic cohort, not 18 independent positions or evidence of full-match tactical strength. Taxonomy limitations and the two residual NEW issues must carry forward.', '',
    'Stopped after the authorized repair comparison and offline reporting. No promotion, new focused validation, prompt tuning, Qwen request, full match, or 300-match benchmark was started.', '',
    'Evidence: [prepared analysis](analysis.json), [supplemental accounting/resources](report-data.json), [live completion seal](live/completion.json), [frozen manifest](manifest.json).']
(p/'final-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
write(p/'report-seal.json',{n:sha(p/n) for n in ('analysis.json','report-data.json','final-report.md','report-offline.py')})
print(json.dumps(extra,indent=2))
