# Decision — INTERIM, 80/100 matches per control

**PASS FOR CONTINUATION unchanged. Recommend authorizing Batches 9–10 to finish the frozen study. Neither batch was executed.**

All 240 cumulative matches passed exact replay. Batches 6 and 7 each passed full replay, ledger reconciliation, source/contract and earlier-artifact preservation gates before the next batch started. Batch 8 also passed. The independent 1,700-request batch ceilings remained unchanged; no unused capacity rolled forward. There were no duplicate committed requests, pending requests, heuristic fallback or retries of forfeited matches. Frozen prompts, model/profile, controls, rules, opponent, schedule, metrics and analysis were unchanged.

| Cohort | Strict W/L/no-result; requests | Bounded W/L/no-result; requests | Stepwise W/L/no-result; requests |
| --- | --- | --- | --- |
| Batch 6 | 0/10/0; 48 | 0/10/0; 124 | 0/8/2; 403 |
| Batch 7 | 0/10/0; 82 | 0/10/0; 89 | 1/6/3; 585 |
| Batch 8 | 0/10/0; 78 | 0/10/0; 74 | 0/8/2; 416 |
| Cumulative | 0/80/0; 555 | 0/80/0; 695 | 3/62/15; 3229 |

## Fourteen research questions

1. **Does Bounded still reduce execution truncation?** Final truncations are 25 versus Strict's 180; the count ratio is 0.139. At halfway it was 14/119 (0.118). Attempted-turn rates are 0.063 versus 0.420. Truncation-derived unused AP is 47 versus 471. Counts and rates are both needed because trajectories and match lengths differ.

2. **Is AP recovery stable?** Cumulative positive recovery is 140/157 (89.17%), versus 88/99 (88.89%) at halfway. It recovered 279 AP, mean 1.777 and median 2 per replan. New-batch positive counts: 6: 18/20; 7: 18/21; 8: 16/17. Second invalidities are 25/157 (15.92%). No new acceptance threshold or trend test is introduced.

3. **Is there an outcome advantage over Strict?** Bounded versus Strict W/L/no-result: 0/80/0 versus 0/80/0. Win difference: +0. Core damage: 42 versus 0; enemy downs: 104 versus 81; Finishes: 11 versus 1. Repair forfeits are 29 versus 20. Mechanical recovery alone does not establish tactical success. Paired differences and terminal causes in the linked tables expose these separate measures rather than combining them into a score.

4. **Is the request premium stable?** Cumulative per-match premium is 25.23% (8.688 versus 6.938 requests/match); per-Luna-turn premium is 35.32% (1.751 versus 1.294). Halfway values were 17.58% and 38.14%. New-batch total premiums: 6: 158.33%; 7: 8.54%; 8: -5.13%. Signed extra requests / recovered AP is 0.5018, descriptive and not causal. Match length, early forfeits and independent responses influence aggregate costs.

5. **Does Bounded have a higher repair-forfeit burden?** strict: 20/80 (25.00%), repair success 106/126 (84.13%); bounded: 29/80 (36.25%), repair success 112/141 (79.43%); stepwise: 4/80 (5.00%), repair success 133/137 (97.08%). All controls are exposed; control-specific decision denominators and per-batch counts are reported in repair-forensics.md. This observational comparison does not identify a stochastic mechanism or establish a causal control effect. Full-turn planning controls and Stepwise must be compared using their different request/turn exposure as well as match-level forfeits.

The two full-turn arms jointly have 49/160 repair-forfeit matches (30.63%), compared with Stepwise 4/80 (5.00%). First-response invalidity is 267/983 (27.16%) for those full-turn decision requests, including Bounded replacement plans, versus 137/3092 (4.43%) for Stepwise. This descriptive grouping shows the association and exposure; it does not establish why the policies failed.

6. **Are exhausted repairs concentrated around range/LOS?** 46/53 (86.79%) carry the descriptive static range/LOS tag. All categories: `{"STATIC_RANGE_OR_LOS": 46, "AP_VIOLATION": 5, "OTHER_CURRENT_ACTION_VALIDATION": 2}`. Counts by batch are [2, 7, 8, 5, 9, 10, 6, 6]. These forfeits directly determine 53/240 (22.08%) losses; outcomes without the failures are unknown. The broad official invalid_reference category can reject geometry with valid IDs. Extra-analysis.md separates explicit range, LOS and ambiguous Fireball range/board diagnostics without rewriting official classifications.

7. **Is Stepwise the only control with wins?** Controls with observed wins: stepwise. Counts: strict 0/80, bounded 0/80, stepwise 3/80. This remains an interim sample from one canonical opening, not a final control ranking.

8. **Is Stepwise's cost tail still large?** Mean requests/match 40.362, median 16.0, uncapped mean 17.369; capped games consume 65.04% of its requests. Uncapped games include early forfeits. Sorted counts and capped states are reported. p75/p90/p95 are not published by the frozen analyzer and are not added as new inferential outputs.

