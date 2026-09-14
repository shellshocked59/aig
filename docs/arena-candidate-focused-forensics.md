# Candidate focused validation: offline forensic audit

## 1. Executive finding

**The candidate family remains fundamentally sound, but freeze should wait for a narrowly scoped repair-contract correction and a separately authorized validation of that correction.** No evidence supports banning EndTurn, changing tactical policy, or redesigning the three controls. There is a demonstrable repair-input defect relative to the intended job of preserving intent: the repair request never includes the rejected plan. It also discards detailed static diagnostics and sends only a category. An intent-preservation sentence alone cannot restore information the request does not contain.

The 24 frozen trials contain 31 decisions and 37 provider attempts: 25 first responses passed static validation; six required repair, two repairs succeeded, and four failed. Final stops were 12 clean completions, three explicit EndTurns, two strict execution truncations, four provider failures, and three victories. All 24 traces and all 31 decision observations independently reverified offline. All 37 outputs were reparsed; 27 were accepted, ten rejected. No invalid plan was accepted.

The four failed trials contain **two repeated AP overruns and two repeated first-action legal-catalog mismatches caused by range**. No malformed JSON, wire-schema error, invented ID, transport error, or EndTurn-ordering failure occurred. POSITION full-turn outputs also have an initially out-of-range Snipe masked by the earlier AP check. The range failures expose a candidate-specific diagnostic weakness, while AP repair failures already occurred in V4/V5.

AP-005 bounded is a poor initial tactical stop, not a repair artifact. POSITION stepwise is an observable repair semantic collapse: proposed damage becomes immediate EndTurn, and the repair input omitted the original proposal. One such event cannot establish a general repair bias or prove that the model selected EndTurn *because* it was easy.

## 2. Evidence, method, and limits

Primary evidence is the entire [frozen validation directory](../artifacts/arena-candidate-focused/20260914-validation-v1), especially [final-report.md](../artifacts/arena-candidate-focused/20260914-validation-v1/final-report.md), manifest, schedule, 24 trial files, 37 request files, request ledger, completion seals, analysis, review-data, and delivery-integrity. The machine-readable [forensics.json](../artifacts/arena-candidate-forensics/20260914-audit-v1/forensics.json) contains every starting state, observation, raw and parsed response, reconstructed diagnostic, request linkage, exact reconstructed prompt/messages, costs, acceptance, execution invalidities, stop provenance, and token/latency metrics. The [offline audit script](../artifacts/arena-candidate-forensics/20260914-audit-v1/audit.py) installs a socket-connection denial guard, constructs no provider, and replays only saved commands.

The manifest's 62 primary evidence hashes, ledger hash, 84 source hashes, exact prompts, and all three wire schemas were independently checked against current bytes. The schedule was used to index the trials, not directory ordering. Each saved pre-send reservation was matched to its ledger entry, observation, command prefix, and eventual response. All 37 requests reconcile; no unexplained attempt, retry, fallback, or request after reached EndTurn appears. Accepted plans in the trial files agree with independent parsing. All 31 observations reproduce from command prefixes, including both bounded replans and all subsequent stepwise decisions.

**Evidence distinction:** frozen files contain raw responses, accepted plans and error categories, but not standalone full wire-request bodies or full rejected-plan diagnostics. Exact repair inputs here are reconstructed from the frozen observation, frozen prompt and hash-verified `provider.py`/`openai.py` code. Detailed diagnostics are recreated with that same parser. They are not represented as richer feedback that Luna actually received. `preceding_inference` in a request artifact is audit instrumentation, not an assistant message sent to the model. The provider sends no `previous_response_id`, uses `store=False`, and does not append its prior response to the next input.

Source review covered [candidate contracts](../backend/aig/arena/ai/benchmark_candidate.py), [shared strict/bounded/stepwise controller](../backend/aig/arena/ai/candidate_control.py), [provider repair path](../backend/aig/arena/ai/provider.py), [static validation](../backend/aig/arena/ai/validation.py), both transport adapters, contracts, observation conversion, authoritative commands, V5 AP guidance, the frozen POSITION witness, and [prompt/stop design](arena-benchmark-prompt-and-stop-semantics.md). No external research, LLM judge, model request, extra trial, or full match was used.

## 3. All 24 trials

Notation: `A` Attack, `S` Snipe, `B` Shield Bash, `F` Finish, `M` Move, `E` EndTurn. Defaults are `actor -> enemy`; other actors/targets are explicit. `w0` is the initial decision; `w1` is the first refreshed decision, not a static repair. `V` valid; `AP` AP-budget rejection; `LC` first-action legal-catalog mismatch (recorded as `invalid_reference`). Repair IDs below resolve to exact feedback and raw sequences in section 4. AP remaining is the acting player's AP **before** normal EndTurn resets the opponent's budget. Rejected plans execute no actions.

