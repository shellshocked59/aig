# Cumulative Batches 1–3 — INTERIM

**n=30/control, 90 sealed matches.** One canonical opening, independent nondeterministic Luna trajectories. No final-study hypothesis test or control winner is claimed. [Decision and research-question answers](decision.md).

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
| strict | 30 | 30 | {"red": 15, "blue": 15} | {"CORE_DESTRUCTION": 10, "TEAM_ELIMINATION": 14, "PROVIDER_FORFEIT": 6} |
| bounded | 30 | 30 | {"red": 15, "blue": 15} | {"TEAM_ELIMINATION": 18, "PROVIDER_FORFEIT": 8, "CORE_DESTRUCTION": 4} |
| stepwise | 30 | 30 | {"red": 15, "blue": 15} | {"REQUEST_LIMIT": 4, "CORE_DESTRUCTION": 16, "TEAM_ELIMINATION": 7, "PROVIDER_FORFEIT": 3} |

## Outcomes and heuristic baseline

| Agent/matchup | Wins | Losses incl. forfeit | No-result | Win rate | Wilson 95% | Requests/turn |
| --- | --- | --- | --- | --- | --- | --- |
| strict Luna | 0 | 30 | 0 | 0.0000 | [0, 0.11351339317396876] | 1.3077 |
| Heuristic vs strict | 30 | 0 | 0 | 1.0000 | [0.8864866068260312, 0.9999999999999999] | 0.0000 |
| bounded Luna | 0 | 30 | 0 | 0.0000 | [0, 0.11351339317396876] | 1.8268 |
| Heuristic vs bounded | 30 | 0 | 0 | 1.0000 | [0.8864866068260312, 0.9999999999999999] | 0.0000 |
| stepwise Luna | 2 | 24 | 4 | 0.0667 | [0.018477023791270378, 0.2132345836261692] | 3.0867 |
| Heuristic vs stepwise | 24 | 2 | 4 | 0.8000 | [0.6269430358685175, 0.9049489282271013] | 0.0000 |

| Control | Luna side | W/L/no-result | Wilson 95% |
| --- | --- | --- | --- |
| strict | red | [0, 15, 0] | [0, 0.20388330103584862] |
| strict | blue | [0, 15, 0] | [0, 0.20388330103584862] |
| bounded | red | [0, 15, 0] | [0, 0.20388330103584862] |
| bounded | blue | [0, 15, 0] | [0, 0.20388330103584862] |
| stepwise | red | [1, 10, 4] | [0.011866895493268553, 0.2981652987378003] |
| stepwise | blue | [1, 14, 0] | [0.011866895493268553, 0.2981652987378003] |

| Control | Forfeits | Request limits | Turn limits | Other no-results | Player turns total/median/range | Rounds total/median/range |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 6 | 0 | 0 | 0 | [369, 9.5, [2, 57]] | [164, 4.0, [0, 28]] |
| bounded | 8 | 0 | 0 | 0 | [254, 10.0, [2, 18]] | [104, 4.0, [0, 8]] |
| stepwise | 3 | 4 | 0 | 0 | [650, 11.0, [1, 94]] | [302, 5.0, [0, 46]] |

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
| provider_requests | 238 | 232 | 997 |
| turns | 182 | 127 | 323 |
| completed_turns | 176 | 119 | 316 |
| repairs | 56 | 48 | 47 |
| repair_success | 50 | 40 | 44 |
| repair_failure | 6 | 8 | 3 |
| execution_truncations | 82 | 9 | 0 |
| initial_execution_invalidities | 82 | 57 | 0 |
| replans | 0 | 57 | 0 |
| ap_recovered | 0 | 103 | 0 |
| replacement_repairs | 0 | 19 | 0 |
| replacement_invalidities | 0 | 4 | 0 |
| second_invalidities | 0 | 9 | 0 |
| decisions | 182 | 184 | 954 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 182 | 127 | 0 |
| repair | 56 | 29 | 47 |
| bounded_replacement_planning | 0 | 57 | 0 |
| bounded_replacement_repair | 0 | 19 | 0 |
| stepwise_decisions | 0 | 0 | 950 |

| Control | Requests/match | Requests/Luna turn | Requests/completed turn | Actions/Luna turn | Execution invalidity categories |
| --- | --- | --- | --- | --- | --- |
| strict | 7.9333 | 1.3077 | 1.2841 | 1.8681 | {"target outside action range": 43, "destination is occupied, blocked, unchanged, or beyond move range": 6, "blocked line of sight": 19, "impact outside Fireball range/board": 10, "invalid target ACTIVE/DOWNED status": 3, "actor must own an ACTIVE unit": 1} |
| bounded | 7.7333 | 1.8268 | 1.7647 | 2.4882 | {"target outside action range": 35, "blocked line of sight": 12, "impact outside Fireball range/board": 10, "invalid target ACTIVE/DOWNED status": 6, "destination is occupied, blocked, unchanged, or beyond move range": 2, "actor must own an ACTIVE unit": 1} |
| stepwise | 33.2333 | 3.0867 | 3.1108 | 2.7399 | {} |

