"""Authoring recipes only; live runs consume the frozen JSON, never regenerate it."""
from aig.arena.ai.probes import create_probe
from aig.arena.state import ArenaUnit, UnitType as U, UnitStatus as S, STATS, Board, Tile, Bonus, Terrain
from aig.state import Position as P
from aig.arena.snapshots import to_snapshot, digest
from aig.arena.mechanics_oracle import evaluate, satisfies


def action(kind, target='enemy', actor='actor', position=None):
    return dict(type=kind, unit_id=actor, **({'destination' if kind=='move' else 'target_position':dict(x=position[0], y=position[1])} if position else {'target_id':target}))


def fixture(kind=U.RANGER, hp=8, ap=2, enemy=(5,2), actor=(1,2)):
    s = create_probe('snipe_vs_basic')
    s.units = {}
    for uid, owner, cls, pos, health in [('actor','blue',kind,actor,STATS[kind].hp),
            ('enemy','red',U.KNIGHT,enemy,hp), ('reserve','red',U.CLERIC,(8,4),11)]:
        s.units[uid] = ArenaUnit(uid,owner,cls,P(*pos),health,S.ACTIVE if health else S.DOWNED)
    s.action_points_remaining=ap
    return s


def tile(s, pos, bonus=None, blocked=False):
    tiles=list(s.board.tiles)
    tiles[pos[1]*9+pos[0]]=Tile(Terrain.BLOCKED if blocked else Terrain.FLOOR,bonus)
    s.board=Board(tuple(tiles))


