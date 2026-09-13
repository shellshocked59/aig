# Environment V3: discoverable map resources

Environment V3 adds static resource yield modifiers to V2 fog and exploration.
Scenario V2 preserves Scenario V1's 12 by 10 terrain, A=(2,2), B=(9,7), seed 42
and turn order; only resource placement changes. V1/V2 remain historical metadata.
Their gameplay requires their recorded source revision; the current benchmark
rejects labeling V3 execution as V1/V2.

| Domain | Concrete version |
| --- | --- |
| Environment / latest | environment-v3 |
| Scenario / latest | scenario-v2 |
| Strategy prompt | strategy-prompt-v1 |
| StrategicPlan schema | strategic-plan-schema-v1 |
| Qwen / Luna configuration | qwen-config-v1 / luna-config-v1 |
| Benchmark | benchmark-v1, additive measurements |
| Snapshot | v10 (previously v9) |

## Resource rules

`ResourceType` is a five-member string enum. `TileState.resource` holds one enum
or `None`, independently of `owner_id`. Strict tile/setup validation rejects
invalid types, duplicate placements, absent tiles, Water and Mountains.
Grassland, Plains, Forest and Hills accept every resource. Placement is static;
derived yields and separate resource ownership are never stored.

| Resource | Food | Production | Gold |
| --- | ---: | ---: | ---: |
| Wheat | 1 | 0 | 0 |
| Cattle | 1 | 1 | 0 |
| Iron | 0 | 2 | 0 |
| Gems | 0 | 0 | 3 |
| Spices | 1 | 0 | 2 |

`resource_yields()` returns immutable `Yields`. `tile_yields()` adds the bonus to
terrain. Centers first apply minimum 2 Food / 1 Production to terrain, then add
the bonus: Grassland/Wheat is 3F/1P; Hills/Iron is 2F/4P. Founding retains the
resource. Centers are free; surrounding citizen assignment still ranks descending
Food, Production, Gold, then ascending y/x, now using effective yields.

Bonuses enter only ordinary city economy: food storage/growth, production
storage/completion and treasury. Discovery grants nothing. Science, combat,
technology and unit prerequisites are unchanged. The existing working rules
remain: radius one, Water workable, Mountains excluded, no tile-ownership gate.

Resource names do not yet imply Civilization-style luxury/bonus/strategic
mechanics. For V3 they are only discoverable yield modifiers. There are no
improvements, trade, stockpiles, depletion, amenities, tech reveals or Iron
requirements. No barbarians, capture, diplomacy, victories, new units or new
technologies are included.

## Knowledge and planning

`PlayerKnowledge` keeps explored positions without a redundant resource
collection. Unexplored resources are absent from planner state and null in the
public DTO. Explored resources persist after losing current sight.
`known_resources()` emits detached coordinate-ordered facts: type, position,
knowledge-safe owner, derived bonus yields and whether inside an own city radius.
Ownership follows current-sight/own-owner rules. Null means unowned or unknown;
trace wording is "with no known owner", not confirmed unclaimed territory.

Every provider receives the same `StrategicState.known_resources` facts. Exact
bonuses make the rules available without changing the frozen prompt. No hidden
resource totals, recommendations or priority scores are sent. The heuristic's
high-level plan rule stays unchanged; every provider shares the executor.

Starting capitals preserve immediate legal founding at the supplied start.
Later Settlers compare reachable legal sites before founding. Rank is
lexicographic: higher total known Food, Production, Gold, then shorter Chebyshev
travel distance, then ascending y/x. Totals include the center and known workable
radius-one tiles, applying center minimums before bonuses. Unknown tiles contribute
nothing; ranking never reads their authoritative contents. Routes use the filtered
PlanningView; issued adjacent steps undergo authoritative command validation.

Scout frontier selection remains expected coordinate reveal, route length and
stable coordinates. It never reads hidden resources. Resource sightings do not
force replanning: the five-turn interval and existing bounded enemy-contact
triggers remain. Discoveries are still traced per command.

