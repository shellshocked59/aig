"""Detached, explicit perfect-information browser DTO and legal action queries."""

from dataclasses import asdict

from aig.state import Position
from aig.arena.queries import legal_actions as query_actions, abilities


def legal_actions(state, unit):
    return {kind: [dict(x=p.x, y=p.y) for p in targets] if kind in ("move", "fireball") else targets
            for kind, targets in query_actions(state, unit).items()}


def public_state(state):
    state.validate()
    def piece(e):
        return dict(id=e.id, owner_id=e.owner_id, x=e.position.x, y=e.position.y, hp=e.hp)
    return dict(
        environment="arena", rules_version=state.config.rules_version, scenario_version=state.config.scenario_version,
        turn=state.turn, active_player_id=state.active_player_id,
        action_points_remaining=state.action_points_remaining, winner_player_id=state.winner_player_id,
        players=[dict(id=p.id, name=p.name) for p in state.players],
        board=dict(width=state.board.width, height=state.board.height,
                   tiles=[dict(x=x, y=y, terrain=t.terrain.value, bonus=t.bonus.value if t.bonus else None)
                          for y in range(state.board.height) for x in range(state.board.width)
                          for t in [state.board.at(Position(x, y))]]),
        units=[dict(**piece(u), unit_type=u.unit_type.value, max_hp=u.max_hp,
                    status=u.status.value, stats=asdict(u.stats), abilities=abilities(u), actions=legal_actions(state, u))
               for u in sorted(state.units.values(), key=lambda u: u.id)],
        cores=[dict(**piece(c), max_hp=30) for c in sorted(state.cores.values(), key=lambda c: c.id)],
    )
