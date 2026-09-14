# Cumulative Batches 1–4 — INTERIM

**n=40/control, 120 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

## Execution and frozen integrity

This root adds Batch 4 to a copied, verified 90-match prefix, preserving all original earlier roots. Frozen resume starts at MATCH-031-strict, request 1468. No earlier request or match was rerun. Scope stops at --through-batch 4. No within-batch interruption recovery was used. Batch 5 is conditional on the separate successful Batch 4 integrity gate; Batch 6 is not authorized or executed.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-04 --through-batch 4 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-04/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-04/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-04/repair-forensics.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-04/interim-report.py
```

postprocess.py calls the unchanged frozen verifier, full-prefix integrity/replay verifier and analyzer for cumulative and batch==4 cohorts. Supplemental scripts are offline derived audits; frozen metrics and analysis remain unchanged.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Batch 4 schedule SHA-256 | b8072ea72dccba0dccf79e0a5ad0ca1b5714f5e84d41e4a099d7a924a7c71c10 |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Source-bound files | 140 |

Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.

Batch 4: schedule entries 91–120, MATCH-031–040, five Red/five Blue per control. Independent 1,700-request batch ceiling, per-control 300/500/900 and per-match 50/80/140; global 15,000. One bounded replan. Natural terminal precedence and 200-player-turn/100-round limits remain frozen. No winner on request limit; provider exhaustion forfeits without fallback.

Final frozen verifier: `{"success": true, "completed_matches": 120, "replay_verified": 120, "completed_requests": 2151, "reserved_requests": 2151, "pending_requests": 0}`. Previous roots verified: `{"artifacts\\arena-case-study-live-v1-01": 2524, "artifacts\\arena-case-study-live-v1-02": 4527, "artifacts\\arena-case-study-live-v1-03": 6476}`; copied immutable prefix files verified: 6400. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.

| Control | Intended | Started/sealed | Side counts | Terminal causes |
| --- | --- | --- | --- | --- |
| strict | 40 | 40 | {"red": 20, "blue": 20} | {"CORE_DESTRUCTION": 15, "TEAM_ELIMINATION": 17, "PROVIDER_FORFEIT": 8} |
| bounded | 40 | 40 | {"red": 20, "blue": 20} | {"TEAM_ELIMINATION": 23, "PROVIDER_FORFEIT": 11, "CORE_DESTRUCTION": 6} |
| stepwise | 40 | 40 | {"red": 20, "blue": 20} | {"REQUEST_LIMIT": 7, "CORE_DESTRUCTION": 22, "TEAM_ELIMINATION": 8, "PROVIDER_FORFEIT": 3} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 40 | 0 | 0.0000 | [0, 0.08762160119728664] | 1.3213 |
| Heuristic vs strict | 40 | 0 | 0 | 1.0000 | [0.9123783988027135, 1] | 0.0000 |
| bounded Luna | 0 | 40 | 0 | 0.0000 | [0, 0.08762160119728664] | 1.8757 |
| Heuristic vs bounded | 40 | 0 | 0 | 1.0000 | [0.9123783988027135, 1] | 0.0000 |
| stepwise Luna | 2 | 31 | 7 | 0.0500 | [0.013820667386148344, 0.16503877369140962] | 3.0535 |
| Heuristic vs stepwise | 31 | 2 | 7 | 0.7750 | [0.6249690325768998, 0.8768390867645927] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 20, 0] | [0, 0.16112515805281938] |
| strict | blue | [0, 20, 0] | [0, 0.16112515805281938] |
| bounded | red | [0, 20, 0] | [0, 0.16112515805281938] |
| bounded | blue | [0, 20, 0] | [0, 0.16112515805281938] |
| stepwise | red | [1, 12, 7] | [0.008881448800795402, 0.23613119344674205] |
| stepwise | blue | [1, 19, 0] | [0.008881448800795402, 0.23613119344674205] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 8 | 0 | 0 | 0 | [449, 9.5, [1, 57]] | [196, 4.0, [0, 28]] |
| bounded | 11 | 0 | 0 | 0 | [338, 10.0, [1, 18]] | [138, 4.0, [0, 8]] |
| stepwise | 3 | 7 | 0 | 0 | [1016, 11.0, [1, 94]] | [476, 5.0, [0, 46]] |

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
| cumulative | strict | 71/221 | 71 | 63 | 8 | 0.8873 | 8 |
| cumulative | bounded | 68/249 | 68 | 57 | 11 | 0.8382 | 11 |
| cumulative | stepwise | 64/1478 | 64 | 61 | 3 | 0.9531 | 3 |

Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).

Batch/cohort 1 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 2 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 3 patterns: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 4 patterns: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort cumulative patterns: `{"initial_categories": {"ap_budget": 2, "schema_validation": 4, "invalid_reference": 16}, "repair_categories": {"invalid_reference": 19, "schema_validation": 3}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 18, "AP_VIOLATION": 3, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 4, "revive": 7, "unavailable": 3, "move": 1, "fireball": 4, "attack": 3}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 2, "schema_validation -> invalid_reference": 2, "invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 15, "schema_validation -> schema_validation": 2}}`. Tags may overlap.

