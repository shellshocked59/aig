"""Additive v6 registry/runner. Default operations never construct a live provider."""
import argparse
import hashlib
import json
from pathlib import Path

from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController, aggregate_turns
from aig.arena.ai.contracts import ArenaTurnPlan, AttackAction, SnipeAction
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.observation import build_observation
from aig.arena.ai.prompts import resolve_prompt
from aig.arena.ai.validation import ArenaProviderError, openai_turn_plan_schema
from aig.arena.benchmark_provider import checked_plan, safe_inference
from aig.arena.benchmark_versions import frozen_probe, probe_set
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import digest, state_hash, to_snapshot, from_snapshot
from aig.settings import Settings, load_settings

VERSION = 'arena-benchmark-v6'
ROOT = Path(__file__).resolve().parents[3]
RECIPE_PATH = Path(__file__).with_name('benchmark_artifacts') / (VERSION + '.json')


def recipe():
    data = json.loads(RECIPE_PATH.read_text(encoding='utf-8'))
    if digest(data) != RECIPE_HASH:
        raise ValueError('bounded replan recipe integrity failure')
    return data


def sources():
    paths = sorted((ROOT / 'backend/aig').rglob('*.py'))
    paths += sorted((ROOT / 'backend/aig/arena/benchmark_artifacts').glob('*.json'))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def prepare(path, *, provider='openai', probes=('snipe_vs_basic',), repetitions=1, arms=('bounded_replan',)):
    if provider not in ('openai', 'ollama') or type(repetitions) is not int or repetitions < 1:
        raise ValueError('invalid provider or repetitions')
    if tuple(arms) not in (('bounded_replan',), ('full_turn', 'bounded_replan')):
        raise ValueError('choose smoke or paired comparison')
    names = list(probe_set()['probes']) if probes == ('all',) else list(probes)
    if not names or len(set(names)) != len(names):
        raise ValueError('unique probes required')
    rows = [dict(name=n, snapshot=to_snapshot(frozen_probe(n))) for n in names]
    config_version, config = resolve_model_profile(provider)
    result = dict(version=VERSION, recipe=recipe(), recipe_hash=RECIPE_HASH, provider=provider,
                  model_profile=config_version, model_configuration=config,
                  prompt_hash=hashlib.sha256(resolve_prompt('arena-turn-prompt-v1')[1].encode()).hexdigest(),
                  wire_schema_hash=digest(openai_turn_plan_schema()), fixtures=rows, fixture_hash=digest(rows),
                  repetitions=repetitions, arms=list(arms),
                  request_ceiling=repetitions*len(rows)*sum(4 if a == 'bounded_replan' else 2 for a in arms),
                  source_files=sources())
    result['plan_hash'] = digest(result)
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    return result


