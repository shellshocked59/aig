"""Diagnostic scripted first wave, real bounded recovery; prepare is offline."""
import argparse
import json
from pathlib import Path

from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController, CONTROL_VERSION, execute_plan_segment
from aig.arena.ai.contracts import ArenaTurnPlan, SnipeAction, AttackAction
from aig.arena.ai.factory import create_arena_turn_provider
from aig.arena.ai.observation import build_observation
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.bounded_replan_benchmark import sources, write
from aig.arena.benchmark_versions import frozen_probe
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, digest, from_snapshot, to_snapshot
from aig.settings import load_settings

VERSION = 'arena-bounded-replan-recovery-smoke-v1'
REQUEST_CEILING = 2


def scripted_plan():
    return ArenaTurnPlan((SnipeAction('actor', 'enemy'), SnipeAction('actor', 'enemy'),
                          AttackAction('actor', 'enemy2')))


def expected_boundary():
    sim = ArenaSimulation(frozen_probe('snipe_vs_basic'))
    initial = build_observation(sim.state)
    plan = parse_turn_plan(canonical_json(scripted_plan().to_dict()), initial)
    execution = execute_plan_segment(sim, plan)
    return initial, execution, build_observation(sim.state), sim


class ScriptedFirstWaveThenDelegateProvider(ModelArenaTurnProvider):
    """Model marker preserves controller request telemetry; no transport for wave 1."""
    name = 'scripted-first-then-openai'

    def __init__(self, delegate, boundary=None):
        self.delegate = delegate
        self.prompt_version = delegate.prompt_version
        self.calls = self.attempts = 0
        self.boundary = boundary

    @property
    def last_trace(self):
        return self.delegate.last_trace if self.calls > 1 else None

    def create_turn_plan(self, observation):
        self.calls += 1
        if self.calls == 1:
            return parse_turn_plan(canonical_json(scripted_plan().to_dict()), observation)
        if self.calls > 2:
            raise ArenaProviderError('request_ceiling')
        old = getattr(self.delegate, 'before_request', None)
        had_hook = 'before_request' in vars(self.delegate)

        def reserve():
            if self.attempts >= REQUEST_CEILING:
                raise ArenaProviderError('request_ceiling')
            if self.boundary:
                self.boundary(observation)
            if old:
                old()
            hook = getattr(self, 'before_request', None)
            if hook:
                hook()
            self.attempts += 1

        self.delegate.before_request = reserve
        try:
            return self.delegate.create_turn_plan(observation)
        finally:
            if had_hook:
                self.delegate.before_request = old
            else:
                del self.delegate.before_request


def prepare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    initial, execution, fresh, sim = expected_boundary()
    profile, configuration = resolve_model_profile('openai')
    manifest = dict(version=VERSION, control_version=CONTROL_VERSION, provider='openai',
                    fixture='snipe_vs_basic', request_ceiling=REQUEST_CEILING,
                    model_profile=profile, model_configuration=configuration,
                    source_files=sources(), initial_observation_hash=initial.hash,
                    replan_observation_hash=fresh.hash, scripted_plan=scripted_plan().to_dict())
    manifest['manifest_hash'] = digest(manifest)
    write(output/'manifest.json', manifest)
    write(output/'initial-state.json', sim.initial_snapshot)
    write(output/'scripted-plan.json', scripted_plan().to_dict())
    write(output/'initial-execution.json', execution)
    write(output/'replan-observation.json', fresh.to_dict())
    write(output/'preparation.json', dict(status='prepared_offline', live_requests=0,
                                         prefix_replay_exact=replay(sim.trace()).trace() == sim.trace()))
    return manifest


def verify(sim, turn, provider):
    initial, expected, fresh, prefix = expected_boundary()
    waves = turn['waves']
    first = waves[0]
    second = waves[1] if len(waves) == 2 else {}
    replayed = replay(sim.trace())
    checks = dict(
        initial_plan_accepted=first['plan'] == scripted_plan().to_dict(),
        initial_observation=first['observation_hash'] == initial.hash,
        committed_prefix=sim.trace()['entries'][:1] == prefix.trace()['entries'],
        invalidity=first.get('invalid_action') == expected['invalid_action'],
        suffix_discarded=first.get('stale_suffix_count') == 2 and first.get('actions_executed') == 1,
        exactly_one_replan=turn['replan_used'] and len(waves) == 2 and provider.calls == 2,
        no_early_end_turn=second.get('command_start') == 1 and first.get('command_end') == 1,
        fresh_observation=second.get('observation') == fresh.to_dict() and second.get('observation_hash') == fresh.hash,
        request_bound=1 <= provider.attempts <= 2 and turn['provider_requests'] == provider.attempts,
        scripted_zero_requests=first['provider_requests'] == 0 and first['static_repairs'] == 0,
        no_fallback=not turn['fallback_used'],
        valid_replacement=second.get('plan') is not None and second.get('planned_ap', 99) <= 3,
        replacement_action=second.get('actions_executed', 0) >= 1,
        provider_success=turn['error_category'] is None,
        correct_turn_end=(not any(c['type'] == 'arena_end_turn' for c in turn['commands_executed'])
                          if sim.state.winner_player_id is not None else
                          bool(turn['commands_executed']) and turn['commands_executed'][-1]['type'] == 'arena_end_turn'),
        replay_exact=replayed.trace() == sim.trace() and to_snapshot(replayed.state) == to_snapshot(sim.state))
    inference = second.get('inference', {})
    checks['provider_purity'] = (inference.get('actual_provider') == 'openai'
                                 and not inference.get('fallback_used')
                                 and len(inference.get('attempts', [])) == provider.attempts)
    return dict(checks=checks, passed=all(checks.values()))


