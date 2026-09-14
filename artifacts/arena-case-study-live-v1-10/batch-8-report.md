# Batch 8 standalone — INTERIM

**n=10/control, 30 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

## Execution and frozen integrity

This root adds Batch 8 to a copied, verified 210-match prefix, preserving all original earlier roots. Frozen resume starts at MATCH-071-bounded, request 3912. No earlier request or match was rerun. Scope stops at --through-batch 8. No within-batch interruption recovery was used. Batches 6–8 have separate mandatory integrity gates; no later batch starts before the preceding gate passes. Batch 9 is not authorized or executed.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-08 --through-batch 8 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-08/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-08/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-08/repair-forensics.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-08/interim-report.py
```

postprocess.py calls the unchanged frozen verifier, full-prefix integrity/replay verifier and analyzer for cumulative and batch==8 cohorts. Supplemental scripts are offline derived audits; frozen metrics and analysis remain unchanged.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Batch 8 schedule SHA-256 | 0e21edff68114e6e190b10c13f9eee8b21a710860d8dd51f315dbc2d734c4a8e |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Source-bound files | 140 |

Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.

Batch 8: schedule entries 211–240, MATCH-071–080, five Red/five Blue per control. Independent 1,700-request batch ceiling, per-control 300/500/900 and per-match 50/80/140; global 15,000. One bounded replan. Natural terminal precedence and 200-player-turn/100-round limits remain frozen. No winner on request limit; provider exhaustion forfeits without fallback.

Final frozen verifier: `{"success": true, "completed_matches": 240, "replay_verified": 240, "completed_requests": 4479, "reserved_requests": 4479, "pending_requests": 0}`. Previous roots verified: `{"artifacts\\arena-case-study-live-v1-01": 2524, "artifacts\\arena-case-study-live-v1-02": 4527, "artifacts\\arena-case-study-live-v1-03": 6476, "artifacts\\arena-case-study-live-v1-04": 9306, "artifacts\\arena-case-study-live-v1-05": 11213, "artifacts\\arena-case-study-live-v1-06": 13687, "artifacts\\arena-case-study-live-v1-07": 16816}`; copied immutable prefix files verified: 16734. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.

| Control | Intended | Started/sealed | Side counts | Terminal causes |
| --- | --- | --- | --- | --- |
| strict | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 6, "CORE_DESTRUCTION": 1, "PROVIDER_FORFEIT": 3} |
| bounded | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 3, "CORE_DESTRUCTION": 4, "PROVIDER_FORFEIT": 3} |
| stepwise | 10 | 10 | {"red": 5, "blue": 5} | {"CORE_DESTRUCTION": 7, "REQUEST_LIMIT": 2, "TEAM_ELIMINATION": 1} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.3000 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.7619 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 0 | 8 | 2 | 0.0000 | [0, 0.2775327998628892] | 2.9928 |
| Heuristic vs stepwise | 8 | 0 | 2 | 0.8000 | [0.49016247153664183, 0.9433178485456247] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 5, 0] | [0, 0.43448246478317476] |
| strict | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | red | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| stepwise | red | [0, 3, 2] | [0, 0.43448246478317476] |
| stepwise | blue | [0, 5, 0] | [0, 0.43448246478317476] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 3 | 0 | 0 | 0 | [119, 9.0, [2, 54]] | [51, 3.5, [0, 26]] |
| bounded | 3 | 0 | 0 | 0 | [85, 8.5, [2, 13]] | [35, 3.5, [0, 6]] |
| stepwise | 0 | 2 | 0 | 0 | [281, 12.0, [6, 94]] | [132, 5.5, [2, 46]] |

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
| 8 | strict | 18/60 | 18 | 15 | 3 | 0.8333 | 3 |
| 8 | bounded | 15/59 | 15 | 12 | 3 | 0.8000 | 3 |
| 8 | stepwise | 16/400 | 16 | 16 | 0 | 1.0000 | 0 |
| cumulative | strict | 126/429 | 126 | 106 | 20 | 0.8413 | 20 |
| cumulative | bounded | 141/554 | 141 | 112 | 29 | 0.7943 | 29 |
| cumulative | stepwise | 137/3092 | 137 | 133 | 4 | 0.9708 | 4 |

Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).

Batch/cohort 1 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 2 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 3 patterns: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 4 patterns: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 5 patterns: `{"initial_categories": {"invalid_reference": 7, "invalid_ability": 1, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 8}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 8}, "repair_identified_action_types": {"unavailable": 1, "snipe": 2, "revive": 1, "attack": 2, "fireball": 3}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 6, "invalid_ability -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 6 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 3, "ap_budget": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 9}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 9}, "repair_identified_action_types": {"unavailable": 1, "fireball": 3, "revive": 4, "snipe": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "schema_validation -> invalid_reference": 3, "invalid_reference -> invalid_reference": 5, "ap_budget -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 7 patterns: `{"initial_categories": {"invalid_reference": 4, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 6}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 6}, "repair_identified_action_types": {"revive": 3, "snipe": 2, "attack": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 4, "ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 8 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 2, "invalid_reference": 3}, "repair_categories": {"invalid_reference": 6}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 2, "move": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 2, "invalid_reference -> invalid_reference": 3}}`. Tags may overlap.