| Snapshot | Control | Start AP | First validity | First raw actions | Repair / feedback | Repair actions / validity | Accepted | Execution invalidity | End provenance | AP spent / left | Final stop | Requests | Replay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AP-001 | strict | 1 | V | A | no | — | yes | no | normal | 1 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| AP-001 | bounded | 1 | V | A | no | — | yes | no | normal | 1 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| AP-001 | stepwise | 1 | V | A | no | — | yes | no | normal | 1 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| AP-003 | strict | 3 | V | S, A | no | — | yes | no | normal | 3 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| AP-003 | bounded | 3 | V | S, E | no | — | yes | no | initial E | 2 / 1 | INTENTIONAL_END_TURN | 1 | exact |
| AP-003 | stepwise | 3 | V | S | no | — | yes; later yes | no | normal | 3 / 0 | CLEAN_PLAN_COMPLETE | 2 | exact |
| AP-005 | strict | 5 | V | S, S | no | — | yes | no | normal | 4 / 1 | CLEAN_PLAN_COMPLETE | 1 | exact |
| AP-005 | bounded | 5 | V | S, A, E | no | — | yes | no | initial E | 3 / 2 | INTENTIONAL_END_TURN | 1 | exact |
| AP-005 | stepwise | 5 | V | S | no | — | yes; later yes | no | normal | 5 / 0 | CLEAN_PLAN_COMPLETE | 3 | exact |
| MULTI-001 | strict | 2 | V | S | no | — | yes | no | normal | 2 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| MULTI-001 | bounded | 2 | V | S | no | — | yes | no | normal | 2 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| MULTI-001 | stepwise | 2 | V | S | no | — | yes | no | normal | 2 / 0 | CLEAN_PLAN_COMPLETE | 1 | exact |
| DOWNED-003 | strict | 2 | V | B, A | no | — | yes | w0: target outside action range | normal | 1 / 1 | EXECUTION_TRUNCATION | 1 | exact |
| DOWNED-003 | bounded | 2 | V | B, A | R1 w1 / F-LC | A / LC | yes; later failed | w0: target outside action range | none | 1 / 1 | PROVIDER_FAILURE | 3 | exact |
| DOWNED-003 | stepwise | 2 | V | A | no | — | yes; later yes | no | normal | 2 / 0 | CLEAN_PLAN_COMPLETE | 2 | exact |
| POSITION-002 | strict | 3 | AP | S, S(actor,reserve), E | R2 w0 / F-AP | S, S(actor,reserve) / AP | no | no | none | 0 / 3 | PROVIDER_FAILURE | 2 | exact |
| POSITION-002 | bounded | 3 | AP | S, S, E | R3 w0 / F-AP | S, S(actor,reserve), E / AP | no | no | none | 0 / 3 | PROVIDER_FAILURE | 2 | exact |
| POSITION-002 | stepwise | 3 | LC | S | R4 w0 / F-LC | E / V | yes | no | repair E | 0 / 3 | INTENTIONAL_END_TURN | 2 | exact |
| CORE-002 | strict | 1 | V | A(actor,red-core) | no | — | yes | no | none | 1 / 0 | TERMINAL | 1 | exact |
| CORE-002 | bounded | 1 | V | A(actor,red-core) | no | — | yes | no | none | 1 / 0 | TERMINAL | 1 | exact |
| CORE-002 | stepwise | 1 | V | A(actor,red-core) | no | — | yes | no | none | 1 / 0 | TERMINAL | 1 | exact |
| FIREBALL-003 | strict | 2 | V | B(ally,enemy), A | no | — | yes | w0: target outside action range | normal | 1 / 1 | EXECUTION_TRUNCATION | 1 | exact |
| FIREBALL-003 | bounded | 2 | V | B(ally,enemy), A | R5 w1 / F-LC | M(ally,(4,2)) / V | yes; later yes | w0: target outside action range | normal | 2 / 0 | CLEAN_PLAN_COMPLETE | 3 | exact |
| FIREBALL-003 | stepwise | 2 | V | B(ally,enemy) | R6 w1 / F-LC | A / LC | yes; later failed | no | none | 1 / 1 | PROVIDER_FAILURE | 3 | exact |

Every row's first raw actions are the whole first response, including rejected suffixes. An accepted initial plan can still have a later provider failure; the acceptance column explicitly distinguishes that situation. `normal` denotes controller-generated turn finalization, never an explicit model stop. Failed trials retain their committed prefix with no synthetic EndTurn. The three terminal trials issue no EndTurn. There are 14 normal finalizations, three explicit stops, and seven trials with neither (four failed, three terminal).

## 4. Six repair episodes

Exact feedback strings actually sent as the second **user** message:

**F-AP:** `Previous output failed validation (ap_budget). Return a corrected ArenaTurnPlan using the same observation and schema. No reasoning or commentary.`

**F-LC:** `Previous output failed validation (invalid_reference). Return a corrected ArenaTurnPlan using the same observation and schema. No reasoning or commentary.`

Every repair also receives the unchanged system instructions and the original user message `ArenaObservation:\n` followed by canonical observation JSON. Thus current AP, costs, board, units, ranges, and all current legal alternatives are available in that observation. Feedback itself supplies no AP number, total, field, action index, rejected value, range explanation, or legal alternative. **No repair receives its original raw/parsed tactical sequence or a valid prefix.** There is no explicit preserve-intent instruction. This is category-only replacement generation from the same state (option B in the requested taxonomy, operationally a new decision from scratch), identically inherited by candidate OpenAI and Ollama and by all three controls.

| ID | Decision | Requests | Current AP | Original | AP total | Invalidity | Feedback | Repair | AP total | Result | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | DOWNED-003-bounded w1 | 18 → 19 | 1 | A | 1 | LC | F-LC | A | 1 | LC | Repeated same invalidity |
| R2 | POSITION-002-strict w0 | 22 → 23 | 3 | S, S(actor,reserve), E | 4 | AP | F-AP | S, S(actor,reserve) | 4 | AP | Repeated same invalidity; E removed |
| R3 | POSITION-002-bounded w0 | 24 → 25 | 3 | S, S, E | 4 | AP | F-AP | S, S(actor,reserve), E | 4 | AP | Repeated same invalidity; target changed |
| R4 | POSITION-002-stepwise w0 | 26 → 27 | 3 | S | 2 | LC | F-LC | E | 0 | V | EndTurn escape |
| R5 | FIREBALL-003-bounded w1 | 33 → 34 | 1 | A | 1 | LC | F-LC | M(ally,(4,2)) | 1 | V | Valid; immediate intent changed, related positioning |
| R6 | FIREBALL-003-stepwise w1 | 36 → 37 | 1 | A(ally,enemy) | 1 | LC | F-LC | A | 1 | LC | Repeated same class; attacker changed |

