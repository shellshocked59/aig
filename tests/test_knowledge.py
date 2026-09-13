"""Environment V2 information boundaries, domain events and adversarial worlds."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from aig.ai.benchmark import benchmark, canonical_hash, initial_state
from aig.ai.controller import AiController
from aig.ai.executor import AiExecutor
from aig.ai.knowledge_planning import exploration_path, planning_view
from aig.ai.strategy import HeuristicStrategyProvider, Posture, StrategicPlan, StrategicStateBuilder
from aig.cities import found_city
from aig.combat import attack_unit
from aig.commands import MoveUnit, apply_command
from aig.economy import resolve_player_economy
from aig.knowledge import (is_explored, is_visible, known_enemy_cities, update_knowledge,
                           visible_enemy_units, visible_positions, vision_positions, vision_range)
from aig.movement import find_path, move_unit
from aig.public_state import observer_state, public_state
from aig.scenarios import scenario_setup
from aig.settings import Settings
from aig.setup import create_game, start_game
from aig.snapshots import SCHEMA_VERSION, from_snapshot, to_snapshot
from aig.state import CityState, ControllerType, GameConfig, GameMap, GameState, KnownCity, PlayerState, Position, Terrain, TileState, UnitType
from aig.versions import ENVIRONMENTS, resolve_version


def world():
    return GameState(GameConfig(42), game_map=GameMap(15, 11),
        players={p: PlayerState(p, ControllerType.AI) for p in 'AB'},
        turn_order=['A', 'B'], active_player_id='A',
        tiles={Position(x, y): TileState(Position(x, y)) for y in range(11) for x in range(15)})


def unit(state, kind=UnitType.WARRIOR, owner='A', x=3, y=3):
    return state.add_unit(owner, kind, Position(x, y))


def city(state, owner='B', x=6, y=3, name='enemy'):
    return state.add_city(CityState(name, owner, Position(x, y), name='Secret name'))


def view(state, actor='A'):
    return StrategicStateBuilder().build(state, actor)


class VisionTests(unittest.TestCase):
    def test_all_unit_ranges_and_diagonals(self):
        for kind in UnitType:
            with self.subTest(kind=kind):
                state = world()
                u = unit(state, kind, x=7, y=5)
                radius = 3 if kind is UnitType.SCOUT else 2
                self.assertEqual(vision_range(kind), radius)
                self.assertEqual(len(visible_positions(state, 'A')), (2 * radius + 1) ** 2)
                self.assertTrue(is_visible(state, 'A', Position(7 + radius, 5 + radius)))
                self.assertFalse(is_visible(state, 'A', Position(8 + radius, 5)))

    def test_city_radius_two(self):
        state = world()
        city(state, 'A', 7, 5)
        self.assertEqual(len(visible_positions(state, 'A')), 25)

    def test_bounds_negative_origin_and_clipping(self):
        bounds = GameMap(5, 4, Position(-4, -3))
        self.assertEqual(len(vision_positions(bounds, bounds.origin, 2)), 9)
        self.assertTrue(all(bounds.contains(p) for p in vision_positions(bounds, Position(0, 0), 3)))

    def test_no_terrain_sight_modifiers(self):
        for terrain in Terrain:
            state = world()
            unit(state)
            for p in (Position(4, 3), Position(4, 4)):
                state.tiles[p].terrain = terrain
            self.assertTrue(is_visible(state, 'A', Position(5, 5)), terrain)

    def test_create_empty_and_start_both_factions(self):
        state = create_game(scenario_setup())
        self.assertTrue(all(not p.knowledge.explored_positions for p in state.players.values()))
        start_game(state)
        for actor in 'AB':
            self.assertEqual(state.players[actor].knowledge.explored_positions, visible_positions(state, actor))
            self.assertEqual(len(state.players[actor].knowledge.explored_positions), 25)
        self.assertFalse(is_explored(state, 'A', Position(11, 0)))

    def test_move_reveals_and_old_exploration_persists(self):
        state = world()
        u = unit(state)
        old = set(state.players['A'].knowledge.explored_positions)
        move_unit(state, u.id, Position(4, 3))
        self.assertGreater(len(state.players['A'].knowledge.explored_positions), len(old))
        self.assertTrue(old <= state.players['A'].knowledge.explored_positions)
        self.assertFalse(is_visible(state, 'A', Position(1, 3)))
        self.assertTrue(is_explored(state, 'A', Position(1, 3)))

    def test_scout_reveals_more_than_warrior(self):
        counts = []
        for kind in (UnitType.WARRIOR, UnitType.SCOUT):
            state = world()
            u = unit(state, kind, x=7, y=5)
            before = len(state.players['A'].knowledge.explored_positions)
            move_unit(state, u.id, Position(8, 5))
            counts.append(len(state.players['A'].knowledge.explored_positions) - before)
        self.assertGreater(counts[1], counts[0])

    def test_unit_death_shrinks_sight_but_not_memory(self):
        state = world()
        victim = unit(state, UnitType.SETTLER)
        attacker = unit(state, owner='B', x=4)
        before = deepcopy(state.players['A'].knowledge)
        attack_unit(state, attacker.id, victim.id)
        self.assertFalse(visible_positions(state, 'A'))
        self.assertEqual(state.players['A'].knowledge, before)

    def test_produced_scout_reveals_from_city(self):
        state = world()
        c = city(state, 'A', 7, 5)
        c.production_target, c.production_stored = UnitType.SCOUT, 20
        resolve_player_economy(state, 'A')
        self.assertEqual(len(state.players['A'].knowledge.explored_positions), 49)

    def test_founding_keeps_vision_after_consuming_settler(self):
        state = world()
        u = unit(state, UnitType.SETTLER)
        # Exercise domain mutation without a controller initializing knowledge.
        state.players['A'].knowledge.explored_positions.clear()
        found_city(state, u.id, 'home', 'Home')
        self.assertEqual(state.players['A'].knowledge.explored_positions, visible_positions(state, 'A'))
        self.assertEqual(len(visible_positions(state, 'A')), 25)


class CityKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.state = world()
        self.u = unit(self.state)
        self.c = city(self.state)
        city(self.state, 'B', 12, 8, name='reserve')

    def discover(self):
        move_unit(self.state, self.u.id, Position(4, 3))

    def hide(self):
        self.u.moves_remaining = 1
        move_unit(self.state, self.u.id, Position(3, 3))

    def test_undiscovered_city_absent(self):
        self.assertEqual(known_enemy_cities(self.state, 'A'), [])
        self.assertEqual(view(self.state)['enemy_cities'], [])

    def test_visible_city_discovered_and_remembered(self):
        self.discover()
        self.assertEqual(known_enemy_cities(self.state, 'A')[0]['population'], 1)
        self.hide()
        self.c.population, self.c.production_stored = 9, 1234
        self.c.production_target = UnitType.ARCHER
        memory = known_enemy_cities(self.state, 'A')[0]
        self.assertEqual(memory, dict(id='enemy', owner_id='B', x=6, y=3, currently_visible=False, live_exists=None))
        self.assertEqual(view(self.state)['enemy_cities'], [memory])

    def test_known_city_record_immutable(self):
        self.discover()
        with self.assertRaises(FrozenInstanceError):
            self.state.players['A'].knowledge.discovered_cities['enemy'].owner_id = 'A'

    def test_explored_empty_tile_does_not_discover_later_hidden_city(self):
        self.state.remove_city('enemy')
        self.discover()
        self.hide()
        city(self.state)
        self.assertTrue(is_explored(self.state, 'A', Position(6, 3)))
        self.assertFalse(known_enemy_cities(self.state, 'A'))

    def test_hidden_removal_unknown_until_site_seen(self):
        self.discover()
        self.hide()
        self.state.remove_city('enemy')
        self.assertIsNone(known_enemy_cities(self.state, 'A')[0]['live_exists'])
        self.u.moves_remaining = 1
        self.discover()
        self.assertIs(known_enemy_cities(self.state, 'A')[0]['live_exists'], False)
        self.assertIn('enemy', self.state.players['A'].knowledge.discovered_cities)

    def test_elimination_retains_both_factions_history(self):
        self.discover()
        memories = {p: deepcopy(s.knowledge) for p, s in self.state.players.items()}
        self.state.eliminate_player('B')
        self.assertEqual({p: s.knowledge for p, s in self.state.players.items()}, memories)
        self.assertFalse(visible_positions(self.state, 'B'))
        self.assertFalse(known_enemy_cities(self.state, 'A')[0]['live_exists'])

    def test_query_does_not_discover(self):
        self.u.position = Position(4, 3)
        before = to_snapshot(self.state)
        self.assertTrue(known_enemy_cities(self.state, 'A'))
        self.assertEqual(to_snapshot(self.state), before)


class InformationBoundaryTests(unittest.TestCase):
    def test_unexplored_sparse_map_holes_do_not_leak_through_public_tiles(self):
        state = world()
        state.players['A'].controller = ControllerType.HUMAN
        unit(state)
        before = public_state(state)
        del state.tiles[Position(14, 10)]
        state.validate()
        self.assertEqual(public_state(state), before)

    def test_hidden_units_hp_positions_and_stacks_absent_global_strength_preserved(self):
        state = world()
        unit(state)
        enemy = unit(state, owner='B', x=12, y=8)
        self.assertFalse(view(state)['enemy_units'])
        self.assertEqual(view(state)['enemy_military_strength'], 20)
        self.assertEqual(view(state)['visible_enemy_military_strength'], 0)
        enemy.position = Position(5, 3)
        enemy.hp = 50
        self.assertEqual(view(state)['enemy_units'][0]['hp'], 50)
        self.assertEqual(view(state)['nearest_visible_enemy_unit_distance'], 2)
        enemy.position = Position(12, 8)
        self.assertFalse(visible_enemy_units(state, 'A'))
        self.assertFalse(view(state)['enemy_units'])

    def test_hidden_terrain_and_deployment_do_not_change_provider_inputs(self):
        state = world()
        unit(state)
        enemy = unit(state, owner='B', x=12, y=8)
        first = view(state)
        for p, tile in state.tiles.items():
            if not is_explored(state, 'A', p) and p != enemy.position:
                tile.terrain = Terrain.FOREST
        enemy.position = Position(13, 8)
        self.assertEqual(view(state), first)
        provider = HeuristicStrategyProvider()
        self.assertEqual(provider.create_plan(first), provider.create_plan(view(state)))
        self.assertIsNone(provider.create_plan(first).target_city_id)

    def test_visible_threat_changes_heuristic(self):
        state = world()
        unit(state)
        city(state, 'A', 3, 3, 'home')
        enemies = [unit(state, owner='B', x=12, y=8) for _ in range(3)]
        self.assertEqual(HeuristicStrategyProvider().create_plan(view(state)).posture, Posture.EXPAND)
        for enemy in enemies:
            enemy.position = Position(5, 3)
        self.assertEqual(HeuristicStrategyProvider().create_plan(view(state)).posture, Posture.DEFEND)

    def test_own_state_complete_and_canonical(self):
        state = initial_state("v3")
        own = view(state)
        self.assertEqual(len(own['own_units']), 2)
        self.assertEqual(len(own['explored_terrain']), 25)
        self.assertEqual(json.loads(json.dumps(own)), own)
        state.tiles = dict(reversed(list(state.tiles.items())))
        state.units = dict(reversed(list(state.units.items())))
        self.assertEqual(view(state), own)

    def test_public_and_observer_separate(self):
        state = world()
        state.players['A'].controller = ControllerType.HUMAN
        u = unit(state)
        enemy = unit(state, owner='B', x=12, y=8)
        move_unit(state, u.id, Position(4, 3))
        dto = public_state(state)
        tiles = {(t['x'], t['y']): t for t in dto['map']['tiles']}
        self.assertEqual((tiles[12, 8]['terrain'], tiles[12, 8]['visible'], tiles[12, 8]['explored']), (None, False, False))
        self.assertEqual((tiles[1, 3]['terrain'], tiles[1, 3]['visible'], tiles[1, 3]['explored']), ('grassland', False, True))
        self.assertTrue(tiles[4, 3]['visible'])
        self.assertNotIn(enemy.id, [u['id'] for u in dto['units']])
        self.assertIn(enemy.id, [u['id'] for u in observer_state(state)['units']])

    def test_hotseat_switches_perspective_and_ai_only_has_no_browser_truth(self):
        state = initial_state("v3")
        self.assertEqual(public_state(state)['units'], [])
        for player in state.players.values():
            if not state.is_barbarian(player.id):
                player.controller = ControllerType.HUMAN
        state.active_player_id = 'B'
        self.assertEqual(public_state(state)['viewerPlayerId'], 'B')
        self.assertTrue(all(u['ownerId'] == 'B' for u in public_state(state)['units']))

    def test_public_hidden_city_has_no_live_details_or_tile_owner_leak(self):
        state = world()
        state.players['A'].controller = ControllerType.HUMAN
        u = unit(state, x=4)
        c = city(state)
        move_unit(state, u.id, Position(3, 3))
        c.population = 17
        dto = public_state(state)
        self.assertEqual(set(dto['cities'][0]), {'id', 'ownerId', 'x', 'y', 'currentlyVisible', 'liveExists'})


class PlanningTests(unittest.TestCase):
    def test_invisible_units_and_cities_do_not_change_command_choice(self):
        state = world()
        u = unit(state)
        other = deepcopy(state)
        unit(other, owner='B', x=12, y=8)
        city(other, x=12, y=8)
        chosen = StrategicPlan(Posture.ATTACK, 'B', 'enemy')
        self.assertEqual(AiExecutor().execute(state, chosen).commands_executed,
                         AiExecutor().execute(other, chosen).commands_executed)

    def test_frontier_ignores_hidden_yields_and_blockers(self):
        state = world()
        scout = unit(state, UnitType.SCOUT)
        safe = planning_view(state, 'A')
        path = exploration_path(safe, scout)
        self.assertTrue(path)
        other = deepcopy(state)
        for p, tile in other.tiles.items():
            if p not in safe.explored:
                tile.terrain = Terrain.MOUNTAINS
        self.assertEqual(exploration_path(planning_view(other, 'A'), other.units[scout.id]), path)

    def test_paths_do_not_use_authoritative_failures_as_an_oracle(self):
        state = world()
        scout = unit(state, UnitType.SCOUT)
        with patch.object(GameState, 'can_enter', side_effect=AssertionError('truth queried')):
            path = exploration_path(planning_view(state, 'A'), scout)
        self.assertTrue(path)

    def test_frontier_maximizes_geometry_reveal_and_deterministic_ties(self):
        state = world()
        scout = unit(state, UnitType.SCOUT)
        safe = planning_view(state, 'A')
        path = exploration_path(safe, scout)
        expected = max(len(vision_positions(state.game_map, p, 3) - safe.explored)
                       for p in safe.tiles if safe.can_enter('A', p))
        self.assertEqual(len(vision_positions(state.game_map, path[-1], 3) - safe.explored), expected)
        safe.tiles = dict(reversed(list(safe.tiles.items())))
        self.assertEqual(exploration_path(safe, scout), path)

    def test_scout_moves_adjacent_steps_and_explores(self):
        state = world()
        scout = unit(state, UnitType.SCOUT)
        before = len(state.players['A'].knowledge.explored_positions)
        origin = scout.position
        result = AiExecutor().execute(state, StrategicPlan(Posture.EXPAND))
        moves = [c for c in result.commands_executed if isinstance(c, MoveUnit)]
        self.assertEqual(len(moves), 2)
        for move in moves:
            self.assertEqual(max(abs(move.destination.x-origin.x), abs(move.destination.y-origin.y)), 1)
            origin = move.destination
        self.assertGreater(len(state.players['A'].knowledge.explored_positions), before)

    def test_fully_explored_scout_does_not_loop(self):
        state = world()
        scout = unit(state, UnitType.SCOUT)
        state.players['A'].knowledge.explored_positions.update(state.tiles)
        self.assertIsNone(exploration_path(planning_view(state, 'A'), scout))
        result = AiExecutor().execute(state, StrategicPlan(Posture.EXPAND))
        self.assertFalse(any(isinstance(c, MoveUnit) for c in result.commands_executed))

    def test_authoritative_command_still_rejects_impassable_move(self):
        state = world()
        u = unit(state)
        state.tiles[Position(4, 3)].terrain = Terrain.MOUNTAINS
        before = to_snapshot(state)
        with self.assertRaises(ValueError):
            apply_command(state, MoveUnit('A', u.id, Position(4, 3)))
        self.assertEqual(to_snapshot(state), before)


class ReplanningTests(unittest.TestCase):
    def test_tiles_reuse_five_turn_plan_and_city_discovery_replans_once(self):
        state = world()
        u = unit(state)
        city(state)
        controller = AiController(HeuristicStrategyProvider())
        first = controller.plan_for(state, 'A')
        move_unit(state, u.id, Position(3, 4))
        self.assertIs(controller.plan_for(state, 'A'), first)
        u.moves_remaining = 1
        move_unit(state, u.id, Position(4, 4))
        controller.plan_for(state, 'A')
        self.assertEqual(controller.last_trace['replan_reason'], 'first_enemy_city_discovered')
        controller.plan_for(state, 'A')
        self.assertIsNone(controller.last_trace)
        state.turn = 5
        controller.plan_for(state, 'A')
        self.assertEqual(controller.last_trace['replan_reason'], 'expired')

    def test_first_military_contact_bounded(self):
        state = world()
        unit(state)
        enemy = unit(state, owner='B', x=12, y=8)
        provider = Mock(wraps=HeuristicStrategyProvider())
        controller = AiController(provider)
        controller.plan_for(state, 'A')
        enemy.position = Position(5, 3)
        controller.plan_for(state, 'A')
        self.assertEqual(controller.last_trace['replan_reason'], 'first_enemy_military_contact')
        for _ in range(10):
            enemy.position = Position(12, 8)
            controller.plan_for(state, 'A')
            enemy.position = Position(5, 3)
            controller.plan_for(state, 'A')
        self.assertEqual(provider.create_plan.call_count, 2)

    def test_hidden_target_removal_does_not_invalidate_plan(self):
        state = world()
        u = unit(state, x=4)
        city(state)
        controller = AiController(HeuristicStrategyProvider())
        controller.plan_for(state, 'A')
        move_unit(state, u.id, Position(3, 3))
        city(state, 'B', 12, 8, name='reserve')
        state.remove_city('enemy')
        controller.plan_for(state, 'A')
        self.assertIsNone(controller.last_trace)


class PersistenceTests(unittest.TestCase):
    def test_roundtrip_canonical_memory_without_current_visibility(self):
        state = world()
        u = unit(state, x=4)
        city(state)
        move_unit(state, u.id, Position(3, 3))
        snapshot = to_snapshot(state)
        restored = from_snapshot(json.loads(json.dumps(snapshot)))
        self.assertEqual(state, restored)
        self.assertEqual(SCHEMA_VERSION, 12)
        self.assertNotIn('visible', json.dumps(snapshot))
        self.assertEqual(visible_positions(state, 'A'), visible_positions(restored, 'A'))
        knowledge = snapshot['players'][0]['knowledge']
        self.assertEqual(knowledge['explored_positions'], sorted(knowledge['explored_positions'], key=lambda p: (p['y'], p['x'])))

    def test_loading_never_reveals_or_discovers(self):
        state = world()
        u = unit(state)
        city(state)
        u.position = Position(4, 3)
        before = to_snapshot(state)
        restored = from_snapshot(before)
        self.assertEqual(to_snapshot(restored), before)
        self.assertNotIn('enemy', restored.players['A'].knowledge.discovered_cities)

    def test_v8_explicitly_unsupported(self):
        snapshot = to_snapshot(initial_state("v3"))
        snapshot['schema_version'] = 8
        with self.assertRaisesRegex(ValueError, 'unsupported schema_version'):
            from_snapshot(snapshot)

    def test_invalid_knowledge_rejected(self):
        snapshot = to_snapshot(initial_state("v3"))
        for mutate in (
            lambda k: k['explored_positions'].append(k['explored_positions'][0]),
            lambda k: k['explored_positions'].append(dict(x=100, y=100)),
            lambda k: k.update(visible_positions=[]),
            lambda k: k['discovered_cities'].append(dict(city_id='bad', owner_id='Z', position=dict(x=1, y=1))),
        ):
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                changed = deepcopy(snapshot)
                mutate(changed['players'][0]['knowledge'])
                from_snapshot(changed)

    def test_multiple_memories_canonical_and_retained_after_elimination(self):
        state = world()
        unit(state, UnitType.SCOUT, x=7, y=5)
        city(state, x=9, y=3, name='z-last')
        city(state, x=6, y=3, name='a-first')
        state.eliminate_player('B')
        snapshot = to_snapshot(state)
        memories = snapshot['players'][0]['knowledge']['discovered_cities']
        self.assertEqual([c['city_id'] for c in memories], ['a-first', 'z-last'])
        self.assertEqual(to_snapshot(from_snapshot(snapshot)), snapshot)


class ArtifactTests(unittest.TestCase):
    def test_v1_metadata_unchanged_and_v2_registered(self):
        from aig.versions import LATEST_ENVIRONMENT_VERSION
        self.assertEqual(ENVIRONMENTS['environment-v1'], 'Original deterministic full-information environment; no fog of war.')
        self.assertEqual(resolve_version('v2', available=ENVIRONMENTS, latest='environment-v2'), 'environment-v2')
        self.assertEqual(LATEST_ENVIRONMENT_VERSION, 'environment-v5')

    def test_v1_provenance_resolves_but_cannot_mislabel_current_run(self):
        from aig.ai.experiments import experiment_manifest
        old = experiment_manifest(provider='heuristic', settings=Settings(), environment_version='v1')
        self.assertEqual(old['environmentVersion'], 'environment-v1')
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'invalid'
            with self.assertRaisesRegex(ValueError, 'provenance only'):
                benchmark(output=output, turns=1, settings=Settings(), environment_version='v1')
            self.assertFalse(output.exists())

    def test_local_frozen_baseline_bytes_when_available(self):
        root = Path(__file__).resolve().parents[1]
        hashes = json.loads((root / 'tests/fixtures/environment-v1-artifact-hashes.json').read_text())
        if not all((root / name).exists() for name in hashes):
            self.skipTest('Frozen local experiment archives are not part of the source checkout')
        for name, expected in hashes.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected)


class BenchmarkKnowledgeTests(unittest.TestCase):
    def test_scout_spawn_attribution_and_no_double_counting(self):
        from aig.ai.benchmark_metrics import RunMetrics
        from aig.commands import EndActivation
        state = world()
        c = city(state, 'A', 7, 5, 'home')
        c.production_target, c.production_stored = UnitType.SCOUT, 20
        controller = Mock(previous_plan=StrategicPlan(Posture.EXPAND))
        metrics = RunMetrics(state, {'A': controller}, Mock())
        command = EndActivation('A')
        metrics.observe('before', state, command)
        apply_command(state, command)
        metrics.observe('after', state, command)
        self.assertEqual(metrics.players['A']['tiles_newly_revealed_by_scouts'], 24)
        self.assertEqual(metrics.players['A']['tiles_newly_revealed'], 24)

    def test_100_turn_exploration_contacts_scout_attribution_and_replay(self):
        from aig.commands import AttackUnit, EndActivation, FoundCity, SetCityProduction, SetResearch
        from aig.state import Technology
        constructors = {c.__name__: c for c in (AttackUnit, EndActivation, FoundCity, MoveUnit,
                                                SetCityProduction, SetResearch)}
        with TemporaryDirectory() as directory, patch('socket.create_connection', side_effect=AssertionError('network forbidden')):
            root = Path(directory)
            report = benchmark(output=root / 'run', turns=100, settings=Settings(), environment_version='v5')
            self.assertEqual(report['runs'][0]['hashes'], report['runs'][1]['hashes'])
            for run in report['runs']:
                self.assertEqual(run['experiment']['environmentVersion'], 'environment-v5')
                self.assertGreater(run['metrics']['scout_movement_commands'], 0)
                self.assertGreater(run['metrics']['tiles_newly_revealed_by_scouts'], 0)
                self.assertGreater(run['metrics']['significant_discovery_replans'], 0)
                for player in run['players'].values():
                    self.assertGreater(player['explored_tile_count'], 25)
                    self.assertGreater(player['map_explored_percent'], 25 / 120 * 100)
                    self.assertIsNotNone(player['first_contacts']['enemy_unit'])
                    self.assertTrue(player['visibility_at_replans'])
                self.assertTrue(any(p['first_contacts']['enemy_city'] for p in run['players'].values()))
                trace_dir = root / 'run' / run['directory']
                replay = from_snapshot(json.loads((trace_dir / 'initial-state.json').read_text()))
                for line in (trace_dir / 'commands.jsonl').read_text().splitlines():
                    row = json.loads(line)['command']
                    kind = row.pop('type')
                    if kind == 'MoveUnit':
                        row['destination'] = Position(**row['destination'])
                    if kind == 'SetCityProduction' and row['unit_type']:
                        row['unit_type'] = UnitType(row['unit_type'])
                    if kind == 'SetResearch' and row['technology']:
                        row['technology'] = Technology(row['technology'])
                    apply_command(replay, constructors[kind](**row))
                self.assertEqual(canonical_hash(to_snapshot(replay)), run['hashes']['final_state'])
                for line in (trace_dir / 'plans.jsonl').read_text().splitlines():
                    row = json.loads(line)
                    target = row['new_plan']['target_city_id']
                    if target is not None:
                        self.assertIn(target, [c['id'] for c in row['strategic_state']['enemy_cities']])

    def test_global_identity_is_valid_without_tactical_contact(self):
        from aig.ai.plan_schema import parse_plan, canonical_json
        state = initial_state("v3")
        chosen = StrategicPlan(Posture.ATTACK, 'B')
        self.assertEqual(parse_plan(canonical_json(chosen.to_dict()), view(state)), chosen)
