"""Versioned matched-cohort binding. No inference except explicit `run --live`."""
import argparse
from collections import Counter
import hashlib
import json
import subprocess
import time
from math import ceil
from pathlib import Path

from aig.arena import tactical_literacy as frozen
from aig.arena.ai.ap_budget_prompt import PROMPT_VERSION, PROMPT_HASHES, PROMPTS, OpenAIAPBudgetProvider
from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION
from aig.arena.ai.observation import build_observation
from aig.arena.ai.validation import openai_turn_plan_schema
from aig.arena.benchmark_provider import checked_plan
from aig.arena.commands import ACTION_COSTS
from aig.arena.mechanics_oracle import score
from aig.arena.snapshots import digest, from_snapshot, canonical_json

ROOT = frozen.ROOT
VERSION = 'arena-ap-budget-literacy-v1'
BINDING = ROOT / 'artifacts/arena-ap-budgeting/binding-v1.json'
BASELINE = ROOT / '.local/arena-luna-tactical-literacy-01'
ADDITIONS = frozenset(('backend/aig/arena/ai/sequential_prompt.py',
                      'backend/aig/arena/sequential_literacy.py',
                      'backend/aig/arena/ai/ap_budget_prompt.py',
                      'backend/aig/arena/ap_budget_literacy.py'))
NEW_ADDITIONS = ADDITIONS - frozenset(('backend/aig/arena/ai/sequential_prompt.py',
                                      'backend/aig/arena/sequential_literacy.py'))
V4_BINDING = ROOT / 'artifacts/arena-sequential-planning/binding-v1.json'
V4_RUN = ROOT / '.local/arena-luna-tactical-literacy-prompt-v4-01'
V4_ANALYSIS = ROOT / '.local/arena-luna-tactical-literacy-prompt-v4-01-analysis'
CEILING = 160


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(directory):
    return {p.relative_to(directory).as_posix(): sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}


def verify_suite():
    """Every original source hash is required; only named additive modules allowed."""
    wrapper = read(frozen.SUITE)
    suite = wrapper['payload']
    current = frozen.hashes()
    if (digest(suite) != wrapper['sha256'] or suite['version'] != frozen.SUITE_VERSION
            or set(current) - set(suite['source_hashes']) != ADDITIONS
            or any(current.get(p) != h for p, h in suite['source_hashes'].items())):
        raise ValueError('frozen suite/source drift')
    previous = read(V4_BINDING)
    if (digest(previous['payload']) != previous['sha256'] or
            {p: h for p, h in current.items() if p not in NEW_ADDITIONS} != previous['payload']['source_hashes']):
        raise ValueError('historical V4 source drift')
    for p in suite['probes']:
        if (digest(p['initial_state']) != p['initial_state_hash']
                or build_observation(from_snapshot(p['initial_state'])).hash != p['observation_hash']
                or score(p, p['reference_sequence'])['execution'] != p['expected_mechanics']):
            raise ValueError('frozen fixture/observation/oracle drift')
    return suite


def schedule(suite):
    return [f'{r:02}-{p["id"]}' for r in range(1, suite['repetitions'] + 1) for p in suite['probes']]


def sizes(suite):
    """Existing bytes/4..bytes/3 convention; estimates, not provider tokenization."""
    def measure(text):
        n = len(text.encode())
        return dict(bytes=n, approximate_tokens=[ceil(n / 4), ceil(n / 3)])
    schema = canonical_json(openai_turn_plan_schema())
    return {v: dict(prompt=measure(PROMPTS[v]), contexts={p['id']: measure(
        PROMPTS[v] + 'ArenaObservation:\n' + build_observation(from_snapshot(p['initial_state'])).canonical + schema
    ) for p in suite['probes']}) for v in ('arena-turn-prompt-v1', 'arena-turn-prompt-v4', PROMPT_VERSION)}


