# Arena Phase 7E — stepwise full-match failure forensics

Offline analysis of the eight Phase 7D attempts. Recommendation: **Option A, a bounded, side-balanced frozen reliability replication**, subject to separate live authorization. The evidence cannot establish a common actionable repair defect: rejected responses were deliberately omitted, and current feedback already gives the proposed catalog-copy remedy. Do not implement repair V2 or reopen stepwise architecture on these records alone.

## 1. Experiment and evidence limits

Evidence: [.local Phase 7D report](../.local/arena-phase7d-stepwise-fullmatch-pilot-20260913-02/report.md), summary.json, per-turn observations/telemetry, command traces and snapshots. The actual manifest says **arena-benchmark-v3**, with arena-control-stepwise-v1, arena-step-prompt-v1, arena-observation-v2, arena-turn-plan-schema-v1, arena-probes-v1, qwen-config-v1 and luna-config-v1. The task description names benchmark V2; this report preserves and describes the actual V3 full-match wrapper, without changing either artifact.

Provider.last_trace temporarily held sanitized raw_content, but benchmark_provider.safe_inference persists only categories, numeric telemetry and IDs. Failed steps retain decision=null and resulting_plan=null. Neither null means actions=[]. No raw initial/repair decision, invalid parsed object, or exact validator detail exists in these persisted stopping records. No provider logs were queried. The six-entry [failure ledger](../.local/arena-phase7e-offline-forensics-20260913/failure-ledger.json) includes full legal catalogs, observations, telemetry, hashes, reconstructed request content and trace paths; null fields explicitly denote missing evidence.

## 2. Eight-match ledger

| Match | Blue / Red | Result | Global / player turns | Decisions / requests / repairs | Model AP | Latency s |
| --- | --- | --- | --- | --- | --- | --- |
| qwen-self/run-001 | ollama / ollama | failed; repair_failed | 2 / 5 | 25 / 26 / 1 | 24 | 71.810 |
| qwen-self/run-002 | ollama / ollama | failed; repair_failed | 2 / 5 | 25 / 26 / 1 | 24 | 52.065 |
| luna-self/run-001 | openai / openai | failed; repair_failed | 4 / 8 | 25 / 27 / 2 | 35 | 46.448 |
| luna-self/run-002 | openai / openai | failed; repair_failed | 9 / 18 | 53 / 62 / 9 | 79 | 92.783 |
| qwen-vs-heuristic/run-001 | ollama / heuristic | failed; repair_failed | 1 / 3 | 6 / 7 / 1 | 5 | 13.664 |
| qwen-vs-heuristic/run-002 | heuristic / ollama | completed; winner blue | 5 / 11 | 20 / 20 / 0 | 25 | 50.525 |
| luna-vs-heuristic/run-001 | openai / heuristic | failed; repair_failed | 6 / 13 | 20 / 22 / 2 | 30 | 36.130 |
| luna-vs-heuristic/run-002 | heuristic / openai | completed; winner red | 4 / 10 | 15 / 15 / 0 | 24 | 23.849 |

Global values above are persisted final zero-based round counters, not counts of model turns. Latency is summed transport wall time including repairs, excluding orchestration and preflight. All eight traces replayed exactly again offline. Two historical preflight requests are excluded from the 205 match requests; historical total remains 207. This phase sent zero requests.

## 3. Six exact stopping points

| Match | Provider / side | Decision global round | Player turn / side turn | Step index (0-based) | AP | Catalog | Initial → repair | Decisions / requests through failure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen-self/run-001 | ollama / blue | 2 | 5 / 3 | 4 | 1 | 38 | invalid_reference → invalid_reference | 25 / 26 |
| qwen-self/run-002 | ollama / blue | 2 | 5 / 3 | 4 | 1 | 38 | invalid_reference → invalid_reference | 25 / 26 |
| luna-self/run-001 | openai / red | 3 | 8 / 4 | 1 | 4 | 54 | invalid_reference → invalid_reference | 25 / 27 |
| luna-self/run-002 | openai / red | 8 | 18 / 9 | 1 | 3 | 43 | invalid_reference → invalid_reference | 53 / 62 |
| qwen-vs-heuristic/run-001 | ollama / blue | 1 | 3 / 2 | 0 | 5 | 52 | invalid_reference → invalid_reference | 6 / 7 |
| luna-vs-heuristic/run-001 | openai / blue | 6 | 13 / 7 | 1 | 4 | 25 | invalid_reference → invalid_reference | 20 / 22 |

