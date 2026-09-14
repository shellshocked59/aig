"""Prespecified outcomes, paired effects, and ten transparent matplotlib figures."""
from collections import Counter
import csv
import json
import os
from math import sqrt, comb
from pathlib import Path
from statistics import median

from aig.arena.case_study_contract import ARMS
from aig.arena.ai.candidate_control import STOP_REASONS


def wilson(wins,n):
    if not n: return None
    z=1.959963984540054
    p=wins/n; divisor=1+z*z/n
    center=(p+z*z/(2*n))/divisor
    radius=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/divisor
    return [max(0,center-radius),min(1,center+radius)]


def exact_mcnemar(gains,losses):
    n=gains+losses
    return min(1.,2*sum(comb(n,k) for k in range(min(gains,losses)+1))/2**n) if n else 1.


def total(values):
    return sum(values) if values and all(v is not None for v in values) else None


def ratio(a,b):
    return a/b if a is not None and b is not None and b>0 else None


def metrics_for(row,heuristic=False):
    side=('red' if row['luna_side']=='blue' else 'blue') if heuristic else row['luna_side']
    return row['metrics'][side]


def summarize(rows,heuristic=False):
    outcomes=Counter('win' if (r['winner'] is not None and (r['winner']!=r['luna_side'] if heuristic
                     else r['winner']==r['luna_side'])) else 'loss' if r['winner'] else 'limit' for r in rows)
    n=len(rows); metrics=[metrics_for(r,heuristic) for r in rows]
    keys=sorted({k for m in metrics for k,v in m.items() if (type(v) in (int,float) or v is None)
                 and not k.endswith(('_per_turn','_rate'))})
    sums={k:total([m.get(k) for m in metrics]) for k in keys}
    turns=sums.get('turns',0)
    result=dict(matches=n,wins=outcomes['win'],losses=outcomes['loss'],limits=outcomes['limit'],
        win_rate=ratio(outcomes['win'],n),wilson_95=wilson(outcomes['win'],n),totals=sums,
        terminal_causes=dict(Counter(r['terminal_cause'] for r in rows)),
        median_player_turns=median(r['player_turns'] for r in rows) if rows else None,
        per_turn={k:ratio(sums.get(k),turns) for k in ('provider_requests','input_tokens','output_tokens','total_tokens',
            'provider_latency_seconds','backend_thinking_seconds','execution_truncations','failure_derived_unused_ap')},
        per_match={k:ratio(sums.get(k),n) for k in ('provider_requests','input_tokens','output_tokens','total_tokens',
            'core_damage_dealt','core_damage_received','core_hp_remaining','enemy_damage','friendly_damage')},
        unused_ap_by_reason={s:sum(m['unused_ap_by_reason'][s] for m in metrics) for s in STOP_REASONS})
    if not heuristic:
        result['repair_success_rate']=ratio(sums.get('repair_success'),sums.get('repairs'))
        result['first_response_static_valid_rate']=ratio(sums.get('first_response_valid'),sums.get('first_responses'))
        result['replan_rate']=ratio(sums.get('replans'),turns)
        result['second_invalid_rate']=ratio(sums.get('second_invalidities'),sums.get('replans'))
        result['requests_per_completed_turn']=ratio(sums.get('requests_in_completed_turns'),sums.get('completed_turns'))
    return result


