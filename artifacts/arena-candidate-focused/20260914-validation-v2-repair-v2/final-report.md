**Fresh candidate-family validation with repair V2 ? 2026-09-14**

**Recommendation: FREEZE CANDIDATE BENCHMARK CONTRACT.** The fresh run completed 24/24 intended turns with 37/86 OpenAI requests and no provider failures. All six naturally invoked repairs succeeded; none repeated the diagnosed error, introduced new invalidity, or escaped through immediate EndTurn. All 24 traces replayed exactly. No observed contract blocker remains before separately authorized full-match benchmark design. This is a recommendation to freeze, not a product promotion or a claim of tactical or match superiority.

Two initial, unrepaired AP-005 plans still stopped with a mechanically available attack that would down the enemy. Those are legal tactical weaknesses and remain benchmark data under the frozen criteria. The run provides no live stepwise EndTurn example and no live bounded-replacement repair episode; their bindings/control paths retain offline test coverage. No additional inference was used to fill those coverage gaps.

**Execution, scope, and evidence.** The ceiling was 16 strict requests (8 x 2), 32 bounded (8 x 4), and 38 stepwise (2 x total 19 available AP): 86 overall. The AP cohort was 1,3,5,2,2,3,1,2. Trial order was the prior snapshot order, each followed by strict, bounded, stepwise. There was no preflight inference. The one live command that launched was:

```powershell
.venv/Scripts/python.exe scripts/arena-candidate-focused-repair-v2.py run --live --output artifacts/arena-candidate-focused/20260914-validation-v2-repair-v2
```

The earlier automatic-approval rejection launched no process and consumed zero requests. The user then explicitly authorized OpenAI payload transmission. The preparation verification.json retains its historical blocked status; completion.json and this report describe the completed run. No live command was retried after starting.

Prepared offline commands run after completion:

```powershell
.venv/Scripts/python.exe scripts/arena-candidate-focused-repair-v2.py analyze --output artifacts/arena-candidate-focused/20260914-validation-v2-repair-v2
.venv/Scripts/python.exe scripts/arena-candidate-focused-repair-v2-review.py --output artifacts/arena-candidate-focused/20260914-validation-v2-repair-v2
```

Created in this new immutable output directory: manifest.json; request-ledger.jsonl; 37 request-NNN.json pre-send reservations/context records; 37 payload-NNN.json exact outgoing message/prompt/schema records; 24 snapshot-control trial JSON files; completion.json; analysis.json; review-data.json; report-data.json; this final-report.md; and delivery-integrity.json. The runner, supplementary review script, runner tests, and preparation directory were added during offline preparation. No pre-existing source or evidence file was edited.

**Frozen binding.** OpenAI endpoint https://api.openai.com/v1/; gpt-5.6-luna / luna-config-v1; reasoning none; max output 512; store false; SDK retries zero. Every provider instance used arena-candidate-repair-v2. OLD repair remains available but was unused. Policy arena-policy-core-v1; full-turn prompt arena-turn-prompt-v6; step prompt arena-step-prompt-v3; observation arena-observation-v4. The repository concrete schema ID corresponding to the requested action-schema V2 is arena-turn-plan-schema-v2. Rules arena-rules-v2 and scenario arena-scenario-v1 were unchanged. All three control versions, prompt/source/snapshot/observation hashes and exact schemas are in manifest.json and preparation-final.json.

**Control totals.** Each control completed eight turns without provider failure. Strict had one execution truncation, so completion does not mean all proposed gameplay executed.

| Control | Requests / structural cap | Decisions | Repairs valid / failed | Replans | Explicit E | First responses valid | AP spent / left |
|---|---|---|---|---|---|---|---|
| strict | 10 / 16 | 8 | 2 / 0 | 0 | 2 | 6 / 8 | 17 / 2 |
| bounded | 10 / 32 | 9 | 1 / 0 | 1 | 3 | 8 / 9 | 17 / 2 |
| stepwise | 17 / 38 | 14 | 3 / 0 | 0 | 0 | 11 / 14 | 19 / 0 |

