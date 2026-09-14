# Batch 4 standalone — INTERIM

**n=10/control, 30 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

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
| strict | 10 | 10 | {"red": 5, "blue": 5} | {"PROVIDER_FORFEIT": 2, "TEAM_ELIMINATION": 3, "CORE_DESTRUCTION": 5} |
| bounded | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 5, "PROVIDER_FORFEIT": 3, "CORE_DESTRUCTION": 2} |
| stepwise | 10 | 10 | {"red": 5, "blue": 5} | {"REQUEST_LIMIT": 3, "CORE_DESTRUCTION": 6, "TEAM_ELIMINATION": 1} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.3846 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 2.0238 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 0 | 7 | 3 | 0.0000 | [0, 0.2775327998628892] | 2.9945 |
| Heuristic vs stepwise | 7 | 0 | 3 | 0.7000 | [0.39677814746114537, 0.8922087325936989] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 5, 0] | [0, 0.43448246478317476] |
| strict | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | red | [0, 5, 0] | [0, 0.43448246478317476] |
| bounded | blue | [0, 5, 0] | [0, 0.43448246478317476] |
| stepwise | red | [0, 2, 3] | [0, 0.43448246478317476] |
| stepwise | blue | [0, 5, 0] | [0, 0.43448246478317476] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 2 | 0 | 0 | 0 | [80, 8.5, [1, 14]] | [32, 3.5, [0, 6]] |
| bounded | 3 | 0 | 0 | 0 | [84, 9.0, [1, 15]] | [34, 3.5, [0, 7]] |
| stepwise | 0 | 3 | 0 | 0 | [366, 10.5, [8, 94]] | [174, 4.5, [3, 46]] |

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
| provider_requests | 54 | 85 | 545 |
| turns | 39 | 42 | 182 |
| completed_turns | 37 | 39 | 179 |
| repairs | 15 | 20 | 17 |
| repair_success | 13 | 17 | 17 |
| repair_failure | 2 | 3 | 0 |
| execution_truncations | 17 | 3 | 0 |
| initial_execution_invalidities | 17 | 23 | 0 |
| replans | 0 | 23 | 0 |
| ap_recovered | 0 | 37 | 0 |
| replacement_repairs | 0 | 7 | 0 |
| replacement_invalidities | 0 | 1 | 0 |
| second_invalidities | 0 | 3 | 0 |
| decisions | 39 | 65 | 531 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 39 | 42 | 0 |
| repair | 15 | 13 | 17 |
| bounded_replacement_planning | 0 | 23 | 0 |
| bounded_replacement_repair | 0 | 7 | 0 |
| stepwise_decisions | 0 | 0 | 528 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 5.4000 | 1.3846 | 1.3514 | 1.8205 | {"target outside action range": 11, "blocked line of sight": 4, "destination is occupied, blocked, unchanged, or beyond move range": 1, "invalid target ACTIVE/DOWNED status": 1} |
| bounded | 8.5000 | 2.0238 | 1.9744 | 2.4048 | {"target outside action range": 11, "blocked line of sight": 9, "invalid target ACTIVE/DOWNED status": 2, "impact outside Fireball range/board": 2, "actor must own an ACTIVE unit": 1, "target already has full HP": 1} |
| stepwise | 54.5000 | 2.9945 | 3.0335 | 2.7418 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 23 |
| positive | 20 |
| positive_fraction | 0.8696 |
| ap_total | 37 |
| mean_ap_per_replan | 1.6087 |
| median_ap_per_replan | 2 |
| ap_at_replan | [2, 2, 3, 3, 2, 4, 3, 1, 3, 4, 2, 1, 1, 1, 3, 4, 4, 2, 2, 2, 4, 1, 2] |
| ap_recovered | [2, 2, 2, 2, 0, 4, 2, 1, 2, 2, 2, 0, 1, 1, 2, 1, 1, 2, 2, 2, 2, 0, 2] |
| Replan rate | 0.5476 |
| Second invalidity rate | 0.1304 |
| Replacement explicit EndTurns | 9 |
| Replacement failures | 1 |
| Extra requests vs Strict | 31 |
| Request premium vs Strict (%) | 57.4074 |
| Extra provider seconds vs Strict | 53.6712 |
| Extra tokens vs Strict | 82168 |
| Extra requests / recovered AP (descriptive) | 0.8378 |
| Strict minus Bounded final truncations | 14 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 3 |
| fraction | 0.3000 |
| requests | 420 |
| request_share | 0.7706 |
| match_ids | ["MATCH-031-stepwise", "MATCH-033-stepwise", "MATCH-037-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 85 | 545 |
| total_tokens | 237784 | 1346955 |
| provider_latency_seconds | 160.2827 | 814.7351 |
| provider_requests/match | 8.5000 | 54.5000 |
| total_tokens/match | 23,778.4000 | 134,695.5000 |
| provider_requests/turn | 2.0238 | 2.9945 |
| total_tokens/turn | 5,661.5238 | 7,400.8516 |
| provider_latency_seconds/turn | 3.8163 | 4.4766 |
| W/L/no-result | [0, 10, 0] | [0, 7, 3] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-031-stepwise | red | [94, 46, 47] | [228, 136] | [140, 2, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-033-stepwise | red | [94, 46, 47] | [225, 137] | [140, 2, 1] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-037-stepwise | red | [94, 46, 47] | [232, 138] | [140, 0, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 195 | 210 | 910 |
| ap_executed | 112 | 158 | 840 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 25 | 28 | 59 |
| CLEAN_PLAN_COMPLETE | 0 | 2 | 0 |
| EXECUTION_TRUNCATION | 45 | 6 | 0 |
| PROVIDER_FAILURE | 10 | 12 | 11 |
| TERMINAL | 3 | 4 | 0 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 11 |
| Actual provider-failure AP | 10 | 12 | 0 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 13 | 2 | {"3": 3, "5": 2, "1": 6, "0": 2} | {"1": 3, "0": 2, "2": 6, "3": 2} | 6 | 2 | 0 |
| bounded | 20 | 2 | {"0": 6, "1": 8, "5": 2, "2": 2, "3": 2} | {"3": 10, "2": 7, "0": 2, "1": 1} | 2 | 0 | 0 |
| stepwise | 29 | 7 | {"1": 21, "5": 7, "3": 1} | {"2": 20, "0": 7, "1": 1, "4": 1} | 3 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 0 | 0 |
| core_damage_received | 175 | 85 | 234 |
| enemy_damage | 149 | 166 | 2041 |
| friendly_damage | 37 | 84 | 85 |
| enemy_units_downed | 8 | 17 | 136 |
| friendly_units_downed | 1 | 2 | 1 |
| units_downed_received | 26 | 33 | 92 |
| finish | 0 | 2 | 3 |
| revive | 0 | 5 | 72 |
| heal | 3 | 4 | 5 |
| snipe | 10 | 7 | 39 |
| shield_bash | 3 | 3 | 4 |
| shield_bash_pushes | 2 | 2 | 1 |
| fireball | 31 | 45 | 230 |
| empty_fireballs | 13 | 10 | 23 |
| friendly_only_fireballs | 6 | 17 | 10 |
| enemy_only_fireballs | 10 | 12 | 185 |
| mixed_fireballs | 2 | 6 | 12 |
| enemy_fireball_damage | 44 | 59 | 1366 |
| friendly_fireball_damage | 37 | 84 | 85 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 12 | 18 | 344 |
| friendly_units_hit | 10 | 26 | 27 |
| enemy_damage | 44 | 59 | 1366 |
| friendly_damage | 37 | 84 | 85 |
| enemy_downs | 1 | 5 | 1 |
| friendly_downs | 1 | 2 | 1 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-031-bounded", "arm": "bounded", "agent": "luna", "ordinal": 8, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-035-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 15, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 6, "friendly_downs": 0, "enemy_damage": 5, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-039-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-039-strict", "arm": "strict", "agent": "luna", "ordinal": 12, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 79 | 62 | 312 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 5 | 6 | 0 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 10 | 6 | 14 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 1 |
| arena_shield_bash enemy_displacements | 2 | 2 | 1 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 175 | 85 | 234 |
| core_damage_received | 0 | 0 | 0 |
| enemy_units_downed | 25 | 31 | 91 |
| finish | 10 | 6 | 13 |
| revive | 6 | 12 | 130 |
| ap_executed | 191 | 192 | 868 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 6.3964 | 6.7975 | 16.5391 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 54 | 85 | 545 |
| input_tokens | 150833 | 231017 | 1322986 |
| cached_input_tokens | 99077 | 101399 | 202256 |
| output_tokens | 4783 | 6767 | 23969 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 155616 | 237784 | 1346955 |
| provider_latency_seconds | 106.6115 | 160.2827 | 814.7351 |
| backend_thinking_seconds | 112.5803 | 168.6296 | 856.8585 |

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
| strict | 5.4000 | 15,561.6000 | 10.6611 | 1.3846 | 3,990.1538 | 2.7336 | 2.8867 | 129.0932 |
| bounded | 8.5000 | 23,778.4000 | 16.0283 | 2.0238 | 5,661.5238 | 3.8163 | 4.0150 | 187.1454 |
| stepwise | 54.5000 | 134,695.5000 | 81.4735 | 2.9945 | 7,400.8516 | 4.4766 | 4.7080 | 927.5072 |

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

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/limit": 3, "loss/loss/loss": 7}`; all-three-same outcome triplets: 7.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 4, "limit_pairs": 0, "median_paired_player_turn_difference": 0.0, "provider_requests_per_turn_ratio": 1.4616402116402116, "total_tokens_per_turn_ratio": 1.418873564231368, "backend_thinking_seconds_per_turn_ratio": 1.3908702331674414, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 3, "loss/loss": 7}, "provider_forfeit_pairs": 3, "limit_pairs": 3, "median_paired_player_turn_difference": 7.0, "provider_requests_per_turn_ratio": 1.4796380090497738, "total_tokens_per_turn_ratio": 1.3072190274819553, "backend_thinking_seconds_per_turn_ratio": 1.1726091757964967, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
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
