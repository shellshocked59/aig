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
| cumulative | strict | 50 | 85/262 | 85 | 75 | 10 | 88.235% | 10 |
| cumulative | bounded | 50 | 86/322 | 86 | 69 | 17 | 80.233% | 17 |
| cumulative | stepwise | 50 | 80/1745 | 80 | 76 | 4 | 95.000% | 4 |

## Category and action patterns

Batch/cohort 1: `{"initial_categories": {"ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 2}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 2}, "repair_identified_action_types": {"snipe": 1, "revive": 1}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 2: `{"initial_categories": {"invalid_reference": 6, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 6}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 5, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"unavailable": 1, "snipe": 1, "move": 1, "fireball": 2, "revive": 2}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 5, "schema_validation -> invalid_reference": 1}}`

Batch/cohort 3: `{"initial_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_categories": {"invalid_reference": 7, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 7, "AP_VIOLATION": 1}, "repair_identified_action_types": {"attack": 3, "revive": 2, "fireball": 1, "snipe": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 7, "schema_validation -> schema_validation": 1}}`

Batch/cohort 4: `{"initial_categories": {"invalid_reference": 3, "ap_budget": 1, "schema_validation": 1}, "repair_categories": {"invalid_reference": 4, "schema_validation": 1}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 4, "AP_VIOLATION": 1}, "repair_identified_action_types": {"revive": 2, "snipe": 1, "fireball": 1, "unavailable": 1}, "initial_to_repair_categories": {"invalid_reference -> invalid_reference": 3, "ap_budget -> invalid_reference": 1, "schema_validation -> schema_validation": 1}}`

Batch/cohort 5: `{"initial_categories": {"invalid_reference": 7, "invalid_ability": 1, "schema_validation": 1}, "repair_categories": {"schema_validation": 1, "invalid_reference": 8}, "repair_classifications": {"AP_VIOLATION": 1, "STATIC_RANGE_OR_LOS": 8}, "repair_identified_action_types": {"unavailable": 1, "snipe": 2, "revive": 1, "attack": 2, "fireball": 3}, "initial_to_repair_categories": {"invalid_reference -> schema_validation": 1, "invalid_reference -> invalid_reference": 6, "invalid_ability -> invalid_reference": 1, "schema_validation -> invalid_reference": 1}}`

Batch/cohort cumulative: `{"initial_categories": {"ap_budget": 2, "schema_validation": 5, "invalid_reference": 23, "invalid_ability": 1}, "repair_categories": {"invalid_reference": 27, "schema_validation": 4}, "repair_classifications": {"STATIC_RANGE_OR_LOS": 26, "AP_VIOLATION": 4, "OTHER_CURRENT_ACTION_VALIDATION": 1}, "repair_identified_action_types": {"snipe": 6, "revive": 8, "unavailable": 4, "move": 1, "fireball": 7, "attack": 5}, "initial_to_repair_categories": {"ap_budget -> invalid_reference": 2, "schema_validation -> invalid_reference": 3, "invalid_reference -> schema_validation": 2, "invalid_reference -> invalid_reference": 21, "schema_validation -> schema_validation": 2, "invalid_ability -> invalid_reference": 1}}`

## Every Batch 4?5 exhausted repair

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

### MATCH-042-bounded — blue

Player-turn ordinal 1; engine round index 0 (round number 1); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-042-bounded\turns\0001.json](matches\MATCH-042-bounded\turns\0001.json); SHA-256 `7b96bec7050b1580a8374429073ae87960be3076fd3cb0162a1a220960528560`.

**Initial response** — request 2206; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "target outside action range", "actual_distance": 6, "allowed_range": 4}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_018f7a7dcacf9b7c016aa8205b86f887d0811ee64c2a7b36c4`; provider request ID `req_9ccc6cf561e8418683d418c44cafd752`. Structured response SHA-256 `c11975c563c2c8afafd73c0a5633ea921ec1465285421e0e0eb261cb9458f8ef`.

**Repair response** — request 2207; category `schema_validation`; descriptive tags `['AP_VIOLATION']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "move", "unit_id": "blue-ranger", "destination": {"x": 4, "y": 0}}, {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_09ee59346b7dd9f7016aa8205cf83487d09016c04af745f321`; provider request ID `req_d9a669e29c3c4ffeb60c728c500c33c1`. Structured response SHA-256 `53149c7458ab4d34c0f305a5ae155322d9e2667bca5d29b03d7451935baaa537`.

### MATCH-042-strict — blue