def paired(rows,left,right,*,inference=True):
    import numpy as np
    indexed={(r['slot'],r['arm']):r for r in rows}
    slots=sorted({r['slot'] for r in rows if (r['slot'],left) in indexed and (r['slot'],right) in indexed})
    pairs=[(indexed[s,left],indexed[s,right]) for s in slots]
    values=np.array([[a['luna_outcome']=='win',b['luna_outcome']=='win'] for a,b in pairs],dtype=int).reshape(-1,2)
    gains=int(sum((values[:,0]==1)&(values[:,1]==0)))
    losses=int(sum((values[:,0]==0)&(values[:,1]==1)))
    result=dict(comparison=f'{left}-{right}',pairs=len(pairs),win_gains=gains,win_losses=losses,
        win_rate_difference=float((values[:,0]-values[:,1]).mean()) if pairs else None,
        exact_mcnemar_p=exact_mcnemar(gains,losses) if inference and pairs else None,
        outcome_cross_table=dict(Counter(a['luna_outcome']+'/'+b['luna_outcome'] for a,b in pairs)),
        provider_forfeit_pairs=sum(a['terminal_cause']=='PROVIDER_FORFEIT' or b['terminal_cause']=='PROVIDER_FORFEIT' for a,b in pairs),
        limit_pairs=sum(a['winner'] is None or b['winner'] is None for a,b in pairs),
        median_paired_player_turn_difference=median(a['player_turns']-b['player_turns'] for a,b in pairs) if pairs else None)
    for field in ('provider_requests','total_tokens','backend_thinking_seconds'):
        totals=[total([metrics_for(r).get(field) for pair in pairs for r in [pair[i]]]) for i in (0,1)]
        turns=[sum(metrics_for(pair[i])['turns'] for pair in pairs) for i in (0,1)]
        result[field+'_per_turn_ratio']=ratio(ratio(totals[0],turns[0]),ratio(totals[1],turns[1]))
    result['win_difference_bootstrap_95']=None
    if inference and pairs:
        rng=np.random.default_rng(5914)
        strata=[np.array([i for i,(a,b) in enumerate(pairs) if a['luna_side']==side]) for side in ('red','blue')]
        draws=np.concatenate([rng.choice(s,size=(10000,len(s)),replace=True) for s in strata if len(s)],axis=1)
        differences=values[:,0]-values[:,1]
        result['win_difference_bootstrap_95']=np.quantile(differences[draws].mean(axis=1),[.025,.975]).tolist()
        result['bootstrap_degenerate']=bool(np.all(differences==differences[0]))
        if result['bootstrap_degenerate']:
            result['bootstrap_warning']='Degenerate empirical bootstrap is not zero population uncertainty or equivalence; retain Wilson intervals and discordant counts.'
        result['effect_intervals']={}
        for field in ('provider_requests','total_tokens','backend_thinking_seconds'):
            data=[[metrics_for(pair[i]).get(field) for pair in pairs] for i in (0,1)]
            if any(v is None for d in data for v in d):
                result['effect_intervals'][field]=None;continue
            turn_data=[np.array([metrics_for(pair[i])['turns'] for pair in pairs]) for i in (0,1)]
            rates=[np.array(data[i])[draws].sum(axis=1)/turn_data[i][draws].sum(axis=1) for i in (0,1)]
            if np.any(rates[1]==0): result['effect_intervals'][field]=None
            else: result['effect_intervals'][field]=np.quantile(rates[0]/rates[1],[.025,.975]).tolist()
        length=np.array([a['player_turns']-b['player_turns'] for a,b in pairs])
        result['median_length_difference_bootstrap_95']=np.quantile(np.median(length[draws],axis=1),[.025,.975]).tolist()
    return result


