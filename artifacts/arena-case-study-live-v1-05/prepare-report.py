"""Adapt supplemental report presentation to the current frozen batch prefix."""
from pathlib import Path
import ast
root=Path(__file__).parent
B=int(root.name[-2:])
old=Path('artifacts/arena-case-study-live-v1-03')
s=(old/'interim-report.py').read_text(encoding='utf-8')
s=s.replace("root=Path(__file__).parent",f"root=Path(__file__).parent\nB={B}")
s=s.replace("'batch-3-preflight.json'","f'batch-{B}-preflight.json'")
s=s.replace('for b in (1,2,3)','for b in range(1,B+1)')
s=s.replace("[('batch_1',[1]),('batch_2',[2]),('batch_3',[3]),('cumulative',[1,2,3])]", "[(f'batch_{b}',[b]) for b in range(1,B+1)]+[('cumulative',list(range(1,B+1)))]")
s=s.replace("data['batch_3_manifest_sha256']","data[f'batch_{B}_manifest_sha256']")
s=s.replace("r['batch']==3", "r['batch']==int(cohort_name.split('_')[1])")
s=s.replace("c['batch']==3", "c['batch']==int(cohort_name.split('_')[1])")
s=s.replace("('Batch 3 standalone' if cohort_name=='batch_3' else 'Cumulative Batches 1–3')", "(f'Batch {cohort_name.split(\"_\")[1]} standalone' if cohort_name!='cumulative' else f'Cumulative Batches 1–{B}')")
s=s.replace("('1','2','3','cumulative')","tuple(str(i) for i in range(1,B+1))+('cumulative',)")
s=s.replace("['Resource','Batch 1','Batch 2','Batch 3','Cumulative']", "['Resource',*[f'Batch {i}' for i in range(1,B+1)],'Cumulative']")
s=s.replace("('batch_1','batch_2','batch_3','cumulative')", "tuple(f'batch_{i}' for i in range(1,B+1))+('cumulative',)")
s=s.replace("'Remaining 70/control'", "f'Remaining {100-B*10}/control'")
s=s.replace('remaining 210 central','remaining {300-B*30} central')
s=s.replace('mean_ap_per_replan=sum(recovered)/len(recovered) if recovered else None,','mean_ap_per_replan=sum(recovered)/len(recovered) if recovered else None,median_ap_per_replan=median(recovered) if recovered else None,')
lines=s.splitlines()
for i,line in enumerate(lines):
    if "p('Only Batch 3 was newly executed." in line:
        lines[i]="    p(f'This root adds Batch {B} to a copied, verified {30*(B-1)}-match prefix, preserving all original earlier roots. Frozen resume starts at '+pre['next_match']['match_id']+', request '+str(pre['next_request_id'])+f'. No earlier request or match was rerun. Scope stops at --through-batch {B}. No within-batch interruption recovery was used. Batch 5 is conditional on the separate successful Batch 4 integrity gate; Batch 6 is not authorized or executed.')"
    elif "p('```powershell" in line:
        lines[i]="    p(f'```powershell\\n.venv/Scripts/python.exe -B -m aig.arena.case_study verify\\n.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-{B:02d} --through-batch {B} --authorize-live arena-case-study-benchmark-v1\\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-{B:02d}/postprocess.py\\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-{B:02d}/supplemental-audit.py\\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-{B:02d}/repair-forensics.py\\n.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-{B:02d}/interim-report.py\\n```')"
    elif "p('postprocess.py calls" in line:
        lines[i]="    p(f'postprocess.py calls the unchanged frozen verifier, full-prefix integrity/replay verifier and analyzer for cumulative and batch=={B} cohorts. Supplemental scripts are offline derived audits; frozen metrics and analysis remain unchanged.')"
    elif "['Batch 3 schedule SHA-256'" in line:
        lines[i]=line.replace("'Batch 3 schedule SHA-256'","f'Batch {B} schedule SHA-256'")
    elif "p('Batch 3 is schedule entries" in line:
        lines[i]="    p(f'Batch {B}: schedule entries {30*(B-1)+1}–{30*B}, MATCH-{10*(B-1)+1:03d}–{10*B:03d}, five Red/five Blue per control. Independent 1,700-request batch ceiling, per-control 300/500/900 and per-match 50/80/140; global 15,000. One bounded replan. Natural terminal precedence and 200-player-turn/100-round limits remain frozen. No winner on request limit; provider exhaustion forfeits without fallback.')"
    elif 'walls=[t[' in line:
        lines[i]="    walls=[t['wall_seconds_upper_bound'] for t in timings.values()];remaining=10-B;p(f'If future workloads resemble observed batches, remaining {remaining} batches span {remaining*min(walls)/3600:.3f}–{remaining*max(walls)/3600:.3f} process wall hours; full study {(sum(walls)+remaining*min(walls))/3600:.3f}–{(sum(walls)+remaining*max(walls))/3600:.3f} hours. This workload illustration excludes later analysis; growing prefix verification and service conditions can add time.')"
    elif "p('See [decision.md]" in line:
        lines[i]="    p(f'See [decision.md](decision.md) for interpretation and continuation recommendation. INTERIM at n={B*10}/control; frozen confirmatory inference waits for 100/control. No tuning or replacement of failed/capped games. [Figures](figures.md); machine metrics: interim-metrics.json; command audit: supplemental-audit.json; repair evidence: repair-forensics.json.')"
    elif line.startswith("render_report('batch_3'"):
        lines[i]="render_report(f'batch_{B}',f'batch-{B}-report.md',10)"
    elif line.startswith("render_report('cumulative'"):
        lines[i]="render_report('cumulative',f'cumulative-batches-1-{B}-report.md',B*10)"
    elif line.startswith('print(json.dumps(dict(batch_3='):
        lines[i]="print(json.dumps(dict(batch=B,new_matches=data[f'batch_{B}']['matches'],cumulative=data['cumulative']['matches'],reports_written=True)))"
s='\n'.join(lines)+'\n'
s=s.replace("p('## Decision and limitations')", "p('## Decision and limitations')\n    p('Additional side-specific forfeits/caps and cost rates, Stepwise capped/uncapped means and sorted distribution, complete triplet classifications and cap gameplay: [focused comparisons](focused-comparisons.md).')")
s=s.replace("'Tokens/match','Requests/turn'", "'Tokens/match','Provider sec/match','Requests/turn'")
s=s.replace("aa[a]['per_match']['total_tokens'],*[aa[a]['per_turn']", "aa[a]['per_match']['total_tokens'],aa[a]['per_match']['provider_latency_seconds'],*[aa[a]['per_turn']")
s=s.replace("aa[a]['per_match']['provider_latency_seconds']", "aa[a]['totals']['provider_latency_seconds']/aa[a]['matches']")
s=s.replace("+' — INTERIM')", "+' — INTERIM'+(' / HALFWAY' if cohort_name=='cumulative' and B==5 else ''))")
ast.parse(s)
(root/'interim-report.py').write_text(s,encoding='utf-8')
print(f'Prepared supplemental report for batch {B}')
