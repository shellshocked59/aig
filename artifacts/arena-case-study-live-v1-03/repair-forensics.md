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
| cumulative | strict | 30 | 56/182 | 56 | 50 | 6 | 89.286% | 6 |
| cumulative | bounded | 30 | 48/184 | 48 | 40 | 8 | 83.333% | 8 |
| cumulative | stepwise | 30 | 47/950 | 47 | 44 | 3 | 93.617% | 3 |

## Category and action patterns

Batch/cohort 1: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 2: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 3: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`

Batch/cohort cumulative: `{"initial_categories": {"ap_budget": 1, "schema_validation": 3, "invalid_reference": 13}, "repair_categories": {"invalid_reference": 15, "schema_validation": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 14, "AP_VIOLATION": 2, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 3, "revive": 5, "unavailable": 2, "move": 1, "fireball": 3, "attack": 3}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 2, "invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 12, "schema_validation -> schema_validation": 1}}`

## Every Batch 3 exhausted repair

### MATCH-022-stepwise — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 2; replacement=False; AP at wave 2, AP left 2. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-022-stepwise\turns\0001.json](matches\MATCH-022-stepwise\turns\0001.json); SHA-256 `7fed3ad3693bef78995181a2090ccb9de81fe096a4e7febc3220c3d2497c1d65`.

**Initial response** — request 1228; category `invalid_reference`; descriptive tags `['INVALID_TARGET_REFERENCE_OR_STATUS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}`. Actor `blue-ranger` (owned=True, status=active); target `red-core` (status=None). Available AP 2; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": "actions[0].target_id", "message": "Only attack can target a Core.", "rejected_value": null}`. Diagnostics: `[{"code": "invalid_reference", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}, "field": "target_id", "message": "Only attack can target a Core."}, {"code": "current_action_invalid", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}, "message": "invalid target ownership or entity type", "actual_distance": 4, "allowed_range": 4}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0c7f6b58c7de73d8016aa811ae165487d0995e07a28f470a0b`; provider request ID `req_e538db1205f24ba89cd322283cac6a69`. Structured response SHA-256 `c66b74a0d105b44217928f62e98ead7f8d22288c121a23ee280df5ecfe13d2e3`.

**Repair response** — request 1229; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "attack", "unit_id": "blue-ranger", "target_id": "red-core"}`. Actor `blue-ranger` (owned=True, status=active); target `red-core` (status=None). Available AP 2; planned AP 1; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "attack", "unit_id": "blue-ranger", "target_id": "red-core"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 3}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "attack", "unit_id": "blue-ranger", "target_id": "red-core"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0a9f444bacd2da4b016aa811b076c087d0b6c8ea2f0ae49ae3`; provider request ID `req_f5677944f4504ed68647b437d824823e`. Structured response SHA-256 `dc54195c62f21fce95dec0d4c907ccefcb36808222a1fb859445882216079f83`.

### MATCH-022-strict — blue

Player-turn ordinal 57; engine round index 28 (round number 29); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-022-strict\turns\0057.json](matches\MATCH-022-strict\turns\0057.json); SHA-256 `f03c279013c9d3b0836d2bdfe5224f70bb9d9ddd1e84776a2f09c910909456ee`.

**Initial response** — request 1216; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "heal", "unit_id": "blue-cleric", "target_id": "blue-mage"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-mage` (status=active). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "heal", "unit_id": "blue-cleric", "target_id": "blue-mage"}, "message": "blocked line of sight", "actual_distance": 1, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "heal", "unit_id": "blue-cleric", "target_id": "blue-mage"}, {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0f5f2dc5efac07e4016aa811910eb887d0886245de92c1edc5`; provider request ID `req_5286c1d8121447c3a2d35f8a8715e576`. Structured response SHA-256 `b78ec894a1e0ea138ec1ad21237d8b4e441846bc6318f7c5d5e94fe3624ab781`.

