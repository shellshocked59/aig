# Arena Phase 5 implementation and verification

Implemented locally on 2026-09-13. The controlled harness adds full matches and
fixed tactical probes without modifying gameplay, provider prompts/profiles,
heuristic behavior, observations, plans, the executor or Empire. No live Qwen or
Luna requests, tuning, GitHub operations, commits or deployments were performed.

## Files and delivered contracts

| Added file | Responsibility |
| --- | --- |
| `backend/aig/arena/benchmark.py` | CLI, schedule, strict trials, saved evidence, offline replay and Markdown report |
| `backend/aig/arena/benchmark_provider.py` | Checked typed plans/provenance, one-request preflight, sanitized numeric telemetry |
| `backend/aig/arena/benchmark_metrics.py` | AP/action/combat summaries and latency/token distributions |
| `backend/aig/arena/benchmark_versions.py` | Concrete Arena manifests, source inventory and frozen artifact integrity |
| `backend/aig/arena/benchmark_artifacts/arena-benchmark-v1.json` | Domain-qualified benchmark methodology |
| `backend/aig/arena/benchmark_artifacts/arena-probes-v1.json` | Seven exact Phase 3 snapshots and state/observation hashes |
| `backend/aig/arena/benchmark_artifacts/arena-heuristic-probes-v1.json` | Frozen heuristic probe outcomes, metrics and behavioral hashes |
| `tests/test_arena_benchmark.py` | Offline harness, failure, replay, accounting, CLI and preservation tests |
| `docs/arena-benchmarking.md` | Methodology, metrics, interpretation, artifacts and exact live commands |
| `docs/arena-phase5-verification.md` | This implementation/evidence report |

README adds concise offline commands. `pyproject.toml` packages the three JSON
artifacts. Existing uncommitted Phase 1–4 work was treated as the baseline.

The manifest records `arena-benchmark-v1`, `arena-probes-v1`, `arena-rules-v2`,
`arena-scenario-v1`, `arena-turn-prompt-v1`, `arena-turn-plan-schema-v1`, provider,
model/profile, source revision/dirty status and a backend source hash inventory.
Defaults identify `qwen-config-v1` and `luna-config-v1`; overrides receive exact
configuration values and a content-derived ID. Saved versions never use `latest`.
Empire's existing source-provenance, model-profile and JSON-writing helpers are
reused without changing their source. Arena metrics remain separate.

## Methods, provider purity and telemetry

Every match uses a fresh canonical scenario. Self-play is the initial baseline;
cross-provider matches are supported. `--side-swap` runs both Blue/Red assignments
per requested game, doubling the game count. The bound defaults to 100 completed
global rounds, consistent with the existing runner, with at most two player turns
per round. Victory stops immediately; a bound produces `turn_limit` with no winner.

Preflight makes one planning request per distinct live provider, disables repair
temporarily, validates a typed/static-valid plan and rejects fallback or provider
mismatch. Failure starts zero trials and returns nonzero CLI status. During a
trial, provider failure or contamination invalidates the trial, preserves partial
evidence and aborts the remaining schedule. The interactive fallback controller
and executor are unchanged. Execution-time truncation remains a measured outcome.

Preflight latency/token usage is separate from trial inference. Ollama's configured
keep-alive is retained. Trial requests, repairs and slow/reloaded calls remain in
the distributions; p95 uses nearest rank only at 20 or more samples. Reports
include initial-request, repair and full planning latency, token/duration metrics,
context occupancy, safe OpenAI request/response IDs and per-mode aggregates.
No raw model text, hidden reasoning, secrets or full settings objects are saved.
Cost estimation was optional and is not included.

Per-side metrics include AP available/planned/executed/unused, all-five/zero-action
turns, accepted plans, static-invalid initial outputs, repairs, provider failure,
fallback, truncation/index, all eight actions, combat/healing/revive/finish/Core
counters, Fireball friendly targets, POWER/SIEGE/WARD actions, turn-start premium
occupancy and final Core/unit HP/status counts. Definitions and aggregation
denominators are in [Arena benchmarking](arena-benchmarking.md).

Observations are regenerated through authoritative Arena queries and checked by
canonical roundtrip. Frozen probes present identical starting observations and
execute on isolated copies. Objective flags exist for immediate victory and
the revive fixture; other probes retain raw consequences without a correctness
label or model judge.

## Evidence and deterministic replay

Evidence is under `.local/arena-phase5-verification/`. The final benchmark is
`heuristic-baseline/summary.json` and `heuristic-baseline/report.md`. Each trial
has manifests, initial/final snapshots, separate observation/plan/command/inference
JSONL, position facts, result metrics and `verification.json`.

All **32 baseline trials** are valid: four complete Heuristic/Heuristic matches
and four repeats of each of seven probes. Each trial was replayed from saved
commands, checking every result/counter/hash, final snapshot and winner. An
independent fresh execution of saved plans also matched observations, attempted
actions, truncation, command sequence and AP. All repeated behavioral hashes
match within their fixture. `repeatability.json` records those comparisons.

All four matches retain Red's deterministic victory after **10 player turns**,
four completed global rounds, **52 commands** and 43 gameplay actions. There
are no execution-invalid, truncated or zero-action turns. All eight action types
appear. AP is **25/25/0** available/executed/unused for Blue and **25/23/2** for
Red. Blue deals 50 damage; Red deals 48 and restores 35 HP. Final team HP is
Blue 0 / Red 33, with both Cores at 30 HP. No tuning followed these results.

