"""HTTP contracts use real commands and the committed scenario, without a network server."""

from concurrent.futures import ThreadPoolExecutor
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from aig.api import create_app
from aig.commands import EndActivation, FoundCity, apply_command
from aig.application import GameSession
from aig.settings import AiSettings, load_settings
from aig.public_state import public_state
from aig.snapshots import to_snapshot
from aig.state import Position, UnitType


class CorsApiTests(unittest.TestCase):
    def test_separate_frontend_origins_allow_reads_errors_and_json_preflight(self):
        for origin in ('http://aig.localhost', 'https://www.agentstrategy.online'):
            settings = load_settings(local_file=None, environ={'AIG_HTTP_CORS_ORIGINS': origin})
            with patch('aig.api.load_settings', return_value=settings), TestClient(create_app()) as client:
                for path, status in (('/api/health', 200), ('/api/game', 404)):
                    response = client.get(path, headers={'Origin': origin})
                    self.assertEqual(response.status_code, status)
                    self.assertEqual(response.headers['access-control-allow-origin'], origin)
                response = client.options('/api/game/commands', headers={
                    'Origin': origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'content-type',
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['access-control-allow-origin'], origin)
                rejected = client.options('/api/game/commands', headers={
                    'Origin': 'https://unrelated.example',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'content-type',
                })
                self.assertEqual(rejected.status_code, 400)
                self.assertNotIn('access-control-allow-origin', rejected.headers)


class GameApiTests(unittest.TestCase):
    def test_normal_api_cannot_select_observer_truth(self):
        self.post('/demo/ai')
        self.post('/start')
        self.command('end_activation')
        result = self.client.get('/api/game?observer=true').json()
        self.assertTrue(all(u['ownerId'] == 'A' for u in result['units']))
        self.assertFalse(result['cities'])
        self.assertTrue(any(t['terrain'] is None for t in result['map']['tiles']))
        for trace in result['aiActivations']:
            self.assertTrue({'plan', 'commands_executed', 'replanReason'}.isdisjoint(trace))

    def setUp(self):
        # API tests must never load developer credentials from the root .env.
        settings_patch = patch('aig.api.load_settings', return_value=load_settings(local_file=None, environ={}))
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        self.app = create_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.addCleanup(self.client.close)
        self.session = self.app.state.session

    def post(self, path, body=None):
        response = self.client.post('/api/game' + path, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def command(self, kind, **fields):
        return self.post('/commands', {'type': kind, **fields})

    def start(self):
        self.post('/demo')
        return self.post('/start')

    def found(self, unit_id='unit-1', name='New Hope'):
        return self.command('found_city', settlerUnitId=unit_id, name=name)

    def test_health_does_not_require_or_mutate_a_game(self):
        self.assertEqual(self.client.get('/api/health').json(), {'status': 'ok'})
        self.assertEqual(self.client.get('/api/game').status_code, 404)
        self.start()
        before = self.client.get('/api/game').json()
        self.assertEqual(self.client.get('/api/health').status_code, 200)
        self.assertEqual(self.client.get('/api/game').json(), before)

    def test_no_game_get_start_and_commands(self):
        responses = [self.client.get('/api/game'),
                     self.client.post('/api/game/start'),
                     self.client.post('/api/game/commands', json={'type': 'end_activation'})]
        for response in responses:
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()['error'], 'no_game')

    def test_create_demo_is_pregame_and_detached(self):
        result = self.post('/demo')
        self.assertEqual(result['game'], {'turn': 0, 'activePlayerId': None, 'status': 'pre_game', 'terminal': False, 'winnerPlayerId': None, 'victoryType': None})
        self.assertEqual((result['map']['width'], result['map']['height']), (12, 10))
        self.assertEqual(len(result['map']['tiles']), 120)
        self.assertEqual([u['id'] for u in result['units']], ['unit-1', 'unit-2'])
        self.assertEqual(result['cities'], [])
        result['units'][0]['hp'] = 1
        self.assertEqual(self.client.get('/api/game').json()['units'][0]['hp'], 100)

    def test_reset_matches_original_demo_and_resets_city_ids(self):
        original = self.post('/demo')
        self.post('/start')
        self.found()
        self.command('end_activation')
        self.assertEqual(self.post('/demo'), original)
        self.post('/start')
        self.assertEqual(self.found()['cities'][0]['id'], 'city-1')

    def test_start_uses_engine_without_advancing_or_economy(self):
        result = self.start()
        self.assertEqual(result['game'], {'turn': 0, 'activePlayerId': 'A', 'status': 'started', 'terminal': False, 'winnerPlayerId': None, 'victoryType': None})
        self.assertTrue(all(p['scienceStored'] == p['gold'] == 0 for p in result['players']))
        before = to_snapshot(self.session._state)
        response = self.client.post('/api/game/start')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(before, to_snapshot(self.session._state))

    def test_pregame_commands_rejected_without_mutation(self):
        self.post('/demo')
        self.assert_invalid_unchanged({'type': 'end_activation'})

    def test_public_dto_serializes_without_snapshot_internals(self):
        self.start()
        self.found()
        self.command('set_city_production', cityId='city-1', unitType='warrior')
        self.command('set_research', technology='archery')
        before = to_snapshot(self.session._state)
        dto = public_state(self.session._state)
        self.assertEqual(json.loads(json.dumps(dto)), self.client.get('/api/game').json())
        self.assertEqual(set(dto), {'game', 'players', 'map', 'units', 'cities', 'viewerPlayerId', 'barbarianCamps'})
        self.assertNotIn('schema_version', dto)
        self.assertNotIn('next_unit_id', dto)
        self.assertNotIn('config', dto)
        self.assertEqual(dto['cities'][0]['productionRemaining'], 20)
        self.assertEqual(dto['players'][0]['researchRemaining'], 15)
        self.assertEqual(dto['units'][0]['maxMovement'], UnitType.WARRIOR.movement_allowance)
        self.assertEqual(before, to_snapshot(self.session._state))
        dto['cities'][0]['name'] = 'Detached'
        self.assertEqual(self.session.current()['cities'][0]['name'], 'New Hope')

    def test_move_through_http_uses_engine_path_and_movement(self):
        self.start()
        result = self.command('move_unit', unitId='unit-1', x=3, y=2)
        settler = next(u for u in result['units'] if u['id'] == 'unit-1')
        self.assertEqual((settler['x'], settler['y'], settler['movesRemaining']), (3, 2, 1))

    def test_attack_through_http_resolves_damage_and_movement(self):
        self.start()
        # Fixture placement only: all gameplay under test still goes through HTTP.
        target = self.session._state.add_unit('B', UnitType.WARRIOR, Position(3, 2))
        result = self.command('attack_unit', attackerUnitId='unit-2', targetUnitId=target.id)
        units = {u['id']: u for u in result['units']}
        self.assertEqual((units['unit-2']['hp'], units[target.id]['hp']), (70, 70))
        self.assertEqual(units['unit-2']['movesRemaining'], 0)

    def test_attack_targets_only_chosen_stack_member(self):
        self.start()
        first = self.session._state.add_unit('B', UnitType.WARRIOR, Position(3, 2))
        second = self.session._state.add_unit('B', UnitType.SCOUT, Position(3, 2))
        self.command('attack_unit', attackerUnitId='unit-2', targetUnitId=second.id)
        self.assertEqual(first.hp, 100)
        self.assertLess(second.hp, 100)

    def test_found_city_consumes_settler_and_claims_center(self):
        self.start()
        result = self.found(name='A & B <Town>')
        town = result['cities'][0]
        self.assertEqual((town['id'], town['name'], town['ownerId']), ('city-1', 'A & B <Town>', 'A'))
        self.assertNotIn('unit-1', [u['id'] for u in result['units']])
        center = next(t for t in result['map']['tiles'] if (t['x'], t['y']) == (2, 2))
        self.assertEqual(center['ownerId'], 'A')

    def test_city_ids_are_deterministic_and_failed_found_does_not_consume(self):
        self.start()
        self.assert_invalid_unchanged({'type': 'found_city', 'settlerUnitId': 'unit-2', 'name': 'Invalid'})
        self.assertEqual(self.found()['cities'][0]['id'], 'city-1')
        self.command('end_activation')
        result = self.found('unit-3', 'Azure Home')
        self.assertEqual([c['id'] for c in result['cities']], ['city-2'])

    def test_city_allocator_skips_existing_ids(self):
        self.start()
        apply_command(self.session._state, FoundCity('A', 'unit-1', 'city-1', 'Existing'))
        self.command('end_activation')
        result = self.found('unit-3')
        self.assertEqual([c['id'] for c in result['cities']], ['city-2'])

    def test_production_set_switch_clear_and_unlock_choices(self):
        self.start()
        self.found()
        for choice in ('warrior', 'scout', None):
            town = self.command('set_city_production', cityId='city-1', unitType=choice)['cities'][0]
            self.assertEqual(town['productionTarget'], choice)
            self.assertEqual(town['productionStored'], 0)
        self.assertEqual({p['unitType'] for p in town['availableProduction']}, {'warrior', 'scout', 'settler'})
        self.assert_invalid_unchanged({'type': 'set_city_production', 'cityId': 'city-1', 'unitType': 'archer'})

    def test_research_set_switch_clear_and_cost_queries(self):
        self.start()
        for choice, cost in [('archery', 15), ('bronze_working', 20), (None, None)]:
            player = self.command('set_research', technology=choice)['players'][0]
            self.assertEqual(player['researchTarget'], choice)
            self.assertEqual(player['researchCost'], cost)
            self.assertEqual(player['researchRemaining'], cost)
        self.assert_invalid_unchanged({'type': 'set_research', 'technology': 'agriculture'})

    def test_hotseat_end_activation_and_economy(self):
        self.start()
        self.found()
        result = self.command('end_activation')
        self.assertEqual(result['game']['activePlayerId'], 'B')
        self.assertEqual(result['players'][0]['scienceStored'], 1)
        self.found('unit-3', 'Blue City')
        result = self.command('end_activation')
        self.assertEqual(result['game'], {'turn': 1, 'activePlayerId': 'A', 'status': 'started', 'terminal': False, 'winnerPlayerId': None, 'victoryType': None})
        self.assertTrue(all(c['productionStored'] > 0 for c in result['cities']))

    def test_commands_always_use_active_faction(self):
        self.start()
        self.assert_invalid_unchanged({'type': 'move_unit', 'unitId': 'unit-3', 'x': 8, 'y': 7})
        self.command('end_activation')
        result = self.command('set_research', technology='archery')
        self.assertIsNone(result['players'][0]['researchTarget'])
        self.assertEqual(result['players'][1]['researchTarget'], 'archery')
        self.command('move_unit', unitId='unit-3', x=8, y=7)

    def test_malformed_or_extra_command_fields_rejected(self):
        self.start()
        payloads = [
            {}, {'type': 'eliminate_player', 'targetPlayerId': 'B'},
            {'type': 'end_activation', 'actorId': 'B'},
            {'type': 'end_activation', 'actor_id': 'A'},
            {'type': 'move_unit', 'unitId': 'unit-1', 'x': True, 'y': 2},
            {'type': 'move_unit', 'unitId': 'unit-1', 'x': '3', 'y': 2},
            {'type': 'move_unit', 'unitId': 'unit-1', 'x': 3.5, 'y': 2},
            {'type': 'set_research', 'technology': 'magic'},
            {'type': 'set_city_production', 'cityId': 'city-1'},
            {'type': 'found_city', 'settlerUnitId': 'unit-1', 'name': 123},
            {'type': 'found_city', 'settlerUnitId': 'unit-1', 'name': 'City', 'cityId': 'client-id'},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assert_invalid_unchanged(payload)

    def test_malformed_json_is_structured_4xx(self):
        self.start()
        response = self.client.post('/api/game/commands', content='{', headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error'], 'invalid_request')

    def test_invalid_command_error_is_structured_and_atomic(self):
        self.start()
        for payload in [
            {'type': 'move_unit', 'unitId': 'unit-1', 'x': 99, 'y': 99},
            {'type': 'attack_unit', 'attackerUnitId': 'unit-2', 'targetUnitId': 'unit-4'},
            {'type': 'found_city', 'settlerUnitId': 'unit-1', 'name': '  '},
            {'type': 'set_city_production', 'cityId': 'missing', 'unitType': 'warrior'},
        ]:
            self.assert_invalid_unchanged(payload)

    def test_engine_value_error_never_becomes_success(self):
        self.start()
        with patch('aig.application.apply_command', side_effect=ValueError('Engine rejected action')):
            response = self.client.post('/api/game/commands', json={'type': 'end_activation'})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {'error': 'invalid_command', 'message': 'Engine rejected action'})

    def test_unexpected_engine_error_is_logged_500_without_traceback(self):
        self.start()
        with patch('aig.application.apply_command', side_effect=RuntimeError('private failure detail')):
            with self.assertLogs('aig.api', level='ERROR'):
                response = self.client.post('/api/game/commands', json={'type': 'end_activation'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error'], 'server_error')
        self.assertNotIn('private failure detail', response.text)
        self.assertNotIn('Traceback', response.text)

    def test_http_opening_produces_units_completes_research_and_unlocks(self):
        self.start()
        for settler in ('unit-1', 'unit-3'):
            result = self.found(settler)
            town = next(c for c in result['cities'] if c['ownerId'] == result['game']['activePlayerId'])
            self.command('set_city_production', cityId=town['id'], unitType='warrior')
            self.command('set_research', technology='archery')
            self.command('end_activation')
        for _ in range(40):
            result = self.command('end_activation')
        self.assertTrue(all('archery' in p['researchedTechnologies'] for p in result['players']))
        self.assertGreaterEqual(len(result['units']), 2)
        self.assertTrue(all('archer' in {c['unitType'] for c in town['availableProduction']} for town in result['cities']))

    def test_no_endpoint_accesses_external_services(self):
        forbidden = AssertionError('External services must never be contacted')
        with patch('socket.create_connection', side_effect=forbidden), \
             patch('httpx2.HTTPTransport.handle_request', side_effect=forbidden), \
             patch('urllib.request.urlopen', side_effect=forbidden):
            self.start()
            self.client.get('/api/game').raise_for_status()
            self.command('move_unit', unitId='unit-2', x=3, y=2)
            target = self.session._state.add_unit('B', UnitType.WARRIOR, Position(4, 2))
            self.command('end_activation')
            self.command('end_activation')
            self.command('attack_unit', attackerUnitId='unit-2', targetUnitId=target.id)
            self.found()
            self.command('set_city_production', cityId='city-1', unitType='warrior')
            self.command('set_research', technology='archery')
            self.command('end_activation')
            self.post('/demo')

    def test_separate_application_instances_have_isolated_sessions(self):
        self.start()
        with TestClient(create_app()) as other:
            self.assertEqual(other.get('/api/game').status_code, 404)

    def test_concurrent_commands_return_coherent_detached_states(self):
        self.start()
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(self.session.execute, EndActivation)
                       for _ in range(12)]
            results = [future.result() for future in futures]
        activations = sorted(r['game']['turn'] * 2 + (r['game']['activePlayerId'] == 'B') for r in results)
        self.assertEqual(activations, list(range(1, 13)))
        self.assertEqual(self.session.current()['game']['turn'], 6)

    def assert_invalid_unchanged(self, payload):
        before = to_snapshot(self.session._state)
        counter = self.session._next_city_id
        response = self.client.post('/api/game/commands', json=payload)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn('error', response.json())
        self.assertTrue(response.json()['message'])
        self.assertEqual(before, to_snapshot(self.session._state))
        self.assertEqual(counter, self.session._next_city_id)

    def test_human_vs_ai_demo_and_start(self):
        pregame = self.post('/demo/ai')
        self.assertEqual([p['controller'] for p in pregame['players']], ['human', 'ai'])
        self.assertIsNone(pregame['game']['activePlayerId'])
        started = self.post('/start')
        self.assertEqual(started['game']['activePlayerId'], 'A')
        self.assertEqual(started['cities'], [])

    def test_human_end_runs_ai_returns_final_state_and_trace(self):
        self.post('/demo/ai')
        self.post('/start')
        self.found()
        result = self.command('end_activation')
        self.assertEqual(result['game'], {'turn': 1, 'activePlayerId': 'A', 'status': 'started', 'terminal': False, 'winnerPlayerId': None, 'victoryType': None})
        self.assertEqual({c['ownerId'] for c in result['cities']}, {'A'})
        trace = result['aiActivations'][0]
        self.assertEqual(trace['player_id'], 'B')
        self.assertNotIn('plan', trace)
        self.assertNotIn('commands_executed', trace)
        self.assertTrue(self.session.ai.latest_results[0].commands_executed)
        self.assertEqual(self.client.get('/api/game').json(), result)

    def test_human_commands_before_end_do_not_auto_play_human_or_ai(self):
        self.post('/demo/ai')
        self.post('/start')
        result = self.command('set_research', technology='archery')
        self.assertEqual(result['game']['activePlayerId'], 'A')
        self.assertEqual(result['cities'], [])
        self.assertNotIn('aiActivations', result)

    def test_ai_demo_reset_clears_plans_traces_and_replays_deterministically(self):
        traces = []
        for _ in range(2):
            result = self.post('/demo/ai')
            self.assertNotIn('aiActivations', result)
            self.assertEqual(self.session.ai.controllers, {})
            self.post('/start')
            traces.append(self.command('end_activation'))
        self.assertEqual(traces[0], traces[1])
        result = self.post('/demo')
        self.assertTrue(all(p['controller'] == 'human' for p in result['players']))
        self.assertNotIn('aiActivations', result)

    def test_ai_summary_is_detached_from_application_memory(self):
        self.session.demo(versus_ai=True)
        self.session.start()
        response = self.session.execute(EndActivation)
        response['aiActivations'][0]['actualProvider'] = 'changed'
        self.assertEqual(self.session.current()['aiActivations'][0]['actualProvider'], 'heuristic')

    def test_browser_cannot_issue_commands_for_ai_actor(self):
        self.post('/demo/ai')
        self.post('/start')
        apply_command(self.session._state, EndActivation('A'))
        self.assert_invalid_unchanged({'type': 'end_activation'})
        self.session.advance_until_human()
        self.assertEqual(self.session.current()['game']['activePlayerId'], 'A')

    def test_start_processes_ai_first_if_scenario_says_so(self):
        self.session.demo(versus_ai=True)
        self.session._state.turn_order = ["B", "A", "barbarians"]
        result = self.session.start()
        self.assertEqual(result['game']['activePlayerId'], 'A')
        self.assertEqual(result['aiActivations'][0]['player_id'], 'B')

    def test_terminal_public_state_and_orchestration(self):
        self.session.demo(versus_ai=True)
        self.session.start()
        self.session._state.eliminate_player('B')
        result = self.session.advance_until_human()
        self.assertEqual(result['game']['status'], 'terminal')
        self.assertIsNone(self.session.run_active_ai_activation())

    def test_ai_bound_error_is_server_failure_not_invalid_human_command(self):
        self.post('/demo/ai')
        self.post('/start')
        self.session.ai.executor.max_actions = 1
        with self.assertLogs('aig.api', level='ERROR'):
            response = self.client.post('/api/game/commands', json={'type': 'end_activation'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error'], 'server_error')

    def test_session_uses_ai_configuration(self):
        session = GameSession(AiSettings(replan_interval=3, max_actions=50))
        session.demo(versus_ai=True)
        session.start()
        session.execute(EndActivation)
        self.assertEqual(session.ai.controllers['B'].replan_interval, 3)
        self.assertEqual(session.ai.executor.max_actions, 50)

    def test_ai_endpoints_never_contact_external_services(self):
        forbidden = AssertionError('No Ollama or external service calls')
        with patch('socket.create_connection', side_effect=forbidden), \
             patch('httpx2.HTTPTransport.handle_request', side_effect=forbidden), \
             patch('urllib.request.urlopen', side_effect=forbidden):
            self.post('/demo/ai')
            self.post('/start')
            for _ in range(12):
                self.command('end_activation')


if __name__ == '__main__':
    unittest.main()