Side turn counts only the stopping side’s turns; self-play model exposure includes both sides. The stopping decision and its two requests are included. Strictly before that decision, subtract one decision and two requests. Failed decisions execute no action. The controller subsequently records EndTurn before the strict match runner stops, so final/partial snapshots can have a later round counter, next active side and refreshed AP. Stopping hashes below are verified before this housekeeping EndTurn.

### qwen-self/run-001

Observation SHA-256: `a0a594ee374e7da09c132a72680912aabcbbdd519c1e84443e31fa020ccc728f`. State before failed decision: `dab7ec2cd9da559727020a635c4726580af2564b66283d1951897cb0dafc8f48`.

blue: 4 active/0 downed/0 removed, HP 48, Core 30; red: 4 active/0 downed/0 removed, HP 48, Core 30.

Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.

The catalog contains 38 actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.

### qwen-self/run-002

Observation SHA-256: `a0a594ee374e7da09c132a72680912aabcbbdd519c1e84443e31fa020ccc728f`. State before failed decision: `dab7ec2cd9da559727020a635c4726580af2564b66283d1951897cb0dafc8f48`.

blue: 4 active/0 downed/0 removed, HP 48, Core 30; red: 4 active/0 downed/0 removed, HP 48, Core 30.

Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.

The catalog contains 38 actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.

### luna-self/run-001

Observation SHA-256: `b5ffffd05aaa84901479e61de90aea8129a6434b1c2cbf932a1a478851d1bc74`. State before failed decision: `58108d21b2f7e83e42a7c4035dca14d496d298878d9c98627df705132b998749`.

blue: 2 active/1 downed/1 removed, HP 20, Core 30; red: 4 active/0 downed/0 removed, HP 37, Core 30.

Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.

The catalog contains 54 actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.

### luna-self/run-002

Observation SHA-256: `8742d279073590dd47556f664926e860dc61ee68988f8580079ce750347d8827`. State before failed decision: `f5078bc1d3afc7cbdb53a51457267a3f13adc6036d8ed3b3fe590506fdd7eff2`.

blue: 2 active/2 downed/0 removed, HP 19, Core 30; red: 3 active/1 downed/0 removed, HP 30, Core 30.

Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.

The catalog contains 43 actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.

### qwen-vs-heuristic/run-001

Observation SHA-256: `b2964c681de70063f7f02ea843effee0ddb6ae44b22e09761c4e58da029cd23c`. State before failed decision: `684fadad5cf691b6a4df2ebe049dbe65fc8fb4087253ae55d23818abc2916ed8`.

blue: 4 active/0 downed/0 removed, HP 36, Core 30; red: 4 active/0 downed/0 removed, HP 48, Core 30.

Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.

The catalog contains 52 actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.

### luna-vs-heuristic/run-001

Observation SHA-256: `f960644ac3e3b01bf23c8f5228e44c623f0cb2df801d8124ba9ccf3e9473a636`. State before failed decision: `2f37a97cf78231183a6ed83b78860c195df4bb92e9119e8e9bcc75fa98e2b6bb`.

blue: 2 active/0 downed/2 removed, HP 11, Core 30; red: 2 active/2 downed/0 removed, HP 27, Core 30.

Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.

The catalog contains 25 actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.

## 4. Initial and repair taxonomy; validator order

All six stopping initials and all six stopping repairs have the repository category `invalid_reference`. Do not relabel them `action_not_in_current_catalog`, `wrong_actor`, or `invalid_ability`: the branch was not retained. Across all match decisions, all 16 initial invalid responses also have invalid_reference; 10 repairs succeeded and 6 failed with invalid_reference.