Batch/cohort cumulative patterns: `{"initial_categories": {"ap_budget": 5, "schema_validation": 11, "invalid_reference": 36, "invalid_ability": 1}, "repair_categories": {"invalid_reference": 48, "schema_validation": 5}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 46, "AP_VIOLATION": 5, "OTHER_CURRENT_ACTION_VALIDATION": 2}, "repair_identified_action_types": {"snipe": 11, "revive": 17, "unavailable": 5, "move": 2, "fireball": 12, "attack": 6}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 5, "schema_validation -> invalid_reference": 9, "invalid_reference -> schema_validation": 3, "invalid_reference -> invalid_reference": 33, "schema_validation -> schema_validation": 2, "invalid_ability -> invalid_reference": 1}}`. Tags may overlap.

## Requests and bounded recovery

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 78 | 74 | 416 |
| turns | 60 | 42 | 139 |
| completed_turns | 57 | 39 | 137 |
| repairs | 18 | 15 | 16 |
| repair_success | 15 | 12 | 16 |
| repair_failure | 3 | 3 | 0 |
| execution_truncations | 12 | 3 | 0 |
| initial_execution_invalidities | 12 | 17 | 0 |
| replans | 0 | 17 | 0 |
| ap_recovered | 0 | 36 | 0 |
| replacement_repairs | 0 | 8 | 0 |
| replacement_invalidities | 0 | 1 | 0 |
| second_invalidities | 0 | 3 | 0 |
| decisions | 60 | 59 | 402 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 60 | 42 | 0 |
| repair | 18 | 7 | 16 |
| bounded_replacement_planning | 0 | 17 | 0 |
| bounded_replacement_repair | 0 | 8 | 0 |
| stepwise_decisions | 0 | 0 | 400 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 7.8000 | 1.3000 | 1.2632 | 1.7000 | {"target outside action range": 9, "blocked line of sight": 1, "impact outside Fireball range/board": 2} |
| bounded | 7.4000 | 1.7619 | 1.7179 | 2.6667 | {"target outside action range": 12, "blocked line of sight": 3, "impact outside Fireball range/board": 4, "invalid target ACTIVE/DOWNED status": 1} |
| stepwise | 41.6000 | 2.9928 | 3.0292 | 2.7266 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 17 |
| positive | 16 |
| positive_fraction | 0.9412 |
| ap_total | 36 |
| mean_ap_per_replan | 2.1176 |
| median_ap_per_replan | 2 |
| ap_at_replan | [2, 4, 2, 4, 2, 2, 4, 2, 2, 3, 4, 4, 2, 2, 3, 2, 4] |
| ap_recovered | [2, 3, 2, 4, 0, 2, 2, 2, 2, 2, 2, 4, 2, 2, 1, 1, 3] |
| Replan rate | 0.4048 |
| Second invalidity rate | 0.1765 |
| Replacement explicit EndTurns | 5 |
| Replacement failures | 1 |
| Extra requests vs Strict | -4 |
| Request premium vs Strict (%) | -5.1282 |
| Extra provider seconds vs Strict | 6.9582 |
| Extra tokens vs Strict | 2783 |
| Extra requests / recovered AP (descriptive) | -0.1111 |
| Strict minus Bounded final truncations | 9 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 2 |
| fraction | 0.2000 |
| requests | 280 |
| request_share | 0.6731 |
| match_ids | ["MATCH-075-stepwise", "MATCH-079-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 74 | 416 |
| total_tokens | 208636 | 1055229 |
| provider_latency_seconds | 131.8318 | 572.5491 |
| provider_requests/match | 7.4000 | 41.6000 |
| total_tokens/match | 20,863.6000 | 105,522.9000 |
| provider_requests/turn | 1.7619 | 2.9928 |
| total_tokens/turn | 4,967.5238 | 7,591.5755 |
| provider_latency_seconds/turn | 3.1389 | 4.1191 |
| W/L/no-result | [0, 10, 0] | [0, 8, 2] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-075-stepwise | red | [94, 46, 47] | [230, 137] | [140, 1, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-079-stepwise | red | [94, 46, 47] | [228, 136] | [140, 2, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 300 | 210 | 695 |
| ap_executed | 180 | 168 | 638 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 60 | 23 | 49 |
| CLEAN_PLAN_COMPLETE | 5 | 0 | 0 |
| EXECUTION_TRUNCATION | 31 | 6 | 0 |
| PROVIDER_FAILURE | 15 | 12 | 8 |
| TERMINAL | 9 | 1 | 0 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 8 |
| Actual provider-failure AP | 15 | 12 | 0 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 34 | 3 | {"1": 22, "0": 1, "3": 7, "5": 3, "2": 1} | {"2": 22, "3": 2, "1": 7, "0": 3} | 11 | 0 | 0 |
| bounded | 19 | 0 | {"1": 9, "2": 4, "3": 2, "0": 4} | {"3": 10, "2": 8, "4": 1} | 8 | 4 | 0 |
| stepwise | 21 | 6 | {"1": 13, "5": 6, "3": 2} | {"2": 13, "0": 6, "1": 2} | 2 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 10 | 0 |
| core_damage_received | 55 | 145 | 266 |
| enemy_damage | 170 | 163 | 1594 |
| friendly_damage | 63 | 83 | 93 |
| enemy_units_downed | 8 | 10 | 106 |
| friendly_units_downed | 3 | 1 | 1 |
| units_downed_received | 28 | 35 | 93 |
| finish | 0 | 0 | 1 |
| revive | 0 | 9 | 75 |
| heal | 0 | 9 | 5 |
| snipe | 6 | 9 | 8 |
| shield_bash | 4 | 7 | 4 |
| shield_bash_pushes | 4 | 3 | 0 |
| fireball | 72 | 38 | 176 |
| empty_fireballs | 10 | 9 | 18 |
| friendly_only_fireballs | 18 | 18 | 6 |
| enemy_only_fireballs | 44 | 7 | 134 |
| mixed_fireballs | 0 | 4 | 18 |
| enemy_fireball_damage | 104 | 41 | 1017 |
| friendly_fireball_damage | 63 | 83 | 93 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 44 | 11 | 255 |
| friendly_units_hit | 18 | 26 | 30 |
| enemy_damage | 104 | 41 | 1017 |
| friendly_damage | 63 | 83 | 93 |
| enemy_downs | 3 | 2 | 2 |
| friendly_downs | 3 | 1 | 1 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-071-strict", "arm": "strict", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-075-bounded", "arm": "bounded", "agent": "luna", "ordinal": 8, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-075-strict", "arm": "strict", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-079-strict", "arm": "strict", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 56 | 77 | 64 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 5 | 6 | 5 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 10 | 16 | 14 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 1 |
| arena_shield_bash enemy_displacements | 4 | 3 | 0 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 55 | 145 | 266 |
| core_damage_received | 0 | 10 | 0 |
| enemy_units_downed | 25 | 34 | 92 |
| finish | 7 | 11 | 9 |
| revive | 5 | 7 | 98 |
| ap_executed | 167 | 205 | 685 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 5.9703 | 7.6903 | 11.4060 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 78 | 74 | 416 |
| input_tokens | 199749 | 202568 | 1036907 |
| cached_input_tokens | 102492 | 100303 | 179027 |
| output_tokens | 6104 | 6068 | 18322 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 205853 | 208636 | 1055229 |
| provider_latency_seconds | 124.8736 | 131.8318 | 572.5491 |
| backend_thinking_seconds | 132.2395 | 139.6624 | 607.2137 |

| Resource | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Batch 5 | Batch 6 | Batch 7 | Batch 8 | Cumulative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| provider_requests | 583 | 447 | 437 | 684 | 429 | 575 | 756 | 568 | 4479 |
| input_tokens | 1492199 | 1144928 | 1144996 | 1704836 | 1110699 | 1414932 | 1940774 | 1439224 | 11392588 |
| cached_input_tokens | 390703 | 337711 | 378495 | 402732 | 515698 | 311921 | 518980 | 381822 | 3238062 |
| output_tokens | 32764 | 25301 | 25531 | 35519 | 24637 | 30906 | 39954 | 30494 | 245106 |
| reasoning_tokens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 1170527 | 1740355 | 1135336 | 1445838 | 1980728 | 1469718 | 11637694 |
| provider_latency_seconds | 963.2223 | 748.6807 | 726.2118 | 1,081.6293 | 680.1648 | 893.1586 | 1,112.4291 | 829.2545 | 7,034.7512 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 773.5757 | 1,138.0684 | 725.1686 | 955.1774 | 1,192.6873 | 879.1155 | 7,468.4684 |

| Control | Requests/match | Tokens/match | Provider sec/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 7.8000 | 20,585.3000 | 12.4874 | 1.3000 | 3,430.8833 | 2.0812 | 2.2040 | 151.9934 |
| bounded | 7.4000 | 20,863.6000 | 13.1832 | 1.7619 | 4,967.5238 | 3.1389 | 3.3253 | 158.8550 |
| stepwise | 41.6000 | 105,522.9000 | 57.2549 | 2.9928 | 7,591.5755 | 4.1191 | 4.3684 | 662.2757 |

| Batch | Observed process wall seconds upper bound | Start UTC | Completion observed UTC |
| --- | --- | --- | --- |
| 1 | 1,160.4115 | 2026-09-14T13:55:14.5492481Z | 2026-09-14T14:14:34.9607496Z |
| 2 | 1,013.4124 | 2026-09-14T14:41:07.0220353Z | 2026-09-14T14:58:00.4344287Z |
| 3 | 1,070.4722 | 2026-09-14T15:15:33.2411670Z | 2026-09-14T15:33:23.7133549Z |
| 4 | 1,468.7011 | 2026-09-14T15:49:31.0663785Z | 2026-09-14T16:13:59.767443+00:00 |
| 5 | 1,086.4948 | 2026-09-14T16:21:20.9995992Z | 2026-09-14T16:39:27.494440+00:00 |
| 6 | 1,448.3484 | 2026-09-14T17:09:50.182916+00:00 | 2026-09-14T17:33:58.531287+00:00 |
| 7 | 1,782.9197 | 2026-09-14T17:43:18.792749+00:00 | 2026-09-14T18:13:01.712487+00:00 |
| 8 | 1,461.0164 | 2026-09-14T18:24:40.507010+00:00 | 2026-09-14T18:49:01.523411+00:00 |

Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.

## Updated projection from cumulative rates

| provider_requests | Observed | Mean/match | Remaining 20/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 555 | 6.9375 | 138.7500 | 693.7500 | [2, 36] | [40, 720] | [595, 1275] |
| bounded | 695 | 8.6875 | 173.7500 | 868.7500 | [2, 49] | [40, 980] | [735, 1675] |
| stepwise | 3229 | 40.3625 | 807.2500 | 4,036.2500 | [2, 140] | [40, 2800] | [3269, 6029] |

Combined provider_requests: remaining 60 central **1,119.750**; full 300 central **5,598.750**. Full-study sensitivity [4599, 8979].

| total_tokens | Observed | Mean/match | Remaining 20/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 1545530 | 19,319.1250 | 386,382.5000 | 1,931,912.5000 | [6150, 97697] | [123000, 1953940] | [1668530, 3499470] |
| bounded | 1911938 | 23,899.2250 | 477,984.5000 | 2,389,922.5000 | [6239, 101589] | [124780, 2031780] | [2036718, 3943718] |
| stepwise | 8180226 | 102,252.8250 | 2,045,056.5000 | 10,225,282.5000 | [6409, 364261] | [128180, 7285220] | [8308406, 15465446] |

Combined total_tokens: remaining 60 central **2,909,423.500**; full 300 central **14,547,117.500**. Full-study sensitivity [12013654, 22908634].

| provider_latency_seconds | Observed | Mean/match | Remaining 20/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 1,006.5459 | 12.5818 | 251.6365 | 1,258.1824 | [3.2305263999733143, 60.84210030012764] | [64.61052799946629, 1216.8420060025528] | [1071.1564735991415, 2223.387951602228] |
| bounded | 1,242.7841 | 15.5348 | 310.6960 | 1,553.4801 | [2.902137700060848, 75.62964820029447] | [58.04275400121696, 1512.5929640058894] | [1300.82683660154, 2755.3770466062124] |
| stepwise | 4,785.4212 | 59.8178 | 1,196.3553 | 5,981.7764 | [3.1789701000088826, 224.93943329993635] | [63.57940200017765, 4498.788665998727] | [4849.00056120177, 9284.20982520032] |

Combined provider_latency_seconds: remaining 60 central **1,758.688**; full 300 central **8,793.439**. Full-study sensitivity [7220.983871402452, 14262.97482340876].

Provider hours: remaining **0.4885**, full **2.4426**.

Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.

If future workloads resemble observed batches, remaining 2 batches span 0.563–0.991 process wall hours; full study 3.477–3.905 hours. This workload illustration excludes later analysis; growing prefix verification and service conditions can add time.

## Matched triplet patterns and differences

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/loss": 8, "loss/loss/limit": 2}`; all-three-same outcome triplets: 8.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 4, "limit_pairs": 0, "median_paired_player_turn_difference": 0.0, "provider_requests_per_turn_ratio": 1.3553113553113552, "total_tokens_per_turn_ratio": 1.447884794350476, "backend_thinking_seconds_per_turn_ratio": 1.50876034395526, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 8, "limit/loss": 2}, "provider_forfeit_pairs": 3, "limit_pairs": 2, "median_paired_player_turn_difference": 5.5, "provider_requests_per_turn_ratio": 1.6986194827921448, "total_tokens_per_turn_ratio": 1.5282413996715358, "backend_thinking_seconds_per_turn_ratio": 1.313701406034812, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-071 | red | ["loss", "loss", "loss"] | [5, 10, 17] | [10, 13, 13] | [5, 7] | [3, 0] |
| MATCH-072 | blue | ["loss", "loss", "loss"] | [4, 8, 9] | [8, 8, 6] | [4, 1] | [0, -2] |
| MATCH-073 | red | ["loss", "loss", "loss"] | [2, 3, 16] | [2, 2, 11] | [1, 13] | [0, 9] |
| MATCH-074 | blue | ["loss", "loss", "loss"] | [3, 9, 14] | [3, 12, 10] | [6, 5] | [9, -2] |
| MATCH-075 | red | ["loss", "loss", "limit"] | [7, 10, 140] | [10, 8, 94] | [3, 130] | [-2, 86] |
| MATCH-076 | blue | ["loss", "loss", "loss"] | [36, 7, 21] | [54, 10, 14] | [-29, 14] | [-44, 4] |
| MATCH-077 | red | ["loss", "loss", "loss"] | [4, 4, 29] | [7, 7, 19] | [0, 25] | [0, 12] |
| MATCH-078 | blue | ["loss", "loss", "loss"] | [8, 6, 16] | [12, 3, 10] | [-2, 10] | [-9, 7] |
| MATCH-079 | red | ["loss", "loss", "limit"] | [5, 9, 140] | [10, 13, 94] | [4, 131] | [3, 81] |
| MATCH-080 | blue | ["loss", "loss", "loss"] | [4, 8, 14] | [3, 9, 10] | [4, 6] | [6, 1] |

## Per-match evidence

| Match | Side | Outcome/cause | Turns/rounds | Requests/Luna turns | AP executed; I/C/X/P/T unused | Core damage dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-071-bounded | red | loss/TEAM_ELIMINATION | [13, 6] | [10, 6] | [28, 2, 0, 0, 0, 0] | [0, 20] | [2, 0, 2] | 1396ce404aa983cbd20c93a8b7eb91f918100efee2028ce961c81e9b3d3db0d8 |
| MATCH-071-stepwise | red | loss/CORE_DESTRUCTION | [13, 6] | [17, 6] | [24, 6, 0, 0, 0, 0] | [0, 30] | [3, 0, 1] | 66462674ac3a4f0186673a9ddc7389417504c8fd21fb8f2da735e813762db5c4 |
| MATCH-071-strict | red | loss/TEAM_ELIMINATION | [10, 4] | [5, 5] | [15, 2, 0, 5, 0, 3] | [0, 5] | [1, 0, 0] | 820b3ea4b1292e7690cbc3c0d8471fb6cdc49ab57cb78f406c038c275430ef21 |
| MATCH-072-bounded | blue | loss/CORE_DESTRUCTION | [8, 3] | [8, 4] | [18, 2, 0, 0, 0, 0] | [0, 30] | [2, 0, 0] | 4ede39d105003e968b6b6f3ec6da35d6ae504752472cb1a6bad79a7fc0f7b687 |
| MATCH-072-stepwise | blue | loss/CORE_DESTRUCTION | [6, 2] | [9, 3] | [10, 5, 0, 0, 0, 0] | [0, 30] | [0, 0, 0] | 9b0dbe90b2fab124226712b51116c305881725a8252917733b6f391fe8332d98 |
| MATCH-072-strict | blue | loss/CORE_DESTRUCTION | [8, 3] | [4, 4] | [14, 1, 0, 5, 0, 0] | [0, 30] | [1, 0, 0] | 61c8714a5f4f5b5e949230cf76896e226cb0575e50f3618a8e8da3610a813886 |
| MATCH-073-bounded | red | loss/PROVIDER_FORFEIT | [2, 0] | [3, 1] | [3, 0, 0, 0, 2, 0] | [0, 0] | [0, 0, 0] | 0ecf81f749b0fe4b6a3c42af077a558c4ad7bc67a0a9d331809bb7d668d93680 |
| MATCH-073-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [16, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | 038bd13a3d1e629941bbda7bb308ab56aec06fa05a96040fd31e1f21e0138f6f |
| MATCH-073-strict | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-074-bounded | blue | loss/CORE_DESTRUCTION | [12, 5] | [9, 6] | [20, 8, 0, 2, 0, 0] | [10, 30] | [1, 0, 0] | 60bc712582193851c181f90e5fb1125ce5e8a826f5d4d76d04a67109dbe3a59a |
| MATCH-074-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [14, 5] | [18, 7, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | da266ef0b1b29e4221a9fc89a9e951d5fe3675a3b67dd0b8f344d7f3161725b1 |
| MATCH-074-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-075-bounded | red | loss/TEAM_ELIMINATION | [8, 3] | [10, 4] | [18, 1, 0, 0, 0, 1] | [0, 5] | [1, 0, 0] | f8dc815981f09fa7d27d50daee9e419e59fce44f321bbb9876041f54ec294a59 |
| MATCH-075-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [230, 2, 0, 0, 3, 0] | [0, 18] | [44, 0, 44] | 67ed067d63ad05e49607a5d4f60eebf12aa7fa51e7a149012b2c94a8ad8c83c6 |
| MATCH-075-strict | red | loss/TEAM_ELIMINATION | [10, 4] | [7, 5] | [17, 3, 0, 2, 0, 3] | [0, 5] | [1, 0, 0] | 820b3ea4b1292e7690cbc3c0d8471fb6cdc49ab57cb78f406c038c275430ef21 |
| MATCH-076-bounded | blue | loss/CORE_DESTRUCTION | [10, 4] | [7, 5] | [21, 2, 0, 2, 0, 0] | [0, 30] | [2, 0, 0] | cf48e27e0463a901369ba2acd1e158ba81beb3f10d99c6ffde0048269862c6b2 |
| MATCH-076-stepwise | blue | loss/TEAM_ELIMINATION | [14, 6] | [21, 7] | [27, 8, 0, 0, 0, 0] | [0, 20] | [4, 0, 1] | d04377d62f1d5daee00369577132139ee9759044d19ecaf37c8257b2c04fb7cd |
| MATCH-076-strict | blue | loss/TEAM_ELIMINATION | [54, 26] | [36, 27] | [82, 46, 2, 5, 0, 0] | [0, 0] | [1, 0, 0] | dd2e9fd4232dc448620f1410ec68bc00d0d6d54cefa3f146a80090b0d2e13308 |
| MATCH-077-bounded | red | loss/CORE_DESTRUCTION | [7, 3] | [4, 3] | [14, 1, 0, 0, 0, 0] | [0, 30] | [0, 0, 2] | 2f9cbbcbc7cf69722932b0523b479d1c647349c8c2e464a1d563572cda8819b8 |
| MATCH-077-stepwise | red | loss/CORE_DESTRUCTION | [19, 9] | [29, 9] | [42, 3, 0, 0, 0, 0] | [0, 30] | [3, 1, 2] | 1329d35d8a5de81501eedcc3d0c43a86c815b975def7b7bca1fb6dff657ad9a5 |
| MATCH-077-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [4, 3] | [9, 4, 0, 2, 0, 0] | [0, 5] | [0, 0, 0] | fbdfd8450e85871ea25cae23d5771bcb8ead05c197e6cf98c2cdfa0eaa735481 |
| MATCH-078-bounded | blue | loss/PROVIDER_FORFEIT | [3, 1] | [6, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-078-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [16, 5] | [20, 5, 0, 0, 0, 0] | [0, 30] | [3, 0, 1] | f5c659b435d12383837dd682e2b2a85efe573fe3c9bd9edf66c59115a3fbb6ff |
| MATCH-078-strict | blue | loss/TEAM_ELIMINATION | [12, 5] | [8, 6] | [19, 1, 3, 7, 0, 0] | [0, 10] | [1, 0, 0] | e2750549fe2edcd33865f93a0ca5c616227eb05ff63654d545c75754c4e269a6 |
| MATCH-079-bounded | red | loss/TEAM_ELIMINATION | [13, 6] | [9, 6] | [25, 3, 0, 2, 0, 0] | [0, 0] | [0, 0, 4] | 8f757b6f3401a79eda462bac90a11799657071a5985564d39dbf7a9aa294ea25 |
| MATCH-079-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [228, 2, 0, 0, 5, 0] | [0, 18] | [44, 0, 26] | 751a909595a50b6d738ab85656a9f65c91fa5d2f60967bde5af3e9c4fedc4ce7 |
| MATCH-079-strict | red | loss/TEAM_ELIMINATION | [10, 4] | [5, 5] | [15, 2, 0, 5, 0, 3] | [0, 0] | [1, 0, 0] | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-080-bounded | blue | loss/PROVIDER_FORFEIT | [9, 4] | [8, 5] | [16, 4, 0, 0, 5, 0] | [0, 0] | [1, 0, 1] | e38e90c634fca066a7cbcb00ad62ab9a30d999b5228a33da9aa5c96701e22a9f |
| MATCH-080-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [14, 5] | [15, 10, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-080-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [4, 1, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | 8b54cc3ea51d623383192428031b0911f06b2bde9e465fcd076b0ba539209445 |

## Decision and limitations

Additional side-specific forfeits/caps and cost rates, Stepwise capped/uncapped means and sorted distribution, complete triplet classifications and cap gameplay: [focused comparisons](focused-comparisons.md).

See [decision.md](decision.md) for interpretation and continuation recommendation. INTERIM at n=80/control; frozen confirmatory inference waits for 100/control. No tuning or replacement of failed/capped games. [Figures](figures.md); machine metrics: interim-metrics.json; command audit: supplemental-audit.json; repair evidence: repair-forensics.json.