def prepare(output=BINDING, baseline=BASELINE):
    suite = verify_suite()
    baseline = Path(baseline)
    if read(baseline / 'suite.json') != read(frozen.SUITE):
        raise ValueError('baseline suite mismatch')
    historic = {Path(p).as_posix(): h for p, h in read(
        ROOT / '.local/arena-luna-tactical-literacy-01-analysis/evidence-hashes.json').items()}
    if inventory(baseline) != historic:
        raise ValueError('baseline evidence drift')
    cohort = [s for s in schedule(suite) if (baseline / s / 'telemetry.json').exists()
              and read(baseline / s / 'telemetry.json')['provider_requests'] > 0]
    if len(cohort) != 122:
        raise ValueError('unexpected baseline coverage')
    validate_v4()
    data = dict(version=VERSION, suite_hash=digest(suite), prompt_version=PROMPT_VERSION,
        prompt_hashes=dict(PROMPT_HASHES), ancestry='arena-turn-prompt-v1',
        source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        source_worktree='dirty; exact source_hashes are authoritative',
        semantic_diff='Replace only the V1 AP sentence with AP_GUIDANCE in ai/ap_budget_prompt.py',
        compatible_controls=['arena-control-full-turn-v1', 'arena-control-full-turn-bounded-replan-v1'],
        v4_binding_hash=sha(V4_BINDING), v4_evidence_hashes=inventory(V4_RUN),
        v4_analysis_hashes=inventory(V4_ANALYSIS),
        control_version='arena-control-full-turn-v1', observation_version=suite['observation_version'],
        plan_schema=PLAN_SCHEMA_VERSION, schema_hash=digest(openai_turn_plan_schema()),
        configuration=suite['configuration'], model_profile=suite['model_profile'],
        source_hashes=frozen.hashes(), baseline=str(baseline.relative_to(ROOT)),
        baseline_hashes=historic, cohort=cohort, excluded_slots=[s for s in schedule(suite) if s not in cohort],
        request_ceiling=CEILING, expected_initial_requests=122, expected_repairs=[7, 18],
        expected_total_requests=[129, 140], measurements=sizes(suite),
        policy='one static repair; no preflight/retry/replan/fallback; independent failures continue')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(dict(payload=data, sha256=digest(data)), stream, indent=2, sort_keys=True)
        stream.write('\n')
    return data


def verify(path=BINDING):
    suite = verify_suite()
    wrapper = read(path)
    b = wrapper['payload']
    if (digest(b) != wrapper['sha256'] or b['version'] != VERSION
            or b['suite_hash'] != digest(suite) or b['source_hashes'] != frozen.hashes()
            or b['prompt_hashes'] != dict(PROMPT_HASHES)
            or b['schema_hash'] != digest(openai_turn_plan_schema())
            or b['configuration'] != suite['configuration'] or b['request_ceiling'] != CEILING
            or b['prompt_version'] != PROMPT_VERSION):
        raise ValueError('binding/source/contract drift')
    previous = read(V4_BINDING)['payload']
    if any(b[key] != previous[key] for key in ('cohort', 'excluded_slots', 'baseline', 'baseline_hashes',
            'configuration', 'model_profile', 'observation_version', 'plan_schema', 'control_version')):
        raise ValueError('matched cohort/protocol drift')
    if inventory(ROOT / b['baseline']) != b['baseline_hashes']:
        raise ValueError('baseline evidence drift')
    validate_v4()
    if (b['v4_binding_hash'] != sha(V4_BINDING) or b['v4_evidence_hashes'] != inventory(V4_RUN)
            or b['v4_analysis_hashes'] != inventory(V4_ANALYSIS)):
        raise ValueError('historical V4 evidence/analysis drift')
    return b, suite


