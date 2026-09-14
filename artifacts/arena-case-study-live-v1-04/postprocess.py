"""Invoke frozen verifier/analyzer for Batch 4 and the cumulative prefix, offline."""
import json
import shutil
from pathlib import Path
from aig.arena.case_study_contract import verify, read, sha
from aig.arena.case_study import exclusive, integrity, refresh_views
from aig.arena.case_study_analysis import analyze

root = Path(__file__).parent
contract = verify()
pre = read(root/'batch-4-preflight.json')
original = Path(pre['original_root'])
for old_root,files in pre['previous_roots'].items():
    old=Path(old_root)
    assert {p.relative_to(old).as_posix():sha(p) for p in old.rglob('*') if p.is_file()} == files
immutable = {n:h for n,h in pre['copied_prefix_files'].items() if n.startswith(('matches/','requests/','gates/')) or n in ('contract.json','schedule.json','benchmark-manifest.json')}
for name, bound in immutable.items(): assert sha(root/name)==bound, name
with exclusive(root):
    checked=integrity(root,contract)
    refresh_views(root,contract,checked)
    print(json.dumps({k:v for k,v in checked.items() if k!='results'}),flush=True)
    assert checked['pending_requests']==0
    assert all(r['batch']<=4 for r in checked['results'])
    analyze(root,checked['results'],contract)
    subset=root/'batch-4-analysis'
    subset.mkdir(exist_ok=True)
    shutil.copy2(root/'benchmark-manifest.json',subset/'benchmark-manifest.json')
    rows=[r for r in checked['results'] if r['batch']==4]
    analyze(subset,rows,contract)
    provenance=dict(contract_sha256=contract['sha256'],selection='batch == 4',
        selected_match_ids=[r['match_id'] for r in rows],
        source_result_hashes={r['match_id']:sha(root/'matches'/r['match_id']/'result.json') for r in rows},
        previous_roots_files_verified={name:len(files) for name,files in pre['previous_roots'].items()},copied_immutable_prefix_files_verified=len(immutable),
        pending_requests=checked['pending_requests'],full_prefix_replays=checked['replay_verified'],
        frozen_analyzer='aig.arena.case_study_analysis.analyze',frozen_verifier='aig.arena.case_study.integrity')
    (root/'postprocess-verification.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(standalone_batch_4=len(rows),cumulative=len(checked['results']),previous_batches_unchanged=True,success=True)),flush=True)
