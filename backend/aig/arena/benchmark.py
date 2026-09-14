"""Controlled Arena matches/probes. Offline heuristic is the explicit default."""

import argparse
import json
from pathlib import Path

from aig.ai.benchmark import write_json
from aig.arena.ai.repair import REPAIR_V1, REPAIR_VERSIONS
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.factory import PROVIDER_NAMES, create_arena_turn_provider
from aig.arena.ai.observation import (ArenaObservation, build_observation, OBSERVATION_VERSION,
                                      resolve_observation_version)
from aig.arena.ai.prompts import PROMPT_VERSION, resolve_prompt
from aig.arena.benchmark_metrics import inference_metrics, trial_metrics
from aig.arena.benchmark_provider import checked_plan
from aig.arena.benchmark_versions import (BENCHMARK_VERSION, frozen_probe, manifest, probe_set, source_manifest)
from aig.arena.commands import ArenaFireball, arena_fireball_affected_units
from aig.arena.prompt_metrics import starting_legality
from aig.arena.replay import ArenaSimulation, replay, TRACE_VERSION
from aig.arena.snapshots import canonical_json, digest, to_snapshot
from aig.arena.state import Bonus, integer
from aig.settings import Settings, load_settings


def write_rows(path, rows):
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def verify_trial(directory):
    """Verify persisted evidence, including every command result and turn AP boundary."""
    try:
        saved_manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        observation_version = resolve_observation_version(saved_manifest.get("observationVersion", OBSERVATION_VERSION))
        initial = json.loads((directory / "initial-snapshot.json").read_text(encoding="utf-8"))
        final = json.loads((directory / "final-snapshot.json").read_text(encoding="utf-8"))
        commands = read_rows(directory / "commands.jsonl")
        plans = read_rows(directory / "plans.jsonl")
        trace = dict(environment="arena", schema_version=TRACE_VERSION, initial_snapshot=initial, entries=commands)
        reproduced = replay(trace)
        reproduced.state.validate()
        if to_snapshot(reproduced.state) != final:
            raise ValueError("final_state")
        for row in plans:
            entries = commands[row["command_start"]:row["command_end"]]
            if ([e["command"] for e in entries] != row["commands_executed"]
                    or sum(e["ap_used"] for e in entries) != row["ap_spent"]
                    or row["ap_available"] != row["ap_spent"] + row["ap_unused"]):
                raise ValueError("ap_accounting")
        # Independent plan execution checks grouping, observations, truncation and terminal AP.
        from aig.arena.ai.contracts import ArenaTurnPlan
        from aig.arena.snapshots import from_snapshot
        chosen = ArenaSimulation(from_snapshot(initial))
        observations = read_rows(directory / "observations.jsonl")
        for index, row in enumerate(plans):
            observation = build_observation(chosen.state, version=observation_version)
            if observation.hash != row["observation_hash"] or observation.to_dict() != observations[index]["observation"]:
                raise ValueError("observation")
            result = execute_arena_turn(chosen.state, ArenaTurnPlan.from_dict(row["plan"]), execute_command=chosen.execute).to_dict()
            if any(result[key] != row[key] for key in result):
                raise ValueError("plan_execution")
        if chosen.trace() != trace:
            raise ValueError("plan_commands")
        return dict(success=True, final_state_hash=digest(final), command_trace_hash=digest(trace),
                    winner=reproduced.state.winner_player_id,
                    ap_executed=sum(e["ap_used"] for e in commands), state_valid=True)
    except Exception:
        return dict(success=False, error_category="replay_mismatch")


