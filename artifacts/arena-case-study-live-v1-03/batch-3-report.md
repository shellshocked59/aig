# Batch 3 standalone — INTERIM

**n=10/control, 30 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

## Execution and frozen integrity

Only Batch 3 was newly executed. Original Batch 1 and Batch 2 roots are preserved byte-for-byte. The verified 60-match prefix was copied to arena-case-study-live-v1-03 so cumulative aggregate updates do not overwrite old reports. Frozen resume continued at MATCH-021 Stepwise (Red), request 1031. No earlier match/request was rerun; no within-Batch-3 interruption recovery was needed. Scope ended at --through-batch 3. Batch 4 was not started.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-03 --through-batch 3 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/repair-forensics.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-03/interim-report.py
```

postprocess.py calls the unchanged frozen source verifier, full-prefix integrity/replay verifier and analyzer for the cumulative prefix and batch==3 subset. Other scripts are separate offline derived audits, without provider calls or changes to frozen metrics/analysis.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Batch 3 schedule SHA-256 | 1be9412983919f2eee272de27118f34ff76d706f40fa3419280bf87aa8c23d92 |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Source-bound files | 140 |

Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.

Batch 3 is schedule entries 61–90, MATCH-021–030, five Red/five Blue matches per control. Budget: 1,700 new requests; per-control batch 300/500/900; per-match 50/80/140; global 15,000. One bounded replan maximum. Every request reserves ledger capacity before transport. Limits produce no winner; provider exhaustion is a forfeit with no fallback. Termination bounds remain 200 started player turns / 100 completed rounds.

Final frozen verifier: `{"success": true, "completed_matches": 90, "replay_verified": 90, "completed_requests": 1467, "reserved_requests": 1467, "pending_requests": 0}`. Previous roots verified: `{"artifacts\\arena-case-study-live-v1-01": 2524, "artifacts\\arena-case-study-live-v1-02": 4527}`; copied immutable prefix files verified: 4455. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.

| Control | Intended | Started/sealed | Side counts | Terminal causes |
| --- | --- | --- | --- | --- |
| strict | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 3, "PROVIDER_FORFEIT": 2, "CORE_DESTRUCTION": 5} |
| bounded | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 5, "PROVIDER_FORFEIT": 4, "CORE_DESTRUCTION": 1} |
| stepwise | 10 | 10 | {"red": 5, "blue": 5} | {"REQUEST_LIMIT": 1, "PROVIDER_FORFEIT": 2, "CORE_DESTRUCTION": 6, "TEAM_ELIMINATION": 1} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.3088 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.9091 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 0 | 9 | 1 | 0.0000 | [0, 0.2775327998628892] | 3.0645 |
| Heuristic vs stepwise | 9 | 0 | 1 | 0.9000 | [0.5958499732047615, 0.9821237869049271] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 5, 0] | [0, 0.43448246478317476] |
| strict | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | red | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| stepwise | red | [0, 4, 1] | [0, 0.43448246478317476] |
| stepwise | blue | [0, 5, 0] | [0, 0.43448246478317476] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 2 | 0 | 0 | 0 | [139, 9.5, [5, 57]] | [63, 4.0, [2, 28]] |
| bounded | 4 | 0 | 0 | 0 | [66, 7.0, [2, 11]] | [26, 3.0, [0, 5]] |
| stepwise | 2 | 1 | 0 | 0 | [188, 10.5, [1, 94]] | [87, 4.5, [0, 46]] |

## Repair reliability — all batches

| Cohort | Control | First invalid/first responses | Repairs attempted | Succeeded | Exhausted | Success rate | Repair-exhaustion forfeits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | strict | 24/61 | 24 | 23 | 1 | 0.9583 | 1 |
| 1 | bounded | 19/76 | 19 | 18 | 1 | 0.9474 | 1 |
| 1 | stepwise | 16/387 | 16 | 16 | 0 | 1.0000 | 0 |
| 2 | strict | 11/53 | 11 | 8 | 3 | 0.7273 | 3 |
| 2 | bounded | 13/61 | 13 | 10 | 3 | 0.7692 | 3 |
| 2 | stepwise | 17/292 | 17 | 16 | 1 | 0.9412 | 1 |
| 3 | strict | 21/68 | 21 | 19 | 2 | 0.9048 | 2 |
| 3 | bounded | 16/47 | 16 | 12 | 4 | 0.7500 | 4 |
| 3 | stepwise | 14/271 | 14 | 12 | 2 | 0.8571 | 2 |
| cumulative | strict | 56/182 | 56 | 50 | 6 | 0.8929 | 6 |
| cumulative | bounded | 48/184 | 48 | 40 | 8 | 0.8333 | 8 |
| cumulative | stepwise | 47/950 | 47 | 44 | 3 | 0.9362 | 3 |

Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).

Batch/cohort 1 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 2 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 3 patterns: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort cumulative patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 3, "invalid_reference": 13}, "repair_categories": {"invalid_reference": 15, "schema_validation": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 14, "AP_VIOLATION": 2, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 3, "revive": 5, "unavailable": 2, "move": 1, "fireball": 3, "attack": 3}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 2, "invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 12, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

## Requests and bounded recovery

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 89 | 63 | 285 |
| turns | 68 | 33 | 93 |
| completed_turns | 66 | 29 | 90 |
| repairs | 21 | 16 | 14 |
| repair_success | 19 | 12 | 12 |
| repair_failure | 2 | 4 | 2 |
| execution_truncations | 36 | 3 | 0 |
| initial_execution_invalidities | 36 | 14 | 0 |
| replans | 0 | 14 | 0 |
| ap_recovered | 0 | 26 | 0 |
| replacement_repairs | 0 | 6 | 0 |
| replacement_invalidities | 0 | 1 | 0 |
| second_invalidities | 0 | 3 | 0 |
| decisions | 68 | 47 | 272 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 68 | 33 | 0 |
| repair | 21 | 10 | 14 |
| bounded_replacement_planning | 0 | 14 | 0 |
| bounded_replacement_repair | 0 | 6 | 0 |
| stepwise_decisions | 0 | 0 | 271 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 8.9000 | 1.3088 | 1.2879 | 1.7794 | {"target outside action range": 17, "invalid target ACTIVE/DOWNED status": 2, "blocked line of sight": 9, "impact outside Fireball range/board": 5, "destination is occupied, blocked, unchanged, or beyond move range": 2, "actor must own an ACTIVE unit": 1} |
| bounded | 6.3000 | 1.9091 | 1.8621 | 2.2727 | {"target outside action range": 9, "blocked line of sight": 3, "impact outside Fireball range/board": 3, "destination is occupied, blocked, unchanged, or beyond move range": 1, "invalid target ACTIVE/DOWNED status": 1} |
| stepwise | 28.5000 | 3.0645 | 3.0778 | 2.6882 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 14 |
| positive | 13 |
| positive_fraction | 0.9286 |
| ap_total | 26 |
| mean_ap_per_replan | 1.8571 |
| ap_at_replan | [2, 4, 4, 4, 2, 4, 3, 2, 4, 1, 3, 2, 4, 1] |
| ap_recovered | [2, 2, 4, 3, 2, 0, 2, 2, 1, 1, 2, 2, 2, 1] |
| Replan rate | 0.4242 |
| Second invalidity rate | 0.2143 |
| Replacement explicit EndTurns | 1 |
| Replacement failures | 1 |
| Extra requests vs Strict | -26 |
| Request premium vs Strict (%) | -29.2135 |
| Extra provider seconds vs Strict | -52.3798 |
| Extra tokens vs Strict | -68891 |
| Extra requests / recovered AP (descriptive) | -1.0000 |
| Strict minus Bounded final truncations | 33 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 1 |
| fraction | 0.1000 |
| requests | 140 |
| request_share | 0.4912 |
| match_ids | ["MATCH-021-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 63 | 285 |
| total_tokens | 180209 | 741218 |
| provider_latency_seconds | 109.5414 | 454.7492 |
| provider_requests/match | 6.3000 | 28.5000 |
| total_tokens/match | 18,020.9000 | 74,121.8000 |
| provider_requests/turn | 1.9091 | 3.0645 |
| total_tokens/turn | 5,460.8788 | 7,970.0860 |
| provider_latency_seconds/turn | 3.3194 | 4.8898 |
| W/L/no-result | [0, 10, 0] | [0, 9, 1] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-021-stepwise | red | [94, 46, 47] | [233, 139] | [140, 0, 1] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 340 | 165 | 465 |
| ap_executed | 193 | 117 | 415 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 40 | 15 | 42 |
| CLEAN_PLAN_COMPLETE | 2 | 5 | 0 |
| EXECUTION_TRUNCATION | 95 | 6 | 0 |
| PROVIDER_FAILURE | 10 | 19 | 8 |
| TERMINAL | 0 | 3 | 0 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 1 |
| Actual provider-failure AP | 10 | 19 | 7 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 23 | 0 | {"3": 4, "1": 12, "4": 1, "2": 6} | {"1": 5, "2": 15, "3": 3} | 11 | 1 | 0 |
| bounded | 10 | 0 | {"1": 7, "2": 1, "3": 2} | {"3": 3, "2": 5, "1": 2} | 4 | 0 | 0 |
| stepwise | 19 | 5 | {"1": 12, "5": 5, "2": 1, "3": 1} | {"2": 13, "0": 5, "1": 1} | 1 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 0 | 0 |
| core_damage_received | 160 | 68 | 216 |
| enemy_damage | 297 | 120 | 1074 |
| friendly_damage | 89 | 67 | 46 |
| enemy_units_downed | 13 | 8 | 63 |
| friendly_units_downed | 3 | 1 | 1 |
| units_downed_received | 30 | 28 | 21 |
| finish | 0 | 0 | 2 |
| revive | 3 | 5 | 8 |
| heal | 10 | 1 | 7 |
| snipe | 8 | 9 | 5 |
| shield_bash | 4 | 4 | 9 |
| shield_bash_pushes | 3 | 4 | 2 |
| fireball | 61 | 28 | 152 |
| empty_fireballs | 15 | 6 | 21 |
| friendly_only_fireballs | 16 | 14 | 2 |
| enemy_only_fireballs | 26 | 5 | 112 |
| mixed_fireballs | 4 | 3 | 17 |
| enemy_fireball_damage | 176 | 26 | 877 |
| friendly_fireball_damage | 89 | 67 | 46 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 53 | 8 | 220 |
| friendly_units_hit | 26 | 19 | 20 |
| enemy_damage | 176 | 26 | 877 |
| friendly_damage | 89 | 67 | 46 |
| enemy_downs | 2 | 3 | 1 |
| friendly_downs | 3 | 1 | 1 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-027-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 71 | 70 | 40 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 5 | 5 | 4 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 10 | 12 | 32 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 2 |
| arena_shield_bash enemy_displacements | 3 | 4 | 2 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 160 | 68 | 216 |
| core_damage_received | 0 | 0 | 0 |
| enemy_units_downed | 27 | 27 | 20 |
| finish | 11 | 6 | 8 |
| revive | 10 | 5 | 56 |
| ap_executed | 243 | 148 | 453 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 14.8199 | 7.0222 | 16.0753 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 89 | 63 | 285 |
| input_tokens | 241451 | 174927 | 728618 |
| cached_input_tokens | 100790 | 91811 | 185894 |
| output_tokens | 7649 | 5282 | 12600 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 249100 | 180209 | 741218 |
| provider_latency_seconds | 161.9212 | 109.5414 | 454.7492 |
| backend_thinking_seconds | 172.1797 | 117.8974 | 483.4986 |

| Resource | Batch 1 | Batch 2 | Batch 3 | Cumulative |
| --- | --- | --- | --- | --- |
| provider_requests | 583 | 447 | 437 | 1467 |
| input_tokens | 1492199 | 1144928 | 1144996 | 3782123 |
| cached_input_tokens | 390703 | 337711 | 378495 | 1106909 |
| output_tokens | 32764 | 25301 | 25531 | 83596 |
| reasoning_tokens | 0 | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 1170527 | 3865719 |
| provider_latency_seconds | 963.2223 | 748.6807 | 726.2118 | 2,438.1149 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 773.5757 | 2,578.2511 |

| Control | Requests/match | Tokens/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 8.9000 | 24,910.0000 | 1.3088 | 3,663.2353 | 2.3812 | 2.5321 | 207.0121 |
| bounded | 6.3000 | 18,020.9000 | 1.9091 | 5,460.8788 | 3.3194 | 3.5726 | 136.1155 |
| stepwise | 28.5000 | 74,121.8000 | 3.0645 | 7,970.0860 | 4.8898 | 5.1989 | 535.5961 |

| Batch | Observed process wall seconds upper bound | Start UTC | Completion observed UTC |
| --- | --- | --- | --- |
| 1 | 1,160.4115 | 2026-09-14T13:55:14.5492481Z | 2026-09-14T14:14:34.9607496Z |
| 2 | 1,013.4124 | 2026-09-14T14:41:07.0220353Z | 2026-09-14T14:58:00.4344287Z |
| 3 | 1,070.4722 | 2026-09-14T15:15:33.2411670Z | 2026-09-14T15:33:23.7133549Z |

Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.

## Updated projection from cumulative rates

| provider_requests | Observed | Mean/match | Remaining 70/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 238 | 7.9333 | 555.3333 | 793.3333 | [2, 36] | [140, 2520] | [378, 2758] |
| bounded | 232 | 7.7333 | 541.3333 | 773.3333 | [2, 16] | [140, 1120] | [372, 1352] |
| stepwise | 997 | 33.2333 | 2,326.3333 | 3,323.3333 | [2, 140] | [140, 9800] | [1137, 10797] |

Combined provider_requests: remaining 210 central **3,423.000**; full 300 central **4,890.000**. Full-study sensitivity [1887, 14907].

| total_tokens | Observed | Mean/match | Remaining 70/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 660235 | 22,007.8333 | 1,540,548.3333 | 2,200,783.3333 | [6218, 97697] | [435260, 6838790] | [1095495, 7499025] |
| bounded | 653148 | 21,771.6000 | 1,524,012.0000 | 2,177,160.0000 | [6263, 43667] | [438410, 3056690] | [1091558, 3709838] |
| stepwise | 2552336 | 85,077.8667 | 5,955,450.6667 | 8,507,786.6667 | [6409, 363431] | [448630, 25440170] | [3000966, 27992506] |

Combined total_tokens: remaining 210 central **9,020,011.000**; full 300 central **12,885,730.000**. Full-study sensitivity [5188019, 39201369].

| provider_latency_seconds | Observed | Mean/match | Remaining 70/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 436.5637 | 14.5521 | 1,018.6487 | 1,455.2124 | [3.2305263999733143, 60.84210030012764] | [226.136847998132, 4258.947021008935] | [662.7005699981237, 4695.5107430089265] |
| bounded | 406.5777 | 13.5526 | 948.6814 | 1,355.2591 | [3.7967910999432206, 29.19422550010495] | [265.77537699602544, 2043.5957850073464] | [672.3531033954932, 2450.173511406814] |
| stepwise | 1,594.9734 | 53.1658 | 3,721.6046 | 5,316.5781 | [3.1789701000088826, 224.93943329993635] | [222.52790700062178, 15745.760330995545] | [1817.501324002049, 17340.733747996972] |

Combined provider_latency_seconds: remaining 210 central **5,688.935**; full 300 central **8,127.050**. Full-study sensitivity [3152.554997395666, 24486.418002412713].

Provider hours: remaining **1.5803**, full **2.2575**.

Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.

If future batch workloads resemble the three observed batches, seven remaining batches span 1.971–2.256 wall hours; full study 2.872–3.158 hours. This is a workload illustration, not a guaranteed bound: larger-prefix verification, provider conditions, caps and post-run analysis can add time.

## Matched triplet patterns and differences

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/limit": 1, "loss/loss/loss": 9}`; all-three-same outcome triplets: 9.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 5, "limit_pairs": 0, "median_paired_player_turn_difference": -2.0, "provider_requests_per_turn_ratio": 1.4586312563840653, "total_tokens_per_turn_ratio": 1.4907256426164497, "backend_thinking_seconds_per_turn_ratio": 1.410969197956183, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 1, "loss/loss": 9}, "provider_forfeit_pairs": 5, "limit_pairs": 1, "median_paired_player_turn_difference": 4.5, "provider_requests_per_turn_ratio": 1.6052227342549923, "total_tokens_per_turn_ratio": 1.459487809763538, "backend_thinking_seconds_per_turn_ratio": 1.45519710556577, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-021 | red | ["loss", "loss", "limit"] | [5, 6, 140] | [7, 5, 94] | [1, 134] | [-2, 89] |
| MATCH-022 | blue | ["loss", "loss", "loss"] | [36, 8, 4] | [57, 8, 1] | [-28, -4] | [-49, -7] |
| MATCH-023 | red | ["loss", "loss", "loss"] | [4, 5, 36] | [7, 7, 23] | [1, 31] | [0, 16] |
| MATCH-024 | blue | ["loss", "loss", "loss"] | [8, 4, 15] | [12, 3, 10] | [-4, 11] | [-9, 7] |
| MATCH-025 | red | ["loss", "loss", "loss"] | [3, 12, 28] | [7, 11, 17] | [9, 16] | [4, 6] |
| MATCH-026 | blue | ["loss", "loss", "loss"] | [8, 7, 13] | [14, 7, 10] | [-1, 6] | [-7, 3] |
| MATCH-027 | red | ["loss", "loss", "loss"] | [6, 7, 16] | [11, 10, 11] | [1, 9] | [-1, 1] |
| MATCH-028 | blue | ["loss", "loss", "loss"] | [6, 3, 2] | [5, 3, 1] | [-3, -1] | [-2, -2] |
| MATCH-029 | red | ["loss", "loss", "loss"] | [6, 2, 16] | [9, 2, 11] | [-4, 14] | [-7, 9] |
| MATCH-030 | blue | ["loss", "loss", "loss"] | [7, 9, 15] | [10, 10, 10] | [2, 6] | [0, 0] |