Request decomposition: strict 8 initial + 2 repairs; bounded 8 initial + 1 execution-triggered replan + 1 initial repair; stepwise 14 decisions + 3 repairs. All 37 ledger reservations reconcile with 37 provider attempts and 37 saved outgoing payloads. No fallback, transport retry, extra repair, unexplained attempt, or request after reached EndTurn occurred.

**All 24 trials.** A=Attack, S=Snipe, B=Shield Bash, F=Finish, M=Move, E=explicit EndTurn. Parentheses give actor and target/destination. Semicolons separate decision waves; static repairs replace a wave without executing the rejected output. C=CLEAN_PLAN_COMPLETE; E=INTENTIONAL_END_TURN; X=EXECUTION_TRUNCATION; T=TERMINAL. First-output validity is the original response, before repair. Rejected actions are safe semantic reconstructions retained by the provider, not arbitrary raw prose.

| Trial | First output | Static result | Repairs | Accepted wave(s) | Exec invalidities | AP spent / left | Stop | Requests |
|---|---|---|---|---|---|---|---|---|
| AP-001-strict | A(actor,enemy) | valid | 0 | A(actor,enemy) | 0 | 1 / 0 | C | 1 |
| AP-001-bounded | A(actor,enemy) | valid | 0 | A(actor,enemy) | 0 | 1 / 0 | C | 1 |
| AP-001-stepwise | A(actor,enemy) | valid | 0 | A(actor,enemy) | 0 | 1 / 0 | C | 1 |
| AP-003-strict | S(actor,enemy), A(actor,enemy), E | valid | 0 | S(actor,enemy), A(actor,enemy), E | 0 | 3 / 0 | E | 1 |
| AP-003-bounded | S(actor,enemy), A(actor,enemy), E | valid | 0 | S(actor,enemy), A(actor,enemy), E | 0 | 3 / 0 | E | 1 |
| AP-003-stepwise | S(actor,enemy) | valid | 0 | S(actor,enemy) ; A(actor,enemy) | 0 | 3 / 0 | C | 2 |
| AP-005-strict | S(actor,enemy), S(actor,enemy), E | valid | 0 | S(actor,enemy), S(actor,enemy), E | 0 | 4 / 1 | E | 1 |
| AP-005-bounded | S(actor,enemy), A(actor,enemy), E | valid | 0 | S(actor,enemy), A(actor,enemy), E | 0 | 3 / 2 | E | 1 |
| AP-005-stepwise | S(actor,enemy) | valid | 0 | S(actor,enemy) ; S(actor,enemy) ; A(actor,enemy) | 0 | 5 / 0 | C | 3 |
| MULTI-001-strict | S(actor,enemy), A(actor,enemy) | ap_budget | 1 | S(actor,enemy) | 0 | 2 / 0 | C | 2 |
| MULTI-001-bounded | S(actor,enemy) | valid | 0 | S(actor,enemy) | 0 | 2 / 0 | C | 1 |
| MULTI-001-stepwise | S(actor,enemy) | valid | 0 | S(actor,enemy) | 0 | 2 / 0 | C | 1 |
| DOWNED-003-strict | A(actor,enemy), A(actor,enemy) | valid | 0 | A(actor,enemy), A(actor,enemy) | 1 | 1 / 1 | X | 1 |
| DOWNED-003-bounded | A(actor,enemy), A(actor,enemy) | valid | 0 | A(actor,enemy), A(actor,enemy) ; F(actor,enemy) | 1 | 2 / 0 | C | 2 |
| DOWNED-003-stepwise | B(actor,enemy) | valid | 1 | B(actor,enemy) ; M(actor,(3,2)) | 0 | 2 / 0 | C | 3 |
| POSITION-002-strict | S(actor,enemy), S(actor,reserve) | ap_budget | 1 | M(actor,(4,2)), S(actor,enemy) | 0 | 3 / 0 | C | 2 |
| POSITION-002-bounded | S(actor,enemy), S(actor,enemy), E | ap_budget | 1 | M(actor,(4,2)), S(actor,enemy), E | 0 | 3 / 0 | E | 2 |
| POSITION-002-stepwise | S(actor,enemy) | invalid_reference | 1 | M(actor,(4,2)) ; S(actor,enemy) | 0 | 3 / 0 | C | 3 |
| CORE-002-strict | A(actor,red-core) | valid | 0 | A(actor,red-core) | 0 | 1 / 0 | T | 1 |
| CORE-002-bounded | A(actor,red-core) | valid | 0 | A(actor,red-core) | 0 | 1 / 0 | T | 1 |
| CORE-002-stepwise | A(actor,red-core) | valid | 0 | A(actor,red-core) | 0 | 1 / 0 | T | 1 |
| FIREBALL-003-strict | A(actor,enemy), A(ally,enemy) | valid | 0 | A(actor,enemy), A(ally,enemy) | 0 | 2 / 0 | C | 1 |
| FIREBALL-003-bounded | A(actor,enemy), B(ally,enemy) | valid | 0 | A(actor,enemy), B(ally,enemy) | 0 | 2 / 0 | C | 1 |
| FIREBALL-003-stepwise | B(ally,enemy) | valid | 1 | B(ally,enemy) ; M(actor,(4,2)) | 0 | 2 / 0 | C | 3 |

