"""Readable greedy tactical baseline, with exact detached command simulation."""

from copy import deepcopy

from aig.state import Position
from aig.arena.ai.contracts import ArenaTurnPlan, action_from_dict, action_command
from aig.arena.ai.observation import simulation_state
from aig.arena.commands import (ACTION_COSTS, apply_command, attack_damage, find_path)
from aig.arena.geometry import distance, arena_line_of_sight
from aig.arena.queries import legal_actions
from aig.arena.snapshots import canonical_json
from aig.arena.state import Bonus, UnitStatus, UnitType

HEURISTIC_VERSION = "arena-heuristic-v1"
TARGET_VALUE = {UnitType.CLERIC: 4, UnitType.MAGE: 3, UnitType.RANGER: 2, UnitType.KNIGHT: 1}


def core_threats(state, player):
    """Enemies able to destroy our Core with one basic attack on their next turn."""
    core = next(c for c in state.cores.values() if c.owner_id == player)
    return {u.id for u in state.units.values() if u.owner_id != player and u.status is UnitStatus.ACTIVE
            and distance(u.position, core.position) <= u.stats.attack_range
            and (u.unit_type is UnitType.KNIGHT or arena_line_of_sight(state.board, u.position, core.position))
            and attack_damage(state, u, core) >= core.hp}


def fireball_utility(before, after, player):
    """Actual capped damage: enemy +1, friendly -2; downs enemy +12, friendly -40."""
    enemies = friends = enemy_downs = friendly_downs = hits = 0
    for uid, unit in before.units.items():
        loss = unit.hp - after.units[uid].hp
        if loss <= 0:
            continue
        down = int(after.units[uid].hp == 0)
        if unit.owner_id == player:
            friends += loss
            friendly_downs += down
        else:
            enemies += loss
            enemy_downs += down
            hits += 1
    return dict(utility=enemies + 12 * enemy_downs - 2 * friends - 40 * friendly_downs,
                enemy_hits=hits, enemy_downs=enemy_downs, friendly_downs=friendly_downs)


