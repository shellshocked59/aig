# Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 60/300. Contract: `dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 20 | 0 | 0.0 | 0.000–0.161 | 1.3070175438596492 |
| Heuristic vs strict | 20 | 0 | 0 | 1.0 | 0.839–1.000 | 0.0 |
| bounded Luna | 0 | 20 | 0 | 0.0 | 0.000–0.161 | 1.797872340425532 |
| Heuristic vs bounded | 20 | 0 | 0 | 1.0 | 0.839–1.000 | 0.0 |
| stepwise Luna | 2 | 15 | 3 | 0.1 | 0.028–0.301 | 3.0956521739130434 |
| Heuristic vs stepwise | 15 | 2 | 3 | 0.75 | 0.531–0.888 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Independent nondeterministic model trajectories.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
