"""Stepwise full-match pilot with cumulative budgets and verified stopping states.

V3 orchestration only: the V2 probes and model decision contracts remain frozen.
"""

import argparse
import hashlib
import json
from pathlib import Path

from aig.ai.benchmark import write_json
from aig.arena.ai.repair import REPAIR_V1, REPAIR_VERSIONS, repair_version as resolve_repair_version
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import OBSERVATION_V2, build_observation
from aig.arena.ai.stepwise import (ArenaStepController, CONTROL_VERSION, STEP_PROMPT_VERSION,
                                  STEP_PROMPT, checked_step, create_arena_step_provider)
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_versions import ARTIFACT_HASHES, artifact, manifest, source_manifest
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import digest, from_snapshot, to_snapshot
from aig.arena.stepwise_benchmark import turn_metrics, verify_stepwise_trial
from aig.settings import DEFAULT_LOCAL_FILE, Settings, load_settings

VERSION = "arena-benchmark-v3"
HARD_STOPS = {"source_mutation", "provider_mismatch", "catalog_execution_defect",
              "replay_mismatch", "controller_safety_bound", "configuration_failure"}
SCHEDULE = (
    ("qwen-self", "ollama", "ollama"), ("qwen-self", "ollama", "ollama"),
    ("luna-self", "openai", "openai"), ("luna-self", "openai", "openai"),
    ("qwen-vs-heuristic", "ollama", "heuristic"), ("qwen-vs-heuristic", "heuristic", "ollama"),
    ("luna-vs-heuristic", "openai", "heuristic"), ("luna-vs-heuristic", "heuristic", "openai"),
)


class RequestBudget:
    def __init__(self, limit, guard=lambda: None):
        if type(limit) is not int or limit < 0:
            raise ValueError("request limit must be a nonnegative integer")
        self.limit, self.used, self.guard = limit, 0, guard

    def take(self):
        self.guard()
        if self.used >= self.limit:
            raise ArenaProviderError("request_ceiling")
        self.used += 1


def auxiliary_source_manifest():
    root = Path(__file__).resolve().parents[3]
    files = {}
    for folder in ("frontend", "scripts", "tests"):
        for path in (root/folder).rglob("*"):
            if any(p in ("node_modules", "dist", "__pycache__", ".vite") for p in path.parts):
                continue
            if path.is_file() and path.suffix in (".py", ".json", ".js", ".ts", ".css", ".html"):
                files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ("pyproject.toml", "uv.lock", "AGENTS.md"):
        path = root/name
        if path.exists():
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def frozen_guard(source, settings_hash, auxiliary=None):
    def check():
        if source_manifest()["sourceManifestHash"] != source["sourceManifestHash"]:
            raise ArenaProviderError("source_mutation")
        env = DEFAULT_LOCAL_FILE
        if (hashlib.sha256(env.read_bytes()).hexdigest() if env.exists() else None) != settings_hash:
            raise ArenaProviderError("source_mutation")
        if auxiliary is not None and auxiliary_source_manifest() != auxiliary:
            raise ArenaProviderError("source_mutation")
    return check


def verify_match(directory):
    """Verify full trace and all detached model/heuristic player-turn boundaries."""
    directory = Path(directory)
    try:
        read = lambda p: json.loads(p.read_text(encoding="utf-8"))
        saved = read(directory/"manifest.json")
        if saved["benchmarkVersion"] not in (VERSION, "arena-benchmark-v2") or (
                saved["controlVersion"], saved["promptVersion"], saved["observationVersion"]) != (
                CONTROL_VERSION, STEP_PROMPT_VERSION, OBSERVATION_V2):
            raise ValueError("version")
        trace = read(directory/"command-trace.json")
        final = read(directory/"final-snapshot.json")
        reproduced = replay(trace)
        if to_snapshot(reproduced.state) != final:
            raise ValueError("final state")
        cursor = trace["initial_snapshot"]
        entries = []
        for turn_dir in sorted((directory/"turns").iterdir()):
            part = read(turn_dir/"command-trace.json")
            turn = read(turn_dir/"turn.json")
            if part["initial_snapshot"] != cursor:
                raise ValueError("turn boundary")
            name = saved["assignments"][cursor["active_player_id"]]
            if name == "heuristic":
                sim = ArenaSimulation(from_snapshot(cursor))
                obs = build_observation(sim.state, version=OBSERVATION_V2)
                plan = HeuristicArenaTurnProvider().create_turn_plan(obs)
                result = execute_arena_turn(sim.state, plan, execute_command=sim.execute).to_dict()
                if result != turn["execution"] or plan.to_dict() != turn["plan"] or sim.trace() != part:
                    raise ValueError("heuristic policy")
            else:
                if not verify_stepwise_trial(turn_dir, full_match_turn=True)["success"]:
                    raise ValueError("step replay")
                for step in turn["steps"]:
                    if step["requested_provider"] != name or step["fallback_used"]:
                        raise ValueError("purity")
                    if step["success"] and step["actual_provider"] != name:
                        raise ValueError("provider")
            cursor = to_snapshot(replay(part).state)
            if cursor != read(turn_dir/"final-snapshot.json"):
                raise ValueError("turn final")
            entries.extend(part["entries"])
        if entries != trace["entries"] or cursor != final:
            raise ValueError("trace coverage")
        return dict(success=True, final_state_hash=digest(final), command_trace_hash=digest(trace))
    except Exception:
        return dict(success=False, error_category="replay_mismatch")