| Question (applies to all 12 rejected responses) | Evidence-supported answer |
| --- | --- |
| Transport/envelope accepted? | Yes, inferred: adapter returned content and application validation reached invalid_reference. |
| JSON syntactically valid? | Yes, inferred from passing strict_json before rejection. |
| Wire schema? | Application structure passed and satisfies the configured wire subset by code inspection; not independently revalidated without raw bytes. |
| arena-turn-plan-schema-v1? | Structural ArenaTurnPlan.from_dict passed; static/reference and stepwise acceptance did not. |
| 0, 1 or >1 actions? | At least one. With AP=1, exactly one. Otherwise 1..AP (bounded by five); exact count unavailable. |
| Current catalog membership? | No valid step was accepted. If exactly one action, it cannot be an exact legal entry; which entry/field failed is unknown. |
| Actor and target valid? | Unknown: rejection could be own-unit ID, target ID/team/Core restriction, or later catalog membership. |
| AP sufficient? | Yes for the declared total action cost: current-AP check precedes every invalid_reference branch. |
| Exact validator? | parse_turn_plan static-reference branches OR parse_step catalog-membership branch. No exception detail retained. |

Order: strict JSON → structural plan (including ≤5 actions/≤5 AP) → current AP budget → actor/ability/target/board reference checks → stepwise ≤1 action → exact canonical catalog membership. Thus an invalid-reference error can precede the too-many-actions check. **Zero confirmed 2+ action origins; four of six stopping decisions remain potentially multi-action; the two AP=1 Qwen self-play stops are necessarily single-action.** This is not evidence that 0/6 actually returned multiple actions. No known malformed JSON, envelope failure, AP-budget rejection or invalid_ability at these stopping pairs. A later hidden issue cannot be excluded.

A/B/C/D repair behavior cannot be separated: the same action may repeat, a different action may fail the same category, or one reference issue may be fixed while another causes the same category. E (malformed repair) is inconsistent with the recorded validator path. Use F/indeterminate if forced to choose a ledger label. Same-category recurrence is 6/6; exact repeated-invalid-decision rate is unknown.

## 5. Repair prompt audit

The following feedback is reconstructed exactly from the frozen stepwise source, checked against its pure return expression. It is identical for all six stopping pairs:

```text
Previous output failed validation (invalid_reference). Stepwise control requires zero or one action. Copy one complete action from the current legal_actions catalog, or return actions=[] to end the turn. Use the same schema. No reasoning or commentary.
```

Every repair uses the original observation user message plus this second user message, with the same system prompt and wire schema. Ollama prepends the system message; Luna supplies it as Responses instructions. There is no assistant message containing the rejected output. Exact HTTP payload bytes were not saved; the ledger therefore labels reconstructed content explicitly.

| Feedback item | Present? |
| --- | --- |
| Validation category | Yes: invalid_reference |
| Action index | No |
| Attempted actor ID/class | No; possible actors/classes exist in observation |
| Attempted action/target | No |
| Exact membership mismatch | No |
| Current AP | Yes, in original observation resent |
| Allowed action count | Yes, zero or one |
| Current Observation V2 and full legal catalog | Yes, same observation resent |
| Original invalid output | No |

**Classification for each pair: GENERIC / UNDER-SPECIFIED about the exact failing object or field, but already specific about the required remedy.** It is inaccurate to describe current repair feedback as only the word invalid_reference. The suggested simplified catalog-copy instruction is already substantially present. Missing raw outputs prevent attributing failures to ignored useful feedback versus a particular confusing mismatch.

## 6. Provider patterns and timing

Qwen: 3 failed matches, all initial/repair invalid_reference, 3/3 same-category recurrence, exact-repeat rate unknown. Its two self-play trajectories and stopping observation/state hashes coincide; equal generated token counts do not prove equal rejected text. Luna: 3 failed matches, same categories and 3/3 category recurrence, exact-repeat rate unknown. Unlike Qwen, Luna recovered 10/13 initial-invalid decisions. Same coarse category does not prove the same underlying cause. These tiny, state-dependent samples are descriptive.

Mechanical timing labels, defined only for this report: early = 0–2 completed global rounds at decision; mid = 3–5; late = ≥6. These are elapsed-round bins, not estimates of how close a battle was to ending. Counts: {'early': 3, 'mid': 1, 'late': 2}. Stopping unit counts, Core HP, AP, step and catalog sizes are above; all Core HP values are 30/30.

