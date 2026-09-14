"""Phase 8C preparation and explicitly authorized paired Qwen repair comparison.

Preparation and comparison are offline. Only the explicit ``run`` subcommand
constructs a provider. Battle logic remains in the historical V3 orchestrator.
"""

import argparse
import hashlib
from pathlib import Path

from aig.ai.benchmark import write_json
from aig.arena.ai.observation import OBSERVATION_V2, build_observation
from aig.arena.ai.repair import REPAIR_V1, REPAIR_V2, REPAIR_VERSIONS
from aig.arena.ai.stepwise import CONTROL_VERSION, STEP_PROMPT_VERSION, STEP_PROMPT, checked_step, create_arena_step_provider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_versions import ARTIFACT_HASHES, artifact, manifest, source_manifest
from aig.arena.fullmatch_benchmark import RequestBudget, HARD_STOPS, auxiliary_source_manifest, frozen_guard, run_match, verify_match
from aig.arena.repair_fullmatch_metrics import aggregate, match_metrics, read
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import digest
from aig.settings import DEFAULT_LOCAL_FILE, load_settings

VERSION = "arena-benchmark-v2"
RECOMMENDED_CEILING = 300
MAX_TURNS = 100
STOP_CATEGORIES = HARD_STOPS | {"wrong_repair_version", "request_accounting_defect", "evidence_corruption"}


def file_hash(path):
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def inventory(root):
    return {p.relative_to(root).as_posix(): file_hash(p) for p in sorted(Path(root).rglob("*"))
            if p.is_file() and p.name != "evidence-sha256.json"}


def slots():
    initial = ArenaSimulation().initial_snapshot
    return [dict(pair_id=f"pair-{i:02d}", qwenSide="blue" if i % 2 else "red",
                 assignments=dict(blue="ollama" if i % 2 else "heuristic", red="heuristic" if i % 2 else "ollama"),
                 initialStateHash=digest(initial)) for i in range(1, 7)]


def contracts(settings, source):
    artifact(VERSION)
    result = manifest(["ollama", "heuristic"], settings, source, observation_version=OBSERVATION_V2)
    if result["providers"]["ollama"]["modelConfigVersion"] != "qwen-config-v1":
        raise ValueError("qwen-config-v1 required")
    result.update(benchmarkVersion=VERSION, benchmarkSpecHash=ARTIFACT_HASHES[VERSION],
                  orchestrationVersion="arena-benchmark-v3", controlMode="stepwise", controlVersion=CONTROL_VERSION,
                  promptVersion=STEP_PROMPT_VERSION, promptHash=hashlib.sha256(STEP_PROMPT.encode()).hexdigest(),
                  baseRecipePromptVersion=STEP_PROMPT_VERSION, baseRecipeObservationVersion=OBSERVATION_V2,
                  experimentOverrides={}, maxGlobalTurns=MAX_TURNS)
    return result


def prepare(output, *, settings, v1_output, v2_output, comparison_output, request_ceiling=RECOMMENDED_CEILING):
    if type(request_ceiling) is not int or request_ceiling <= 0:
        raise ValueError("positive explicit per-arm request ceiling required")
    paths = [Path(p).resolve() for p in (output, v1_output, v2_output, comparison_output)]
    if any(p.exists() for p in paths) or len(set(paths)) != 4:
        raise ValueError("preparation and all future output roots must be distinct and new")
    if any(a in b.parents for a in paths for b in paths if a != b):
        raise ValueError("output roots must not contain each other")
    source = source_manifest()
    if source["sourceRevision"] is None or source["sourceDirty"] is None:
        raise ValueError("Git provenance unavailable")
    common = contracts(settings, source)
    plan = dict(version="arena-repair-fullmatch-experiment-v1", armOrder=list(REPAIR_VERSIONS),
        requestCeilingPerArm=request_ceiling, intendedMatchesPerArm=6, preflightRequestsPerArm=1,
        initialSnapshot=ArenaSimulation().initial_snapshot, source=source,
        auxiliarySource=auxiliary_source_manifest(), settingsFileHash=file_hash(DEFAULT_LOCAL_FILE),
        comparisonOutput=str(paths[3]), arms={})
    for version, target in zip(REPAIR_VERSIONS, paths[1:3]):
        arm = dict(common, repairVersion=version, experimentOverrides={"repairVersion": version})
        plan["arms"][version] = dict(output=str(target), manifest=arm,
                                   matches=[dict(arm, **slot) for slot in slots()])
    # Pairing differences are restricted to explicit repair provenance.
    for a, b in zip(plan["arms"][REPAIR_V1]["matches"], plan["arms"][REPAIR_V2]["matches"]):
        assert {k for k in a if a[k] != b[k]} == {"repairVersion", "experimentOverrides"}
    paths[0].mkdir(parents=True, exist_ok=False)
    write_json(paths[0]/"plan.json", plan)
    write_json(paths[0]/"plan-sha256.json", {"sha256": file_hash(paths[0]/"plan.json")})
    return plan


