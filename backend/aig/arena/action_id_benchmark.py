"""Explicit action-ID probe experiment. No full-match or implicit preflight path."""
import argparse
import hashlib
import json
from pathlib import Path

from aig.ai.benchmark import write_json
from aig.arena.ai.action_id import (CONTROL_VERSION, STEP_PROMPT_VERSION, STEP_PROMPT, SCHEMA_VERSION,
    REPAIR_VERSION, ArenaActionIdController, create_action_id_provider, parse_choice, resolve_action, catalog_hash)
from aig.arena.ai.observation import OBSERVATION_V3, build_observation
from aig.arena.benchmark_versions import (manifest, artifact, ARTIFACT_HASHES, source_manifest, probe_set, frozen_probe)
from aig.arena.fullmatch_benchmark import RequestBudget, frozen_guard, auxiliary_source_manifest
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import (canonical_json, digest, from_snapshot, to_snapshot, command_from_dict,
                                 command_to_dict, state_hash)
from aig.arena.ai.contracts import action_command
from aig.arena.commands import ArenaEndTurn
from aig.arena.stepwise_benchmark import turn_metrics
from aig.arena.benchmark_metrics import inference_metrics
from aig.settings import Settings, load_settings, DEFAULT_LOCAL_FILE
from aig.arena.ai.validation import ArenaProviderError

# V3 already names the frozen structured full-match orchestrator. Never redefine it.
BENCHMARK_VERSION = "arena-benchmark-v4"


def experiment_manifest(name, settings, source):
    artifact(BENCHMARK_VERSION)
    result = manifest([name], settings, source, observation_version=OBSERVATION_V3)
    result.update(benchmarkVersion=BENCHMARK_VERSION, benchmarkSpecHash=ARTIFACT_HASHES[BENCHMARK_VERSION],
        controlMode="stepwise-action-id", controlVersion=CONTROL_VERSION, promptVersion=STEP_PROMPT_VERSION,
        promptHash=hashlib.sha256(STEP_PROMPT.encode()).hexdigest(), planSchemaVersion=SCHEMA_VERSION,
        decisionSchemaVersion=SCHEMA_VERSION, repairVersion=REPAIR_VERSION,
        baseRecipePromptVersion=STEP_PROMPT_VERSION, baseRecipeObservationVersion=OBSERVATION_V3,
        experimentOverrides={})
    return result


