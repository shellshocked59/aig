# OFFLINE FAKE FIXTURE — Arena case study



Status: COMPLETE_OFFLINE_FIXTURE. Completed: 300/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 100 | 0 | 0.0 | 0.000–0.037 | 1.0 |
| Heuristic vs strict | 100 | 0 | 0 | 1.0 | 0.963–1.000 | 0.0 |
| bounded Luna | 0 | 100 | 0 | 0.0 | 0.000–0.037 | 1.0 |
| Heuristic vs bounded | 100 | 0 | 0 | 1.0 | 0.963–1.000 | 0.0 |
| stepwise Luna | 0 | 100 | 0 | 0.0 | 0.000–0.037 | 3.5714285714285716 |
| Heuristic vs stepwise | 100 | 0 | 0 | 1.0 | 0.963–1.000 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Fake outcomes do not estimate Luna performance.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
