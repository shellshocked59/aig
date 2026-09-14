# Repair-exhaustion forensics — interim Batches 1–3

invalid_reference is broad: first-action catalog failures can be range/LOS or status errors with valid IDs. Classification tags may overlap. Schema-invalid outputs may lack retained actions; no raw prose or hidden reasoning is used.

This is a descriptive audit of saved structured outputs and repository-owned diagnostics. It does not modify validation, replay, telemetry or the benchmark contract. No chain-of-thought or raw prose is included.

| Batch | Control | Matches | First invalid/decisions | Repairs attempted | Succeeded | Exhausted | Success rate | Forfeits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | strict | 10 | 24/61 | 24 | 23 | 1 | 95.833% | 1 |
| 1 | bounded | 10 | 19/76 | 19 | 18 | 1 | 94.737% | 1 |
| 1 | stepwise | 10 | 16/387 | 16 | 16 | 0 | 100.000% | 0 |
| 2 | strict | 10 | 11/53 | 11 | 8 | 3 | 72.727% | 3 |
| 2 | bounded | 10 | 13/61 | 13 | 10 | 3 | 76.923% | 3 |
| 2 | stepwise | 10 | 17/292 | 17 | 16 | 1 | 94.118% | 1 |
| 3 | strict | 10 | 21/68 | 21 | 19 | 2 | 90.476% | 2 |
| 3 | bounded | 10 | 16/47 | 16 | 12 | 4 | 75.000% | 4 |
| 3 | stepwise | 10 | 14/271 | 14 | 12 | 2 | 85.714% | 2 |
| 4 | strict | 10 | 15/39 | 15 | 13 | 2 | 86.667% | 2 |
| 4 | bounded | 10 | 20/65 | 20 | 17 | 3 | 85.000% | 3 |
| 4 | stepwise | 10 | 17/528 | 17 | 17 | 0 | 100.000% | 0 |
| 5 | strict | 10 | 14/41 | 14 | 12 | 2 | 85.714% | 2 |
| 5 | bounded | 10 | 18/73 | 18 | 12 | 6 | 66.667% | 6 |
| 5 | stepwise | 10 | 16/267 | 16 | 15 | 1 | 93.750% | 1 |
| 6 | strict | 10 | 9/39 | 9 | 4 | 5 | 44.444% | 5 |
| 6 | bounded | 10 | 20/104 | 20 | 15 | 5 | 75.000% | 5 |
| 6 | stepwise | 10 | 19/384 | 19 | 19 | 0 | 100.000% | 0 |
| 7 | strict | 10 | 14/68 | 14 | 12 | 2 | 85.714% | 2 |
| 7 | bounded | 10 | 20/69 | 20 | 16 | 4 | 80.000% | 4 |
| 7 | stepwise | 10 | 22/563 | 22 | 22 | 0 | 100.000% | 0 |
| 8 | strict | 10 | 18/60 | 18 | 15 | 3 | 83.333% | 3 |
| 8 | bounded | 10 | 15/59 | 15 | 12 | 3 | 80.000% | 3 |
| 8 | stepwise | 10 | 16/400 | 16 | 16 | 0 | 100.000% | 0 |
| cumulative | strict | 80 | 126/429 | 126 | 106 | 20 | 84.127% | 20 |
| cumulative | bounded | 80 | 141/554 | 141 | 112 | 29 | 79.433% | 29 |
| cumulative | stepwise | 80 | 137/3092 | 137 | 133 | 4 | 97.080% | 4 |

## Category and action patterns

Batch/cohort 1: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 2: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 3: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`

Batch/cohort 4: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`

Batch/cohort 5: `{"initial_categories": {"invalid_reference": 7, "invalid_ability": 1, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 8}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 8}, "repair_identified_action_types": {"unavailable": 1, "snipe": 2, "revive": 1, "attack": 2, "fireball": 3}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 6, "invalid_ability -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 6: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 3, "ap_budget": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 9}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 9}, "repair_identified_action_types": {"unavailable": 1, "fireball": 3, "revive": 4, "snipe": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "schema_validation -> invalid_reference": 3, "invalid_reference -> invalid_reference": 5, "ap_budget -> invalid_reference": 1}}`