def verify_action_id_trial(directory):
    """Rebuild every catalog at its command boundary; replay without providers."""
    try:
        directory = Path(directory)
        read = lambda name: json.loads((directory/name).read_text(encoding="utf-8"))
        manifest_data, trace, final, turn = [read(n) for n in
            ("manifest.json", "command-trace.json", "final-snapshot.json", "turn.json")]
        expected = dict(benchmarkVersion=BENCHMARK_VERSION, controlVersion=CONTROL_VERSION,
            observationVersion=OBSERVATION_V3, promptVersion=STEP_PROMPT_VERSION,
            decisionSchemaVersion=SCHEMA_VERSION, repairVersion=REPAIR_VERSION)
        if any(manifest_data.get(k) != v for k,v in expected.items()):
            raise ValueError("versions")
        if to_snapshot(replay(trace).state) != final:
            raise ValueError("replay")
        sim = ArenaSimulation(from_snapshot(trace["initial_snapshot"]))
        actions = []
        for index,row in enumerate(turn["steps"]):
            obs = build_observation(sim.state, version=OBSERVATION_V3)
            if (index >= 5 or row["step_index"] != index or row["observation"] != obs.to_dict()
                or row["observation_hash"] != obs.hash or row["action_catalog_hash"] != catalog_hash(obs)
                or row["ap_before"] != sim.state.action_points_remaining or row["ap_before"] <= 0
                or row["player_id"] != turn["player_id"] or row["turn"] != turn["turn"]
                or row["observation_version"] != OBSERVATION_V3 or row["schema_version"] != SCHEMA_VERSION
                or row["prompt_version"] != STEP_PROMPT_VERSION
                or row["legal_action_count"] != len(obs.to_dict()["legal_actions"])):
                raise ValueError("observation")
            selected = None
            if row["decision"] is not None:
                choice = parse_choice(canonical_json(row["decision"]), obs)
                action = resolve_action(choice, obs)
                selected = action.to_dict() if action else None
                if (not row["success"] or row["decision"] != row["resulting_decision"]
                    or row["selected_action_id"] != choice.action_id
                    or row["explicit_end_turn"] != (choice.action_id is None)):
                    raise ValueError("choice")
                if action and row["execution_error"] is None:
                    ci = len(sim.trace()["entries"])
                    command = action_command(action, turn["player_id"])
                    if row["command_index"] != ci or trace["entries"][ci]["command"] != command_to_dict(command):
                        raise ValueError("command association")
                    sim.execute(command)
                    if row["command_result"] != sim.trace()["entries"][-1]:
                        raise ValueError("command result")
                    actions.append(selected)
                elif row["command_index"] is not None or row["command_result"] is not None:
                    raise ValueError("unexpected command")
            elif (row["success"] or row["selected_action_id"] is not None or row["explicit_end_turn"]
                  or row["command_index"] is not None or row["command_result"] is not None):
                raise ValueError("failed choice")
            if (row["resolved_action"] != selected or row["selected_action"] != selected
                or row["selected_current_legal"] != (True if selected else None)
                or row["ap_after"] != sim.state.action_points_remaining
                or row["resulting_state_hash"] != state_hash(sim.state)
                or row["terminal"] != sim.state.winner_player_id):
                raise ValueError("step result")
            if (not row["success"] or row["explicit_end_turn"] or row["execution_error"]) and index != len(turn["steps"])-1:
                raise ValueError("decision after stop")
        unused = sim.state.action_points_remaining
        if sim.state.winner_player_id is None and turn["error_category"] is None:
            if unused and not turn["explicit_early_end"]:
                raise ValueError("unexplained stop")
            sim.execute(ArenaEndTurn(turn["player_id"]))
        if (sim.trace() != trace or to_snapshot(sim.state) != final or turn["action_sequence"] != actions
            or turn["actions_executed"] != len(actions) or turn["steps_requested"] != len(turn["steps"])
            or turn["control_version"] != CONTROL_VERSION or turn["control_mode"] != "stepwise-action-id"
            or turn["ap_unused"] != unused or turn["ap_available"] != trace["initial_snapshot"]["action_points_remaining"]
            or turn["ap_executed"] != sum(e["ap_used"] for e in trace["entries"])
            or turn["ap_executed"] + unused != turn["ap_available"]
            or turn["explicit_early_end"] != any(s["explicit_end_turn"] for s in turn["steps"])
            or turn["terminal"] != sim.state.winner_player_id):
            raise ValueError("turn")
        return dict(success=True, final_state_hash=digest(final), command_trace_hash=digest(trace))
    except Exception:
        return dict(success=False, error_category="replay_mismatch")


