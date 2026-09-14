"""Controlled repair-only benchmark: one inference per injected invalid decision."""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

from aig.ai.benchmark import write_json
from aig.ai.plan_schema import strict_json
from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION, action_command
from aig.arena.ai.observation import OBSERVATION_V2, build_observation
from aig.arena.ai.repair import REPAIR_V1, REPAIR_VERSIONS, repair_version as resolve_repair_version
from aig.arena.ai.stepwise import STEP_PROMPT, STEP_PROMPT_VERSION, create_arena_step_provider, parse_step
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_provider import safe_inference
from aig.arena.benchmark_versions import ARTIFACTS, artifact, ARTIFACT_HASHES, manifest, source_manifest
from aig.arena.commands import ArenaEndTurn
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json, digest, from_snapshot, state_hash
from aig.settings import Settings, load_settings

BENCHMARK_VERSION = "arena-repair-benchmark-v1"
CHALLENGE_VERSION = "arena-repair-challenges-v1"
CHALLENGE_HASH = "03e2b680769d937493a064ce53fc10ffce2d5a28702b628f10799b5506de88f4"


def challenge_set():
    data = artifact(CHALLENGE_VERSION)
    if data["version"] != CHALLENGE_VERSION or data["content_hash"] != CHALLENGE_HASH or digest(data["challenges"]) != CHALLENGE_HASH:
        raise ValueError("frozen repair challenge integrity failure")
    for challenge in data["challenges"]:
        validate_challenge(challenge)
    return data


def validate_challenge(challenge):
    state = from_snapshot(challenge["snapshot"])
    obs = build_observation(state, version=OBSERVATION_V2)
    if state_hash(state) != challenge["state_hash"] or obs.hash != challenge["observation_hash"] or obs.to_dict() != challenge["observation"]:
        raise ValueError("repair challenge state/observation mismatch")
    try:
        parse_step(canonical_json(challenge["invalid_decision"]), obs)
    except ArenaProviderError as error:
        if error.category != "invalid_reference" or error.diagnostic.to_dict() != challenge["expected_failure"]:
            raise ValueError("repair challenge diagnostic mismatch") from None
        return obs, error
    raise ValueError("repair challenge injection unexpectedly valid")


def run_trial(provider, challenge, trial, *, execute=True):
    """No initial inference, create_step, fallback, or repair-of-repair call."""
    obs, failure = validate_challenge(challenge)
    evidence = provider.rejection_evidence(canonical_json(challenge["invalid_decision"]), obs, failure)
    messages = provider.repair_messages(obs, failure, evidence)
    row = dict(provider=provider.name, repair_version=provider.repair_version, challenge_id=challenge["id"],
        trial=trial, state_hash=challenge["state_hash"], observation_hash=obs.hash,
        injected_invalid_decision=challenge["invalid_decision"], expected_failure=challenge["expected_failure"],
        repair_request_count=0, parse_status=None, schema_status=None, current_catalog_status=None,
        repair_success=False, repaired_action=None, end_turn=None, ap_cost=None,
        execution_success=None, error_category=None, rejected_decisions=[evidence])
    record = dict(metrics={})
    plan = None
    started = perf_counter()
    try:
        guard = getattr(provider, "before_request", None)
        if guard is not None:
            guard()
        row["repair_request_count"] = 1
        raw = provider.request(messages, record)
        record["wall_clock_seconds"] = perf_counter() - started
        try:
            if not isinstance(raw, str) or len(raw) > 32768:
                raise ArenaProviderError("schema_validation", message="Response exceeds the size limit.")
            try:
                data = strict_json(raw)
                row["parse_status"] = True
            except (ValueError, TypeError, RecursionError):
                row["parse_status"] = False
                raise ArenaProviderError("malformed_json", message="Response is not valid strict JSON.") from None
            try:
                ArenaTurnPlan.from_dict(data)
                row["schema_status"] = True
            except (ValueError, TypeError, KeyError, RecursionError):
                row["schema_status"] = False
                raise ArenaProviderError("schema_validation", message="Response does not satisfy ArenaTurnPlan schema.") from None
            # Always use the unchanged authoritative parser; never fix or approximate.
            plan = parse_step(raw, obs)
            row["current_catalog_status"] = True
        except ArenaProviderError as error:
            if row["schema_status"]:
                row["current_catalog_status"] = False
            row["rejected_decisions"].append(provider.rejection_evidence(raw, obs, error))
            raise
        row.update(repair_success=True, repaired_action=plan.actions[0].to_dict() if plan.actions else None,
                   end_turn=not bool(plan.actions), ap_cost=plan.ap_cost)
    except ArenaProviderError as error:
        row["error_category"] = record["error_category"] = error.category
    except Exception:
        row["error_category"] = record["error_category"] = "provider_exception"
    finally:
        record.setdefault("wall_clock_seconds", perf_counter()-started)
    for item in row["rejected_decisions"]:
        item["repair_result"] = "succeeded" if row["repair_success"] else "failed"
    row["telemetry"] = safe_inference(dict(attempts=[record]))["attempts"][0]
    if plan is not None and execute:
        sim = ArenaSimulation(from_snapshot(challenge["snapshot"]))
        try:
            sim.execute(action_command(plan.actions[0], sim.state.active_player_id) if plan.actions
                        else ArenaEndTurn(sim.state.active_player_id))
            row.update(execution_success=True, resulting_state_hash=state_hash(sim.state))
        except ValueError:
            row.update(execution_success=False, error_category="catalog_execution_defect")
    return row