For all four LC originals, the reconstructed diagnostic is exactly `category=invalid_reference, action_index=0, field_path=null, message="Response failed static validation.", rejected_value=null`. For both AP originals and their repairs it is `category=ap_budget, action_index=null, field_path="actions", message="Selected actions exceed current AP.", rejected_value=4`. These fields are **not** serialized into the repair input; only the category is retained.

R1 repeats the exact action and error; no shortening, new action, or stop. R2 retains both Snipe actors/targets and removes only the zero-cost EndTurn: three entries become two, gameplay count and cost remain two/four. R3 changes the second target from enemy to reserve; entry count, gameplay count, and AP remain unchanged. Neither is a successful budget correction; both retain the out-of-range first action. R4 replaces one Snipe with one EndTurn: gameplay count falls to zero and the identifiable damage objective disappears. R5 changes actor and action type from mage Attack to knight Move; it remains one gameplay action, costs one AP, and moves the knight toward the same enemy. This is a valid replacement with a changed immediate objective, plausibly related positioning, not a faithful local correction of the original mage attack. R6 changes attacker from knight to mage while retaining the target; one action and one AP remain, but the new actor is also out of range. It introduces a different invalid action instance, **not a new error class**.

Classification totals: zero clearly faithful successful local repairs; one valid but immediate tactical intent changed (R5); one EndTurn escape (R4); four repeated-same-class invalidities (R1/R2/R3/R6). Calling all changed outputs semantically unrelated would overstate the evidence: R5 closes distance to the same enemy, and R6 still proposes damage to it. Only R4 abandons the identifiable offensive objective entirely. Outcome success alone does not establish intent preservation.

## 5. Exact four failed-trial reconstructions

**DOWNED-003 bounded — requests 17, 18, 19; R1.** Start: 2 AP, blue knight `actor` at (2,2), enemy knight at (3,2), 6 HP; reserve cleric at (8,4), 11 HP. Initial `[B, A]` costs 2 and passes static validation. Bash spends 1 AP, deals 4 damage, leaves enemy ACTIVE at 2 HP and pushes it to (4,2). Execution rejects the planned Attack: `target outside action range` (distance 2, knight range 1). Bounded correctly starts one fresh decision with 1 AP. Both its original `[A]` and repair `[A]` are absent from the fresh legal catalog, hence LC rejection. All IDs and ownership are valid. The repair only sees F-LC, not the range explanation. Final result: `repair_failed` / `PROVIDER_FAILURE`, 1 AP spent, 1 remaining; Bash prefix preserved. A catalog Move to (3,2), for example, is a legal 1-AP positioning replacement toward the same target, but cannot also attack this turn. No legal immediate damage alternative is available. This is a repeated range error after correctly triggered bounded replan, not AP/schema/EndTurn failure.

**POSITION-002 strict — requests 22, 23; R2.** Start: 3 AP; ranger at (1,2); 8-HP enemy knight at (6,2); reserve cleric at (8,4), 11 HP. Original `[S(enemy), S(reserve), E]`: 2+2+0=4 AP. F-AP prompts repair `[S(enemy), S(reserve)]`: still 4 AP. Both fail `ap_budget` by 1; zero execution, zero automatic finalization. Both also begin with an out-of-range Snipe (distance 5, range 4), but AP validation returns first. Removing only EndTurn cannot save AP. Simply deleting the second Snipe would fix the sum while leaving an illegal first action. A valid tactical replacement exists: frozen `[M(actor,(3,2)), S(enemy)]`, cost 1+2=3, downing the enemy. This requires fixing the missing movement prerequisite, not merely trimming a suffix.

**POSITION-002 bounded — requests 24, 25; R3.** Identical starting state. Original `[S(enemy), S(enemy), E]`, repair `[S(enemy), S(reserve), E]`; both 4 AP against 3. Same AP rejection and masked first-action range defect as strict. Repair changes target, not budget. No initial plan was accepted, so **no bounded replan** was triggered. Zero execution and 3 AP remain; failure has no finalization. The same frozen Move/Snipe repair exists. EndTurn is legally ordered, costs zero, and is never reached; it is not the source of invalidity.

**FIREBALL-003 stepwise — requests 35, 36, 37; R6.** Start: 2 AP; mage `actor` at (2,2), knight `ally` at (3,2), 18-HP enemy knight at (4,2), reserve at (8,4). First decision `[B(ally,enemy)]` is accepted and executed: enemy loses 4 HP and is pushed to (5,2), leaving 1 AP. The next decision proposes `[A(ally,enemy)]`: distance 2 exceeds knight range 1. F-LC repair proposes `[A(actor,enemy)]`: distance 3 exceeds mage range 2. Both fail first-action membership; the repair has merely switched the invalid actor. No schema, reference existence, AP, LOS-obstruction, or EndTurn-ordering error occurred. A legal tactical replacement `[M(ally,(4,2))]` was actually accepted in the bounded arm at the identical post-Bash state. It recovers positioning, not damage within the remaining AP. Stepwise preserves the Bash prefix and finishes provider-failed, without EndTurn.

All four repairs repeat their original failure **class**. None introduces AP overbudget where the original was budget-valid. There is no deterministic evidence that repair must fail on these states: FIREBALL bounded succeeds on the same refresh state where stepwise fails. The shared loss of diagnostic and intent information is systematic in code; the specific sampled outputs and magnitude of their failure probability are not established as systematic. The retained four failed artifacts must remain failures in any future accounting.

## 6. EndTurn provenance and rates

