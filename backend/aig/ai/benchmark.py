"""Paired same-state strategy-provider experiments: python -m aig.ai.benchmark."""

import argparse
from contextlib import ExitStack
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from aig import commands as command_types
from aig.ai.benchmark_metrics import RunMetrics, inference_metrics
from aig.ai.controller import AiController, AiOrchestrator
from aig.ai.benchmark_preflight import CheckedProvider, ProviderPreflightResult, preflight
from aig.ai.executor import AiExecutor
from aig.ai.ollama import OllamaStrategyProvider
from aig.ai.openai import OpenAIStrategyProvider, public_configuration
from aig.ai.plan_schema import canonical_json
from aig.ai.strategy import HeuristicStrategyProvider, StrategicStateBuilder, StrategyProviderError
from aig.scenarios import scenario_setup
from aig.ai.experiments import experiment_manifest, source_provenance
from aig.ai.model_profiles import apply_model_profile, inference_configuration, public_ollama_configuration
from aig.ai.prompts import resolve_prompt
from aig.versions import LATEST_BENCHMARK_VERSION, RUNTIME_ENVIRONMENT_VERSION
from aig.settings import Settings, load_settings
from aig.setup import create_game, start_game
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import ControllerType, Position, Technology, UnitType, _integer

BENCHMARK_VERSION = LATEST_BENCHMARK_VERSION


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


def initial_state(scenario_version=None):
    setup = scenario_setup(scenario_version)
    setup = replace(setup, players=tuple(replace(p, controller=ControllerType.AI) for p in setup.players))
    state = create_game(setup)
    start_game(state)
    return state


def make_provider(name: str, settings: Settings, *, plan_schema_version=None):
    if name == "heuristic":
        return HeuristicStrategyProvider()
    if name == "ollama":
        return OllamaStrategyProvider(settings.ollama, prompt_version=settings.ai.strategy_prompt_version,
                                      plan_schema_version=plan_schema_version)
    if name == "openai":
        return OpenAIStrategyProvider(settings.openai, prompt_version=settings.ai.strategy_prompt_version,
                                      plan_schema_version=plan_schema_version)
    raise ValueError(f"unknown provider: {name}")


def verify_replay(initial, final, command_path):
    """Replay saved commands offline, including the prefix of an invalid trial."""
    state = from_snapshot(initial)
    with command_path.open(encoding="utf-8") as rows:
        for line in rows:
            payload = json.loads(line)["command"]
            kind = payload.pop("type")
            if kind == "MoveUnit":
                payload["destination"] = Position(**payload["destination"])
            if kind == "SetCityProduction" and payload["unit_type"] is not None:
                payload["unit_type"] = UnitType(payload["unit_type"])
            if kind == "SetResearch" and payload["technology"] is not None:
                payload["technology"] = Technology(payload["technology"])
            command_types.apply_command(state, getattr(command_types, kind)(**payload))
    state.validate()
    if to_snapshot(state) != final:
        raise AssertionError("command replay differs from saved final state")
    return dict(success=True, final_state_sha256=canonical_hash(final))


