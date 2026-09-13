# Environment V4: barbarian camps and local hostile threats

V4 adds a small deterministic system faction to V3 resources and fog. It reuses
Warrior movement, HP, attacks, retaliation, occupancy, pathfinding and unit IDs.
It has no StrategyProvider, cities, economy, research, Settlers or civilization
scoreboard entry. No city combat/capture, victory, diplomacy, pillaging, XP,
promotions, improvements or prompt tuning were added.

| Artifact | Concrete version |
| --- | --- |
| Environment / runtime / latest | environment-v4 |
| Scenario / latest | scenario-v3 |
| Strategic instructions | strategy-prompt-v1 |
| Six-field plan schema | strategic-plan-schema-v1 |
| Qwen / Luna profiles | qwen-config-v1 / luna-config-v1 |
| Benchmark | benchmark-v1, additive observations |
| Snapshot | v11, previously v10 |

Luna is the production target. Qwen's frozen 4096-token context is a comparison
constraint, not a requirement to remove useful game information. No profile or
prompt changed. No live Ollama or OpenAI requests were made in this slice.
Historical environments remain registered metadata and require their recorded
source revision; the current engine refuses to label V4 execution as V1/V2/V3.
Scenario V1/V2 inputs remain available unchanged.

## State and lifecycle

`PlayerState.kind` explicitly distinguishes `civilization` from `barbarian`.
The reserved internal owner `barbarians` uses the AI controller marker plus the
separate system kind. Setup creates it internally only for camp-bearing scenarios,
after validating the normal civilization roster. Its technologies are empty.
Normal research, economy, founding and production commands reject system actors.
The shared allocator restricts their units to Warriors.

Activation order is A, B, barbarians. Entering the system activation refreshes
its existing Warriors and resolves scheduled replacements before they act.
`BarbarianController` issues ordinary `MoveUnit`, `AttackUnit`, `EndActivation`
commands. System EndActivation skips civilization economy, then wraps the global
turn and refreshes A. Applications automatically process this phase before
returning control to a human; simulation and benchmark loops explicitly include
it without calling a strategic provider. Benchmark command replay uses the same
entry hook, so spawn commands or redundant timer state are unnecessary.

Terminal-state checks count surviving civilizations, excluding the system owner.
With fewer than two surviving civilizations, activation becomes null without
incrementing the turn or executing another barbarian phase. Infrastructure
elimination of the final normal activation enters the system phase only while at
least two civilizations survive. The system owner cannot itself be eliminated.
No conquest-driven elimination was introduced.

## Camps and Scenario V3

`BarbarianCamp(id, position)` is immutable; `GameState.camps` is the mutable
ID-keyed live collection. Camp IDs are scenario-supplied. Camps require unique
passable land: Grassland, Plains, Forest or Hills. Water, Mountains, missing tiles,
duplicate IDs/positions, cities and civilization starting positions are rejected.
Cities cannot subsequently be founded on camps. Camps have no territory or yields.
Resources may share their tiles and remain after clearing.

Scenario V3 preserves V2's 12 × 10 terrain, all 14 resources, seed 42, A=(2,2),
B=(9,7), and A/B order. Each of the three camps starts with one ordinary Warrior.

| Camp | Position | Resource | Placement rationale |
| --- | --- | --- | --- |
| camp-1 | (1,6) | Spices | A's southern exploration opportunity, four tiles from A |
| camp-2 | (10,3) | Spices | B's northern exploration opportunity, four tiles from B |
| camp-3 | (6,4) | Cattle | Central contested corridor, near the central resource region |

All camps are outside both starting radius-two sight areas. The central camp is
four tiles from A and three from B; the original asymmetric map remains intact.
Initial defenders use unit-5, unit-6, unit-7 in camp-ID order, after the unchanged
four civilization starting units. They guard when no local target is visible.

## Local tactical behavior

Each Warrior acts in ascending unit-ID order. Its current radius-two sight and
its home camp's radius-two sight determine its available targets and routing
terrain. Other camps' or Warriors' sightings cannot disclose distant targets.
No persistent enemy-unit memory or omniscient pursuit is used.

