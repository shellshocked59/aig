"""Sequential command execution: invalid action -> truncate -> EndTurn, no repair."""

from dataclasses import dataclass, asdict

from aig.arena.ai.contracts import ArenaTurnPlan, action_command
from aig.arena.commands import ArenaEndTurn, apply_command
from aig.arena.snapshots import command_to_dict


@dataclass(frozen=True)
class ArenaTurnExecutionResult:
    player_id: str
    plan: ArenaTurnPlan
    actions_attempted: tuple[dict, ...]
    commands_executed: tuple[dict, ...]
    invalid_action: dict | None
    truncation_reason: str | None
    ap_available: int
    ap_spent: int
    ap_unused: int
    terminal_result: str | None
    resulting_active_player: str | None

    def to_dict(self):
        result = asdict(self)
        result["plan"] = self.plan.to_dict()
        result["actions_attempted"] = list(result["actions_attempted"])
        result["commands_executed"] = list(result["commands_executed"])
        return result


def execute_arena_turn(state, plan, *, execute_command=None):
    """Optional command sink is the session's ArenaSimulation.execute for exact replay.

    Structural rejection occurs before any command. State-dependent rejection commits
    the preceding valid prefix and discards the suffix. Terminal turns never EndTurn.
    """
    if type(plan) is not ArenaTurnPlan:
        raise ValueError("provider must return ArenaTurnPlan")
    plan.__post_init__()
    state.validate()
    if state.active_player_id is None:
        raise ValueError("cannot execute a plan after victory")
    execute = execute_command if execute_command is not None else lambda c: apply_command(state, c)
    player, available = state.active_player_id, state.action_points_remaining
    attempts, commands = [], []
    invalid = reason = None
    for index, action in enumerate(plan.actions):
        before = state.action_points_remaining
        attempt = dict(index=index, action=action.to_dict(), ap_before=before, ap_after=before, executed=False)
        attempts.append(attempt)
        command = action_command(action, player)
        try:
            execute(command)
        except ValueError as error:
            invalid = dict(index=index, action=action.to_dict(), reason=str(error))
            reason = "invalid_action"
            attempt["error"] = str(error)
            break
        commands.append(command_to_dict(command))
        attempt.update(ap_after=state.action_points_remaining, executed=True)
        if state.winner_player_id is not None:
            reason = "terminal" if index + 1 < len(plan.actions) else None
            break
    unused = state.action_points_remaining
    if state.winner_player_id is None:
        command = ArenaEndTurn(player)
        execute(command)
        commands.append(command_to_dict(command))
    return ArenaTurnExecutionResult(player, plan, tuple(attempts), tuple(commands), invalid, reason,
                                    available, available - unused, unused, state.winner_player_id,
                                    state.active_player_id)
