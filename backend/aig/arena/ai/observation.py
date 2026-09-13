"""Immutable canonical JSON facts; a lossless projection supports local simulation."""

from dataclasses import dataclass
import json

from aig.arena.public_state import public_state
from aig.arena.snapshots import canonical_json, digest, from_snapshot, SNAPSHOT_VERSION

OBSERVATION_VERSION = "arena-observation-v1"


@dataclass(frozen=True)
class ArenaObservation:
    # Only text is retained: no mutable DTO, Position, ArenaState or Empire objects.
    canonical: str

    def __post_init__(self):
        data = json.loads(self.canonical)
        if self.canonical != canonical_json(data) or data.get("schema_version") != OBSERVATION_VERSION:
            raise ValueError("Arena observation requires canonical v1 JSON")

    def to_dict(self):
        return json.loads(self.canonical)

    @property
    def hash(self):
        return digest(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        result = cls(canonical_json(data))
        # Recompute facts through the authoritative queries; reject forged metadata.
        if build_observation(simulation_state(result)) != result:
            raise ValueError("inconsistent Arena observation facts")
        return result


def build_observation(state):
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
    return ArenaObservation(canonical_json(data))


def simulation_state(observation):
    """Build a NEW state from JSON facts, never a hidden reference to the live state."""
    data = observation.to_dict()
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