Player-turn ordinal 15; engine round index 7 (round number 8); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-042-strict\turns\0015.json](matches\MATCH-042-strict\turns\0015.json); SHA-256 `98acb70e42610d2be9973a5bc648248ef804e40ce91b51cc9c78249fa05cc62f`.

**Initial response** — request 2204; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0a55399ffe14b5d2016aa82054cd7087d086aabb4b3e8e8349`; provider request ID `req_9fa0bb8dbb5441c4b3486429e92e4293`. Structured response SHA-256 `ef3fe6bb607b417aff05fe462a1aeaa64acc0cb0d5cc373b5e1d0e182195436a`.

**Repair response** — request 2205; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0dd25159a091e3f3016aa820588e3087d0849969e9e182a0ef`; provider request ID `req_d79a27f6f2b140a48e415039f185d3df`. Structured response SHA-256 `ef3fe6bb607b417aff05fe462a1aeaa64acc0cb0d5cc373b5e1d0e182195436a`.

### MATCH-043-stepwise — red

Player-turn ordinal 14; engine round index 6 (round number 7); wave 1; replacement=False; AP at wave 4, AP left 4. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-043-stepwise\turns\0014.json](matches\MATCH-043-stepwise\turns\0014.json); SHA-256 `fdeac921a25d83dad06d4ffea72e1b37518aa9eef3bfa63c5ad5d5e8c0bfdbea`.

**Initial response** — request 2244; category `invalid_ability`; descriptive tags `['ILLEGAL_ACTION_REFERENCE', 'INVALID_ACTOR_REFERENCE_OR_STATUS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-knight", "target_id": "red-knight"}`. Actor `red-knight` (owned=True, status=downed); target `red-knight` (status=downed). Available AP 4; planned AP 2; over budget 0.

Validator: `{"category": "invalid_ability", "action_index": 0, "field_path": "actions[0].type", "message": "Selected unit does not have this ability.", "rejected_value": null}`. Diagnostics: `[{"code": "invalid_ability", "action_index": 0, "action": {"type": "revive", "unit_id": "red-knight", "target_id": "red-knight"}, "field": "type", "message": "Selected unit does not have this ability."}, {"code": "actor_reference_or_status", "action_index": 0, "action": {"type": "revive", "unit_id": "red-knight", "target_id": "red-knight"}, "message": "actor must own an ACTIVE unit", "actual_distance": 0, "allowed_range": null}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-knight", "target_id": "red-knight"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0671e53a1e7be34f016aa820ab9f2c87d0b44b92233ef7de7c`; provider request ID `req_c4f4e0fba64d40838ceb70e2a536d702`. Structured response SHA-256 `582ec6c02e808758c71114d7dd8276b54818e5de52419a91a84b03215b9d98a4`.

**Repair response** — request 2245; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}`. Actor `red-cleric` (owned=True, status=active); target `red-knight` (status=downed). Available AP 4; planned AP 2; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 1, "allowed_range": 2, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "revive", "unit_id": "red-cleric", "target_id": "red-knight"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_02355a703ad7cb87016aa820ad1a1087d08f10ed79b74bf3c6`; provider request ID `req_41054bd789c7425cb64d330e5ed739ec`. Structured response SHA-256 `1894f48bb79200ebbbd53e482444f7b44dd435f121ed5eb8856415d7b9d77faf`.

### MATCH-044-bounded — blue

Player-turn ordinal 9; engine round index 4 (round number 5); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-044-bounded\turns\0009.json](matches\MATCH-044-bounded\turns\0009.json); SHA-256 `47eb33b5a1a5b17607515cfc787fcf35b469393b5d49ca1d181fa1fdf7d6c35e`.

**Initial response** — request 2252; category `invalid_reference`; descriptive tags `['INVALID_TARGET_REFERENCE_OR_STATUS']`.