## 7. Compound reliability

| Provider | Decisions | Initial invalid | Repair failure / attempted | Eventual decision failure | Requests / AP | Total latency s |
| --- | --- | --- | --- | --- | --- | --- |
| ollama | 76 | 3/76 (3.95%) | 3/3 (100.00%) | 3.95% | 1.013 | 188.064 |
| openai | 113 | 13/113 (11.50%) | 3/13 (23.08%) | 2.65% | 0.750 | 199.211 |

Pooled: 189 model decisions = 173 first-response valid + 16 initial invalid. Repairs: 10 successful + 6 failed. First-response invalid rate 16/189 = 8.47%; conditional repair failure 6/16 = 37.50%; eventual fatal decision rate 6/189 = 3.17%; eventual accepted decision rate 183/189 = 96.83%. Accepted includes 11 empty EndTurn decisions; 172 selected actions were current-catalog valid and executed. There were zero execution defects and zero heuristic fallback contamination.

Completed matches consumed 35 model decisions and 35 requests; failed matches consumed 154 decisions and 170 requests. Individual counts through failure are 25, 25, 25, 53, 6 and 20 in schedule order. These are observed censored exposures, not required full-match lengths.

For illustration only, assume constant independent fatal probability p and survival S(N)=(1-p)^N. N counts model decisions, not repairs or heuristic turns. Using pooled p=6/189:

| Model | 10 decisions | 25 | 50 | 75 | 100 |
| --- | --- | --- | --- | --- | --- |
| pooled | 72.4% | 44.6% | 19.9% | 8.9% | 4.0% |
| Qwen | 66.8% | 36.5% | 13.3% | 4.9% | 1.8% |
| Luna | 76.4% | 51.0% | 26.0% | 13.3% | 6.8% |

Independence and a stationary hazard are not established. Matches share starting states, Qwen self-play duplicates a trajectory, providers differ, and bad states can cluster failures. Do not fit a win-rate claim or extrapolate confidence from these eight attempts. Phase 7C’s 100% Qwen / 98.86% Luna first-response validity and 56/56 completed probe turns concern shorter selected state exposures. The full-match first-response rates are 96.05% and 88.50%, on different trajectories; this distribution shift and compounded exposure explain why reliable probes can coexist with six failed matches. No statistical contradiction follows.

## 8. Completed Qwen and Luna mechanics

### Qwen: qwen-vs-heuristic/run-002

11 recorded player turns; final global counter 5; 5 Qwen-controlled turns. Winner blue by team_elimination. AP per model turn: [5, 5, 5, 5, 5]; mean 5.00.

Action distribution (executed): `{"attack": 8, "finish": 2, "fireball": 1, "move": 5, "revive": 3, "snipe": 1}`.

Unit damage 38, including friendly damage 4; Core damage 0. Finish 2; Revive 3; Fireball 1; Shield Bash 0; Snipe 1. Both sides' full metrics and terminal snapshot are in derived analysis.json.

Terminal state: blue: 2 active/0 downed/2 removed, HP 29, Core 30; red: 0 active/4 downed/0 removed, HP 0, Core 30.

Player turn 10, 5 AP: `[{"destination": {"x": 4, "y": 1}, "type": "move", "unit_id": "red-ranger"}, {"target_id": "blue-mage", "type": "snipe", "unit_id": "red-ranger"}, {"target_id": "blue-mage", "type": "finish", "unit_id": "red-ranger"}, {"target_id": "blue-cleric", "type": "attack", "unit_id": "red-ranger"}]`.

Player turn 8, 5 AP: `[{"destination": {"x": 6, "y": 0}, "type": "move", "unit_id": "red-ranger"}, {"destination": {"x": 5, "y": 0}, "type": "move", "unit_id": "red-ranger"}, {"target_position": {"x": 5, "y": 1}, "type": "fireball", "unit_id": "red-mage"}, {"destination": {"x": 6, "y": 0}, "type": "move", "unit_id": "red-ranger"}]`.

