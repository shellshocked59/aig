"""Shared experimental loop: only observation scheduling varies by control mode."""
from copy import deepcopy

from aig.arena.ai.benchmark_candidate import (
    CandidatePlan, EndTurnAction, candidate_observation, parse_candidate,
    POLICY_VERSION, TURN_PROMPT_VERSION, STEP_PROMPT_VERSION, SCHEMA_VERSION,
    OBSERVATION_VERSION,
)
from aig.arena.ai.contracts import action_command
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.commands import ArenaEndTurn
from aig.arena.snapshots import canonical_json, command_to_dict, state_hash

CONTROL_VERSIONS = dict(strict='arena-control-full-turn-v2',
    bounded='arena-control-full-turn-bounded-replan-v2', stepwise='arena-control-stepwise-v2')
STOP_REASONS = ('INTENTIONAL_END_TURN', 'CLEAN_PLAN_COMPLETE', 'EXECUTION_TRUNCATION',
                'PROVIDER_FAILURE', 'TERMINAL')


class CandidateController:
    """Explicit construction only. No tactical fallback, at most one static repair/call."""
    def __init__(self, provider, *, mode):
        if mode not in CONTROL_VERSIONS:
            raise ValueError('unknown candidate control')
        self.provider, self.mode = provider, mode
        expected = STEP_PROMPT_VERSION if mode == 'stepwise' else TURN_PROMPT_VERSION
        if getattr(provider, 'prompt_version', expected) != expected:
            raise ValueError('prompt/control mismatch')

    def run_turn(self, simulation):
        state, provider = simulation.state, self.provider
        state.validate()
        if state.active_player_id is None:
            raise ValueError('cannot plan after victory')
        player, turn, available = state.active_player_id, state.turn, state.action_points_remaining
        start = len(simulation.trace()['entries'])
        waves, commands = [], []
        requests, replans, executed = 0, 0, 0
        unused, reason = available, 'CLEAN_PLAN_COMPLETE'
        ceiling = dict(strict=2, bounded=4, stepwise=10)[self.mode]
        model = isinstance(provider, ModelArenaTurnProvider)
        old_hook = getattr(provider, 'before_request', None)
        had_hook = 'before_request' in vars(provider)

        def reserve():
            nonlocal requests
            if requests >= ceiling:
                raise ArenaProviderError('request_ceiling')
            if old_hook is not None:
                old_hook()
            requests += 1

        if model:
            provider.before_request = reserve
        try:
            while state.action_points_remaining and state.winner_player_id is None:
                observation = candidate_observation(state)
                before_requests = requests
                row = dict(wave_index=len(waves), observation=observation.to_dict(),
                    observation_hash=observation.hash, ap_available=state.action_points_remaining,
                    plan=None, planned_ap=0, actions_attempted=[], commands_executed=[],
                    explicit_end_turn=False, planned_end_turn=False, clean_plan_complete=False,
                    invalid_action=None, error_category=None, command_start=len(simulation.trace()['entries']))
                waves.append(row)
                try:
                    if not model:
                        reserve()  # offline scripted decision count
                    plan = provider.create_turn_plan(observation)
                    if type(plan) is not CandidatePlan:
                        raise ArenaProviderError('schema_validation')
                    plan = parse_candidate(canonical_json(plan.to_dict()), observation, step=self.mode == 'stepwise')
                    row.update(plan=plan.to_dict(), planned_ap=plan.ap_cost,
                               planned_end_turn=bool(plan.actions and type(plan.actions[-1]) is EndTurnAction))
                except ArenaProviderError as error:
                    row['error_category'] = error.category
                    reason = 'PROVIDER_FAILURE'
                    plan = None
                row['provider_requests'] = requests-before_requests
                # Provider trace is already redacted by the inherited transport boundary.
                row['inference'] = deepcopy(getattr(provider, 'last_trace', None)) or {}
                for index, action in enumerate(plan.actions if plan else ()):
                    before = state.action_points_remaining
                    attempt = dict(index=index, action=action.to_dict(), ap_before=before,
                                   ap_after=before, executed=False)
                    row['actions_attempted'].append(attempt)
                    if type(action) is EndTurnAction:
                        # Capture this player's AP before EndTurn resets the next player's budget.
                        unused = before
                        command = ArenaEndTurn(player)
                    else:
                        command = action_command(action, player)
                    try:
                        simulation.execute(command)
                    except ValueError as error:
                        row['invalid_action'] = dict(index=index, action=action.to_dict(),
                            reason=str(error), ap_remaining=before)
                        attempt['error'] = str(error)
                        reason = 'EXECUTION_TRUNCATION'
                        break
                    saved = command_to_dict(command)
                    row['commands_executed'].append(saved)
                    commands.append(saved)
                    attempt['executed'] = True
                    if type(action) is EndTurnAction:
                        row['explicit_end_turn'] = True
                        reason = 'INTENTIONAL_END_TURN'
                        break
                    executed += 1
                    unused = state.action_points_remaining
                    attempt['ap_after'] = unused
                    if state.winner_player_id is not None:
                        reason = 'TERMINAL'
                        break
                else:
                    if plan is not None:
                        row['clean_plan_complete'] = True
                        reason = 'CLEAN_PLAN_COMPLETE'
                row.update(ap_remaining=unused, ap_executed=row['ap_available']-unused,
                    command_end=len(simulation.trace()['entries']), resulting_state_hash=state_hash(state))
                row['stale_suffix_count'] = len(plan.actions)-row['invalid_action']['index'] if row['invalid_action'] else 0
                if reason in ('TERMINAL', 'INTENTIONAL_END_TURN', 'PROVIDER_FAILURE'):
                    break
                if reason == 'EXECUTION_TRUNCATION':
                    if self.mode == 'bounded' and replans == 0 and unused > 0:
                        replans += 1
                        continue
                    break
                if self.mode != 'stepwise' or not plan.actions:
                    break
                # Every successful non-stop step costs >=1 AP; at most five decisions.
        finally:
            if model:
                if had_hook:
                    provider.before_request = old_hook
                else:
                    del provider.before_request
        if state.winner_player_id is not None:
            reason = 'TERMINAL'
        failure = next((w['error_category'] for w in reversed(waves) if w['error_category']), None)
        # Uniform strict provider failure policy: preserve the exact failing prefix.
        if state.winner_player_id is None and state.active_player_id == player and reason != 'PROVIDER_FAILURE':
            command = ArenaEndTurn(player)
            simulation.execute(command)
            commands.append(command_to_dict(command))
        replacement = waves[1] if self.mode == 'bounded' and len(waves) > 1 else None
        trace = dict(version='arena-candidate-turn-trace-v1', control_mode=self.mode,
            control_version=CONTROL_VERSIONS[self.mode], policy_version=POLICY_VERSION,
            prompt_version=STEP_PROMPT_VERSION if self.mode == 'stepwise' else TURN_PROMPT_VERSION,
            schema_version=SCHEMA_VERSION, observation_version=OBSERVATION_VERSION,
            player_id=player, turn=turn, waves=waves, ap_available=available,
            ap_executed=available-unused, ap_remaining=unused, ap_unused=unused,
            stop_reason=reason, explicit_end_turn=reason == 'INTENTIONAL_END_TURN',
            clean_short_plan=reason == 'CLEAN_PLAN_COMPLETE' and unused > 0,
            truncation=reason == 'EXECUTION_TRUNCATION', provider_failure=reason == 'PROVIDER_FAILURE',
            terminal=reason == 'TERMINAL', terminal_result=state.winner_player_id,
            execution_invalidities=sum(w['invalid_action'] is not None for w in waves),
            replan_used=bool(replans), ap_at_replan=replacement['ap_available'] if replacement else None,
            ap_recovered=replacement['ap_executed'] if replacement else 0,
            first_plan_explicit_end_turn=waves[0]['explicit_end_turn'] if waves else False,
            first_plan_planned_end_turn=waves[0]['planned_end_turn'] if waves else False,
            initial_plan_completed_cleanly=(waves[0]['clean_plan_complete'] or waves[0]['explicit_end_turn']) if waves else False,
            invalidity_triggered_replan=bool(replans),
            replacement_explicit_end_turn=replacement['explicit_end_turn'] if replacement else False,
            replacement_clean_short_plan=bool(replacement and replacement['clean_plan_complete'] and unused > 0),
            second_invalidity=bool(replacement and replacement['invalid_action']),
            explicit_end_turn_decisions=sum(w['explicit_end_turn'] for w in waves),
            actions_before_intentional_stop=executed if reason == 'INTENTIONAL_END_TURN' else None,
            actions_executed=executed, decisions=len(waves), provider_requests=requests,
            static_repairs=sum(max(0, w['provider_requests']-1) for w in waves),
            commands_executed=commands, command_start=start, command_end=len(simulation.trace()['entries']),
            error_category=failure, resulting_state_hash=state_hash(state))
        attempts = [a for w in waves for a in w['inference'].get('attempts', [])]
        trace['backend_thinking_seconds'] = sum(a.get('wall_clock_seconds') or 0 for a in attempts)
        metrics = []
        for attempt in attempts:
            m = dict(attempt.get('metrics', {}))
            if 'prompt_eval_count' in m and 'eval_count' in m:
                m.update(input_tokens=m['prompt_eval_count'], output_tokens=m['eval_count'],
                         total_tokens=m['prompt_eval_count']+m['eval_count'])
            metrics.append(m)
        for key in ('input_tokens', 'output_tokens', 'total_tokens'):
            values = [m.get(key) for m in metrics]
            trace[key] = sum(values) if values and all(v is not None for v in values) else None
        return deepcopy(trace)