def run_trial(provider, *, provider_name: str, turns: int, settings: Settings, directory: Path,
              scenario_version=None, manifest=None, allow_provider_fallback=False) -> dict:
    """Fresh state/controllers for every trial; injected providers need no network."""
    _integer(turns, "turns", minimum=1)
    if manifest is None:
        effective = settings
        if provider_name in ("ollama", "openai") and hasattr(provider, "settings"):
            effective = replace(settings, **{provider_name: provider.settings})
        manifest = experiment_manifest(
            provider=provider_name, settings=effective, scenario_version=scenario_version,
            prompt_version=getattr(provider, "prompt_version", None),
            plan_schema_version=getattr(provider, "schema_version", None))
    if manifest["environmentVersion"] != RUNTIME_ENVIRONMENT_VERSION:
        raise ValueError("historical environment is provenance only; use its recorded source revision to run it")
    directory.mkdir(parents=True, exist_ok=False)
    state = initial_state(scenario_version)
    initial = to_snapshot(state)
    write_json(directory / "initial-state.json", initial)
    checked = CheckedProvider(provider, provider_name, manifest["strategicPlanSchemaVersion"])
    ai = AiOrchestrator(checked, replan_interval=settings.ai.replan_interval, max_actions=settings.ai.max_actions)
    inference = []
    replan_index = []
    invalid = False
    started = perf_counter()
    with ExitStack() as stack:
        traces = {name: stack.enter_context(JsonlTrace(directory / f"{name}.jsonl"))
                  for name in ("plans", "commands", "inference", "activations")}
        metrics = RunMetrics(state, ai.controllers, traces["commands"])
        ai.executor = AiExecutor(settings.ai.max_actions, observer=metrics.observe)
        for activation in range(turns * len(state.turn_order)):
            metrics.activation = activation
            turn, actor = state.turn, state.active_player_id
            if actor is None:
                break
            if state.turn >= initial["turn"] + turns:
                break
            if state.is_barbarian(actor):
                from aig.barbarians import BarbarianController
                result = BarbarianController().execute(state, observer=metrics.observe)
                traces["activations"].write(dict(activation=activation, turn=turn, player_id=actor,
                    system_phase=True, commands_executed=len(result.commands_executed)))
                state.validate()
                continue
            controller = ai.controllers.setdefault(actor, AiController(checked, settings.ai.replan_interval))
            plan_result = controller.plan_for(state, actor)
            metrics.barbarians.decision(state, actor, plan_result, controller.last_trace)
            contaminated = (controller.summary["fallbackUsed"]
                            or controller.summary["actualProvider"] != provider_name)
            invalid |= contaminated
            # Check before executor entry: no fallback command can contaminate strict metrics.
            result = (None if contaminated and not allow_provider_fallback
                      else ai.executor.execute(state, plan_result))
            metrics.record_plan(actor, controller)
            traces["activations"].write(dict(activation=activation, turn=turn, player_id=actor,
                                             plan=plan_result.to_dict(), plan_reused=controller.summary["planReused"],
                                             plan_age_turns=controller.summary["planAgeTurns"],
                                             actual_provider=controller.summary["actualProvider"],
                                             fallback_used=controller.summary["fallbackUsed"],
                                             commands_executed=len(result.commands_executed) if result else 0))
            trace = controller.last_trace
            if trace is not None:
                strategic_hash = canonical_hash(trace["strategic_state"])
                plan = dict(activation=activation, turn=turn, player_id=actor,
                            requested_provider=trace["requested_provider"], actual_provider=trace["actual_provider"],
                            previous_plan=trace["previous_plan"], new_plan=trace["resulting_plan"],
                            replan_reason=trace["replan_reason"], plan_age_turns=trace["plan_age_turns"],
                            strategic_state=trace["strategic_state"], strategic_state_sha256=strategic_hash,
                            fallback_used=trace["fallback_used"])
                if "invalidated_previous_plan" in trace:
                    plan["invalidated_previous_plan"] = trace["invalidated_previous_plan"]
                traces["plans"].write(plan)
                replan_index.append(dict(player_id=actor, strategic_state_sha256=strategic_hash,
                                         plan_sha256=canonical_hash(plan["new_plan"])))
                # Whitelist telemetry: no messages, prompts, or hidden reasoning.
                record = {key: trace[key] for key in (
                    "requested_provider", "actual_provider", "model", "model_configuration", "prompt_version",
                    "schema_version", "provider_schema_version", "retry_count", "fallback_used",
                    "wall_clock_seconds", "error", "error_category") if key in trace}
                record.update(activation=activation, turn=turn, player_id=actor, strategic_state_sha256=strategic_hash,
                              attempts=[{k: a[k] for k in ("raw_content", "metrics", "wall_clock_seconds", "error",
                                                           "error_category", "response_id", "request_id",
                                                           "model", "http_status") if k in a}
                                        for a in trace.get("attempts", [])])
                if provider_name in ("ollama", "openai") or record["attempts"] or trace["fallback_used"]:
                    traces["inference"].write(record)
                    inference.append(record)
            state.validate()
            if contaminated and not allow_provider_fallback:
                break
        total, players = metrics.finish(state)
        total["turnCapReached"] = state.result is None and state.turn >= initial["turn"] + turns
    total["wall_clock_seconds"] = perf_counter() - started
    final = to_snapshot(state)
    write_json(directory / "final-state.json", final)
    replay = verify_replay(initial, final, directory / "commands.jsonl")
    llm = inference_metrics(inference, settings.ollama.context_size if provider_name == "ollama" else None)
    return dict(experiment=manifest, replay=replay,
                provider=provider_name, pureProviderRun=not invalid, validModelTrial=not invalid,
                status="fallback_contaminated" if invalid else "completed",
                aborted=invalid and not allow_provider_fallback,
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
    return dict(environmentVersions=dict(a=a["experiment"]["environmentVersion"], b=b["experiment"]["environmentVersion"]),
                environmentChanged=a["experiment"]["environmentVersion"] != b["experiment"]["environmentVersion"],
                deltaDirection="B minus A", initialStatesEqual=a["hashes"]["initial_state"] == b["hashes"]["initial_state"],
                pureProviderRuns=a["pureProviderRun"] and b["pureProviderRun"],
                fallbackCounts=dict(a=a["fallbackCount"], b=b["fallbackCount"]), deltas=deltas,
                playerDeltas={actor: {key: b["players"][actor][key] - value
                                      for key, value in player.items()
                                      if type(value) in (int, float)
                                      and type(b["players"][actor].get(key)) in (int, float)}
                              for actor, player in a["players"].items() if actor in b['players']},
                playerRosterChanged=set(a['players']) != set(b['players']),
                hashesEqual={key: a["hashes"][key] == b["hashes"][key] for key in a["hashes"]},
                equivalentStateReplans=dict(matched=len(common), identicalPlans=sum(left[k] == right[k] for k in common),
                                           differentPlans=sum(left[k] != right[k] for k in common)))


def benchmark(*, output: Path, games: int = 1, turns: int = 100, provider_a: str = "heuristic",
              provider_b: str = "heuristic", scenario: str = "human-vs-ai", settings: Settings | None = None,
              provider_factory=make_provider, environment_version=None, scenario_version=None,
              prompt_version=None, plan_schema_version=None,
              qwen_config_version=None, luna_config_version=None, preflight_only=False,
              allow_provider_fallback=False) -> dict:
    _integer(games, "games", minimum=1)
    _integer(turns, "turns", minimum=1)
    if scenario != "human-vs-ai":
        raise ValueError("only the fixed human-vs-ai scenario is supported")
    if any(p not in ("heuristic", "ollama", "openai") for p in (provider_a, provider_b)):
        raise ValueError("providers must be heuristic, ollama, or openai")
    settings = settings if settings is not None else load_settings()
    prompt, _ = resolve_prompt(settings.ai.strategy_prompt_version if prompt_version is None else prompt_version)
    settings = replace(settings, ai=replace(settings.ai, strategy_prompt_version=prompt))
    # Omission preserves existing runtime tuning. Explicit selection pins the profile.
    for provider, selection in (("ollama", qwen_config_version), ("openai", luna_config_version)):
        if selection is not None:
            settings = apply_model_profile(settings, provider, selection)
    source = source_provenance()
    manifests = {name: experiment_manifest(
        provider=name, settings=settings, environment_version=environment_version,
        scenario_version=scenario_version, prompt_version=prompt,
        plan_schema_version=plan_schema_version,
        model_config_version=qwen_config_version if name == "ollama" else luna_config_version if name == "openai" else None,
        source=source) for name in (provider_a, provider_b)}
    if any(m["environmentVersion"] != RUNTIME_ENVIRONMENT_VERSION for m in manifests.values()):
        raise ValueError("historical environment is provenance only; use its recorded source revision to run it")
    output = Path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("output must be a new or empty directory")
    output.mkdir(parents=True, exist_ok=True)
    initial = initial_state(scenario_version)
    report = dict(benchmarkVersion=BENCHMARK_VERSION, scenario=scenario,
                  configuration=dict(games=games, turns=turns, mode="paired-same-state-all-factions",
                                     providers=dict(a=provider_a, b=provider_b), ai=asdict(settings.ai),
                                     ollama=public_ollama_configuration(settings.ollama)
                                     if "ollama" in (provider_a, provider_b) else None,
                                     gameSeed=initial.config.seed, scenarioUsesRandomness=False,
                                     turnOrder=initial.turn_order, executionOrder="A then B per pair",
                                     promptVersion=prompt, planSchemaVersion=manifests[provider_a]["strategicPlanSchemaVersion"]),
                  runs=[], comparison=[])
    if "openai" in (provider_a, provider_b):
        report["configuration"]["openai"] = public_configuration(settings.openai)
    report.update(status="preflighting", strictProviderMode=not allow_provider_fallback,
                  experiments=manifests, preflight=[], trialsStarted=0, validModelTrials=0,
                  invalidModelTrials=0, pureProviderRuns=0, repeatability={},
                  requestAccounting=dict(preflightRequests={}, trialProviderRequests={},
                                         repairRequests=dict(preflight={}, trials={}), fallbackPlans={}))

    def construct(name):
        provider = (make_provider(name, settings, plan_schema_version=plan_schema_version)
                    if provider_factory is make_provider else provider_factory(name, settings))
        for attribute, field in (("prompt_version", "strategyPromptVersion"),
                                 ("schema_version", "strategicPlanSchemaVersion")):
            if hasattr(provider, attribute) and getattr(provider, attribute) != manifests[name][field]:
                raise ValueError(f"injected provider {attribute} does not match experiment manifest")
        if name in ("ollama", "openai") and hasattr(provider, "settings"):
            effective = replace(settings, **{name: provider.settings})
            if inference_configuration(name, effective) != manifests[name]["modelConfiguration"]:
                raise ValueError("injected provider inference settings do not match experiment manifest")
        return provider

    providers = {}
    strategic = StrategicStateBuilder().build(initial, initial.active_player_id)
    for name in manifests:
        if name == "heuristic":
            continue
        try:
            providers[name] = construct(name)
        except StrategyProviderError:
            # Constructor errors (e.g. missing credentials) have no network attempts.
            check = asdict(ProviderPreflightResult(name, model=manifests[name]["model"],
                           error_category="configuration_failure",
                           sanitized_error="Provider configuration failed; check required credentials/settings."))
        else:
            check = preflight(providers[name], name, strategic, manifests[name])
        report["preflight"].append(check)
        report["requestAccounting"]["preflightRequests"][name] = check["requests"]
        report["requestAccounting"]["repairRequests"]["preflight"][name] = check["retry_count"]
        report["requestAccounting"]["trialProviderRequests"][name] = 0
        report["requestAccounting"]["fallbackPlans"][name] = 0
        report["requestAccounting"]["repairRequests"]["trials"][name] = 0
    if any(not check["success"] for check in report["preflight"]):
        report["status"] = "preflight_failed"
    elif preflight_only:
        report["status"] = "preflight_passed"
    else:
        report["status"] = "completed"
    if report["status"] != "completed":
        write_json(output / "summary.json", report)
        return report
    for pair in range(games):
        paired = []
        for slot, name in (("a", provider_a), ("b", provider_b)):
            run_id = f"pair-{pair + 1:04d}-{slot}-{name}"
            provider = construct(name)
            result = run_trial(provider, provider_name=name, turns=turns,
                               settings=settings, directory=output / "runs" / run_id,
                               scenario_version=scenario_version, manifest=manifests[name],
                               allow_provider_fallback=allow_provider_fallback)
            result.update(runId=run_id, pair=pair + 1, slot=slot, directory=f"runs/{run_id}")
            paired.append(result)
            report["runs"].append(result)
            report["trialsStarted"] += 1
            report["validModelTrials"] += int(result["validModelTrial"])
            report["invalidModelTrials"] += int(not result["validModelTrial"])
            report["pureProviderRuns"] += int(result["pureProviderRun"])
            accounting = report["requestAccounting"]
            accounting["trialProviderRequests"][name] = accounting["trialProviderRequests"].get(name, 0) + result["inference"]["requests"]
            accounting["repairRequests"]["trials"][name] = accounting["repairRequests"]["trials"].get(name, 0) + result["inference"]["retries"]
            accounting["fallbackPlans"][name] = accounting["fallbackPlans"].get(name, 0) + result["fallbackCount"]
            if not result["validModelTrial"]:
                report["status"] = "fallback_contaminated" if allow_provider_fallback else "trial_failed"
                if not allow_provider_fallback:
                    for run in report["runs"]:
                        run.pop("replan_index", None)
                    write_json(output / "summary.json", report)
                    return report
        comparison = compare_runs(*paired)
        if not comparison["initialStatesEqual"]:
            raise AssertionError("paired initial states differ")
        report["comparison"].append(dict(pair=pair + 1, runA=paired[0]["runId"], runB=paired[1]["runId"], **comparison))
        for result in paired:
            result.pop("replan_index")
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
    lines = [f"Benchmark {report.get('status', 'completed')} ({report['benchmarkVersion']}; deltas are B minus A)"]
    for check in report.get("preflight", []):
        lines.append(f"Preflight {check['requested_provider']}: {'PASS' if check['success'] else 'FAIL'}; "
                     f"model {check['model']}; latency {check['duration_seconds']:.3f}s; "
                     f"requests {check['requests']}; usage {check['usage']}; "
                     f"diagnostics {check['sanitized_error'] or 'none'}")
    lines.append(f"Trials started: {report.get('trialsStarted', len(report['runs']))}; "
                 f"validModelTrials: {report.get('validModelTrials', 0)}; "
                 f"invalidModelTrials: {report.get('invalidModelTrials', 0)}; "
                 f"pureProviderRuns: {report.get('pureProviderRuns', 0)}")
    if "requestAccounting" in report:
        lines.append(f"Request accounting: {report['requestAccounting']}")
    for run in report["runs"]:
        if "experiment" in run:
            experiment = run["experiment"]
            lines.append(f"Experiment ({run['runId']}):")
            for label, field in (("Environment", "environmentVersion"), ("Scenario", "scenarioVersion"),
                                 ("Prompt", "strategyPromptVersion"), ("Plan schema", "strategicPlanSchemaVersion"),
                                 ("Provider", "provider"), ("Model config", "modelConfigVersion"),
                                 ("Model", "model"), ("Benchmark", "benchmarkVersion")):
                value = experiment[field]
                if field == "modelConfigVersion" and value is None:
                    value = "custom" if experiment["model"] else "not applicable"
                lines.append(f"  {label}: {value}")
            dirty = experiment["sourceDirty"]
            status = "dirty" if dirty else "clean" if dirty is False else "unknown"
            lines.append(f"  Revision: {experiment['sourceRevision'] or 'unknown'} ({status})")
        m, llm = run["metrics"], run["inference"]
        if "winnerPlayerId" in m:
            lines.append(f"  Conquest: winner {m['winnerPlayerId']}; turn {m['victoryTurn']}; "
                         f"activation {m['victoryActivation']}; turn cap {m['turnCapReached']}; "
                         f"captures {len(m['city_capture_events'])}; "
                         f"eliminations {len(m['civilization_eliminations'])}")
        purity = "pure" if run["pureProviderRun"] else f"fallback-contaminated: {run['fallbackCount']} heuristic fallbacks"
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
    for flag in ("environment-version", "scenario-version", "prompt-version", "plan-schema-version"):
        parser.add_argument(f"--{flag}", help="artifact version: latest (default), v1, or qualified ID")
    for flag in ("qwen-config-version", "luna-config-version"):
        parser.add_argument(f"--{flag}", help="pin frozen inference profile; omission retains runtime tuning")
    parser.add_argument("--preflight-only", action="store_true", help="one request per live provider; no trials")
    parser.add_argument("--allow-provider-fallback", action="store_true", help="continue contaminated trials after successful preflight")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results"))
    args = parser.parse_args(argv)
    try:
        report = benchmark(**vars(args))
    except (ValueError, StrategyProviderError) as error:
        parser.error(str(error))
    print(terminal_summary(report))
    print(f"Report: {args.output / 'summary.json'}")
    return 0 if report["status"] in ("completed", "preflight_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