The browser adds five original inline SVG icons beside the existing sprite art,
only for explored tiles, including remembered fogged tiles. No external art,
redesign or public observer endpoint was added. `observer_state()` and benchmarks
may inspect all resources; normal player responses filter hidden resource truth.

Snapshot v10 stores each tile's resource string/null and existing exploration.
Serialization is canonical and ordered by y/x. Restore is detached and changes no
visibility, economy, decisions or exploration. Earlier schemas, including v9,
are explicitly rejected under the existing no-migration policy.

## Deterministic placement

Zero-based coordinates; opportunities are comparable without altering the
asymmetric original terrain.

| Area | Resource placements (x,y) |
| --- | --- |
| A starting area | Wheat (2,2), Cattle (3,1), Iron (4,4) |
| A outer exploration | Spices (1,6), Gems (0,8) |
| B starting area | Wheat (9,7), Cattle (8,7), Iron (8,8) |
| B outer exploration | Spices (10,3), Gems (11,1) |
| Central opportunities | Cattle (6,4), Spices (6,6), Gems (7,3), Iron (5,7) |

There are 14 tiles: two Wheat and three each of the other types. These totals are
documentation/observer truth, not undiscovered planner facts. The immutable
scenario tuple and initial-state hash are tested. Scenario V1's original snapshot
projection retains its original digest.

## Measurements

Per-player `resource_tiles_discovered` and `resource_discoveries_by_type` include
initial sight. `first_resource_discovered` records the first zero-based global
turn/activation. Command outcomes list new discoveries for every faction.
`resource_discoveries_by_scouts` counts new resources covered by Scout movement or
newly produced Scout sight, excluding explored tiles. Spawn attribution does not
assert exclusive causality when sight sources overlap.

Founding records resources known before founding within center/radius one and
the center resource. Counters are `cities_founded_near_known_resources`,
`known_resources_in_radius_at_founding`, and `city_center_resources_used`.

Before EndActivation, instrumentation observes the exact free center and
pre-growth citizen assignments resolved by economy. `resource_tiles_worked`
counts distinct coordinates ever worked; `resource_tile_workings` counts
city-tile-activation contributions; `activations_working_resources` counts
faction activations with any contribution. `resource_bonus_food`,
`resource_bonus_production`, and `resource_bonus_gold` count gross generation
before food consumption, growth or production spending. Command outcomes retain
bonuses separately from terrain. Overlapping city radii follow actual economy,
including repeated contributions; distinct-coordinate counts still deduplicate.

Replan measurements include known resource count/by-type, resources in own city
radii and locations with no known owner. Existing exploration, combat, research,
economy, plan-churn and inference measurements remain. Whole-world faction totals
sum player discoveries/workings, so both factions may count the same tile;
`world_resource_tiles` and `world_resources_by_type` separately describe unique
authoritative placement. No arbitrary efficiency score is introduced. Settler
intent is not inferred from individual movements: saved commands, planner facts
and founding events support inspection without an invented judgment score.

## Verification and limits

Final verification results are in the accompanying completion report and local
`.local/environment-v3-verification-accepted/` artifacts. The starting checkout
passed 693 Python tests (688 passed, 5 skipped) and 35 frontend tests, with snapshot
v9. The preservation fixture hashes 921 existing files, including V1/V2 archives,
prior fixtures and preserved V2/baseline documentation. Frozen prompt/schema
digests and model-profile checks remain.

Paired-world tests found no hidden-resource leak through provider, public or
planning boundaries. Initial capitals do not optimize sites. Later settlement
ranking sums all known radius tiles rather than predicting growth or the first
citizen's assignment; food-first ranking can overlook production/gold sites.
Unknown tiles contribute no yield, so more explored sites can rank higher. The
existing two-city expansion cap, military-shortage rule and heuristic posture
can block expansion despite discovery. The heuristic does not change its
high-level plan merely because it receives resource facts.

Resource facts increase provider input size; actual model context use remains
unmeasured until a separately authorized comparison. No live model calls, prompt
tuning or model changes were made.

## Final offline results

