# Arena Phase 8A: factual repair feedback and controlled experiment preparation

Implementation and offline preparation only. **No live inference is authorized by this document.** Normal gameplay remains `arena-step-repair-v1`. V2 is available only by explicit selection.

## Evidence and research question

Phase 7F completed six intended model-versus-heuristic matches per model. Qwen completed 3/6, had three provider failures, zero wins, used 82/350 requests, and repaired 0/3 invalid initial decisions. Successful Qwen turns averaged 5.00 AP. Luna completed 6/6, won four, used 132/350 requests, and repaired 2/2; successful turns averaged 4.68 AP. All twelve stopping/final states replayed exactly. There was no execution defect, fallback contamination, source mutation, or replay failure.

Phase 7E established six Phase 7D stopping pairs of `invalid_reference → invalid_reference`. The persisted evidence lacked rejected decisions and exact validator branches. These records establish failures, but cannot identify the original mistaken field or action. See the unchanged [Phase 7E report](arena-stepwise-fullmatch-failure-analysis.md) and local Phase 7F evidence under `.local/arena-phase7f-stepwise-reliability-20260913-01`.

The question is whether factual contract diagnostics improve Qwen repair recovery while preserving its initial tactical task. This phase does not tune tactics or promote V2. The model-facing independent variable is **repair feedback version**. Rejected-output persistence affects only evidence capture and is identical across arms; it is not an independent variable.

## Contracts

Repair V1 is explicitly named `arena-step-repair-v1`. Its exact text, including whitespace, is frozen in `tests/fixtures/arena-step-repair-v1.json` with SHA-256 and request shape. For `invalid_reference` it is:

```text
Previous output failed validation (invalid_reference). Stepwise control requires zero or one action. Copy one complete action from the current legal_actions catalog, or return actions=[] to end the turn. Use the same schema. No reasoning or commentary.
```

Its request remains two user messages: `ArenaObservation:\n` followed by the identical current canonical Observation V2, then this category-only feedback. The rejected decision is not echoed in V1. Ollama includes the unchanged step system prompt and application schema; OpenAI uses the same prompt as instructions and its existing wire schema conversion. No assistant message is fabricated for the injected response.

`arena-step-repair-v2` changes only the second user message. It adds a bounded safe representation of the rejected decision and the validator's structured evidence. It requires zero actions to end the turn OR exactly one complete object copied from the current `legal_actions`, without changing IDs, targets, coordinates, or fields. It requires contract-only output without reasoning or commentary. It does not recommend, rank, approximate, or select a legal action. The observation and its catalog are unchanged and authoritative.

`RepairValidationFailure` contains `category`, `action_index`, `field_path`, `message`, and `rejected_value`. Existing validator branches now attach fixed factual messages about ownership, unknown references, Core target restrictions, ability, position, AP, action count, and exact catalog membership. No traceback, exception repr, or inferred tactical explanation is exposed. A schema failure whose exact field is not deterministically known remains generic. Field paths use the actual schema's `target_id`, not an invented `target_unit_id`.

Initial acceptance and branch ordering are unchanged. Nonempty decisions still pass only when the canonical returned action equals a complete object in the current catalog. An empty plan remains legal. Offline differential verification compared the valid and invalid decisions recorded in the local validation-equivalence audit against the pre-edit parser with zero differences. `ArenaStepController` and its execution loop are unchanged.

## Safe rejected-output evidence

Both failed initial responses and failed repairs retain `rejected_decision` alongside step attempt telemetry. Each record includes the parsed safe decision when available, validation detail, repair version, and outcome (`pending`, `succeeded`, `failed`, or `not_attempted`). Initial-invalid and repaired-success metrics stay distinct.

Raw rejected content is **always omitted**, including malformed JSON, because arbitrary text cannot be guaranteed free of secrets or reasoning. `raw_content` is null. Only a fully schema-parsed decision is eligible for retention. Extra fields, client configuration, Settings reprs, headers, and prose are never copied. Identifier values are retained only if they are authoritative current unit/Core IDs (at most 128 characters) and do not contain configured secret strings. Unknown references become `[REDACTED_UNKNOWN_REFERENCE]`, including in the diagnostic; the exact unsafe value is deliberately unavailable. Contract keys/types and bounded coordinate/AP integers are allowlisted. Lists have at most five items. Input parsing is bounded at 32,768 characters and each evidence record at 8,192 UTF-8 bytes. Known-reference mismatches retain the exact safe value and relationship.

