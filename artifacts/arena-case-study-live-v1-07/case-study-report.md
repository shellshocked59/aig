# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 210/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 70 | 0 | 0.0 | 0.000–0.052 | 1.2926829268292683 |
| Heuristic vs strict | 70 | 0 | 0 | 1.0 | 0.948–1.000 | 0.0 |
| bounded Luna | 0 | 70 | 0 | 0.0 | 0.000–0.052 | 1.7492957746478872 |
| Heuristic vs bounded | 70 | 0 | 0 | 1.0 | 0.948–1.000 | 0.0 |
| stepwise Luna | 3 | 54 | 13 | 0.04285714285714286 | 0.015–0.119 | 3.044372294372294 |
| Heuristic vs stepwise | 54 | 3 | 13 | 0.7714285714285715 | 0.660–0.854 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
