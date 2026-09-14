"""Static provider validation only; never simulate, reorder or correct tactics."""

from dataclasses import asdict, dataclass

from aig.ai.plan_schema import strict_json
from aig.arena.ai.contracts import ArenaTurnPlan, turn_plan_schema
from aig.arena.ai.observation import observation_facts


@dataclass(frozen=True)
class RepairValidationFailure:
    category: str
    action_index: int | None = None
    field_path: str | None = None
    message: str = "Response failed static validation."
    rejected_value: object = None

    def to_dict(self):
        return asdict(self)


class ArenaProviderError(Exception):
    def __init__(self, category, *, action_index=None, field_path=None,
                 message="Response failed static validation.", rejected_value=None):
        self.category = category
        self.diagnostic = RepairValidationFailure(category, action_index, field_path, message, rejected_value)
        super().__init__(f"Arena provider failed ({category}).")


def parse_turn_plan(raw, observation):
    try:
        data = strict_json(raw)
    except (ValueError, TypeError, RecursionError):
        raise ArenaProviderError("malformed_json", message="Response is not valid strict JSON.") from None
    try:
        plan = ArenaTurnPlan.from_dict(data)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise ArenaProviderError("schema_validation", message="Response does not satisfy ArenaTurnPlan schema.") from None
    facts = observation_facts(observation)
    own = {u["id"]: u for u in facts["own_team"]["units"]}
    units = {u["id"]: u for team in ("own_team", "enemy_team") for u in facts[team]["units"]}
    cores = {facts[team]["core"]["id"] for team in ("own_team", "enemy_team")}
    board = {(t["x"], t["y"]) for t in facts["board"]["tiles"]}
    if plan.ap_cost > facts["action_points_remaining"]:
        raise ArenaProviderError("ap_budget", field_path="actions", message="Selected actions exceed current AP.", rejected_value=plan.ap_cost)
    for index, action in enumerate(plan.actions):
        def failure(category, field, message, value):
            return ArenaProviderError(category, action_index=index, field_path=f"actions[{index}].{field}",
                                      message=message, rejected_value=value)
        if action.unit_id not in own:
            raise failure("invalid_reference", "unit_id", "Selected unit is not owned by the active player.", action.unit_id)
        if action.type not in own[action.unit_id]["abilities"]:
            raise failure("invalid_ability", "type", "Selected unit does not have this ability.", action.type)
        value = action.to_dict()
        if "target_id" in value:
            target = value["target_id"]
            if target not in units and target not in cores:
                raise failure("invalid_reference", "target_id", "Target ID does not reference a current unit or Core.", target)
            if target in cores and action.type != "attack":
                raise failure("invalid_reference", "target_id", "Only attack can target a Core.", target)
            if target == facts["own_team"]["core"]["id"]:
                raise failure("invalid_reference", "target_id", "Selected action cannot target the friendly Core.", target)
            if target in units:
                friendly = units[target]["owner_id"] == facts["active_player_id"]
                if friendly != (action.type in ("heal", "revive")):
                    raise failure("invalid_reference", "target_id", "Target ownership does not match the selected action type.", target)
        else:
            p = value.get("destination", value.get("target_position"))
            if (p["x"], p["y"]) not in board:
                raise failure("invalid_reference", "destination" if "destination" in value else "target_position", "Position is not a board tile.", p)
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
