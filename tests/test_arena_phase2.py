"""Phase 2 tactical boundaries, atomicity, geometry and persistence."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import unittest

from aig.state import Position as P
from aig.arena import (ArenaAttack, ArenaEndTurn, ArenaHeal, ArenaMove, ArenaFinish,
                       ArenaRevive, ArenaShieldBash, ArenaSnipe, ArenaFireball,
                       ArenaSimulation, apply_command, create_scenario, from_snapshot,
                       to_snapshot, replay, state_hash)
from aig.arena.commands import (arena_action_cost, arena_fireball_affected_units,
                                find_path, COMMAND_TYPES)
from aig.arena.geometry import arena_line_of_sight, can_step
from aig.arena.queries import legal_actions, abilities
from aig.arena.state import ArenaUnit, UnitType as U, UnitStatus as S, Board, Tile, Terrain, Bonus
from aig.arena.snapshots import command_from_dict, command_to_dict, command_hash
from test_arena import duel


def add(state, uid, owner, kind, position, hp=None, downed=False):
    from aig.arena.state import STATS
    state.units[uid] = ArenaUnit(uid, owner, kind, position,
                                 0 if downed else STATS[kind].hp if hp is None else hp,
                                 S.DOWNED if downed else S.ACTIVE)
    return state.units[uid]


def board_tile(state, p, terrain=Terrain.FLOOR, bonus=None):
    tiles = list(state.board.tiles)
    tiles[p.y * 9 + p.x] = Tile(terrain, bonus)
    state.board = Board(tuple(tiles))


def tactical(kind=U.KNIGHT):
    state = duel(kind)
    add(state, "survivor", "red", U.CLERIC, P(7, 4))
    return state


class Phase2Tests(unittest.TestCase):
    def reject(self, state, command):
        before = deepcopy(state)
        with self.assertRaises(ValueError):
            apply_command(state, command)
        self.assertEqual(state, before)

    def test_every_new_command_is_frozen_strict_and_roundtrips(self):
        for cls in (ArenaFinish, ArenaRevive, ArenaShieldBash, ArenaSnipe, ArenaFireball):
            target = P(3, 2) if cls is ArenaFireball else "target"
            command = cls("blue", "actor", target)
            with self.subTest(cls=cls):
                with self.assertRaises(FrozenInstanceError):
                    command.unit_id = "changed"
                for args in (("", "actor", target), ("blue", "", target),
                             ("blue", "actor", (3, 2) if cls is ArenaFireball else "")):
                    with self.assertRaises(ValueError):
                        cls(*args)
                self.assertEqual(command_from_dict(command_to_dict(command)), command)
                self.assertEqual(command_hash(command_from_dict(command_to_dict(command))), command_hash(command))
                data = command_to_dict(command)
                data["extra"] = 1
                with self.assertRaises(ValueError):
                    command_from_dict(data)

    def test_downed_actor_cannot_perform_any_action_or_spend_ap(self):
        for kind in U:
            state = tactical(kind)
            add(state, "friend", "blue", U.CLERIC, P(1, 4))
            state.units["actor"].hp, state.units["actor"].status = 0, S.DOWNED
            commands = [ArenaMove("blue", "actor", P(1, 2)), ArenaFireball("blue", "actor", P(3, 2))]
            commands += [cls("blue", "actor", "target") for cls in
                         (ArenaAttack, ArenaHeal, ArenaFinish, ArenaRevive, ArenaShieldBash, ArenaSnipe)]
            for command in commands:
                with self.subTest(kind=kind, command=command):
                    self.reject(state, command)
            self.assertFalse(any(legal_actions(state, state.units["actor"]).values()))
            self.assertIsNone(find_path(state, "actor", P(1, 2)))

    def test_bodies_block_transit_and_do_not_disappear_on_turn_change(self):
        state = tactical()
        for y in range(5):
            add(state, f"body{y}", "red", U.MAGE, P(4, y), downed=True)
        self.assertIsNone(find_path(state, "actor", P(5, 2)))
        self.reject(state, ArenaMove("blue", "actor", P(4, 2)))
        apply_command(state, ArenaEndTurn("blue"))
        apply_command(state, ArenaEndTurn("red"))
        self.assertEqual(sum(u.status is S.DOWNED for u in state.units.values()), 5)

    def test_offensive_entity_actions_cannot_target_bodies(self):
        for cls, kind in ((ArenaAttack, U.RANGER), (ArenaShieldBash, U.KNIGHT), (ArenaSnipe, U.RANGER)):
            state = tactical(kind)
            state.units["target"].hp, state.units["target"].status = 0, S.DOWNED
            self.reject(state, cls("blue", "actor", "target"))

    def test_every_class_can_finish_adjacent_enemy_body(self):
        for kind in U:
            state = tactical(kind)
            body = state.units["target"]
            body.hp, body.status = 0, S.DOWNED
            sim = ArenaSimulation(state)
            entry = sim.execute(ArenaFinish("blue", "actor", "target"))
            self.assertNotIn("target", sim.state.units)
            self.assertTrue(sim.state.can_enter(body.position))
            self.assertEqual(sim.state.units["actor"].position, state.units["actor"].position)
            self.assertEqual((entry["ap_used"], entry["units_finished"], entry["damage_dealt"]), (1, 1, 0))
            self.assertIsNone(sim.state.winner_player_id)
            self.assertEqual(replay(sim.trace()).state, sim.state)

    def test_finish_rejects_active_friendly_distant_core_missing(self):
        for variant in ("active", "friendly", "distant", "core", "missing"):
            state = tactical()
            target = state.units["target"]
            target.hp, target.status = 0, S.DOWNED
            uid = "target"
            if variant == "active":
                target.hp, target.status = 1, S.ACTIVE
            if variant == "friendly":
                target.owner_id = "blue"
            if variant == "distant":
                target.position = P(4, 2)
            if variant in ("core", "missing"):
                uid = "red-core" if variant == "core" else "missing"
            self.reject(state, ArenaFinish("blue", "actor", uid))

    def test_revive_at_range_two_then_act_same_turn(self):
        state = tactical(U.CLERIC)
        add(state, "friend", "blue", U.RANGER, P(2, 4), downed=True)
        sim = ArenaSimulation(state)
        entry = sim.execute(ArenaRevive("blue", "actor", "friend"))
        self.assertEqual((sim.state.units["friend"].hp, sim.state.units["friend"].status), (5, S.ACTIVE))
        self.assertEqual(sim.state.units["friend"].position, P(2, 4))
        self.assertEqual((entry["ap_used"], entry["units_revived"], entry["healing_done"]), (2, 1, 5))
        sim.execute(ArenaAttack("blue", "friend", "target"))
        self.assertEqual(sim.state.action_points_remaining, 2)
        self.assertEqual(replay(sim.trace()).state, sim.state)

    def test_revive_and_heal_target_restrictions(self):
        state = tactical(U.CLERIC)
        add(state, "friend", "blue", U.MAGE, P(2, 4), downed=True)
        self.reject(state, ArenaHeal("blue", "actor", "friend"))
        for uid in ("target", "actor", "red-core", "blue-core", "missing"):
            self.reject(state, ArenaRevive("blue", "actor", uid))
        state.units["friend"].position = P(2, 0)
        apply_command(state, ArenaRevive("blue", "actor", "friend"))
        self.reject(state, ArenaRevive("blue", "actor", "friend"))

    def test_revive_out_of_range_and_enemy_body_rejected(self):
        state = tactical(U.CLERIC)
        add(state, "friend", "blue", U.MAGE, P(6, 4), downed=True)
        self.reject(state, ArenaRevive("blue", "actor", "friend"))
        state.units["target"].hp, state.units["target"].status = 0, S.DOWNED
        self.reject(state, ArenaRevive("blue", "actor", "target"))

    def test_specials_are_class_specific_and_never_target_cores(self):
        for cls, owner_kind in ((ArenaShieldBash, U.KNIGHT), (ArenaSnipe, U.RANGER),
                                (ArenaFireball, U.MAGE), (ArenaRevive, U.CLERIC)):
            for kind in U:
                if kind == owner_kind:
                    continue
                state = tactical(kind)
                target = P(3, 2) if cls is ArenaFireball else "target"
                self.reject(state, cls("blue", "actor", target))
            if cls is not ArenaFireball:
                state = tactical(owner_kind)
                self.reject(state, cls("blue", "actor", "red-core"))

    def test_bash_straight_and_diagonal_push(self):
        for position, destination in ((P(3, 2), P(4, 2)), (P(3, 3), P(4, 4))):
            state = tactical()
            state.units["target"].position = position
            sim = ArenaSimulation(state)
            entry = sim.execute(ArenaShieldBash("blue", "actor", "target"))
            self.assertEqual(sim.state.units["target"].position, destination)
            self.assertEqual(sim.state.units["actor"].position, P(2, 2))
            self.assertEqual((sim.state.units["target"].hp, entry["shield_bash_pushes"], entry["ap_used"]), (14, 1, 1))

    def test_bash_blocked_push_still_damages(self):
        for obstruction in ("blocked", "active", "downed", "core", "edge"):
            state = tactical()
            if obstruction == "blocked":
                board_tile(state, P(4, 2), Terrain.BLOCKED)
            elif obstruction in ("active", "downed"):
                add(state, "obstacle", "blue", U.MAGE, P(4, 2), downed=obstruction == "downed")
            elif obstruction == "core":
                state.cores["red-core"].position = P(4, 2)
            else:
                state.units["actor"].position, state.units["target"].position = P(7, 2), P(8, 2)
            original = state.units["target"].position
            apply_command(state, ArenaShieldBash("blue", "actor", "target"))
            self.assertEqual((state.units["target"].hp, state.units["target"].position), (14, original))

    def test_bash_lethal_does_not_push_and_nonadjacent_rejected(self):
        state = tactical()
        state.units["target"].hp = 4
        apply_command(state, ArenaShieldBash("blue", "actor", "target"))
        self.assertEqual((state.units["target"].status, state.units["target"].position), (S.DOWNED, P(3, 2)))
        state = tactical()
        state.units["target"].position = P(4, 2)
        self.reject(state, ArenaShieldBash("blue", "actor", "target"))

    def test_snipe_range_four_cost_damage_and_downing(self):
        for reach in (4, 5):
            state = tactical(U.RANGER)
            state.units["target"].position = P(2 + reach, 2)
            if reach == 5:
                self.reject(state, ArenaSnipe("blue", "actor", "target"))
            else:
                state.units["target"].hp = 8
                sim = ArenaSimulation(state)
                entry = sim.execute(ArenaSnipe("blue", "actor", "target"))
                self.assertEqual((entry["damage_dealt"], entry["units_downed"], entry["ap_used"]), (8, 1, 2))
                self.assertEqual(sim.state.units["target"].status, S.DOWNED)

    def test_bonus_matrix_for_all_offensive_actions(self):
        for cls, kind, base in ((ArenaAttack, U.KNIGHT, 6), (ArenaShieldBash, U.KNIGHT, 4),
                                (ArenaSnipe, U.RANGER, 8), (ArenaFireball, U.MAGE, 4)):
            for bonus in (None, Bonus.POWER, Bonus.SIEGE, Bonus.WARD):
                for ward in (False, True):
                    with self.subTest(cls=cls, bonus=bonus, ward=ward):
                        state = tactical(kind)
                        board_tile(state, P(2, 2), bonus=bonus)
                        board_tile(state, P(3, 2), bonus=Bonus.WARD if ward else None)
                        target = P(3, 2) if cls is ArenaFireball else "target"
                        apply_command(state, cls("blue", "actor", target))
                        expected = max(1, base + (2 if bonus is Bonus.POWER else 0) - (2 if ward else 0))
                        self.assertEqual(state.units["target"].hp, 18 - expected)

    def test_fireball_empty_or_body_impact_friendly_fire_and_radius(self):
        for occupant in ("empty", "body", "friendly", "enemy"):
            state = tactical(U.MAGE)
            impact = P(3, 3)
            if occupant != "empty":
                add(state, "impact", "red" if occupant == "enemy" else "blue", U.MAGE,
                    impact, downed=occupant == "body")
            add(state, "friend", "blue", U.KNIGHT, P(4, 4))
            add(state, "outside", "red", U.MAGE, P(5, 4))
            sim = ArenaSimulation(state)
            entry = sim.execute(ArenaFireball("blue", "actor", impact))
            self.assertEqual(sim.state.units["actor"].hp, 5)
            self.assertEqual(sim.state.units["friend"].hp, 14)
            self.assertEqual(sim.state.units["target"].hp, 14)
            self.assertEqual(sim.state.units["outside"].hp, 9)
            self.assertGreaterEqual(entry["friendly_fire_damage"], 8)
            self.assertEqual(entry["fireball_targets_hit"], 4 if occupant in ("friendly", "enemy") else 3)
            if occupant == "body":
                self.assertEqual(sim.state.units["impact"], state.units["impact"])
            self.assertEqual(replay(sim.trace()).state, sim.state)

    def test_fireball_core_immune_and_no_splash_los(self):
        state = tactical(U.MAGE)
        state.cores["red-core"].position = P(4, 3)
        state.units["target"].position = P(4, 2)
        board_tile(state, P(3, 2), Terrain.BLOCKED)
        self.assertFalse(arena_line_of_sight(state.board, P(2, 2), P(4, 2)))
        apply_command(state, ArenaFireball("blue", "actor", P(3, 2)))  # blocked endpoint is legal
        self.assertEqual(state.units["target"].hp, 14)
        self.assertEqual(state.cores["red-core"].hp, 30)

    def test_fireball_atomic_damage_even_when_caster_downed_first(self):
        state = tactical(U.MAGE)
        state.units["actor"].hp = 1
        state.units["target"].hp = 5
        board_tile(state, P(2, 2), bonus=Bonus.POWER)
        add(state, "friend", "blue", U.CLERIC, P(1, 4))
        a, b = ArenaSimulation(state), ArenaSimulation(state)
        b.state.units = dict(reversed(list(b.state.units.items())))
        cmd = ArenaFireball("blue", "actor", P(3, 2))
        a.execute(cmd)
        b.execute(cmd)
        self.assertEqual(a.trace(), b.trace())
        self.assertEqual((a.state.units["actor"].status, a.state.units["target"].status), (S.DOWNED, S.DOWNED))
        self.assertIsNone(a.state.winner_player_id)
        self.assertEqual(replay(a.trace()).state, a.state)

    def test_fireball_self_elimination_and_simultaneous_defeat(self):
        for both in (False, True):
            state = duel(U.MAGE)
            state.units["actor"].hp = 4
            if both:
                state.units["target"].hp = 4
            sim = ArenaSimulation(state)
            sim.execute(ArenaFireball("blue", "actor", P(3, 2)))
            self.assertEqual((sim.state.winner_player_id, sim.state.active_player_id), ("red", None))
            self.assertEqual(from_snapshot(to_snapshot(sim.state)), sim.state)
            self.assertEqual(replay(sim.trace()).state, sim.state)
            self.reject(sim.state, ArenaEndTurn("red"))

    def test_fireball_outside_board_or_range_rejects_without_mutation(self):
        for p in (P(-1, 2), P(9, 2), P(2, 5), P(5, 2)):
            self.reject(tactical(U.MAGE), ArenaFireball("blue", "actor", p))

    def test_one_active_unit_of_any_class_prevents_elimination(self):
        for kind in U:
            state = duel()
            state.units["target"].hp = 1
            add(state, "survivor", "red", kind, P(4, 2))
            for i, p in enumerate((P(4, 3), P(5, 3))):
                add(state, str(i), "red", U.MAGE, p, downed=True)
            apply_command(state, ArenaAttack("blue", "actor", "target"))
            self.assertIsNone(state.winner_player_id)
            state.units["actor"].position = P(3, 1)
            state.units["survivor"].hp = 1
            apply_command(state, ArenaAttack("blue", "actor", "survivor"))
            self.assertEqual(state.winner_player_id, "blue")
            self.assertEqual(sum(u.status is S.DOWNED for u in state.units.values()), 4)

    def test_every_action_rejects_after_terminal(self):
        state = duel()
        state.units["target"].hp = 1
        apply_command(state, ArenaAttack("blue", "actor", "target"))
        for cls in COMMAND_TYPES:
            cmd = (cls("blue") if cls is ArenaEndTurn else
                   cls("blue", "actor", P(1, 2) if cls in (ArenaMove, ArenaFireball) else "target"))
            self.reject(state, cmd)

    def test_costs_and_insufficient_ap_are_atomic_for_every_action(self):
        cases = [(ArenaMove, U.KNIGHT, P(1, 2), 1), (ArenaAttack, U.KNIGHT, "target", 1),
                 (ArenaHeal, U.CLERIC, "actor", 1), (ArenaFinish, U.KNIGHT, "target", 1),
                 (ArenaShieldBash, U.KNIGHT, "target", 1), (ArenaSnipe, U.RANGER, "target", 2),
                 (ArenaRevive, U.CLERIC, "friend", 2), (ArenaFireball, U.MAGE, P(3, 2), 2)]
        for cls, kind, target, cost in cases:
            state = tactical(kind)
            state.units["actor"].hp -= 1
            add(state, "friend", "blue", U.MAGE, P(1, 3), downed=True)
            if cls is ArenaFinish:
                state.units["target"].hp, state.units["target"].status = 0, S.DOWNED
            cmd = cls("blue", "actor", target)
            self.assertEqual(arena_action_cost(cmd), cost)
            for ap in range(cost):
                state.action_points_remaining = ap
                self.reject(state, cmd)
                self.assertFalse(legal_actions(state, state.units["actor"])[command_to_dict(cmd)["type"][6:]])
            state.action_points_remaining = cost
            apply_command(state, cmd)
            self.assertEqual(state.action_points_remaining, 0)
            apply_command(state, ArenaEndTurn("blue"))
            self.assertEqual(state.action_points_remaining, 5)
        self.assertEqual(arena_action_cost(ArenaEndTurn("blue")), 0)

    def test_status_snapshot_strictness_and_side_effect_free_loading(self):
        state = tactical()
        state.units["target"].hp, state.units["target"].status = 0, S.DOWNED
        state.action_points_remaining = 2
        state.cores["red-core"].hp = 7
        snapshot = to_snapshot(state)
        self.assertEqual(snapshot["schema_version"], "arena-snapshot-v2")
        self.assertEqual(from_snapshot(snapshot), state)
        self.assertEqual(to_snapshot(state), snapshot)
        for hp, status in ((0, "active"), (1, "downed"), (-1, "downed"), (False, "downed"), (0, "unknown")):
            data = deepcopy(snapshot)
            data["units"][0].update(hp=hp, status=status)
            with self.assertRaises(ValueError):
                from_snapshot(data)
        for key in ("status", "hp"):
            data = deepcopy(snapshot)
            del data["units"][0][key]
            with self.assertRaises(ValueError):
                from_snapshot(data)

    def test_v1_is_explicit_history_never_silently_loaded_as_v2(self):
        from aig.arena import v1
        snapshot = v1.to_snapshot(v1.create_scenario())
        self.assertEqual(v1.state_hash(v1.from_snapshot(snapshot)),
                         "879d9e26f1116cb9628d2889f09526c2ccf7f947bd5c0c2a1727df991cd7c800")
        with self.assertRaises(ValueError):
            from_snapshot(snapshot)
        with self.assertRaises(ValueError):
            v1.from_snapshot(to_snapshot(create_scenario()))
        with self.assertRaises(ValueError):
            replay(v1.ArenaSimulation().trace())

    def test_legal_queries_are_pure_and_agree_with_every_validator(self):
        from aig.arena.commands import COMMAND_KINDS
        for kind in U:
            state = tactical(kind)
            add(state, "friend", "blue", U.MAGE, P(1, 3), downed=True)
            add(state, "enemybody", "red", U.MAGE, P(3, 3), downed=True)
            before = to_snapshot(state)
            actions = legal_actions(state, state.units["actor"])
            for cls, name in COMMAND_KINDS.items():
                if cls is ArenaEndTurn:
                    continue
                candidates = ([P(x, y) for y in range(5) for x in range(9)] if cls in (ArenaMove, ArenaFireball)
                              else sorted([*state.units, *state.cores]))
                for target in candidates:
                    copy = from_snapshot(before)
                    try:
                        apply_command(copy, cls("blue", "actor", target))
                    except ValueError:
                        self.assertNotIn(target, actions[name])
                        self.assertEqual(to_snapshot(copy), before)
                    else:
                        self.assertIn(target, actions[name])
                        copy.validate()
            self.assertEqual(to_snapshot(state), before)
            self.assertEqual(set(abilities(state.units["actor"])),
                             {"move", "attack", "finish", *({U.KNIGHT: ["shield_bash"], U.RANGER: ["snipe"],
                                                             U.MAGE: ["fireball"], U.CLERIC: ["heal", "revive"]}[kind])})


class GeometryTests(unittest.TestCase):
    def test_los_straight_diagonal_nearby_obstacle_endpoints_and_bounds(self):
        state = duel()
        for end in (P(6, 2), P(6, 4), P(4, 4), P(2, 2), P(2, 4)):
            self.assertTrue(arena_line_of_sight(state.board, P(2, 2), end))
        board_tile(state, P(3, 0), Terrain.BLOCKED)
        self.assertTrue(arena_line_of_sight(state.board, P(2, 2), P(6, 2)))
        board_tile(state, P(4, 2), Terrain.BLOCKED)
        self.assertFalse(arena_line_of_sight(state.board, P(2, 2), P(6, 2)))
        self.assertTrue(arena_line_of_sight(state.board, P(2, 2), P(4, 2)))
        self.assertTrue(arena_line_of_sight(state.board, P(4, 2), P(6, 2)))
        self.assertFalse(arena_line_of_sight(state.board, P(-1, 2), P(4, 2)))

    def test_los_supercover_corner_and_symmetry_exhaustively(self):
        state = create_scenario()
        points = [P(x, y) for y in range(5) for x in range(9)]
        for a in points:
            for b in points:
                self.assertEqual(arena_line_of_sight(state.board, a, b), arena_line_of_sight(state.board, b, a))
        state = duel()
        board_tile(state, P(3, 2), Terrain.BLOCKED)
        self.assertFalse(arena_line_of_sight(state.board, P(2, 2), P(3, 3)))

    def test_units_cores_and_bonuses_never_block_los(self):
        state = tactical()
        state.cores["red-core"].position = P(4, 2)
        add(state, "body", "blue", U.MAGE, P(5, 2), downed=True)
        for bonus in Bonus:
            board_tile(state, P(6, 2), bonus=bonus)
            self.assertTrue(arena_line_of_sight(state.board, P(2, 2), P(7, 2)))

    def test_all_ranged_actions_use_same_los_including_heal_revive(self):
        for cls, kind in ((ArenaAttack, U.RANGER), (ArenaAttack, U.MAGE), (ArenaAttack, U.CLERIC),
                          (ArenaHeal, U.CLERIC), (ArenaRevive, U.CLERIC),
                          (ArenaSnipe, U.RANGER), (ArenaFireball, U.MAGE)):
            state = tactical(kind)
            state.units["target"].position = P(4, 2)
            if cls in (ArenaHeal, ArenaRevive):
                state.units["target"].owner_id = "blue"
                state.units["target"].hp = 1
            if cls is ArenaRevive:
                state.units["target"].hp, state.units["target"].status = 0, S.DOWNED
            board_tile(state, P(3, 2), Terrain.BLOCKED)
            cmd = cls("blue", "actor", P(4, 2) if cls is ArenaFireball else "target")
            before = deepcopy(state)
            with self.assertRaisesRegex(ValueError, "line of sight"):
                apply_command(state, cmd)
            self.assertEqual(state, before)
            board_tile(state, P(3, 2))
            apply_command(state, cmd)

    def test_knight_adjacency_ignores_los(self):
        state = tactical()
        state.units["target"].position = P(3, 3)
        board_tile(state, P(3, 2), Terrain.BLOCKED)
        self.assertFalse(arena_line_of_sight(state.board, P(2, 2), P(3, 3)))
        apply_command(state, ArenaAttack("blue", "actor", "target"))

    def test_diagonal_steps_require_each_orthogonal_terrain_open(self):
        for blocked in (None, P(2, 1), P(1, 2)):
            state = duel(start=P(1, 1), target=P(7, 2))
            if blocked:
                board_tile(state, blocked, Terrain.BLOCKED)
            self.assertEqual(can_step(state, P(1, 1), P(2, 2)), blocked is None)
            path = find_path(state, "actor", P(2, 2))
            self.assertEqual(len(path) - 1, 1 if blocked is None else 2)
            for a, b in zip(path, path[1:]):
                self.assertTrue(can_step(state, a, b))
            apply_command(state, ArenaMove("blue", "actor", P(2, 2)))  # legal two-step detour

    def test_adjacent_entities_do_not_prevent_diagonal_corner_passage(self):
        state = duel(start=P(1, 1), target=P(2, 1))
        add(state, "body", "blue", U.MAGE, P(1, 2), downed=True)
        self.assertTrue(can_step(state, P(1, 1), P(2, 2)))
        self.assertEqual(find_path(state, "actor", P(2, 2)), [P(1, 1), P(2, 2)])
