# Arena Phase 8C: authorized Qwen Repair V1/V2 full-match comparison

**Repair V2 did not improve full-match reliability in this experiment.** Both arms
completed 3/6 matches, failed all three naturally triggered repairs, and used 82
requests. All six paired command traces are identical across arms. V2 changed the
content of the failed repair, but recovered no decision. Keep V1 as the default
and V2 experimental; this evidence does not support promotion.

## Authorization, execution and preservation

The user authorized the two prepared arms with “authorized” after reviewing the
[Phase 8C preparation](arena-repair-v2-fullmatch-experiment.md). V1 ran first, then
V2, with the frozen six-slot Blue/Red sequence and 300-request cumulative ceiling
per arm. Exactly **164 Qwen requests** were recorded: 156 normal decisions, six
repairs and two unrepaired preflights. No ceiling was reached. There were no
replacement matches, extra inference retries, tactical probes, repair-only reruns,
Luna/OpenAI calls or automatic promotion.

Before inference, the read-only Ollama version check encountered sandbox
`PermissionError [WinError 10013]`. The escalated read-only check succeeded with
HTTP 200 and Ollama `0.34.0`. Both authorized run commands consequently used the
same escalated execution permissions. These connectivity checks were not inference.

Executed commands:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_fullmatch_experiment run --plan .local/arena-phase8c-fullmatch-plan-01/plan.json --repair-version arena-step-repair-v1 --request-ceiling 300 --output .local/arena-phase8c-qwen-fullmatch-repair-v1-01
.venv/Scripts/python.exe -B -m aig.arena.repair_fullmatch_experiment run --plan .local/arena-phase8c-fullmatch-plan-01/plan.json --repair-version arena-step-repair-v2 --request-ceiling 300 --output .local/arena-phase8c-qwen-fullmatch-repair-v2-01
```

Both arms retained `arena-benchmark-v2`, the V3 orchestration tool,
`arena-control-stepwise-v1`, `arena-step-prompt-v1`, `arena-observation-v2`,
`arena-turn-plan-schema-v1`, `qwen-config-v1`, Arena rules/scenario and the
deterministic heuristic. Repair version and its explicit override are the only
paired-manifest differences. Initial-state hashes and side assignments match.

Git SHA remained `794fca9f46cbfe93d9406200c824033a59b7e812`; the previously dirty
tree was recorded. The backend source manifest remained
`9b576833b8de5f13a4eaaa003915d8d2e298bb97ea0b38e467411bb831fc6f4b` before, between
and after both arms. Settings and auxiliary source guards passed. No implementation,
prompt, repair, profile, game, heuristic or Empire changes occurred during this
live phase. All **6,809 pre-existing local evidence files** in the preparation
inventory remain unchanged. Phase 8B results were not rewritten.

All 12 stopping states passed exact replay, including partial failures. Every
accepted catalog action executed successfully: 75 per arm, 150 combined. There
were no source, provenance, fallback, accounting, catalog-execution or replay hard
stops. Offline comparison rechecked sealed inventories, manifests, detached turns,
metrics and request accounting. Preparation's 1,136-test result remains applicable;
no source changes required another regression run in this data-collection phase.

## Primary reliability and repair outcomes

| Metric | Repair V1 | Repair V2 |
| --- | ---: | ---: |
| Intended / started matches | 6 / 6 | 6 / 6 |
| Completed matches | 3/6 (50%) | 3/6 (50%) |
| Provider-failed matches | 3 | 3 |
| Turn-limit / request-ceiling outcomes | 0 / 0 | 0 / 0 |
| Normal provider decisions | 78 | 78 |
| First responses valid | 75 | 75 |
| First responses invalid | 3 (3.85%) | 3 (3.85%) |
| Other first-request failures | 0 | 0 |
| Repairs attempted / successful / failed | 3 / 0 / 3 | 3 / 0 / 3 |
| Repair success rate | 0% | 0% |
| Eventual decision reliability | 75/78 (96.15%) | 75/78 (96.15%) |
| Total invalid responses, including failed repairs | 6 | 6 |
| Successful repaired EndTurns | 0 | 0 |
| AP abandoned by repaired EndTurns | 0 | 0 |
| Repaired EndTurns with non-Move actions available | 0 | 0 |
| Successful repaired nonempty actions | 0 | 0 |

The same three matches in each arm had repair exposure and all three failed.
The other three had zero repair events and all three completed. Thus completion
among repair-exposed matches was **0/3 in both arms**. V2 neither converted fatal
failures into EndTurns nor enabled subsequent survival through a repaired action.
The tactical consequences of *successful* V2 repairs remain unobserved here.

## Paired slots, exposure and stopping states

| Pair | Qwen side | V1 result | V2 result | Requests per arm, excluding preflight | Global / player turns |
| --- | --- | --- | --- | ---: | ---: |
| pair-01 | Blue | Repair failure | Repair failure | 7 | 1 / 3 |
| pair-02 | Red | Heuristic win | Heuristic win | 20 | 5 / 11 |
| pair-03 | Blue | Repair failure | Repair failure | 7 | 1 / 3 |
| pair-04 | Red | Heuristic win | Heuristic win | 20 | 5 / 11 |
| pair-05 | Blue | Repair failure | Repair failure | 7 | 1 / 3 |
| pair-06 | Red | Heuristic win | Heuristic win | 20 | 5 / 11 |

Each failed match had five valid model decisions before the sixth, invalid
decision. Its single repair then failed. Failure occurred at global turn 1,
player-turn ordinal 3, zero-based step 0, with 5 AP remaining, 52 legal actions
and 17 non-Move legal actions. The exact pre-failure state hash was
`684fadad5cf691b6a4df2ebe049dbe65fc8fb4087253ae55d23818abc2916ed8` in all six
failed matches. Both cores had 30 HP; each team retained four active units.
The existing strict failure semantics then applied EndTurn and preserved the
stopping-state hash `f7e3611af0e32e03fc36715c06f69d0e956b2ea1e29c2063e5d3eaa3f228f340`.
That forced EndTurn is **not** a successful repaired EndTurn.

Each completed match contained five Qwen-controlled turns and 20 valid model
decisions, with no repair. All ended by team elimination: heuristic Blue retained
two active units, zero downed and two removed; Qwen Red had zero active units,
four downed and zero removed. Both cores remained at 30 HP. Qwen won zero and
lost three **completed** matches per arm; provider-failed matches are reported
separately rather than counted as tactical losses.

All six V1/V2 paired command traces are byte-identical. Each V1 trace also matches
its corresponding Phase 7F trace exactly. Repetition under the frozen temperature-0,
seed-42 profile gives very narrow exposure, not six independent diverse failures.
There is no basis for a robust win-rate or statistical superiority claim.

## What the rejected-output evidence reveals

Every initial invalid response selected:

```json
{"type":"heal","unit_id":"blue-cleric","target_id":"red-cleric"}
```

The diagnostic was `invalid_reference` at `actions[0].target_id`: the target's
ownership did not match Heal. V1 repeated that exact invalid action in all three
repairs. V2 instead selected:

```json
{"type":"heal","unit_id":"blue-cleric","target_id":"blue-cleric"}
```

That action also failed `invalid_reference`, now at `actions[0]`, because it did
not exactly match the current legal catalog. V2 changed the error from target
ownership to a different catalog violation. Both rejected decisions were parsed
and schema-valid; the problem was legality, not malformed JSON. No raw unsafe
provider text was persisted. Sanitized parsed decisions, validation fields,
repair versions and failed outcomes remain in the per-step artifacts.

This clarifies the transfer limitation in [Phase 8B](arena-repair-v2-results.md).
Its `qwen-early` challenge has the **same state and observation hash**, but injected
`red-cleric` healing `blue-knight`. That failed at `actions[0].unit_id` because the
selected actor was not owned by the active player. The actual full-match rejection
uses the correct-side actor and an enemy target, producing a different diagnostic
and therefore different V2 repair input. The repair-only improvement (8/24 versus
20/24) remains valid for its frozen inputs; it did not transfer to this observed
natural failure. The original duplicate-challenge limitation and its descriptive
40% versus 80% sensitivity result also remain unchanged.

## AP, tactical behavior and request efficiency

Both arms had 18 successful Qwen turns, including successful turns in matches that
later failed. Those turns had 90 AP available, 90 executed and zero unused;
mean/median executed AP were 5.00/5.00. Full-5 and >=4 AP rates were 100%; <=2 AP
rate was 0%. Normal explicit EndTurn and repaired EndTurn rates were both 0%.
The three failed turns additionally left 15 AP unspent per arm; these are excluded
from the requested successful-turn AP denominator, not hidden or attributed to
successful repair.

| Executed Qwen tactical fact, across all matches | V1 | V2 |
| --- | ---: | ---: |
| Unit damage, including friendly damage | 114 | 114 |
| Core damage | 0 | 0 |
| Finish | 6 | 6 |
| Revive | 9 | 9 |
| Snipe | 3 | 3 |
| Fireball | 3 | 3 |
| Shield Bash | 0 | 0 |
| Attack | 24 | 24 |
| Move | 30 | 30 |
| Heal | 0 | 0 |

There is no observed tactical difference: the authoritative trajectories are
identical. This does not show that successful V2 repairs would preserve tactics,
because none occurred. No weighted tactical score was calculated.

Per arm: 60 requests occurred in completed matches, 21 in failed matches and one
in preflight. Total requests per completion were 82/3 = **27.33**; restricting to
completed-match requests gives 20.00. Match requests per Qwen-controlled turn were
81/21 = **3.86**. Repairs represented 3/82 = **3.66%** of total requests. The 300
ceiling did not censor any slot; 218 authorized requests per arm remained unused
and were not spent on additional experiments.

## Latency and context

| Observed telemetry | V1 | V2 |
| --- | ---: | ---: |
| Normal decision wall latency, mean / median seconds | 2.372 / 2.419 | 2.206 / 2.294 |
| Repair wall latency, mean / median seconds | 1.659 / 1.658 | 1.109 / 1.075 |
| Preflight wall latency, seconds | 11.573 | 3.044 |
| Provider wall time in matches, seconds | 190.022 | 175.373 |
| Provider wall time including preflight, seconds | 201.594 | 178.417 |
| Mean provider time per controlled turn, seconds | 9.049 | 8.351 |
| Mean provider time per match, seconds | 31.670 | 29.229 |
| Normal input / output tokens, totals | 144,027 / 2,772 | 144,027 / 2,772 |
| Repair input / output tokens, totals | 6,912 / 105 | 7,404 / 102 |
| Repair input / output tokens per request | 2,304 / 35 | 2,468 / 34 |
| Maximum normal combined context occupancy | 56.98% | 56.98% |
| Maximum repair combined context occupancy | 57.10% | 61.08% |

Context occupancy is `(prompt_eval_count + eval_count) / 4096`; normal and repair
requests are separate. V2 repair input grew by 164 tokens per request, but observed
capacity remained well below the unchanged limit. Maximum normal input/output
occupancy was 56.08%/0.95% in both arms; corresponding maxima for repairs were
56.25%/0.85% in V1 and 60.25%/0.83% in V2. Separate maxima need not occur in the
same normal request. No context failure occurred and the profile was not tuned.

Ollama reported normal prompt-evaluation/evaluation/total durations of
56.710/78.647/184.293 seconds for V1 and 44.989/79.118/171.464 for V2; repair
durations were 1.517/3.217/4.953 versus 0.977/2.075/3.304 seconds. Raw numeric
duration telemetry remains in its original nanoseconds in artifacts. Per-attempt
counts, durations, occupancy distributions and per-turn latency are retained.
The latency difference is descriptive: V1 always ran first, preflight load differed,
and only three repairs were observed per arm. It is not evidence of an intrinsic
V2 speed advantage. Provider wall time excludes orchestration/replay overhead.

## Decision and artifacts

**Do not promote V2 on this evidence.** Completion and fatal repair failures did
not improve. There was no engine/replay regression, no observed tactical change
and adequate observed context headroom, but the primary reliability requirement
was not met. Keep V1 default and V2 experimental. Before considering another live
experiment, a separately specified offline study could use these now-observed
sanitized rejections as inputs to a new, explicitly versioned challenge set.
Do not overwrite the existing challenge set or infer authorization for more calls.

Evidence roots:

- [V1 summary](../.local/arena-phase8c-qwen-fullmatch-repair-v1-01/summary.json)
- [V2 summary](../.local/arena-phase8c-qwen-fullmatch-repair-v2-01/summary.json)
- [Verified comparison](../.local/arena-phase8c-fullmatch-comparison-01/comparison.json)
- [Detailed offline audit](../.local/arena-phase8c-live-audit-01/analysis.json)
- [Paired trace checks](../.local/arena-phase8c-live-audit-01/paired-traces.json)
- [Historical control replication](../.local/arena-phase8c-live-audit-01/control-replication.json)

Both arm roots retain immutable evidence inventories, explicit manifests, all six
match directories, sanitized decisions, repair metrics and exact replay checks.
The authorized A/B is complete. No further inference was performed.
