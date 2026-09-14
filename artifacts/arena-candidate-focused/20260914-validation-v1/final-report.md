# Focused candidate-family validation — 2026-09-14

**Evidence: 24/24 intended turn trials completed, 37/86 requests used, all 24 command traces replayed exactly.** Twenty trials finished without provider failure; four failed after the single permitted static repair. Two of the twenty non-provider-failure trials ended in strict execution truncation. No fallback, transport retry, integrity failure, extra probe, Qwen inference, or full match occurred.

**Recommendation: hold an unconditional candidate-family freeze.** The implementation contract is coherent, but the behavioral check is mixed. The smallest concrete concern is a premature explicit EndTurn on AP-005 bounded: 2 AP remained, the enemy had 5 HP, and the current legal catalog still allowed the ranger's 1-AP, 5-damage attack. The stop passed up an immediately available down. POSITION-002 stepwise also repaired an illegal action into immediate EndTurn with 3 AP and a frozen move/snipe opportunity. These are specific opportunity costs, not a rule that leftover AP is inherently bad or an arbitrary frequency threshold.

This recommendation is **not** based on the expected stale-state truncations, does not select a winning control, and does not justify prompt tuning after seeing these results. No prompts, controls, schema, model/profile, mechanics, defaults, or frozen manifests were changed during the run. The evidence is sufficient to review the stop behavior; no additional live work was started.

## Evidence and execution

Primary artifacts in this directory:

- `manifest.json`: original frozen preparation, schedule, exact prompts, wire schemas, runner hash, command, runtime timeout.
- `request-ledger.jsonl`: 37 persisted pre-send reservations, including repairs.
- `request-001.json` through `request-037.json`: authoritative observations, preceding inference/repair context, and command prefixes before sends.
- `<snapshot>-<control>.json`: 24 trial records with raw model outputs, parsed plans, repairs/replans, action attempts, AP/stop telemetry, commands, final states, token/latency metrics, outcome evaluation, and replay verification.
- `completion.json`: run completion and hashes of 62 primary evidence files plus the ledger hash.
- `analysis.json`: the harness's offline verification and aggregation.
- `review-data.json`: supplementary mechanical review, raw versus accepted first decisions, all 31 observation-refresh checks, plan-shape metrics, stop opportunities, and preservation findings.

The live command that actually ran, after the user's direct approval, was:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe scripts/arena-candidate-focused.py run --live --output artifacts/arena-candidate-focused/20260914-validation-v1
```

The two earlier escalation rejections never launched a process and consumed zero requests. Their report is preserved separately as `../20260914-blocked-report.md`; it describes the earlier blocked state, not the completed run.

Offline commands run afterward:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe scripts/arena-candidate-focused.py analyze --output artifacts/arena-candidate-focused/20260914-validation-v1 > artifacts/arena-candidate-focused/20260914-analysis-command.log
.venv/Scripts/python.exe -m aig.arena.candidate_validation
.venv/Scripts/python.exe scripts/arena-candidate-focused-review.py --output artifacts/arena-candidate-focused/20260914-validation-v1 > artifacts/arena-candidate-focused/20260914-review-command.log
```

The documented `candidate_validation` entry point verifies preparation only. Its printed `live_requests: 0` and `prepared-not-authorized` describe that immutable preparation operation/artifact; the completed live ledger is the authority for this run's 37 requests and the user's subsequent approval.

The original documentation intentionally had no live CLI or complete analysis command. The additive harness was prepared and tested before live execution without changing the frozen family. Its three offline tests and the existing 27 candidate tests passed before execution. Supplementary review was necessary for requested details not included in the basic aggregate; it performs no inference and reuses the authoritative observation/parser/replay functions.

## Frozen bindings and comparability

