"""Offline-only preparation and evaluation for a proposed focused candidate check.

No live runner or provider construction is exposed by this module.
"""
import json
from pathlib import Path

from aig.arena.ai.benchmark_candidate import (
    candidate_observation, PROMPTS, PROMPT_HASHES, POLICY_VERSION, SCHEMA_VERSION,
    OBSERVATION_VERSION, TURN_PROMPT_VERSION, STEP_PROMPT_VERSION,
)
from aig.arena.ai.candidate_control import CONTROL_VERSIONS
from aig.arena.mechanics_oracle import score
from aig.arena.snapshots import digest, from_snapshot
from aig.arena.tactical_literacy import hashes

DIRECTORY = Path(__file__).parent/'benchmark_artifacts'
SOURCE = DIRECTORY/'arena-tactical-literacy-v1.json'
TARGET = DIRECTORY/'arena-candidate-focused-validation-v1.json'
PROBE_IDS = ('AP-001', 'AP-003', 'AP-005', 'MULTI-001', 'DOWNED-003',
             'POSITION-002', 'CORE-002', 'FIREBALL-003')


def prepare():
    """Bind eight existing snapshots, one repetition, three controls; zero requests."""
    original = json.loads(SOURCE.read_text(encoding='utf-8'))
    suite = original['payload']
    if digest(suite) != original['sha256']:
        raise ValueError('historical fixture integrity failure')
    probes = {p['id']: p for p in suite['probes']}
    schedule = []
    for probe_id in PROBE_IDS:
        p = probes[probe_id]
        state = from_snapshot(p['initial_state'])
        for mode in CONTROL_VERSIONS:
            ceiling = dict(strict=2, bounded=4, stepwise=2*p['ap'])[mode]
            schedule.append(dict(trial=f'{probe_id}-{mode}', probe=probe_id,
                control_mode=mode, control_version=CONTROL_VERSIONS[mode],
                prompt_version=STEP_PROMPT_VERSION if mode == 'stepwise' else TURN_PROMPT_VERSION,
                initial_state_hash=p['initial_state_hash'], observation_hash=candidate_observation(state).hash,
                ap_available=p['ap'], request_ceiling=ceiling))
    return dict(version='arena-candidate-focused-validation-v1', status='prepared-not-authorized',
        source_suite_sha256=original['sha256'], policy_version=POLICY_VERSION,
        source_hashes=hashes(),
        prompt_hashes=dict(PROMPT_HASHES), prompt_sizes={v:dict(characters=len(p), utf8_bytes=len(p.encode())) for v,p in PROMPTS.items()},
        schema_version=SCHEMA_VERSION, observation_version=OBSERVATION_VERSION,
        model_profile=suite['model_profile'], configuration=suite['configuration'],
        repetitions=1, trial_count=len(schedule), preflight_requests=0,
        hard_request_ceiling=sum(t['request_ceiling'] for t in schedule),
        repair_policy='at most one static repair per decision; no transport retry; no fallback',
        recovery_policy='bounded: at most one replan, only after execution invalidity',
        schedule=schedule, probes=[probes[k] for k in PROBE_IDS],
        review_questions=[
            'AP compliance: first-response validity and overbudget/repair counts, split by available AP.',
            'Intentional stops: frequency and leftover AP, inspect board outcomes; declaration is not proof of good play.',
            'Plan shape: gameplay actions per plan, one-action frequency, and witnessed objectives; never count EndTurn as gameplay.',
            'Policy comparability: paired starting states and final objectives, including productive multi-action and position cases.',
        ],
        interpretation='Descriptive small-sample screening, not a significance test or proof of V5 equivalence. No opaque score.',
        live_requirements='Separate authorization, new output directory, frozen source bindings and persisted pre-send request ledger; no substitution or retry.')


def verify_preparation():
    wrapper = json.loads(TARGET.read_text(encoding='utf-8'))
    if digest(wrapper['payload']) != wrapper['sha256'] or wrapper['payload'] != prepare():
        raise ValueError('candidate preparation drift')
    return wrapper['payload']


def evaluate_candidate_trace(probe, trace):
    """Use the historical outcome predicate on committed gameplay, excluding stop."""
    actions = [a['action'] for w in trace['waves'] for a in w['actions_attempted']
               if a['executed'] and a['action']['type'] != 'end_turn']
    result = score(probe, actions)
    result.update(stop_reason=trace['stop_reason'], ap_remaining=trace['ap_remaining'],
        explicit_end_turn=trace['explicit_end_turn'], execution_invalidities=trace['execution_invalidities'],
        gameplay_actions_executed=len(actions),
        planned_gameplay_actions=[sum(a['type'] != 'end_turn' for a in w['plan']['actions'])
                                  for w in trace['waves'] if w['plan']])
    return result


if __name__ == '__main__':
    result = verify_preparation()
    print(json.dumps(dict(status=result['status'], trials=result['trial_count'],
        proposed_request_ceiling=result['hard_request_ceiling'], live_requests=0),indent=2))
