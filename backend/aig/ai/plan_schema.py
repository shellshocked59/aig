"""Versioned wire representation of the existing six-field StrategicPlan."""

import json

from aig.ai.strategy import ExpansionPriority, Posture, StrategicPlan, StrategicState
from aig.state import Technology, UnitType
from types import MappingProxyType
from aig.versions import LATEST_PLAN_SCHEMA_VERSION, resolve_version

PLAN_SCHEMA_VERSION = LATEST_PLAN_SCHEMA_VERSION
# Serialized immutable contract: enum additions must not silently rewrite V1.
PLAN_SCHEMA_V1 = r'''
{
  "type": "object",
  "properties": {
    "posture": {
      "type": "string",
      "enum": [
        "expand",
        "defend",
        "attack"
      ]
    },
    "primary_enemy_id": {
      "type": [
        "string",
        "null"
      ],
      "minLength": 1
    },
    "target_city_id": {
      "type": [
        "string",
        "null"
      ],
      "minLength": 1
    },
    "expansion_priority": {
      "type": "string",
      "enum": [
        "high",
        "low"
      ]
    },
    "production_priority": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "settler",
          "scout",
          "warrior",
          "archer",
          "spearman"
        ]
      },
      "minItems": 1,
      "maxItems": 5,
      "uniqueItems": true
    },
    "research_priority": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "agriculture",
          "archery",
          "bronze_working"
        ]
      },
      "minItems": 1,
      "maxItems": 3,
      "uniqueItems": true
    }
  },
  "required": [
    "posture",
    "primary_enemy_id",
    "target_city_id",
    "expansion_priority",
    "production_priority",
    "research_priority"
  ],
  "additionalProperties": false
}
'''
PLAN_SCHEMAS = MappingProxyType({"strategic-plan-schema-v1": PLAN_SCHEMA_V1})


class PlanValidationError(ValueError):
    """Diagnostic category only; the accepted plan contract is unchanged."""

    def __init__(self, message: str, category: str = "schema_validation"):
        super().__init__(message)
        self.category = category


def plan_json_schema(version=None) -> dict:
    selected = resolve_version(version, available=PLAN_SCHEMAS, latest=LATEST_PLAN_SCHEMA_VERSION)
    return json.loads(PLAN_SCHEMAS[selected])


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def strict_json(raw: str) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("JSON contains duplicate properties")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("JSON contains a non-finite number")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except json.JSONDecodeError as error:
        raise ValueError("Response is not valid JSON") from error


def parse_plan(raw: str, state: StrategicState, schema_version=None) -> StrategicPlan:
    """Validate wire types, all dataclass rules, and references before execution."""
    try:
        value = strict_json(raw)
    except (ValueError, RecursionError) as error:
        reason = str(error) if isinstance(error, ValueError) else "JSON nesting is too deep"
        raise PlanValidationError(reason, "malformed_json_content") from error
    schema = plan_json_schema(schema_version)
    if not isinstance(value, dict) or set(value) != set(schema["required"]):
        raise ValueError("Plan must contain exactly the six required schema properties")
    # Validate against the selected frozen contract; no coercion of wire types.
    for field, rule in schema["properties"].items():
        item = value[field]
        if rule["type"] == "array":
            if (not isinstance(item, list) or not item
                    or any(type(v) is not str or v not in rule["items"]["enum"] for v in item)
                    or len(set(item)) != len(item)):
                raise ValueError(f"{field} must be a nonempty array of unique allowed enum strings")
        elif isinstance(rule["type"], list):
            if item is not None and (type(item) is not str or not item.strip()):
                raise ValueError(f"{field} must be a nonblank string or null")
        elif type(item) is not str or item not in rule["enum"]:
            raise ValueError(f"{field} must be one of {', '.join(rule['enum'])}")
    plan = StrategicPlan(
        posture=Posture(value["posture"]), primary_enemy_id=value["primary_enemy_id"],
        target_city_id=value["target_city_id"], expansion_priority=ExpansionPriority(value["expansion_priority"]),
        production_priority=tuple(UnitType(v) for v in value["production_priority"]),
        research_priority=tuple(Technology(v) for v in value["research_priority"]),
    )
    enemies = {item["owner_id"] for item in [*state["enemy_cities"], *state["enemy_units"]]}
    enemies.update(c["id"] for c in state.get("civilizations", [])
                   if c["id"] != state["player_id"] and not c["eliminated"])
    enemies.difference_update(c['id'] for c in state.get('civilizations', []) if c['eliminated'])
    if plan.primary_enemy_id is not None and (
            plan.primary_enemy_id == state["player_id"] or plan.primary_enemy_id not in enemies):
        raise PlanValidationError("primary_enemy_id is not an enemy present in the strategic state",
                                  "invalid_strategic_references")
    if plan.target_city_id is not None:
        city = next((c for c in state["enemy_cities"] if c["id"] == plan.target_city_id), None)
        if city is None or city.get("live_exists") is False or city['owner_id'] not in enemies:
            raise PlanValidationError("target_city_id is not an enemy city present in the strategic state",
                                      "invalid_strategic_references")
        if plan.primary_enemy_id is not None and city["owner_id"] != plan.primary_enemy_id:
            raise PlanValidationError("target_city_id does not belong to primary_enemy_id",
                                      "invalid_strategic_references")
    return plan
