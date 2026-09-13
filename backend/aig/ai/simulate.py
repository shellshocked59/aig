"""Reproducible headless smoke run: python -m aig.ai.simulate --turns 100."""

import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json

from aig.ai.controller import AiOrchestrator
from aig.scenarios import human_vs_ai_demo_setup, scenario_setup
from aig.setup import create_game, start_game
from aig.snapshots import to_snapshot
from aig.state import ControllerType, _integer


def simulate(turns: int = 100, scenario_version=None) -> dict:
    _integer(turns, "turns", minimum=1)
    setup = human_vs_ai_demo_setup() if scenario_version is None else scenario_setup(scenario_version)
    setup = replace(setup, players=tuple(replace(p, controller=ControllerType.AI) for p in setup.players))
    state = create_game(setup)
    start_game(state)
    ai = AiOrchestrator()
    counts = Counter()
    trace = hashlib.sha256()
    for _ in range(turns * len(state.turn_order)):
        if state.turn >= turns:
            break
        result = ai.run_active_ai_activation(state)
        if result is None:
            break
        counts.update(type(c).__name__ for c in result.commands_executed)
        trace.update(json.dumps(result.to_dict(), sort_keys=True).encode())
        state.validate()
    snapshot = to_snapshot(state)
    return dict(turn=state.turn, activations=counts["EndActivation"],
                winner_player_id=state.result.winner_player_id if state.result else None,
                victory_type=state.result.victory_type.value if state.result else None,
                turn_cap_reached=state.result is None and state.turn >= turns,
                commands=dict(sorted(counts.items())), cities=len(state.cities),
                living_units=len(state.units), units_created=state.next_unit_id - 1,
                technologies={p.id: sorted(t.value for t in p.researched_technologies)
                              for p in sorted(state.players.values(), key=lambda p: p.id) if not state.is_barbarian(p.id)},
                snapshot_sha256=hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest(),
                trace_sha256=trace.hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=100)
    parser.add_argument("--scenario-version")
    args = parser.parse_args()
    print(json.dumps(simulate(args.turns, args.scenario_version), indent=2))
