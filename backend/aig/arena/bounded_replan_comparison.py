"""Offline preparation and separately gated historical-state Luna comparison.

Reuses frozen v6 contracts and existing executors; v6's probe schedule is untouched.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from time import perf_counter

from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController, execute_plan_segment
from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.observation import ArenaObservation, build_observation, simulation_state
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.prompts import resolve_prompt
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan, openai_turn_plan_schema
from aig.arena.benchmark_provider import safe_inference
from aig.arena.benchmark_versions import frozen_probe, probe_set
from aig.arena.bounded_replan_benchmark import ROOT, recipe, sources, write
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, digest, state_hash, to_snapshot, from_snapshot
from aig.settings import Settings, load_settings

VERSION = 'arena-bounded-luna-comparison-v1'
ARMS = ('full_turn', 'bounded_replan')
STATIC = {'malformed_json', 'schema_validation', 'ap_budget', 'invalid_reference', 'invalid_ability'}
ORDINARY = STATIC | {'repair_failed', 'authentication_failure', 'timeout', 'connection_failure',
    'dns_failure', 'transport_failure', 'malformed_envelope', 'refusal', 'configuration_failure',
    'rate_limit', 'server_error', 'context_limit'}
TOKENS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_tokens', 'total_tokens')


class IntegrityError(RuntimeError):
    """Hard stop, never converted to a provider failure or fallback."""


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def inventory():
    result = sources()
    for pattern in ('scripts/arena-bounded-replan-audit.py', 'tests/test_arena_bounded_replan_comparison.py',
                    'docs/arena-bounded-replan-benchmark-plan.md'):
        path = ROOT / pattern
        if path.exists():
            result[pattern] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def historical_audit():
    """Extend the original audit without overwriting it or any original artifacts."""
    spec = importlib.util.spec_from_file_location('historical_audit', ROOT/'scripts/arena-bounded-replan-audit.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    previous = json.loads(old.read(ROOT/'docs/arena-bounded-replan-audit.json'))
    all_rows, summaries = [], []
    for cohort in previous['cohorts']:
        if cohort['provider'] != 'openai':
            continue
        summary = old.audit(cohort['label'], cohort['root'], 'openai')
        require(digest(summary) == digest(cohort), 'historical audit changed')
        summaries.append(summary)
        for path in sorted((ROOT/cohort['root']).rglob('plans.jsonl')):
            saved, observations = old.rows(path), old.rows(path.with_name('observations.jsonl'))
            initial = json.loads(old.read(path.with_name('initial-snapshot.json')))
            entries = old.rows(path.with_name('commands.jsonl'))
            original = ArenaSimulation(from_snapshot(initial))
            starts = {0: to_snapshot(original.state)}
            from aig.arena.snapshots import command_from_dict
            for index, entry in enumerate(entries):
                require(original.execute(command_from_dict(entry['command'])) == entry, 'historical command mismatch')
                starts[index+1] = to_snapshot(original.state)
            require(to_snapshot(original.state) == json.loads(old.read(path.with_name('final-snapshot.json'))),
                    'historical final state mismatch')
            max_turn = max(r['turn'] for r in saved)
            for index, row in enumerate(saved):
                if row['provider_type'] != 'openai':
                    continue
                obs = ArenaObservation.from_dict(observations[row['inference_index']]['observation'])
                snapshot = to_snapshot(simulation_state(obs))
                require(snapshot == starts[row['command_start']], 'historical starting state mismatch')
                require(obs.hash == row['observation_hash'], 'historical observation mismatch')
                plan = parse_turn_plan(canonical_json(row['plan']), obs)
                sim = ArenaSimulation(from_snapshot(snapshot))
                segment = execute_plan_segment(sim, plan)
                invalid = segment['invalid_action']
                terminal = sim.state.winner_player_id is not None
                phase = ('early', 'mid', 'late')[min(2, row['turn']*3//(max_turn+1))]
                metadata = dict(case_id=f'{path.relative_to(ROOT).as_posix()}#{index}',
                    cohort=cohort['label'], path=path.relative_to(ROOT).as_posix(), row_index=index,
                    turn=row['turn'], player_id=row['player_id'], phase=phase,
                    initial_state_hash=digest(snapshot), initial_observation_hash=obs.hash,
                    initial_ap=row['ap_available'], planned_ap=plan.ap_cost,
                    executed_ap_before_invalidity=segment['ap_spent'] if invalid else None,
                    historical_executed_ap=segment['ap_spent'], ap_remaining=segment['ap_unused'],
                    invalid_index=invalid['index'] if invalid else None,
                    invalid_action_type=invalid['action']['type'] if invalid else None,
                    invalid_reason=invalid['reason'] if invalid else None,
                    stale_suffix_length=segment['stale_suffix_count'],
                    suffix_after_invalid_length=max(0, segment['stale_suffix_count']-1),
                    terminal_before_invalidity=terminal if invalid else None,
                    replan_eligible=bool(invalid and not terminal and segment['ap_unused'] > 0),
                    category='no_historical_truncation' if not invalid else
                        'early_truncation' if invalid['index'] <= 1 else 'mid_late_truncation',
                    recoverable_ap_category=None if not invalid else
                        'high' if segment['ap_unused'] >= 3 else 'low' if segment['ap_unused'] == 1 else 'medium',
                    snapshot=snapshot, historical_plan=row['plan'],
                    boundary_snapshot=to_snapshot(sim.state) if invalid else None,
                    historical_prompt=row['prompt_version'], historical_observation=obs.version)
                metadata.update(features(snapshot, plan.to_dict()))
                all_rows.append(metadata)
    require(all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p, h in old.INPUTS.items()),
            'historical evidence drift')
    return dict(version=VERSION, cohorts=summaries, cases=all_rows, input_sha256=old.INPUTS,
                stepwise_reference=previous['stepwise_comparison'])


def features(snapshot, plan=None):
    obs = build_observation(from_snapshot(snapshot)).to_dict()
    actions = Counter(a['type'] for a in (plan or {}).get('actions', []))
    available = set()
    core_ids = {c['id'] for c in snapshot['cores']}
    pressure = False
    for unit in obs['own_team']['units']:
        for action, targets in unit['actions'].items():
            if targets:
                available.add(action)
            if action == 'attack' and any(t in core_ids for t in targets):
                pressure = True
    return dict(unit_count=len(snapshot['units']),
                downed_units=sum(u['status'] == 'downed' for u in snapshot['units']),
                available_action_types=sorted(available), historical_action_types=sorted(actions),
                core_pressure=pressure)


def tags(row):
    result = [f'{k}:{row.get(k)}' for k in ('phase', 'player_id', 'invalid_index',
        'invalid_reason', 'recoverable_ap_category', 'unit_count', 'downed_units', 'core_pressure')]
    return result + ['action:'+a for a in row['available_action_types']]


def select_cases(audit):
    pool = [r for r in audit['cases'] if r['cohort'] == 'luna V1 full matches']
    # Fixed quotas, inverse-frequency coverage, digest tie break. No replacement outcomes.
    frequency = Counter(t for r in pool for t in tags(r))
    coverage, selected, used = Counter(), [], set()
    def pick(invalid):
        candidates = [r for r in pool if bool(r['invalid_reason']) == invalid and r['initial_state_hash'] not in used]
        require(bool(candidates), 'selection quota unavailable')
        least_phase = min(coverage['phase:'+r['phase']] for r in candidates)
        candidates = [r for r in candidates if coverage['phase:'+r['phase']] == least_phase]
        row = min(candidates, key=lambda r: (-sum(1/(frequency[t]*(1+coverage[t])) for t in tags(r)),
                                              digest(r['case_id'])))
        selected.append(deepcopy(row)); used.add(row['initial_state_hash']); coverage.update(tags(row))
    for _ in range(3):
        for invalid in (True, True, True, False):
            pick(invalid)
    # Two explicit tactical anchors in Stage 1; remaining probes go in Stage 2.
    def probe(name):
        snapshot = to_snapshot(frozen_probe(name))
        row = dict(case_id='probe:'+name, cohort='frozen_probe', snapshot=snapshot,
                   initial_state_hash=digest(snapshot), category='no_historical_label',
                   historical_plan=None, initial_ap=snapshot['action_points_remaining'])
        row.update(features(snapshot)); selected.append(row)
    for name in ('revive_decision', 'finish_or_core'):
        probe(name)
    for _ in range(5):
        for invalid in (True, True, True, False):
            pick(invalid)
    for name in probe_set()['probes']:
        if name not in ('revive_decision', 'finish_or_core'):
            probe(name)
    for ap in (1, 2, 3):
        row = min((r for r in pool if r['replan_eligible'] and r['ap_remaining'] == ap),
                  key=lambda r: digest(r['case_id']))
        snapshot = row['boundary_snapshot']
        selected.append(dict(case_id='boundary:'+row['case_id'], cohort='historical_partial_boundary',
            snapshot=snapshot, initial_state_hash=digest(snapshot), category='no_historical_label',
            historical_plan=None, initial_ap=ap, parent_case_id=row['case_id'], **features(snapshot)))
    require(len(selected) == 42, 'selection size')
    require(len({r['initial_state_hash'] for r in selected}) == 42, 'duplicate states')
    for index, row in enumerate(selected, 1):
        row['pair_id'] = f'pair-{index:03d}'
        row['initial_observation_hash'] = build_observation(from_snapshot(row['snapshot'])).hash
        row['player_id'] = row['snapshot']['active_player_id']
    return selected


def distribution(rows):
    return {key: dict(Counter(str(r.get(key)) for r in rows)) for key in
            ('cohort', 'category', 'recoverable_ap_category', 'phase', 'initial_ap', 'unit_count',
             'invalid_index', 'invalid_reason', 'downed_units', 'player_id')}


def seal(data):
    return dict(data, plan_hash=digest(data))


def prepare(output):
    output = Path(output)
    require(not output.exists(), 'use a new immutable preparation root')
    audit = historical_audit()
    cases = select_cases(audit)
    profile, config = resolve_model_profile('openai', 'luna-config-v1')
    original_path = ROOT/'.local/arena-bounded-paired-plan.json'
    original = json.loads(original_path.read_text())
    original_audit = dict(path=str(original_path.relative_to(ROOT)),
        sha256=hashlib.sha256(original_path.read_bytes()).hexdigest(),
        fixture_names=[r['name'] for r in original['fixtures']], repetitions=original['repetitions'],
        intended_turns=28, pairs=14, request_ceiling=original['request_ceiling'],
        source_manifest_current=original['source_files'] == sources(),
        design='seven probes x two repetitions x two arms; 84 is a maximum request count')
    base = dict(version=VERSION, recipe=recipe(), recipe_hash=digest(recipe()),
        policy=dict(version='arena-bounded-comparison-schedule-v1',
            failure_policy='ordinary provider failures persist prefix and continue independent arms; integrity failures stop',
            order='pair_id ascending; strict then bounded', fallback=False, preflight_requests=0,
            transport_retries=0, max_execution_replans=1),
        provider='openai', model_profile=profile, model_configuration=config,
        transport=dict(adapter='OpenAIArenaTurnProvider', api='Responses', timeout_seconds=Settings().openai.timeout_seconds,
                       format='existing adapter JSON schema; unchanged'),
        prompt_hash=hashlib.sha256(resolve_prompt('arena-turn-prompt-v1')[1].encode()).hexdigest(),
        wire_schema_hash=digest(openai_turn_plan_schema()), pricing=None,
        fixture_version='arena-bounded-historical-states-v1', source_files=inventory(),
        source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        source_dirty=bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
        evidence_sha256=audit['input_sha256'], original_prepared_audit=original_audit)
    output.mkdir(parents=True)
    write(output/'historical-audit.json', audit)
    write(output/'selection.json', dict(rule='fixed quotas; inverse-frequency coverage; digest tie break',
          cases=cases, stage1_distribution=distribution(cases[:14]), full_distribution=distribution(cases)))
    for stage, rows, ceilings in [('stage1', cases[:14], dict(full_turn=18, bounded_replan=32, total=50)),
                                  ('stage2', cases[14:], dict(full_turn=36, bounded_replan=64, total=100))]:
        plan = seal(dict(base, stage=stage, cases=rows, fixture_hash=digest(rows), ceilings=ceilings,
                         intended_turns=2*len(rows), architectural_maximum=6*len(rows)))
        write(output/(stage+'-plan.json'), plan)
    return dict(prepared_root=str(output), pairs=42, stage1_pairs=14, stage2_additional_pairs=28,
                original=original_audit)


def nullable_sum(values):
    values = list(values)
    return sum(values) if all(v is not None for v in values) else None


def wave_metrics(wave):
    attempts = wave.get('inference', {}).get('attempts', [])
    invalid = wave.get('invalid_action')
    planned = wave.get('plan')
    static = bool(attempts and attempts[0].get('error_category') in STATIC)
    return dict(planned_ap=wave.get('planned_ap'), actions_planned=len(planned['actions']) if planned else None,
        invalid_action=invalid, executed_ap=wave.get('ap_spent', 0),
        ap_remaining=wave.get('ap_unused', wave['observation']['action_points_remaining']),
        stale_suffix_discarded=wave.get('stale_suffix_count', 0),
        first_response_valid=attempts[0].get('error_category') is None if attempts else None,
        static_invalid=static, static_repair_attempts=max(0, len(attempts)-1),
        static_repair_success=bool(static and len(attempts) == 2 and planned is not None),
        provider_failure=wave.get('error_category'), observation_hash=wave['observation_hash'],
        provider_attempts=len(attempts), latency_seconds=nullable_sum(a.get('wall_clock_seconds') for a in attempts),
        **{key: nullable_sum(a.get('metrics', {}).get(key) for a in attempts) for key in TOKENS})


def arm_metrics(turn, waves, sim, elapsed):
    wm = [wave_metrics(w) for w in waves]
    initial, replacement = wm[0], wm[1] if len(wm) > 1 else None
    error = turn.get('error_category')
    unused = turn['ap_unused']
    terminal = sim.state.winner_player_id
    invalid = initial['invalid_action']
    return dict(initial=initial, replacement=replacement,
        initial_execution_invalidity=invalid is not None,
        ap_before_first_invalidity=initial['executed_ap'] if invalid else None,
        ap_at_first_invalidity=initial['ap_remaining'] if invalid else None,
        replan_triggered=replacement is not None,
        replan_success=bool(replacement and not replacement['provider_failure'] and not replacement['invalid_action']),
        second_execution_invalidity=bool(replacement and replacement['invalid_action']),
        terminal_replacement=bool(replacement and terminal),
        ap_at_replan=waves[1]['observation']['action_points_remaining'] if replacement else None,
        ap_recovered=replacement['executed_ap'] if replacement else 0,
        ap_available=turn['ap_available'], ap_executed=turn['ap_spent'], ap_unused=unused,
        short_plan_unused_AP=unused if not invalid and not error and terminal is None else 0,
        replacement_short_plan_unused_AP=unused if replacement and not replacement['invalid_action'] and not error and terminal is None else 0,
        truncation_unused_AP=unused if invalid and not error and terminal is None and
            (not replacement or replacement['invalid_action']) else 0,
        provider_failed_unused_AP=unused if error else 0, terminal_unused_AP=unused if terminal else 0,
        provider_failure=error, completed_turn=error is None,
        terminal_result=terminal, commands_executed=len(sim.trace()['entries']),
        final_state_hash=state_hash(sim.state), combat=sim.metrics(), backend_thinking_seconds=elapsed,
        provider_attempts=sum(w['provider_attempts'] for w in wm),
        static_repair_attempts=sum(w['static_repair_attempts'] for w in wm),
        static_repair_successes=sum(w['static_repair_success'] for w in wm),
        provider_latency_seconds=nullable_sum(w['latency_seconds'] for w in wm),
        estimated_cost_usd=None, **{key: nullable_sum(w[key] for w in wm) for key in TOKENS})


def summarize(report):
    results = {}
    for arm in ARMS:
        rows = [r['metrics'] for r in report['runs'] if r['arm'] == arm and 'metrics' in r]
        n = len(rows)
        if not n:
            continue
        replans = [r for r in rows if r['replan_triggered']]
        result = dict(started_turns=n, intended_turns=report['intended_turns']//2,
            unstarted_turns=report['intended_turns']//2-n,
            execution_truncation_rate=sum(r['initial_execution_invalidity'] for r in rows)/n,
            completion_rate=sum(r['completed_turn'] for r in rows)/n,
            provider_failure_rate=sum(bool(r['provider_failure']) for r in rows)/n,
            replan_rate=len(replans)/n,
            replan_success_rate=sum(r['replan_success'] for r in replans)/len(replans) if replans else None,
            second_invalid_rate=sum(r['second_execution_invalidity'] for r in replans)/len(replans) if replans else None,
            ap_recovered_per_replan=sum(r['ap_recovered'] for r in replans)/len(replans) if replans else None)
        initial_attempted = [r for r in rows if r['initial']['first_response_valid'] is not None]
        result['initial_first_response_validity'] = sum(r['initial']['first_response_valid'] for r in initial_attempted)/len(initial_attempted) if initial_attempted else None
        result['static_repairs'] = sum(r['static_repair_attempts'] for r in rows)
        result['static_repair_successes'] = sum(r['static_repair_successes'] for r in rows)
        result['initial_static_invalid_turns'] = sum(r['initial']['static_invalid'] for r in rows)
        result['replacement_static_invalid_turns'] = sum(r['replacement']['static_invalid'] for r in replans)
        result['initial_execution_invalid_turns'] = sum(r['initial_execution_invalidity'] for r in rows)
        result['replacement_execution_invalid_turns'] = sum(r['second_execution_invalidity'] for r in rows)
        result['historical_category_strata'] = {}
        for category in sorted({r['category'] for r in report['runs'] if r['arm'] == arm}):
            subset = [r['metrics'] for r in report['runs'] if r['arm'] == arm and r['category'] == category and 'metrics' in r]
            if subset:
                result['historical_category_strata'][category] = dict(turns=len(subset),
                    mean_ap_executed=sum(r['ap_executed'] for r in subset)/len(subset),
                    mean_provider_attempts=sum(r['provider_attempts'] for r in subset)/len(subset),
                    recovered_ap=sum(r['ap_recovered'] for r in subset))
        for key in ('provider_attempts', 'ap_executed', 'ap_unused', 'provider_latency_seconds',
                    'backend_thinking_seconds', *TOKENS):
            total = nullable_sum(r[key] for r in rows)
            result['mean_'+key] = total/n if total is not None else None
        results[arm] = result
    pairs = []
    for pair_id in dict.fromkeys(r['pair_id'] for r in report['runs']):
        arms = {r['arm']: r for r in report['runs'] if r['pair_id'] == pair_id}
        pair = dict(pair_id=pair_id, arms=arms)
        if all(a in arms and 'metrics' in arms[a] for a in ARMS):
            a, b = (arms[k]['metrics'] for k in ARMS)
            pair['delta'] = {k: b[k]-a[k] if b[k] is not None and a[k] is not None else None for k in
                ('provider_attempts', 'ap_executed', 'provider_latency_seconds', 'backend_thinking_seconds', 'total_tokens')}
            pair['tactical_state_differences'] = {p: {k: b['combat']['players'][p][k]-a['combat']['players'][p][k]
                for k in ('living_units', 'downed_units', 'total_hp', 'core_hp', 'damage_dealt', 'friendly_fire_damage')}
                for p in a['combat']['players']}
        pairs.append(pair)
    return dict(version=VERSION, evidence_kind=report['evidence_kind'], status=report['status'],
                headlines=results, pairs=pairs, pricing=None)


def render(comparison):
    lines = [f"# {comparison['evidence_kind']}", '',
        'Independent live initial plans measure end-to-end behavior. Offline scripted output is mechanical evidence only.', '',
        '| Pair | Strict calls | AP | Unused | Invalid | Bounded calls | Replan | Recovered AP | AP | Extra calls | AP delta | Latency delta | Token delta |',
        '|---|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|']
    for p in comparison['pairs']:
        arms = p['arms']
        if 'delta' not in p:
            lines.append(f"| {p['pair_id']} | incomplete |")
            continue
        a, b = (arms[k]['metrics'] for k in ARMS); d = p['delta']
        lines.append(f"| {p['pair_id']} | {a['provider_attempts']} | {a['ap_executed']} | {a['ap_unused']} | {a['initial_execution_invalidity']} | {b['provider_attempts']} | {b['replan_triggered']} | {b['ap_recovered']} | {b['ap_executed']} | {d['provider_attempts']} | {d['ap_executed']} | {d['provider_latency_seconds']} | {d['total_tokens']} |")
    lines += ['', 'Final hashes, tactical differences, wave details, and aggregates: comparison.json and per-arm turn.json.', '']
    return '\n'.join(lines)


def validate_plan(saved):
    require(digest({k:v for k,v in saved.items() if k != 'plan_hash'}) == saved['plan_hash'], 'plan corruption')
    require(saved['version'] == VERSION and saved['recipe'] == recipe(), 'version mismatch')
    require(saved['recipe_hash'] == digest(recipe()), 'recipe mismatch')
    require(saved['source_files'] == inventory(), 'source drift')
    require(saved['fixture_hash'] == digest(saved['cases']), 'fixture corruption')
    require(saved['provider'] == 'openai' and saved['model_profile'] == 'luna-config-v1', 'wrong provider/profile')
    require(saved['model_configuration'] == resolve_model_profile('openai', 'luna-config-v1')[1], 'profile mismatch')
    require(saved['prompt_hash'] == hashlib.sha256(resolve_prompt('arena-turn-prompt-v1')[1].encode()).hexdigest(), 'prompt drift')
    require(saved['wire_schema_hash'] == digest(openai_turn_plan_schema()), 'schema drift')
    require(saved['intended_turns'] == 2*len(saved['cases']), 'schedule corruption')
    require(len({c['pair_id'] for c in saved['cases']}) == len(saved['cases']), 'pair identity corruption')
    for c in saved['cases']:
        state = from_snapshot(c['snapshot'])
        require(state_hash(state) == c['initial_state_hash'] and build_observation(state).hash == c['initial_observation_hash'], 'state corruption')
        require(state.active_player_id == c['player_id'] and state.action_points_remaining == c['initial_ap'], 'pair metadata corruption')
    require(all(type(saved['ceilings'][k]) is int and saved['ceilings'][k] > 0 for k in (*ARMS, 'total')), 'invalid ceilings')
    require(all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in saved['evidence_sha256'].items()), 'evidence corruption')


def run(plan_path, output, *, settings=None, provider_factory=None, offline=False):
    """Single orchestration, all arms frozen together. No automatic preflight or retry."""
    saved = json.loads(Path(plan_path).read_text())
    validate_plan(saved)
    settings = settings or Settings()
    require(inference_configuration('openai', settings) == saved['model_configuration'], 'runtime profile mismatch')
    require(settings.openai.timeout_seconds == saved['transport']['timeout_seconds'], 'transport mismatch')
    require(not offline or provider_factory is not None, 'offline requires fake transport')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    write(output/'plan.json', saved)
    report = dict(version=VERSION, status='complete', evidence_kind='OFFLINE SCRIPTED POLICY REPLAY' if offline else 'LIVE END-TO-END PAIRED',
                  intended_turns=saved['intended_turns'], requests={a:0 for a in (*ARMS, 'total')}, runs=[])
    def persist():
        report['unstarted_turns'] = report['intended_turns']-len(report['runs'])
        write(output/'report.json', report)
        comparison = summarize(report)
        write(output/'comparison.json', comparison)
        (output/'report.md').write_text(render(comparison), encoding='utf-8')
    persist()
    for case in saved['cases']:
        for arm in ARMS:
            sim = ArenaSimulation(from_snapshot(case['snapshot']))
            folder = output / ('strict' if arm == 'full_turn' else 'bounded') / case['pair_id']
            folder.mkdir(parents=True)
            row = dict(pair_id=case['pair_id'], arm=arm, initial_state_hash=state_hash(sim.state),
                       player_id=sim.state.active_player_id, ap=sim.state.action_points_remaining,
                       category=case['category'], control_version=saved['recipe'][
                           'comparison_control_version' if arm == 'full_turn' else 'control_version'])
            waves = []
            started = perf_counter()
            before_arm = report['requests'][arm]
            try:
                require(inventory() == saved['source_files'], 'source drift')
                provider = provider_factory(settings, case, arm) if provider_factory else create_arena_turn_provider(settings, 'openai')
                require(isinstance(provider, OpenAIArenaTurnProvider) and provider.name == 'openai'
                    and provider.configuration() == saved['model_configuration'] and provider.repair
                    and provider.prompt_version == saved['recipe']['prompt']
                    and provider.schema_version == saved['recipe']['schema'], 'provider contract mismatch')
                def boundary():
                    require(inventory() == saved['source_files'], 'source drift')
                    require(all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h
                                for p,h in saved['evidence_sha256'].items()), 'evidence corruption')
                    if (report['requests'][arm] >= saved['ceilings'][arm] or
                            report['requests']['total'] >= saved['ceilings']['total']):
                        raise ArenaProviderError('request_ceiling')
                    require(report['requests'][arm]-before_arm < (2 if arm == 'full_turn' else 4), 'turn request accounting')
                    report['requests'][arm] += 1; report['requests']['total'] += 1
                    # Durable reservation before transport; a crash cannot imply zero spending.
                    with (output/'request-ledger.jsonl').open('a', encoding='utf-8') as stream:
                        stream.write(canonical_json(dict(pair_id=case['pair_id'], arm=arm,
                            reservation=report['requests']['total'], arm_reservation=report['requests'][arm]))+'\n')
                        stream.flush()
                provider.before_request = boundary
                original = provider.create_turn_plan
                def verified(observation):
                    before = report['requests'][arm]
                    error, candidate = None, None
                    try:
                        candidate = original(observation)
                    except ArenaProviderError as caught:
                        error = caught.category
                    raw = provider.last_trace or {}
                    attempts = report['requests'][arm]-before
                    require(raw.get('requested_provider') == 'openai' and not raw.get('fallback_used') and
                        raw.get('actual_provider') == ('openai' if candidate is not None else None), 'provider purity')
                    require(len(raw.get('attempts', [])) == attempts and attempts <= 2 and
                        (attempts >= 1 or error == 'request_ceiling'), 'request accounting corruption')
                    require(raw.get('model_configuration') == saved['model_configuration'] and
                        raw.get('model_config_version') == saved['model_profile'] and
                        raw.get('observation_version') == saved['recipe']['observation'] and
                        raw.get('observation_hash') == observation.hash and
                        raw.get('prompt_version') == saved['recipe']['prompt'] and
                        raw.get('schema_version') == saved['recipe']['schema'], 'inference version mismatch')
                    inference = safe_inference(raw)
                    inference['error_category'] = error
                    for clean, attempt in zip(inference['attempts'], raw['attempts']):
                        clean['error_category'] = attempt.get('error_category')
                    wave = dict(observation=observation.to_dict(), observation_hash=observation.hash,
                        inference=inference, error_category=error, plan=candidate.to_dict() if candidate else None,
                        planned_ap=candidate.ap_cost if candidate else None)
                    waves.append(wave)
                    if error:
                        require(error in ORDINARY or error == 'request_ceiling', 'unclassified provider failure: '+error)
                        raise ArenaProviderError(error)
                    return parse_turn_plan(canonical_json(candidate.to_dict()), observation)
                provider.create_turn_plan = verified
                if arm == 'bounded_replan':
                    turn = ArenaBoundedReplanController(provider, fallback=False).run_turn(sim).to_dict()
                    require(not turn['fallback_used'], 'fallback contamination')
                    require(len(turn['waves']) == len(waves), 'wave accounting corruption')
                    for clean, actual in zip(waves, turn['waves']):
                        for key in ('invalid_action', 'ap_spent', 'ap_unused', 'stale_suffix_count', 'actions_attempted', 'commands_executed'):
                            if key in actual:
                                clean[key] = actual[key]
                    row['turn'] = {k:v for k,v in turn.items() if k != 'waves'}
                else:
                    observation = build_observation(sim.state)
                    try:
                        plan = verified(observation)
                    except ArenaProviderError as caught:
                        turn = dict(ap_available=case['initial_ap'], ap_spent=0, ap_unused=case['initial_ap'], error_category=caught.category)
                    else:
                        turn = execute_arena_turn(sim.state, plan, execute_command=sim.execute).to_dict()
                        turn['error_category'] = None
                        invalid = turn['invalid_action']
                        waves[0].update({k:turn[k] for k in ('invalid_action', 'ap_spent', 'ap_unused', 'actions_attempted', 'commands_executed')})
                        waves[0]['stale_suffix_count'] = len(plan.actions)-invalid['index'] if invalid else 0
                    row['turn'] = turn
                row['waves'] = waves
                row['metrics'] = arm_metrics(turn, waves, sim, perf_counter()-started)
                require(row['metrics']['provider_attempts'] == report['requests'][arm]-before_arm, 'turn accounting mismatch')
                if turn.get('error_category') == 'request_ceiling':
                    report['status'] = 'ceiling_stop'
                elif turn.get('error_category'):
                    report['status'] = 'complete_with_provider_failures'
            except Exception as error:
                row['hard_stop'] = type(error).__name__ + ': ' + str(error)[:200]
                report['status'] = 'hard_stop'
            finally:
                row['waves'] = waves
                try:
                    require(replay(sim.trace()).trace() == sim.trace(), 'replay mismatch')
                    require(state_hash(replay(sim.trace()).state) == state_hash(sim.state), 'final replay mismatch')
                    require(inventory() == saved['source_files'], 'source drift')
                    row['replay_verified'] = True
                except Exception as error:
                    row['hard_stop'] = type(error).__name__ + ': ' + str(error)[:200]
                    report['status'] = 'hard_stop'
                row.update(actual_attempts=report['requests'][arm]-before_arm, final_state_hash=state_hash(sim.state))
                write(folder/'commands.json', sim.trace()); write(folder/'final-snapshot.json', to_snapshot(sim.state))
                write(folder/'turn.json', row)
                report['runs'].append(row); persist()
            if report['status'] in ('hard_stop', 'ceiling_stop'):
                return report
    # Detect changes to evidence even when the last case made no further request.
    try:
        validate_plan(saved)
    except Exception as error:
        report['status'] = 'hard_stop'; report['integrity_error'] = str(error)
    persist()
    return report


class HistoricalFake(OpenAIArenaTurnProvider):
    """Real static parsing/repair path, overridden transport; never uses a client."""
    def __init__(self, settings, case):
        super().__init__(settings.openai, client=object())
        self.case, self.calls = case, 0

    def request(self, messages, record):
        self.calls += 1
        record['metrics'] = dict(input_tokens=10, cached_input_tokens=0, output_tokens=5,
                                  reasoning_tokens=0, total_tokens=15)
        if self.calls == 1 and self.case.get('historical_plan'):
            return canonical_json(self.case['historical_plan'])
        # Scripted local legal continuation; purely mechanical and never a live fallback.
        from aig.arena.ai.contracts import action_from_dict
        facts = json.loads(messages[0]['content'].split('\n', 1)[1])
        state = simulation_state(ArenaObservation.from_dict(facts))
        catalog = build_observation(state, version='arena-observation-v2').to_dict()['legal_actions']
        actions = (action_from_dict(catalog[0]),) if catalog else ()
        return canonical_json(ArenaTurnPlan(actions).to_dict())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--output', type=Path, required=True)
    for command in ('dry-run', 'run'):
        cmd = sub.add_parser(command)
        cmd.add_argument('--plan', type=Path, required=True); cmd.add_argument('--output', type=Path, required=True)
        if command == 'run':
            cmd.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.output)
    elif args.command == 'dry-run':
        # Defense in depth: any accidental network operation is a hard failure.
        from unittest.mock import patch
        with patch('socket.socket.connect', side_effect=IntegrityError('offline network forbidden')):
            result = run(args.plan, args.output, offline=True,
                         provider_factory=lambda settings, case, arm: HistoricalFake(settings, case))
    else:
        if not args.live:
            parser.error('separate live authorization and --live required')
        result = run(args.plan, args.output, settings=load_settings())
    print(json.dumps({k:v for k,v in result.items() if k != 'runs'}, indent=2))
    if result.get('status') in ('hard_stop', 'ceiling_stop'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
