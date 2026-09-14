# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 90/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 30 | 0 | 0.0 | 0.000–0.114 | 1.3076923076923077 |
| Heuristic vs strict | 30 | 0 | 0 | 1.0 | 0.886–1.000 | 0.0 |
| bounded Luna | 0 | 30 | 0 | 0.0 | 0.000–0.114 | 1.8267716535433072 |
| Heuristic vs bounded | 30 | 0 | 0 | 1.0 | 0.886–1.000 | 0.0 |
| stepwise Luna | 2 | 24 | 4 | 0.06666666666666667 | 0.018–0.213 | 3.086687306501548 |
| Heuristic vs stepwise | 24 | 2 | 4 | 0.8 | 0.627–0.905 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
