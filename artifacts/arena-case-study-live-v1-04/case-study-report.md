# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 120/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 40 | 0 | 0.0 | 0.000–0.088 | 1.3212669683257918 |
| Heuristic vs strict | 40 | 0 | 0 | 1.0 | 0.912–1.000 | 0.0 |
| bounded Luna | 0 | 40 | 0 | 0.0 | 0.000–0.088 | 1.8757396449704142 |
| Heuristic vs bounded | 40 | 0 | 0 | 1.0 | 0.912–1.000 | 0.0 |
| stepwise Luna | 2 | 31 | 7 | 0.05 | 0.014–0.165 | 3.0534653465346535 |
| Heuristic vs stepwise | 31 | 2 | 7 | 0.775 | 0.625–0.877 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