9. **How often is Stepwise capped?** 15/80 (18.75%), each at 140 requests, consuming 2100 requests. All capped games retain no winner and a nonterminal final state. Natural uncapped outcomes and length are unknown. Each cap's rounds, Luna turns, AP/actions, repairs, EndTurns, Core/unit state and final hash are retained.

10. **Does Stepwise's outcome advantage justify the cost?** Its W/L/no-result is 3/62/15, versus Bounded 0/80/0. Costs: 3229 versus 695 requests, 8,180,226 versus 1,911,938 tokens, and 4785.42 versus 1242.78 provider seconds. Per turn, requests are 3.038 versus 1.751. No value threshold was frozen to declare a small outcome gain worth that cost. Caps, early forfeits and uncertainty prevent a final cost-quality ranking.

11. **Is Heuristic V2 stronger in the observed matchups?** Its matchup-specific W/L/no-result is strict 80/0/0; bounded 80/0/0; stepwise 62/3/15. This describes the observed dominance without pooling three different matchups into a homogeneous skill estimate. Its policy is unchanged; tactical weakness is benchmark data.

12. **Are intentional stops mechanically and tactically reasonable?** All 562 observed explicit EndTurns had zero subsequent provider requests within the turn. Counts/immediate stops: strict 159/6; bounded 176/3; stepwise 227/44. Stops with a legal single-action damaging opportunity: strict 55; bounded 40; stepwise 20. These are candidate premature-looking stops, not proof an attack was strategically preferable. Mechanical correctness is verified; overall tactical reasonableness remains limited to objective trace facts, with no model judge.

13. **Has an actual contract defect appeared?** No observed hard integrity failure occurred in source/runtime checks, exact replay, request accounting, schedule/bindings, immutable evidence or no-fallback audits. Saved structured output and validators make repair failures interpretable. Exact replay is not a proof of ideal benchmark design, but there is no evidence supporting a mid-study contract change.

14. **Is the study still interpretable as designed?** Yes, as a fixed imperfect Luna policy under three fixed control strategies against unchanged Heuristic V2 on one canonical opening. Recovery, output validity, outcomes and resource exposure remain separate. No tuning or early stopping based on apparent significance occurred. The intended sample remains 100/control, and confirmatory analysis remains reserved for the full cohort.

## Objective long-game and Fireball evidence

Every Bounded match with nonzero Core damage is listed below, so observed pressure is retained alongside its terminal outcome. This is a descriptive subset; the full outcome denominator remains all 80 matches.

| Match | Side | Core damage | Outcome/cause | Requests | Player turns |
| --- | --- | --- | --- | --- | --- |
| MATCH-044-bounded | blue | 5 | loss/PROVIDER_FORFEIT | 8 | 9 |
| MATCH-056-bounded | blue | 18 | loss/TEAM_ELIMINATION | 27 | 28 |
| MATCH-058-bounded | blue | 9 | loss/PROVIDER_FORFEIT | 7 | 7 |
| MATCH-074-bounded | blue | 10 | loss/CORE_DESTRUCTION | 9 | 12 |

| Cap | Luna turns | Requests | Repairs | EndTurns | Luna/Heuristic revives | Luna Core damage |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-001-stepwise | 47 | 140 | 0 | 2 | 44/44 | 0 |
| MATCH-009-stepwise | 47 | 140 | 2 | 2 | 26/44 | 0 |
| MATCH-015-stepwise | 46 | 140 | 3 | 2 | 4/43 | 0 |
| MATCH-021-stepwise | 47 | 140 | 0 | 1 | 0/44 | 0 |
| MATCH-031-stepwise | 47 | 140 | 2 | 2 | 0/44 | 0 |
| MATCH-033-stepwise | 47 | 140 | 2 | 1 | 43/41 | 0 |
| MATCH-037-stepwise | 47 | 140 | 0 | 2 | 28/44 | 0 |
| MATCH-047-stepwise | 47 | 140 | 1 | 2 | 25/44 | 0 |
| MATCH-051-stepwise | 47 | 140 | 2 | 2 | 27/44 | 0 |
| MATCH-058-stepwise | 45 | 140 | 6 | 39 | 0/0 | 0 |
| MATCH-063-stepwise | 47 | 140 | 1 | 2 | 33/44 | 0 |
| MATCH-067-stepwise | 46 | 140 | 2 | 1 | 3/43 | 0 |
| MATCH-069-stepwise | 47 | 140 | 0 | 2 | 0/44 | 0 |
| MATCH-075-stepwise | 47 | 140 | 1 | 2 | 44/44 | 0 |
| MATCH-079-stepwise | 47 | 140 | 2 | 2 | 26/44 | 0 |

These trace counts distinguish long-game decision exposure from repair volume. Repeated legal actions, unit downs, revivals and healing can be described directly; hidden reasoning, unwillingness to stop or a general causal stalemate mechanism cannot be inferred. Cap Core/unit configurations and final hashes are in cap-details.json.

