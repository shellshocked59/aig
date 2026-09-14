# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 180/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 60 | 0 | 0.0 | 0.000–0.060 | 1.3122923588039868 |
| Heuristic vs strict | 60 | 0 | 0 | 1.0 | 0.940–1.000 | 0.0 |
| bounded Luna | 0 | 60 | 0 | 0.0 | 0.000–0.060 | 1.732899022801303 |
| Heuristic vs bounded | 60 | 0 | 0 | 1.0 | 0.940–1.000 | 0.0 |
| stepwise Luna | 2 | 48 | 10 | 0.03333333333333333 | 0.009–0.114 | 3.052054794520548 |
| Heuristic vs stepwise | 48 | 2 | 10 | 0.8 | 0.682–0.882 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
