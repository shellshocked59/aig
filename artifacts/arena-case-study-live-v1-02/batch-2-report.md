# Batch 2 standalone — interim case-study report

**Preliminary n=10/control; 30 sealed matches.** One canonical opening and nondeterministic Luna trajectories. No confirmatory tests, composite score, superiority or equivalence claim. [Decision and interpretation](decision.md).

## Execution and integrity

Only Batch 2 was newly run. The original Batch 1 directory was preserved byte-for-byte; the verified prefix was copied to arena-case-study-live-v1-02 because frozen resume refreshes cumulative aggregate views. Resume continued at MATCH-011 Bounded, request 584. No Batch 1 request/match was repeated. No interruption recovery was needed during Batch 2. The command stops at --through-batch 2; Batch 3 was not started.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-02 --through-batch 2 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-02/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-02/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-02/interim-report.py
```

postprocess.py invokes the unchanged case_study_contract.verify and case_study.integrity, then the unchanged case_study_analysis.analyze on the verified cumulative prefix and the batch==2 subset. Supplemental scripts only derive reporting from sealed evidence and never call providers.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Batch 2 schedule SHA-256 | eafa23891704896fec1bb5e3d8a84d897803b75e71ba55f43b66dd5eafc90f2b |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Frozen source files | 140 |

Frozen bindings: gpt-5.6-luna / luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 / arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2; arena-scenario-v1. Full immutable hashes/configuration are in contract.json. No frozen source or analyzer was modified.

Final frozen verification: `{"success": true, "completed_matches": 60, "replay_verified": 60, "completed_requests": 1030, "reserved_requests": 1030, "pending_requests": 0}`. It verifies source/runtime, exact schedule/side prefix, all command replays, observations/control bindings, deterministic heuristic actions, metrics, request ledger/receipts/seals and zero fallback. Original Batch 1 files checked: 2524; copied immutable prefix files checked: 2485.

Batch 2 manifest is schedule.json entries 31–60, MATCH-011–020, 30 intended matches and five Red/five Blue per control. The authoritative pre-send ledger enforces 1,700 Batch 2 requests, per-control 300/500/900 and per-match 50/80/140. Study ceiling remains 15,000. No extra retries or fallback. Provider repair exhaustion is a forfeit; limits receive no winner. Turn bounds remain 200 player turns / 100 completed rounds.

| Control | Intended | Started in cohort | Sealed | Red/Blue | Natural endings | Forfeits | No-result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 10 | 10 | {"red": 5, "blue": 5} | 7 | 3 | 0 |
| bounded | 10 | 10 | 10 | {"red": 5, "blue": 5} | 7 | 3 | 0 |
| stepwise | 10 | 10 | 10 | {"red": 5, "blue": 5} | 8 | 1 | 1 |

## Outcomes and heuristic baseline

| Agent / matchup | Wins | Losses incl. forfeits | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.2075 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.6818 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 1 | 8 | 1 | 0.1000 | [0.017876213095072896, 0.4041500267952385] | 3.1856 |
| Heuristic vs stepwise | 8 | 1 | 1 | 0.8000 | [0.49016247153664183, 0.9433178485456247] | 0.0000 |

| Control | Luna side | Wins | Losses | Limits | Wilson 95% |
| --- | --- | --- | --- | --- | --- |
| strict | red | 0 | 5 | 0 | [0, 0.43448246478317476] |
| strict | blue | 0 | 5 | 0 | [0, 0.43448246478317476] |
| bounded | red | 0 | 5 | 0 | [0, 0.43448246478317476] |
| bounded | blue | 0 | 5 | 0 | [0, 0.43448246478317476] |
| stepwise | red | 1 | 3 | 1 | [0.03622410863243014, 0.6244653702374747] |
| stepwise | blue | 0 | 5 | 0 | [0, 0.43448246478317476] |

| Control | Terminal causes | Player turns total/median/min/max | Rounds total/median/min/max |
| --- | --- | --- | --- |
| strict | {"TEAM_ELIMINATION": 6, "CORE_DESTRUCTION": 1, "PROVIDER_FORFEIT": 3} | [106, 9.5, 2, 38] | [45, 4.0, 0, 18] |
| bounded | {"TEAM_ELIMINATION": 5, "CORE_DESTRUCTION": 2, "PROVIDER_FORFEIT": 3} | [87, 10.0, 5, 14] | [36, 4.0, 2, 6] |
| stepwise | {"TEAM_ELIMINATION": 5, "CORE_DESTRUCTION": 3, "REQUEST_LIMIT": 1, "PROVIDER_FORFEIT": 1} | [195, 12.0, 1, 92] | [90, 5.5, 0, 45] |

## Requests and controls

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Provider requests | 64 | 74 | 309 |
| Attempted Luna turns | 53 | 44 | 97 |
| Completed Luna turns | 50 | 41 | 95 |
| First responses | 53 | 61 | 292 |
| First valid responses | 42 | 48 | 275 |
| Repairs | 11 | 13 | 17 |
| Successful repairs | 8 | 10 | 16 |
| Failed repairs | 3 | 3 | 1 |
| Provider failures excluding budget denial | 3 | 3 | 1 |
| Execution truncations | 20 | 2 | 0 |
| Initial execution invalidities | 20 | 17 | 0 |
| Bounded replans | 0 | 17 | 0 |
| Replacement repairs | 0 | 6 | 0 |
| Replacement invalidities | 0 | 2 | 0 |
| Second execution invalidities | 0 | 2 | 0 |
| AP recovered | 0 | 32 | 0 |
| Decisions including denied budgets | 53 | 61 | 293 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 6.4000 | 1.2075 | 1.1600 | 1.9811 | {"target outside action range": 9, "destination is occupied, blocked, unchanged, or beyond move range": 2, "blocked line of sight": 6, "impact outside Fireball range/board": 3} |
| bounded | 7.4000 | 1.6818 | 1.5610 | 2.5227 | {"target outside action range": 11, "blocked line of sight": 4, "actor must own an ACTIVE unit": 1, "invalid target ACTIVE/DOWNED status": 2, "impact outside Fireball range/board": 1} |
| stepwise | 30.9000 | 3.1856 | 3.2105 | 2.7938 | {} |

| Disjoint request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 53 | 44 | 0 |
| repair | 11 | 7 | 17 |
| bounded_replacement_planning | 0 | 17 | 0 |
| bounded_replacement_repair | 0 | 6 | 0 |
| stepwise_decisions | 0 | 0 | 292 |

Stepwise decisions in the request-purpose table exclude repair and budget-denied decisions. Repair includes initial-wave and Stepwise repairs; replacement repairs are separate. Requests/turn use attempted Luna turns. Truncations are execution-ending stops, not every invalidity that Bounded subsequently recovered.

| Bounded question | Observed |
| --- | --- |
| Replans | 17 |
| Positive-AP recoveries | 14 |
| Positive recovery fraction | 0.8235 |
| Total AP recovered | 32 |
| Mean AP/replan | 1.8824 |
| Second-invalidity rate | 0.1176 |
| Requests/turn | 1.6818 |
| Extra total requests vs Strict | 10 |
| Bounded/Strict total request ratio | 1.1562 |
| Bounded/Strict requests-per-turn ratio | 1.3928 |
| AP at each replan | [3, 4, 3, 3, 3, 2, 3, 3, 1, 3, 1, 1, 3, 3, 3, 4, 4] |
| AP recovered per replan | [3, 4, 3, 3, 3, 2, 2, 3, 0, 1, 1, 1, 2, 1, 3, 0, 0] |

| Stepwise question | Observed |
| --- | --- |
| count | 1 |
| fraction | 0.1000 |
| requests | 140 |
| request_share | 0.4531 |
| match_ids | ["MATCH-015-stepwise"] |
| Requests/Luna turn | 3.1856 |
| Decisions/Luna turn | 3.0206 |
| Requests after explicit EndTurn | 0 |

## AP and EndTurn

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| AP available | 265 | 220 | 485 |
| AP executed | 166 | 180 | 428 |

| AP reason | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 28 | 14 | 46 |
| CLEAN_PLAN_COMPLETE | 2 | 2 | 0 |
| EXECUTION_TRUNCATION | 50 | 4 | 0 |
| PROVIDER_FAILURE | 15 | 13 | 6 |
| TERMINAL | 4 | 7 | 5 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 1 |
| Actual provider-failure AP | 15 | 13 | 5 |

Generic PROVIDER_FAILURE includes budget denial in frozen controller telemetry; actual provider-failure AP is adjusted in the last row. Intentional, clean, truncation, provider, budget and terminal AP are not a composite quality score.

| Control | Explicit stops | Immediate | AP remaining distribution | Actions before stop | Damaging option left | Down option left | Replacement stops | Requests after EndTurn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 21 | 0 | {"2": 2, "1": 12, "0": 3, "3": 4} | {"2": 12, "3": 3, "1": 4, "4": 2} | 4 | 1 | 0 | 0 |
| bounded | 18 | 0 | {"0": 6, "1": 11, "3": 1} | {"3": 7, "2": 9, "1": 1, "4": 1} | 1 | 0 | 5 | 0 |
| stepwise | 20 | 6 | {"1": 12, "5": 6, "2": 2} | {"2": 14, "0": 6} | 3 | 0 | 0 | 0 |

Damaging/down opportunities are legal single actions simulated from the authoritative pre-EndTurn state. They flag potentially premature stops without claiming an action was strategically preferable. Exact stop records/opportunities are in supplemental-audit.json. No model judge or live counterfactual inference was used.

## Combat and tactics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Core damage dealt | 0 | 0 | 0 |
| Core damage received | 105 | 70 | 180 |
| Enemy unit damage | 173 | 194 | 1022 |
| Friendly unit damage | 42 | 90 | 111 |
| Enemy downs | 10 | 12 | 61 |
| Friendly downs | 2 | 4 | 6 |
| Downs received | 31 | 31 | 32 |
| Finishes | 0 | 2 | 8 |
| Revives | 3 | 5 | 7 |
| Snipe uses | 6 | 9 | 0 |
| Shield Bash uses | 7 | 4 | 13 |
| Shield Bash pushes | 6 | 3 | 3 |
| Fireball uses | 52 | 55 | 150 |
| Enemy Fireball damage | 72 | 86 | 794 |
| Friendly Fireball damage | 42 | 90 | 111 |
| Empty Fireballs | 23 | 17 | 21 |
| Friendly-only Fireballs | 10 | 16 | 10 |
| Enemy-only Fireballs | 15 | 14 | 102 |
| Mixed Fireballs | 4 | 8 | 17 |
| Basic attacks | 6 | 4 | 66 |
| Core attacks | 0 | 0 | 0 |
| Moves | 28 | 26 | 17 |
| Heals | 3 | 6 | 10 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 19 | 23 | 200 |
| friendly_units_hit | 14 | 28 | 36 |
| enemy_damage | 72 | 86 | 794 |
| friendly_damage | 42 | 90 | 111 |
| enemy_downs | 2 | 3 | 2 |
| friendly_downs | 2 | 4 | 6 |

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 56 | 74 | 0 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 5 | 5 | 0 |
| arena_snipe friendly_downs | 0 | 0 | 0 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 22 | 14 | 46 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 3 |
| arena_shield_bash friendly_downs | 0 | 0 | 0 |
| arena_shield_bash enemy_displacements | 6 | 3 | 3 |

| Heuristic mechanical total by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 105 | 70 | 180 |
| core_damage_received | 0 | 0 | 0 |
| enemy_units_downed | 29 | 27 | 26 |
| finish | 9 | 8 | 15 |
| revive | 6 | 7 | 49 |
| ap_executed | 188 | 186 | 446 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 8.2960 | 7.1688 | 21.9719 |

Counts are exposure-dependent and can include repeated downs/revivals of the same unit. Heuristic inference is zero; measured heuristic computation is separate. Heuristic matchup strata are not pooled. Per-match engine command traces preserve all action effects.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 64 | 74 | 309 |
| input_tokens | 170305 | 198586 | 776037 |
| cached_input_tokens | 82047 | 102871 | 152793 |
| output_tokens | 5666 | 6006 | 13629 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 175971 | 204592 | 789666 |
| provider_latency_seconds | 111.3446 | 128.3283 | 509.0078 |
| backend_thinking_seconds | 119.2452 | 137.5747 | 539.1377 |

| Resource | Batch 1 | Batch 2 | Cumulative |
| --- | --- | --- | --- |
| provider_requests | 583 | 447 | 1030 |
| input_tokens | 1492199 | 1144928 | 2637127 |
| cached_input_tokens | 390703 | 337711 | 728414 |
| output_tokens | 32764 | 25301 | 58065 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 2695192 |
| provider_latency_seconds | 963.2223 | 748.6807 | 1,711.9030 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 1,804.6754 |

| Control | Requests/match | Tokens/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 6.4000 | 17,597.1000 | 1.2075 | 3,320.2075 | 2.1008 | 2.2499 | 141.5576 |
| bounded | 7.4000 | 20,459.2000 | 1.6818 | 4,649.8182 | 2.9166 | 3.1267 | 158.4647 |
| stepwise | 30.9000 | 78,966.6000 | 3.1856 | 8,140.8866 | 5.2475 | 5.5581 | 598.3945 |

Batch 1 observed process wall upper bound: 1160.412 s. Batch 2 process wall upper bound: 1013.412 s. Sum: 2173.824 s. Timing begins at process start and ends at observed successful exit, including short observation delay and Batch 2 initial offline prefix verification. Post-run analysis time is excluded. Provider and backend times overlap, so do not add them. Match evidence elapsed is manifest-to-seal duration; it excludes between-match gates. Cached input is a subset of input, and reasoning a subset of output.

## Updated projection from cumulative observations

| provider_requests | Observed cumulative | Per-match mean | Remaining 80/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 149 | 7.4500 | 596.0000 | 745.0000 | [2, 26] | [160, 2080] | [309, 2229] |
| bounded | 169 | 8.4500 | 676.0000 | 845.0000 | [3, 16] | [240, 1280] | [409, 1449] |
| stepwise | 712 | 35.6000 | 2,848.0000 | 3,560.0000 | [2, 140] | [160, 11200] | [872, 11912] |

Combined provider_requests: remaining 240 central **4,120.000**, full 300 central **5,150.000**. Remaining observed-extreme sensitivity: [560, 14560]; full-study sensitivity: [1590, 15590].

| total_tokens | Observed cumulative | Per-match mean | Remaining 80/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 411135 | 20,556.7500 | 1,644,540.0000 | 2,055,675.0000 | [6218, 66117] | [497440, 5289360] | [908575, 5700495] |
| bounded | 472939 | 23,646.9500 | 1,891,756.0000 | 2,364,695.0000 | [7843, 43667] | [627440, 3493360] | [1100379, 3966299] |
| stepwise | 1811118 | 90,555.9000 | 7,244,472.0000 | 9,055,590.0000 | [6409, 363431] | [512720, 29074480] | [2323838, 30885598] |

Combined total_tokens: remaining 240 central **10,780,768.000**, full 300 central **13,475,960.000**. Remaining observed-extreme sensitivity: [1637600, 37857200]; full-study sensitivity: [4332792, 40552392].

| provider_latency_seconds | Observed cumulative | Per-match mean | Remaining 80/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 274.6426 | 13.7321 | 1,098.5702 | 1,373.2128 | [3.2305263999733143, 42.251198099926114] | [258.44211199786514, 3380.095847994089] | [533.0846710976912, 3654.738407093915] |
| bounded | 297.0363 | 14.8518 | 1,188.1453 | 1,485.1816 | [7.052771400019992, 29.19422550010495] | [564.2217120015994, 2335.538040008396] | [861.2580293015344, 2632.574357308331] |
| stepwise | 1,140.2242 | 57.0112 | 4,560.8967 | 5,701.1208 | [3.184885499998927, 216.68082660034997] | [254.79083999991417, 17334.466128027998] | [1395.0150094011915, 18474.690297429275] |

Combined provider_latency_seconds: remaining 240 central **6,847.612**, full 300 central **8,559.515**. Remaining observed-extreme sensitivity: [1077.4546639993787, 23050.100016030483]; full-study sensitivity: [2789.357709800417, 24762.00306183152].

Provider hours: remaining **1.9021**, full study **2.3776**.

Central projection uses each control’s cumulative mean. The extreme sensitivity assigns every remaining game that control’s observed minimum or maximum and holds collected results fixed; it is not a confidence interval. It can exceed frozen limits, in which case guards stop the study. Request-limited games are censored outcomes, and early forfeits can lower observed costs. No dollar pricing is inferred.

Wall-clock planning sensitivity, if future batches resemble either observed batch: remaining eight batches 2.252–2.579 hours; full study 2.856–3.183 hours. This excludes future standalone analysis and is only a two-batch workload illustration. Longer cumulative prefix verification, provider conditions and cap frequency can move wall time outside it.

## Paired triplets

Order in each list: Strict / Bounded / Stepwise. Frozen analysis is descriptive at this interim sample; McNemar p-values and bootstrap inferential intervals remain absent until the prespecified complete cohort.

Outcome patterns: `{"loss/loss/loss": 8, "loss/loss/limit": 1, "loss/loss/win": 1}`; all-three-same outcome triplets: 8.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 4, "limit_pairs": 0, "median_paired_player_turn_difference": 1.5, "provider_requests_per_turn_ratio": 1.3927556818181819, "total_tokens_per_turn_ratio": 1.4004600964725076, "backend_thinking_seconds_per_turn_ratio": 1.3896992054984807, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 1, "win_losses": 0, "win_rate_difference": 0.1, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 8, "limit/loss": 1, "win/loss": 1}, "provider_forfeit_pairs": 4, "limit_pairs": 1, "median_paired_player_turn_difference": 5.0, "provider_requests_per_turn_ratio": 1.8941209250487598, "total_tokens_per_turn_ratio": 1.7507967579830996, "backend_thinking_seconds_per_turn_ratio": 1.777633087446402, "win_difference_bootstrap_95": null}`

