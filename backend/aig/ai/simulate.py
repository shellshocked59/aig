"""Reproducible headless smoke run: python -m aig.ai.simulate --turns 100."""

import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json

from aig.ai.controller import AiOrchestrator
from aig.scenarios import human_vs_ai_demo_setup
from aig.setup import create_game, start_game
from aig.snapshots import to_snapshot
from aig.state import ControllerType, _integer


def simulate(turns: int = 100) -> dict:
    _integer(turns, "turns", minimum=1)
    setup = human_vs_ai_demo_setup()
    setup = replace(setup, players=tuple(replace(p, controller=ControllerType.AI) for p in setup.players))
    state = create_game(setup)
    start_game(state)
    ai = AiOrchestrator()
    counts = Counter()
    trace = hashlib.sha256()
    for _ in range(turns * len(setup.players)):
        result = ai.run_active_ai_activation(state)
        if result is None:
            break
        counts.update(type(c).__name__ for c in result.commands_executed)
        trace.update(json.dumps(result.to_dict(), sort_keys=True).encode())
        state.validate()
    snapshot = to_snapshot(state)
    return dict(turn=state.turn, activations=counts["EndActivation"],
                commands=dict(sorted(counts.items())), cities=len(state.cities),
                living_units=len(state.units), units_created=state.next_unit_id - 1,
                technologies={p.id: sorted(t.value for t in p.researched_technologies)
                              for p in sorted(state.players.values(), key=lambda p: p.id)},
                snapshot_sha256=hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest(),
                trace_sha256=trace.hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(simulate(args.turns), indent=2))
