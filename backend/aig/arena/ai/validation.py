"""Static provider validation only; never simulate, reorder or correct tactics."""

from aig.ai.plan_schema import strict_json
from aig.arena.ai.contracts import ArenaTurnPlan, turn_plan_schema


class ArenaProviderError(Exception):
    def __init__(self, category):
        self.category = category
        super().__init__(f"Arena provider failed ({category}).")


def parse_turn_plan(raw, observation):
    try:
        data = strict_json(raw)
    except (ValueError, TypeError, RecursionError):
        raise ArenaProviderError("malformed_json") from None
    try:
        plan = ArenaTurnPlan.from_dict(data)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ArenaProviderError("schema_validation") from None
    facts = observation.to_dict()
    own = {u["id"]: u for u in facts["own_team"]["units"]}
    units = {u["id"]: u for team in ("own_team", "enemy_team") for u in facts[team]["units"]}
    cores = {facts[team]["core"]["id"] for team in ("own_team", "enemy_team")}
    board = {(t["x"], t["y"]) for t in facts["board"]["tiles"]}
    if plan.ap_cost > facts["action_points_remaining"]:
        raise ArenaProviderError("ap_budget")
    for action in plan.actions:
        if action.unit_id not in own:
            raise ArenaProviderError("invalid_reference")
        if action.type not in own[action.unit_id]["abilities"]:
            raise ArenaProviderError("invalid_ability")
        value = action.to_dict()
        if "target_id" in value:
            target = value["target_id"]
            if target not in units and target not in cores:
                raise ArenaProviderError("invalid_reference")
            if target in cores and action.type != "attack":
                raise ArenaProviderError("invalid_reference")
            if target == facts["own_team"]["core"]["id"]:
                raise ArenaProviderError("invalid_reference")
            if target in units:
                friendly = units[target]["owner_id"] == facts["active_player_id"]
                if friendly != (action.type in ("heal", "revive")):
                    raise ArenaProviderError("invalid_reference")
        else:
            p = value.get("destination", value.get("target_position"))
            if (p["x"], p["y"]) not in board:
                raise ArenaProviderError("invalid_reference")
    # Status, range, LOS and occupancy can change within the accepted sequence.
    return plan


def openai_turn_plan_schema():
    """Disjoint discriminator branches: oneOf -> anyOf; const -> typed enum.

    Remove schema metadata and string constraints for the provider wire subset.
    The unchanged v1 application parser still enforces every logical constraint.
    """
    def transform(value):
        if isinstance(value, list):
            return [transform(v) for v in value]
        if not isinstance(value, dict):
            return value
        result = {("anyOf" if k == "oneOf" else k): transform(v) for k, v in value.items()
                  if k not in ("$schema", "$id", "minLength", "pattern", "const")}
        if "const" in value:
            result.update(type="string", enum=[value["const"]])
        return result
    return transform(turn_plan_schema())