| Behavioral artifact | SHA-256, identical across four matches |
| --- | --- |
| Initial state | `fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d` |
| Plan array | `5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c` |
| Command array | `88328e37527ddb68abf63b091613f7c1282a4581ebe72da394511838b3e6f0ae` |
| Final snapshot | `01720d448acca31206574e16fa3182ffc5c2a40e033e89d5043d56fb21939f2a` |
| Complete command trace | `6b7c60fbb3d8dcd8451e0692bd764135a5c1b31c5abd35dbcc1101042b6f4f5d` |
| Observation trace | `528adb2bfb33e37891a6daa239521b63afbd46620690ea0f2f2739e7cc4ab6c5` |
| Behavioral plan trace | `cf0b7588d93f8d68b4b9d93f8e5b095d989782d9f33608929c877de723aad15b` |
| Player-turn/AP trace | `7baac4be9ec87b774da8d2489abec6aa1c04ca278394a0534d2661239f62776c` |

A separate run of the untouched Phase 3 simulator also preserves its full AI
trace hash `9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1`
and all four other previously pinned hashes; see `phase3-hashes.json`.

| Probe | First action | AP executed | Recorded consequence |
| --- | --- | ---: | --- |
| Finish or Core | Finish | 5 | One Finish, 24 Core damage |
| Revive decision | Revive | 5 | Ally active; one Revive, nine restored HP across the plan |
| Fireball friendly fire | Fireball | 5 | 19 total damage including two friendly damage; one Finish |
| Shield Bash position | Shield Bash | 5 | 14 damage across the plan |
| Snipe vs basic | Snipe | 5 | 23 damage across the plan |
| Winning Core line | Attack | 1 | Nine Core damage, immediate Blue victory |
| Team elimination | Attack | 1 | Six damage, immediate Blue victory |

The frozen heuristic JSON contains the complete metrics and all hashes. Actual
ordered plans are retained in every trial's `plans.jsonl` and displayed in its
report; the table above summarizes only first actions, not entire plans.

## Preservation and limitations

| Verification | Result |
| --- | --- |
| Full Python suite | **1,052 total: 1,047 passed, five existing skips**, 145.220 seconds |
| Added benchmark coverage | **27 tests passed**, including parameterized modes/providers/fixtures |
| Frontend suite | **76 passed**, zero failures |
| Production frontend build | Passed |
| Offline benchmark baseline | **32/32 valid**, exact command and plan replay |
| Four-match / four-repeat probe hashes | Identical within each fixture |
| Legacy Arena Phase 3 hashes | All five unchanged |
| Pre-existing source/local-artifact inventory | Zero changes/removals |

Logs: `python-tests-final.log`, `frontend-test.log`, `frontend-build.log` under
`.local/arena-phase5-verification/`. Python coverage includes preserved Empire
hashes `8859a9dbe564c70105c62e9764ef6d857ea22b674049983857f0256ef3f9bb48`
and `b9f5bc4faf4b13b8aa0262170ec3f7c058dc14b33e2f2bc20758ea98adbb2302`,
Arena frozen v1 tests and Phase 2 regression traces. New model paths use fakes
with guards against real inference transports. No extra frontend test code was
needed because this slice adds no UI behavior.

The before/after inventory checked **2,383 pre-existing files**, including
**2,236 local artifacts**: zero changed or removed. This includes existing Arena
rules, states, snapshots, scenarios, observation/schema, heuristic, executor,
providers and frozen v1 code, plus Empire engine/provider/benchmark sources and
tests. README and packaging metadata were outside this source/artifact inventory
and have the intentional edits described above. Existing frontend sources were
not edited. `preservation.json` records the result.

Benchmark integrity initially exposed a Windows newline mismatch between
generated JSON bytes and normalized loader bytes. The harness hashes were
corrected to normalize CRLF/LF consistently. Probe data and gameplay were not
modified. The initial failing suite log was retained; final verification uses
the corrected code.

Known interpretation limits:

- Finish cannot newly win under immediate zero-active victory; the valid Phase 3
  elimination fixture is preserved.
- Four identical deterministic games establish repeatability, not statistical
  playing strength, generalization or a balanced first-player distribution.
- Token metrics count provider attempts; a failed authentication/transport attempt
  may never reach the service. No live latency/token baseline is claimed.
- Position measurements cover actions and turn-start occupancy, not continuous
  residence time. No slow-request filter or subjective probe score is added.
- Detailed valid plans and safe telemetry are retained; malformed raw output is
  omitted, so diagnosis uses categories and repair counts rather than raw text.
- No automatic resume after process termination, dashboard, cloud cost estimate,
  live-model validation, Docker verification or deployment is included.

## Prepared live commands

The six exact commands for Qwen/Luna preflight, four-match baselines and four-repeat
probe baselines are in [Arena benchmarking](arena-benchmarking.md#live-commands-authorization-required-before-execution).
Each baseline performs a fresh strict preflight even if a standalone preflight
was run earlier. Existing output directories must be replaced by new output
names. **Explicit authorization is required before any of those live requests.**
