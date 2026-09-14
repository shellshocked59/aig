# Halfway decision — INTERIM, 50 matches/control

**PASS FOR CONTINUATION unchanged. Recommend Batches 6–8 as the next authorization scope, retaining separate frozen gates. Execution stopped after Batch 5; this recommendation does not authorize or execute any later batch.**

The study is halfway complete: 150 of 300 intended matches. Batch 4 passed the separate mechanical gate before Batch 5 began. All 150 cumulative matches passed exact replay, request accounting reconciled with zero pending requests, and prior roots were preserved. The frozen source/runtime/contract, exact schedule, side/control/model/opponent bindings, seals and no-fallback checks passed. [Final gate](batch-5-gate.md) records the verified counts and hashes.

| Cohort | Strict W/L/no-result; requests | Bounded W/L/no-result; requests | Stepwise W/L/no-result; requests |
| --- | --- | --- | --- |
| Batch 4 | 0/10/0; 54 | 0/10/0; 85 | 0/7/3; 545 |
| Batch 5 | 0/10/0; 55 | 0/10/0; 91 | 0/9/1; 283 |
| Cumulative | 0/50/0; 347 | 0/50/0; 408 | 2/40/8; 1825 |

## Seventeen halfway questions

1. **Is the benchmark mechanically healthy?** Yes on the observed evidence: all 150 replays and the required gates passed. All 60 newly authorized matches are sealed, and no later match was started. No prompt, schema, repair, control, opponent, rules, cap or analysis definition was tuned.

2. **Is Bounded recovering stale plans reliably?** It replanned 99 times and recovered at least one AP on 88 (88.89%), recovering 172 AP in total. Mean/median recovery is 1.737/2 AP per replan. This measures mechanical recovery, not match quality.

3. **What is Bounded's real premium?** Totals are 408 versus Strict's 347: a signed difference of +61 (17.58%), or 8.160 versus 6.940 per match. Per attempted Luna turn the rates are 1.830 versus 1.324, a 38.14% premium. Different trajectories, match lengths and forfeits affect totals. Signed extra requests divided by recovered AP is 0.3547, descriptive and not causal.

4. **Has Bounded improved outcomes over Strict?** Observed W/L/no-result is 0/50/0 versus 0/50/0; win difference is +0. Repair-exhaustion forfeits are 17 versus 10; Luna Core damage is 5 versus 0. Final execution truncations are 14 versus 119, with truncation-derived AP 27 versus 317. Recovery alone cannot substantiate the bounded outcome/reliability thesis. The frozen paired comparisons remain interim and descriptive.

5. **How frequent are second invalidities?** 14/99 replans (14.14%). Counts/rates by batch: 1: 4/26; 2: 2/17; 3: 3/14; 4: 3/23; 5: 2/19. No acceptability threshold was frozen; these failures remain data under the one-replan limit.

6. **How important are repair forfeits?** There are 31/150 (20.67%) cumulatively, with batch counts [2, 7, 8, 5, 9]. They directly determine recorded losses without natural terminal outcomes. The outcomes without these failures are unknown; no failed game was retried or manually repaired. Counts across five small batches do not by themselves establish a temporal trend or stochastic cause.

7. **Which controls are affected?** strict: 10/50 matches (20.00%), repair success 75/85 (88.24%); bounded: 17/50 matches (34.00%), repair success 69/86 (80.23%); stepwise: 4/50 matches (8.00%), repair success 76/80 (95.00%). Different decision exposure and game duration preclude equating raw counts with a causal control effect. Full first-response denominators are reported separately.

8. **Are failures dominated by range/LOS references?** 26/31 exhausted repairs carry the descriptive static range/LOS tag (83.87%). Classification counts: `{"STATIC_RANGE_OR_LOS": 26, "AP_VIOLATION": 4, "OTHER_CURRENT_ACTION_VALIDATION": 1}`. The official invalid_reference label is broad and can reject a current first action with valid IDs but invalid geometry. AP/schema failures and ambiguous move diagnostics remain separate. The retained initial/repair structured output, validators and receipt evidence support the classification without hidden reasoning or unredacting unknown IDs.