Batch/cohort 7: `{"initial_categories": {"invalid_reference": 4, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 6}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 6}, "repair_identified_action_types": {"revive": 3, "snipe": 2, "attack": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 4, "ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 8: `{"initial_categories": {"ap_budget": 1, "schema_validation": 2, "invalid_reference": 3}, "repair_categories": {"invalid_reference": 6}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 2, "move": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 2, "invalid_reference -> invalid_reference": 3}}`

Batch/cohort cumulative: `{"initial_categories": {"ap_budget": 5, "schema_validation": 11, "invalid_reference": 36, "invalid_ability": 1}, "repair_categories": {"invalid_reference": 48, "schema_validation": 5}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 46, "AP_VIOLATION": 5, "OTHER_CURRENT_ACTION_VALIDATION": 2}, "repair_identified_action_types": {"snipe": 11, "revive": 17, "unavailable": 5, "move": 2, "fireball": 12, "attack": 6}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 5, "schema_validation -> invalid_reference": 9, "invalid_reference -> schema_validation": 3, "invalid_reference -> invalid_reference": 33, "schema_validation -> schema_validation": 2, "invalid_ability -> invalid_reference": 1}}`

## Every Batch 4?5 exhausted repair

### MATCH-052-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-052-strict\turns\0003.json](matches\MATCH-052-strict\turns\0003.json); SHA-256 `f638101aacd4aa575c6257b7ded8ec52c6703e2a61787df86956346cc903f248`.

**Initial response** — request 2776; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0ac430b35f1fff06016aa82d002a2c87d0932b95d063387d08`; provider request ID `req_4770e6fb2503424e8f8104fe51e085e5`. Structured response SHA-256 `1b1fe1128a326080a20b2de6937179943da5bb50d200dde5bc154e5627642437`.

**Repair response** — request 2777; category `schema_validation`; descriptive tags `['AP_VIOLATION']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "move", "unit_id": "blue-ranger", "destination": {"x": 5, "y": 2}}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_01ef8e67c39e41aa016aa82d01f8d887d0a01eb20cac381afd`; provider request ID `req_1bdee09f560b413bbf0253ed2facd942`. Structured response SHA-256 `9a0c38d5d9bf5f4ae23f659ba9c2a586e011c3af11fe3931e23c5775c3053c17`.

### MATCH-053-bounded — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-053-bounded\turns\0002.json](matches\MATCH-053-bounded\turns\0002.json); SHA-256 `50029ae88da88b0734cbf5631e07c100a3eb36f1162a1bf0c173eea9830f89bf`.

**Initial response** — request 2800; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 0}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_04814bda1cccb259016aa82d30fd8487d09b602db0a41d0e05`; provider request ID `req_dfd19c0df6194a11a9cf2a9cbf15ce28`. Structured response SHA-256 `b0769ce2552c57f50b221f8dcdc0087fc5789f18b485bfacef548dd0c738db56`.

**Repair response** — request 2801; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 0}}`. Actor `red-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 0}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 0}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0d783db1db8151a7016aa82d32f5e087d0b5671bc9f7f450c4`; provider request ID `req_769255dd07bf417d85836629a6f47476`. Structured response SHA-256 `5198cc19417449f46d448cdf5b26d978caf8bfc4801e7d2b589e29dab48b0787`.

### MATCH-053-strict — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-053-strict\turns\0002.json](matches\MATCH-053-strict\turns\0002.json); SHA-256 `f5b0dd326e956b52f88bf8e9b8f1448680aca73d2de488e18810728248e170f3`.

**Initial response** — request 2829; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 3, "y": 2}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0383896dd33e713d016aa82d63799487d0ab406e44f33c343d`; provider request ID `req_f583f21bcaa4492aa231907dc8a3e790`. Structured response SHA-256 `66e99282e2881dcf9d125c777044012d642750b2d5ec43062be0896da5e5f844`.

**Repair response** — request 2830; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 3, "y": 2}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_069c9847c3d09c2e016aa82d656e1487d0aabab9ba5ae63e68`; provider request ID `req_b0da46cd455f4bbf8fcd253ee708717c`. Structured response SHA-256 `66e99282e2881dcf9d125c777044012d642750b2d5ec43062be0896da5e5f844`.

### MATCH-054-bounded — blue

