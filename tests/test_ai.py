"""Planning contracts, legal command execution, reuse, and long deterministic play."""

from copy import deepcopy
from dataclasses import replace
import json
import unittest
from unittest.mock import Mock, patch

from aig.ai.controller import AiController, AiOrchestrator
from aig.ai.executor import AiActionLimitError, AiExecutor
from aig.ai.simulate import simulate
from aig.ai.strategy import (
    ExpansionPriority, HeuristicStrategyProvider, Posture, StrategicPlan, StrategicStateBuilder,
)
from aig.cities import can_found_city_at
from aig.combat import preview_attack
from aig.commands import (
    AttackUnit, EndActivation, FoundCity, MoveUnit, SetCityProduction, SetResearch, apply_command,
)
from aig.scenarios import demo_game_setup, human_vs_ai_demo_setup
from aig.setup import create_game, start_game
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    CityState, ControllerType, GameConfig, GameMap, GameState, PlayerState,
    Position, Technology, Terrain, TileState, UnitType,
)


def world():
    return GameState(GameConfig(42), game_map=GameMap(9, 7),
                     players={p: PlayerState(p, ControllerType.AI) for p in "AB"},
                     turn_order=["A", "B"], active_player_id="A",
                     tiles={Position(x, y): TileState(Position(x, y))
                            for y in range(7) for x in range(9)})


def city(state, owner="A", x=1, y=1, name=None):
    return state.add_city(CityState(name or f"city-{owner}", owner, Position(x, y), name="Town"))


def unit(state, kind=UnitType.WARRIOR, owner="A", x=1, y=1, hp=100):
    result = state.add_unit(owner, kind, Position(x, y))
    result.hp = hp
    return result


def plan(state):
    return HeuristicStrategyProvider().create_plan(StrategicStateBuilder().build(state, "A"))


def commands(result, kind):
    return [c for c in result.commands_executed if isinstance(c, kind)]


class StrategicStateTests(unittest.TestCase):
    def setUp(self):
        self.state = world()
        city(self.state)
        city(self.state, "B", 7, 5)
        unit(self.state)
        unit(self.state, UnitType.SETTLER)
        unit(self.state, UnitType.ARCHER, "B", 7, 5, 50)

    def test_own_and_enemy_entities_are_compressed_and_sorted(self):
        view = StrategicStateBuilder().build(self.state, "A")
        self.assertEqual([u["type"] for u in view["own_units"]], ["warrior", "settler"])
        self.assertEqual(view["own_cities"][0]["population"], 1)
        self.assertEqual(view["enemy_cities"][0]["owner_id"], "B")
        self.assertEqual(view["enemy_units"][0]["hp"], 50)
        self.assertNotIn("tiles", view)
        self.assertNotIn("config", view)

    def test_strength_is_hp_scaled_and_ranged_aware(self):
        view = StrategicStateBuilder().build(self.state, "A")
        self.assertEqual(view["own_military_strength"], 20)
        self.assertEqual(view["enemy_military_strength"], 10)

    def test_economy_and_available_choices(self):
        self.state.players["A"].gold = 12
        self.state.players["A"].science_stored = 7
        view = StrategicStateBuilder().build(self.state, "A")
        self.assertEqual((view["gold"], view["science_stored"], view["science_per_activation"]), (12, 7, 1))
        self.assertEqual(view["available_research"], ["archery", "bronze_working"])
        self.assertEqual(view["known_technologies"], ["agriculture"])
        self.assertNotIn("archer", view["available_production"])

    def test_view_is_detached_and_contains_only_json_primitives(self):
        view = StrategicStateBuilder().build(self.state, "A")
        def check(value):
            self.assertIn(type(value), (dict, list, str, int, type(None)))
            if type(value) is dict:
                for key, child in value.items():
                    self.assertIs(type(key), str)
                    check(child)
            elif type(value) is list:
                for child in value:
                    check(child)
        check(view)
        self.assertEqual(json.loads(json.dumps(view)), view)
        view["own_units"][0]["hp"] = 1
        self.assertEqual(self.state.units["unit-1"].hp, 100)

    def test_construction_ignores_dictionary_order(self):
        expected = StrategicStateBuilder().build(self.state, "A")
        for name in ("players", "tiles", "units", "cities"):
            setattr(self.state, name, dict(reversed(list(getattr(self.state, name).items()))))
        self.assertEqual(StrategicStateBuilder().build(self.state, "A"), expected)

    def test_unknown_or_eliminated_player_rejected(self):
        with self.assertRaises(ValueError):
            StrategicStateBuilder().build(self.state, "missing")
        self.state.eliminate_player("B")
        with self.assertRaises(ValueError):
            StrategicStateBuilder().build(self.state, "B")


