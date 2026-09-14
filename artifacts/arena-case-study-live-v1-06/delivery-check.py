"""Offline integrity gate and report-delivery inventory for a frozen prefix."""
import json
from pathlib import Path
from collections import Counter
from PIL import Image
from aig.arena.case_study_contract import verify,sha,digest
root=Path(__file__).parent;B=int(root.name[-2:])
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
c=verify();pre=read(root/f'batch-{B}-preflight.json');post=read(root/'postprocess-verification.json');integ=read(root/'integrity.json')
assert integ['success'] and integ['completed_matches']==integ['replay_verified']==B*30
assert integ['pending_requests']==0 and integ['completed_requests']==integ['reserved_requests']
assert c['payload']['limits']['batch_requests']==1700
prior={}
for name,files in pre['previous_roots'].items():
    d=Path(name)
    assert {f.relative_to(d).as_posix():sha(f) for f in d.rglob('*') if f.is_file()}==files,name
    prior[name]=len(files)
rows=[json.loads(x) for x in (root/'results.jsonl').read_text().splitlines() if x]
new=[r for r in rows if r['batch']==B]
assert len(new)==30 and max(r['batch'] for r in rows)==B
assert [r['match_id'] for r in new]==[s['match_id'] for s in pre['schedule']]
ledger=read(root/'request-ledger.json');res=ledger['reservations'];newres=[r for r in res if r['batch']==B]
assert [r['id'] for r in res]==list(range(1,len(res)+1))
assert newres[0]['id']==pre['next_request_id'] and len(newres)<=1700
assert len(res)==integ['completed_requests']
counts=Counter(r['arm'] for r in newres);matchcounts=Counter(r['match_id'] for r in newres)
for a,cap in c['payload']['limits']['per_batch_control'].items():assert counts[a]<=cap
for r in new:assert matchcounts[r['match_id']]==r['requests']<=c['payload']['limits']['per_match'][r['arm']]
for mid,h in post['source_result_hashes'].items():assert sha(root/'matches'/mid/'result.json')==h
gate=read(root/'gates'/f'batch-{B:02d}.json');assert gate['success'] and gate['matches']==B*30
status=Counter(read(root/'requests'/f"{q['id']:06d}"/'receipt.json')['status'] for q in newres)
result=dict(success=True,batch=B,decision='PASS',criteria='mechanical and integrity only; tactical results do not gate continuation',
    source_contract_verified=True,contract_sha256=c['sha256'],schedule_sha256=pre['batch_schedule_sha256'],
    new_matches=30,cumulative_matches=B*30,replays_verified=integ['replay_verified'],
    new_requests=len(newres),cumulative_requests=len(res),new_request_ids=[newres[0]['id'],newres[-1]['id']],
    pending_requests=0,duplicate_committed_requests=0,no_fallback_verified_by_frozen_integrity=True,
    batch_request_ceiling=1700,request_counts=dict(counts),receipt_statuses=dict(status),
    previous_roots_unchanged=prior,frozen_gate_sha256=sha(root/'gates'/f'batch-{B:02d}.json'),
    next_batch_authorized_after_this_gate=B<8,batch9_authorized=False)
(root/f'batch-{B}-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(root/f'batch-{B}-gate.md').write_text(f'# Batch {B} integrity gate\n\n**PASS.** All {B*30} cumulative matches replayed, including the 30 new Batch {B} matches. Source/contract, exact schedule/sides, model/profile, seals, request evidence, accounting and no fallback passed the frozen verifier.\n\nNew requests: {len(newres)}/1,700; cumulative {len(res)}; zero pending or duplicate committed requests. Earlier roots are unchanged: `{json.dumps(prior)}`.\n\n'+(f'Batch {B+1} may proceed under the existing authorization after this mechanical integrity gate.' if B<8 else 'Authorized execution ends here. Batch 9 must not run.')+f'\n\n[Machine gate](batch-{B}-gate.json) · [Frozen gate](gates/batch-{B:02d}.json) · [Full replay verification](postprocess-verification.json)\n',encoding='utf-8')
lines=[f'# Frozen figures through Batch {B} — INTERIM','',f'Unchanged analyzer outputs: 11 figures in PNG/SVG for Batch {B} (n=10/control) and cumulative Batches 1–{B} (n={B*10}/control). Wilson intervals and descriptive comparisons remain interim.','',
    'The generic failure-derived AP plot includes request-budget denial. The main report separates budget-denied AP from actual provider-failure AP. Intentional and clean completion AP remain separate. These figures do not provide a composite quality score.','',
    '| Figure | Standalone PNG / SVG | Cumulative PNG / SVG |','| --- | --- | --- |']
for d in [root/'plots',root/f'batch-{B}-analysis'/'plots']:
    assert len(list(d.glob('*.png')))==len(list(d.glob('*.svg')))==11
    for f in d.glob('*.png'):
        with Image.open(f) as im:im.verify()
for f in sorted((root/'plots').glob('*.png')):
    s=f.stem;lines.append(f'| {s} | [PNG](batch-{B}-analysis/plots/{s}.png) / [SVG](batch-{B}-analysis/plots/{s}.svg) | [PNG](plots/{s}.png) / [SVG](plots/{s}.svg) |')
(root/'figures.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(root/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
files={f.relative_to(root).as_posix():sha(f) for f in sorted(root.rglob('*')) if f.is_file() and f.name not in ('delivery-manifest.json','.lock') and 'mpl-cache' not in f.parts}
(root/'delivery-manifest.json').write_text(json.dumps(dict(success=True,files=files,excluded=['delivery-manifest.json','.lock','mpl-cache']),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(success=True,batch=B,new_requests=len(newres),cumulative_requests=len(res),previous_roots_unchanged=prior,files=len(files))))
