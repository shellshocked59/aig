"""V4 rule, lifecycle, fog, fairness, replay and preservation regressions; offline."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from aig.ai.benchmark import benchmark, canonical_hash, initial_state
from aig.ai.barbarian_metrics import BarbarianMetrics
from aig.ai.controller import AiController, AiOrchestrator
from aig.ai.executor import AiExecutor
from aig.ai.knowledge_planning import planning_view
from aig.ai.strategy import HeuristicStrategyProvider, StrategicStateBuilder, StrategicPlan, Posture
from aig.application import GameSession
from aig.barbarians import BarbarianController, spawn_replacements
from aig.cities import found_city
from aig.combat import preview_attack
from aig.commands import AttackUnit, EndActivation, MoveUnit, FoundCity, SetResearch, SetCityProduction, apply_command
from aig.economy import resolve_player_economy
from aig.knowledge import known_camps, update_knowledge, visible_enemy_units, visible_positions
from aig.public_state import public_state, observer_state
from aig.scenarios import scenario_setup, SCENARIO_V3_CAMPS
from aig.settings import Settings
from aig.setup import GameSetup, PlayerSetup, create_game, start_game
from aig.snapshots import to_snapshot, from_snapshot
from aig.state import (BARBARIAN_ID as B, BarbarianCamp as Camp, KnownCamp, FactionKind,
                       CityState, ControllerType as C, GameConfig, GameMap, Position as P,
                       ResourceType as R, Terrain as T, UnitType as U, PlayerState)


def world(camp_position=P(5,5)):
    setup = GameSetup(GameConfig(42), GameMap(14,12),
        tuple((P(x,y),T.GRASSLAND) for y in range(12) for x in range(14)),
        (PlayerSetup('A',C.AI,P(1,1)),PlayerSetup('Z',C.AI,P(12,10))), ('A','Z'),
        camps=(Camp('camp',camp_position),))
    state = create_game(setup)
    start_game(state)
    return state


def warrior(state):
    return next(u for u in state.units.values() if u.owner_id == B)


def place(state, owner, kind, position, hp=100):
    unit = state.add_unit(owner,kind,position)
    unit.hp = hp
    update_knowledge(state)
    return unit


class CampRulesTests(unittest.TestCase):
    def test_all_terrain_legality(self):
        setup = scenario_setup('v3')
        for terrain in T:
            changed = tuple((p,terrain if p==setup.camps[0].position else t) for p,t in setup.tiles)
            # Remove resource when testing otherwise independently illegal resource terrain.
            if terrain.land_passable:
                create_game(replace(setup,tiles=changed,resources=()))
            else:
                with self.assertRaises(ValueError): replace(setup,tiles=changed,resources=())

    def test_duplicate_id_position_and_start_rejected(self):
        setup=scenario_setup('v3')
        for camps in ((Camp('x',P(0,0)),Camp('x',P(1,0))),
                      (Camp('x',P(0,0)),Camp('y',P(0,0))),
                      (Camp('x',setup.players[0].starting_position),)):
            with self.assertRaises(ValueError): replace(setup,camps=camps)

    def test_city_collision_and_resource_coexistence(self):
        state=world(); position=state.camps['camp'].position
        state.tiles[position].resource=R.GEMS
        state.validate()
        del state.units[warrior(state).id]
        with self.assertRaises(ValueError): state.add_city(CityState('c','A',position,name='C'))

    def test_camp_and_knowledge_validation(self):
        for args in (('',P(0,0)),('x',(0,0))):
            with self.assertRaises(ValueError): Camp(*args)
        state=world(); state.camps['wrong']=state.camps['camp']
        with self.assertRaises(ValueError): state.validate()
        with self.assertRaises(ValueError): KnownCamp('x',P(0,0),True)

    def test_detached_copies(self):
        state=world(); clone=deepcopy(state); clone.camps.clear()
        clone.players['A'].knowledge.discovered_camps.clear()
        self.assertEqual(len(state.camps),1)
        self.assertEqual(len(create_game(scenario_setup('v3')).camps),3)

    def test_initial_defenders_normal_stats_and_association(self):
        state=initial_state('v3')
        self.assertEqual(len(state.camps),3)
        self.assertEqual(len(state.units),7)
        for unit in state.units.values():
            if state.is_barbarian(unit.owner_id):
                self.assertEqual((unit.unit_type,unit.hp,unit.moves_remaining),(U.WARRIOR,100,1))
                self.assertEqual(unit.position,state.camps[unit.home_camp_id].position)

    def test_scenario_preserves_v2_geometry_resources_starts(self):
        old,new=scenario_setup('v2'),scenario_setup('v3')
        self.assertEqual(replace(new,camps=()),old)
        self.assertEqual(new.camps,SCENARIO_V3_CAMPS)
        state=create_game(new); start_game(state)
        for p in ('A','B'):
            self.assertFalse(known_camps(state,p))
            start=next(s.starting_position for s in new.players if s.id==p)
            nearest=min(max(abs(start.x-c.position.x),abs(start.y-c.position.y)) for c in new.camps)
            self.assertIn(nearest,(3,4))
        self.assertTrue(all(dict(new.resources).get(c.position) for c in new.camps))


class CampFogTests(unittest.TestCase):
    def test_undiscovered_camps_and_units_absent_at_all_player_boundaries(self):
        state=world(); state.players['A'].controller=C.HUMAN
        view=StrategicStateBuilder().build(state,'A')
        self.assertEqual(view['known_barbarian_camps'],[])
        self.assertEqual(view['visible_barbarian_units'],[])
        self.assertEqual(public_state(state)['barbarianCamps'],[])
        self.assertFalse(any(u['barbarian'] for u in public_state(state)['units']))
        self.assertEqual(len(observer_state(state)['barbarianCamps']),1)
        self.assertEqual(planning_view(state,'A').camps,{})

    def test_discovered_camp_persists_units_do_not(self):
        state=world(); scout=place(state,'A',U.SCOUT,P(3,5))
        self.assertTrue(known_camps(state,'A')[0]['currently_visible'])
        self.assertEqual(len(StrategicStateBuilder().build(state,'A')['visible_barbarian_units']),1)
        scout.position=P(0,0); update_knowledge(state)
        row=known_camps(state,'A')[0]
        self.assertFalse(row['currently_visible']); self.assertIsNone(row['live_exists'])
        self.assertEqual(StrategicStateBuilder().build(state,'A')['visible_barbarian_units'],[])

    def test_hidden_clear_stays_stale_until_revisit_and_roundtrips(self):
        state=world(); scout=place(state,'A',U.SCOUT,P(3,5))
        scout.position=P(0,0); update_knowledge(state)
        del state.units[warrior(state).id]
        clearer=place(state,'Z',U.SCOUT,P(6,5)); state.active_player_id='Z'
        apply_command(state,MoveUnit('Z',clearer.id,P(5,5)))
        self.assertIn('camp',state.players['A'].knowledge.discovered_camps)
        self.assertIsNone(known_camps(state,'A')[0]['live_exists'])
        restored=from_snapshot(to_snapshot(state)); self.assertEqual(restored,state)
        scout.position=P(3,5); update_knowledge(state)
        self.assertFalse(known_camps(state,'A'))

    def test_hidden_changes_cannot_change_planner_executor_or_public(self):
        state=world(); changed=deepcopy(state)
        changed.camps['hidden']=Camp('hidden',P(10,1))
        place(changed,B,U.WARRIOR,P(10,1)).home_camp_id='hidden'
        state.players['A'].controller=changed.players['A'].controller=C.HUMAN
        builder=StrategicStateBuilder()
        self.assertEqual(builder.build(state,'A'),builder.build(changed,'A'))
        self.assertEqual(public_state(state),public_state(changed))
        self.assertEqual(planning_view(state,'A'),planning_view(changed,'A'))
        state.players['A'].controller=changed.players['A'].controller=C.AI
        plan=HeuristicStrategyProvider().create_plan(builder.build(state,'A'))
        self.assertEqual(AiExecutor().execute(state,plan).commands_executed,
                         AiExecutor().execute(changed,plan).commands_executed)

    def test_no_global_barbarian_strength_or_home_association(self):
        state=world(); place(state,'A',U.SCOUT,P(3,5))
        view=StrategicStateBuilder().build(state,'A')
        self.assertEqual([p['id'] for p in view['civilizations']],['A','Z'])
        self.assertEqual(view['enemy_units'],[])
        self.assertEqual(view['enemy_military_strength'],20)
        self.assertNotIn('home_camp',json.dumps(view))
        state.players['A'].controller=C.HUMAN
        dto=public_state(state)
        self.assertNotIn(B,[p['id'] for p in dto['players']])
        self.assertNotIn('homeCampId',json.dumps(dto))
        self.assertIn('homeCampId',json.dumps(observer_state(state)))

    def test_hidden_spawn_does_not_reveal(self):
        state=world(); state.turn=8; state._begin_activation(B)
        self.assertEqual(len([u for u in state.units.values() if u.owner_id==B]),2)
        self.assertFalse(StrategicStateBuilder().build(state,'A')['visible_barbarian_units'])

    def test_visible_spawn_appears_normally(self):
        state=world(); place(state,'A',U.SCOUT,P(3,5)); state.turn=8; state._begin_activation(B)
        self.assertEqual(len(StrategicStateBuilder().build(state,'A')['visible_barbarian_units']),2)


class BarbarianLifecycleTests(unittest.TestCase):
    def test_exact_phase_order_wrap_no_economy_or_provider(self):
        state=world(); provider=Mock(); ai=AiOrchestrator(provider)
        apply_command(state,EndActivation('A')); apply_command(state,EndActivation('Z'))
        self.assertEqual((state.active_player_id,state.turn),(B,0))
        before=deepcopy(state.players[B])
        ai.run_active_ai_activation(state)
        self.assertEqual((state.active_player_id,state.turn),('A',1))
        self.assertEqual(state.players[B],before)
        provider.create_plan.assert_not_called()

    def test_manual_economy_research_founding_and_production_forbidden(self):
        state=world(); state.active_player_id=B
        for command in (SetResearch(B,None),SetCityProduction(B,'missing',None),FoundCity(B,warrior(state).id,'c','C')):
            before=to_snapshot(state)
            with self.assertRaises(ValueError): apply_command(state,command)
            self.assertEqual(to_snapshot(state),before)
        with self.assertRaises(ValueError): resolve_player_economy(state,B)
        with self.assertRaises(ValueError): state.add_city(CityState('c',B,P(8,8),name='C'))
        with self.assertRaises(ValueError): state.add_unit(B,U.SETTLER,P(8,8))
        with self.assertRaises(ValueError): AiController(Mock()).plan_for(state,B)
        with self.assertRaises(ValueError): StrategicStateBuilder().build(state,B)

    def test_human_never_stuck_on_system_phase(self):
        session=GameSession(); session.demo(); session.start()
        session.execute(EndActivation); result=session.execute(EndActivation)
        self.assertEqual((result['game']['activePlayerId'],result['game']['turn']),('A',1))
        self.assertNotIn(B,result.get('aiProviders',{}))

    def test_ai_first_and_system_last_reaches_human(self):
        state=world(); state.players['Z'].controller=C.HUMAN
        ai=AiOrchestrator(); ai.advance_until_human(state)
        self.assertEqual(state.active_player_id,'Z')
        apply_command(state,EndActivation('Z')); ai.advance_until_human(state)
        self.assertEqual((state.active_player_id,state.turn),('Z',1))

    def test_elimination_counts_civilizations_only(self):
        for active in ('A','Z',B):
            state=world(); state.active_player_id=active
            state.eliminate_player('Z')
            self.assertIsNone(state.active_player_id); self.assertEqual(state.turn,0)
            state.validate()
            with self.assertRaises(ValueError): start_game(state)
            with self.assertRaisesRegex(ValueError, 'game has ended'):
                state.eliminate_player('A')
            state.validate()
            self.assertIsNone(state.active_player_id)

    def test_system_marker_and_final_position_enforced(self):
        state=world(); state.turn_order.reverse()
        with self.assertRaises(ValueError): state.validate()
        with self.assertRaises(ValueError): PlayerState(B,C.HUMAN,kind=FactionKind.BARBARIAN)

    def test_eliminating_last_civilization_in_three_civ_round_enters_system_once(self):
        state=world()
        state.players['third']=PlayerState('third',C.AI)
        state.turn_order.insert(-1,'third'); state.active_player_id='third'
        state.eliminate_player('third')
        self.assertEqual((state.active_player_id,state.turn),(B,0))
        BarbarianController().execute(state)
        self.assertEqual((state.active_player_id,state.turn),('A',1))


class BarbarianCombatTests(unittest.TestCase):
    def attack_choice(self, entries):
        state=world(); state.active_player_id=B
        targets=[place(state,'A',kind,p,hp) for kind,p,hp in entries]
        result=BarbarianController().execute(state)
        attacks=[c for c in result.commands_executed if isinstance(c,AttackUnit)]
        return state,targets,attacks

    def test_adjacent_normal_damage_and_retaliation(self):
        state,targets,attacks=self.attack_choice([(U.WARRIOR,P(4,5),100)])
        self.assertEqual(len(attacks),1)
        self.assertEqual((targets[0].hp,warrior(state).hp),(70,70))

    def test_lethal_before_settler_then_low_hp(self):
        _,targets,attacks=self.attack_choice([(U.WARRIOR,P(4,5),20),(U.SETTLER,P(4,6),100)])
        # Both are lethal; civilian wins the next priority.
        self.assertEqual(attacks[0].target_unit_id,targets[1].id)
        _,targets,attacks=self.attack_choice([(U.WARRIOR,P(4,5),100),(U.WARRIOR,P(4,6),20)])
        self.assertEqual(attacks[0].target_unit_id,targets[1].id)

    def test_lowest_hp_and_stable_id(self):
        _,targets,attacks=self.attack_choice([(U.WARRIOR,P(4,5),90),(U.WARRIOR,P(4,6),60)])
        self.assertEqual(attacks[0].target_unit_id,targets[1].id)
        _,targets,attacks=self.attack_choice([(U.WARRIOR,P(4,5),90),(U.WARRIOR,P(4,6),90)])
        self.assertEqual(attacks[0].target_unit_id,min(t.id for t in targets))

    def test_settlers_and_scouts_can_die(self):
        for kind,hp in ((U.SETTLER,100),(U.SCOUT,40)):
            state,targets,_=self.attack_choice([(kind,P(4,5),hp)])
            self.assertNotIn(targets[0].id,state.units)

    def test_visible_local_pursuit_and_repeatability(self):
        state=world(); place(state,'A',U.WARRIOR,P(3,5)); state.active_player_id=B
        other=deepcopy(state)
        result=BarbarianController().execute(state)
        self.assertEqual(result,BarbarianController().execute(other))
        self.assertTrue(any(isinstance(c,MoveUnit) for c in result.commands_executed))
        self.assertEqual(warrior(state).position,P(4,4))

    def test_hidden_enemy_does_not_change_guard(self):
        state=world(); other=deepcopy(state)
        place(other,'A',U.SCOUT,P(9,5))
        state.active_player_id=other.active_player_id=B
        self.assertEqual(BarbarianController().execute(state),BarbarianController().execute(other))
        self.assertEqual(warrior(state).position,P(5,5))

    def test_other_camp_sight_cannot_disclose_targets(self):
        state=world(); state.camps['remote']=Camp('remote',P(10,5))
        place(state,'A',U.WARRIOR,P(9,5)); state.active_player_id=B
        result=BarbarianController().execute(state)
        self.assertEqual(len(result.commands_executed),1)

    def test_home_bound_and_return(self):
        state=world(); unit=warrior(state); unit.position=P(9,5)
        place(state,'A',U.SCOUT,P(11,5)); state.active_player_id=B
        BarbarianController().execute(state)
        self.assertLess(unit.position.x,9)

    def test_orphan_survives_and_never_enters_city(self):
        state=world(); del state.camps['camp']
        state.add_city(CityState('city','A',P(4,5),name='City'))
        place(state,'A',U.WARRIOR,P(4,5),1); state.active_player_id=B
        BarbarianController().execute(state)
        self.assertEqual(warrior(state).position,P(5,5))
        self.assertIn('city',state.cities)


class ClearingTests(unittest.TestCase):
    def test_defender_blocks_failed_move_atomically(self):
        state=world(); unit=place(state,'A',U.WARRIOR,P(4,5)); before=to_snapshot(state)
        with self.assertRaises(ValueError): apply_command(state,MoveUnit('A',unit.id,P(5,5)))
        self.assertEqual(to_snapshot(state),before)

    def test_kill_leaves_camp_even_after_melee_advance(self):
        state=world(); warrior(state).hp=1
        unit=place(state,'A',U.WARRIOR,P(4,5))
        apply_command(state,AttackUnit('A',unit.id,warrior(state).id))
        self.assertIn('camp',state.camps); self.assertEqual(state.players['A'].gold,0)
        self.assertEqual(unit.position,P(5,5))

    def test_each_combat_type_clears_once_resource_retained(self):
        for kind in (U.WARRIOR,U.SCOUT,U.ARCHER,U.SPEARMAN):
            state=world(); del state.units[warrior(state).id]
            state.tiles[P(5,5)].resource=R.GEMS
            unit=place(state,'A',kind,P(4,5))
            apply_command(state,MoveUnit('A',unit.id,P(5,5)))
            self.assertFalse(state.camps); self.assertEqual(state.players['A'].gold,25)
            self.assertEqual(state.tiles[P(5,5)].resource,R.GEMS)
            unit.moves_remaining=1; apply_command(state,MoveUnit('A',unit.id,P(4,5)))
            unit.moves_remaining=1; apply_command(state,MoveUnit('A',unit.id,P(5,5)))
            self.assertEqual(state.players['A'].gold,25)

    def test_settler_cannot_clear_or_found_on_camp(self):
        state=world(); del state.units[warrior(state).id]
        unit=place(state,'A',U.SETTLER,P(4,5)); apply_command(state,MoveUnit('A',unit.id,P(5,5)))
        self.assertTrue(state.camps); self.assertEqual(state.players['A'].gold,0)
        with self.assertRaises(ValueError): found_city(state,unit.id,'city','City')

    def test_shared_executor_takes_visible_attack_and_local_camp(self):
        state=world(); unit=place(state,'A',U.WARRIOR,P(4,5)); warrior(state).hp=1
        commands=AiExecutor().execute(state,StrategicPlan(Posture.EXPAND)).commands_executed
        self.assertTrue(any(isinstance(c,AttackUnit) and c.attacker_unit_id==unit.id for c in commands))
        state=world(); del state.units[warrior(state).id]; unit=place(state,'A',U.WARRIOR,P(4,5))
        AiExecutor().execute(state,StrategicPlan(Posture.DEFEND))
        self.assertFalse(state.camps); self.assertEqual(state.players['A'].gold,25)


class SpawningSnapshotTests(unittest.TestCase):
    def test_schedule_cap_order_and_allocator(self):
        state=initial_state('v3')
        state.turn=7; state._begin_activation(B); self.assertEqual(len(state.units),7)
        state.turn=8; state._begin_activation(B)
        self.assertEqual([(u.id,u.home_camp_id) for u in state.units.values() if int(u.id.split('-')[1])>=8],
                         [('unit-8','camp-1'),('unit-9','camp-2'),('unit-10','camp-3')])
        state.turn=16; state._begin_activation(B); self.assertEqual(len(state.units),10)

    def test_one_per_cycle_after_all_defenders_die(self):
        state=world(); del state.units[warrior(state).id]; state.turn=8; state._begin_activation(B)
        self.assertEqual(sum(u.owner_id==B for u in state.units.values()),1)

    def test_spawn_allocator_skips_colliding_ids(self):
        state=world(); state.next_unit_id=1; state.turn=8; state._begin_activation(B)
        self.assertEqual(state.next_unit_id,7)
        self.assertEqual(state.units['unit-6'].home_camp_id,'camp')

    def test_blocked_camp_skipped_and_cleared_never_spawns(self):
        state=world(); del state.units[warrior(state).id]
        place(state,'A',U.SETTLER,P(5,5)); state.turn=8; state._begin_activation(B)
        self.assertFalse(any(u.owner_id==B for u in state.units.values()))
        state.camps.clear(); state.turn=16; state._begin_activation(B)
        self.assertFalse(any(u.owner_id==B for u in state.units.values()))

    def test_restore_canonical_no_phase_spawn_clear_reward_or_refresh(self):
        state=world(); place(state,'A',U.SCOUT,P(3,5)); state.turn=8; state._begin_activation(B)
        warrior(state).moves_remaining=0
        snapshot=to_snapshot(state)
        self.assertEqual(snapshot['schema_version'],12)
        with patch('aig.barbarians.spawn_replacements',side_effect=AssertionError('spawn on load')), \
                patch('aig.knowledge.update_knowledge',side_effect=AssertionError('reveal on load')):
            restored=from_snapshot(deepcopy(snapshot))
        self.assertEqual(to_snapshot(restored),snapshot)
        restored.camps.clear(); self.assertTrue(state.camps)

    def test_old_schema_and_duplicate_camp_rejected(self):
        snapshot=to_snapshot(world()); old=deepcopy(snapshot); old['schema_version']=10
        with self.assertRaisesRegex(ValueError,'unsupported schema_version'): from_snapshot(old)
        snapshot['camps'].append(snapshot['camps'][0])
        with self.assertRaisesRegex(ValueError,'duplicate camp'): from_snapshot(snapshot)


class ReplanningMetricsTests(unittest.TestCase):
    def test_bounded_discovery_contact_and_five_turn_reuse(self):
        state=world(); controller=AiController(HeuristicStrategyProvider()); controller.plan_for(state,'A')
        place(state,'A',U.SCOUT,P(3,5)); controller.plan_for(state,'A')
        self.assertEqual(controller.last_trace['replan_reason'],'first_barbarian_contact')
        warrior(state).position=P(6,5); update_knowledge(state); controller.plan_for(state,'A')
        self.assertIsNone(controller.last_trace)
        state.turn=4; controller.plan_for(state,'A'); self.assertIsNone(controller.last_trace)
        state.turn=5; controller.plan_for(state,'A'); self.assertEqual(controller.last_trace['replan_reason'],'expired')

    def test_empty_camp_first_discovery(self):
        state=world(); del state.units[warrior(state).id]
        controller=AiController(HeuristicStrategyProvider()); controller.plan_for(state,'A')
        place(state,'A',U.SCOUT,P(3,5)); controller.plan_for(state,'A')
        self.assertEqual(controller.last_trace['replan_reason'],'first_camp_discovered')

    def test_clear_scout_discovery_and_gold_metrics(self):
        state=world(); del state.units[warrior(state).id]
        scout=place(state,'A',U.SCOUT,P(1,5)); metrics=BarbarianMetrics(state)
        for destination in (P(2,5),P(4,5),P(5,5)):
            scout.moves_remaining=2; command=MoveUnit('A',scout.id,destination)
            metrics.observe('before',state,command,3); apply_command(state,command); metrics.observe('after',state,command,3)
        players,_=metrics.finish(state); counts=players['A']
        self.assertEqual((counts['camps_discovered'],counts['scout_camp_discoveries'],counts['camps_cleared'],counts['camp_clear_gold']),(1,1,1,25))
        self.assertEqual(counts['camp_clears'][0]['unit_type'],'scout')

    def test_combat_deaths_and_defend_classification(self):
        state=world(); settler=place(state,'A',U.SETTLER,P(4,5)); metrics=BarbarianMetrics(state)
        metrics.decision(state,'A',StrategicPlan(Posture.DEFEND),None)
        self.assertEqual(metrics.counts['A']['defend_with_visible_barbarian_threat'],1)
        state.active_player_id=B; command=AttackUnit(B,warrior(state).id,settler.id)
        metrics.observe('before',state,command,2); apply_command(state,command); metrics.observe('after',state,command,2)
        self.assertEqual(metrics.counts['A']['settlers_killed_by_barbarians'],1)
        self.assertEqual(metrics.counts['A']['damage_received_from_barbarians'],100)
        metrics.decision(state,'A',StrategicPlan(Posture.DEFEND),None)
        self.assertEqual(metrics.counts['A']['defend_without_visible_threat'],1)

    def test_civilization_and_simultaneous_threat_decisions(self):
        state=world(); place(state,'Z',U.WARRIOR,P(3,1)); metrics=BarbarianMetrics(state)
        metrics.decision(state,'A',StrategicPlan(Posture.DEFEND),None)
        self.assertEqual(metrics.counts['A']['defend_with_visible_civilization_threat'],1)
        place(state,'A',U.SCOUT,P(3,5))
        metrics.decision(state,'A',StrategicPlan(Posture.DEFEND),None)
        self.assertEqual(metrics.counts['A']['defend_with_visible_civilization_threat'],2)
        self.assertEqual(metrics.counts['A']['defend_with_visible_barbarian_threat'],1)
        self.assertEqual(metrics.counts['A']['defend_without_visible_threat'],0)

    def test_spawn_and_skip_events_are_measured_on_phase_entry(self):
        state=world(); metrics=BarbarianMetrics(state)
        for turn in (8,16):
            state.turn=turn; state.active_player_id='Z'; command=EndActivation('Z')
            metrics.observe('before',state,command,turn*3+1)
            apply_command(state,command)
            metrics.observe('after',state,command,turn*3+1)
        _,observer=metrics.finish(state)
        self.assertEqual(observer['total_barbarian_warriors_spawned'],1)
        self.assertEqual(observer['skipped_spawn_attempts'],0)
        self.assertEqual(observer['capped_spawn_cycles'],1)
        self.assertEqual(observer['spawns_per_camp'],{'camp':1})
        self.assertEqual(observer['maximum_concurrent_barbarian_units'],2)

    def test_blocked_spawn_attempt_count_is_separate_from_cap(self):
        state=world(); del state.units[warrior(state).id]
        place(state,'A',U.SETTLER,P(5,5)); state.turn=8; state.active_player_id='Z'
        metrics=BarbarianMetrics(state); command=EndActivation('Z')
        metrics.observe('before',state,command,25); apply_command(state,command); metrics.observe('after',state,command,25)
        _,observer=metrics.finish(state)
        self.assertEqual(observer['skipped_spawn_attempts'],1)
        self.assertEqual(observer['capped_spawn_cycles'],0)
        self.assertEqual(observer['total_barbarian_warriors_spawned'],0)

    def test_scout_spawn_discovery_attribution(self):
        state=world(P(5,1)); found_city(state,'unit-1','capital','Capital')
        state.cities['capital'].production_target=U.SCOUT
        state.cities['capital'].production_stored=20
        # Radius-three Scout sees the camp; radius-two city/Warrior do not.
        state.camps['camp']=Camp('camp',P(4,1)); warrior(state).position=P(4,1)
        metrics=BarbarianMetrics(state); command=EndActivation('A')
        metrics.observe('before',state,command,0); apply_command(state,command); metrics.observe('after',state,command,0)
        self.assertEqual(metrics.counts['A']['scout_camp_discoveries'],1)

    def test_100_turn_paired_runs_replay_without_external_calls(self):
        with TemporaryDirectory() as folder, patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            report=benchmark(output=Path(folder)/'run',turns=100,settings=Settings(),environment_version='v5',scenario_version='v3')
        a,b=report['runs']; self.assertEqual(a['hashes'],b['hashes'])
        self.assertLess(a['metrics']['global_turns_completed'],100)
        self.assertEqual(a['metrics']['victoryType'], 'conquest')
        self.assertFalse(a['metrics']['turnCapReached'])
        self.assertEqual(set(a['players']),{'A','B'})
        self.assertEqual(a['inference']['requests'],0)
        self.assertGreater(a['metrics']['camps_discovered'],0)
        self.assertGreater(a['metrics']['attacks_against_barbarians'],0)
        self.assertLessEqual(a['metrics']['barbarian_spawning']['maximum_concurrent_barbarian_units'],6)
        self.assertTrue(a['players']['A']['strategic_state_sizes'])

    def test_frozen_artifact_hashes(self):
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'tests/fixtures/environment-v4-preserved-artifacts.json').read_text())
        for name,digest in rows.items():
            path=root/name
            if name == 'backend/aig/ai/prompts.py':
                # This V4 manifest predates the additive prompt-v2 registry.
                # Freeze its historical payload, not the extensible source file.
                from aig.ai.prompts import STRATEGY_PROMPT_V1
                self.assertEqual(hashlib.sha256(STRATEGY_PROMPT_V1.encode()).hexdigest(),
                    '1af8d0e613b1661f59e84b6dce118d31afd45fce0bef5cae97ecd9b6994cc598')
                continue
            if path.exists():
                payload = path.read_bytes()
                if name == 'docs/baselines.md':
                    payload = payload.split(b'\n## Scenario V4 (Environment V5)', 1)[0]
                self.assertEqual(hashlib.sha256(payload).hexdigest(),digest,name)
