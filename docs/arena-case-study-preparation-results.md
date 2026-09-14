# Arena case-study preparation results

**Complete: offline preparation only. Zero OpenAI inference, zero Ollama requests, zero Luna full matches.**

Frozen benchmark: `arena-case-study-benchmark-v1`. Contract payload SHA-256: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.
Source revision: `0999120892df07ee709c59e3f2596801cb025711` plus 140 exact source-file hashes; the pre-existing dirty tree was preserved.

## Delivered files

- `docs/arena-case-study-benchmark.md`: frozen design, decisions, metrics, statistics, budgets and commands.
- `backend/aig/arena/benchmark_artifacts/arena-case-study-benchmark-v1.json`: immutable machine contract, snapshots, slots, schedule, hashes and analysis plan.
- `backend/aig/arena/case_study_contract.py`: create-only freeze and verification.
- `backend/aig/arena/case_study.py`: full-match runner, journals, replay, resume, budgets and gates.
- `backend/aig/arena/case_study_metrics.py`: mechanical and reliability metrics.
- `backend/aig/arena/case_study_analysis.py`: paired analysis, report, CSV and matplotlib figures.
- `tests/test_arena_case_study.py`: 24 offline tests.
- `requirements-case-study.txt`: pinned report dependencies, installed into the workspace virtual environment.
- `artifacts/arena-case-study-preparation-v1/`: preservation, development evidence, definitive dry run, tests and resume proof.

All repository implementation changes are additions. No frozen AI, heuristic, game or Empire source was edited.

## Frozen identity and match design

| Binding | Version |
| --- | --- |
| Policy | `arena-policy-core-v1` |
| Full-turn prompt | `arena-turn-prompt-v6` |
| Step prompt | `arena-step-prompt-v3` |
| Observation | `arena-observation-v4` |
| Schema | `arena-turn-plan-schema-v2` |
| Repair | `arena-candidate-repair-v2` |
| Model/profile | `gpt-5.6-luna / luna-config-v1` |
| Rules/scenario | `arena-rules-v2 / arena-scenario-v1` |
| Heuristic | `arena-heuristic-v2` |

The request’s `arena-action-schema-v2` is recorded as an alias; the transmitted repository schema ID remains `arena-turn-plan-schema-v2`.
Heuristic V2 source SHA-256: `f72cfb52aac16da34f51690ba680c5936e92a448796f9a772c5c084c7bee8c48`. Its unchanged tactical-helper dependency hash is `4d521b59ba4ea15a4c1d709fa97adc200e964f65fd4e113f0175409c58f23241`.

300 means 100 Strict–Heuristic, 100 Bounded–Heuristic and 100 Stepwise–Heuristic full matches, arranged as 100 matched triplets. The heuristic is a first-class comparator within each matchup, not an additional arm or a pooled homogeneous sample.
Odd slots assign Luna Red, even slots Blue: 50/50 per arm, with Blue moving first. Slots MATCH-001–MATCH-100 use the same canonical opening; no seeds or invented scenario variants. Model responses are independent and nondeterministic in a future live study.
Initial-state hash: `fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d`. Schedule hash: `e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc`.
Ten batches of ten slots contain 30 matches each. Arm order rotates Strict/Bounded/Stepwise, Bounded/Stepwise/Strict, Stepwise/Strict/Bounded deterministically.
No new heuristic-only cohort is scheduled. The existing canonical V2/V2 reference (nine player turns, Blue Core win) supplies environment context; identical deterministic repetitions add no independent evidence.

## Policies and metrics

Provider exhaustion after permitted static repair, or a recognized transport/provider error, causes PROVIDER_FORFEIT: Luna loss and heuristic win, with the engine state and failure category preserved. No fallback or transport retry. Per-match budget denial is REQUEST_LIMIT with no winner; cumulative budget exhaustion stops the study. Heuristic exceptions, unclassified errors, replay or binding failures are hard integrity stops.
Natural outcomes are CORE_DESTRUCTION or TEAM_ELIMINATION. TURN_LIMIT occurs at 200 started player turns or 100 completed rounds without an invented winner. Limits are reported separately and count as nonwins in the complete primary binary win-rate denominator.
Gameplay inventory: wins/losses/limits and cause, side-specific rates, player turns and rounds, active control duration, Core damage dealt/received and HP remaining, active/downed/removed units, downs and finishes received/inflicted, revivals, healing, and AP available/executed/unused.
Reliability inventory: provider requests per attempted/completed turn and match; first-response validity and denominators; repairs/success/failure; provider failures separately from budget denial; initial execution invalidities; invalid action index/AP; truncations; provider latency, backend time, input/output/total/cached/reasoning tokens with null for genuinely unknown telemetry.
Heuristic inventory: the same mechanical outcomes/AP/tactics within each matchup, plus measured computation time. Model requests, tokens and provider latency are zero. Intentional EndTurn is unsupported by its plan schema; clean and terminal AP are distinguished.
Unused AP taxonomy: INTENTIONAL_END_TURN, CLEAN_PLAN_COMPLETE, EXECUTION_TRUNCATION, PROVIDER_FAILURE, TERMINAL. Budget-denied AP is identified within the controller’s generic failure bucket and excluded from provider-failure-derived AP. Recovered AP is reported separately.
Bounded inventory: replans/rate, AP at replan, recovered AP distribution, replacement repairs/first invalidity/final failure, and second execution invalidity/rate. Stepwise inventory: decisions per turn, explicit EndTurn decisions and requests per completed turn.
Tactical inventory: attacks/Core attacks, Snipe, Shield Bash, Fireball, Finish, Revive, Heal, Move, enemy/friendly damage; friendly/enemy Fireball damage; empty, friendly-only, mixed and enemy-only casts classified from pre-action ACTIVE targets. No tactical count or AP total is a quality score.

