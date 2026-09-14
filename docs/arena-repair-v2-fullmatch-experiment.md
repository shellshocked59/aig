# Arena Phase 8C: Qwen Repair V1/V2 full-match preparation

This phase is offline preparation. No live inference, connectivity check, tactical
probe, repair benchmark, or provider preflight is authorized by this document.
The two live commands below require a separate user authorization. V1 remains
the normal default; V2 must be explicitly selected. Promotion is a separate decision.

## Evidence and research question

[Phase 8B](arena-repair-v2-results.md) recorded exactly 48 repair-only requests:
V1 recovered 8/24 (33.3%), V2 20/24 (83.3%). All 28 accepted decisions executed.
V1 produced eight nonempty actions; V2 produced twelve nonempty actions and eight
EndTurns. Both arms had 24/24 schema-valid responses. Two challenge IDs represented
the same repair problem; descriptively removing the duplicate gives 40% versus
80%. Preserve the original experiment and its denominators. Repeated deterministic
outputs are not independent diverse problems.

The next question is whether V2 improves end-to-end match reliability without a
large tactical regression. Ending a turn is legal, but may abandon AP and useful
actions. Repair-only validity is insufficient evidence of tactical improvement.

Phase 7F's frozen V1 Qwen-versus-heuristic replication had three completions and
three provider failures in six intended attempts, zero Qwen wins, 82 requests
(81 match requests plus one preflight), and zero successes in three repairs.
Successful Qwen turns averaged 5.00 AP. All stopping states replayed exactly.
Historical manifests without repair provenance continue to resolve as V1; they
are never rewritten.

## Paired design and frozen contracts

Run all six V1 slots, then all six V2 slots. No randomization, self-play, Luna,
Qwen-versus-Luna, replacement matches, retries, or manual tactical intervention.

| Pair ID | Blue | Red | Attempts |
| --- | --- | --- | --- |
| pair-01 | Qwen | Heuristic | One per repair arm |
| pair-02 | Heuristic | Qwen | One per repair arm |
| pair-03 | Qwen | Heuristic | One per repair arm |
| pair-04 | Heuristic | Qwen | One per repair arm |
| pair-05 | Qwen | Heuristic | One per repair arm |
| pair-06 | Heuristic | Qwen | One per repair arm |

Each arm has three Blue and three Red Qwen attempts. Pair IDs, assignments and
initial-state hashes match across arms. All twelve start from the same frozen
scenario snapshot; pairing guarantees equivalent setup, not identical inference.
Six matches per arm support a moderate reliability experiment, not robust win-rate
statistics.

The new wrapper uses the existing `fullmatch_benchmark.run_match`; it duplicates
no battle logic and adds no controller branches. That runner already supported
`--repair-version`. Its pilot API and CLI default remain V1. The new comparison
CLI requires an explicit version for either arm.

New manifests label methodology `arena-benchmark-v2` and separately record the
historical V3 orchestration tooling. The existing V2 JSON artifact describes probe
scope, whereas the old V3 artifact describes its original eight-match pilot.
Neither artifact is changed: this document and the prepared plan explicitly
specify the six-match full-match schedule override and 100-global-round bound.
Replay now accepts both the new V2 label and historical V3 labels in full-match
mode, preserving historical verification behavior.

Every match manifest records the benchmark/spec hash, `arena-control-stepwise-v1`,
`arena-step-prompt-v1` and hash, `arena-observation-v2`,
`arena-turn-plan-schema-v1`, explicit repair version and override,
`qwen-config-v1` and complete model configuration, `arena-rules-v2`,
`arena-scenario-v1`, deterministic heuristic version, source SHA, dirty status,
source file hashes, pair ID, Qwen side, assignments, initial-state hash and bound.
Paired manifests differ **only** in `repairVersion` and its explicit
`experimentOverrides.repairVersion` entry. Output locations live outside these
contracts. No model/profile, transport, catalog, prompt, observation, repair wording,
schema, game rules, scenario, heuristic, single-repair limit or EndTurn change.

Preparation records a common source manifest, auxiliary source manifest and a hash
of the settings file, without persisting credentials. Live runs validate against
that same preparation before provider creation and before each request, including
repairs. They also check at turn and match boundaries. V2 requires V1's sealed
evidence, verifies its replay/accounting, and refuses to follow a hard stop.
Completed evidence is checked for mutation during subsequent requests.

## Metrics and evidence

`repair_fullmatch_metrics.py` derives metrics offline from saved decision and
authoritative command traces. It does not feed anything back to Qwen.
Every intended slot has a summary row; started matches retain manifests, detached
turns, decisions, commands, final snapshots, verification and `repair-metrics.json`.
Unstarted slots at a ceiling/preflight failure retain their pair IDs and reason.