| Component | Verified binding |
|---|---|
| Model / profile | `gpt-5.6-luna` / `luna-config-v1` |
| Configuration | reasoning effort `none`, max output tokens 512, `store=false`, `max_retries=0` |
| Destination | `https://api.openai.com/v1/`, checked by the harness |
| Shared policy | `arena-policy-core-v1` |
| Strict / bounded prompt | `arena-turn-prompt-v6`, 2,046 UTF-8 bytes |
| Stepwise prompt | `arena-step-prompt-v3`, 2,052 UTF-8 bytes |
| Observation | `arena-observation-v4` |
| Semantic plan schema | **`arena-turn-plan-schema-v2`** |
| Controls | `arena-control-full-turn-v2`; `arena-control-full-turn-bounded-replan-v2`; `arena-control-stepwise-v2` |
| Rules / scenario | `arena-rules-v2` / `arena-scenario-v1` |

The repository schema ID is `arena-turn-plan-schema-v2`, not the anticipated `arena-action-schema-v2` name in the request. The actual frozen manifest, prompts, parser and all three providers agree on the former. All use the same semantic action names and fields, including exactly `{"type":"end_turn"}`. There are no action IDs, reasons, tactical explanations, or hidden extra legal-action facts in an arm.

The first observation was byte-equivalent across all three arms for every one of the eight starting states. All 31 decision observations were independently rebuilt from their authoritative command prefixes and matched the persisted observations/hashes. The OpenAI wire schemas are identical after normalizing only `actions.maxItems`: six for full-turn, one for stepwise. Strict and bounded use the exact same prompt bytes; stepwise changes the wrapper and output cardinality while retaining the exact shared policy core.

Prompt SHA-256:

- Full-turn: `39c88e2287589b943d9a9b3e9f9e9a4feaa19036a18e5f922eb7e362d27ae5c6`
- Stepwise: `95845aca75bbdb17a0cc36f91f8c13cb2288699c886fa43c87a4eb85dee6d1d5`

The configured request model/profile is proven by the provider configuration and inference manifests. No model override or heuristic substitution occurred. Response IDs and request IDs are retained; the adapter does not retain a separate response-reported model field.

## Trial and request accounting

“Accepted” below means completed without provider failure; it includes a valid accepted plan whose later action was execution-invalid. A failed trial may retain an already committed legal prefix. Failed trials were not replaced or retried as new trials.

| Measure | Strict | Bounded | Stepwise | Total |
|---|---:|---:|---:|---:|
| Intended / completed trials | 8 / 8 | 8 / 8 | 8 / 8 | 24 / 24 |
| Accepted / failed trials | 7 / 1 | 6 / 2 | 7 / 1 | 20 / 4 |
| Primary decisions | 8 | 10 | 13 | 31 |
| Provider requests | 9 | 13 | 15 | **37 / 86** |
| Arm request ceiling | 16 | 32 | 38 | 86 |
| Requests per intended turn | 1.125 | 1.625 | 1.875 | 1.542 |
| Static repairs | 1 | 3 | 2 | 6 |
| Repairs succeeded / failed | 0 / 1 | 1 / 2 | 1 / 1 | 2 / 4 |
| Bounded replans | 0 | 2 | 0 | 2 |
| Transport retries / failures | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

Repair split: strict initial 1; bounded initial 1 and replacement 2; stepwise 2. The two bounded replans account for two primary decisions, not two static repairs. Each replacement separately had its allowed repair. The maximum observed trial used three requests. All global and per-trial reservations reconcile exactly with inference attempts. Request 38 was not issued; no extra inference was used for analysis.

## Stop reasons and AP

| Final stop | Strict | Bounded | Stepwise |
|---|---:|---:|---:|
| Explicit EndTurn | 0 | 2 | 1 |
| Clean plan completion | 4 | 3 | 5 |
| Of which clean short plans with positive AP | 1 | 0 | 0 |
| Execution truncation | 2 | 0 | 0 |
| Provider failure | 1 | 2 | 1 |
| Terminal state | 1 | 1 | 1 |

