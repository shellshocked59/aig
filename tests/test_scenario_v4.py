"""Scenario V4 contracts and generic four-civilization regression tests."""
from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import unittest

from aig.ai.benchmark import canonical_hash, initial_state, run_trial, compare_runs
from aig.ai.controller import AiController, AiOrchestrator
from aig.ai.executor import AiExecutor
from aig.ai.conquest_metrics import ConquestMetrics
from aig.ai.plan_schema import canonical_json, parse_plan
from aig.ai.prompts import PROMPTS
from aig.ai.strategy import HeuristicStrategyProvider, StrategicStateBuilder, StrategicPlan, Posture
from aig.knowledge import update_knowledge, visible_positions, known_enemy_cities
from aig.commands import MoveUnit, EndActivation, apply_command
from aig.public_state import public_state
from aig.scenarios import scenario_setup
from aig.settings import Settings
from aig.snapshots import SCHEMA_VERSION, from_snapshot, to_snapshot
from aig.state import Position, UnitType, Terrain, ResourceType, CityState, KnownCity, are_hostile


class ScenarioV4Tests(unittest.TestCase):
    def test_latest_scenario_and_preserved_browser_demo(self):
        from aig.scenarios import human_vs_ai_demo_setup
        self.assertEqual(scenario_setup(), scenario_setup('v4'))
        self.assertEqual(initial_state().civilization_ids, list('ABCD'))
        self.assertEqual(human_vs_ai_demo_setup(), scenario_setup('v3'))

    def test_frozen_scenario_payloads(self):
        expected = ('c0520470d90c76629f698116cbc5cd8e34c0d34867226dcfbd179b7210c3e202',
                    '17866d3250b925b4025e8889b523b1a23355e8714f50e1c5abdf3db4bef6fe8a',
                    '73a9100cf98b6de5d2ea19a32bfb341d8b23a287d63cf00d986c4b6a628f4fda',
                    'efa7b8c38d6174dee7679391395110940d8b6cfaf75aabfaca727727b1ece5f9')
        for i, digest in enumerate(expected, 1):
            self.assertEqual(canonical_hash(asdict(scenario_setup(f'v{i}'))), digest)

    def test_frozen_prompts(self):
        self.assertEqual([hashlib.sha256(p.encode()).hexdigest() for p in PROMPTS.values()], [
            '1af8d0e613b1661f59e84b6dce118d31afd45fce0bef5cae97ecd9b6994cc598',
            'f7e8ffcbef66173ff967cdca72588da565346552801c4761c8b0eae0d5722f8e'])

    def test_geometry_and_connectivity(self):
        setup = scenario_setup('v4')
        self.assertEqual((setup.game_map.width, setup.game_map.height), (16, 12))
        self.assertEqual(set(t for _, t in setup.tiles), set(Terrain))
        starts = [p.starting_position for p in setup.players]
        land = {p for p, t in setup.tiles if t.land_passable}
        seen, todo = {starts[0]}, [starts[0]]
        while todo:
            p = todo.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = Position(p.x+dx, p.y+dy)
                    if q in land and q not in seen:
                        seen.add(q); todo.append(q)
        self.assertEqual(seen, land)
        for a in starts:
            self.assertIn(a, seen)
            for b in starts:
                if a != b: self.assertGreaterEqual(max(abs(a.x-b.x), abs(a.y-b.y)), 7)

    def test_setup_resources_camps_and_fog(self):
        state = initial_state('v4')
        self.assertEqual(state.turn_order, ['A', 'B', 'C', 'D', 'barbarians'])
        self.assertEqual(len(state.camps), 5)
        self.assertEqual({t.resource for t in state.tiles.values() if t.resource}, set(ResourceType))
        for actor in state.civilization_ids:
            self.assertEqual(sorted(u.unit_type for u in state.units.values() if u.owner_id == actor),
                             sorted([UnitType.SETTLER, UnitType.WARRIOR]))
            view = StrategicStateBuilder().build(state, actor)
            self.assertEqual(len(view['civilizations']), 4)
            self.assertEqual(sum(c['hostile'] for c in view['civilizations']), 3)
            self.assertFalse(view['enemy_units']); self.assertFalse(view['enemy_cities'])
            self.assertTrue(view['known_resources'])
            self.assertLess(len({r['type'] for r in view['known_resources']}), 5)
            for other in state.players:
                self.assertEqual(are_hostile(state.players[actor], state.players[other]), actor != other)
        self.assertEqual(from_snapshot(to_snapshot(state)), state)
        self.assertEqual(SCHEMA_VERSION, 12)

    def test_four_activations_and_barbarian_wrap(self):
        state = initial_state('v4'); ai = AiOrchestrator()
        actors = []
        for _ in range(5):
            actors.append(state.active_player_id)
            ai.run_active_ai_activation(state)
        self.assertEqual(actors, ['A', 'B', 'C', 'D', 'barbarians'])
        self.assertEqual((state.turn, state.active_player_id), (1, 'A'))
        self.assertEqual(set(ai.controllers), set('ABCD'))
        self.assertEqual({c.owner_id for c in state.cities.values()}, set('ABCD'))

    def test_multi_owner_strategic_state_and_validation(self):
        state = initial_state('v4')
        for actor, x, y in [('B', 6, 2), ('C', 6, 8), ('D', 10, 6)]:
            state.add_city(CityState('city-'+actor, actor, Position(x, y), name=actor))
            state.add_unit('A', UnitType.SCOUT, Position(x-1, y))
            state.add_unit(actor, UnitType.WARRIOR, Position(x, y))
        update_knowledge(state)
        view = StrategicStateBuilder().build(state, 'A')
        self.assertEqual({c['owner_id'] for c in view['enemy_cities']}, set('BCD'))
        self.assertEqual({u['owner_id'] for u in view['enemy_units']}, set('BCD'))
        self.assertEqual(canonical_json(view), canonical_json(StrategicStateBuilder().build(state, 'A')))
        for actor in 'BCD':
            plan = StrategicPlan(Posture.ATTACK, actor, 'city-'+actor)
            self.assertEqual(parse_plan(canonical_json(plan.to_dict()), view), plan)
        for enemy, city in [('missing', None), ('B', 'city-C'), ('A', None)]:
            with self.assertRaises(ValueError):
                parse_plan(canonical_json(StrategicPlan(Posture.ATTACK, enemy, city).to_dict()), view)
        for actor in 'ABCD':
            state.active_player_id = actor
            dto = public_state(state)
            self.assertEqual({p['id'] for p in dto['players']}, set('ABCD'))

    def test_eliminated_remembered_target_cannot_reenter_plan(self):
        state = initial_state('v4')
        state.players['A'].knowledge.explored_positions.add(Position(13, 2))
        state.players['A'].knowledge.discovered_cities['old'] = KnownCity('old', 'B', Position(13, 2))
        controller = AiController(HeuristicStrategyProvider(), previous_plan=StrategicPlan(Posture.ATTACK, 'B', 'old'), plan_creation_turn=0)
        state.eliminate_player('B')
        plan = controller.plan_for(state, 'A')
        self.assertIsNone(plan.primary_enemy_id)
        self.assertEqual(controller.last_trace['replan_reason'], 'invalid_target')
        self.assertIn('old', state.players['A'].knowledge.discovered_cities)
        self.assertTrue(known_enemy_cities(state, 'A'))
        self.assertTrue(StrategicStateBuilder().build(state, 'A')['enemy_cities'])
        # Schema v1 also permits a city target without a primary enemy ID.
        controller.previous_plan = StrategicPlan(Posture.ATTACK, None, 'old')
        self.assertIsNone(controller.plan_for(state, 'A').target_city_id)
        self.assertEqual(controller.last_trace['replan_reason'], 'invalid_target')
        with self.assertRaises(ValueError):
            parse_plan(canonical_json(StrategicPlan(Posture.ATTACK, 'B').to_dict()), StrategicStateBuilder().build(state, 'A'))

    def test_executor_pursues_each_rival(self):
        for enemy in 'BCD':
            state = initial_state('v4')
            state.units.clear()
            state.add_city(CityState('home', 'A', Position(2, 2), name='Home'))
            state.add_city(CityState('target', enemy, Position(6, 2), name='Target'))
            unit = state.add_unit('A', UnitType.WARRIOR, Position(5, 2))
            update_knowledge(state)
            result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK, enemy, 'target'))
            self.assertTrue(any(isinstance(c, MoveUnit) and c.unit_id == unit.id for c in result.commands_executed))
            self.assertEqual(state.cities['target'].owner_id, 'A')
            self.assertTrue(state.players[enemy].eliminated)
            self.assertIsNone(state.result)
            self.assertEqual(from_snapshot(to_snapshot(state)), state)

    def test_elimination_sequence_other_killer_and_terminal(self):
        state = initial_state('v4'); state.units.clear(); state.camps.clear()
        for actor, x, y in [('A', 2, 2), ('B', 6, 2), ('C', 10, 2), ('D', 13, 9)]:
            state.add_city(CityState('city-'+actor, actor, Position(x, y), name=actor))
        metrics = ConquestMetrics(state)
        # C eliminates B; A later inherits that conquest by eliminating C.
        for index, (killer, victim) in enumerate([('C', 'B'), ('A', 'C'), ('A', 'D')]):
            cities = [c for c in state.cities.values() if c.owner_id == victim]
            for city in cities:
                state.active_player_id = killer
                unit = state.add_unit(killer, UnitType.WARRIOR, Position(city.position.x-1, city.position.y))
                command = MoveUnit(killer, unit.id, city.position)
                metrics.observe('before', state, command, index)
                apply_command(state, command)
                metrics.observe('after', state, command, index)
                state.units.pop(unit.id)
            state.validate()
            self.assertEqual(len(state.civilization_ids), 3-index)
            self.assertEqual(from_snapshot(to_snapshot(state)), state)
            if index < 2: self.assertIsNone(state.result)
        total, players = metrics.finish(state)
        self.assertEqual(total['elimination_order'], ['B', 'C', 'D'])
        self.assertEqual(total['winnerPlayerId'], 'A')
        self.assertEqual(total['rivals_eliminated_by_winner'], 2)
        self.assertEqual(total['rivals_eliminated_by_other_civs'], 1)
        self.assertEqual(players['C']['captures_by_victim_civ'], {'B': 1})
        self.assertEqual(state.turn_order, ['A', 'barbarians'])
        with self.assertRaises(ValueError): apply_command(state, EndActivation('A'))

    def test_active_elimination_continues_without_skipping(self):
        state = initial_state('v4')
        state.active_player_id = 'B'; state.eliminate_player('B')
        self.assertEqual(state.active_player_id, 'C')
        state.active_player_id = 'D'; state.eliminate_player('D')
        self.assertEqual(state.active_player_id, 'barbarians')
        AiOrchestrator().run_active_ai_activation(state)
        self.assertEqual((state.turn, state.active_player_id), (1, 'A'))

    def test_benchmark_four_players_and_replay(self):
        with TemporaryDirectory() as directory:
            run = run_trial(HeuristicStrategyProvider(), provider_name='heuristic', turns=2,
                            settings=Settings(), directory=Path(directory)/'run', scenario_version='v4')
        self.assertEqual(set(run['players']), set('ABCD'))
        self.assertTrue(run['replay']['success'])
        self.assertTrue(run['metrics']['turnCapReached'])
        self.assertEqual(run['metrics']['cities_founded'], 4)
        self.assertEqual(run['metrics']['maximum_simultaneous_visible_enemy_civilizations'],
                         max(p['maximum_simultaneous_visible_enemy_civilizations']
                             for p in run['players'].values()))
        self.assertFalse(compare_runs(run, run)['playerRosterChanged'])
        for player in run['players'].values():
            self.assertIn('primary_enemy_switches', player)
            self.assertIn('multi_front_visibility_at_replans', player)

    def test_multifront_metric_definitions(self):
        from aig.ai.multifront_metrics import MultiFrontMetrics
        from types import SimpleNamespace
        state = initial_state('v4'); metrics = MultiFrontMetrics(state)
        view = StrategicStateBuilder().build(state, 'A')
        view['own_cities'] = [dict(id='home', x=2, y=2)]
        view['enemy_units'] = [dict(owner_id=p, strength=20, x=3, y=2) for p in 'BC']
        previous = None
        for turn, enemy in enumerate(['B', 'B', 'C', None, 'C']):
            plan = StrategicPlan(Posture.ATTACK, enemy, 'target-'+enemy if enemy else None)
            trace = dict(turn=turn, strategic_state=view, previous_plan=previous)
            metrics.record('A', SimpleNamespace(previous_plan=plan, last_trace=trace))
            previous = plan.to_dict()
        row = metrics.finish()['A']
        self.assertEqual(row['primary_enemy_switches'], 3)
        self.assertEqual(row['target_city_switches'], 3)
        self.assertEqual(row['consecutive_plans_same_primary_enemy'], [2, 1, 1])
        self.assertEqual(row['targeting_activations_by_rival'], {'B': 2, 'C': 2})
        self.assertEqual(row['maximum_simultaneous_visible_enemy_civilizations'], 2)
        self.assertEqual(row['multi_front_visibility_at_replans'][0][
            'own_cities_with_multiple_rivals_within_three_tiles'], {'home': ['B', 'C']})
        # Two viewers seeing two rivals each is a world maximum of two, not four.
        from aig.ai.benchmark_metrics import RunMetrics
        metrics.visibility['B'] = metrics.visibility['A']
        observed = RunMetrics(state, {}, SimpleNamespace(write=lambda row: None))
        observed.multifront = metrics
        self.assertEqual(observed.finish(state)[0]['maximum_simultaneous_visible_enemy_civilizations'], 2)


if __name__ == '__main__': unittest.main()
