"""Benchmark v2 probe runner. No fallback, implicit retries, or full matches."""

import hashlib
import json
from math import isfinite
from pathlib import Path

from aig.ai.benchmark import write_json
from aig.arena.ai.repair import REPAIR_V1, repair_version as resolve_repair_version
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.observation import OBSERVATION_V2, build_observation
from aig.arena.ai.stepwise import (CONTROL_VERSION, STEP_PROMPT_VERSION, STEP_PROMPT,
    ArenaStepController, checked_step, create_arena_step_provider, parse_step)
from aig.arena.benchmark_metrics import distribution, inference_metrics
from aig.arena.benchmark_versions import artifact, ARTIFACT_HASHES, frozen_probe, manifest, probe_set, source_manifest
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, digest, to_snapshot, command_from_dict, state_hash
from aig.arena.state import integer
from aig.settings import Settings

BENCHMARK_VERSION = "arena-benchmark-v2"


def validate_pricing(pricing, model):
    if pricing is None:
        return None
    required = {"model", "as_of", "source", "input_usd_per_million", "cached_input_usd_per_million", "output_usd_per_million"}
    if set(pricing) != required or pricing["model"] != model:
        raise ValueError("pricing requires matching model, as_of, source and three USD/million rates")
    from datetime import date
    date.fromisoformat(pricing["as_of"])
    if not isinstance(pricing["source"], str) or not pricing["source"].strip():
        raise ValueError("pricing source required")
    for key in required - {"model", "as_of", "source"}:
        v = pricing[key]
        if type(v) not in (int, float) or not isfinite(v) or v < 0:
            raise ValueError("pricing rates must be finite nonnegative numbers")
    return dict(pricing)


def decision_usage(row, pricing=None):
    attempts = row["attempts"]
    def total(key):
        values = [a["metrics"].get(key) for a in attempts]
        return sum(values) if values and all(v is not None for v in values) else None
    local = row["requested_provider"] == "ollama"
    tokens = dict(input_tokens=total("prompt_eval_count" if local else "input_tokens"),
                  output_tokens=total("eval_count" if local else "output_tokens"),
                  cached_input_tokens=total("cached_input_tokens"))
    i, o, c = tokens["input_tokens"], tokens["output_tokens"], tokens["cached_input_tokens"]
    tokens["uncached_input_tokens"] = i-c if i is not None and c is not None and c <= i else None
    tokens["estimated_cost_usd"] = ((i-c)*pricing["input_usd_per_million"] + c*pricing["cached_input_usd_per_million"]
        + o*pricing["output_usd_per_million"]) / 1e6 if pricing and row["requested_provider"] == "openai" and i is not None and o is not None and c is not None and c <= i else None
    return tokens


def turn_metrics(turn, pricing=None):
    steps = turn["steps"]
    for step in steps:
        step["usage"] = decision_usage(step, pricing)
    def total(key):
        values = [s["usage"][key] for s in steps]
        return sum(values) if values and all(v is not None for v in values) else None
    ap = turn["ap_executed"]
    return dict(provider_calls_per_turn=len(steps), provider_requests_per_turn=turn["provider_requests"],
                provider_calls_per_ap=len(steps)/ap if ap else None,
                provider_requests_per_ap=turn["provider_requests"]/ap if ap else None,
                repairs_per_turn=turn["repair_requests"],
                selected_current_legal_rate=sum(s["selected_current_legal"] is True for s in steps)/sum(s["selected_action"] is not None for s in steps)
                    if any(s["selected_action"] is not None for s in steps) else None,
                total_provider_latency_seconds=turn["provider_latency_seconds"],
                **{k: total(k) for k in ("input_tokens", "output_tokens", "cached_input_tokens", "uncached_input_tokens", "estimated_cost_usd")})


