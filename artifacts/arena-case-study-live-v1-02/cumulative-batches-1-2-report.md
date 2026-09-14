# Cumulative Batches 1–2 — interim case-study report

**Preliminary n=20/control; 60 sealed matches.** One canonical opening and nondeterministic Luna trajectories. No confirmatory tests, composite score, superiority or equivalence claim. [Decision and interpretation](decision.md).

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
| strict | 20 | 20 | 20 | {"red": 10, "blue": 10} | 16 | 4 | 0 |
| bounded | 20 | 20 | 20 | {"red": 10, "blue": 10} | 16 | 4 | 0 |
| stepwise | 20 | 20 | 20 | {"red": 10, "blue": 10} | 16 | 1 | 3 |

## Outcomes and heuristic baseline

| Agent / matchup | Wins | Losses incl. forfeits | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 20 | 0 | 0.0000 | [0, 0.16112515805281938] | 1.3070 |
| Heuristic vs strict | 20 | 0 | 0 | 1.0000 | [0.8388748419471806, 1] | 0.0000 |
| bounded Luna | 0 | 20 | 0 | 0.0000 | [0, 0.16112515805281938] | 1.7979 |
| Heuristic vs bounded | 20 | 0 | 0 | 1.0000 | [0.8388748419471806, 1] | 0.0000 |
| stepwise Luna | 2 | 15 | 3 | 0.1000 | [0.027866481213768224, 0.3010336452284873] | 3.0957 |
| Heuristic vs stepwise | 15 | 2 | 3 | 0.7500 | [0.531299122381256, 0.8881382985923343] | 0.0000 |

| Control | Luna side | Wins | Losses | Limits | Wilson 95% |
| --- | --- | --- | --- | --- | --- |
| strict | red | 0 | 10 | 0 | [0, 0.2775327998628892] |
| strict | blue | 0 | 10 | 0 | [0, 0.2775327998628892] |
| bounded | red | 0 | 10 | 0 | [0, 0.2775327998628892] |
| bounded | blue | 0 | 10 | 0 | [0, 0.2775327998628892] |
| stepwise | red | 1 | 6 | 3 | [0.017876213095072896, 0.4041500267952385] |
| stepwise | blue | 1 | 9 | 0 | [0.017876213095072896, 0.4041500267952385] |

| Control | Terminal causes | Player turns total/median/min/max | Rounds total/median/min/max |
| --- | --- | --- | --- |
| strict | {"CORE_DESTRUCTION": 5, "TEAM_ELIMINATION": 11, "PROVIDER_FORFEIT": 4} | [230, 9.5, 2, 38] | [101, 4.0, 0, 18] |
| bounded | {"TEAM_ELIMINATION": 13, "PROVIDER_FORFEIT": 4, "CORE_DESTRUCTION": 3} | [188, 10.0, 3, 18] | [78, 4.0, 1, 8] |
| stepwise | {"REQUEST_LIMIT": 3, "CORE_DESTRUCTION": 10, "TEAM_ELIMINATION": 6, "PROVIDER_FORFEIT": 1} | [462, 11.0, 1, 94] | [215, 5.0, 0, 46] |

## Requests and controls

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Provider requests | 149 | 169 | 712 |
| Attempted Luna turns | 114 | 94 | 230 |
| Completed Luna turns | 110 | 90 | 226 |
| First responses | 114 | 137 | 679 |
| First valid responses | 79 | 105 | 646 |
| Repairs | 35 | 32 | 33 |
| Successful repairs | 31 | 28 | 32 |
| Failed repairs | 4 | 4 | 1 |
| Provider failures excluding budget denial | 4 | 4 | 1 |
| Execution truncations | 46 | 6 | 0 |
| Initial execution invalidities | 46 | 43 | 0 |
| Bounded replans | 0 | 43 | 0 |
| Replacement repairs | 0 | 13 | 0 |
| Replacement invalidities | 0 | 3 | 0 |
| Second execution invalidities | 0 | 6 | 0 |
| AP recovered | 0 | 77 | 0 |
| Decisions including denied budgets | 114 | 137 | 682 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 7.4500 | 1.3070 | 1.2818 | 1.9211 | {"target outside action range": 26, "destination is occupied, blocked, unchanged, or beyond move range": 4, "blocked line of sight": 10, "impact outside Fireball range/board": 5, "invalid target ACTIVE/DOWNED status": 1} |
| bounded | 8.4500 | 1.7979 | 1.7333 | 2.5638 | {"target outside action range": 26, "blocked line of sight": 9, "impact outside Fireball range/board": 7, "invalid target ACTIVE/DOWNED status": 5, "destination is occupied, blocked, unchanged, or beyond move range": 1, "actor must own an ACTIVE unit": 1} |
| stepwise | 35.6000 | 3.0957 | 3.1239 | 2.7609 | {} |

