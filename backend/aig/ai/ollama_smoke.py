"""Opt-in live planning smoke test: python -m aig.ai.ollama_smoke.

Use --turns 10 for a short heuristic-A vs Ollama-B simulation. Never run in CI.
"""

import argparse
from dataclasses import replace
import json

from aig.ai import AiOrchestrator, HeuristicStrategyProvider, OllamaStrategyProvider, StrategicStateBuilder, StrategyProviderError
from aig.scenarios import human_vs_ai_demo_setup
from aig.settings import load_settings
from aig.setup import create_game, start_game
from aig.state import ControllerType


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, help="run this many global turns instead of one planning call")
    args = parser.parse_args()
    if args.turns is not None and args.turns < 1:
        parser.error("--turns must be positive")
    settings = load_settings()
    provider = OllamaStrategyProvider(settings.ollama, prompt_version=settings.ai.strategy_prompt_version)
    setup = human_vs_ai_demo_setup()
    if args.turns is not None:
        setup = replace(setup, players=tuple(replace(p, controller=ControllerType.AI) for p in setup.players))
    state = create_game(setup)
    if args.turns is None:
        try:
            plan = provider.create_plan(StrategicStateBuilder().build(state, "B"))
        except StrategyProviderError as error:
            print(json.dumps(dict(error=str(error), model=settings.ollama.model,
                                  duration_seconds=provider.last_trace["wall_clock_seconds"],
                                  retry_count=provider.last_trace["retry_count"]), indent=2))
            return 1
        trace = provider.last_trace
        print(json.dumps(dict(model=settings.ollama.model, plan=plan.to_dict(),
                              duration_seconds=trace["wall_clock_seconds"], retry_count=trace["retry_count"],
                              attempts=[dict(metrics=a["metrics"], duration_seconds=a["wall_clock_seconds"])
                                        for a in trace["attempts"]]), indent=2))
        return 0

    start_game(state)
    orchestrators = {
        "A": AiOrchestrator(HeuristicStrategyProvider(), replan_interval=settings.ai.replan_interval,
                            max_actions=settings.ai.max_actions),
        "B": AiOrchestrator(provider, replan_interval=settings.ai.replan_interval,
                            max_actions=settings.ai.max_actions),
    }
    replans = reused = retries = fallbacks = requests = 0
    duration = 0.0
    while state.turn < args.turns and state.active_player_id is not None:
        actor = state.active_player_id
        ai = orchestrators[actor]
        ai.run_active_ai_activation(state)
        state.validate()
        if actor == "B":
            summary = ai.latest_summaries[0]
            if summary["planReused"]:
                reused += 1
            else:
                replans += 1
                retries += summary["retryCount"]
                fallbacks += int(summary["fallbackUsed"])
                trace = ai.controllers[actor].last_trace
                requests += len(trace["attempts"])
                duration += trace["wall_clock_seconds"]
    print(json.dumps(dict(model=settings.ollama.model, game_seed=state.config.seed, turn=state.turn,
                          ollama_replans=replans, reused_plans=reused, http_requests=requests,
                          retries=retries, fallbacks=fallbacks, game_valid=True,
                          average_request_seconds=duration / requests if requests else None,
                          average_planning_seconds=duration / replans if replans else None), indent=2))
    return 1 if fallbacks else 0


if __name__ == "__main__":
    raise SystemExit(main())
