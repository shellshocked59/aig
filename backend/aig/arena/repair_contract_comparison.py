"""Freeze, run (explicit live gate), and analyze the 36-slot repair-only screen."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
from time import perf_counter

from aig.arena.ai.benchmark_candidate import CandidateObservation, PROMPTS, candidate_schema, parse_candidate
from aig.arena.ai.candidate_repair import (OLD, NEW, CONTEXT_VERSION, PROMPT_VERSION, POLICY,
    PROMPT_HASH, CONTEXT_SCHEMA, context, repair_messages, compare, fingerprint, OpenAIRepairCandidateProvider)
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.snapshots import canonical_json

FORENSICS = Path('artifacts/arena-candidate-forensics/20260914-audit-v1/forensics.json')
DEFAULT = Path('artifacts/arena-repair-contract-comparison-01')
VERSION = 'arena-candidate-repair-comparison-v1'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, indent=2, sort_keys=True)+'\n')
        f.flush()
        os.fsync(f.fileno())


def sha(path):
    from hashlib import sha256
    return sha256(Path(path).read_bytes()).hexdigest()


def sources():
    return {p.as_posix(): sha(p) for p in sorted(Path('backend').rglob('*.py'))}


def challenges():
    forensic = read(FORENSICS)
    rows = []
    for r in forensic['repairs']:
        t = next(t for t in forensic['trials'] if t['trial']==r['trial'])
        obs = CandidateObservation(canonical_json(t['waves'][r['wave']]['observation']))
        raw = r['original']['raw_content']
        step = t['trial_binding']['control_mode']=='stepwise'
        try:
            parse_candidate(raw, obs, step=step)
        except ArenaProviderError as error:
            if error.diagnostic.to_dict()!=r['original']['reconstructed_diagnostic']:
                raise ValueError('historical rejection drift')
            evidence = context(raw, obs, error, step=step)
            payloads = {arm: dict(instructions=PROMPTS[t['trial_binding']['prompt_version']],
                input=repair_messages(obs, error, evidence, arm),
                schema=candidate_schema(step=step, openai=True)) for arm in (OLD,NEW)}
        else:
            raise ValueError('challenge must remain invalid')
        rows.append(dict(id=r['id'], trial=r['trial'], wave=r['wave'], step=step,
            provenance='authentic focused-validation first rejection', source=t['source'],
            original_request=r['original']['request'], observation=obs.to_dict(), observation_hash=obs.hash,
            raw=raw, evidence=evidence, payloads=payloads,
            payload_hashes={arm:fingerprint(p) for arm,p in payloads.items()},
            historical_repair_metrics=r['repaired']['metrics'],
            historical_repair_seconds=r['repaired']['wall_seconds']))
    if [r['id'] for r in rows] != ['R1','R2','R3','R4','R5','R6']:
        raise ValueError('unexpected forensic cohort')
    return rows


def prepare(output):
    output = Path(output)
    rows = challenges()
    configuration = read('artifacts/arena-candidate-focused/20260914-validation-v1/manifest.json')['preparation']['payload']['configuration']
    schedule = []
    # Fixed, alternating arm order, balanced across the 18 pairs.
    for rep in range(1,4):
        for i,c in enumerate(rows):
            for arm in ((OLD,NEW) if (i+rep)%2 else (NEW,OLD)):
                schedule.append(dict(slot=len(schedule)+1, pair_id=f"{c['id']}-rep{rep}",
                    challenge=c['id'], repetition=rep, arm=arm, payload_hash=c['payload_hashes'][arm]))
    estimates = {arm:[math.ceil(len(canonical_json(c['payloads'][arm]))/4) for c in rows] for arm in (OLD,NEW)}
    budget = dict(method='ceil(canonical payload characters / 4), including schema; estimate, not tokenizer measurement',
        tokens_per_request={arm:statistics.mean(v) for arm,v in estimates.items()},
        input_tokens_total=3*sum(sum(v) for v in estimates.values()),
        input_token_delta_per_request=statistics.mean(estimates[NEW])-statistics.mean(estimates[OLD]),
        output_token_ceiling=36*configuration['max_output_tokens'],
        historical_output_tokens_mean=statistics.mean(c['historical_repair_metrics']['output_tokens'] for c in rows),
        historical_seconds_mean=statistics.mean(c['historical_repair_seconds'] for c in rows))
    budget['expected_seconds']=36*budget['historical_seconds_mean']
    budget['expected_total_tokens']=budget['input_tokens_total']+36*budget['historical_output_tokens_mean']
    manifest = dict(version=VERSION, status='prepared-not-run', intended_requests=36, hard_request_ceiling=36,
        unique_challenges=6, pairs=18, repetitions=3, authentic_challenges=6, synthetic_challenges=0,
        preflight_requests=0, retries=0, fallback=False, model_profile='luna-config-v1', configuration=configuration,
        contracts=[OLD,NEW], context_version=CONTEXT_VERSION, prompt_version=PROMPT_VERSION,
        prompt_hash=PROMPT_HASH, ancestry=['generic ModelArenaTurnProvider.repair_feedback (candidate old arm)',
            'arena-step-repair-v2 (historical design precedent; distinct namespace and schema)'],
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_hashes=sources(), forensic_hash=sha(FORENSICS), challenge_hash=fingerprint(rows),
        schedule_hash=fingerprint(schedule), budget=budget,
        analysis_definitions=dict(validity='Unchanged parse_candidate; static acceptance only',
            repeated_error='same validator category; detailed first-action codes also compared',
            endturn_escape='Potential escape: immediate EndTurn replaces gameplay while current legal gameplay exists; necessity unknown',
            intent='Exact actions, suffix, or same type/actor/target proxy; otherwise AMBIGUOUS',
            range_reference_rates='First-action current range and all immutable references; unknown when unparseable',
            success='Descriptive favorable screen: more valid repairs, fewer repeated errors, no increase in potential EndTurn escapes. Otherwise inconclusive/adverse; no automatic promotion.',
            next_gate='Separately authorized fresh 8-snapshot x 3-control validation, then full-match freeze review'),
        future_paths=dict(ledger='live/request-ledger.jsonl', results='live/result-NNN.json', report='analysis.json'))
    output.mkdir(parents=True, exist_ok=False)
    write(output/'challenges.json', rows)
    write(output/'schedule.json', schedule)
    write(output/'manifest.json', manifest)
    write(output/'context-schema.json', CONTEXT_SCHEMA)
    write(output/'repair-prompt.json',dict(version=PROMPT_VERSION,text=POLICY,sha256=PROMPT_HASH))
    write(output/'seal.json', {p.name:sha(p) for p in output.glob('*.json')})
    write(output/'request-ledger-template.json', dict(status='not-started', requests=[], ceiling=36))
    audit = ['# Frozen repair payload audit', '', 'Six authentic episodes, three repetitions each. No inference performed.', '']
    for c in rows:
        audit += [f"## {c['id']} — {c['trial']} wave {c['wave']}", '',
            'OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.',
            'NEW: same instructions/observation/schema, plus shared repair instruction and the following context:', '',
            '```json', json.dumps(c['evidence'],indent=2), '```', '',
            f"Payload hashes: OLD `{c['payload_hashes'][OLD]}`; NEW `{c['payload_hashes'][NEW]}`.", '']
    audit += ['## Budget estimate', '', '```json', json.dumps(budget,indent=2), '```']
    (output/'payload-audit.md').write_text('\n'.join(audit)+'\n',encoding='utf-8')
    return manifest


def verify(output):
    output=Path(output)
    for name,expected in read(output/'seal.json').items():
        if sha(output/name)!=expected:
            raise ValueError('frozen artifact drift: '+name)
    m, rows, schedule = (read(output/n) for n in ('manifest.json','challenges.json','schedule.json'))
    if m['version']!=VERSION or m['source_hashes']!=sources() or m['forensic_hash']!=sha(FORENSICS):
        raise ValueError('source/evidence drift')
    if m['challenge_hash']!=fingerprint(rows) or m['schedule_hash']!=fingerprint(schedule):
        raise ValueError('cohort/schedule drift')
    if rows!=challenges() or len(schedule)!=36 or m['hard_request_ceiling']!=36:
        raise ValueError('payload/count mismatch')
    return m,rows,schedule


def run(output, *, live=False, provider_factory=None):
    if not live:
        raise ValueError('requires --live after separate user authorization')
    output=Path(output)
    m,rows,schedule=verify(output)
    # Settings/client construction occurs only beyond the explicit live gate.
    from aig.settings import load_settings
    settings=load_settings()
    factory=provider_factory or OpenAIRepairCandidateProvider
    providers={step:factory(settings.openai,step=step,repair=False) for step in (False,True)}
    if any(p.configuration()!=m['configuration'] for p in providers.values()):
        raise ValueError('Luna profile differs from frozen historical configuration')
    target=output/'live'
    target.mkdir(exist_ok=False)  # No resume/retry can consume additional slots.
    ledger=target/'request-ledger.jsonl'
    ledger.touch(exist_ok=False)
    write(target/'manifest.json',dict(preparation_sha256=sha(output/'manifest.json'), ceiling=36))
    completed=[]
    for slot in schedule:
        verify(output)
        c=next(c for c in rows if c['id']==slot['challenge'])
        p=providers[c['step']]
        payload=c['payloads'][slot['arm']]
        if p.system_prompt!=payload['instructions'] or p.output_schema()!=payload['schema']:
            raise ValueError('provider wire binding drift')
        if len(ledger.read_text().splitlines())!=len(completed) or len(completed)>=36:
            raise ValueError('request accounting mismatch')
        reservation=dict(slot, observation_hash=c['observation_hash'], utc=datetime.now(timezone.utc).isoformat())
        with ledger.open('a',encoding='utf-8') as f:
            f.write(canonical_json(reservation)+'\n'); f.flush(); os.fsync(f.fileno())
        record=dict(metrics={})
        started=perf_counter()
        row=dict(slot, reservation=reservation, observation_hash=c['observation_hash'],
            rejected_output_sha256=c['evidence']['rejected_output_sha256'], repair_contract=slot['arm'])
        try:
            raw=p.request(payload['input'], record)  # Exactly one transport call; no create_turn_plan.
            row.update(compare(c['evidence'],raw,CandidateObservation(canonical_json(c['observation'])),step=c['step']))
            # Existing provider redaction contract: successful contract only, rejected free text omitted.
            row['raw_output']=canonical_json(row['parsed_output']) if row['parsed_output'] is not None else None
            row['raw_output_sha256']=__import__('hashlib').sha256(raw.encode()).hexdigest()
            row['raw_output_representation']='Sanitized semantic JSON; exact provider bytes represented by hash.'
        except Exception as error:
            row.update(valid=False, category='PROVIDER_FAILURE',
                       error_category=error.category if isinstance(error,ArenaProviderError) else 'provider_exception')
        row.update(telemetry=p._safe(record), latency_seconds=perf_counter()-started)
        row=p._safe(row)
        write(target/f"result-{slot['slot']:03}.json",row)
        completed.append(row)
        if row['category']=='PROVIDER_FAILURE':
            break
    write(target/'completion.json',dict(status='complete' if len(completed)==36 else 'stopped',
        reserved_requests=len(completed), ledger_sha256=sha(ledger),
        result_hashes={p.name:sha(p) for p in target.glob('result-*.json')}))
    return dict(reserved_requests=len(completed))


def analyze(output):
    output=Path(output)
    m,ch,schedule=verify(output)
    target=output/'live'
    seal=read(target/'completion.json')
    if sha(target/'request-ledger.jsonl')!=seal['ledger_sha256']:
        raise ValueError('ledger drift')
    for name,h in seal['result_hashes'].items():
        if sha(target/name)!=h:
            raise ValueError('result drift')
    rows=[read(target/name) for name in sorted(seal['result_hashes'])]
    ledger=[json.loads(s) for s in (target/'request-ledger.jsonl').read_text().splitlines()]
    if len(rows)!=len(ledger) or len(rows)!=seal['reserved_requests']:
        raise ValueError('incomplete accounting')
    for row,entry,slot in zip(rows,ledger,schedule):
        if row['reservation']!=entry or any(row[k]!=v or entry[k]!=v for k,v in slot.items()):
            raise ValueError('result binding drift')
    summary=dict(status=seal['status'], requests=len(rows), arms={}, pairs=[])
    for arm in (OLD,NEW):
        selected=[r for r in rows if r['arm']==arm]
        summary['arms'][arm]=dict(n=len(selected), valid=sum(r['valid'] for r in selected),
            categories=dict(Counter(r['category'] for r in selected)),
            end_turn=sum(bool(r.get('end_turn')) for r in selected),
            potential_endturn_escape=sum(bool(r.get('potential_endturn_escape')) for r in selected),
            ap_valid=sum(r.get('ap_valid') is True for r in selected),
            range_valid=sum(r.get('range_valid') is True for r in selected),
            range_known=sum(r.get('range_valid') is not None for r in selected),
            reference_valid=sum(r.get('reference_valid') is True for r in selected),
            reference_known=sum(r.get('reference_valid') is not None for r in selected),
            latency_seconds=sum(r['latency_seconds'] for r in selected),
            metrics={k:sum(r['telemetry']['metrics'].get(k,0) or 0 for r in selected)
                     for k in ('input_tokens','output_tokens','total_tokens')})
        s=summary['arms'][arm]
        s['valid_rate']=s['valid']/s['n'] if s['n'] else None
        s['ap_known']=sum(r.get('ap_valid') is not None for r in selected)
        for kind in ('ap','range','reference'):
            s[kind+'_valid_rate']=s[kind+'_valid']/s[kind+'_known'] if s[kind+'_known'] else None
        s['unknown_token_metrics']=sum(any(r['telemetry']['metrics'].get(k) is None
            for k in ('input_tokens','output_tokens','total_tokens')) for r in selected)
    for pair in dict.fromkeys(s['pair_id'] for s in schedule):
        values={r['arm']:r for r in rows if r['pair_id']==pair}
        summary['pairs'].append(dict(pair_id=pair, complete=len(values)==2,
            outcomes={arm:{k:r.get(k) for k in ('valid','category','action_count_delta','ap_plan_delta','error_category')}
                      for arm,r in values.items()}))
    write(output/'analysis.json',summary)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('prepare','verify','run','analyze'))
    parser.add_argument('--output',type=Path,default=DEFAULT)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args(argv)
    if args.operation=='prepare':
        result=prepare(args.output)
    elif args.operation=='verify':
        result=dict(verified=bool(verify(args.output)), live_requests=0)
    elif args.operation=='run':
        result=run(args.output,live=args.live)
    else:
        result=analyze(args.output)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
