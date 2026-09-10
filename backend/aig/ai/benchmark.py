"""Paired same-state strategy-provider experiments: python -m aig.ai.benchmark."""

import argparse
from contextlib import ExitStack
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from aig.ai.benchmark_metrics import RunMetrics, inference_metrics
from aig.ai.controller import AiOrchestrator
from aig.ai.executor import AiExecutor
from aig.ai.ollama import OllamaStrategyProvider, PROMPT_VERSION
from aig.ai.openai import OpenAIStrategyProvider, public_configuration
from aig.ai.plan_schema import PLAN_SCHEMA_VERSION, canonical_json
from aig.ai.strategy import HeuristicStrategyProvider, StrategyProviderError
from aig.scenarios import human_vs_ai_demo_setup
from aig.settings import Settings, load_settings
from aig.setup import create_game, start_game
from aig.snapshots import to_snapshot
from aig.state import ControllerType, _integer

BENCHMARK_VERSION = "benchmark-v1"


def canonical_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


class JsonlTrace:
    """Stream canonical UTF-8 rows; the hash includes one LF per record."""

    def __init__(self, path: Path):
        self.file = path.open("wb")
        self.hash = hashlib.sha256()

    def write(self, record):
        data = (canonical_json(record) + "\n").encode("utf-8")
        self.file.write(data)
        self.hash.update(data)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.file.close()


def initial_state():
    setup = human_vs_ai_demo_setup()
    setup = replace(setup, players=tuple(replace(p, controller=ControllerType.AI) for p in setup.players))
    state = create_game(setup)
    start_game(state)
    return state


def make_provider(name: str, settings: Settings):
    if name == "heuristic":
        return HeuristicStrategyProvider()
    if name == "ollama":
        return OllamaStrategyProvider(settings.ollama)
    if name == "openai":
        return OpenAIStrategyProvider(settings.openai)
    raise ValueError(f"unknown provider: {name}")


def run_trial(provider, *, provider_name: str, turns: int, settings: Settings, directory: Path) -> dict:
    """Fresh state/controllers for every trial; injected providers need no network."""
    _integer(turns, "turns", minimum=1)
    directory.mkdir(parents=True, exist_ok=False)
    state = initial_state()
    initial = to_snapshot(state)
    write_json(directory / "initial-state.json", initial)
    ai = AiOrchestrator(provider, replan_interval=settings.ai.replan_interval, max_actions=settings.ai.max_actions)
    inference = []
    replan_index = []
    started = perf_counter()
    with ExitStack() as stack:
        traces = {name: stack.enter_context(JsonlTrace(directory / f"{name}.jsonl"))
                  for name in ("plans", "commands", "inference", "activations")}
        metrics = RunMetrics(state, ai.controllers, traces["commands"])
        ai.executor = AiExecutor(settings.ai.max_actions, observer=metrics.observe)
        for activation in range(turns * len(state.turn_order)):
            metrics.activation = activation
            turn, actor = state.turn, state.active_player_id
            result = ai.run_active_ai_activation(state)
            if result is None:
                break
            controller = ai.controllers[actor]
            metrics.record_plan(actor, controller)
            traces["activations"].write(dict(activation=activation, turn=turn, player_id=actor,
                                             plan=result.plan.to_dict(), plan_reused=controller.summary["planReused"],
                                             plan_age_turns=controller.summary["planAgeTurns"],
                                             actual_provider=controller.summary["actualProvider"],
                                             fallback_used=controller.summary["fallbackUsed"],
                                             commands_executed=len(result.commands_executed)))
            trace = controller.last_trace
            if trace is not None:
                strategic_hash = canonical_hash(trace["strategic_state"])
                plan = dict(activation=activation, turn=turn, player_id=actor,
                            requested_provider=trace["requested_provider"], actual_provider=trace["actual_provider"],
                            previous_plan=trace["previous_plan"], new_plan=trace["resulting_plan"],
                            replan_reason=trace["replan_reason"], plan_age_turns=trace["plan_age_turns"],
                            strategic_state=trace["strategic_state"], strategic_state_sha256=strategic_hash,
                            fallback_used=trace["fallback_used"])
                traces["plans"].write(plan)
                replan_index.append(dict(player_id=actor, strategic_state_sha256=strategic_hash,
                                         plan_sha256=canonical_hash(plan["new_plan"])))
                # Whitelist telemetry: no messages, prompts, or hidden reasoning.
                record = {key: trace[key] for key in (
                    "requested_provider", "actual_provider", "model", "model_configuration", "prompt_version",
                    "schema_version", "provider_schema_version", "retry_count", "fallback_used",
                    "wall_clock_seconds", "error") if key in trace}
                record.update(activation=activation, turn=turn, player_id=actor, strategic_state_sha256=strategic_hash,
                              attempts=[{k: a[k] for k in ("raw_content", "metrics", "wall_clock_seconds", "error",
                                                           "error_category", "response_id", "request_id",
                                                           "model", "http_status") if k in a}
                                        for a in trace.get("attempts", [])])
                if provider_name in ("ollama", "openai") or record["attempts"] or trace["fallback_used"]:
                    traces["inference"].write(record)
                    inference.append(record)
            state.validate()
        total, players = metrics.finish(state)
    total["wall_clock_seconds"] = perf_counter() - started
    final = to_snapshot(state)
    write_json(directory / "final-state.json", final)
    llm = inference_metrics(inference, settings.ollama.context_size if provider_name == "ollama" else None)
    return dict(provider=provider_name, pureProviderRun=total["fallback_count"] == 0,
                fallbackCount=total["fallback_count"], metrics=total, players=players, inference=llm,
                hashes=dict(initial_state=canonical_hash(initial), final_state=canonical_hash(final),
                            commands=traces["commands"].hash.hexdigest(), plans=traces["plans"].hash.hexdigest()),
                traces={name: f"{name}.jsonl" for name in traces},
                snapshots=dict(initial="initial-state.json", final="final-state.json"),
                replan_index=replan_index)


