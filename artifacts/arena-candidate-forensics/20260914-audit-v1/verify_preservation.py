"""Read-only hash checks; writes only new audit evidence and its report paragraph."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=read(HERE/'preservation-before.json')
changed=[name for name,value in before.items() if not Path(name).is_file() or sha(Path(name))!=value]
assert not changed,changed
frozen=Path('artifacts/arena-candidate-focused/20260914-validation-v1')
delivery=read(frozen/'delivery-integrity.json')
for name,value in delivery['derived_files_sha256'].items():assert sha(Path(name))==value,name
prior=read(frozen.parent/'preservation-before-20260914.json')
assert all(Path(n).is_file() and sha(Path(n))==v for n,v in prior.items())
historical=read(Path('docs/arena-candidate-preservation.json'))['evidence_inventory']
assert all(Path(n).is_file() and sha(Path(n))==v for n,v in historical.items())
new=[]
for root in ['backend','docs','scripts','tests','artifacts']:
    for p in Path(root).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.as_posix() not in before:
            assert HERE.resolve() in p.resolve().parents or p.as_posix()=='docs/arena-candidate-focused-forensics.md',p
            new.append(p.as_posix())
result=dict(status='verified',files_checked=len(before),changed_or_missing=changed,
    original_run_preservation_files=len(prior),delivery_hashes_verified=len(delivery['derived_files_sha256']),
    earlier_historical_evidence_inventory_verified=len(historical),
    source_and_historical_evidence_byte_identical=True,new_files=new,
    scope='backend/docs/scripts/tests/artifacts except bytecode caches, plus all existing .local/arena-luna-tactical-literacy* files. Historical .local inventory added before historical inspection; no prior audit writes there.',
    live_inference=0,extra_trials=0,runtime_changes=0)
doc=Path('docs/arena-candidate-focused-forensics.md')
text=doc.read_text(encoding='utf-8')
text=text.replace('<!-- PRESERVATION -->',
    f"Preservation verified **{len(before):,} existing files unchanged**, including current/historical source and the inspected frozen evidence. "
    f"The original live run's separate {len(prior)}-file preservation inventory and all {len(delivery['derived_files_sha256'])} delivery-integrity hashes also match. "
    "The audit baseline covers backend, docs, scripts, tests and artifacts (excluding bytecode caches), plus the existing `.local/arena-luna-tactical-literacy*` evidence trees; "
    "the historical `.local` inventory was added before inspecting those trees and no audit writes occurred there. "
    "All newly created files in the scanned source/evidence roots are confined to this report and the additive forensic directory. "
    "The user's pre-existing dirty files remain byte-identical. Details: [preservation-verification.json](../artifacts/arena-candidate-forensics/20260914-audit-v1/preservation-verification.json).")
doc.write_text(text,encoding='utf-8')
result['report_sha256']=sha(doc)
(HERE/'preservation-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert '<!--' not in text
print(json.dumps(result,indent=2))
