"""Headless command runner and verified trace; no autonomous decisions."""

from copy import deepcopy

from aig.arena.v1.commands import ArenaAttack, ArenaEndTurn, ArenaHeal, apply_command
from aig.arena.v1.scenarios import create_scenario
from aig.arena.v1.snapshots import (canonical_json, command_from_dict, command_hash, command_to_dict, fields,
                                 from_snapshot, state_hash, to_snapshot)

TRACE_VERSION = "arena-trace-v1"


def metrics(state):
    """Pure current-state measurements. Global turns count completed round wraps."""
    state.validate()
    return dict(turns_elapsed=state.turn, winner_player_id=state.winner_player_id,
                action_points_remaining=state.action_points_remaining,
                players={p.id: dict(living_units=sum(u.owner_id == p.id for u in state.units.values()),
                                   total_hp=sum(u.hp for u in state.units.values() if u.owner_id == p.id),
                                   core_hp=next(c.hp for c in state.cores.values() if c.owner_id == p.id))
                         for p in state.players})


class ArenaSimulation:
    """Owns a detached initial state and records only successfully applied commands."""

    def __init__(self, state=None):
        self.initial_snapshot = to_snapshot(create_scenario() if state is None else state)
        self.state = from_snapshot(self.initial_snapshot)
        self._entries = []

    def execute(self, command):
        before_hash = state_hash(self.state)
        ap = self.state.action_points_remaining
        before_hp = sum(u.hp for u in self.state.units.values()) + sum(c.hp for c in self.state.cores.values())
        # Validate serialization before mutation too (reject foreign commands).
        encoded = command_to_dict(command)
        apply_command(self.state, command)
        after_hp = sum(u.hp for u in self.state.units.values()) + sum(c.hp for c in self.state.cores.values())
        entry = dict(command=encoded, command_hash=command_hash(command), before_hash=before_hash,
                     after_hash=state_hash(self.state), ap_used=0 if isinstance(command, ArenaEndTurn) else 1,
                     ap_unused=ap if isinstance(command, ArenaEndTurn) else 0,
                     damage_dealt=before_hp - after_hp if isinstance(command, ArenaAttack) else 0,
                     healing_done=after_hp - before_hp if isinstance(command, ArenaHeal) else 0)
        self._entries.append(entry)
        return deepcopy(entry)

    def trace(self):
        return deepcopy(dict(environment="arena", schema_version=TRACE_VERSION,
                             initial_snapshot=self.initial_snapshot, entries=self._entries))

    def metrics(self):
        result = metrics(self.state)
        for player, values in result["players"].items():
            entries = [e for e in self._entries if e["command"]["actor_id"] == player]
            values.update({key: sum(e[key] for e in entries)
                           for key in ("damage_dealt", "healing_done", "ap_used", "ap_unused")})
            values["attacks_made"] = sum(e["command"]["type"] == "arena_attack" for e in entries)
        return result


def replay(trace):
    """Reexecute on a fresh state and verify every command, state hash and metric."""
    fields(trace, "environment schema_version initial_snapshot entries")
    if trace["environment"] != "arena" or trace["schema_version"] != TRACE_VERSION or type(trace["entries"]) is not list:
        raise ValueError("unsupported Arena trace")
    simulation = ArenaSimulation(from_snapshot(trace["initial_snapshot"]))
    for index, expected in enumerate(trace["entries"]):
        fields(expected, "command command_hash before_hash after_hash ap_used ap_unused damage_dealt healing_done")
        actual = simulation.execute(command_from_dict(expected["command"]))
        if canonical_json(actual) != canonical_json(expected):
            raise ValueError(f"Arena replay mismatch at entry {index}")
    return simulation
