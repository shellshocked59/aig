"""Offline facts from verified full-match traces; no model or gameplay changes."""

from collections import Counter
from pathlib import Path
import json

from aig.arena.benchmark_metrics import distribution
from aig.arena.benchmark_provider import METRIC_KEYS
from aig.arena.ai.observation import ArenaObservation, simulation_state
from aig.arena.snapshots import digest, state_hash, canonical_json

INVALID = {"malformed_json", "schema_validation", "ap_budget", "invalid_reference", "invalid_ability"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ratio(n, d):
    return n / d if d else None


def telemetry(attempts, context):
    return dict(
        wall_latency_seconds=distribution(a["wall_clock_seconds"] for a in attempts),
        telemetry={k: distribution(a["metrics"].get(k) for a in attempts) for k in METRIC_KEYS},
        input_occupancy=distribution(a["metrics"]["prompt_eval_count"] / context for a in attempts
                                    if "prompt_eval_count" in a["metrics"]),
        output_occupancy=distribution(a["metrics"]["eval_count"] / context for a in attempts
                                     if "eval_count" in a["metrics"]),
        context_occupancy=distribution((a["metrics"]["prompt_eval_count"] + a["metrics"]["eval_count"]) / context
                                      for a in attempts if {"prompt_eval_count", "eval_count"} <= a["metrics"].keys()))


def failure_kind(step):
    """Use only sanitized evidence; unavailable/redacted references stay unknown."""
    attempts = step["attempts"]
    if len(attempts) < 2 or step["success"]:
        return None
    first = attempts[0].get("rejected_decision", {})
    last = attempts[1].get("rejected_decision", {})
    if attempts[1]["error_category"] != "invalid_reference":
        return attempts[1]["error_category"]
    a, b = first.get("validation", {}), last.get("validation", {})
    if a.get("field_path") != b.get("field_path"):
        return "different_catalog_violation"
    values = (a.get("rejected_value"), b.get("rejected_value"))
    if any(v is None or "REDACTED" in str(v) for v in values):
        return "reference_comparison_unavailable"
    return "repeated_bad_reference" if values[0] == values[1] else "new_bad_reference"


def match_metrics(directory):
    directory = Path(directory)
    result, manifest = read(directory/"result.json"), read(directory/"manifest.json")
    trace, final = read(directory/"command-trace.json"), read(directory/"final-snapshot.json")
    side = manifest["qwenSide"]
    turns = [t for t in result["turns"] if t["player_id"] == side]
    steps = [s for t in turns for s in t["steps"]]
    successful = [t for t in turns if t["error_category"] is None]
    events = []
    for turn_number, turn in enumerate(result["turns"], 1):
        for s in turn.get("steps", []):
            if not s["repair_requests"]:
                continue
            obs = s["observation"]
            action = s["selected_action"]
            event = dict(player_turn=turn_number, global_turn=s["turn"], step_index=s["step_index"],
                ap_remaining=s["ap_before"], legal_action_count=s["legal_action_count"],
                nonmove_legal_action_count=sum(a["type"] != "move" for a in obs["legal_actions"]),
                teams={k: obs[k] for k in ("own_team", "enemy_team")}, terminal=s["terminal"] is not None,
                winner=s["terminal"],
                repair_version=s["repair_version"], rejected= [a.get("rejected_decision") for a in s["attempts"]],
                repaired_decision=s["decision"], repaired_outcome="succeeded" if s["success"] else "failed",
                failure_kind=failure_kind(s), repaired_endturn=s["repair_succeeded"] and s["explicit_end_turn"],
                ap_abandoned=s["ap_before"] if s["repair_succeeded"] and s["explicit_end_turn"] else 0,
                action_type=action["type"] if action else None,
                exact_catalog_membership=s["selected_current_legal"],
                authoritative_execution_succeeded=s["command_index"] is not None and s["execution_error"] is None,
                ap_cost=s["ap_before"]-s["ap_after"] if action else 0,
                resulting_ap=s["ap_after"], resulting_state_hash=s["resulting_state_hash"])
            events.append(event)
    initial_invalid = [i for i, s in enumerate(steps) if s["attempts"] and s["attempts"][0]["error_category"] in INVALID]
    fatal = next((s for s in reversed(steps) if not s["success"]), None)
    initial = [s["attempts"][0] for s in steps if s["attempts"]]
    repairs = [a for s in steps for a in s["attempts"][1:]]
    entries = [e for e in trace["entries"] if e["command"]["actor_id"] == side]
    mechanics = result["mechanical_metrics"]["players"][side]
    teams = {p: dict(core_hp=next(c["hp"] for c in final["cores"] if c["owner_id"] == p),
                    active=sum(u["owner_id"] == p and u["status"] == "active" for u in final["units"]),
                    downed=sum(u["owner_id"] == p and u["status"] == "downed" for u in final["units"]),
                    removed=sum(u["owner_id"] == p for u in trace["initial_snapshot"]["units"])
                            - sum(u["owner_id"] == p for u in final["units"])) for p in ("blue", "red")}
    return dict(pair_id=manifest["pair_id"], side=side, status=result["status"], error_category=result["error_category"],
        winner=result["winner"], qwen_win=result["winner"] == side,
        terminal_mechanism=result["terminal_mechanism"], global_turns=result["global_turns"],
        player_turns=result["player_turns"], teams=teams, stopping_state_hash=digest(final),
        decisions=len(initial), decision_boundaries=len(steps), first_response_valid=sum(a["error_category"] is None for a in initial),
        first_response_invalid=len(initial_invalid), first_response_other_failures=sum(a["error_category"] is not None and a["error_category"] not in INVALID for a in initial),
        total_invalid_responses=sum(a["error_category"] in INVALID for a in initial+repairs),
        eventual_decision_success=sum(s["success"] for s in steps),
        repairs_attempted=len(repairs), repairs_successful=sum(s["repair_succeeded"] for s in steps),
        repairs_failed=sum(s["repair_requests"] > 0 and not s["success"] for s in steps),
        initial_failure_taxonomy=dict(Counter(a["error_category"] for a in initial if a["error_category"])),
        repair_failure_taxonomy=dict(Counter(a["error_category"] for a in repairs if a["error_category"])),
        decisions_before_first_invalid=initial_invalid[0] if initial_invalid else None,
        fatal_boundary=dict(turn=fatal["turn"], step=fatal["step_index"], ap=fatal["ap_before"],
                            observation_hash=fatal["observation_hash"],
                            state_hash=state_hash(simulation_state(ArenaObservation(canonical_json(fatal["observation"])))),
                            decisions_before_fatal=len(initial)-1) if fatal else None,
        repair_events=events, requests=len(initial)+len(repairs), qwen_turns=len(turns),
        successful_turns=[dict(ap_available=t["ap_available"], ap_executed=t["ap_executed"], ap_unused=t["ap_unused"],
                              normal_endturn=any(s["explicit_end_turn"] and not s["repair_requests"] for s in t["steps"]),
                              repaired_endturn=any(s["explicit_end_turn"] and s["repair_succeeded"] for s in t["steps"])) for t in successful],
        provider_latency_seconds=sum(t["provider_latency_seconds"] for t in turns),
        turn_latency_seconds=[t["provider_latency_seconds"] for t in turns], initial_attempts=initial, repair_attempts=repairs,
        action_distribution=dict(Counter(e["command"]["type"] for e in entries if e["command"]["type"] != "arena_end_turn")),
        tactical=dict(unit_damage=mechanics["damage_dealt"]-mechanics["core_damage"], core_damage=mechanics["core_damage"],
                      finishes=mechanics["units_finished"], revives=mechanics["units_revived"]))


def aggregate(matches, *, total_requests, preflight=(), context=4096):
    completed = [m for m in matches if m["status"] == "completed"]
    failed = [m for m in matches if m["status"] == "failed"]
    turns = [t for m in matches for t in m["successful_turns"]]
    events = [e for m in matches for e in m["repair_events"]]
    ends = [e for e in events if e["repaired_endturn"]]
    repaired_actions = [e for e in events if e["action_type"] and e["authoritative_execution_succeeded"]]
    initial = [a for m in matches for a in m["initial_attempts"]]
    repair = [a for m in matches for a in m["repair_attempts"]]
    normal = [t["normal_endturn"] for t in turns]
    total = lambda key: sum(m[key] for m in matches)
    return dict(intended_matches=6, started_matches=len(matches), completed_matches=len(completed),
        provider_failed_matches=sum(m["error_category"] not in {"source_mutation", "provider_mismatch", "catalog_execution_defect", "replay_mismatch", "controller_safety_bound", "configuration_failure"} for m in failed),
        turn_limit_matches=sum(m["status"] == "turn_limit" for m in matches),
        request_ceiling_matches=sum(m["status"] == "request_ceiling" for m in matches), completion_rate=len(completed)/6,
        **{k: total(k) for k in ("decisions", "first_response_valid", "first_response_invalid", "first_response_other_failures", "total_invalid_responses",
                               "eventual_decision_success", "repairs_attempted", "repairs_successful", "repairs_failed")},
        first_response_invalid_rate=ratio(total("first_response_invalid"), total("decisions")),
        eventual_decision_reliability=ratio(total("eventual_decision_success"), total("decisions")),
        repair_success_rate=ratio(total("repairs_successful"), total("repairs_attempted")),
        REPAIR_ENDTURN_COUNT=len(ends), REPAIR_ENDTURN_AP_ABANDONED=sum(e["ap_abandoned"] for e in ends),
        REPAIR_ENDTURN_WITH_NONMOVE_ACTIONS_AVAILABLE=sum(e["nonmove_legal_action_count"] > 0 for e in ends),
        repaired_action_count=len(repaired_actions), repaired_action_distribution=dict(Counter(e["action_type"] for e in repaired_actions)),
        ap_available=sum(t["ap_available"] for t in turns), ap_unused=sum(t["ap_unused"] for t in turns),
        ap_executed=distribution(t["ap_executed"] for t in turns),
        full_5_ap_rate=ratio(sum(t["ap_executed"] == 5 for t in turns), len(turns)),
        at_least_4_ap_rate=ratio(sum(t["ap_executed"] >= 4 for t in turns), len(turns)),
        at_most_2_ap_rate=ratio(sum(t["ap_executed"] <= 2 for t in turns), len(turns)),
        normal_endturn_rate=ratio(sum(normal), len(turns)), repaired_endturn_rate=ratio(sum(t["repaired_endturn"] for t in turns), len(turns)),
        qwen_wins=sum(m["qwen_win"] for m in completed), heuristic_wins=sum(not m["qwen_win"] for m in completed),
        repair_survival={"zero_repairs": sum(not m["repairs_attempted"] for m in matches),
                         "with_repairs": sum(m["repairs_attempted"] > 0 for m in matches),
                         "completed_with_repairs": sum(m["repairs_attempted"] > 0 for m in completed),
                         "failed_with_repairs": sum(m["repairs_attempted"] > 0 for m in failed)},
        total_requests=total_requests, requests_completed=sum(m["requests"] for m in completed),
        requests_failed=sum(m["requests"] for m in failed),
        requests_per_completed_match=ratio(total_requests, len(completed)),
        completed_match_only_requests_per_match=ratio(sum(m["requests"] for m in completed), len(completed)),
        requests_per_qwen_turn=ratio(total("requests"), total("qwen_turns")),
        repairs_fraction_of_requests=ratio(len(repair), total_requests),
        normal_decision_telemetry=telemetry(initial, context), repair_telemetry=telemetry(repair, context),
        warm_normal_latency_seconds=distribution(a["wall_clock_seconds"] for a in initial),
        preflight_telemetry=telemetry(preflight, context),
        turn_latency_seconds=distribution(v for m in matches for v in m["turn_latency_seconds"]),
        match_latency_seconds=distribution(m["provider_latency_seconds"] for m in matches),
        action_distribution=dict(sum((Counter(m["action_distribution"]) for m in matches), Counter())),
        tactical=dict(sum((Counter(m["tactical"]) for m in matches), Counter())),
        initial_failure_taxonomy=dict(sum((Counter(m["initial_failure_taxonomy"]) for m in matches), Counter())),
        repair_failure_taxonomy=dict(sum((Counter(m["repair_failure_taxonomy"]) for m in matches), Counter())),
        repaired_failure_kinds=dict(Counter(e["failure_kind"] for e in events if e["failure_kind"])))
