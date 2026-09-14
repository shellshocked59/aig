"""Offline historical trigger audit. No provider construction or inference.

Run from the checkout with .venv/Scripts/python.exe -B scripts/arena-bounded-replan-audit.py.
Writes only docs/arena-bounded-replan-audit.json; historical inputs are read-only.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.observation import ArenaObservation, simulation_state
from aig.arena.ai.validation import parse_turn_plan
from aig.arena.snapshots import canonical_json

INPUTS = {}


def read(path):
    raw = path.read_bytes()
    INPUTS[path.relative_to(ROOT).as_posix()] = hashlib.sha256(raw).hexdigest()
    return raw.decode('utf-8-sig')


def rows(path):
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def audit(label, root, provider):
    calls, plans, failures = [], [], []
    versions = set()
    for path in sorted((ROOT / root).rglob('plans.jsonl')):
        manifest = json.loads(read(path.with_name('manifest.json')))
        assert manifest['benchmarkVersion'] == 'arena-benchmark-v1'
        assert manifest.get('controlMode', 'full-turn') == 'full-turn'
        saved = rows(path)
        observations = rows(path.with_name('observations.jsonl'))
        calls.extend(r for r in rows(path.with_name('inference.jsonl'))
                     if r['requested_provider'] == provider)
        for row in saved:
            if row['provider_type'] != provider:
                continue
            obs = ArenaObservation.from_dict(observations[row['inference_index']]['observation'])
            plan = parse_turn_plan(canonical_json(row['plan']), obs)
            assert isinstance(plan, ArenaTurnPlan)
            result = execute_arena_turn(simulation_state(obs), plan).to_dict()
            for key in result:
                assert result[key] == row[key], (str(path), key)
            plans.append(row)
            versions.add((row['prompt_version'], obs.version))
            if row['invalid_action']:
                invalid = row['invalid_action']
                attempt = row['actions_attempted'][invalid['index']]
                assert not attempt['executed'] and attempt['ap_before'] == row['ap_unused']
                failures.append(dict(path=path.relative_to(ROOT).as_posix(),
                    turn=row['turn'], player_id=row['player_id'],
                    index=invalid['index'], reason=invalid['reason'],
                    ap_remaining=attempt['ap_before'], ap_spent=row['ap_spent'],
                    eligible=attempt['ap_before'] > 0 and row['terminal_result'] is None))
    eligible = [f for f in failures if f['eligible']]
    attempted = len(calls)
    requests = sum(c['provider_requests'] for c in calls)
    return dict(label=label, root=root, provider=provider, contracts=sorted(versions),
        attempted_model_turns=attempted, accepted_model_turns=len(plans),
        provider_failed_turns=sum(not c['success'] for c in calls),
        provider_failure_categories=dict(Counter(c['error_category'] for c in calls if not c['success'])),
        static_repair_requests=sum(c['repair_requests'] for c in calls), actual_requests=requests,
        accepted_without_execution_invalidity=len(plans)-len(failures),
        execution_invalid_turns=len(failures), eligible_replans=len(eligible),
        invalid_index_distribution=dict(sorted(Counter(f['index'] for f in failures).items())),
        invalid_ap_remaining_distribution=dict(sorted(Counter(f['ap_remaining'] for f in failures).items())),
        invalid_reason_distribution=dict(Counter(f['reason'] for f in failures)),
        ap_at_eligible_boundaries=sum(f['ap_remaining'] for f in eligible),
        ap_executed=sum(p['ap_spent'] for p in plans),
        observed_calls_per_attempted_turn=requests/attempted if attempted else None,
        projected_calls_no_replan_repairs=(requests+len(eligible))/attempted if attempted else None,
        projected_calls_all_replans_repaired=(requests+2*len(eligible))/attempted if attempted else None,
        failures=failures)


def main():
    cohorts = []
    for name, provider in [('luna', 'openai'), ('qwen', 'ollama')]:
        cohorts.append(audit(name+' V1 full matches', '.local/arena-phase5-fullmatches-20260913-01', provider))
        for phase, suffix in [('6b', 'v2'), ('7a', 'observation-v2')]:
            cohorts.append(audit(name+' Phase '+phase+' probes',
                f'.local/arena-phase{phase}-{name}-{suffix}-probes-20260913-01', provider))
    cohorts.append(audit('luna V1 probes', '.local/arena-phase5-continuation-20260913/luna-all', 'openai'))
    stepwise = []
    for name in ('luna', 'qwen'):
        root = ROOT / f'.local/arena-phase7c-{name}-stepwise-probes-20260913-01'
        turns = [json.loads(read(p)) for p in sorted(root.rglob('turn.json'))]
        stepwise.append(dict(provider=name, root=root.relative_to(ROOT).as_posix(),
            turns=len(turns), requests=sum(t['provider_requests'] for t in turns),
            repairs=sum(t['repair_requests'] for t in turns),
            ap_executed=sum(t['ap_executed'] for t in turns),
            requests_per_turn=sum(t['provider_requests'] for t in turns)/len(turns)))
    for path, expected in INPUTS.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
    output = dict(method='Frozen-turn local counterfactual request counts; no replacement responses simulated.',
        excludes='Preflights, heuristic turns, unstarted turns. Cohorts are separate, never pooled.',
        verification='Every accepted model plan statically reparsed and execution result reproduced from saved observation; input hashes unchanged.',
        cohorts=cohorts, stepwise_comparison=stepwise, input_sha256=INPUTS)
    (ROOT/'docs/arena-bounded-replan-audit.json').write_text(json.dumps(output, indent=2)+'\n', encoding='utf-8')
    print(json.dumps([{k:v for k,v in c.items() if k != 'failures'} for c in cohorts], indent=2))
    print(json.dumps(stepwise, indent=2))


if __name__ == '__main__':
    main()
