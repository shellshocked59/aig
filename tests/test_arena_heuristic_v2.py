"""Positional behavior, frozen V1, and offline V2 integration."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from aig.state import Position as P
from aig.settings import Settings
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.heuristic_v2 import HeuristicArenaTurnProviderV2, position_components, routes
from aig.arena.gameplay import create_offline_turn_provider as create_arena_turn_provider
from aig.arena.ai.observation import build_observation
from aig.arena.ai.probes import PROBE_NAMES, create_probe
from aig.arena.ai.contracts import action_command
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.commands import apply_command, find_path, ArenaEndTurn
from aig.arena.scenarios import create_scenario
from aig.arena.state import Bonus, Board, Tile, Terrain, ArenaUnit, UnitType as U, UnitStatus as S
from aig.arena.snapshots import state_hash
from aig.arena.gameplay import ArenaGameplaySession as ArenaSession
from aig.arena.heuristic_evaluation import board_metrics
from aig.arena.replay import ArenaSimulation


def positional_fixture(name):
    state = create_scenario()
    state.board = Board(tuple(Tile() for _ in range(45)))
    state.units = {"actor": ArenaUnit("actor", "blue", U.RANGER, P(2, 2), 10),
                   "enemy": ArenaUnit("enemy", "red", U.KNIGHT, P(7, 4), 18)}
    tiles = list(state.board.tiles)
    if name == "power":
        tiles[4] = Tile(bonus=Bonus.POWER)
        state.units["enemy"].position = P(7, 0)
    elif name == "ward":
        state.units["actor"].hp = 4
        state.units["enemy"].position = P(3, 2)
        tiles[2 * 9 + 5] = Tile(bonus=Bonus.WARD)
    elif name == "siege":
        tiles[2 * 9 + 5] = Tile(bonus=Bonus.SIEGE)
    elif name == "unsafe":
        state.units["actor"].hp = 3
        state.units["enemy"].position = P(5, 0)
        tiles[4] = Tile(bonus=Bonus.POWER)
        tiles[3 * 9 + 3] = Tile(bonus=Bonus.WARD)
    elif name != "open":
        raise ValueError(name)
    state.board = Board(tuple(tiles))
    state.validate()
    return state


class HeuristicV2Tests(unittest.TestCase):
    def plan(self, state):
        return HeuristicArenaTurnProviderV2().create_turn_plan(build_observation(state))

    def test_deterministic_detached_and_stable_ties(self):
        state = create_scenario()
        before = state_hash(state)
        plan = self.plan(state)
        self.assertEqual(state_hash(state), before)
        state.units = dict(reversed(list(state.units.items())))
        self.assertEqual(plan, self.plan(state))

    def test_open_center_advances_and_claims_power(self):
        for name in ("open", "power"):
            state = positional_fixture(name)
            action = self.plan(state).actions[0]
            self.assertEqual(action.type, "move")
            old = sum(position_components(state, state.units["actor"]).values())
            apply_command(state, action_command(action, "blue"))
            self.assertGreater(sum(position_components(state, state.units["actor"]).values()), old)
            if name == "power":
                self.assertIs(state.board.at(state.units["actor"].position).bonus, Bonus.POWER)

    def test_ward_safety_and_attack_vs_position(self):
        state = positional_fixture("ward")
        action = self.plan(state).actions[0]
        # A nonlethal attack exists, but leaving lethal exposure is more valuable.
        self.assertEqual(action.type, "move")
        apply_command(state, action_command(action, "blue"))
        self.assertIs(state.board.at(state.units["actor"].position).bonus, Bonus.WARD)

    def test_siege_approach_enables_core_attack(self):
        state = positional_fixture("siege")
        plan = self.plan(state)
        self.assertTrue(any(a.type == "attack" and a.target_id == "red-core" for a in plan.actions))
        first = plan.actions[0]
        self.assertEqual(first.type, "move")
        apply_command(state, action_command(first, "blue"))
        self.assertIs(state.board.at(state.units["actor"].position).bonus, Bonus.SIEGE)

    def test_does_not_claim_suicidal_power(self):
        state = positional_fixture("unsafe")
        first = self.plan(state).actions[0]
        if first.type == "move":
            self.assertNotEqual((first.destination.x, first.destination.y), (4, 0))
        else:
            self.assertEqual(first.type, "attack")
        apply_command(state, action_command(first, "blue"))
        self.assertGreaterEqual(position_components(state, state.units["actor"])["exposure"], -6)

    def test_all_frozen_tactical_behaviors_and_legal_suffixes(self):
        expected = ("finish", "revive", "fireball", "shield_bash", "snipe", "attack", "attack")
        for name, kind in zip(PROBE_NAMES, expected):
            with self.subTest(name=name):
                state = create_probe(name)
                plan = self.plan(state)
                self.assertEqual(plan.actions[0].type, kind)
                result = execute_arena_turn(state, plan)
                self.assertIsNone(result.invalid_action)

    def test_heal_and_no_friendly_fire_down(self):
        state = create_probe("revive_decision")
        state.units["ally"].status, state.units["ally"].hp = S.ACTIVE, 3
        state.units["actor"].hp = 5
        state.units["enemy"].position = P(7, 4)
        self.assertEqual(self.plan(state).actions[0].type, "heal")
        state = create_probe("fireball_friendly_fire")
        state.units["ally"].hp = 1
        action = self.plan(state).actions[0]
        apply_command(state, action_command(action, "blue"))
        self.assertGreater(state.units["ally"].hp, 0)

    def test_ap_and_no_loops(self):
        for ap in range(6):
            state = create_scenario()
            state.action_points_remaining = ap
            plan = self.plan(state)
            self.assertLessEqual(plan.ap_cost, ap)
            visited = {u.id: {u.position} for u in state.units.values()}
            for action in plan.actions:
                apply_command(state, action_command(action, "blue"))
                if action.type == "move":
                    pos = state.units[action.unit_id].position
                    self.assertNotIn(pos, visited[action.unit_id])
                    visited[action.unit_id].add(pos)
            self.assertGreaterEqual(state.action_points_remaining, 0)

    def test_ends_when_no_productive_action_exists(self):
        state = positional_fixture("open")
        occupied = {u.position for u in state.units.values()} | {c.position for c in state.cores.values()}
        state.board = Board(tuple(Tile() if P(x, y) in occupied else Tile(Terrain.BLOCKED)
                                  for y in range(5) for x in range(9)))
        self.assertEqual(self.plan(state).actions, ())

    def test_revived_ally_can_act_and_core_emergency_dominates(self):
        plan = self.plan(create_probe("revive_decision"))
        self.assertTrue(any(a.unit_id == "ally" for a in plan.actions[1:]))
        state = create_probe("team_elimination")
        state.units["enemy"].position = P(1, 2)
        state.cores["blue-core"].hp = 6
        state.units["survivor"] = ArenaUnit("survivor", "red", U.CLERIC, P(7, 4), 11)
        action = self.plan(state).actions[0]
        self.assertEqual((action.type, action.target_id), ("attack", "enemy"))

    def test_bash_denial_and_siege_are_contextual(self):
        state = create_probe("shield_bash_position")
        provider = HeuristicArenaTurnProviderV2()
        action = provider.create_turn_plan(build_observation(state)).actions[0]
        self.assertGreater(provider.last_scores[0]["components"]["premium_denial"], 0)
        apply_command(state, action_command(action, "blue"))
        self.assertIsNone(state.board.at(state.units["enemy"].position).bonus)
        state = positional_fixture("siege")
        unit = state.units["actor"]
        unit.position = P(5, 2)
        offensive = position_components(state, unit)["premium_control"]
        unit.unit_type = U.KNIGHT
        self.assertLess(position_components(state, unit)["premium_control"], offensive)

    def test_mixed_controller_versions_do_not_silently_switch(self):
        from aig.arena.simulate import simulate
        report = simulate(blue_provider="heuristic-v1", red_provider="heuristic-v2", max_turns=1,
                          provider_factory=create_arena_turn_provider)
        self.assertEqual([t["provider_type"] for t in report["ai_traces"]], ["arena-heuristic-v1", "arena-heuristic-v2"])

    def test_routes_match_authoritative_bfs_and_los(self):
        state = create_scenario()
        unit = state.units["blue-ranger"]
        for pos, length in routes(state, unit).items():
            self.assertEqual(length, len(find_path(state, unit.id, pos)) - 1)
        # Entire plan passes real movement, LOS, and AP validation.
        self.assertIsNone(execute_arena_turn(state, self.plan(state)).invalid_action)

    def test_explicit_versions_defaults_and_session_no_network(self):
        settings = Settings()
        for name in (None, "heuristic", "heuristic-v1"):
            self.assertIs(type(create_arena_turn_provider(settings, name)), HeuristicArenaTurnProvider)
        self.assertIsInstance(create_arena_turn_provider(settings, "heuristic-v2"), HeuristicArenaTurnProviderV2)
        with patch("aig.arena.ai.factory.OllamaArenaTurnProvider", side_effect=AssertionError("network")), patch("aig.arena.ai.factory.OpenAIArenaTurnProvider", side_effect=AssertionError("network")):
            session = ArenaSession(settings)
            self.assertEqual(session.demo(versus_ai=True, provider="heuristic-v2")["controllers"]["red"], "heuristic-v2_ai")
            result = session.execute(ArenaEndTurn("blue"))
            self.assertEqual(result["ai_turns"][0]["provider_type"], "arena-heuristic-v2")
            self.assertIsNone(result["ai_turns"][0]["invalid_action"])

    def test_metrics_do_not_count_end_turn_as_occupancy_action(self):
        sim = ArenaSimulation(positional_fixture("power"))
        sim.execute(ArenaEndTurn("blue"))
        rows = board_metrics(sim.trace())
        self.assertEqual(rows["blue"]["premium_occupancy_actions"], 0)
        self.assertEqual(len(rows["blue"]["progression"]), 1)

    def test_http_v2_uses_standard_presentation_events(self):
        from fastapi.testclient import TestClient
        from aig.web import create_app
        from aig.arena.snapshots import command_to_dict
        with TestClient(create_app()) as client:
            response = client.post("/api/arena/demo-ai/heuristic-v2")
            self.assertEqual(response.status_code, 200)
            response = client.post("/api/arena/commands", json=command_to_dict(ArenaEndTurn("blue")))
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["ai_turns"][0]["provider_type"], "arena-heuristic-v2")
            self.assertTrue(payload["presentation"]["events"])


if __name__ == "__main__":
    unittest.main()