| Reached stop | Provenance | Actions before / AP left | Remaining legal gameplay | Other arms | Assessment |
|---|---|---|---|---|---|
| AP-003 bounded | Initial output, request 5 | Snipe / 1 | Attack + 22 moves | Strict and stepwise Snipe then Attack | Debatable intentional stop; Attack gives 5 further damage (enemy 10 -> 5 HP), not a down or immediate win |
| AP-005 bounded | Initial output, request 9 | Snipe, Attack / 2 | Attack, Snipe + 22 moves | Strict two Snipes; stepwise two Snipes then Attack | Clearly poor stop under immediate mechanics; available 1-AP down, no observed repair involvement |
| POSITION-002 stepwise | Repair output, request 27 | None / 3 | 23 moves | Both full-turn arms fail AP repair; neither executes | Repair-induced loss of offensive intent; frozen Move/Snipe opportunity |

No first raw action among the 24 turn starts was EndTurn. The two initial-output explicit stops are suffixes. They are genuine model-selected EndTurns, not empty arrays or automatic finalization. POSITION's repair returns the direct valid action `{"type":"end_turn"}`. No request follows any reached stop.

Denominators matter:

| Measure | First response to a decision (31) | Repair response (6) |
|---|---:|---:|
| Contains a syntactic EndTurn, including rejected plans | 4/31 (12.9%) | 2/6 (33.3%) |
| Contains accepted/reached explicit EndTurn | 2/31 (6.5%) | 1/6 (16.7%) |
| EndTurn among valid outputs only | 2/25 (8.0%) | 1/2 (50.0%) |

The extra raw stops are the rejected initial POSITION strict/bounded plans and bounded's rejected repair. There are six raw outputs containing EndTurn but only **three actual explicit decisions reached**. At initial-turn level the reached initial-output rate is 2/24 (8.3%); among full-turn first responses across all waves it is 2/18. Stepwise has 0/13 reached initial-output stops and 1/2 repair-output stops. The full-turn repair denominator is four (none reached EndTurn). Conditioning on valid repairs selects only two successes, so 50% is particularly unstable. The observations are suspicious enough to examine the contract, not enough to infer a statistically reliable bias, compare rates to full matches, or causally attribute a stepwise stop preference.

## 7. AP-005 mechanical classification

All three controls use the same 5-AP starting state and observation. The ranger at (1,2) faces an 18-HP knight at (3,2). The board has no blocked/bonus tiles. Strict produces two Snipes (16 damage, 4 AP), then completes normally with the enemy still ACTIVE at 2 HP and 1 AP unused. Bounded produces Snipe plus Attack (13 damage, 3 AP), then explicit EndTurn with 2 AP unused and enemy ACTIVE at 5 HP. Stepwise produces Snipe, Snipe, Attack from fresh observations (5 AP; the final Attack downs the enemy). None of these three trials requires repair.

At bounded's stop, the ordinary ranger Attack is at distance 2 within range 3, has unobstructed LOS, costs 1 AP, and deals deterministic 5 damage on these plain tiles. It is in both the delivered starting legal catalog and the reconstructed stop-state catalog. Damage is HP-clamped and sets the knight DOWNED; there is no retaliation, friendly damage, movement, self-elimination, or attack-induced loss of position. EndTurn discards unused AP; it cannot bank those 2 AP. The enemy is not already downed or strategically removed.

**Classification B: clearly dominated tactical stop under the stated immediate mechanical comparison (Attack then stop versus stop).** The extra attack secures a down at unchanged friendly HP/position, with no current-mechanics downside found. This is not a theorem about every eventual opponent response or a universal rule to attack when a target can be downed. A downed target can later be revived and still occupies its tile. Also, the user summary's “remaining enemy” must not be read as the only ACTIVE enemy: the reserve cleric is still ACTIVE at (8,4). The down therefore does not immediately win this snapshot. It is nevertheless a concrete positive outcome, not AP-filling.

Keep this as observed model behavior and monitor it separately from repair. Strict's implicit clean completion likewise leaves an available down, showing that removing explicit EndTurn would not remove all premature stopping. Bounded uses the **identical** system prompt and first observation as strict; its suffix difference cannot be caused by a distinct bounded policy sentence or replan context at this first call.

## 8. POSITION mechanical classification

Original stepwise action is Snipe(`actor`,`enemy`), cost 2 against 3 AP. IDs, ability, target ownership and ACTIVE status are correct. Distance from (1,2) to (6,2) is 5; Snipe range is 4. The board has no LOS blocker; failure is range, recorded generically as LC/`invalid_reference`. The current catalog contains 23 Moves and EndTurn, no legal Snipe. The model received movement range 3, Snipe range 4/damage 8, enemy HP 8, all positions, and Move(3,2). It did **not** receive the frozen two-action witness or a precomputed “move-and-snipe opportunity.” Repair had the facts needed to derive that line; we cannot claim it knew the line.

The frozen [literacy fixture](../backend/aig/arena/benchmark_artifacts/arena-tactical-literacy-v1.json), POSITION-002, records `[Move(actor,(3,2)), Snipe(actor,enemy)]`, cost 3, no failure, and enemy down. Only its first Move appears in the current legal catalog; future Snipe becomes legal after movement. Stepwise must return just the Move, then receive fresh state. Returning both actions in its repair would violate its cardinality contract. Strict and bounded propose Snipe-related damage from the same start, but **neither proposes the prerequisite movement**, and neither accepts or executes a line.

**Classification: repair semantic collapse at the observed output level, with a demonstrated contract contributor.** A recognizable attempt to damage the enemy becomes no gameplay action and immediate EndTurn. Repair has no rejected sequence to preserve and is asked only for a corrected plan. This is not proof of hidden motivation, nor proof that retaining the sequence would have prevented the stop. It is distinct from an unprompted initial tactical decision to stop. A related legal first move exists, but choosing it is still a model decision; the wrapper must not implement a tactical similarity engine or force that line.

## 9. All four AP-overbudget outputs