Legal attacks rank lethal first, then Settler, lowest HP, shortest Chebyshev
distance and stable unit ID. A Settler is lethal under the existing combat rules,
so it wins the civilian tie-break among lethal targets. If no attack is legal,
the Warrior approaches the nearest visible target within five tiles of both
itself and its surviving home camp. With no qualifying target it stays within,
or attempts to return to, radius two of its camp using locally visible routes.
Paths can be blocked; idle Warriors do not wander randomly or search unseen terrain.
An orphan keeps living and can react locally, but has no return destination.

Settlers die on attack under existing civilian rules. Scouts can fight, clear
camps and die under ordinary damage rules. Cities block hostile entry even when
their last defending unit dies. There is no city damage, capture or pillaging.

## Fog and planner boundaries

Normal sight adds `KnownCamp(id, position, last_seen_turn)` to player knowledge.
Presence is the last observed fact, not guaranteed current truth. Hidden cleared
camps remain in another player's memory; revisiting their empty tile removes the
record. There is no persistent barbarian-unit tactical memory.

`StrategicState` adds `known_barbarian_camps` and `visible_barbarian_units`.
Known camp rows have coordinates, last-seen turn, current visibility and
`live_exists` (null outside sight). Unit rows supply visible ordinary combat facts.
Barbarians are excluded from `civilizations`, civilization `enemy_units`, and
global/visible civilization military summaries. No global barbarian count,
strength, spawn schedule state or home association enters provider input.

The heuristic applies its existing local-strength comparison to visible
civilization and barbarian troops together. It still chooses civilization
targets only. Every provider shares the same filtered executor: existing legal
combat opportunities include visible barbarians; an adjacent known enterable camp
is a one-step tactical opportunity. There is no global camp-clearing campaign or
hidden camp targeting. Settlers route around visible occupied tiles normally.
PlanningView removes home associations from visible enemy-unit copies.

First camp discovery or first barbarian contact can trigger an early replan at
the next planning boundary. Each is bounded to one trigger; simultaneous facts
coalesce with other discovery reasons. Ordinary movement does not trigger replans.
Five-turn reuse otherwise remains. Traces record the reason.

Public DTOs remove the system scoreboard entry, omit hidden units/camps and remove
all unit home associations. `barbarianCamps` is rebuilt from player memory.
`observer_state()` retains authoritative camps and home associations only for
backend inspection. The browser reuses the Warrior sprite with a hostile tint and
adds an original compact SVG camp icon, dimmed under explored fog. No UI redesign.

## Spawning, clearing and persistence

On entry to the system activation at global turns 8,16,24,... (never turn zero),
each surviving camp in ascending ID order attempts one Warrior replacement if it
has fewer than two associated live Warriors. Only its own tile is considered.
Enemy occupancy blocks spawning; same-owner stacking remains legal. A skipped
cycle allocates no ID and creates no backlog. Spawned Warriors can act immediately.
Cleared camps never spawn again; their surviving associated Warriors do not despawn.

A successful civilization combat-unit move through or onto an undefended camp
removes it and awards exactly 25 Gold, atomically with movement. Warrior, Scout,
Archer and Spearman qualify. Settlers may enter an empty camp but cannot clear it
or found a city there. Failed moves award nothing. Multi-step moves treat each
traversed tile as an entry; resources remain. Removal prevents repeat rewards.

Existing melee combat advances a surviving attacker onto a killed defender's
tile. This **does not clear a camp**: the camp remains until a later qualifying
move enters it. A melee survivor standing there must leave and re-enter. This
preserves the requested separation between killing a defender and clearing its
camp without changing normal combat advance.

Snapshot v11 stores the faction kind, live camps, per-unit nullable home camp ID,
and remembered camp records. Camps/memories are ordered by ID; other canonical
ordering is unchanged. Current visibility, threat conclusions and spawn countdowns
are not persisted. Restore validates and reconstructs exact state without running
the entry hook, refreshing movement, revealing camps, clearing, rewarding or
spawning. Earlier snapshot schemas, including v10, are explicitly rejected.

## Benchmark measurements