def load_plan(path, settings):
    path = Path(path)
    if file_hash(path) != read(path.with_name("plan-sha256.json"))["sha256"]:
        raise ArenaProviderError("evidence_corruption")
    plan = read(path)
    if plan["armOrder"] != list(REPAIR_VERSIONS) or plan["intendedMatchesPerArm"] != 6:
        raise ArenaProviderError("configuration_failure")
    expected = contracts(settings, plan["source"])
    for version in REPAIR_VERSIONS:
        arm = plan["arms"][version]
        contract = dict(expected, repairVersion=version, experimentOverrides={"repairVersion": version})
        if arm["manifest"] != contract or arm["matches"] != [dict(contract, **s) for s in slots()]:
            raise ArenaProviderError("configuration_failure")
    if plan["initialSnapshot"] != ArenaSimulation().initial_snapshot:
        raise ArenaProviderError("configuration_failure")
    return plan


def verify_arm(directory, expected, ceiling):
    """Offline evidence verification, including manifests, pairing and accounting."""
    directory = Path(directory)
    if inventory(directory) != read(directory/"evidence-sha256.json"):
        raise ArenaProviderError("evidence_corruption")
    if read(directory/"manifest.json") != expected["manifest"]:
        raise ArenaProviderError("configuration_failure")
    summary = read(directory/"summary.json")
    for check in summary["preflight"]:
        if check.get("repair_version") != expected["manifest"]["repairVersion"] or check["requested_provider"] != "ollama" or check["fallback_used"]:
            raise ArenaProviderError("provider_mismatch")
        if check["provider_requests"] != len(check["attempts"]) or check["repair_requests"] or len(check["attempts"]) > 1:
            raise ArenaProviderError("request_accounting_defect")
    total = sum(r["provider_requests"] for r in summary["preflight"])
    if len(summary["matches"]) != 6:
        raise ArenaProviderError("evidence_corruption")
    for row, contract in zip(summary["matches"], expected["matches"]):
        if row["pair_id"] != contract["pair_id"]:
            raise ArenaProviderError("evidence_corruption")
        if row["status"] == "not_started":
            continue
        target = directory/row["pair_id"]
        if read(target/"manifest.json") != contract or not verify_match(target)["success"]:
            raise ArenaProviderError("replay_mismatch")
        result = read(target/"result.json")
        trace = read(target/"command-trace.json")
        if digest(trace["initial_snapshot"]) != contract["initialStateHash"]:
            raise ArenaProviderError("configuration_failure")
        turn_dirs = sorted((target/"turns").iterdir())
        if result["turns"] != [read(t/"turn.json") for t in turn_dirs] or any(read(t/"manifest.json") != contract for t in turn_dirs):
            raise ArenaProviderError("evidence_corruption")
        if row["status"] != result["status"] or row["error_category"] != result["error_category"]:
            raise ArenaProviderError("evidence_corruption")
        for turn in result["turns"]:
            for step in turn.get("steps", []):
                if step.get("repair_version") != contract["repairVersion"]:
                    raise ArenaProviderError("wrong_repair_version")
                if step["provider_requests"] != len(step["attempts"]) or step["repair_requests"] != max(0, len(step["attempts"])-1) or len(step["attempts"]) > 2:
                    raise ArenaProviderError("request_accounting_defect")
                total += step["provider_requests"]
        if read(target/"repair-metrics.json") != match_metrics(target):
            raise ArenaProviderError("evidence_corruption")
    if total != summary["requests"] or total > ceiling:
        raise ArenaProviderError("request_accounting_defect")
    metrics = [read(directory/r["pair_id"]/"repair-metrics.json") for r in summary["matches"] if r["status"] != "not_started"]
    expected_metrics = aggregate(metrics, total_requests=total,
        preflight=[a for r in summary["preflight"] for a in r["attempts"]],
        context=expected["manifest"]["providers"]["ollama"]["modelConfiguration"]["context_size"])
    if summary["metrics"] != expected_metrics:
        raise ArenaProviderError("evidence_corruption")
    return summary


