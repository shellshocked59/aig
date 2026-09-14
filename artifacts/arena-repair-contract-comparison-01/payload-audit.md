# Frozen repair payload audit

Six authentic episodes, three repetitions each. No inference performed.

## R1 — DOWNED-003-bounded wave 1

OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.
NEW: same instructions/observation/schema, plus shared repair instruction and the following context:

```json
{
  "context_version": "arena-candidate-repair-context-v2",
  "prompt_version": "arena-candidate-repair-prompt-v2",
  "observation_hash": "ed59cf4bdbbb13c1ff21d6b5e75155f471921bc001777cabee1e0943e8728e14",
  "rejected_output_sha256": "0326eda2a27ade27658b35c4585eff5d74c5dc81f3b2787670b72e6c76691e0c",
  "rejected_plan": {
    "schema_version": "arena-turn-plan-schema-v2",
    "actions": [
      {
        "type": "attack",
        "unit_id": "actor",
        "target_id": "enemy"
      }
    ]
  },
  "cardinality": "full_plan",
  "validation": {
    "category": "invalid_reference",
    "action_index": 0,
    "field_path": null,
    "message": "Response failed static validation.",
    "rejected_value": null
  },
  "diagnostics": [
    {
      "code": "range",
      "action_index": 0,
      "action": {
        "type": "attack",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "message": "target outside action range",
      "actual_distance": 2,
      "allowed_range": 1
    }
  ],
  "available_ap": 1,
  "legal_actions_location": "ArenaObservation.legal_actions",
  "omission": "Raw prose omitted; unknown references redacted; semantic actions retained when parseable.",
  "planned_ap": 1,
  "over_budget_by": 0,
  "action_costs": [
    {
      "action_index": 0,
      "action": {
        "type": "attack",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "ap_cost": 1
    }
  ],
  "first_action_in_current_catalog": false
}
```

Payload hashes: OLD `1ab51d3682e392f6c85c303493b262b65823cd3a622398f66009b58195304a82`; NEW `288f650e299caaacb2d53c6049c663fa9f723c974990fb96ef29fb3abadd1521`.

## R2 — POSITION-002-strict wave 0

OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.
NEW: same instructions/observation/schema, plus shared repair instruction and the following context:

```json
{
  "context_version": "arena-candidate-repair-context-v2",
  "prompt_version": "arena-candidate-repair-prompt-v2",
  "observation_hash": "24b0be07ef9b166c42428cf4a38fd13061b2bfb2a0c7b864ee02a2d1113f3b0c",
  "rejected_output_sha256": "d2c9f3e7dac5991bf0ff2b3d2c4d0740fff9fda47c3e1022defe9da0ac9ef6c6",
  "rejected_plan": {
    "schema_version": "arena-turn-plan-schema-v2",
    "actions": [
      {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "reserve"
      },
      {
        "type": "end_turn"
      }
    ]
  },
  "cardinality": "full_plan",
  "validation": {
    "category": "ap_budget",
    "action_index": null,
    "field_path": "actions",
    "message": "Selected actions exceed current AP.",
    "rejected_value": null
  },
  "diagnostics": [
    {
      "code": "ap_budget",
      "available_ap": 3,
      "planned_ap": 4,
      "over_budget_by": 1
    },
    {
      "code": "range",
      "action_index": 0,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "message": "target outside action range",
      "actual_distance": 5,
      "allowed_range": 4
    }
  ],
  "available_ap": 3,
  "legal_actions_location": "ArenaObservation.legal_actions",
  "omission": "Raw prose omitted; unknown references redacted; semantic actions retained when parseable.",
  "planned_ap": 4,
  "over_budget_by": 1,
  "action_costs": [
    {
      "action_index": 0,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "ap_cost": 2
    },
    {
      "action_index": 1,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "reserve"
      },
      "ap_cost": 2
    },
    {
      "action_index": 2,
      "action": {
        "type": "end_turn"
      },
      "ap_cost": 0
    }
  ],
  "first_action_in_current_catalog": false
}
```

Payload hashes: OLD `16322b052d2f134b5904ccbc433a7274cde29f23089eafc13a38dc58145f9219`; NEW `fedebf664a8c811453dd21d877dd57092d9cea1e26d201fbd21ca805121a1263`.

## R3 — POSITION-002-bounded wave 0

OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.
NEW: same instructions/observation/schema, plus shared repair instruction and the following context:

```json
{
  "context_version": "arena-candidate-repair-context-v2",
  "prompt_version": "arena-candidate-repair-prompt-v2",
  "observation_hash": "24b0be07ef9b166c42428cf4a38fd13061b2bfb2a0c7b864ee02a2d1113f3b0c",
  "rejected_output_sha256": "438b344e178d1890840029414974c5a444bdfc3ea0e27f0d2f7171d2948ceb2e",
  "rejected_plan": {
    "schema_version": "arena-turn-plan-schema-v2",
    "actions": [
      {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      {
        "type": "end_turn"
      }
    ]
  },
  "cardinality": "full_plan",
  "validation": {
    "category": "ap_budget",
    "action_index": null,
    "field_path": "actions",
    "message": "Selected actions exceed current AP.",
    "rejected_value": null
  },
  "diagnostics": [
    {
      "code": "ap_budget",
      "available_ap": 3,
      "planned_ap": 4,
      "over_budget_by": 1
    },
    {
      "code": "range",
      "action_index": 0,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "message": "target outside action range",
      "actual_distance": 5,
      "allowed_range": 4
    }
  ],
  "available_ap": 3,
  "legal_actions_location": "ArenaObservation.legal_actions",
  "omission": "Raw prose omitted; unknown references redacted; semantic actions retained when parseable.",
  "planned_ap": 4,
  "over_budget_by": 1,
  "action_costs": [
    {
      "action_index": 0,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "ap_cost": 2
    },
    {
      "action_index": 1,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "ap_cost": 2
    },
    {
      "action_index": 2,
      "action": {
        "type": "end_turn"
      },
      "ap_cost": 0
    }
  ],
  "first_action_in_current_catalog": false
}
```

Payload hashes: OLD `16322b052d2f134b5904ccbc433a7274cde29f23089eafc13a38dc58145f9219`; NEW `77071f1363fae5dcfa142c00e01026c08577e7d1a1d3d4a4070b88f17b1c9df3`.

## R4 — POSITION-002-stepwise wave 0

OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.
NEW: same instructions/observation/schema, plus shared repair instruction and the following context:

```json
{
  "context_version": "arena-candidate-repair-context-v2",
  "prompt_version": "arena-candidate-repair-prompt-v2",
  "observation_hash": "24b0be07ef9b166c42428cf4a38fd13061b2bfb2a0c7b864ee02a2d1113f3b0c",
  "rejected_output_sha256": "861471258b68452827fd53cbfd63c73ffc6a803d1aa2abd3827ee7e15026753a",
  "rejected_plan": {
    "schema_version": "arena-turn-plan-schema-v2",
    "actions": [
      {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      }
    ]
  },
  "cardinality": "at_most_one",
  "validation": {
    "category": "invalid_reference",
    "action_index": 0,
    "field_path": null,
    "message": "Response failed static validation.",
    "rejected_value": null
  },
  "diagnostics": [
    {
      "code": "range",
      "action_index": 0,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "message": "target outside action range",
      "actual_distance": 5,
      "allowed_range": 4
    }
  ],
  "available_ap": 3,
  "legal_actions_location": "ArenaObservation.legal_actions",
  "omission": "Raw prose omitted; unknown references redacted; semantic actions retained when parseable.",
  "planned_ap": 2,
  "over_budget_by": 0,
  "action_costs": [
    {
      "action_index": 0,
      "action": {
        "type": "snipe",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "ap_cost": 2
    }
  ],
  "first_action_in_current_catalog": false
}
```

Payload hashes: OLD `dce4d63abb4f125f9e1c14bffd2fdefcf86a6049f616618de22348ab84255952`; NEW `680b543116d6be73f2916d562bff012d8818e9503968c932da8f21c7bdbcdbd6`.

## R5 — FIREBALL-003-bounded wave 1

OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.
NEW: same instructions/observation/schema, plus shared repair instruction and the following context:

