"""Presentation projection and API tests; all providers remain offline."""
from copy import deepcopy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from aig.arena import ArenaSimulation, ArenaEndTurn, ArenaMove, replay, state_hash
from aig.arena.presentation import PresentationSimulation, VERSION
from aig.arena.snapshots import command_from_dict, command_to_dict, canonical_json
from aig.settings import load_settings
from aig.web import create_app
from aig.state import Position

examples = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/arena-presentation-fixtures.py'))['examples']


class PresentationProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = examples()

    def event(self, name):
        return self.fixtures[name]['batch']['events'][0]

    def effects(self, name, kind):
        return [e for e in self.event(name)['effects'] if e['type'] == kind]

    def test_move_actor_path_positions_ap_hashes(self):
        e = self.event('Move')
        self.assertEqual(e['actor_id'], 'blue-knight')
        self.assertEqual(e['origin'], dict(x=3, y=2))
        self.assertEqual(e['destination'], dict(x=2, y=2))
        self.assertEqual(e['path'], [e['origin'], e['destination']])
        self.assertEqual((e['ap_before'], e['ap_after']), (5, 4))
        self.assertEqual(e['sequence'], 1)
        self.assertNotEqual(e['before_hash'], e['after_hash'])

    def test_attack_resolved_damage_and_positions(self):
        e = self.event('Attack')
        self.assertEqual(e['target'], dict(x=4, y=2))
        d = self.effects('Attack', 'damage')[0]
        self.assertEqual((d['entity_id'], d['amount'], d['hp_before'], d['hp_after']), ('red-knight', 6, 18, 12))
        self.assertEqual(e['actor_class'], 'knight')

    def test_downed_is_explicit_and_lethal_damage_is_clamped(self):
        self.assertEqual(self.effects('Down', 'damage')[0]['amount'], 1)
        self.assertEqual(self.effects('Down', 'downed')[0]['status_after'], 'downed')

    def test_heal_exact_hp(self):
        e = self.effects('Heal', 'heal')[0]
        self.assertEqual((e['amount'], e['hp_before'], e['hp_after']), (5, 2, 7))

    def test_revive_position_hp_and_status(self):
        e = self.effects('Revive', 'revived')[0]
        self.assertEqual(e['position'], dict(x=2, y=3))
        self.assertEqual((e['status_before'], e['status_after'], e['hp_after']), ('downed', 'active', 5))

    def test_finish_removes_identified_target(self):
        e = self.effects('Finish', 'removed')[0]
        self.assertEqual(e['entity_id'], 'red-knight')
        self.assertEqual(e['position'], dict(x=4, y=2))

    def test_shield_bash_damage_then_authoritative_push(self):
        e = self.event('Shield Bash')
        self.assertEqual([f['type'] for f in e['effects']], ['damage', 'push'])
        self.assertEqual(e['effects'][0]['amount'], 4)
        self.assertEqual(e['effects'][1]['position'], dict(x=4, y=2))
        self.assertEqual(e['effects'][1]['destination'], dict(x=5, y=2))

    def test_snipe_has_distinct_semantics(self):
        self.assertEqual(self.event('Snipe')['type'], 'snipe')
        self.assertEqual(self.effects('Snipe', 'damage')[0]['amount'], 8)

    def test_fireball_all_victims_order_and_friendly_owners(self):
        e = self.event('Fireball')
        self.assertEqual(e['target'], dict(x=3, y=2))
        victims = self.effects('Fireball', 'damage')
        self.assertEqual([v['entity_id'] for v in victims], ['blue-knight', 'blue-mage', 'red-knight'])
        self.assertEqual([v['owner_id'] for v in victims], ['blue', 'blue', 'red'])
        self.assertTrue(all(v['hp_before'] - v['hp_after'] == v['amount'] for v in victims))

    def test_core_and_delayed_victory_with_terminal_mechanism(self):
        self.assertEqual(self.effects('Core damage', 'core_damage')[0]['entity_id'], 'red-core')
        events = self.fixtures['Victory']['batch']['events']
        self.assertEqual([e['type'] for e in events], ['attack', 'victory'])
        self.assertEqual(events[1]['winner_player_id'], 'blue')
        self.assertEqual(events[1]['terminal_reason'], 'Core destroyed')

    def test_end_turn_contains_next_player_turn_and_ap(self):
        e = self.event('Turn')
        self.assertEqual(e['type'], 'turn_end')
        self.assertEqual(e['transition'], dict(turn=0, active_player_id='red', action_points_remaining=5))

    def test_fixture_generation_is_deterministic_and_committed_json_matches(self):
        self.assertEqual(canonical_json(examples()), canonical_json(self.fixtures))
        committed = json.loads((Path(__file__).parents[1] / 'frontend/src/js/arena-lab-fixtures.json').read_text())
        self.assertEqual(committed, self.fixtures)

    def test_replay_and_state_hashes_identical_without_presentation(self):
        raw = ArenaSimulation()
        web = PresentationSimulation(raw)
        commands = [ArenaMove('blue', 'blue-ranger', Position(4, 0)), ArenaEndTurn('blue'), ArenaEndTurn('red')]
        for command in commands:
            self.assertEqual(raw.execute(command), web.execute(command))
            self.assertEqual(state_hash(raw.state), state_hash(web.state))
        self.assertEqual(raw.trace(), web.trace())
        self.assertEqual(replay(web.trace()).state, web.state)
        self.assertNotIn('presentation', canonical_json(raw.trace()))

    def test_rejection_does_not_generate_events(self):
        sim = PresentationSimulation(ArenaSimulation())
        with self.assertRaises(ValueError): sim.execute(ArenaEndTurn('red'))
        self.assertEqual(sim.presentation_events, [])

    def test_api_batches_entire_heuristic_turn_in_execution_order(self):
        with patch('aig.api.load_settings', return_value=load_settings(local_file=None, environ={})):
            app = create_app()
        with TestClient(app) as client:
            start = client.post('/api/arena/demo-ai').json()
            response = client.post('/api/arena/commands', json=command_to_dict(ArenaEndTurn('blue')))
            self.assertEqual(response.status_code, 200)
            final = response.json()
            batch = final['presentation']
            self.assertEqual(batch['version'], VERSION)
            self.assertEqual(batch['start_state_hash'], start['state_hash'])
            self.assertEqual(batch['final_state_hash'], final['state_hash'])
            events = batch['events']
            trace = app.state.arena_session.trace()
            self.assertGreater(len(events), 2)
            self.assertEqual([e['sequence'] for e in events], list(range(1, len(events)+1)))
            self.assertEqual([e['type'] for e in events], [e['command']['type'].removeprefix('arena_').replace('end_turn', 'turn_end') for e in trace['entries']])
            self.assertEqual([e['after_hash'] for e in events], [e['after_hash'] for e in trace['entries']])
            self.assertEqual(final['battle_log'], [e['log'] for e in events])
            self.assertNotIn('presentation', client.get('/api/arena').json())
            self.assertEqual(client.post('/api/arena/demo').json()['battle_log'], [])
            self.assertIn(client.get('/arena/presentation-lab').status_code, (200, 503))