Full-turn Qwen baseline: 22 accepted plans executed 0 AP. This completed stepwise match demonstrates fresh-decision multi-action execution and meaningful combat despite losing. The interface/observation/control changed together, so this is not an isolated causal effect.

### Luna: luna-vs-heuristic/run-002

10 recorded player turns; final global counter 4; 5 Luna-controlled turns. Winner red by team_elimination. AP per model turn: [5, 5, 5, 4, 5]; mean 4.80.

Action distribution (executed): `{"attack": 3, "fireball": 4, "heal": 1, "revive": 2, "snipe": 4}`.

Unit damage 48, including friendly damage 0; Core damage 0. Finish 0; Revive 2; Fireball 4; Shield Bash 0; Snipe 4. Both sides' full metrics and terminal snapshot are in derived analysis.json.

Terminal state: blue: 0 active/4 downed/0 removed, HP 0, Core 30; red: 3 active/1 downed/0 removed, HP 18, Core 30.

Player turn 10, 5 AP: `[{"target_id": "blue-knight", "type": "snipe", "unit_id": "red-ranger"}, {"target_id": "blue-knight", "type": "snipe", "unit_id": "red-ranger"}, {"target_id": "blue-knight", "type": "attack", "unit_id": "red-ranger"}]`.

Player turn 8, 4 AP: `[{"target_id": "blue-mage", "type": "snipe", "unit_id": "red-ranger"}, {"target_id": "blue-mage", "type": "snipe", "unit_id": "red-ranger"}]`.

Frozen full-turn Luna lost all four heuristic matches. This one completed stepwise win is positive mechanical evidence, not evidence of superior stable strength: the other side-swapped attempt failed and cannot be discarded from the denominator.

## 9. Partial self-play

### qwen-self/run-001

Stopped after 5 recorded player turns, 25 model decisions, 26 requests (1 repairs). No winner. Final prefix: blue: 4 active/0 downed/0 removed, HP 48, Core 30; red: 4 active/0 downed/0 removed, HP 48, Core 30.

| Side | AP | Unit damage (incl. friendly) | Friendly damage | Core damage |
| --- | --- | --- | --- | --- |
| blue | 14 | 0 | 0 | 0 |
| red | 10 | 0 | 0 | 0 |

Blue-minus-red mechanical differences: active units 0; retained unit HP 0; Core HP 0. These measure only material at stop, not position, initiative, future tactical advantage or who would have won.

### qwen-self/run-002

Stopped after 5 recorded player turns, 25 model decisions, 26 requests (1 repairs). No winner. Final prefix: blue: 4 active/0 downed/0 removed, HP 48, Core 30; red: 4 active/0 downed/0 removed, HP 48, Core 30.

| Side | AP | Unit damage (incl. friendly) | Friendly damage | Core damage |
| --- | --- | --- | --- | --- |
| blue | 14 | 0 | 0 | 0 |
| red | 10 | 0 | 0 | 0 |

Blue-minus-red mechanical differences: active units 0; retained unit HP 0; Core HP 0. These measure only material at stop, not position, initiative, future tactical advantage or who would have won.

### luna-self/run-001

Stopped after 8 recorded player turns, 25 model decisions, 27 requests (2 repairs). No winner. Final prefix: blue: 2 active/1 downed/1 removed, HP 20, Core 30; red: 4 active/0 downed/0 removed, HP 37, Core 30.

| Side | AP | Unit damage (incl. friendly) | Friendly damage | Core damage |
| --- | --- | --- | --- | --- |
| blue | 20 | 12 | 4 | 0 |
| red | 15 | 36 | 8 | 0 |

Blue-minus-red mechanical differences: active units -2; retained unit HP -17; Core HP 0. These measure only material at stop, not position, initiative, future tactical advantage or who would have won.

### luna-self/run-002

Stopped after 18 recorded player turns, 53 model decisions, 62 requests (9 repairs). No winner. Final prefix: blue: 2 active/2 downed/0 removed, HP 19, Core 30; red: 3 active/1 downed/0 removed, HP 30, Core 30.

| Side | AP | Unit damage (incl. friendly) | Friendly damage | Core damage |
| --- | --- | --- | --- | --- |
| blue | 43 | 34 | 34 | 0 |
| red | 36 | 32 | 22 | 0 |