| Trial / request | Stage | Raw sequence | Costs | Available / total / excess | Rejection |
|---|---|---|---|---|---|
| POSITION strict / 22 | Initial | S(enemy), S(reserve), E | 2+2+0 | 3 / 4 / 1 | ap_budget |
| POSITION strict / 23 | Repair | S(enemy), S(reserve) | 2+2 | 3 / 4 / 1 | ap_budget |
| POSITION bounded / 24 | Initial | S(enemy), S(enemy), E | 2+2+0 | 3 / 4 / 1 | ap_budget |
| POSITION bounded / 25 | Repair | S(enemy), S(reserve), E | 2+2+0 | 3 / 4 / 1 | ap_budget |

All four receive the exact V6 system prompt reproduced in section 11, `action_points_remaining: 3`, and `action_costs.snipe: 2` / `end_turn: 0` in the same canonical observation. Repair adds only F-AP. `forensics.json` records the exact reconstructed messages per request. There is no stale AP value, ambiguous per-unit budget, hidden AP replenishment, or omitted cost. The wire schema cannot enforce the cross-action sum against observation AP; static validation enforces it. These 4-AP plans fit the historical five-AP schema envelope, so the correct current-budget rejection is `ap_budget`, not a wire-shape error.

The candidate retains V5's complete-budget and running-total instruction. Compliance is an observed residual model arithmetic/constraint-following problem, not evidence that the guidance vanished. Repair's failure to expose the rejected 4-AP sequence and quantitative diagnostic is an avoidable weakness. Removing E in strict is an observed ineffective edit, but because the prior output was absent from the request we cannot infer Luna deliberately attempted that local edit.

There are two overbudget first responses among 31 decisions (6.5%), both in the 16 full-turn initial plans (12.5%); including the two bounded replacement decisions gives 2/18 full-turn decisions (11.1%). All four overbudget outputs including repairs are 4/37 requests. Stepwise's maximum-one-action shape naturally reduces opportunities for summed-cost errors; this is intended cardinality asymmetry, not evidence of superior budgeting policy. Do not compare these denominators as a regression estimate against V5's 10/122 initial decisions. Both candidate AP failures are the same deliberately selected POSITION state.

## 10. Repair contract, EndTurn escape, and static/replan boundary

EndTurn is an especially easy valid output in a nonterminal active-player decision: zero AP, no unit/target/position fields, no range/LOS/ownership reference, and legal regardless of remaining AP. A singleton E trivially satisfies ordering and cardinality. Empty arrays also remain a zero-action valid completion escape, including historically; explicit EndTurn is not the first way the system can accept passivity. The schema does not optimize for such an action, but category-only correction leaves validity as the sole explicit repair objective. This structurally permits validity-seeking semantic collapse. The sample demonstrates one instance, not a general optimization law.

The provider's comment is explicit: `Same observation/schema, no raw output echo or exception text.` Rich `RepairValidationFailure` exists, but this candidate does not use the separate rejection-evidence/repair-message hooks. Both candidate transports inherit the same generic repair methods. There is no hidden control-specific intent preservation. OpenAI keeps the system prompt as instructions; Ollama would prepend it as a system message. No Ollama behavior was sampled.

The candidate adds symmetric first-action catalog validation beyond historical full-turn parsing. That correctly rejects immediately illegal range/status/occupancy actions, but labels a range mismatch `invalid_reference` even when IDs are valid. A repair told only “invalid_reference” cannot distinguish a nonexistent target from a valid target out of range. This is a contract/feedback artifact worth fixing; it is not an argument to weaken the legality check. AP failure precedes membership checking, so POSITION full-turn feedback currently conceals an additional initial-state range error. Feedback should accurately explain detected invalidity without simulating an entire planned future.

The intended boundary is respected in execution: static repair uses the same observation and cannot roll back already committed actions. Later full-turn actions are not required to belong to the starting catalog, because earlier movement/damage may alter legality. DOWNED and FIREBALL Bash/Attack plans are statically acceptable and fail only after Bash pushes the target; strict truncates, bounded refreshes once. Bounded's refreshed invalid Attack is then a **new static repair episode within the replacement decision**, not a second bounded replan. Stepwise's refreshed bad Attack is also caught before execution. Both bounded refreshes occurred for genuine execution invalidity, and one recovered 1 AP through repaired movement. Neither clean completion nor explicit EndTurn triggered replan.

## 11. Exact prompt and wrapper comparison

V5 AP text:

```text
The observation's action_points_remaining is the complete AP budget for this plan.
Keep a running total of action costs. Before adding each action, ensure its cost
fits within the AP still remaining. The total cost of all planned actions MUST NOT
exceed this budget. You may return a shorter plan if no worthwhile legal action
fits the remaining AP.
```

Candidate core AP text:

```text
action_points_remaining is the complete AP budget for this decision/plan.
Keep a running total of action costs. Before adding each action, ensure its cost
fits within the AP still remaining. Total planned cost MUST NOT exceed this budget.
```

The budgeting requirement is semantically equivalent. It moves from V5 line 3 to candidate line 6, following objective/observation/sequencing facts, but remains near the start and before game-rule detail. The middle running-total sentences are unchanged. Candidate “several actions may be worthwhile” and “no further action worthwhile” preserve productive-action permission while permitting explicit judgment to stop; they do not require AP exhaustion. This does not prove equal behavioral salience.

One real salience difference: V5 repeats numerical action costs and several damage/range values in the system prompt; candidate says to use supplied costs/ranges and places the numbers in the observation's explicit cost/rule maps. Information is retained, repetition is reduced. That could affect a model, but this eight-state sample cannot causally attribute either budgeting error to it. No wrapper-specific AP dilution is found. Reintroducing broad policy text or V4 sequencing checklists is not justified.

