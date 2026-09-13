"""Independent Arena wire contract; strict loading with no lifecycle effects."""

import hashlib
import json

from aig.state import Position
from aig.arena.v1.state import (ArenaConfig, ArenaCore, ArenaPlayer, ArenaState, ArenaUnit,
                             Board, Bonus, Terrain, Tile, UnitType)
from aig.arena.v1.commands import ArenaAttack, ArenaEndTurn, ArenaHeal, ArenaMove

SNAPSHOT_VERSION = "arena-snapshot-v1"
COMMAND_VERSION = "arena-command-v1"


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def fields(value, names):
    if type(value) is not dict or set(value) != set(names.split()):
        raise ValueError(f"expected fields: {names}")
    return value


def position_data(position):
    return dict(x=position.x, y=position.y)


def read_position(data):
    return Position(**fields(data, "x y"))


def to_snapshot(state):
    state.validate()
    def entity(e):
        return dict(id=e.id, owner_id=e.owner_id, position=position_data(e.position), hp=e.hp)
    return dict(
        environment="arena", schema_version=SNAPSHOT_VERSION,
        config=dict(rules_version=state.config.rules_version, scenario_version=state.config.scenario_version),
        turn=state.turn, active_player_id=state.active_player_id,
        action_points_remaining=state.action_points_remaining, winner_player_id=state.winner_player_id,
        players=[dict(id=p.id, name=p.name) for p in state.players],
        board=dict(width=state.board.width, height=state.board.height,
                   tiles=[dict(terrain=t.terrain.value, bonus=t.bonus.value if t.bonus else None)
                          for t in state.board.tiles]),
        units=[dict(**entity(u), unit_type=u.unit_type.value) for u in sorted(state.units.values(), key=lambda u: u.id)],
        cores=[entity(c) for c in sorted(state.cores.values(), key=lambda c: c.id)],
    )


def from_snapshot(data):
    fields(data, "environment schema_version config turn active_player_id action_points_remaining winner_player_id players board units cores")
    if data["environment"] != "arena" or data["schema_version"] != SNAPSHOT_VERSION:
        raise ValueError("unsupported Arena snapshot")
    config = ArenaConfig(**fields(data["config"], "rules_version scenario_version"))
    board = fields(data["board"], "width height tiles")
    for items in (board["tiles"], data["players"], data["units"], data["cores"]):
        if type(items) is not list:
            raise ValueError("snapshot collections must be arrays")
    tiles = []
    for item in board["tiles"]:
        fields(item, "terrain bonus")
        tiles.append(Tile(Terrain(item["terrain"]), Bonus(item["bonus"]) if item["bonus"] is not None else None))
    players = tuple(ArenaPlayer(**fields(p, "id name")) for p in data["players"])
    def entities(items, unit):
        result = {}
        for item in items:
            fields(item, "id owner_id position hp unit_type" if unit else "id owner_id position hp")
            from aig.arena.v1.state import identifier
            identifier(item["id"])
            if item["id"] in result:
                raise ValueError("duplicate entity ID")
            args = dict(id=item["id"], owner_id=item["owner_id"], position=read_position(item["position"]), hp=item["hp"])
            result[item["id"]] = ArenaUnit(**args, unit_type=UnitType(item["unit_type"])) if unit else ArenaCore(**args)
        return result
    return ArenaState(
        Board(tuple(tiles), board["width"], board["height"]), players,
        entities(data["units"], True), entities(data["cores"], False), data["active_player_id"],
        config, data["turn"], data["action_points_remaining"], data["winner_player_id"],
    )


def command_to_dict(command):
    kinds = {ArenaMove: "arena_move", ArenaAttack: "arena_attack", ArenaHeal: "arena_heal", ArenaEndTurn: "arena_end_turn"}
    if type(command) not in kinds:
        raise ValueError("unsupported Arena command")
    result = dict(schema_version=COMMAND_VERSION, type=kinds[type(command)], actor_id=command.actor_id)
    if isinstance(command, ArenaMove):
        result.update(unit_id=command.unit_id, destination=position_data(command.destination))
    elif isinstance(command, (ArenaAttack, ArenaHeal)):
        result.update(unit_id=command.unit_id, target_id=command.target_id)
    return result


def command_from_dict(data):
    if type(data) is not dict or data.get("schema_version") != COMMAND_VERSION:
        raise ValueError("unsupported Arena command schema")
    kind = data.get("type")
    base = "schema_version type actor_id"
    if kind == "arena_move":
        fields(data, base + " unit_id destination")
        return ArenaMove(data["actor_id"], data["unit_id"], read_position(data["destination"]))
    if kind in ("arena_attack", "arena_heal"):
        fields(data, base + " unit_id target_id")
        cls = ArenaAttack if kind == "arena_attack" else ArenaHeal
        return cls(data["actor_id"], data["unit_id"], data["target_id"])
    if kind == "arena_end_turn":
        fields(data, base)
        return ArenaEndTurn(data["actor_id"])
    raise ValueError("unsupported Arena command type")


def state_hash(state):
    return digest(to_snapshot(state))


def command_hash(command):
    return digest(command_to_dict(command))
