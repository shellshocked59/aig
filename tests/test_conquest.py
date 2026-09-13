"""V5 authoritative capture, terminal lifecycle, fog and replay contracts."""

from copy import deepcopy
import unittest

from aig.ai.conquest_metrics import ConquestMetrics
from aig.ai.executor import AiExecutor
from aig.ai.knowledge_planning import planning_view
from aig.ai.strategy import Posture, StrategicPlan, StrategicStateBuilder
from aig.commands import MoveUnit, EndActivation, SetCityProduction, apply_command
from aig.combat import attack_unit
from aig.knowledge import update_knowledge, known_enemy_cities
from aig.movement import find_path
from aig.public_state import public_state, observer_state
from aig.snapshots import to_snapshot, from_snapshot
from aig.state import (GameState, GameConfig, GameMap, PlayerState, ControllerType,
                       Position, TileState, CityState, UnitType, FactionKind,
                       GameResult, VictoryType, KnownCity, are_hostile)


def capture_state(kind=UnitType.WARRIOR, *, third=False):
    ids = ['A', 'B', 'C'] if third else ['A', 'B']
    state = GameState(GameConfig(42), game_map=GameMap(15, 7),
                      players={p: PlayerState(p, ControllerType.AI) for p in ids},
                      turn_order=ids,
                      tiles={Position(x, y): TileState(Position(x, y))
                             for y in range(7) for x in range(15)})
    state.add_city(CityState('town', 'B', Position(3, 2), name='Original', population=3,
                             food_stored=7, production_stored=19, production_target=UnitType.WARRIOR))
    state.add_unit('A', kind, Position(2, 2))
    state.add_unit('B', UnitType.SETTLER, Position(8, 2))
    state.add_unit('B', UnitType.WARRIOR, Position(9, 2))
    state.active_player_id = 'A'
    update_knowledge(state)
    return state


