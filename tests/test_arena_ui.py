"""Offline browser presentation additions; engine and provider contracts stay fixed."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from aig.web import create_app
from aig.arena import ArenaAttack, ArenaHeal, ArenaSimulation
from aig.arena.snapshots import command_to_dict
from aig.arena.state import UnitType
from aig.settings import load_settings
from test_arena import core_win_commands, duel


class ArenaUiTests(unittest.TestCase):
    def setUp(self):
        with patch('aig.api.load_settings', return_value=load_settings(local_file=None, environ={})):
            self.app = create_app()
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def send(self, command):
        response = self.client.post('/api/arena/commands', json=command_to_dict(command))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_page_routes_and_actionable_missing_build(self):
        for route in ('/', '/arena', '/arena/', '/empire'):
            response = self.client.get(route)
            self.assertIn(response.status_code, (200, 503))
            if response.status_code == 200:
                self.assertIn('/assets/main.js', response.text)
        with patch('pathlib.Path.is_file', return_value=False):
            response = self.client.get('/arena')
        self.assertEqual(response.status_code, 503)
        self.assertIn('npm run build', response.json()['message'])
        self.assertEqual(self.client.get('/api/health').status_code, 200)

    def test_web_session_preserves_empire_and_frozen_api_factory(self):
        empire = self.client.post('/api/game/demo').json()
        self.client.post('/api/arena/demo')
        self.assertEqual(self.client.get('/api/game').json(), empire)
        self.client.post('/api/game/start')
        self.assertEqual(self.client.get('/api/arena').json()['battle_log'], [])
        from aig.api import create_app as create_frozen_api
        with patch('aig.api.load_settings', return_value=load_settings(local_file=None, environ={})):
            frozen = create_frozen_api()
        with TestClient(frozen) as client:
            self.assertNotIn('battle_log', client.post('/api/arena/demo').json())

    def test_successful_commands_have_semantic_log_and_reset_clears_it(self):
        self.client.post('/api/arena/demo')
        for command in core_win_commands():
            state = self.send(command)
        self.assertEqual(state['terminal_reason'], 'Core destroyed')
        self.assertTrue(any('moved to' in item['text'] for item in state['battle_log']))
        self.assertTrue(any('damage' in item['text'] for item in state['battle_log']))
        self.assertTrue(any('ended turn' in item['text'] for item in state['battle_log']))
        self.assertEqual(state['battle_log'], self.client.get('/api/arena').json()['battle_log'])
        reset = self.client.post('/api/arena/demo').json()
        self.assertEqual(reset['battle_log'], [])
        self.assertIsNone(reset['terminal_reason'])

    def test_actual_healing_and_damage_summaries(self):
        state = duel(UnitType.CLERIC)
        state.units['actor'].hp = 1
        self.app.state.arena_session._simulation = ArenaSimulation(state)
        result = self.send(ArenaHeal('blue', 'actor', 'actor'))
        self.assertIn('5 HP restored', result['battle_log'][-1]['text'])
        result = self.send(ArenaAttack('blue', 'actor', 'target'))
        self.assertIn('3 damage', result['battle_log'][-1]['text'])

    def test_heuristic_actions_are_in_same_log_and_no_provider_details_leak(self):
        self.client.post('/api/arena/demo-ai')
        from aig.arena import ArenaEndTurn
        state = self.send(ArenaEndTurn('blue'))
        self.assertEqual(state['active_player_id'], 'blue')
        self.assertTrue(any('Red Team' in entry['text'] for entry in state['battle_log']))
        self.assertTrue(all(set(entry) == {'id', 'text'} for entry in state['battle_log']))
        self.assertEqual(state['battle_log'][0]['text'], 'Blue Team ended turn')

    def test_log_is_bounded_and_invalid_command_does_not_add_an_entry(self):
        from aig.arena.battle_log import battle_log
        from aig.arena import ArenaEndTurn
        self.client.post('/api/arena/demo')
        self.send(ArenaEndTurn('blue'))
        trace = self.app.state.arena_session.trace()
        trace['entries'] *= 70
        entries = battle_log(trace)
        self.assertEqual(len(entries), 60)
        self.assertEqual(entries[0]['id'], 11)
        before = self.client.get('/api/arena').json()
        self.assertEqual(self.client.post('/api/arena/commands', json=command_to_dict(ArenaEndTurn('blue'))).status_code, 422)
        self.assertEqual(before, self.client.get('/api/arena').json())