## Requests and bounded recovery

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 292 | 317 | 1542 |
| turns | 221 | 169 | 505 |
| completed_turns | 213 | 158 | 495 |
| repairs | 71 | 68 | 64 |
| repair_success | 63 | 57 | 61 |
| repair_failure | 8 | 11 | 3 |
| execution_truncations | 99 | 12 | 0 |
| initial_execution_invalidities | 99 | 80 | 0 |
| replans | 0 | 80 | 0 |
| ap_recovered | 0 | 140 | 0 |
| replacement_repairs | 0 | 26 | 0 |
| replacement_invalidities | 0 | 5 | 0 |
| second_invalidities | 0 | 12 | 0 |
| decisions | 221 | 249 | 1485 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 221 | 169 | 0 |
| repair | 71 | 42 | 64 |
| bounded_replacement_planning | 0 | 80 | 0 |
| bounded_replacement_repair | 0 | 26 | 0 |
| stepwise_decisions | 0 | 0 | 1478 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 7.3000 | 1.3213 | 1.2958 | 1.8597 | {"target outside action range": 54, "destination is occupied, blocked, unchanged, or beyond move range": 7, "blocked line of sight": 23, "impact outside Fireball range/board": 10, "invalid target ACTIVE/DOWNED status": 4, "actor must own an ACTIVE unit": 1} |
| bounded | 7.9250 | 1.8757 | 1.8165 | 2.4675 | {"target outside action range": 46, "blocked line of sight": 21, "impact outside Fireball range/board": 12, "invalid target ACTIVE/DOWNED status": 8, "destination is occupied, blocked, unchanged, or beyond move range": 2, "actor must own an ACTIVE unit": 2, "target already has full HP": 1} |
| stepwise | 38.5500 | 3.0535 | 3.0828 | 2.7406 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 80 |
| positive | 71 |
| positive_fraction | 0.8875 |
| ap_total | 140 |
| mean_ap_per_replan | 1.7500 |
| median_ap_per_replan | 2.0000 |
| ap_at_replan | [2, 3, 3, 1, 3, 2, 2, 4, 4, 4, 2, 2, 4, 3, 2, 4, 2, 2, 2, 3, 1, 4, 2, 2, 2, 2, 3, 4, 3, 3, 3, 2, 3, 3, 1, 3, 1, 1, 3, 3, 3, 4, 4, 2, 4, 4, 4, 2, 4, 3, 2, 4, 1, 3, 2, 4, 1, 2, 2, 3, 3, 2, 4, 3, 1, 3, 4, 2, 1, 1, 1, 3, 4, 4, 2, 2, 2, 4, 1, 2] |
| ap_recovered | [2, 3, 2, 1, 0, 2, 2, 2, 3, 1, 2, 2, 3, 1, 2, 2, 2, 2, 1, 2, 0, 1, 2, 2, 2, 1, 3, 4, 3, 3, 3, 2, 2, 3, 0, 1, 1, 1, 2, 1, 3, 0, 0, 2, 2, 4, 3, 2, 0, 2, 2, 1, 1, 2, 2, 2, 1, 2, 2, 2, 2, 0, 4, 2, 1, 2, 2, 2, 0, 1, 1, 2, 1, 1, 2, 2, 2, 2, 0, 2] |
| Replan rate | 0.4734 |
| Second invalidity rate | 0.1500 |
| Replacement explicit EndTurns | 24 |
| Replacement failures | 5 |
| Extra requests vs Strict | 25 |
| Request premium vs Strict (%) | 8.5616 |
| Extra provider seconds vs Strict | 23.6852 |
| Extra tokens vs Strict | 75081 |
| Extra requests / recovered AP (descriptive) | 0.1786 |
| Strict minus Bounded final truncations | 87 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 7 |
| fraction | 0.1750 |
| requests | 980 |
| request_share | 0.6355 |
| match_ids | ["MATCH-001-stepwise", "MATCH-009-stepwise", "MATCH-015-stepwise", "MATCH-021-stepwise", "MATCH-031-stepwise", "MATCH-033-stepwise", "MATCH-037-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 317 | 1542 |
| total_tokens | 890932 | 3899291 |
| provider_latency_seconds | 566.8604 | 2,409.7086 |
| provider_requests/match | 7.9250 | 38.5500 |
| total_tokens/match | 22,273.3000 | 97,482.2750 |
| provider_requests/turn | 1.8757 | 3.0535 |
| total_tokens/turn | 5,271.7870 | 7,721.3683 |
| provider_latency_seconds/turn | 3.3542 | 4.7717 |
| W/L/no-result | [0, 40, 0] | [2, 31, 7] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-001-stepwise | red | [94, 46, 47] | [232, 138] | [140, 0, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-009-stepwise | red | [94, 46, 47] | [228, 136] | [140, 2, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-015-stepwise | red | [92, 45, 46] | [227, 135] | [140, 3, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-021-stepwise | red | [94, 46, 47] | [233, 139] | [140, 0, 1] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-031-stepwise | red | [94, 46, 47] | [228, 136] | [140, 2, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-033-stepwise | red | [94, 46, 47] | [225, 137] | [140, 2, 1] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-037-stepwise | red | [94, 46, 47] | [232, 138] | [140, 0, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 1105 | 845 | 2525 |
| ap_executed | 653 | 659 | 2293 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 125 | 82 | 191 |
| CLEAN_PLAN_COMPLETE | 10 | 14 | 0 |
| EXECUTION_TRUNCATION | 264 | 24 | 0 |
| PROVIDER_FAILURE | 40 | 47 | 31 |
| TERMINAL | 13 | 19 | 10 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 19 |
| Actual provider-failure AP | 40 | 47 | 12 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 78 | 3 | {"0": 7, "5": 3, "1": 42, "2": 11, "3": 14, "4": 1} | {"4": 3, "0": 3, "2": 48, "1": 15, "3": 9} | 30 | 5 | 0 |
| bounded | 71 | 2 | {"2": 7, "0": 18, "1": 37, "3": 7, "5": 2} | {"2": 31, "3": 32, "1": 5, "4": 1, "0": 2} | 13 | 1 | 0 |
| stepwise | 91 | 22 | {"1": 61, "5": 22, "3": 4, "2": 4} | {"2": 64, "0": 22, "1": 4, "4": 1} | 9 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 0 | 30 |
| core_damage_received | 585 | 303 | 851 |
| enemy_damage | 823 | 689 | 5637 |
| friendly_damage | 245 | 350 | 299 |
| enemy_units_downed | 41 | 53 | 361 |
| friendly_units_downed | 9 | 11 | 9 |
| units_downed_received | 122 | 132 | 235 |
| finish | 1 | 6 | 14 |
| revive | 11 | 21 | 158 |
| heal | 17 | 15 | 26 |
| snipe | 33 | 32 | 47 |
| shield_bash | 21 | 17 | 29 |
| shield_bash_pushes | 17 | 14 | 6 |
| fireball | 198 | 189 | 704 |
| empty_fireballs | 63 | 47 | 89 |
| friendly_only_fireballs | 44 | 71 | 28 |
| enemy_only_fireballs | 71 | 45 | 532 |
| mixed_fireballs | 20 | 26 | 55 |
| enemy_fireball_damage | 374 | 257 | 4023 |
| friendly_fireball_damage | 245 | 350 | 299 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 115 | 72 | 1011 |
| friendly_units_hit | 74 | 110 | 101 |
| enemy_damage | 374 | 257 | 4023 |
| friendly_damage | 245 | 350 | 299 |
| enemy_downs | 6 | 13 | 5 |
| friendly_downs | 9 | 11 | 9 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-001-bounded", "arm": "bounded", "agent": "luna", "ordinal": 18, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 2, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-002-strict", "arm": "strict", "agent": "luna", "ordinal": 21, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "red"}, {"match_id": "MATCH-003-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-003-strict", "arm": "strict", "agent": "heuristic", "ordinal": 9, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 4, "friendly_downs": 0, "enemy_damage": 1, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-005-bounded", "arm": "bounded", "agent": "luna", "ordinal": 12, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-006-strict", "arm": "strict", "agent": "luna", "ordinal": 33, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "red"}, {"match_id": "MATCH-007-stepwise", "arm": "stepwise", "agent": "luna", "ordinal": 8, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-009-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 11, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 2, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-011-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-011-strict", "arm": "strict", "agent": "luna", "ordinal": 38, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-013-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-013-strict", "arm": "strict", "agent": "heuristic", "ordinal": 9, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 5, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-015-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-015-strict", "arm": "strict", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-018-stepwise", "arm": "stepwise", "agent": "heuristic", "ordinal": 10, "friendly_units_hit": 0, "enemy_units_hit": 1, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 1, "enemy_downs": 1, "winner_after_action": "red"}, {"match_id": "MATCH-019-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 7, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 2, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-020-stepwise", "arm": "stepwise", "agent": "luna", "ordinal": 13, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 2, "enemy_downs": 0, "winner_after_action": "red"}, {"match_id": "MATCH-027-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-031-bounded", "arm": "bounded", "agent": "luna", "ordinal": 8, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-035-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 15, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 6, "friendly_downs": 0, "enemy_damage": 5, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-039-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-039-strict", "arm": "strict", "agent": "luna", "ordinal": 12, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 282 | 267 | 378 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 20 | 22 | 5 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 60 | 52 | 101 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 8 |
| arena_shield_bash enemy_displacements | 17 | 14 | 6 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 585 | 303 | 851 |
| core_damage_received | 0 | 0 | 30 |
| enemy_units_downed | 113 | 121 | 226 |
| finish | 38 | 31 | 44 |
| revive | 30 | 32 | 330 |
| ap_executed | 845 | 744 | 2414 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 42.7130 | 29.2105 | 82.2675 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 292 | 317 | 1542 |
| input_tokens | 790382 | 865181 | 3831396 |
| cached_input_tokens | 387285 | 407302 | 715054 |
| output_tokens | 25469 | 25751 | 67895 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 815851 | 890932 | 3899291 |
| provider_latency_seconds | 543.1752 | 566.8604 | 2,409.7086 |
| backend_thinking_seconds | 574.8312 | 601.1741 | 2,540.3142 |

| Resource | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Cumulative |
| --- | --- | --- | --- | --- | --- |
| provider_requests | 583 | 447 | 437 | 684 | 2151 |
| input_tokens | 1492199 | 1144928 | 1144996 | 1704836 | 5486959 |
| cached_input_tokens | 390703 | 337711 | 378495 | 402732 | 1509641 |
| output_tokens | 32764 | 25301 | 25531 | 35519 | 119115 |
| reasoning_tokens | 0 | 0 | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 1170527 | 1740355 | 5606074 |
| provider_latency_seconds | 963.2223 | 748.6807 | 726.2118 | 1,081.6293 | 3,519.7442 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 773.5757 | 1,138.0684 | 3,716.3195 |

| Control | Requests/match | Tokens/match | Provider sec/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 7.3000 | 20,396.2750 | 13.5794 | 1.3213 | 3,691.6335 | 2.4578 | 2.6010 | 675.7204 |
| bounded | 7.9250 | 22,273.3000 | 14.1715 | 1.8757 | 5,271.7870 | 3.3542 | 3.5572 | 679.8375 |
| stepwise | 38.5500 | 97,482.2750 | 60.2427 | 3.0535 | 7,721.3683 | 4.7717 | 5.0303 | 2,789.5170 |

| Batch | Observed process wall seconds upper bound | Start UTC | Completion observed UTC |
| --- | --- | --- | --- |
| 1 | 1,160.4115 | 2026-09-14T13:55:14.5492481Z | 2026-09-14T14:14:34.9607496Z |
| 2 | 1,013.4124 | 2026-09-14T14:41:07.0220353Z | 2026-09-14T14:58:00.4344287Z |
| 3 | 1,070.4722 | 2026-09-14T15:15:33.2411670Z | 2026-09-14T15:33:23.7133549Z |
| 4 | 1,468.7011 | 2026-09-14T15:49:31.0663785Z | 2026-09-14T16:13:59.767443+00:00 |

Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.

## Updated projection from cumulative rates

| provider_requests | Observed | Mean/match | Remaining 60/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 292 | 7.3000 | 438.0000 | 730.0000 | [2, 36] | [120, 2160] | [412, 2452] |
| bounded | 317 | 7.9250 | 475.5000 | 792.5000 | [2, 16] | [120, 960] | [437, 1277] |
| stepwise | 1542 | 38.5500 | 2,313.0000 | 3,855.0000 | [2, 140] | [120, 8400] | [1662, 9942] |

Combined provider_requests: remaining 180 central **3,226.500**; full 300 central **5,377.500**. Full-study sensitivity [2511, 13671].

| total_tokens | Observed | Mean/match | Remaining 60/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 815851 | 20,396.2750 | 1,223,776.5000 | 2,039,627.5000 | [6150, 97697] | [369000, 5861820] | [1184851, 6677671] |
| bounded | 890932 | 22,273.3000 | 1,336,398.0000 | 2,227,330.0000 | [6263, 43711] | [375780, 2622660] | [1266712, 3513592] |
| stepwise | 3899291 | 97,482.2750 | 5,848,936.5000 | 9,748,227.5000 | [6409, 364261] | [384540, 21855660] | [4283831, 25754951] |

Combined total_tokens: remaining 180 central **8,409,111.000**; full 300 central **14,015,185.000**. Full-study sensitivity [6735394, 35946214].

| provider_latency_seconds | Observed | Mean/match | Remaining 60/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 543.1752 | 13.5794 | 814.7628 | 1,357.9380 | [3.2305263999733143, 60.84210030012764] | [193.83158399839886, 3650.5260180076584] | [737.0067702982924, 4193.701204307552] |
| bounded | 566.8604 | 14.1715 | 850.2906 | 1,417.1510 | [3.7967910999432206, 32.23841570003424] | [227.80746599659324, 1934.3049420020543] | [794.6678811962483, 2501.1653572017094] |
| stepwise | 2,409.7086 | 60.2427 | 3,614.5628 | 6,024.2714 | [3.1789701000088826, 224.93943329993635] | [190.73820600053295, 13496.365997996181] | [2600.4467656014604, 15906.074557597109] |

Combined provider_latency_seconds: remaining 180 central **5,279.616**; full 300 central **8,799.360**. Full-study sensitivity [4132.121417096001, 22600.94111910637].

Provider hours: remaining **1.4666**, full **2.4443**.

Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.

If future workloads resemble observed batches, remaining 6 batches span 1.689–2.448 process wall hours; full study 2.998–3.757 hours. This workload illustration excludes later analysis; growing prefix verification and service conditions can add time.

## Matched triplet patterns and differences

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/limit": 7, "loss/loss/loss": 31, "loss/loss/win": 2}`; all-three-same outcome triplets: 31.

`{"comparison": "bounded-strict", "pairs": 40, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 40}, "provider_forfeit_pairs": 15, "limit_pairs": 0, "median_paired_player_turn_difference": 0.0, "provider_requests_per_turn_ratio": 1.4196522655426767, "total_tokens_per_turn_ratio": 1.4280363976717845, "backend_thinking_seconds_per_turn_ratio": 1.3676201321050492, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 40, "win_gains": 2, "win_losses": 0, "win_rate_difference": 0.05, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 7, "loss/loss": 31, "win/loss": 2}, "provider_forfeit_pairs": 13, "limit_pairs": 7, "median_paired_player_turn_difference": 5.0, "provider_requests_per_turn_ratio": 1.6278726926320393, "total_tokens_per_turn_ratio": 1.4646586333688254, "backend_thinking_seconds_per_turn_ratio": 1.4141077654613514, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
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
| MATCH-031 | red | ["loss", "loss", "limit"] | [2, 11, 140] | [2, 8, 94] | [9, 129] | [6, 86] |
| MATCH-032 | blue | ["loss", "loss", "loss"] | [2, 4, 14] | [1, 1, 10] | [2, 10] | [0, 9] |
| MATCH-033 | red | ["loss", "loss", "limit"] | [3, 14, 140] | [5, 13, 94] | [11, 126] | [8, 81] |
| MATCH-034 | blue | ["loss", "loss", "loss"] | [6, 8, 11] | [10, 10, 8] | [2, 3] | [0, -2] |
| MATCH-035 | red | ["loss", "loss", "loss"] | [5, 16, 18] | [7, 15, 11] | [11, 2] | [8, -4] |
| MATCH-036 | blue | ["loss", "loss", "loss"] | [8, 6, 11] | [12, 6, 8] | [-2, 5] | [-6, 2] |
| MATCH-037 | red | ["loss", "loss", "limit"] | [4, 4, 140] | [7, 4, 94] | [0, 136] | [-3, 90] |
| MATCH-038 | blue | ["loss", "loss", "loss"] | [7, 10, 13] | [10, 12, 10] | [3, 3] | [2, -2] |
| MATCH-039 | red | ["loss", "loss", "loss"] | [7, 7, 42] | [12, 10, 27] | [0, 35] | [-2, 17] |
| MATCH-040 | blue | ["loss", "loss", "loss"] | [10, 5, 16] | [14, 5, 10] | [-5, 11] | [-9, 5] |

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
| MATCH-031-bounded | red | loss/TEAM_ELIMINATION | [8, 3] | [11, 4] | [18, 1, 0, 0, 0, 1] | [0, 5] | [1, 0, 0] | f8dc815981f09fa7d27d50daee9e419e59fce44f321bbb9876041f54ec294a59 |
| MATCH-031-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [228, 2, 0, 0, 5, 0] | [0, 18] | [44, 0, 0] | de81ed69c3c41e222649e35208fa65959abd42076901a450f3d83e777a4218fa |
| MATCH-031-strict | red | loss/PROVIDER_FORFEIT | [2, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | e9ba5bcc061b8de995cb4fb3d27521b342649c55fd2128a39d2ebf034b7685b7 |
| MATCH-032-bounded | blue | loss/PROVIDER_FORFEIT | [1, 0] | [4, 1] | [3, 0, 0, 0, 2, 0] | [0, 0] | [1, 0, 0] | 040a5e5553ea7b31bda3b59a5d490a7f4d6403582462418ed8cdd2c1a516cf9a |
| MATCH-032-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [14, 5] | [15, 10, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-032-strict | blue | loss/PROVIDER_FORFEIT | [1, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d |
| MATCH-033-bounded | red | loss/TEAM_ELIMINATION | [13, 6] | [14, 6] | [21, 8, 0, 1, 0, 0] | [0, 0] | [3, 1, 2] | 46c9320b3338a21ffd48c354189d34dd54fb7ca7522c72de7d1457473e85c4b4 |
| MATCH-033-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [225, 5, 0, 0, 5, 0] | [0, 18] | [42, 1, 43] | 4b99a6d240d87e55c4378872334e9c62e1686febb27e1e10431800ea6bae2082 |
| MATCH-033-strict | red | loss/TEAM_ELIMINATION | [5, 2] | [3, 2] | [5, 3, 0, 2, 0, 0] | [0, 0] | [0, 0, 0] | be4a7aeaf3bd5626f866b5b457ce1bb998081dccb5b59fb329b04b07b73bc9b7 |
| MATCH-034-bounded | blue | loss/CORE_DESTRUCTION | [10, 4] | [8, 5] | [21, 4, 0, 0, 0, 0] | [0, 30] | [2, 0, 0] | cd075649440124ce8d850b04840cdca2515d494696bb7badc8e59886745f07bd |
| MATCH-034-stepwise | blue | loss/TEAM_ELIMINATION | [8, 3] | [11, 4] | [15, 5, 0, 0, 0, 0] | [0, 0] | [0, 0, 1] | 379d6ec12a6b5c4fcd8a0cb4936674357f4c53bab353f67a340b04b3e4042adb |
| MATCH-034-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [6, 5] | [17, 0, 0, 8, 0, 0] | [0, 30] | [1, 0, 0] | b5f063c00133ef18bbae95dcf528a053c6371dc01f3310f9bce166086291ec12 |
| MATCH-035-bounded | red | loss/TEAM_ELIMINATION | [15, 7] | [16, 7] | [28, 3, 1, 3, 0, 0] | [0, 20] | [3, 1, 3] | 390327bd990ce18071fd1ebefb347709cf16ebdc70088af70cc8f08df0d98fe7 |
| MATCH-035-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [18, 5] | [23, 2, 0, 0, 0, 0] | [0, 30] | [2, 1, 0] | 160d1fcc62a1e41eb8f09e9aefb4ec718fc575d61fc2b975c808b353674bd746 |
| MATCH-035-strict | red | loss/CORE_DESTRUCTION | [7, 3] | [5, 3] | [7, 6, 0, 2, 0, 0] | [0, 30] | [0, 0, 0] | 61e2e6aad4e7fe8727f349b595bca7e47edb7e954f8ff6511cb4d7b43eb1daae |
| MATCH-036-bounded | blue | loss/TEAM_ELIMINATION | [6, 2] | [6, 3] | [15, 0, 0, 0, 0, 0] | [0, 0] | [1, 0, 0] | 6f94813f42356643b23bd7d09116d41b8fcc39e2f50b3e540671bd134e997266 |
| MATCH-036-stepwise | blue | loss/CORE_DESTRUCTION | [8, 3] | [11, 4] | [13, 7, 0, 0, 0, 0] | [0, 30] | [0, 0, 0] | 16d40de12ba750419e9990708d5fa59f400e9730ab643c471826ca118eff18d7 |
| MATCH-036-strict | blue | loss/TEAM_ELIMINATION | [12, 5] | [8, 6] | [19, 0, 0, 11, 0, 0] | [0, 20] | [1, 0, 0] | 08f0936ff9b33de28dcfd080b09413d89068bc0f26cee1f1b0a9b8343141f887 |
| MATCH-037-bounded | red | loss/PROVIDER_FORFEIT | [4, 1] | [4, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | bb080660a9277c95d406d433ccc2f398aca453494b4a9d28879a36b6e6701c78 |
| MATCH-037-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [232, 2, 0, 0, 1, 0] | [0, 18] | [44, 0, 28] | 7954225d425bd09c3cad4ac80d48079a16917b02548861d2ce403f651bc33fca |
| MATCH-037-strict | red | loss/CORE_DESTRUCTION | [7, 3] | [4, 3] | [7, 6, 0, 2, 0, 0] | [0, 30] | [0, 0, 0] | 61e2e6aad4e7fe8727f349b595bca7e47edb7e954f8ff6511cb4d7b43eb1daae |
| MATCH-038-bounded | blue | loss/CORE_DESTRUCTION | [12, 5] | [10, 6] | [20, 7, 1, 2, 0, 0] | [0, 30] | [4, 0, 0] | eba6f28b879eb8332de11b1c3c6a66f68854df8736324c051aea57f9b0aa32b6 |
| MATCH-038-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [13, 5] | [13, 12, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | b34b6b4ff4d34a8630b7f613d15cb45ba503f5ccdbecf821e076bcb0c2809eca |
| MATCH-038-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [7, 5] | [17, 0, 0, 8, 0, 0] | [0, 30] | [3, 0, 0] | 2f0c08db56c4daf71ab4c4c51aa107fd80d87722297b710c0a01d4837bd90447 |
| MATCH-039-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [7, 5] | [17, 5, 0, 0, 0, 3] | [0, 0] | [1, 0, 0] | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-039-stepwise | red | loss/CORE_DESTRUCTION | [27, 13] | [42, 13] | [58, 7, 0, 0, 0, 0] | [0, 30] | [1, 1, 0] | d77c68f9dc1442e6bbc466e943c0087934056c39fb66701ed0a98f2a28350c28 |
| MATCH-039-strict | red | loss/TEAM_ELIMINATION | [12, 5] | [7, 6] | [19, 6, 0, 2, 0, 3] | [0, 5] | [1, 0, 0] | 381421cc330429cb459da14cc518f444685b04e859634505943fd11c3ae95992 |
| MATCH-040-bounded | blue | loss/PROVIDER_FORFEIT | [5, 2] | [5, 3] | [10, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | e07574029ad1d9b0c59a6d457e1c5bbe9ff68d4032edc6d4bd6c75f2c0746588 |
| MATCH-040-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [16, 5] | [18, 7, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | 27294a13bb02689f97b7fb6c72fabd9dee1bb795b88ed314ae764030f811c13e |
| MATCH-040-strict | blue | loss/CORE_DESTRUCTION | [14, 6] | [10, 7] | [21, 4, 0, 10, 0, 0] | [0, 30] | [2, 0, 0] | d09df0eee2a0ddb85cafa9dfd16eb47b695001cf4424efd3c0be9694a7a53d53 |

## Decision and limitations

Additional side-specific forfeits/caps and cost rates, Stepwise capped/uncapped means and sorted distribution, complete triplet classifications and cap gameplay: [focused comparisons](focused-comparisons.md).

See [decision.md](decision.md) for interpretation and continuation recommendation. INTERIM at n=40/control; frozen confirmatory inference waits for 100/control. No tuning or replacement of failed/capped games. [Figures](figures.md); machine metrics: interim-metrics.json; command audit: supplemental-audit.json; repair evidence: repair-forensics.json.
