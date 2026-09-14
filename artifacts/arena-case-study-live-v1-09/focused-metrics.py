"""Descriptive side, request-tail and matched-slot tables from frozen results."""
import json
from pathlib import Path
from statistics import mean,median
from collections import Counter
root=Path(__file__).parent
B=int(root.name[-2:])
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rows=[json.loads(x) for x in (root/'results.jsonl').read_text().splitlines() if x]
arms=('strict','bounded','stepwise')
out={};lines=[f'# Focused descriptive comparisons through Batch {B} — INTERIM','']
def p(s=''):lines.extend([s,''])
def table(head,values):
    lines.append('| '+' | '.join(head)+' |');lines.append('| '+' | '.join('---' for _ in head)+' |')
    for row in values:lines.append('| '+' | '.join(json.dumps(v) if isinstance(v,(dict,list)) else str(round(v,5)) if isinstance(v,float) else str(v) for v in row)+' |')
    lines.append('')
for label,batches in [(f'batch_{b}',[b]) for b in range(6,B+1)]+[('cumulative',list(range(1,B+1)))]:
    rr=[r for r in rows if r['batch'] in batches];sides=[];cost=[];triplets=[]
    p('## '+label)
    for arm in arms:
        ar=[r for r in rr if r['arm']==arm]
        for side in ('red','blue'):
            sr=[r for r in ar if r['luna_side']==side];m=[r['metrics'][side] for r in sr]
            sides.append(dict(control=arm,side=side,matches=len(sr),wins=sum(r['luna_outcome']=='win' for r in sr),losses=sum(r['luna_outcome']=='loss' for r in sr),no_results=sum(r['luna_outcome']=='limit' for r in sr),forfeits=sum(r['terminal_cause']=='PROVIDER_FORFEIT' for r in sr),caps=sum(r['terminal_cause']=='REQUEST_LIMIT' for r in sr),requests=sum(r['requests'] for r in sr),requests_per_match=sum(r['requests'] for r in sr)/len(sr),requests_per_luna_turn=sum(r['requests'] for r in sr)/sum(x['turns'] for x in m)))
        mm=[r['metrics'][r['luna_side']] for r in ar];turns=sum(m['turns'] for m in mm)
        co=dict(control=arm,matches=len(ar),luna_turns=turns)
        for k in ('provider_requests','total_tokens','provider_latency_seconds'):
            total=sum(m[k] for m in mm);co[k]=total;co[k+'_per_match']=total/len(ar);co[k+'_per_turn']=total/turns
        cost.append(co)
    table(list(sides[0]),[list(s.values()) for s in sides])
    table(list(cost[0]),[list(s.values()) for s in cost])
    step=[r for r in rr if r['arm']=='stepwise'];capped=[r for r in step if r['terminal_cause']=='REQUEST_LIMIT'];uncapped=[r for r in step if r['terminal_cause']!='REQUEST_LIMIT']
    tail=dict(matches=len(step),capped=len(capped),cap_rate=len(capped)/len(step),capped_request_share=sum(r['requests'] for r in capped)/sum(r['requests'] for r in step),mean_including_caps=mean(r['requests'] for r in step),mean_excluding_caps=mean(r['requests'] for r in uncapped) if uncapped else None,median=median(r['requests'] for r in step),sorted_requests=sorted(r['requests'] for r in step))
    p('Stepwise request distribution: `'+json.dumps(tail)+'`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.')
    classifications=Counter({k:0 for k in ('all_three_lose','all_three_win','strict_only_win','bounded_only_win','stepwise_only_win','strict_bounded_win','bounded_stepwise_win','strict_stepwise_win','mixed_no_result','stepwise_cap_other_two_natural','stepwise_cap_other_two_finish','provider_forfeit_difference')})
    for slot in sorted({r['slot'] for r in rr}):
        tri=[next(r for r in rr if r['slot']==slot and r['arm']==a) for a in arms]
        wins=[a for a,r in zip(arms,tri) if r['luna_outcome']=='win'];causes=[r['terminal_cause'] for r in tri];outcomes=[r['luna_outcome'] for r in tri]
        if outcomes==['loss']*3:classifications['all_three_lose']+=1
        if len(wins)==3:classifications['all_three_win']+=1
        elif len(wins)==1:classifications[wins[0]+'_only_win']+=1
        elif len(wins)==2:classifications['_'.join(wins)+'_win']+=1
        classifications['mixed_no_result']+=('limit' in outcomes and len(set(outcomes))>1)
        classifications['stepwise_cap_other_two_natural']+=(causes[2]=='REQUEST_LIMIT' and all(c in ('CORE_DESTRUCTION','TEAM_ELIMINATION') for c in causes[:2]))
        classifications['stepwise_cap_other_two_finish']+=(causes[2]=='REQUEST_LIMIT' and all(c not in ('REQUEST_LIMIT','TURN_LIMIT') for c in causes[:2]))
        classifications['provider_forfeit_difference']+=(0<sum(c=='PROVIDER_FORFEIT' for c in causes)<3)
        triplets.append(dict(slot=slot,side=tri[0]['luna_side'],outcomes=outcomes,causes=causes,requests=[r['requests'] for r in tri],player_turns=[r['player_turns'] for r in tri],core_damage=[r['metrics'][r['luna_side']]['core_damage_dealt'] for r in tri],enemy_downs=[r['metrics'][r['luna_side']]['enemy_units_downed'] for r in tri],finishes=[r['metrics'][r['luna_side']]['finish'] for r in tri],revives=[r['metrics'][r['luna_side']]['revive'] for r in tri]))
    p('Matched-triplet classification counts (some categories overlap): `'+json.dumps(classifications)+'`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.')
    table(list(triplets[0]),[list(t.values()) for t in triplets])
    capfacts=[]
    for r in capped:
        m=r['metrics'][r['luna_side']];op=r['metrics']['blue' if r['luna_side']=='red' else 'red']
        capfacts.append(dict(match_id=r['match_id'],luna_turns=m['turns'],requests=r['requests'],repairs=m['repairs'],end_turns=m['explicit_end_turn_decisions'],luna_revives=m['revive'],heuristic_revives=op['revive'],luna_heals=m['heal'],heuristic_heals=op['heal'],luna_enemy_downs=m['enemy_units_downed'],heuristic_enemy_downs=op['enemy_units_downed'],luna_core_damage=m['core_damage_dealt']))
    if capfacts:table(list(capfacts[0]),[list(t.values()) for t in capfacts])
    out[label]=dict(sides=sides,cost=cost,stepwise_tail=tail,triplet_classifications=dict(classifications),triplets=triplets,cap_gameplay=capfacts)
p('Complete nonterminal Core/unit states and hashes: [cap-details.json](cap-details.json). AP/stop distributions and frozen Wilson/paired outputs are in the main reports. No model judge, hidden reasoning or causal explanation is inferred from these counts.')
(root/'focused-metrics.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
(root/'focused-comparisons.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(dict(success=True,cohorts=list(out))))