def run_arm(plan_path, *, settings, repair_version, request_ceiling, output, provider_factory=create_arena_step_provider):
    plan_path = Path(plan_path)
    plan = load_plan(plan_path, settings)
    arm = plan["arms"][repair_version]
    output = Path(output).resolve()
    if str(output) != arm["output"] or request_ceiling != plan["requestCeilingPerArm"]:
        raise ValueError("output and ceiling must equal the frozen preparation")
    if output.exists():
        raise ValueError("immutable arm root already exists; never overwrite or resume")
    base_guard = frozen_guard(plan["source"], plan["settingsFileHash"], plan["auxiliarySource"])
    initial_plan_hash = file_hash(plan_path)
    previous = None
    if repair_version == REPAIR_V2:
        previous = plan["arms"][REPAIR_V1]
        control = verify_arm(Path(previous["output"]), previous, request_ceiling)
        if control["status"] == "hard_stop":
            raise ArenaProviderError(control["hard_stop"])
    sealed = {}
    provider = None
    in_preflight = False

    def guard():
        base_guard()
        current_source = source_manifest()
        if any(current_source[k] != plan["source"][k] for k in ("sourceRevision", "sourceDirty")):
            raise ArenaProviderError("source_mutation")
        if file_hash(plan_path) != initial_plan_hash or any(file_hash(p) != h for p, h in sealed.items()):
            raise ArenaProviderError("source_mutation")
        if provider is not None:
            profile = arm["manifest"]["providers"]["ollama"]
            if (provider.name != "ollama" or provider.configuration() != profile["modelConfiguration"] or
                    provider.prompt_version != STEP_PROMPT_VERSION or provider.schema_version != arm["manifest"]["planSchemaVersion"] or
                    provider.repair is not (not in_preflight)):
                raise ArenaProviderError("source_mutation")
            if provider.repair_version != repair_version:
                raise ArenaProviderError("source_mutation")

    guard()
    if previous:
        sealed.update({Path(previous["output"])/p: h for p, h in inventory(Path(previous["output"])).items()})
        sealed[Path(previous["output"])/"evidence-sha256.json"] = file_hash(Path(previous["output"])/"evidence-sha256.json")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/"manifest.json", arm["manifest"])
    write_json(output/"source-before.json", plan["source"])
    sealed.update({output/p: file_hash(output/p) for p in ("manifest.json", "source-before.json")})
    report = dict(status="complete", hard_stop=None, preflight=[], matches=[], requests=0,
                  request_ceiling=request_ceiling, repair_version=repair_version)
    budget = RequestBudget(request_ceiling, guard)
    stop = None
    try:
        provider = provider_factory(settings, "ollama", repair_version=repair_version)
        guard()
        provider.before_request = budget.take
        in_preflight = True
        _, check = checked_step(provider, "ollama", build_observation(ArenaSimulation().state, version=OBSERVATION_V2), preflight=True)
        in_preflight = False
        report["preflight"].append(check)
        if check.get("repair_version") != repair_version:
            stop = "wrong_repair_version"
        elif check["fallback_used"] or check["actual_provider"] not in (None, "ollama"):
            stop = "provider_mismatch"
        elif not check["success"]:
            stop = check["error_category"]
        if budget.used != check["provider_requests"]:
            stop = "request_accounting_defect"
        for contract in arm["matches"]:
            pair_id = contract["pair_id"]
            if stop or budget.used >= request_ceiling:
                report["matches"].append(dict(pair_id=pair_id, status="not_started", reason=stop or "request_ceiling"))
                continue
            guard()
            before = budget.used
            target = output/pair_id
            result = run_match(target, contract["assignments"], {"ollama": provider}, contract, turns=MAX_TURNS, guard=guard)
            report["matches"].append(dict(pair_id=pair_id, status=result["status"], error_category=result["error_category"]))
            if result["error_category"] in STOP_CATEGORIES:
                stop = result["error_category"]
            steps = [s for t in result["turns"] for s in t.get("steps", [])]
            if any(s.get("repair_version") != repair_version for s in steps):
                stop = "wrong_repair_version"
            if budget.used-before != sum(s["provider_requests"] for s in steps):
                stop = "request_accounting_defect"
            if not result["verification"]["success"]:
                stop = "replay_mismatch"
            if result["error_category"] == "request_ceiling":
                stop = "request_ceiling"
            write_json(target/"repair-metrics.json", match_metrics(target))
            sealed.update({target/p: h for p, h in inventory(target).items()})
            report["requests"] = budget.used
            write_json(output/"summary.json", report)
            guard()
    except ArenaProviderError as error:
        stop = error.category
    # Ordinary failed repairs remain outcomes; only integrity stops block the other arm.
    for contract in arm["matches"][len(report["matches"]):]:
        report["matches"].append(dict(pair_id=contract["pair_id"], status="not_started", reason=stop))
    try:
        guard()
    except ArenaProviderError as error:
        stop = error.category
    report.update(requests=budget.used, status="hard_stop" if stop in STOP_CATEGORIES else "stopped" if stop else "complete",
                  hard_stop=stop if stop in STOP_CATEGORIES else None, stop_reason=stop)
    measured = [read(output/m["pair_id"]/"repair-metrics.json") for m in report["matches"] if m["status"] != "not_started"]
    report["metrics"] = aggregate(measured, total_requests=budget.used,
        preflight=[a for r in report["preflight"] for a in r["attempts"]], context=settings.ollama.context_size)
    write_json(output/"source-after.json", source_manifest())
    write_json(output/"summary.json", report)
    write_json(output/"evidence-sha256.json", inventory(output))
    verify_arm(output, arm, request_ceiling)
    return report


