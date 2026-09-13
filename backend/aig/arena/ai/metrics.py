"""Raw match and per-player facts, using the existing verified combat counters."""

from aig.arena.ai.contracts import ACTION_TYPES


def ai_metrics(simulation, traces):
    result = simulation.metrics()
    entries = simulation.trace()["entries"]
    rows = [t.to_dict() if hasattr(t, "to_dict") else t for t in traces]
    initial = simulation.initial_snapshot
    result["ai_turns"] = len(rows)
    result["turns_to_victory"] = len(rows) if simulation.state.winner_player_id else None
    for player, values in result["players"].items():
        turns = [t for t in rows if t["player_id"] == player]
        commands = [e for e in entries if e["command"]["actor_id"] == player]
        other = [e for e in entries if e["command"]["actor_id"] != player]
        spent = sum(t["ap_spent"] for t in turns)
        initial_units = sum(u["owner_id"] == player for u in initial["units"])
        values.update(
            turns_taken=len(turns), ap_available=sum(t["ap_available"] for t in turns),
            ap_spent=spent, ap_unused=sum(t["ap_unused"] for t in turns),
            actions_by_type={kind: sum(e["command"]["type"] == "arena_" + kind for e in commands) for kind in ACTION_TYPES},
            damage_received=sum(e["damage_dealt"] - e["friendly_fire_damage"] for e in other)
                            + sum(e["friendly_fire_damage"] for e in commands),
            planned_actions=sum(len(t["plan"]["actions"]) for t in turns),
            successfully_executed_actions=sum(t["actions_executed"] for t in turns),
            invalid_planned_actions=sum(t["invalid_action"] is not None for t in turns),
            truncated_turns=sum(t["truncation_reason"] is not None for t in turns),
            average_ap_used=spent / len(turns) if turns else 0,
            zero_action_turns=sum(t["actions_executed"] == 0 for t in turns),
            removed_units=initial_units - values["living_units"] - values["downed_units"],
            winner=simulation.state.winner_player_id == player,
            turns_to_victory=result["turns_to_victory"],
        )
    return result