9. **Does Stepwise's long tail persist?** Yes descriptively: sorted request counts are `[2, 2, 4, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 17, 17, 18, 18, 21, 22, 24, 24, 24, 28, 36, 36, 42, 140, 140, 140, 140, 140, 140, 140, 140]`; mean 36.500, median 16.0, and uncapped mean 16.786. Uncapped games include early forfeits. The capped-game trace table records repeated unit downs, revivals and healing; these prolonged matches repeatedly incur observation/decision cost. Those trace facts do not prove model intent or a general causal explanation.

10. **How often is Stepwise capped?** 8/50 (16.00%) at exactly 140 requests. Cap IDs and sides: MATCH-001-stepwise red, MATCH-009-stepwise red, MATCH-015-stepwise red, MATCH-021-stepwise red, MATCH-031-stepwise red, MATCH-033-stepwise red, MATCH-037-stepwise red, MATCH-047-stepwise red. Each retains a nonterminal final state and no winner; natural uncapped outcomes are censored. The final Core/unit states and hashes are available in cap-details.json.

11. **What share of Stepwise spending comes from caps?** 1120/1825 requests, or 61.37%. The cap remains fixed; this concentration is an observed operational result, not a reason to increase it.

12. **Is Stepwise's outcome advantage commensurate with cost?** It has 2 wins versus Bounded's 0 and Strict's 0. Its W/L/no-result is 2/40/8. Costs are 1825 requests, 4,623,631 tokens and 2835.63 provider seconds, versus Bounded's 408, 1,143,654 and 717.50. Per turn, Bounded uses 40.05% fewer requests. No value threshold was frozen for deciding whether an outcome gain justifies that cost. Broad Wilson intervals, caps and independent outputs prevent a final control ranking.

13. **Is Heuristic V2 dominant?** Matchup-specific Heuristic W/L/no-result: strict 50/0/0; bounded 50/0/0; stepwise 40/2/8. Its model-request cost is zero; measured heuristic computation is reported separately. These are distinct matchups, not a pooled homogeneous skill estimate. The opponent is unchanged.

14. **Do EndTurns behave correctly?** All 297 explicit stops had zero subsequent requests within the turn. Control totals/immediate stops are strict: 88/3; bounded: 94/2; stepwise: 115/28. Legal damaging opportunities at a stop are mechanically audited but do not prove an attack would have been strategically preferable. Intentional, clean completion, truncation, actual provider failure, budget denial and terminal AP remain separate.

15. **Are there interesting Fireball patterns?** strict: 225 casts, 54 friendly-only, 26 mixed, 71 empty; friendly damage 308, friendly downs 10; bounded: 230 casts, 86 friendly-only, 33 mixed, 54 empty; friendly damage 428, friendly downs 13; stepwise: 842 casts, 33 friendly-only, 67 mixed, 112 empty; friendly damage 358, friendly downs 10. Engine-replayed terminal Fireballs and enemy damage/downs are listed in the main report. Counts reflect different exposure and repeated revive cycles; they are not quality scores or grounds for prompt tuning.

16. **Is there evidence of a contract defect?** No observed hard-stop condition was found. Exact replay, source/runtime checks and evidence reconciliation passed. The recorded failures are interpretable using the frozen current-action and AP validators. This does not prove the design flawless, but there is no evidence supporting a mid-study change. Ordinary model failures and tactical weakness remain benchmark evidence.

17. **Should the second half continue unchanged?** Yes. Mechanical checks remain clean, costs are measurable and bounded, and failure patterns are interpretable. The study must retain its fixed imperfect policy and opponent to answer the intended comparison. The halfway results cannot establish the full bounded thesis from AP recovery alone.

## Statistical and resource limits