def benchmark(*, output, provider="ollama", repair_version=REPAIR_V1, challenge="all", trials=4,
              request_ceiling=24, settings=None, provider_factory=create_arena_step_provider, strict_provider=True):
    selected_version = resolve_repair_version(repair_version)
    if provider not in ("ollama", "openai") or not strict_provider:
        raise ValueError("repair benchmark requires a strict model provider; heuristic is not a repair adapter")
    if type(trials) is not int or trials < 1 or type(request_ceiling) is not int or request_ceiling < 1:
        raise ValueError("trials and request ceiling must be positive integers")
    data = challenge_set()
    selected = [c for c in data["challenges"] if challenge in ("all", c["id"])]
    maximum = len(selected)*trials
    if not selected or maximum > request_ceiling:
        raise ValueError("unknown challenge or schedule exceeds request ceiling")
    settings = settings or Settings()
    source = source_manifest()
    experiment = manifest([provider], settings, source, observation_version=OBSERVATION_V2)
    profile = experiment["providers"][provider]
    if profile["modelConfigVersion"] != ("qwen-config-v1" if provider == "ollama" else "luna-config-v1"):
        raise ValueError("repair experiment requires unchanged model profile")
    spec = artifact(BENCHMARK_VERSION)
    experiment.update(benchmarkVersion=BENCHMARK_VERSION, benchmarkSpecHash=ARTIFACT_HASHES[BENCHMARK_VERSION],
        repairBenchmarkVersion=BENCHMARK_VERSION, repairChallengeVersion=CHALLENGE_VERSION,
        repairChallengeHash=CHALLENGE_HASH, repairVersion=selected_version, controlMode="repair-only",
        controlVersion=BENCHMARK_VERSION, promptVersion=STEP_PROMPT_VERSION,
        promptHash=hashlib.sha256(STEP_PROMPT.encode()).hexdigest(), baseRecipePromptVersion=STEP_PROMPT_VERSION,
        baseRecipeObservationVersion=OBSERVATION_V2, experimentOverrides={},
        theoreticalRequestCeiling=maximum, requestCeiling=request_ceiling, initialInferenceRequests=0,
        preflightRequests=0, selectedChallenges=[c["id"] for c in selected], trialsPerChallenge=trials)
    for key in ("probeSetVersion", "probeSetHash"):
        experiment.pop(key, None)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/"manifest.json", experiment)
    model = provider_factory(settings, provider, repair_version=selected_version)
    if (model.name != provider or model.configuration() != profile["modelConfiguration"] or
            model.prompt_version != STEP_PROMPT_VERSION or model.schema_version != PLAN_SCHEMA_VERSION or
            model.repair_version != selected_version):
        raise ValueError("repair provider contract mismatch")
    requests = 0

    def guard():
        nonlocal requests
        if source_manifest()["sourceManifestHash"] != source["sourceManifestHash"]:
            raise ArenaProviderError("source_mutation")
        if requests >= maximum:
            raise ArenaProviderError("request_ceiling")
        requests += 1

    model.before_request = guard
    report = dict(benchmarkVersion=BENCHMARK_VERSION, status="complete", plannedRepairRequests=maximum,
                  repairRequests=0, repairSuccesses=0, runs=[])
    static_failures = {"malformed_json", "schema_validation", "invalid_reference", "invalid_ability", "ap_budget"}
    for item in selected:
        for trial in range(1, trials+1):
            row = run_trial(model, item, trial)
            report["runs"].append(row)
            report["repairRequests"] = requests
            report["repairSuccesses"] += int(row["repair_success"])
            write_json(output/f"{item['id']}-{trial:03d}.json", row)
            if row["error_category"] and row["error_category"] not in static_failures:
                report["status"] = "stopped"
            if source_manifest()["sourceManifestHash"] != source["sourceManifestHash"]:
                report.update(status="stopped", stopReason="source_mutation")
            write_json(output/"summary.json", report)
            if report["status"] == "stopped":
                break
        if report["status"] == "stopped":
            break
    report["challengeResults"] = {}
    for item in selected:
        rows = [r for r in report["runs"] if r["challenge_id"] == item["id"]]
        report["challengeResults"][item["id"]] = dict(trials=len(rows), successes=sum(r["repair_success"] for r in rows),
            endTurns=sum(r["end_turn"] is True for r in rows),
            uniqueRepairedActions=sorted({canonical_json(r["repaired_action"]) for r in rows if r["repair_success"]}))
    write_json(output/"source-after.json", source_manifest())
    write_json(output/"summary.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("ollama", "openai"), default="ollama")
    parser.add_argument("--repair-version", choices=REPAIR_VERSIONS, default=REPAIR_V1)
    parser.add_argument("--challenge", default="all")
    parser.add_argument("--trials", type=int, default=4)
    parser.add_argument("--request-ceiling", type=int, default=24)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict-provider", action="store_true", default=True)
    args = parser.parse_args(argv)
    report = benchmark(**vars(args), settings=load_settings())
    print(json.dumps({k: report[k] for k in ("status", "repairRequests", "repairSuccesses")}))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
