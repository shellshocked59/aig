"""Immutable canonical JSON facts; a lossless projection supports local simulation."""

from dataclasses import dataclass
import json
from types import MappingProxyType

from aig.arena.ai.contracts import action_from_dict
from aig.arena.commands import ACTION_COSTS
from aig.arena.public_state import public_state
from aig.arena.snapshots import canonical_json, digest, from_snapshot, SNAPSHOT_VERSION
from aig.versions import resolve_version

OBSERVATION_VERSION = "arena-observation-v1"
OBSERVATION_V2 = "arena-observation-v2"
OBSERVATION_V3 = "arena-observation-v3"
OBSERVATIONS = MappingProxyType({OBSERVATION_VERSION: "actor-grouped", OBSERVATION_V2: "action-explicit",
                               OBSERVATION_V3: "action-id"})


def resolve_observation_version(version=None):
    return resolve_version(version, available=OBSERVATIONS, latest=OBSERVATION_VERSION)


@dataclass(frozen=True)
class ArenaObservation:
    # Only text is retained: no mutable DTO, Position, ArenaState or Empire objects.
    canonical: str

    def __post_init__(self):
        data = json.loads(self.canonical)
        if self.canonical != canonical_json(data) or data.get("schema_version") not in OBSERVATIONS:
            raise ValueError("Arena observation requires canonical versioned JSON")

    def to_dict(self):
        return json.loads(self.canonical)

    @property
    def hash(self):
        return digest(self.to_dict())

    @property
    def version(self):
        return self.to_dict()["schema_version"]

    @classmethod
    def from_dict(cls, data):
        result = cls(canonical_json(data))
        # Recompute facts through the authoritative queries; reject forged metadata.
        if build_observation(simulation_state(result), version=result.version) != result:
            raise ValueError("inconsistent Arena observation facts")
        return result


def build_observation(state, *, version=OBSERVATION_VERSION):
    version = resolve_observation_version(version)
    if state.active_player_id is None:
        raise ValueError("observation requires a nonterminal turn")
    data = public_state(state)
    units, cores = data.pop("units"), data.pop("cores")
    data["schema_version"] = OBSERVATION_VERSION
    # Rule facts needed to compare actions; these are not recommendations/scores.
    data["action_rules"] = dict(shield_bash=dict(base_damage=4, push_tiles=1),
                                snipe=dict(base_damage=8),
                                fireball=dict(base_damage=4, radius=1, friendly_fire=True, damages_cores=False),
                                revive=dict(restored_hp=5), heal=dict(restored_hp=5))
    data["bonus_rules"] = dict(power_damage=2, ward_reduction=2, minimum_unit_damage=1, siege_core_damage=4)
    for key, own in (("own_team", True), ("enemy_team", False)):
        player = next(p for p in data["players"] if (p["id"] == state.active_player_id) == own)
        data[key] = dict(player_id=player["id"], core=next(c for c in cores if c["owner_id"] == player["id"]),
                         units=[u for u in units if u["owner_id"] == player["id"]])
    if version in (OBSERVATION_V2, OBSERVATION_V3):
        data = _compact_v2(data)
    if version == OBSERVATION_V3:
        data["schema_version"] = OBSERVATION_V3
        data["legal_actions"] = action_id_catalog(data["legal_actions"])
    return ArenaObservation(canonical_json(data))


def action_id_catalog(actions):
    """Wrap V2 order unchanged. Width expands with catalog size; no namespace cap."""
    width = max(2, len(str(len(actions))))
    return [dict(id=f"A{index:0{width}d}", action=action) for index, action in enumerate(actions, 1)]


def action_order(action):
    """Actor, discriminator, target ID, then destination/target y and x; no scores."""
    position = action.get("destination", action.get("target_position", {}))
    return (action["unit_id"], action["type"], action.get("target_id", ""),
            position.get("y", -1), position.get("x", -1))


