"""Browser-only semantic projection. No rules, clocks, or replay dependencies."""
from copy import deepcopy

from aig.arena.replay import ArenaSimulation
from aig.arena.commands import find_path
from aig.state import Position
from aig.arena.snapshots import position_data, state_hash

VERSION = "arena-presentation-events-v1"


def terminal_reason(state):
    if state.winner_player_id is None:
        return None
    return "Core destroyed" if any(c.hp == 0 for c in state.cores.values()) else "Team eliminated"


def project(before, after, entry, sequence):
    command = entry["command"]
    kind = command["type"].removeprefix("arena_")
    actor = before.units.get(command.get("unit_id"))
    target = before.units.get(command.get("target_id")) or before.cores.get(command.get("target_id"))
    players = {p.id: p.name for p in before.players}
    def label(entity):
        return players[entity.owner_id] + " " + (entity.unit_type.value.title() if hasattr(entity, "unit_type") else "Core")
    event = dict(sequence=sequence, type="turn_end" if kind == "end_turn" else kind,
                 turn=before.turn, acting_player=command["actor_id"], actor_id=actor.id if actor else None,
                 actor_class=actor.unit_type.value if actor else None, actor_team=command["actor_id"],
                 actor_label=label(actor) if actor else players[command["actor_id"]],
                 origin=position_data(actor.position) if actor else None,
                 destination=command.get("destination"), target_id=command.get("target_id"),
                 target=position_data(target.position) if target else command.get("target_position"),
                 ap_before=before.action_points_remaining, ap_after=after.action_points_remaining,
                 before_hash=entry["before_hash"], after_hash=entry["after_hash"], effects=[],
                 transition=dict(turn=after.turn, active_player_id=after.active_player_id,
                                 action_points_remaining=after.action_points_remaining))
    for entity_kind in ("unit", "core"):
        old = before.units if entity_kind == "unit" else before.cores
        new = after.units if entity_kind == "unit" else after.cores
        for uid in sorted(old):
            a, b = old[uid], new.get(uid)
            common = dict(entity_kind=entity_kind, entity_id=uid, owner_id=a.owner_id,
                          label=label(a), position=position_data(a.position))
            if b is None:
                event["effects"].append(dict(common, type="removed"))
                continue
            if a.hp != b.hp:
                effect = "core_damage" if entity_kind == "core" else "damage" if b.hp < a.hp else "heal"
                event["effects"].append(dict(common, type=effect, amount=abs(b.hp-a.hp), hp_before=a.hp, hp_after=b.hp))
            if entity_kind == "unit" and a.status != b.status:
                event["effects"].append(dict(common, type="downed" if b.status.value == "downed" else "revived",
                                             status_before=a.status.value, status_after=b.status.value, hp_after=b.hp))
            if a.position != b.position:
                event["effects"].append(dict(common, type="move" if uid == event["actor_id"] else "push",
                                             destination=position_data(b.position)))
    if kind == "move":
        event["path"] = [position_data(p) for p in find_path(before, actor.id, Position(**command["destination"]))]
    events = [event]
    if before.winner_player_id != after.winner_player_id:
        events.append(dict(sequence=sequence+1, type="victory", actor_class=None, effects=[],
                           winner_player_id=after.winner_player_id, terminal_reason=terminal_reason(after),
                           actor_label=players[after.winner_player_id], transition={}))
    return events


def event_text(event):
    kind, actor = event["type"], event["actor_label"]
    if kind == "victory":
        return f'{actor} wins: {event["terminal_reason"]}'
    if kind == "turn_end":
        return f"{actor} ended turn"
    if kind == "move":
        p = event["destination"]
        return f'{actor} moved to ({p["x"]}, {p["y"]})'
    details = []
    for effect in event["effects"]:
        kind = effect["type"]
        text = {"damage": "damage", "core_damage": "damage", "heal": "HP restored"}.get(kind)
        details.append(f'{effect["label"]}: {effect["amount"]} {text}' if text else
                       f'{effect["label"]}: {kind.upper()}')
    return f'{actor} used {event["type"].replace("_", " ").title()} · ' + "; ".join(details)


class PresentationSimulation(ArenaSimulation):
    """Only installed by the playable web session, never the research API."""
    def __init__(self, source):
        self.__dict__.update(deepcopy(source.__dict__))
        self.presentation_events = []

    def execute(self, command):
        before = deepcopy(self.state)
        entry = super().execute(command)
        events = project(before, self.state, entry, len(self.presentation_events)+1)
        for event in events:
            event["log"] = dict(id=event["sequence"], text=event_text(event))
        self.presentation_events.extend(events)
        return entry
