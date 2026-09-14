# Batch 5 standalone — INTERIM

**n=10/control, 30 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

## Execution and frozen integrity

This root adds Batch 5 to a copied, verified 120-match prefix, preserving all original earlier roots. Frozen resume starts at MATCH-041-bounded, request 2152. No earlier request or match was rerun. Scope stops at --through-batch 5. No within-batch interruption recovery was used. Batch 5 is conditional on the separate successful Batch 4 integrity gate; Batch 6 is not authorized or executed.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-05 --through-batch 5 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-05/postprocess.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-05/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-05/repair-forensics.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-05/interim-report.py
```

postprocess.py calls the unchanged frozen verifier, full-prefix integrity/replay verifier and analyzer for cumulative and batch==5 cohorts. Supplemental scripts are offline derived audits; frozen metrics and analysis remain unchanged.

| Binding | Value |
| --- | --- |
| Benchmark | arena-case-study-benchmark-v1 |
| Contract payload SHA-256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| Contract file SHA-256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| Batch 5 schedule SHA-256 | 687cf42a802b0d11df7a8a9db80614f1fc1d6405e187d214fe9c5b18c1ca60cf |
| Full schedule SHA-256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| Source manifest SHA-256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| Source-bound files | 140 |

Frozen: gpt-5.6-luna/luna-config-v1; arena-policy-core-v1; arena-turn-prompt-v6 and arena-step-prompt-v3; arena-observation-v4; arena-turn-plan-schema-v2; arena-candidate-repair-v2; arena-heuristic-v2; arena-rules-v2/arena-scenario-v1. Full schema/prompt/control/profile hashes and exact initial state remain in contract.json. The benchmark and its analyzer were not changed.

Batch 5: schedule entries 121–150, MATCH-041–050, five Red/five Blue per control. Independent 1,700-request batch ceiling, per-control 300/500/900 and per-match 50/80/140; global 15,000. One bounded replan. Natural terminal precedence and 200-player-turn/100-round limits remain frozen. No winner on request limit; provider exhaustion forfeits without fallback.

Final frozen verifier: `{"success": true, "completed_matches": 150, "replay_verified": 150, "completed_requests": 2580, "reserved_requests": 2580, "pending_requests": 0}`. Previous roots verified: `{"artifacts\\arena-case-study-live-v1-01": 2524, "artifacts\\arena-case-study-live-v1-02": 4527, "artifacts\\arena-case-study-live-v1-03": 6476, "artifacts\\arena-case-study-live-v1-04": 9306}`; copied immutable prefix files verified: 9223. Checks cover replay, source/runtime, exact schedule/side/control/model bindings, deterministic heuristic behavior, metric recomputation, request evidence, seals and zero fallback.

| Control | Intended | Started/sealed | Side counts | Terminal causes |
| --- | --- | --- | --- | --- |
| strict | 10 | 10 | {"red": 5, "blue": 5} | {"CORE_DESTRUCTION": 4, "PROVIDER_FORFEIT": 2, "TEAM_ELIMINATION": 4} |
| bounded | 10 | 10 | {"red": 5, "blue": 5} | {"TEAM_ELIMINATION": 4, "PROVIDER_FORFEIT": 6} |
| stepwise | 10 | 10 | {"red": 5, "blue": 5} | {"CORE_DESTRUCTION": 8, "PROVIDER_FORFEIT": 1, "REQUEST_LIMIT": 1} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.3415 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 10 | 0 | 0.0000 | [0, 0.2775327998628892] | 1.6852 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0000 | [0.7224672001371107, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 0 | 9 | 1 | 0.0000 | [0, 0.2775327998628892] | 3.0430 |
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
| strict | 2 | 0 | 0 | 0 | [84, 7.0, [3, 15]] | [36, 3.0, [1, 7]] |
| bounded | 6 | 0 | 0 | 0 | [105, 10.0, [1, 29]] | [46, 4.0, [0, 14]] |
| stepwise | 1 | 1 | 0 | 0 | [189, 10.5, [8, 94]] | [86, 4.5, [3, 46]] |

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
| cumulative | strict | 85/262 | 85 | 75 | 10 | 0.8824 | 10 |
| cumulative | bounded | 86/322 | 86 | 69 | 17 | 0.8023 | 17 |
| cumulative | stepwise | 80/1745 | 80 | 76 | 4 | 0.9500 | 4 |

Forensics use saved structured decisions and validator/repair diagnostics, never hidden reasoning. Unknown references remain redacted; missing semantic fields remain unavailable. Frozen invalid_reference can also denote first-action catalog rejection for range/LOS/status with valid IDs. Descriptive subcategories do not replace the frozen recorded category. Full match/turn/AP/action/actor/target/request/response evidence: [repair-forensics.json](repair-forensics.json); readable cases: [repair-forensics.md](repair-forensics.md).

Batch/cohort 1 patterns: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 2 patterns: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort 3 patterns: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 4 patterns: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`. Tags may overlap.