| Property | V5 | Strict / bounded V6 | Stepwise V3 |
|---|---|---|---|
| Characters / UTF-8 bytes | 2005 | 2046 | 2052 |
| AP rule | Complete budget, running total | Shared core, same requirement | Identical shared core |
| Rule ordering | AP before objective | Common core before wrapper | Same core ordering |
| Stop meaning | Automatic finalization; short plan allowed | Explicit E or clean empty/short completion | Same E; empty completion also accepted |
| Output cardinality | 0–5 gameplay actions | 0–5 gameplay plus optional last E | At most 1 action, including E |
| Refresh statement | Whole plan execution | Commit until completion/E/victory/invalidity | Fresh observation after successful step if AP remains |

Strict and bounded have byte-identical prompts. Candidate full-turn and stepwise differ only in the final wrapper, by six bytes in total length. There is no separate bounded “recover aggressively” or “stop early” instruction. Stepwise explains that another decision follows a successful action; this is necessary control information but may influence choices. Both wrappers inherit “several actions may be worthwhile”; stepwise's one-action output constraint scopes what may be returned now. Empty arrays are schema-valid even though stepwise prose asks for “the single next action or end_turn”; that small wording gap exists but no empty output occurred, and it does not explain these failures. Align its description at a future version boundary only if changing that contract is otherwise warranted.

Exact frozen V6 instructions (core followed by full-turn wrapper):

```text
You control one team in a perfect-information fantasy tactics battle.
Use the authoritative observation, rule facts, and legal actions. Win by destroying
the enemy Core or leaving the enemy with no ACTIVE units. Use supplied IDs,
positions, and ability names. Legal actions describe the current observation;
actions execute in order and earlier actions can change later legality.
action_points_remaining is the complete AP budget for this decision/plan.
Keep a running total of action costs. Before adding each action, ensure its cost
fits within the AP still remaining. Total planned cost MUST NOT exceed this budget.
Use the supplied costs, ranges, damage, status, movement, and bonus rules.
Movement is eight-directional and cannot pass occupied/blocked tiles or cut blocked
corners. Ruins block ranged line of sight. DOWNED units occupy tiles and cannot act.
Attack targets an ACTIVE enemy or enemy Core; special abilities cannot damage Cores.
Heal targets ACTIVE allies, including self; Finish removes an adjacent DOWNED enemy;
Revive restores a DOWNED ally, which can act immediately. Shield Bash can push its
target if the destination is free. Fireball affects ACTIVE units in its area,
including allies and caster; if both teams lose all ACTIVE units, the caster loses.
Choose useful legal actions for the current tactical situation; several actions
may be worthwhile. You may explicitly end_turn with AP remaining when you judge
no further action worthwhile. Do not add meaningless or speculative actions merely
to consume AP. end_turn costs 0 AP and must be last; victory stops execution before
any later action. An empty or short plan without end_turn is plan completion,
not an explicit intentional stop. Output only the required structured plan.
No reasoning, explanation, or commentary.
Return ArenaTurnPlan with zero to five gameplay actions for the remaining turn,
optionally followed by end_turn. Follow schema_version=arena-turn-plan-schema-v2.
Execution commits valid actions until completion, end_turn, victory, or invalidity.
```

Exact stepwise wrapper (the preceding core is identical):

```text
Return ArenaTurnPlan with the single next action or end_turn (at most one action).
Follow schema_version=arena-turn-plan-schema-v2. After a successful gameplay action,
if AP remains, you receive a fresh authoritative observation for the next decision.
```

**The 7/8 match:** AP-001 Attack, AP-003 Snipe, AP-005 Snipe, MULTI-001 Snipe, POSITION-002 Snipe, CORE-002 Attack(core), FIREBALL-003 Bash(ally) match exactly across all three first raw responses. POSITION's matching proposal was rejected in all arms. The sole mismatch is DOWNED-003: strict/bounded Bash(actor,enemy), stepwise Attack(actor,enemy), each 1 AP. Bash deals 4 and pushes the 6-HP enemy, leaving 2 HP out of reach; Attack deals 6 and downs it in place, allowing the next Finish. They are not mechanically equivalent. Target and AP cost match across all eight snapshots; strict/bounded first raw actions match 8/8. No refresh had occurred at these first calls. Nondeterminism and output-cardinality/wrapper effects remain confounded; one response per arm cannot establish which caused the difference. Identical strict/bounded inputs yielding different stop suffixes reinforce the need not to overattribute differences to wrapper policy.

## 12. Observation and action-schema comparability

| Snapshot | Strict = bounded = stepwise | Canonical observation SHA-256 |
|---|---|---|
| AP-001 | yes | `ffcbf87208fc8918b89238ff002969a637c374fdfb0b0afdcf25702be671ccf4` |
| AP-003 | yes | `54dc8721d2e3565dec3b26b1083cfc54a95facf58d9fbda3d56dcf2233916495` |
| AP-005 | yes | `063ead27299e8b082a058b5bd9421d075b849ad21982b14d7f400507b422dfd4` |
| MULTI-001 | yes | `e014337f98841ff345ddf0ad50d555674ad1bf196370f38e488d102e1bd565a1` |
| DOWNED-003 | yes | `e4de37b63b1f7a27975f594e1282f3f70da9572a790b65e201b2695800b04dac` |
| POSITION-002 | yes | `24b0be07ef9b166c42428cf4a38fd13061b2bfb2a0c7b864ee02a2d1113f3b0c` |
| CORE-002 | yes | `1141b11b0a0e604739856d519c126bab30782b269866c1f69530fdd6d760bba8` |
| FIREBALL-003 | yes | `94ec863f1b1a590b9634ff2f258a2e8e52337063035454eef8fdeddde1471956` |

All eight initial states and full canonical observation contents are equal across strict, bounded, and stepwise—not merely selected tactical fields after lossy normalization. No tactical fact differs; only outer control binding/output schema/prompt wrapper does. Candidate V4 observation consistently derives from the compact V2 facts, labels the legal catalog `current_observation`, adds explicit EndTurn and a shared action cost map. All 31 observations, including refreshes, were independently rebuilt from committed command prefixes. Updated observations legitimately differ after different actions; that is the experimental intervention.