Player-turn ordinal 5; engine round index 2 (round number 3); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-054-bounded\turns\0005.json](matches\MATCH-054-bounded\turns\0005.json); SHA-256 `897f1e6eef4347d269623b96a069c89fac8d4863293028f526f6bd7e84947f94`.

**Initial response** — request 2858; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_01ebd222da54b6b8016aa82da0123887d0b8f65db1d0b33c66`; provider request ID `req_82e8bf581633409485da214da3e219ff`. Structured response SHA-256 `b34715aba46a569d6b23849d873c20ccdb650175f683f0662a810652297baa0a`.

**Repair response** — request 2859; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_033f029f4cfa0c4d016aa82da1a4e487d092cec75ac5e4466c`; provider request ID `req_c78866148de3498cbf95f772b7eeb017`. Structured response SHA-256 `083789b6acb9bea733e440eff57c0b11d246210aa9554ca4c28ca28023004876`.

### MATCH-055-bounded — red

Player-turn ordinal 4; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-055-bounded\turns\0004.json](matches\MATCH-055-bounded\turns\0004.json); SHA-256 `7c1c66141377124deac81c97d2c4d28429c09efc52f66ce290b1dd2ddd99e795`.

**Initial response** — request 2865; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_015bd682ee2fe55b016aa82db1b7e887d0967ac92853c175ff`; provider request ID `req_7703f6c2713d405c9cc3779d55be6736`. Structured response SHA-256 `bec5b20e08152abbfaa21453dade0d1421a0c0ac3244c60ea95f563de55d57fb`.

**Repair response** — request 2866; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_006694afca518689016aa82db35b6887d0a7b58f357a13ea55`; provider request ID `req_6f69b67d10714fb1a1fc9866943aad8d`. Structured response SHA-256 `bec5b20e08152abbfaa21453dade0d1421a0c0ac3244c60ea95f563de55d57fb`.

### MATCH-056-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-056-strict\turns\0003.json](matches\MATCH-056-strict\turns\0003.json); SHA-256 `ac65dd47b530db15cf385b94465a7fec92ec0105dc6938dbe9e0053cdb002883`.

**Initial response** — request 2921; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}`. Actor `blue-ranger` (owned=True, status=active); target `red-cleric` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0f301838bdf60c0f016aa82e29a2bc87d09884d35035c475e0`; provider request ID `req_805d7b6b5b86406e83cce4d68eea39f6`. Structured response SHA-256 `61011418d376d4e239e3a05ff7e01ed5f4524cc0a92159247b204459b21e7c6f`.

**Repair response** — request 2922; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0b3495bcc19d809a016aa82e2b648087d0995a56228ba2ee76`; provider request ID `req_67e845d502004cc58ab4df5b8133884a`. Structured response SHA-256 `39db167bd7bbeac3ecec222ffc37219a3cacf168786656e15b6860b21bac90cb`.

### MATCH-058-bounded — blue

Player-turn ordinal 7; engine round index 3 (round number 4); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-058-bounded\turns\0007.json](matches\MATCH-058-bounded\turns\0007.json); SHA-256 `0c4ad77afd8f273db87fa41a77758d2bdcf85e4863c7b86e47703b81a6233d99`.

**Initial response** — request 2963; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-ranger` (status=downed). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, "message": "target outside action range", "actual_distance": 3, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, {"type": "move", "unit_id": "blue-ranger", "destination": {"x": 5, "y": 1}}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_06f5b5df8c271b1d016aa82e8fcd1887d0a6fe38b350c8623e`; provider request ID `req_29ccb1c0d3124cae9108737bff1ccac4`. Structured response SHA-256 `b36e4b80127089e638f616c903c316abf795a6e42881cb05d64a21ac666a42af`.

**Repair response** — request 2964; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-ranger` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, "message": "target outside action range", "actual_distance": 3, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_096a1074b8818a9a016aa82e92868087d0bc973b9ba10fba94`; provider request ID `req_3b6894fad8f04c5eb132d4e8d18b915e`. Structured response SHA-256 `b48d74aaa8b0d28b03e7c3a8b6271b9941ed2d7cdd74c01d2a49e7d509fb46d8`.

### MATCH-058-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-058-strict\turns\0003.json](matches\MATCH-058-strict\turns\0003.json); SHA-256 `aa377e75b55e1662a0f7f77be294a0dd99cf73f85cd6a9cea260f3d5b1c2e07b`.

**Initial response** — request 2956; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_06a78ba2be44b115016aa82e80955087d099234d0000b504d2`; provider request ID `req_3f731eb5a6f941fbb15278d6e9caaddf`. Structured response SHA-256 `fa5aff05f43f2e4a888902f568e7d30a49c1d9b687741770bf3088bdcdcc1249`.

