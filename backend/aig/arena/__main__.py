"""Inspect a scenario or apply/replay supplied commands; never chooses actions."""

import argparse
import json
from pathlib import Path

from aig.arena import ArenaSimulation, from_snapshot, replay, to_snapshot
from aig.arena.snapshots import command_from_dict
from aig.arena.public_state import public_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--snapshot", type=Path)
    source.add_argument("--replay", type=Path, help="arena-trace-v2 JSON file")
    parser.add_argument("--commands", type=Path, help="JSON array of arena-command-v2 commands")
    args = parser.parse_args()
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))
    simulation = (replay(read(args.replay)) if args.replay else
                  ArenaSimulation(from_snapshot(read(args.snapshot)) if args.snapshot else None))
    if args.commands:
        commands = read(args.commands)
        if type(commands) is not list:
            parser.error("commands must be a JSON array")
        for command in commands:
            simulation.execute(command_from_dict(command))
    print(json.dumps(dict(snapshot=to_snapshot(simulation.state), inspection=public_state(simulation.state), metrics=simulation.metrics(),
                          trace=simulation.trace()), indent=2))


if __name__ == "__main__":
    main()