Request-purpose rows are disjoint: Stepwise decisions exclude repairs and unsent budget-denied decisions; initial/Stepwise repairs and bounded replacement repairs are separate. Cost/turn uses attempted Luna turns.

| Bounded metric | Observed |
| --- | --- |
| replans | 57 |
| positive | 51 |
| positive_fraction | 0.8947 |
| ap_total | 103 |
| mean_ap_per_replan | 1.8070 |
| ap_at_replan | [2, 3, 3, 1, 3, 2, 2, 4, 4, 4, 2, 2, 4, 3, 2, 4, 2, 2, 2, 3, 1, 4, 2, 2, 2, 2, 3, 4, 3, 3, 3, 2, 3, 3, 1, 3, 1, 1, 3, 3, 3, 4, 4, 2, 4, 4, 4, 2, 4, 3, 2, 4, 1, 3, 2, 4, 1] |
| ap_recovered | [2, 3, 2, 1, 0, 2, 2, 2, 3, 1, 2, 2, 3, 1, 2, 2, 2, 2, 1, 2, 0, 1, 2, 2, 2, 1, 3, 4, 3, 3, 3, 2, 2, 3, 0, 1, 1, 1, 2, 1, 3, 0, 0, 2, 2, 4, 3, 2, 0, 2, 2, 1, 1, 2, 2, 2, 1] |
| Replan rate | 0.4488 |
| Second invalidity rate | 0.1579 |
| Replacement explicit EndTurns | 15 |
| Replacement failures | 4 |
| Extra requests vs Strict | -6 |
| Request premium vs Strict (%) | -2.5210 |
| Extra provider seconds vs Strict | -29.9860 |
| Extra tokens vs Strict | -7087 |
| Extra requests / recovered AP (descriptive) | -0.0583 |
| Strict minus Bounded final truncations | 73 |
| Bounded minus Strict wins | 0 |

Extra requests/recovered AP is a descriptive difference across independent trajectories, not a causal cost of recovering one AP. Different match lengths and early forfeits affect totals. AP recovery does not establish better game quality. Replacement failure counts above are exhausted repairs; all frozen replacement-error totals are separately listed.

## Stepwise caps and Bounded comparison

| Stepwise cap metric | Observed |
| --- | --- |
| count | 4 |
| fraction | 0.1333 |
| requests | 560 |
| request_share | 0.5617 |
| match_ids | ["MATCH-001-stepwise", "MATCH-009-stepwise", "MATCH-015-stepwise", "MATCH-021-stepwise"] |

| Metric | Bounded | Stepwise |
| --- | --- | --- |
| provider_requests | 232 | 997 |
| total_tokens | 653148 | 2552336 |
| provider_latency_seconds | 406.5777 | 1,594.9734 |
| provider_requests/match | 7.7333 | 33.2333 |
| total_tokens/match | 21,771.6000 | 85,077.8667 |
| provider_requests/turn | 1.8268 | 3.0867 |
| total_tokens/turn | 5,142.8976 | 7,901.9690 |
| provider_latency_seconds/turn | 3.2014 | 4.9380 |
| W/L/no-result | [0, 30, 0] | [2, 24, 4] |