**Repair response** — request 1217; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-knight` (status=downed). Available AP 5; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0588902e31907529016aa8119274dc87d083370fa7e31bc28c`; provider request ID `req_d1a89f5221034af8a923466c7283d91d`. Structured response SHA-256 `0974fcbf7b9fcabe246e2d1d51c8ee5cd9bf433db89b8b1163e9cd09229decd3`.

### MATCH-024-bounded — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 1; replacement=True; AP at wave 4, AP left 4. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-024-bounded\turns\0003.json](matches\MATCH-024-bounded\turns\0003.json); SHA-256 `f7330b1b4f0804ec8847ded679d399977fb51d8317c1b4b3265cb6ccdb1dd170`.

**Initial response** — request 1300; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 4; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 5, "y": 4}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0e1d8a7e8df4ffe1016aa81242990487d096d18c4dbbe63b69`; provider request ID `req_846e752cfd5a470ba3d34b8cba151ce9`. Structured response SHA-256 `bcd8ba8b86a46a98341cd4b13363abff1f3e9ae41e1ec8504ef080de9c0d1217`.

**Repair response** — request 1301; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 5, "y": 4}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 4; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 5, "y": 4}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 5, "y": 4}}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_08bf8f09f0142924016aa812442fc887d0ad80c7c7a963b929`; provider request ID `req_7c253133cd284d3189490b68e3ec9340`. Structured response SHA-256 `4f3d89a09aeef44b65d590e92e0c75d32a1869e61243f007423c04c8d6c8985b`.

### MATCH-026-bounded — blue

Player-turn ordinal 7; engine round index 3 (round number 4); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-026-bounded\turns\0007.json](matches\MATCH-026-bounded\turns\0007.json); SHA-256 `3cdfc0b8462975022973b39f6e99d83f21099a185b62f22a9eccb097c467f2c3`.

**Initial response** — request 1350; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}`. Actor `blue-ranger` (owned=True, status=active); target `red-mage` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-mage"}, {"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0c52112055a499c0016aa812a5764487d082bdfa2f926778c0`; provider request ID `req_24ec31cf99fe44dcba251372a4720803`. Structured response SHA-256 `399597a958b4237b6fa871e51326d8285a79f61cddf9dfa136e16682d1cb5b02`.

**Repair response** — request 1351; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}`. Actor `blue-knight` (owned=True, status=active); target `red-cleric` (status=active). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}, "message": "target outside action range", "actual_distance": 2, "allowed_range": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "attack", "unit_id": "blue-knight", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-cleric"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_09e0326a8881d5b1016aa812a7657887d09e1b80573a6ba854`; provider request ID `req_57bdc39b61774452884455c712205c98`. Structured response SHA-256 `6c550e728f159daffeecc8d95d57d1dbbc0079359ea2beaa22e5fd39e44161ef`.

### MATCH-028-bounded — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-028-bounded\turns\0003.json](matches\MATCH-028-bounded\turns\0003.json); SHA-256 `4a9225679c465b287f015d5fc263737bbfed287003ca76365e953a2805a83b3c`.

**Initial response** — request 1409; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0a31b102549509a8016aa8132099d887d0b4ff7fa736ddb1a5`; provider request ID `req_125d8787d76b4cfba0b4db8d3a346028`. Structured response SHA-256 `fa5aff05f43f2e4a888902f568e7d30a49c1d9b687741770bf3088bdcdcc1249`.

**Repair response** — request 1410; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_013376e10b2263ca016aa813225bc487d0b182f5230b104ab8`; provider request ID `req_1fa970bd21134d4a85e432abfa7a5743`. Structured response SHA-256 `c11975c563c2c8afafd73c0a5633ea921ec1465285421e0e0eb261cb9458f8ef`.

### MATCH-028-stepwise — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-028-stepwise\turns\0001.json](matches\MATCH-028-stepwise\turns\0001.json); SHA-256 `b2c68cc130e38cf9162fd4dc256aa3a6ccb59e5651570e2a96498cf4392a737b`.