**Repair response** — request 2957; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0f0856581be0a9d5016aa82e82651c87d08371d50a54781878`; provider request ID `req_cb5343af27914630a297210a0f6b96ed`. Structured response SHA-256 `eb4afd0ff65230d1d2f2e4e8a1877b490ffde93b913d9c3bd7d10588c104992c`.

### MATCH-059-strict — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-059-strict\turns\0002.json](matches\MATCH-059-strict\turns\0002.json); SHA-256 `b59f7ca472273f8542f3a22cc536cf09bd3e8614a51e3ef7fcb5b3ecd0a3c0c4`.

**Initial response** — request 3128; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "snipe", "unit_id": "red-ranger", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "shield_bash", "unit_id": "red-knight", "target_id": "blue-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0419d8a3471ef09b016aa82fa199a887d09d6ce54c36d6400f`; provider request ID `req_1e6f765f3ccc4e6fbae489fdcbda7baa`. Structured response SHA-256 `66c12419fd6dca2b5e426ad9d1fc6b4a9bb3582aac1ca06f8c5039938d6672fb`.

**Repair response** — request 3129; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "shield_bash", "unit_id": "red-knight", "target_id": "blue-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0673fd8fd1607522016aa82fa43c8887d08e730661a3347158`; provider request ID `req_dc75c553ffd741a0ac3a03a4684d4114`. Structured response SHA-256 `aa83f896ec5e33e32793489d5dc0e29cc839e2679774b5b2d0cbaf3807c6839d`.

### MATCH-060-bounded — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 1; replacement=True; AP at wave 2, AP left 2. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-060-bounded\turns\0001.json](matches\MATCH-060-bounded\turns\0001.json); SHA-256 `aa25c148742718c7cb178dfaad1e702e681541f8829420f8af099493af03cf5c`.

**Initial response** — request 3154; category `ap_budget`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 2; planned AP 4; over budget 2.

Validator: `{"category": "ap_budget", "action_index": null, "field_path": "actions", "message": "Selected actions exceed current AP.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 2, "planned_ap": 4, "over_budget_by": 2}, {"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0b6ca8df0010c1a6016aa82fd90e4c87d0ba77f445429cdbff`; provider request ID `req_07c01c25b0e04338b8ec38a2afd55b62`. Structured response SHA-256 `0c237ac08bbf33ba037323846f00cb25c840f5f01e5756eda998dac78e1fcc68`.

**Repair response** — request 3155; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}`. Actor `blue-ranger` (owned=True, status=active); target `red-mage` (status=active). Available AP 2; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_00b77f749bc0beea016aa82fdb45e487d0b5f15f5980ca63e9`; provider request ID `req_fdd33ffbe4f04576bf7c262dfc4bd4d5`. Structured response SHA-256 `36fb857b672d6c9c48d772fbde1d75f88794b8954c01c1539a2bfb28eabb3472`.

### MATCH-061-bounded — red

Player-turn ordinal 6; engine round index 2 (round number 3); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-061-bounded\turns\0006.json](matches\MATCH-061-bounded\turns\0006.json); SHA-256 `1e45b150654ed8504d474d3146a774eb63751b8c26b6ccf2cf0cc6cd05163a0d`.

**Initial response** — request 3164; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-cleric", "target_id": "blue-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_065a72f9c66cdab4016aa833cfe87087d0af2c0e7a6f83e84e`; provider request ID `req_98dd8f170efd47f0b4b6ac0693331c65`. Structured response SHA-256 `8a828b834956e40e7191b478db4dddd5faeb74af6a65f5fe29a0ad02cf4f48a4`.

**Repair response** — request 3165; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-cleric", "target_id": "blue-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0f34954981b9f306016aa833d1755087d091c94b2344ee0225`; provider request ID `req_7e383c20b8a4496ea48e52a9a614253b`. Structured response SHA-256 `41187ab7648baf5e89500f14fc023a0f31cd1aeb4a2c6d06d54fcbc2385fab10`.