| Disjoint request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 114 | 94 | 0 |
| repair | 35 | 19 | 33 |
| bounded_replacement_planning | 0 | 43 | 0 |
| bounded_replacement_repair | 0 | 13 | 0 |
| stepwise_decisions | 0 | 0 | 679 |

Stepwise decisions in the request-purpose table exclude repair and budget-denied decisions. Repair includes initial-wave and Stepwise repairs; replacement repairs are separate. Requests/turn use attempted Luna turns. Truncations are execution-ending stops, not every invalidity that Bounded subsequently recovered.

| Bounded question | Observed |
| --- | --- |
| Replans | 43 |
| Positive-AP recoveries | 38 |
| Positive recovery fraction | 0.8837 |
| Total AP recovered | 77 |
| Mean AP/replan | 1.7907 |
| Second-invalidity rate | 0.1395 |
| Requests/turn | 1.7979 |
| Extra total requests vs Strict | 20 |
| Bounded/Strict total request ratio | 1.1342 |
| Bounded/Strict requests-per-turn ratio | 1.3756 |
| AP at each replan | [2, 3, 3, 1, 3, 2, 2, 4, 4, 4, 2, 2, 4, 3, 2, 4, 2, 2, 2, 3, 1, 4, 2, 2, 2, 2, 3, 4, 3, 3, 3, 2, 3, 3, 1, 3, 1, 1, 3, 3, 3, 4, 4] |
| AP recovered per replan | [2, 3, 2, 1, 0, 2, 2, 2, 3, 1, 2, 2, 3, 1, 2, 2, 2, 2, 1, 2, 0, 1, 2, 2, 2, 1, 3, 4, 3, 3, 3, 2, 2, 3, 0, 1, 1, 1, 2, 1, 3, 0, 0] |

| Stepwise question | Observed |
| --- | --- |
| count | 3 |
| fraction | 0.1500 |
| requests | 420 |
| request_share | 0.5899 |
| match_ids | ["MATCH-001-stepwise", "MATCH-009-stepwise", "MATCH-015-stepwise"] |
| Requests/Luna turn | 3.0957 |
| Decisions/Luna turn | 2.9652 |
| Requests after explicit EndTurn | 0 |

## AP and EndTurn

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| AP available | 570 | 470 | 1150 |
| AP executed | 348 | 384 | 1038 |

| AP reason | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 60 | 39 | 90 |
| CLEAN_PLAN_COMPLETE | 8 | 7 | 0 |
| EXECUTION_TRUNCATION | 124 | 12 | 0 |
| PROVIDER_FAILURE | 20 | 16 | 12 |
| TERMINAL | 10 | 12 | 10 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 7 |
| Actual provider-failure AP | 20 | 16 | 5 |

Generic PROVIDER_FAILURE includes budget denial in frozen controller telemetry; actual provider-failure AP is adjusted in the last row. Intentional, clean, truncation, provider, budget and terminal AP are not a composite quality score.

| Control | Explicit stops | Immediate | AP remaining distribution | Actions before stop | Damaging option left | Down option left | Replacement stops | Requests after EndTurn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 42 | 1 | {"0": 5, "5": 1, "1": 24, "2": 5, "3": 7} | {"4": 3, "0": 1, "2": 27, "1": 7, "3": 4} | 13 | 2 | 0 | 0 |
| bounded | 41 | 0 | {"2": 4, "0": 12, "1": 22, "3": 3} | {"2": 19, "3": 19, "1": 2, "4": 1} | 7 | 1 | 14 | 0 |
| stepwise | 43 | 10 | {"1": 28, "5": 10, "3": 2, "2": 3} | {"2": 31, "0": 10, "1": 2} | 5 | 0 | 0 | 0 |

Damaging/down opportunities are legal single actions simulated from the authoritative pre-EndTurn state. They flag potentially premature stops without claiming an action was strategically preferable. Exact stop records/opportunities are in supplemental-audit.json. No model judge or live counterfactual inference was used.

