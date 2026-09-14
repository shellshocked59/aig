"""Verify delivered Batches 6–8 form the authorized gated continuation."""
import json,re
from pathlib import Path
from aig.arena.case_study_contract import verify,sha
ops=Path(__file__).parent;root=Path('artifacts/arena-case-study-live-v1-08')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
c=verify();chain=[];last=2580
for b in (6,7,8):
    d=Path(f'artifacts/arena-case-study-live-v1-{b:02d}');old=Path(f'artifacts/arena-case-study-live-v1-{b-1:02d}')
    pre=read(d/f'batch-{b}-preflight.json');gate=read(d/f'batch-{b}-gate.json')
    assert gate['success'] and gate['replays_verified']==b*30 and gate['pending_requests']==0
    assert pre['preceding_gate_sha256']==sha(old/f'batch-{b-1}-gate.json')
    assert pre['next_request_id']==last+1==gate['new_request_ids'][0]
    assert gate['new_request_ids'][1]-gate['new_request_ids'][0]+1==gate['new_requests']<=1700
    last=gate['new_request_ids'][1]
    chain.append(dict(batch=b,gate_sha256=sha(d/f'batch-{b}-gate.json'),preceding_gate_sha256=pre['preceding_gate_sha256'],requests=gate['new_requests'],request_ids=gate['new_request_ids'],schedule_sha256=gate['schedule_sha256'],replays=gate['replays_verified']))
assert sum(x['requests'] for x in chain)==last-2580<=5100
assert read(root/'match-index.json')['next_ordinal']==241
assert not any(p.name.startswith('MATCH-081-') for p in (root/'matches').iterdir())
for n in ('decision.md','batch-8-report.md','cumulative-batches-1-8-report.md','repair-forensics.md','figures.md','extra-analysis.md','focused-comparisons.md'):
    for t in re.findall(r'\]\(([^)]+)\)',(root/n).read_text(encoding='utf-8')):
        if not t.startswith(('http:','https:','#')):assert (root/t).exists(),(n,t)
proof=dict(success=True,authorized_batches=[6,7,8],contract_sha256=c['sha256'],independent_batch_ceiling=1700,combined_authorization_ceiling=5100,
    combined_new_matches=90,new_requests=last-2580,cumulative_matches=240,cumulative_requests=last,next_ordinal=241,batch9_executed=False,
    gate_chain=chain,report_links_verified=True,operation_scripts={p.name:sha(p) for p in ops.glob('*.py')})
(root/'block-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
