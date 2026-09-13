"""Four identical heuristic matches and tactical probes; no model/network calls."""

import argparse
import json
from pathlib import Path

from aig.arena import ArenaSimulation, to_snapshot
from aig.arena.ai.controller import ArenaAiController
from aig.arena.ai.observation import build_observation
from aig.arena.ai.probes import PROBE_NAMES, PROBE_VERSION, create_probe
from aig.arena.ai.contracts import turn_plan_schema
from aig.arena.simulate import simulate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".local/arena-phase3-verification"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    def write(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    runs = []
    for index in range(4):
        report = simulate()
        write(f"match-{index + 1}.json", report)
        runs.append({k: report[k] for k in ("hashes", "outcome", "winner", "player_turns", "global_turns", "replay_exact")})
    if not all(run == runs[0] for run in runs):
        raise RuntimeError("identical fixed-scenario runs diverged")
    probes = {}
    for name in PROBE_NAMES:
        state = create_probe(name)
        sim = ArenaSimulation(state)
        trace = ArenaAiController().run_turn(sim).to_dict()
        if trace["invalid_action"] is not None:
            raise RuntimeError(f"illegal heuristic probe plan: {name}")
        probes[name] = dict(initial_snapshot=to_snapshot(state), observation=build_observation(state).to_dict(),
                            ai_trace=trace, trace=sim.trace())
    write("probes.json", dict(schema_version=PROBE_VERSION, probes=probes))
    write("arena-turn-plan-schema-v1.json", turn_plan_schema())
    summary = dict(identical_runs=4, runs=runs, probes={name: value["ai_trace"]["plan"] for name, value in probes.items()})
    write("verification.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
