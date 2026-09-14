"""Read-only evidence audit; writes derived summaries only, never runs providers."""
import json
from pathlib import Path
from collections import Counter
from aig.arena.case_study_contract import read, digest, sha
from aig.arena.case_study_analysis import summarize
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import from_snapshot, to_snapshot, command_from_dict, state_hash
from aig.arena.ai.benchmark_candidate import candidate_observation
from aig.arena.ai.contracts import action_from_dict, action_command
from aig.arena.commands import arena_fireball_affected_units

ROOT = Path(__file__).parent
ARMS = ('strict', 'bounded', 'stepwise')
rows = [read(p) for p in sorted(ROOT.glob('matches/*/result.json')) if (p.parent/'seal.json').exists()]
report = dict(arms={}, end_turns=[], fireballs=[], matches=[], request_categories={})
report['ability_effects']=[]
for arm in ARMS:
    selected = [r for r in rows if r['arm'] == arm]
    report['arms'][arm] = summarize(selected)
    report['request_categories'][arm] = Counter()
for row in rows:
    directory = ROOT/'matches'/row['match_id']
    side = row['luna_side']
    paired = {k: v for k,v in row.items() if k != 'metrics'}
    paired.update(luna_metrics=row['metrics'][side], final_state_hash=state_hash(from_snapshot(read(directory/'final-state.json'))),
                  final_state_file_sha256=sha(directory/'final-state.json'), seal_sha256=sha(directory/'seal.json'),
                  evidence_elapsed_seconds=(directory/'seal.json').stat().st_mtime-(directory/'manifest.json').stat().st_mtime)
    report['matches'].append(paired)
    for path in sorted((directory/'turns').glob('*.json')):
        bundle = read(path); turn = bundle['turn']
        sim = ArenaSimulation(from_snapshot(bundle['trace']['initial_snapshot']))
        is_luna = turn['player_id'] == side
        if is_luna:
            ids=[]
            for wi,wave in enumerate(turn['waves']):
                attempts=wave['inference'].get('attempts',[])
                ids += [a['ledger_id'] for a in attempts]
                category = 'stepwise_decisions' if row['arm']=='stepwise' else 'bounded_replacement_planning' if wi else 'initial_planning'
                repair = 'bounded_replacement_repair' if row['arm']=='bounded' and wi else 'repair'
                if attempts: report['request_categories'][row['arm']][category] += 1
                report['request_categories'][row['arm']][repair] += max(0,len(attempts)-1)
            assert ids == bundle['request_ids']
            if turn['explicit_end_turn']:
                stop_index=next(i for i,w in enumerate(turn['waves']) if w['explicit_end_turn'])
                assert stop_index == len(turn['waves'])-1, 'wave after EndTurn'
                assert turn['waves'][stop_index]['commands_executed'][-1]['type']=='arena_end_turn'
        for entry in bundle['trace']['entries']:
            command = command_from_dict(entry['command'])
            kind=entry['command']['type']
            if is_luna and turn['explicit_end_turn'] and kind=='arena_end_turn':
                opportunities=[]
                for action in candidate_observation(sim.state).to_dict()['legal_actions']:
                    if action['type'] not in ('attack','snipe','shield_bash','fireball'): continue
                    trial=ArenaSimulation(from_snapshot(to_snapshot(sim.state)))
                    before={u.id:(u.hp,u.owner_id,u.status.value) for u in trial.state.units.values()}
                    cores={c.id:(c.hp,c.owner_id) for c in trial.state.cores.values()}
                    trial.execute(action_command(action_from_dict(action),side))
                    damage=sum(max(0,hp-trial.state.units[uid].hp) for uid,(hp,owner,status) in before.items() if owner!=side)
                    core_damage=sum(max(0,hp-trial.state.cores[cid].hp) for cid,(hp,owner) in cores.items() if owner!=side)
                    downs=sum(status=='active' and trial.state.units[uid].status.value=='downed' for uid,(hp,owner,status) in before.items() if owner!=side)
                    if damage+core_damage: opportunities.append(dict(action=action,enemy_unit_damage=damage,enemy_core_damage=core_damage,enemy_downs=downs))
                report['end_turns'].append(dict(match_id=row['match_id'],arm=row['arm'],ordinal=bundle['ordinal'],
                    ap_remaining=sim.state.action_points_remaining,actions_before=turn['actions_before_intentional_stop'],
                    replacement=turn['replacement_explicit_end_turn'],requests_after_end_turn=0,
                    legal_damaging_opportunities=opportunities))
            fire=None
            ability=None
            if kind in ('arena_snipe','arena_shield_bash'):
                ability_before={u.id:(u.hp,u.owner_id,u.status.value,u.position) for u in sim.state.units.values()}
                ability=dict(match_id=row['match_id'],arm=row['arm'],agent='luna' if is_luna else 'heuristic',
                    ordinal=bundle['ordinal'],kind=kind,actor=command.actor_id)
            if kind=='arena_fireball':
                actor=command.actor_id
                affected=arena_fireball_affected_units(sim.state,command.target_position)
                before={u.id:(u.hp,u.owner_id,u.status.value) for u in sim.state.units.values()}
                fire=dict(match_id=row['match_id'],arm=row['arm'],agent='luna' if is_luna else 'heuristic',ordinal=bundle['ordinal'],
                    friendly_units_hit=sum(sim.state.units[u].owner_id==actor for u in affected),
                    enemy_units_hit=sum(sim.state.units[u].owner_id!=actor for u in affected))
            assert sim.execute(command)==entry
            if ability is not None:
                for relation in ('friendly','enemy'):
                    units={uid:v for uid,v in ability_before.items() if (v[1]==command.actor_id)==(relation=='friendly')}
                    ability[relation+'_damage']=sum(max(0,hp-sim.state.units[uid].hp) for uid,(hp,owner,status,pos) in units.items())
                    ability[relation+'_downs']=sum(status=='active' and sim.state.units[uid].status.value=='downed' for uid,(hp,owner,status,pos) in units.items())
                    ability[relation+'_displacements']=sum(pos!=sim.state.units[uid].position for uid,(hp,owner,status,pos) in units.items())
                report['ability_effects'].append(ability)
            if fire is not None:
                for relation in ('friendly','enemy'):
                    selected={u:v for u,v in before.items() if (v[1]==actor)==(relation=='friendly')}
                    fire[relation+'_damage']=sum(max(0,hp-sim.state.units[u].hp) for u,(hp,owner,status) in selected.items())
                    fire[relation+'_downs']=sum(status=='active' and sim.state.units[u].status.value=='downed' for u,(hp,owner,status) in selected.items())
                fire['winner_after_action']=sim.state.winner_player_id
                report['fireballs'].append(fire)
        assert to_snapshot(sim.state)==bundle['final_state']
