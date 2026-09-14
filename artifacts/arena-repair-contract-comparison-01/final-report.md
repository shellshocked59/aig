# Frozen Arena repair-only results

**36/36 requests completed: OLD 18, NEW 18. NEW valid repairs 17/18 (94.4%) versus OLD 7/18 (38.9%), a 55.6 percentage-point gain.**

All 18 pairs completed. Ten pairs changed from OLD invalid to NEW valid; none regressed from valid to invalid; seven were valid in both arms and one invalid in both. No retries, request 37, fallback, downstream planning, or match execution occurred.

The exact authorized live command and exact prepared analysis command both completed successfully. The frozen source, challenge cohort, arm payloads, schedule, provider configuration, and validators were not modified.

## Static repair outcomes

| Metric | OLD | NEW |
| --- | ---: | ---: |
| Valid | 7 | 17 |
| Repeated same error (frozen category) | 9 | 1 |
| New invalidity (frozen category; caveat below) | 2 | 0 |
| AP-valid | 15 | 18 |
| First-action range-valid | 7 | 17 |
| Reference-valid | 18 | 18 |
| Contains EndTurn, including invalid/suffix outputs | 7 | 6 |
| Immediate potential EndTurn escape | 5 | 1 |

All AP/range/reference denominators are 18. AP rates: 83.3%/100%; range rates: 38.9%/94.4%; reference rates: 100%/100%. All responses parsed; zero malformed/schema outputs or provider failures. Range checks concern the first action only; later execution-state changes were neither simulated nor penalized. The cohort has no original bad-reference, status, or LOS failure, so it does not establish improvement on those challenge types.

## Exact paired outcomes

M denotes Move; E denotes EndTurn. Actor/target IDs are literal frozen IDs. Each delta is (action count, planned AP) relative to that episode’s rejected proposal; EndTurn counts as an action but costs zero. V/I denotes statically valid/invalid. Categories are the unmodified prepared classifications.

| Pair | OLD output | OLD result | OLD delta | NEW output | NEW result | NEW delta |
| --- | --- | --- | --- | --- | --- | --- |
| R1-1 | M(actor,3,2) | V AMBIGUOUS | (+0, +0) | M(actor,3,2) | V AMBIGUOUS | (+0, +0) |
| R1-2 | attack(actor,enemy) | I REPEATED_SAME_ERROR | (+0, +0) | M(actor,3,2) | V AMBIGUOUS | (+0, +0) |
| R1-3 | M(actor,3,2) | V AMBIGUOUS | (+0, +0) | M(actor,3,2) | V AMBIGUOUS | (+0, +0) |
| R2-1 | snipe(actor,enemy); attack(actor,enemy); E | I NEW_INVALIDITY | (+0, -1) | M(actor,4,2); snipe(actor,enemy); E | V AMBIGUOUS | (+0, -1) |
| R2-2 | snipe(actor,enemy); snipe(actor,reserve) | I REPEATED_SAME_ERROR | (-1, +0) | M(actor,4,2); snipe(actor,enemy); E | V AMBIGUOUS | (+0, -1) |
| R2-3 | snipe(actor,enemy) | I NEW_INVALIDITY | (-2, -2) | M(actor,4,2); snipe(actor,enemy); E | V AMBIGUOUS | (+0, -1) |
| R3-1 | snipe(actor,enemy); snipe(actor,enemy); E | I REPEATED_SAME_ERROR | (+0, +0) | M(actor,4,2); snipe(actor,enemy) | V AMBIGUOUS | (-1, -1) |
| R3-2 | E | V ENDTURN_ESCAPE | (-2, -4) | M(actor,4,2); snipe(actor,enemy); E | V AMBIGUOUS | (+0, -1) |
| R3-3 | snipe(actor,enemy); snipe(actor,reserve) | I REPEATED_SAME_ERROR | (-1, +0) | M(actor,4,2); snipe(actor,enemy); E | V AMBIGUOUS | (+0, -1) |
| R4-1 | snipe(actor,enemy) | I REPEATED_SAME_ERROR | (+0, +0) | M(actor,4,2) | V AMBIGUOUS | (+0, -1) |
| R4-2 | E | V ENDTURN_ESCAPE | (+0, -2) | M(actor,4,2) | V AMBIGUOUS | (+0, -1) |
| R4-3 | snipe(actor,enemy) | I REPEATED_SAME_ERROR | (+0, +0) | M(actor,4,2) | V AMBIGUOUS | (+0, -1) |
| R5-1 | attack(actor,enemy) | I REPEATED_SAME_ERROR | (+0, +0) | M(actor,4,2) | V AMBIGUOUS | (+0, +0) |
| R5-2 | attack(actor,enemy) | I REPEATED_SAME_ERROR | (+0, +0) | M(actor,4,2) | V AMBIGUOUS | (+0, +0) |
| R5-3 | attack(actor,enemy) | I REPEATED_SAME_ERROR | (+0, +0) | attack(ally,enemy) | I REPEATED_SAME_ERROR | (+0, +0) |
| R6-1 | E | V ENDTURN_ESCAPE | (+0, -1) | M(ally,4,2) | V AMBIGUOUS | (+0, +0) |
| R6-2 | E | V ENDTURN_ESCAPE | (+0, -1) | E | V ENDTURN_ESCAPE | (+0, -1) |
| R6-3 | E | V ENDTURN_ESCAPE | (+0, -1) | M(ally,4,2) | V AMBIGUOUS | (+0, +0) |