Successful repaired EndTurns record global/player turn, step, AP remaining,
legal-action and non-Move legal-action counts, both teams' Core HP and complete
unit state, terminal status, resulting hash and AP abandoned. Aggregate fields:
`REPAIR_ENDTURN_COUNT`, `REPAIR_ENDTURN_AP_ABANDONED`, and
`REPAIR_ENDTURN_WITH_NONMOVE_ACTIONS_AVAILABLE`. Normal explicit EndTurns and
repaired EndTurns have separate successful-turn rates.

Successful repaired actions record type, AP cost, exact catalog membership,
authoritative execution success, resulting AP and state hash. Counts and action
distributions are separate from EndTurns.

First-response valid, statically invalid, and other request failures remain
separate, even after successful repair. Report decisions, first-invalid rate,
repairs attempted/succeeded/failed, and eventual decision reliability. Denied
requests are not attempts. Initial failure categories and repaired failure
categories remain visible. Sanitized evidence supports repeated bad reference,
new bad reference, different catalog violation, or other failure classifications;
unavailable/redacted references remain explicitly unclassifiable.

The existing Phase 8A evidence policy persists parsed schema-valid rejected
decisions, structured validation details, repair version/outcome and the accepted
repaired decision. Raw rejected text is omitted; unknown identifiers are redacted;
malformed or schema-invalid decision objects are omitted. Do not reconstruct
missing unsafe evidence. Failed repaired parsed decisions remain in the second
attempt's sanitized evidence.

Per match, report decisions before first invalid response, invalid responses,
repair counts, fatal turn/step/AP/state and decision exposure, completion status,
terminal mechanism, global/player turns, winner, both Core HP and active/downed/
removed units. Report matches with zero repairs, with repairs, and completion/
failure among those exposed to repairs. Pair outcomes and repaired-EndTurn events
must be inspected together to determine whether EndTurn recovery allowed survival.

Across **all successful Qwen turns**, including matches that later fail, report
AP available/executed/unused, mean and median executed AP, full-5, >=4 and <=2 AP
rates, and the two EndTurn rates. Failed partial turns are excluded from these
successful-turn AP rates but retained in match traces and tactical totals.
Compare unit/Core damage, Finish, Revive, Snipe, Fireball, Shield Bash, Attack,
Move and all other executed action counts. Core damage and action distributions
provide objective-pressure evidence. There is no weighted tactical score.

Report total requests, requests in completed and failed matches, total requests
per completion (including wasted attempts/preflight), completed-match-only
requests per completion, requests per controlled turn, and repairs/request ratio.
Higher total requests alone are not a regression: surviving matches can be longer.

Normal decisions and repairs have separate wall latency, prompt/eval counts,
prompt/eval/total durations and input/output/combined context occupancy distributions.
Retain per-attempt telemetry, per-turn latency and per-match latency. Missing
telemetry remains missing, not zero. Maximum combined live occupancy is reported
separately for initial and repair requests against the unchanged 4096 context.
Preflight telemetry is separate; subsequent normal latency is labeled warm by
schedule only, not a guarantee against cache eviction/reloading. Arm order, output
length and load effects can confound latency. Preserve capacity violations as
evidence; do not tune the profile.

## Request ceiling calculation

Read-only source: `.local/arena-phase7f-stepwise-reliability-20260913-01/matches.csv`
and its Qwen match traces. Completed matches used 20, 20, 20 requests; partial
matches used 7, 7, 7. Thus `3*20 + 3*7 + 1 preflight = 82`.

Use `max(20, 7) = 20`, allow a repair after every baseline decision (`*2`),
allow 20% longer play (`*1.2`), multiply by six intended matches and add the
unchanged single unrepaired preflight:

`ceil(20 * 2 * 1.2 * 6 + 1) = 289`, rounded up to **300 requests per arm**.

The maximum combined authorization is **600 requests**, including both preflights
and every repair. This is a conservative allowance relative to observed games,
not a guarantee against censoring at the 100-round bound. No finite smaller
empirical budget can guarantee all possible future trajectories complete. Record
ceiling outcomes separately; never silently raise the ceiling or retry censored
slots. A higher allowance requires new authorization and new immutable roots.

Each arm has one cumulative `RequestBudget`, called before transport. Failed
requests and repairs count; denied calls do not. A ceiling mid-turn preserves the
exact prefix without an automatic EndTurn. Ordinary failed repairs retain existing
strict stopping semantics, including the historical automatic EndTurn behavior.
Later paired slots remain independent after ordinary model failures.

## Exact commands and paths

Offline preparation (run only once with these new paths):

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_fullmatch_experiment prepare --output .local/arena-phase8c-fullmatch-plan-01 --v1-output .local/arena-phase8c-qwen-fullmatch-repair-v1-01 --v2-output .local/arena-phase8c-qwen-fullmatch-repair-v2-01 --comparison-output .local/arena-phase8c-fullmatch-comparison-01 --request-ceiling 300
```

Future authorized V1 command, first:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_fullmatch_experiment run --plan .local/arena-phase8c-fullmatch-plan-01/plan.json --repair-version arena-step-repair-v1 --request-ceiling 300 --output .local/arena-phase8c-qwen-fullmatch-repair-v1-01
```