Strict DOWNED accepts two Attacks statically; the first downs the enemy and the second is rejected at execution for ACTIVE/DOWNED status. One action and 1 AP execute; 1 AP remains under EXECUTION_TRUNCATION. No repair is used for that stale-state suffix. All other strict accepted plans execute completely, stopping on explicit E, clean completion, or terminal victory as recorded. There are no clean short-plan leftovers in this run.

**Bounded behavior.** Only DOWNED replanned: after Attack, 1 AP remained and the stale suffix was one Attack(enemy), rejected for invalid target ACTIVE/DOWNED status. Replacement Finish(enemy) was valid on its first response, executed, recovered 1 AP, and cleanly completed at zero AP. No second invalidity and no replacement repair occurred. POSITION initial static rejection used repair, not replan.

| Bounded trial | Initial repair | Execution invalidity / AP | Stale suffix | Replan / replacement | Replacement repair | Second invalidity | Recovered AP | Final AP / stop |
|---|---|---|---|---|---|---|---|---|
| AP-001-bounded | False | - | 0 | no | False | False | 0 | 0 / CLEAN_PLAN_COMPLETE |
| AP-003-bounded | False | - | 0 | no | False | False | 0 | 0 / INTENTIONAL_END_TURN |
| AP-005-bounded | False | - | 0 | no | False | False | 0 | 2 / INTENTIONAL_END_TURN |
| MULTI-001-bounded | False | - | 0 | no | False | False | 0 | 0 / CLEAN_PLAN_COMPLETE |
| DOWNED-003-bounded | False | invalid target ACTIVE/DOWNED status / 1 | 1 | F(actor,enemy) | False | False | 1 | 0 / CLEAN_PLAN_COMPLETE |
| POSITION-002-bounded | True | - | 0 | no | False | False | 0 | 0 / INTENTIONAL_END_TURN |
| CORE-002-bounded | False | - | 0 | no | False | False | 0 | 0 / TERMINAL |
| FIREBALL-003-bounded | False | - | 0 | no | False | False | 0 | 0 / CLEAN_PLAN_COMPLETE |

**Stepwise behavior.** All 14 accepted actions executed legally; requests ended at AP exhaustion or terminal victory. The sequence and repair counts appear below. No explicit EndTurn was sampled, so a fresh live post-EndTurn test is not claimed. Existing offline fake-controller tests cover that branch; the unchanged stop guard was verified. There was no request after any reached E in any control.

