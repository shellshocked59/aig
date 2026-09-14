"""Render compact evidence tables into the additive forensic report."""
import json
from pathlib import Path
HERE=Path(__file__).parent
d=json.loads((HERE/'forensics.json').read_text())
p=Path('docs/arena-candidate-focused-forensics.md')
s=p.read_text(encoding='utf-8')
def action(a):
    if a['type']=='end_turn':return 'E'
    kind=dict(attack='A',snipe='S',shield_bash='B',finish='F',move='M')[a['type']]
    if a['type']=='move':return f"M({a['unit_id']},({a['destination']['x']},{a['destination']['y']}))"
    actor=a['unit_id'];target=a['target_id']
    return kind if actor=='actor' and target=='enemy' else f'{kind}({actor},{target})'
def seq(a):return ', '.join(action(x) for x in a['parsed_json']['actions']) or '[]'
def valid(a):return 'V' if a['valid'] else 'AP' if a['reconstructed_diagnostic']['category']=='ap_budget' else 'LC'
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','|'+'|'.join('---' for _ in head)+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])
rows=[]
for r in d['trials']:
    first=r['waves'][0]['attempts'][0]
    repairs=[x for x in d['repairs'] if x['trial']==r['trial']]
    rr=repairs[0] if repairs else None
    accepted='yes' if r['waves'][0]['accepted_plan'] else 'no'
    if len(r['waves'])>1:accepted+='; later '+('failed' if r['stop_reason']=='PROVIDER_FAILURE' else 'yes')
    inv='; '.join('w'+str(w['index'])+': '+w['execution_invalidity']['reason'] for w in r['waves'] if w['execution_invalidity']) or 'no'
    prov={'controller finalization (not explicit)':'normal','initial output':'initial E','repair':'repair E','none':'none'}[r['end_turn_provenance']]
    rows.append([r['trial_binding']['probe'],r['trial_binding']['control_mode'],r['ap_available'],valid(first),seq(first),
        rr['id']+f" w{rr['wave']} / "+('F-AP' if valid(rr['original'])=='AP' else 'F-LC') if rr else 'no',
        seq(rr['repaired'])+' / '+valid(rr['repaired']) if rr else '—',accepted,inv,prov,
        f"{r['ap_executed']} / {r['ap_remaining']}",r['stop_reason'],r['provider_attempts'],'exact'])
s=s.replace('<!-- TRIAL_TABLE -->',table(['Snapshot','Control','Start AP','First validity','First raw actions','Repair / feedback','Repair actions / validity','Accepted','Execution invalidity','End provenance','AP spent / left','Final stop','Requests','Replay'],rows))
classes={'R1':'Repeated same invalidity','R2':'Repeated same invalidity; E removed','R3':'Repeated same invalidity; target changed','R4':'EndTurn escape','R5':'Valid; immediate intent changed, related positioning','R6':'Repeated same class; attacker changed'}
rows=[]
for r in d['repairs']:
    a,b=r['original'],r['repaired']
    rows.append([r['id'],r['trial']+f" w{r['wave']}",f"{a['request']} → {b['request']}",r['ap_available'],seq(a),a['planned_ap'],valid(a),
        'F-AP' if valid(a)=='AP' else 'F-LC',seq(b),b['planned_ap'],valid(b),classes[r['id']]])
s=s.replace('<!-- REPAIR_TABLE -->',table(['ID','Decision','Requests','Current AP','Original','AP total','Invalidity','Feedback','Repair','AP total','Result','Classification'],rows))
s=s.replace('<!-- OBSERVATION_TABLE -->',table(['Snapshot','Strict = bounded = stepwise','Canonical observation SHA-256'],[[x['probe'],'yes',f"`{x['hash']}`"] for x in d['observation_pairs']]))
s=s.replace('<!-- V6_PROMPT -->','```text\n'+d['prompts']['arena-turn-prompt-v6']+'\n```')
p.write_text(s,encoding='utf-8')
print('Rendered',len(d['trials']),'trial rows,',len(d['repairs']),'repair rows')