def run_trial(*, directory, assignments, providers, experiment, turns, probe=None):
    directory.mkdir(parents=True, exist_ok=False)
    sim = ArenaSimulation(frozen_probe(probe) if probe else None)
    observations, plans, inference, positions = [], [], [], []
    run_manifest = dict(experiment, assignments=assignments, probe=probe,
                        initialStateHash=digest(sim.initial_snapshot), maxGlobalTurns=turns)
    write_json(directory / "manifest.json", run_manifest)
    write_json(directory / "initial-snapshot.json", sim.initial_snapshot)
    failure = None
    while sim.state.winner_player_id is None and (not plans if probe else sim.state.turn < turns):
        state = sim.state
        player, turn = state.active_player_id, state.turn
        name = assignments[player]
        observation = build_observation(state, version=experiment.get("observationVersion", OBSERVATION_VERSION))
        # This roundtrip regenerates legal actions through authoritative Arena queries.
        ArenaObservation.from_dict(observation.to_dict())
        observations.append(dict(turn=turn, player_id=player, observation_hash=observation.hash,
                                 observation=observation.to_dict()))
        plan, call = checked_plan(providers[name], name, observation)
        call.update(turn=turn, player_id=player, observation_hash=observation.hash,
                    observation_version=observation.version,
                    prompt_version=experiment["promptVersion"], schema_version=PLAN_SCHEMA_VERSION)
        inference.append(call)
        if plan is None:
            failure = call["error_category"]
            break
        start = len(sim.trace()["entries"])
        occupancy = {p.id: {bonus.value: sum(u.owner_id == p.id and u.status.value == "active"
                     and state.board.at(u.position).bonus is bonus for u in state.units.values())
                     for bonus in Bonus} for p in state.players}

        def execute(command):
            unit = state.units.get(getattr(command, "unit_id", None))
            bonus = state.board.at(unit.position).bonus if unit else None
            kind = type(command).__name__
            facts = dict(player_id=player, power_attacks=int(bonus is Bonus.POWER and kind in
                         ("ArenaAttack", "ArenaShieldBash", "ArenaSnipe", "ArenaFireball")),
                         siege_core_attacks=int(bonus is Bonus.SIEGE and kind == "ArenaAttack"
                         and command.target_id in state.cores), ward_actions=int(bonus is Bonus.WARD),
                         fireball_friendly_targets_hit=sum(state.units[uid].owner_id == player for uid in
                         arena_fireball_affected_units(state, command.target_position))
                         if type(command) is ArenaFireball else 0)
            result = sim.execute(command)
            positions.append(facts)
            return result

        result = execute_arena_turn(state, plan, execute_command=execute).to_dict()
        result.update(turn=turn, observation_hash=observation.hash, provider_type=name,
                      observation_version=observation.version,
                      prompt_version=experiment["promptVersion"], schema_version=PLAN_SCHEMA_VERSION,
                      model_profile=experiment["providers"][name], ap_planned=plan.ap_cost,
                      static_validation=True, repair_count=call["repair_requests"],
                      inference_index=len(inference) - 1,
                      actions_executed=sum(a["executed"] for a in result["actions_attempted"]),
                      command_start=start, command_end=len(sim.trace()["entries"]),
                      premium_tile_occupancy=occupancy)
        result["starting_legality"] = starting_legality(observation, plan)
        plans.append(result)
    trace = sim.trace()
    final = to_snapshot(sim.state)
    for filename, rows in (("observations", observations), ("plans", plans), ("commands", trace["entries"]),
                           ("inference", inference), ("positions", positions)):
        write_rows(directory / (filename + ".jsonl"), rows)
    write_json(directory / "final-snapshot.json", final)
    verification = verify_trial(directory)
    write_json(directory / "verification.json", verification)
    failure = failure or (None if verification["success"] else "replay_mismatch")
    metrics = trial_metrics(sim, plans, inference, positions)
    outcome = "invalid" if failure else "victory" if sim.state.winner_player_id else "probe_complete" if probe else "turn_limit"
    # Behavioral plan hashes deliberately exclude profile/provenance, repairs and telemetry.
    behavioral_plans = [{k: p[k] for k in ("turn", "player_id", "observation_hash", "plan",
                        "ap_available", "ap_spent", "ap_unused", "invalid_action", "truncation_reason",
                        "commands_executed")} for p in plans]
    hashes = dict(initial_state=digest(sim.initial_snapshot), final_state=digest(final),
                  observations=digest(observations), plans=digest([p["plan"] for p in plans]),
                  plan_trace=digest(behavioral_plans), commands=digest([e["command"] for e in trace["entries"]]),
                  command_trace=digest(trace), player_turns=digest([{k: p[k] for k in
                  ("turn", "player_id", "ap_available", "ap_spent", "ap_unused")} for p in plans]))
    by_provider = {name: inference_metrics([r for r in inference if r["requested_provider"] == name],
                   (experiment["providers"][name]["modelConfiguration"] or {}).get("context_size"))
                   for name in sorted(set(assignments.values()))}
    result = dict(directory=str(directory), probe=probe, assignments=assignments, outcome=outcome,
                  valid=failure is None, error_category=failure, pureProviderRun=all(r["success"] for r in inference),
                  requestedProvider=assignments, actualProvider=sorted({r["actual_provider"] for r in inference
                  if r["actual_provider"]}), providerRequests=sum(r["provider_requests"] for r in inference),
                  repairRequests=sum(r["repair_requests"] for r in inference),
                  fallbackCount=sum(r["fallback_used"] for r in inference),
                  metrics=metrics, inference=by_provider, hashes=hashes, verification=verification)
    result["starting_legality"] = [p["starting_legality"] for p in plans]
    if probe:
        result["probe_outcome"] = dict(action_sequence=plans[0]["plan"]["actions"] if plans else [],
            immediate_victory=sim.state.winner_player_id == sim.initial_snapshot["active_player_id"],
            ally_active=bool(sim.state.units.get("ally") and sim.state.units["ally"].status.value == "active")
            if probe == "revive_decision" else None,
            objective_achieved=(sim.state.winner_player_id == sim.initial_snapshot["active_player_id"])
            if probe in ("winning_core_line", "team_elimination") else
            bool(sim.state.units.get("ally") and sim.state.units["ally"].status.value == "active")
            if probe == "revive_decision" else None)
    write_json(directory / "result.json", result)
    return result