The injected fixture decisions are separately known, authored experiment inputs and are saved exactly. Redaction does not change those inputs or validator results. It changes only what is safely echoed and captured. Successful-response tracing is preserved. Rejected evidence is detached from state snapshots, command traces, and deterministic behavioral hashes.

## Frozen representative challenges

`arena-repair-challenges-v1` is separate from tactical probes. Its artifact contains six exact snapshots, full Observation V2 objects, state/observation hashes, fixed invalid decisions, exact expected diagnostics, and historical source paths/hashes. Artifact and content hashes are checked before use.

| ID | Historical source | Selection |
| --- | --- | --- |
| `qwen-early` | Phase 7F `qwen/run-001` | Turn 1 stopping state, 5 AP |
| `qwen-later` | Phase 7D `qwen-self/run-001` | Turn 2 stopping state, 1 AP |
| `luna-failure` | Phase 7D `luna-self/run-001` | Turn 3 stopping state, downed unit, 4 AP |
| `downed-revive` | Phase 7F `luna/run-001` | Turn 4 decision with a current legal Revive, 5 AP |
| `midgame` | Phase 7D `luna-vs-heuristic/run-001` | Turn 6, 4 AP |
| `low-ap` | Phase 7D `qwen-self/run-002` | Separate turn 2 stopping state, 1 AP |

“Later Qwen” means later than its turn-1 failures; the retained Qwen stopping evidence does not establish a late-midgame Qwen failure. Five states are failure boundaries; the revive challenge is a successful historical decision boundary selected for its current legal Revive option. All states were reconstructed by replaying the retained turn command prefix and comparing each available step observation and hash. The reconstruction script is `scripts/arena-freeze-repair-challenges.py`; it is offline and refuses to overwrite frozen artifacts.

Injected decisions start with an actual catalog action shape and substitute an unowned actor, missing reference, or invalid friendly Core target. Every injection deterministically fails with `invalid_reference`. **These are representative constructed mistakes, not recovered original model outputs.** The original rejected decisions are unavailable. If V1 succeeds strongly here, this challenge set may be too easy or insufficiently representative; it would not disprove the historical repair failures.

## Repair-only methodology and provenance

`arena-repair-benchmark-v1` uses the fixed state, observation, invalid decision, and expected failure. It validates the injection offline, constructs the selected repair request, makes exactly one provider repair call, validates the result with the existing parser, and executes a valid decision on detached state. EndTurn is accepted and recorded. No initial decision inference, preflight, repair-of-repair, match, or tactical probe is part of this methodology.

Adapters reuse existing Ollama transport and OpenAI Responses handling, schema conversion, configuration, error classification, and numeric telemetry. Both accept `repair_version=` when constructing a step provider. The dedicated CLI supports Ollama and OpenAI; heuristic is excluded because it has no repair inference contract. Strict provider purity is always enforced, and no fallback exists.

Each trial records provider/version/challenge, state and observation hashes, injection and expected diagnostic, request count, parse/schema/current-catalog status, repair success, chosen action or EndTurn, AP, detached execution, latency, numeric token metrics and safe request IDs when returned. Null status means the stage was not reached. Empty decisions count as valid catalog-contract responses. Summaries include challenge success, unique legal decisions, and EndTurn counts. There is no tactical-quality score or normal first-response validity metric.

Manifest provenance includes repair benchmark, challenge, and feedback versions; prompt, observation and plan schema versions; exact model profile/configuration; source files and hashes; selected challenges; trial counts; and request ceilings. New stepwise V2 probe-runner and V3 full-match manifests also record a concrete `repairVersion`. Existing manifests without that field resolve to V1; they are never rewritten. The repository already calls its full-match wrapper `arena-benchmark-v3`; neither that frozen artifact nor `arena-benchmark-v2` changes here.

The stepwise probe CLI and full-match pilot CLI now accept `--repair-version`, defaulting to V1. Explicit future V2 overrides are recorded. This does not authorize those runs. Existing full-turn gameplay is unaffected.

## Prepared Qwen A/B, awaiting authorization