def build_probes():
    probes=[]
    def add(category, name, s, seq, objective=None, info='C', alternatives=()):
        snap=to_snapshot(s)
        result=evaluate(snap,seq)
        if objective is None:
            target=next(e for e in result['final_state']['units'] if e['id']=='enemy')
            objective=dict(kind='down',target='enemy') if target['hp']==0 else dict(kind='hp_at_most',target='enemy',hp=target['hp'])
        if category == 'FIREBALL' and name not in ('empty', 'friendly-only'):
            target=next(e for e in result['final_state']['units'] if e['id']=='enemy')
            objective=dict(kind='hp_at_most',target='enemy',hp=target['hp'],
                max_friendly_damage=sum(step['friendly_damage']['maximum'] for step in result['steps']))
        refs=[list(x) for x in (seq,*alternatives) if satisfies(evaluate(snap,x),objective)]
        probes.append(dict(id=f'{category}-{sum(p["category"]==category for p in probes)+1:03}',
            category=category,name=name,initial_state=snap,initial_state_hash=digest(snap),
            player=s.active_player_id,ap=s.action_points_remaining,objective=objective,
            information_class=info,tags=[category,'full-turn-v1'],reference_sequence=seq,
            expected_mechanics=result,acceptable_reference_sequences=refs,
            minimum_ap_reference=min((evaluate(snap,x)['ap_used'] for x in refs),default=None),
            guaranteed_objective_witness_exists=bool(refs),
            impossible_reference_actions=[result['failure']] if result['failure'] else [],
            minimum_ap_global=None,reference_scope='witnesses, not exhaustive; all plans scored by outcome predicate'))
    # Thresholds are measured from resolution, not handwritten special damage rules.
    calibration=fixture(hp=18)
    damage=evaluate(to_snapshot(calibration),[action('snipe')])['steps'][0]['affected'][0]['damage']['minimum']
    for label,hp in [('exact',damage),('overkill',damage-2),('one-above',damage+1),('nonlethal',18)]:
        add('LETHAL',label,fixture(hp=hp),[action('snipe')])
    for label,hp,ap,seq in [('two-attacks',10,2,['attack','attack']),('snipe-attack',13,3,['snipe','attack']),
            ('ap-short',13,2,['snipe','attack']),('down-stale-attack',5,2,['attack','attack'])]:
        s=fixture(hp=hp,ap=ap,enemy=(3,2))
        add('MULTI',label,s,[action(k) for k in seq],dict(kind='down',target='enemy'))
    for ap,seq in [(1,['attack']),(2,['attack','attack']),(3,['attack']*3),(4,['snipe']*2),(5,['snipe','snipe','attack']),(5,['snipe']*3)]:
        add('AP',f'{ap}-AP-'+ '+'.join(seq),fixture(hp=18,ap=ap,enemy=(3,2)),[action(k) for k in seq],dict(kind='diagnostic'))
    for category,bonus in [('POWER',Bonus.POWER),('WARD',Bonus.WARD)]:
        for kind,ability,hp in [(U.RANGER,'snipe',damage),(U.CLERIC,'attack',STATS[U.CLERIC].damage)]:
            s=fixture(kind,hp+1 if bonus==Bonus.POWER else hp,2,enemy=(3,2),actor=(2,2))
            tile(s,(2,2) if bonus==Bonus.POWER else (3,2),bonus)
            add(category,ability,s,[action(ability)],info='B')
    for siege,hp in [(False,9),(True,9),(False,5),(True,10)]:
        s=fixture(ap=1,actor=(5,2),enemy=(7,4));s.cores['red-core'].hp=hp
        if siege: tile(s,(5,2),Bonus.SIEGE)
        add('CORE',f'siege-{siege}-hp-{hp}',s,[action('attack','red-core')],dict(kind='win',player='blue'),info='B')
    for label,hp,ap,seq in [('down',6,1,['attack']),('finish',0,1,['finish']),('down-finish',6,2,['attack','finish']),('short-down-finish',6,1,['attack','finish'])]:
        s=fixture(U.KNIGHT,hp,ap,enemy=(3,2),actor=(2,2))
        add('DOWNED',label,s,[action(k) for k in seq],dict(kind='down' if label=='down' else 'removed',target='enemy'))
    for label,ap,seq in [('revive',2,[action('revive','ally')]),('revive-act',3,[action('revive','ally'),action('attack',actor='ally')]),('revive-short',1,[action('revive','ally')])]:
        s=fixture(U.CLERIC,18,ap,enemy=(4,2),actor=(2,2))
        s.units['ally']=ArenaUnit('ally','blue',U.MAGE,P(3,2),0,S.DOWNED)
        add('REVIVE',label,s,seq,dict(kind='revived',target='ally',hp=5))
    for label,impact,ally_hp,enemy_hp,bonus in [('enemy-only',(4,2),None,18,None),('mixed',(3,2),18,18,None),
            ('friendly-only',(1,2),18,18,None),('empty',(0,0),None,18,None),
            ('enemy-down',(3,2),18,4,None),('friendly-down',(3,2),4,18,None),
            ('ward',(3,2),18,4,Bonus.WARD),('power',(3,2),18,6,Bonus.POWER)]:
        s=fixture(U.MAGE,enemy_hp,2,enemy=(4,2),actor=(2,2))
        if ally_hp is not None:s.units['ally']=ArenaUnit('ally','blue',U.KNIGHT,P(3,2),ally_hp)
        if bonus:tile(s,(4,2) if bonus==Bonus.WARD else (2,2),bonus)
        add('FIREBALL',label,s,[action('fireball',position=impact)],dict(kind='diagnostic'),info='B')
    for label,seq,blocked in [('out-of-range',[action('snipe')],False),('move-snipe',[action('move',position=(3,2)),action('snipe')],False),('blocked-los',[action('snipe')],True)]:
        s=fixture(hp=damage,ap=3,enemy=(6,2) if not blocked else (5,2))
        if blocked:tile(s,(3,2),blocked=True)
        add('POSITION',label,s,seq,dict(kind='down',target='enemy'),info='B')
    # Ancillary consequences within existing categories.
    s=fixture(U.KNIGHT,18,1,enemy=(3,2),actor=(2,2))
    add('POSITION','bash-push',s,[action('shield_bash')],dict(kind='diagnostic'),info='B')
    s=fixture(U.CLERIC,18,1,enemy=(4,2),actor=(2,2));s.units['actor'].hp=9
    add('REVIVE','heal-clamp',s,[action('heal','actor')],dict(kind='hp_at_least',target='actor',hp=11),info='B')
    return probes

