"""Regenerate offline presentation lab examples using real authoritative commands."""
import json
from pathlib import Path
from aig.arena import (ArenaSimulation, ArenaMove, ArenaAttack, ArenaSnipe, ArenaHeal,
    ArenaRevive, ArenaFinish, ArenaShieldBash, ArenaFireball, ArenaEndTurn, create_scenario)
from aig.arena.presentation import PresentationSimulation, VERSION, terminal_reason
from aig.arena.public_state import public_state
from aig.arena.snapshots import state_hash
from aig.arena.state import UnitStatus
from aig.state import Position as P


def examples():
    result = {}
    for name in ('Move', 'Attack', 'Snipe', 'Heal', 'Revive', 'Down', 'Finish', 'Shield Bash', 'Fireball', 'Core damage', 'Victory', 'Turn', 'Knight Attack', 'Ranger Attack', 'Mage Attack', 'Cleric Attack'):
        state = create_scenario()
        state.units['blue-knight'].position = P(3, 2)
        state.units['red-knight'].position = P(4, 2)
        state.units['blue-ranger'].position = P(3, 0)
        state.units['blue-mage'].position = P(2, 3)
        state.units['blue-cleric'].position = P(2, 4)
        if name.endswith(' Attack'):
            kind = name.split()[0].lower()
            state.units[f'blue-{kind}'].position = P(3, 2)
            if kind != 'knight': state.units['blue-knight'].position = P(1, 1)
            command = ArenaAttack('blue', f'blue-{kind}', 'red-knight')
        elif name == 'Move': command = ArenaMove('blue', 'blue-knight', P(2, 2))
        elif name in ('Attack', 'Down'): command = ArenaAttack('blue', 'blue-knight', 'red-knight')
        elif name == 'Snipe': command = ArenaSnipe('blue', 'blue-ranger', 'red-ranger')
        elif name == 'Heal':
            state.units['blue-mage'].hp = 2
            command = ArenaHeal('blue', 'blue-cleric', 'blue-mage')
        elif name in ('Revive', 'Finish'):
            target = 'blue-mage' if name == 'Revive' else 'red-knight'
            state.units[target].hp = 0
            state.units[target].status = UnitStatus.DOWNED
            command = ArenaRevive('blue', 'blue-cleric', target) if name == 'Revive' else ArenaFinish('blue', 'blue-knight', target)
        elif name == 'Shield Bash': command = ArenaShieldBash('blue', 'blue-knight', 'red-knight')
        elif name == 'Fireball':
            state.units['blue-mage'].position = P(2, 2)
            command = ArenaFireball('blue', 'blue-mage', P(3, 2))
        elif name in ('Core damage', 'Victory'):
            state.units['blue-ranger'].position = P(5, 2)
            if name == 'Victory': state.cores['red-core'].hp = 1
            command = ArenaAttack('blue', 'blue-ranger', 'red-core')
        else: command = ArenaEndTurn('blue')
        if name == 'Down': state.units['red-knight'].hp = 1
        sim = PresentationSimulation(ArenaSimulation(state))
        def view():
            value = public_state(sim.state)
            # Lab has no gameplay controls; legal lists are unnecessary fixture weight.
            for unit in value['units']:
                unit['actions'] = {key: [] for key in unit['actions']}
            return dict(value, state_hash=state_hash(sim.state), terminal_reason=terminal_reason(sim.state),
                        battle_log=[e['log'] for e in sim.presentation_events], controllers={})
        start = view()
        try: sim.execute(command)
        except ValueError as error: raise ValueError(name) from error
        final = view()
        result[name] = dict(start=start, final=final, batch=dict(version=VERSION,
            start_state_hash=start['state_hash'], final_state_hash=final['state_hash'], events=sim.presentation_events))
    return result

if __name__ == '__main__':
    Path('frontend/src/js/arena-lab-fixtures.json').write_text(json.dumps(examples(), separators=(',', ':')) + '\n')



