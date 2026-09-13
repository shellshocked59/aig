"""Factual multi-opponent observations; never fed back into planning."""

from collections import Counter
from statistics import mean


class MultiFrontMetrics:
    def __init__(self, state):
        self.turns = {p: Counter() for p in state.civilization_ids}
        self.plans = {p: [] for p in state.civilization_ids}
        self.visibility = {p: [] for p in state.civilization_ids}

    def record(self, actor, controller):
        # One sample per normal activation, including reused plans. Eliminated
        # factions have no subsequent samples; a terminal partial turn counts.
        enemy = controller.previous_plan.primary_enemy_id
        if enemy is not None:
            self.turns[actor][enemy] += 1
        trace = controller.last_trace
        if trace is None:
            return
        view = trace['strategic_state']
        strength = Counter()
        for unit in view.get('enemy_units', []):
            strength[unit['owner_id']] += unit['strength']
        owners = set(strength) | {c['owner_id'] for c in view.get('enemy_cities', [])
                                 if c.get('currently_visible') and c.get('live_exists') is not False}
        threatened = {}
        for city in view.get('own_cities', []):
            rivals = sorted({u['owner_id'] for u in view['enemy_units'] if u['strength'] > 0
                and max(abs(u['x']-city['x']), abs(u['y']-city['y'])) <= 3})
            if len(rivals) > 1:
                threatened[city['id']] = rivals
        self.visibility[actor].append(dict(turn=trace['turn'],
            visible_enemy_civilizations=sorted(owners), visible_hostile_strength_by_rival=dict(strength),
            own_cities_with_multiple_rivals_within_three_tiles=threatened))
        old = trace.get('invalidated_previous_plan') or trace['previous_plan']
        dead = {c['id'] for c in view.get('civilizations', []) if c['eliminated']}
        self.plans[actor].append(dict(enemy=enemy, city=controller.previous_plan.target_city_id,
            eliminated_target_transition=bool(old and old['primary_enemy_id'] in dead
                                             and old['primary_enemy_id'] != enemy)))

    def finish(self):
        result = {}
        for actor, plans in self.plans.items():
            streaks = []
            previous = None
            for plan in plans:
                enemy = plan['enemy']
                if enemy is not None:
                    if enemy == previous:
                        streaks[-1] += 1
                    else:
                        streaks.append(1)
                previous = enemy
            pairs = list(zip(plans, plans[1:]))
            result[actor] = dict(
                distinct_primary_enemies_selected=sorted({p['enemy'] for p in plans if p['enemy'] is not None}),
                primary_enemy_switches=sum(a['enemy'] != b['enemy'] for a, b in pairs),
                target_city_switches=sum(a['city'] != b['city'] for a, b in pairs),
                targeting_activations_by_rival=dict(self.turns[actor]),
                consecutive_plans_same_primary_enemy=streaks,
                average_consecutive_plans_same_primary_enemy=mean(streaks) if streaks else None,
                eliminated_target_transitions=sum(p['eliminated_target_transition'] for p in plans),
                maximum_simultaneous_visible_enemy_civilizations=max(
                    (len(v['visible_enemy_civilizations']) for v in self.visibility[actor]), default=0),
                multi_front_visibility_at_replans=self.visibility[actor])
        return result
