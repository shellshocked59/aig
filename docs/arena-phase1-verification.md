# Arena Phase 1 implementation and verification

Verified locally on 2026-09-13 with Python 3.14.3 and Node 24.14.1. Arena is additive; no Phase 2 mechanics or Arena
AI were implemented. [Rules and usage](arena.md) are the implementation contract.

## Implementation inventory

| Added files | Responsibility |
| --- | --- |
| `backend/aig/arena/state.py` | Distinct validated ArenaState, row-major immutable 9x5 board, players, units, Cores, centralized class stats and Arena config |
| `backend/aig/arena/scenarios.py` | Original deterministic mirrored `arena-scenario-v1` setup |
| `backend/aig/arena/commands.py` | Frozen Move/Attack/Heal/EndTurn commands, deterministic BFS, atomic resolution, AP and immediate victory |
| `backend/aig/arena/snapshots.py` | Strict `arena-snapshot-v1` / `arena-command-v1` conversion and canonical SHA-256 hashes |
| `backend/aig/arena/replay.py` | Headless supplied-command simulation, verified `arena-trace-v1`, pure/trace-derived metrics |
| `backend/aig/arena/public_state.py` | Detached perfect-information DTO with authoritative legal destinations and targets |
| `backend/aig/arena/application.py` | Independent locked Arena hot-seat session |
| `backend/aig/arena/api.py` | Arena read/demo/command/trace routes |
| `backend/aig/arena/__init__.py`, `__main__.py` | Headless library exports and CLI inspection/application/resume/replay |
| `frontend/src/js/arena.js`, `api/arena.js` | Arena DOM controller and versioned API client |
| `frontend/src/js/arena-icons.js`, `frontend/src/css/arena.css` | Original inline SVG placeholders and scoped Arena presentation |
| `frontend/src/js/environments.js` | Explicit Empire/Arena selection with independent retained views |
| `tests/test_arena.py`, `tests/test_arena_api.py` | 52 new Python tests, including parameterized subcases |
| `frontend/tests/arena.test.js` | 16 new frontend tests |
| `scripts/arena-smoke.mjs` | Real HTTP plus DOM complete-match smoke |
| `docs/arena.md`, this document | Rules, architecture, usage, limitations and verification |

Existing files changed:

- `backend/aig/api.py`: mount the independent Arena router/session and expose
  `/api/environments`. Existing Empire routes and DTOs are retained.
- `frontend/src/js/main.js`: mount the environment selector and import Arena CSS.
- `frontend/src/js/api/game.js`: export the existing native fetch wrapper for
  Arena, keeping native network calls at the existing audited location. The
  Empire client's payloads, routes, errors and origin handling are unchanged.
- `README.md`, `docs/architecture.md`, `frontend/src/assets/README.md`: document
  both environments, Arena launch, and original icon provenance.

No shared engine utilities were extracted. Arena reuses only `Position` and the
fixed neighbor-order tuple. It owns separate pathfinding because occupancy is
different. Existing Empire canonicalization remains unchanged; Arena hashes have
their own explicit contract. Small browser error/escaping/fetch utilities are
reused without introducing generic game-state or planner abstractions.

## Rules delivered

Two teams each start with Knight (18 HP, 6 damage, range 1, move 2), Ranger
(10/5/3/3), Mage (9/6/2/2), Cleric (11/3/2/2, heal 5 within range 2), and a 30-HP
Core. The full board and both teams are always visible.

Each player turn has five shared AP; every successful Move/Attack/Heal costs one.
Units may act repeatedly. Invalid actions are atomic no-ops. End Turn is explicit,
including at zero AP, restores five AP, and increments global turn only on the
Red-to-Blue wrap.

Movement is deterministic eight-direction BFS. A move covers up to class range
for one AP. All units, Cores and blocked terrain prevent entry/transit; diagonal
corner cutting follows the existing geometry. Attacks use Chebyshev range with
no retaliation or LOS. POWER adds two damage; WARD removes two incoming unit
damage with minimum one; SIEGE adds four damage against a Core. Clerics heal
friendly units, including themselves, clamped to max HP; full HP, Core and enemy
healing are rejected. Core destruction or zero enemy units wins immediately,
clears the active player and prevents every further gameplay command.