def aggregate_candidate_turns(rows):
    """Disjoint AP attribution; recovered truncations remain separate event counts."""
    n = len(rows)
    totals = {reason: sum(r['ap_remaining'] for r in rows if r['stop_reason'] == reason)
              for reason in STOP_REASONS}
    result = dict(turns=n, unused_ap_by_reason=totals,
        stop_counts={reason: sum(r['stop_reason'] == reason for r in rows) for reason in STOP_REASONS})
    for key in ('ap_available', 'ap_executed', 'ap_remaining', 'provider_requests',
                'static_repairs', 'execution_invalidities', 'ap_recovered', 'backend_thinking_seconds'):
        result[key] = sum(r[key] for r in rows)
        result[key+'_per_turn'] = result[key]/n if n else 0
    result['execution_failure_rate'] = sum(r['execution_invalidities'] > 0 for r in rows)/n if n else 0
    result['truncation_ap_loss_per_turn'] = totals['EXECUTION_TRUNCATION']/n if n else 0
    result['failure_derived_unused_ap'] = totals['EXECUTION_TRUNCATION']+totals['PROVIDER_FAILURE']
    for key in ('input_tokens', 'output_tokens', 'total_tokens'):
        values = [r[key] for r in rows]
        result[key] = sum(values) if values and all(v is not None for v in values) else None
    return result