Repair reliability is now a major study finding, not just an isolated incident: 31 of 150 matches ended in exhausted-repair forfeits (20.67%), including 17 of 50 Bounded matches (34%). Batch counts 2, 7, 8, 5 and 9 show that the elevated burden persists with variation; they do not establish a monotonic increase. Failures occur in every control, while Bounded has the largest observed match-level burden. Static range/LOS constraints account for 26 of 31 cases (83.87%).

All 1,113 provider receipts from Batches 4–5 record returned responses. The 14 new exhausted repairs therefore have affirmative response evidence, rather than an observed transport outage. Their exact validator reasons are preserved in repair-forensics.md. No failed game was retried.

The hoped-for Bounded win improvement is absent at halfway: Strict and Bounded are both 0/50 wins. Bounded has dealt five Core damage versus Strict's zero, a small observed Core-pressure difference that has not produced a win. Bounded reduces final execution truncations but has more repair forfeits. Its selective recovery mechanism works often; these data do not show that it compensates for the tactical and output-reliability limitations against Heuristic V2.

All eight capped Stepwise matches are Luna Red, with final Red Core HP 12 and Blue Core HP 30. Unit configurations differ, so these are not claims of identical full engine states. The new capped games show 41–44 Heuristic revives each and 42–132 Heuristic heals, plus recurring unit downs. Each new capped match reached 47 Luna turns with only 0–2 repairs and 1–2 explicit EndTurns. Thus most capped-game spending comes from repeatedly deciding through a long match, not repair retry volume. The traces do not identify unwillingness to EndTurn as a cause; explicit stop semantics were correct. All eight caps among the 25 Red assignments is a descriptive concentration, not proof of a general side effect.

| Control | Wins / losses / no-result | Win rate | Wilson 95% |
| --- | --- | --- | --- |
| strict | 0/50/0 | 0.00% | [6.938893903907228e-18, 0.07134759913335872] |
| bounded | 0/50/0 | 0.00% | [6.938893903907228e-18, 0.07134759913335872] |
| stepwise | 2/40/8 | 4.00% | [0.011038884327619805, 0.1346009068750702] |

Wilson intervals use all completed scheduled matches, including capped nonwins and forfeits. Frozen confirmatory McNemar/Holm and bootstrap inference waits for the full cohort; halfway paired differences, side splits and distributions are descriptive. One canonical opening and service-period/model variation limit generalization. No final winner is declared.

| Resource | Observed 150 | Remaining 150 estimate | Full 300 estimate |
| --- | --- | --- | --- |
| provider_requests | 2,580.000 | 2,580.000 | 5,160.000 |
| total_tokens | 6,741,410.000 | 6,741,410.000 | 13,482,820.000 |
| Provider hours | 1.1666 | 1.1666 | 2.3333 |

Observed process wall time totals 1.611 hours. Repeating the observed batch range gives 1.408–2.040 remaining wall hours, or 3.018–3.651 full-study hours. This excludes later analysis and is not a guaranteed bound: growing prefix verification and provider conditions can increase it. Provider/backend times overlap; cached input is part of input and reasoning tokens part of output. No frozen pricing exists, so no dollars are estimated.

## Next authorization recommendation

Recommend **Batches 6–8 only**, retaining independent 1,700-request ceilings, all per-control/per-match/global guards, and separate frozen integrity gates. At halfway observed rates, 90 further matches imply approximately 1,548.0 requests, 4,044,846 tokens and 0.700 provider hours. These are estimates, not increased ceilings. Five batches provide enough operational evidence that individual approval after every batch adds limited value. Reviewing again at 80/control retains a checkpoint before the final two batches. **No Batch 6 or later execution occurred.**

[Batch 4 report](../arena-case-study-live-v1-04/batch-4-report.md) · [Batch 4 gate](../arena-case-study-live-v1-04/batch-4-gate.md) · [Batch 5 report](batch-5-report.md) · [Halfway cumulative report](cumulative-batches-1-5-report.md) · [Focused comparisons](focused-comparisons.md) · [Repair forensics](repair-forensics.md) · [Figures](figures.md)