class CaptureTests(unittest.TestCase):
    def capture(self, state):
        apply_command(state, MoveUnit('A', 'unit-1', Position(3, 2)))

    def test_eligible_types_reset_preserve_and_win(self):
        for kind in (UnitType.WARRIOR, UnitType.SCOUT, UnitType.SPEARMAN):
            with self.subTest(kind=kind):
                state = capture_state(kind)
                city = state.cities['town']
                from aig.state import ResourceType
                state.tiles[city.position].resource = ResourceType.WHEAT
                state.tiles[Position(4, 2)].owner_id = 'B'
                old_knowledge = deepcopy(state.players['B'].knowledge)
                self.capture(state)
                self.assertIs(state.cities['town'], city)
                self.assertEqual((city.owner_id, city.name, city.population), ('A', 'Original', 2))
                self.assertEqual((city.food_stored, city.production_stored, city.production_target), (0, 0, None))
                self.assertEqual(state.units['unit-1'].position, city.position)
                self.assertEqual(state.tiles[city.position].owner_id, 'A')
                self.assertEqual(state.tiles[city.position].resource, ResourceType.WHEAT)
                self.assertEqual(state.tiles[Position(4, 2)].owner_id, 'B')
                self.assertTrue(state.players['A'].has_ever_owned_city)
                self.assertTrue(state.players['B'].has_ever_owned_city)
                self.assertTrue(state.players['B'].eliminated)
                self.assertFalse(any(u.owner_id == 'B' for u in state.units.values()))
                self.assertTrue(old_knowledge.explored_positions <= state.players['B'].knowledge.explored_positions)
                self.assertEqual(state.result, GameResult('A', VictoryType.CONQUEST))
                self.assertIsNone(state.active_player_id)
                self.assertEqual(from_snapshot(to_snapshot(state)), state)

    def test_ineligible_and_defended_moves_are_atomic(self):
        for kind, defenders in ((UnitType.ARCHER, 0), (UnitType.SETTLER, 0),
                                (UnitType.WARRIOR, 1), (UnitType.SCOUT, 2)):
            with self.subTest(kind=kind, defenders=defenders):
                state = capture_state(kind)
                for _ in range(defenders):
                    state.add_unit('B', UnitType.WARRIOR, Position(3, 2))
                before = deepcopy(state)
                with self.assertRaises(ValueError):
                    self.capture(state)
                self.assertEqual(state, before)

    def test_insufficient_budget_invalid_state_and_path_are_atomic(self):
        for change in (lambda s: setattr(s.units['unit-1'], 'moves_remaining', 0),
                       lambda s: setattr(s.players['B'], 'has_ever_owned_city', False),
                       lambda s: setattr(s.units['unit-1'], 'position', Position(0, 6))):
            state = capture_state()
            change(state)
            before = deepcopy(state)
            with self.assertRaises(ValueError): self.capture(state)
            self.assertEqual(state, before)

    def test_minimum_population_and_no_pregame_victory(self):
        state = capture_state()
        state.cities['town'].population = 1
        self.assertIsNone(state.result)
        self.assertFalse(state.players['A'].has_ever_owned_city)
        self.capture(state)
        self.assertEqual(state.cities['town'].population, 1)

    def test_inactive_elimination_preserves_activation_and_captured_economy(self):
        state = capture_state(third=True)
        self.capture(state)
        self.assertEqual(state.active_player_id, 'A')
        self.assertEqual(state.turn_order, ['A', 'C'])
        self.assertIsNone(state.result)
        apply_command(state, SetCityProduction('A', 'town', UnitType.WARRIOR))
        apply_command(state, EndActivation('A'))
        self.assertGreater(state.cities['town'].production_stored, 0)
        self.assertEqual(state.players['B'].gold, 0)
        self.assertEqual(state.active_player_id, 'C')

    def test_last_defender_death_does_not_capture(self):
        for kind in (UnitType.ARCHER, UnitType.WARRIOR):
            state = capture_state(kind)
            defender = state.add_unit('B', UnitType.WARRIOR, Position(3, 2))
            defender.hp = 1
            attack_unit(state, 'unit-1', defender.id)
            self.assertEqual(state.cities['town'].owner_id, 'B')
            self.assertEqual(state.units['unit-1'].position, Position(2, 2))
            self.assertIsNone(state.result)

    def test_recapture_preserves_id_and_resets_again(self):
        state = capture_state(third=True)
        state.add_city(CityState('reserve', 'B', Position(8, 5), name='Reserve'))
        self.capture(state)
        state.units['unit-1'].position = Position(1, 2)
        state.active_player_id = 'B'
        scout = state.add_unit('B', UnitType.SCOUT, Position(4, 2))
        state.cities['town'].food_stored = 8
        apply_command(state, MoveUnit('B', scout.id, Position(3, 2)))
        self.assertEqual(state.cities['town'].owner_id, 'B')
        self.assertEqual(state.cities['town'].population, 1)
        self.assertEqual(state.cities['town'].food_stored, 0)
        self.assertTrue(state.players['A'].eliminated)
        self.assertEqual(state.active_player_id, 'B')

    def test_hidden_capture_preserves_third_party_memory(self):
        state = capture_state(third=True)
        p = state.players['C']
        p.knowledge.explored_positions.add(Position(3, 2))
        p.knowledge.discovered_cities['town'] = KnownCity('town', 'B', Position(3, 2))
        before = deepcopy(planning_view(state, 'C'))
        self.capture(state)
        self.assertEqual(known_enemy_cities(state, 'C')[0]['owner_id'], 'B')
        self.assertEqual(planning_view(state, 'C').cities, before.cities)
        self.assertEqual(StrategicStateBuilder().build(state, 'C')['enemy_cities'][0]['owner_id'], 'B')
        self.assertEqual(observer_state(state)['cities'][0]['ownerId'], 'A')
        state.add_unit('C', UnitType.SCOUT, Position(5, 2))
        self.assertEqual(known_enemy_cities(state, 'C')[0]['owner_id'], 'A')

    def test_terminal_commands_executor_and_public_status(self):
        state = capture_state()
        state.players['A'].controller = ControllerType.HUMAN
        self.capture(state)
        before = deepcopy(state)
        for command in (EndActivation('A'), MoveUnit('A', 'unit-1', Position(4, 2)),
                        SetCityProduction('A', 'town', UnitType.WARRIOR)):
            with self.assertRaises(ValueError): apply_command(state, command)
            self.assertEqual(state, before)
        from aig.ai.controller import AiOrchestrator
        self.assertIsNone(AiOrchestrator().run_active_ai_activation(state))
        self.assertEqual(public_state(state)['game']['winnerPlayerId'], 'A')
        self.assertEqual(public_state(state)['game']['victoryType'], 'conquest')
        self.assertEqual(public_state(state)['game']['status'], 'terminal')

    def test_executor_captures_and_issues_no_end_activation_after_win(self):
        state = capture_state(UnitType.SCOUT)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK, 'B', 'town'))
        self.assertIsInstance(result.commands_executed[-1], MoveUnit)
        self.assertEqual(state.result, GameResult('A'))
        self.assertEqual(state.turn, 0)

    def test_planning_uses_only_known_city_and_capture_eligibility(self):
        for kind in UnitType:
            state = capture_state(kind)
            path = find_path(planning_view(state, 'A'), state.units['unit-1'], Position(3, 2))
            self.assertEqual(path is not None, kind.can_capture)
        state = capture_state()
        state.add_city(CityState('hidden', 'B', Position(12, 2), name='Hidden'))
        self.assertNotIn('hidden', planning_view(state, 'A').cities)
        self.assertNotIn('hidden', {c['id'] for c in StrategicStateBuilder().build(state, 'A')['enemy_cities']})

    def test_barbarians_hostility_and_exclusion(self):
        state = capture_state()
        barbarian = PlayerState('barbarians', ControllerType.AI, kind=FactionKind.BARBARIAN,
                                researched_technologies=frozenset())
        state.players[barbarian.id] = barbarian
        state.turn_order.append(barbarian.id)
        unit = state.add_unit(barbarian.id, UnitType.WARRIOR, Position(4, 2))
        self.assertIsNone(find_path(state, unit, Position(3, 2)))
        self.assertTrue(are_hostile(state.players['A'], state.players['B']))
        self.assertTrue(are_hostile(barbarian, state.players['A']))
        self.assertFalse(are_hostile(barbarian, barbarian))
        self.assertFalse(are_hostile(state.players['A'], state.players['A']))
        self.capture(state)
        self.assertIn(unit.id, state.units)
        self.assertEqual(state.result.winner_player_id, 'A')

    def test_snapshot_rejects_bad_history_and_results_without_effects(self):
        state = capture_state()
        snap = to_snapshot(state)
        bad = deepcopy(snap)
        bad['players'][1]['has_ever_owned_city'] = False
        with self.assertRaises(ValueError): from_snapshot(bad)
        self.capture(state)
        snap = to_snapshot(state)
        for result in ({'winner_player_id': 'B', 'victory_type': 'conquest'},
                       {'winner_player_id': 'A', 'victory_type': 'score'},
                       {'winner_player_id': [], 'victory_type': 'conquest'}):
            bad = deepcopy(snap); bad['result'] = result
            with self.assertRaises(ValueError): from_snapshot(bad)
        bad = deepcopy(snap); bad['schema_version'] = 11
        with self.assertRaisesRegex(ValueError, 'unsupported'): from_snapshot(bad)

    def test_observer_capture_and_elimination_metrics(self):
        state = capture_state(UnitType.SCOUT)
        metrics = ConquestMetrics(state)
        command = MoveUnit('A', 'unit-1', Position(3, 2))
        metrics.observe('before', state, command, 4)
        apply_command(state, command)
        metrics.observe('after', state, command, 4)
        total, players = metrics.finish(state)
        self.assertEqual(total['winnerPlayerId'], 'A')
        self.assertEqual(total['victoryActivation'], 4)
        self.assertEqual(players['A']['capture_unit_types'], {'scout': 1})
        self.assertEqual(players['A']['captured_food_reset'], 7)
        self.assertEqual(players['B']['elimination']['units_removed'], 2)
        self.assertEqual(players['B']['elimination']['settlers_removed'], 1)

    def test_terminal_domain_economy_and_spawn_are_stopped(self):
        state = capture_state()
        self.capture(state)
        from aig.economy import resolve_player_economy
        from aig.barbarians import spawn_replacements
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, 'game has ended'):
            resolve_player_economy(state, 'A')
        with self.assertRaisesRegex(ValueError, 'game has ended'):
            state.remove_city('town')
        with self.assertRaisesRegex(ValueError, 'game has ended'):
            state.add_unit('A', UnitType.SETTLER, Position(3, 2))
        spawn_replacements(state)
        self.assertEqual(state, before)

    def test_one_of_multiple_defenders_is_not_enough(self):
        state = capture_state(UnitType.ARCHER)
        first = state.add_unit('B', UnitType.WARRIOR, Position(3, 2))
        second = state.add_unit('B', UnitType.SCOUT, Position(3, 2))
        first.hp = 1
        attack_unit(state, 'unit-1', first.id)
        state.units['unit-1'].unit_type = UnitType.SCOUT
        state.units['unit-1'].moves_remaining = 1
        before = deepcopy(state)
        with self.assertRaises(ValueError): self.capture(state)
        self.assertEqual(state, before)
        self.assertIn(second.id, state.units)

    def test_history_boolean_and_visible_witnesses(self):
        for value in (0, 1, None, 'true', []):
            with self.assertRaises(ValueError):
                PlayerState('A', ControllerType.AI, has_ever_owned_city=value)
        state = capture_state(third=True)
        state.add_unit('C', UnitType.SCOUT, Position(4, 2))
        self.capture(state)
        self.assertEqual(known_enemy_cities(state, 'C')[0]['owner_id'], 'A')
        self.assertEqual(state.players['B'].knowledge.discovered_cities['town'].owner_id, 'A')

    def test_benchmark_terminal_replay_and_turn_cap(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from aig.ai.benchmark import run_trial
        from aig.settings import Settings

        class Provider:
            name = 'heuristic'

            def create_plan(self, state, previous_plan=None):
                return StrategicPlan(Posture.ATTACK, 'B', 'town')

        with TemporaryDirectory() as folder:
            with patch('aig.ai.benchmark.initial_state', side_effect=lambda _: capture_state()):
                result = run_trial(Provider(), provider_name='heuristic', turns=100,
                                   settings=Settings(), directory=Path(folder)/'terminal')
            self.assertTrue(result['replay']['success'])
            self.assertEqual(result['metrics']['winnerPlayerId'], 'A')
            self.assertEqual(result['metrics']['victoryActivation'], 0)
            self.assertEqual(result['metrics']['activations_completed'], 0)
            self.assertFalse(result['metrics']['turnCapReached'])
            from aig.ai.strategy import HeuristicStrategyProvider
            capped = run_trial(HeuristicStrategyProvider(), provider_name='heuristic', turns=1,
                               settings=Settings(), directory=Path(folder)/'capped')
            self.assertTrue(capped['metrics']['turnCapReached'])
            self.assertIsNone(capped['metrics']['winnerPlayerId'])