**Version naming correction:** the actual frozen schema identifier is `arena-turn-plan-schema-v2`. The request's `arena-action-schema-v2` is a descriptive label, not a separate literal binding found here. All arms use the actual V2 plan schema and identical semantic action variants. Stepwise is still an ArenaTurnPlan **array**, restricted to at most one entry, not a distinct naked-action JSON object. Normalizing only `properties.actions.maxItems` from 1 to 6 makes its saved OpenAI wire schema exactly equal to strict/bounded. No dynamically narrowed target schema is applied to one arm.

Full-turn permits six entries to accommodate five gameplay actions plus zero-cost E; the application validates at most five gameplay actions, total AP, and at most one E last. The wire schema handles field shape and cardinality, not AP sum or EndTurn ordering. Both transports use the same logical branches; OpenAI transforms discriminator constants to enums and oneOf to anyOf. Every observed raw output had valid shape, including correctly placed EndTurn suffixes in rejected plans. All arms share the same first-action catalog check; full-turn suffix legality remains authoritative execution's job. E advances the turn once, preserves pre-stop AP telemetry, and is suppressed after terminal victory. It does not create schema ambiguity in this evidence.

Controls therefore remain sufficiently comparable as a **candidate design**, with intentional differences in action cardinality, observation timing, call count and repair opportunities. Repair semantics must be explicit before interpreting a full-match comparison: repeated repair opportunities can change policy exposure differently by arm even when shared code is identical. Stepwise never requests another action at zero AP; full-turn may syntactically append E after spending all AP. Do not compare raw EndTurn counts without AP/provenance conditioning. No observation or schema-equivalence blocker was found.

## 13. Failure probabilities, telemetry, and historical repair comparison

| Control | Trials | Decisions | Invalid first responses | Repairs succeed / fail | Failed trials | Requests |
|---|---:|---:|---:|---:|---:|---:|
| Strict | 8 | 8 | 1 AP | 0 / 1 | 1 | 9 |
| Bounded | 8 | 10 | 1 AP + 2 LC | 1 / 2 | 2 | 13 |
| Stepwise | 8 | 13 | 2 LC | 1 / 1 | 1 | 15 |
| Total | 24 | 31 | 2 AP + 4 LC | 2 / 4 | 4 | 37 |

Initial-turn first responses are invalid in 3/24 (POSITION in all three controls). Across all decisions, invalid-first probability is 6/31 (19.4%), repair is attempted for every one, and conditional repair failure is 4/6 (66.7%). AP repairs fail 2/2; LC repairs fail 2/4. Decision-level final failure is 4/31 (12.9%); trial-level is 4/24 (16.7%). These are empirical fractions from selected dependent snapshots, not a calibrated full-match probability. Bounded and stepwise incur failures after a successful prefix, so the first-turn validity rate alone understates their failure exposure. Do not multiply/extrapolate these fractions into 300-match predictions.

| Historical cohort | Initial decisions | Repairs | Success / failure | Initial repair category |
|---|---:|---:|---:|---|
| V1 literacy | 122 requested | 18 | 18 / 0 | AP for all 18 |
| V4 literacy | 122 | 7 | 6 / 1 | AP for all 7 |
| V5 literacy | 122 | 10 | 9 / 1 | AP for all 10 |
| Candidate focused | 31 decisions in 24 turns | 6 | 2 / 4 | 2 AP, 4 LC |

Counts were independently recovered from saved `*/telemetry.json` in `.local/arena-luna-tactical-literacy-01`, `...-prompt-v4-01`, and `...-prompt-v5-01`, and cross-checked against the [three-way report](../.local/arena-luna-tactical-literacy-prompt-v5-01-analysis/three-way.md). V1 has an extra no-request ceiling-denial result row; that is not a 123rd provider decision. V4's failed repair is `01-REVIVE-001`; V5's is `03-REVIVE-001`. Both saved attempt-output pairs are Attack(enemy) + Revive(ally), cost 3 against the 2-AP observation, unchanged after AP feedback. Thus repeated AP-invalid repair predates V2 and EndTurn.

The candidate first-action membership check moves some range failures into static repair that historical full-turn parsing would have deferred to execution. Historical repair cohorts therefore test mostly budgeting, while four of six candidate repairs test current-action legality after a poor initial proposal or changed state. Prompt/observation versions, cardinalities, exposure, repetition counts and snapshot distributions also differ. Candidate repair success is concerning, but these cohorts cannot isolate a schema-V2 regression. The legacy generic repair path was successful often, not guaranteed to be intent-preserving.

Recorded totals remain 73,825 input tokens (27,906 cached, a subset), 1,634 output tokens, 75,459 total; request wall time sums to 54.740 seconds. No reasoning tokens are reported. Per-control request counts are 9/13/15 and request wall seconds 15.829/17.511/21.400. Every attempt has raw output and usage; nothing indicates truncation or transport exhaustion. The fixed strict→bounded→stepwise ordering affects caching; bounded's large cached share is not an intrinsic efficiency finding. The audit retains per-attempt latency/metrics in JSON rather than inventing a server-only or reasoning-time measure.

## 14. Decision matrix and smallest correction