def run(output, *, binding=BINDING, live=False, provider=None):
    b, suite = verify(binding)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    frozen.write(output / 'binding.json', read(binding))
    frozen.write(output / 'suite.json', read(frozen.SUITE))
    frozen.write(output / 'manifest.json', dict(binding_hash=digest(b), mode='live' if live else 'offline-scripted',
        prompt_version=PROMPT_VERSION, configuration=b['configuration'], cohort=b['cohort'], request_ceiling=CEILING))
    if live and provider is None:
        from aig.settings import load_settings
        from aig.ai.model_profiles import apply_model_profile
        settings = apply_model_profile(load_settings(), 'openai', b['model_profile'])
        provider = OpenAIAPBudgetProvider(settings.openai, prompt_version=PROMPT_VERSION)
    started = time.perf_counter()
    rows, ledger = [], []
    probes = {p['id']: p for p in suite['probes']}
    integrity = None

    def reserve():
        nonlocal integrity
        if frozen.hashes() != b['source_hashes'] or read(binding) != read(output / 'binding.json'):
            integrity = 'source/binding drift before transport'
        elif (provider.name != 'openai' or provider.prompt_version != PROMPT_VERSION
              or provider.system_prompt != PROMPTS[PROMPT_VERSION] or provider.repair is not True
              or provider.configuration() != b['configuration']):
            integrity = 'provider contract drift before transport'
        elif len(ledger) >= CEILING:
            integrity = 'hard request ceiling reached'
        if integrity:
            raise RuntimeError(integrity)
        ledger.append(dict(number=len(ledger) + 1, trial=trial))
        frozen.write(output / 'request-ledger.json', ledger)

    if provider is not None:
        provider.before_request = reserve
    frozen.write(output / 'request-ledger.json', ledger)
    try:
        for trial in b['cohort']:
            p = probes[trial[3:]]
            d = output / trial
            d.mkdir()
            observation = build_observation(from_snapshot(p['initial_state']))
            frozen.write(d / 'starting-state.json', p['initial_state'])
            frozen.write(d / 'observation.json', observation.to_dict())
            before = len(ledger)
            if provider is None:
                actions = p['reference_sequence']
                telemetry = dict(offline_scripted=True, provider_requests=0, repair_requests=0, attempts=[])
            else:
                plan, telemetry = checked_plan(provider, 'openai', observation)
                actions = plan.to_dict()['actions'] if plan is not None else None
                outputs = []
                for attempt in (provider.last_trace or {}).get('attempts', []):
                    try:
                        parsed = ArenaTurnPlan.from_dict(json.loads(attempt.get('raw_content') or 'null')).to_dict()
                    except (ValueError, TypeError, KeyError):
                        parsed = None
                    outputs.append(dict(parsed_output=parsed, error_category=attempt.get('error_category')))
                frozen.write(d / 'attempt-outputs.json', outputs)
                if telemetry['provider_requests'] != len(ledger) - before:
                    integrity = 'request accounting mismatch'
            evaluation = score(p, actions) if actions is not None else dict(
                classification='static invalidity' if telemetry['error_category'] in
                {'malformed_json', 'schema_validation', 'ap_budget', 'invalid_reference', 'invalid_ability', 'repair_failed'}
                else 'provider failure', objective_satisfied=None, information_class=p['information_class'])
            frozen.write(d / 'telemetry.json', telemetry)
            frozen.write(d / 'parsed-plan.json', dict(schema_version=PLAN_SCHEMA_VERSION, actions=actions))
            frozen.write(d / 'evaluation.json', evaluation)
            if 'execution' in evaluation:
                ex = evaluation['execution']
                frozen.write(d / 'execution.json', ex)
                frozen.write(d / 'replay-verification.json', dict(verified=ex['replay_verified']))
                if not ex['replay_verified']:
                    integrity = 'replay mismatch'
            rows.append(dict(probe=p['id'], repetition=int(trial[:2]), category=p['category'],
                classification=evaluation['classification'], objective_satisfied=evaluation['objective_satisfied'],
                scorable_opportunity=bool(p['acceptable_reference_sequences'])))
            frozen.write(output / 'results.json', rows)
            frozen.write(output / 'summary.json', frozen.summarize(rows, len(b['cohort']), len(ledger)))
            # Recognized provider failures remain failed decisions and continue.
            if integrity or telemetry.get('error_category') in ('provider_mismatch', 'provider_exception'):
                raise RuntimeError(integrity or 'unclassified provider/integrity failure')
        verify(binding)
    except BaseException as error:
        frozen.write(output / 'stopped.json', dict(error_type=type(error).__name__, reason=integrity,
            completed=len(rows), requests=len(ledger)))
        raise
    finally:
        frozen.write(output / 'timing.json', dict(backend_elapsed_seconds=time.perf_counter() - started,
            scope='after manifest creation through decisions and final verification; excludes startup'))
        frozen.write(output / 'summary.json', frozen.summarize(rows, len(b['cohort']), len(ledger)))
        frozen.write(output / 'evidence-hashes.json', {k: v for k, v in inventory(output).items() if k != 'evidence-hashes.json'})
    return rows


