# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 240/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 80 | 0 | 0.0 | 0.000–0.046 | 1.2937062937062938 |
| Heuristic vs strict | 80 | 0 | 0 | 1.0 | 0.954–1.000 | 0.0 |
| bounded Luna | 0 | 80 | 0 | 0.0 | 0.000–0.046 | 1.7506297229219143 |
| Heuristic vs bounded | 80 | 0 | 0 | 1.0 | 0.954–1.000 | 0.0 |
| stepwise Luna | 3 | 62 | 15 | 0.0375 | 0.013–0.105 | 3.037629350893697 |
| Heuristic vs stepwise | 62 | 3 | 15 | 0.775 | 0.672–0.853 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
