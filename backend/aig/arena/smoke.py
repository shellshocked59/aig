"""Explicit one-request Arena smoke helper; never invoked by application or CI."""

import argparse
import json

from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.observation import build_observation
from aig.arena.ai.probes import PROBE_NAMES, create_probe
from aig.arena.ai.validation import ArenaProviderError
from aig.settings import load_settings


def main(provider, argv=None):
    parser = argparse.ArgumentParser(description=f"One live {provider} Arena request; no repair or fallback.")
    parser.add_argument("--probe", choices=PROBE_NAMES, default="snipe_vs_basic")
    args = parser.parse_args(argv)
    try:
        engine = create_arena_turn_provider(load_settings(), provider, repair=False)
        plan = engine.create_turn_plan(build_observation(create_probe(args.probe)))
    except ArenaProviderError as error:
        print(json.dumps(dict(provider=provider, error_category=error.category)))
        return 1
    except ValueError:
        print(json.dumps(dict(provider=provider, error_category="configuration")))
        return 1
    print(json.dumps(dict(provider=provider, plan=plan.to_dict(), ap_total=plan.ap_cost,
                         inference={k: v for k, v in engine.last_trace.items() if k != "attempts"},
                         metrics=engine.last_trace["attempts"][0]["metrics"]), sort_keys=True))
    return 0