def render_report(report):
    lines = ["# Arena benchmark v1", "", f"Status: {report['status']}. Trials started: {report['trialsStarted']}.",
             "", "No aggregate tactical score. Invalid trials are excluded from provider comparisons.",
             "", "## Preflight / cold warmup", "",
             "| Provider | Passed | Seconds | Requests |", "| --- | --- | ---: | ---: |"]
    for row in report["preflight"]:
        lines.append(f"| {row['requested_provider']} | {row['success']} | {row['wall_clock_seconds']:.6f} | {row['provider_requests']} |")
    lines += ["", "## Match outcomes and AP", "", "| Trial | Blue / Red | Result | Winner | Player turns | AP planned / executed / unused |",
              "| --- | --- | --- | --- | ---: | --- |"]
    for row in report["runs"]:
        if row["probe"]:
            continue
        players = row["metrics"]["players"].values()
        ap = " / ".join(str(sum(p[k] for p in players)) for k in ("ap_planned", "ap_executed", "ap_unused"))
        lines.append(f"| {Path(row['directory']).name} | {row['assignments']['blue']} / {row['assignments']['red']} | {row['outcome']} | {row['metrics']['winner']} | {row['metrics']['player_turns']} | {ap} |")
    lines += ["", "## Combat, abilities and plan validity", "", "| Trial / side | Damage / friendly / healing | Downs / revives / finishes | Core damage | Truncated / zero-action | Actions |",
              "| --- | --- | --- | ---: | --- | --- |"]
    for row in report["runs"]:
        for side, p in row["metrics"]["players"].items():
            lines.append(f"| {row['probe'] or Path(row['directory']).name} / {side} | {p['damage_dealt']} / {p['friendly_fire_damage']} / {p['healing_done']} | {p['units_downed']} / {p['units_revived']} / {p['units_finished']} | {p['core_damage']} | {p['truncated_turns']} / {p['zero_action_turns']} | `{json.dumps(p['actions_by_type'], sort_keys=True)}` |")
    lines += ["", "## Provider latency and tokens (valid trials only)", "", "Preflight is excluded. All trial attempts, including repairs and slow requests, remain included.",
              "p95 uses nearest rank and requires at least 20 samples. Durations from Ollama are nanoseconds."]
    for name, metrics in report["inference"].items():
        lines += ["", f"### {name}", "", "```json", json.dumps(metrics, indent=2, sort_keys=True), "```"]
    lines += ["", "## Probe decisions", "", "Rows with the same probe name share an identical starting observation; repeats remain visible.",
              "", "| Probe | Provider | Plan | Objective achieved | Final state hash |", "| --- | --- | --- | --- | --- |"]
    for row in report["runs"]:
        if row["probe"]:
            lines.append(f"| {row['probe']} | {row['assignments']['blue']} | `{json.dumps(row['probe_outcome']['action_sequence'], sort_keys=True)}` | {row['probe_outcome']['objective_achieved']} | `{row['hashes']['final_state']}` |")
    lines += ["", "Cost is not estimated. Repeated deterministic games measure reproducibility, not statistical playing strength.",
              "Finish cannot newly win under immediate zero-active victory. No subjective objective is assigned to other probes.",
              "Exact metrics, end states, errors, telemetry and offline replay checks are in each trial's artifacts."]
    return "\n".join(lines) + "\n"


