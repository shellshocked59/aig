# Focused candidate validation: blocked before execution

No live process started. No provider requests were sent. No full matches, Qwen runs, extra probes, or Fireball experiments occurred. Candidate freeze cannot yet be recommended from live evidence.

## Preparation evidence

The documented offline command passed:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m aig.arena.candidate_validation
.venv/Scripts/python.exe -m unittest discover -s tests -p test_arena_benchmark_candidate.py -q
```

The preparation verifier confirmed the complete manifest matches regenerated preparation, including frozen source hashes, snapshots, observations, prompts, controls, and configuration. All 27 candidate tests passed. Three additional harness tests passed, covering global/per-trial limits, denying request 87, ledger corruption, a complete fake 24-trial schedule, replay, immediate EndTurn stops, offline analysis, refusal to overwrite a run, and evidence corruption. Fake requests are not live model evidence. The harness test log is `artifacts/candidate-runner-offline.log`.

The manifest has 24 intended trials: AP-001, AP-003, AP-005, MULTI-001, DOWNED-003, POSITION-002, CORE-002, FIREBALL-003, each strict, bounded, then stepwise. Per-arm ceilings are 16, 32, and 38 requests, totaling 86. No preflight inference or transport retries are permitted.

Actual bindings:

- `arena-policy-core-v1`
- `arena-turn-prompt-v6` (2046 bytes), shared by strict and bounded
- `arena-step-prompt-v3` (2052 bytes)
- `arena-observation-v4`
- **`arena-turn-plan-schema-v2`**, consistently used by the manifest and all candidate providers; the user's expected `arena-action-schema-v2` name is not the repository ID
- `arena-control-full-turn-v2`, `arena-control-full-turn-bounded-replan-v2`, `arena-control-stepwise-v2`
- `gpt-5.6-luna`, `luna-config-v1`, reasoning effort `none`, max output 512, store false, max retries zero

The manifest binds equal first-observation hashes across each matched triplet. Live payload equivalence and model behavior remain unobserved.

## Preparation defect and additive harness

Contrary to the task's assumption, the documentation explicitly supplies no live execution CLI, output path convention, persisted request ledger implementation, or complete live analysis CLI. `candidate_validation.py` is offline-only and exposes an outcome evaluator.

Added `scripts/arena-candidate-focused.py` to execute the existing frozen schedule without modifying candidate source files or manifest. It persists a reservation and authoritative observation before each request; checks source/evidence integrity before sends; enforces the global and trial ceilings; preserves outputs and interrupted prefixes; verifies replay, bindings, accounting and stop invariants; and reuses `evaluate_candidate_trace` and `aggregate_candidate_turns` for offline analysis. OpenAI endpoint and zero retries are explicitly checked. Runtime model settings must match the manifest; they are not silently overridden.

The new tests are `tests/test_arena_candidate_focused_runner.py`. The preservation audit checked 423 inventoried files with zero changes or missing files between its before/after captures. This is the inventory available in this checkout, not a claim to have rechecked the previous task's larger historical inventories. The captures occurred after the harness and tests were added. No existing source, prompt, schema, control, default, or historical evidence file was edited during this task.

## Attempted live command — never launched

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe scripts/arena-candidate-focused.py run --live --output artifacts/arena-candidate-focused/20260914-validation-v1
```

Automatic approval review rejected this command twice, both before process creation. After the first rejection, the current request and AGENTS.md were rechecked and authorization evidence was supplied through the same escalation mechanism. The second rejection stated that the attachment did not clearly authorize sending the specific workspace-derived Arena observations to `api.openai.com`, and requires explicit authorization. No alternate execution route was attempted. The intended live output directory was absent after the first rejection; the second also rejected process creation.

Offline analysis command prepared for a completed run:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe scripts/arena-candidate-focused.py analyze --output artifacts/arena-candidate-focused/20260914-validation-v1
```

It was exercised only on fake test data, not live evidence. The live command and its analysis remain blocked/pending.

## Accounting and interpretation

| Measure | Result |
|---|---|
| Intended / completed trials | 24 / 0 |
| Accepted / failed trials | 0 / 0; all 24 unstarted |
| Total provider requests | 0 / 86 |
| Strict / bounded / stepwise requests | 0 / 0 / 0 |
| Repairs / bounded replans | 0 / 0 |
| Live token usage | 0 |
| Live latency | Not measured |
| Full-match benchmarks started | 0 |

EndTurn counts/rates/AP, clean short plans, truncations, provider failures, terminal outcomes, static validity, plan shape, matched first actions, recovery correctness, wrapper divergence, and live replay are **not measured**, rather than successful zero-event outcomes. No conclusion about coherent or excessive EndTurn use, AP compliance, tactical comparability, recovery, or candidate readiness can be drawn from this unstarted run.

Next required step: obtain direct approval to send these frozen Arena snapshots/observations to the OpenAI API at `https://api.openai.com/v1/` using the configured Luna profile, solely for the specified 24 turn trials and at most 86 total requests. After focused results are available, assess contract coherence before recommending a candidate freeze. The 300-match phase additionally needs its own matched schedule/runner freeze, failure adjudication, budget/provenance controls, and separate live authorization.
