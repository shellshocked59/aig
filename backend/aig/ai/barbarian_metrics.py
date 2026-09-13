"""Observer-only V4 events. Nothing here is passed to tactical/planning code."""

from collections import Counter
import json

from aig.commands import AttackUnit, EndActivation, MoveUnit
from aig.knowledge import visible_enemy_units, vision_positions
from aig.state import BARBARIAN_ID, UnitType


class BarbarianMetrics:
    def __init__(self, state):
        self.counts = {p: Counter(dict(camps_discovered=0, scout_camp_discoveries=0,
            barbarian_units_sighted=0, attacks_against_barbarians=0, barbarian_units_killed=0,
            units_killed_by_barbarians=0, settlers_killed_by_barbarians=0, scouts_killed_by_barbarians=0,
            damage_dealt_to_barbarians=0, damage_received_from_barbarians=0,
            camps_cleared=0, camp_clear_gold=0, settler_movement_commands=0,
            defend_with_visible_civilization_threat=0, defend_with_visible_barbarian_threat=0,
            defend_without_visible_threat=0)) for p in state.civilization_ids}
        self.discoveries = {p: {} for p in self.counts}
        self.sightings = {p: {} for p in self.counts}
        self.clears = {p: [] for p in self.counts}
        self.spawns = Counter()
        self.skips = Counter()
        self.capped = Counter()
        self.maximum = 0
        self.sizes = {p: [] for p in self.counts}
        self.contacts(state, 0)

    def contacts(self, state, activation):
        self.maximum = max(self.maximum, sum(state.is_barbarian(u.owner_id) for u in state.units.values()))
        for p in self.counts:
            for c in state.players[p].knowledge.discovered_camps.values():
                if c.id not in self.discoveries[p]:
                    self.discoveries[p][c.id] = dict(turn=state.turn, activation=activation)
                    self.counts[p]['camps_discovered'] += 1
            for u in visible_enemy_units(state, p):
                if state.is_barbarian(u.owner_id) and u.id not in self.sightings[p]:
                    self.sightings[p][u.id] = dict(turn=state.turn, activation=activation)
                    self.counts[p]['barbarian_units_sighted'] += 1

    def observe(self, phase, state, command, activation):
        if phase == 'before':
            self.turn = state.turn
            self.units = {u.id: (u.owner_id, u.unit_type.value, u.hp, u.home_camp_id) for u in state.units.values()}
            self.camps = dict(state.camps)
            self.discovered = {p: set(self.discoveries[p]) for p in self.counts}
            self.spawn_cycle = (isinstance(command, EndActivation) and command.actor_id != BARBARIAN_ID
                and state.turn_order[-1] == BARBARIAN_ID
                and state.turn_order.index(command.actor_id) == len(state.turn_order)-2
                and state.turn > 0 and state.turn % 8 == 0)
            return
        self.contacts(state, activation)
        self.last_events = dict(spawns=[], skipped_spawns=[], capped_camps=[], clears=[])
        actor = command.actor_id
        new_units = [u for u in state.units.values() if u.id not in self.units]
        spawned = [u for u in new_units if state.is_barbarian(u.owner_id)]
        for u in spawned:
            self.spawns[u.home_camp_id] += 1
            self.last_events['spawns'].append(dict(unit_id=u.id, camp_id=u.home_camp_id, turn=self.turn))
        if self.spawn_cycle:
            for c in sorted(self.camps):
                if not any(u.home_camp_id == c for u in spawned):
                    capped = sum(owner == BARBARIAN_ID and home == c
                                 for owner, _, _, home in self.units.values()) >= 2
                    if capped:
                        self.capped[c] += 1
                        self.last_events['capped_camps'].append(dict(camp_id=c, turn=self.turn))
                    else:
                        self.skips[c] += 1
                        self.last_events['skipped_spawns'].append(dict(camp_id=c, turn=self.turn))
        if actor in self.counts:
            counts = self.counts[actor]
            scouts = set().union(*(vision_positions(state.game_map, u.position, 3)
                                 for u in new_units if u.owner_id == actor and u.unit_type is UnitType.SCOUT))
            if isinstance(command, MoveUnit):
                kind = self.units[command.unit_id][1]
                counts['settler_movement_commands'] += kind == 'settler'
                if kind == 'scout':
                    scouts |= vision_positions(state.game_map, state.units[command.unit_id].position, 3)
                for camp_id in sorted(self.camps.keys() - state.camps.keys()):
                    counts['camps_cleared'] += 1
                    counts['camp_clear_gold'] += 25
                    discovered = self.discoveries[actor].get(camp_id)
                    self.clears[actor].append(dict(camp_id=camp_id, turn=self.turn, activation=activation,
                        unit_type=kind, gold=25,
                        discovery_delay_turns=self.turn-discovered['turn'] if discovered else None,
                        discovery_delay_activations=activation-discovered['activation'] if discovered else None))
                    self.last_events['clears'].append(dict(self.clears[actor][-1], player_id=actor))
            counts['scout_camp_discoveries'] += sum(
                state.players[actor].knowledge.discovered_camps[c].position in scouts
                for c in self.discoveries[actor].keys()-self.discovered[actor]
                if c in state.players[actor].knowledge.discovered_camps)
        if isinstance(command, AttackUnit):
            attacker = self.units[command.attacker_unit_id][0]
            target = self.units[command.target_unit_id][0]
            if attacker != BARBARIAN_ID and target == BARBARIAN_ID:
                self.counts[attacker]['attacks_against_barbarians'] += 1
            for unit_id, source in ((command.attacker_unit_id,target),(command.target_unit_id,attacker)):
                owner, kind, hp, _ = self.units[unit_id]
                survivor = state.units.get(unit_id)
                lost = hp - (survivor.hp if survivor else 0)
                if owner == BARBARIAN_ID and source in self.counts:
                    self.counts[source]['damage_dealt_to_barbarians'] += lost
                    self.counts[source]['barbarian_units_killed'] += survivor is None
                if source == BARBARIAN_ID and owner in self.counts:
                    self.counts[owner]['damage_received_from_barbarians'] += lost
                    if survivor is None:
                        self.counts[owner]['units_killed_by_barbarians'] += 1
                        if kind in ('settler','scout'):
                            self.counts[owner][kind+'s_killed_by_barbarians'] += 1

    def decision(self, state, actor, plan, trace):
        enemies = visible_enemy_units(state, actor)
        if plan.posture.value == 'defend':
            civ = any(not state.is_barbarian(u.owner_id) and u.unit_type.combat_strength for u in enemies)
            barb = any(state.is_barbarian(u.owner_id) for u in enemies)
            self.counts[actor]['defend_with_visible_civilization_threat'] += bool(civ)
            self.counts[actor]['defend_with_visible_barbarian_threat'] += bool(barb)
            self.counts[actor]['defend_without_visible_threat'] += not civ and not barb
        if trace:
            view = trace['strategic_state']
            serialize = lambda v: len(json.dumps(v, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode())
            without = {k:v for k,v in view.items() if k not in ('known_barbarian_camps','visible_barbarian_units')}
            self.sizes[actor].append(dict(turn=state.turn, bytes=serialize(view),
                                          barbarian_fields_bytes=serialize(view)-serialize(without)))

    def finish(self, state):
        players = {}
        for p, counts in self.counts.items():
            known = state.players[p].knowledge.discovered_camps
            players[p] = dict(counts, camps_known_at_end=len(known),
                stale_known_camps=sum(c not in state.camps for c in known),
                first_camp_discovery=next(iter(self.discoveries[p].values()), None),
                first_barbarian_sighting=next(iter(self.sightings[p].values()), None),
                camp_discoveries=self.discoveries[p], camp_clears=self.clears[p],
                strategic_state_sizes=self.sizes[p])
        observer = dict(total_barbarian_warriors_spawned=sum(self.spawns.values()),
            spawns_per_camp=dict(sorted(self.spawns.items())), skipped_spawn_attempts=sum(self.skips.values()),
            capped_spawn_cycles=sum(self.capped.values()), capped_cycles_per_camp=dict(sorted(self.capped.items())),
            skipped_spawns_per_camp=dict(sorted(self.skips.items())), maximum_concurrent_barbarian_units=self.maximum)
        return players, observer
