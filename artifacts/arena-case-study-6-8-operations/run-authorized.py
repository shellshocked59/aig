"""Execute only authorized frozen Batches 6–8, failing closed at every gate.

This wrapper changes no benchmark code. It copies sealed prefixes, invokes the
frozen CLI separately per batch, and produces supplemental offline reports.
"""
import ast,json,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from aig.arena.case_study_contract import verify,sha,digest

ops=Path(__file__).parent
template=Path('artifacts/arena-case-study-live-v1-05')
python=Path('.venv/Scripts/python.exe').resolve()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def stage(b,name):
    v=dict(batch=b,stage=name,time_utc=datetime.now(timezone.utc).isoformat(),authorized_through_batch=8)
    write(ops/'status.json',v);print(json.dumps(v),flush=True)
def call(*args):subprocess.run([str(python),'-B',*map(str,args)],check=True)
def inventory(d):return {p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()}

def prepare(b):
    stage(b,'verify and copy sealed prefix')
    c=verify();p=c['payload'];assert p['limits']['batch_requests']==1700
    old=Path(f'artifacts/arena-case-study-live-v1-{b-1:02d}');root=Path(f'artifacts/arena-case-study-live-v1-{b:02d}')
    assert not root.exists(),f'{root} already exists; no automatic retry or overwrite'
    gate=read(old/f'batch-{b-1}-gate.json');assert gate['success'] and gate['replays_verified']==(b-1)*30 and gate['pending_requests']==0
    manifest=read(old/'delivery-manifest.json');assert all(sha(old/n)==h for n,h in manifest['files'].items())
    previous={str(Path(f'artifacts/arena-case-study-live-v1-{i:02d}')):inventory(Path(f'artifacts/arena-case-study-live-v1-{i:02d}')) for i in range(1,b)}
    root.mkdir()
    for n in ('matches','requests','gates'):shutil.copytree(old/n,root/n)
    for n in ('benchmark-manifest.json','contract.json','schedule.json','match-index.json','request-ledger.json','integrity.json','results.jsonl'):shutil.copy2(old/n,root/n)
    copied=inventory(root);assert all(previous[str(old)][n]==h for n,h in copied.items())
    ledger=read(root/'request-ledger.json');assert ledger['pending_requests']==0
    schedule=p['schedule'][(b-1)*30:b*30];assert len(schedule)==30 and all(s['batch']==b for s in schedule)
    pre=dict(contract_sha256=c['sha256'],batch=b,batch_schedule_sha256=digest(schedule),schedule=schedule,
        source_manifest_sha256=digest(p['source_hashes']),limits=p['limits'],original_root=str(old),original_files=previous[str(old)],previous_roots=previous,
        continuation_root=str(root),copied_prefix_files=copied,next_match=schedule[0],next_request_id=ledger['completed_requests']+1,
        authorized_new_matches=30,authorized_through_batch=b,outer_authorization_through_batch=8,preceding_gate_sha256=sha(old/f'batch-{b-1}-gate.json'))
    write(root/f'batch-{b}-preflight.json',pre)
    s=(template/'postprocess.py').read_text(encoding='utf-8').replace('Batch 5',f'Batch {b}').replace('batch-5',f'batch-{b}').replace('batch_5',f'batch_{b}').replace("r['batch']<=5",f"r['batch']<={b}").replace("r['batch']==5",f"r['batch']=={b}").replace('batch == 5',f'batch == {b}')
    (root/'postprocess.py').write_text(s,encoding='utf-8')
    s=(template/'supplemental-audit.py').read_text(encoding='utf-8').replace('batch_5_schedule_sha256',f'batch_{b}_schedule_sha256').replace('[120:150]',f'[{(b-1)*30}:{b*30}]')
    (root/'supplemental-audit.py').write_text(s,encoding='utf-8')
    s=(template/'repair-forensics.py').read_text(encoding='utf-8').replace('(1,2,3,4,5)',str(tuple(range(1,b+1)))).replace("('1','2','3','4','5','cumulative')",repr(tuple(map(str,range(1,b+1)))+('cumulative',))).replace('Batches 1–5',f'Batches 1–{b}').replace('Every Batch 4–5 exhausted repair',f'Every Batch 6–{b} exhausted repair').replace("c['batch'] not in (4,5)",f"c['batch'] not in {tuple(range(6,b+1))}").replace("c['batch'] in (4,5)",f"c['batch'] in {tuple(range(6,b+1))}").replace('batches_4_5=',f'batches_6_{b}=')
    (root/'repair-forensics.py').write_text(s,encoding='utf-8')
    s=(template/'prepare-report.py').read_text(encoding='utf-8').replace('Batch 5 is conditional on the separate successful Batch 4 integrity gate; Batch 6 is not authorized or executed.','Batches 6–8 have separate mandatory integrity gates; no later batch starts before the preceding gate passes. Batch 9 is not authorized or executed.').replace("' / HALFWAY' if cohort_name=='cumulative' and B==5", "f' / {B*10}/100 MATCHES PER CONTROL' if cohort_name=='cumulative'")
    (root/'prepare-report.py').write_text(s,encoding='utf-8')
    s=(template/'focused-metrics.py').read_text(encoding='utf-8').replace('range(4,B+1)','range(6,B+1)')
    (root/'focused-metrics.py').write_text(s,encoding='utf-8')
    s=(template/'delivery-check.py').read_text(encoding='utf-8').replace('batch5_authorized_after_this_gate=B==4,batch6_authorized=False','next_batch_authorized_after_this_gate=B<8,batch9_authorized=False').replace("'Batch 5 may proceed under the existing authorization. This gate evaluates integrity and mechanics only; losses, repair forfeits and caps do not block continuation.' if B==4 else 'Authorized execution ends here. Batch 6 must not run.'", "f'Batch {B+1} may proceed under the existing authorization after this mechanical integrity gate.' if B<8 else 'Authorized execution ends here. Batch 9 must not run.'")
    (root/'delivery-check.py').write_text(s,encoding='utf-8')
    for f in root.glob('*.py'):ast.parse(f.read_text(encoding='utf-8'))
    call(root/'prepare-report.py')
    return root

