"""Arena Phase 2 rule, persistence and complete-match regressions, all offline."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json
import unittest

from aig.state import Position
from aig.arena import (ArenaAttack, ArenaEndTurn, ArenaHeal, ArenaMove, ArenaSimulation,
                       apply_command, create_scenario, from_snapshot, replay, state_hash, to_snapshot)
from aig.arena.commands import attack_damage, find_path
from aig.arena.public_state import public_state
from aig.arena.replay import metrics
from aig.arena.snapshots import command_from_dict, command_hash, command_to_dict
from aig.arena.state import (ArenaCore, ArenaPlayer, ArenaState, ArenaUnit, Board, Bonus,
                             STATS, Terrain, Tile, UnitType, UnitStatus)


def duel(kind=UnitType.KNIGHT, start=Position(2, 2), target=Position(3, 2), bonuses=None):
    tiles = tuple(Tile(bonus=(bonuses or {}).get(Position(x, y))) for y in range(5) for x in range(9))
    return ArenaState(Board(tiles), (ArenaPlayer("blue", "Blue Team"), ArenaPlayer("red", "Red Team")),
                      {"actor": ArenaUnit("actor", "blue", kind, start, STATS[kind].hp),
                       "target": ArenaUnit("target", "red", UnitType.KNIGHT, target, 18)},
                      {"blue-core": ArenaCore("blue-core", "blue", Position(0, 0)),
                       "red-core": ArenaCore("red-core", "red", Position(8, 4))}, "blue")


def core_win_commands():
    return [ArenaMove("blue", "blue-ranger", Position(4, 0)),
            ArenaMove("blue", "blue-ranger", Position(5, 2)),
            *[ArenaAttack("blue", "blue-ranger", "red-core") for _ in range(3)],
            ArenaEndTurn("blue"), ArenaEndTurn("red"),
            ArenaAttack("blue", "blue-ranger", "red-core")]


class ArenaSetupTests(unittest.TestCase):
    def test_scenario_roster_dimensions_and_unique_occupancy(self):
        s = create_scenario()
        self.assertEqual((s.board.width, s.board.height, len(s.board.tiles)), (9, 5, 45))
        self.assertEqual(len(s.players), 2)
        self.assertEqual(len(s.cores), 2)
        self.assertEqual(len(s.units), 8)
        for p in s.players:
            self.assertEqual({u.unit_type for u in s.units.values() if u.owner_id == p.id}, set(UnitType))
        pieces = [*s.units.values(), *s.cores.values()]
        self.assertEqual(len({p.position for p in pieces}), 10)
        self.assertTrue(all(c.hp == 30 for c in s.cores.values()))

    def test_setup_and_board_are_left_right_mirrored(self):
        s = create_scenario()
        for y in range(5):
            for x in range(9):
                self.assertEqual(s.board.at(Position(x, y)), s.board.at(Position(8 - x, y)))
        for kind in UnitType:
            a, b = s.units[f"blue-{kind.value}"], s.units[f"red-{kind.value}"]
            self.assertEqual((8 - a.position.x, a.position.y), (b.position.x, b.position.y))

    def test_all_bonus_types_and_blockers_exist(self):
        board = create_scenario().board
        self.assertEqual({t.bonus for t in board.tiles if t.bonus}, set(Bonus))
        self.assertEqual(sum(t.terrain is Terrain.BLOCKED for t in board.tiles), 4)

    def test_deterministic_initial_hash_and_board_serialization(self):
        a, b = create_scenario(), create_scenario()
        self.assertEqual(to_snapshot(a), to_snapshot(b))
        self.assertEqual(state_hash(a), "fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d")
        self.assertEqual(to_snapshot(from_snapshot(json.loads(json.dumps(to_snapshot(a))))), to_snapshot(a))

    def test_stats_are_centralized_and_immutable(self):
        self.assertEqual([(s.hp, s.damage, s.attack_range, s.move_range) for s in STATS.values()],
                         [(18, 6, 1, 2), (10, 5, 3, 3), (9, 6, 2, 2), (11, 3, 2, 2)])
        with self.assertRaises(TypeError):
            STATS[UnitType.KNIGHT] = STATS[UnitType.RANGER]
        with self.assertRaises(FrozenInstanceError):
            STATS[UnitType.KNIGHT].hp = 1

    def test_unknown_scenario_rejected(self):
        with self.assertRaises(ValueError):
            create_scenario("scenario-v1")

    def test_invalid_board_shapes_tiles_and_types(self):
        for make in (lambda: Board(tuple(Tile() for _ in range(44))),
                     lambda: Board(tuple(Tile() for _ in range(45)), width=True),
                     lambda: Tile(Terrain.BLOCKED, Bonus.POWER), lambda: Tile("floor")):
            with self.subTest(make=make), self.assertRaises(ValueError):
                make()

    def test_state_rejects_inconsistent_dynamic_fields(self):
        changes = [dict(turn=-1), dict(turn=True), dict(action_points_remaining=-1),
                   dict(action_points_remaining=6), dict(action_points_remaining=True),
                   dict(active_player_id=None), dict(active_player_id="unknown"),
                   dict(winner_player_id="blue"), dict(players=()), dict(cores={}), dict(units={})]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(create_scenario(), **change)

    def test_entity_validation_and_identity(self):
        for change in (dict(hp=0), dict(hp=19), dict(hp=True), dict(owner_id="none"),
                       dict(unit_type="knight"), dict(position=Position(9, 2)),
                       dict(position=Position(3, 1)), dict(position=Position(0, 2)),
                       dict(position=Position(1, 0)), dict(id="red-core")):
            s = create_scenario()
            for key, value in change.items():
                setattr(s.units["blue-knight"], key, value)
            with self.subTest(change=change), self.assertRaises(ValueError):
                s.validate()

    def test_core_and_player_validation(self):
        for mutation in (lambda s: setattr(s.cores["blue-core"], "owner_id", "red"),
                         lambda s: setattr(s.cores["blue-core"], "hp", 31),
                         lambda s: setattr(s.cores["blue-core"], "hp", 0),
                         lambda s: setattr(s, "players", (s.players[0], s.players[0]))):
            s = create_scenario()
            mutation(s)
            with self.assertRaises(ValueError):
                s.validate()


class ArenaRuleTests(unittest.TestCase):
    def rejected(self, state, command):
        before = to_snapshot(state)
        with self.assertRaises(ValueError):
            apply_command(state, command)
        self.assertEqual(to_snapshot(state), before)

    def test_commands_are_frozen_and_validate_inputs(self):
        for command in (ArenaMove("blue", "actor", Position(1, 2)), ArenaAttack("blue", "actor", "target"),
                        ArenaHeal("blue", "actor", "actor"), ArenaEndTurn("blue")):
            with self.assertRaises(FrozenInstanceError):
                command.actor_id = "red"
        for make in (lambda: ArenaEndTurn(""), lambda: ArenaAttack("blue", "", "a"),
                     lambda: ArenaHeal("blue", "a", ""), lambda: ArenaMove("blue", "a", (1, 2))):
            with self.assertRaises(ValueError):
                make()

    def test_shared_ap_repeated_actions_zero_ap_and_manual_end(self):
        s = duel()
        self.assertEqual((s.turn, s.active_player_id, s.action_points_remaining), (0, "blue", 5))
        for index in range(5):
            apply_command(s, ArenaMove("blue", "actor", Position(1 if index % 2 == 0 else 2, 2)))
            self.assertEqual(s.action_points_remaining, 4 - index)
        self.assertEqual(s.active_player_id, "blue")
        self.rejected(s, ArenaMove("blue", "actor", Position(2, 2)))
        self.rejected(s, ArenaAttack("blue", "actor", "target"))
        apply_command(s, ArenaEndTurn("blue"))
        self.assertEqual((s.turn, s.active_player_id, s.action_points_remaining), (0, "red", 5))
        apply_command(s, ArenaEndTurn("red"))
        self.assertEqual((s.turn, s.active_player_id, s.action_points_remaining), (1, "blue", 5))

    def test_inactive_and_unknown_actor_cannot_act_or_end(self):
        s = duel()
        for actor in ("red", "missing"):
            for cmd in (ArenaEndTurn(actor), ArenaMove(actor, "actor", Position(1, 2)),
                        ArenaAttack(actor, "actor", "target"), ArenaHeal(actor, "actor", "actor")):
                self.rejected(s, cmd)

    def test_each_class_move_range_cost_is_one(self):
        for kind in UnitType:
            s = duel(kind, Position(0, 2), Position(8, 2))
            steps = STATS[kind].move_range
            self.rejected(s, ArenaMove("blue", "actor", Position(steps + 1, 2)))
            apply_command(s, ArenaMove("blue", "actor", Position(steps, 2)))
            self.assertEqual(s.action_points_remaining, 4)
            self.assertEqual(s.units["actor"].position, Position(steps, 2))

    def test_move_out_of_bounds_occupied_core_enemy_and_noop(self):
        s = duel()
        for destination in (Position(-1, 2), Position(9, 2), Position(2, 5), Position(3, 2),
                            Position(0, 0), Position(8, 4), Position(2, 2)):
            self.rejected(s, ArenaMove("blue", "actor", destination))
        self.rejected(s, ArenaMove("blue", "target", Position(4, 2)))
        self.rejected(s, ArenaMove("blue", "missing", Position(1, 2)))

    def test_blocked_tiles_and_occupied_units_block_transit(self):
        for barrier in ("terrain", "units"):
            s = duel(start=Position(2, 2), target=Position(7, 2))
            if barrier == "terrain":
                s.board = Board(tuple(Tile(Terrain.BLOCKED if x == 3 else Terrain.FLOOR)
                                      for y in range(5) for x in range(9)))
            else:
                for y in range(5):
                    uid = f"barrier-{y}"
                    s.units[uid] = ArenaUnit(uid, "blue" if y % 2 else "red", UnitType.MAGE, Position(3, y), 9)
            self.assertIsNone(find_path(s, "actor", Position(4, 2)))
            self.rejected(s, ArenaMove("blue", "actor", Position(4, 2)))
            self.rejected(s, ArenaMove("blue", "actor", Position(3, 2)))

    def test_path_tie_order_diagonals_and_corner_cutting(self):
        s = duel(start=Position(1, 2), target=Position(8, 2))
        expected = [Position(1, 2), Position(2, 1), Position(3, 2)]
        self.assertEqual(find_path(s, "actor", Position(3, 2)), expected)
        self.assertEqual(find_path(s, "actor", Position(3, 2)), expected)
        tiles = list(s.board.tiles)
        tiles[2 * 9 + 2] = tiles[1 * 9 + 1] = Tile(Terrain.BLOCKED)
        s.board = Board(tuple(tiles))
        self.rejected(s, ArenaMove("blue", "actor", Position(2, 1)))

    def test_each_class_attack_range_damage_ap_and_no_retaliation(self):
        for kind in UnitType:
            stats = STATS[kind]
            s = duel(kind, Position(1, 2), Position(1 + stats.attack_range, 2))
            hp = s.units["actor"].hp
            apply_command(s, ArenaAttack("blue", "actor", "target"))
            self.assertEqual(s.units["target"].hp, 18 - stats.damage)
            self.assertEqual(s.units["actor"].hp, hp)
            self.assertEqual(s.action_points_remaining, 4)
            s.units["target"].position = Position(2 + stats.attack_range, 2)
            self.rejected(s, ArenaAttack("blue", "actor", "target"))

    def test_chebyshev_attack_range(self):
        s = duel(UnitType.RANGER, Position(1, 1), Position(4, 4))
        apply_command(s, ArenaAttack("blue", "actor", "target"))
        self.assertEqual(s.units["target"].hp, 13)

    def test_ranged_attacks_reject_blocked_los(self):
        s = duel(UnitType.RANGER, Position(1, 2), Position(4, 2))
        tiles = list(s.board.tiles)
        tiles[2 * 9 + 2] = Tile(Terrain.BLOCKED)
        s.board = Board(tuple(tiles))
        self.rejected(s, ArenaAttack("blue", "actor", "target"))

    def test_attack_rejects_friendly_own_core_unknown_and_enemy_actor_unit(self):
        s = duel()
        for target in ("actor", "blue-core", "unknown"):
            self.rejected(s, ArenaAttack("blue", "actor", target))
        self.rejected(s, ArenaAttack("blue", "target", "actor"))

    def test_power_and_ward_additive_damage(self):
        for bonuses, damage in (({Position(2, 2): Bonus.POWER}, 8),
                                ({Position(3, 2): Bonus.WARD}, 4),
                                ({Position(2, 2): Bonus.POWER, Position(3, 2): Bonus.WARD}, 6)):
            s = duel(bonuses=bonuses)
            apply_command(s, ArenaAttack("blue", "actor", "target"))
            self.assertEqual(s.units["target"].hp, 18 - damage)

    def test_minimum_unit_damage_one(self):
        s = duel(UnitType.CLERIC, bonuses={Position(3, 2): Bonus.WARD})
        self.assertEqual(attack_damage(s, s.units["actor"], s.units["target"]), 1)
        apply_command(s, ArenaAttack("blue", "actor", "target"))
        self.assertEqual(s.units["target"].hp, 17)

    def test_siege_only_affects_core_power_affects_core_ward_does_not(self):
        for bonus, expected in ((Bonus.SIEGE, 10), (Bonus.POWER, 8), (Bonus.WARD, 6), (None, 6)):
            s = duel(start=Position(7, 3), target=Position(6, 3),
                     bonuses={Position(7, 3): bonus, Position(8, 4): Bonus.WARD})
            self.assertEqual(attack_damage(s, s.units["actor"], s.units["target"]), 8 if bonus is Bonus.POWER else 6)
            apply_command(s, ArenaAttack("blue", "actor", "red-core"))
            self.assertEqual(s.cores["red-core"].hp, 30 - expected)

    def test_lethal_damage_downs_and_preserves_occupancy(self):
        s = duel()
        s.units["target"].hp = 1
        s.units["survivor"] = ArenaUnit("survivor", "red", UnitType.MAGE, Position(7, 3), 9)
        apply_command(s, ArenaAttack("blue", "actor", "target"))
        self.assertEqual(s.units["target"].status, UnitStatus.DOWNED)
        self.assertEqual(s.units["target"].hp, 0)
        self.assertIsNone(s.winner_player_id)
        self.assertFalse(s.can_enter(Position(3, 2)))

    def test_heal_friendly_amount_clamping_and_ap(self):
        for hp, expected in ((1, 6), (16, 18)):
            s = duel(UnitType.CLERIC)
            s.units["friend"] = ArenaUnit("friend", "blue", UnitType.KNIGHT, Position(2, 4), hp)
            apply_command(s, ArenaHeal("blue", "actor", "friend"))
            self.assertEqual(s.units["friend"].hp, expected)
            self.assertEqual(s.action_points_remaining, 4)

    def test_cleric_self_heal(self):
        s = duel(UnitType.CLERIC)
        s.units["actor"].hp = 1
        apply_command(s, ArenaHeal("blue", "actor", "actor"))
        self.assertEqual(s.units["actor"].hp, 6)

    def test_heal_rejects_enemy_core_full_dead_out_of_range_and_non_cleric(self):
        s = duel(UnitType.CLERIC)
        for target in ("target", "blue-core", "red-core", "unknown", "actor"):
            self.rejected(s, ArenaHeal("blue", "actor", target))
        s.units["friend"] = ArenaUnit("friend", "blue", UnitType.KNIGHT, Position(6, 4), 1)
        self.rejected(s, ArenaHeal("blue", "actor", "friend"))
        for kind in (UnitType.KNIGHT, UnitType.RANGER, UnitType.MAGE):
            s = duel(kind)
            s.units["actor"].hp = 1
            self.rejected(s, ArenaHeal("blue", "actor", "actor"))

    def test_zero_ap_heal_rejected(self):
        s = duel(UnitType.CLERIC)
        s.units["actor"].hp = 1
        s.action_points_remaining = 0
        self.rejected(s, ArenaHeal("blue", "actor", "actor"))

    def test_elimination_victory_and_every_post_terminal_command_rejected(self):
        s = duel()
        s.units["target"].hp = 6
        apply_command(s, ArenaAttack("blue", "actor", "target"))
        self.assertEqual((s.winner_player_id, s.active_player_id, s.turn, s.action_points_remaining), ("blue", None, 0, 4))
        s.validate()
        for command in (ArenaEndTurn("blue"), ArenaMove("blue", "actor", Position(1, 2)),
                        ArenaAttack("blue", "actor", "red-core"), ArenaHeal("blue", "actor", "actor")):
            self.rejected(s, command)

    def test_complete_scenario_core_victory_replays_without_extra_turn(self):
        simulation = ArenaSimulation()
        for command in core_win_commands():
            simulation.execute(command)
        s = simulation.state
        self.assertEqual((s.winner_player_id, s.active_player_id, s.turn, s.action_points_remaining), ("blue", None, 1, 4))
        self.assertEqual(s.cores["red-core"].hp, 0)
        self.assertEqual(len(s.units), 8)
        self.assertEqual(to_snapshot(replay(simulation.trace()).state), to_snapshot(s))
        self.assertEqual(simulation.metrics()["players"]["blue"]["damage_dealt"], 30)

    def test_red_can_win_without_wrap(self):
        s = duel()
        s.units["actor"].hp = 1
        apply_command(s, ArenaEndTurn("blue"))
        apply_command(s, ArenaAttack("red", "target", "actor"))
        self.assertEqual((s.winner_player_id, s.turn, s.action_points_remaining), ("red", 0, 4))


class ArenaPersistenceTests(unittest.TestCase):
    def test_midturn_snapshot_preserves_hp_core_ap_and_has_no_effects(self):
        s = duel(UnitType.CLERIC, Position(7, 3), Position(6, 2))
        apply_command(s, ArenaAttack("blue", "actor", "red-core"))
        s.units["actor"].hp = 4
        before = deepcopy(s)
        data = to_snapshot(s)
        restored = from_snapshot(data)
        self.assertEqual(s, before)
        self.assertEqual(restored, s)
        self.assertEqual(restored.action_points_remaining, 4)
        restored.units["actor"].hp = 2
        self.assertEqual(s.units["actor"].hp, 4)
        self.assertEqual(data, to_snapshot(s))

    def test_terminal_snapshot_preserves_winner_and_core(self):
        sim = ArenaSimulation()
        for command in core_win_commands():
            sim.execute(command)
        self.assertEqual(from_snapshot(to_snapshot(sim.state)), sim.state)
        sim = ArenaSimulation(duel())
        for _ in range(3):
            sim.execute(ArenaAttack("blue", "actor", "target"))
        self.assertEqual(from_snapshot(to_snapshot(sim.state)), sim.state)

    def test_snapshot_strict_schema_versions_duplicate_ids_and_hp(self):
        mutations = [lambda d: d.update(schema_version=12), lambda d: d.update(environment="empire"),
                     lambda d: d.update(extra=True), lambda d: d["config"].update(scenario_version="scenario-v1"),
                     lambda d: d["units"].append(deepcopy(d["units"][0])),
                     lambda d: d["cores"].append(deepcopy(d["cores"][0])),
                     lambda d: d["units"][0].update(hp=0), lambda d: d["units"][0]["position"].update(x=True),
                     lambda d: d.update(action_points_remaining=1.5), lambda d: d["board"]["tiles"].pop(),
                     lambda d: d.update(players=[d["players"][0]]),
                     lambda d: d.update(winner_player_id="blue", active_player_id=None)]
        for mutate in mutations:
            data = to_snapshot(create_scenario())
            mutate(data)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                from_snapshot(data)

    def test_hash_independent_of_entity_dictionary_order(self):
        s = create_scenario()
        before = state_hash(s)
        s.units = dict(reversed(list(s.units.items())))
        s.cores = dict(reversed(list(s.cores.items())))
        self.assertEqual(state_hash(s), before)

    def test_command_roundtrips_and_hashes(self):
        commands = [ArenaMove("blue", "actor", Position(3, 4)), ArenaAttack("blue", "actor", "target"),
                    ArenaHeal("blue", "actor", "actor"), ArenaEndTurn("blue")]
        for command in commands:
            encoded = command_to_dict(command)
            decoded = command_from_dict(json.loads(json.dumps(encoded)))
            self.assertEqual(decoded, command)
            self.assertEqual(command_hash(decoded), command_hash(command))
        self.assertNotEqual(command_hash(commands[1]), command_hash(replace(commands[1], target_id="other")))
        self.assertEqual(command_hash(ArenaEndTurn("blue")),
                         "fdd1266518b21c3d3940e49b473d53b983462840e9b10d6825a925656052b886")

    def test_command_schema_rejects_foreign_extra_and_malformed_fields(self):
        for data in ({"type": "end_activation"}, {"schema_version": "arena-command-v1", "type": "move_unit"},
                     {**command_to_dict(ArenaEndTurn("blue")), "extra": 1},
                     {**command_to_dict(ArenaMove("blue", "actor", Position(3, 4))), "destination": {"x": True, "y": 1}}):
            with self.assertRaises(ValueError):
                command_from_dict(data)

    def test_trace_failed_command_does_not_append_or_mutate(self):
        simulation = ArenaSimulation()
        before = simulation.trace()
        with self.assertRaises(ValueError):
            simulation.execute(ArenaAttack("red", "red-knight", "blue-knight"))
        self.assertEqual(simulation.trace(), before)
        self.assertEqual(to_snapshot(simulation.state), before["initial_snapshot"])

    def test_replay_all_command_types_and_trace_derived_metrics(self):
        s = duel(UnitType.CLERIC)
        s.units["actor"].hp = 2
        simulation = ArenaSimulation(s)
        for command in (ArenaHeal("blue", "actor", "actor"), ArenaAttack("blue", "actor", "target"),
                        ArenaMove("blue", "actor", Position(1, 2)), ArenaEndTurn("blue"), ArenaEndTurn("red")):
            simulation.execute(command)
        trace = simulation.trace()
        self.assertEqual(replay(trace).state, simulation.state)
        self.assertEqual(replay(trace).metrics(), simulation.metrics())
        values = simulation.metrics()["players"]["blue"]
        self.assertEqual([values[k] for k in ("ap_used", "ap_unused", "damage_dealt", "healing_done", "attacks_made")], [3, 2, 3, 5, 1])
        self.assertEqual(simulation.metrics()["turns_elapsed"], 1)
        self.assertEqual(metrics(s)["players"]["blue"]["total_hp"], 2)

    def test_replay_detects_tampering_and_trace_is_detached(self):
        sim = ArenaSimulation()
        sim.execute(ArenaEndTurn("blue"))
        for key in ("before_hash", "after_hash", "command_hash", "ap_unused"):
            trace = sim.trace()
            trace["entries"][0][key] = "tampered"
            with self.assertRaises(ValueError):
                replay(trace)
        self.assertEqual(replay(sim.trace()).state, sim.state)

    def test_replay_rejects_boolean_counter_even_when_equal_to_integer(self):
        sim = ArenaSimulation()
        sim.execute(ArenaEndTurn("blue"))
        trace = sim.trace()
        trace["entries"][0]["ap_used"] = False
        with self.assertRaises(ValueError):
            replay(trace)

    def test_public_dto_full_information_detached_actions_authoritative(self):
        s = create_scenario()
        before = to_snapshot(s)
        dto = public_state(s)
        self.assertEqual(dto["environment"], "arena")
        self.assertEqual(len(dto["units"]), 8)
        self.assertEqual(len(dto["board"]["tiles"]), 45)
        for u in dto["units"]:
            for dest in u["actions"]["move"]:
                copy = from_snapshot(before)
                apply_command(copy, ArenaMove(s.active_player_id, u["id"], Position(**dest)))
            if u["owner_id"] == "red":
                self.assertFalse(any(u["actions"].values()))
        dto["units"][0]["hp"] = 1
        self.assertEqual(to_snapshot(s), before)

    def test_no_legal_actions_at_zero_ap_or_terminal(self):
        s = duel()
        s.action_points_remaining = 0
        self.assertTrue(all(not any(u["actions"].values()) for u in public_state(s)["units"]))
        s.action_points_remaining = 5
        s.units["target"].hp = 1
        apply_command(s, ArenaAttack("blue", "actor", "target"))
        self.assertTrue(all(not any(u["actions"].values()) for u in public_state(s)["units"]))

    def test_foreign_engine_commands_rejected_without_mutation(self):
        from aig.commands import EndActivation, apply_command as empire_apply
        from aig.scenarios import demo_game_setup
        from aig.setup import create_game, start_game
        from aig.snapshots import to_snapshot as empire_snapshot
        s = create_scenario()
        before = to_snapshot(s)
        with self.assertRaises(ValueError):
            apply_command(s, EndActivation("blue"))
        self.assertEqual(to_snapshot(s), before)
        empire = create_game(demo_game_setup())
        start_game(empire)
        before = empire_snapshot(empire)
        with self.assertRaises(ValueError):
            empire_apply(empire, ArenaEndTurn(empire.active_player_id))
        self.assertEqual(empire_snapshot(empire), before)
