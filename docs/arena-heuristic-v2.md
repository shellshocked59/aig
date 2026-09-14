# Arena Heuristic V2: board control and advancement

Implemented and evaluated locally on 2026-09-13. Recommendation **B: keep V2
explicitly experimental**. V2 creates more useful premium control and Core
pressure, but the side-swapped cases do not demonstrate consistently stronger
play. No default promotion or balance change was made.

## Why V1 turtles

The frozen provider is `HeuristicArenaTurnProvider`, named
`arena-heuristic-v1`, in `backend/aig/arena/ai/heuristic.py`.
Its `tactical_score` is lexicographic: basic attacks have tier 250, Core attacks
200, and every move 100. Therefore even one point of basic damage beats any
positional improvement. This is a hard ordering, not an insufficient damage
weight. Finish, Revive and specials have still higher tiers.

V1 does generate movements while attacks exist, and it does already use BFS,
LOS and bonuses. The problem is not absent move generation. Its positional
value is a maximum of present attack/support opportunities plus fixed bonuses;
it has no exposure cost or continuous enemy/Core approach term. Once a unit has
a high-valued firing position, most other squares have no positive gain.
`movement_options` rejects those goals, and the attack tier wins against the
remaining moves. This also permits premature advances into unsafe firing lanes.

The preserved self-play case demonstrates the asymmetry: Blue makes 11 moves,
Red only one; Red wins by elimination at player turn 10. Neither Core takes
damage; neither side uses POWER. V1 is not universally stationary, but its
reactive side can remain near its starting area while attacking/healing.

## Architecture and selection

`HeuristicArenaTurnProviderV2` lives in a separate `heuristic_v2.py`, with identity
`arena-heuristic-v2`. It uses the existing observation reconstruction, legal
action queries, detached command application, turn plan, executor and trace.
Each AP decision enumerates legal actions, evaluates their actual post-action
state, chooses deterministically and applies the choice to the detached state.
There is no minimax, MCTS, randomness, model call or new game-state field.

The new `gameplay.create_offline_turn_provider` accepts `heuristic` and
`heuristic-v1` for V1, and `heuristic-v2` for V2. The research provider factory,
controller module and API router are source-hash-frozen and remain byte-identical.
The existing `heuristic` default, model-failure fallback, stepwise/action-ID
baselines and historical benchmark selections still resolve V1. The existing
settings validation is unchanged; use an explicit provider argument to select
V2 through the offline factory. Browser selection uses
`/api/arena/demo-ai/heuristic-v2` on the web host and the public gameplay label
`heuristic-v2_ai`. Internally the session retains the frozen heuristic controller
enum and supplies an explicit V2 provider to the existing orchestrator. Exact
V1/V2 gameplay routes precede the frozen generic provider route. The API-only
research host is unchanged. The original offline button remains V1.
Normal experiment code can inject `create_offline_turn_provider` into
`simulate(provider_factory=..., blue_provider="heuristic-v1", red_provider="heuristic-v2")`.

## Inspectable scoring

Urgent V1 tactical rules remain shared read-only helpers: immediate win, removal
of an obvious one-basic-hit Core threat, Finish, Revive and lethal/down actions
retain their tiers. Nonwinning Fireball that downs a friendly remains rejected.
Ordinary attacks instead earn three utility points per actual capped damage.
Their value can be exceeded by a productive move. Useful Heal, Fireball, Snipe
and Bash retain explicit tactical utility derived from the existing helper.

Position is evaluated for the acting unit before and after a move:

| Component | Formula / meaning |
| --- | --- |
| Advancement | -4 times the minimum legal steps to a firing square for an active enemy |
| Core pressure | -2 times steps to a Core firing square; -1 for Cleric; +8 when Core is presently attackable |
| Future threat | +8 per currently reachable enemy, capped at two targets |
| POWER | 8 + base damage, allowing offensive stats to determine value |
| WARD | 5 + missing HP + 6 when an enemy currently has a firing lane |
| SIEGE | max(0, 18 - 5 times steps to a Core firing square) |
| Cleric support | Best ally proximity value, plus downed-ally access within two squares |
| Exposure | Negative estimated concentrated basic damage, with an additional fourfold penalty for damage reaching/exceeding current HP |
| Move repetition | -3 per previous move by that unit; -40 for a position already visited this turn |

Exposure takes the four largest currently legal enemy basic damage potentials
and repeats the largest once, representing at most five AP. It uses actual
POWER/WARD damage and existing LOS. This is a conservative potential estimate,
not a prediction of enemy actions. It does not estimate enemy movement or
special attacks. Knight durability naturally tolerates more exposure; fragile
classes reach their lethal penalty sooner. Ranger range creates more safe
firing squares, Mage range creates closer engagement, and Cleric support keeps
allies relevant without fixed class routes.

One BFS per positional evaluation uses engine `can_step`, including occupancy
and blocked-corner rules. Firing-square goals use engine Chebyshev distance and
the shared LOS helper. Unreachable goals use a bounded 12-step penalty. No
Euclidean metric or duplicated LOS implementation is introduced.