```json
{
  "context_version": "arena-candidate-repair-context-v2",
  "prompt_version": "arena-candidate-repair-prompt-v2",
  "observation_hash": "75471148d107042125fad27e8608e1b0684b3e6a0c49dd4cd9504a0a92f08088",
  "rejected_output_sha256": "0326eda2a27ade27658b35c4585eff5d74c5dc81f3b2787670b72e6c76691e0c",
  "rejected_plan": {
    "schema_version": "arena-turn-plan-schema-v2",
    "actions": [
      {
        "type": "attack",
        "unit_id": "actor",
        "target_id": "enemy"
      }
    ]
  },
  "cardinality": "full_plan",
  "validation": {
    "category": "invalid_reference",
    "action_index": 0,
    "field_path": null,
    "message": "Response failed static validation.",
    "rejected_value": null
  },
  "diagnostics": [
    {
      "code": "range",
      "action_index": 0,
      "action": {
        "type": "attack",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "message": "target outside action range",
      "actual_distance": 3,
      "allowed_range": 2
    }
  ],
  "available_ap": 1,
  "legal_actions_location": "ArenaObservation.legal_actions",
  "omission": "Raw prose omitted; unknown references redacted; semantic actions retained when parseable.",
  "planned_ap": 1,
  "over_budget_by": 0,
  "action_costs": [
    {
      "action_index": 0,
      "action": {
        "type": "attack",
        "unit_id": "actor",
        "target_id": "enemy"
      },
      "ap_cost": 1
    }
  ],
  "first_action_in_current_catalog": false
}
```

Payload hashes: OLD `88e358a8f986fab3bb960e7b21b815dfee39867d437c43cecb3abc598c78c608`; NEW `4fb22f2a6031255b6df6a5728404503d8eed7df207ddd4ae5ddc27da34d9e70d`.

## R6 — FIREBALL-003-stepwise wave 1

OLD: unchanged policy instructions, authoritative observation V4, category-only feedback, unchanged output schema.
NEW: same instructions/observation/schema, plus shared repair instruction and the following context:

```json
{
  "context_version": "arena-candidate-repair-context-v2",
  "prompt_version": "arena-candidate-repair-prompt-v2",
  "observation_hash": "75471148d107042125fad27e8608e1b0684b3e6a0c49dd4cd9504a0a92f08088",
  "rejected_output_sha256": "007d8bd3104555778b57124b7e73d18181fa5a509754ad4d0f5b71d68000182e",
  "rejected_plan": {
    "schema_version": "arena-turn-plan-schema-v2",
    "actions": [
      {
        "type": "attack",
        "unit_id": "ally",
        "target_id": "enemy"
      }
    ]
  },
  "cardinality": "at_most_one",
  "validation": {
    "category": "invalid_reference",
    "action_index": 0,
    "field_path": null,
    "message": "Response failed static validation.",
    "rejected_value": null
  },
  "diagnostics": [
    {
      "code": "range",
      "action_index": 0,
      "action": {
        "type": "attack",
        "unit_id": "ally",
        "target_id": "enemy"
      },
      "message": "target outside action range",
      "actual_distance": 2,
      "allowed_range": 1
    }
  ],
  "available_ap": 1,
  "legal_actions_location": "ArenaObservation.legal_actions",
  "omission": "Raw prose omitted; unknown references redacted; semantic actions retained when parseable.",
  "planned_ap": 1,
  "over_budget_by": 0,
  "action_costs": [
    {
      "action_index": 0,
      "action": {
        "type": "attack",
        "unit_id": "ally",
        "target_id": "enemy"
      },
      "ap_cost": 1
    }
  ],
  "first_action_in_current_catalog": false
}
```

Payload hashes: OLD `ceab7f1ec585063f7412d5bce8da2b49d9563c9e8be55312096d0051cabe332b`; NEW `8f043caf9b96e37d0ac66860d76af4662b3306eb68afd5679d106039882de21a`.

## Budget estimate

```json
{
  "method": "ceil(canonical payload characters / 4), including schema; estimate, not tokenizer measurement",
  "tokens_per_request": {
    "arena-candidate-repair-v1": 2326.5,
    "arena-candidate-repair-v2": 2835.6666666666665
  },
  "input_tokens_total": 92919,
  "input_token_delta_per_request": 509.1666666666665,
  "output_token_ceiling": 18432,
  "historical_output_tokens_mean": 44.166666666666664,
  "historical_seconds_mean": 1.3087867000043236,
  "expected_seconds": 47.11632120015565,
  "expected_total_tokens": 94509.0
}
```