def run(plan_path, output, *, settings=None, provider_factory=create_arena_turn_provider):
    saved = json.loads(Path(plan_path).read_text(encoding='utf-8'))
    unsigned = {k: v for k, v in saved.items() if k != 'plan_hash'}
    if (digest(unsigned) != saved['plan_hash'] or saved['recipe'] != recipe()
            or saved['source_files'] != sources() or saved['fixture_hash'] != digest(saved['fixtures'])):
        raise ValueError('prepared experiment mismatch; prepare and review again')
    settings = settings or Settings()
    if inference_configuration(saved['provider'], settings) != saved['model_configuration']:
        raise ValueError('requires unchanged frozen model profile')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    write(output/'manifest.json', saved)
    provider = provider_factory(settings, saved['provider'])
    if (provider.name != saved['provider'] or provider.configuration() != saved['model_configuration']
            or provider.prompt_version != recipe()['prompt'] or not provider.repair):
        raise ValueError('provider contract mismatch')
    requests = 0
    def boundary():
        nonlocal requests
        if sources() != saved['source_files']:
            raise ArenaProviderError('source_mutation')
        if requests >= saved['request_ceiling']:
            raise ArenaProviderError('request_ceiling')
        requests += 1
    provider.before_request = boundary
    original_plan = provider.create_turn_plan
    def verified_plan(observation):
        before = requests
        candidate = original_plan(observation)
        trace = provider.last_trace
        if (trace.get('requested_provider') != saved['provider']
                or trace.get('actual_provider') != saved['provider'] or trace.get('fallback_used')
                or len(trace.get('attempts', [])) != requests-before
                or not 1 <= requests-before <= 2):
            raise ArenaProviderError('provider_mismatch')
        return candidate
    provider.create_turn_plan = verified_plan
    report = dict(version=VERSION, status='complete', requests=0, runs=[],
                  scheduled_turns=saved['repetitions']*len(saved['fixtures'])*len(saved['arms']))
    write(output/'report.json', report)
    stop = False
    for repetition in range(saved['repetitions']):
        for fixture in saved['fixtures']:
            for arm in saved['arms']:
                sim = ArenaSimulation(from_snapshot(fixture['snapshot']))
                directory = output / f'turn-{len(report["runs"])+1:04d}'
                directory.mkdir()
                start_requests = requests
                row = dict(arm=arm, probe=fixture['name'], repetition=repetition+1)
                try:
                    if arm == 'bounded_replan':
                        turn = ArenaBoundedReplanController(provider, fallback=False).run_turn(sim).to_dict()
                        for wave in turn['waves']:
                            wave['inference'] = safe_inference(wave['inference'])
                        row.update(turn=turn, error_category=turn['error_category'], ap_spent=turn['ap_spent'],
                                   ap_unused=turn['ap_unused'], ap_recovered=turn['ap_recovered'],
                                   planning_waves=turn['planning_waves'], static_repairs=turn['static_repairs'])
                    else:
                        plan, call = checked_plan(provider, saved['provider'], build_observation(sim.state))
                        raw_error = (provider.last_trace or {}).get('error_category')
                        if raw_error in ('transport_failure', 'source_mutation', 'request_ceiling'):
                            call['error_category'] = raw_error
                        result = execute_arena_turn(sim.state, plan, execute_command=sim.execute).to_dict() if plan else None
                        row.update(turn=result, inference=call, error_category=call['error_category'],
                                   ap_spent=result['ap_spent'] if result else 0,
                                   ap_unused=result['ap_unused'] if result else sim.state.action_points_remaining,
                                   ap_recovered=0, planning_waves=1, static_repairs=call['repair_requests'])
                    if state_hash(replay(sim.trace()).state) != state_hash(sim.state):
                        raise ValueError('replay mismatch')
                    if sources() != saved['source_files']:
                        raise ValueError('source mutation')
                except Exception:
                    row['error_category'] = 'runner_defect'
                    raise
                finally:
                    row.update(provider_requests=requests-start_requests, resulting_state_hash=state_hash(sim.state),
                               terminal_result=sim.state.winner_player_id)
                    write(directory/'commands.json', sim.trace())
                    write(directory/'turn.json', row)
                    report['runs'].append(row)
                    report['requests'] = requests
                    if row.get('error_category'):
                        report['status'] = 'failed'; stop = True
                    report['unstarted_turns'] = report['scheduled_turns']-len(report['runs'])
                    bounded = [r['turn'] for r in report['runs'] if r['arm'] == 'bounded_replan' and r.get('turn')]
                    report['bounded_metrics'] = aggregate_turns(bounded)
                    write(output/'report.json', report)
                if stop:
                    break
            if stop:
                break
        if stop:
            break
    return report


def demo():
    class Fake:
        def __init__(self):
            self.calls = 0

        def create_turn_plan(self, observation):
            self.calls += 1
            if self.calls == 1:
                return ArenaTurnPlan((SnipeAction('actor', 'enemy'), SnipeAction('actor', 'enemy'), AttackAction('actor', 'enemy2')))
            return ArenaTurnPlan((AttackAction('actor', 'enemy2'),)*3)
    provider = Fake()
    sim = ArenaSimulation(frozen_probe('snipe_vs_basic'))
    trace = ArenaBoundedReplanController(provider).run_turn(sim).to_dict()
    assert replay(sim.trace()).trace() == sim.trace()
    return dict(trace=trace, metrics=aggregate_turns([trace]), fake_provider_calls=provider.calls, replay_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('demo')
    prep = subs.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--provider', choices=('openai', 'ollama'), default='openai')
    prep.add_argument('--probe', default='snipe_vs_basic')
    prep.add_argument('--repetitions', type=int, default=1)
    prep.add_argument('--paired', action='store_true')
    live = subs.add_parser('run')
    live.add_argument('--plan', type=Path, required=True)
    live.add_argument('--output', type=Path, required=True)
    live.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.command == 'demo':
        result = demo()
    elif args.command == 'prepare':
        result = prepare(args.output, provider=args.provider, probes=(args.probe,), repetitions=args.repetitions,
                         arms=('full_turn', 'bounded_replan') if args.paired else ('bounded_replan',))
        result = {k: result[k] for k in ('version', 'plan_hash', 'request_ceiling')}
    else:
        if not args.live:
            parser.error('run requires explicit live authorization and --live')
        result = run(args.plan, args.output, settings=load_settings())
    print(json.dumps(result, indent=2, sort_keys=True))


# Canonical JSON hash; independent registry keeps all historical registries frozen.
RECIPE_HASH = '0b38a61ab30290054e6ec0f1d3fec4f77975b8520e34cb34e69b6bab6fce7502'

if __name__ == '__main__':
    main()
