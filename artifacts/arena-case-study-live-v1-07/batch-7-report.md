# Batch 7 standalone — INTERIM

**n=10/control, 30 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

## Execution and frozen integrity

This root adds Batch 7 to a copied, verified 180-match prefix, preserving all original earlier roots. Frozen resume starts at MATCH-061-strict, request 3156. No earlier request or match was rerun. Scope stops at --through-batch 7. No within-batch interruption recovery was used. Batches 6–8 have separate mandatory integrity gates; no later batch starts before the preceding gate passes. Batch 9 is not authorized or executed.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-07 --through-batch 7 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-07/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-07/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-07/repair-forensics.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-07/interim-report.py
```

postprocess.py calls the unchanged frozen verifier, full-prefix integrity/replay verifier and analyzer for cumulative and batch==7 cohorts. Supplemental scripts are offline derived audits; frozen metrics and analysis remain unchanged.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Batch 7 schedule SHA-256 | 2c001155d36885b7a12e6c148719b45138562b1100e5f87b7ceca1bbc341df85 |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Source-bound files | 140 |

Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.

Batch 7: schedule entries 181–210, MATCH-061–070, five Red/five Blue per control. Independent 1,700-request batch ceiling, per-control 300/500/900 and per-match 50/80/140; global 15,000. One bounded replan. Natural terminal precedence and 200-player-turn/100-round limits remain frozen. No winner on request limit; provider exhaustion forfeits without fallback.

Final frozen verifier: `{"success": true, "completed_matches": 210, "replay_verified": 210, "completed_requests": 3911, "reserved_requests": 3911, "pending_requests": 0}`. Previous roots verified: `{"artifacts\\arena-case-study-live-v1-01": 2524, "artifacts\\arena-case-study-live-v1-02": 4527, "artifacts\\arena-case-study-live-v1-03": 6476, "artifacts\\arena-case-study-live-v1-04": 9306, "artifacts\\arena-case-study-live-v1-05": 11213, "artifacts\\arena-case-study-live-v1-06": 13687}`; copied immutable prefix files verified: 13605. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.

| Control | Intended | Started/sealed | Side counts | Terminal causes |
| --- | --- | --- | --- | --- |
| strict | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 5, "CORE_DESTRUCTION": 3, "PROVIDER_FORFEIT": 2} |
| bounded | 10 | 10 | {"red": 5, "blue": 5} | {"PROVIDER_FORFEIT": 4, "TEAM_ELIMINATION": 4, "CORE_DESTRUCTION": 2} |
| stepwise | 10 | 10 | {"red": 5, "blue": 5} | {"CORE_DESTRUCTION": 6, "REQUEST_LIMIT": 3, "TEAM_ELIMINATION": 1} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.2059 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.8542 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 1 | 6 | 3 | 0.1000 | [0.017876213095072896, 0.4041500267952385] | 3.0155 |
| Heuristic vs stepwise | 6 | 1 | 3 | 0.6000 | [0.31267376973365824, 0.8318196702937638] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 5, 0] | [0, 0.43448246478317476] |
| strict | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | red | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| stepwise | red | [0, 2, 3] | [0, 0.43448246478317476] |
| stepwise | blue | [1, 4, 0] | [0.03622410863243014, 0.6244653702374747] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 2 | 0 | 0 | 0 | [136, 11.0, [3, 52]] | [60, 4.5, [1, 25]] |
| bounded | 4 | 0 | 0 | 0 | [96, 8.5, [1, 16]] | [40, 3.5, [0, 7]] |
| stepwise | 0 | 3 | 0 | 0 | [388, 12.0, [10, 94]] | [185, 5.5, [4, 46]] |

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
| 4 | strict | 15/39 | 15 | 13 | 2 | 0.8667 | 2 |
| 4 | bounded | 20/65 | 20 | 17 | 3 | 0.8500 | 3 |
| 4 | stepwise | 17/528 | 17 | 17 | 0 | 1.0000 | 0 |
| 5 | strict | 14/41 | 14 | 12 | 2 | 0.8571 | 2 |
| 5 | bounded | 18/73 | 18 | 12 | 6 | 0.6667 | 6 |
| 5 | stepwise | 16/267 | 16 | 15 | 1 | 0.9375 | 1 |
| 6 | strict | 9/39 | 9 | 4 | 5 | 0.4444 | 5 |
| 6 | bounded | 20/104 | 20 | 15 | 5 | 0.7500 | 5 |
| 6 | stepwise | 19/384 | 19 | 19 | 0 | 1.0000 | 0 |
| 7 | strict | 14/68 | 14 | 12 | 2 | 0.8571 | 2 |
| 7 | bounded | 20/69 | 20 | 16 | 4 | 0.8000 | 4 |
| 7 | stepwise | 22/563 | 22 | 22 | 0 | 1.0000 | 0 |
| cumulative | strict | 108/369 | 108 | 91 | 17 | 0.8426 | 17 |
| cumulative | bounded | 126/495 | 126 | 100 | 26 | 0.7937 | 26 |
| cumulative | stepwise | 121/2692 | 121 | 117 | 4 | 0.9669 | 4 |

Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).

Batch/cohort 1 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 2 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 3 patterns: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 4 patterns: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 5 patterns: `{"initial_categories": {"invalid_reference": 7, "invalid_ability": 1, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 8}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 8}, "repair_identified_action_types": {"unavailable": 1, "snipe": 2, "revive": 1, "attack": 2, "fireball": 3}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 6, "invalid_ability -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 6 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 3, "ap_budget": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 9}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 9}, "repair_identified_action_types": {"unavailable": 1, "fireball": 3, "revive": 4, "snipe": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "schema_validation -> invalid_reference": 3, "invalid_reference -> invalid_reference": 5, "ap_budget -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 7 patterns: `{"initial_categories": {"invalid_reference": 4, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 6}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 6}, "repair_identified_action_types": {"revive": 3, "snipe": 2, "attack": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 4, "ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort cumulative patterns: `{"initial_categories": {"ap_budget": 4, "schema_validation": 9, "invalid_reference": 33, "invalid_ability": 1}, "repair_categories": {"invalid_reference": 42, "schema_validation": 5}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 41, "AP_VIOLATION": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 10, "revive": 15, "unavailable": 5, "move": 1, "fireball": 10, "attack": 6}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 4, "schema_validation -> invalid_reference": 7, "invalid_reference -> schema_validation": 3, "invalid_reference -> invalid_reference": 30, "schema_validation -> schema_validation": 2, "invalid_ability -> invalid_reference": 1}}`. Tags may overlap.

## Requests and bounded recovery

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 82 | 89 | 585 |
| turns | 68 | 48 | 194 |
| completed_turns | 66 | 44 | 191 |
| repairs | 14 | 20 | 22 |
| repair_success | 12 | 16 | 22 |
| repair_failure | 2 | 4 | 0 |
| execution_truncations | 30 | 4 | 0 |
| initial_execution_invalidities | 30 | 21 | 0 |
| replans | 0 | 21 | 0 |
| ap_recovered | 0 | 39 | 0 |
| replacement_repairs | 0 | 6 | 0 |
| replacement_invalidities | 0 | 1 | 0 |
| second_invalidities | 0 | 4 | 0 |
| decisions | 68 | 69 | 566 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 68 | 48 | 0 |
| repair | 14 | 14 | 22 |
| bounded_replacement_planning | 0 | 21 | 0 |
| bounded_replacement_repair | 0 | 6 | 0 |
| stepwise_decisions | 0 | 0 | 563 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 8.2000 | 1.2059 | 1.1818 | 1.9118 | {"target outside action range": 10, "blocked line of sight": 15, "invalid target ACTIVE/DOWNED status": 1, "impact outside Fireball range/board": 1, "destination is occupied, blocked, unchanged, or beyond move range": 2, "target already has full HP": 1} |
| bounded | 8.9000 | 1.8542 | 1.7955 | 2.3750 | {"target outside action range": 15, "impact outside Fireball range/board": 3, "target already has full HP": 1, "destination is occupied, blocked, unchanged, or beyond move range": 2, "invalid target ACTIVE/DOWNED status": 1, "blocked line of sight": 3} |
| stepwise | 58.5000 | 3.0155 | 3.0366 | 2.7216 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 21 |
| positive | 18 |
| positive_fraction | 0.8571 |
| ap_total | 39 |
| mean_ap_per_replan | 1.8571 |
| median_ap_per_replan | 2 |
| ap_at_replan | [2, 2, 3, 3, 1, 3, 2, 4, 4, 4, 2, 3, 4, 1, 3, 2, 2, 1, 3, 2, 4] |
| ap_recovered | [2, 0, 3, 2, 1, 2, 2, 2, 3, 2, 2, 3, 3, 0, 3, 2, 2, 0, 1, 1, 3] |
| Replan rate | 0.4375 |
| Second invalidity rate | 0.1905 |
| Replacement explicit EndTurns | 8 |
| Replacement failures | 1 |
| Extra requests vs Strict | 7 |
| Request premium vs Strict (%) | 8.5366 |
| Extra provider seconds vs Strict | 24.4653 |
| Extra tokens vs Strict | 19697 |
| Extra requests / recovered AP (descriptive) | 0.1795 |
| Strict minus Bounded final truncations | 26 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 3 |
| fraction | 0.3000 |
| requests | 420 |
| request_share | 0.7179 |
| match_ids | ["MATCH-063-stepwise", "MATCH-067-stepwise", "MATCH-069-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 89 | 585 |
| total_tokens | 248890 | 1502645 |
| provider_latency_seconds | 166.1316 | 804.6312 |
| provider_requests/match | 8.9000 | 58.5000 |
| total_tokens/match | 24,889.0000 | 150,264.5000 |
| provider_requests/turn | 1.8542 | 3.0155 |
| total_tokens/turn | 5,185.2083 | 7,745.5928 |
| provider_latency_seconds/turn | 3.4611 | 4.1476 |
| W/L/no-result | [0, 10, 0] | [1, 6, 3] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-063-stepwise | red | [94, 46, 47] | [230, 137] | [140, 1, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-067-stepwise | red | [92, 45, 46] | [228, 137] | [140, 2, 1] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-069-stepwise | red | [94, 46, 47] | [232, 138] | [140, 0, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 340 | 240 | 970 |
| ap_executed | 209 | 174 | 889 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 30 | 40 | 69 |
| CLEAN_PLAN_COMPLETE | 4 | 2 | 0 |
| EXECUTION_TRUNCATION | 78 | 6 | 0 |
| PROVIDER_FAILURE | 10 | 17 | 5 |
| TERMINAL | 9 | 1 | 7 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 5 |
| Actual provider-failure AP | 10 | 17 | 0 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 27 | 0 | {"3": 2, "1": 14, "2": 5, "0": 6} | {"1": 2, "2": 13, "3": 12} | 8 | 1 | 0 |
| bounded | 26 | 1 | {"2": 9, "1": 7, "0": 6, "4": 1, "3": 2, "5": 1} | {"2": 11, "3": 11, "1": 3, "0": 1} | 11 | 9 | 0 |
| stepwise | 35 | 6 | {"1": 23, "5": 6, "3": 4, "2": 2} | {"2": 26, "0": 6, "1": 3} | 4 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 0 | 30 |
| core_damage_received | 140 | 145 | 243 |
| enemy_damage | 272 | 239 | 2455 |
| friendly_damage | 66 | 69 | 99 |
| enemy_units_downed | 16 | 13 | 144 |
| friendly_units_downed | 3 | 1 | 5 |
| units_downed_received | 30 | 31 | 59 |
| finish | 0 | 0 | 2 |
| revive | 3 | 5 | 38 |
| heal | 9 | 5 | 6 |
| snipe | 5 | 12 | 7 |
| shield_bash | 4 | 5 | 1 |
| shield_bash_pushes | 2 | 4 | 0 |
| fireball | 71 | 43 | 316 |
| empty_fireballs | 11 | 7 | 28 |
| friendly_only_fireballs | 18 | 12 | 19 |
| enemy_only_fireballs | 35 | 18 | 261 |
| mixed_fireballs | 7 | 6 | 8 |
| enemy_fireball_damage | 164 | 84 | 1954 |
| friendly_fireball_damage | 66 | 69 | 99 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 42 | 24 | 494 |
| friendly_units_hit | 25 | 20 | 35 |
| enemy_damage | 164 | 84 | 1954 |
| friendly_damage | 66 | 69 | 99 |
| enemy_downs | 2 | 3 | 2 |
| friendly_downs | 3 | 1 | 5 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-063-bounded", "arm": "bounded", "agent": "luna", "ordinal": 14, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-065-stepwise", "arm": "stepwise", "agent": "luna", "ordinal": 44, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 3, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-065-strict", "arm": "strict", "agent": "luna", "ordinal": 16, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 2, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-067-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 13, "friendly_units_hit": 0, "enemy_units_hit": 1, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 1, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-067-strict", "arm": "strict", "agent": "luna", "ordinal": 12, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-069-strict", "arm": "strict", "agent": "luna", "ordinal": 52, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 46 | 103 | 56 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 4 | 7 | 4 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 8 | 16 | 4 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 1 |
| arena_shield_bash enemy_displacements | 2 | 4 | 0 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 140 | 145 | 243 |
| core_damage_received | 0 | 0 | 30 |
| enemy_units_downed | 27 | 30 | 54 |
| finish | 10 | 13 | 12 |
| revive | 13 | 7 | 135 |
| ap_executed | 226 | 216 | 876 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 9.5050 | 6.6887 | 24.2153 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 82 | 89 | 585 |
| input_tokens | 222205 | 241797 | 1476772 |
| cached_input_tokens | 105148 | 112954 | 300878 |
| output_tokens | 6988 | 7093 | 25873 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 229193 | 248890 | 1502645 |
| provider_latency_seconds | 141.6663 | 166.1316 | 804.6312 |
| backend_thinking_seconds | 151.7266 | 176.9800 | 863.9808 |

| Resource | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Batch 5 | Batch 6 | Batch 7 | Cumulative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| provider_requests | 583 | 447 | 437 | 684 | 429 | 575 | 756 | 3911 |
| input_tokens | 1492199 | 1144928 | 1144996 | 1704836 | 1110699 | 1414932 | 1940774 | 9953364 |
| cached_input_tokens | 390703 | 337711 | 378495 | 402732 | 515698 | 311921 | 518980 | 2856240 |
| output_tokens | 32764 | 25301 | 25531 | 35519 | 24637 | 30906 | 39954 | 214612 |
| reasoning_tokens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 1170527 | 1740355 | 1135336 | 1445838 | 1980728 | 10167976 |
| provider_latency_seconds | 963.2223 | 748.6807 | 726.2118 | 1,081.6293 | 680.1648 | 893.1586 | 1,112.4291 | 6,205.4967 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 773.5757 | 1,138.0684 | 725.1686 | 955.1774 | 1,192.6873 | 6,589.3530 |

| Control | Requests/match | Tokens/match | Provider sec/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 8.2000 | 22,919.3000 | 14.1666 | 1.2059 | 3,370.4853 | 2.0833 | 2.2313 | 180.6352 |
| bounded | 8.9000 | 24,889.0000 | 16.6132 | 1.8542 | 5,185.2083 | 3.4611 | 3.6871 | 199.3790 |
| stepwise | 58.5000 | 150,264.5000 | 80.4631 | 3.0155 | 7,745.5928 | 4.1476 | 4.4535 | 962.8134 |

| Batch | Observed process wall seconds upper bound | Start UTC | Completion observed UTC |
| --- | --- | --- | --- |
| 1 | 1,160.4115 | 2026-09-14T13:55:14.5492481Z | 2026-09-14T14:14:34.9607496Z |
| 2 | 1,013.4124 | 2026-09-14T14:41:07.0220353Z | 2026-09-14T14:58:00.4344287Z |
| 3 | 1,070.4722 | 2026-09-14T15:15:33.2411670Z | 2026-09-14T15:33:23.7133549Z |
| 4 | 1,468.7011 | 2026-09-14T15:49:31.0663785Z | 2026-09-14T16:13:59.767443+00:00 |
| 5 | 1,086.4948 | 2026-09-14T16:21:20.9995992Z | 2026-09-14T16:39:27.494440+00:00 |
| 6 | 1,448.3484 | 2026-09-14T17:09:50.182916+00:00 | 2026-09-14T17:33:58.531287+00:00 |
| 7 | 1,782.9197 | 2026-09-14T17:43:18.792749+00:00 | 2026-09-14T18:13:01.712487+00:00 |

Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.

## Updated projection from cumulative rates

| provider_requests | Observed | Mean/match | Remaining 30/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 477 | 6.8143 | 204.4286 | 681.4286 | [2, 36] | [60, 1080] | [537, 1557] |
| bounded | 621 | 8.8714 | 266.1429 | 887.1429 | [2, 49] | [60, 1470] | [681, 2091] |
| stepwise | 2813 | 40.1857 | 1,205.5714 | 4,018.5714 | [2, 140] | [60, 4200] | [2873, 7013] |

Combined provider_requests: remaining 90 central **1,676.143**; full 300 central **5,587.143**. Full-study sensitivity [4091, 10661].

| total_tokens | Observed | Mean/match | Remaining 30/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 1339677 | 19,138.2429 | 574,147.2857 | 1,913,824.2857 | [6150, 97697] | [184500, 2930910] | [1524177, 4270587] |
| bounded | 1703302 | 24,332.8857 | 729,986.5714 | 2,433,288.5714 | [6239, 101589] | [187170, 3047670] | [1890472, 4750972] |
| stepwise | 7124997 | 101,785.6714 | 3,053,570.1429 | 10,178,567.1429 | [6409, 364261] | [192270, 10927830] | [7317267, 18052827] |

Combined total_tokens: remaining 90 central **4,357,704.000**; full 300 central **14,525,680.000**. Full-study sensitivity [10731916, 27074386].

| provider_latency_seconds | Observed | Mean/match | Remaining 30/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 881.6723 | 12.5953 | 377.8596 | 1,259.5319 | [3.2305263999733143, 60.84210030012764] | [96.91579199919943, 1825.2630090038292] | [978.5881250989623, 2706.935342103592] |
| bounded | 1,110.9523 | 15.8707 | 476.1224 | 1,587.0747 | [2.902137700060848, 75.62964820029447] | [87.06413100182544, 2268.889446008834] | [1198.016446101945, 3379.8417611089535] |
| stepwise | 4,212.8721 | 60.1839 | 1,805.5166 | 6,018.3887 | [3.1789701000088826, 224.93943329993635] | [95.36910300026648, 6748.182998998091] | [4308.241186801984, 10961.055082799809] |

Combined provider_latency_seconds: remaining 90 central **2,659.499**; full 300 central **8,864.995**. Full-study sensitivity [6484.845758002892, 17047.832186012354].

Provider hours: remaining **0.7387**, full **2.4625**.

Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.

If future workloads resemble observed batches, remaining 3 batches span 0.845–1.486 process wall hours; full study 3.353–3.994 hours. This workload illustration excludes later analysis; growing prefix verification and service conditions can add time.

## Matched triplet patterns and differences

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/loss": 6, "loss/loss/limit": 3, "loss/loss/win": 1}`; all-three-same outcome triplets: 6.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 5, "limit_pairs": 0, "median_paired_player_turn_difference": 0.0, "provider_requests_per_turn_ratio": 1.5376016260162604, "total_tokens_per_turn_ratio": 1.5384159492945537, "backend_thinking_seconds_per_turn_ratio": 1.652456831993726, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 1, "win_losses": 0, "win_rate_difference": 0.1, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 6, "limit/loss": 3, "win/loss": 1}, "provider_forfeit_pairs": 4, "limit_pairs": 3, "median_paired_player_turn_difference": 7.0, "provider_requests_per_turn_ratio": 1.6263176184408663, "total_tokens_per_turn_ratio": 1.4937862252732028, "backend_thinking_seconds_per_turn_ratio": 1.2078680429634476, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-061 | red | ["loss", "loss", "loss"] | [4, 6, 17] | [7, 6, 11] | [2, 11] | [-1, 5] |
| MATCH-062 | blue | ["loss", "loss", "loss"] | [7, 4, 15] | [10, 1, 10] | [-3, 11] | [-9, 9] |
| MATCH-063 | red | ["loss", "loss", "limit"] | [4, 12, 140] | [7, 14, 94] | [8, 128] | [7, 80] |
| MATCH-064 | blue | ["loss", "loss", "loss"] | [4, 8, 13] | [3, 7, 10] | [4, 5] | [4, 3] |
| MATCH-065 | red | ["loss", "loss", "loss"] | [8, 5, 67] | [16, 6, 44] | [-3, 62] | [-10, 38] |
| MATCH-066 | blue | ["loss", "loss", "win"] | [8, 10, 22] | [14, 10, 13] | [2, 12] | [-4, 3] |
| MATCH-067 | red | ["loss", "loss", "limit"] | [6, 9, 140] | [12, 13, 92] | [3, 131] | [1, 79] |
| MATCH-068 | blue | ["loss", "loss", "loss"] | [4, 13, 15] | [3, 16, 10] | [9, 2] | [13, -6] |
| MATCH-069 | red | ["loss", "loss", "limit"] | [30, 7, 140] | [52, 7, 94] | [-23, 133] | [-45, 87] |
| MATCH-070 | blue | ["loss", "loss", "loss"] | [7, 15, 16] | [12, 16, 10] | [8, 1] | [4, -6] |