| Stepwise trial | Sequential accepted actions | Repairs | Explicit E / AP at E | Requests | Request after E | Final stop |
|---|---|---|---|---|---|---|
| AP-001-stepwise | A(actor,enemy) | 0 | no / N/A | 1 | no (no E reached) | CLEAN_PLAN_COMPLETE |
| AP-003-stepwise | S(actor,enemy), A(actor,enemy) | 0 | no / N/A | 2 | no (no E reached) | CLEAN_PLAN_COMPLETE |
| AP-005-stepwise | S(actor,enemy), S(actor,enemy), A(actor,enemy) | 0 | no / N/A | 3 | no (no E reached) | CLEAN_PLAN_COMPLETE |
| MULTI-001-stepwise | S(actor,enemy) | 0 | no / N/A | 1 | no (no E reached) | CLEAN_PLAN_COMPLETE |
| DOWNED-003-stepwise | B(actor,enemy), M(actor,(3,2)) | 1 | no / N/A | 3 | no (no E reached) | CLEAN_PLAN_COMPLETE |
| POSITION-002-stepwise | M(actor,(4,2)), S(actor,enemy) | 1 | no / N/A | 3 | no (no E reached) | CLEAN_PLAN_COMPLETE |
| CORE-002-stepwise | A(actor,red-core) | 0 | no / N/A | 1 | no (no E reached) | TERMINAL |
| FIREBALL-003-stepwise | B(ally,enemy), M(actor,(4,2)) | 1 | no / N/A | 3 | no (no E reached) | CLEAN_PLAN_COMPLETE |

**Six naturally invoked repairs.** Every repair returned a valid complete replacement. Repeated-same-error=0; NEW_INVALIDITY=0; new detailed diagnostic codes=0; malformed=0; repair EndTurn outputs=1; EndTurn introduced=0; potential immediate repair escapes=0. The retained comparison classifier gives one VALID_SUFFIX_TRIM and five AMBIGUOUS, with no LLM judge. No bounded-replacement repair happened live; explicit V2 binding for that path was checked offline.

R1: **MULTI-001-strict, wave 0 (initial)**. Rejected [S(actor,enemy), A(actor,enemy)]. AP available/planned 2/3; costs [2, 1]. Static category ap_budget; diagnostics: AP 3 > 2 by 1.

Repair [S(actor,enemy)]: valid; repeated error no; new invalidity no; E present no; E introduced no; potential escape no. Class VALID_SUFFIX_TRIM. Retains exact Snipe actor/target prefix; trims AP-invalid Attack suffix. Input 2,343 (cached subset 1,862), output 40, reasoning 0, total 2,383; request wall time 1.352 s. Exact original diagnostics, safe rejected plan, output, comparison, and per-action AP ledger are retained in report-data.json and the trial/payload records.

R2: **DOWNED-003-stepwise, wave 1 (stepwise decision)**. Rejected [A(actor,enemy)]. AP available/planned 1/1; costs [1]. Static category invalid_reference; diagnostics: action 0: range, distance 2 > range 1.

Repair [M(actor,(3,2))]: valid; repeated error no; new invalidity no; E present no; E introduced no; potential escape no. Class AMBIGUOUS. Same actor moves adjacent toward original enemy; damage action replaced with positioning. Intent not mechanically proven. Input 2,242 (cached subset 1,778), output 43, reasoning 0, total 2,285; request wall time 1.455 s. Exact original diagnostics, safe rejected plan, output, comparison, and per-action AP ledger are retained in report-data.json and the trial/payload records.

R3: **POSITION-002-strict, wave 0 (initial)**. Rejected [S(actor,enemy), S(actor,reserve)]. AP available/planned 3/4; costs [2, 2]. Static category ap_budget; diagnostics: AP 4 > 3 by 1; action 0: range, distance 5 > range 4.

Repair [M(actor,(4,2)), S(actor,enemy)]: valid; repeated error no; new invalidity no; E present no; E introduced no; potential escape no. Class AMBIGUOUS. Retains original actor/enemy Snipe behind legal Move; drops reserve-target Snipe. Input 2,388 (cached subset 1,851), output 60, reasoning 0, total 2,448; request wall time 1.053 s. Exact original diagnostics, safe rejected plan, output, comparison, and per-action AP ledger are retained in report-data.json and the trial/payload records.

R4: **POSITION-002-bounded, wave 0 (initial)**. Rejected [S(actor,enemy), S(actor,enemy), E]. AP available/planned 3/4; costs [2, 2, 0]. Static category ap_budget; diagnostics: AP 4 > 3 by 1; action 0: range, distance 5 > range 4.