def checkpoint(root,b):
    d=read(root/'interim-metrics.json')[f'batch_{b}'];aa=d['arms'];lines=[f'# Batch {b} mechanical continuation checkpoint — INTERIM','',
      f'All {b*30} cumulative matches passed the full frozen replay verifier. Earlier roots are preserved. The [gate](batch-{b}-gate.md) binds source/contract, request ledger, exact schedule, evidence seals, no duplicate committed requests and no fallback. Tactical outcomes do not gate continuation.','',
      '| Control | W/L/no-result | Requests | Repair forfeits |','| --- | --- | --- | --- |']
    for a,v in aa.items():lines.append(f"| {a} | {v['wins']}/{v['losses']}/{v['limits']} | {v['totals']['provider_requests']} | {v['totals']['repair_failure']} |")
    rec=aa['bounded']['recovery'];tail=aa['stepwise']['caps'];lines+=['',f"Bounded: {rec['positive']}/{rec['replans']} positive recoveries, {rec['ap_total']} AP recovered. Stepwise caps: {tail['count']}/10. Full costs, AP categories, repair diagnostics, EndTurn audit, combat and matched-slot tables remain in the reports.",'',
      f'[Standalone report](batch-{b}-report.md) · [Cumulative report](cumulative-batches-1-{b}-report.md) · [Repair forensics](repair-forensics.md) · [Focused comparisons](focused-comparisons.md) · [Figures](figures.md)','',
      f'PASS for the already authorized Batch {b+1}, subject to the recorded gate. All contracts remain unchanged.' if b<8 else 'Execution stops after Batch 8. The 80/control research interpretation and final-scope recommendation are supplied with the final delivery. Batch 9 is not authorized.','']
    (root/'decision.md').write_text('\n'.join(lines),encoding='utf-8')

start=int(sys.argv[1]) if len(sys.argv)>1 else 6
assert start in (6,7,8)
try:
    for b in range(start,9):
        root=prepare(b)
        stage(b,'live frozen CLI; stop at this batch')
        c=verify();assert c['payload']['limits']['batch_requests']==1700
        begun=datetime.now(timezone.utc)
        call('-m','aig.arena.case_study','run-live','--output',root,'--through-batch',b,'--authorize-live','arena-case-study-benchmark-v1')
        ended=datetime.now(timezone.utc)
        write(root/'execution-timing.json',dict(start_utc=begun.isoformat(),end_observed_utc=ended.isoformat(),wall_seconds_upper_bound=(ended-begun).total_seconds(),exit_code=0,scope=f'Batch {b} only',includes_prefix_verification=True,excludes_postprocessing=True))
        stage(b,'full-prefix verifier and frozen analyzer; no inference')
        call(root/'postprocess.py')
        stage(b,'offline audits and report')
        for script in ('repair-forensics.py','supplemental-audit.py','focused-metrics.py','interim-report.py'):call(root/script)
        checkpoint(root,b)
        call(root/'delivery-check.py')
        gate=read(root/f'batch-{b}-gate.json');assert gate['success'] and gate['replays_verified']==b*30 and gate['pending_requests']==0
        stage(b,'PASS: batch sealed; next authorized batch may proceed' if b<8 else 'PASS: STOP after Batch 8')
except Exception as exc:
    stage(b,'STOP: '+type(exc).__name__+': '+str(exc))
    raise