| Control | Fireballs | Enemy-only/mixed/friendly-only/empty | Enemy/friendly damage | Enemy/friendly downs |
| --- | --- | --- | --- | --- |
| strict | 406 | 174/33/99/100 | 762/466 | 13/17 |
| bounded | 344 | 88/46/130/80 | 488/630 | 25/17 |
| stepwise | 1542 | 1108/103/74/257 | 8293/633 | 13/17 |

Immediate engine-winner consequences are listed in the cumulative report. Cast counts and friendly-fire patterns are descriptive; repeated revive cycles and unequal duration affect exposure. They do not establish internal Fireball comprehension.

## Resources and projections

| Resource | Batch 6 | Batch 7 | Batch 8 | Cumulative 240 |
| --- | --- | --- | --- | --- |
| provider_requests | 575.000 | 756.000 | 568.000 | 4,479.000 |
| input_tokens | 1,414,932.000 | 1,940,774.000 | 1,439,224.000 | 11,392,588.000 |
| cached_input_tokens | 311,921.000 | 518,980.000 | 381,822.000 | 3,238,062.000 |
| output_tokens | 30,906.000 | 39,954.000 | 30,494.000 | 245,106.000 |
| reasoning_tokens | 0.000 | 0.000 | 0.000 | 0.000 |
| total_tokens | 1,445,838.000 | 1,980,728.000 | 1,469,718.000 | 11,637,694.000 |
| provider_latency_seconds | 893.159 | 1,112.429 | 829.254 | 7,034.751 |
| backend_thinking_seconds | 955.177 | 1,192.687 | 879.115 | 7,468.468 |

| Control | W/L/no-result | Win rate | Wilson 95% |
| --- | --- | --- | --- |
| strict | 0/80/0 | 0.00% | [0, 0.0458181295355271] |
| bounded | 0/80/0 | 0.00% | [0, 0.0458181295355271] |
| stepwise | 3/62/15 | 3.75% | [0.012834568919911402, 0.10454720090045115] |

| Resource | Remaining 60 estimate | Full 300 estimate |
| --- | --- | --- |
| Requests | 1,119.75 | 5,598.75 |
| Tokens | 2,909,424 | 14,547,118 |
| Provider hours | 0.4885 | 2.4426 |

Projections use observed per-control rates with 20 matches/control remaining. Caps and forfeits censor natural cost; these are estimates, not confidence bounds or authorization. Cached input is part of input; reasoning tokens part of output. Provider and backend times overlap. Process wall timings and sensitivity are in the cumulative report. No frozen pricing exists, so no dollars are estimated.

## Decision and next authorization

At 80/control, the large truncation reduction persists: Bounded has 86.1% fewer final truncations than Strict, versus 88.2% fewer at halfway. Positive recovery remains descriptively stable near 89%. The request premium is not stable across individual batches; its cumulative per-match value increased while its per-turn value decreased. No win advantage over Strict has emerged, although Bounded has more observed Core damage, downs and Finishes. These combat differences are descriptive and affected by unequal trajectories and repair forfeits.

The higher Bounded repair-forfeit burden persists in the cumulative sample (36.25% versus 25.00% for Strict), a difference of 11.25 percentage points. It is not uniformly higher in every new batch: Batches 6 and 8 were tied, while Batch 7 had four versus two. The evidence therefore supports a descriptive imbalance, dominated by geometry failures and associated with full-turn planning, without identifying a stochastic or causal explanation. All 1,899 newly authorized requests returned normally; no recorded transport failure accounts for these forfeits.

The Stepwise tail reflects long sequences of accepted actions, not mainly repair attempts: the capped games lasted 45–47 Luna turns, with only 0–6 repairs each. Fourteen Red-side caps include extensive repeated downs and heuristic revivals, without Luna Core damage. The Blue-side MATCH-058 cap had 39 explicit EndTurns and no revivals by either agent. Intentional stopping therefore occurred even in a capped game; a universal failure-to-stop explanation is unsupported. These are objective trace patterns consistent with recurrent low-progress play, not a claim about hidden reasoning or the uncapped counterfactual.

**Continue unchanged. Recommend authorizing Batches 9–10 together**, with separate frozen integrity gates, independent 1,700-request ceilings and all existing per-control/per-match/global limits. Eight batches provide operational calibration; no integrity concern warrants splitting the last two authorizations. Tactical results must not change the study design. This recommendation is not executed: the runner stopped at Batch 8.

[Batch 6 report](../arena-case-study-live-v1-06/batch-6-report.md) · [Batch 6 gate](../arena-case-study-live-v1-06/batch-6-gate.md) · [Batch 7 report](../arena-case-study-live-v1-07/batch-7-report.md) · [Batch 7 gate](../arena-case-study-live-v1-07/batch-7-gate.md) · [Batch 8 report](batch-8-report.md) · [Cumulative report](cumulative-batches-1-8-report.md) · [Repair forensics](repair-forensics.md) · [Paired mechanics and diagnostics](extra-analysis.md) · [Figures](figures.md)