All V4 metrics are observer instrumentation, excluded from provider state.

- Discovery: distinct camps ever discovered, first discovery turn/activation,
  Scout movement/production attribution, current known count and objectively stale
  known count at the end. Per-camp discovery timestamps remain in reports.
- Combat: distinct barbarian unit IDs sighted, first sighting, attacks against
  barbarians, kills, civilization losses (including Settlers/Scouts), and actual
  capped HP damage in both directions, including retaliation.
- Clearing: camp ID, turn/activation, unit type, Gold, and discovery-to-clear delay.
  Camp Gold stays separate from resource-bonus Gold.
- Spawning: replacement count, per-camp count, blocked attempts, separate capped cycles,
  and maximum concurrent barbarian units. Initial defenders are not replacements.
  Command outcomes include system spawn/skip/clear events; system activations are
  marked separately and have no fabricated plan or provider inference.
- Military response: existing production-by-type, military strength and posture
  counts plus DEFEND activations with visible civilization threats, barbarian
  threats, or neither. The first two may both count when both kinds are visible.
  These are visible combat-unit facts, not an inferred danger/efficiency score.
- Expansion/economy: existing founding timestamps, Settlers produced, city count,
  population, treasury, resource discovery/workings/yields; added Settler movement
  and barbarian deaths. Cross-environment timing comparisons remain descriptive.
- Context: compact canonical UTF-8 StrategicState bytes at each replan and the
  marginal bytes of the two barbarian fields on that same state. This isolates
  serialization overhead, not behavioral differences between V3/V4 worlds.
  No token estimates or model tokenizer requests are made.

## Verification and files

The starting checkout passed 710 Python tests (705 passed, five skipped), 37
frontend tests, and used snapshot v10. Existing V1/V2/V3 archive checks remain;
the new preservation manifest covers another explicit set of 821 files including
V3 live archives, prior fixtures, historical environment/baseline documentation
and frozen prompt/profile source. Original scenario projection digests remain
checked without rewriting old expected hashes.

Source changes in this slice:

- Domain: new `backend/aig/barbarians.py`; `state.py`, `setup.py`, `scenarios.py`,
  `knowledge.py`, `movement.py`, `commands.py`, `economy.py`, `research.py`,
  `snapshots.py`, `public_state.py`, `application.py`, `versions.py`.
- AI: new `backend/aig/ai/barbarian_metrics.py`; `strategy.py`, `controller.py`,
  `executor.py`, `knowledge_planning.py`, `simulate.py`, `benchmark.py`,
  `benchmark_metrics.py`.
- Browser: `frontend/src/js/presentation.js`, `game.js`, `frontend/src/css/main.css`,
  `frontend/tests/game.test.js`.
- Tests: new `tests/test_barbarians.py` and
  `tests/fixtures/environment-v4-preserved-artifacts.json`; schema/version/phase
  expectation updates in `test_ai`, `test_api`, `test_benchmark`,
  `test_benchmark_preflight`, `test_cities`, `test_combat`, `test_commands`,
  `test_economy`, `test_experiment_versions`, `test_knowledge`, `test_ollama`,
  `test_openai`, `test_production`, `test_provider_selection`, `test_research`,
  `test_resources`, `test_setup`, `test_state`.
- Documentation: this report, `docs/benchmarking.md`, `README.md`.

Pre-existing uncommitted work was retained. No commit, deployment, GitHub operation,
live model benchmark or Environment V5 work was performed.

## Offline results and limitations

Four deterministic heuristic trials each completed 100 global turns: 200
civilization activations and 100 automatic system activations. Each validated
and replayed exactly. They made zero inference requests. All four initial-state,
final-state, command and plan digests matched. Frontend verification passed all
40 tests and the production build; the focused V4 suite adds 51 Python tests.

The following are per-trial results, not totals across the four repeats:

| Factual measurement | A | B |
| --- | ---: | ---: |
| Camps discovered | 3 | 2 |
| Scout-attributed camp discoveries | 3 | 2 |
| First camp/barbarian contact turn | 10 | 19 |
| Distinct barbarian Warriors sighted | 10 | 4 |
| Attacks against barbarians | 23 | 8 |
| Barbarian units killed, including retaliation | 8 | 1 |
| Civilization units killed by barbarians | 6 | 3 |
| Scouts killed by barbarians | 4 | 3 |
| Settlers killed by barbarians | 0 | 0 |
| Camps cleared | 0 | 1 |
| Camp-clear Gold | 0 | 25 |
| Camps still known / objectively stale at end | 2 / 0 | 1 / 0 |
| Final cities / population | 2 / 15 | 1 / 8 |
| Settlers produced / movement commands | 1 / 4 | 0 / 0 |
| Final treasury | 145 | 83 |
| Resource-bonus Food / Production / Gold | 327 / 166 / 122 | 200 / 188 / 0 |
| DEFEND with visible civilization threat | 15 | 34 |
| DEFEND with visible barbarian threat | 4 | 4 |
| DEFEND without either visible threat | 2 | 2 |

B's Warrior clears camp-3 at turn 23, activation 70, four turns / twelve
all-faction activations after discovery. A never clears a camp in this run.
There are ten replacement spawns: three at camp-1, five at camp-2 and two at
camp-3. Maximum concurrent barbarians is six. Sixteen camp cycles are capped;
no eligible spawn is blocked in this scenario run. Focused tests separately
exercise blocked spawning and distinguish it from cap suppression.

The full command stream contains 104 attacks: 93 civilization attacks and eleven
system attacks. Civilization production is A: 19 Archers, six Scouts, one Settler,
one Warrior; B: three Archers, three Scouts, eleven Warriors. There are 44 plans
created and 156 reused. DEFEND categories may overlap. Four DEFEND activations
have neither kind currently visible, consistent with the retained five-turn plan
reuse; the instrumentation records this instead of forcing better-looking results.

Both capitals are founded at turn zero. A's second city is founded at turn 34,
versus turn 22 in the preserved accepted V3 heuristic report: twelve turns later
and at a different site. This is a descriptive comparison to the existing archive;
V3 was not rerun. B remains at one city. No Settler dies in these four identical
trials, while focused ordinary-combat tests prove Settler vulnerability. Seven
Scout losses demonstrate actual exploration risk. Remaining camps and asymmetric
expansion are experimental outcomes, not targets for heuristic tuning.

Serialized StrategicState ranges from 2,240 to 9,341 UTF-8 bytes for A and 2,262
to 6,624 for B. The two V4 fields add 56–687 bytes for A and 56–370 for B over the
same state with those fields omitted. This is a measured serialization delta,
not a Qwen token estimate or a claim about live model context consumption.

No hidden-state leak was found in the tested provider/public/executor boundaries.
Paired-world tests change hidden camps and Warriors without changing decisions
or player payloads. Local barbarian targeting separately rejects distant shared
sight. Stale memory, terminal phase behavior and melee advance are explicit above.
The supported local controller may idle behind impassable terrain and does not
coordinate a campaign. These limitations remain visible in the experiment.


Final Python total: **761 tests, 756 passed and five existing skips**. All 821
preservation files were present and byte-identical. `git diff --check` passed.
Final reports, snapshots, command/planner traces and verification JSON are under
`.local/environment-v4-verification-accepted/`. Source revision is
`dad2e55c15196e045ac95bbde2d69b2a905a7910`, with the existing working tree dirty.

Canonical SHA-256 values, identical across all four accepted trials:

```text
commands       60adae1b6f6e32edff99d5fec2615db5f192efe7ee651e04197a8f412e07ffb9
final_state    c9ffd44b7b50bc0e9fc42bd2753a3be474f74bc606cccf3b151c5d30adfb6e2c
initial_state  fbe659d267383596aba464375c11a1276fdcefe549217662ec42d6986f8f02d1
plans          eea8a9f5dcdf65bd0080dfdad491443bb5f9df234d718287e63cea0da3ddf598
```

The replay final hash equals `final_state` above. Scenario V3's deterministic
started AI setup is the `initial_state` hash. Neither repeated trials nor replay
perform any external model calls.

Environment V4 is ready for controlled heuristic/Qwen/Luna comparison.