## Combat and tactics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Core damage dealt | 0 | 0 | 30 |
| Core damage received | 250 | 150 | 401 |
| Enemy unit damage | 377 | 403 | 2522 |
| Friendly unit damage | 119 | 199 | 168 |
| Enemy downs | 20 | 28 | 162 |
| Friendly downs | 5 | 8 | 7 |
| Downs received | 66 | 71 | 122 |
| Finishes | 1 | 4 | 9 |
| Revives | 8 | 11 | 78 |
| Snipe uses | 15 | 16 | 3 |
| Shield Bash uses | 14 | 10 | 16 |
| Shield Bash pushes | 12 | 8 | 3 |
| Fireball uses | 106 | 116 | 322 |
| Enemy Fireball damage | 154 | 172 | 1780 |
| Friendly Fireball damage | 119 | 199 | 168 |
| Empty Fireballs | 35 | 31 | 45 |
| Friendly-only Fireballs | 22 | 40 | 16 |
| Enemy-only Fireballs | 35 | 28 | 235 |
| Mixed Fireballs | 14 | 17 | 26 |
| Basic attacks | 12 | 17 | 170 |
| Core attacks | 0 | 0 | 6 |
| Moves | 59 | 57 | 23 |
| Heals | 4 | 10 | 14 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 50 | 46 | 447 |
| friendly_units_hit | 38 | 65 | 54 |
| enemy_damage | 154 | 172 | 1780 |
| friendly_damage | 119 | 199 | 168 |
| enemy_downs | 3 | 5 | 3 |
| friendly_downs | 5 | 8 | 7 |

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 132 | 135 | 26 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 10 | 11 | 1 |
| arena_snipe friendly_downs | 0 | 0 | 0 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 40 | 34 | 55 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 5 |
| arena_shield_bash friendly_downs | 0 | 0 | 0 |
| arena_shield_bash enemy_displacements | 12 | 8 | 3 |

| Heuristic mechanical total by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 250 | 150 | 401 |
| core_damage_received | 0 | 0 | 30 |
| enemy_units_downed | 61 | 63 | 115 |
| finish | 17 | 19 | 23 |
| revive | 14 | 15 | 144 |
| ap_executed | 411 | 404 | 1093 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 21.4968 | 15.3908 | 49.6531 |

Counts are exposure-dependent and can include repeated downs/revivals of the same unit. Heuristic inference is zero; measured heuristic computation is separate. Heuristic matchup strata are not pooled. Per-match engine command traces preserve all action effects.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 149 | 169 | 712 |
| input_tokens | 398098 | 459237 | 1779792 |
| cached_input_tokens | 187418 | 214092 | 326904 |
| output_tokens | 13037 | 13702 | 31326 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 411135 | 472939 | 1811118 |
| provider_latency_seconds | 274.6426 | 297.0363 | 1,140.2242 |
| backend_thinking_seconds | 290.0712 | 314.6471 | 1,199.9571 |

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
| strict | 7.4500 | 20,556.7500 | 1.3070 | 3,606.4474 | 2.4091 | 2.5445 | 339.6151 |
| bounded | 8.4500 | 23,646.9500 | 1.7979 | 5,031.2660 | 3.1600 | 3.3473 | 356.5765 |
| stepwise | 35.6000 | 90,555.9000 | 3.0957 | 7,874.4261 | 4.9575 | 5.2172 | 1,326.4137 |

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

Outcome patterns: `{"loss/loss/limit": 3, "loss/loss/loss": 15, "loss/loss/win": 2}`; all-three-same outcome triplets: 15.

`{"comparison": "bounded-strict", "pairs": 20, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 20}, "provider_forfeit_pairs": 6, "limit_pairs": 0, "median_paired_player_turn_difference": 1.5, "provider_requests_per_turn_ratio": 1.3755533342853061, "total_tokens_per_turn_ratio": 1.3950753867925043, "backend_thinking_seconds_per_turn_ratio": 1.3155156410397022, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 20, "win_gains": 2, "win_losses": 0, "win_rate_difference": 0.1, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 3, "loss/loss": 15, "win/loss": 2}, "provider_forfeit_pairs": 5, "limit_pairs": 3, "median_paired_player_turn_difference": 4.5, "provider_requests_per_turn_ratio": 1.721842037561101, "total_tokens_per_turn_ratio": 1.5650983576611635, "backend_thinking_seconds_per_turn_ratio": 1.558626399243094, "win_difference_bootstrap_95": null}`