Snapshots preserve full board, identities, positions, HP, AP, turn and terminal
result without loading effects. Replay verifies versioned commands, command
hashes, before/after state hashes and exact trace counters on detached state.
Metrics report per-player unit count, unit/Core HP, attacks, actual damage/healing,
AP spent/discarded, turn wraps, remaining AP and winner without a quality score.

## Verification results

| Check | Result |
| --- | --- |
| Baseline Python suite before implementation | 805 tests, OK, 5 skipped |
| Final full Python suite | **857 tests: 852 passed, 5 skipped**, 106.719 seconds |
| New Arena Python tests | **52**, all passing as part of the full suite |
| Frontend suite | **58 passed**, including all 42 existing tests and 16 Arena tests |
| Production frontend build | Passed; esbuild emitted JS, CSS and original Empire sprite asset |
| Live HTTP + DOM smoke | Passed: 14 commands, movement, unit attack, self-heal, Core attack, 0 AP, End Turn and victory |
| Headless CLI | Scenario inspection, supplied command application, snapshot resume and trace replay passed |
| Whitespace checks | `git diff --check` passed |
| Pre-existing local artifacts | **2,206 files compared; zero changed**, including 1,296 benchmark-related files and 11 ZIP archives |

The Python suite exercises blocked/occupied transit, move ranges/ties, AP and turn
wraps, all class attacks, additive bonuses, heal restrictions, both victory paths,
terminal rejection, strict snapshot loading, exact hashes, replay tampering,
detached DTOs, real API command routes, concurrent End Turn serialization and
cross-environment rejection. A complete fixed-scenario Core win is tested through
both the headless runner and HTTP.

The frontend suite covers visible entry/board/units/Core/bonus icons, selection,
Move/Attack/Heal including self-heal, Core victory, explicit End Turn, unavailable
actions, invalid targets, server rejection, in-flight duplicate prevention,
reset, escaped labels, environment switching, and API errors/origin handling.
The live smoke uses these controllers with an actual local Uvicorn API rather
than a stubbed API response. Its terminal state hash is:

```text
ddfef0720614c5170d9c586572fa75295a79897c6b27e4efa41a14ea47664a14
```

Arena initial-state regression hash:

```text
879d9e26f1116cb9628d2889f09526c2ccf7f947bd5c0c2a1727df991cd7c800
```

Arena `ArenaEndTurn("blue")` command regression hash:

```text
ec36997239f1c123371122f3efdd7fd4d5a413a9d953b5cba3d6c4714cbacee1
```

## Empire preservation evidence

Git comparison confirms no changes to Empire state, rules, commands, movement,
application session, public state, snapshot v12, scenario/version registries,
AI/provider/prompt/schema/model/benchmark code, existing regression tests, browser
view, stylesheet or CI configuration. All existing tests remain passing.

Existing frozen prompt/schema/scenario/profile tests ran unchanged. The existing
100-turn-budget heuristic regression still reproduces its recorded conquest at
turn 75 with 225 activations, and preserves these pinned hashes:

```text
Empire snapshot: 8859a9dbe564c70105c62e9764ef6d857ea22b674049983857f0256ef3f9bb48
Empire trace:    b9f5bc4faf4b13b8aa0262170ec3f7c058dc14b33e2f2bc20758ea98adbb2302
```

The before/after SHA-256 comparison covered accessible pre-existing `.local`
files, including the saved benchmark traces, reports, provenance files and ZIPs.
Three pre-existing Python dependency directories under `.local/docker-validation`
were unreadable and excluded; they are not benchmark artifacts and were not edited.
No live Qwen/Luna experiments or provider calls were run.

## Verification boundaries and Phase 2 decisions

The available browser tool reported no browser surfaces, so native browser visual
review was unavailable. jsdom interaction tests, the real HTTP/DOM complete match
and the production build passed, but they do not prove visual layout quality.
Remote GitHub CI/deployment and Docker stack jobs were not run; their configuration
is unchanged. Local Python/Node checks corresponding to CI's test/build stages
passed. The five Python skips are the same pre-existing opt-in checks.

Arena retains the documented Phase 1 limits: one fixed scenario, local in-memory
hot-seat sessions, no automatic draw/cap, no LOS, no persistence UI, no special
skills/reinforcements/statuses and no Arena AI. Balance and first-player advantage
remain unmeasured. Before Phase 2 decide corner cutting, Core pressure, LOS and
how downed/revive units would affect occupancy and elimination. Future direct
`ArenaTurnPlan` work remains deferred and can use the existing command boundary.