def run_match(directory, assignments, providers, experiment, *, turns=100, guard=lambda: None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory/"turns").mkdir()
    sim = ArenaSimulation()
    write_json(directory/"manifest.json", dict(experiment, assignments=assignments, maxGlobalTurns=turns))
    rows, failure = [], None
    while sim.state.winner_player_id is None and sim.state.turn < turns:
        try:
            guard()
        except ArenaProviderError as error:
            failure = error.category
            break
        name = assignments[sim.state.active_player_id]
        # Detached per-turn traces retain the unchanged V2 verification contract.
        part = ArenaSimulation(from_snapshot(to_snapshot(sim.state)))
        player = part.state.active_player_id
        if name == "heuristic":
            obs = build_observation(part.state, version=OBSERVATION_V2)
            plan = HeuristicArenaTurnProvider().create_turn_plan(obs)
            execution = execute_arena_turn(part.state, plan, execute_command=part.execute).to_dict()
            row = dict(provider=name, player_id=player, turn=sim.state.turn,
                       plan=plan.to_dict(), execution=execution)
        else:
            row = ArenaStepController(providers[name], name).run_turn(part)
            row["metrics"] = turn_metrics(row)
            failure = row["error_category"]
            if any(s["fallback_used"] or s["requested_provider"] != name or
                   s["actual_provider"] not in (None, name) or
                   (s["success"] and s["actual_provider"] != name) for s in row["steps"]):
                failure = "provider_mismatch"
        target = directory/"turns"/f"turn-{len(rows)+1:04d}"
        target.mkdir()
        turn_contract = dict(experiment)
        for filename, value in (("manifest", turn_contract), ("turn", row),
                                ("command-trace", part.trace()), ("final-snapshot", to_snapshot(part.state))):
            write_json(target/(filename+".json"), value)
        rows.append(row)
        # Replay checks command metrics, AP and state before advancing the match.
        from aig.arena.snapshots import command_from_dict
        for entry in part.trace()["entries"]:
            sim.execute(command_from_dict(entry["command"]))
        if to_snapshot(sim.state) != to_snapshot(part.state):
            failure = "replay_mismatch"
        write_json(directory/"command-trace.json", sim.trace())
        write_json(directory/"final-snapshot.json", to_snapshot(sim.state))
        verification = verify_match(directory)
        write_json(target/"verification.json", verification)
        if not verification["success"]:
            failure = "replay_mismatch"
        try:
            guard()
        except ArenaProviderError as error:
            failure = error.category
        if failure:
            break
    write_json(directory/"command-trace.json", sim.trace())
    write_json(directory/"final-snapshot.json", to_snapshot(sim.state))
    verification = verify_match(directory)
    if not verification["success"]:
        failure = "replay_mismatch"
    winner = sim.state.winner_player_id
    status = ("request_ceiling" if failure == "request_ceiling" else "failed") if failure else (
        "completed" if winner else "turn_limit")
    mechanism = failure or ("core_destruction" if any(c.hp == 0 for c in sim.state.cores.values())
                           else "team_elimination") if winner or failure else "turn_limit"
    result = dict(status=status, error_category=failure, winner=winner, terminal_mechanism=mechanism,
                  assignments=assignments, global_turns=sim.state.turn, player_turns=len(rows),
                  turns=rows, mechanical_metrics=sim.metrics(), verification=verification)
    write_json(directory/"verification.json", verification)
    write_json(directory/"result.json", result)
    return result


