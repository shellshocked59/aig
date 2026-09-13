# Frozen Arena Phase 1

These modules preserve Phase 1 state, rules, queries, snapshots, commands and
replay. Only their internal import namespace changed from `aig.arena` to
`aig.arena.v1`. The original rule and hash assertions remain in
`tests/test_arena_v1.py`.

Use explicit imports to inspect or replay historical v1 data:

```python
from aig.arena.v1 import from_snapshot, replay
```

The default `aig.arena`, CLI and browser/API use v2. Neither loader migrates or
reinterprets the other version. Do not extend this frozen package with v2 rules.
