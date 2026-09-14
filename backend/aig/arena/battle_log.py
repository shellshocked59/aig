"""Browser-only summaries derived from successful replay entries, never provider text."""


def battle_log(trace, limit=60):
    initial = trace["initial_snapshot"]
    players = {p["id"]: p["name"] for p in initial["players"]}
    pieces = {p["id"]: f'{players[p["owner_id"]]} {p.get("unit_type", "Core").title()}'
              for p in initial["units"] + initial["cores"]}
    entries = trace["entries"]
    result = []
    for index, entry in enumerate(entries[-limit:], start=max(0, len(entries) - limit)):
        command = entry["command"]
        kind = command["type"].removeprefix("arena_")
        actor = pieces.get(command.get("unit_id"), players[command["actor_id"]])
        target = pieces.get(command.get("target_id"), command.get("target_id", ""))
        if kind == "end_turn":
            message = f"{actor} ended turn"
        elif kind == "move":
            position = command["destination"]
            message = f'{actor} moved to ({position["x"]}, {position["y"]})'
        elif kind == "fireball":
            position = command["target_position"]
            message = f'{actor} used Fireball at ({position["x"]}, {position["y"]})'
        else:
            message = f'{actor} used {kind.replace("_", " ").title()} on {target}'
        effects = []
        for key, label in (("damage_dealt", "damage"), ("healing_done", "HP restored"),
                           ("units_downed", "DOWNED"), ("units_revived", "revived"),
                           ("units_finished", "finished")):
            if entry[key]:
                effects.append(f"{entry[key]} {label}")
        if effects:
            message += " · " + ", ".join(effects)
        result.append({"id": index + 1, "text": message})
    return result
