# Environment V2 implementation and verification

Environment V2 is ready for controlled heuristic/Qwen/Luna comparison. This slice
ran only offline heuristic simulations and mocked provider tests. No live Qwen,
Luna, paid, or cloud inference was performed.

## Version artifacts and preservation

| Domain | Final version |
| --- | --- |
| Environment / latest | `environment-v2` |
| Scenario / latest | `scenario-v1` |
| Strategy prompt / latest | `strategy-prompt-v1` |
| StrategicPlan schema / latest | `strategic-plan-schema-v1` |
| Qwen / Luna profiles | `qwen-config-v1` / `luna-config-v1` |
| Benchmark format | `benchmark-v1` (additive metrics) |
| Snapshot schema | v9, previously v8 |

The starting checkout passed 624 Python tests with 5 skips and used snapshot v8
and Environment V1. Its in-progress artifact-versioning changes were preserved.
The exact scenario map, starts, prompt text, logical plan schema and model-profile
payloads remain unchanged. The original prompt already restricts choices to
supplied information, so neither prompt tuning nor a new prompt/schema was needed.
Plan-reference validation now accepts globally supplied civilization IDs and
rejects a remembered city when its visible site is empty; the frozen six-field
schema itself is unchanged.

Environment V1 metadata remains unchanged and selectable for provenance. The
current benchmark refuses to label V2 execution as V1; historical runs require
their recorded source revision. There is no runtime V1 emulation. The latest
environment pointer moved only after implementation checks passed.

All 95 existing local baseline/provenance files matched their pre-change SHA-256
digests after verification, including heuristic, Qwen and Luna artifacts. The
checked-in `tests/fixtures/environment-v1-artifact-hashes.json` preserves those
digests; its regression test checks archives when present and skips when they are
not available in a clean source checkout. Existing prompt/schema digest checks,
profile-value checks and the scenario's original V1 data-projection hash also pass.

## Information and execution behavior