for arm in ARMS:
    item=report['arms'][arm]
    stops=[s for s in report['end_turns'] if s['arm']==arm]
    item['end_turn_audit']=dict(count=len(stops),immediate=sum(s['actions_before']==0 for s in stops),
        ap_distribution=dict(Counter(s['ap_remaining'] for s in stops)),actions_before_distribution=dict(Counter(s['actions_before'] for s in stops)),
        damaging_opportunity_stops=sum(bool(s['legal_damaging_opportunities']) for s in stops),
        down_opportunity_stops=sum(any(o['enemy_downs'] for o in s['legal_damaging_opportunities']) for s in stops),requests_after_end_turn=0)
    casts=[c for c in report['fireballs'] if c['arm']==arm and c['agent']=='luna']
    item['fireball_audit']={k:sum(c[k] for c in casts) for k in ('friendly_units_hit','enemy_units_hit','friendly_damage','enemy_damage','friendly_downs','enemy_downs')}
    assert sum(report['request_categories'][arm].values())==item['totals'].get('provider_requests',0)
    selected=[r for r in rows if r['arm']==arm]
    item['projection']={}
    for field in ('provider_requests','total_tokens','provider_latency_seconds'):
        values=[r['metrics'][r['luna_side']][field] for r in selected]
        item['projection'][field]=None if not values or any(v is None for v in values) else dict(
            remaining_matches=sum(values)/len(values)*(100-len(selected)),full_100=sum(values)/len(values)*100,
            per_match_observed_range=[min(values),max(values)],remaining_matches_sensitivity=[min(values)*(100-len(selected)),max(values)*(100-len(selected))],
            full_100_sensitivity=[sum(values)+min(values)*(100-len(selected)),sum(values)+max(values)*(100-len(selected))])
contract=read(ROOT/'contract.json')
report['bindings']=dict(contract_sha256=contract['sha256'],contract_file_sha256=sha(ROOT/'contract.json'),
    schedule_sha256=contract['payload']['schedule_hash'],batch_4_schedule_sha256=digest(contract['payload']['schedule'][90:120]),
    source_manifest_sha256=digest(contract['payload']['source_hashes']),source_files=len(contract['payload']['source_hashes']))
(ROOT/'supplemental-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(matches=len(rows),end_turns=len(report['end_turns']),fireballs=len(report['fireballs']),success=True)))