Bash adds contextual premium denial: the enemy's premium utility before minus
after displacement. Occupancy rewards inherently favor available useful tiles;
there is no speculative credit for forcing an enemy to move later.

Moves must improve total utility by at least two after repeat penalties.
Canonical action JSON and AP cost break ties. The original square and all
subsequent destinations are remembered only within this plan. Revisits have a
large penalty, not an absolute ban on a tactically justified return. No tested
opening or full comparison match has an intra-turn movement revisit (see
`final/movement-audit.json`). These rules do not prevent cross-turn oscillation.

`provider.last_scores` exposes each decision's selected action and all scored
candidates, with tier, total and named components. It is provider-local debug
data, never part of an observation, game snapshot or model contract. JSON
examples are in the evaluation output.

## Deterministic comparison

Run the offline-only harness:

```powershell
.venv/Scripts/python.exe -m aig.arena.heuristic_evaluation --output .local/arena-heuristic-v2/final
```

It constructs only the two local heuristics and uses the frozen mirrored 9x5
scenario. Four cases with side swaps are useful evidence; repetitions of an
identical deterministic match are not independent samples. Each command trace
replays exactly. The bound is 30 global rounds; every case finished normally.

| Blue / Red | Winner / mechanism | Player turns | Moves B/R | AP spent B/R | AP unused B/R | Basic attacks B/R | Core damage B/R |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| V1 / V1 | Red / elimination | 10 | 11 / 1 | 25 / 23 | 0 / 2 | 8 / 7 | 0 / 0 |
| V2 / V2 | Blue / Core destroyed | 9 | 6 / 3 | 25 / 20 | 0 / 0 | 4 / 1 | 30 / 0 |
| V1 / V2 | Red / Core destroyed | 8 | 4 / 5 | 20 / 19 | 0 / 1 | 5 / 5 | 9 / 30 |
| V2 / V1 | Red / elimination | 10 | 11 / 4 | 25 / 22 | 0 / 3 | 2 / 5 | 0 / 0 |

Movement AP equals move count. Unused AP includes terminal leftovers. No case
has an invalid/truncated plan or zero-action turn. V2 spends its AP, but more
movement is not automatically better: V2 Blue still loses against V1 Red.

| Blue / Red | Occupancy actions B/R | Unique premium squares B/R | End turns POWER B/R | WARD B/R | SIEGE B/R | Actual premium displacements B/R |
| --- | --- | --- | --- | --- | --- | --- |
| V1 / V1 | 14 / 2 | 3 / 1 | 0 / 0 | 1 / 1 | 1 / 0 | 1 / 1 |
| V2 / V2 | 14 / 9 | 3 / 1 | 4 / 0 | 0 / 4 | 5 / 0 | 0 / 0 |
| V1 / V2 | 16 / 12 | 3 / 3 | 2 / 1 | 0 / 4 | 2 / 2 | 1 / 1 |
| V2 / V1 | 12 / 10 | 5 / 2 | 3 / 2 | 1 / 1 | 5 / 0 | 0 / 0 |

Occupancy actions count gameplay actions whose actor ends on a premium tile,
not all stationary units and not End Turn commands. Unique squares use that
same definition. End-turn counts mean at least one active friendly occupies
that bonus type, with the acting side's terminal position included. Actual
displacements include removal or a changed position of an enemy previously on
a bonus; hypothetical denial is not counted.

All sides first occupy a premium tile on their first player turn except V1 Red
in V1 self-play, which first occupies one at player turn 6. First combat B/R is
1/2, 1/4, 1/4 and 1/2 respectively. First Core damage B/R is absent/absent,
9/absent, 3/8 and absent/absent. V2 self-play Blue delivers four Core attacks;
V2 Red against V1 likewise delivers four.

`board_control.progression` contains mean/minimum active-unit Chebyshev distance
to enemy Core and nearest active enemy, center-column occupancy and opponent-half
occupancy after each side's turns. These are descriptive geometry metrics;
planning itself uses path distance to firing squares. In self-play V2 Blue's
mean Core distance changes from 5.75 after its first turn to 4.67 at victory;
Red changes from 6.5 to 6.0. V1 self-play Red finishes at 7.67. Loss/removal of
units changes these means, so they are not a standalone performance score.

Full snapshots, final unit/Core HP, plans, per-action tactical counts, all
progression samples and replay hashes are preserved in the four case JSON files
under `.local/arena-heuristic-v2/final/`. Initial exploratory outputs in the
parent directory were retained separately.

## Preservation and tests

`heuristic.py` itself was not edited. The original controller, factory and API
router are also restored byte-identically; the full suite's frozen-source test
revealed that their selection plumbing is part of the research preservation
boundary. V2 selection therefore lives in the separate gameplay layer, without
changing any frozen hashes or weakening the preservation test. All five
historical Phase 3 hashes match:

| Artifact | SHA-256 |
| --- | --- |
| Plans | `5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c` |
| Commands | `88328e37527ddb68abf63b091613f7c1282a4581ebe72da394511838b3e6f0ae` |
| Final state | `01720d448acca31206574e16fa3182ffc5c2a40e033e89d5043d56fb21939f2a` |
| Command trace | `6b7c60fbb3d8dcd8451e0692bd764135a5c1b31c5abd35dbcc1101042b6f4f5d` |
| AI trace | `9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1` |