Future authorized V2 command, only after V1 finishes without an integrity stop:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_fullmatch_experiment run --plan .local/arena-phase8c-fullmatch-plan-01/plan.json --repair-version arena-step-repair-v2 --request-ceiling 300 --output .local/arena-phase8c-qwen-fullmatch-repair-v2-01
```

Future offline verification/comparison:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_fullmatch_experiment compare --plan .local/arena-phase8c-fullmatch-plan-01/plan.json
```

Future roots must not already exist. The wrapper does not overwrite/resume them.
The common prepared source must remain unchanged between preparation and both
arms. If further source edits are needed, stop and prepare a newly reviewed plan
with new output roots. Existing Phase 7F/8B evidence is never rewritten.

## Stops and future interpretation

Hard stop on replay mismatch, catalog-valid action failing execution, wrong repair
version, wrong provider/fallback, source/profile/contract mutation, request
accounting defects or evidence corruption. The before-request guard maps mutated
runtime configuration/evidence to `source_mutation` so the frozen controller
preserves its exact prefix; offline evidence checks use more specific categories.
Preflight failure or cumulative ceiling stops that arm and preserves the reason.
No hard stop merely for failed repairs, losses, wasted repaired-EndTurn AP, weak
tactics, or unequal failure counts. Those are experimental outcomes.

The comparison must lead with completions/6, initial-invalid rates, repair rates,
fatal failures, repaired EndTurns/actions and abandoned AP. Then compare AP per
successful turn, wins/losses, tactical distributions, requests per completion,
latency and context. Inspect whether V2 merely converts fatal failures to EndTurns,
whether those matches subsequently survive, and whether tactical output degrades
materially. Totals alone cannot isolate causality from diverging match trajectories.

Promotion requires judgment across materially improved completion, fewer fatal
repairs, no engine/replay regression, safe context fit, absence of pathological
EndTurn dependence and reasonably intact tactics. No single numerical threshold
or automatic promotion is encoded. Recommend promotion, continued experiment, or
rejection only after reviewing future evidence.

## Preparation verification

Targeted tests use fake model transports with socket/HTTP/provider APIs blocked.
They exercise pairing, manifests, explicit arm selection/defaults, repaired
EndTurn/action metrics, initial-invalid retention, failed repairs, partial replay,
cumulative ceilings, independent later slots, source mutation, evidence corruption
and offline comparison. Existing repair wire-shape and preservation tests cover
both unchanged repair contracts and sanitized rejected-output behavior.

The preparation audit in `.local/arena-phase8c-preparation-01/` records before/after
file hashes, test results and historical preservation. Source changes in this
phase are limited to two replay-label compatibility checks and the new wrapper,
metrics and tests. Source is frozen only after these preparation changes finish.

The prepared plan is `.local/arena-phase8c-fullmatch-plan-01/plan.json`; future
V1/V2/comparison roots remain uncreated. Frozen provenance:

- Git SHA: `794fca9f46cbfe93d9406200c824033a59b7e812`; working tree already dirty.
- Backend source manifest: `9b576833b8de5f13a4eaaa003915d8d2e298bb97ea0b38e467411bb831fc6f4b`.
- Plan SHA-256: `1f6bbc397c9aa93b16738eb902095b98d2f5fa3eb3b97561499d737a31339a6c`.
- All twelve initial snapshots: `fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d`.

The preparation audit compared 6,996 pre-existing files. Only
`fullmatch_benchmark.py` and `stepwise_benchmark.py` changed, for replay-label
compatibility. All 6,809 pre-existing local evidence files were unchanged,
including 1,122 files under Phase 7D/7F roots and 59 Phase 8B files. All six
historical Phase 7F Qwen stopping states were independently replayed exactly.
This audit's historical count includes supporting files and is not a revision
to Phase 8B's earlier evidence inventory or findings.

Final offline regression result: **1,136 tests run, 1,131 passed, five skipped,
zero failures/errors**. The skips are Linux-only deployment tests requiring bash
and flock. This includes all 14 new Phase 8C tests and nine existing repair tests.
The initial broad-suite socket block also blocked Windows asyncio's internal
socketpair; that audit attempt was stopped. The final audit permitted only that
internal self-pipe while continuing to block external connections and DNS. No
application-source changes were needed for the test harness. Logs and structured
results are in `tests.log` and `tests.json` under the preparation audit root.

Preparation completed with **zero live inference, zero live preflights and zero
external-service calls**. Recommend authorizing the two commands above, V1 then
V2, with at most 300 requests per arm / 600 combined. Execution remains stopped
pending the user's separate authorization. Do not promote V2 automatically.