def pilot(output, *, settings=None, provider_factory=create_arena_step_provider, request_limit=400, repair_version=REPAIR_V1):
    if type(request_limit) is not int or not 0 <= request_limit <= 400:
        raise ValueError("pilot request limit must be between 0 and 400 per model")
    repair_version = resolve_repair_version(repair_version)
    settings = settings or Settings()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    source = source_manifest()
    env = DEFAULT_LOCAL_FILE
    env_hash = hashlib.sha256(env.read_bytes()).hexdigest() if env.exists() else None
    auxiliary = auxiliary_source_manifest()
    guard = frozen_guard(source, env_hash, auxiliary)
    spec = artifact(VERSION)
    experiment = manifest(["ollama", "openai", "heuristic"], settings, source, observation_version=OBSERVATION_V2)
    experiment.update(benchmarkVersion=VERSION, benchmarkSpecHash=ARTIFACT_HASHES[VERSION], controlMode="stepwise",
                      controlVersion=CONTROL_VERSION, promptVersion=STEP_PROMPT_VERSION,
                      promptHash=hashlib.sha256(STEP_PROMPT.encode()).hexdigest(),
                      baseRecipePromptVersion=STEP_PROMPT_VERSION, repairVersion=repair_version,
                      experimentOverrides={"repairVersion": repair_version} if repair_version != REPAIR_V1 else {})
    write_json(output/"source-before.json", source)
    write_json(output/"auxiliary-source-before.json", auxiliary)
    write_json(output/"settings-file-hash.json", dict(env_sha256=env_hash))
    write_json(output/"manifest.json", experiment)
    budgets = {n: RequestBudget(request_limit, guard) for n in ("ollama", "openai")}
    providers, disabled = {}, {}
    report = dict(status="complete", preflight=[], matches=[], requests={}, request_limit=request_limit)
    hard_stop = None
    counters = {}
    for group, blue, red in SCHEDULE:
        counters[group] = counters.get(group, 0)+1
        match_id = f"{group}/run-{counters[group]:03d}"
        model = blue if blue != "heuristic" else red
        if hard_stop or model in disabled:
            report["matches"].append(dict(match_id=match_id, status="not_started", reason=hard_stop or disabled[model]))
            continue
        try:
            guard()
            if model not in providers:
                profile = experiment["providers"][model]
                expected = "qwen-config-v1" if model == "ollama" else "luna-config-v1"
                if profile["modelConfigVersion"] != expected:
                    raise ArenaProviderError("configuration_failure")
                provider = provider_factory(settings, model, **({"repair_version": repair_version} if repair_version != REPAIR_V1 else {}))
                if (provider.name != model or provider.configuration() != profile["modelConfiguration"]
                        or provider.prompt_version != STEP_PROMPT_VERSION
                        or provider.schema_version != experiment["planSchemaVersion"]
                        or getattr(provider, "repair_version", REPAIR_V1) != repair_version):
                    raise ArenaProviderError("configuration_failure")
                provider.before_request = budgets[model].take
                providers[model] = provider
                _, check = checked_step(provider, model, build_observation(ArenaSimulation().state, version=OBSERVATION_V2), preflight=True)
                report["preflight"].append(check)
                if check["fallback_used"] or check["actual_provider"] not in (None, model):
                    raise ArenaProviderError("provider_mismatch")
                if not check["success"]:
                    raise ArenaProviderError(check["error_category"])
            if budgets[model].used >= request_limit:
                raise ArenaProviderError("request_ceiling")
            result = run_match(output/match_id, dict(blue=blue, red=red), providers, experiment,
                               turns=spec["default_turns"], guard=guard)
            report["matches"].append(dict(match_id=match_id, **result))
            if result["error_category"] in HARD_STOPS:
                hard_stop = result["error_category"]
            if result["error_category"] == "request_ceiling":
                disabled[model] = "request_ceiling"
        except ArenaProviderError as error:
            if error.category in HARD_STOPS:
                hard_stop = error.category
            else:
                disabled[model] = error.category
            report["matches"].append(dict(match_id=match_id, status="not_started", reason=error.category))
        report["requests"] = {n: b.used for n, b in budgets.items()}
        write_json(output/"summary.json", report)
    report.update(status="hard_stop" if hard_stop else "stopped" if disabled else "complete",
                  hard_stop=hard_stop, disabled=disabled, requests={n:b.used for n,b in budgets.items()})
    write_json(output/"source-after.json", source_manifest())
    write_json(output/"summary.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repair-version", choices=REPAIR_VERSIONS, default=REPAIR_V1)
    args = parser.parse_args(argv)
    report = pilot(args.output, settings=load_settings(), repair_version=args.repair_version)
    print(json.dumps(dict(status=report["status"], requests=report["requests"])))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