def benchmark_action_id(*, output, provider="heuristic", probe="all", probe_trials=1,
                        request_ceiling=70, settings=None, provider_factory=create_action_id_provider):
    if type(probe_trials) is not int or probe_trials < 1:
        raise ValueError("positive probe_trials required")
    if provider not in ("heuristic", "ollama", "openai"):
        raise ValueError("unknown provider")
    probes = list(probe_set()["probes"]) if probe == "all" else [probe]
    if any(p not in probe_set()["probes"] for p in probes):
        raise ValueError("unknown probe")
    maximum = 0 if provider == "heuristic" else len(probes)*probe_trials*10
    budget = RequestBudget(request_ceiling)
    settings = settings or Settings()
    source = source_manifest()
    experiment = experiment_manifest(provider, settings, source)
    profile = experiment["providers"][provider]
    if provider != "heuristic" and profile["modelConfigVersion"] not in ("qwen-config-v1", "luna-config-v1"):
        raise ValueError("requires unchanged v1 model profile")
    experiment.update(theoreticalRequestCeiling=maximum, requestCeiling=request_ceiling,
                      preflightRequests=0, plannedProbeTrials=len(probes)*probe_trials,
                      orchestrationPolicy="phase9c-bounded-independent-trials-v1")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/"manifest.json", experiment)
    instance = provider_factory(settings, provider)
    if (instance.prompt_version != STEP_PROMPT_VERSION or instance.schema_version != SCHEMA_VERSION
        or instance.repair_version != REPAIR_VERSION or (provider != "heuristic" and
        (instance.configuration() != profile["modelConfiguration"] or not instance.repair))):
        raise ValueError("provider contract mismatch")
    env_hash = hashlib.sha256(DEFAULT_LOCAL_FILE.read_bytes()).hexdigest() if DEFAULT_LOCAL_FILE.exists() else None
    budget.guard = frozen_guard(source, env_hash, auxiliary_source_manifest())
    instance.before_request = budget.take
    report = dict(benchmarkVersion=BENCHMARK_VERSION, experiment=experiment, status="complete", runs=[])
    for name in probes:
        for trial in range(1,probe_trials+1):
            if provider != "heuristic" and budget.used >= budget.limit:
                report["status"] = "request_ceiling"
                break
            directory = output/"probes"/name/f"run-{trial:03d}"
            directory.mkdir(parents=True)
            sim = ArenaSimulation(frozen_probe(name))
            turn = ArenaActionIdController(instance, provider).run_turn(sim, trial=trial)
            metrics = turn_metrics(turn)
            for filename,value in (("manifest.json", experiment), ("turn.json", turn),
                                   ("command-trace.json", sim.trace()), ("final-snapshot.json", to_snapshot(sim.state))):
                write_json(directory/filename, value)
            verification = verify_action_id_trial(directory)
            write_json(directory/"verification.json", verification)
            win = sim.state.winner_player_id == sim.initial_snapshot["active_player_id"]
            objective = win if name in ("winning_core_line", "team_elimination") else (
                sim.state.units["ally"].status.value == "active" if name == "revive_decision" else None)
            valid = turn["error_category"] is None and verification["success"]
            row = dict(probe=name, trial=trial, directory=str(directory), valid=valid, turn=turn,
                       metrics=metrics, verification=verification, mechanical_metrics=sim.metrics(),
                       probe_outcome=dict(objective_achieved=objective, immediate_victory=win))
            report["runs"].append(row)
            failure = turn["error_category"]
            if not verification["success"]:
                failure = "replay_mismatch"
            if any(s["fallback_used"] or s["requested_provider"] != provider or
                   s["actual_provider"] not in (None, provider) or
                   (s["success"] and s["actual_provider"] != provider) for s in turn["steps"]):
                failure = "provider_mismatch"
            if budget.used != sum(r["turn"]["provider_requests"] for r in report["runs"]):
                failure = "accounting_failed"
            try:
                budget.guard()
            except ArenaProviderError as error:
                failure = error.category
            # Ordinary provider/selection failures consume their intended trial.
            # Unknown errors fail closed; integrity failures never advance.
            ordinary = {"invalid_action_id", "repair_failed", "malformed_json",
                        "schema_validation", "invalid_reference", "invalid_ability",
                        "transport_failure", "provider_exception", "timeout",
                        "connection_failure", "dns_failure", "malformed_envelope",
                        "authentication_failure", "rate_limit", "server_error", "context_limit",
                        "ap_budget", "truncated_output", "empty_output", "refusal"}
            if failure and failure not in ordinary:
                report["status"] = failure
                break
        if report["status"] != "complete":
            break
    runs = report["runs"]
    if report["status"] == "complete" and any(not r["valid"] for r in runs):
        report["status"] = "completed_with_failures"
    calls = [s for r in runs for s in r["turn"]["steps"]]
    initial = [s for s in calls if s["first_response_valid"] is not None]
    selected = [s for s in calls if s["selected_action_id"] is not None]
    attempts = [a for s in calls for a in s["attempts"]]
    report.update(trialsStarted=len(runs), validTrials=sum(r["valid"] for r in runs),
        providerRequests=budget.used, recordedProviderRequests=sum(s["provider_requests"] for s in calls),
        firstResponseValidRate=sum(s["first_response_valid"] for s in initial)/len(initial) if initial else None,
        firstResponseSchemaValidRate=sum(s["attempts"][0]["error_category"] in (None,"invalid_action_id")
            for s in initial)/len(initial) if initial else None,
        invalidActionIdAttempts=sum(a["error_category"] == "invalid_action_id" for a in attempts),
        validActionIdRate=len(selected)/(len(selected)+sum(a["error_category"] == "invalid_action_id" for a in attempts))
            if selected or any(a["error_category"] == "invalid_action_id" for a in attempts) else None,
        selectedCurrentLegalRate=sum(s["selected_current_legal"] is True for s in selected)/len(selected) if selected else None,
        repairAttempts=sum(s["repair_requests"] for s in calls), repairSuccesses=sum(s["repair_succeeded"] for s in calls),
        explicitEndTurns=sum(s["explicit_end_turn"] for s in calls),
        inferenceAllAttempts=inference_metrics(calls, (profile["modelConfiguration"] or {}).get("context_size")))
    report["inferenceAllAttempts"]["statically_invalid_initial_outputs"] += sum(
        s["attempts"][0]["error_category"] == "invalid_action_id" for s in initial)
    if report["providerRequests"] != report["recordedProviderRequests"]:
        report["status"] = "accounting_failed"
    write_json(output/"summary.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("heuristic", "ollama", "openai"), default="heuristic")
    parser.add_argument("--probe", default="all")
    parser.add_argument("--probe-trials", type=int, default=1)
    parser.add_argument("--request-ceiling", type=int, default=70)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = benchmark_action_id(**vars(args), settings=load_settings())
    print(canonical_json({k:report[k] for k in ("status","trialsStarted","validTrials","providerRequests")}))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
