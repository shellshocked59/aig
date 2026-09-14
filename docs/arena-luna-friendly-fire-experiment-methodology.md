# Arena Luna friendly-fire experiment: corrected methodology

## Scope and evidence

This is offline preparation for `arena-fireball-methodology-v2`, dated 2026-09-14.
No additional OpenAI or Ollama inference occurred during this correction.

The authorized V1 pilot stopped because the experiment runner treated any
`execution.invalid_action` as a global failure. In `friendly_only`, a later ally
Attack was outside range. The unchanged executor correctly committed the first
Mage attack, rejected the ally attack, truncated the suffix, and ended the turn.
This revealed no prompt A/B result: V3 had not run, and neither pilot plan selected
Fireball. A global execution-legality stop prevented collection of independent
Fireball observations.

The original two successful requests and earlier sandbox connection failure remain
**ABORTED-METHODOLOGY PILOT EVIDENCE**, excluded from the corrected primary dataset.
Neither the historical attempt document nor its artifacts were modified. Both new
arms start at trial 1; there is no resume or reuse of pilot decisions.

## Files and version boundary

- `backend/aig/arena/friendly_fire_methodology.py`: new independent-trial runner,
  replay checks, descriptive metrics, hard stops and shared request accounting.
- `backend/aig/arena/friendly_fire_experiment.py`: adds explicit `--methodology`
  dispatch. The original V1 runner implementation remains unchanged.
- `artifacts/arena-luna-friendly-fire/methodology-v2.json`: separate reviewed
  source manifest and policy, pinned to the byte hash of the original plan.
- `tests/test_arena_fireball_methodology.py`: offline fake-provider tests.
- `tests/fixtures/arena-fireball-methodology-preservation.json`: preservation
  hashes, including pilot artifacts and the historical document.
- This document records the corrected methodology and future commands.

The original `artifacts/arena-luna-friendly-fire/plan-v1.json` is byte-unchanged,
including its original source manifest. Rather than rewriting that historical
manifest, the methodology sidecar permits only the CLI dispatch change and the
new methodology module. It hashes the entire original plan and the current source
set. Any subsequent source or artifact drift invalidates the corrected experiment.
Preparation rejects changes to other frozen sources.

Both prompts are unchanged: `arena-turn-prompt-v1` and `arena-turn-prompt-v3`.
The six fixture snapshots, Observation v1, plan schema v1, full-turn control,
Luna profile, provider settings, bounded repair, Fireball rules, gameplay, and
ArenaTurnExecutor are unchanged. No tactical score or heuristic policy was added.

## Independent trial semantics

Each of six frozen states is requested once per trial, for four trials per arm.
The order remains trial-major, fixture-interleaved: empty_blast, friendly_only,
clean_cluster, mixed_blast, bad_trade, winning_trade.

Each intended trial obtains one plan with the existing maximum of one static
repair. It then executes through the unchanged `execute_arena_turn`, saves the
result and command trace, verifies replay, and advances to the next independent
state. A truncated trial is not retried. Earlier valid actions remain committed;
there is no rollback and no execution repair.

If both provider responses fail static validation, the trial is recorded as
`provider_failed`, with the original attempt/repair diagnostics, and the batch
continues. There is no retry-until-success loop. The static-error allowlist is
malformed JSON, schema validation, AP budget, invalid reference and invalid
ability. Continuation requires two such attempts and a `repair_failed` result.
Infrastructure errors, unknown error categories, malformed envelopes, refusals,
and ambiguous failures stop conservatively instead of being treated as ordinary
static plan failures.

Provider-failed trials have no executed prefix under the current architecture:
validation completes before execution. Their empty trace is still replayed against
the unchanged starting snapshot. Complete and truncated plans replay through the
unchanged executor's final stopping state, including EndTurn when applicable.

## Planned, executed and unreached Fireballs

**Planned**: every Fireball in the returned validated plan, recording action index
and impact coordinate. It is not an execution claim.

**Executed**: a Fireball in the committed authoritative prefix. Consequences come
from the actual state immediately before execution, using the existing evaluation
helper and authoritative rules. Records include action index, impact, ACTIVE enemy
and friendly IDs, actual HP removed, downs, terminal result and immediate victory.

**Planned but unreached**: Fireballs strictly after the first execution-invalid
action. These retain index and impact but have no damage or outcome estimates.
No hypothetical state is constructed by assuming invalid actions succeeded.

A Fireball rejected at the invalid action index is separately marked
`rejected_at_execution`. A Fireball skipped after a terminal victory is separately
marked `unreached_after_terminal`. Neither is counted as executed or as a Fireball
unreached due to an earlier invalid action.

## Metrics

Per trial, record `execution_truncated`, `invalid_action_index`,
`invalid_action_type`, `invalid_reason`, `planned_ap`, `executed_ap`,
`ap_before_truncation` (AP spent in the committed prefix),
`fireballs_before_truncation`, and planned-but-unreached entries.
The full executor result retains exact attempted actions and executed commands.
First-response validity, repair attempts, failure categories, latency and token
usage are preserved separately from execution legality.

