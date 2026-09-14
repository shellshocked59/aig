# Batch 6 standalone — INTERIM

**n=10/control, 30 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

## Execution and frozen integrity

This root adds Batch 6 to a copied, verified 150-match prefix, preserving all original earlier roots. Frozen resume starts at MATCH-051-stepwise, request 2581. No earlier request or match was rerun. Scope stops at --through-batch 6. No within-batch interruption recovery was used. Batches 6–8 have separate mandatory integrity gates; no later batch starts before the preceding gate passes. Batch 9 is not authorized or executed.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-06 --through-batch 6 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-06/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-06/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-06/repair-forensics.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-06/interim-report.py
```

postprocess.py calls the unchanged frozen verifier, full-prefix integrity/replay verifier and analyzer for cumulative and batch==6 cohorts. Supplemental scripts are offline derived audits; frozen metrics and analysis remain unchanged.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Batch 6 schedule SHA-256 | 7efd6302e681543e66c89ed626163d6f2ab662f92da0b3374dc3e27ac345148f |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Source-bound files | 140 |

Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.

Batch 6: schedule entries 151–180, MATCH-051–060, five Red/five Blue per control. Independent 1,700-request batch ceiling, per-control 300/500/900 and per-match 50/80/140; global 15,000. One bounded replan. Natural terminal precedence and 200-player-turn/100-round limits remain frozen. No winner on request limit; provider exhaustion forfeits without fallback.

Final frozen verifier: `{"success": true, "completed_matches": 180, "replay_verified": 180, "completed_requests": 3155, "reserved_requests": 3155, "pending_requests": 0}`. Previous roots verified: `{"artifacts\\arena-case-study-live-v1-01": 2524, "artifacts\\arena-case-study-live-v1-02": 4527, "artifacts\\arena-case-study-live-v1-03": 6476, "artifacts\\arena-case-study-live-v1-04": 9306, "artifacts\\arena-case-study-live-v1-05": 11213}`; copied immutable prefix files verified: 11129. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.

| Control | Intended | Started/sealed | Side counts | Terminal causes |
| --- | --- | --- | --- | --- |
| strict | 10 | 10 | {"red": 5, "blue": 5} | {"CORE_DESTRUCTION": 2, "PROVIDER_FORFEIT": 5, "TEAM_ELIMINATION": 3} |
| bounded | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 5, "PROVIDER_FORFEIT": 5} |
| stepwise | 10 | 10 | {"red": 5, "blue": 5} | {"REQUEST_LIMIT": 2, "CORE_DESTRUCTION": 5, "TEAM_ELIMINATION": 3} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.2308 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.4762 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 0 | 8 | 2 | 0.0000 | [0, 0.2775327998628892] | 3.0530 |
| Heuristic vs stepwise | 8 | 0 | 2 | 0.8000 | [0.49016247153664183, 0.9433178485456247] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 5, 0] | [0, 0.43448246478317476] |
| strict | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | red | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| stepwise | red | [0, 4, 1] | [0, 0.43448246478317476] |
| stepwise | blue | [0, 4, 1] | [0, 0.43448246478317476] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 5 | 0 | 0 | 0 | [77, 5.0, [2, 26]] | [31, 2.0, [0, 12]] |
| bounded | 5 | 0 | 0 | 0 | [167, 7.5, [1, 91]] | [76, 3.0, [0, 45]] |
| stepwise | 0 | 2 | 0 | 0 | [266, 10.0, [7, 94]] | [125, 4.0, [3, 46]] |

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
| cumulative | strict | 94/301 | 94 | 79 | 15 | 0.8404 | 15 |
| cumulative | bounded | 106/426 | 106 | 84 | 22 | 0.7925 | 22 |
| cumulative | stepwise | 99/2129 | 99 | 95 | 4 | 0.9596 | 4 |

Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).

Batch/cohort 1 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 2 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 3 patterns: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 4 patterns: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 5 patterns: `{"initial_categories": {"invalid_reference": 7, "invalid_ability": 1, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 8}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 8}, "repair_identified_action_types": {"unavailable": 1, "snipe": 2, "revive": 1, "attack": 2, "fireball": 3}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 6, "invalid_ability -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 6 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 3, "ap_budget": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 9}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 9}, "repair_identified_action_types": {"unavailable": 1, "fireball": 3, "revive": 4, "snipe": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "schema_validation -> invalid_reference": 3, "invalid_reference -> invalid_reference": 5, "ap_budget -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort cumulative patterns: `{"initial_categories": {"ap_budget": 3, "schema_validation": 8, "invalid_reference": 29, "invalid_ability": 1}, "repair_categories": {"invalid_reference": 36, "schema_validation": 5}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 35, "AP_VIOLATION": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 8, "revive": 12, "unavailable": 5, "move": 1, "fireball": 10, "attack": 5}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 3, "schema_validation -> invalid_reference": 6, "invalid_reference -> schema_validation": 3, "invalid_reference -> invalid_reference": 26, "schema_validation -> schema_validation": 2, "invalid_ability -> invalid_reference": 1}}`. Tags may overlap.

