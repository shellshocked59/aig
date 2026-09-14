"""Full remaining-turn plans with one execution recovery; no frozen executor edits."""
from copy import deepcopy
from dataclasses import dataclass

from aig.arena.ai.contracts import ArenaTurnPlan, action_command
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import build_observation
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.benchmark_provider import safe_inference
from aig.arena.commands import ArenaEndTurn
from aig.arena.snapshots import canonical_json, command_to_dict, state_hash

CONTROL_VERSION = "arena-control-full-turn-bounded-replan-v1"
MAX_EXECUTION_REPLANS = 1
MAX_PROVIDER_REQUESTS = 4


@dataclass(frozen=True)
class ArenaBoundedReplanTurnTrace:
    data: dict

    def to_dict(self):
        return deepcopy(self.data)


def execute_plan_segment(simulation, plan):
    """Commit through the normal command sink, stopping before automatic EndTurn."""
    state = simulation.state
    player, available = state.active_player_id, state.action_points_remaining
    attempts, commands = [], []
    invalid = None
    for index, action in enumerate(plan.actions):
        before = state.action_points_remaining
        row = dict(index=index, action=action.to_dict(), ap_before=before,
                   ap_after=before, executed=False)
        attempts.append(row)
        command = action_command(action, player)
        try:
            simulation.execute(command)
        except ValueError as error:
            invalid = dict(index=index, action=action.to_dict(), reason=str(error), ap_remaining=before)
            row['error'] = str(error)
            break
        commands.append(command_to_dict(command))
        row.update(executed=True, ap_after=state.action_points_remaining)
        if state.winner_player_id is not None:
            break
    return dict(actions_attempted=attempts, commands_executed=commands,
                invalid_action=invalid, stale_suffix_count=len(plan.actions)-invalid['index'] if invalid else 0,
                ap_available=available, ap_spent=available-state.action_points_remaining,
                ap_unused=state.action_points_remaining, actions_executed=len(commands))


class ArenaBoundedReplanController:
    control_version = CONTROL_VERSION

    def __init__(self, provider=None, *, fallback=True):
        self.provider = provider if provider is not None else HeuristicArenaTurnProvider()
        self.fallback = fallback
        if getattr(self.provider, 'prompt_version', 'arena-turn-prompt-v1') != 'arena-turn-prompt-v1':
            raise ValueError('bounded replan v1 requires arena-turn-prompt-v1')

    def run_turn(self, simulation):
        state = simulation.state
        state.validate()
        if state.active_player_id is None:
            raise ValueError('cannot start bounded replan after victory')
        player, turn, available = state.active_player_id, state.turn, state.action_points_remaining
        waves, commands = [], []
        requests = 0
        failure = None
        provider = self.provider
        old_hook = getattr(provider, 'before_request', None)

        def reserve():
            nonlocal requests
            if requests >= MAX_PROVIDER_REQUESTS:
                raise ArenaProviderError('request_ceiling')
            if old_hook is not None:
                old_hook()
            requests += 1

        # Built-in transports reserve before sending, including static repairs.
        model = isinstance(provider, ModelArenaTurnProvider)
        had_hook = 'before_request' in vars(provider) if model else False
        if model:
            provider.before_request = reserve
        try:
            for wave_index in range(1 + MAX_EXECUTION_REPLANS):
                if not state.action_points_remaining:
                    break
                observation = build_observation(state)
                plan = None
                error_category = None
                before_requests = requests
                try:
                    plan = provider.create_turn_plan(observation)
                    if type(plan) is not ArenaTurnPlan:
                        raise ArenaProviderError('schema_validation')
                    plan = parse_turn_plan(canonical_json(plan.to_dict()), observation)
                except ArenaProviderError as error:
                    plan = None
                    error_category = failure = error.category
                raw_inference = deepcopy(getattr(provider, 'last_trace', None)) or {}
                inference = safe_inference(raw_inference) if raw_inference else {}
                if raw_inference:
                    inference.update({k: raw_inference.get(k) for k in (
                        'model', 'model_config_version', 'model_configuration', 'prompt_version',
                        'schema_version', 'observation_version', 'wall_clock_seconds')})
                    # The frozen sanitizer predates these transport/control categories.
                    inference['error_category'] = error_category
                row = dict(wave_index=wave_index, observation_hash=observation.hash,
                           observation=observation.to_dict(), plan=plan.to_dict() if plan else None,
                           planned_ap=plan.ap_cost if plan else 0, inference=inference,
                           provider_requests=requests-before_requests,
                           static_repairs=max(0, len(inference.get('attempts', []))-1),
                           requested_provider=getattr(provider, 'name', type(provider).__name__),
                           error_category=error_category, fallback_used=False,
                           command_start=len(simulation.trace()['entries']))
                waves.append(row)
                if error_category:
                    if not self.fallback or error_category in ('request_ceiling', 'source_mutation'):
                        break  # strict failures preserve the prefix, without EndTurn
                    plan = HeuristicArenaTurnProvider().create_turn_plan(observation)
                    row.update(fallback_used=True, fallback_plan=plan.to_dict(), fallback_provider='arena-heuristic-v1')
                row.update(execute_plan_segment(simulation, plan))
                row.update(command_end=len(simulation.trace()['entries']), resulting_state_hash=state_hash(state))
                commands.extend(row['commands_executed'])
                if (state.winner_player_id is not None or row['fallback_used']
                        or row['invalid_action'] is None or state.active_player_id != player):
                    break
        finally:
            if model:
                if had_hook:
                    provider.before_request = old_hook
                else:
                    del provider.before_request
        unused = state.action_points_remaining
        if (state.winner_player_id is None and state.active_player_id == player
                and (failure is None or waves[-1]['fallback_used'])):
            command = ArenaEndTurn(player)
            simulation.execute(command)
            commands.append(command_to_dict(command))
        replan = waves[1] if len(waves) == 2 else None
        fallback_ap = sum(w.get('ap_spent', 0) for w in waves if w['fallback_used'])
        data = dict(schema_version='arena-bounded-replan-turn-trace-v1', control_version=CONTROL_VERSION,
                    player_id=player, turn=turn, waves=waves, replan_used=replan is not None,
                    planning_waves=len(waves), provider_requests=requests,
                    static_repairs=sum(w['static_repairs'] for w in waves),
                    ap_available=available, ap_spent=available-unused, ap_unused=unused,
                    ap_before_replan=replan['observation']['action_points_remaining'] if replan else None,
                    ap_recovered=replan.get('ap_spent', 0) if replan else 0,
                    model_ap_executed=available-unused-fallback_ap if model else 0,
                    fallback_ap_executed=fallback_ap, fallback_used=any(w['fallback_used'] for w in waves),
                    actions_executed=sum(w.get('actions_executed', 0) for w in waves),
                    commands_executed=commands, error_category=failure,
                    terminal_result=state.winner_player_id, resulting_state_hash=state_hash(state),
                    model_controlled=model)
        return ArenaBoundedReplanTurnTrace(data)