Each arm began with 19 total AP across its eight snapshots. AP was partitioned once by the **final** stop reason:

| AP measure | Strict | Bounded | Stepwise |
|---|---:|---:|---:|
| Executed AP | 13 | 12 | 15 |
| Total remaining AP | 6 | 7 | 4 |
| Intentional-stop AP | 0 | 3 | 3 |
| Clean-completion AP | 1 | 0 | 0 |
| Truncation AP | 2 | 0 | 0 |
| Provider-failure AP | 3 | 4 | 1 |
| Terminal leftover AP | 0 | 0 | 0 |

Bounded still had two execution-invalidity events. One ended in provider failure and the other recovered, so neither is falsely reported as final truncation AP. The invalidity preceding provider failure remains visible.

| Explicit stop trial | Starting AP | Executed AP | AP at EndTurn | Gameplay actions before stop | Requests |
|---|---:|---:|---:|---:|---:|
| AP-003 bounded | 3 | 2 | 1 | 1 | 1 |
| AP-005 bounded | 5 | 3 | 2 | 2 | 1 |
| POSITION-002 stepwise | 3 | 0 | 3 | 0 | 2, including repair |

Explicit-stop frequency: strict 0/8 (0%); bounded 2/8 (25%); stepwise 1/8 (12.5%). Mean/median AP remaining at explicit stops: strict not applicable; bounded 1.5/1.5; stepwise 3/3. Actions before stops were bounded `[1, 2]` and stepwise `[0]`.

There was no immediate EndTurn with 5 AP. One accepted plan was one gameplay action plus EndTurn. This sample cannot establish a frequency increase against historical cohorts or an excessive-use rate.

Nevertheless, the stop opportunities deserve review:

- **AP-003 bounded:** after Snipe, a legal Attack on the same enemy and 22 moves remained. Strict and stepwise both took the additional Attack. Legal availability alone does not prove every action worthwhile, but this was not an exhausted catalog.
- **AP-005 bounded:** after Snipe + Attack, the enemy had 5 HP and both Attack and Snipe were legal, with 2 AP remaining. The ranger's ordinary 5-damage Attack costs 1 AP; the current board has no defensive bonus at that target. This was an available down left unused. Strict also stopped short, but by clean completion with 1 AP; its separate label is preserved.
- **POSITION-002 stepwise:** the first Snipe was statically illegal; the repair returned EndTurn. The stop occurred without a gameplay action. Only moves were currently legal (23), and the frozen witness is Move to `(3,2)` then Snipe to down the enemy within 3 AP. This is repair-associated immediate stopping, not proof that the wrapper initially preferred EndTurn.

## Every trial

Notation: `A` Attack, `S` Snipe, `B` Shield Bash, `F` Finish, `M` Move, `E` explicit EndTurn. Unless indicated, the acting unit is `actor` and target is `enemy`. `B(ally)` uses `ally`; `A(core)` targets `red-core`. `!` marks the execution-invalid suffix action. A rejected initial plan is described separately below; it is not an accepted plan. The stop “clean” includes AP-zero completion and is distinct from `E`.

