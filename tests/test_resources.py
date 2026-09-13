"""Environment V3 economy, discovery and adversarial paired-world regressions."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from aig.ai.benchmark import benchmark, initial_state
from aig.ai.executor import AiExecutor
from aig.ai.benchmark_metrics import RunMetrics
from aig.ai.controller import AiController
from aig.ai.knowledge_planning import planning_view, exploration_path
from aig.ai.strategy import StrategicStateBuilder, HeuristicStrategyProvider
from aig.cities import found_city
from aig.commands import EndActivation, FoundCity, apply_command
from aig.economy import (Yields, terrain_yields, resource_yields, tile_yields,
                         city_center_yields, worked_positions, city_yields, resolve_player_economy)
from aig.knowledge import known_resources, update_knowledge, visible_positions
from aig.public_state import public_state, observer_state
from aig.scenarios import scenario_setup, SCENARIO_V2_RESOURCES
from aig.settings import Settings
from aig.setup import create_game, start_game
from aig.snapshots import to_snapshot, from_snapshot
from aig.state import ResourceType as R, Terrain as T, TileState, Position as P, UnitType, ControllerType


class ResourceRulesTests(unittest.TestCase):
    def test_exact_bonuses_and_all_terrain_combinations(self):
        expected = {R.WHEAT: Yields(1), R.CATTLE: Yields(1, 1), R.IRON: Yields(0, 2),
                    R.GEMS: Yields(0, 0, 3), R.SPICES: Yields(1, 0, 2)}
        self.assertEqual(set(R), set(expected))
        for terrain in T:
            self.assertEqual(tile_yields(TileState(P(0, 0), terrain)), terrain_yields(terrain))
            for resource, bonus in expected.items():
                with self.subTest(terrain=terrain, resource=resource):
                    self.assertEqual(resource_yields(resource), bonus)
                    if terrain.land_passable:
                        tile = TileState(P(0, 0), terrain, resource=resource)
                        self.assertEqual(tile_yields(tile), terrain_yields(terrain) + bonus)
                    else:
                        with self.assertRaises(ValueError):
                            TileState(P(0, 0), terrain, resource=resource)
        for bad in ('wheat', 1, [], [R.GEMS], False):
            with self.assertRaises(ValueError):
                TileState(P(0, 0), resource=bad)
            with self.assertRaises(ValueError):
                resource_yields(bad)

    def test_center_order_and_founding_preserves_resource(self):
        for terrain, resource, expected in ((T.GRASSLAND, R.WHEAT, Yields(3, 1)),
                                             (T.HILLS, R.IRON, Yields(2, 4))):
            state = initial_state('v1')
            tile = state.tiles[P(2, 2)]
            tile.terrain, tile.resource = terrain, resource
            found_city(state, 'unit-1', 'city', 'City')
            self.assertEqual(tile.resource, resource)
            self.assertEqual(city_center_yields(state, state.cities['city']), expected)

    def test_assignment_uses_food_production_gold_and_stable_ties(self):
        state = initial_state('v1')
        found_city(state, 'unit-1', 'city', 'City')
        city = state.cities['city']
        for y in range(1, 4):
            for x in range(1, 4):
                state.tiles[P(x,y)].terrain = T.GRASSLAND
        self.assertEqual(worked_positions(state, city), [P(1,1)])
        state.tiles[P(3,3)].resource = R.GEMS
        self.assertEqual(worked_positions(state, city), [P(3,3)])
        state.tiles[P(3,2)].resource = R.IRON
        self.assertEqual(worked_positions(state, city), [P(3,2)])
        state.tiles[P(2,3)].resource = R.WHEAT
        self.assertEqual(worked_positions(state, city), [P(2,3)])

    def test_all_resources_feed_normal_economy_every_activation(self):
        for resource in R:
            state = initial_state('v1')
            found_city(state, 'unit-1', 'city', 'City')
            city = state.cities['city']
            state.tiles[city.position].resource = resource
            for _ in range(3):
                before = (city.food_stored, city.production_stored, state.players['A'].gold)
                yields = city_yields(state, city)
                resolve_player_economy(state, 'A')
                self.assertEqual(city.production_stored, before[1] + yields.production)
                self.assertEqual(state.players['A'].gold, before[2] + yields.gold)
                state.validate()

    def test_multiple_resource_workings_aggregate(self):
        state = initial_state('v1')
        found_city(state, 'unit-1', 'city', 'City')
        city = state.cities['city']; city.population = 8
        plain = city_yields(state, city)
        positions = [city.position, *worked_positions(state, city)]
        for position, resource in zip(positions, R):
            state.tiles[position].resource = resource
        self.assertEqual(city_yields(state, city), plain + sum((resource_yields(r) for r in R), Yields()))


class ResourceKnowledgeTests(unittest.TestCase):
    def test_hidden_resource_does_not_change_any_decision_or_player_payload(self):
        state = initial_state('v1')
        state.players['A'].controller = ControllerType.HUMAN
        scout = state.add_unit('A', UnitType.SCOUT, P(2,2))
        hidden = P(11,1)
        self.assertNotIn(hidden, state.players['A'].knowledge.explored_positions)
        changed = deepcopy(state); changed.tiles[hidden].resource = R.GEMS
        builder = StrategicStateBuilder()
        a, b = builder.build(state,'A'), builder.build(changed,'A')
        self.assertEqual(a,b)
        self.assertEqual(HeuristicStrategyProvider().create_plan(a), HeuristicStrategyProvider().create_plan(b))
        self.assertEqual(public_state(state), public_state(changed))
        self.assertNotEqual(observer_state(state), observer_state(changed))
        self.assertEqual(planning_view(state,'A').tiles, planning_view(changed,'A').tiles)
        self.assertEqual(AiExecutor._settlement_path(state,state.units['unit-1']),
                         AiExecutor._settlement_path(changed,changed.units['unit-1']))
        self.assertEqual(exploration_path(planning_view(state,'A'),scout),
                         exploration_path(planning_view(changed,'A'),changed.units[scout.id]))
        restored = from_snapshot(to_snapshot(changed))
        self.assertEqual(public_state(restored), public_state(state))
        self.assertEqual(restored.tiles[hidden].resource, R.GEMS)

    def test_scout_and_warrior_discover_and_remember_without_economic_reward(self):
        for kind in (UnitType.SCOUT, UnitType.WARRIOR):
            state = initial_state('v1'); state.players['A'].controller = ControllerType.HUMAN
            position = P(11,1); state.tiles[position].resource = R.GEMS
            before_gold = state.players['A'].gold
            unit = state.add_unit('A', kind, P(10,1))
            self.assertIn(position, state.players['A'].knowledge.explored_positions)
            del state.units[unit.id]; update_knowledge(state)
            self.assertNotIn(position, visible_positions(state,'A'))
            self.assertIn('gems', [r['type'] for r in known_resources(state,'A')])
            self.assertEqual(state.players['A'].gold, before_gold)
            self.assertEqual(next(t for t in public_state(state)['map']['tiles'] if (t['x'],t['y']) == (11,1))['resource'], 'gems')
            self.assertEqual(known_resources(from_snapshot(to_snapshot(state)),'A'), known_resources(state,'A'))

    def test_known_resource_changes_settlement_target(self):
        state = initial_state('v1')
        # Equal all-grass candidates; a discovered food resource moves the best radius.
        for tile in state.tiles.values():
            if tile.terrain.land_passable: tile.terrain = T.GRASSLAND
        original = AiExecutor._settlement_path(state,state.units['unit-1'])
        state.tiles[P(4,4)].resource = R.WHEAT
        changed = AiExecutor._settlement_path(state,state.units['unit-1'])
        self.assertNotEqual(original[-1], changed[-1])
        copied = deepcopy(state)
        self.assertEqual(changed, AiExecutor._settlement_path(copied,copied.units['unit-1']))

    def test_snapshot_strict_canonical_and_detached(self):
        state = initial_state('v2'); snap = to_snapshot(state)
        self.assertEqual(snap['schema_version'],12)
        self.assertEqual(to_snapshot(from_snapshot(snap)),snap)
        restored = from_snapshot(snap); restored.tiles[P(2,2)].resource = None
        self.assertEqual(state.tiles[P(2,2)].resource,R.WHEAT)
        for bad in (9,8,True):
            broken = deepcopy(snap); broken['schema_version'] = bad
            with self.assertRaises(ValueError): from_snapshot(broken)
        for bad in ('unknown', [], True):
            broken = deepcopy(snap); broken['tiles'][0]['resource'] = bad
            with self.assertRaises(ValueError): from_snapshot(broken)


class ResourceScenarioTests(unittest.TestCase):
    def test_version_domains_and_environment_history(self):
        from aig import versions as v
        self.assertEqual(v.LATEST_ENVIRONMENT_VERSION, 'environment-v5')
        self.assertEqual(v.LATEST_SCENARIO_VERSION, 'scenario-v4')
        self.assertEqual(v.ENVIRONMENTS['environment-v2'],
            'Fog of war, persistent exploration and knowledge-safe planning; Chebyshev sight without LOS blocking.')
        for name in ('LATEST_STRATEGY_PROMPT_VERSION', 'LATEST_PLAN_SCHEMA_VERSION',
                     'LATEST_QWEN_CONFIG_VERSION', 'LATEST_LUNA_CONFIG_VERSION', 'LATEST_BENCHMARK_VERSION'):
            self.assertTrue(getattr(v, name).endswith('-v1'))
        with self.assertRaises(TypeError): v.ENVIRONMENTS['environment-v3'] = 'changed'

    def test_geometry_layout_validation_and_starting_opportunities(self):
        old,new = scenario_setup('v1'),scenario_setup('v2')
        self.assertEqual(replace(new,resources=()),old)
        self.assertEqual(set(r for _,r in new.resources),set(R))
        self.assertEqual(len(new.resources),len(set(p for p,_ in new.resources)))
        self.assertEqual(new,scenario_setup('v2'))
        from aig.ai.benchmark import canonical_hash
        historical = to_snapshot(initial_state('v2'))
        historical['schema_version'] = 10
        historical.pop('result')
        for player in historical['players']: player.pop('has_ever_owned_city')
        historical.pop('camps')
        for unit in historical['units']: unit.pop('home_camp_id')
        for player in historical['players']:
            player.pop('kind')
            player['knowledge'].pop('discovered_camps')
        self.assertEqual(canonical_hash(historical),
                         '95b5c4355a587e4d9473d7636488ea21c5d962e1e25f4bae3b887a12fba837ae')
        state=create_game(new)
        self.assertFalse(known_resources(state,'A'))
        start_game(state)
        for actor in state.players:
            self.assertGreater(len(known_resources(state,actor)),0)
            self.assertLess(len(known_resources(state,actor)),len(new.resources))
        with self.assertRaises(ValueError): replace(new,resources=((P(6,1),R.GEMS),))
        with self.assertRaises(ValueError): replace(new,resources=(new.resources[0],new.resources[0]))

    def test_frozen_artifacts_unchanged(self):
        root=Path(__file__).resolve().parents[1]
        hashes=json.loads((root/'tests/fixtures/environment-v3-preserved-artifacts.json').read_text())
        checked=0
        for name,expected in hashes.items():
            path=root/name
            if path.exists():
                payload = path.read_bytes()
                if name == 'docs/baselines.md':
                    payload = payload.split(b'\n## Scenario V4 (Environment V5)', 1)[0]
                self.assertEqual(hashlib.sha256(payload).hexdigest(),expected,name)
                checked+=1
        self.assertGreater(checked,0)

    def test_resource_benchmark_and_replay(self):
        with TemporaryDirectory() as folder:
            report=benchmark(output=Path(folder)/'run',turns=20,settings=Settings(),
                             environment_version='v5',scenario_version='v2')
        a,b=report['runs']
        self.assertEqual(a['hashes'],b['hashes'])
        self.assertEqual(a['experiment']['environmentVersion'],'environment-v5')
        self.assertEqual(a['experiment']['scenarioVersion'],'scenario-v2')
        self.assertEqual(a['inference']['requests'],0)
        self.assertGreater(a['metrics']['resource_tiles_discovered'],0)
        self.assertGreater(a['metrics']['resource_bonus_food'],0)
        self.assertGreater(a['metrics']['resource_tiles_worked'],0)
        self.assertGreater(a['metrics']['cities_founded_near_known_resources'],0)


class ResourceObservationTests(unittest.TestCase):
    def test_actual_pre_growth_bonus_accounting_and_unique_worked_tiles(self):
        state = initial_state('v1')
        found_city(state, 'unit-1', 'city', 'City')
        city = state.cities['city']; city.population = 8
        positions = [city.position, *worked_positions(state,city)]
        for position, resource in zip(positions,R): state.tiles[position].resource = resource
        controller = AiController(HeuristicStrategyProvider())
        controller.plan_for(state,'A')
        metrics = RunMetrics(state, {'A': controller}, Mock())
        command = EndActivation('A')
        expected = sum((resource_yields(r) for r in R), Yields())
        for _ in range(2):
            # Start another A activation without resolving B's irrelevant economy.
            state.active_player_id = 'A'
            metrics.observe('before',state,command)
            before_gold = state.players['A'].gold
            apply_command(state,command)
            metrics.observe('after',state,command)
            self.assertEqual(state.players['A'].gold-before_gold,expected.gold)
            self.assertEqual(metrics.pending['outcome']['resource_bonus_yields'],
                             dict(food=expected.food,production=expected.production,gold=expected.gold))
        _, players = metrics.finish(state)
        self.assertEqual(players['A']['resource_tiles_worked'],5)
        self.assertEqual(players['A']['resource_tile_workings'],10)
        self.assertEqual(players['A']['activations_working_resources'],2)
        for field in ('food','production','gold'):
            self.assertEqual(players['A']['resource_bonus_'+field],2*getattr(expected,field))

    def test_scout_spawn_resource_attribution_and_first_discovery(self):
        state=initial_state('v1')
        found_city(state,'unit-1','city','City')
        state.tiles[P(5,2)].resource=R.GEMS
        city=state.cities['city']; city.production_target=UnitType.SCOUT; city.production_stored=20
        controller=AiController(HeuristicStrategyProvider()); controller.plan_for(state,'A')
        metrics=RunMetrics(state,{'A':controller},Mock())
        command=EndActivation('A')
        metrics.observe('before',state,command); apply_command(state,command); metrics.observe('after',state,command)
        _,players=metrics.finish(state)
        self.assertEqual(players['A']['resource_discoveries_by_scouts'],1)
        self.assertEqual(players['A']['resource_discoveries_by_type'],{'gems':1})
        self.assertEqual(players['A']['first_resource_discovered'],{'turn':0,'activation':0})
        self.assertEqual(players['A']['resource_bonus_gold'],0)
        self.assertEqual(metrics.pending['outcome']['resource_discoveries']['A'][0]['type'],'gems')

    def test_founding_counts_only_resources_known_before_founding(self):
        state=initial_state('v2')
        metrics=RunMetrics(state,{},Mock())
        command=FoundCity('A','unit-1','city','City')
        metrics.observe('before',state,command); apply_command(state,command); metrics.observe('after',state,command)
        self.assertEqual(metrics.players['A']['known_resources_in_radius_at_founding'],2)
        self.assertEqual(metrics.players['A']['city_center_resources_used'],1)
        self.assertEqual(metrics.founded[0]['center_resource'],'wheat')

    def test_resource_discovery_does_not_force_replan(self):
        state=initial_state('v1')
        controller=AiController(HeuristicStrategyProvider())
        first=controller.plan_for(state,'A')
        state.tiles[P(5,2)].resource=R.GEMS
        state.add_unit('A',UnitType.SCOUT,P(2,2))
        self.assertEqual(controller.plan_for(state,'A'),first)
        self.assertIsNone(controller.last_trace)