## Statistics and resource budget

Report exact counts and Wilson 95% win-rate intervals, overall and by side. For the complete cohort, exact two-sided McNemar win/nonwin contrasts compare Bounded–Strict and Stepwise–Bounded, with Holm adjustment across those two tests. Draws/limits remain nonwins, forfeits remain losses; incomplete slots do not receive imputed results. Partial cohorts are descriptive only.
Publish paired win-rate differences, cost/turn ratios, median paired match-length differences and side-stratified matched-slot bootstrap effect intervals (10,000 resamples, seed 5914). Degenerate empirical bootstrap intervals are flagged and do not establish equivalence. Tactical-only natural-victory subsets are secondary. There is no composite score, post-hoc expansion or generalization to a map population.

| Control | Requests low / central / high (100 games) | Central input / output tokens | Central total tokens | Provider hours low / central / high |
| --- | ---: | ---: | ---: | ---: |
| strict | 525.0 / 1,100.0 / 2,400.0 | 2,530,000 / 110,000 | 2,640,000 | 0.219 / 0.764 / 3.333 |
| bounded | 577.5 / 1,787.5 / 4,320.0 | 4,111,250 / 178,750 | 4,290,000 | 0.241 / 1.241 / 6.000 |
| stepwise | 1,312.5 / 3,179.0 / 9,600.0 | 7,311,700 / 317,900 | 7,629,600 | 0.547 / 2.208 / 13.333 |

Central total: 6,066.5 expected requests, 14,559,600 tokens and 4.213 provider hours; elapsed runtime adds heuristic, controller, storage and verification overhead. Low/high: 2,415/16,320 requests. These are planning ranges (5/10/20 Luna turns per game), not observations. No dollar estimate is supplied.

| Request ceiling | Strict | Bounded | Stepwise |
| --- | ---: | ---: | ---: |
| Per turn | 2 | 4 | 10 |
| Per match | 50 | 80 | 140 |
| Per batch/control | 300 | 500 | 900 |
| Per control/study | 3,000 | 5,000 | 9,000 |

Combined: 1,700 requests/batch; 15,000/study. Bounded permits at most one execution replan per turn; Stepwise at most five decisions. The high-consumption estimate exceeds the global ceiling: the runner stops rather than spending without authorization.

## Verification and dry-run results

- **300/300 final fake full matches** completed; **300/300 exact replays**; all ten batch integrity gates passed.
- **1850 fake transport requests**, 0 pending/unreconciled; **zero live inference**.
- 2,050 player turns. Fixture terminal counts: `{"CORE_DESTRUCTION": 200, "TEAM_ELIMINATION": 100}`. These are not Luna performance results.
- Deliberate interruption after MATCH-037 Bounded (110 completed arms); resumed at MATCH-037 Stepwise. Completed match seals and request files remained identical; no completed arm or request was duplicated.
- All 24 final targeted tests passed. Of 131 unmodified historical regressions, 130 passed and one old whole-tree freeze guard rejected source additions as designed. All original frozen source hashes and all non-source payload fields match. That behavioral test also passed under the independently verified historical source projection; its manifest was not rewritten.
- Preservation: **16,405/16,405 pre-existing files unchanged**, covering candidate/repair/prompt/tactical evidence, historical Stepwise/Bounded, engine, heuristic and Empire.
- The earlier three-match smoke and 110-match development fixture remain preserved in separate directories. The definitive 300-match cohort uses the final contract hash throughout.

Definitive outputs: `artifacts/arena-case-study-preparation-v1/dry-run-300-final/` contains benchmark-manifest.json, contract.json, schedule.json, results.jsonl, match-index.json, request-ledger.json, integrity.json, analysis.json, plot-data.csv, case-study-report.md, sealed matches, request journals and gates.
Eleven figures are prepared in PNG/SVG: win rates/CIs; three cost frontiers; match lengths; failure AP; stop-reason AP; bounded recovery; static repairs; side outcomes; additional truncation/AP-loss frontier. All fixture plots are labeled OFFLINE FAKE FIXTURE.

## Resume and future authorization

An exclusive OS lock prevents competing writers. Pre-send reservations are fsynced and counted before transport; turn checkpoints and sealed match hashes support exact-prefix resume. A request/response without a committed turn blocks automatic resume for manual evidence resolution; it is never automatically resent. This is fail-closed protection against duplicate billing, not a claim that remote exactly-once delivery can be proved after a crash.
Batch gates recheck requests, source/runtime and bindings, no fallback, metric recomputation, new-batch replay and prior sealed evidence. Resume/analysis replay the entire completed prefix. The CLI never advances beyond an explicitly supplied batch scope.

**Recommend first live authorization: batch 1 only, 30 matches, at most 1,700 requests.** Prior tactical validation is sufficient; this checkpoint addresses full-game expenditure and integration risk. Inspect integrity and cost without selecting on desired outcomes, then separately authorize the remaining frozen 270 games.

Future commands—not executed:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 1 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B -m aig.arena.case_study verify --output artifacts/arena-case-study-live-v1-01
.venv/Scripts/python.exe -B -m aig.arena.case_study analyze --output artifacts/arena-case-study-live-v1-01
```

Only after separate authorization for the remaining scope:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 10 --authorize-live arena-case-study-benchmark-v1
```

No known preparation blocker remains. Live execution still needs explicit authorization, working credentials and any required network permissions, with the frozen configuration/runtime verified. The historical whole-tree guard mismatch is documented expected provenance behavior. One canonical scenario, nondeterministic service conditions, possible limit censoring and potentially degenerate empirical bootstrap uncertainty restrict interpretation.

**Stopped after preparation. Candidate contracts, Luna configuration, heuristic tactics and game rules remain unchanged.**
