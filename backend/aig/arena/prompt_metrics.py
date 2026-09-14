"""Passive starting-observation membership, independent of execution legality."""

from aig.arena.ai.contracts import action_from_dict
from aig.arena.ai.observation import OBSERVATION_V2
from aig.arena.snapshots import canonical_json


def is_starting_legal_action(observation, planned_action):
    """Exact actor/type/target membership; never dynamic validation or correction."""
    try:
        data = planned_action if isinstance(planned_action, dict) else planned_action.to_dict()
        action = action_from_dict(data)
    except (ValueError, TypeError, KeyError, AttributeError):
        return False
    facts = observation.to_dict()
    if observation.version == OBSERVATION_V2:
        return canonical_json(data) in {canonical_json(a) for a in facts["legal_actions"]}
    units = {unit["id"]: unit for unit in facts["own_team"]["units"]}
    target = data.get("destination", data.get("target_position", data.get("target_id")))
    return target in units.get(action.unit_id, {}).get("actions", {}).get(action.type, [])


def starting_legality(observation, plan):
    membership = [is_starting_legal_action(observation, action) for action in plan.actions]
    prefix = next((i for i, legal in enumerate(membership) if not legal), len(membership))
    return dict(first_action_starting_legal=membership[0] if membership else None,
                starting_legal_prefix_length=prefix, starting_action_membership=membership)
