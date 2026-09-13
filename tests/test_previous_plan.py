"""Controller/provider continuity contract, with offline model transports only."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from aig.ai.benchmark import initial_state, run_trial
from aig.ai.controller import AiController, AiOrchestrator
from aig.ai.multifront_metrics import MultiFrontMetrics
from aig.ai.ollama import OllamaStrategyProvider
from aig.ai.openai import OpenAIStrategyProvider
from aig.ai.plan_schema import canonical_json, parse_plan
from aig.ai.strategy import HeuristicStrategyProvider, Posture, StrategicPlan, StrategyProviderError
from aig.commands import MoveUnit, apply_command
from aig.knowledge import update_knowledge
from aig.settings import OllamaSettings, OpenAISettings, Settings
from aig.state import CityState, Position, UnitType
from test_openai import response


def four_player_world():
    state = initial_state('v4')
    state.units.clear()
    state.camps.clear()
    for player in state.players.values():
        player.knowledge.discovered_camps.clear()
    for actor, x, y in [('A', 2, 2), ('B', 6, 2), ('C', 10, 2), ('D', 13, 9)]:
        state.add_city(CityState('city-'+actor, actor, Position(x, y), name=actor))
    state.add_unit('C', UnitType.SCOUT, Position(3, 3))
    update_knowledge(state)
    state.active_player_id = 'C'
    return state


def capture_a(state, *, reserve=False):
    if reserve:
        state.add_city(CityState('reserve-A', 'A', Position(2, 8), name='Reserve'))
    state.active_player_id = 'B'
    attacker = state.add_unit('B', UnitType.WARRIOR, Position(1, 2))
    apply_command(state, MoveUnit('B', attacker.id, Position(2, 2)))
    state.active_player_id = 'C'


class PreviousPlanTests(unittest.TestCase):
    def setUp(self):
        # Fail closed if any test accidentally uses a real model transport.
        for target in ('socket.socket.connect', 'httpx.Client.send'):
            guard = patch(target, side_effect=AssertionError('live network forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def controller(self, state, previous=None, provider=None):
        provider = provider or Mock(wraps=HeuristicStrategyProvider())
        previous = previous or StrategicPlan(Posture.ATTACK, 'A', 'city-A')
        controller = AiController(provider, previous_plan=previous, plan_creation_turn=0)
        controller._seen_city = True
        return controller, provider, previous

    def test_valid_expired_plan_keeps_enemy_city_and_identity(self):
        state = four_player_world()
        controller, provider, previous = self.controller(state)
        state.turn = 5
        controller.plan_for(state, 'C')
        self.assertIs(provider.create_plan.call_args.args[1], previous)
        self.assertEqual(controller.last_trace['previous_plan'], previous.to_dict())
        self.assertEqual(controller.last_trace['replan_reason'], 'expired')
        self.assertNotIn('invalidated_previous_plan', controller.last_trace)

    def test_young_valid_plan_reused_without_provider_call(self):
        state = four_player_world()
        controller, provider, previous = self.controller(state)
        self.assertIs(controller.plan_for(state, 'C'), previous)
        provider.create_plan.assert_not_called()

    def test_reference_invariants_clear_context_for_heuristic(self):
        for case in ('eliminated', 'unknown_enemy', 'self_enemy', 'removed_city',
                     'unknown_city', 'unknown_to_actor', 'captured', 'city_only_dead_owner'):
            with self.subTest(case=case):
                state = four_player_world()
                previous = StrategicPlan(Posture.ATTACK, 'A', 'city-A')
                if case == 'eliminated':
                    capture_a(state)
                elif case == 'unknown_enemy':
                    previous = StrategicPlan(Posture.ATTACK, 'unknown')
                elif case == 'self_enemy':
                    previous = StrategicPlan(Posture.ATTACK, 'C')
                elif case == 'removed_city':
                    state.add_city(CityState('reserve-A', 'A', Position(2, 8), name='Reserve'))
                    state.remove_city('city-A')
                elif case == 'unknown_city':
                    previous = StrategicPlan(Posture.ATTACK, 'A', 'missing-city')
                elif case == 'unknown_to_actor':
                    previous = StrategicPlan(Posture.ATTACK, 'D', 'city-D')
                elif case == 'captured':
                    capture_a(state, reserve=True)
                else:
                    previous = StrategicPlan(Posture.ATTACK, None, 'city-A')
                    state.eliminate_player('A')
                controller, provider, _ = self.controller(state, previous)
                controller.plan_for(state, 'C')
                self.assertIsNone(provider.create_plan.call_args.args[1])
                trace = controller.last_trace
                self.assertEqual(trace['replan_reason'], 'invalid_target')
                self.assertIsNone(trace['previous_plan'])
                self.assertEqual(trace['invalidated_previous_plan'], previous.to_dict())
                parse_plan(canonical_json(controller.previous_plan.to_dict()), trace['strategic_state'])

    def test_third_party_elimination_allows_fresh_b_or_d_target(self):
        for target in 'BD':
            with self.subTest(target=target):
                state = four_player_world()
                self.assertEqual(state.civilization_ids, list('ABCD'))
                fresh = StrategicPlan(Posture.ATTACK, target)
                provider = Mock(create_plan=Mock(return_value=fresh), last_trace=None)
                controller, _, previous = self.controller(state, provider=provider)
                capture_a(state)
                self.assertTrue(state.players['A'].eliminated)
                self.assertIsNone(state.result)
                metrics = MultiFrontMetrics(state)
                self.assertIs(controller.plan_for(state, 'C'), fresh)
                view, prior = provider.create_plan.call_args.args
                self.assertIsNone(prior)
                self.assertEqual({c['id'] for c in view['civilizations']
                                  if c['hostile'] and not c['eliminated']}, set('BD'))
                self.assertEqual(controller.previous_plan, fresh)
                metrics.record('C', controller)
                self.assertEqual(metrics.finish()['C']['eliminated_target_transitions'], 1)
                self.assertEqual(controller.last_trace['invalidated_previous_plan'], previous.to_dict())

    def test_ownership_change_does_not_reinterpret_previous_plan(self):
        state = four_player_world()
        fresh = StrategicPlan(Posture.ATTACK, 'B', 'city-A')
        provider = Mock(create_plan=Mock(return_value=fresh), last_trace=None)
        controller, _, previous = self.controller(state, provider=provider)
        capture_a(state, reserve=True)
        self.assertFalse(state.players['A'].eliminated)
        self.assertIs(controller.plan_for(state, 'C'), fresh)
        self.assertIsNone(provider.create_plan.call_args.args[1])
        self.assertEqual(previous.primary_enemy_id, 'A')
        self.assertEqual(controller.last_trace['invalidated_previous_plan']['primary_enemy_id'], 'A')

    def test_hidden_removal_or_capture_preserves_knowledge_valid_context(self):
        for captured in (False, True):
            with self.subTest(captured=captured):
                state = four_player_world()
                controller, provider, previous = self.controller(state)
                next(u for u in state.units.values() if u.owner_id == 'C').position = Position(10, 3)
                update_knowledge(state)
                if captured:
                    capture_a(state, reserve=True)
                else:
                    state.add_city(CityState('reserve-A', 'A', Position(2, 8), name='Reserve'))
                    state.remove_city('city-A')
                state.turn = 5
                controller.plan_for(state, 'C')
                self.assertIs(provider.create_plan.call_args.args[1], previous)
                known = next(c for c in controller.last_trace['strategic_state']['enemy_cities'] if c['id'] == 'city-A')
                self.assertEqual(known['owner_id'], 'A')
                self.assertIsNone(known['live_exists'])
                self.assertEqual(controller.last_trace['replan_reason'], 'expired')

    def test_first_city_and_military_contact_keep_valid_plan(self):
        for event in ('first_enemy_city_discovered', 'first_enemy_military_contact'):
            with self.subTest(event=event):
                state = four_player_world()
                controller, provider, previous = self.controller(state)
                if event == 'first_enemy_city_discovered':
                    controller._seen_city = False
                else:
                    state.add_unit('A', UnitType.WARRIOR, Position(2, 3))
                controller.plan_for(state, 'C')
                self.assertEqual(controller.last_trace['replan_reason'], event)
                self.assertIs(provider.create_plan.call_args.args[1], previous)

    def test_barbarian_and_camp_discovery_keep_valid_plan(self):
        from test_barbarians import world, place, warrior
        for empty in (False, True):
            with self.subTest(empty=empty):
                state = world()
                if empty:
                    del state.units[warrior(state).id]
                provider = Mock(wraps=HeuristicStrategyProvider())
                controller = AiController(provider)
                previous = controller.plan_for(state, 'A')
                place(state, 'A', UnitType.SCOUT, Position(3, 5))
                controller.plan_for(state, 'A')
                self.assertIs(provider.create_plan.call_args.args[1], previous)
                self.assertEqual(controller.last_trace['replan_reason'],
                                 'first_camp_discovered' if empty else 'first_barbarian_contact')

    def test_fallback_receives_same_validated_context(self):
        for invalid in (False, True):
            with self.subTest(invalid=invalid):
                state = four_player_world()
                provider = Mock(create_plan=Mock(side_effect=StrategyProviderError('offline failure')), last_trace=None)
                controller, _, previous = self.controller(state, provider=provider)
                if invalid:
                    capture_a(state)
                state.turn = 5
                with patch('aig.ai.controller.HeuristicStrategyProvider') as fallback:
                    fallback.return_value.create_plan.return_value = StrategicPlan(Posture.EXPAND)
                    controller.plan_for(state, 'C')
                self.assertIs(provider.create_plan.call_args.args[1], None if invalid else previous)
                self.assertEqual(fallback.return_value.create_plan.call_args, provider.create_plan.call_args)
                self.assertTrue(controller.last_trace['fallback_used'])

    def test_fake_model_requests_use_null_or_unchanged_valid_previous_plan(self):
        for kind in ('openai', 'ollama'):
            for version in ('v1', 'v2'):
                for case in ('eliminated', 'removed', 'captured', 'expired'):
                    with self.subTest(kind=kind, version=version, case=case):
                        state = four_player_world()
                        raw = canonical_json(StrategicPlan(Posture.EXPAND).to_dict())
                        if kind == 'openai':
                            client = Mock()
                            client.responses.create.return_value = response(raw)
                            provider = OpenAIStrategyProvider(OpenAISettings(api_key='offline-test'),
                                                             client=client, prompt_version=version)
                        else:
                            requester = Mock(return_value=json.dumps({'done': True, 'message': {'content': raw}}))
                            provider = OllamaStrategyProvider(OllamaSettings(), requester=requester, prompt_version=version)
                        controller, _, previous = self.controller(state, provider=provider)
                        if case == 'eliminated':
                            capture_a(state)
                        elif case == 'removed':
                            state.add_city(CityState('reserve-A', 'A', Position(2, 8), name='Reserve'))
                            state.remove_city('city-A')
                        elif case == 'captured':
                            capture_a(state, reserve=True)
                        state.turn = 5
                        controller.plan_for(state, 'C')
                        messages = (client.responses.create.call_args.kwargs['input'] if kind == 'openai'
                                    else json.loads(requester.call_args.args[1])['messages'])
                        content = messages[-1]['content']
                        wire = content.split('PREVIOUS PLAN:\n')[1].split('\n\nPRIORITY OPTIONS:')[0]
                        expected = previous.to_dict() if case == 'expired' else None
                        self.assertEqual(wire, canonical_json(expected))
                        self.assertEqual(controller.last_trace['previous_plan'], expected)
                        self.assertEqual(provider.last_trace['serialized_previous_plan'], wire)
                        self.assertNotIn('invalidated_previous_plan', content)
                        self.assertNotIn('invalidated_previous_plan', provider.last_trace)

    def test_final_conquest_stops_orchestration_before_provider(self):
        state = four_player_world()
        state.eliminate_player('B')
        state.eliminate_player('D')
        state.active_player_id = 'C'
        attacker = state.add_unit('C', UnitType.WARRIOR, Position(1, 2))
        provider = Mock()
        ai = AiOrchestrator(provider)
        ai.controllers['C'] = self.controller(state, provider=provider)[0]
        apply_command(state, MoveUnit('C', attacker.id, Position(2, 2)))
        self.assertIsNotNone(state.result)
        self.assertIsNone(state.active_player_id)
        self.assertIsNone(ai.run_active_ai_activation(state))
        self.assertEqual(ai.advance_until_human(state), ())
        provider.create_plan.assert_not_called()

    def test_benchmark_turn_39_context_and_audit_detects_stale_input(self):
        spec = importlib.util.spec_from_file_location('knowledge_audit',
            Path(__file__).resolve().parents[1] / 'scripts/audit-benchmark-knowledge.py')
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        with TemporaryDirectory() as directory:
            root = Path(directory) / 'run'
            run_trial(HeuristicStrategyProvider(), provider_name='heuristic', turns=40,
                      settings=Settings(), directory=root, scenario_version='v4')
            rows = [json.loads(line) for line in (root/'plans.jsonl').read_text().splitlines()]
            row = next(r for r in rows if r['turn'] == 39 and r['player_id'] == 'C')
            self.assertEqual(row['activation'], 196)
            self.assertEqual(row['replan_reason'], 'invalid_target')
            self.assertIsNone(row['previous_plan'])
            self.assertEqual(row['invalidated_previous_plan']['primary_enemy_id'], 'A')
            self.assertEqual(row['invalidated_previous_plan']['target_city_id'], 'ai-city-unit-1')
            self.assertIsNone(row['new_plan']['primary_enemy_id'])
            self.assertTrue(audit.audit(root)['valid_previous_plan_references'])
            row['previous_plan'] = deepcopy(row['invalidated_previous_plan'])
            (root/'plans.jsonl').write_text('\n'.join(canonical_json(r) for r in rows))
            with self.assertRaises(ValueError):
                audit.audit(root)