The known Red elimination victory, ten player turns and 52 commands are unchanged.
Existing frozen probe and benchmark-preservation tests remain in the suite.
No historical artifact, rules module, scenario, LOS, combat bonus, model
provider, research benchmark implementation or Empire source was changed by
this phase. POWER +2, WARD -2 and SIEGE +4 remain unchanged.

The 16 new Python tests cover determinism, detached observations and reordered
unit ties; advancement; beneficial POWER; safe WARD versus nonlethal attack;
SIEGE/Core approach; avoiding exposed POWER; the seven existing tactical probe
first choices and legal suffixes; Heal/friendly-fire safety; revived-ally action;
Core emergency; contextual Bash denial; AP/no loops; no-action termination;
blocked-path agreement; version selection including mixed controllers; offline
session integration; metric boundaries; and HTTP presentation events.
The frontend adds a V2 selection/label/reset regression test. Assertions focus
on behavior rather than pinning arbitrary coordinates except the deliberately
unsafe POWER square.

Final Python suite: **1,215 passed, 5 skipped** (1,220 tests, 352.506 seconds),
including frozen-source and historical probe/hash preservation. The successful
log is `.local/arena-heuristic-v2/python-tests-final.log`. The initial failed
source-boundary check is retained in `python-tests.log`; the frozen files were
restored and no preservation expectations were edited.

Frontend: **172 passed**. Production build: **passed**. Logs are
`frontend-tests.log` and `build.log` in the same output directory. After isolating
selection, all four cases were rerun under `verified/`; plans, all five hashes,
board metrics and tactical metrics exactly match the reported `final/` cases.
See `verified/selection-layer-preservation.json`. Those reruns verify the
selection layer, not independent gameplay samples.

## Planning timing

Single local samples including detached reconstruction, excluding observation
construction and animation, with the full test suite running concurrently:

| State | V1 ms | V2 ms |
| --- | ---: | ---: |
| Opening | 369 | 428 |
| Finish / Core | 88 | 144 |
| Revive | 140 | 249 |
| Fireball | 158 | 430 |
| Bash | 100 | 204 |
| Snipe | 96 | 257 |
| Immediate Core win | 23 | 77 |
| Immediate elimination | 21 | 59 |

These are basic planning checks, not latency percentiles. V2 is slower on small
tactical states but stays below half a second in these samples. The opening
cost is comparable; browser animation remains separate. No large search tree
was introduced.

## Browser and manual playtest

The browser offers **Human vs Heuristic V2 · Offline** alongside the unchanged
V1 button. Reset retains V2. It uses the existing semantic presentation engine
and animation handlers without a V2 animation special case. HTTP tests verify
the provider trace and standard presentation events.

The user tried manual play during this session and reported: **“tried manual
seemed to be fine.”** This is user-supplied qualitative feedback, not an
instrumented or assistant-observed complete-game record. Exact duration,
winner, and detailed Finish/Revive/oscillation observations were not supplied.
The assistant could not perform its own visual game: computer-use inventory
returned `apps: []` and `browsers: []`. No screenshots were captured, and this
report does not substitute headless results for visual observations.

The automated evidence shows advancement, useful bonus occupation and Core
pressure. It does **not** prove absence of turtling: V2 Red self-play remains
largely defensive, repeatedly healing/reviving near WARD while Blue pressures
the Core. Nor does it prove absence of overextension: V2 Blue loses by team
elimination to V1. The intentionally obvious suicidal premium fixture passes.
Detailed visual assessment remains unverified despite the user's satisfactory
initial playtest; a complete-game visual record was not captured.

Normal launch:

```powershell
cd C:\code\aig
npm.cmd run dev
```

Open `http://127.0.0.1:5173/arena`. Since that port was already in use during this
session, the evaluated build was also hosted without stopping the existing
server at `http://127.0.0.1:8016/arena` using:

```powershell
npm.cmd run build
.venv/Scripts/python.exe -m uvicorn aig.web:create_app --factory --host 127.0.0.1 --port 8016
```

## Changed files and next priority

Added `backend/aig/arena/ai/heuristic_v2.py`, `backend/aig/arena/gameplay.py`,
`backend/aig/arena/heuristic_evaluation.py`,
`tests/test_arena_heuristic_v2.py`, and this document.
Connected the separate gameplay session/routes in `backend/aig/web.py`;
added the V2 option and regression test in `frontend/src/js/arena.js` and
`frontend/tests/arena.test.js`, and linked this report from `docs/arena-ai.md`.
The pre-existing uncommitted UI Phase 4 work was
preserved. No live model inference occurred.

Premium bonuses are valuable enough to affect V2 play under current rules;
there is no evidence here requiring a bonus-value change. Next priority is
gameplay review of defensive recovery loops and exposure after enemy movement,
followed by modest heuristic tuning if observed play warrants it. Complete a
recorded meaningful visual game before any promotion decision. Keep balancing,
research defaults and future model comparisons as separate decisions.