| Slot | Side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-011 | red | ["loss", "loss", "loss"] | [19, 7, 24] | [38, 10, 15] | [-12, 17] | [-28, 5] |
| MATCH-012 | blue | ["loss", "loss", "loss"] | [7, 15, 12] | [12, 14, 10] | [8, -3] | [2, -4] |
| MATCH-013 | red | ["loss", "loss", "loss"] | [7, 6, 24] | [9, 10, 15] | [-1, 18] | [1, 5] |
| MATCH-014 | blue | ["loss", "loss", "loss"] | [8, 4, 15] | [12, 5, 10] | [-4, 11] | [-7, 5] |
| MATCH-015 | red | ["loss", "loss", "limit"] | [5, 8, 140] | [10, 10, 92] | [3, 132] | [0, 82] |
| MATCH-016 | blue | ["loss", "loss", "loss"] | [6, 9, 2] | [10, 10, 1] | [3, -7] | [0, -9] |
| MATCH-017 | red | ["loss", "loss", "win"] | [3, 10, 36] | [7, 11, 18] | [7, 26] | [4, 7] |
| MATCH-018 | blue | ["loss", "loss", "loss"] | [4, 6, 16] | [3, 5, 10] | [2, 10] | [2, 5] |
| MATCH-019 | red | ["loss", "loss", "loss"] | [2, 3, 18] | [2, 7, 11] | [1, 15] | [5, 4] |
| MATCH-020 | blue | ["loss", "loss", "loss"] | [3, 6, 22] | [3, 5, 13] | [3, 16] | [2, 8] |

