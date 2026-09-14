# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 150/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 50 | 0 | 0.0 | 0.000–0.071 | 1.3244274809160306 |
| Heuristic vs strict | 50 | 0 | 0 | 1.0 | 0.929–1.000 | 0.0 |
| bounded Luna | 0 | 50 | 0 | 0.0 | 0.000–0.071 | 1.8295964125560538 |
| Heuristic vs bounded | 50 | 0 | 0 | 1.0 | 0.929–1.000 | 0.0 |
| stepwise Luna | 2 | 40 | 8 | 0.04 | 0.011–0.135 | 3.051839464882943 |
| Heuristic vs stepwise | 40 | 2 | 8 | 0.8 | 0.670–0.888 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
