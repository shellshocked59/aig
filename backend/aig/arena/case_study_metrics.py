"""Mechanical match telemetry, computed from authoritative commands and turn records."""
from collections import Counter

from aig.arena.ai.candidate_control import STOP_REASONS, aggregate_candidate_turns
from aig.arena.commands import arena_fireball_affected_units
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import from_snapshot, command_from_dict, to_snapshot

TACTICAL = ('attacks','core_attacks','snipe','shield_bash','fireball','finish','revive','heal','move',
    'enemy_damage','friendly_damage','friendly_fireball_damage','enemy_fireball_damage',
    'empty_fireballs','friendly_only_fireballs','mixed_fireballs','enemy_only_fireballs',
    'enemy_units_downed','friendly_units_downed','units_downed_received','units_finished_received')


def mechanical(trace):
    sim = ArenaSimulation(from_snapshot(trace['initial_snapshot']))
    counts = {p.id:dict.fromkeys(TACTICAL,0) for p in sim.state.players}
    for entry in trace['entries']:
        command = command_from_dict(entry['command'])
        side, kind = command.actor_id, entry['command']['type'].removeprefix('arena_')
        row = counts[side]
        units = {u.id:(u.hp,u.owner_id,u.status.value) for u in sim.state.units.values()}
        if kind in ('attack','snipe','shield_bash','fireball','finish','revive','heal','move'):
            row['attacks' if kind == 'attack' else kind] += 1
        if kind == 'attack' and command.target_id in sim.state.cores:
            row['core_attacks'] += 1
        if kind == 'fireball':
            affected = arena_fireball_affected_units(sim.state,command.target_position)
            friendly = sum(sim.state.units[uid].owner_id == side for uid in affected)
            enemy = len(affected)-friendly
            category = ('mixed' if friendly and enemy else 'friendly_only' if friendly
                        else 'enemy_only' if enemy else 'empty')
            row[category+'_fireballs'] += 1
        sim.execute(command)
        for uid,(hp, owner, status) in units.items():
            after = sim.state.units.get(uid)
            if after is None:
                counts[owner]['units_finished_received'] += 1
                continue
            loss = max(0,hp-after.hp)
            relation = 'friendly' if owner == side else 'enemy'
            row[relation+'_damage'] += loss
            if kind == 'fireball':
                row[relation+'_fireball_damage'] += loss
            if status == 'active' and after.status.value == 'downed':
                row[relation+'_units_downed'] += 1
                counts[owner]['units_downed_received'] += 1
    result = sim.metrics()['players']
    initial = from_snapshot(trace['initial_snapshot'])
    for side, values in result.items():
        values.update(counts[side])
        core = next(c for c in sim.state.cores.values() if c.owner_id == side)
        initial_hp = next(c.hp for c in initial.cores.values() if c.owner_id == side)
        values.update(core_hp_remaining=core.hp,core_damage_received=initial_hp-core.hp,
            core_damage_dealt=values['core_damage'],
            units_removed=sum(u.owner_id==side for u in initial.units.values())-
                          sum(u.owner_id==side for u in sim.state.units.values()))
    return result


def reliability(rows):
    result = aggregate_candidate_turns(rows)
    waves = [w for r in rows for w in r['waves']]
    attempts = [a for w in waves for a in w['inference'].get('attempts',[])]
    first = [w['inference']['attempts'][0] for w in waves if w['inference'].get('attempts')]
    repairs = [a for w in waves for a in w['inference'].get('attempts',[])[1:]]
    replacement = [r['waves'][1] for r in rows if r['replan_used']]
    result.update(provider_failures=sum(r['provider_failure'] and r['error_category']!='request_ceiling' for r in rows),
        request_limit_decisions=sum(r['error_category']=='request_ceiling' for r in rows),
        request_limit_unused_ap=sum(r['ap_remaining'] for r in rows if r['error_category']=='request_ceiling'),
        provider_latency_seconds=sum(a.get('wall_clock_seconds',0) for a in attempts),
        backend_thinking_seconds=sum(r['control_wall_seconds'] for r in rows),
        first_responses=len(first), first_response_valid=sum(not a.get('error_category') for a in first),
        repairs=len(repairs), repair_success=sum(not a.get('error_category') for a in repairs),
        repair_failure=sum(bool(a.get('error_category')) for a in repairs),
        initial_execution_invalidities=sum(bool(r['waves'] and r['waves'][0]['invalid_action']) for r in rows),
        execution_truncations=sum(r['truncation'] for r in rows),
        invalidities=[dict(turn=r['turn'],wave=w['wave_index'],**w['invalid_action'])
            for r in rows for w in r['waves'] if w['invalid_action']],
        replans=len(replacement), ap_at_replan=[r['ap_at_replan'] for r in rows if r['replan_used']],
        ap_recovered_distribution=[r['ap_recovered'] for r in rows if r['replan_used']],
        replacement_repairs=sum(max(0,w['provider_requests']-1) for w in replacement),
        replacement_invalidities=sum(bool(w['error_category']) for w in replacement),
        second_invalidities=sum(r['second_invalidity'] for r in rows),
        decisions=sum(r['decisions'] for r in rows), decisions_per_turn=[r['decisions'] for r in rows],
        explicit_end_turn_decisions=sum(r['explicit_end_turn_decisions'] for r in rows),
        completed_turns=sum(not r['provider_failure'] for r in rows),
        requests_in_completed_turns=sum(r['provider_requests'] for r in rows if not r['provider_failure']))
    result['first_response_static_valid_rate'] = result['first_response_valid']/len(first) if first else None
    result['failure_derived_unused_ap'] -= result['request_limit_unused_ap']
    result['backend_thinking_seconds_per_turn'] = result['backend_thinking_seconds']/len(rows) if rows else 0
    result['provider_latency_seconds_per_turn'] = result['provider_latency_seconds']/len(rows) if rows else 0
    result['replacement_first_invalidities'] = sum(bool(w['inference'].get('attempts') and
        w['inference']['attempts'][0].get('error_category')) for w in replacement)
    for key in ('input_tokens','output_tokens','total_tokens','cached_input_tokens','reasoning_tokens'):
        values = [a.get('metrics',{}).get(key) for a in attempts]
        result[key] = sum(values) if all(v is not None for v in values) else None
    return result


def match_metrics(trace,turns,luna_side):
    result = mechanical(trace)
    for side, values in result.items():
        rows = [r for r in turns if r['player_id']==side]
        if side == luna_side:
            values.update(reliability(rows))
        else:
            unused = {reason:sum(r['ap_remaining'] for r in rows if r['stop_reason']==reason) for reason in STOP_REASONS}
            values.update(turns=len(rows),provider_requests=0,input_tokens=0,output_tokens=0,total_tokens=0,
                provider_latency_seconds=0,backend_thinking_seconds=0,
                heuristic_compute_seconds=sum(r['control_wall_seconds'] for r in rows),
                ap_available=sum(r['ap_available'] for r in rows),ap_executed=sum(r['ap_executed'] for r in rows),
                unused_ap_by_reason=unused, intentional_unused_ap_supported=False,
                stop_counts=dict(Counter(r['stop_reason'] for r in rows)))
        values['ap_unused']=sum(values['unused_ap_by_reason'].values())
        values['ap_remaining']=values['ap_unused']
    return result