## Per-match evidence

| Match | Side | Outcome/cause | Turns/rounds | Requests/Luna turns | AP executed; I/C/X/P/T unused | Core damage dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-011-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [7, 5] | [21, 3, 0, 0, 0, 1] | [0, 5] | [1, 0, 0] | a83443d93475e61e6afefa0a0cbcb74917a5677b97fb6649465b6260d2f80eb4 |
| MATCH-011-stepwise | red | loss/TEAM_ELIMINATION | [15, 7] | [24, 7] | [33, 2, 0, 0, 0, 0] | [0, 0] | [2, 2, 1] | e5eca616cf8e7d82f772f6a7e30e9bdda20c5b3455058e5c377c2b3285048120 |
| MATCH-011-strict | red | loss/TEAM_ELIMINATION | [38, 18] | [19, 19] | [70, 18, 1, 5, 0, 1] | [0, 20] | [2, 0, 3] | 40d86dabc28fa41d709129542734d2e46cea5743639955889bcfdbb9c070dc4e |
| MATCH-012-bounded | blue | loss/CORE_DESTRUCTION | [14, 6] | [15, 7] | [34, 0, 1, 0, 0, 0] | [0, 30] | [4, 1, 0] | 8c131dce765dec1b799d985f51e12f10dd2f087508d61d8811803b0c1ec6d219 |
| MATCH-012-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [12, 5] | [13, 12, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | 3c5d633acdc1e7f71cb3291c5f584a9eb592d0e22a1f5ba7fc312dfff4948008 |
| MATCH-012-strict | blue | loss/TEAM_ELIMINATION | [12, 5] | [7, 6] | [22, 2, 1, 5, 0, 0] | [0, 15] | [1, 0, 0] | 30733168b5679b1dcb228bd7fe3b237068e63599a0380c15e38bb87a5d29f7a4 |
| MATCH-013-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [6, 5] | [17, 5, 0, 0, 0, 3] | [0, 0] | [1, 0, 0] | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-013-stepwise | red | loss/TEAM_ELIMINATION | [15, 7] | [24, 7] | [30, 5, 0, 0, 0, 0] | [0, 18] | [3, 1, 0] | d5fbcb97cab332ac120f9241c436cc5de398cf23c742ac45f0c1e78cfe5de216 |
| MATCH-013-strict | red | loss/TEAM_ELIMINATION | [9, 4] | [7, 4] | [12, 0, 0, 8, 0, 0] | [0, 25] | [1, 0, 0] | 5017faaadb1df232a916270089b6b03cfd431213c904165d164cc10069d8baa7 |
| MATCH-014-bounded | blue | loss/PROVIDER_FORFEIT | [5, 2] | [4, 3] | [10, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | e07574029ad1d9b0c59a6d457e1c5bbe9ff68d4032edc6d4bd6c75f2c0746588 |
| MATCH-014-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [16, 9, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | dfb65e3b4fe23e8646b886799fea3df292d18aa64d58d75bd46c99a915f76235 |
| MATCH-014-strict | blue | loss/TEAM_ELIMINATION | [12, 5] | [8, 6] | [14, 4, 0, 12, 0, 0] | [0, 5] | [1, 0, 0] | cd4179ef13bcfa9ae5d721b8d89ebda3fc749041014f0bb7cabd42d567d86b91 |
| MATCH-015-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [8, 5] | [19, 3, 0, 0, 0, 3] | [0, 5] | [1, 0, 0] | 820b3ea4b1292e7690cbc3c0d8471fb6cdc49ab57cb78f406c038c275430ef21 |
| MATCH-015-stepwise | red | limit/REQUEST_LIMIT | [92, 45] | [140, 46] | [227, 2, 0, 0, 1, 0] | [0, 18] | [43, 0, 4] | a38d7e323816f260b9340a7b4c46ab269a4f85fabd7e9571e25d2ba67fed19a0 |
| MATCH-015-strict | red | loss/TEAM_ELIMINATION | [10, 4] | [5, 5] | [15, 2, 0, 5, 0, 3] | [0, 5] | [1, 0, 0] | 820b3ea4b1292e7690cbc3c0d8471fb6cdc49ab57cb78f406c038c275430ef21 |
| MATCH-016-bounded | blue | loss/TEAM_ELIMINATION | [10, 4] | [9, 5] | [21, 2, 0, 2, 0, 0] | [0, 0] | [1, 0, 1] | 29593deaca8deb9bb10b5e2e6573a2ade97876b7d505b470dc9ae30893f6c0de |
| MATCH-016-stepwise | blue | loss/PROVIDER_FORFEIT | [1, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d |
| MATCH-016-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [6, 5] | [16, 1, 0, 8, 0, 0] | [0, 30] | [2, 0, 0] | 10ce9c78f5249cb2b0df39b031d31ccd26f84da6a35a5cd4c413529bbb7e9860 |
| MATCH-017-bounded | red | loss/CORE_DESTRUCTION | [11, 5] | [10, 5] | [22, 0, 1, 2, 0, 0] | [0, 30] | [1, 1, 1] | 0c859a21d90df32a734cb529939179978478cbaa37eb728c83aad5bc4d98224c |
| MATCH-017-stepwise | red | win/TEAM_ELIMINATION | [18, 8] | [36, 9] | [42, 1, 0, 0, 0, 2] | [0, 18] | [5, 3, 0] | bb98042d394177dbb9d3cd2bac44aa9ab6a222712b1afa93d69ab02b16aada62 |
| MATCH-017-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [3, 3] | [9, 1, 0, 5, 0, 0] | [0, 5] | [0, 0, 0] | c85aae76941ff976e99aba55ed65a8249617386f6bbb03a82a415241bed4a754 |
| MATCH-018-bounded | blue | loss/PROVIDER_FORFEIT | [5, 2] | [6, 3] | [11, 0, 0, 0, 4, 0] | [0, 0] | [1, 0, 0] | ba473f89754f256a8ea8918b3adfc15eec91dc16c3de0d7fe49080bb917598e0 |
| MATCH-018-stepwise | blue | loss/TEAM_ELIMINATION | [10, 4] | [16, 5] | [16, 9, 0, 0, 0, 0] | [0, 18] | [1, 0, 0] | 135e32d6319f9fa5772c8d95b96be3b36edc00be347e516b79a027f6dc6953fa |
| MATCH-018-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [3, 0, 0, 2, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-019-bounded | red | loss/TEAM_ELIMINATION | [7, 3] | [3, 3] | [14, 1, 0, 0, 0, 0] | [0, 0] | [0, 0, 3] | 881f9000a9d384e636a768f3b737dc7ce61ae905283ad0f55bf548a2079d5877 |
| MATCH-019-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [18, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 1, 0] | a72726e5bc2b91876f49a853f82d02f415ba3f1ec183c923027a93eb8dc75560 |
| MATCH-019-strict | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-020-bounded | blue | loss/PROVIDER_FORFEIT | [5, 2] | [6, 3] | [11, 0, 0, 0, 4, 0] | [0, 0] | [1, 0, 0] | ba473f89754f256a8ea8918b3adfc15eec91dc16c3de0d7fe49080bb917598e0 |
| MATCH-020-stepwise | blue | loss/TEAM_ELIMINATION | [13, 6] | [22, 7] | [27, 5, 0, 0, 0, 3] | [0, 18] | [2, 1, 2] | d6c120f6d7c596e10d3f84280668b0bab504062f6142a12b4ee439018c670ef4 |
| MATCH-020-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |

## Decision and limitations

See [decision.md](decision.md) for the final PASS/PAUSE recommendation, comparisons and next authorization scope. Tactical weakness alone is not an infrastructure blocker. This sample remains interim; spending AP or recovering AP does not prove better game quality. Do not change prompts, controls, caps, opponent or analysis after observing these results. Batch 3 was not run.

Prepared figures: standalone in batch-2-analysis/plots/; cumulative in plots/. Each view contains 11 PNG and 11 SVG outputs from the unchanged frozen analyzer. See [figures.md](figures.md) for small-sample and AP-bucket captions. Full metrics and audit details: interim-metrics.json, supplemental-audit.json, analysis.json and batch-2-analysis/analysis.json.
