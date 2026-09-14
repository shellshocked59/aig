"""Web-only observer orchestration; fake provider, no network inference."""
import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from aig.web import create_app
from aig.settings import load_settings
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.replay import replay
from aig.arena.snapshots import state_hash

class ArenaObserverTests(unittest.TestCase):
    def setUp(self):
        with patch('aig.api.load_settings', return_value=load_settings(local_file=None,environ={})):
            self.app=create_app()
        self.client=TestClient(self.app)
        self.addCleanup(self.client.close)
        self.provider=HeuristicArenaTurnProvider()
        self.provider.create_turn_plan=Mock(wraps=self.provider.create_turn_plan)
        self.factory=patch('aig.arena.application.create_arena_turn_provider',return_value=self.provider)
        self.factory.start();self.addCleanup(self.factory.stop)

    def test_creation_is_idle_and_each_request_runs_one_turn_with_replayable_events(self):
        response=self.client.post('/api/arena/observer/demo')
        self.assertEqual(response.status_code,200)
        before=response.json()
        self.assertEqual(before['controllers'],{'blue':'openai_ai','red':'openai_ai'})
        self.provider.create_turn_plan.assert_not_called()
        for turn,expected in [(1,'red'),(2,'blue')]:
            response=self.client.post('/api/arena/observer/turn')
            self.assertEqual(response.status_code,200,response.text)
            after=response.json()
            self.assertEqual(self.provider.create_turn_plan.call_count,turn)
            self.assertEqual(after['active_player_id'],expected)
            self.assertEqual(len(after['ai_turns']),1)
            self.assertEqual(after['presentation']['start_state_hash'],before['state_hash'])
            self.assertEqual(after['presentation']['final_state_hash'],after['state_hash'])
            self.assertTrue(after['presentation']['events'])
            self.assertEqual(state_hash(replay(self.app.state.arena_session.trace()).state),after['state_hash'])
            before=after

    def test_only_observer_can_step_and_human_commands_are_rejected(self):
        self.client.post('/api/arena/demo')
        self.assertEqual(self.client.post('/api/arena/observer/turn').status_code,422)
        self.client.post('/api/arena/observer/demo')
        self.assertEqual(self.client.post('/api/arena/commands',json={'schema_version':'arena-command-v2','type':'arena_end_turn','actor_id':'blue'}).status_code,422)
        self.provider.create_turn_plan.assert_not_called()
        self.client.post('/api/arena/demo-ai/heuristic-v2')
        self.assertEqual(self.client.post('/api/arena/observer/turn').status_code,422)