### MATCH-062-bounded — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 1; replacement=True; AP at wave 2, AP left 2. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-062-bounded\turns\0001.json](matches\MATCH-062-bounded\turns\0001.json); SHA-256 `80af2aa22b8b66b404cafa479fe38b02382f8cfdf54c8a9aa977f255e103f1da`.

**Initial response** — request 3185; category `ap_budget`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 2; planned AP 4; over budget 2.

Validator: `{"category": "ap_budget", "action_index": null, "field_path": "actions", "message": "Selected actions exceed current AP.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 2, "planned_ap": 4, "over_budget_by": 2}, {"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 2, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_06d994a6c67b5fa6016aa833f6698887d094053106899e0a3c`; provider request ID `req_2bc3187edaac4e6d93d1671af2250c98`. Structured response SHA-256 `1a22a8ee11fde37b484b6265099dcd6a7fce2bdf475979c45fa83f18c1f20014`.

**Repair response** — request 3186; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}`. Actor `blue-ranger` (owned=True, status=active); target `red-mage` (status=active). Available AP 2; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0df404ef2f2acca0016aa833f9189c87d08b67cb6c75fafab3`; provider request ID `req_0318cd8bb13d4ea0be4950d56755341d`. Structured response SHA-256 `36fb857b672d6c9c48d772fbde1d75f88794b8954c01c1539a2bfb28eabb3472`.

### MATCH-064-bounded — blue

Player-turn ordinal 7; engine round index 3 (round number 4); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-064-bounded\turns\0007.json](matches\MATCH-064-bounded\turns\0007.json); SHA-256 `ecf567b4e04710b551e0e97648cf26b0060c353edf7fcaeeb36fabba34311304`.

**Initial response** — request 3375; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}`. Actor `blue-ranger` (owned=True, status=active); target `red-mage` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, {"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_03ddd33af820cd2a016aa8353c6ff487d0bc1a93e233f01562`; provider request ID `req_e0ba309bacde40a9b83bbde8da55d944`. Structured response SHA-256 `399597a958b4237b6fa871e51326d8285a79f61cddf9dfa136e16682d1cb5b02`.

**Repair response** — request 3376; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}`. Actor `blue-knight` (owned=True, status=active); target `red-cleric` (status=active). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}, "message": "target outside action range", "actual_distance": 2, "allowed_range": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_087f322a06704010016aa8353e3e7487d0802fb3d6a2c6d979`; provider request ID `req_b5a84b9d1057408bad2be70f68b4c691`. Structured response SHA-256 `6c550e728f159daffeecc8d95d57d1dbbc0079359ea2beaa22e5fd39e44161ef`.

### MATCH-064-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-064-strict\turns\0003.json](matches\MATCH-064-strict\turns\0003.json); SHA-256 `6a63170338afda640ad1c6b991ae0588da4f5ce53717b393a9f0c4211fac5f8c`.

**Initial response** — request 3367; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}`. Actor `blue-ranger` (owned=True, status=active); target `red-cleric` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0f38edae9894d186016aa8352dd4dc87d081691ba7ec9021f6`; provider request ID `req_d8f8137ccf834d13828bbaae7317a012`. Structured response SHA-256 `fcfe0424643aafc2320ed4a6babc25f953fea756aeaab71d7f209521df4dbda1`.

**Repair response** — request 3368; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0a9d81600de8b201016aa8352f974487d0bb902133b75162cf`; provider request ID `req_c1d7f605fc0d49c3a49915df7e3a27eb`. Structured response SHA-256 `b0e33ee0b1960e5a1ee004019c2cd77edc48090f9985fe4be557560472233d63`.

### MATCH-065-bounded — red

Player-turn ordinal 6; engine round index 2 (round number 3); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-065-bounded\turns\0006.json](matches\MATCH-065-bounded\turns\0006.json); SHA-256 `01e5336e77e7ba9daa7a840cd2fca399683d54c234ff85389f7b8d3c91dea711`.

**Initial response** — request 3393; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0739f0d1e9ca34a4016aa8355ae84887d097f6b633a316fa3a`; provider request ID `req_063fa0e4e3de493e816c80b59f8d2fd0`. Structured response SHA-256 `df1880835aab9c27d26add6a80ce99f3f98498f3232014aad3712bac0f53e8c1`.