def analyze_arm(root, cohort, suite, *, scripted=False):
    root = Path(root)
    probes = {p['id']: p for p in suite['probes']}
    counts = Counter()
    failures, rows, errors, categories = [], [], Counter(), {}
    ledger = read(root / 'request-ledger.json')
    reserved = Counter(r['trial'] for r in ledger)
    if [r['number'] for r in ledger] != list(range(1, len(ledger) + 1)):
        raise ValueError('ledger sequence mismatch')
    for slot in cohort:
        d = root / slot
        if not (d / 'telemetry.json').exists():
            counts['unrequested_slots'] += 1
            continue
        p = probes[slot[3:]]
        t = read(d / 'telemetry.json')
        if t.get('offline_scripted') and not scripted:
            raise ValueError('scripted evidence cannot be a live comparison')
        if t.get('fallback_used') or t['provider_requests'] != reserved[slot] or len(t['attempts']) != reserved[slot]:
            raise ValueError('provenance/accounting mismatch')
        if not scripted and not t['provider_requests']:
            counts['unrequested_slots'] += 1
            continue
        if (read(d / 'starting-state.json') != p['initial_state']
                or digest(read(d / 'observation.json')) != p['observation_hash']):
            raise ValueError('state/observation mismatch')
        counts['requested_decisions'] += 1
        counts['backend_decision_seconds'] += t.get('wall_clock_seconds') or 0
        counts['requests'] += t['provider_requests']
        counts['repairs'] += t['repair_requests']
        first_error = t['attempts'][0]['error_category'] if t['attempts'] else None
        if first_error:
            errors[first_error] += 1
        else:
            counts['first_response_valid'] += 1
        for a in t['attempts']:
            counts['provider_seconds'] += a['wall_clock_seconds'] or 0
            for key in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens'):
                if a['metrics'].get(key) is None:
                    counts['missing_' + key] += 1
                else:
                    counts[key] += a['metrics'][key]
        ev = read(d / 'evaluation.json')
        c = categories.setdefault(p['category'], Counter())
        c[ev['classification']] += 1
        if p['acceptable_reference_sequences']:
            c['objective_denominator'] += 1
            c['objective_satisfied'] += ev['objective_satisfied'] is True
        actions = read(d / 'parsed-plan.json')['actions']
        row = dict(slot=slot, actions=None, planned_ap=0, executed_ap=0, clean_unused_ap=None)
        if actions is None:
            counts['exhausted_repairs'] += bool(t['repair_requests']) and ev['classification'] == 'static invalidity'
            counts['static_failure_unused_ap'] += p['ap']
        if actions is not None:
            counts['accepted_decisions'] += 1
            if ev != score(p, actions) or not ev['execution']['replay_verified']:
                raise ValueError('score/replay mismatch')
            ex = ev['execution']
            planned = sum(ACTION_COSTS[a['type']] for a in actions)
            row.update(actions=len(actions), planned_ap=planned, executed_ap=ex['ap_used'],
                clean_unused_ap=p['ap'] - ex['ap_used'] if not ex['failure'] and not ex['terminal'] else None)
            counts['executed_actions'] += len(ex['steps'])
            counts['actions'] += len(actions)
            counts['planned_ap'] += planned
            counts['executed_ap'] += ex['ap_used']
            counts['one_action_plans'] += len(actions) == 1
            counts['zero_action_plans'] += len(actions) == 0
            counts['short_plans'] += planned < p['ap']
            counts['clean_unused_ap'] += row['clean_unused_ap'] or 0
            counts['terminal_suffix_actions'] += ex['ignored_terminal_suffix']
            failure = ex['failure']
            if failure:
                counts['truncation_unused_ap'] += p['ap'] - ex['ap_used']
                counts['all_later_action_failures'] += failure['index'] > 0
                counts['range_failures'] += 'range' in failure['reason'].lower()
                counts['shield_bash_range_failures'] += ('range' in failure['reason'].lower() and
                    any(a['type'] == 'shield_bash' for a in actions[:failure['index']]))
                counts['execution_invalid_plans'] += 1
                counts['ap_before_truncation'] += ex['ap_used']
                target = failure['action'].get('target_id')
                stale = (failure['action']['type'] in ('attack', 'snipe', 'shield_bash') and any(
                    e['id'] == target and e['guaranteed_down'] for s in ex['steps'] for e in s['affected']))
                los = 'line of sight' in failure['reason'].lower()
                counts['stale_downed_plans'] += stale
                counts['blocked_los_plans'] += los
                counts['other_sequence_errors'] += failure['index'] > 0 and not stale and not los
                failures.append(dict(slot=slot, **failure, ap_before_truncation=ex['ap_used']))
        rows.append(row)
    n, accepted = counts['requested_decisions'], counts['accepted_decisions']
    ratios = dict(first_response_valid_rate=counts['first_response_valid'] / n if n else None,
        repair_rate=counts['repairs'] / n if n else None,
        requests_per_accepted_decision=counts['requests'] / accepted if accepted else None)
    for key in ('actions', 'planned_ap', 'executed_ap', 'one_action_plans', 'zero_action_plans', 'short_plans'):
        ratios[key + '_per_accepted_decision'] = counts[key] / accepted if accepted else None
    ratios['executed_actions_per_intended_decision'] = counts['executed_actions'] / len(cohort)
    ratios['executed_ap_per_intended_decision'] = counts['executed_ap'] / len(cohort)
    counts['backend_elapsed_seconds'] = (read(root / 'timing.json')['backend_elapsed_seconds']
        if (root / 'timing.json').exists() else
        (root / 'summary.json').stat().st_mtime - (root / 'manifest.json').stat().st_mtime)
    return dict(counts=dict(counts), rates=ratios, first_response_errors=dict(errors),
        categories={k: dict(v) for k, v in categories.items()}, failures=failures, decisions=rows)