| Capped match | Side | Player turns/rounds/Luna turns | AP/actions | Requests/repairs/EndTurns | Core HP | Engine winner |
| --- | --- | --- | --- | --- | --- | --- |
| MATCH-001-stepwise | red | [94, 46, 47] | [232, 138] | [140, 0, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-009-stepwise | red | [94, 46, 47] | [228, 136] | [140, 2, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-015-stepwise | red | [92, 45, 46] | [227, 135] | [140, 3, 2] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |
| MATCH-021-stepwise | red | [94, 46, 47] | [233, 139] | [140, 0, 1] | {"blue-core": 30, "red-core": 12} | unknown / not applicable |

Every cap retains a nonterminal authoritative final state without inventing a winner. [cap-details.json](cap-details.json) includes each unit’s ID, side, HP, status and position plus final-state paths/hashes. Natural uncapped outcomes are unknown for capped games.

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| ap_available | 910 | 635 | 1615 |
| ap_executed | 541 | 501 | 1453 |

| Unused AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 100 | 54 | 132 |
| CLEAN_PLAN_COMPLETE | 10 | 12 | 0 |
| EXECUTION_TRUNCATION | 219 | 18 | 0 |
| PROVIDER_FAILURE | 30 | 35 | 20 |
| TERMINAL | 10 | 15 | 10 |
| Budget-denied AP within generic failure bucket | 0 | 0 | 8 |
| Actual provider-failure AP | 30 | 35 | 12 |

The frozen generic PROVIDER_FAILURE bucket includes request-budget denial; the final two rows separate it. Intentional, clean, truncation, actual provider failure, budget denial and terminal AP must not be collapsed into “waste.”

| Control | Explicit stops | Immediate | AP left distribution | Actions before stop | Damaging option left | Down option left | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 65 | 1 | {"0": 5, "5": 1, "1": 36, "2": 11, "3": 11, "4": 1} | {"4": 3, "0": 1, "2": 42, "1": 12, "3": 7} | 24 | 3 | 0 |
| bounded | 51 | 0 | {"2": 5, "0": 12, "1": 29, "3": 5} | {"2": 24, "3": 22, "1": 4, "4": 1} | 11 | 1 | 0 |
| stepwise | 62 | 15 | {"1": 40, "5": 15, "3": 3, "2": 4} | {"2": 44, "0": 15, "1": 3} | 6 | 0 | 0 |

A damaging/down opportunity is a legal single action simulated from the saved stop state. It does not prove taking the action was strategically preferable. No model judge or counterfactual inference was used.

## Gameplay and combat

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 0 | 0 | 30 |
| core_damage_received | 410 | 218 | 617 |
| enemy_damage | 674 | 523 | 3596 |
| friendly_damage | 208 | 266 | 214 |
| enemy_units_downed | 33 | 36 | 225 |
| friendly_units_downed | 8 | 9 | 8 |
| units_downed_received | 96 | 99 | 143 |
| finish | 1 | 4 | 11 |
| revive | 11 | 16 | 86 |
| heal | 14 | 11 | 21 |
| snipe | 23 | 25 | 8 |
| shield_bash | 18 | 14 | 25 |
| shield_bash_pushes | 15 | 12 | 5 |
| fireball | 167 | 144 | 474 |
| empty_fireballs | 50 | 37 | 66 |
| friendly_only_fireballs | 38 | 54 | 18 |
| enemy_only_fireballs | 61 | 33 | 347 |
| mixed_fireballs | 18 | 20 | 43 |
| enemy_fireball_damage | 330 | 198 | 2657 |
| friendly_fireball_damage | 208 | 266 | 214 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 103 | 54 | 667 |
| friendly_units_hit | 64 | 84 | 74 |
| enemy_damage | 330 | 198 | 2657 |
| friendly_damage | 208 | 266 | 214 |
| enemy_downs | 5 | 8 | 4 |
| friendly_downs | 8 | 9 | 8 |

Fireballs immediately producing an engine winner: `[{"match_id": "MATCH-001-bounded", "arm": "bounded", "agent": "luna", "ordinal": 18, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 2, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-002-strict", "arm": "strict", "agent": "luna", "ordinal": 21, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "red"}, {"match_id": "MATCH-003-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-003-strict", "arm": "strict", "agent": "heuristic", "ordinal": 9, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 4, "friendly_downs": 0, "enemy_damage": 1, "enemy_downs": 1, "winner_after_action": "blue"}, {"match_id": "MATCH-005-bounded", "arm": "bounded", "agent": "luna", "ordinal": 12, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-006-strict", "arm": "strict", "agent": "luna", "ordinal": 33, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "red"}, {"match_id": "MATCH-007-stepwise", "arm": "stepwise", "agent": "luna", "ordinal": 8, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-009-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 11, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 2, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-011-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-011-strict", "arm": "strict", "agent": "luna", "ordinal": 38, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-013-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-013-strict", "arm": "strict", "agent": "heuristic", "ordinal": 9, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 5, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-015-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-015-strict", "arm": "strict", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}, {"match_id": "MATCH-018-stepwise", "arm": "stepwise", "agent": "heuristic", "ordinal": 10, "friendly_units_hit": 0, "enemy_units_hit": 1, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 1, "enemy_downs": 1, "winner_after_action": "red"}, {"match_id": "MATCH-019-bounded", "arm": "bounded", "agent": "heuristic", "ordinal": 7, "friendly_units_hit": 0, "enemy_units_hit": 2, "friendly_damage": 0, "friendly_downs": 0, "enemy_damage": 2, "enemy_downs": 2, "winner_after_action": "blue"}, {"match_id": "MATCH-020-stepwise", "arm": "stepwise", "agent": "luna", "ordinal": 13, "friendly_units_hit": 1, "enemy_units_hit": 1, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 2, "enemy_downs": 0, "winner_after_action": "red"}, {"match_id": "MATCH-027-bounded", "arm": "bounded", "agent": "luna", "ordinal": 10, "friendly_units_hit": 1, "enemy_units_hit": 0, "friendly_damage": 1, "friendly_downs": 1, "enemy_damage": 0, "enemy_downs": 0, "winner_after_action": "blue"}]`. Other longer-term consequences are not assigned causal credit. Counts can reflect repeated down/revive cycles and different exposure; they are not quality scores.

| Ability effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| arena_snipe enemy_damage | 203 | 205 | 66 |
| arena_snipe friendly_damage | 0 | 0 | 0 |
| arena_snipe enemy_downs | 15 | 16 | 5 |
| arena_snipe enemy_displacements | 0 | 0 | 0 |
| arena_shield_bash enemy_damage | 50 | 46 | 87 |
| arena_shield_bash friendly_damage | 0 | 0 | 0 |
| arena_shield_bash enemy_downs | 0 | 0 | 7 |
| arena_shield_bash enemy_displacements | 15 | 12 | 5 |

| Heuristic mechanics by matchup | strict | bounded | stepwise |
| --- | --- | --- | --- |
| core_damage_dealt | 410 | 218 | 617 |
| core_damage_received | 0 | 0 | 30 |
| enemy_units_downed | 88 | 90 | 135 |
| finish | 28 | 25 | 31 |
| revive | 24 | 20 | 200 |
| ap_executed | 654 | 552 | 1546 |
| provider_requests | 0 | 0 | 0 |
| total_tokens | 0 | 0 | 0 |
| provider_latency_seconds | 0 | 0 | 0 |
| heuristic_compute_seconds | 36.3167 | 22.4129 | 65.7284 |

Heuristic V2 is a first-class matchup-specific baseline. Its inference cost is zero; measured computation time is separate. No homogeneous pooled heuristic skill estimate is asserted.

## Resources and calibration

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| provider_requests | 238 | 232 | 997 |
| input_tokens | 639549 | 634164 | 2508410 |
| cached_input_tokens | 288208 | 305903 | 512798 |
| output_tokens | 20686 | 18984 | 43926 |
| reasoning_tokens | 0 | 0 | 0 |
| total_tokens | 660235 | 653148 | 2552336 |
| provider_latency_seconds | 436.5637 | 406.5777 | 1,594.9734 |
| backend_thinking_seconds | 462.2509 | 432.5445 | 1,683.4557 |

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
| strict | 7.9333 | 22,007.8333 | 1.3077 | 3,627.6648 | 2.3987 | 2.5398 | 546.6271 |
| bounded | 7.7333 | 21,771.6000 | 1.8268 | 5,142.8976 | 3.2014 | 3.4059 | 492.6920 |
| stepwise | 33.2333 | 85,077.8667 | 3.0867 | 7,901.9690 | 4.9380 | 5.2119 | 1,862.0098 |

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

Order is Strict / Bounded / Stepwise. Outcome patterns: `{"loss/loss/limit": 4, "loss/loss/loss": 24, "loss/loss/win": 2}`; all-three-same outcome triplets: 24.

`{"comparison": "bounded-strict", "pairs": 30, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 30}, "provider_forfeit_pairs": 11, "limit_pairs": 0, "median_paired_player_turn_difference": 0.0, "provider_requests_per_turn_ratio": 1.396943029180176, "total_tokens_per_turn_ratio": 1.4176882020473622, "backend_thinking_seconds_per_turn_ratio": 1.3409751043180687, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 30, "win_gains": 2, "win_losses": 0, "win_rate_difference": 0.06666666666666667, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 4, "loss/loss": 24, "win/loss": 2}, "provider_forfeit_pairs": 10, "limit_pairs": 4, "median_paired_player_turn_difference": 4.5, "provider_requests_per_turn_ratio": 1.6896952065762785, "total_tokens_per_turn_ratio": 1.536481881765626, "backend_thinking_seconds_per_turn_ratio": 1.5302841154057127, "win_difference_bootstrap_95": null}`

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

## Decision and limitations

See [decision.md](decision.md) for PASS/PAUSE, all ten research-question answers and next authorization scope. Results remain interim at n=30/control. Frozen confirmatory analysis waits for 100/control. No tuning, replacement of failed/capped games, or next-batch execution occurred. Figures: [figures.md](figures.md); machine-readable metrics: interim-metrics.json; command audits: supplemental-audit.json; repair evidence: repair-forensics.json.