Action index 0; action `{"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-core"}`. Actor `blue-knight` (owned=True, status=active); target `red-core` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": "actions[0].target_id", "message": "Only attack can target a Core.", "rejected_value": null}`. Diagnostics: `[{"code": "invalid_reference", "action_index": 0, "action": {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-core"}, "field": "target_id", "message": "Only attack can target a Core."}, {"code": "current_action_invalid", "action_index": 0, "action": {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-core"}, "message": "invalid target ownership or entity type", "actual_distance": 2, "allowed_range": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-core"}, {"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}, {"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_042ca0555982857f016aa820bd88bc87d0bfc9842cadcf39e8`; provider request ID `req_7f27d2e8898e4772a98ceba63b236511`. Structured response SHA-256 `ad459977a947b1451b16c782f60de5064228743403c55327e62475bbbbcbff3a`.

**Repair response** — request 2253; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}`. Actor `blue-knight` (owned=True, status=active); target `red-core` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "range", "action_index": 0, "action": {"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}, "message": "target outside action range", "actual_distance": 2, "allowed_range": 1}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}, {"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}, {"type": "attack", "unit_id": "blue-knight", "target_id": "red-core"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_088c58823d852e89016aa820bf0d5887d094b01d0e68193967`; provider request ID `req_6282bccc84a04ee9b3b5a0c1a76c9367`. Structured response SHA-256 `089a2f007603bd4b41489f1b8cf4c3636acb8081e454fe4110181649569794f7`.

### MATCH-045-bounded — red

Player-turn ordinal 16; engine round index 7 (round number 8); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-045-bounded\turns\0016.json](matches\MATCH-045-bounded\turns\0016.json); SHA-256 `74535264b3d7e514e7bb739544ac7efa247ab8b60a3407674ee5b85629c38e74`.

**Initial response** — request 2309; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "red-ranger", "target_id": "blue-knight"}`. Actor `red-ranger` (owned=True, status=active); target `blue-knight` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "red-ranger", "target_id": "blue-knight"}, "message": "blocked line of sight", "actual_distance": 4, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "red-ranger", "target_id": "blue-knight"}, {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 4}}, {"type": "heal", "unit_id": "red-cleric", "target_id": "red-ranger"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_014325a950682b73016aa8212be07487d08f46975cbf7d2980`; provider request ID `req_eb80048bffb842868e321cdba452f743`. Structured response SHA-256 `29132c2bee83dc0e7eff1f3fd04307377302789450d8d8bac7c0af7e416dcaa9`.

**Repair response** — request 2310; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 4}}`. Actor `red-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 4}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "red-mage", "target_position": {"x": 4, "y": 4}}, {"type": "heal", "unit_id": "red-cleric", "target_id": "red-ranger"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_08f165e34112210d016aa8212d837087d0b1808f0ddbc9ef27`; provider request ID `req_c0b0bacf556444348561c2c60beead89`. Structured response SHA-256 `b44ffa139a1fa34bc8697facb103908aaedadc5700847fb011eb05569a3bb335`.

### MATCH-046-bounded — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-046-bounded\turns\0003.json](matches\MATCH-046-bounded\turns\0003.json); SHA-256 `cc19dab390b0baf5caa7f913800526f3bd50948af596abc1759e3869839e6064`.

**Initial response** — request 2315; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_08f8ca0cc16862cb016aa821392eac87d0ad31166ebb27b4f4`; provider request ID `req_9e8ea75157a1480ab81ba9cc465429ec`. Structured response SHA-256 `e9e2f10fb928b7cbc88619021b61835e42cd944dc6dd9d90d939bdc6d4338a24`.

**Repair response** — request 2316; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}`. Actor `blue-ranger` (owned=True, status=active); target `red-knight` (status=active). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-knight"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 7, "y": 2}}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_01ecec52dba78e7f016aa8213ae00087d0abe8ff3c4ec8df10`; provider request ID `req_841f25de298f4abf918654eb29a7f38c`. Structured response SHA-256 `e9e2f10fb928b7cbc88619021b61835e42cd944dc6dd9d90d939bdc6d4338a24`.

### MATCH-046-strict — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-046-strict\turns\0003.json](matches\MATCH-046-strict\turns\0003.json); SHA-256 `0bfe621a4568092988e29e63b786b572d73e4dd7a14a5847fb3d6ee4c2647187`.

**Initial response** — request 2312; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}`. Actor `blue-ranger` (owned=True, status=active); target `red-cleric` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_00422e8a63f10f36016aa82132d44887d0a6646de66521f708`; provider request ID `req_4c6f22023c5743da8c1958b417858489`. Structured response SHA-256 `61011418d376d4e239e3a05ff7e01ed5f4524cc0a92159247b204459b21e7c6f`.