| Observed issue | Decision | Mechanical/contract basis | Minimum response |
|---|---|---|---|
| AP-005 initial bounded stop; strict clean short plan | KEEP AS MODEL BEHAVIOR; monitor | Legal choices, poor available-down outcome, no repair involvement | Preserve evidence and stop taxonomy; no lethal heuristic |
| AP-003 initial stop | KEEP AS MODEL BEHAVIOR | Some damage forgone; no demonstrated hidden contract defect | Record opportunity cost without AP-maximization rule |
| POSITION repaired stop | FIX BEFORE BENCHMARK: repair contract | Original offensive proposal omitted; repair accepts semantically unrelated stop | Give repair the rejected structured decision and state intent-preservation objective |
| Generic `invalid_reference` for range mismatch | FIX BEFORE BENCHMARK: feedback | Valid IDs misdescribed, detailed/action-specific context not sent | Explain first-action catalog mismatch with action/index and existing static facts |
| Repeated AP-invalid repairs | FIX deficient repair input; MONITOR residual budgeting | Both failed to reduce 4 AP to 3; same class exists historically | Include current AP, computed costs/total and rejected plan; no core tuning |
| EndTurn as cheap validity escape | FIX repair objective/input; MONITOR frequency | Always-valid simple action in active nonterminal state, one observed escape | Preserve E as strategic option; do not ban it or require AP exhaustion |
| Bash-induced stale suffixes | KEEP experimental control behavior | Earlier authoritative action changes range | Preserve strict truncation/bounded refresh boundary |
| FIREBALL repaired Move | KEEP legal model replacement; monitor intent | Valid forward positioning but changed actor/action | No tactical similarity engine; report semantic change |
| DOWNED first-action mismatch | MONITOR | Bash and Attack differ mechanically; nondeterminism/cardinality confounded | Do not add wrapper-specific tactical advice |
| Observation, schema, request accounting, replay | KEEP | Equality and replay independently pass | Retain frozen bindings and verification |
| 4/24 trial failures | HOLD full-match freeze pending narrow repair validation | Large selected-sample exposure plus a concrete repair-input weakness | Do not extrapolate rate or discard failed prefixes |

**Smallest coherent correction to explore:** an explicitly versioned, shared candidate repair contract, retaining one repair and the same observation/schema. Supply the rejected **structured** plan as inert data, plus action-specific static diagnostic information (for AP: current budget, planned sum and costs; for first-action mismatch: offending action/index and clear current-catalog mismatch). Ask to preserve original tactical intent and valid parts where possible while satisfying the contract, and not to choose EndTurn merely as the easiest valid replacement. Do not claim a prefix is valid unless actually established; POSITION has no legal first-action prefix. Do not echo arbitrary exception text as instructions or add hidden tactics.

The priority is repair-contract clarification, but it requires minimal serialization of the missing rejected decision to be meaningful. A sentence alone is insufficient to preserve an unseen plan. Existing validation structures can supply some diagnostics; the candidate membership error needs a clearer semantic explanation. These are a single narrow repair-boundary intervention, not a prompt-core redesign. No wrapper alignment or core change is currently justified. Keep explicit EndTurn and empty completion semantics versioned and unchanged. No “always attack,” forced movement, extra repair allowance, target priorities, or model/profile change is recommended.

This audit supports **repair should preserve intent, not silently replan tactics** as an objective, with limits: infeasible intent cannot always be preserved, and a stepwise response cannot return a two-action line. “Preserve where possible” must never override legality/cardinality or promise tactical optimality. The evidence supports exploring simple wording **with the missing input**, not claiming it is sufficient to fix behavior before testing.

## 15. Exact next experimental step and preservation

Next, seek separate authorization to implement only that shared, versioned repair-input/feedback clarification, with offline payload checks for all six frozen rejection episodes. Those checks should verify the actual messages contain rejected actions, appropriate AP/catalog diagnostics, unchanged state and schema, and no extra request budget. They should assert no specific tactical output and make no provider calls. Review the concrete message diff before any live validation.

If then separately authorized, freeze a paired repair-only diagnostic: six saved invalid-first-response episodes × two repair contracts (current versus proposed) × three prespecified repetitions = **36 repair requests**, one response per slot, same Luna profile, same saved observation/schema and rejected proposal per episode, no retries/fallback or downstream decisions, no full matches. Freeze order, request ceiling, new output directory and analysis before sending. Compare validity, repeated/new invalidity, EndTurn provenance and mechanical relationship to original actions; do not model-judge or tune against individual preferred moves. These are conditional recommendations, not authorization or an experiment run in this audit.

A successful repair-only screen would still require a separately approved fresh matched 24-trial candidate validation to check controller integration and revised stop provenance before full-match freeze. Do not run it automatically after the 36-slot screen. Repair-only reuse isolates the boundary; it does not measure full-match strength or establish the future match-failure probability. Only after reviewing those results should the final family and failure-adjudicating full-match runner be frozen for a separately authorized study. No numerical success threshold is retroactively imposed on this frozen sample.

Preservation verified **4,567 existing files unchanged**, including current/historical source and the inspected frozen evidence. The original live run's separate 423-file preservation inventory and all 8 delivery-integrity hashes also match. The audit baseline covers backend, docs, scripts, tests and artifacts (excluding bytecode caches), plus the existing `.local/arena-luna-tactical-literacy*` evidence trees; the historical `.local` inventory was added before inspecting those trees and no audit writes occurred there. All newly created files in the scanned source/evidence roots are confined to this report and the additive forensic directory. The user's pre-existing dirty files remain byte-identical. Details: [preservation-verification.json](../artifacts/arena-candidate-forensics/20260914-audit-v1/preservation-verification.json).

An additional independent check against the earlier candidate preservation inventory verified **13,842 historical evidence files byte-identical**, with zero mismatches or unreadable/missing files. This is a pre-existing inventory comparison, not a retroactive audit-start baseline. See [historical-preservation.json](../artifacts/arena-candidate-forensics/20260914-audit-v1/historical-preservation.json).

Stopped after the forensic report. **Zero live inference, zero OpenAI/Ollama requests (including connectivity probes), zero additional trials, zero full matches, and zero runtime/source/prompt/schema/repair changes occurred.** Only this document and additive forensic artifacts were created.