| Snapshot / control | Accepted plan or decision sequence | Gameplay actions executed | AP spent / left | Requests | Final stop |
|---|---|---:|---:|---:|---|
| AP-001 strict | A | 1 | 1 / 0 | 1 | clean |
| AP-001 bounded | A | 1 | 1 / 0 | 1 | clean |
| AP-001 stepwise | A | 1 | 1 / 0 | 1 | clean |
| AP-003 strict | S, A | 2 | 3 / 0 | 1 | clean |
| AP-003 bounded | S, E | 1 | 2 / 1 | 1 | explicit |
| AP-003 stepwise | S; A | 2 | 3 / 0 | 2 | clean |
| AP-005 strict | S, S | 2 | 4 / 1 | 1 | clean short |
| AP-005 bounded | S, A, E | 2 | 3 / 2 | 1 | explicit |
| AP-005 stepwise | S; S; A | 3 | 5 / 0 | 3 | clean |
| MULTI-001 strict | S | 1 | 2 / 0 | 1 | clean |
| MULTI-001 bounded | S | 1 | 2 / 0 | 1 | clean |
| MULTI-001 stepwise | S | 1 | 2 / 0 | 1 | clean |
| DOWNED-003 strict | B, A! | 1 | 1 / 1 | 1 | truncation |
| DOWNED-003 bounded | B, A!; replacement failed | 1 | 1 / 1 | 3 | provider failure |
| DOWNED-003 stepwise | A; F | 2 | 2 / 0 | 2 | clean |
| POSITION-002 strict | no accepted plan | 0 | 0 / 3 | 2 | provider failure |
| POSITION-002 bounded | no accepted plan | 0 | 0 / 3 | 2 | provider failure |
| POSITION-002 stepwise | E after repair | 0 | 0 / 3 | 2 | explicit |
| CORE-002 strict | A(core) | 1 | 1 / 0 | 1 | terminal |
| CORE-002 bounded | A(core) | 1 | 1 / 0 | 1 | terminal |
| CORE-002 stepwise | A(core) | 1 | 1 / 0 | 1 | terminal |
| FIREBALL-003 strict | B(ally), A! | 1 | 1 / 1 | 1 | truncation |
| FIREBALL-003 bounded | B(ally), A!; M(ally) to (4,2) after repair | 2 | 2 / 0 | 3 | clean |
| FIREBALL-003 stepwise | B(ally); next decision failed | 1 | 1 / 1 | 3 | provider failure |

No Fireball action was selected. This is not a failure criterion. The FIREBALL snapshot records Shield Bash's authoritative push and subsequent range consequences; no Fireball tuning or extra Fireball experiment occurred.

## Bounded recovery, strictness and stepwise legality

For bounded AP-001, MULTI-001 and CORE-002, the initial one-action plans contained no EndTurn; they completed at AP zero or terminal state, with no replan. AP-003 and AP-005 contained and reached EndTurn, with positive remaining AP and no replan. POSITION-002 produced no accepted initial plan and no replan. Its raw first response and repair both included a syntactic EndTurn suffix, but neither was accepted or reached.

| Bounded recovery detail | DOWNED-003 | FIREBALL-003 |
|---|---|---|
| Initial plan | Shield Bash(actor, enemy), Attack(actor, enemy) | Shield Bash(ally, enemy), Attack(actor, enemy) |
| Initial explicit EndTurn planned / reached | no / no | no / no |
| First invalidity | second action, target outside action range | second action, target outside action range |
| Stale suffix length | 1 | 1 |
| AP at invalidity / refresh | 1 | 1 |
| Replan triggered | yes, exactly one | yes, exactly one |
| Replacement first response | Attack(actor, enemy), statically illegal | Attack(actor, enemy), statically illegal |
| Replacement repair | same illegal Attack; failed | Move(ally, (4,2)); accepted |
| Replacement explicit EndTurn | no | no |
| Second execution invalidity | no; replacement never accepted | no |
| Recovered AP | 0 | 1 |
| Final stop / requests | provider failure / 3 | clean completion / 3 |

Recovery scheduling worked correctly in both cases; tactical recovery succeeded once and failed once. Static repair is not a second replan. Failure retained the committed Shield Bash prefix without fallback or an automatic EndTurn.

Strict had exactly one observation/decision per trial, with repairs using that same observation. Both later-action range failures truncated, and strict never acquired bounded behavior.

All **11 executed stepwise gameplay actions**, plus its explicit EndTurn, were legal. The three rejected stepwise outputs were caught before execution: POSITION-002 initial out-of-range Snipe, and two out-of-range attack proposals in the second FIREBALL-003 decision. Their traces are preserved. Stepwise used a fresh verified observation for every subsequent decision. Its EndTurn was the repaired response on POSITION-002; **zero provider requests followed it**. CORE-002 stopped on victory, also without another request.