- Python: **710 tests; 705 passed, 5 skipped**. Includes 17 focused resource
  tests covering all resource/terrain combinations, economy, anti-leak behavior,
  persistence, settlement ranking, versioning and benchmark attribution.
- Frontend: **37 passed**; production frontend build passed; `git diff --check`
  passed. Original vector icon mappings and hidden-resource DOM exclusion tested.
- Four heuristic trials completed **100 global turns / 200 activations** each.
  All four initial/final/command/plan hashes match. Each 473-command stream was
  replayed exactly; all 42 planner inputs per trial matched reconstructed faction
  knowledge, for 168 audited replans. Network access was blocked during verification.
- All **921 pre-existing file digests** matched. Existing V1/V2 archive fixtures,
  Scenario V1 projection, prompt/schema digests and model-profile regressions pass.
- No Qwen/Luna or other live inference calls were made.

| Per identical trial | A | B |
| --- | ---: | ---: |
| Explored tiles | 120 | 36 |
| Resource tiles discovered | 14 | 5 |
| Discoveries attributed to Scouts | 11 | 1 |
| Cities founded near known resources | 2 | 1 |
| Known radius resources summed at founding | 3 | 3 |
| Cities founded on a resource | 2 | 1 |
| Distinct resource tiles worked | 3 | 3 |
| Resource tile workings | 278 | 244 |
| Activations working resources | 100 | 100 |
| Bonus Food / Production / Gold | 278 / 100 / 156 | 200 / 188 / 0 |

Both factions first know resources at turn/activation zero. A discovers every
type (2 Wheat, 3 of each other type); B discovers 1 Wheat, 2 Cattle, 1 Iron and
1 Spices. A's later Settler founds on known Spices at (1,6), turn 22 / global
activation 44. B does not expand and generates no resource Gold in this run.
These are observed asymmetries, not a provider ranking or efficiency score.

Canonical benchmark SHA-256 values:

```text
initial  95b5c4355a587e4d9473d7636488ea21c5d962e1e25f4bae3b887a12fba837ae
final    e68c54e4d88a579facc5780d9aff7da4f3cfee09cafd4fe5a38bce22a8648e6a
commands 52fa602971d75cbcfed6a5633137fb0ee05e10601bbb97cc07bcdede3e5712d3
plans    44ed6123ed234b15040db104fa55ce703b6b53b08a2d1c3dbf024a9b3f4f3f2e
replay   e68c54e4d88a579facc5780d9aff7da4f3cfee09cafd4fe5a38bce22a8648e6a
```

The summary, verification JSON and per-run command/planner traces are under
`.local/environment-v3-verification-accepted/`. Provenance records revision
`dad2e55c15196e045ac95bbde2d69b2a905a7910`, `sourceDirty=true`; work remains in
the existing working tree, with no commit or deployment performed.

## Files changed in this slice

- Domain: `backend/aig/state.py`, `economy.py`, `setup.py`, `scenarios.py`,
  `snapshots.py`, `knowledge.py`, `public_state.py`, `versions.py`.
- AI: `backend/aig/ai/executor.py`, `strategy.py`, `benchmark_metrics.py`.
- Browser: `frontend/src/js/game.js`, `presentation.js`, `frontend/src/css/main.css`,
  `frontend/tests/game.test.js`.
- Tests: new `tests/test_resources.py` and
  `tests/fixtures/environment-v3-preserved-artifacts.json`; updated
  `test_ai.py`, `test_benchmark.py`, `test_benchmark_preflight.py`, `test_cities.py`,
  `test_combat.py`, `test_commands.py`, `test_economy.py`, `test_experiment_versions.py`,
  `test_knowledge.py`, `test_ollama.py`, `test_openai.py`, `test_production.py`,
  `test_research.py`, `test_state.py`. Historical archive comparisons retain frozen
  digests; live simulation expectations now target V3 rather than V2 emulation.
- Documentation: `README.md`, `docs/benchmarking.md`, this report. Preserved
  `docs/environment-v2.md` and `docs/baselines.md` remain byte-identical.

Environment V3 is ready for controlled heuristic/Qwen/Luna comparison.
