"""Offline delivery checks; never invokes a provider or changes sealed evidence."""
import json
from pathlib import Path
from collections import Counter
from PIL import Image
from aig.arena.case_study_contract import verify, sha

root = Path(__file__).parent
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
contract = verify()
pre = read(root/'batch-3-preflight.json')
post = read(root/'postprocess-verification.json')
checked = read(root/'integrity.json')
assert checked == dict(success=True, completed_matches=90, replay_verified=90,
    completed_requests=1467, reserved_requests=1467, pending_requests=0)
preserved = {}
for name, files in pre['previous_roots'].items():
    previous = Path(name)
    assert {p.relative_to(previous).as_posix():sha(p) for p in previous.rglob('*') if p.is_file()} == files
    preserved[name] = len(files)
for match_id, digest in post['source_result_hashes'].items():
    assert sha(root/'matches'/match_id/'result.json') == digest
rows = [json.loads(line) for line in (root/'results.jsonl').read_text().splitlines() if line]
batch = [r for r in rows if r['batch']==3]
assert len(rows)==90 and len(batch)==30 and max(r['batch'] for r in rows)==3
assert [r['match_id'] for r in batch] == post['selected_match_ids']
ledger = read(root/'request-ledger.json')
reservations = ledger['reservations']
assert [r['id'] for r in reservations]==list(range(1,1468))
new = [r for r in reservations if r['batch']==3]
assert [r['id'] for r in new]==list(range(1031,1468))
counts = Counter(r['arm'] for r in new)
assert counts==dict(strict=89,bounded=63,stepwise=285)
assert len(new)<=1700
for arm, cap in [('strict',300),('bounded',500),('stepwise',900)]:
    assert counts[arm]<=cap
per_match = Counter(r['match_id'] for r in new)
for r in batch:
    assert per_match[r['match_id']] <= dict(strict=50,bounded=80,stepwise=140)[r['arm']]
assert all(read(root/'requests'/f"{r['id']:06d}"/'receipt.json')['status']=='returned' for r in new)
figure_lines = ['# Frozen analyzer figures — INTERIM', '',
    'Unchanged analyzer output: 11 figures per cohort, each in PNG and SVG. Batch 3 is n=10/control; cumulative Batches 1–3 is n=30/control. These are interim descriptive results, not a final control ranking.', '',
    'The win-rate figure uses Wilson 95% intervals. Heuristic results are matchup-specific. Figure 06 uses the frozen generic failure-derived AP bucket: Stepwise request-budget denial contributes 1 AP in Batch 3 and 8 AP cumulatively. The reports separate this from actual provider failure; intentional unused AP is not included as a failure. Figure 11 is the frozen scatter visualization, not a composite score.', '',
    '| Figure | Batch 3 PNG / SVG | Cumulative PNG / SVG |', '| --- | --- | --- |']
image_counts = {}
for directory in [root/'plots',root/'batch-3-analysis'/'plots']:
    pngs = sorted(directory.glob('*.png'))
    svgs = sorted(directory.glob('*.svg'))
    assert len(pngs)==len(svgs)==11
    for path in pngs:
        with Image.open(path) as img:
            assert min(img.size)>100
            img.verify()
    image_counts[directory.relative_to(root).as_posix()] = dict(png=11,svg=11)
for path in sorted((root/'plots').glob('*.png')):
    stem=path.stem
    figure_lines.append(f'| {stem} | [PNG](batch-3-analysis/plots/{stem}.png) / [SVG](batch-3-analysis/plots/{stem}.svg) | [PNG](plots/{stem}.png) / [SVG](plots/{stem}.svg) |')
figure_lines += ['', 'Frozen machine outputs: [Batch 3 analysis](batch-3-analysis/analysis.json), [cumulative analysis](analysis.json), [Batch 3 plot data](batch-3-analysis/plot-data.csv), [cumulative plot data](plot-data.csv).', '',
    'Supplemental reporting: [Batch 3](batch-3-report.md), [cumulative](cumulative-batches-1-3-report.md), [repair forensics](repair-forensics.md), [decision](decision.md).', '']
(root/'figures.md').write_text('\n'.join(figure_lines),encoding='utf-8')
result = dict(success=True,benchmark=contract['benchmark_id'] if 'benchmark_id' in contract else 'arena-case-study-benchmark-v1',
    source_contract_verification='passed',contract_sha256=contract['sha256'],
    full_prefix_integrity=checked,previous_roots_files_verified=preserved,
    batch_3_matches=30,cumulative_matches=90,batch_3_requests=len(new),cumulative_requests=1467,
    batch_3_request_ids=[1031,1467],batch_3_request_counts=dict(counts),batch_3_ceiling=1700,
    selected_results_hashes_rechecked=30,duplicate_committed_requests=0,
    later_batch_started=False,next_scope_recommendation='Batches 4–5, not executed',
    frozen_integrity_checks_cover=['replay','evidence seals','schedule','side','model/profile','no fallback'],
    figure_files_verified=image_counts,visual_spot_checks=['plots/01-win-rates.png','batch-3-analysis/plots/06-failure-ap.png'])
(root/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
files = {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
    if p.is_file() and p.name not in ('delivery-manifest.json','.lock') and 'mpl-cache' not in p.parts}
(root/'delivery-manifest.json').write_text(json.dumps(dict(success=True,files=files,excluded=['delivery-manifest.json','.lock','mpl-cache']),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(success=True,delivery_files=len(files),previous_roots_unchanged=preserved,figures=image_counts)))