Repair [M(actor,(4,2)), S(actor,enemy), E]: valid; repeated error no; new invalidity no; E present yes; E introduced no; potential escape no. Class AMBIGUOUS. Retains actor/enemy Snipe behind legal Move; preserves original final E. Input 2,414 (cached subset 2,411), output 65, reasoning 0, total 2,479; request wall time 1.347 s. Exact original diagnostics, safe rejected plan, output, comparison, and per-action AP ledger are retained in report-data.json and the trial/payload records.

R5: **POSITION-002-stepwise, wave 0 (stepwise decision)**. Rejected [S(actor,enemy)]. AP available/planned 3/2; costs [2]. Static category invalid_reference; diagnostics: action 0: range, distance 5 > range 4.

Repair [M(actor,(4,2))]: valid; repeated error no; new invalidity no; E present no; E introduced no; potential escape no. Class AMBIGUOUS. Legal Move by original actor; following independent decision Snipes the original enemy. Input 2,322 (cached subset 2,319), output 43, reasoning 0, total 2,365; request wall time 1.860 s. Exact original diagnostics, safe rejected plan, output, comparison, and per-action AP ledger are retained in report-data.json and the trial/payload records.

R6: **FIREBALL-003-stepwise, wave 1 (stepwise decision)**. Rejected [A(actor,enemy)]. AP available/planned 1/1; costs [1]. Static category invalid_reference; diagnostics: action 0: range, distance 3 > range 2.

Repair [M(actor,(4,2))]: valid; repeated error no; new invalidity no; E present no; E introduced no; potential escape no. Class AMBIGUOUS. Same mage moves toward original enemy; Attack becomes positioning with 1 AP. Intent not mechanically proven. Input 2,749 (cached subset 2,284), output 43, reasoning 0, total 2,792; request wall time 1.639 s. Exact original diagnostics, safe rejected plan, output, comparison, and per-action AP ledger are retained in report-data.json and the trial/payload records.

Repair context supplied the authoritative current observation, safe rejected semantic sequence, precise AP and first-action range diagnostics, and the unchanged preserve-intent instruction. The POSITION repairs corrected both AP and masked range faults. They do not establish tactical optimality, and the static validator does not simulate later execution. Live payload assertions checked the actual enriched messages before transport.

**Reached EndTurn provenance.** Five reached explicit stops: strict 2, bounded 3, stepwise 0. Four originated in unrepaired initial responses; one was preserved in a repaired POSITION bounded response. All occurred after two gameplay actions. No immediate explicit stop occurred. Original EndTurn preservation is distinct from repair introduction.

| Trial | Output provenance | Actions before E | AP at E | Repair introduced E | Legal tactical continuation | Stop reason |
|---|---|---|---|---|---|---|
| AP-003-strict | initial output | 2 | 0 | False | no: zero AP | INTENTIONAL_END_TURN |
| AP-005-strict | initial output | 2 | 1 | False | yes: legal Attack downs enemy | INTENTIONAL_END_TURN |
| AP-003-bounded | initial output | 2 | 0 | False | no: zero AP | INTENTIONAL_END_TURN |
| AP-005-bounded | initial output | 2 | 2 | False | yes: legal Attack downs enemy | INTENTIONAL_END_TURN |
| POSITION-002-bounded | repair output | 2 | 0 | False | no: zero AP | INTENTIONAL_END_TURN |

At AP-005 strict, two Snipes leave enemy at 2 HP with 1 AP; at AP-005 bounded, Snipe+Attack leaves enemy at 5 HP with 2 AP. The legal catalog includes the ranger's 1-AP, 5-damage Attack in both states. Thus a coherent immediate down is available. These are dominated initial tactical stops, not repair escapes or differing EndTurn semantics. Other reached stops have zero AP. None was rejected merely for leaving legal gameplay available. Five first-response outputs contain E (including rejected POSITION bounded); one repair output contains E. Only the five reached stops count as explicit stop decisions.

