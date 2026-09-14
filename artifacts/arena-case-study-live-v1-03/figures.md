# Frozen analyzer figures — INTERIM

Unchanged analyzer output: 11 figures per cohort, each in PNG and SVG. Batch 3 is n=10/control; cumulative Batches 1–3 is n=30/control. These are interim descriptive results, not a final control ranking.

The win-rate figure uses Wilson 95% intervals. Heuristic results are matchup-specific. Figure 06 uses the frozen generic failure-derived AP bucket: Stepwise request-budget denial contributes 1 AP in Batch 3 and 8 AP cumulatively. The reports separate this from actual provider failure; intentional unused AP is not included as a failure. Figure 11 is the frozen scatter visualization, not a composite score.

| Figure | Batch 3 PNG / SVG | Cumulative PNG / SVG |
| --- | --- | --- |
| 01-win-rates | [PNG](batch-3-analysis/plots/01-win-rates.png) / [SVG](batch-3-analysis/plots/01-win-rates.svg) | [PNG](plots/01-win-rates.png) / [SVG](plots/01-win-rates.svg) |
| 02-efficiency-provider_requests | [PNG](batch-3-analysis/plots/02-efficiency-provider_requests.png) / [SVG](batch-3-analysis/plots/02-efficiency-provider_requests.svg) | [PNG](plots/02-efficiency-provider_requests.png) / [SVG](plots/02-efficiency-provider_requests.svg) |
| 03-efficiency-total_tokens | [PNG](batch-3-analysis/plots/03-efficiency-total_tokens.png) / [SVG](batch-3-analysis/plots/03-efficiency-total_tokens.svg) | [PNG](plots/03-efficiency-total_tokens.png) / [SVG](plots/03-efficiency-total_tokens.svg) |
| 04-efficiency-backend_thinking_seconds | [PNG](batch-3-analysis/plots/04-efficiency-backend_thinking_seconds.png) / [SVG](batch-3-analysis/plots/04-efficiency-backend_thinking_seconds.svg) | [PNG](plots/04-efficiency-backend_thinking_seconds.png) / [SVG](plots/04-efficiency-backend_thinking_seconds.svg) |
| 05-match-length | [PNG](batch-3-analysis/plots/05-match-length.png) / [SVG](batch-3-analysis/plots/05-match-length.svg) | [PNG](plots/05-match-length.png) / [SVG](plots/05-match-length.svg) |
| 06-failure-ap | [PNG](batch-3-analysis/plots/06-failure-ap.png) / [SVG](batch-3-analysis/plots/06-failure-ap.svg) | [PNG](plots/06-failure-ap.png) / [SVG](plots/06-failure-ap.svg) |
| 07-stop-reasons | [PNG](batch-3-analysis/plots/07-stop-reasons.png) / [SVG](batch-3-analysis/plots/07-stop-reasons.svg) | [PNG](plots/07-stop-reasons.png) / [SVG](plots/07-stop-reasons.svg) |
| 08-bounded-recovery | [PNG](batch-3-analysis/plots/08-bounded-recovery.png) / [SVG](batch-3-analysis/plots/08-bounded-recovery.svg) | [PNG](plots/08-bounded-recovery.png) / [SVG](plots/08-bounded-recovery.svg) |
| 09-static-repair | [PNG](batch-3-analysis/plots/09-static-repair.png) / [SVG](batch-3-analysis/plots/09-static-repair.svg) | [PNG](plots/09-static-repair.png) / [SVG](plots/09-static-repair.svg) |
| 10-side-outcomes | [PNG](batch-3-analysis/plots/10-side-outcomes.png) / [SVG](batch-3-analysis/plots/10-side-outcomes.svg) | [PNG](plots/10-side-outcomes.png) / [SVG](plots/10-side-outcomes.svg) |
| 11-reliability-frontier | [PNG](batch-3-analysis/plots/11-reliability-frontier.png) / [SVG](batch-3-analysis/plots/11-reliability-frontier.svg) | [PNG](plots/11-reliability-frontier.png) / [SVG](plots/11-reliability-frontier.svg) |

Frozen machine outputs: [Batch 3 analysis](batch-3-analysis/analysis.json), [cumulative analysis](analysis.json), [Batch 3 plot data](batch-3-analysis/plot-data.csv), [cumulative plot data](plot-data.csv).

Supplemental reporting: [Batch 3](batch-3-report.md), [cumulative](cumulative-batches-1-3-report.md), [repair forensics](repair-forensics.md), [decision](decision.md).
