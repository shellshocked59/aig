"""Offline regression wrapper; preserves frozen candidate source inventories."""
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch


def denied(*args, **kwargs):
    raise AssertionError('Network forbidden in repair-contract offline validation')


socket.socket.connect=denied
socket.socket.connect_ex=denied
socket.create_connection=denied
sys.path.insert(0,str(Path('tests').resolve()))
from aig.arena import candidate_validation
from aig.arena.ai.benchmark_candidate import PROMPTS, candidate_schema

OUTPUT=Path('artifacts/arena-repair-contract-v2')
ADDITIONS={'backend/aig/arena/ai/candidate_repair.py', 'backend/aig/arena/repair_contract_comparison.py'}
original=candidate_validation.hashes
frozen=json.loads(candidate_validation.TARGET.read_text())['payload']['source_hashes']
actual=original()
if set(actual)-set(frozen)!=ADDITIONS or any(actual.get(k)!=v for k,v in frozen.items()):
    raise AssertionError('Unexpected change to frozen candidate source scope')


def historical_scope():
    # Only these two additive modules are omitted for historical regression tests.
    # This is not used by either live runner or the new experiment verification.
    return {k:v for k,v in original().items() if k not in ADDITIONS}


stream=io.StringIO()
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in (
    'test_arena_candidate_repair','test_arena_benchmark_candidate','test_arena_candidate_focused_runner'))
with patch.object(candidate_validation,'hashes',historical_scope):
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
(OUTPUT/'offline-tests.log').write_text(stream.getvalue(),encoding='utf-8')
baseline=json.loads((OUTPUT/'baseline.json').read_text())
differences=[name for name,h in baseline.items() if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest()!=h]
manifest=json.loads(Path('artifacts/arena-candidate-focused/20260914-validation-v1/manifest.json').read_text())
assert dict(PROMPTS)==manifest['prompts']
assert all(candidate_schema(step=mode=='stepwise',openai=True)==s for mode,s in manifest['schemas'].items())
report=dict(tests=result.testsRun,failures=[n.id() for n,_ in result.failures], errors=[n.id() for n,_ in result.errors],
    successful=result.wasSuccessful(), live_inference_requests=0, network='denied',
    baseline_files=len(baseline), changed_existing_files=differences,
    frozen_scope_test_exclusions=sorted(ADDITIONS), candidate_prompts_and_schemas_unchanged=True)
(OUTPUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
sys.exit(0 if result.wasSuccessful() and not differences else 1)
