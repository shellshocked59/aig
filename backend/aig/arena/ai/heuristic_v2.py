"""Offline positional opponent. V1 and all research defaults remain frozen.

V1 gives every attack tier 250 and every move tier 100: positional gains
cannot compete with even one damage. V2 retains urgent tactical tiers but
compares ordinary actions against a post-action positional delta.
"""
from collections import deque
from copy import deepcopy

from aig.state import Position
from aig.movement import NEIGHBOR_OFFSETS
from aig.arena.geometry import distance, can_step, arena_line_of_sight
from aig.arena.commands import ACTION_COSTS, apply_command, attack_damage
from aig.arena.state import Bonus, UnitStatus, UnitType
from aig.arena.queries import legal_actions
from aig.arena.snapshots import canonical_json
from aig.arena.ai.contracts import ArenaTurnPlan, action_from_dict, action_command
from aig.arena.ai.observation import simulation_state
from aig.arena.ai.heuristic import tactical_score, core_threats

HEURISTIC_VERSION = "arena-heuristic-v2"
MIN_MOVE_GAIN = 2


def reaches(state, unit, target):
    return distance(unit.position, target.position) <= unit.stats.attack_range and (
        unit.unit_type is UnitType.KNIGHT or
        arena_line_of_sight(state.board, unit.position, target.position))


def routes(state, unit):
    """One BFS per unit, using engine geometry, occupancy and corner rules."""
    lengths = {unit.position: 0}
    queue = deque([unit.position])
    while queue:
        pos = queue.popleft()
        for dx, dy in NEIGHBOR_OFFSETS:
            end = Position(pos.x + dx, pos.y + dy)
            if end not in lengths and can_step(state, pos, end):
                lengths[end] = lengths[pos] + 1
                queue.append(end)
    return lengths


def position_components(state, unit):
    enemies = [u for u in state.units.values() if u.owner_id != unit.owner_id and u.status is UnitStatus.ACTIVE]
    core = next(c for c in state.cores.values() if c.owner_id != unit.owner_id)
    paths = routes(state, unit)
    # Distance to a reachable firing square, not distance through a wall/occupant.
    def approach(target):
        return min((steps for pos, steps in paths.items()
                    if distance(pos, target.position) <= unit.stats.attack_range and
                    (unit.unit_type is UnitType.KNIGHT or arena_line_of_sight(state.board, pos, target.position))), default=12)
    enemy_steps = min((approach(e) for e in enemies), default=0)
    core_steps = approach(core)
    incoming = sorted((attack_damage(state, e, unit) for e in enemies if reaches(state, e, unit)), reverse=True)
    # Two concentrated attacks plus other immediate lanes, bounded by shared AP.
    exposure = sum(incoming[:4]) + (incoming[0] if incoming else 0)
    danger = max(0, exposure - unit.hp + 1)
    bonus = state.board.at(unit.position).bonus
    premium = 0
    if bonus is Bonus.POWER:
        premium = 8 + unit.stats.damage
    elif bonus is Bonus.WARD:
        premium = 5 + (unit.max_hp - unit.hp) + (6 if incoming else 0)
    elif bonus is Bonus.SIEGE:
        premium = max(0, 18 - 5 * core_steps)
    support = 0
    if unit.unit_type is UnitType.CLERIC:
        allies = [a for a in state.units.values() if a.owner_id == unit.owner_id and a.id != unit.id]
        support = max((max(0, 12 - 3 * distance(unit.position, a.position)) +
                       (12 if a.status is UnitStatus.DOWNED and distance(unit.position, a.position) <= 2 else 0)
                       for a in allies), default=0)
    targets = sum(reaches(state, unit, e) for e in enemies)
    return dict(premium_control=premium, advancement=-4 * enemy_steps,
                core_pressure=-(1 if unit.unit_type is UnitType.CLERIC else 2) * core_steps + 8 * int(reaches(state, unit, core)),
                future_threat=8 * min(2, targets), support=support,
                exposure=-exposure - 4 * danger)


class HeuristicArenaTurnProviderV2:
    name = HEURISTIC_VERSION

    def __init__(self):
        self.last_scores = []

    def create_turn_plan(self, observation):
        state = simulation_state(observation)
        actions, visited, moved = [], {}, {}
        self.last_scores = []
        while state.action_points_remaining and state.winner_player_id is None:
            candidates = []
            threats = core_threats(state, state.active_player_id)
            for unit in sorted(state.units.values(), key=lambda u: u.id):
                if unit.owner_id != state.active_player_id or unit.status is not UnitStatus.ACTIVE:
                    continue
                visited.setdefault(unit.id, {unit.position})
                before = position_components(state, unit)
                for kind, targets in sorted(legal_actions(state, unit).items()):
                    for target in targets:
                        details = ({"destination" if kind == "move" else "target_position": dict(x=target.x, y=target.y)}
                                   if kind in ("move", "fireball") else dict(target_id=target))
                        action = action_from_dict(dict(type=kind, unit_id=unit.id, **details))
                        after = deepcopy(state)
                        apply_command(after, action_command(action, state.active_player_id))
                        tactical = tactical_score(state, after, action, threats)
                        parts = dict(tactical=0)
                        tier = 0
                        if kind == "move":
                            parts.update({k: v - before[k] for k, v in position_components(after, after.units[unit.id]).items()})
                            parts["movement_repeat"] = -3 * moved.get(unit.id, 0) - (40 if target in visited[unit.id] else 0)
                            if sum(parts.values()) < MIN_MOVE_GAIN:
                                continue
                        elif tactical is None:
                            continue
                        elif tactical[0] >= 600:
                            tier = tactical[0]
                            parts["tactical"] = tactical[1] * 10 + tactical[2]
                        else:
                            # Ordinary damage competes with position; specials retain their utility.
                            parts["tactical"] = {500: 45, 450: 35, 350: 24, 300: 28, 250: 0, 200: 0, 1: 1}.get(tactical[0], 0)
                            if kind == "attack":
                                victim = state.units.get(target) or state.cores[target]
                                remaining = after.units.get(target) or after.cores[target]
                                parts["damage"] = 3 * (victim.hp - remaining.hp)
                            else:
                                parts["tactical"] += tactical[1]
                            if kind == "shield_bash":
                                parts["premium_denial"] = (position_components(state, state.units[target])["premium_control"] -
                                                           position_components(after, after.units[target])["premium_control"])
                        total = sum(parts.values())
                        candidates.append((tier, total, action, parts))
            if not candidates:
                break
            candidates.sort(key=lambda row: (-row[0], -row[1], ACTION_COSTS[row[2].type], canonical_json(row[2].to_dict())))
            tier, total, action, parts = candidates[0]
            self.last_scores.append(dict(selected=action.to_dict(), tier=tier, total=total, components=parts,
                                         candidates=[dict(action=a.to_dict(), tier=t, total=s, components=p) for t, s, a, p in candidates]))
            apply_command(state, action_command(action, state.active_player_id))
            actions.append(action)
            if action.type == "move":
                visited[action.unit_id].add(state.units[action.unit_id].position)
                moved[action.unit_id] = moved.get(action.unit_id, 0) + 1
        return ArenaTurnPlan(tuple(actions))