Hold fixed: `qwen-config-v1`, Qwen model/settings, all six snapshots and injections, Observation V2 and catalog, `arena-turn-plan-schema-v1`, `arena-step-prompt-v1`, game rules, and stepwise semantics. Use four trials per challenge per version. Do not run Luna initially. The two commands below have **not been executed**:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_benchmark --provider ollama --repair-version arena-step-repair-v1 --challenge all --trials 4 --request-ceiling 24 --strict-provider --output .local/arena-phase8b-qwen-repair-v1-01
.venv/Scripts/python.exe -B -m aig.arena.repair_benchmark --provider ollama --repair-version arena-step-repair-v2 --challenge all --trials 4 --request-ceiling 24 --strict-provider --output .local/arena-phase8b-qwen-repair-v2-01
```

Each command permits 24 repair requests, for **48 total intended and maximum requests**. There are zero additional inference preflights and no initial inference requests. Output directories must not already exist. A static-invalid repair is a failed trial and the schedule continues; provider/transport/configuration/source/provenance/execution failures stop the run. No automatic retries or replacement trials are permitted. Source files are checked before each call and after each trial. Use the documented sandbox connectivity diagnosis only if separately authorized live execution encounters the known fast transport failure; no connectivity check was made in Phase 8A.

Compare repair successes / 24, schema validity, exact catalog-contract validity, detached execution, latency, and output tokens. Report challenge-level variation, unique repaired actions, and EndTurn choices without grading tactical quality. Preserve missing telemetry as missing. A stopped arm is incomplete; report started and unstarted counts, not a completed 24-trial result. Run order is fixed V1 then V2 and can confound transient server conditions; do not silently reorder or add trials after seeing outcomes.

Substantial improvement would support requesting a later model-versus-heuristic full-match replication, not automatic promotion. Similar poor performance suggests wording may not be the main problem. Action-ID repairs, end-turn-on-failure policies, and larger models remain unimplemented. Strong V1 performance warrants revisiting challenge representativeness.

## Stop point

Phase 8A ends after offline tests and preservation checks. **Ask for explicit authorization before the 48-request Qwen A/B.** Do not run Luna A/B, full matches, tactical probes, or inference preflights under this preparation task.

## Implementation inventory and offline verification

Added:

- `backend/aig/arena/ai/repair.py`: version selection, frozen feedback, safe evidence.
- `backend/aig/arena/repair_benchmark.py`: dedicated one-request repair harness and CLI.
- `backend/aig/arena/benchmark_artifacts/arena-repair-{benchmark,challenges}-v1.json`: frozen methodology and six fixtures.
- `scripts/arena-freeze-repair-challenges.py`: offline replay-based fixture construction.
- `tests/test_arena_repair.py`: nine dedicated offline tests, including every challenge in both arms, real adapter wire construction with fake transports, canaries, EndTurn, invalid repairs, stop behavior, and ceilings.
- `tests/fixtures/arena-step-repair-v1.json` and `arena-phase8a-preservation.json`: legacy compatibility and 82 preserved source/artifact hashes.
- This experiment document.

Changed only the needed integration points: `ai/validation.py`, `ai/provider.py`, `ai/stepwise.py`, `benchmark.py`, `benchmark_versions.py`, `stepwise_benchmark.py`, `fullmatch_benchmark.py`, `docs/arena-ai.md`, and `docs/arena-benchmarking.md`. Existing uncommitted Phase 7 edits were preserved. Neither transport adapter file needed a Phase 8A edit.

The final six-fixture parser comparison covers **1,368 decisions with zero acceptance/category differences**. The controller AST is identical to the pre-edit baseline. All **1,118 Phase 7D/7F evidence files** match their starting byte hashes. Frozen prompt, Observation V2, plan schema, Arena rules/commands, heuristic, model profiles, benchmark/probe artifacts, and Empire source checks pass. Local audit artifacts are under `.local/arena-phase8a-preparation/`: `validation-equivalence.json`, `preservation.json`, `implementation-files.json`, and `python-tests.txt`. No frontend source was touched; no frontend build was needed.

Final Python verification: **1,122 tests, 0 failures, 0 errors, 5 skipped** (1,117 passed), including all nine dedicated repair tests. The final complete run used an audit hook rejecting external socket connections and DNS requests while allowing loopback required by Windows test event loops. An earlier overstrict guard run was stopped because it also blocked those local sockets; its log is retained separately. Zero live model inference, external-service requests, tactical probes, or live full matches occurred. `git diff --check` passed; frontend/build checks were not run because no frontend files changed.
