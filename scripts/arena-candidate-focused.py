"""Focused candidate execution harness; frozen candidate sources remain untouched."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time

from aig.arena.candidate_validation import verify_preparation, TARGET, evaluate_candidate_trace
from aig.arena.ai.benchmark_candidate import OpenAICandidateProvider, candidate_observation, candidate_schema, PROMPTS
from aig.arena.ai.candidate_control import CandidateController, aggregate_candidate_turns
from aig.arena.commands import ACTION_COSTS
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import digest, from_snapshot, to_snapshot, state_hash
from aig.settings import load_settings


class IntegrityError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


class Ledger:
    def __init__(self, path, ceiling):
        self.path, self.ceiling, self.rows = Path(path), ceiling, []
        self.path.touch(exist_ok=False)

    def reserve(self, trial, observation_hash, attempt):
        stored = [json.loads(line) for line in self.path.read_text().splitlines()]
        require(stored == self.rows, 'request accounting corruption')
        require(len(self.rows) < self.ceiling, 'global request ceiling exhausted')
        count = sum(r['trial'] == trial['trial'] for r in self.rows)
        require(count < trial['request_ceiling'], 'trial request ceiling exhausted')
        row = dict(request=len(self.rows)+1, trial=trial['trial'], control=trial['control_mode'],
                   trial_request=count+1, observation_hash=observation_hash, attempt=attempt,
                   reserved_utc=datetime.now(timezone.utc).isoformat())
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True)+'\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.rows.append(row)
        return row


def check_trial(result, trial, prepared):
    t = result['turn']
    require(result['replay_exact'], 'replay mismatch')
    reproduced = replay(result['command_trace'])
    require(to_snapshot(reproduced.state) == result['final_state'], 'final state mismatch')
    require(t['resulting_state_hash'] == state_hash(reproduced.state), 'final hash mismatch')
    for key in ('control_version', 'prompt_version'):
        require(t[key] == trial[key], key+' mismatch')
    for key in ('schema_version', 'observation_version', 'policy_version'):
        require(t[key] == prepared[key], key+' mismatch')
    require(t['waves'][0]['observation_hash'] == trial['observation_hash'], 'initial observation mismatch')
    require(t['ap_executed'] + t['ap_remaining'] == trial['ap_available'], 'AP accounting mismatch')
    require(sum(w['provider_requests'] for w in t['waves']) == t['provider_requests'], 'wave accounting mismatch')
    require(sum(w['ap_executed'] for w in t['waves']) == t['ap_executed'], 'wave AP mismatch')
    for index, wave in enumerate(t['waves']):
        inference = wave['inference']
        require(digest(wave['observation']) == wave['observation_hash'], 'observation corruption')
        require(not inference['fallback_used'], 'heuristic contamination')
        require(inference['requested_provider'] == 'openai', 'wrong provider')
        require(inference['actual_provider'] in (None, 'openai'), 'wrong actual provider')
        require(inference['model_configuration'] == prepared['configuration'], 'wrong configuration')
        require(inference['model_config_version'] == prepared['model_profile'], 'wrong profile')
        require(inference['model'] == prepared['configuration']['model'], 'wrong model')
        require(inference['observation_hash'] == wave['observation_hash'], 'provider observation mismatch')
        require(inference['schema_version'] == prepared['schema_version'], 'provider schema mismatch')
        require(inference['prompt_version'] == trial['prompt_version'], 'provider prompt mismatch')
        require(len(inference['attempts']) == wave['provider_requests'], 'attempt accounting mismatch')
        if wave['explicit_end_turn']:
            require(index == len(t['waves'])-1, 'request after EndTurn')
        if index and trial['control_mode'] == 'bounded':
            require(index == 1 and t['waves'][0]['invalid_action'] is not None,
                    'bounded refresh without invalidity')
        if trial['control_mode'] == 'strict':
            require(index == 0, 'strict re-observation')


def run(output, factory=None):
    prepared = verify_preparation()
    settings = load_settings().openai
    # Credentials are never included in artifacts. Do not silently apply overrides.
    provider_check = OpenAICandidateProvider(settings, client=object())
    require(provider_check.configuration() == prepared['configuration'], 'runtime configuration differs from frozen profile')
    require(factory is not None or bool(settings.api_key), 'missing credentials')
    runner_hash, preparation_hash = sha(__file__), sha(TARGET)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'manifest.json', dict(preparation=json.loads(TARGET.read_text()), runner_sha256=runner_hash,
        preparation_file_sha256=preparation_hash, command=sys.argv, started_utc=datetime.now(timezone.utc).isoformat(),
        timeout_seconds=settings.timeout_seconds, schemas={mode:candidate_schema(step=mode == 'stepwise', openai=True)
        for mode in ('strict','bounded','stepwise')}, prompts=dict(PROMPTS)))
    evidence_hashes = {'manifest.json': sha(output/'manifest.json')}
    ledger = Ledger(output/'request-ledger.jsonl', prepared['hard_request_ceiling'])
    probes = {p['id']:p for p in prepared['probes']}
    results = []

    def integrity():
        require(sha(__file__) == runner_hash, 'runner source drift')
        require(sha(TARGET) == preparation_hash, 'preparation drift')
        verify_preparation()
        require(all(sha(output/name) == value for name,value in evidence_hashes.items()), 'evidence corruption')

    try:
        for trial in prepared['schedule']:
            integrity()
            probe = probes[trial['probe']]
            sim = ArenaSimulation(from_snapshot(probe['initial_state']))
            require(state_hash(sim.state) == trial['initial_state_hash'], 'snapshot mismatch')
            require(candidate_observation(sim.state).hash == trial['observation_hash'], 'observation mismatch')
            provider = (factory(settings, trial) if factory else
                        OpenAICandidateProvider(settings, step=trial['control_mode'] == 'stepwise'))
            if factory is None:
                require(str(provider._client.base_url) == 'https://api.openai.com/v1/', 'unexpected provider endpoint')
                require(provider._client.max_retries == 0, 'transport retries enabled')

            def before_request():
                integrity()
                require(provider.configuration() == prepared['configuration'], 'provider configuration drift')
                require(provider.system_prompt == PROMPTS[trial['prompt_version']], 'prompt mismatch')
                inf = provider.last_trace
                reservation = ledger.reserve(trial, inf['observation_hash'], len(inf['attempts']))
                name = 'request-%03d.json' % reservation['request']
                # Save authoritative facts before the send, including repair decisions.
                write_new(output/name, dict(reservation=reservation, observation=candidate_observation(sim.state).to_dict(),
                    preceding_inference=inf, command_trace=sim.trace()))
                evidence_hashes[name] = sha(output/name)

            provider.before_request = before_request
            started = time.perf_counter()
            try:
                turn = CandidateController(provider, mode=trial['control_mode']).run_turn(sim)
            except BaseException:
                write_new(output/(trial['trial']+'-interrupted.json'), dict(inference=provider.last_trace,
                    command_trace=sim.trace(), final_state=to_snapshot(sim.state)))
                raise
            command_trace = sim.trace()
            reproduced = replay(command_trace)
            result = dict(trial=trial, turn=turn, command_trace=command_trace, final_state=to_snapshot(sim.state),
                replay_exact=reproduced.trace() == command_trace and to_snapshot(reproduced.state) == to_snapshot(sim.state),
                elapsed_seconds=time.perf_counter()-started, outcome=evaluate_candidate_trace(probe, turn))
            name = trial['trial']+'.json'
            write_new(output/name, result)
            evidence_hashes[name] = sha(output/name)
            check_trial(result, trial, prepared)
            require(turn['provider_requests'] == sum(r['trial'] == trial['trial'] for r in ledger.rows), 'ledger mismatch')
            results.append(result)
            print(json.dumps(dict(trial=trial['trial'], stop=turn['stop_reason'], requests=turn['provider_requests'],
                                  total_requests=len(ledger.rows))), flush=True)
        integrity()
        write_new(output/'completion.json', dict(status='completed', trials=len(results), requests=len(ledger.rows),
            evidence_hashes=evidence_hashes, ledger_sha256=sha(ledger.path)))
    except BaseException as error:
        write_new(output/'hard-stop.json', dict(status='stopped', error_type=type(error).__name__,
            completed_trials=len(results), reserved_requests=len(ledger.rows), evidence_hashes=evidence_hashes))
        raise


def analyze(output):
    manifest = json.loads((output/'manifest.json').read_text())
    prepared = manifest['preparation']['payload']
    require(digest(prepared) == manifest['preparation']['sha256'], 'manifest corruption')
    completion = json.loads((output/'completion.json').read_text())
    require(all(sha(output/name) == value for name,value in completion['evidence_hashes'].items()), 'evidence corruption')
    require(sha(output/'request-ledger.jsonl') == completion['ledger_sha256'], 'ledger corruption')
    ledger = [json.loads(line) for line in (output/'request-ledger.jsonl').read_text().splitlines()]
    require([r['request'] for r in ledger] == list(range(1,len(ledger)+1)), 'ledger sequence corruption')
    require(len(ledger) <= 86, 'ceiling exceeded')
    results = [json.loads((output/(t['trial']+'.json')).read_text()) for t in prepared['schedule']]
    for result, trial in zip(results, prepared['schedule']):
        check_trial(result, trial, prepared)
        require(result['turn']['provider_requests'] == sum(r['trial'] == trial['trial'] for r in ledger), 'ledger mismatch')
    report = dict(trials=len(results), requests=len(ledger), controls={}, first_actions={}, observations_equal=True,
                  replay_exact=True, per_trial=results)
    for mode in ('strict','bounded','stepwise'):
        selected = [r for r in results if r['trial']['control_mode'] == mode]
        rows = [r['turn'] for r in selected]
        summary = aggregate_candidate_turns(rows)
        stops = [t for t in rows if t['explicit_end_turn']]
        waves = [w for t in rows for w in t['waves']]
        attempts = [a for w in waves for a in w['inference']['attempts']]
        summary.update(accepted=sum(not t['provider_failure'] for t in rows), failed=sum(t['provider_failure'] for t in rows),
            explicit_rate=len(stops)/len(rows), explicit_remaining_ap=[t['ap_remaining'] for t in stops],
            explicit_remaining_mean=statistics.mean([t['ap_remaining'] for t in stops]) if stops else None,
            explicit_remaining_median=statistics.median([t['ap_remaining'] for t in stops]) if stops else None,
            actions_before_end=[t['actions_before_intentional_stop'] for t in stops],
            clean_short_plans=sum(t['clean_short_plan'] for t in rows), replans=sum(t['replan_used'] for t in rows),
            decisions=len(waves), first_response_valid=sum('error_category' not in w['inference']['attempts'][0] for w in waves),
            attempt_error_categories=dict(Counter(a['error_category'] for a in attempts if 'error_category' in a)),
            repair_success=sum(w['provider_requests'] == 2 and w['plan'] is not None for w in waves),
            repair_failure=sum(w['provider_requests'] == 2 and w['plan'] is None for w in waves),
            elapsed_seconds=sum(r['elapsed_seconds'] for r in selected),
            initial_plans=[dict(trial=r['trial']['trial'], actions=r['turn']['waves'][0]['plan'],
                               planned_ap=r['turn']['waves'][0]['planned_ap']) for r in selected],
            actions_per_turn=[t['actions_executed'] for t in rows], requests_per_turn=[t['provider_requests'] for t in rows])
        for key in ('input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens'):
            values = [a['metrics'].get(key) for a in attempts]
            summary[key] = sum(values) if values and all(v is not None for v in values) else None
        report['controls'][mode] = summary
    for probe in prepared['probes']:
        matched = [r for r in results if r['trial']['probe'] == probe['id']]
        observations = [r['turn']['waves'][0]['observation'] for r in matched]
        require(all(o == observations[0] for o in observations), 'first game facts differ')
        report['first_actions'][probe['id']] = {}
        for r in matched:
            plan = r['turn']['waves'][0]['plan']
            action = plan['actions'][0] if plan and plan['actions'] else None
            report['first_actions'][probe['id']][r['trial']['control_mode']] = dict(action=action,
                ap_cost=ACTION_COSTS[action['type']] if action else None)
    write_new(output/'analysis.json', report)
    print(json.dumps({k:v for k,v in report.items() if k != 'per_trial'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['run','analyze'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.operation == 'run':
        require(args.live, 'run requires explicit --live')
        run(args.output)
    else:
        analyze(args.output)