class StrategyTests(unittest.TestCase):
    def test_valid_plan_json(self):
        result = StrategicPlan(Posture.ATTACK, "B", "city-B")
        encoded = json.loads(json.dumps(result.to_dict()))
        self.assertEqual(encoded["posture"], "attack")
        self.assertEqual(encoded["research_priority"][:2], ["archery", "bronze_working"])
        self.assertNotIn("reasoning", encoded)

    def test_invalid_plan_fields_rejected(self):
        for kwargs in ({"posture": "attack"}, {"primary_enemy_id": ""},
                       {"expansion_priority": "high"}, {"production_priority": ()},
                       {"research_priority": (Technology.ARCHERY, Technology.ARCHERY)},
                       {"production_priority": [UnitType.WARRIOR]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                StrategicPlan(**{"posture": Posture.EXPAND, **kwargs})

    def test_no_city_and_settler_expands(self):
        state = world()
        unit(state, UnitType.SETTLER)
        self.assertEqual(plan(state).posture, Posture.EXPAND)
        self.assertEqual(plan(state).expansion_priority, ExpansionPriority.HIGH)

    def test_low_military_production_priority(self):
        state = world()
        city(state)
        self.assertEqual(plan(state).production_priority[0], UnitType.WARRIOR)

    def test_adequate_military_one_city_prioritizes_settler(self):
        state = world()
        city(state)
        unit(state)
        unit(state)
        self.assertEqual(plan(state).production_priority[0], UnitType.SETTLER)

    def test_two_cities_prioritize_archer_spearman_warrior(self):
        state = world()
        city(state)
        city(state, "A", 5, 1, "second")
        unit(state)
        unit(state)
        self.assertEqual(plan(state).production_priority, (UnitType.ARCHER, UnitType.SPEARMAN, UnitType.WARRIOR))

    def test_nearest_city_and_id_tie_break(self):
        state = world()
        city(state)
        unit(state)
        unit(state)
        city(state, "B", 1, 4, "z-city")
        city(state, "B", 4, 1, "a-city")
        city(state, "B", 8, 5, "far-city")
        chosen = plan(state)
        self.assertEqual((chosen.posture, chosen.primary_enemy_id, chosen.target_city_id),
                         (Posture.ATTACK, "B", "a-city"))

    def test_badly_outnumbered_locally_defends(self):
        state = world()
        city(state)
        unit(state)
        for _ in range(3):
            unit(state, owner="B", x=3, y=1)
        self.assertEqual(plan(state).posture, Posture.DEFEND)
        self.assertEqual(plan(state).expansion_priority, ExpansionPriority.LOW)

    def test_distant_enemy_army_does_not_trigger_local_defense(self):
        state = world()
        city(state)
        city(state, "B", 7, 5)
        unit(state)
        unit(state)
        for _ in range(6):
            unit(state, owner="B", x=7, y=5)
        self.assertEqual(plan(state).posture, Posture.ATTACK)

    def test_plans_are_deterministic(self):
        state = world()
        unit(state, UnitType.SETTLER)
        first = plan(state)
        self.assertEqual(plan(deepcopy(state)), first)
        self.assertEqual(HeuristicStrategyProvider().create_plan(
            StrategicStateBuilder().build(state, "A"), first), first)


class PlanReuseTests(unittest.TestCase):
    def setUp(self):
        self.state = world()
        city(self.state, "B", 7, 5)
        self.provider = Mock(wraps=HeuristicStrategyProvider())
        self.controller = AiController(self.provider, replan_interval=5)

    def test_first_plan_and_reuse_before_interval(self):
        initial = self.controller.plan_for(self.state, "A")
        self.state.turn = 4
        self.assertIs(self.controller.plan_for(self.state, "A"), initial)
        self.assertEqual(self.provider.create_plan.call_count, 1)
        self.assertEqual(self.controller.plan_creation_turn, 0)

    def test_replan_at_interval_passes_previous_plan(self):
        initial = self.controller.plan_for(self.state, "A")
        self.state.turn = 5
        self.controller.plan_for(self.state, "A")
        self.assertEqual(self.provider.create_plan.call_count, 2)
        self.assertIs(self.provider.create_plan.call_args.args[1], initial)
        self.assertEqual(self.controller.plan_creation_turn, 5)

    def test_removed_target_invalidates_plan(self):
        self.controller.plan_for(self.state, "A")
        self.state.remove_city("city-B")
        self.assertIsNone(self.controller.plan_for(self.state, "A").target_city_id)
        self.assertEqual(self.provider.create_plan.call_count, 2)

    def test_eliminated_enemy_invalidates_plan(self):
        self.controller.plan_for(self.state, "A")
        self.state.eliminate_player("B")
        self.assertIsNone(self.controller.plan_for(self.state, "A").primary_enemy_id)

    def test_invalid_configuration_rejected(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                AiController(self.provider, value)

    def test_independent_plans_per_player(self):
        orchestrator = AiOrchestrator()
        orchestrator.run_active_ai_activation(self.state)
        orchestrator.run_active_ai_activation(self.state)
        self.assertEqual(set(orchestrator.controllers), {"A", "B"})
        self.assertIsNot(orchestrator.controllers["A"], orchestrator.controllers["B"])


class SettlerExecutorTests(unittest.TestCase):
    def test_founds_current_site_and_sets_new_city_production(self):
        state = world()
        settler = unit(state, UnitType.SETTLER)
        result = AiExecutor().execute(state, plan(state))
        self.assertNotIn(settler.id, state.units)
        founded = next(iter(state.cities.values()))
        self.assertEqual(founded.position, Position(1, 1))
        self.assertEqual(founded.production_target, UnitType.WARRIOR)
        self.assertEqual(len(commands(result, FoundCity)), 1)
        self.assertEqual(founded.production_stored, 1)

    def test_does_not_found_on_foreign_owned_tile(self):
        state = world()
        settler = unit(state, UnitType.SETTLER)
        state.tiles[settler.position].owner_id = "B"
        result = AiExecutor().execute(state, plan(state))
        self.assertTrue(commands(result, MoveUnit))
        self.assertFalse(any(c.position == Position(1, 1) for c in state.cities.values()))

    def test_spacing_requires_travel_then_founds_next_activation(self):
        state = world()
        city(state)
        unit(state, UnitType.SETTLER)
        result = AiExecutor().execute(state, plan(state))
        self.assertTrue(commands(result, MoveUnit))
        self.assertFalse(commands(result, FoundCity))
        apply_command(state, EndActivation("B"))
        result = AiExecutor().execute(state, plan(state))
        self.assertEqual(len(commands(result, FoundCity)), 1)
        self.assertEqual(len(state.cities), 2)
        state.validate()

    def test_equal_sites_choose_y_then_x(self):
        state = world()
        unit(state, UnitType.SETTLER, x=4, y=3)
        state.tiles[Position(4, 3)].owner_id = "B"
        path = AiExecutor._settlement_path(state, state.units["unit-1"])
        self.assertEqual(path[-1], Position(3, 2))

    def test_site_food_then_production_preference(self):
        state = world()
        settler = unit(state, UnitType.SETTLER, x=4, y=3)
        state.tiles[settler.position].owner_id = "B"
        # More food to the east overrules the stable western coordinate tie.
        for y in range(1, 6):
            state.tiles[Position(2, y)].terrain = Terrain.HILLS
        self.assertGreater(AiExecutor._settlement_path(state, settler)[-1].x, 3)
        # Plains and forest have equal food; forest offers more production.
        for tile in state.tiles.values():
            tile.terrain = Terrain.PLAINS
        for y in range(1, 6):
            state.tiles[Position(6, y)].terrain = Terrain.FOREST
        self.assertEqual(AiExecutor._settlement_path(state, settler)[-1].x, 5)

    def test_no_legal_site_ends_without_illegal_founding(self):
        state = world()
        unit(state, UnitType.SETTLER)
        for tile in state.tiles.values():
            tile.owner_id = "B"
        result = AiExecutor().execute(state, plan(state))
        self.assertFalse(commands(result, FoundCity))
        self.assertFalse(commands(result, MoveUnit))
        self.assertIsInstance(result.commands_executed[-1], EndActivation)

    def test_unreachable_legal_sites_do_not_loop(self):
        state = world()
        settler = unit(state, UnitType.SETTLER, x=0, y=0)
        state.tiles[settler.position].owner_id = "B"
        for position in (Position(0, 1), Position(1, 0), Position(1, 1)):
            state.tiles[position].terrain = Terrain.MOUNTAINS
        result = AiExecutor().execute(state, plan(state))
        self.assertFalse(commands(result, MoveUnit))
        self.assertFalse(commands(result, FoundCity))

    def test_exhausted_settler_waits(self):
        state = world()
        unit(state, UnitType.SETTLER).moves_remaining = 0
        result = AiExecutor().execute(state, plan(state))
        self.assertFalse(commands(result, FoundCity))

    def test_ai_city_ids_skip_collisions(self):
        state = world()
        settler = unit(state, UnitType.SETTLER)
        city(state, "B", 7, 5, f"ai-city-{settler.id}")
        result = AiExecutor().execute(state, plan(state))
        self.assertEqual(commands(result, FoundCity)[0].city_id, f"ai-city-{settler.id}-1")


class EconomicExecutorTests(unittest.TestCase):
    def test_selects_archery_then_unresearched_bronze(self):
        state = world()
        result = AiExecutor().execute(state, plan(state))
        self.assertEqual(commands(result, SetResearch)[0].technology, Technology.ARCHERY)
        apply_command(state, EndActivation("B"))
        state.players["A"].research_target = None
        state.players["A"].researched_technologies |= {Technology.ARCHERY}
        result = AiExecutor().execute(state, plan(state))
        self.assertEqual(commands(result, SetResearch)[0].technology, Technology.BRONZE_WORKING)

    def test_all_researched_no_command(self):
        state = world()
        state.players["A"].researched_technologies = frozenset(Technology)
        self.assertFalse(commands(AiExecutor().execute(state, plan(state)), SetResearch))

    def test_research_retained_unless_plan_prefers_another_available_target(self):
        state = world()
        state.players["A"].research_target = Technology.ARCHERY
        first = plan(state)
        self.assertFalse(commands(AiExecutor().execute(state, first), SetResearch))
        apply_command(state, EndActivation("B"))
        changed = replace(first, research_priority=(Technology.BRONZE_WORKING, Technology.ARCHERY))
        result = AiExecutor().execute(state, changed)
        self.assertEqual(commands(result, SetResearch)[0].technology, Technology.BRONZE_WORKING)

    def test_locked_unit_falls_back_to_legal_warrior(self):
        state = world()
        city(state)
        result = AiExecutor().execute(state, StrategicPlan(Posture.DEFEND))
        self.assertEqual(commands(result, SetCityProduction)[0].unit_type, UnitType.WARRIOR)

    def test_unlocked_archer_selected(self):
        state = world()
        city(state)
        state.players["A"].researched_technologies |= {Technology.ARCHERY}
        result = AiExecutor().execute(state, StrategicPlan(Posture.DEFEND))
        self.assertEqual(commands(result, SetCityProduction)[0].unit_type, UnitType.ARCHER)

    def test_missing_military_interrupts_settler_construction(self):
        state = world()
        city(state).production_target = UnitType.SETTLER
        result = AiExecutor().execute(state, StrategicPlan(Posture.DEFEND))
        self.assertEqual(commands(result, SetCityProduction)[0].unit_type, UnitType.WARRIOR)

    def test_existing_military_build_is_retained(self):
        state = world()
        city(state).production_target = UnitType.WARRIOR
        state.players["A"].researched_technologies |= {Technology.ARCHERY}
        result = AiExecutor().execute(state, StrategicPlan(Posture.DEFEND))
        self.assertFalse(commands(result, SetCityProduction))

    def test_expansion_builds_one_settler_with_adequate_military(self):
        state = world()
        city(state)
        unit(state)
        unit(state)
        result = AiExecutor().execute(state, plan(state))
        self.assertEqual(commands(result, SetCityProduction)[0].unit_type, UnitType.SETTLER)

    def test_existing_settler_prevents_another_even_with_stale_plan(self):
        state = world()
        city(state)
        unit(state)
        unit(state)
        chosen = plan(state)
        unit(state, UnitType.SETTLER).moves_remaining = 0
        result = AiExecutor().execute(state, chosen)
        self.assertNotEqual(commands(result, SetCityProduction)[0].unit_type, UnitType.SETTLER)

    def test_no_legal_sites_prevents_settler_production(self):
        state = world()
        city(state)
        unit(state)
        unit(state)
        for tile in state.tiles.values():
            tile.owner_id = "B"
        result = AiExecutor().execute(state, plan(state))
        self.assertNotEqual(commands(result, SetCityProduction)[0].unit_type, UnitType.SETTLER)

    def test_production_completes_through_end_activation(self):
        state = world()
        city(state)
        ai = AiOrchestrator()
        for _ in range(40):
            ai.run_active_ai_activation(state)
        self.assertGreaterEqual(state.next_unit_id, 2)
        self.assertTrue(any(u.owner_id == "A" for u in state.units.values()))


class CombatExecutorTests(unittest.TestCase):
    def test_legal_adjacent_attack(self):
        state = world()
        attacker = unit(state)
        enemy = unit(state, owner="B", x=2)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK))
        self.assertEqual(commands(result, AttackUnit), [AttackUnit("A", attacker.id, enemy.id)])
        self.assertEqual((attacker.hp, enemy.hp), (70, 70))

    def test_ranged_attack_at_two_without_retaliation(self):
        state = world()
        attacker = unit(state, UnitType.ARCHER)
        enemy = unit(state, owner="B", x=3)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK))
        self.assertTrue(commands(result, AttackUnit))
        self.assertEqual((attacker.hp, enemy.hp), (100, 70))
        self.assertEqual(attacker.position, Position(1, 1))

    def test_lethal_target_precedes_lower_hp_nonlethal_target(self):
        state = world()
        unit(state)
        unit(state, UnitType.SPEARMAN, "B", 2, 1, 26)
        lethal = unit(state, UnitType.SCOUT, "B", 2, 1, 40)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK))
        self.assertEqual(commands(result, AttackUnit)[0].target_unit_id, lethal.id)
        self.assertNotIn(lethal.id, state.units)

    def test_weakest_target_then_id(self):
        state = world()
        unit(state)
        unit(state, owner="B", x=2)
        chosen = unit(state, owner="B", x=2, hp=60)
        unit(state, owner="B", x=2, hp=60)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK))
        self.assertEqual(commands(result, AttackUnit)[0].target_unit_id, chosen.id)

    def test_moves_toward_city_without_entering_it(self):
        state = world()
        attacker = unit(state)
        target = city(state, "B", 7, 5)
        chosen = StrategicPlan(Posture.ATTACK, "B", target.id)
        moves = []
        for _ in range(9):
            result = AiExecutor().execute(state, chosen)
            moves += commands(result, MoveUnit)
            apply_command(state, EndActivation("B"))
        self.assertTrue(moves)
        self.assertTrue(all(c.destination != target.position for c in moves))
        self.assertEqual(max(abs(attacker.position.x - 7), abs(attacker.position.y - 5)), 1)
        self.assertFalse(commands(result, MoveUnit))

    def test_moves_toward_enemy_concentration_without_cities(self):
        state = world()
        unit(state)
        unit(state, owner="B", x=7, y=5)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK, "B"))
        self.assertTrue(commands(result, MoveUnit))

    def test_defend_holds_home_instead_of_marching_to_enemy_city(self):
        state = world()
        city(state)
        unit(state)
        city(state, "B", 7, 5)
        result = AiExecutor().execute(state, StrategicPlan(Posture.DEFEND, "B", "city-B"))
        self.assertFalse(commands(result, MoveUnit))

    def test_unreachable_enemy_city_ends_activation(self):
        state = world()
        unit(state, x=0, y=0)
        city(state, "B", 7, 5)
        for p in (Position(0, 1), Position(1, 0), Position(1, 1)):
            state.tiles[p].terrain = Terrain.MOUNTAINS
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK, "B", "city-B"))
        self.assertFalse(commands(result, MoveUnit))
        self.assertIsInstance(result.commands_executed[-1], EndActivation)

    def test_scout_multiple_attacks_and_attacker_death_terminate(self):
        state = world()
        attacker = unit(state, UnitType.SCOUT, hp=20)
        unit(state, owner="B", x=2)
        result = AiExecutor().execute(state, StrategicPlan(Posture.ATTACK))
        self.assertNotIn(attacker.id, state.units)
        self.assertEqual(len(commands(result, AttackUnit)), 1)
        self.assertEqual(len(commands(result, EndActivation)), 1)