**Initial response** — request 1411; category `invalid_reference`; descriptive tags `['INVALID_TARGET_REFERENCE_OR_STATUS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}`. Actor `blue-ranger` (owned=True, status=active); target `red-core` (status=None). Available AP 5; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": "actions[0].target_id", "message": "Only attack can target a Core.", "rejected_value": null}`. Diagnostics: `[{"code": "invalid_reference", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}, "field": "target_id", "message": "Only attack can target a Core."}, {"code": "current_action_invalid", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}, "message": "invalid target ownership or entity type", "actual_distance": 7, "allowed_range": 4}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-core"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0716b70a039f87a0016aa8132467c887d0b2b7099e4fba09df`; provider request ID `req_87ae2ad9680f45c9ac7369b8e1daaa87`. Structured response SHA-256 `c66b74a0d105b44217928f62e98ead7f8d22288c121a23ee280df5ecfe13d2e3`.

**Repair response** — request 1412; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "attack", "unit_id": "blue-ranger", "target_id": "red-core"}`. Actor `blue-ranger` (owned=True, status=active); target `red-core` (status=None). Available AP 5; planned AP 1; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "attack", "unit_id": "blue-ranger", "target_id": "red-core"}, "message": "target outside action range", "actual_distance": 7, "allowed_range": 3}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "attack", "unit_id": "blue-ranger", "target_id": "red-core"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0cf72eabdca902da016aa81326075c87d09de0fff080b4fa32`; provider request ID `req_2a680af5a78f4bc2afc6707526b4f4fa`. Structured response SHA-256 `dc54195c62f21fce95dec0d4c907ccefcb36808222a1fb859445882216079f83`.

### MATCH-028-strict — blue

Player-turn ordinal 5; engine round index 2 (round number 3); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-028-strict\turns\0005.json](matches\MATCH-028-strict\turns\0005.json); SHA-256 `dba1e3b32b51c60d270bcc62f0c2c4e785785253ccd0e405feba270f4aecdcf3`.

**Initial response** — request 1406; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-mage"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_00f468855bcd2d33016aa81319da7087d08be127894fdfc9ea`; provider request ID `req_dcf21236887c4135b9545a610df6d84b`. Structured response SHA-256 `40cd8d5fd4e3a040853fdeecd16eb0b45daed0444cbffbe5d19c2b8d27e4b0f0`.

**Repair response** — request 1407; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}`. Actor `blue-cleric` (owned=True, status=active); target `blue-knight` (status=downed). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-knight"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0b013e438c43aca6016aa8131b6f2887d0abf3651761873714`; provider request ID `req_b1a10fbd9d8c46c0a8918c95e2b33e35`. Structured response SHA-256 `c7869ec032f6f16303f7dd7c540cfc65ce91a7711e40809824e9f3b34bf4b027`.

### MATCH-029-bounded — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-029-bounded\turns\0002.json](matches\MATCH-029-bounded\turns\0002.json); SHA-256 `294dcdbe2184398aa35924c092f6812c8774631b1c084b79dd5c3a2e33cfbaf5`.

**Initial response** — request 1413; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 5, "y": 2}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}, {"type": "attack", "unit_id": "red-knight", "target_id": "blue-mage"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0683c1b551a87fcc016aa81328594087d0aad69a806252b613`; provider request ID `req_73a4611207bc4fd7b991099b45638d22`. Structured response SHA-256 `4f3db5fca03ca145eddb896971f43ebdf0ae2c5cdabb3ffec60c2784e064d65d`.

**Repair response** — request 1414; category `schema_validation`; descriptive tags `['AP_VIOLATION']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "move", "unit_id": "red-cleric", "destination": {"x": 6, "y": 3}}, {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 5, "y": 2}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0b613d284e1237e3016aa8132a79b887d0a4bf4b51dd94d4fe`; provider request ID `req_2858c70bdf83457aae828c7bc01acd91`. Structured response SHA-256 `58c3b12c9eff34f0bcd1c524307eeac78b5161658e49bbc9e4dbe2314105b0b0`.

Full initial and repair structured plans, detailed diagnostics, and earlier-batch cases are in [repair-forensics.json](repair-forensics.json). A field absent from sanitized evidence is unavailable, not evidence that the model omitted it.