def plots(output,rows,summary,synthetic):
    output=Path(output);output.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str((output/'mpl-cache').resolve()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    output=Path(output);output.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'arena-case-study-v1'})
    prefix='OFFLINE FAKE FIXTURE — ' if synthetic else ''
    colors=['#326bb0','#c66a18','#328c65']
    def save(fig,name,title):
        fig.suptitle(prefix+title,fontsize=12)
        fig.tight_layout(rect=(0,0,1,.94))
        for suffix in ('png','svg'):
            fig.savefig(output/(name+'.'+suffix),dpi=150)
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5))
    labels=[]; vals=[]; errors=[]
    for arm in ARMS:
        for name in ('luna','heuristic'):
            item=summary[arm][name];v=item['win_rate'] or 0;ci=item['wilson_95'] or [0,0]
            labels.append(arm+' Luna' if name=='luna' else 'Heuristic vs '+arm)
            vals.append(v);errors.append([max(0,v-ci[0]),max(0,ci[1]-v)])
    ax.bar(range(6),vals,color=[c for c in colors for _ in range(2)],alpha=.8)
    ax.errorbar(range(6),vals,yerr=np.array(errors).T,fmt='none',color='black',capsize=4)
    ax.set(ylim=(0,1),ylabel='Win rate (Wilson 95% CI)',xticks=range(6),xticklabels=labels)
    ax.tick_params(axis='x',rotation=20);save(fig,'01-win-rates','Matchup-specific agent win rates')
    for number,field,label in [(2,'provider_requests','Requests / Luna turn'),(3,'total_tokens','Tokens / Luna turn'),
                                (4,'backend_thinking_seconds','Backend seconds / Luna turn')]:
        fig,ax=plt.subplots(figsize=(8,5))
        for arm,color in zip(ARMS,colors):
            item=summary[arm]['luna'];x=item['per_turn'][field];y=item['win_rate']
            if x is not None and y is not None:
                ax.scatter([x],[y],label=arm,color=color,s=65);ax.annotate(arm,(x,y),xytext=(4,6),textcoords='offset points')
            baseline=summary[arm]['heuristic']['win_rate']
            if baseline is not None:
                ax.scatter([0],[baseline],marker='x',color=color,label='Heuristic vs '+arm)
        ax.set(xlabel=label,ylabel='Win rate',ylim=(-.03,1.05));ax.legend(fontsize=8)
        save(fig,f'{number:02d}-efficiency-{field}','Performance / inference cost; heuristic architecture differs')
    fig,ax=plt.subplots(figsize=(8,5))
    values=[[r['player_turns'] for r in rows if r['arm']==a] for a in ARMS]
    ax.boxplot([v or [float('nan')] for v in values],tick_labels=ARMS,showmeans=True)
    ax.set(ylabel='Started player turns');save(fig,'05-match-length','Match length, including stopping states')
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for ax,field,label in zip(axes,('failure_derived_unused_ap','execution_truncations','provider_requests'),
                             ('Failure-derived AP / Luna turn','Truncations / Luna turn','Requests / Luna turn')):
        ax.bar(ARMS,[summary[a]['luna']['per_turn'].get(field) or 0 for a in ARMS],color=colors);ax.set(ylabel=label)
    save(fig,'06-failure-ap','Failure-derived AP and request exposure')
    fig,ax=plt.subplots(figsize=(10,5));bottom=[0]*3
    for reason in STOP_REASONS:
        v=[summary[a]['luna']['unused_ap_by_reason'][reason] for a in ARMS]
        ax.bar(ARMS,v,bottom=bottom,label=reason);bottom=[b+x for b,x in zip(bottom,v)]
    ax.set(ylabel='Unused AP (total)');ax.legend(fontsize=8)
    save(fig,'07-stop-reasons','Unused AP by disjoint stop reason')
    fig,axes=plt.subplots(1,3,figsize=(12,4));item=summary['bounded']['luna']
    axes[0].bar(['Replans / turn'],[item.get('replan_rate') or 0]);axes[0].set_ylim(0,1)
    recovered=[v for r in rows if r['arm']=='bounded' for v in metrics_for(r)['ap_recovered_distribution']]
    if recovered: axes[1].hist(recovered,bins=[-.5,.5,1.5,2.5,3.5,4.5,5.5]);axes[1].set_xlabel('AP recovered / replan')
    else: axes[1].text(.5,.5,'No replans observed',ha='center',transform=axes[1].transAxes)
    if item.get('second_invalid_rate') is not None: axes[2].bar(['Second invalid / replan'],[item['second_invalid_rate']])
    else: axes[2].text(.5,.5,'Rate undefined (0 replans)',ha='center',transform=axes[2].transAxes)
    axes[2].set_ylim(0,1);save(fig,'08-bounded-recovery','Bounded recovery')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    axes[0].bar(ARMS,[summary[a]['luna']['totals'].get('repairs') or 0 for a in ARMS],color=colors)
    axes[0].set_ylabel('Repair attempts')
    for i,a in enumerate(ARMS):
        rate=summary[a]['luna'].get('repair_success_rate')
        if rate is not None:axes[1].bar(i,rate,color=colors[i])
        else:axes[1].text(i,.1,'N/A',ha='center')
    axes[1].set(xticks=range(3),xticklabels=ARMS,ylim=(0,1),ylabel='Repair success / attempted repair')
    save(fig,'09-static-repair','Static repair exposure and success')
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,arm in zip(axes,ARMS):
        bottom=[0,0]
        for outcome,color in [('wins','#328c65'),('losses','#ba4a48'),('limits','#999999')]:
            v=[summary[arm]['sides'][s]['luna'][outcome] for s in ('red','blue')]
            ax.bar(['Luna Red','Luna Blue'],v,bottom=bottom,label=outcome,color=color)
            bottom=[b+x for b,x in zip(bottom,v)]
        ax.set_title(arm+' vs Heuristic V2');ax.set_ylabel('Matches')
    axes[-1].legend();save(fig,'10-side-outcomes','Side-specific paired matchup outcomes')
    # Two additional frontier views requested for truncation and failure AP.
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,field in zip(axes,('execution_truncations','failure_derived_unused_ap')):
        for arm,color in zip(ARMS,colors):
            item=summary[arm]['luna']['per_turn']
            if item.get('provider_requests') is not None:
                ax.scatter(item['provider_requests'],item.get(field) or 0,color=color,label=arm)
        ax.set(xlabel='Requests / Luna turn',ylabel=field.replace('_',' ')+' / turn');ax.legend()
        ax.set_ylim(bottom=0)
    save(fig,'11-reliability-frontier','Reliability / request cost')