def verify_stepwise_trial(directory, *, full_match_turn=False):
    """Recreate commands without providers, then check detached decision boundaries."""
    try:
        def read(name):
            return json.loads((Path(directory)/name).read_text(encoding="utf-8"))
        saved = read("manifest.json")
        resolve_repair_version(saved.get("repairVersion"))
        expected_benchmarks = (BENCHMARK_VERSION, "arena-benchmark-v3") if full_match_turn else (BENCHMARK_VERSION,)
        if saved["benchmarkVersion"] not in expected_benchmarks or (
                saved["controlVersion"], saved["observationVersion"], saved["promptVersion"]) != (
                CONTROL_VERSION, OBSERVATION_V2, STEP_PROMPT_VERSION):
            raise ValueError("version mismatch")
        trace, final, turn = read("command-trace.json"), read("final-snapshot.json"), read("turn.json")
        reproduced = replay(trace)
        if to_snapshot(reproduced.state) != final:
            raise ValueError("final snapshot mismatch")
        from aig.arena.snapshots import from_snapshot
        sim = ArenaSimulation(from_snapshot(trace["initial_snapshot"]))
        entries = trace["entries"]
        index, actions = 0, []
        for step_index, row in enumerate(turn["steps"]):
            obs = build_observation(sim.state, version=OBSERVATION_V2)
            if (row["step_index"] != step_index or obs.hash != row["observation_hash"] or obs.to_dict() != row["observation"]
                    or row["ap_before"] != sim.state.action_points_remaining or row["ap_before"] <= 0
                    or row["player_id"] != turn["player_id"] or row["turn"] != turn["turn"]
                    or row["observation_version"] != OBSERVATION_V2 or row["prompt_version"] != STEP_PROMPT_VERSION
                    or row["schema_version"] != PLAN_SCHEMA_VERSION
                    or row["legal_action_count"] != len(obs.to_dict()["legal_actions"])):
                raise ValueError("observation mismatch")
            if (row["explicit_end_turn"] or not row["success"]) and step_index != len(turn["steps"])-1:
                raise ValueError("decision after stop")
            if row["decision"] is not None:
                plan = parse_step(canonical_json(row["decision"]), obs)
                selected = plan.actions[0].to_dict() if plan.actions else None
                if (row["selected_action"] != selected or row["explicit_end_turn"] != (not plan.actions)
                        or row["decision"] != row["resulting_plan"] or not row["success"]
                        or row["selected_current_legal"] != (True if plan.actions else None)):
                    raise ValueError("decision mismatch")
                if plan.actions and row["command_index"] is None and row["execution_error"] != "catalog_execution_defect":
                    raise ValueError("missing action command")
            elif row["success"] or row["selected_action"] is not None or row["explicit_end_turn"]:
                raise ValueError("failed decision mismatch")
            if row["command_index"] is not None:
                from aig.arena.ai.contracts import action_command, action_from_dict
                from aig.arena.snapshots import command_to_dict
                expected = command_to_dict(action_command(action_from_dict(row["selected_action"]), turn["player_id"]))
                if row["command_index"] != index or entries[index]["command"] != expected:
                    raise ValueError("command association mismatch")
                sim.execute(command_from_dict(entries[index]["command"]))
                actions.append(row["selected_action"])
                index += 1
            if row["ap_after"] != sim.state.action_points_remaining or row["resulting_state_hash"] != state_hash(sim.state) or row["terminal"] != sim.state.winner_player_id:
                raise ValueError("step result mismatch")
        unused = sim.state.action_points_remaining
        prefix_stops = ("catalog_execution_defect", "request_ceiling", "source_mutation") if full_match_turn else ("catalog_execution_defect",)
        if (sim.state.winner_player_id is None and turn["error_category"] not in prefix_stops
                and index == len(entries)):
            raise ValueError("missing EndTurn")
        if index < len(entries):
            if len(entries)-index != 1 or entries[index]["command"]["type"] != "arena_end_turn" or sim.state.winner_player_id:
                raise ValueError("end turn mismatch")
            sim.execute(command_from_dict(entries[index]["command"]))
        if (sim.trace() != trace or turn["action_sequence"] != actions or turn["actions_executed"] != len(actions)
                or turn["steps_requested"] != len(turn["steps"]) or len(turn["steps"]) > 5
                or turn["terminal"] != sim.state.winner_player_id
                or turn["explicit_early_end"] != any(s["explicit_end_turn"] for s in turn["steps"])
                or turn["ap_unused"] != unused or turn["ap_available"] != trace["initial_snapshot"]["action_points_remaining"]
                or turn["ap_executed"] != sum(e["ap_used"] for e in entries)
                or turn["ap_available"] != turn["ap_executed"]+unused):
            raise ValueError("turn mismatch")
        return dict(success=True, final_state_hash=digest(final), command_trace_hash=digest(trace))
    except Exception:
        return dict(success=False, error_category="replay_mismatch")