def compare(candidate, output, *, binding=BINDING, scripted=False):
    b, suite = verify(binding)
    candidate = Path(candidate)
    if read(candidate / 'binding.json') != read(binding):
        raise ValueError('candidate binding mismatch')
    manifest = read(candidate / 'manifest.json')
    if not scripted and manifest['mode'] != 'live':
        raise ValueError('offline run cannot be live comparison evidence')
    if (manifest['binding_hash'] != digest(b) or manifest['prompt_version'] != PROMPT_VERSION
            or manifest['configuration'] != b['configuration'] or manifest['cohort'] != b['cohort']
            or read(candidate / 'suite.json') != read(frozen.SUITE)):
        raise ValueError('candidate manifest/suite mismatch')
    if any((candidate / slot).exists() for slot in b['excluded_slots']):
        raise ValueError('excluded cohort slot present')
    recorded = read(candidate / 'evidence-hashes.json')
    if recorded != {k: v for k, v in inventory(candidate).items() if k != 'evidence-hashes.json'}:
        raise ValueError('candidate evidence drift')
    a = analyze_arm(ROOT / b['baseline'], b['cohort'], suite)
    z = analyze_arm(candidate, b['cohort'], suite, scripted=scripted)
    result = dict(version=VERSION, diagnostic_only=scripted, matched_intended_decisions=len(b['cohort']),
        excluded_slots=b['excluded_slots'], baseline=a, candidate=z, measurements=b['measurements'],
        repair_requests_avoided=a['counts'].get('repairs', 0) - z['counts'].get('repairs', 0),
        count_deltas={k: z['counts'].get(k, 0) - a['counts'].get(k, 0) for k in set(a['counts']) | set(z['counts'])},
        ap_overbudget_reduction=a['first_response_errors'].get('ap_budget', 0) - z['first_response_errors'].get('ap_budget', 0),
        complete_matched_coverage=z['counts'].get('requested_decisions') == len(b['cohort']))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    frozen.write(output / 'comparison.json', result)
    lines = ['# AP budgeting matched comparison', '',
        'Offline scripted plumbing check; NOT model evidence.' if scripted else 'Frozen 122-slot intended cohort; failures remain visible.', '',
        '| Metric | V1 | V5 |', '|---|---:|---:|']
    for section in ('counts', 'rates', 'first_response_errors'):
        for key in sorted(set(a[section]) | set(z[section])):
            lines.append(f'| {key} | {a[section].get(key, 0)} | {z[section].get(key, 0)} |')
    lines += ['', 'Full category preservation, per-decision AP/shape, indexed failures, prompt/context size and coverage are in comparison.json.',
        'Missing candidate slots are unrequested, not successful decisions. Incomplete coverage cannot support a full matched improvement conclusion.',
        'No tactical or arithmetic belief is inferred from a legal alternative; Fireball remains unresolved without selections.']
    (output / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    write_three_way(result, suite, b, output, scripted=scripted)
    return result



def validate_v4():
    """Verify preserved V4 provenance without weakening its historical source guard."""
    wrapper = read(V4_BINDING)
    b = wrapper['payload']
    manifest = read(V4_RUN / 'manifest.json')
    if (read(V4_RUN / 'binding.json') != wrapper or manifest['mode'] != 'live'
            or manifest['binding_hash'] != digest(b) or manifest['cohort'] != b['cohort']
            or manifest['configuration'] != b['configuration']
            or manifest['prompt_version'] != 'arena-turn-prompt-v4'
            or read(V4_RUN / 'suite.json') != read(frozen.SUITE)
            or read(V4_RUN / 'evidence-hashes.json') != {
                k: v for k, v in inventory(V4_RUN).items() if k != 'evidence-hashes.json'}):
        raise ValueError('historical V4 provenance drift')


def write_three_way(pair, suite, binding, output, *, scripted=False):
    v4 = analyze_arm(V4_RUN, binding['cohort'], suite)
    arms = {'V1': pair['baseline'], 'V4': v4, 'V5': pair['candidate']}
    delta = binding['measurements'][PROMPT_VERSION]['prompt']['bytes'] - binding['measurements']['arena-turn-prompt-v1']['prompt']['bytes']
    overhead = [ceil(delta / 4), ceil(delta / 3)]
    avoided = pair['repair_requests_avoided']
    result = dict(version=VERSION, diagnostic_only=scripted, arms=arms,
        complete_matched_coverage=pair['complete_matched_coverage'],
        measurements=binding['measurements'], extra_prompt_tokens_approximate=overhead,
        repairs_avoided=avoided,
        repairs_avoided_per_extra_prompt_token_approximate=[avoided / overhead[1], avoided / overhead[0]],
        extra_prompt_input_across_candidate_requests_approximate=[
            t * pair['candidate']['counts'].get('requests', 0) for t in overhead],
        token_change=pair['candidate']['counts'].get('total_tokens', 0) - pair['baseline']['counts'].get('total_tokens', 0),
        caveat='Raw ingredients, not a universal efficiency score. Token estimates are bytes/4..bytes/3, not measured prompt tokens. Missing usage stays explicit. Historical elapsed uses file timestamps; V5 uses a monotonic timer.')
    frozen.write(output / 'three-way.json', result)
    lines = ['# V1 / V4 / V5 AP-only comparison', '',
        'SCRIPTED PLUMBING ONLY; V5 IS NOT MODEL EVIDENCE.' if scripted else
        'Frozen matched cohort. Incomplete coverage cannot support an improvement claim.', '',
        '| Metric | V1 | V4 | V5 |', '|---|---:|---:|---:|']
    for section, key in [('first_response_errors', 'ap_budget'), ('counts', 'first_response_valid'),
            ('counts', 'repairs'), ('counts', 'exhausted_repairs'),
            ('rates', 'requests_per_accepted_decision'), ('rates', 'actions_per_accepted_decision'),
            ('rates', 'one_action_plans_per_accepted_decision'), ('rates', 'zero_action_plans_per_accepted_decision'),
            ('rates', 'planned_ap_per_accepted_decision'), ('rates', 'executed_ap_per_accepted_decision'),
            ('counts', 'short_plans'), ('counts', 'clean_unused_ap'), ('counts', 'truncation_unused_ap'),
            ('rates', 'executed_actions_per_intended_decision'), ('counts', 'stale_downed_plans'),
            ('counts', 'blocked_los_plans'), ('counts', 'range_failures'),
            ('counts', 'shield_bash_range_failures'), ('counts', 'all_later_action_failures'),
            ('counts', 'execution_invalid_plans'), ('counts', 'requests'),
            ('counts', 'input_tokens'), ('counts', 'cached_input_tokens'), ('counts', 'output_tokens'),
            ('counts', 'total_tokens'), ('counts', 'provider_seconds'), ('counts', 'backend_elapsed_seconds')]:
        values = [str(arm[section].get(key, 0)) for arm in arms.values()]
        lines.append('| ' + key + ' | ' + ' | '.join(values) + ' |')
    for category in sorted(set().union(*(a['categories'] for a in arms.values()))):
        values = []
        for arm in arms.values():
            c = arm['categories'].get(category, {})
            values.append(str(c.get('objective_satisfied', 0)) + '/' + str(c.get('objective_denominator', 0)))
        lines.append('| Objective ' + category + ' | ' + ' | '.join(values) + ' |')
    lines += ['', 'All indexed failures, category classifications, per-slot plans/AP, usage-missing counts and cost ingredients are in three-way.json.',
        'Judge AP improvements alongside preserved plan shape and objectives. Reduced stale-state failures are not required.',
        'Reject a candidate with little AP improvement, materially shorter plans/lower executed AP, objective regressions, or excessive token overhead. No automatic promotion.']
    (output / 'three-way.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare', 'verify', 'dry-run', 'run', 'compare'])
    p.add_argument('--binding', type=Path, default=BINDING)
    p.add_argument('--output', type=Path)
    p.add_argument('--candidate', type=Path)
    p.add_argument('--prompt', choices=[PROMPT_VERSION], default=PROMPT_VERSION)
    p.add_argument('--suite', choices=[frozen.SUITE_VERSION], default=frozen.SUITE_VERSION)
    p.add_argument('--provider', choices=['openai'], default='openai')
    p.add_argument('--live', action='store_true')
    p.add_argument('--scripted', action='store_true')
    args = p.parse_args()
    if args.live != (args.command == 'run'):
        p.error('only run requires --live; other commands forbid it')
    if args.command == 'prepare':
        prepare(args.binding)
    elif args.command == 'verify':
        b, _ = verify(args.binding)
        print(json.dumps(dict(verified=True, matched=len(b['cohort']), prompt=PROMPT_VERSION)))
    else:
        if not args.output:
            p.error('--output required')
        if args.command == 'compare':
            if not args.candidate:
                p.error('--candidate required')
            compare(args.candidate, args.output, binding=args.binding, scripted=args.scripted)
        else:
            run(args.output, binding=args.binding, live=args.live)


if __name__ == '__main__':
    main()
