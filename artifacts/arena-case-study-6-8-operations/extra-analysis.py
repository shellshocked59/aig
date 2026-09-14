"""Descriptive paired mechanical differences and diagnostic labels; no inference."""
import json,sys
from pathlib import Path
from collections import Counter
from statistics import mean,median
root=Path(sys.argv[1]);read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rows=[json.loads(s) for s in (root/'results.jsonl').read_text().splitlines() if s]
forensic=read(root/'repair-forensics.json');B=max(r['batch'] for r in rows)
out={};lines=[f'# Additional descriptive evidence through Batch {B} — INTERIM','',
    'These are arithmetic summaries of frozen result fields and saved validators. They add no model judge, hypothesis tests or changes to official categories. Paired differences compare independent Luna trajectories sharing a frozen slot/side.','']
def p(s):lines.extend([s,''])
def table(head,rs):
    lines.append('| '+' | '.join(head)+' |');lines.append('| '+' | '.join('---' for _ in head)+' |')
    for row in rs:lines.append('| '+' | '.join(json.dumps(v) if isinstance(v,(dict,list)) else str(round(v,5)) if isinstance(v,float) else str(v) for v in row)+' |')
    lines.append('')
for name,batches in [(f'batch_{b}',[b]) for b in range(6,B+1)]+[('cumulative',list(range(1,B+1)))]:
    rr=[r for r in rows if r['batch'] in batches];indexed={(r['slot'],r['arm']):r for r in rr};slots=sorted({r['slot'] for r in rr})
    pairs=[]
    for a,b in [('bounded','strict'),('stepwise','bounded')]:
        for field in ('requests','player_turns','core_damage_dealt','enemy_units_downed','finish'):
            values=[]
            for slot in slots:
                ar=indexed[slot,a];br=indexed[slot,b]
                av=ar[field] if field in ('requests','player_turns') else ar['metrics'][ar['luna_side']][field]
                bv=br[field] if field in ('requests','player_turns') else br['metrics'][br['luna_side']][field]
                values.append(av-bv)
            pairs.append(dict(comparison=a+' minus '+b,field=field,pairs=len(values),sum_difference=sum(values),mean_difference=mean(values),median_difference=median(values),positive=sum(x>0 for x in values),zero=sum(x==0 for x in values),negative=sum(x<0 for x in values),differences=values))
    cases=[c for c in forensic['exhaustions'] if c['batch'] in batches]
    patterns={}
    detailed=[]
    for c in cases:
        a=c['repair'];diagnostics=a['diagnostics'];messages=' '.join(d.get('message','') for d in diagnostics).lower();codes={d.get('code') for d in diagnostics}
        if 'AP_VIOLATION' in a['classifications']:tag='AP'
        elif 'los' in codes or 'line of sight' in messages:tag='LOS'
        elif 'impact outside fireball range/board' in messages:tag='Fireball range/board (not disambiguated)'
        elif 'occupied, blocked, unchanged, or beyond move range' in messages:tag='Ambiguous move validation'
        elif 'range' in codes or 'target outside action range' in messages or 'outside range' in messages:tag='Range'
        else:tag=' / '.join(a['classifications']) or 'Other / unavailable'
        detailed.append(dict(batch=c['batch'],match_id=c['match_id'],control=c['control'],side=c['luna_side'],tag=tag,official_category=a['error_category'],validator_messages=[d.get('message') for d in diagnostics],response_received=a['transport_completed']))
    for a in ('strict','bounded','stepwise','all'):
        cc=[x for x in detailed if a=='all' or x['control']==a];patterns[a]=dict(Counter(x['tag'] for x in cc))
    out[name]=dict(paired_mechanics=pairs,repair_diagnostic_patterns=patterns,repair_cases=detailed)
    p('## '+name)
    table(list(pairs[0]),[list(x.values()) for x in pairs])
    p('Diagnostic grouping: `'+json.dumps(patterns)+'`. Categories preserve diagnostic ambiguity: Fireball range/board and occupied/blocked/unchanged/out-of-range movement cannot be uniquely separated from those messages.')
    if detailed:table(list(detailed[0]),[list(x.values()) for x in detailed])
p('All statistical inference remains governed by the frozen analysis plan. These supplementary differences are descriptive and do not attribute AP recovery or tactical quality causally to a control.')
(root/'extra-analysis.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
(root/'extra-analysis.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(dict(success=True,cohorts=list(out))))
