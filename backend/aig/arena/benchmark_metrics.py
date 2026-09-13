"""Arena facts and inference distributions; no weighted tactical score."""

from statistics import mean, median
from math import ceil

from aig.arena.ai.metrics import ai_metrics
from aig.arena.benchmark_provider import METRIC_KEYS


def distribution(values):
    values = sorted(v for v in values if v is not None)
    return dict(samples=len(values), min=min(values) if values else None,
                max=max(values) if values else None, mean=mean(values) if values else None,
                median=median(values) if values else None,
                p95=values[ceil(.95 * len(values)) - 1] if len(values) >= 20 else None,
                total=sum(values))


def inference_metrics(rows, context_size=None):
    attempts = [a for row in rows for a in row["attempts"]]
    first = [row["attempts"][0] for row in rows if row["attempts"]]
    repairs = [a for row in rows for a in row["attempts"][1:]]
    occupancy = [(a["metrics"]["prompt_eval_count"] + a["metrics"]["eval_count"]) / context_size
                 for a in attempts if context_size and "prompt_eval_count" in a["metrics"]
                 and "eval_count" in a["metrics"]]
    return dict(provider_calls=len(rows), provider_requests=len(attempts),
                trial_inference_requests=len(first), repair_requests=len(repairs),
                fallback_count=sum(r["fallback_used"] for r in rows),
                provider_failures=sum(not r["success"] for r in rows),
                statically_invalid_initial_outputs=sum(bool(r["attempts"] and
                    r["attempts"][0]["error_category"] in ("malformed_json", "schema_validation",
                    "ap_budget", "invalid_reference", "invalid_ability")) for r in rows),
                repaired_plans=sum(r["success"] and r["repair_requests"] > 0 for r in rows),
                latency_seconds=distribution(a["wall_clock_seconds"] for a in attempts),
                initial_request_latency_seconds=distribution(a["wall_clock_seconds"] for a in first),
                repair_latency_seconds=distribution(a["wall_clock_seconds"] for a in repairs),
                planning_latency_seconds=distribution(r["wall_clock_seconds"] for r in rows),
                tokens_and_durations={k: distribution(a["metrics"].get(k) for a in attempts) for k in METRIC_KEYS},
                configured_context=context_size, max_context_occupancy=max(occupancy) if occupancy else None)


def trial_metrics(simulation, plans, inference, positions):
    result = ai_metrics(simulation, plans)
    winner = simulation.state.winner_player_id
    result.update(winner=winner, loser=next((p.id for p in simulation.state.players if p.id != winner), None)
                  if winner else None, global_turns=simulation.state.turn,
                  player_turns=len(plans), first_player=simulation.initial_snapshot["active_player_id"])
    for player, values in result["players"].items():
        turns = [p for p in plans if p["player_id"] == player]
        calls = [r for r in inference if r["player_id"] == player]
        values.update(ap_planned=sum(p["ap_planned"] for p in turns),
                      ap_executed=values["ap_spent"], turns_using_all_5_ap=sum(p["ap_spent"] == 5 for p in turns),
                      plans_created=len(turns), execution_invalid_actions=sum(p["invalid_action"] is not None for p in turns),
                      truncation_indices=[p["invalid_action"]["index"] for p in turns if p["invalid_action"]],
                      provider_requests=sum(r["provider_requests"] for r in calls),
                      repair_requests=sum(r["repair_requests"] for r in calls),
                      fallback_count=sum(r["fallback_used"] for r in calls),
                      provider_failures=sum(not r["success"] for r in calls),
                      **{key: sum(p[key] for p in positions if p["player_id"] == player)
                         for key in ("power_attacks", "siege_core_attacks", "ward_actions", "fireball_friendly_targets_hit")})
    return result