**AP compliance and leftovers.** First responses were valid on 25/31 decisions (80.6%); turn-initial responses on 20/24 turns (83.3%). Three outputs were overbudget, all first responses: MULTI strict 3>2, POSITION strict 4>3, POSITION bounded 4>3. No repaired or accepted output exceeded AP. All 31 accepted plans reparsed successfully; 53 of 57 starting AP executed. Leftover AP is attributed by reason, not pooled as waste.

| Reason | Strict AP / stops | Bounded AP / stops | Stepwise AP / stops | Total AP |
|---|---|---|---|---|
| INTENTIONAL_END_TURN | 1 / 2 | 2 / 3 | 0 / 0 | 3 |
| CLEAN_PLAN_COMPLETE | 0 / 4 | 0 / 4 | 0 / 7 | 0 |
| EXECUTION_TRUNCATION | 1 / 1 | 0 / 0 | 0 / 0 | 1 |
| PROVIDER_FAILURE | 0 / 0 | 0 / 0 | 0 / 0 | 0 |
| TERMINAL | 0 / 1 | 0 / 1 | 0 / 1 | 0 |

**First raw-action comparability.** Six snapshots match exactly across all three controls. Zero snapshots differ only in target; zero nonidentical actions are classified as mechanically equivalent. Two are materially different: Attack downs the DOWNED enemy while Bash damages/pushes it; FIREBALL uses mage Attack versus knight Bash, also with different damage/push outcomes. Equal generic damage intent would not establish mechanical equivalence. Strict/bounded agree on all eight raw first actions.

| Snapshot | Strict raw first | Bounded raw first | Stepwise raw first | Classification |
|---|---|---|---|---|
| AP-001 | A(actor,enemy) | A(actor,enemy) | A(actor,enemy) | exact match |
| AP-003 | S(actor,enemy) | S(actor,enemy) | S(actor,enemy) | exact match |
| AP-005 | S(actor,enemy) | S(actor,enemy) | S(actor,enemy) | exact match |
| CORE-002 | A(actor,red-core) | A(actor,red-core) | A(actor,red-core) | exact match |
| DOWNED-003 | A(actor,enemy) | A(actor,enemy) | B(actor,enemy) | materially different |
| FIREBALL-003 | A(actor,enemy) | A(actor,enemy) | B(ally,enemy) | materially different |
| MULTI-001 | S(actor,enemy) | S(actor,enemy) | S(actor,enemy) | exact match |
| POSITION-002 | S(actor,enemy) | S(actor,enemy) | S(actor,enemy) | exact match |

All eight starting observations are equal across controls, including board/unit/core state, AP, legal actions, action costs, model-visible rules and mechanics. All 31 initial/refreshed observations reproduce from their committed command prefixes. Full-turn and single-action wire schemas differ only in actions.maxItems; action meanings are identical. The exact shared policy is identical, with expected full-plan versus single-action cardinality wrappers and observation cadence. There is no tactical-information or schema divergence.

**Resources.** Cached input is a subset of input, not additive. Reasoning token usage is zero in every request. Request wall time includes the provider adapter call and local outgoing-payload audit/persistence; it is not server-only latency. The existing backend_thinking_seconds telemetry equals the sum of those same request wall times, so those two columns must not be added. Trial elapsed also includes controller and integrity overhead; it excludes some inter-trial/pre/post-run work.

| Control | Requests | Repairs | Replans | Input | Cached input | Output | Reasoning | Total | Request wall s | Backend thinking s | Trial elapsed s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| strict | 10 | 2 | 0 | 20733 | 3713 | 511 | 0 | 21244 | 22.453 | 22.453 | 28.256 |
| bounded | 10 | 1 | 1 | 20211 | 18389 | 505 | 0 | 20716 | 13.275 | 13.275 | 18.967 |
| stepwise | 17 | 3 | 0 | 35048 | 6381 | 678 | 0 | 35726 | 28.175 | 28.175 | 37.964 |
| Total | 37 | 6 | 1 | 75992 | 28483 | 1694 | 0 | 77686 | 63.903 | 63.903 | 85.186 |