Coverage limits: no strict trial reached explicit EndTurn; no bounded trial had clean completion with *positive* AP; no live terminal trial had positive leftover AP or a planned suffix after victory. Those branches retain source/offline-test coverage, but this run did not independently exercise them. No second bounded execution invalidity occurred.

## AP compliance and repairs

| Measure, per decision unless noted | Strict | Bounded | Stepwise |
|---|---:|---:|---:|
| First-response static validity, all decisions | 7/8 (87.5%) | 7/10 (70.0%) | 11/13 (84.6%) |
| Initial-turn first-response validity | 7/8 | 7/8 | 7/8 |
| First-response AP-overbudget outputs | 1 | 1 | 0 |
| All AP-overbudget outputs, including repairs | 2 | 2 | 0 |
| All static-invalid outputs | 2 | 5 | 3 |
| Invalid-reference outputs | 0 | 3 | 3 |
| Accepted plans/actions exceeding current AP | 0 | 0 | 0 |

The two initial AP failures were both POSITION-002, where each full-turn arm proposed two 2-AP Snipes against a 3-AP budget. Both repairs remained 4-AP plans. Bounded's other two initially invalid decisions were replacement waves, both with 1 AP and an out-of-range Attack. Stepwise's invalid decisions were an initial Snipe in POSITION and a later Attack in FIREBALL.

First-response validity by current AP (valid / decisions):

| Current AP | Strict | Bounded, including replacement | Stepwise, including later steps |
|---|---:|---:|---:|
| 1 | 2/2 | 2/4 | 5/6 |
| 2 | 3/3 | 3/3 | 3/3 |
| 3 | 1/2 | 1/2 | 2/3 |
| 5 | 1/1 | 1/1 | 1/1 |

Overall, 25/31 decision first responses were statically valid, with 6 repairs and 4 repair failures. AP-overbudget initial outputs were 2/16 full-turn initial plans; the two failures came from the same snapshot. AP enforcement held, but model compliance was imperfect and the repair did not fix either budget error. The tiny, deliberately selected cohort does not establish a regression or equivalence against V5's 122-decision cohort. It would be inaccurate to call AP discipline uniformly healthy from this run.

## Plan and action shape

EndTurn is excluded from gameplay-action counts. Full-turn statistics below use **accepted initial plans** (7 per arm); rejected POSITION plans remain in compliance/failure counts, not silently counted as zero-action tactical plans.

| Initial-plan measure | Strict | Bounded |
|---|---:|---:|
| Gameplay actions per plan | [1,2,2,1,2,1,2] | [1,1,2,1,2,1,2] |
| Mean gameplay actions | 1.571 | 1.429 |
| One-action plans | 3/7 (42.9%) | 4/7 (57.1%) |
| Multi-action plans | 4/7 (57.1%) | 3/7 (42.9%) |
| Planned AP | [1,3,4,2,2,1,2] | [1,2,3,2,2,1,2] |
| Mean planned AP | 2.143 | 1.857 |
| Plans below starting AP budget | 1/7 | 2/7 |
| Full-budget plans | 6/7 | 5/7 |
| Accepted explicit EndTurn placements | none | after 1 action; after 2 actions |

Both arms still produced multiple gameplay actions; there was no collapse to universally single-action plans. Sequence execution was imperfect, as intended to be measured. The two bounded replacement waves must be separate: one failed to produce an accepted plan; the other accepted one Move costing its full remaining 1 AP. Neither replacement ended explicitly.

Stepwise gameplay actions per turn were `[1,2,3,1,2,0,1,1]` (mean 1.375); requests per turn were `[1,2,3,1,2,2,1,3]` (mean 1.875), in frozen snapshot order.