def run(output, *, settings, provider_factory=create_arena_turn_provider):
    output = Path(output)
    saved = json.loads((output/'manifest.json').read_text())
    if (digest({k: v for k, v in saved.items() if k != 'manifest_hash'}) != saved['manifest_hash']
            or saved['source_files'] != sources()
            or saved['version'] != VERSION or saved['request_ceiling'] != REQUEST_CEILING
            or saved['scripted_plan'] != scripted_plan().to_dict()):
        raise ValueError('prepared smoke mismatch; prepare and review a new evidence root')
    initial, execution, fresh, prefix = expected_boundary()
    expected_files = {'initial-state.json': prefix.initial_snapshot,
                      'scripted-plan.json': scripted_plan().to_dict(),
                      'initial-execution.json': execution, 'replan-observation.json': fresh.to_dict()}
    if any(json.loads((output/name).read_text()) != value for name, value in expected_files.items()):
        raise ValueError('prepared evidence mismatch')
    if inference_configuration('openai', settings) != saved['model_configuration']:
        raise ValueError('requires unchanged frozen Luna profile')
    # Exclusive sentinel prevents retries or overwriting failed evidence.
    with (output/'live-started.json').open('x') as stream:
        json.dump({'status': 'started', 'request_ceiling': 2}, stream)
    sim = ArenaSimulation(from_snapshot(prefix.initial_snapshot))
    delegate = provider_factory(settings, 'openai')
    if (not isinstance(delegate, ModelArenaTurnProvider) or delegate.name != 'openai'
            or delegate.prompt_version != 'arena-turn-prompt-v1' or not delegate.repair
            or delegate.configuration() != saved['model_configuration']):
        raise ValueError('requires normal OpenAI turn provider with one static repair')

    def boundary(observation):
        if sources() != saved['source_files']:
            raise ArenaProviderError('source_mutation')
        if observation != fresh or build_observation(sim.state) != fresh:
            raise ArenaProviderError('observation_mismatch')
        if sim.trace()['entries'] != prefix.trace()['entries']:
            raise ArenaProviderError('prefix_mismatch')
        write(output/'replan-observation.json', observation.to_dict())

    provider = ScriptedFirstWaveThenDelegateProvider(delegate, boundary)
    turn = None
    try:
        turn = ArenaBoundedReplanController(provider, fallback=False).run_turn(sim).to_dict()
        verification = verify(sim, turn, provider)
        verification['checks']['source_preserved'] = sources() == saved['source_files']
        verification['passed'] = all(verification['checks'].values())
        second = turn['waves'][1]
        write(output/'replacement-plan.json', second['plan'])
        write(output/'replan-observation.json', second['observation'])
        write(output/'offline-verification.json', verification)
        report = dict(version=VERSION, status='pass' if verification['passed'] else 'fail',
                      stronger_pass=verification['passed'] and second.get('invalid_action') is None,
                      replacement_truncated=second.get('invalid_action') is not None,
                      initial_ap=5, ap_spent_before_invalidity=2, ap_remaining_at_replan=3,
                      initial_observation_hash=initial.hash, replan_observation_hash=fresh.hash,
                      invalid_action=execution['invalid_action'], stale_suffix_size=2,
                      unattempted_suffix_size=1, replans_used=int(turn['replan_used']),
                      changed_unit_before=initial.to_dict()['enemy_team']['units'],
                      changed_unit_after=fresh.to_dict()['enemy_team']['units'], turn=turn)
        write(output/'report.json', report)
        return report
    finally:
        write(output/'commands.json', sim.trace())  # Repository-native replay envelope.
        (output/'command-trace.jsonl').write_text(''.join(canonical_json(e)+'\n' for e in sim.trace()['entries']))
        write(output/'final-state.json', to_snapshot(sim.state))
        inference = delegate.last_trace
        (output/'luna-inference.jsonl').write_text(canonical_json(inference)+'\n' if inference else '')
        if turn is None:
            write(output/'report.json', dict(status='runner_failure', provider_attempts=provider.attempts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.output)
        print(json.dumps({k: result[k] for k in ('version', 'manifest_hash', 'request_ceiling')}))
    else:
        if not args.live:
            parser.error('run requires separately authorized --live')
        result = run(args.output, settings=load_settings())
        print(json.dumps({'status': result['status'], 'requests': result['turn']['provider_requests']}))
        if result['status'] != 'pass':
            raise SystemExit(1)


if __name__ == '__main__':
    main()