**Repair response** — request 3394; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0a09d11a195672b1016aa8355c9ac487d09faa0efaa9b9cb29`; provider request ID `req_5b0c9b190ea4468881e3d6e85c6b3c2f`. Structured response SHA-256 `df1880835aab9c27d26add6a80ce99f3f98498f3232014aad3712bac0f53e8c1`.

### MATCH-068-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-068-strict\turns\0003.json](matches\MATCH-068-strict\turns\0003.json); SHA-256 `509a12c999d4a4f3ce860e420b0f98db551ab575fab150966844733a1687039e`.

**Initial response** — request 3695; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 3}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0aa0e8e934c2a273016aa83773f8b087d0a839f7b83ce1a3e4`; provider request ID `req_50b45a1594d3444e8ef0d01f6531ea40`. Structured response SHA-256 `e957ea6496b77a3e445b7bf832b59af4280d9492d2053ab27ddeedb49a629e15`.

**Repair response** — request 3696; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0aa186f6ce6a78f4016aa83775ea6087d0be4324df66617d37`; provider request ID `req_1d015f59193e40a492dfcef68b45dc99`. Structured response SHA-256 `c24d2523b3fc87e9ccdff8a7fe04e6559a16680d089e876f2a7d30e8b56c3b2a`.

### MATCH-073-bounded — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 1; replacement=True; AP at wave 2, AP left 2. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-073-bounded\turns\0002.json](matches\MATCH-073-bounded\turns\0002.json); SHA-256 `d152b2a8f66c71a61a44fcb2585a913b49f859120c374b97a3716e07f9a61c41`.

**Initial response** — request 3968; category `ap_budget`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 2; planned AP 4; over budget 2.

Validator: `{"category": "ap_budget", "action_index": null, "field_path": "actions", "message": "Selected actions exceed current AP.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 2, "planned_ap": 4, "over_budget_by": 2}, {"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_08450991ba44b556016aa83e236a1087d08c0b9da4927e41f5`; provider request ID `req_f31177500e854be9b9d6e1dc6121b921`. Structured response SHA-256 `866af79a8030ee61976d578e952485b54d3f3fa0c6c4803041bf594084d8661a`.

**Repair response** — request 3969; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 2; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_095651316d829f72016aa83e25324487d0a873ce8a9452fd30`; provider request ID `req_a8463528bdcf414e94da925396a48872`. Structured response SHA-256 `2bf968f25afa835553882c572f1332551271ee02c80606862928e34ce762bc8a`.

### MATCH-073-strict — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-073-strict\turns\0002.json](matches\MATCH-073-strict\turns\0002.json); SHA-256 `acbdfef8b07032b79f3423497aae40011f64ee28e526e6d3643f0f8bd08e4a9c`.

**Initial response** — request 3965; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 7; over budget 2.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 7, "over_budget_by": 2}, {"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "snipe", "unit_id": "red-ranger", "target_id": "blue-ranger"}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 0}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0314ec3c63c17fd2016aa83e1ca85887d081ec7bb7d5a240e1`; provider request ID `req_69629b369a914be2b32b90f3270c84c3`. Structured response SHA-256 `fbc894ad8c41e021403e19004940f133674442fb22faf4d087fbeecba673df54`.

**Repair response** — request 3966; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0992fcada0638908016aa83e1e864c87d0b6ecb18c21c851a6`; provider request ID `req_eb0add9410504d0f85295c734e25a65c`. Structured response SHA-256 `29e0070acae4df34cfa25c35bedd5eda2d750cd39a43a113c50cfc18c8f07958`.

### MATCH-074-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-074-strict\turns\0003.json](matches\MATCH-074-strict\turns\0003.json); SHA-256 `bbf9cabc14198266aad2ce5a37d5db71cf34670dbf5972edc1210a1f6fb54c5f`.

**Initial response** — request 4010; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_028b4a6ec170260a016aa83e6eec2487d0a7e92a2762793127`; provider request ID `req_1f90319f532146a5af8a9dfd8dcb62b0`. Structured response SHA-256 `4319a5dbc91a82ef8f16e593df25497e772ca79379829ff482a97101e7f726ed`.

**Repair response** — request 4011; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}`. Actor `blue-ranger` (owned=True, status=active); target `red-cleric` (status=active). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0eb91a21e87dcd0a016aa83e70713887d0a6eb116086a873d8`; provider request ID `req_c564ec30ca8a4a0888a8143002c4c86c`. Structured response SHA-256 `d1862e81018865c7c78e860a5f995f684da883454c234a4ce52d11ff9c48c954`.

