"""Bounded provider-driven Arena play; defaults to offline heuristic vs heuristic."""

import argparse
import json
from pathlib import Path

from aig.arena.ai.controller import ArenaAiController
from aig.arena.ai.metrics import ai_metrics
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import digest, state_hash, to_snapshot
from aig.arena.state import SCENARIO_VERSION, integer
from aig.arena.ai.factory import PROVIDER_NAMES, create_arena_turn_provider
from aig.settings import Settings, load_settings


def simulate(*, max_turns=100, scenario=SCENARIO_VERSION, red_provider="heuristic", blue_provider="heuristic", settings=None, provider_factory=create_arena_turn_provider):
    """max_turns is completed global rounds; at most two player turns per round."""
    integer(max_turns, "max_turns", 1)
    if scenario != SCENARIO_VERSION:
        raise ValueError("unknown Arena scenario")
    simulation = ArenaSimulation()
    settings = settings if settings is not None else Settings()
    names = dict(red=red_provider, blue=blue_provider)
    controllers = {p: ArenaAiController(provider_factory(settings, name)) for p, name in names.items()}
    traces = []
    while simulation.state.winner_player_id is None and simulation.state.turn < max_turns:
        traces.append(controllers[simulation.state.active_player_id].run_turn(simulation))
    trace = simulation.trace()
    reproduced = replay(trace)
    snapshot = to_snapshot(simulation.state)
    exact = reproduced.trace() == trace and to_snapshot(reproduced.state) == snapshot
    if not exact:
        raise RuntimeError("Arena AI command replay mismatch")
    rows = [t.to_dict() for t in traces]
    return dict(environment="arena", scenario_version=scenario, max_turns=max_turns,
                controllers={p: name + "_ai" for p, name in names.items()},
                outcome="victory" if simulation.state.winner_player_id else "turn_limit",
                winner=simulation.state.winner_player_id, global_turns=simulation.state.turn,
                player_turns=len(rows), metrics=ai_metrics(simulation, traces), snapshot=snapshot,
                ai_traces=rows, trace=trace, replay_exact=exact,
                hashes=dict(plans=digest([t["plan"] for t in rows]),
                            commands=digest([e["command"] for e in trace["entries"]]),
                            ai_trace=digest(rows), command_trace=digest(trace), final_state=state_hash(simulation.state)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-turns", type=int, default=100, help="maximum completed global rounds (default 100)")
    parser.add_argument("--scenario", choices=[SCENARIO_VERSION], default=SCENARIO_VERSION)
    parser.add_argument("--red-provider", choices=PROVIDER_NAMES, default="heuristic")
    parser.add_argument("--blue-provider", choices=PROVIDER_NAMES, default="heuristic")
    parser.add_argument("--output", type=Path, help="write full plans, command trace, snapshot and metrics as JSON")
    args = parser.parse_args()
    if args.max_turns < 1:
        parser.error("--max-turns must be positive")
    report = simulate(max_turns=args.max_turns, scenario=args.scenario,
                      red_provider=args.red_provider, blue_provider=args.blue_provider,
                      settings=load_settings())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("snapshot", "ai_traces", "trace")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