def _compact_v2(data):
    data["schema_version"] = OBSERVATION_V2
    data["legal_actions_state"] = "turn_start"
    catalog, unit_types = [], {}
    for team in ("own_team", "enemy_team"):
        for unit in data[team]["units"]:
            stats, abilities = unit.pop("stats"), unit.pop("abilities")
            # Retain ranges for later-state reasoning, including unavailable abilities.
            unit_types[unit["unit_type"]] = dict(stats=stats, action_ranges={
                kind: value["range"] for kind, value in abilities.items()})
            for kind, targets in unit.pop("actions").items():
                key = "destination" if kind == "move" else "target_position" if kind == "fireball" else "target_id"
                for target in targets:
                    catalog.append(action_from_dict(dict(type=kind, unit_id=unit["id"], **{key: target})).to_dict())
    data["unit_types"] = unit_types
    data["legal_actions"] = sorted(catalog, key=action_order)
    board = data["board"]
    tiles = board.pop("tiles")
    board["default_tile"] = dict(terrain="floor", bonus=None)
    board["blocked_tiles"] = [dict(x=t["x"], y=t["y"]) for t in tiles if t["terrain"] == "blocked"]
    for bonus in ("power", "ward", "siege"):
        board[bonus] = [dict(x=t["x"], y=t["y"]) for t in tiles if t["bonus"] == bonus]
    return data


def observation_facts(observation):
    """Losslessly expand V2 for existing internal consumers; never sent to models."""
    data = observation.to_dict()
    if data["schema_version"] == OBSERVATION_V3:
        data["legal_actions"] = [entry["action"] for entry in data["legal_actions"]]
    if data["schema_version"] == OBSERVATION_VERSION:
        return data
    data["schema_version"] = OBSERVATION_VERSION
    data.pop("legal_actions_state")
    catalog, unit_types = data.pop("legal_actions"), data.pop("unit_types")
    for team in ("own_team", "enemy_team"):
        for unit in data[team]["units"]:
            metadata = unit_types[unit["unit_type"]]
            unit["stats"] = metadata["stats"]
            unit["abilities"] = {kind: dict(range=value, ap_cost=ACTION_COSTS[kind])
                                 for kind, value in metadata["action_ranges"].items()}
            unit["actions"] = {kind: [] for kind in ACTION_COSTS if kind != "end_turn"}
            for action in catalog:
                if action["unit_id"] == unit["id"]:
                    unit["actions"][action["type"]].append(action.get("destination",
                        action.get("target_position", action.get("target_id"))))
    board = data["board"]
    default = board.pop("default_tile")
    blocked = board.pop("blocked_tiles")
    bonuses = {bonus: board.pop(bonus) for bonus in ("power", "ward", "siege")}
    board["tiles"] = []
    for y in range(board["height"]):
        for x in range(board["width"]):
            position = dict(x=x, y=y)
            tile = dict(position, **default)
            if position in blocked:
                tile["terrain"] = "blocked"
            for bonus, positions in bonuses.items():
                if position in positions:
                    tile["bonus"] = bonus
            board["tiles"].append(tile)
    return data


def simulation_state(observation):
    """Build a NEW state from JSON facts, never a hidden reference to the live state."""
    data = observation_facts(observation)
    def entity(e, unit=False):
        result = {k: e[k] for k in ("id", "owner_id", "hp")}
        result["position"] = dict(x=e["x"], y=e["y"])
        if unit:
            result.update(unit_type=e["unit_type"], status=e["status"])
        return result
    return from_snapshot(dict(
        environment=data["environment"], schema_version=SNAPSHOT_VERSION,
        config={k: data[k] for k in ("rules_version", "scenario_version")},
        **{k: data[k] for k in ("turn", "active_player_id", "action_points_remaining", "winner_player_id", "players")},
        board=dict(width=data["board"]["width"], height=data["board"]["height"],
                   tiles=[{k: t[k] for k in ("terrain", "bonus")} for t in data["board"]["tiles"]]),
        units=[entity(u, True) for team in ("own_team", "enemy_team") for u in data[team]["units"]],
        cores=[entity(data[team]["core"]) for team in ("own_team", "enemy_team")]))
