"""Headless command runner and verified trace; no autonomous decisions."""

from copy import deepcopy

from aig.arena.commands import (ArenaAttack, ArenaEndTurn, ArenaHeal, ArenaRevive, ArenaFireball,
                                ArenaShieldBash, ArenaSnipe, arena_action_cost,
                                arena_fireball_affected_units, apply_command)
from aig.arena.state import UnitStatus
from aig.arena.scenarios import create_scenario
from aig.arena.snapshots import (canonical_json, command_from_dict, command_hash, command_to_dict, fields,
                                 from_snapshot, state_hash, to_snapshot)

TRACE_VERSION = "arena-trace-v2"
COUNTERS = ("damage_dealt", "healing_done", "ap_used", "ap_unused", "units_downed", "units_revived",
            "units_finished", "friendly_fire_damage", "core_damage", "bonus_tile_attacks",
            "shield_bash_pushes", "fireball_targets_hit")


def metrics(state):
    """Pure current-state measurements. Global turns count completed round wraps."""
    state.validate()
    return dict(turns_elapsed=state.turn, winner_player_id=state.winner_player_id,
                action_points_remaining=state.action_points_remaining,
                players={p.id: dict(living_units=sum(u.owner_id == p.id and u.status is UnitStatus.ACTIVE for u in state.units.values()),
                                   downed_units=sum(u.owner_id == p.id and u.status is UnitStatus.DOWNED for u in state.units.values()),
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
        before = deepcopy(self.state)
        encoded = command_to_dict(command)
        apply_command(self.state, command)
        losses = {uid: max(0, u.hp - self.state.units[uid].hp)
                  for uid, u in before.units.items() if uid in self.state.units}
        gains = sum(max(0, u.hp - before.units[uid].hp) for uid, u in self.state.units.items())
        core_damage = sum(c.hp - self.state.cores[uid].hp for uid, c in before.cores.items())
        offensive = type(command) in (ArenaAttack, ArenaShieldBash, ArenaSnipe, ArenaFireball)
        entry = dict(command=encoded, command_hash=command_hash(command), before_hash=before_hash,
                     after_hash=state_hash(self.state), ap_used=arena_action_cost(command),
                     ap_unused=ap if type(command) is ArenaEndTurn else 0,
                     damage_dealt=sum(losses.values()) + core_damage,
                     healing_done=gains if type(command) in (ArenaHeal, ArenaRevive) else 0,
                     units_downed=sum(u.status is UnitStatus.DOWNED and before.units[uid].status is UnitStatus.ACTIVE
                                      for uid, u in self.state.units.items()),
                     units_revived=sum(u.status is UnitStatus.ACTIVE and before.units[uid].status is UnitStatus.DOWNED
                                       for uid, u in self.state.units.items()),
                     units_finished=len(before.units) - len(self.state.units),
                     friendly_fire_damage=sum(loss for uid, loss in losses.items()
                                              if before.units[uid].owner_id == command.actor_id),
                     core_damage=core_damage,
                     bonus_tile_attacks=int(offensive and before.board.at(before.units[command.unit_id].position).bonus is not None),
                     shield_bash_pushes=int(type(command) is ArenaShieldBash and
                                           before.units[command.target_id].position != self.state.units[command.target_id].position),
                     fireball_targets_hit=len(arena_fireball_affected_units(before, command.target_position))
                                          if type(command) is ArenaFireball else 0)
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
                           for key in COUNTERS})
            values["ap_spent_by_action"] = {kind: sum(e["ap_used"] for e in entries if e["command"]["type"] == kind)
                                             for kind in sorted({e["command"]["type"] for e in entries})}
            values["attacks_made"] = sum(e["command"]["type"] == "arena_attack" for e in entries)
        return result


def replay(trace):
    """Reexecute on a fresh state and verify every command, state hash and metric."""
    fields(trace, "environment schema_version initial_snapshot entries")
    if trace["environment"] != "arena" or trace["schema_version"] != TRACE_VERSION or type(trace["entries"]) is not list:
        raise ValueError("unsupported Arena trace")
    simulation = ArenaSimulation(from_snapshot(trace["initial_snapshot"]))
    for index, expected in enumerate(trace["entries"]):
        fields(expected, "command command_hash before_hash after_hash " + " ".join(COUNTERS))
        actual = simulation.execute(command_from_dict(expected["command"]))
        if canonical_json(actual) != canonical_json(expected):
            raise ValueError(f"Arena replay mismatch at entry {index}")
    return simulation