def aggregate_turns(traces):
    """AP recovered is committed AP after the first rejection, not tactical quality."""
    rows = [t.to_dict() if hasattr(t, 'to_dict') else t for t in traces]
    n = len(rows)
    replans = [r for r in rows if r['replan_used']]
    second_invalid = sum(r['waves'][1].get('invalid_action') is not None for r in replans)
    success = sum(not r['waves'][1]['error_category'] and r['waves'][1].get('invalid_action') is None for r in replans)
    result = dict(turns=n, model_controlled_turns=sum(r['model_controlled'] for r in rows),
                  one_wave_turns=sum(r['planning_waves'] == 1 for r in rows),
                  replan_turns=len(replans), replan_rate=len(replans)/n if n else 0,
                  replan_success_rate=success/len(replans) if replans else 0,
                  second_invalid_rate=second_invalid/len(replans) if replans else 0,
                  fallback_turns=sum(r['fallback_used'] for r in rows))
    for key in ('provider_requests', 'static_repairs', 'planning_waves', 'ap_spent', 'ap_unused',
                'ap_recovered', 'model_ap_executed', 'fallback_ap_executed'):
        result[key] = sum(r[key] for r in rows)
        result[key + '_per_turn'] = result[key]/n if n else 0
    result['ap_before_replan'] = [r['ap_before_replan'] for r in replans]
    result['terminal_ap_left'] = sum(r['ap_unused'] for r in rows if r['terminal_result'] is not None)
    result['nonterminal_ap_unused'] = sum(r['ap_unused'] for r in rows if r['terminal_result'] is None)
    attempts = [a for r in rows for w in r['waves'] for a in w['inference'].get('attempts', [])]
    result['latency_seconds'] = sum(a.get('wall_clock_seconds') or 0 for a in attempts)
    result['latency_seconds_per_turn'] = result['latency_seconds']/n if n else 0
    for token in ('input_tokens', 'output_tokens', 'total_tokens'):
        values = [a.get('metrics', {}).get(token) for a in attempts]
        result[token] = sum(values) if values and all(v is not None for v in values) else None
        result[token + '_per_turn'] = result[token]/n if n and result[token] is not None else None
    return result
