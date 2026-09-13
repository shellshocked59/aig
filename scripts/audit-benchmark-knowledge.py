"""Offline knowledge-boundary audit of benchmark commands and planning inputs."""
import argparse
import json
from pathlib import Path

from aig import commands
from aig.ai.benchmark import canonical_hash
from aig.ai.plan_schema import canonical_json, parse_plan
from aig.ai.strategy import StrategicStateBuilder
from aig.knowledge import visible_positions
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import Position, Technology, UnitType


def audit(directory):
    state = from_snapshot(json.loads((directory/'initial-state.json').read_text(encoding='utf-8')))
    plans = {r['activation']: r for r in map(json.loads, (directory/'plans.jsonl').read_text(encoding='utf-8').splitlines())}
    activations = {r['activation']: r for r in map(json.loads, (directory/'activations.jsonl').read_text(encoding='utf-8').splitlines())}
    previous = None
    checked, boundary_checks, maximum_barbarians = 0, 0, 0
    for line in (directory/'commands.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        index = row['activation']
        if index != previous:
            activation = activations[index]
            assert state.active_player_id == activation['player_id']
            assert state.turn == activation['turn']
            if not activation.get('system_phase'):
                actor = activation['player_id']
                view = StrategicStateBuilder().build(state, actor)
                parse_plan(canonical_json(activation['plan']), view)
                if index in plans:
                    assert view == plans[index]['strategic_state']
                    assert canonical_hash(view) == plans[index]['strategic_state_sha256']
                    prior = plans[index]['previous_plan']
                    if prior is not None:
                        parse_plan(canonical_json(prior), view)
                    if plans[index]['replan_reason'] == 'invalid_target':
                        assert prior is None, 'invalidated plan reached provider context'
                    invalidated = plans[index].get('invalidated_previous_plan')
                    if invalidated is not None:
                        assert prior is None
                        assert plans[index]['replan_reason'] == 'invalid_target'
                        try:
                            parse_plan(canonical_json(invalidated), view)
                        except ValueError:
                            pass
                        else:
                            raise AssertionError('valid plan incorrectly marked invalidated')
                    checked += 1
                visible = visible_positions(state, actor)
                assert all(Position(u['x'], u['y']) in visible
                           for u in view['enemy_units'] + view['visible_barbarian_units'])
                assert all(Position(**r['position']) in state.players[actor].knowledge.explored_positions
                           for r in view['known_resources'])
                boundary_checks += 1
            previous = index
        payload = row['command'].copy(); kind = payload.pop('type')
        if kind == 'MoveUnit': payload['destination'] = Position(**payload['destination'])
        if kind == 'SetCityProduction' and payload['unit_type'] is not None:
            payload['unit_type'] = UnitType(payload['unit_type'])
        if kind == 'SetResearch' and payload['technology'] is not None:
            payload['technology'] = Technology(payload['technology'])
        commands.apply_command(state, getattr(commands, kind)(**payload))
        state.validate()
        maximum_barbarians = max(maximum_barbarians, sum(state.is_barbarian(u.owner_id) for u in state.units.values()))
        if row['outcome'].get('conquest_events', {}).get('eliminations'):
            assert from_snapshot(to_snapshot(state)) == state
    assert to_snapshot(state) == json.loads((directory/'final-state.json').read_text(encoding='utf-8'))
    return dict(replans_verified=checked, activation_knowledge_checks=boundary_checks,
                maximum_barbarians=maximum_barbarians, final_hash=canonical_hash(to_snapshot(state)),
                replay=True, valid_plan_references=True, valid_previous_plan_references=True,
                knowledge_boundaries=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory), indent=2))
