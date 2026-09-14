"""Offline consequence oracle. No alternate Arena combat implementation."""
from dataclasses import dataclass, asdict
from aig.arena.ai.contracts import action_from_dict, action_command
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import from_snapshot, to_snapshot, state_hash

ORACLE_VERSION = 'arena-mechanics-oracle-v1'

@dataclass(frozen=True)
class Bounds:
    minimum: int
    maximum: int

    def __post_init__(self):
        if type(self.minimum) is not int or type(self.maximum) is not int or not 0 <= self.minimum <= self.maximum:
            raise ValueError('invalid bounds')

    def lethal(self, hp):
        if type(hp) is not int or hp <= 0:
            raise ValueError('lethal requires positive initial HP')
        return dict(guaranteed=self.minimum >= hp, possible=self.maximum >= hp,
                    classification='guaranteed' if self.minimum >= hp else 'possible' if self.maximum >= hp else 'impossible')

    def hp_after(self, hp):
        return Bounds(max(0, hp-self.maximum), max(0, hp-self.minimum))


def exact(value):
    return asdict(Bounds(value, value))


def evaluate(snapshot, actions):
    """HP loss is effective (clamped) damage, not nominal overkill damage.

    A future mechanics adapter must supply authoritative joint outcome branches;
    do not independently sum ranges or invent their probability distribution.
    """
    sim = ArenaSimulation(from_snapshot(snapshot))
    actor = sim.state.active_player_id
    steps, failure = [], None
    for index, encoded in enumerate(actions):
        if sim.state.winner_player_id is not None:
            break
        before = to_snapshot(sim.state)
        try:
            command = action_command(action_from_dict(encoded), actor)
            entry = sim.execute(command)
        except ValueError as error:
            failure = dict(index=index, reason=str(error), action=encoded)
            break
        after = to_snapshot(sim.state)
        entities = {e['id']: e for k in ('units', 'cores') for e in after[k]}
        affected = []
        for kind in ('units', 'cores'):
            for old in before[kind]:
                new = entities.get(old['id'])
                if new == old:
                    continue
                loss = max(0, old['hp']-new['hp']) if new else 0
                gain = max(0, new['hp']-old['hp']) if new else 0
                down = bool(new and kind == 'units' and old['status'] == 'active' and new['status'] == 'downed')
                core = bool(new and kind == 'cores' and old['hp'] > 0 and new['hp'] == 0)
                affected.append(dict(id=old['id'], friendly=old['owner_id']==actor,
                    damage=exact(loss), healing=exact(gain), target_hp_before=old['hp'],
                    target_hp_after=exact(new['hp']) if new else None,
                    guaranteed_down=down, possible_down=down,
                    guaranteed_core_destroy=core, possible_core_destroy=core,
                    status_after=new.get('status', 'core') if new else 'removed',
                    position_before=old['position'], position_after=new['position'] if new else None))
        steps.append(dict(action=encoded, ap_cost=entry['ap_used'], affected=affected,
            friendly_damage=exact(entry['friendly_fire_damage']),
            enemy_damage=exact(entry['damage_dealt']-entry['friendly_fire_damage']),
            after_hash=entry['after_hash']))
    trace = sim.trace()
    verified = state_hash(replay(trace).state) == state_hash(sim.state)
    return dict(oracle_version=ORACLE_VERSION, damage_semantics='effective_hp_loss',
        steps=steps, failure=failure, ap_used=sum(s['ap_cost'] for s in steps),
        terminal=sim.state.winner_player_id is not None, winner=sim.state.winner_player_id,
        ignored_terminal_suffix=len(actions)-len(steps) if sim.state.winner_player_id else 0,
        final_state=to_snapshot(sim.state), final_hash=state_hash(sim.state), trace=trace,
        replay_verified=verified)


def satisfies(result, objective):
    if result['failure']:
        return False
    entities = {e['id']: e for k in ('units', 'cores') for e in result['final_state'][k]}
    target = entities.get(objective.get('target'))
    kind = objective['kind']
    if kind == 'down':
        return target is None or target.get('status') == 'downed'
    if kind == 'removed':
        return target is None
    if kind == 'revived':
        return bool(target and target.get('status') == 'active' and target['hp'] >= objective['hp'])
    if kind == 'hp_at_most':
        friendly = sum(step['friendly_damage']['maximum'] for step in result['steps'])
        return (target is None or target['hp'] <= objective['hp']) and friendly <= objective.get('max_friendly_damage', float('inf'))
    if kind == 'hp_at_least':
        return bool(target and target['hp'] >= objective['hp'])
    if kind == 'win':
        return result['winner'] == objective['player']
    if kind == 'diagnostic':
        return None
    raise ValueError('unknown objective')


def score(probe, actions):
    result = evaluate(probe['initial_state'], actions)
    success = satisfies(result, probe['objective'])
    failure = result['failure']
    classification = ('execution-sequence failure' if failure and failure['index'] else
                      'arithmetic/rule-inconsistent' if failure else
                      'correct mechanical recognition' if success else
                      'ambiguous tactical choice' if success is None or not probe['acceptable_reference_sequences'] else 'legal but missed opportunity')
    # Prefix consistency is positive evidence only; the frozen witness list is not exhaustive.
    prefix = bool(actions and any(seq and seq[0] == actions[0] for seq in probe['acceptable_reference_sequences']))
    return dict(classification=classification, objective_satisfied=success,
                first_action_reference_consistent=prefix if prefix else None,
                first_action_objective_satisfied=satisfies(evaluate(probe['initial_state'], actions[:1]), probe['objective']) if actions else None,
                information_class=probe['information_class'], execution=result,
                reasoning_failure_inferred=False)