def compare_runs(a: dict, b: dict) -> dict:
    """Raw B minus A deltas, with explicit provenance and matched inputs."""
    deltas = {key: b["metrics"][key] - value for key, value in a["metrics"].items()
              if type(value) in (int, float) and type(b["metrics"].get(key)) in (int, float)}
    deltas["inference_time_seconds"] = (b["inference"]["request_wall_clock_total_seconds"]
                                        - a["inference"]["request_wall_clock_total_seconds"])
    left = {(r["player_id"], r["strategic_state_sha256"]): r["plan_sha256"] for r in a["replan_index"]}
    right = {(r["player_id"], r["strategic_state_sha256"]): r["plan_sha256"] for r in b["replan_index"]}
    common = left.keys() & right.keys()
    return dict(deltaDirection="B minus A", initialStatesEqual=a["hashes"]["initial_state"] == b["hashes"]["initial_state"],
                pureProviderRuns=a["pureProviderRun"] and b["pureProviderRun"],
                fallbackCounts=dict(a=a["fallbackCount"], b=b["fallbackCount"]), deltas=deltas,
                playerDeltas={actor: {key: b["players"][actor][key] - value
                                      for key, value in player.items()
                                      if type(value) in (int, float)
                                      and type(b["players"][actor].get(key)) in (int, float)}
                              for actor, player in a["players"].items()},
                hashesEqual={key: a["hashes"][key] == b["hashes"][key] for key in a["hashes"]},
                equivalentStateReplans=dict(matched=len(common), identicalPlans=sum(left[k] == right[k] for k in common),
                                           differentPlans=sum(left[k] != right[k] for k in common)))


