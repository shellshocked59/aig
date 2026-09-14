# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 30/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 10 | 0 | 0.0 | 0.000–0.278 | 1.3934426229508197 |
| Heuristic vs strict | 10 | 0 | 0 | 1.0 | 0.722–1.000 | 0.0 |
| bounded Luna | 0 | 10 | 0 | 0.0 | 0.000–0.278 | 1.9 |
| Heuristic vs bounded | 10 | 0 | 0 | 1.0 | 0.722–1.000 | 0.0 |
| stepwise Luna | 1 | 7 | 2 | 0.1 | 0.018–0.404 | 3.030075187969925 |
| Heuristic vs stepwise | 7 | 1 | 2 | 0.7 | 0.397–0.892 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