class ExecutionBoundaryTests(unittest.TestCase):
    def test_ends_exactly_once_and_refreshes_next_player(self):
        state = world()
        enemy = unit(state, owner="B", x=7, y=5)
        enemy.moves_remaining = 0
        result = AiExecutor().execute(state, plan(state))
        self.assertEqual(commands(result, EndActivation), [EndActivation("A")])
        self.assertEqual((state.active_player_id, state.turn, enemy.moves_remaining), ("B", 0, 1))

    def test_action_limit_fails_loudly(self):
        state = world()
        unit(state, UnitType.SETTLER)
        with self.assertRaisesRegex(AiActionLimitError, "exceeded 1 actions"):
            AiExecutor(max_actions=1).execute(state, plan(state))

    def test_nonprogressing_command_cannot_loop_forever(self):
        state = world()
        unit(state)
        unit(state, owner="B", x=2)
        with patch("aig.ai.executor.apply_command"), self.assertRaises(AiActionLimitError):
            AiExecutor(max_actions=8).execute(state, StrategicPlan(Posture.ATTACK))

    def test_mutation_only_inside_command_boundary_and_replay_matches(self):
        state = world()
        unit(state, UnitType.SETTLER)
        unit(state)
        unit(state, owner="B", x=2)
        before = to_snapshot(state)
        expected = before
        def checked_apply(current, command):
            nonlocal expected
            self.assertEqual(to_snapshot(current), expected)
            apply_command(current, command)
            expected = to_snapshot(current)
        with patch("aig.ai.executor.apply_command", side_effect=checked_apply) as boundary:
            result = AiExecutor().execute(state, plan(state))
        self.assertEqual(to_snapshot(state), expected)
        self.assertEqual(boundary.call_count, len(result.commands_executed))
        restored = from_snapshot(before)
        for command in result.commands_executed:
            apply_command(restored, command)
        self.assertEqual(to_snapshot(restored), to_snapshot(state))

    def test_same_state_and_plan_same_trace_despite_dictionary_order(self):
        first = world()
        unit(first, UnitType.SETTLER)
        unit(first)
        unit(first, owner="B", x=2)
        unit(first, owner="B", x=2)
        second = deepcopy(first)
        for name in ("units", "cities", "tiles", "players"):
            setattr(second, name, dict(reversed(list(getattr(second, name).items()))))
        chosen = plan(first)
        self.assertEqual(AiExecutor().execute(first, chosen), AiExecutor().execute(second, chosen))
        self.assertEqual(to_snapshot(first), to_snapshot(second))

    def test_result_json_has_plan_and_commands_without_persistent_trace(self):
        state = world()
        unit(state, UnitType.SETTLER)
        result = AiExecutor().execute(state, plan(state))
        data = json.loads(json.dumps(result.to_dict()))
        self.assertEqual(data["commands_executed"][-1]["type"], "EndActivation")
        self.assertEqual(data["plan"]["posture"], "expand")
        self.assertNotIn("plan", to_snapshot(state))
        self.assertEqual(to_snapshot(state)["schema_version"], 8)

    def test_human_and_pregame_rejected_by_executor(self):
        state = world()
        state.players["A"].controller = ControllerType.HUMAN
        with self.assertRaisesRegex(ValueError, "active AI"):
            AiExecutor().execute(state, plan(state))
        state.active_player_id = None
        with self.assertRaises(ValueError):
            AiExecutor().execute(state, plan(state))

    def test_injected_provider_controls_executor_without_provider_coupling(self):
        state = world()
        unit(state)
        city(state)
        city(state, "B", 7, 5)
        provider = Mock()
        provider.create_plan.return_value = StrategicPlan(Posture.ATTACK, "B", "city-B")
        result = AiOrchestrator(provider).run_active_ai_activation(state)
        self.assertTrue(commands(result, MoveUnit))
        self.assertEqual(result.plan, provider.create_plan.return_value)
        self.assertIs(type(provider.create_plan.call_args.args[0]), dict)

    def test_shared_queries_are_read_only_and_match_execution(self):
        state = world()
        attacker = unit(state)
        target = unit(state, owner="B", x=2)
        before = to_snapshot(state)
        preview = preview_attack(state, attacker.id, target.id)
        self.assertTrue(can_found_city_at(state, "A", Position(1, 1)))
        self.assertEqual(to_snapshot(state), before)
        apply_command(state, AttackUnit("A", attacker.id, target.id))
        self.assertEqual(target.hp, 100 - preview.target_damage)