def benchmark(*, output: Path, games: int = 1, turns: int = 100, provider_a: str = "heuristic",
              provider_b: str = "heuristic", scenario: str = "human-vs-ai", settings: Settings | None = None,
              provider_factory=make_provider) -> dict:
    _integer(games, "games", minimum=1)
    _integer(turns, "turns", minimum=1)
    if scenario != "human-vs-ai":
        raise ValueError("only the fixed human-vs-ai scenario is supported")
    if any(p not in ("heuristic", "ollama", "openai") for p in (provider_a, provider_b)):
        raise ValueError("providers must be heuristic, ollama, or openai")
    settings = settings if settings is not None else load_settings()
    output = Path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("output must be a new or empty directory")
    output.mkdir(parents=True, exist_ok=True)
    initial = initial_state()
    report = dict(benchmarkVersion=BENCHMARK_VERSION, scenario=scenario,
                  configuration=dict(games=games, turns=turns, mode="paired-same-state-all-factions",
                                     providers=dict(a=provider_a, b=provider_b), ai=asdict(settings.ai),
                                     ollama=asdict(settings.ollama) if "ollama" in (provider_a, provider_b) else None,
                                     gameSeed=initial.config.seed, scenarioUsesRandomness=False,
                                     turnOrder=initial.turn_order, executionOrder="A then B per pair",
                                     promptVersion=PROMPT_VERSION, planSchemaVersion=PLAN_SCHEMA_VERSION),
                  runs=[], comparison=[])
    if "openai" in (provider_a, provider_b):
        report["configuration"]["openai"] = public_configuration(settings.openai)
    for pair in range(games):
        paired = []
        for slot, name in (("a", provider_a), ("b", provider_b)):
            run_id = f"pair-{pair + 1:04d}-{slot}-{name}"
            result = run_trial(provider_factory(name, settings), provider_name=name, turns=turns,
                               settings=settings, directory=output / "runs" / run_id)
            result.update(runId=run_id, pair=pair + 1, slot=slot, directory=f"runs/{run_id}")
            paired.append(result)
        comparison = compare_runs(*paired)
        if not comparison["initialStatesEqual"]:
            raise AssertionError("paired initial states differ")
        report["comparison"].append(dict(pair=pair + 1, runA=paired[0]["runId"], runB=paired[1]["runId"], **comparison))
        for result in paired:
            result.pop("replan_index")
            report["runs"].append(result)
    report["repeatability"] = {}
    for slot in ("a", "b"):
        runs = [r for r in report["runs"] if r["slot"] == slot]
        identical = {key: len({r["hashes"][key] for r in runs}) == 1 for key in runs[0]["hashes"]}
        report["repeatability"][slot] = dict(provider=runs[0]["provider"], trials=len(runs),
                                              measured=len(runs) > 1, hashesIdentical=identical if len(runs) > 1 else None,
                                              allPureProviderRuns=all(r["pureProviderRun"] for r in runs))
    write_json(output / "summary.json", report)
    return report


def terminal_summary(report: dict) -> str:
    lines = [f"Benchmark complete ({report['benchmarkVersion']}; deltas are B minus A)"]
    for run in report["runs"]:
        m, llm = run["metrics"], run["inference"]
        purity = "pure" if run["pureProviderRun"] else f"MIXED: {run['fallbackCount']} heuristic fallbacks"
        lines.append(f"{run['runId']} [{purity}]: turns {m['global_turns_completed']}, "
                     f"cities {m['final_city_count']} ({m['cities_founded']} founded), pop {m['total_population']}, "
                     f"military {m['final_military_strength']}, attacks {m['attacks_executed']}, kills {m['kills']}")
        lines.append(f"  plans {m['plans_created']}, reuses {m['plans_reused']}, "
                     f"requests {llm['requests']}, retries {llm['retries']}, fallbacks {llm['fallback_count']}")
        if llm["requests"]:
            timing = llm["timings"]["request_wall_clock_seconds"]["mean"]
            percent = llm["maximum_prompt_context_percent"]
            lines.append(f"  mean request {timing:.3f}s; max prompt {llm['maximum_prompt_tokens']} tokens; "
                         f"context {percent:.1f}%" if percent is not None else
                         f"  mean request {timing:.3f}s; prompt/context counts unavailable")
    for comparison in report["comparison"]:
        delta = comparison["deltas"]
        lines.append(f"Pair {comparison['pair']} delta: cities {delta['final_city_count']:+}, "
                     f"pop {delta['total_population']:+}, military {delta['final_military_strength']:+}, "
                     f"attacks {delta['attacks_executed']:+}, research {delta['research_completions']:+}")
    for slot, repeat in report["repeatability"].items():
        if repeat["measured"]:
            lines.append(f"Repeated {slot}/{repeat['provider']} hashes identical: {repeat['hashesIdentical']}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=1, help="number of pairs (each pair has two runs)")
    parser.add_argument("--turns", type=int, default=100, help="global turns per run")
    parser.add_argument("--provider-a", choices=("heuristic", "ollama", "openai"), default="heuristic")
    parser.add_argument("--provider-b", choices=("heuristic", "ollama", "openai"), default="heuristic",
                        help="select ollama or openai explicitly to opt into network inference")
    parser.add_argument("--scenario", choices=("human-vs-ai",), default="human-vs-ai")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results"))
    args = parser.parse_args(argv)
    try:
        report = benchmark(**vars(args))
    except (ValueError, StrategyProviderError) as error:
        parser.error(str(error))
    print(terminal_summary(report))
    print(f"Report: {args.output / 'summary.json'}")


if __name__ == "__main__":
    main()