def benchmark(*, output, mode="matches", blue_provider="heuristic", red_provider="heuristic",
              games=4, turns=100, probe="all", probe_trials=4, side_swap=False, preflight_only=False,
              settings=None, provider_factory=create_arena_turn_provider, prompt_version=None,
              observation_version=None, control_mode="full-turn", pricing=None, request_ceiling=None, repair_version=REPAIR_V1):
    if control_mode == "stepwise":
        from aig.arena.ai.stepwise import STEP_PROMPT_VERSION, create_arena_step_provider
        from aig.arena.stepwise_benchmark import benchmark_stepwise
        if mode != "probes" or side_swap or red_provider != "heuristic":
            raise ValueError("stepwise benchmark v2 supports probes with --blue-provider only")
        if prompt_version not in (None, STEP_PROMPT_VERSION) or observation_version not in (None, "arena-observation-v2"):
            raise ValueError("stepwise requires arena-step-prompt-v1 and arena-observation-v2")
        return benchmark_stepwise(output=output, blue_provider=blue_provider, probe=probe,
            probe_trials=probe_trials, settings=settings, preflight_only=preflight_only,
            provider_factory=create_arena_step_provider if provider_factory is create_arena_turn_provider else provider_factory,
            pricing=pricing, request_ceiling=request_ceiling, repair_version=repair_version)
    if control_mode != "full-turn" or pricing is not None or request_ceiling is not None or repair_version != REPAIR_V1:
        raise ValueError("invalid full-turn control options")
    prompt_version, _ = resolve_prompt(prompt_version)
    observation_version = resolve_observation_version(observation_version)
    if mode not in ("matches", "probes", "all") or any(n not in PROVIDER_NAMES for n in (blue_provider, red_provider)):
        raise ValueError("invalid benchmark mode/provider")
    for value, name in ((games, "games"), (turns, "turns"), (probe_trials, "probe_trials")):
        integer(value, name, 1)
    probes = list(probe_set()["probes"]) if probe == "all" else [probe]
    if any(p not in probe_set()["probes"] for p in probes):
        raise ValueError("unknown Arena probe")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be new or empty; existing evidence is never overwritten")
    output.mkdir(parents=True, exist_ok=True)
    settings = settings if settings is not None else Settings()
    names = sorted(set((blue_provider, red_provider) if mode != "probes" else (blue_provider,)))
    experiment = manifest(names, settings, source_manifest(), prompt_version=prompt_version,
                          observation_version=observation_version)
    report = dict(benchmarkVersion=BENCHMARK_VERSION, experiment=experiment, mode=mode,
                  strictProvider=True, games=games, sideSwap=side_swap, probeTrials=probe_trials,
                  plannedMatchTrials=games * (2 if side_swap else 1) if mode != "probes" else 0,
                  plannedProbeTrials=len(probes) * probe_trials * len(names) if mode != "matches" else 0,
                  preflight=[], trialsStarted=0, status="complete", runs=[], inference={})
    providers = {}
    for name in names:
        try:
            # Preserve the existing V1 injected-factory interface. Overrides must
            # be supported at construction; never mutate a provider's prompt.
            provider = (provider_factory(settings, name, prompt_version=prompt_version)
                        if prompt_version != PROMPT_VERSION and name != "heuristic"
                        else provider_factory(settings, name))
            providers[name] = provider
            # Assert settings identity for injected providers that expose configuration.
            if hasattr(provider, "configuration") and provider.configuration() != experiment["providers"][name]["modelConfiguration"]:
                raise ValueError("configuration mismatch")
            if name != "heuristic" and prompt_version != PROMPT_VERSION and not hasattr(provider, "prompt_version"):
                raise ValueError("provider must expose its selected prompt version")
            for attribute, expected in (("prompt_version", prompt_version), ("schema_version", PLAN_SCHEMA_VERSION)):
                if hasattr(provider, attribute) and getattr(provider, attribute) != expected:
                    raise ValueError("provider contract version mismatch")
            if name == "heuristic":
                continue
            _, check = checked_plan(provider, name, build_observation(ArenaSimulation().state,
                                   version=observation_version), preflight=True)
        except Exception:
            check = dict(requested_provider=name, actual_provider=None, success=False,
                         error_category="configuration_failure", wall_clock_seconds=0,
                         provider_requests=0, repair_requests=0, fallback_used=False, attempts=[])
        check.update(prompt_version=prompt_version, observation_version=observation_version,
                     schema_version=PLAN_SCHEMA_VERSION)
        report["preflight"].append(check)
        if not check["success"]:
            report["status"] = "preflight_failed"
    schedule = []
    if report["status"] == "complete" and not preflight_only:
        if mode != "probes":
            for game in range(games):
                assignments = dict(blue=blue_provider, red=red_provider)
                schedule.append((output / "runs" / f"run-{len(schedule) + 1:03d}", assignments, None))
                if side_swap:
                    schedule.append((output / "runs" / f"run-{len(schedule) + 1:03d}",
                                     dict(blue=red_provider, red=blue_provider), None))
        if mode != "matches":
            for name in names:
                for selected in probes:
                    for trial in range(probe_trials):
                        schedule.append((output / "probes" / selected / name / f"run-{trial + 1:03d}",
                                         dict(blue=name, red=name), selected))
    for directory, assignments, selected in schedule:
        report["trialsStarted"] += 1
        row = run_trial(directory=directory, assignments=assignments, providers=providers,
                        experiment=experiment, turns=turns, probe=selected)
        report["runs"].append(row)
        if not row["valid"]:
            report["status"] = "trial_failed"
            break
    valid_calls = [call for run in report["runs"] if run["valid"]
                   for call in read_rows(Path(run["directory"]) / "inference.jsonl")]
    report["inference"] = {name: inference_metrics([r for r in valid_calls if r["requested_provider"] == name],
        (experiment["providers"][name]["modelConfiguration"] or {}).get("context_size")) for name in names}
    report["inferenceByMode"] = {kind: {name: inference_metrics([
        call for run in report["runs"] if run["valid"] and bool(run["probe"]) == (kind == "probes")
        for call in read_rows(Path(run["directory"]) / "inference.jsonl") if call["requested_provider"] == name],
        (experiment["providers"][name]["modelConfiguration"] or {}).get("context_size")) for name in names}
        for kind in ("matches", "probes")}
    report["validTrials"] = sum(r["valid"] for r in report["runs"])
    write_json(output / "summary.json", report)
    (output / "report.md").write_text(render_report(report), encoding="utf-8")
    return report