def run_probe(directory, probe, provider, name, experiment, trial, pricing):
    directory.mkdir(parents=True, exist_ok=False)
    sim = ArenaSimulation(frozen_probe(probe))
    write_json(directory/"manifest.json", dict(experiment, probe=probe, trial=trial))
    turn = ArenaStepController(provider, name).run_turn(sim, trial=trial)
    metrics = turn_metrics(turn, pricing)
    write_json(directory/"turn.json", turn)
    write_json(directory/"command-trace.json", sim.trace())
    write_json(directory/"final-snapshot.json", to_snapshot(sim.state))
    verification = verify_stepwise_trial(directory)
    write_json(directory/"verification.json", verification)
    win = sim.state.winner_player_id == sim.initial_snapshot["active_player_id"]
    objective = win if probe in ("winning_core_line", "team_elimination") else (
        sim.state.units["ally"].status.value == "active" if probe == "revive_decision" else None)
    failure = turn["error_category"] or (None if verification["success"] else "replay_mismatch")
    result = dict(directory=str(directory), probe=probe, trial=trial, valid=failure is None,
        error_category=failure, probe_outcome=dict(objective_achieved=objective, immediate_victory=win,
        action_sequence=turn["action_sequence"]), turn=turn, metrics=metrics, mechanical_metrics=sim.metrics(),
        verification=verification)
    write_json(directory/"result.json", result)
    return result