def tactical_score(state, after, action, threats):
    """Lexicographic tier, value, HP tie-break; None means not worthwhile."""
    player = state.active_player_id
    if after.winner_player_id is not None:
        return (10000, 1 if action.type == "attack" and action.target_id in state.cores else 0, 0) if after.winner_player_id == player else None
    if threats and not core_threats(after, player):
        return (9000, 0, 0)
    target = state.units.get(getattr(action, "target_id", None))
    value = TARGET_VALUE[target.unit_type] if target else 0
    hp = -target.hp if target else 0
    if action.type == "finish":
        return (800, value, hp)
    if action.type == "revive":
        return (700, value, hp)
    if action.type == "fireball":
        impact = fireball_utility(state, after, player)
        if impact["utility"] <= 0 or not (impact["enemy_hits"] >= 2 or impact["enemy_downs"]):
            return None
        # A friendly down is never justified by a nonterminal greedy opportunity.
        if impact["friendly_downs"]:
            return None
        return (600 if impact["enemy_downs"] else 500, impact["utility"], 0)
    if action.type in ("attack", "snipe", "shield_bash") and target:
        if after.units[target.id].hp == 0:
            return (600, value, hp)
        loss = target.hp - after.units[target.id].hp
        if action.type == "shield_bash":
            pushed = after.units[target.id].position != target.position
            own_core = next(c for c in state.cores.values() if c.owner_id == player)
            off_bonus = state.board.at(target.position).bonus is not None
            away = distance(after.units[target.id].position, own_core.position) > distance(target.position, own_core.position)
            if pushed and (off_bonus or away):
                return (450, 10 * int(off_bonus) + int(away), hp)
            return None
        if action.type == "snipe":
            attacker = state.units[action.unit_id]
            # Two basic attacks win comparable trades whenever basic range is available.
            if distance(attacker.position, target.position) <= attacker.stats.attack_range:
                return None
            return (350, value, hp)
        return (250, loss, hp)
    if action.type == "heal":
        missing = target.max_hp - target.hp
        return (300 if missing >= 3 else 1, missing, -(1000 * target.hp // target.max_hp))
    if action.type == "attack":
        core = state.cores[action.target_id]
        return (200, core.hp - after.cores[core.id].hp, 0)
    return None


def position_value(state, unit, position):
    """Factual range/LOS objectives plus small explicit bonus preferences."""
    enemies = [u for u in state.units.values() if u.owner_id != unit.owner_id and u.status is UnitStatus.ACTIVE]
    core = next(c for c in state.cores.values() if c.owner_id != unit.owner_id)
    def in_range(target, reach):
        return distance(position, target.position) <= reach and (unit.unit_type is UnitType.KNIGHT
                or arena_line_of_sight(state.board, position, target.position))
    value = max([0] + [35 + TARGET_VALUE[u.unit_type] for u in enemies if in_range(u, unit.stats.attack_range)])
    core_range = in_range(core, unit.stats.attack_range)
    value = max(value, 30 if core_range else 0)
    if unit.unit_type is UnitType.CLERIC:
        for ally in state.units.values():
            if ally.owner_id == unit.owner_id and in_range(ally, 2):
                value = max(value, 55 + TARGET_VALUE[ally.unit_type] if ally.status is UnitStatus.DOWNED
                            else 40 if ally.max_hp - ally.hp >= 3 else 0)
    bonus = state.board.at(position).bonus
    value += (14 if bonus is Bonus.POWER else 16 if bonus is Bonus.SIEGE and core_range
              else 8 if bonus is Bonus.WARD and unit.unit_type is not UnitType.KNIGHT else 0)
    return value


def movement_options(state, unit, legal, visited):
    """Route to useful attack/support/bonus squares through the existing engine BFS."""
    if not legal:
        return []
    current_value = position_value(state, unit, unit.position)
    options = []
    for y in range(state.board.height):
        for x in range(state.board.width):
            goal = Position(x, y)
            if not state.can_enter(goal):
                continue
            gain = position_value(state, unit, goal) - current_value
            if gain <= 0:
                continue
            path = find_path(state, unit.id, goal)
            if not path:
                continue
            destination = path[min(unit.stats.move_range, len(path) - 1)]
            if destination not in legal or destination in visited.get(unit.id, set()):
                continue
            utility = gain * 10 - (len(path) - 1) * 3
            if utility > 0:
                action = action_from_dict(dict(type="move", unit_id=unit.id,
                                                destination=dict(x=destination.x, y=destination.y)))
                options.append((action, (100, utility, -(len(path) - 1))))
    return options


class HeuristicArenaTurnProvider:
    name = HEURISTIC_VERSION

    def create_turn_plan(self, observation):
        state = simulation_state(observation)
        actions, visited = [], {}
        while state.action_points_remaining and state.winner_player_id is None:
            candidates = []
            threats = core_threats(state, state.active_player_id)
            for unit in sorted(state.units.values(), key=lambda u: u.id):
                if unit.owner_id != state.active_player_id or unit.status is not UnitStatus.ACTIVE:
                    continue
                visited.setdefault(unit.id, {unit.position})
                legal = legal_actions(state, unit)
                candidates.extend(movement_options(state, unit, legal["move"], visited))
                for kind in sorted(legal):
                    if kind == "move":
                        continue
                    for target in legal[kind]:
                        details = dict(target_position=dict(x=target.x, y=target.y)) if kind == "fireball" else dict(target_id=target)
                        action = action_from_dict(dict(type=kind, unit_id=unit.id, **details))
                        after = deepcopy(state)
                        apply_command(after, action_command(action, state.active_player_id))
                        score = tactical_score(state, after, action, threats)
                        if score is not None:
                            candidates.append((action, score))
            if not candidates:
                break
            # Canonical action JSON supplies stable unit/target/coordinate/discriminator ties.
            action, _ = min(candidates, key=lambda item: (*(-v for v in item[1]),
                              ACTION_COSTS[item[0].type], canonical_json(item[0].to_dict())))
            apply_command(state, action_command(action, state.active_player_id))
            actions.append(action)
            if action.type == "move":
                visited[action.unit_id].add(state.units[action.unit_id].position)
        return ArenaTurnPlan(tuple(actions))
