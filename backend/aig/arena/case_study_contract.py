"""Create-only case-study freeze. This module never constructs a model client."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import importlib.metadata

from aig.ai.model_profiles import LUNA_CONFIGS
from aig.arena.ai import benchmark_candidate as candidate
from aig.arena.ai.candidate_control import CONTROL_VERSIONS, STOP_REASONS
from aig.arena.ai.candidate_repair import NEW, POLICY, CONTEXT_SCHEMA
from aig.arena.ai.heuristic_v2 import HEURISTIC_VERSION
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import digest
from aig.arena.state import RULES_VERSION, SCENARIO_VERSION

ROOT = Path(__file__).resolve().parents[3]
ID = 'arena-case-study-benchmark-v1'
DEFAULT_CONTRACT = Path(__file__).parent/'benchmark_artifacts'/f'{ID}.json'
ARMS = ('strict', 'bounded', 'stepwise')
LIMITS = dict(player_turns=200, full_rounds=100,
    per_turn=dict(strict=2, bounded=4, stepwise=10),
    per_match=dict(strict=50, bounded=80, stepwise=140),
    per_batch_control=dict(strict=300, bounded=500, stepwise=900),
    per_control=dict(strict=3000, bounded=5000, stepwise=9000),
    global_requests=15000, batch_requests=1700, batch_slots=10,
    bounded_replans_per_turn=1, bounded_replans_per_match=100,
    stepwise_decisions_per_turn=5, provider_timeout_seconds=20)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    files = list((ROOT/'backend').rglob('*.py'))
    files += list((ROOT/'backend').rglob('*.json'))
    files += list((ROOT/'tests').glob('*case_study*.py'))
    files += [ROOT/'docs/arena-case-study-benchmark.md', ROOT/'pyproject.toml',ROOT/'requirements-case-study.txt']
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)
            if p != DEFAULT_CONTRACT and '__pycache__' not in p.parts and p.is_file()}


def schedule(initial):
    slots, order = [], []
    for i in range(100):
        side = 'red' if i % 2 == 0 else 'blue'
        slot = dict(id=f'MATCH-{i+1:03d}', batch=i//10+1, luna_side=side,
            heuristic_side='blue' if side == 'red' else 'red',
            scenario=SCENARIO_VERSION, seed=None, initial_state_hash=digest(initial))
        slots.append(slot)
        # Balanced Latin rotations: each arm occupies each temporal position 33/34 times.
        rotation = ARMS[i % 3:] + ARMS[:i % 3]
        for arm in rotation:
            order.append(dict(slot, arm=arm, match_id=f'{slot["id"]}-{arm}', ordinal=len(order)+1))
    return slots, order


def budget():
    """Planning ranges, not forecasts. Full games have no candidate-length evidence."""
    scenarios = dict(low=(5, .05, .10, 2.5, 1800, 50, 1.5),
                     central=(10, .10, .625, 2.89, 2300, 100, 2.5),
                     high=(20, .20, .80, 4.0, 3500, 180, 5.0))
    result = {}
    for name, (turns, repair, replan, decisions, inp, out, seconds) in scenarios.items():
        rates = dict(strict=1+repair, bounded=(1+replan)*(1+repair), stepwise=decisions*(1+repair))
        rows = {}
        for arm, rate in rates.items():
            requests = turns*rate*100
            rows[arm] = dict(luna_turns_per_match=turns, repair_rate=repair,
                replan_rate=replan if arm == 'bounded' else 0,
                requests_per_turn=rate, requests_per_match=requests/100, requests=requests,
                input_tokens=requests*inp, output_tokens=requests*out,
                total_tokens=requests*(inp+out), provider_seconds=requests*seconds,
                provider_hours=requests*seconds/3600)
        result[name] = dict(arms=rows, total={k:sum(r[k] for r in rows.values()) for k in
            ('requests','input_tokens','output_tokens','total_tokens','provider_seconds','provider_hours')})
    return result


def runtime():
    return dict(python=platform.python_version(), packages={name:importlib.metadata.version(name)
        for name in ('openai','matplotlib','numpy','contourpy','cycler','fonttools','kiwisolver',
                     'packaging','pillow','pyparsing','python-dateutil','six')})


def freeze(path=DEFAULT_CONTRACT):
    initial = ArenaSimulation().initial_snapshot
    slots, order = schedule(initial)
    full, step = candidate.candidate_schema(openai=True), candidate.candidate_schema(step=True, openai=True)
    step['properties']['actions']['maxItems'] = full['properties']['actions']['maxItems']
    if full != step:
        raise ValueError('candidate semantic schema divergence')
    payload = dict(id=ID, status='FROZEN_NOT_AUTHORIZED', source_revision=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), source_hashes=sources(), runtime=runtime(),
        rules=RULES_VERSION, scenario=SCENARIO_VERSION, initial_state=initial,
        initial_state_hash=digest(initial), slots=slots, schedule=order, schedule_hash=digest(order),
        model='gpt-5.6-luna', profile='luna-config-v1', configuration=dict(LUNA_CONFIGS['luna-config-v1']),
        policy=candidate.POLICY_VERSION, policy_hash=digest(candidate.POLICY_CORE),
        prompts=dict(candidate.PROMPTS), prompt_hashes=dict(candidate.PROMPT_HASHES),
        observation=candidate.OBSERVATION_VERSION, schema=candidate.SCHEMA_VERSION,
        semantic_schema_alias='arena-action-schema-v2',
        schemas={a:candidate.candidate_schema(step=a=='stepwise',openai=True) for a in ARMS},
        repair=NEW, repair_policy=POLICY, repair_policy_hash=digest(POLICY),
        repair_context_hash=digest(CONTEXT_SCHEMA), controls=CONTROL_VERSIONS,
        heuristic=HEURISTIC_VERSION, heuristic_hash=sha(ROOT/'backend/aig/arena/ai/heuristic_v2.py'),
        heuristic_dependency_hash=sha(ROOT/'backend/aig/arena/ai/heuristic.py'),
        stop_reasons=list(STOP_REASONS), end_turn='zero AP; no reason; last; intentional; never triggers replan',
        failure_policy='PROVIDER_FORFEIT: Luna loss, heuristic win; preserve engine state; no fallback/retry',
        budget_policy='per-match REQUEST_LIMIT nonwin/censored; cumulative budget denial stops study; no winner',
        turn_policy='TURN_LIMIT: no winner after 200 started player turns or 100 completed rounds',
        limits=LIMITS, metric_schema='arena-case-study-metrics-v1',
        artifact_schema='arena-case-study-artifacts-v1', analysis_schema='arena-case-study-analysis-v1',
        statistical_plan=dict(win_interval='Wilson 95%', primary_denominator='all completed scheduled slots, limits nonwins',
            comparisons=['bounded-strict','stepwise-bounded'],
            paired_test='exact two-sided McNemar on win vs nonwin, within matched slots; Holm across two comparisons',
            effect_ci='10000 side-stratified matched-slot percentile bootstrap draws; seed 5914',
            missing='no confirmatory inference before all 300 slots; interrupted/integrity cases are not outcomes',
            scope='conditional on canonical opening and service period; no scenario-population inference'),
        estimates=budget(), pricing=None, reference_cohort='not scheduled; existing V2/V2 canonical reference sufficient',
        requested_first_authorization=dict(batches=[1], matches=30, requests=1700), preflight_requests=0)
    wrapper = dict(payload=payload, sha256=digest(payload))
    with Path(path).open('x',encoding='utf-8') as file:
        json.dump(wrapper,file,indent=2); file.write('\n')
    return wrapper


def verify(path=DEFAULT_CONTRACT):
    wrapper = read(path)
    p = wrapper['payload']
    if digest(p) != wrapper['sha256'] or p['id'] != ID:
        raise ValueError('contract integrity failure')
    if sources() != p['source_hashes'] or runtime() != p['runtime']:
        raise ValueError('frozen source/runtime drift; create a new reviewed version, never refreeze v1')
    slots, order = schedule(ArenaSimulation().initial_snapshot)
    if slots != p['slots'] or order != p['schedule']:
        raise ValueError('schedule drift')
    return wrapper