class OrchestrationTests(unittest.TestCase):
    def test_human_not_auto_played(self):
        state = create_game(human_vs_ai_demo_setup())
        start_game(state)
        before = to_snapshot(state)
        ai = AiOrchestrator()
        self.assertIsNone(ai.run_active_ai_activation(state))
        self.assertEqual(ai.advance_until_human(state), ())
        self.assertEqual(to_snapshot(state), before)

    def test_ai_runs_and_stops_on_human(self):
        state = create_game(human_vs_ai_demo_setup())
        start_game(state)
        apply_command(state, EndActivation("A"))
        results = AiOrchestrator().advance_until_human(state)
        self.assertEqual([r.player_id for r in results], ["B"])
        self.assertEqual((state.active_player_id, state.turn), ("A", 1))

    def test_consecutive_ai_players_stop_at_next_human(self):
        state = world()
        state.players["C"] = PlayerState("C", ControllerType.HUMAN)
        state.turn_order.append("C")
        results = AiOrchestrator().advance_until_human(state)
        self.assertEqual([r.player_id for r in results], ["A", "B"])
        self.assertEqual((state.active_player_id, state.turn), ("C", 0))

    def test_terminal_stops_without_command(self):
        state = world()
        state.eliminate_player("B")
        before = to_snapshot(state)
        ai = AiOrchestrator()
        self.assertIsNone(ai.run_active_ai_activation(state))
        self.assertEqual(ai.advance_until_human(state), ())
        self.assertEqual(to_snapshot(state), before)

    def test_all_ai_advance_until_human_rejected_before_mutation(self):
        state = world()
        before = to_snapshot(state)
        with self.assertRaisesRegex(ValueError, "live human"):
            AiOrchestrator().advance_until_human(state)
        self.assertEqual(to_snapshot(state), before)

    def test_scenarios_deterministic_and_hotseat_unchanged(self):
        hotseat = demo_game_setup()
        mixed = human_vs_ai_demo_setup()
        self.assertTrue(all(p.controller is ControllerType.HUMAN for p in hotseat.players))
        self.assertEqual(mixed, human_vs_ai_demo_setup())
        self.assertEqual(replace(mixed, players=hotseat.players), hotseat)
        state = create_game(mixed)
        start_game(state)
        self.assertEqual((state.active_player_id, state.active_controller), ("A", ControllerType.HUMAN))

    def test_100_turn_runs_match_and_exercise_all_systems_without_network(self):
        forbidden = AssertionError("AI must not use a network")
        with patch("socket.create_connection", side_effect=forbidden), \
             patch("urllib.request.urlopen", side_effect=forbidden):
            first, second = simulate(100), simulate(100)
        self.assertEqual(first, second)
        self.assertEqual((first["turn"], first["activations"]), (100, 200))
        for kind in ("MoveUnit", "AttackUnit", "FoundCity", "SetResearch", "SetCityProduction"):
            self.assertGreater(first["commands"][kind], 0)
        self.assertGreater(first["cities"], 2)
        self.assertGreater(first["units_created"], 4)
        self.assertTrue(all(techs == ["agriculture", "archery", "bronze_working"]
                            for techs in first["technologies"].values()))


if __name__ == "__main__":
    unittest.main()