## Per-match evidence

| Match | Side | Outcome/cause | Turns/rounds | Requests/Luna turns | AP executed; I/C/X/P/T unused | Core damage dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-021-bounded | red | loss/TEAM_ELIMINATION | [5, 2] | [6, 2] | [8, 0, 2, 0, 0, 0] | [0, 0] | [0, 0, 0] | 262f9b49b00b51017eb8e0ccd11f56e77e84272322f4e7630c4992426ab1f543 |
| MATCH-021-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [233, 1, 0, 0, 1, 0] | [0, 18] | [44, 0, 0] | ef6d56e5c963c57eb7ccc4731204e13429ea9d8e17284ba5d7d708aebda33e85 |
| MATCH-021-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [5, 3] | [9, 4, 0, 2, 0, 0] | [0, 5] | [0, 0, 0] | fbdfd8450e85871ea25cae23d5771bcb8ead05c197e6cf98c2cdfa0eaa735481 |
| MATCH-022-bounded | blue | loss/TEAM_ELIMINATION | [8, 3] | [8, 4] | [17, 3, 0, 0, 0, 0] | [0, 18] | [1, 0, 1] | 53394d3a7f5e11eb2ae9622bdcbc9801771ac0b94380e7c1fd8ed5240023e199 |
| MATCH-022-stepwise | blue | loss/PROVIDER_FORFEIT | [1, 0] | [4, 1] | [3, 0, 0, 0, 2, 0] | [0, 0] | [1, 0, 0] | 040a5e5553ea7b31bda3b59a5d490a7f4d6403582462418ed8cdd2c1a516cf9a |
| MATCH-022-strict | blue | loss/PROVIDER_FORFEIT | [57, 28] | [36, 29] | [82, 22, 2, 34, 5, 0] | [0, 0] | [3, 0, 2] | 439fd2bb02b33e7065b934df0257266c439d7d4c056b1380e1196397f8ef2f74 |
| MATCH-023-bounded | red | loss/TEAM_ELIMINATION | [7, 3] | [5, 3] | [11, 4, 0, 0, 0, 0] | [0, 0] | [0, 0, 0] | 21015faf395cfd393cafc53c7a4fea07bb4d9885699fab0c7f9789b7da9b6772 |
| MATCH-023-stepwise | red | loss/CORE_DESTRUCTION | [23, 11] | [36, 11] | [52, 3, 0, 0, 0, 0] | [0, 30] | [3, 1, 6] | fb5a4a413bd08b0e45d29dbe0a04d229ab944e58bc58b8770886cee17784fab7 |
| MATCH-023-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [4, 3] | [9, 4, 0, 2, 0, 0] | [0, 5] | [0, 0, 0] | c85aae76941ff976e99aba55ed65a8249617386f6bbb03a82a415241bed4a754 |
| MATCH-024-bounded | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [5, 1, 0, 0, 4, 0] | [0, 0] | [0, 0, 0] | 1db9a83397b56e4d9e380153396887be576f5b0e7f35b7329b8d59799fc90c2c |
| MATCH-024-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [17, 8, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-024-strict | blue | loss/CORE_DESTRUCTION | [12, 5] | [8, 6] | [18, 0, 0, 12, 0, 0] | [0, 30] | [1, 0, 1] | e365273fcb108601f2b073ff31a66123cdeaba4392e028d8865b5f5ec94ff4f5 |
| MATCH-025-bounded | red | loss/TEAM_ELIMINATION | [11, 5] | [12, 5] | [18, 1, 3, 3, 0, 0] | [0, 20] | [2, 0, 3] | c4627309f16168a9a651c814f6e8e7d61e3ffff890a67eb9f1f97c799860e774 |
| MATCH-025-stepwise | red | loss/TEAM_ELIMINATION | [17, 8] | [28, 8] | [34, 6, 0, 0, 0, 0] | [0, 18] | [4, 1, 1] | fbfc457ae7de7a43ec0abbe405cedb55a1f90976f872cba0e4994eb2572eeae8 |
| MATCH-025-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [3, 3] | [10, 3, 0, 2, 0, 0] | [0, 0] | [0, 0, 0] | fb1139ce703c48d015f162a25a2b8525adc14a90b04ec92a86bf042a55b78017 |
| MATCH-026-bounded | blue | loss/PROVIDER_FORFEIT | [7, 3] | [7, 4] | [14, 0, 0, 1, 5, 0] | [0, 0] | [2, 0, 0] | 9b38b9317828b36382d554a3afe1303b64b90b8b5935e564654fb9e39bfd59da |
| MATCH-026-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [13, 5] | [13, 12, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | b34b6b4ff4d34a8630b7f613d15cb45ba503f5ccdbecf821e076bcb0c2809eca |
| MATCH-026-strict | blue | loss/CORE_DESTRUCTION | [14, 6] | [8, 7] | [19, 1, 0, 15, 0, 0] | [0, 30] | [2, 0, 0] | a207d94289e3918d36d0d4e63c75d085e59a2bce322dc9ae169dfa15ad3c4998 |
| MATCH-027-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [7, 5] | [17, 5, 0, 0, 0, 3] | [0, 0] | [1, 0, 0] | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-027-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [16, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | 9190667dd60c2269cec348ee735973b80a6d072d2f71cfa614525c1fa3dd4075 |
| MATCH-027-strict | red | loss/CORE_DESTRUCTION | [11, 5] | [6, 5] | [15, 2, 0, 8, 0, 0] | [0, 30] | [3, 0, 0] | 351eed6a498d5339bc4f7e7bb3340b1279212f6ebb8b8d2442fcb7cbe3d9c3b8 |
| MATCH-028-bounded | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-028-stepwise | blue | loss/PROVIDER_FORFEIT | [1, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d |
| MATCH-028-strict | blue | loss/PROVIDER_FORFEIT | [5, 2] | [6, 3] | [5, 0, 0, 5, 5, 0] | [0, 0] | [0, 0, 0] | 94c7dcabf381b9dd63e5947a4b09e24ea0594e26f8ef2d3c918341f7912b7d70 |
| MATCH-029-bounded | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-029-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [16, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | 694610ac9c30fdf6c4af25efe73afa833619106312d874df7d353cbd5e2fba2b |
| MATCH-029-strict | red | loss/CORE_DESTRUCTION | [9, 4] | [6, 4] | [14, 2, 0, 4, 0, 0] | [0, 30] | [2, 0, 0] | 2a267556ec9d7b7e88f5413cfdefd77aea10908548956d1f1a203285f44ad4d6 |
| MATCH-030-bounded | blue | loss/CORE_DESTRUCTION | [10, 4] | [9, 5] | [22, 1, 0, 2, 0, 0] | [0, 30] | [1, 0, 1] | 59ff81b34d39906ff92d730bda071f7c282cfb956702dab72fa4b3d0a02b4624 |
| MATCH-030-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [15, 10, 0, 0, 0, 0] | [0, 30] | [3, 0, 1] | 67d91e3715d11717c762ba2c4227a5f0970aa212b0d480e65e9d4f295fbf28c0 |
| MATCH-030-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [7, 5] | [12, 2, 0, 11, 0, 0] | [0, 30] | [2, 0, 0] | 935a1e7c789850b2d4dfed3625dccbbe4f571bc204f7e039b62e1a4ffd4de110 |

## Decision and limitations

See [decision.md](decision.md) for PASS/PAUSE, all ten research-question answers and next authorization scope. Results remain interim at n=30/control. Frozen confirmatory analysis waits for 100/control. No tuning, replacement of failed/capped games, or next-batch execution occurred. Figures: [figures.md](figures.md); machine-readable metrics: interim-metrics.json; command audits: supplemental-audit.json; repair evidence: repair-forensics.json.