Tactical outcomes are descriptive only. All three arms chose Snipe on MULTI-001 and missed the frozen down objective; the witness uses two Attacks. All missed POSITION's down objective. Stepwise achieved DOWNED's Finish/removal objective; strict and bounded did not. All achieved CORE's victory objective. Diagnostic AP/FIREBALL probes do not carry a binary success judgment. These results do not justify a control ranking or a universal plan-quality claim.

## First-decision comparison

It is essential to separate the **first raw response's first action** from the first **accepted** action after repair. The cleanest pre-refresh comparison is the raw first proposal; a syntactically present action in a rejected full-turn plan was never executed.

| Snapshot | Strict first raw action | Bounded first raw action | Stepwise first raw action | AP cost S/B/W | Mechanical objective class |
|---|---|---|---|---|---|
| AP-001 | Attack(actor, enemy) | same | same | 1/1/1 | unit damage |
| AP-003 | Snipe(actor, enemy) | same | same | 2/2/2 | unit damage |
| AP-005 | Snipe(actor, enemy) | same | same | 2/2/2 | unit damage |
| MULTI-001 | Snipe(actor, enemy) | same | same | 2/2/2 | unit damage |
| DOWNED-003 | Shield Bash(actor, enemy) | same | Attack(actor, enemy) | 1/1/1 | damage + push versus ordinary damage |
| POSITION-002 | Snipe(actor, enemy), rejected plan | same, rejected plan | same, rejected action | 2/2/2 | proposed unit damage; currently out of range |
| CORE-002 | Attack(actor, red-core) | same | same | 1/1/1 | Core damage / victory |
| FIREBALL-003 | Shield Bash(ally, enemy) | same | same | 1/1/1 | unit damage + push |

Raw first semantic actions matched exactly across all arms on **7/8 snapshots**. Strict and bounded matched on **8/8**. All arms matched first target and AP cost on all eight snapshots, and no raw first response chose EndTurn. On DOWNED the action type and push consequence differ, so the actions are not mechanically equivalent even though actor, target and cost match.

Raw first-action type counts:

- Strict and bounded each: Attack 2, Snipe 4, Shield Bash 2, EndTurn 0; seven unit-target proposals and one Core-target proposal.
- Stepwise: Attack 3, Snipe 4, Shield Bash 1, EndTurn 0; the same target totals.

After validation/repair, POSITION has **no accepted initial plan** for strict/bounded and **EndTurn** for stepwise. Thus accepted first actions match across all arms on six snapshots; DOWNED differs, and POSITION cannot be compared as three accepted tactical actions. The all-decision accepted-action counts would conceal this repair effect if substituted for raw first decisions.

No first-action difference can be attributed to control-specific state refresh: refresh had not yet happened. Wrapper/cardinality effects and model nondeterminism are confounded in DOWNED's one difference. The agreement across seven states, equal schemas/facts, and differences between strict/bounded stop suffixes despite identical prompt bytes provide no evidence of an obvious broad wrapper-induced policy shift. POSITION's repaired EndTurn may reflect repair/output-cardinality behavior, but causation cannot be assigned from one sample. No LLM judge was used.

## Resources

Cached input is a subset of input tokens, not an additional token category to add to totals. Latency is observed backend request wall time, including transport; the adapter has no separately measured provider-server latency. The “thinking” field is not hidden reasoning time. Turn elapsed includes runner/controller work and instrumentation inside the timed boundary, but is not whole-process wall time.

| Resource | Strict | Bounded | Stepwise | Total |
|---|---:|---:|---:|---:|
| Requests | 9 | 13 | 15 | 37 |
| Input tokens | 17,886 | 26,078 | 29,861 | 73,825 |
| Cached input tokens | 1,851 | 21,919 | 4,136 | 27,906 |
| Output tokens | 452 | 608 | 574 | 1,634 |
| Reasoning tokens | 0 | 0 | 0 | 0 |
| Total tokens | 18,338 | 26,686 | 30,435 | 75,459 |
| Request wall time / backend thinking, seconds | 15.829 | 17.511 | 21.400 | 54.740 |
| Sum of timed turn elapsed, seconds | 21.521 | 25.196 | 30.255 | 76.973 |

