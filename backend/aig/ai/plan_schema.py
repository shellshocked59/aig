"""Versioned wire representation of the existing six-field StrategicPlan."""

import json

from aig.ai.strategy import ExpansionPriority, Posture, StrategicPlan, StrategicState
from aig.state import Technology, UnitType

PLAN_SCHEMA_VERSION = "strategic-plan-schema-v1"


def plan_json_schema() -> dict:
    def enum(kind):
        return {"type": "string", "enum": [v.value for v in kind]}

    def priorities(kind):
        return {"type": "array", "items": enum(kind), "minItems": 1,
                "maxItems": len(kind), "uniqueItems": True}

    properties = {
        "posture": enum(Posture),
        "primary_enemy_id": {"type": ["string", "null"], "minLength": 1},
        "target_city_id": {"type": ["string", "null"], "minLength": 1},
        "expansion_priority": enum(ExpansionPriority),
        "production_priority": priorities(UnitType),
        "research_priority": priorities(Technology),
    }
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


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


def parse_plan(raw: str, state: StrategicState) -> StrategicPlan:
    """Validate wire types, all dataclass rules, and references before execution."""
    value = strict_json(raw)
    schema = plan_json_schema()
    if not isinstance(value, dict) or set(value) != set(schema["required"]):
        raise ValueError("Plan must contain exactly the six required schema properties")
    # The schema and parser share enum definitions; no coercion of wire types.
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
    if plan.primary_enemy_id is not None and (
            plan.primary_enemy_id == state["player_id"] or plan.primary_enemy_id not in enemies):
        raise ValueError("primary_enemy_id is not an enemy present in the strategic state")
    if plan.target_city_id is not None:
        city = next((c for c in state["enemy_cities"] if c["id"] == plan.target_city_id), None)
        if city is None:
            raise ValueError("target_city_id is not an enemy city present in the strategic state")
        if plan.primary_enemy_id is not None and city["owner_id"] != plan.primary_enemy_id:
            raise ValueError("target_city_id does not belong to primary_enemy_id")
    return plan