## Per-match evidence

| Match | Side | Outcome/cause | Turns/rounds | Requests/Luna turns | AP executed; I/C/X/P/T unused | Core damage dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-061-bounded | red | loss/PROVIDER_FORFEIT | [6, 2] | [6, 3] | [8, 2, 0, 0, 5, 0] | [0, 20] | [0, 0, 0] | 5aee1b1794e1b6dc743a16d85d01a198a78480f48e8367fc0c63f789e104d5d4 |
| MATCH-061-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [17, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [2, 1, 0] | 66e6ab61ed729cd4daaae7b07c11986ce303d2604082954462236f12e165e9f3 |
| MATCH-061-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [4, 3] | [9, 4, 0, 2, 0, 0] | [0, 5] | [0, 0, 0] | c85aae76941ff976e99aba55ed65a8249617386f6bbb03a82a415241bed4a754 |
| MATCH-062-bounded | blue | loss/PROVIDER_FORFEIT | [1, 0] | [4, 1] | [3, 0, 0, 0, 2, 0] | [0, 0] | [1, 0, 0] | 040a5e5553ea7b31bda3b59a5d490a7f4d6403582462418ed8cdd2c1a516cf9a |
| MATCH-062-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [18, 7, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | 27294a13bb02689f97b7fb6c72fabd9dee1bb795b88ed314ae764030f811c13e |
| MATCH-062-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [7, 5] | [18, 2, 0, 5, 0, 0] | [0, 30] | [3, 0, 0] | 4078a21075193d26651cb1836cc8062da932b2b2f82f425091ca4b9e1094f7c9 |
| MATCH-063-bounded | red | loss/TEAM_ELIMINATION | [14, 6] | [12, 7] | [29, 5, 0, 0, 0, 1] | [0, 20] | [1, 0, 0] | ceb2e7a808a993556007bef5e8f759363fddd379cf51e09f70db21cc1bac60e0 |
| MATCH-063-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [230, 2, 0, 0, 3, 0] | [0, 18] | [44, 0, 33] | a66b4f227cdf789884e24bbd8715c9f345e02a4573c920fe6cad24be086069a2 |
| MATCH-063-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [4, 3] | [9, 1, 0, 5, 0, 0] | [0, 5] | [0, 0, 0] | fbdfd8450e85871ea25cae23d5771bcb8ead05c197e6cf98c2cdfa0eaa735481 |
| MATCH-064-bounded | blue | loss/PROVIDER_FORFEIT | [7, 3] | [8, 4] | [14, 0, 0, 1, 5, 0] | [0, 0] | [2, 0, 0] | 9b38b9317828b36382d554a3afe1303b64b90b8b5935e564654fb9e39bfd59da |
| MATCH-064-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [13, 5] | [11, 14, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | 3c5d633acdc1e7f71cb3291c5f584a9eb592d0e22a1f5ba7fc312dfff4948008 |
| MATCH-064-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [3, 0, 0, 2, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-065-bounded | red | loss/PROVIDER_FORFEIT | [6, 2] | [5, 3] | [9, 1, 0, 0, 5, 0] | [0, 20] | [0, 0, 0] | 5aee1b1794e1b6dc743a16d85d01a198a78480f48e8367fc0c63f789e104d5d4 |
| MATCH-065-stepwise | red | loss/TEAM_ELIMINATION | [44, 21] | [67, 22] | [97, 10, 0, 0, 0, 3] | [0, 21] | [3, 1, 2] | 63d1fa8d6c92cbbd1f0e65b50ffc2ae0f5be87842953e485de21b5974197ca56 |
| MATCH-065-strict | red | loss/TEAM_ELIMINATION | [16, 7] | [8, 8] | [32, 3, 0, 2, 0, 3] | [0, 15] | [2, 0, 3] | 31bf70b936b21c9cda115b0c7deee624c010152bdc5e525d9665640438c587a4 |
| MATCH-066-bounded | blue | loss/CORE_DESTRUCTION | [10, 4] | [10, 5] | [16, 7, 0, 2, 0, 0] | [0, 30] | [1, 0, 0] | 69177ca22c9e3ba3d8e27c375c237c36c112ffd118d648eac7001e21ddc7e2a3 |
| MATCH-066-stepwise | blue | win/CORE_DESTRUCTION | [13, 6] | [22, 7] | [16, 15, 0, 0, 0, 4] | [30, 18] | [2, 0, 0] | 0a598aeb42148cbf014aaabdeb1d9bcba1039967d01ea63a6f6b6a663db7dcb9 |
| MATCH-066-strict | blue | loss/CORE_DESTRUCTION | [14, 6] | [8, 7] | [19, 5, 3, 8, 0, 0] | [0, 30] | [4, 0, 0] | 537f84f597b5b1fee9ff32c32ea9067b03da57ff0739e84ae10912ce19a03c87 |
| MATCH-067-bounded | red | loss/TEAM_ELIMINATION | [13, 6] | [9, 6] | [28, 2, 0, 0, 0, 0] | [0, 15] | [3, 0, 3] | 800a609f8e9239ae10cab839e6d048d584dd8e50ac794d81506be588779710e5 |
| MATCH-067-stepwise | red | limit/REQUEST_LIMIT | [92, 45] | [140, 46] | [228, 1, 0, 0, 1, 0] | [0, 18] | [43, 0, 3] | efcbc7d17212c472ef8ceb0273f6859a965fcef3809cdbe9f73230c78bd30b54 |
| MATCH-067-strict | red | loss/TEAM_ELIMINATION | [12, 5] | [6, 6] | [15, 1, 0, 11, 0, 3] | [0, 5] | [1, 0, 0] | fb0d8e64fec5263ad17cc76e69f593aff79cf753d1a76900c89afe44017a05c5 |
| MATCH-068-bounded | blue | loss/CORE_DESTRUCTION | [16, 7] | [13, 8] | [31, 8, 1, 0, 0, 0] | [0, 30] | [2, 0, 2] | ae9dabaf5aec7ee4cc023241b237be889f7dc891163f09b0e98310488bf6d724 |
| MATCH-068-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [14, 11, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | d51240769bea81d80ee13dc26d573946b59f97748c19c203cb762b9290108089 |
| MATCH-068-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [4, 1, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | 524e8b6ef69164541f547904632840dd46aaacc41c1b7b7ffc69d7643fee5af8 |
| MATCH-069-bounded | red | loss/TEAM_ELIMINATION | [7, 3] | [7, 3] | [10, 5, 0, 0, 0, 0] | [0, 0] | [0, 0, 0] | e0631810f62f091d8b578f236f3d5e207b253bbd5be73b2041f4e94603ac8768 |
| MATCH-069-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [232, 2, 0, 0, 1, 0] | [0, 18] | [44, 0, 0] | 9c9bde65b94ece72f5f8a45d56d6bfe92880038b90310c3a3f760dbb3e0b9962 |
| MATCH-069-strict | red | loss/TEAM_ELIMINATION | [52, 25] | [30, 26] | [81, 7, 0, 39, 0, 3] | [0, 20] | [1, 0, 0] | d2031e4abcf14400207d087b5830fb2a4a38e7c30ada4cc3344fa3c5cde98f9c |
| MATCH-070-bounded | blue | loss/TEAM_ELIMINATION | [16, 7] | [15, 8] | [26, 10, 1, 3, 0, 0] | [0, 10] | [3, 0, 0] | da13994f74674bde17c9560a1bcd9bd88c8fc7a96c1468ce6631e98f21c05309 |
| MATCH-070-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [16, 5] | [19, 6, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-070-strict | blue | loss/CORE_DESTRUCTION | [12, 5] | [7, 6] | [19, 6, 1, 4, 0, 0] | [0, 30] | [4, 0, 0] | 8bf419014856fcc9d55d3d74a4879c20d918f88219ad5a80666c9ea29a024ee9 |

## Decision and limitations

Additional side-specific forfeits/caps and cost rates, Stepwise capped/uncapped means and sorted distribution, complete triplet classifications and cap gameplay: [focused comparisons](focused-comparisons.md).

See [decision.md](decision.md) for interpretation and continuation recommendation. INTERIM at n=70/control; frozen confirmatory inference waits for 100/control. No tuning or replacement of failed/capped games. [Figures](figures.md); machine metrics: interim-metrics.json; command audit: supplemental-audit.json; repair evidence: repair-forensics.json.
