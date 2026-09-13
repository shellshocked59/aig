"""Strict, immutable tactical actions and a local discriminated JSON schema."""

from dataclasses import dataclass
from typing import ClassVar

from aig.arena.commands import ACTION_COSTS
from aig.arena.snapshots import COMMAND_VERSION, command_from_dict, fields
from aig.arena.state import TURN_AP, identifier, integer

PLAN_SCHEMA_VERSION = "arena-turn-plan-schema-v1"


@dataclass(frozen=True)
class ArenaPosition:
    x: int
    y: int

    def __post_init__(self):
        integer(self.x, "x", 0, 8)
        integer(self.y, "y", 0, 4)

    def to_dict(self):
        return dict(x=self.x, y=self.y)


@dataclass(frozen=True)
class MoveAction:
    unit_id: str
    destination: ArenaPosition
    type: ClassVar[str] = "move"

    def __post_init__(self):
        identifier(self.unit_id, "unit_id")
        if type(self.destination) is not ArenaPosition:
            raise ValueError("destination requires ArenaPosition")

    def to_dict(self):
        return dict(type=self.type, unit_id=self.unit_id, destination=self.destination.to_dict())


@dataclass(frozen=True)
class FireballAction:
    unit_id: str
    target_position: ArenaPosition
    type: ClassVar[str] = "fireball"

    def __post_init__(self):
        identifier(self.unit_id, "unit_id")
        if type(self.target_position) is not ArenaPosition:
            raise ValueError("target_position requires ArenaPosition")

    def to_dict(self):
        return dict(type=self.type, unit_id=self.unit_id, target_position=self.target_position.to_dict())


@dataclass(frozen=True)
class AttackAction:
    unit_id: str
    target_id: str
    type: ClassVar[str] = "attack"

    def __post_init__(self):
        identifier(self.unit_id, "unit_id")
        identifier(self.target_id, "target_id")

    def to_dict(self):
        return dict(type=self.type, unit_id=self.unit_id, target_id=self.target_id)


@dataclass(frozen=True)
class HealAction(AttackAction):
    type: ClassVar[str] = "heal"


@dataclass(frozen=True)
class FinishAction(AttackAction):
    type: ClassVar[str] = "finish"


@dataclass(frozen=True)
class ReviveAction(AttackAction):
    type: ClassVar[str] = "revive"


@dataclass(frozen=True)
class ShieldBashAction(AttackAction):
    type: ClassVar[str] = "shield_bash"


@dataclass(frozen=True)
class SnipeAction(AttackAction):
    type: ClassVar[str] = "snipe"


ArenaPlannedAction = MoveAction | AttackAction | HealAction | FinishAction | ReviveAction | ShieldBashAction | SnipeAction | FireballAction
ACTION_TYPES = {cls.type: cls for cls in (MoveAction, AttackAction, HealAction, FinishAction,
                                         ReviveAction, ShieldBashAction, SnipeAction, FireballAction)}


def action_from_dict(data):
    if type(data) is not dict or not isinstance(data.get("type"), str) or data["type"] not in ACTION_TYPES:
        raise ValueError("unknown Arena planned action discriminator")
    kind = data["type"]
    key = "destination" if kind == "move" else "target_position" if kind == "fireball" else "target_id"
    fields(data, "type unit_id " + key)
    target = ArenaPosition(**fields(data[key], "x y")) if kind in ("move", "fireball") else data[key]
    return ACTION_TYPES[kind](data["unit_id"], target)


def action_command(action, player_id):
    data = action.to_dict()
    return command_from_dict(dict(data, type="arena_" + action.type,
                                  schema_version=COMMAND_VERSION, actor_id=player_id))


@dataclass(frozen=True)
class ArenaTurnPlan:
    actions: tuple[ArenaPlannedAction, ...] = ()
    schema_version: str = PLAN_SCHEMA_VERSION

    def __post_init__(self):
        if self.schema_version != PLAN_SCHEMA_VERSION:
            raise ValueError("unsupported Arena turn plan schema")
        if type(self.actions) is not tuple or len(self.actions) > TURN_AP:
            raise ValueError("Arena plan requires a tuple of at most five actions")
        if any(type(a) not in ACTION_TYPES.values() for a in self.actions):
            raise ValueError("unknown Arena planned action")
        if self.ap_cost > TURN_AP:
            raise ValueError("Arena plan exceeds five AP")

    @property
    def ap_cost(self):
        return sum(ACTION_COSTS[a.type] for a in self.actions)

    def to_dict(self):
        return dict(schema_version=self.schema_version, actions=[a.to_dict() for a in self.actions])

    @classmethod
    def from_dict(cls, data):
        fields(data, "schema_version actions")
        if type(data["actions"]) is not list:
            raise ValueError("actions must be an array")
        return cls(tuple(action_from_dict(a) for a in data["actions"]), data["schema_version"])


def turn_plan_schema():
    """Fresh JSON Schema. Sum of AP costs is additionally checked by ArenaTurnPlan."""
    identity = dict(type="string", minLength=1, pattern=r"\S")
    position = dict(type="object", additionalProperties=False, required=["x", "y"],
                    properties=dict(x=dict(type="integer", minimum=0, maximum=8),
                                    y=dict(type="integer", minimum=0, maximum=4)))
    variants = []
    for kind in ACTION_TYPES:
        key = "destination" if kind == "move" else "target_position" if kind == "fireball" else "target_id"
        variants.append(dict(type="object", additionalProperties=False, required=["type", "unit_id", key],
                             properties={"type": {"const": kind}, "unit_id": identity,
                                         key: position if kind in ("move", "fireball") else identity}))
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": PLAN_SCHEMA_VERSION,
            "type": "object", "additionalProperties": False, "required": ["schema_version", "actions"],
            "properties": {"schema_version": {"const": PLAN_SCHEMA_VERSION},
                           "actions": {"type": "array", "maxItems": 5, "items": {"oneOf": variants}}}}