The fixed strict→bounded→stepwise order and identical strict/bounded prompt/first observation can affect caching. Bounded's high cached-token share must not be treated as an intrinsic efficiency advantage or directly projected to a 300-match study. These are resource observations for this run, not a cost benchmark.

## Integrity and preservation

- All 24 command traces, including failed-trial prefixes, replayed exactly and reproduced final states/hashes. All 27 accepted decision plans independently reparsed against their authoritative observation and AP budget.
- All 31 decision observations matched independently reconstructed command-prefix states. There was no state-information mismatch between controls at the first decision.
- Source/preparation/prompt checks ran before requests; all frozen source hashes and preparation still verify after execution. Runtime configuration matched the manifest.
- All 37 ledger reservations reconcile with attempts and stay inside per-trial/global ceilings. The ledger SHA-256 is `7c994a7020b08b0e0ea7b4e622d086c9ee9b9f70cb5330daf92263ab253d555a`.
- All 62 primary evidence-file hashes verified. Additional reports are derived artifacts, not edits to the sealed trial evidence.
- The existing 423-file preservation inventory had zero changed/missing files. This inventory was captured after adding the harness/tests and before the live run. It covers the files available in this checkout, not an unsupported claim to recheck the prior task's larger historical evidence inventory.
- No heuristic fallback, transport retry, impossible transition, source drift, prompt drift, wrong profile/control/observation/schema binding, request-accounting corruption, or evidence corruption was detected.

## Answers and next-phase blockers

1. **Same tactical information/action vocabulary?** Yes: identical starting observations and semantic fields, with only intended cardinality/wrapper differences.
2. **Explicit EndTurn implemented correctly?** Yes in the observed bounded and stepwise cases. Strict's explicit-stop branch was not exercised live; existing offline tests cover it.
3. **Used sensibly or excessively?** Only three reached explicit stops, so no broad frequency claim is justified. AP-005 bounded was concretely premature; POSITION stepwise's repaired immediate stop missed a known movement sequence. Not a clean behavioral pass.
4. **AP compliance good?** Enforcement was correct; model compliance was mixed. Both full-turn POSITION plans and their repairs exceeded 3 AP. No accepted plan exceeded AP. No statistically defensible V5-regression estimate follows from eight states.
5. **Full-turn shape healthy?** Multi-action plans remained common (4/7 strict, 3/7 bounded accepted initial plans). Tactical objective success and stop choice remained imperfect.
6. **Bounded recovery worked?** Yes as a control contract: two correctly triggered refreshes, one successful repaired replacement recovering 1 AP, one preserved failure.
7. **No replan after stop/clean completion?** Yes for the observed completions; both positive-AP explicit stops caused no replan. Positive-AP clean bounded completion was not sampled live.
8. **Stepwise stopped after EndTurn?** Yes, zero further requests after its repaired EndTurn.
9. **Obvious wrapper-induced policy shift?** No demonstrated broad shift: first raw actions agree on 7/8 states. The one initial difference cannot be separated from nondeterminism/cardinality. Repair-associated stop behavior remains a concern.
10. **Freeze now?** Hold an unconditional behavioral freeze pending review of the specific premature-stop evidence. The execution contract passes; do not describe this as a tactical-strength failure or tune away the benchmark's stale-state phenomenon. No changes or new live tests have been made in response.

Before the 300-match benchmark: resolve whether the observed premature stops are accepted characteristics of the frozen candidate; record the final family/model contract; prepare and freeze a matched full-match schedule/runner with explicit adjudication of provider-failed committed prefixes, request budgets, replay and provenance; and obtain separate authorization for that study. Do not promote bounded from these eight snapshots. **No full-match benchmark or 300-match study was started.**