| Slot | Side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-001 | red | ["loss", "loss", "limit"] | [8, 16, 140] | [11, 18, 94] | [8, 124] | [7, 76] |
| MATCH-002 | blue | ["loss", "loss", "loss"] | [12, 4, 13] | [21, 3, 10] | [-8, 9] | [-18, 7] |
| MATCH-003 | red | ["loss", "loss", "loss"] | [6, 7, 16] | [9, 10, 11] | [1, 9] | [1, 1] |
| MATCH-004 | blue | ["loss", "loss", "win"] | [8, 12, 15] | [12, 8, 7] | [4, 3] | [-4, -1] |
| MATCH-005 | red | ["loss", "loss", "loss"] | [4, 10, 16] | [7, 12, 11] | [6, 6] | [5, -1] |
| MATCH-006 | blue | ["loss", "loss", "loss"] | [26, 13, 15] | [33, 10, 10] | [-13, 2] | [-23, 0] |
| MATCH-007 | red | ["loss", "loss", "loss"] | [4, 9, 12] | [7, 9, 8] | [5, 3] | [2, -1] |
| MATCH-008 | blue | ["loss", "loss", "loss"] | [7, 9, 21] | [10, 10, 12] | [2, 12] | [0, 2] |
| MATCH-009 | red | ["loss", "loss", "limit"] | [6, 7, 140] | [9, 11, 94] | [1, 133] | [2, 83] |
| MATCH-010 | blue | ["loss", "loss", "loss"] | [4, 8, 15] | [5, 10, 10] | [4, 7] | [5, 0] |
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
| MATCH-001-bounded | red | loss/TEAM_ELIMINATION | [18, 8] | [16, 9] | [37, 6, 0, 1, 0, 1] | [0, 15] | [2, 0, 0] | 9e1d6d8856be427c587cd21d17076722eeb6d6ca8ed6913cf96b6a804ce9ac47 |
| MATCH-001-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [232, 2, 0, 0, 1, 0] | [0, 18] | [44, 0, 44] | dfa39cdbc2aaacf72499db1212dd3beaee614a8b3ae92a2c7da68e50105bbef6 |
| MATCH-001-strict | red | loss/CORE_DESTRUCTION | [11, 5] | [8, 5] | [12, 0, 0, 13, 0, 0] | [0, 30] | [1, 1, 0] | 4137bf08bcd3c276f4b61cb4e91860c155f17293dbbeb3396a8c0a3897335bb1 |
| MATCH-002-bounded | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [7, 0, 0, 0, 3, 0] | [0, 0] | [1, 0, 0] | e0217d3afc1feb10fde3e67ac7bb4f0440acfc52fe7c50ce81d5c21a72828db4 |
| MATCH-002-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [13, 5] | [13, 12, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | 630c70acca8b8f66c2c1601db2ee8fa9deb78a3afa493431f9e204f2895ca772 |
| MATCH-002-strict | blue | loss/TEAM_ELIMINATION | [21, 10] | [12, 11] | [29, 12, 0, 11, 0, 3] | [0, 0] | [2, 0, 0] | 8840d8e4fb865f614b27c4e5a367ca9d825a3f010f68e4380a7d2cbed17e745f |
| MATCH-003-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [7, 5] | [17, 5, 0, 0, 0, 3] | [0, 0] | [1, 0, 0] | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-003-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [16, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | cd8751d4e7780a5b961c75719b4311ef5f8d975b1207e056840a29b26a6c5a89 |
| MATCH-003-strict | red | loss/TEAM_ELIMINATION | [9, 4] | [6, 4] | [13, 1, 0, 6, 0, 0] | [0, 0] | [1, 0, 2] | 6989d7f26bba06449809a535ce93820e4f8ec05bda5a2c174435a9cb3e80f768 |
| MATCH-004-bounded | blue | loss/TEAM_ELIMINATION | [8, 3] | [12, 4] | [14, 4, 0, 2, 0, 0] | [0, 0] | [1, 0, 0] | 1f6efb7be975777850adcffae6099b787633e85e648068cd82468e34e45ade73 |
| MATCH-004-stepwise | blue | win/CORE_DESTRUCTION | [7, 3] | [15, 4] | [14, 2, 0, 0, 0, 4] | [30, 0] | [1, 0, 0] | a0b03604c518808ab021118078c94b4422474b2c5707eaa8537f89efe2beefe2 |
| MATCH-004-strict | blue | loss/TEAM_ELIMINATION | [12, 5] | [8, 6] | [22, 2, 1, 5, 0, 0] | [0, 15] | [1, 0, 0] | 30733168b5679b1dcb228bd7fe3b237068e63599a0380c15e38bb87a5d29f7a4 |
| MATCH-005-bounded | red | loss/TEAM_ELIMINATION | [12, 5] | [10, 6] | [29, 0, 0, 0, 0, 1] | [0, 15] | [2, 0, 3] | 99fd244b014bd5efba51b5a8b646c94d88367191b740fe5d7ffd1f9dc817b204 |
| MATCH-005-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [16, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [2, 1, 0] | 1437bfd8b6b9199d40b42b61ef9a252a750e012f0fafc1da20491237c954aba7 |
| MATCH-005-strict | red | loss/CORE_DESTRUCTION | [7, 3] | [4, 3] | [11, 2, 2, 0, 0, 0] | [0, 30] | [0, 0, 3] | c5d8f58675ae4bc3ae30544e13169e6c95f9a69e3473c3e4c3543f7cd12920ba |
| MATCH-006-bounded | blue | loss/TEAM_ELIMINATION | [10, 4] | [13, 5] | [20, 2, 1, 2, 0, 0] | [0, 0] | [2, 1, 0] | 7eb1c54a5637995a32241b5905709f19dfa6e4efb73ff82049decc5f9cee111b |
| MATCH-006-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [17, 8, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-006-strict | blue | loss/TEAM_ELIMINATION | [33, 16] | [26, 17] | [55, 14, 3, 10, 0, 3] | [0, 0] | [1, 0, 0] | 71550616ea60841abe25e92bcb74d1ec9efceff018ceb464d75e94a557d6dadd |
| MATCH-007-bounded | red | loss/CORE_DESTRUCTION | [9, 4] | [9, 4] | [17, 2, 1, 0, 0, 0] | [0, 30] | [1, 1, 0] | 67b44626028493b42e86b1007a381f62cada3552508befc1231a1c92b7ab329e |
| MATCH-007-stepwise | red | loss/TEAM_ELIMINATION | [8, 3] | [12, 4] | [17, 2, 0, 0, 0, 1] | [0, 5] | [1, 0, 0] | f8dc815981f09fa7d27d50daee9e419e59fce44f321bbb9876041f54ec294a59 |
| MATCH-007-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [4, 3] | [8, 1, 0, 6, 0, 0] | [0, 10] | [0, 0, 0] | ab50ee66a77f533eab8c0034407e8e20e2461e86a85de932d2f6ccd6269a596e |
| MATCH-008-bounded | blue | loss/TEAM_ELIMINATION | [10, 4] | [9, 5] | [16, 3, 3, 3, 0, 0] | [0, 0] | [2, 0, 0] | 2b4664c7d629c2a439affcc13da3372c90f4fe0b7da4f5a7bb395794596c5182 |
| MATCH-008-stepwise | blue | loss/CORE_DESTRUCTION | [12, 5] | [21, 6] | [24, 6, 0, 0, 0, 0] | [0, 30] | [3, 0, 1] | 20d0c27aa2e8c152f495ce36736ba335e689dbcbf40607c54ac8e3a3cc64ad5d |
| MATCH-008-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [7, 5] | [13, 0, 0, 12, 0, 0] | [0, 30] | [1, 0, 0] | dfdca7bef66800e6b7abf59a0edacc1de64271c94143fa8bb4654161857c1b9a |
| MATCH-009-bounded | red | loss/TEAM_ELIMINATION | [11, 5] | [7, 5] | [25, 0, 0, 0, 0, 0] | [0, 15] | [2, 0, 3] | 4a55a81299e93b50a50fb3758133d6fbd4a1bc785dbc8f905cc18cd99331b2ee |
| MATCH-009-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [228, 2, 0, 0, 5, 0] | [0, 18] | [44, 0, 26] | 7a6f5f92df9f3bd1ee6ad2a9f3f163e6ce4b9ef037f91dccf341f62183be1045 |
| MATCH-009-strict | red | loss/CORE_DESTRUCTION | [9, 4] | [6, 4] | [9, 0, 0, 11, 0, 0] | [0, 30] | [2, 0, 0] | 0691d5213a6486826c0d9c626234bd3ec531461c5afb5c6e8cf0d2cd3baee7c9 |
| MATCH-010-bounded | blue | loss/TEAM_ELIMINATION | [10, 4] | [8, 5] | [22, 3, 0, 0, 0, 0] | [0, 5] | [2, 0, 0] | b5486ef6bbe03f644f6c6f30c98651029a82558a27c33ceb05326ee71bb96034 |
| MATCH-010-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [17, 8, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-010-strict | blue | loss/PROVIDER_FORFEIT | [5, 2] | [4, 3] | [10, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | e07574029ad1d9b0c59a6d457e1c5bbe9ff68d4032edc6d4bd6c75f2c0746588 |
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