Blue-minus-red mechanical differences: active units -1; retained unit HP -11; Core HP 0. These measure only material at stop, not position, initiative, future tactical advantage or who would have won.

## 10. Request and latency implications

| Match | Requests / executed model AP | Latency through final prefix s |
| --- | --- | --- |
| qwen-self/run-001 | 26/24 = 1.083 | 71.810 |
| qwen-self/run-002 | 26/24 = 1.083 | 52.065 |
| luna-self/run-001 | 27/35 = 0.771 | 46.448 |
| luna-self/run-002 | 62/79 = 0.785 | 92.783 |
| qwen-vs-heuristic/run-001 | 7/5 = 1.400 | 13.664 |
| qwen-vs-heuristic/run-002 | 20/25 = 0.800 | 50.525 |
| luna-vs-heuristic/run-001 | 22/30 = 0.733 | 36.130 |
| luna-vs-heuristic/run-002 | 15/24 = 0.625 | 23.849 |

The match ledger reports all requests, repairs and latency through each stop. Requests strictly before the terminal invalid decision exclude its two attempts; latency for that pair is separately retained in failure-ledger.json. Qwen consumed 59 requests over its three failed matches and 20 in its completed match; Luna 111 and 15 respectively. Match-request cost per executed AP: Qwen 79/78=1.013; Luna 126/168=0.750. Lower requests/AP partly reflects two-AP actions and is not a tactical-quality score.

No dollar cost is inferred. Luna’s historical match telemetry records 292,433 input tokens, 5,486 output and 55,682 cached input. Qwen records 163,513 prompt tokens and 2,883 generated tokens. Latency sums exclude local overhead and the two historical preflights. Failed-prefix means underestimate the work required if longer matches begin surviving.

## 11. Terminology

| Term | Recommended report meaning |
| --- | --- |
| Transport-valid | Adapter accepted response envelope/content; not game legality. |
| Schema-valid | JSON and wire/application structure accepted; specify which layer. |
| Statically valid | parse_turn_plan returned, including AP and reference checks. |
| Current-catalog valid | Exactly one action matches current catalog; empty valid decisions reported separately. |
| Executed | Authoritative command applied and appears in replay trace. |
| Repaired | Initially invalid decision subsequently accepted after the single repair; report action or EndTurn. |
| Failed decision | No accepted decision after allowed request(s). |
| Failed match | Strict runner stopped without gameplay winner; not a team-elimination loss. |

Historical first_valid in the stepwise analysis means accepted first response after the full step validator, not merely parseable JSON. plan_valid is a boundary result, not an independent wire-schema test. Legal/selected denominators exclude rejected outputs, so 100% selected-action legality is compatible with frequent initial invalid decisions. Always retain initial-invalid, repaired-success and repaired-failure counts separately. Do not rewrite historical reports.

## 12. Cause assessment and options

Model output reliability is the observed bottleneck. A repair-feedback weakness is plausible because exact errors and rejected outputs are absent, but a specific failure mechanism is unproven. Contract layering is real: the full-turn wire schema allows up to five actions while the stepwise prompt/parser requires at most one; these records do not establish multi-action violations as the cause. Diagnostic category conflation and discarded rejected output limit attribution. No authoritative execution, replay, observation mismatch or fallback defect was found. Do not call this an implementation defect merely because the diagnostics are coarse.

| Option | Information gained | Tradeoff / conclusion |
| --- | --- | --- |
| A — frozen replication | Estimates end-to-end completion and both reliability layers without changing contract. | More failures may consume requests; identical Qwen paths reduce new information. Preferred bounded next run. |
| B — repair-feedback V2 A/B | Tests whether factual mismatch plus rejected decision improves conditional recovery. | Existing remedy already says copy catalog; cannot select a targeted change from missing raw outputs. Would change provider reliability contract and requires separate design/authorization. |
| C — invalid decision ends turn, battle continues; no repair | Measures tactics under recoverable decision faults and avoids whole-match censoring. | Changes benchmark/control semantics and unused-AP penalty; no longer strict reliability. Separate policy/version required. Not recommended next. |

## 13. Recommended next experiment (design only)

