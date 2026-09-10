"""Explicit live, single-request smoke test: python -m aig.ai.openai_smoke.

Never run automatically or in CI. No repair, orchestration, or fallback.
"""

import argparse
import json

from aig.ai.openai import OpenAIStrategyProvider
from aig.ai.strategy import StrategicStateBuilder, StrategyProviderError
from aig.scenarios import human_vs_ai_demo_setup
from aig.settings import load_settings
from aig.setup import create_game


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    provider = None
    result = dict(provider="openai", fallback_used=False)
    try:
        settings = load_settings()
        provider = OpenAIStrategyProvider(settings.openai, repair=False)
        state = StrategicStateBuilder().build(create_game(human_vs_ai_demo_setup()), "B")
        plan = provider.create_plan(state)
        result["plan"] = plan.to_dict()
    except (ValueError, StrategyProviderError) as error:
        result["error"] = str(error)
    trace = provider.last_trace if provider else None
    if trace:
        result.update(model=trace["model"], duration_seconds=trace["wall_clock_seconds"],
                      requests=len(trace["attempts"]),
                      usage=[a["metrics"] for a in trace["attempts"]])
    print(json.dumps(result, indent=2))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