**Repair response** — request 2313; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 3; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 3, "y": 2}}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_0cef7819298075ba016aa821348e3887d0a10109c2fc0663b5`; provider request ID `req_b969219b29c9474cb8009210f820edc1`. Structured response SHA-256 `39db167bd7bbeac3ecec222ffc37219a3cacf168786656e15b6860b21bac90cb`.

### MATCH-048-bounded — blue

Player-turn ordinal 3; engine round index 1 (round number 2); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-048-bounded\turns\0003.json](matches\MATCH-048-bounded\turns\0003.json); SHA-256 `80e7a6efae0f7ba26c53a8ed5a9ef9304e4716c9641896e936134539128ea9b8`.

**Initial response** — request 2509; category `schema_validation`; descriptive tags `['AP_VIOLATION', 'STATIC_RANGE_OR_LOS']`.

Action index None; action `null`. Actor `None` (owned=None, status=None); target `None` (status=None). Available AP 5; planned AP 6; over budget 1.

Validator: `{"category": "schema_validation", "action_index": null, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "ap_budget", "available_ap": 5, "planned_ap": 6, "over_budget_by": 1}, {"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, "message": "blocked line of sight", "actual_distance": 2, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-cleric"}, {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 5, "y": 2}}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-cleric"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_02b3f2aaff0da88d016aa8228f55b487d0a18d61fdba7d35d9`; provider request ID `req_51ac6234c4744408a4961a377fb18411`. Structured response SHA-256 `ee65923762ac8fbedb42c656f1e9a6293d49e3f89724d17bda0d0d2041afd476`.

**Repair response** — request 2510; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}`. Actor `blue-mage` (owned=True, status=active); target `None` (status=None). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "current_action_invalid", "action_index": 0, "action": {"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, "message": "impact outside Fireball range/board"}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "fireball", "unit_id": "blue-mage", "target_position": {"x": 6, "y": 2}}, {"type": "move", "unit_id": "blue-knight", "destination": {"x": 5, "y": 2}}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-cleric"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_03803d1d47f0c2fb016aa8229126f487d0b9e5b4b510432688`; provider request ID `req_2110ffb92f0f426ab29189a1b334b91d`. Structured response SHA-256 `083eef8d54d0cdc60b3ddae3ea10dcc0bba0824e9f405313dea004151c67349b`.

### MATCH-050-bounded — blue

Player-turn ordinal 11; engine round index 5 (round number 6); wave 0; replacement=False; AP at wave 5, AP left 5. Result: PROVIDER_FORFEIT, forfeit=True. Engine winner remains None.

Evidence: [matches\MATCH-050-bounded\turns\0011.json](matches\MATCH-050-bounded\turns\0011.json); SHA-256 `090e516154e6ffd38ba03fb6375ce466c19d9d0045afcf0e5d070f80b0f51347`.

**Initial response** — request 2564; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 5; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 4, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "snipe", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-knight"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-ranger"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_04aee45b55e3402f016aa822f8177487d0beec8c374344b2cc`; provider request ID `req_d00fdaa8bb44407e831d29460227b26c`. Structured response SHA-256 `16e1134c1ece0e3f4634ac30bced44a7013f92c7a571fb07f4cac66a5483b9ef`.

**Repair response** — request 2565; category `invalid_reference`; descriptive tags `['STATIC_RANGE_OR_LOS']`.

Action index 0; action `{"type": "attack", "unit_id": "blue-ranger", "target_id": "red-ranger"}`. Actor `blue-ranger` (owned=True, status=active); target `red-ranger` (status=active). Available AP 5; planned AP 4; over budget 0.

Validator: `{"category": "invalid_reference", "action_index": 0, "field_path": null, "message": "Response failed static validation.", "rejected_value": null}`. Diagnostics: `[{"code": "los", "action_index": 0, "action": {"type": "attack", "unit_id": "blue-ranger", "target_id": "red-ranger"}, "message": "blocked line of sight", "actual_distance": 3, "allowed_range": 3, "los_required": true, "los_clear": false}]`.

Retained structured plan: `{"schema_version": "arena-turn-plan-schema-v2", "actions": [{"type": "attack", "unit_id": "blue-ranger", "target_id": "red-ranger"}, {"type": "shield_bash", "unit_id": "blue-knight", "target_id": "red-knight"}, {"type": "attack", "unit_id": "blue-mage", "target_id": "red-ranger"}, {"type": "attack", "unit_id": "blue-cleric", "target_id": "red-cleric"}, {"type": "end_turn"}]}`. A global AP/schema error may have no unique failing action index; all identifiable semantic actions remain shown here.

Payload present=True; receipt present=True; receipt status=returned; transport completed=True; response ID `resp_03e7dc8e7f0251f8016aa822f9afac87d09f6d80df50285fa4`; provider request ID `req_04e3fca9bbd349b0b39acb08e1805f69`. Structured response SHA-256 `e88e881b07c29d80b68f183400f885d32b46be2a952b974379732d15a6080215`.

Full initial and repair structured plans, detailed diagnostics, and earlier-batch cases are in [repair-forensics.json](repair-forensics.json). A field absent from sanitized evidence is unavailable, not evidence that the model omitted it.
