"""Observer-only capture and elimination events, independent of planner inputs."""

from collections import Counter
from dataclasses import asdict

from aig.commands import AttackUnit, MoveUnit


class ConquestMetrics:
    def __init__(self, state):
        self.captures = []
        self.eliminations = []
        self.attacks = []
        self.victory = None
        self.initial_turn = state.turn
        self.owners = {c.id: {c.owner_id} for c in state.cities.values()}

    def observe(self, phase, state, command, activation):
        if phase == "before":
            self.cities = {c.id: asdict(c) for c in state.cities.values()}
            self.units = {u.id: (u.owner_id, u.unit_type.value) for u in state.units.values()}
            self.live = set(state.civilization_ids)
            self.turn = state.turn
            self.last_events = dict(captures=[], eliminations=[])
            if isinstance(command, AttackUnit):
                target = state.units[command.target_unit_id]
                if not state.is_barbarian(target.owner_id):
                    self.attacks.append((command.actor_id, target.owner_id, target.position))
            return
        for city in state.cities.values():
            old = self.cities.get(city.id)
            owners = self.owners.setdefault(city.id, {city.owner_id})
            if old is None or old["owner_id"] == city.owner_id:
                continue
            event = dict(city_id=city.id, player_id=city.owner_id, former_owner_id=old["owner_id"],
                         turn=self.turn, activation=activation,
                         capture_unit_type=self.units[command.unit_id][1] if isinstance(command, MoveUnit) else None,
                         population_lost=old["population"]-city.population,
                         food_reset=old["food_stored"], production_reset=old["production_stored"],
                         production_target_canceled=old["production_target"] is not None,
                         recapture=city.owner_id in owners, undefended=True,
                         attacks_near_city=sum(a == city.owner_id and b == old["owner_id"]
                             and max(abs(p.x-city.position.x), abs(p.y-city.position.y)) <= 1
                             for a, b, p in self.attacks))
            owners.add(city.owner_id)
            self.captures.append(event)
            self.last_events["captures"].append(event)
        for player in sorted(self.live - set(state.civilization_ids)):
            removed = [(i, kind) for i, (owner, kind) in self.units.items()
                       if owner == player and i not in state.units]
            event = dict(player_id=player, turn=self.turn, activation=activation,
                         capturing_player_id=next((c["player_id"] for c in self.last_events["captures"]
                                                   if c["former_owner_id"] == player), None),
                         units_removed=len(removed), settlers_removed=sum(k == "settler" for _, k in removed))
            self.eliminations.append(event)
            self.last_events["eliminations"].append(event)
        if state.result is not None and self.victory is None:
            self.victory = dict(winnerPlayerId=state.result.winner_player_id,
                               victoryType=state.result.victory_type.value,
                               victoryTurn=self.turn, victoryActivation=activation)

    def finish(self, state):
        players = {}
        for actor in state.players:
            captures = [c for c in self.captures if c["player_id"] == actor]
            players[actor] = dict(cities_captured=len(captures),
                captures_by_victim_civ=dict(Counter(c['former_owner_id'] for c in captures)),
                losses_by_capturing_civ=dict(Counter(c['player_id'] for c in self.captures
                                                   if c['former_owner_id'] == actor)),
                rivals_eliminated=sum(e['capturing_player_id'] == actor for e in self.eliminations),
                cities_lost=sum(c["former_owner_id"] == actor for c in self.captures),
                first_city_capture_turn=captures[0]["turn"] if captures else None,
                capture_unit_types=dict(Counter(c["capture_unit_type"] for c in captures)),
                population_lost_through_capture=sum(c["population_lost"] for c in self.captures
                                                   if c["former_owner_id"] == actor),
                captured_food_reset=sum(c["food_reset"] for c in captures),
                captured_production_reset=sum(c["production_reset"] for c in captures),
                production_targets_canceled=sum(c["production_target_canceled"] for c in captures),
                recaptures=sum(c["recapture"] for c in captures), undefended_city_captures=len(captures),
                eliminated=state.players[actor].eliminated,
                elimination=next((e for e in self.eliminations if e["player_id"] == actor), None))
        result = self.victory or dict(winnerPlayerId=None, victoryType=None,
                                      victoryTurn=None, victoryActivation=None)
        return dict(result, gameDurationTurns=state.turn-self.initial_turn,
                    elimination_order=[e['player_id'] for e in self.eliminations],
                    eliminations_by_killer_civ=dict(Counter(e['capturing_player_id'] for e in self.eliminations
                                                           if e['capturing_player_id'] is not None)),
                    surviving_city_count=sum(c.owner_id in state.civilization_ids for c in state.cities.values()),
                    rivals_eliminated_by_winner=(sum(e['capturing_player_id'] == result['winnerPlayerId']
                        for e in self.eliminations) if result['winnerPlayerId'] else None),
                    rivals_eliminated_by_other_civs=(sum(e['capturing_player_id'] is not None
                        and e['capturing_player_id'] != result['winnerPlayerId'] for e in self.eliminations)
                        if result['winnerPlayerId'] else None),
                    city_capture_events=self.captures, civilization_eliminations=self.eliminations), players