## Requests and bounded recovery

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 48 | 124 | 403 |
| turns | 39 | 84 | 132 |
| completed_turns | 34 | 79 | 130 |
| repairs | 9 | 20 | 19 |
| repair_success | 4 | 15 | 19 |
| repair_failure | 5 | 5 | 0 |
| execution_truncations | 19 | 4 | 0 |
| initial_execution_invalidities | 19 | 20 | 0 |
| replans | 0 | 20 | 0 |
| ap_recovered | 0 | 32 | 0 |
| replacement_repairs | 0 | 8 | 0 |
| replacement_invalidities | 0 | 1 | 0 |
| second_invalidities | 0 | 4 | 0 |
| decisions | 39 | 104 | 386 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 39 | 84 | 0 |
| repair | 9 | 12 | 19 |
| bounded_replacement_planning | 0 | 20 | 0 |
| bounded_replacement_repair | 0 | 8 | 0 |
| stepwise_decisions | 0 | 0 | 384 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 4.8000 | 1.2308 | 1.1176 | 1.7179 | {"target outside action range": 15, "invalid target ACTIVE/DOWNED status": 1, "impact outside Fireball range/board": 2, "blocked line of sight": 1} |
| bounded | 12.4000 | 1.4762 | 1.4177 | 2.2381 | {"target outside action range": 11, "invalid target ACTIVE/DOWNED status": 1, "blocked line of sight": 4, "impact outside Fireball range/board": 5, "destination is occupied, blocked, unchanged, or beyond move range": 2, "actor must own an ACTIVE unit": 1} |
| stepwise | 40.3000 | 3.0530 | 3.0923 | 2.4848 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 20 |
| positive | 18 |
| positive_fraction | 0.9000 |
| ap_total | 32 |
| mean_ap_per_replan | 1.6000 |
| median_ap_per_replan | 2.0000 |
| ap_at_replan | [3, 1, 3, 4, 2, 4, 2, 2, 1, 4, 2, 2, 3, 4, 4, 2, 2, 3, 2, 2] |
| ap_recovered | [2, 1, 2, 2, 2, 1, 2, 2, 0, 4, 1, 1, 2, 2, 2, 2, 2, 1, 1, 0] |
| Replan rate | 0.2381 |
| Second invalidity rate | 0.2000 |
| Replacement explicit EndTurns | 7 |
| Replacement failures | 1 |
| Extra requests vs Strict | 76 |
| Request premium vs Strict (%) | 158.3333 |
| Extra provider seconds vs Strict | 134.0966 |
| Extra tokens vs Strict | 174399 |
| Extra requests / recovered AP (descriptive) | 2.3750 |
| Strict minus Bounded final truncations | 15 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 2 |
| fraction | 0.2000 |
| requests | 280 |
| request_share | 0.6948 |
| match_ids | ["MATCH-051-stepwise", "MATCH-058-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 124 | 403 |
| total_tokens | 310758 | 998721 |
| provider_latency_seconds | 227.3238 | 572.6076 |
| provider_requests/match | 12.4000 | 40.3000 |
| total_tokens/match | 31,075.8000 | 99,872.1000 |
| provider_requests/turn | 1.4762 | 3.0530 |
| total_tokens/turn | 3,699.5000 | 7,566.0682 |
| provider_latency_seconds/turn | 2.7062 | 4.3379 |
| W/L/no-result | [0, 10, 0] | [0, 8, 2] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-051-stepwise | red | [94, 46, 47] | [228, 136] | [140, 2, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-058-stepwise | blue | [89, 44, 45] | [183, 95] | [140, 6, 39] | {"blue-core": 21, "red-core": 30} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 195 | 420 | 660 |
| ap_executed | 113 | 322 | 571 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 11 | 40 | 78 |
| CLEAN_PLAN_COMPLETE | 0 | 27 | 0 |
| EXECUTION_TRUNCATION | 45 | 8 | 0 |
| PROVIDER_FAILURE | 25 | 22 | 8 |
| TERMINAL | 1 | 1 | 3 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 8 |
| Actual provider-failure AP | 25 | 22 | 0 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 0 | {"1": 8, "3": 1, "0": 1} | {"3": 2, "1": 1, "2": 7} | 2 | 0 | 0 |
| bounded | 37 | 0 | {"1": 25, "0": 5, "2": 6, "3": 1} | {"2": 26, "3": 6, "4": 4, "1": 1} | 6 | 0 | 0 |
| stepwise | 56 | 4 | {"1": 48, "5": 4, "2": 2, "3": 2} | {"2": 48, "0": 4, "3": 2, "1": 2} | 2 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 27 | 0 |
| core_damage_received | 70 | 45 | 217 |
| enemy_damage | 176 | 191 | 875 |
| friendly_damage | 29 | 50 | 83 |
| enemy_units_downed | 9 | 11 | 59 |
| friendly_units_downed | 1 | 2 | 1 |
| units_downed_received | 19 | 114 | 57 |
| finish | 0 | 3 | 2 |
| revive | 1 | 90 | 31 |
| heal | 0 | 4 | 7 |
| snipe | 7 | 11 | 4 |
| shield_bash | 2 | 4 | 3 |
| shield_bash_pushes | 2 | 4 | 1 |
| fireball | 38 | 33 | 208 |
| empty_fireballs | 8 | 10 | 99 |
| friendly_only_fireballs | 9 | 14 | 16 |
| enemy_only_fireballs | 21 | 6 | 83 |
| mixed_fireballs | 0 | 3 | 10 |
| enemy_fireball_damage | 90 | 32 | 595 |
| friendly_fireball_damage | 29 | 50 | 83 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 23 | 9 | 153 |
| friendly_units_hit | 10 | 18 | 28 |
| enemy_damage | 90 | 32 | 595 |
| friendly_damage | 29 | 50 | 83 |
| enemy_downs | 1 | 1 | 4 |
| friendly_downs | 1 | 2 | 1 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-057-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-057-stepwise", "arm": "stepwise", "agent": "heuristic", "ordinal": 9, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 3, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-057-strict", "arm": "strict", "agent": "luna", "ordinal": 26, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-059-stepwise", "arm": "stepwise", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 62 | 92 | 38 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 5 | 5 | 4 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 6 | 12 | 12 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 0 |
| arena_shield_bash enemy_displacements | 2 | 4 | 1 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 70 | 45 | 217 |
| core_damage_received | 0 | 27 | 0 |
| enemy_units_downed | 18 | 112 | 56 |
| finish | 5 | 5 | 11 |
| revive | 8 | 4 | 50 |
| ap_executed | 147 | 369 | 451 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 6.9394 | 20.3367 | 16.2755 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 48 | 124 | 403 |
| input_tokens | 132190 | 301461 | 981281 |
| cached_input_tokens | 63103 | 97266 | 151552 |
| output_tokens | 4169 | 9297 | 17440 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 136359 | 310758 | 998721 |
| provider_latency_seconds | 93.2272 | 227.3238 | 572.6076 |
| backend_thinking_seconds | 100.5690 | 241.5770 | 613.0314 |

| Resource | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Batch 5 | Batch 6 | Cumulative |
| --- | --- | --- | --- | --- | --- | --- | --- |
| provider_requests | 583 | 447 | 437 | 684 | 429 | 575 | 3155 |
| input_tokens | 1492199 | 1144928 | 1144996 | 1704836 | 1110699 | 1414932 | 8012590 |
| cached_input_tokens | 390703 | 337711 | 378495 | 402732 | 515698 | 311921 | 2337260 |
| output_tokens | 32764 | 25301 | 25531 | 35519 | 24637 | 30906 | 174658 |
| reasoning_tokens | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 1170527 | 1740355 | 1135336 | 1445838 | 8187248 |
| provider_latency_seconds | 963.2223 | 748.6807 | 726.2118 | 1,081.6293 | 680.1648 | 893.1586 | 5,093.0676 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 773.5757 | 1,138.0684 | 725.1686 | 955.1774 | 5,396.6656 |

| Control | Requests/match | Tokens/match | Provider sec/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 4.8000 | 13,635.9000 | 9.3227 | 1.2308 | 3,496.3846 | 2.3904 | 2.5787 | 119.9224 |
| bounded | 12.4000 | 31,075.8000 | 22.7324 | 1.4762 | 3,699.5000 | 2.7062 | 2.8759 | 287.9617 |
| stepwise | 40.3000 | 99,872.1000 | 57.2608 | 3.0530 | 7,566.0682 | 4.3379 | 4.6442 | 679.3335 |

| Batch | Observed process wall seconds upper bound | Start UTC | Completion observed UTC |
| --- | --- | --- | --- |
| 1 | 1,160.4115 | 2026-09-14T13:55:14.5492481Z | 2026-09-14T14:14:34.9607496Z |
| 2 | 1,013.4124 | 2026-09-14T14:41:07.0220353Z | 2026-09-14T14:58:00.4344287Z |
| 3 | 1,070.4722 | 2026-09-14T15:15:33.2411670Z | 2026-09-14T15:33:23.7133549Z |
| 4 | 1,468.7011 | 2026-09-14T15:49:31.0663785Z | 2026-09-14T16:13:59.767443+00:00 |
| 5 | 1,086.4948 | 2026-09-14T16:21:20.9995992Z | 2026-09-14T16:39:27.494440+00:00 |
| 6 | 1,448.3484 | 2026-09-14T17:09:50.182916+00:00 | 2026-09-14T17:33:58.531287+00:00 |

Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.

## Updated projection from cumulative rates

| provider_requests | Observed | Mean/match | Remaining 40/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 395 | 6.5833 | 263.3333 | 658.3333 | [2, 36] | [80, 1440] | [475, 1835] |
| bounded | 532 | 8.8667 | 354.6667 | 886.6667 | [2, 49] | [80, 1960] | [612, 2492] |
| stepwise | 2228 | 37.1333 | 1,485.3333 | 3,713.3333 | [2, 140] | [80, 5600] | [2308, 7828] |

Combined provider_requests: remaining 120 central **2,103.333**; full 300 central **5,258.333**. Full-study sensitivity [3395, 12155].

| total_tokens | Observed | Mean/match | Remaining 40/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 1110484 | 18,508.0667 | 740,322.6667 | 1,850,806.6667 | [6150, 97697] | [246000, 3907880] | [1356484, 5018364] |
| bounded | 1454412 | 24,240.2000 | 969,608.0000 | 2,424,020.0000 | [6239, 101589] | [249560, 4063560] | [1703972, 5517972] |
| stepwise | 5622352 | 93,705.8667 | 3,748,234.6667 | 9,370,586.6667 | [6409, 364261] | [256360, 14570440] | [5878712, 20192792] |

Combined total_tokens: remaining 120 central **5,458,165.333**; full 300 central **13,645,413.333**. Full-study sensitivity [8939168, 30729128].

| provider_latency_seconds | Observed | Mean/match | Remaining 40/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 740.0060 | 12.3334 | 493.3373 | 1,233.3434 | [3.2305263999733143, 60.84210030012764] | [129.22105599893257, 2433.6840120051056] | [869.2270727988216, 3173.6900288049947] |
| bounded | 944.8207 | 15.7470 | 629.8805 | 1,574.7012 | [2.902137700060848, 75.62964820029447] | [116.08550800243393, 3025.1859280117787] | [1060.9062323024846, 3970.0066523118294] |
| stepwise | 3,408.2409 | 56.8040 | 2,272.1606 | 5,680.4014 | [3.1789701000088826, 224.93943329993635] | [127.1588040003553, 8997.577331997454] | [3535.399665101955, 12405.818193099054] |

Combined provider_latency_seconds: remaining 120 central **3,395.378**; full 300 central **8,488.446**. Full-study sensitivity [5465.532970203261, 19549.514874215878].

Provider hours: remaining **0.9432**, full **2.3579**.

Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.

If future workloads resemble observed batches, remaining 4 batches span 1.126–1.632 process wall hours; full study 3.139–3.645 hours. This workload illustration excludes later analysis; growing prefix verification and service conditions can add time.

## Matched triplet patterns and differences

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/limit": 2, "loss/loss/loss": 8}`; all-three-same outcome triplets: 8.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 8, "limit_pairs": 0, "median_paired_player_turn_difference": 2.0, "provider_requests_per_turn_ratio": 1.1994047619047619, "total_tokens_per_turn_ratio": 1.0580929751611554, "backend_thinking_seconds_per_turn_ratio": 1.115261939230328, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 2, "loss/loss": 8}, "provider_forfeit_pairs": 5, "limit_pairs": 2, "median_paired_player_turn_difference": 3.0, "provider_requests_per_turn_ratio": 2.0681818181818183, "total_tokens_per_turn_ratio": 2.0451596653110373, "backend_thinking_seconds_per_turn_ratio": 1.6148508471432705, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-051 | red | ["loss", "loss", "limit"] | [5, 49, 140] | [11, 91, 94] | [44, 91] | [80, 3] |
| MATCH-052 | blue | ["loss", "loss", "loss"] | [3, 10, 12] | [3, 8, 8] | [7, 2] | [5, 0] |
| MATCH-053 | red | ["loss", "loss", "loss"] | [2, 2, 27] | [2, 2, 17] | [0, 25] | [0, 15] |
| MATCH-054 | blue | ["loss", "loss", "loss"] | [6, 6, 17] | [8, 5, 12] | [0, 11] | [-3, 7] |
| MATCH-055 | red | ["loss", "loss", "loss"] | [3, 4, 11] | [7, 4, 7] | [1, 7] | [-3, 3] |
| MATCH-056 | blue | ["loss", "loss", "loss"] | [3, 27, 15] | [3, 28, 10] | [24, -12] | [25, -18] |
| MATCH-057 | red | ["loss", "loss", "loss"] | [13, 6, 12] | [26, 10, 9] | [-7, 6] | [-16, -1] |
| MATCH-058 | blue | ["loss", "loss", "limit"] | [4, 7, 140] | [3, 7, 89] | [3, 133] | [4, 82] |
| MATCH-059 | red | ["loss", "loss", "loss"] | [2, 9, 14] | [2, 11, 10] | [7, 5] | [9, -1] |
| MATCH-060 | blue | ["loss", "loss", "loss"] | [7, 4, 15] | [12, 1, 10] | [-3, 11] | [-11, 9] |

## Per-match evidence

| Match | Side | Outcome/cause | Turns/rounds | Requests/Luna turns | AP executed; I/C/X/P/T unused | Core damage dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-051-bounded | red | loss/TEAM_ELIMINATION | [91, 45] | [49, 45] | [183, 18, 23, 1, 0, 0] | [0, 18] | [1, 1, 84] | 1c4a9b6ff8bd5787278b78e952bc8b859c20b3d6c34b29bfb10741d5b834d454 |
| MATCH-051-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [228, 2, 0, 0, 5, 0] | [0, 18] | [44, 0, 27] | 751a909595a50b6d738ab85656a9f65c91fa5d2f60967bde5af3e9c4fedc4ce7 |
| MATCH-051-strict | red | loss/CORE_DESTRUCTION | [11, 5] | [5, 5] | [15, 0, 0, 10, 0, 0] | [0, 30] | [3, 0, 0] | 9e60c422d3fb3d40bc124bf77a89090352460b5bb8f38110b7a3625dc1f2685c |
| MATCH-052-bounded | blue | loss/TEAM_ELIMINATION | [8, 3] | [10, 4] | [15, 0, 0, 5, 0, 0] | [0, 0] | [1, 0, 0] | e78773fec99b5b2b955eb21db3cc50fa4d26e231b5f1d304bba7330dad1ac006 |
| MATCH-052-stepwise | blue | loss/CORE_DESTRUCTION | [8, 3] | [12, 4] | [13, 7, 0, 0, 0, 0] | [0, 30] | [0, 0, 0] | a7291ba523635d657928f066ee12c1617b1309a7bedee987bb6df7a200aa5d60 |
| MATCH-052-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-053-bounded | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-053-stepwise | red | loss/CORE_DESTRUCTION | [17, 8] | [27, 8] | [32, 8, 0, 0, 0, 0] | [0, 30] | [4, 1, 1] | bcda37b5d766af09901ca29532fc3f68ee3e4df89b38e1d1862cea6eb19cd742 |
| MATCH-053-strict | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-054-bounded | blue | loss/PROVIDER_FORFEIT | [5, 2] | [6, 3] | [10, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | 5a11cdcf3b220f7d195d21998469e324d45850fc8a0707468d0c60c77831e6f4 |
| MATCH-054-stepwise | blue | loss/CORE_DESTRUCTION | [12, 5] | [17, 6] | [20, 10, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | facd045d48e9da2ab308c14286c12cd9661a20e5c4688d5e31399a858cd8fe1b |
| MATCH-054-strict | blue | loss/TEAM_ELIMINATION | [8, 3] | [6, 4] | [12, 4, 0, 4, 0, 0] | [0, 0] | [1, 0, 1] | f5cf37d083ae61bef42c2f0a8f463b31c66700457f6ccbb58275a671112a58f3 |
| MATCH-055-bounded | red | loss/PROVIDER_FORFEIT | [4, 1] | [4, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | bb080660a9277c95d406d433ccc2f398aca453494b4a9d28879a36b6e6701c78 |
| MATCH-055-stepwise | red | loss/TEAM_ELIMINATION | [7, 3] | [11, 3] | [15, 0, 0, 0, 0, 0] | [0, 0] | [0, 0, 1] | b0f944d0976d1f5fc132751c1d11bb00772b36eacb921921605191cedd6b13f1 |
| MATCH-055-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [3, 3] | [9, 1, 0, 5, 0, 0] | [0, 5] | [0, 0, 0] | fbdfd8450e85871ea25cae23d5771bcb8ead05c197e6cf98c2cdfa0eaa735481 |
| MATCH-056-bounded | blue | loss/TEAM_ELIMINATION | [28, 13] | [27, 14] | [50, 18, 2, 0, 0, 0] | [18, 9] | [4, 1, 2] | 3c24460719eda672a7be07847cce1f32973d93240cce535097ec679deb6ed6a4 |
| MATCH-056-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [22, 3, 0, 0, 0, 0] | [0, 30] | [3, 0, 1] | f5c659b435d12383837dd682e2b2a85efe573fe3c9bd9edf66c59115a3fbb6ff |
| MATCH-056-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-057-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [6, 5] | [22, 2, 0, 0, 0, 1] | [0, 0] | [1, 0, 0] | 4b60991d2c74d258a694357ef0670afa84719a6133219d440bf681be06fb01cd |
| MATCH-057-stepwise | red | loss/TEAM_ELIMINATION | [9, 4] | [12, 4] | [18, 2, 0, 0, 0, 0] | [0, 20] | [1, 0, 0] | 8cb826473475b41191da5522b488378f13bbc3aa188d53c05c021dbeff37025d |
| MATCH-057-strict | red | loss/TEAM_ELIMINATION | [26, 12] | [13, 13] | [44, 6, 0, 14, 0, 1] | [0, 5] | [1, 0, 0] | 91c9848ef6cbe40ac3ce894759ce3cc09819204d53c02a7adf5cac74424c70f3 |
| MATCH-058-bounded | blue | loss/PROVIDER_FORFEIT | [7, 3] | [7, 4] | [15, 0, 0, 0, 5, 0] | [9, 0] | [1, 0, 0] | 3018c608b9d29be9d2c503b34f3dd91416a407c5c84daa53f11e7701d9109409 |
| MATCH-058-stepwise | blue | limit/REQUEST_LIMIT | [89, 44] | [140, 45] | [183, 39, 0, 0, 3, 0] | [0, 9] | [2, 1, 0] | 90123b553d3e62775a1ba6ed62c2cbdacf9eada72c551c7e5298eb5e5e028d91 |
| MATCH-058-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [3, 0, 0, 2, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-059-bounded | red | loss/TEAM_ELIMINATION | [11, 5] | [9, 5] | [19, 2, 2, 2, 0, 0] | [0, 18] | [1, 1, 4] | 60edefb2a6fd0dc919e296033927c2c712f9bd636e9bf939210ef643bdd23b8d |
| MATCH-059-stepwise | red | loss/TEAM_ELIMINATION | [10, 4] | [14, 5] | [20, 2, 0, 0, 0, 3] | [0, 20] | [1, 0, 0] | b4f6ab66f8a81fe6b2c51c3bb20dca4ed418a003ed933ce556b49831c8a71cc9 |
| MATCH-059-strict | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-060-bounded | blue | loss/PROVIDER_FORFEIT | [1, 0] | [4, 1] | [3, 0, 0, 0, 2, 0] | [0, 0] | [1, 0, 0] | 040a5e5553ea7b31bda3b59a5d490a7f4d6403582462418ed8cdd2c1a516cf9a |
| MATCH-060-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [20, 5, 0, 0, 0, 0] | [0, 30] | [3, 0, 1] | f5c659b435d12383837dd682e2b2a85efe573fe3c9bd9edf66c59115a3fbb6ff |
| MATCH-060-strict | blue | loss/CORE_DESTRUCTION | [12, 5] | [7, 6] | [20, 0, 0, 10, 0, 0] | [0, 30] | [1, 0, 0] | 647bb0124fc6370bcb9ec9aedc0064cb35eedeadb221b67039c35a8a96db3dd4 |

## Decision and limitations

Additional side-specific forfeits/caps and cost rates, Stepwise capped/uncapped means and sorted distribution, complete triplet classifications and cap gameplay: [focused comparisons](focused-comparisons.md).

See [decision.md](decision.md) for interpretation and continuation recommendation. INTERIM at n=60/control; frozen confirmatory inference waits for 100/control. No tuning or replacement of failed/capped games. [Figures](figures.md); machine metrics: interim-metrics.json; command audit: supplemental-audit.json; repair evidence: repair-forensics.json.