def compare(plan_path, *, settings):
    plan = load_plan(plan_path, settings)
    reports = {v: verify_arm(Path(plan["arms"][v]["output"]), plan["arms"][v], plan["requestCeilingPerArm"]) for v in REPAIR_VERSIONS}
    target = Path(plan["comparisonOutput"])
    target.mkdir(parents=True, exist_ok=False)
    result = dict(arms={v: r["metrics"] for v, r in reports.items()},
                  paired_outcomes=[dict(pair_id=f"pair-{i+1:02d}", **{v: reports[v]["matches"][i] for v in REPAIR_VERSIONS}) for i in range(6)],
                  promotion="Separate human decision required; no automatic promotion.")
    write_json(target/"comparison.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="offline; no provider constructed")
    for name in ("output", "v1-output", "v2-output", "comparison-output"):
        prep.add_argument("--"+name, type=Path, required=True)
    prep.add_argument("--request-ceiling", type=int, required=True)
    run = sub.add_parser("run", help="LIVE: requires separate user authorization")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--repair-version", choices=REPAIR_VERSIONS, required=True)
    run.add_argument("--request-ceiling", type=int, required=True)
    run.add_argument("--output", type=Path, required=True)
    comparison = sub.add_parser("compare", help="offline evidence verification and comparison")
    comparison.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    settings = load_settings()
    if args.command == "prepare":
        prepare(args.output, settings=settings, v1_output=args.v1_output, v2_output=args.v2_output,
                comparison_output=args.comparison_output, request_ceiling=args.request_ceiling)
    elif args.command == "run":
        report = run_arm(args.plan, settings=settings, repair_version=args.repair_version,
                         request_ceiling=args.request_ceiling, output=args.output)
        print(report["status"], report["requests"])
        return 1 if report["status"] == "hard_stop" else 0
    else:
        compare(args.plan, settings=settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
