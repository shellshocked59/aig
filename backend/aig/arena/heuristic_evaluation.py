"""Offline deterministic case studies; never constructs a model provider."""
import argparse
import json
from pathlib import Path
from time import perf_counter

from aig.arena.simulate import simulate
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.heuristic_v2 import HeuristicArenaTurnProviderV2
from aig.arena.ai.observation import build_observation
from aig.arena.ai.probes import PROBE_NAMES, create_probe
from aig.arena.commands import apply_command
from aig.arena.geometry import distance
from aig.arena.snapshots import from_snapshot, command_from_dict
from aig.arena.state import UnitStatus, Bonus
from aig.arena.scenarios import create_scenario
from aig.arena.gameplay import create_offline_turn_provider


def board_metrics(trace):
    state = from_snapshot(trace["initial_snapshot"])
    rows = {p.id: dict(premium_occupancy_actions=0, unique_premium_tiles=[],
                       turns_ending_on={b.value: 0 for b in Bonus}, premium_displacements=0,
                       movement_actions=0, movement_ap=0, attacks=0, core_attacks=0, core_damage=0,
                       first_combat_turn=None, first_core_damage_turn=None,
                       first_premium_turn=None, progression=[]) for p in state.players}
    turn = 1
    def ending(player):
        row = rows[player]
        units = [u for u in state.units.values() if u.owner_id == player and u.status is UnitStatus.ACTIVE]
        enemies = [u for u in state.units.values() if u.owner_id != player and u.status is UnitStatus.ACTIVE]
        core = next(c for c in state.cores.values() if c.owner_id != player)
        distances = [distance(u.position, core.position) for u in units]
        near = [min(distance(u.position, e.position) for e in enemies) for u in units] if enemies else []
        for bonus in Bonus:
            row["turns_ending_on"][bonus.value] += int(any(state.board.at(u.position).bonus is bonus for u in units))
        row["progression"].append(dict(player_turn=turn, core_mean=sum(distances)/len(distances) if distances else None,
                                        core_min=min(distances, default=None), enemy_mean=sum(near)/len(near) if near else None,
                                        enemy_min=min(near, default=None), center_units=sum(u.position.x == 4 for u in units),
                                        opponent_half_units=sum(u.position.x > 4 if core.position.x == 8 else u.position.x < 4 for u in units)))
    for entry in trace["entries"]:
        command = command_from_dict(entry["command"])
        player = command.actor_id
        row = rows[player]
        kind = entry["command"]["type"].removeprefix("arena_")
        if kind == "end_turn":
            ending(player)
        occupied = {u.id: u.position for u in state.units.values() if u.owner_id != player and state.board.at(u.position).bonus}
        core_attack = kind == "attack" and command.target_id in state.cores
        apply_command(state, command)
        row["movement_actions"] += int(kind == "move")
        row["movement_ap"] += entry["ap_used"] if kind == "move" else 0
        row["attacks"] += int(kind == "attack")
        row["core_attacks"] += int(core_attack)
        row["core_damage"] += entry["core_damage"]
        row["premium_displacements"] += sum(uid not in state.units or state.units[uid].position != pos for uid, pos in occupied.items())
        if kind != "end_turn":
            unit = state.units.get(getattr(command, "unit_id", None))
            if unit and state.board.at(unit.position).bonus:
                row["premium_occupancy_actions"] += 1
                coord = [unit.position.x, unit.position.y]
                if coord not in row["unique_premium_tiles"]:
                    row["unique_premium_tiles"].append(coord)
                if row["first_premium_turn"] is None:
                    row["first_premium_turn"] = turn
        for key, condition in (("first_combat_turn", entry["damage_dealt"] > 0), ("first_core_damage_turn", entry["core_damage"] > 0)):
            if condition and row[key] is None:
                row[key] = turn
        if state.winner_player_id:
            ending(player)
        if kind == "end_turn":
            turn += 1
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".local/arena-heuristic-v2"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {}
    for blue, red in (("v1", "v1"), ("v2", "v2"), ("v1", "v2"), ("v2", "v1")):
        report = simulate(blue_provider="heuristic-" + blue, red_provider="heuristic-" + red, max_turns=30,
                          provider_factory=create_offline_turn_provider)
        report["board_control"] = board_metrics(report["trace"])
        report["terminal_mechanism"] = ("core_destroyed" if any(c["hp"] == 0 for c in report["snapshot"]["cores"]) else "team_elimination") if report["winner"] else "turn_limit"
        key = blue + "-vs-" + red
        (args.output / (key + ".json")).write_text(json.dumps(report, indent=2) + "\n")
        summary[key] = {k: v for k, v in report.items() if k not in ("trace", "snapshot", "ai_traces")}
        print(key, report["winner"], report["player_turns"], flush=True)
    timing = {}
    for name, state in [("opening", create_scenario()), *[(n, create_probe(n)) for n in PROBE_NAMES]]:
        observation = build_observation(state)
        timing[name] = {}
        for version, provider in (("v1", HeuristicArenaTurnProvider()), ("v2", HeuristicArenaTurnProviderV2())):
            start = perf_counter()
            plan = provider.create_turn_plan(observation)
            timing[name][version] = dict(seconds=perf_counter() - start, plan=plan.to_dict())
            if version == "v2":
                (args.output / (name + "-scores.json")).write_text(json.dumps(provider.last_scores, indent=2) + "\n")
    summary["timing"] = timing
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