def benchmark_stepwise(*, output, blue_provider="heuristic", probe="all", probe_trials=4,
                       settings=None, provider_factory=create_arena_step_provider,
                       preflight_only=False, pricing=None, request_ceiling=None, repair_version=REPAIR_V1):
    repair_version = resolve_repair_version(repair_version)
    integer(probe_trials, "probe_trials", 1)
    settings = settings or Settings()
    if blue_provider not in ("heuristic", "ollama", "openai"):
        raise ValueError("unknown stepwise provider")
    probes = list(probe_set()["probes"]) if probe == "all" else [probe]
    if any(p not in probe_set()["probes"] for p in probes):
        raise ValueError("unknown Arena probe")
    pricing = validate_pricing(pricing, settings.openai.model)
    maximum = 0 if blue_provider == "heuristic" else 1 + (0 if preflight_only else len(probes)*probe_trials*10)
    if request_ceiling is not None:
        integer(request_ceiling, "request_ceiling", 0)
        if maximum > request_ceiling:
            raise ValueError(f"schedule maximum {maximum} exceeds request ceiling {request_ceiling}; reduce trial count")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be new or empty; prior evidence is never overwritten")
    output.mkdir(parents=True, exist_ok=True)
    artifact(BENCHMARK_VERSION)
    experiment = manifest([blue_provider], settings, source_manifest(), observation_version=OBSERVATION_V2)
    experiment.update(benchmarkVersion=BENCHMARK_VERSION, benchmarkSpecHash=ARTIFACT_HASHES[BENCHMARK_VERSION],
        controlMode="stepwise", controlVersion=CONTROL_VERSION, promptVersion=STEP_PROMPT_VERSION,
        promptHash=hashlib.sha256(STEP_PROMPT.encode()).hexdigest(), baseRecipePromptVersion=STEP_PROMPT_VERSION,
        baseRecipeObservationVersion=OBSERVATION_V2, repairVersion=repair_version,
        experimentOverrides={"repairVersion": repair_version} if repair_version != REPAIR_V1 else {}, pricing=pricing,
        pricingHash=digest(pricing) if pricing else None, theoreticalRequestCeiling=maximum)
    profile = experiment["providers"][blue_provider]
    if blue_provider != "heuristic" and profile["modelConfigVersion"] not in ("qwen-config-v1", "luna-config-v1"):
        raise ValueError("stepwise experiment requires the unchanged v1 model profile")
    report = dict(benchmarkVersion=BENCHMARK_VERSION, experiment=experiment, status="complete", preflight=[],
                  trialsStarted=0, validTrials=0, plannedProbeTrials=len(probes)*probe_trials, runs=[])
    try:
        provider = provider_factory(settings, blue_provider, **({"repair_version": repair_version} if repair_version != REPAIR_V1 else {}))
        if blue_provider != "heuristic" and (provider.configuration() != profile["modelConfiguration"] or
                provider.prompt_version != STEP_PROMPT_VERSION or provider.schema_version != PLAN_SCHEMA_VERSION or
                getattr(provider, "repair_version", REPAIR_V1) != repair_version):
            raise ValueError("provider contract mismatch")
    except Exception:
        provider = None
        report["status"] = "configuration_failed"
    if provider is not None and blue_provider != "heuristic":
        _, check = checked_step(provider, blue_provider, build_observation(ArenaSimulation().state, version=OBSERVATION_V2), preflight=True)
        report["preflight"].append(check)
        if not check["success"]:
            report["status"] = "preflight_failed"
    if report["status"] == "complete" and not preflight_only:
        for name in probes:
            for trial in range(1, probe_trials+1):
                row = run_probe(output/"probes"/name/blue_provider/f"run-{trial:03d}", name, provider, blue_provider, experiment, trial, pricing)
                report["runs"].append(row)
                report["trialsStarted"] += 1
                if not row["valid"]:
                    report["status"] = "trial_failed"
                    break
            if report["status"] != "complete":
                break
    runs = report["runs"]
    report["validTrials"] = sum(r["valid"] for r in runs)
    report["failedTurns"] = len(runs)-report["validTrials"]
    report["turnsWithoutProviderFailure"] = sum(r["turn"]["provider_failures"] == 0 for r in runs)
    report["turnsWithProviderFailure"] = sum(r["turn"]["provider_failures"] > 0 for r in runs)
    calls = [s for r in runs for s in r["turn"]["steps"]]
    report["inferenceAllAttempts"] = inference_metrics(calls, (profile["modelConfiguration"] or {}).get("context_size"))
    report["inferenceValidTurns"] = inference_metrics([s for r in runs if r["valid"] for s in r["turn"]["steps"]],
                                                       (profile["modelConfiguration"] or {}).get("context_size"))
    report["providerRequestsIncludingPreflight"] = sum(r["provider_requests"] for r in calls+report["preflight"])
    report["explicitEarlyStopRate"] = sum(r["turn"]["explicit_early_end"] for r in runs)/len(runs) if runs else None
    selected = [s for s in calls if s["selected_action"] is not None]
    report["selectedCurrentLegalRate"] = sum(s["selected_current_legal"] is True for s in selected)/len(selected) if selected else None
    initial = [s for s in calls if s["first_response_valid"] is not None]
    report["firstResponseValidRate"] = sum(s["first_response_valid"] for s in initial)/len(initial) if initial else None
    report["turnDistributions"] = {k: distribution(r["metrics"][k] for r in runs if r["valid"])
        for k in ("total_provider_latency_seconds", "input_tokens", "output_tokens", "cached_input_tokens",
                  "uncached_input_tokens", "estimated_cost_usd", "provider_calls_per_turn", "provider_calls_per_ap")}
    report["decisionDistributions"] = {k: distribution(s["usage"][k] for s in calls)
        for k in ("input_tokens", "output_tokens", "cached_input_tokens", "uncached_input_tokens", "estimated_cost_usd")}
    write_json(output/"summary.json", report)
    lines = ["# Arena stepwise benchmark v2", "", f"Status: {report['status']}; {report['validTrials']}/{len(runs)} valid turns.", "",
             "Preflight is separate. Failed turns remain in reliability denominators. No tactical aggregate score.", "",
             "| Probe | AP used / unused | Actions / decisions | Objective | Replay |",
             "| --- | ---: | ---: | --- | --- |"]
    for r in runs:
        t = r["turn"]
        lines.append(f"| {r['probe']} | {t['ap_executed']} / {t['ap_unused']} | {t['actions_executed']} / {t['steps_requested']} | {r['probe_outcome']['objective_achieved']} | {r['verification']['success']} |")
    lines += ["", "Compare total provider latency and tokens/cost per completed player turn with full-turn controls.",
              "Per-decision telemetry, missing-usage coverage and all failed-turn evidence are retained in summary.json.",
              "Cost is null unless explicit dated pricing and complete usage are supplied; no pricing lookup occurs."]
    (output/"report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return report