Choose **A as a bounded replication**, not an automatic large expansion. Proposed schedule: four model-vs-heuristic attempts per provider, two per side, alternating side order; eight intended attempts total, no replacement or retry, no self-play and no Qwen-vs-Luna. Preserve the actual V3 runner and every frozen model/prompt/schema/observation/repair/game contract. Use a new output directory and retain failed, unstarted and ceiling-stopped slots distinctly. Proposed ceiling: 400 requests/provider including preflight and repairs, 800 combined, subject to separate authorization. No authorization is implied here.

Primary outcomes: initial-invalid/initial decisions, repaired-success/initial-invalid, repaired-failure/initial-invalid, fatal decisions/initial decisions, and completed/intended matches. Secondary: decisions to first failure, failure category, per-side completion, executed AP, requests/AP, summed transport latency and terminal mechanism. Fixed schedule; no optional stopping for a favorable win. Integrity failures retain hard-stop rules. Report repeated deterministic paths as replication with limited state diversity, not independent samples.

Pilot model-vs-heuristic totals suggest a rough eight-attempt workload of 54 Qwen + 74 Luna = 128 match requests and about 128.4 + 120.0 = 248.3 transport seconds, before preflight/overhead; this doubles the two-attempt matchup observations and is not a ceiling forecast. Improved survival could increase exposure sharply. Keep request ceilings binding rather than promising completion.

Why not B now: the user’s proposed simple instruction is already present; missing outputs prevent showing one shared correctable error or an exact repetition pattern. A is less assumption-dependent for the next reliability estimate. Its limitation remains: unchanged telemetry will not recover the missing forensic detail. If mechanistic repair research becomes the priority, separately authorize an evidence-retention design before a repair A/B; do not quietly modify the frozen replication.

If B is subsequently selected, reserve **arena-step-repair-v1** for the current feedback and **arena-step-repair-v2** for a specified richer factual representation. These are proposed labels only, not existing manifest versions or implemented changes. Keep initial request byte-equivalent, use one repair in each arm and the same state/schema/model settings; preserve every initial-invalid event. Compare conditional repair recovery on a separately retained, sanitized fixed set of invalid-decision/observation pairs before full-match follow-up. Do not cherry-pick rescued cases or erase first-response failures. A benchmark provenance revision may be needed to record repair version; no such revision is made here.

## 14. Offline verification and artifacts

Verified 417 Phase 7D files against its original SHA-256 inventory; checked 89 frozen backend/source files against Phase 7D; reproduced all 8 full/partial traces and every turn boundary; rebuilt and hash-checked 189 current observations; reconciled command metrics, decisions and request ceilings. Step prompt hash remains `791f842d479527929f504c505254cd2d21dee668b2550f31cad5e7458b572d5f`. Provider/model profile artifacts, benchmark/probe artifacts and all historical observations remain covered by byte hashes. Existing user changes were preserved.

The analysis script installs an audit hook rejecting network connections/DNS and child-process launches; it imports domain replay and observation code only, never constructs providers or runs a benchmark. Zero live inference, probes, preflights, repairs or connectivity requests occurred. Command replay is offline verification, not a new full-match run. No full test suite was run because runtime packages were not edited.

Code evidence: [stepwise parser and repair feedback](../backend/aig/arena/ai/stepwise.py), [static validator](../backend/aig/arena/ai/validation.py), [repair message construction](../backend/aig/arena/ai/provider.py), [persistence filter](../backend/aig/arena/benchmark_provider.py), [wire/application schema](../backend/aig/arena/ai/contracts.py), [Ollama adapter](../backend/aig/arena/ai/ollama.py), [Luna adapter](../backend/aig/arena/ai/openai.py). Historical comparisons: [Phase 7C](arena-stepwise-expanded-results.md) and [Phase 5](../.local/arena-phase5-fullmatches-20260913-01/report.md).

Created: this document; `scripts/arena-phase7e-forensics.py`; `.local/arena-phase7e-offline-forensics-20260913/{preservation-before.json,failure-ledger.json,analysis.json,verification.json}`. verification.json records preservation counts and checks. The next experiment is neither implemented nor run.
