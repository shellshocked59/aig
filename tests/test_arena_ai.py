"""Phase 3 contracts, real sequential execution, tactical probes and deterministic matches."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest
from unittest.mock import Mock, patch

from aig.state import Position as P
from aig.arena import ArenaSimulation, create_scenario, state_hash, to_snapshot, replay
from aig.arena.commands import apply_command, ArenaEndTurn, ACTION_COSTS
from aig.arena.state import UnitStatus as S, UnitType as U, ArenaUnit, Board, Tile, Bonus
from aig.arena.snapshots import canonical_json, digest
from aig.arena.ai import ArenaTurnPlan, build_observation, HeuristicArenaTurnProvider, execute_arena_turn
from aig.arena.ai.contracts import (ArenaPosition as AP, AttackAction, MoveAction, HealAction, FinishAction,
                                   ReviveAction, ShieldBashAction, SnipeAction, FireballAction,
                                   action_command, action_from_dict, turn_plan_schema, PLAN_SCHEMA_VERSION)
from aig.arena.ai.observation import ArenaObservation, simulation_state
from aig.arena.ai.controller import (ArenaAiController, ArenaControllerType, advance_until_human,
                                    controller_setup, AI_TRACE_VERSION)
from aig.arena.ai.heuristic import fireball_utility
from aig.arena.ai.metrics import ai_metrics
from aig.arena.ai.probes import create_probe, PROBE_NAMES
from aig.arena.simulate import simulate


def plan_for(state):
    return HeuristicArenaTurnProvider().create_turn_plan(build_observation(state))


class ObservationTests(unittest.TestCase):
    def test_full_board_teams_stats_abilities_and_legal_options(self):
        state = create_scenario()
        data = build_observation(state).to_dict()
        self.assertEqual(len(data["board"]["tiles"]), 45)
        self.assertEqual((data["board"]["width"], data["board"]["height"]), (9, 5))
        self.assertEqual({t["bonus"] for t in data["board"]["tiles"]}, {None, "power", "ward", "siege"})
        self.assertEqual(sum(t["terrain"] == "blocked" for t in data["board"]["tiles"]), 4)
        for team, owner in (("own_team", "blue"), ("enemy_team", "red")):
            self.assertEqual(data[team]["player_id"], owner)
            self.assertEqual(data[team]["core"]["hp"], 30)
            self.assertEqual(len(data[team]["units"]), 4)
            for unit in data[team]["units"]:
                self.assertEqual(unit["hp"], unit["max_hp"])
                self.assertIn("attack", unit["abilities"])
                self.assertIn("range", unit["abilities"]["attack"])
                self.assertIn("damage", unit["stats"])
        self.assertTrue(any(u["actions"]["move"] for u in data["own_team"]["units"]))
        self.assertEqual(data["action_points_remaining"], 5)
        self.assertEqual(data["action_rules"]["snipe"]["base_damage"], 8)
        self.assertTrue(data["action_rules"]["fireball"]["friendly_fire"])
        self.assertEqual(data["bonus_rules"]["siege_core_damage"], 4)

    def test_active_and_downed_are_explicit(self):
        data = build_observation(create_probe("revive_decision")).to_dict()
        body = next(u for u in data["own_team"]["units"] if u["id"] == "ally")
        self.assertEqual((body["status"], body["hp"]), ("downed", 0))
        self.assertFalse(any(body["actions"].values()))

    def test_observation_frozen_detached_json_only_and_roundtrip(self):
        state = create_scenario()
        obs = build_observation(state)
        before = state_hash(state)
        self.assertEqual(state_hash(simulation_state(obs)), before)
        self.assertEqual(ArenaObservation.from_dict(json.loads(obs.canonical)), obs)
        self.assertEqual(obs.hash, digest(obs.to_dict()))
        with self.assertRaises(FrozenInstanceError):
            obs.canonical = "changed"
        data = obs.to_dict()
        data["own_team"]["units"].clear()
        self.assertEqual(state_hash(state), before)
        apply_command(state, ArenaEndTurn("blue"))
        self.assertEqual(obs.to_dict()["active_player_id"], "blue")
        self.assertEqual(build_observation(state).to_dict()["own_team"]["player_id"], "red")

    def test_order_deterministic(self):
        state = create_scenario()
        obs = build_observation(state)
        state.units = dict(reversed(list(state.units.items())))
        state.cores = dict(reversed(list(state.cores.items())))
        self.assertEqual(obs, build_observation(state))

    def test_forged_facts_rejected(self):
        data = build_observation(create_scenario()).to_dict()
        data["own_team"]["units"][0]["stats"]["damage"] = 1000
        with self.assertRaises(ValueError):
            ArenaObservation.from_dict(data)

    def test_terminal_has_no_observation(self):
        state = create_probe("winning_core_line")
        execute_arena_turn(state, plan_for(state))
        with self.assertRaises(ValueError):
            build_observation(state)


class TurnPlanTests(unittest.TestCase):
    def test_empty_short_and_mixed_plan_roundtrip(self):
        for plan in (ArenaTurnPlan(), ArenaTurnPlan((AttackAction("u", "core"),)),
                     ArenaTurnPlan((MoveAction("u", AP(1, 2)), SnipeAction("r", "e"), ReviveAction("c", "u")))):
            self.assertEqual(ArenaTurnPlan.from_dict(plan.to_dict()), plan)
            self.assertEqual(canonical_json(plan.to_dict()), canonical_json(ArenaTurnPlan.from_dict(plan.to_dict()).to_dict()))
            self.assertLessEqual(plan.ap_cost, 5)
            self.assertEqual(plan.schema_version, PLAN_SCHEMA_VERSION)

    def test_every_discriminated_action_maps_to_existing_command(self):
        for cls in (AttackAction, HealAction, FinishAction, ReviveAction, ShieldBashAction, SnipeAction, MoveAction, FireballAction):
            action = cls("actor", AP(1, 2) if cls in (MoveAction, FireballAction) else "target")
            self.assertEqual(action_from_dict(action.to_dict()), action)
            command = action_command(action, "blue")
            self.assertEqual(command.unit_id, "actor")
            self.assertEqual(command.actor_id, "blue")
            with self.assertRaises(FrozenInstanceError):
                action.unit_id = "changed"

    def test_budget_and_action_count_rejected(self):
        for actions in ((SnipeAction("r", "e"),) * 3, (AttackAction("a", "e"),) * 6, []):
            with self.subTest(actions=actions), self.assertRaises(ValueError):
                ArenaTurnPlan(actions)

    def test_malformed_unknown_extra_and_end_turn_rejected(self):
        bad = [dict(type="unknown", unit_id="a", target_id="b"), dict(type="attack", unit_id="a"),
               dict(type="end_turn"), dict(type=[], unit_id="a"),
               dict(type="attack", unit_id=" ", target_id="b"),
               dict(type="attack", unit_id="a", target_id="b", reasoning="x"),
               dict(type="move", unit_id="a", destination=dict(x=True, y=0)),
               dict(type="move", unit_id="a", destination=dict(x=9, y=0)),
               dict(type="fireball", unit_id="a", target_position=dict(x=0, y=-1))]
        for action in bad:
            with self.subTest(action=action), self.assertRaises(ValueError):
                ArenaTurnPlan.from_dict(dict(schema_version=PLAN_SCHEMA_VERSION, actions=[action]))

    def test_schema_version_and_local_schema(self):
        with self.assertRaises(ValueError):
            ArenaTurnPlan(schema_version="strategic-plan-schema-v1")
        schema = turn_plan_schema()
        self.assertEqual(schema["$id"], PLAN_SCHEMA_VERSION)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(len(schema["properties"]["actions"]["items"]["oneOf"]), 8)


class ExecutorTests(unittest.TestCase):
    def test_five_ap_in_order_and_explicit_end_turn(self):
        sim = ArenaSimulation(create_probe("finish_or_core"))
        plan = ArenaTurnPlan((AttackAction("actor", "red-core"),) * 4 + (FinishAction("actor", "body"),))
        result = execute_arena_turn(sim.state, plan, execute_command=sim.execute)
        self.assertEqual((result.ap_spent, result.ap_unused), (5, 0))
        self.assertEqual([a["ap_after"] for a in result.actions_attempted], [4, 3, 2, 1, 0])
        self.assertEqual(len(result.commands_executed), 6)
        self.assertEqual(result.commands_executed[-1]["type"], "arena_end_turn")
        self.assertEqual(result.resulting_active_player, "red")
        self.assertEqual(sim.state.cores["red-core"].hp, 6)
        self.assertNotIn("body", sim.state.units)
        self.assertEqual(replay(sim.trace()).trace(), sim.trace())

    def test_empty_and_short_plans_end_turn_and_record_unused(self):
        for actions, spent in (((), 0), ((FinishAction("actor", "body"),), 1)):
            state = create_probe("finish_or_core")
            result = execute_arena_turn(state, ArenaTurnPlan(actions))
            self.assertEqual((result.ap_spent, result.ap_unused), (spent, 5 - spent))
            self.assertIsNone(result.truncation_reason)
            self.assertEqual(state.active_player_id, "red")

    def test_later_invalid_truncates_keeps_prefix_and_ends_turn(self):
        state = create_probe("snipe_vs_basic")
        plan = ArenaTurnPlan((SnipeAction("actor", "enemy"), SnipeAction("actor", "enemy"), AttackAction("actor", "enemy2")))
        result = execute_arena_turn(state, plan)
        self.assertEqual(state.units["enemy"].status, S.DOWNED)
        self.assertEqual(state.units["enemy2"].hp, 18)
        self.assertEqual((result.ap_spent, result.ap_unused), (2, 3))
        self.assertEqual(len(result.actions_attempted), 2)
        self.assertIn("status", result.invalid_action["reason"])
        self.assertEqual(result.invalid_action["index"], 1)
        self.assertEqual(result.truncation_reason, "invalid_action")
        self.assertEqual([c["type"] for c in result.commands_executed], ["arena_snipe", "arena_end_turn"])
        state.validate()

    def test_first_invalid_consumes_no_ap(self):
        state = create_scenario()
        result = execute_arena_turn(state, ArenaTurnPlan((AttackAction("missing", "red-core"),)))
        self.assertEqual((result.ap_spent, result.ap_unused), (0, 5))
        self.assertEqual(result.invalid_action["index"], 0)
        self.assertEqual(state.active_player_id, "red")

    def test_remaining_ap_validated_sequentially(self):
        state = create_probe("snipe_vs_basic")
        state.action_points_remaining = 1
        result = execute_arena_turn(state, ArenaTurnPlan((SnipeAction("actor", "enemy"),)))
        self.assertEqual((result.ap_available, result.ap_spent, result.ap_unused), (1, 0, 1))
        self.assertIn("insufficient AP", result.invalid_action["reason"])

    def test_terminal_truncation_no_end_turn_or_remaining_actions(self):
        state = create_probe("winning_core_line")
        plan = ArenaTurnPlan((AttackAction("actor", "red-core"), FinishAction("actor", "body")))
        result = execute_arena_turn(state, plan)
        self.assertEqual(result.truncation_reason, "terminal")
        self.assertEqual(result.terminal_result, "blue")
        self.assertIsNone(result.resulting_active_player)
        self.assertEqual(len(result.commands_executed), 1)
        self.assertEqual(len(result.actions_attempted), 1)
        self.assertIn("body", state.units)
        self.assertEqual((result.ap_spent, result.ap_unused), (1, 4))

    def test_invalid_structure_and_terminal_input_do_not_mutate(self):
        state = create_probe("winning_core_line")
        before = state_hash(state)
        with self.assertRaises(ValueError):
            execute_arena_turn(state, {"actions": []})
        self.assertEqual(state_hash(state), before)
        execute_arena_turn(state, plan_for(state))
        before = state_hash(state)
        with self.assertRaises(ValueError):
            execute_arena_turn(state, ArenaTurnPlan())
        self.assertEqual(state_hash(state), before)


class HeuristicTests(unittest.TestCase):
    def test_all_probes_validate_and_produce_legal_sensible_plans(self):
        expected = dict(finish_or_core="finish", revive_decision="revive", fireball_friendly_fire="fireball",
                        shield_bash_position="shield_bash", snipe_vs_basic="snipe", winning_core_line="attack", team_elimination="attack")
        for name in PROBE_NAMES:
            with self.subTest(probe=name):
                state = create_probe(name)
                state.validate()
                before = state_hash(state)
                plan = plan_for(state)
                self.assertEqual(state_hash(state), before)
                self.assertEqual(plan.actions[0].type, expected[name])
                result = execute_arena_turn(state, plan)
                self.assertIsNone(result.invalid_action)
                state.validate()

    def test_same_observation_plan_even_reordered_units(self):
        state = create_scenario()
        first = plan_for(state)
        state.units = dict(reversed(list(state.units.items())))
        self.assertEqual(plan_for(state), first)
        self.assertEqual(first.ap_cost, 5)

    def test_core_win_beats_finish_and_includes_siege_modifier(self):
        state = create_probe("winning_core_line")
        plan = plan_for(state)
        self.assertEqual(plan.actions, (AttackAction("actor", "red-core"),))

    def test_final_active_down_wins_without_finish(self):
        state = create_probe("team_elimination")
        plan = plan_for(state)
        self.assertEqual(plan.actions, (AttackAction("actor", "enemy"),))
        execute_arena_turn(state, plan)
        self.assertEqual(state.winner_player_id, "blue")
        self.assertIn("body", state.units)

    def test_revived_unit_can_act_later_in_same_plan(self):
        state = create_probe("revive_decision")
        plan = plan_for(state)
        self.assertEqual(plan.actions[0], ReviveAction("actor", "ally"))
        self.assertTrue(any(a.unit_id == "ally" for a in plan.actions[1:]))

    def test_fireball_accepts_small_friendly_damage_for_two_enemies(self):
        state = create_probe("fireball_friendly_fire")
        action = plan_for(state).actions[0]
        before = deepcopy(state)
        apply_command(state, action_command(action, "blue"))
        score = fireball_utility(before, state, "blue")
        self.assertEqual(score["enemy_hits"], 2)
        self.assertEqual(before.units["ally"].hp - state.units["ally"].hp, 2)
        self.assertGreater(score["utility"], 0)

    def test_fireball_avoids_friendly_down(self):
        state = create_probe("fireball_friendly_fire")
        state.units["ally"].hp = 1
        action = plan_for(state).actions[0]
        after = deepcopy(state)
        apply_command(after, action_command(action, "blue"))
        self.assertGreater(after.units["ally"].hp, 0)

    def test_shield_bash_pushes_off_bonus(self):
        state = create_probe("shield_bash_position")
        action = plan_for(state).actions[0]
        apply_command(state, action_command(action, "blue"))
        self.assertEqual(state.units["enemy"].position, P(4, 2))
        self.assertIsNone(state.board.at(state.units["enemy"].position).bonus)

    def test_snipe_lethal_distant_and_basic_when_comparable(self):
        state = create_probe("snipe_vs_basic")
        self.assertEqual(plan_for(state).actions[0], SnipeAction("actor", "enemy"))
        state.units["enemy"].position = P(4, 2)
        state.units["enemy"].hp = 5
        self.assertEqual(plan_for(state).actions[0], AttackAction("actor", "enemy"))

    def test_heal_most_missing_hp_then_health_ratio(self):
        state = create_probe("revive_decision")
        state.units["ally"].status, state.units["ally"].hp = S.ACTIVE, 3
        state.units["actor"].hp = 5
        state.units["enemy"].position = P(7, 4)
        self.assertEqual(plan_for(state).actions[0], HealAction("actor", "ally"))

    def test_core_pressure_when_no_useful_unit_interaction(self):
        state = create_probe("finish_or_core")
        del state.units["body"]
        self.assertEqual(plan_for(state).actions[0], AttackAction("actor", "red-core"))

    def test_movement_uses_bonus_and_engine_routes(self):
        state = create_scenario()
        action = plan_for(state).actions[0]
        self.assertEqual(action.type, "move")
        self.assertIsNotNone(state.board.at(P(action.destination.x, action.destination.y)).bonus)
        apply_command(state, action_command(action, "blue"))
        state.validate()

    def test_lethal_target_class_then_hp_then_id(self):
        state = create_probe("snipe_vs_basic")
        state.units["enemy"].position, state.units["enemy"].hp = P(3, 2), 3
        state.units["enemy2"].hp = 3
        state.units["cleric"] = ArenaUnit("cleric", "red", U.CLERIC, P(2, 3), 3)
        self.assertEqual(plan_for(state).actions[0].target_id, "cleric")
        del state.units["cleric"]
        self.assertEqual(plan_for(state).actions[0].target_id, "enemy")
        state.units["enemy2"].unit_type = U.MAGE
        state.units["enemy2"].hp = 2
        self.assertEqual(plan_for(state).actions[0].target_id, "enemy2")
        state.units["enemy2"].hp = 3
        self.assertEqual(plan_for(state).actions[0].target_id, "enemy")

    def test_prevents_obvious_core_loss_before_finishing_body(self):
        state = create_probe("team_elimination")
        state.units["enemy"].position = P(1, 2)
        state.cores["blue-core"].hp = 6
        state.units["survivor"] = ArenaUnit("survivor", "red", U.CLERIC, P(7, 4), 11)
        self.assertEqual(plan_for(state).actions[0], AttackAction("actor", "enemy"))

    def test_available_ap_bounds_and_zero_ap(self):
        for ap in range(6):
            state = create_scenario()
            state.action_points_remaining = ap
            plan = plan_for(state)
            self.assertLessEqual(plan.ap_cost, ap)
            self.assertIsNone(execute_arena_turn(state, plan).invalid_action)


class ControllerTests(unittest.TestCase):
    def test_observation_and_provider_once_trace_detached_not_persistent(self):
        sim = ArenaSimulation()
        provider = Mock()
        provider.name = "stub"
        provider.create_turn_plan.return_value = ArenaTurnPlan()
        with patch("aig.arena.ai.controller.build_observation", wraps=build_observation) as build:
            trace = ArenaAiController(provider).run_turn(sim)
        self.assertEqual(build.call_count, 1)
        self.assertEqual(provider.create_turn_plan.call_count, 1)
        row = trace.to_dict()
        self.assertEqual(row["schema_version"], AI_TRACE_VERSION)
        self.assertEqual(row["actions_executed"], 0)
        self.assertEqual(row["ap_unused"], 5)
        row["plan"]["actions"].append("bad")
        self.assertEqual(trace.to_dict()["plan"]["actions"], [])
        self.assertNotIn("plan", to_snapshot(sim.state))
        self.assertNotIn("controllers", to_snapshot(sim.state))

    def test_human_not_played_and_ai_returns_to_human(self):
        sim = ArenaSimulation()
        controllers = controller_setup(sim.state, "human_vs_heuristic")
        self.assertEqual(advance_until_human(sim, controllers), ())
        sim.execute(ArenaEndTurn("blue"))
        traces = advance_until_human(sim, controllers)
        self.assertEqual(len(traces), 1)
        self.assertEqual(sim.state.active_player_id, "blue")

    def test_consecutive_ai_turns_stop_at_terminal(self):
        sim = ArenaSimulation(create_probe("winning_core_line"))
        traces = advance_until_human(sim, controller_setup(sim.state, "heuristic_vs_heuristic"))
        self.assertEqual(len(traces), 1)
        self.assertEqual(sim.state.winner_player_id, "blue")

    def test_ai_only_empty_provider_is_bounded_without_game_draw(self):
        sim = ArenaSimulation()
        provider = Mock()
        provider.name = "empty"
        provider.create_turn_plan.return_value = ArenaTurnPlan()
        traces = advance_until_human(sim, controller_setup(sim.state, "heuristic_vs_heuristic"),
                                     controller=ArenaAiController(provider), max_ai_turns=3)
        self.assertEqual(len(traces), 3)
        self.assertIsNone(sim.state.winner_player_id)

    def test_provider_failure_does_not_retry_or_mutate(self):
        sim = ArenaSimulation()
        provider = Mock()
        provider.create_turn_plan.side_effect = RuntimeError("provider unavailable")
        before = state_hash(sim.state)
        with self.assertRaises(RuntimeError):
            ArenaAiController(provider).run_turn(sim)
        self.assertEqual(provider.create_turn_plan.call_count, 1)
        self.assertEqual(state_hash(sim.state), before)
        self.assertEqual(sim.trace()["entries"], [])


class MatchMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = simulate()

    def test_full_match_all_mechanics_legal_replay_and_deterministic_hashes(self):
        report = self.report
        self.assertEqual(report["outcome"], "victory")
        self.assertTrue(report["replay_exact"])
        self.assertEqual(report["hashes"], simulate()["hashes"])
        players = report["metrics"]["players"]
        for kind in ACTION_COSTS:
            if kind != "end_turn":
                self.assertGreater(sum(p["actions_by_type"][kind] for p in players.values()), 0)
        self.assertTrue(all(p["invalid_planned_actions"] == 0 for p in players.values()))

    def test_metrics_budget_action_quality_and_final_units(self):
        report = self.report
        for player, m in report["metrics"]["players"].items():
            self.assertEqual(m["ap_available"], m["ap_spent"] + m["ap_unused"])
            self.assertEqual(m["ap_available"], 5 * m["turns_taken"])
            self.assertEqual(m["planned_actions"], m["successfully_executed_actions"])
            self.assertEqual(m["successfully_executed_actions"], sum(m["actions_by_type"].values()))
            self.assertEqual(m["living_units"] + m["downed_units"] + m["removed_units"], 4)
            self.assertEqual(m["winner"], report["winner"] == player)
            self.assertEqual(m["average_ap_used"], m["ap_spent"] / m["turns_taken"])
        self.assertEqual(report["metrics"]["turns_to_victory"], report["player_turns"])

    def test_explicit_simulation_limit_is_nonterminal(self):
        report = simulate(max_turns=1)
        self.assertEqual(report["outcome"], "turn_limit")
        self.assertIsNone(report["winner"])
        self.assertEqual(report["global_turns"], 1)
        self.assertEqual(report["player_turns"], 2)
        self.assertTrue(report["replay_exact"])

    def test_invalid_limit(self):
        for limit in (0, -1, True):
            with self.assertRaises(ValueError):
                simulate(max_turns=limit)

    def test_friendly_fire_metrics_and_damage_received(self):
        sim = ArenaSimulation(create_probe("fireball_friendly_fire"))
        provider = Mock()
        provider.name = "probe"
        provider.create_turn_plan.return_value = ArenaTurnPlan((FireballAction("actor", AP(4, 1)),))
        trace = ArenaAiController(provider).run_turn(sim)
        metrics = ai_metrics(sim, [trace])["players"]
        self.assertEqual(metrics["blue"]["friendly_fire_damage"], 2)
        self.assertEqual(metrics["blue"]["damage_dealt"], 10)
        self.assertEqual(metrics["red"]["damage_received"], 8)
        self.assertEqual(metrics["blue"]["damage_received"], 2)
        self.assertEqual(metrics["blue"]["fireball_targets_hit"], 3)

    def test_invalid_plan_quality_and_zero_action_metrics(self):
        sim = ArenaSimulation()
        provider = Mock()
        provider.name = "probe"
        provider.create_turn_plan.return_value = ArenaTurnPlan((AttackAction("missing", "red-core"),))
        trace = ArenaAiController(provider).run_turn(sim)
        m = ai_metrics(sim, [trace])["players"]["blue"]
        self.assertEqual((m["planned_actions"], m["successfully_executed_actions"], m["invalid_planned_actions"]), (1, 0, 1))
        self.assertEqual((m["truncated_turns"], m["zero_action_turns"], m["ap_unused"]), (1, 1, 5))

    def test_exact_healing_revive_finish_core_and_down_metrics(self):
        cases = [("revive_decision", ReviveAction("actor", "ally"), "units_revived", 1),
                 ("finish_or_core", FinishAction("actor", "body"), "units_finished", 1),
                 ("winning_core_line", AttackAction("actor", "red-core"), "core_damage", 9),
                 ("team_elimination", AttackAction("actor", "enemy"), "units_downed", 1)]
        for name, action, counter, expected in cases:
            with self.subTest(counter=counter):
                sim = ArenaSimulation(create_probe(name))
                provider = Mock()
                provider.name = "probe"
                provider.create_turn_plan.return_value = ArenaTurnPlan((action,))
                trace = ArenaAiController(provider).run_turn(sim)
                m = ai_metrics(sim, [trace])["players"]["blue"]
                self.assertEqual(m[counter], expected)
                if action.type == "revive":
                    self.assertEqual(m["healing_done"], 5)
        state = create_probe("revive_decision")
        state.units["actor"].hp = 3
        sim = ArenaSimulation(state)
        provider.create_turn_plan.return_value = ArenaTurnPlan((HealAction("actor", "actor"),))
        trace = ArenaAiController(provider).run_turn(sim)
        self.assertEqual(ai_metrics(sim, [trace])["players"]["blue"]["healing_done"], 5)


if __name__ == "__main__":
    unittest.main()
