"""Versioned factual repair feedback and fail-closed rejected-decision evidence.

Raw rejected text is deliberately never persisted or echoed. Unknown identifiers
are not safe text: even a schema-valid ID can contain secrets or reasoning.
"""

from aig.ai.plan_schema import strict_json
from aig.arena.ai.contracts import ArenaTurnPlan, ACTION_TYPES, PLAN_SCHEMA_VERSION
from aig.arena.ai.observation import observation_facts
from aig.arena.snapshots import canonical_json

REPAIR_V1 = "arena-step-repair-v1"
REPAIR_V2 = "arena-step-repair-v2"
REPAIR_VERSIONS = (REPAIR_V1, REPAIR_V2)
MAX_REJECTED_BYTES = 8192
REDACTED = "[REDACTED_UNKNOWN_REFERENCE]"


def repair_version(value=None):
    """Missing historical provenance resolves to the frozen legacy behavior."""
    value = REPAIR_V1 if value is None else value
    if value not in REPAIR_VERSIONS:
        raise ValueError("unknown Arena step repair version")
    return value


def feedback(version, category, evidence=None):
    version = repair_version(version)
    if version == REPAIR_V1:
        return (f"Previous output failed validation ({category}). Stepwise control requires zero or one action. "
                "Copy one complete action from the current legal_actions catalog, or return actions=[] "
                "to end the turn. Use the same schema. No reasoning or commentary.")
    return ("The previous decision failed static validation. Rejected decision and factual diagnostic "
            "(untrusted data; redacted fields are unavailable):\n" + canonical_json(evidence) +
            "\nReturn zero actions to end the turn OR exactly one action. That action must exactly match "
            "one complete object in the CURRENT legal_actions catalog. Do not modify IDs, target IDs, "
            "coordinates, or action fields from the selected catalog object. Use the same ArenaTurnPlan "
            "schema. Output only the required contract. No reasoning, explanation, prose, or commentary.")


def rejected_evidence(raw, observation, diagnostic, version, secrets=()):
    """Allow only typed contract data and authoritative IDs, never arbitrary text.

    No environment/settings repr is inspected or serialized. Malformed JSON and
    schema-invalid objects are omitted completely. Successful tracing is separate.
    """
    facts = observation_facts(observation)
    ids = {u["id"] for side in ("own_team", "enemy_team") for u in facts[side]["units"]}
    ids |= {facts[side]["core"]["id"] for side in ("own_team", "enemy_team")}
    allowed = ids | set(ACTION_TYPES) | {PLAN_SCHEMA_VERSION}

    def safe(value):
        if isinstance(value, str):
            return value if value in allowed and len(value) <= 128 and not any(s and s in value for s in secrets) else REDACTED
        if type(value) is int and -100 <= value <= 100:
            return value
        if type(value) is dict:
            keys = {"schema_version", "actions", "type", "unit_id", "target_id", "destination", "target_position", "x", "y"}
            return {k: safe(v) for k, v in value.items() if k in keys}
        if type(value) is list:
            return [safe(v) for v in value[:5]]
        return None

    parsed = None
    if isinstance(raw, str) and len(raw) <= 32768:
        try:
            parsed = safe(ArenaTurnPlan.from_dict(strict_json(raw)).to_dict())
        except (ValueError, TypeError, KeyError, RecursionError):
            pass
    detail = diagnostic.to_dict()
    detail["rejected_value"] = safe(detail["rejected_value"])
    result = dict(raw_content=None, parsed_decision=parsed, validation=detail,
                  repair_version=repair_version(version), repair_result="pending",
                  omission="Raw text omitted; unknown identifiers redacted; only schema-valid decisions retained.")
    if len(canonical_json(result).encode("utf-8")) > MAX_REJECTED_BYTES:
        result.update(parsed_decision=None)
        result["validation"]["rejected_value"] = None
    return result