def main(argv=None, *, provider_factory=create_arena_turn_provider):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("matches", "probes", "all"), default="matches")
    parser.add_argument("--blue-provider", choices=PROVIDER_NAMES, default="heuristic", help="also selects provider in probes mode")
    parser.add_argument("--red-provider", choices=PROVIDER_NAMES, default=None, help="matches/all only")
    parser.add_argument("--games", type=int, default=4, help="4 matches; side swap doubles this count")
    parser.add_argument("--turns", type=int, default=100, help="completed global rounds, at most two player turns each")
    parser.add_argument("--probe", choices=("all", *probe_set()["probes"]), default="all")
    parser.add_argument("--probe-trials", type=int, default=4)
    parser.add_argument("--control-mode", choices=("full-turn", "stepwise"), default="full-turn")
    parser.add_argument("--repair-version", choices=REPAIR_VERSIONS, default=REPAIR_V1)
    parser.add_argument("--pricing", type=Path, help="stepwise only: explicit dated USD/million token pricing JSON")
    parser.add_argument("--request-ceiling", type=int, help="stepwise only: reject schedules exceeding this total bound")
    parser.add_argument("--prompt-version", default=None,
                        help="Arena prompt registry version; default arena-turn-prompt-v1")
    parser.add_argument("--observation-version", default=None,
                        help="Arena observation contract; default arena-observation-v1")
    parser.add_argument("--side-swap", action="store_true")
    parser.add_argument("--strict-provider", action="store_true", default=True, help="always enforced; no fallback mode")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "probes" and (args.red_provider is not None or args.side_swap):
        parser.error("probes mode uses --blue-provider; red provider/side swaps apply to matches/all")
    if min(args.games, args.turns, args.probe_trials) < 1:
        parser.error("game, turn and probe trial counts must be positive")
    args.red_provider = args.red_provider or "heuristic"
    del args.strict_provider
    match_count = args.games * (2 if args.side_swap else 1) if args.mode != "probes" else 0
    probe_count = (len(probe_set()["probes"]) if args.probe == "all" else 1) * args.probe_trials * (
        len({args.blue_provider, args.red_provider}) if args.mode == "all" else 1) if args.mode != "matches" else 0
    print(f"Requested: {0 if args.preflight_only else match_count} matches, {0 if args.preflight_only else probe_count} probes; strict provider purity.")
    try:
        if args.pricing is not None:
            args.pricing = json.loads(args.pricing.read_text(encoding="utf-8"))
        result = benchmark(**vars(args), settings=load_settings(), provider_factory=provider_factory)
    except ValueError as error:
        parser.error(str(error))
    print(f"{result['status']}: {result['validTrials']}/{result['trialsStarted']} valid trials. Report: {args.output / 'report.md'}")
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
