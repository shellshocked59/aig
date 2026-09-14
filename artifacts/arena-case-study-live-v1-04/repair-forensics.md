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
| cumulative | strict | 40 | 71/221 | 71 | 63 | 8 | 88.732% | 8 |
| cumulative | bounded | 40 | 68/249 | 68 | 57 | 11 | 83.824% | 11 |
| cumulative | stepwise | 40 | 64/1478 | 64 | 61 | 3 | 95.312% | 3 |

## Category and action patterns

Batch/cohort 1: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 2: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 3: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`

Batch/cohort 4: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`

Batch/cohort cumulative: `{"initial_categories": {"ap_budget": 2, "schema_validation": 4, "invalid_reference": 16}, "repair_categories": {"invalid_reference": 19, "schema_validation": 3}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 18, "AP_VIOLATION": 3, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 4, "revive": 7, "unavailable": 3, "move": 1, "fireball": 4, "attack": 3}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 2, "schema_validation -> invalid_reference": 2, "invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 15, "schema_validation -> schema_validation": 2}}`

## Every Batch 4 exhausted repair

### MATCH-031-strict — red

Player-turn ordinal 2; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-031-strict\turns\0002.json](matches\MATCH-031-strict\turns\0002.json); SHA-256 `f20c90212c5b0c5bd8dc792da946f32e0e408793887e70b2d61c57f2e4ecbe5d`.

**Initial response** — request 1468; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 5, "y": 1}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_07572a8d6ddaf403016aa818387b2087d09cf722a50af78ab3`; provider request ID `req_b4f2d3232696427cad288af09d151459`. Structured response SHA-256 `14c377a46f05decf9609d75a5a5fd6b183dde0199de61031d7090fc6732a3471`.

**Repair response** — request 1469; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}`. Actor `red-cleric` (owned=True, status=active); target `red-ranger` (status=downed). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 4, "allowed_range": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 5, "y": 1}}, {"type": "move", "unit_id": "red-knight", "destination": {"x": 5, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0406cdc67e0d26ae016aa8183adc9c87d0ae2fa9ca19c3223f`; provider request ID `req_1ada31a30eb04a328744a994fdd6f113`. Structured response SHA-256 `14c377a46f05decf9609d75a5a5fd6b183dde0199de61031d7090fc6732a3471`.

### MATCH-032-bounded — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 1; replacement=True; AP at wave 2, AP left 2. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-032-bounded\turns\0001.json](matches\MATCH-032-bounded\turns\0001.json); SHA-256 `1e5c3182836a476c1537031f7b89207c9262de27d63122885b38312a451cf5ae`.

**Initial response** — request 1623; category `ap_budget`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 2; planned AP 4; over budget 2.

Validator: `{"category": "ap_budget", "action_index": null, "field_path": "actions", "message": "Selected actions exceed current AP.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 2, "planned_ap": 4, "over_budget_by": 2}, {"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_09062fd20b539f23016aa8193e59ec87d0b33f552af06b5c58`; provider request ID `req_cd2a639978ca443a977925ee62a67d36`. Structured response SHA-256 `991c782dbcb3515e09220be429341cc4f5d9bc1aea06e2af1dd5b1ba03bbf1a1`.

**Repair response** — request 1624; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 2; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0f9a7a5eafff119c016aa819408ba087d0b2acfd34635ff542`; provider request ID `req_4a4857733ba44e6f8160668a80322599`. Structured response SHA-256 `4dc0c1ae3b2c933001fca3ef6272c090af9e21aa2709e97c874c888750f8f656`.

### MATCH-032-strict — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-032-strict\turns\0001.json](matches\MATCH-032-strict\turns\0001.json); SHA-256 `6bcca5e4fb9ab8f2f55b9caa978e7fedf5daef09bb16b31a64465f655189fbce`.

**Initial response** — request 1639; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 6, "allowed_range": 4}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0c1f9769e01ff40c016aa8195aa1c087d0a7d6f217c1c287d9`; provider request ID `req_672be856da504dd9a789b2c45bcbef62`. Structured response SHA-256 `c11975c563c2c8afafd73c0a5633ea921ec1465285421e0e0eb261cb9458f8ef`.

**Repair response** — request 1640; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_066e8fde166288a5016aa8195c388087d0a2a5b20072682494`; provider request ID `req_d160b4ec619d410fa844ba2dc7513c88`. Structured response SHA-256 `eb4afd0ff65230d1d2f2e4e8a1877b490ffde93b913d9c3bd7d10588c104992c`.

### MATCH-037-bounded — red

Player-turn ordinal 4; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-037-bounded\turns\0004.json](matches\MATCH-037-bounded\turns\0004.json); SHA-256 `6698fae319c583ab358a797a97a1bec20f90a42fb4b7edcf771d618cd6966a78`.

**Initial response** — request 1893; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-cleric", "target_id": "blue-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_035c84d7917139ba016aa81b3c4fd087d0bc421b491b9509c6`; provider request ID `req_40de7fa810534849ab3f31f0eccfe109`. Structured response SHA-256 `41187ab7648baf5e89500f14fc023a0f31cd1aeb4a2c6d06d54fcbc2385fab10`.

**Repair response** — request 1894; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, {"type": "attack", "unit_id": "red-mage", "target_id": "blue-mage"}, {"type": "attack", "unit_id": "red-cleric", "target_id": "blue-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_058ea65c2349c6fc016aa81b3e2bb087d09fc74a400b651641`; provider request ID `req_6a8e8202be2b46a38ba53a09d7b3eb36`. Structured response SHA-256 `41187ab7648baf5e89500f14fc023a0f31cd1aeb4a2c6d06d54fcbc2385fab10`.

### MATCH-040-bounded — blue

Player-turn ordinal 5; engine round index 2 (round number 3); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-040-bounded\turns\0005.json](matches\MATCH-040-bounded\turns\0005.json); SHA-256 `9ba2c2910b0062115f9e0d47c2d6fb3c18a0dd3df2507ea87ac6da2fed78c725`.

**Initial response** — request 2134; category `schema_validation`; descriptive tags `['AP_VIOLATION']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 7; over budget 2.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 7, "over_budget_by": 2}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}, {"type": "move", "unit_id": "blue-cleric", "destination": {"x": 2, "y": 2}}, {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_04c76aa5c9890c08016aa81ce87d3887d08e499ff505c1b68a`; provider request ID `req_d2fdfc2aeba04e8797ecaefe91aa98b9`. Structured response SHA-256 `77c8128572e4885b1b3e0cacaf627b10ab106b6dbb98096dbc92ff8b92f792b5`.

**Repair response** — request 2135; category `schema_validation`; descriptive tags `['AP_VIOLATION']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 3, "y": 2}}, {"type": "revive", "unit_id": "blue-cleric", "target_id": "blue-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_06d58d46e6afcca2016aa81ceb803c87d0b9a8638a226c9a81`; provider request ID `req_f3ddf0a019344918b26203edab3f490d`. Structured response SHA-256 `9f3c682c4ceff1a82885e3afacd347cc902c36d971ce706f993fa5ed3818a893`.

Full initial and repair structured plans, detailed diagnostics, and earlier-batch cases are in [repair-forensics.json](repair-forensics.json). A field absent from sanitized evidence is unavailable, not evidence that the model omitted it.