Aggregate planning metrics count plans containing Fireball and total planned
Fireballs, with per-trial action indices. Execution metrics count executed
Fireballs, planned-but-unreached Fireballs, truncations and failed-provider trials.
All started trials remain in reliability reporting; unstarted trials are explicit.

Executed Fireballs receive descriptive categories:

| Category | ACTIVE enemies | ACTIVE friendlies |
| --- | ---: | ---: |
| EMPTY | 0 | 0 |
| FRIENDLY_ONLY | 0 | At least 1 |
| ENEMY_ONLY | At least 1 | 0 |
| MIXED | At least 1 | At least 1 |

`ZERO_ENEMY` combines EMPTY and FRIENDLY_ONLY. MIXED is not automatically bad.
Aggregate facts include enemy/friendly damage and downs and Fireballs producing
immediate victory. Damage is HP removed after clamping, not nominal overkill.
There is no weighted quality score. Fireball count alone is not success, and
unreached casts must never be described as actual damage events.

## Integrity and infrastructure hard stops

Global stops remain for replay mismatch (including replay exceptions), source or
artifact drift, observation/schema/prompt/profile mismatch, wrong provider or
fallback contamination, request-accounting disagreement, authoritative-state
inconsistency, corrupted artifacts and provider infrastructure failures.

Provider and schema identities are checked before inference and at request
boundaries. Source and artifact identities are rechecked during the run. Every
executed prefix must replay exactly. Available trial evidence is saved on a stop;
exception messages are not serialized because they may contain sensitive data.
A `halted.json` marker blocks a later command from starting the other arm in that
batch. Investigating or restarting a halted batch requires review; do not delete
markers or overwrite evidence to continue.

## Request budget and output safety

The corrected dataset has **24 intended decisions per arm, 48 combined**.
At most one repair per decision permits **48 requests per arm, 96 combined**.
The prior pilot requests do not belong to this newly authorized budget/dataset.
There is no inference preflight, extra trial, full match or fallback.

Both commands MUST use the same batch output root. An exclusive lock prevents
concurrent arms. The shared checksummed ledger binds the batch to the exact plan
and methodology; reservations are written before transport, so a crash never
refunds requests. Actual attempt counts must match reservations. Corruption stops
before more requests. Each arm directory is created exclusively: rerunning the
same arm in that batch is rejected. A stale lock after a crash is a stop for
review, not a signal to bypass accounting.

The ledger enforces the combined 96 ceiling as well as each arm's 48 ceiling.
If a ceiling is reached before the schedule finishes, remaining unstarted
fixture/trial identities are saved. If all 24 trials fail both static responses,
the arm legitimately completes with 48 requests and 24 recorded failed trials.

## Offline validation and preservation

The methodology suite passes **19 tests**, covering continuation after truncation,
Fireball before/after truncation, terminal-unreached casts, no-Fireball counts,
all four consequence categories, failed repair continuation, 96 combined calls,
rejected arm reruns, exhausted-budget unstarted trials, source drift, wrong provider,
fallback, accounting corruption, replay mismatch/exception, state inconsistency,
infrastructure failure and artifact preservation. Tests block the real Responses
transport and use fake providers. The original friendly-fire suite also passes
**17 tests**. The Arena AI/executor/control regression suite passes **45 tests**:
**81 passing offline tests total** across these three suites.

Preservation checks compare the original plan, prompts, protected source files,
ArenaTurnExecutor, research artifacts, prior live output files and historical
attempt document against hashes recorded before editing. The methodology sidecar
records only the deliberate harness source differences. Existing unrelated UI
workspace changes were not edited by this task.

## Prepared commands — not executed

From `C:\code\aig`, OLD:

```powershell
.venv/Scripts/python.exe -m aig.arena.friendly_fire_experiment --live --plan artifacts/arena-luna-friendly-fire/plan-v1.json --methodology artifacts/arena-luna-friendly-fire/methodology-v2.json --prompt arena-turn-prompt-v1 --output .local/arena-luna-fireball-methodology-v2-rerun
```

TUNED, only if the old arm has no integrity/infrastructure hard stop:

```powershell
.venv/Scripts/python.exe -m aig.arena.friendly_fire_experiment --live --plan artifacts/arena-luna-friendly-fire/plan-v1.json --methodology artifacts/arena-luna-friendly-fire/methodology-v2.json --prompt arena-turn-prompt-v3 --output .local/arena-luna-fireball-methodology-v2-rerun
```

Arm outputs are separate subdirectories named by prompt version, each containing
manifest and summary JSON; accounting and the lock are shared at the batch root.
The commands require elevated network execution permissions, as diagnosed in the
prior attempt. No settings need to be changed.

**Fresh authorization is required.** The previous authorization covered the old
stop policy. These corrected commands have not been run; zero additional live
inference occurred. No V1-vs-V3 behavioral conclusion is claimed.
