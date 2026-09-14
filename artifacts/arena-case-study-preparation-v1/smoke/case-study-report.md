# OFFLINE FAKE FIXTURE — Arena case study



Status: PARTIAL_DESCRIPTIVE_ONLY. Completed: 3/300. Contract: `ba305fdbc37ecb4934e9e9c81b3fe48e1ae2052e9d401652d0936cf705d50442`.

| Agent/control | Wins | Losses | Limits | Win rate | Wilson 95% | Requests/turn |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| strict Luna | 0 | 1 | 0 | 0.0 | 0.000–0.793 | 1.0 |
| Heuristic vs strict | 1 | 0 | 0 | 1.0 | 0.207–1.000 | 0.0 |
| bounded Luna | 0 | 1 | 0 | 0.0 | 0.000–0.793 | 1.0 |
| Heuristic vs bounded | 1 | 0 | 0 | 1.0 | 0.207–1.000 | 0.0 |
| stepwise Luna | 0 | 1 | 0 | 0.0 | 0.000–0.793 | 3.5 |
| Heuristic vs stepwise | 1 | 0 | 0 | 1.0 | 0.207–1.000 | 0.0 |

All mechanical totals, side strata, costs, repairs, recovery, paired effects and intervals are in `analysis.json`.
Per-match data are in `plot-data.csv`; eleven figures are available as PNG and SVG in `plots/`.

Fake outcomes do not estimate Luna performance.
One canonical opening; no scenario-population inference.
Forfeits count as losses; turn/request limits as nonwins. Tactical-only subset is secondary and selected.
Ratios of total cost to total attempted Luna turns; missing telemetry stays null.
Heuristic records remain matchup-specific; zero inference does not mean zero computation.