Batch/cohort 5 patterns: `{"initial_categories": {"invalid_reference": 7, "invalid_ability": 1, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 8}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 8}, "repair_identified_action_types": {"unavailable": 1, "snipe": 2, "revive": 1, "attack": 2, "fireball": 3}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 6, "invalid_ability -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`. Tags may overlap.

Batch/cohort cumulative patterns: `{"initial_categories": {"ap_budget": 2, "schema_validation": 5, "invalid_reference": 23, "invalid_ability": 1}, "repair_categories": {"invalid_reference": 27, "schema_validation": 4}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 26, "AP_VIOLATION": 4, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 6, "revive": 8, "unavailable": 4, "move": 1, "fireball": 7, "attack": 5}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 2, "schema_validation -> invalid_reference": 3, "invalid_reference -> schema_validation": 2, "invalid_reference -> invalid_reference": 21, "schema_validation -> schema_validation": 2, "invalid_ability -> invalid_reference": 1}}`. Tags may overlap.

## Requests and bounded recovery

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 55 | 91 | 283 |
| turns | 41 | 54 | 93 |
| completed_turns | 39 | 48 | 91 |
| repairs | 14 | 18 | 16 |
| repair_success | 12 | 12 | 15 |
| repair_failure | 2 | 6 | 1 |
| execution_truncations | 20 | 2 | 0 |
| initial_execution_invalidities | 20 | 19 | 0 |
| replans | 0 | 19 | 0 |
| ap_recovered | 0 | 32 | 0 |
| replacement_repairs | 0 | 4 | 0 |
| replacement_invalidities | 0 | 0 | 0 |
| second_invalidities | 0 | 2 | 0 |
| decisions | 41 | 73 | 268 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 41 | 54 | 0 |
| repair | 14 | 14 | 16 |
| bounded_replacement_planning | 0 | 19 | 0 |
| bounded_replacement_repair | 0 | 4 | 0 |
| stepwise_decisions | 0 | 0 | 267 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 5.5000 | 1.3415 | 1.3077 | 1.9756 | {"target outside action range": 10, "impact outside Fireball range/board": 3, "blocked line of sight": 6, "destination is occupied, blocked, unchanged, or beyond move range": 1} |
| bounded | 9.1000 | 1.6852 | 1.6458 | 2.3333 | {"target outside action range": 12, "blocked line of sight": 4, "invalid target ACTIVE/DOWNED status": 3, "destination is occupied, blocked, unchanged, or beyond move range": 1, "impact outside Fireball range/board": 1} |
| stepwise | 28.3000 | 3.0430 | 3.0549 | 2.6022 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 19 |
| positive | 17 |
| positive_fraction | 0.8947 |
| ap_total | 32 |
| mean_ap_per_replan | 1.6842 |
| median_ap_per_replan | 2 |
| ap_at_replan | [2, 2, 1, 2, 1, 1, 2, 1, 2, 3, 2, 3, 3, 1, 3, 2, 4, 2, 3] |
| ap_recovered | [2, 2, 0, 2, 1, 1, 2, 1, 2, 3, 2, 3, 2, 1, 2, 0, 3, 2, 1] |
| Replan rate | 0.3519 |
| Second invalidity rate | 0.1053 |
| Replacement explicit EndTurns | 4 |
| Replacement failures | 0 |
| Extra requests vs Strict | 36 |
| Request premium vs Strict (%) | 65.4545 |
| Extra provider seconds vs Strict | 47.0329 |
| Extra tokens vs Strict | 94448 |
| Extra requests / recovered AP (descriptive) | 1.1250 |
| Strict minus Bounded final truncations | 18 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 1 |
| fraction | 0.1000 |
| requests | 140 |
| request_share | 0.4947 |
| match_ids | ["MATCH-047-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 91 | 283 |
| total_tokens | 252722 | 724340 |
| provider_latency_seconds | 150.6365 | 425.9247 |
| provider_requests/match | 9.1000 | 28.3000 |
| total_tokens/match | 25,272.2000 | 72,434.0000 |
| provider_requests/turn | 1.6852 | 3.0430 |
| total_tokens/turn | 4,680.0370 | 7,788.6022 |
| provider_latency_seconds/turn | 2.7896 | 4.5798 |
| W/L/no-result | [0, 10, 0] | [0, 9, 1] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-047-stepwise | red | [94, 46, 47] | [230, 137] | [140, 1, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 205 | 270 | 465 |
| ap_executed | 127 | 204 | 406 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 11 | 21 | 52 |
| CLEAN_PLAN_COMPLETE | 2 | 6 | 0 |
| EXECUTION_TRUNCATION | 53 | 3 | 0 |
| PROVIDER_FAILURE | 10 | 30 | 7 |
| TERMINAL | 2 | 6 | 0 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 3 |
| Actual provider-failure AP | 10 | 30 | 4 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 0 | {"0": 2, "1": 5, "2": 3} | {"3": 3, "2": 7} | 4 | 0 | 0 |
| bounded | 23 | 0 | {"1": 16, "3": 1, "0": 5, "2": 1} | {"2": 13, "1": 1, "4": 1, "3": 8} | 2 | 0 | 0 |
| stepwise | 24 | 6 | {"1": 16, "5": 6, "3": 2} | {"2": 16, "0": 6, "1": 2} | 3 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 5 | 0 |
| core_damage_received | 143 | 47 | 276 |
| enemy_damage | 141 | 220 | 950 |
| friendly_damage | 63 | 78 | 59 |
| enemy_units_downed | 7 | 17 | 60 |
| friendly_units_downed | 1 | 2 | 1 |
| units_downed_received | 32 | 46 | 44 |
| finish | 0 | 2 | 1 |
| revive | 8 | 28 | 26 |
| heal | 4 | 6 | 1 |
| snipe | 11 | 9 | 0 |
| shield_bash | 2 | 5 | 9 |
| shield_bash_pushes | 2 | 4 | 1 |
| fireball | 27 | 41 | 138 |
| empty_fireballs | 8 | 7 | 23 |
| friendly_only_fireballs | 10 | 15 | 5 |
| enemy_only_fireballs | 3 | 12 | 98 |
| mixed_fireballs | 6 | 7 | 12 |
| enemy_fireball_damage | 30 | 74 | 704 |
| friendly_fireball_damage | 63 | 78 | 59 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 9 | 21 | 178 |
| friendly_units_hit | 20 | 26 | 21 |
| enemy_damage | 30 | 74 | 704 |
| friendly_damage | 63 | 78 | 59 |
| enemy_downs | 1 | 6 | 0 |
| friendly_downs | 1 | 2 | 1 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-041-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-043-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-043-strict", "arm": "strict", "agent": "heuristic", "ordinal": 11, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 6, "friendly_downs": 0, "enemy_damage": 5, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-047-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 13, "friendly_units_hit": 0, "enemy_units_hit": 1, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 1, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-050-strict", "arm": "strict", "agent": "luna", "ordinal": 7, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "red"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 97 | 76 | 0 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 6 | 6 | 0 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 4 | 14 | 32 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 2 |
| arena_shield_bash enemy_displacements | 2 | 4 | 1 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 143 | 47 | 276 |
| core_damage_received | 0 | 5 | 0 |
| enemy_units_downed | 31 | 44 | 43 |
| finish | 7 | 6 | 10 |
| revive | 5 | 8 | 55 |
| ap_executed | 198 | 230 | 453 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 8.3125 | 9.9149 | 4.7897 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 55 | 91 | 283 |
| input_tokens | 153364 | 245396 | 711939 |
| cached_input_tokens | 93844 | 108857 | 312997 |
| output_tokens | 4910 | 7326 | 12401 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 158274 | 252722 | 724340 |
| provider_latency_seconds | 103.6036 | 150.6365 | 425.9247 |
| backend_thinking_seconds | 110.9328 | 161.0875 | 453.1483 |

| Resource | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Batch 5 | Cumulative |
| --- | --- | --- | --- | --- | --- | --- |
| provider_requests | 583 | 447 | 437 | 684 | 429 | 2580 |
| input_tokens | 1492199 | 1144928 | 1144996 | 1704836 | 1110699 | 6597658 |
| cached_input_tokens | 390703 | 337711 | 378495 | 402732 | 515698 | 2025339 |
| output_tokens | 32764 | 25301 | 25531 | 35519 | 24637 | 143752 |
| reasoning_tokens | 0 | 0 | 0 | 0 | 0 | 0 |
| total_tokens | 1524963 | 1170229 | 1170527 | 1740355 | 1135336 | 6741410 |
| provider_latency_seconds | 963.2223 | 748.6807 | 726.2118 | 1,081.6293 | 680.1648 | 4,199.9090 |
| backend_thinking_seconds | 1,008.7178 | 795.9576 | 773.5757 | 1,138.0684 | 725.1686 | 4,441.4882 |

| Control | Requests/match | Tokens/match | Provider sec/match | Requests/turn | Tokens/turn | Provider sec/turn | Backend sec/turn | Evidence elapsed sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 5.5000 | 15,827.4000 | 10.3604 | 1.3415 | 3,860.3415 | 2.5269 | 2.7057 | 131.3660 |
| bounded | 9.1000 | 25,272.2000 | 15.0637 | 1.6852 | 4,680.0370 | 2.7896 | 2.9831 | 186.9530 |
| stepwise | 28.3000 | 72,434.0000 | 42.5925 | 3.0430 | 7,788.6022 | 4.5798 | 4.8726 | 492.3798 |

| Batch | Observed process wall seconds upper bound | Start UTC | Completion observed UTC |
| --- | --- | --- | --- |
| 1 | 1,160.4115 | 2026-09-14T13:55:14.5492481Z | 2026-09-14T14:14:34.9607496Z |
| 2 | 1,013.4124 | 2026-09-14T14:41:07.0220353Z | 2026-09-14T14:58:00.4344287Z |
| 3 | 1,070.4722 | 2026-09-14T15:15:33.2411670Z | 2026-09-14T15:33:23.7133549Z |
| 4 | 1,468.7011 | 2026-09-14T15:49:31.0663785Z | 2026-09-14T16:13:59.767443+00:00 |
| 5 | 1,086.4948 | 2026-09-14T16:21:20.9995992Z | 2026-09-14T16:39:27.494440+00:00 |

Wall timing includes initial prefix verification and short completion-observation delay, but excludes later standalone analysis. Provider and backend times overlap. Evidence elapsed is per-match manifest-to-seal time; it excludes between-match gates. Cached input is part of input and reasoning tokens are part of output.

## Updated projection from cumulative rates

| provider_requests | Observed | Mean/match | Remaining 50/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 347 | 6.9400 | 347.0000 | 694.0000 | [2, 36] | [100, 1800] | [447, 2147] |
| bounded | 408 | 8.1600 | 408.0000 | 816.0000 | [2, 19] | [100, 950] | [508, 1358] |
| stepwise | 1825 | 36.5000 | 1,825.0000 | 3,650.0000 | [2, 140] | [100, 7000] | [1925, 8825] |

Combined provider_requests: remaining 150 central **2,580.000**; full 300 central **5,160.000**. Full-study sensitivity [2880, 12330].

| total_tokens | Observed | Mean/match | Remaining 50/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 974125 | 19,482.5000 | 974,125.0000 | 1,948,250.0000 | [6150, 97697] | [307500, 4884850] | [1281625, 5858975] |
| bounded | 1143654 | 22,873.0800 | 1,143,654.0000 | 2,287,308.0000 | [6263, 51830] | [313150, 2591500] | [1456804, 3735154] |
| stepwise | 4623631 | 92,472.6200 | 4,623,631.0000 | 9,247,262.0000 | [6409, 364261] | [320450, 18213050] | [4944081, 22836681] |

Combined total_tokens: remaining 150 central **6,741,410.000**; full 300 central **13,482,820.000**. Full-study sensitivity [7682510, 32430810].

| provider_latency_seconds | Observed | Mean/match | Remaining 50/control | All 100/control | Observed match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 646.7788 | 12.9356 | 646.7788 | 1,293.5577 | [3.2305263999733143, 60.84210030012764] | [161.5263199986657, 3042.105015006382] | [808.3051503986353, 3688.8838454063516] |
| bounded | 717.4969 | 14.3499 | 717.4969 | 1,434.9939 | [2.902137700060848, 32.23841570003424] | [145.1068850030424, 1611.920785001712] | [862.603810202796, 2329.4177102014655] |
| stepwise | 2,835.6332 | 56.7127 | 2,835.6332 | 5,671.2664 | [3.1789701000088826, 224.93943329993635] | [158.94850500044413, 11246.971664996818] | [2994.5817281018826, 14082.604888098256] |

Combined provider_latency_seconds: remaining 150 central **4,199.909**; full 300 central **8,399.818**. Full-study sensitivity [4665.490688703314, 20100.906443706073].

Provider hours: remaining **1.1666**, full **2.3333**.

Sensitivity fixes observed results and assigns every future game each control’s observed minimum/maximum. It is not a confidence interval. Caps censor natural duration, and early forfeits may reduce apparent costs. Extreme projections may exceed frozen ceilings, in which case guards must stop the study. No dollars are inferred.

If future workloads resemble observed batches, remaining 5 batches span 1.408–2.040 process wall hours; full study 3.018–3.651 hours. This workload illustration excludes later analysis; growing prefix verification and service conditions can add time.

## Matched triplet patterns and differences

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/loss": 9, "loss/loss/limit": 1}`; all-three-same outcome triplets: 9.

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 6, "limit_pairs": 0, "median_paired_player_turn_difference": 1.5, "provider_requests_per_turn_ratio": 1.2562289562289561, "total_tokens_per_turn_ratio": 1.2123375824109994, "backend_thinking_seconds_per_turn_ratio": 1.1025344838015978, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 9, "limit/loss": 1}, "provider_forfeit_pairs": 7, "limit_pairs": 1, "median_paired_player_turn_difference": 2.5, "provider_requests_per_turn_ratio": 1.805742644452322, "total_tokens_per_turn_ratio": 1.6642180582973871, "backend_thinking_seconds_per_turn_ratio": 1.6333877114658222, "win_difference_bootstrap_95": null}`

| Slot | Luna side | Outcomes S/B/W | Requests S/B/W | Player turns S/B/W | Request difference B-S/W-B | Turn difference B-S/W-B |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-041 | red | ["loss", "loss", "loss"] | [5, 8, 16] | [7, 10, 11] | [3, 8] | [3, 1] |
| MATCH-042 | blue | ["loss", "loss", "loss"] | [11, 2, 14] | [15, 1, 10] | [-9, 12] | [-14, 9] |
| MATCH-043 | red | ["loss", "loss", "loss"] | [7, 7, 24] | [11, 10, 14] | [0, 17] | [-1, 4] |
| MATCH-044 | blue | ["loss", "loss", "loss"] | [6, 8, 15] | [10, 9, 10] | [2, 7] | [-1, 1] |
| MATCH-045 | red | ["loss", "loss", "loss"] | [5, 14, 17] | [7, 16, 11] | [9, 3] | [9, -5] |
| MATCH-046 | blue | ["loss", "loss", "loss"] | [3, 3, 14] | [3, 3, 10] | [0, 11] | [0, 7] |
| MATCH-047 | red | ["loss", "loss", "limit"] | [4, 10, 140] | [5, 13, 94] | [6, 130] | [8, 81] |
| MATCH-048 | blue | ["loss", "loss", "loss"] | [7, 4, 15] | [12, 3, 10] | [-3, 11] | [-9, 7] |
| MATCH-049 | red | ["loss", "loss", "loss"] | [3, 19, 17] | [7, 29, 11] | [16, -2] | [22, -18] |
| MATCH-050 | blue | ["loss", "loss", "loss"] | [4, 16, 11] | [7, 11, 8] | [12, -5] | [4, -3] |

## Per-match evidence

| Match | Side | Outcome/cause | Turns/rounds | Requests/Luna turns | AP executed; I/C/X/P/T unused | Core damage dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-041-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [8, 5] | [20, 1, 1, 0, 0, 3] | [0, 5] | [1, 0, 0] | 820b3ea4b1292e7690cbc3c0d8471fb6cdc49ab57cb78f406c038c275430ef21 |
| MATCH-041-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [16, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | 038bd13a3d1e629941bbda7bb308ab56aec06fa05a96040fd31e1f21e0138f6f |
| MATCH-041-strict | red | loss/CORE_DESTRUCTION | [7, 3] | [5, 3] | [11, 0, 1, 3, 0, 0] | [0, 30] | [0, 0, 2] | 005103d6f1ef96e981f4a5242bfc077dc7ad638fe0ac97dc620fdb38a8bf320c |
| MATCH-042-bounded | blue | loss/PROVIDER_FORFEIT | [1, 0] | [2, 1] | [0, 0, 0, 0, 5, 0] | [0, 0] | [0, 0, 0] | fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d |
| MATCH-042-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [14, 5] | [16, 9, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d23222574ff12b66c647dc8d1f005a3008399e097365b91c2ca306ef40d195c3 |
| MATCH-042-strict | blue | loss/PROVIDER_FORFEIT | [15, 7] | [11, 8] | [20, 1, 0, 14, 5, 0] | [0, 18] | [2, 0, 0] | 3f2b24c8edf2c9caf0639547cd56cea044630e8e8eb057d4ca0ae75645e4d3a7 |
| MATCH-043-bounded | red | loss/TEAM_ELIMINATION | [10, 4] | [7, 5] | [17, 5, 0, 0, 0, 3] | [0, 0] | [1, 0, 0] | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-043-stepwise | red | loss/PROVIDER_FORFEIT | [14, 6] | [24, 7] | [30, 1, 0, 0, 4, 0] | [0, 18] | [4, 0, 1] | 6645dfc8b456d76c346819c16450038ae639342cf20df28f1489ad8eb01bc100 |
| MATCH-043-strict | red | loss/TEAM_ELIMINATION | [11, 5] | [7, 5] | [15, 1, 1, 8, 0, 0] | [0, 0] | [1, 0, 2] | 0845b1a7052e6166331bf6708593bd12aac0a7bb2eedb1fa49d2ee8089865a75 |
| MATCH-044-bounded | blue | loss/PROVIDER_FORFEIT | [9, 4] | [8, 5] | [19, 0, 1, 0, 5, 0] | [5, 0] | [3, 0, 0] | d7991b8bb4e3226a1a10510e1c3c20b09499566ba5c5291292eec9d15154d8fa |
| MATCH-044-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [17, 8, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-044-strict | blue | loss/CORE_DESTRUCTION | [10, 4] | [6, 5] | [15, 0, 0, 10, 0, 0] | [0, 30] | [1, 0, 0] | aebf7905c96802762e3dacc02b2da885efc58f927703aecd4fe48a7de421b58b |
| MATCH-045-bounded | red | loss/PROVIDER_FORFEIT | [16, 7] | [14, 8] | [33, 2, 0, 0, 5, 0] | [0, 9] | [3, 1, 3] | c27096a915e099436461b2468548786153c098002f226ee3982ec58b8fcc974d |
| MATCH-045-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [17, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [2, 1, 0] | 1437bfd8b6b9199d40b42b61ef9a252a750e012f0fafc1da20491237c954aba7 |
| MATCH-045-strict | red | loss/CORE_DESTRUCTION | [7, 3] | [5, 3] | [11, 2, 0, 2, 0, 0] | [0, 30] | [0, 0, 3] | 153accf95b3f76572ce8a66c461d436c2bae3fb8b32d1d4b283477182f67ec38 |
| MATCH-046-bounded | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-046-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [14, 5] | [11, 14, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | 23cf3727d8fb813df2d314c0115b134d0f40d36c923dde242a1f6e7fd3dcc65f |
| MATCH-046-strict | blue | loss/PROVIDER_FORFEIT | [3, 1] | [3, 2] | [5, 0, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | f08940b0dd5b4bc94a1cd040bef854c7f854e2fd322813d765302e2939b04070 |
| MATCH-047-bounded | red | loss/TEAM_ELIMINATION | [13, 6] | [10, 6] | [28, 2, 0, 0, 0, 0] | [0, 15] | [3, 0, 3] | 800a609f8e9239ae10cab839e6d048d584dd8e50ac794d81506be588779710e5 |
| MATCH-047-stepwise | red | limit/REQUEST_LIMIT | [94, 46] | [140, 47] | [230, 2, 0, 0, 3, 0] | [0, 18] | [44, 0, 25] | a66b4f227cdf789884e24bbd8715c9f345e02a4573c920fe6cad24be086069a2 |
| MATCH-047-strict | red | loss/TEAM_ELIMINATION | [5, 2] | [4, 2] | [8, 2, 0, 0, 0, 0] | [0, 0] | [0, 0, 0] | 262f9b49b00b51017eb8e0ccd11f56e77e84272322f4e7630c4992426ab1f543 |
| MATCH-048-bounded | blue | loss/PROVIDER_FORFEIT | [3, 1] | [4, 2] | [4, 1, 0, 0, 5, 0] | [0, 0] | [1, 0, 0] | 8b54cc3ea51d623383192428031b0911f06b2bde9e465fcd076b0ba539209445 |
| MATCH-048-stepwise | blue | loss/CORE_DESTRUCTION | [10, 4] | [15, 5] | [17, 8, 0, 0, 0, 0] | [0, 30] | [1, 0, 0] | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-048-strict | blue | loss/CORE_DESTRUCTION | [12, 5] | [7, 6] | [19, 2, 0, 9, 0, 0] | [0, 30] | [1, 0, 1] | 281ba32bf24926c4c9bfa329cefdf837bc8478619a15ae47e68ab08e75ee8e32 |
| MATCH-049-bounded | red | loss/TEAM_ELIMINATION | [29, 14] | [19, 14] | [59, 7, 3, 1, 0, 0] | [0, 18] | [1, 1, 22] | 04dd4440df30657bcc27830a3e6ad279f98b7fb76af6de20ecaa4a81bfb9f17b |
| MATCH-049-stepwise | red | loss/CORE_DESTRUCTION | [11, 5] | [17, 5] | [24, 1, 0, 0, 0, 0] | [0, 30] | [3, 0, 0] | 038bd13a3d1e629941bbda7bb308ab56aec06fa05a96040fd31e1f21e0138f6f |
| MATCH-049-strict | red | loss/TEAM_ELIMINATION | [7, 3] | [3, 3] | [9, 1, 0, 5, 0, 0] | [0, 5] | [0, 0, 0] | c85aae76941ff976e99aba55ed65a8249617386f6bbb03a82a415241bed4a754 |
| MATCH-050-bounded | blue | loss/PROVIDER_FORFEIT | [11, 5] | [16, 6] | [19, 3, 1, 2, 5, 0] | [0, 0] | [3, 0, 0] | da51b2cc86959bbcbdebfb1689aacb1722c7ece27cf4296fe9c5dbfff8576ef0 |
| MATCH-050-stepwise | blue | loss/CORE_DESTRUCTION | [8, 3] | [11, 4] | [13, 7, 0, 0, 0, 0] | [0, 30] | [0, 0, 0] | 16d40de12ba750419e9990708d5fa59f400e9730ab643c471826ca118eff18d7 |
| MATCH-050-strict | blue | loss/TEAM_ELIMINATION | [7, 3] | [4, 4] | [14, 2, 0, 2, 0, 2] | [0, 0] | [1, 0, 0] | 6d3a8490aa3f1803cff1f1d599d64c3bae2d2d9d4a9a3ace05071178a1902385 |

## Decision and limitations

Additional side-specific forfeits/caps and cost rates, Stepwise capped/uncapped means and sorted distribution, complete triplet classifications and cap gameplay: [focused comparisons](focused-comparisons.md).

See [decision.md](decision.md) for interpretation and continuation recommendation. INTERIM at n=50/control; frozen confirmatory inference waits for 100/control. No tuning or replacement of failed/capped games. [Figures](figures.md); machine metrics: interim-metrics.json; command audit: supplemental-audit.json; repair evidence: repair-forensics.json.