The [architecture](architecture.md#environment-v2-three-information-classes)
documents three distinct information classes:

- **Global:** faction identity/elimination, total military strength, and permitted
  research/economy scoreboard information. Global strength never becomes a list
  of hidden deployments.
- **Persistent:** `PlayerKnowledge` stores explored positions in a set and frozen
  `KnownCity(city_id, owner_id, position)` records in an ID-keyed dictionary. It
  does not duplicate maps or remember enemy unit positions.
- **Current:** enemy unit types, positions, HP and stacks, plus live enemy city
  details, require sight. Undiscovered cities are absent. Hidden discovered cities
  expose identity/location only, with visibility false and live existence unknown.

Sight is derived from live own units/cities using clipped Chebyshev squares.
Settlers, Warriors, Archers and Spearmen see radius 2; Scouts see radius 3; cities
see radius 2. There are no terrain modifiers or line-of-sight blockers.
`create_game()` leaves knowledge empty. `start_game()` initializes legitimate sight
for every faction before the first activation. Domain movement, founding, placement,
production and combat advance update discovery for all observing factions.
Movement/death/removal can shrink current sight without erasing exploration.
Exploring an empty tile never reveals a later city founded there outside sight.
Eliminated players and removed cities retain historical knowledge.

StrategicState exposes complete own unit/city/economy/research data, global summaries,
explored terrain, remembered cities and current visible enemies. Serialization is
detached, canonical and JSON-compatible. Heuristic and LLM providers receive this
same boundary. The heuristic cannot select an undiscovered city or react to hidden
local troops. No threat conclusions were added to the supplied state.

The executor's filtered `PlanningView` prevents hidden terrain, enemy blockers,
undiscovered cities or authoritative failed routes from influencing command choice.
It uses known routes and issues adjacent steps; authoritative engine validation
remains separate and retains the original pathfinder. City-ID collision allocation
is infrastructure and does not influence spatial decisions.

Scouts take immediate legal combat opportunities, otherwise choose known reachable
frontiers by expected coordinate reveal, route length and stable y/x ties. Unit IDs
break execution-order ties. The conventional executor can build one Scout after
initial military needs while unexplored map remains. This is shared across all
providers and does not change their strategic prompt or model. Settlers can seek
frontiers too. Fully explored/unreachable frontiers stop exploration movement.

Five-turn plan reuse remains normal. First city discovery or first military contact
can each trigger a bounded early replan at an activation boundary; simultaneous
discoveries coalesce. Ordinary tiles do not cause replans. Backend traces record the
reason and factual visible strength/distance. Hidden city disappearance does not
invalidate a plan until the site is seen or its owner's elimination is global.

Normal browser DTOs use the active human perspective. Unexplored terrain is null,
explored hidden terrain is dimmed, invisible units disappear, and remembered cities
display without current statistics. AI command coordinates, plans and discovery
reasons stay backend-only. `observer_state()` and benchmark/save truth are separate
Python interfaces; no public observer endpoint was introduced.

Snapshot v9 persists only player knowledge, with coordinates ordered by (y,x) and
cities by ID. It does not persist visibility. Loading has no exploration, discovery,
economy, movement, activation or start side effects. V8 is explicitly rejected.

## Verification

- Python: **671 tests**, **666 passed / 5 skipped**; starting suite 624 tests.
- Frontend: **35 passed**, including fog flags, remembered city inspection and
  disappearing enemy units; frontend build passed.
- Secret-exclusion, mocked provider, API, settings, versioning and existing engine
  regressions passed. No normal automated test called a live model provider.
- Four heuristic trials each completed **100 global turns / 200 activations**.
  Every final state validated; all four initial/final/command/plan hashes matched.
  Every recorded command stream replayed to its recorded final-state hash.
- Each trial founded 3 cities, created 20 units including the four starting units,
  issued 72 movement commands and 18 attacks, and completed Archery and Bronze
  Working for both factions. Plans never selected a city absent from supplied
  discovered-city information.

The final local reports are under `.local/environment-v2-verification/`, with
`summary.json`, `verification.json`, and per-run snapshots/command/plan traces.
Manifests record source revision `dad2e55c15196e045ac95bbde2d69b2a905a7910`
with `sourceDirty=true`: the implementation is in the working tree, not a new commit.

| Factual metric, per identical trial | A | B |
| --- | ---: | ---: |
| Explored tiles | 120 / 120 | 48 / 120 |
| Map explored | 100% | 40% |
| Tiles newly revealed after start | 95 | 23 |
| New tiles attributed to Scouts (movement + spawn sight) | 95 | 23 |
| Scout movement commands | 22 | 2 |
| Discovered enemy cities | 1 | 0 |
| First enemy city: turn / activation, zero-based | 35 / 70 | none |
| First enemy unit: turn / activation, zero-based | 35 / 70 | 36 / 72 |
| Significant-discovery replans | 1 | 1 |
| Plans created / reused | 21 / 79 | 20 / 80 |

B's Scout died in combat before discovering A's city. The scenario supports
discovery, but symmetrical exploration outcomes are not forced. No scenario change
or provider tuning was used to change this result. Visibility-at-replan samples,
existing economy/production/combat metrics and inference counters are in the report;
no arbitrary exploration-quality score was added.

Canonical benchmark SHA-256 digests, identical in all four trials:

```text
initial  9909cafc0758aac5819975f5fbf1e7fb58e631cb26e818047fcad42ec6e58655
final    91cd0ec4b3a2cd4b16b99adb4abd332b54d3c088fb0e49b0afbd428a95b76c5f
commands 770ccb1c9993f148d2e4599c84c2490014328de980a0f3c92a91ef7bb52ac86f
plans    e0f0d4f50eb8ed55e0f481115cdcefda23efcb8c9d70c6f1424b00ff1e9ca778
replay   91cd0ec4b3a2cd4b16b99adb4abd332b54d3c088fb0e49b0afbd428a95b76c5f
```

## Files changed by this slice

- Domain: `backend/aig/state.py`, new `knowledge.py`, `setup.py`, `movement.py`,
  `cities.py`, `combat.py`, `economy.py`, and `snapshots.py`.
- AI: `backend/aig/ai/strategy.py`, new `knowledge_planning.py`, `executor.py`,
  `controller.py`, and runtime reference validation in `plan_schema.py`.
- Versions/measurement: `backend/aig/versions.py`, `ai/benchmark.py`,
  `ai/benchmark_metrics.py`, and the frozen-file hash fixture.
- Public/browser: `backend/aig/public_state.py`, `application.py`,
  `frontend/src/js/game.js`, `frontend/src/css/main.css`, frontend fog tests.
- Tests: new `tests/test_knowledge.py`; updated AI, API, benchmark, city, combat,
  command, economy, experiment-version, Ollama/OpenAI, production, provider-selection,
  research, setup and state tests for V2 boundaries and snapshot v9.
- Documentation: README, architecture, benchmarking, and this report.

Other pre-existing working-tree changes remain intact. No resources, barbarians,
city capture/combat, victory, diplomacy, new units/technologies, prompt tuning,
model changes or UI redesign were added.

## Explicit semantics and limits

No remaining hidden-spatial-information leak was found in the audited provider,
executor or public-response paths; adversarial paired-state tests cover those
boundaries. Hidden city existence is deliberately unknown, including hidden removal.
Historical records remain even after a visible site becomes empty. Terrain is
static; changing terrain outside sight would require a future last-seen terrain model.
First-contact metrics observe every command, but early planning triggers sample
knowledge/current sight at activation boundaries; fleeting unit contact that has
already disappeared does not create enemy-unit memory. Plan caches remain ephemeral.
Operational provider timing remains public; tactical discovery reasons do not.
Observer truth remains available only through explicitly separate backend interfaces.
Cross-environment metric differences must be labeled as environment changes.