Repair-only incremental request resources within this run (already included above):

| Control | Repair requests | Input | Cached input | Output | Reasoning | Total | Request wall s |
|---|---|---|---|---|---|---|---|
| strict | 2 | 4731 | 3713 | 100 | 0 | 4831 | 2.405 |
| bounded | 1 | 2414 | 2411 | 65 | 0 | 2479 | 1.347 |
| stepwise | 3 | 7313 | 6381 | 129 | 0 | 7442 | 4.955 |
| Total | 6 | 14458 | 12505 | 294 | 0 | 14752 | 8.707 |

No fresh OLD counterfactual was sent, so the incremental cost of V2 wording/context itself is not identifiable from this run. The prior repair-only paired experiment supplies that separate estimate; these 14,752 repair tokens and 8.707 seconds measure whole repair requests. Fixed control order and caching prevent interpreting cached-token differences as inherent control efficiency.

**Descriptive comparison with previous focused validation.** Fresh model outputs are nondeterministic and the naturally encountered repair cohorts differ; equal starting snapshots do not make this a deterministic paired causal experiment.

| Measure | Previous focused OLD | Fresh repair V2 |
|---|---|---|
| Completed turns | 24 | 24 |
| Requests | 37 | 37 |
| Decisions / first-valid | 31 / 25 | 31 / 25 |
| Trials without provider failure | 20 | 24 |
| Repair episodes | 6 | 6 |
| Successful / failed repairs | 2 / 4 | 6 / 0 |
| Repeated repair errors | 4 | 0 |
| Frozen new-invalidity labels | 0 | 0 |
| Repair outputs containing E | 2 | 1 |
| Potential immediate repair escapes | 1 | 0 |
| Explicit E strict / bounded / stepwise | 0 / 2 / 1 | 2 / 3 / 0 |
| Strict truncations | 2 | 1 |
| Bounded replans / recovered AP | 2 / 1 | 1 / 1 |
| First raw actions exact | 7/8 | 6/8 |
| Replay exact | 24/24 | 24/24 |
| Input / output / total tokens | 73,825 / 1,634 / 75,459 | 75,992 / 1,694 / 77,686 |
| Request wall seconds | 54.740 | 63.903 |

The repair reliability and escape findings descriptively support transfer of the repair-only benefit to natural planning. Unchanged first-response validity and recurring poor initial stops show why this is a repair-contract result, not general tactical superiority. The new 6/6 denominator is small; it does not imply zero future failure probability. Different live exposure, provider variance, caching, and local audit timing limit latency and control comparisons.

**Integrity and freeze decision.** The prepared runner completed without hard stop. It verified binding/source and existing live-evidence hashes before each request and full preservation before and after live inference. Offline analysis independently rechecked all 24 replays and request accounting; supplementary review reparsed all 31 accepted plans and reconstructed all 31 observations. Completion seals 99 primary evidence files plus the ledger. All 16,304 pre-existing inventory files remained byte-identical, covering prior focused validation, paired repair comparison, V1/V4/V5 literacy evidence, candidate prompts, repair V2, observations/schema, controls, game rules, defaults, and Empire. No frozen runner, prompt, source, control, or model setting was edited during this run. Delivery hashes additionally cover the final reports and prepared analysis scripts.

Recommend freezing the existing shared policy, full-turn/stepwise prompts, observation V4, action schema V2, explicit EndTurn semantics, repair V2, strict/bounded/stepwise controls, Luna model/profile, and rules/scenario versions exactly as bound in the manifest. No contract blocker was observed. Retain monitoring of poor legal initial stops, model errors, and the two naturally unexercised branches; do not tune from these results. Subsequent 300-match case-study design and its frozen deterministic opponent/side balancing remain a separate phase requiring authorization. No full matches, additional probes, Qwen/Ollama calls, Fireball-specific experiments, or 300-match work were started. Stopped after this validation and offline reporting.

Final prepared verification also ran successfully: `.venv/Scripts/python.exe scripts/arena-candidate-focused-repair-v2.py verify` returned `{"verified": true}` after reporting.
