"""Tiny research rules, command atomicity, economy timing and strict persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import unittest
from unittest.mock import patch

from aig.commands import (
    AttackUnit, EliminatePlayer, EndActivation, FoundCity, MoveUnit,
    SetCityProduction, SetResearch, apply_command,
)
from aig.research import (
    available_technologies, research_remaining, technology_cost,
    technology_prerequisites, unit_is_unlocked,
)
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    CityState, ControllerType, GameConfig, GameMap, GameState, PlayerState,
    Position, Technology, TileState, UnitType,
)


def research_state():
    state = GameState(
        GameConfig(42), players={p: PlayerState(p, ControllerType.HUMAN) for p in "ABC"},
        turn_order=list("ABC"), active_player_id="A", game_map=GameMap(10, 8),
        tiles={Position(x, y): TileState(Position(x, y))
               for y in range(8) for x in range(10)},
    )
    state.add_city(CityState("a", "A", Position(1, 1), name="Alpha"))
    return state


class ResearchRulesTests(unittest.TestCase):
    def test_exact_tree_costs_and_prerequisites(self):
        self.assertEqual(list(Technology), [Technology.AGRICULTURE, Technology.ARCHERY,
                                          Technology.BRONZE_WORKING])
        for tech, cost, prerequisites in (
            (Technology.AGRICULTURE, 0, frozenset()),
            (Technology.ARCHERY, 15, frozenset({Technology.AGRICULTURE})),
            (Technology.BRONZE_WORKING, 20, frozenset({Technology.AGRICULTURE})),
        ):
            with self.subTest(tech=tech):
                self.assertEqual(technology_cost(tech), cost)
                self.assertEqual(technology_prerequisites(tech), prerequisites)

    def test_player_defaults(self):
        player = PlayerState("A", ControllerType.HUMAN)
        self.assertEqual(player.researched_technologies, frozenset({Technology.AGRICULTURE}))
        self.assertEqual(player.science_stored, 0)
        self.assertIsNone(player.research_target)

    def test_invalid_science_construction_and_mutation(self):
        for value in (-1, True, 1.5, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    PlayerState("A", ControllerType.HUMAN, science_stored=value)
                state = research_state()
                state.players["A"].science_stored = value
                with self.assertRaises(ValueError):
                    state.validate()

    def test_invalid_collection_and_target_invariants(self):
        for values in ([Technology.AGRICULTURE] * 2, {Technology.AGRICULTURE},
                       frozenset({"agriculture"}), None):
            with self.subTest(values=values), self.assertRaises(ValueError):
                PlayerState("A", ControllerType.HUMAN, researched_technologies=values)
        for target in (Technology.AGRICULTURE, "archery", True):
            with self.subTest(target=target), self.assertRaises(ValueError):
                PlayerState("A", ControllerType.HUMAN, research_target=target)
        with self.assertRaises(ValueError):
            PlayerState("A", ControllerType.HUMAN, researched_technologies=frozenset(),
                        research_target=Technology.ARCHERY)

    def test_available_options_are_ordered_pure_and_prerequisite_sensitive(self):
        player = PlayerState("A", ControllerType.HUMAN)
        before = deepcopy(player)
        for _ in range(3):
            self.assertEqual(available_technologies(player),
                             (Technology.ARCHERY, Technology.BRONZE_WORKING))
        self.assertEqual(player, before)
        player.researched_technologies = frozenset()
        self.assertEqual(available_technologies(player), (Technology.AGRICULTURE,))
        player.researched_technologies = frozenset(Technology)
        self.assertEqual(available_technologies(player), ())

    def test_remaining_science_and_direct_queries_are_pure(self):
        player = PlayerState("A", ControllerType.HUMAN)
        self.assertIsNone(research_remaining(player))
        player.research_target = Technology.ARCHERY
        for stored, remaining in ((0, 15), (13, 2), (15, 0), (100, 0)):
            player.science_stored = stored
            before = deepcopy(player)
            self.assertEqual(research_remaining(player), remaining)
            self.assertEqual(player, before)

    def test_queries_reject_runtime_strings_and_invalid_inputs(self):
        player = PlayerState("A", ControllerType.HUMAN)
        for value in ("archery", None, 1, True, [], {}):
            for query in (technology_cost, technology_prerequisites):
                with self.subTest(query=query, value=value), self.assertRaises(ValueError):
                    query(value)
            with self.assertRaises(ValueError):
                unit_is_unlocked(player, value)
        for query in (available_technologies, research_remaining):
            with self.assertRaises(ValueError):
                query(None)

    def test_all_unit_unlock_rules(self):
        player = PlayerState("A", ControllerType.HUMAN, researched_technologies=frozenset())
        for unit_type in UnitType:
            self.assertEqual(unit_is_unlocked(player, unit_type),
                             unit_type in (UnitType.WARRIOR, UnitType.SCOUT))
        for tech, unit_type in ((Technology.AGRICULTURE, UnitType.SETTLER),
                               (Technology.ARCHERY, UnitType.ARCHER),
                               (Technology.BRONZE_WORKING, UnitType.SPEARMAN)):
            player.researched_technologies |= {tech}
            self.assertTrue(unit_is_unlocked(player, unit_type))


class ResearchCommandTests(unittest.TestCase):
    def assert_rejected(self, state, command):
        before = deepcopy(state)
        with self.assertRaises(ValueError):
            apply_command(state, command)
        self.assertEqual(state, before)

    def test_command_is_frozen_and_validates_fields(self):
        command = SetResearch("A", Technology.ARCHERY)
        with self.assertRaises(FrozenInstanceError):
            command.technology = None
        for actor, technology in (("", None), (True, None), ("A", "archery"), ("A", [])):
            with self.subTest(actor=actor, technology=technology), self.assertRaises(ValueError):
                SetResearch(actor, technology)

    def test_select_switch_clear_preserve_every_other_field_even_when_affordable(self):
        state = research_state()
        state.players["A"].science_stored = 100
        state.add_unit("A", UnitType.SCOUT, Position(1, 1)).moves_remaining = 1
        state.cities["a"].production_target = UnitType.WARRIOR
        for tech in (Technology.ARCHERY, Technology.BRONZE_WORKING, None, None, Technology.ARCHERY):
            expected = deepcopy(state)
            expected.players["A"].research_target = tech
            self.assertIsNone(apply_command(state, SetResearch("A", tech)))
            self.assertEqual(state, expected)

    def test_inactive_unknown_and_eliminated_actor_rejected_atomically(self):
        state = research_state()
        state.eliminate_player("C")
        for actor in ("B", "missing", "C"):
            self.assert_rejected(state, SetResearch(actor, Technology.ARCHERY))

    def test_known_technology_and_missing_prerequisites_rejected(self):
        state = research_state()
        self.assert_rejected(state, SetResearch("A", Technology.AGRICULTURE))
        state.players["A"].researched_technologies = frozenset()
        for tech in (Technology.ARCHERY, Technology.BRONZE_WORKING):
            self.assert_rejected(state, SetResearch("A", tech))

    def test_runtime_bad_target_and_invalid_state_rejected(self):
        state = research_state()
        for value in ("archery", [], True, 15):
            command = SetResearch("A", None)
            object.__setattr__(command, "technology", value)
            self.assert_rejected(state, command)
        state.players["A"].science_stored = -1
        self.assert_rejected(state, SetResearch("A", None))

    def test_pregame_and_terminal_rejected(self):
        state = research_state()
        state.active_player_id = None
        self.assert_rejected(state, SetResearch("A", Technology.ARCHERY))
        state.eliminate_player("B")
        state.eliminate_player("C")
        self.assert_rejected(state, SetResearch("A", None))

    def test_production_enforces_each_unlock_and_clear_is_allowed(self):
        state = research_state()
        for tech, unit_type in ((Technology.AGRICULTURE, UnitType.SETTLER),
                               (Technology.ARCHERY, UnitType.ARCHER),
                               (Technology.BRONZE_WORKING, UnitType.SPEARMAN)):
            state.players["A"].researched_technologies = frozenset()
            self.assert_rejected(state, SetCityProduction("A", "a", unit_type))
            state.players["A"].researched_technologies = frozenset({Technology.AGRICULTURE, tech})
            apply_command(state, SetCityProduction("A", "a", unit_type))
            self.assertIs(state.cities["a"].production_target, unit_type)
            apply_command(state, SetCityProduction("A", "a", None))
        state.players["A"].researched_technologies = frozenset()
        for unit_type in (UnitType.WARRIOR, UnitType.SCOUT):
            apply_command(state, SetCityProduction("A", "a", unit_type))


class ScienceEconomyTests(unittest.TestCase):
    def test_population_income_with_no_target(self):
        for population in (1, 3):
            state = research_state()
            state.cities["a"].population = population
            apply_command(state, EndActivation("A"))
            self.assertEqual(state.players["A"].science_stored, population)
            self.assertIsNone(state.players["A"].research_target)

    def test_multiple_cities_only_outgoing_owner_and_removed_city_excluded(self):
        state = research_state()
        state.cities["a"].population = 3
        state.add_city(CityState("a2", "A", Position(4, 1), name="Second", population=2))
        state.add_city(CityState("b", "B", Position(7, 1), name="Beta", population=4))
        state.add_city(CityState("removed", "A", Position(1, 4), name="Removed", population=9))
        state.remove_city("removed")
        apply_command(state, EndActivation("A"))
        self.assertEqual([p.science_stored for p in state.players.values()], [5, 0, 0])

    def test_no_cities_still_completes_affordable_research(self):
        state = research_state()
        state.remove_city("a")
        player = state.players["A"]
        player.science_stored = 15
        player.research_target = Technology.ARCHERY
        apply_command(state, EndActivation("A"))
        self.assertEqual(player.science_stored, 0)
        self.assertIn(Technology.ARCHERY, player.researched_technologies)

    def test_growth_science_uses_starting_population_then_next_activation(self):
        state = research_state()
        city = state.cities["a"]
        city.population, city.food_stored = 2, 18
        apply_command(state, EndActivation("A"))
        self.assertEqual((city.population, state.players["A"].science_stored), (3, 2))
        for actor in "BCA":
            apply_command(state, EndActivation(actor))
        self.assertEqual(state.players["A"].science_stored, 5)

    def test_thresholds_cost_overflow_and_at_most_one_completion(self):
        for tech in (Technology.ARCHERY, Technology.BRONZE_WORKING):
            cost = technology_cost(tech)
            for stored in (cost - 2, cost - 1, cost, 10**30):
                with self.subTest(tech=tech, stored=stored):
                    state = research_state()
                    player = state.players["A"]
                    player.science_stored, player.research_target = stored, tech
                    apply_command(state, EndActivation("A"))
                    completed = stored + 1 >= cost
                    self.assertEqual(player.science_stored, stored + 1 - (cost if completed else 0))
                    self.assertEqual(player.research_target, None if completed else tech)
                    self.assertEqual(player.researched_technologies,
                                     frozenset({Technology.AGRICULTURE, tech} if completed
                                               else {Technology.AGRICULTURE}))
                    state.validate()

    def test_completed_unlock_can_be_selected_on_next_activation(self):
        state = research_state()
        state.players["A"].science_stored = 14
        apply_command(state, SetResearch("A", Technology.ARCHERY))
        apply_command(state, EndActivation("A"))
        for actor in "BC":
            apply_command(state, EndActivation(actor))
        apply_command(state, SetCityProduction("A", "a", UnitType.ARCHER))

    def test_ordinary_commands_generate_no_science_or_research(self):
        state = research_state()
        player = state.players["A"]
        player.science_stored, player.research_target = 100, Technology.ARCHERY
        before = deepcopy(state.players)
        scout = state.add_unit("A", UnitType.SCOUT, Position(2, 2))
        enemy = state.add_unit("B", UnitType.WARRIOR, Position(4, 2))
        settler = state.add_unit("A", UnitType.SETTLER, Position(1, 4))
        for command in (MoveUnit("A", scout.id, Position(3, 2)),
                        AttackUnit("A", scout.id, enemy.id),
                        FoundCity("A", settler.id, "new", "New"),
                        SetCityProduction("A", "a", UnitType.WARRIOR)):
            apply_command(state, command)
            self.assertEqual(state.players, before)

    def test_invalid_end_activation_is_atomic(self):
        for actor in ("B", "missing", "C"):
            state = research_state()
            state.eliminate_player("C")
            state.players["A"].science_stored = 100
            state.players["A"].research_target = Technology.ARCHERY
            before = deepcopy(state)
            with self.assertRaises(ValueError):
                apply_command(state, EndActivation(actor))
            self.assertEqual(state, before)

    def test_failed_production_preparation_cannot_commit_science(self):
        state = research_state()
        state.players["A"].science_stored, state.players["A"].research_target = 14, Technology.ARCHERY
        state.cities["a"].production_stored = 100
        state.cities["a"].production_target = UnitType.WARRIOR
        before = deepcopy(state)
        with patch.object(GameState, "_prepare_unit", side_effect=ValueError("placement")):
            with self.assertRaises(ValueError):
                apply_command(state, EndActivation("A"))
        self.assertEqual(state, before)

    def test_active_elimination_skips_research_and_advances_once_including_wrap(self):
        for active, successor, turn in (("A", "B", 0), ("C", "A", 1)):
            state = research_state()
            state.active_player_id = active
            state.add_city(CityState("extra", active, Position(4, 1), name="Extra"))
            state.add_unit(active, UnitType.WARRIOR, Position(4, 1))
            for player in state.players.values():
                player.science_stored, player.research_target = 100, Technology.ARCHERY
            before = deepcopy(state.players)
            apply_command(state, EliminatePlayer(active, active))
            before[active].eliminated = True
            self.assertEqual(state.players, before)
            self.assertEqual((state.active_player_id, state.turn), (successor, turn))
            self.assertFalse(any(c.owner_id == active for c in state.cities.values()))
            self.assertFalse(any(u.owner_id == active for u in state.units.values()))

    def test_inactive_elimination_does_not_resolve_either_factions_research(self):
        state = research_state()
        for player in state.players.values():
            player.science_stored, player.research_target = 100, Technology.ARCHERY
        expected = deepcopy(state.players)
        expected["B"].eliminated = True
        apply_command(state, EliminatePlayer("A", "B"))
        self.assertEqual(state.players, expected)
        self.assertEqual((state.active_player_id, state.turn), ("A", 0))


class ResearchSnapshotTests(unittest.TestCase):
    def test_exact_round_trip_mid_research_and_affordable_without_resolution(self):
        for stored in (13, 100):
            state = research_state()
            state.players["A"].science_stored = stored
            state.players["A"].research_target = Technology.BRONZE_WORKING
            state.players["A"].researched_technologies |= {Technology.ARCHERY}
            unit = state.add_unit("A", UnitType.SCOUT, Position(1, 1))
            unit.moves_remaining, unit.hp = 0, 50
            state.cities["a"].production_stored = 100
            state.cities["a"].production_target = UnitType.ARCHER
            before = deepcopy(state)
            restored = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
            self.assertEqual(restored, before)
            self.assertEqual(state, before)
            restored.players["A"].researched_technologies |= {Technology.BRONZE_WORKING}
            self.assertNotEqual(restored.players["A"], state.players["A"])

    def test_canonical_technology_serialization_and_no_derived_fields(self):
        state = research_state()
        state.players["A"].researched_technologies = frozenset(reversed(list(Technology)))
        snapshot = to_snapshot(state)
        self.assertEqual(snapshot["schema_version"], 8)
        self.assertEqual(snapshot["players"][0], {
            "id": "A", "controller": "human", "eliminated": False, "gold": 0,
            "science_stored": 0, "research_target": None,
            "researched_technologies": ["agriculture", "archery", "bronze_working"],
        })

    def test_malformed_research_fields_rejected_without_mutating_input(self):
        cases = [("science_stored", value) for value in (-1, True, 1.5, "1", None)]
        cases += [("research_target", value) for value in ("unknown", True, [], "agriculture")]
        cases += [("researched_technologies", value) for value in
                  (None, "agriculture", {}, [True], ["unknown"], ["agriculture"] * 2)]
        for field, value in cases:
            snapshot = to_snapshot(research_state())
            snapshot["players"][0][field] = value
            before = deepcopy(snapshot)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                from_snapshot(snapshot)
            self.assertEqual(snapshot, before)

    def test_missing_fields_unknown_fields_and_unmet_prerequisite_rejected(self):
        for field in ("science_stored", "research_target", "researched_technologies"):
            snapshot = to_snapshot(research_state())
            del snapshot["players"][0][field]
            with self.assertRaises(ValueError):
                from_snapshot(snapshot)
        snapshot = to_snapshot(research_state())
        snapshot["players"][0]["science_income"] = 1
        with self.assertRaises(ValueError):
            from_snapshot(snapshot)
        snapshot = to_snapshot(research_state())
        snapshot["players"][0].update(researched_technologies=[], research_target="archery")
        with self.assertRaises(ValueError):
            from_snapshot(snapshot)

    def test_v7_is_rejected_without_supplying_research_defaults(self):
        snapshot = to_snapshot(research_state())
        snapshot["schema_version"] = 7
        for player in snapshot["players"]:
            for field in ("science_stored", "research_target", "researched_technologies"):
                del player[field]
        with self.assertRaisesRegex(ValueError, "unsupported schema_version"):
            from_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