Episode map: R1 DOWNED bounded replacement; R2 POSITION strict; R3 POSITION bounded initial; R4 POSITION stepwise; R5 FIREBALL bounded replacement; R6 FIREBALL stepwise.

## Classification limits and mechanical interpretation

The frozen classifier reports OLD 9 repeated errors and 2 new invalidities, versus NEW 1 and 0. **The two OLD NEW_INVALIDITY labels are category transitions, not newly introduced defects:** R2-1/R2-3 fix AP but retain the original out-of-range first Snipe, which the original AP rejection masked. At detailed-diagnostic level, all 11 OLD invalid repairs and the one NEW invalid repair repeat an existing range/AP defect; none demonstrates a newly introduced error class. The saved analysis is preserved unchanged.

Intent categories: OLD 2 AMBIGUOUS, 5 ENDTURN_ESCAPE, 9 REPEATED_SAME_ERROR, 2 NEW_INVALIDITY; NEW 16 AMBIGUOUS, 1 ENDTURN_ESCAPE, 1 REPEATED_SAME_ERROR. Both arms have zero EXACT_VALIDATION_FIX, VALID_SUFFIX_TRIM, or VALID_INTENT_PRESERVED. The conservative classifier does not recognize adding a movement prerequisite as intent preservation, so the 16 AMBIGUOUS results must not be presented as 16 proven intent-preserving repairs.

Observed structure nevertheless differs clearly: all six NEW POSITION full-plan repairs use Move(actor,4,2) followed by Snipe(actor,enemy), preserving the originally attempted first actor/target damage action and fitting 3 AP. All three NEW POSITION stepwise repairs use the same actor’s legal Move, consistent with the one-action limit. Other successful non-stop repairs move the original actor closer to the original target. These are observable structural relationships, not hidden-intent judgments or tactical-strength claims.

OLD contains EndTurn in seven outputs: five immediate valid escapes plus two suffixes in invalid plans. NEW contains EndTurn in six outputs: one immediate escape and five valid Move/Snipe suffixes preserving an original explicit EndTurn. Suffix EndTurns were not executed in this repair-only experiment and are not escapes.

Every flagged escape has a same-episode observed legal repair witness using the original actor and moving closer to the original target; witness slots are recorded in report-data.json. These demonstrate coherent positioning alternatives under the same cardinality/AP facts without requiring future damage. EndTurn remains valid, and the report does not infer why it was chosen.

The remaining NEW failure is R5-3: it changes the attacking unit from mage actor to knight ally, but the Attack remains out of range (distance 2, range 1). R6-2 remains an immediate EndTurn escape in both arms. No paired validity regression occurred, but these residual failures prevent claiming the problem is solved.

## Resources

| Quantity | OLD | NEW |
| --- | ---: | ---: |
| requests | 18 | 18 |
| input_tokens | 36288 | 44670 |
| cached_input_tokens | 26037 | 29744 |
| output_tokens | 735 | 882 |
| reasoning_tokens | 0 | 0 |
| total_tokens | 37023 | 45552 |
| mean_latency | 1.3964 | 1.8148 |
| median_latency | 1.2900 | 1.4021 |
| total_latency | 25.1344 | 32.6660 |
| mean_action_count_delta | -0.3333 | -0.0556 |
| mean_ap_plan_delta | -0.6667 | -0.5556 |

Latency values are seconds. The recorded timer includes the provider request plus local parsing/classification; transport-only latency is unavailable. Actual mean input tokens/request: OLD 2,016, NEW 2,481.667. Added input: 465.667/request (+23.10%), about 43.5 below the approximate 509.2-token preparation estimate. Total observed input was 80,958 versus the estimated 92,919; total input+output was 82,575. Cached input is a subset of input tokens, not an additional chargeable token count.

NEW added 8,382 input tokens and 147 output tokens across its 18 requests, for 8,529 additional total tokens. Mean recorded latency rose by 0.4184 seconds (+29.97%); medians rose from 1.2900 to 1.4021 seconds. Total recorded request latency was 57.8004 seconds, versus the preparation’s 47.12-second extrapolation. No dollar price is assumed.

## Integrity and next gate

The ledger, 36 unique provider request IDs, 36 unique response IDs, all result seals, pair/slot/payload bindings, and all static classifications reconcile. Source and prepared artifacts verify after the run. The 16,380-file historical preservation inventory remains byte-identical. No provider/model/profile, prompt, schema, observation, game rule, control, repair wording, or default was changed. Raw output fields are sanitized semantic JSON; exact provider bytes are represented by hashes, as frozen before execution.

**NEW clearly outperformed OLD on this frozen repair-only cohort**, primarily through improved static validity and fewer immediate EndTurn substitutions. This supports a separately authorized fresh 24-turn candidate-family validation using the new repair binding. The six repeated episodes are a small selected diagnostic cohort, not 18 independent positions or evidence of full-match tactical strength. Taxonomy limitations and the two residual NEW issues must carry forward.

Stopped after the authorized repair comparison and offline reporting. No promotion, new focused validation, prompt tuning, Qwen request, full match, or 300-match benchmark was started.

Evidence: [prepared analysis](analysis.json), [supplemental accounting/resources](report-data.json), [live completion seal](live/completion.json), [frozen manifest](manifest.json).