def analyze(output,rows,contract):
    output=Path(output)
    synthetic=json.loads((output/'benchmark-manifest.json').read_text())['mode']=='fake'
    complete=len(rows)==300 and all(sum(r['arm']==a for r in rows)==100 for a in ARMS)
    summary={}
    for arm in ARMS:
        selected=[r for r in rows if r['arm']==arm]
        summary[arm]=dict(luna=summarize(selected),heuristic=summarize(selected,True),
            sides={s:dict(luna=summarize([r for r in selected if r['luna_side']==s]),
                heuristic=summarize([r for r in selected if r['luna_side']==s],True)) for s in ('red','blue')},
            tactical_only=summarize([r for r in selected if r['terminal_cause'] in ('CORE_DESTRUCTION','TEAM_ELIMINATION')]))
    pairs=[paired(rows,a,b,inference=complete) for a,b in [('bounded','strict'),('stepwise','bounded')]]
    pvalues=[(p['exact_mcnemar_p'],i) for i,p in enumerate(pairs) if p['exact_mcnemar_p'] is not None]
    previous=0
    for rank,(p,i) in enumerate(sorted(pvalues)):
        previous=max(previous,min(1,p*(len(pvalues)-rank)));pairs[i]['holm_adjusted_p']=previous
    result=dict(schema='arena-case-study-analysis-v1',synthetic=synthetic,completed_matches=len(rows),
        status='COMPLETE_OFFLINE_FIXTURE' if synthetic and complete else 'COMPLETE' if complete else 'PARTIAL_DESCRIPTIVE_ONLY',
        contract_sha256=contract['sha256'],summary=summary,paired=pairs,
        caveats=['Fake outcomes do not estimate Luna performance.' if synthetic else 'Independent nondeterministic model trajectories.',
            'One canonical opening; no scenario-population inference.',
            'Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.',
            'Ratios of total cost to total attempted Luna turns; missing telemetry stays null.',
            'Heuristic records remain matchup-specific; zero inference does not mean zero computation.'])
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (output/'plot-data.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=['slot','arm','luna_side','terminal_cause','luna_outcome','player_turns','requests',
            'luna_turns','tokens','backend_seconds','core_damage','heuristic_core_damage'])
        writer.writeheader()
        for r in rows:
            m=metrics_for(r);h=metrics_for(r,True)
            writer.writerow({**{k:r[k] for k in ('slot','arm','luna_side','terminal_cause','luna_outcome','player_turns','requests')},
                'luna_turns':m['turns'],'tokens':m['total_tokens'],'backend_seconds':m['backend_thinking_seconds'],
                'core_damage':m['core_damage_dealt'],'heuristic_core_damage':h['core_damage_dealt']})
    lines=['# '+('OFFLINE FAKE FIXTURE — ' if synthetic else '')+'Arena case study',
        '',f'Status: {result["status"]}. Completed: {len(rows)}/300. Contract: `{contract["sha256"]}`.',
        '', '| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |',
        '| --- | ---: | ---: | ---: | ---: | --- | ---: |']
    for arm in ARMS:
        for kind in ('luna','heuristic'):
            m=summary[arm][kind]; name=arm+' Luna' if kind=='luna' else 'Heuristic vs '+arm
            ci=m['wilson_95'];interval=f'{ci[0]:.3f}–{ci[1]:.3f}' if ci else 'N/A'
            lines.append(f'| {name} | {m["wins"]} | {m["losses"]} | {m["limits"]} | {m["win_rate"]} | {interval} | {m["per_turn"]["provider_requests"]} |')
    lines+=['','All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.',
        'Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.','',*result['caveats']]
    (output/'case-study-report.md').write_text('\n\n'.join(lines[:3])+'\n'+'\n'.join(lines[3:])+'\n',encoding='utf-8')
    plots(output/'plots',rows,summary,synthetic)
    return result