### MATCH-078-bounded — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-078-bounded\turns\0003.json](matches\MATCH-078-bounded\turns\0003.json); SHA-256 `0b55d99ac834fafbc0bf432be104c4de31f72ef995bd91a561bea9db5b2d3f1e`.

**Initial response** — request 4298; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_077b795a2b3cdda2016aa8404f0b2087d0af69d30585e4947e`; provider request ID `req_fd8f3580428f449bacfb8580888a07c7`. Structured response SHA-256 `fa5aff05f43f2e4a888902f568e7d30a49c1d9b687741770bf3088bdcdcc1249`.

**Repair response** — request 4299; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0ed2659897606137016aa84050b4e087d0898f7c4a742db19f`; provider request ID `req_45d1d543d8e3470eab654dbd6cfdb8b1`. Structured response SHA-256 `eb4afd0ff65230d1d2f2e4e8a1877b490ffde93b913d9c3bd7d10588c104992c`.

### MATCH-080-bounded — blue

Player-turn ordinal 9; engine round index 4 (round number 5); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-080-bounded\turns\0009.json](matches\MATCH-080-bounded\turns\0009.json); SHA-256 `1b450aba120cdcdb7e966571dbc9bc1be86cb5b35fb574a10f562043d60524ef`.

**Initial response** — request 4460; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-ranger` (status=downed). Available AP 5; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, "message": "target outside action range", "actual_distance": 3, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0cb058fa70bfc95d016aa841589d8887d0a7f2b85257852f88`; provider request ID `req_c514f55a568e4ee586c55a1f0fcba7fc`. Structured response SHA-256 `1fae3d1bccebec3b56de6d8b26dfe101dd1950eedeeb4d5915902fa2ffce7fab`.

**Repair response** — request 4461; category `invalid_reference`; descriptive tags `['OTHER_CURRENT_ACTION_VALIDATION']`.

Action index 0; action `{"type": "move", "unit_id": "blue-cleric", "destination": {"x": 3, "y": 3}}`. Actor `blue-cleric` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "move", "unit_id": "blue-cleric", "destination": {"x": 3, "y": 3}}, "message": "destination is occupied, blocked, unchanged, or beyond move range"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "move", "unit_id": "blue-cleric", "destination": {"x": 3, "y": 3}}, {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_086721075f107635016aa8415ae70087d0992dd05a88037e3c`; provider request ID `req_72980c62a17e4eaa8f52053f676b47b2`. Structured response SHA-256 `f988729a6123f46e87089f6cb5e9dbe19fa3f9810ebb616b6019b27e7787583a`.

### MATCH-080-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-080-strict\turns\0003.json](matches\MATCH-080-strict\turns\0003.json); SHA-256 `1c51357e0c897008cd1511511d950a667cd577c332a67b5a7c94ba925ca4a5b8`.

**Initial response** — request 4478; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 5, "y": 2}}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-cleric"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_063fbe85415c02c7016aa84179717c87d0a8191614b4457006`; provider request ID `req_0fdf19aa2b5842a798e5ce44180eedd8`. Structured response SHA-256 `a1dd15b3168ec78a44d0f4edc97ebc3988821e63bd2277e9dccb96f293d4055c`.

**Repair response** — request 4479; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 5, "y": 2}}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-cleric"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_065c1b10b1039a11016aa8417b479887d0876df637d7fe0502`; provider request ID `req_db82521e815740599fbe67a447651684`. Structured response SHA-256 `083eef8d54d0cdc60b3ddae3ea10dcc0bba0824e9f405313dea004151c67349b`.

Full initial and repair structured plans, detailed diagnostics, and earlier-batch cases are in [repair-forensics.json](repair-forensics.json). A field absent from sanitized evidence is unavailable, not evidence that the model omitted it.
