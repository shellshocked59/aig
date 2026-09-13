# Arena Phase 2 implementation and verification

Verified locally on 2026-09-13, Python 3.14.3 and Node 24.14.1. Phase 2 is complete
through deterministic rules, persistence, manual browser controls and headless/
HTTP verification. No Arena AI or Phase 3 contract was implemented.

## Checkout and baseline

Phase 1 was present as uncommitted/untracked workspace work. It was preserved as
the starting point; no reset, commit, GitHub operation or deployment was made.
The actual baseline was **857 Python tests: 852 passed, 5 skipped**, plus
**58 frontend tests passed**. The system Python lacked project dependencies;
verification used the existing `.venv/Scripts/python.exe`. Windows PowerShell's
execution policy required `npm.cmd`, not the `npm.ps1` shim.

Inspection covered Arena state, commands/BFS/combat/Core/bonuses, snapshots,
replay, DTO, session/API, browser, CLI, scenario/version constants, tests and
Phase 1 docs, plus Empire architecture/version conventions, regression hashes
and CI configuration. No shared engine refactor was needed.

## Files changed or added in this phase

Paths below are relative to the repository. This inventory distinguishes this
phase from the pre-existing Phase 1 changes visible in Git status.

| Changed files | Result |
| --- | --- |
| `backend/aig/arena/state.py` | v2 rules identity, explicit UnitStatus and zero-active defeat validation |
| `backend/aig/arena/commands.py` | Five frozen commands, AP costs, pure validator, downing, revive, shove and atomic friendly-fire damage |
| `backend/aig/arena/snapshots.py` | Strict v2 snapshot/command codecs and status persistence |
| `backend/aig/arena/replay.py` | v2 traces, actual per-victim deltas and additional verified counters |
| `backend/aig/arena/public_state.py` | Detached status/ability metadata and authoritative targets |
| `backend/aig/arena/__init__.py`, `__main__.py` | New command exports and CLI inspection including legal actions |
| `frontend/src/js/arena.js`, `api/arena.js` | Explicit class buttons/AP costs, body display, Fireball position selection and v2 requests |
| `frontend/src/css/arena.css` | Downed badge and faded/rotated existing icon |
| `tests/test_arena.py` | Existing baseline assertions updated for v2 behavior/hashes |
| `frontend/tests/arena.test.js` | v2 fixtures and eight new action/UI tests |
| `docs/arena.md`, `docs/architecture.md`, `README.md` | Current mechanics/versioning, architecture note and concise launch text |

| Added files | Result |
| --- | --- |
| `backend/aig/arena/geometry.py` | Integer supercover LOS and terrain-corner step validation |
| `backend/aig/arena/queries.py` | Pure legal-action/ability helpers, independent of browser formatting |
| `backend/aig/arena/v1/{state,commands,scenarios,snapshots,replay,public_state,__init__}.py` | Frozen historical implementation |
| `backend/aig/arena/v1/README.md` | Explicit historical loading policy |
| `tests/test_arena_v1.py` | Original 45 domain tests against frozen v1, original hash assertions retained |
| `tests/test_arena_phase2.py` | 33 broad rule/geometry tests with parameterized cases |
| `tests/test_arena_phase2_api.py` | Five new HTTP, replay and isolation tests |
| `scripts/arena-phase2-smoke.py` | Fixed 28-command tactical fixture, offline replay and optional loopback test server |
| `scripts/arena-phase2-smoke.mjs` | Same sequence through actual DOM controls and HTTP; complete trace comparison |
| `docs/arena-phase2-verification.md` | This report |

The existing Arena API/router/session need no source changes: their explicit
command decoder now accepts the new versioned commands. Their lock/error/
environment boundaries remain intact. Original Arena scenario/assets,
`tests/test_arena_api.py`, `scripts/arena-smoke.mjs` and the Phase 1 verification
report are unchanged.

## Rules and decisions delivered

- `UnitStatus.ACTIVE/DOWNED` encodes as `active/downed`. Lethal damage sets HP to
  zero and leaves the body occupying its tile. Bodies cannot act and are excluded
  from offensive unit targets and splash victims.
- Finish: any active owned unit removes an adjacent enemy body for 1 AP, without
  damage or movement. It checks victory afterward.
- Team defeat: zero active units or destroyed Core immediately ends the battle,
  regardless of bodies. Any remaining active class keeps the team alive.
- Revive: active Cleric, friendly body, range 2 and LOS, 2 AP, exactly 5 HP in
  place. The revived unit may act immediately. Heal remains 1 AP/5 HP/range 2,
  permits active self-heal and excludes bodies/Cores.
- Shield Bash: Knight, adjacent active enemy, 1 AP, 4 damage with modifiers,
  then one tile directly away, including diagonals. A lethal hit does not push.
  Blocked/outside/occupied/Core destinations prevent only the push.
- Snipe: Ranger, active enemy unit, range 4 and LOS, 2 AP, 8 damage. No Core target
  or movement-history prerequisite.
- Fireball: Mage, board impact within range 2 and LOS, 2 AP, radius-1 area,
  4 base damage to all active units including allies/caster. Bodies and Cores are
  immune. All damage is computed before mutation and victory checked once.
- Simultaneous team elimination by Fireball: casting team loses. This resolves
  the otherwise unspecified double knockout using the existing single-winner
  representation. Snapshot validation allows both teams down only with living
  Cores; replay verifies the winner against the caster.
- LOS: integer center-to-center supercover. Intermediate BLOCKED cells obstruct;
  exact corner crossings include both side cells; endpoints are excluded. Units,
  bodies, Cores and bonuses do not obstruct. All specified ranged actions share
  this helper. Knight adjacency actions and Finish do not need LOS.
- Diagonal Move steps require both adjoining orthogonal terrain cells open.
  Occupied neighboring side cells do not themselves block the corner. BFS and
  Move use the same step rule; legal detours still count against move range.
- POWER adds 2 to all offensive damage; WARD subtracts 2 per unit victim, minimum
  1; SIEGE adds 4 only to basic Core attacks. Other actions ignore bonuses.
- Move/Attack/Heal/Finish/Bash cost 1 AP; Snipe/Fireball/Revive cost 2; explicit
  End Turn costs zero. Rejections are atomic and do not consume AP or append trace.

The request's proposed test that Finish newly triggers elimination conflicts
with immediate zero-active defeat: removing a body cannot reduce the active
count. Finish calls the check, but valid battles end when the final active unit
is downed. This consequence is documented rather than introducing stalled states.

## Versioning, queries and browser

The default engine/API/CLI use `arena-rules-v2`, `arena-snapshot-v2`,
`arena-command-v2`, and `arena-trace-v2`. The mirrored layout stays
`arena-scenario-v1`. The explicit `aig.arena.v1` package preserves the original
contracts and behavior, including immediate removal, corner cutting and no LOS.
No implicit migration is performed; cross-version loaders reject data.

Seven frozen source modules and the original test file were checked against the
pre-edit hashes after reversing only import namespaces and normalizing newline
encoding. All matched. Historical v1 hashes also reproduce exactly below.

V2 snapshots persist status, HP including zero, positions/identities, board,
Core state, AP, player order, turn and winner. Derived stats, abilities, LOS and
legal actions remain outside persistence. Serialization is canonical and replay
checks every command/state hash and trace counter, including simultaneous damage.
Empire snapshot v12 and all Empire version/experiment registries are unchanged.

Pure queries include LOS, legal moves/attacks/Finish/Revive/Fireball targets,
Fireball victims, AP cost, active-team checks, class ability metadata and complete
legal-action maps. Query legality and execution share `validate_command`.

The DTO adds status and `{ap_cost, range}` ability metadata. Class-specific
left-click buttons show costs and use server targets. Bodies have accessible
DOWNED text, a badge and a faded/rotated original icon. Fireball uses highlighted
impact tiles with friendly-fire guidance; hover splash preview is not included.
The browser does not compute legality. No Empire UI redesign or new art.

Trace counters cover AP by action, actual damage/healing, downings, revivals,
finishes, friendly-fire/Core damage, attacks from bonus tiles, pushes and
Fireball victims. Damage/downings include friendly damage; healing includes
Revive HP; separate counters allow analysis. No arbitrary quality score or
benchmark harness was added.

## Automated and integration results

| Check | Result |
| --- | --- |
| Baseline Python | 857 tests; 852 passed, 5 existing skips |
| Final full Python | **940 tests; 935 passed, 5 existing skips**, 76.194 seconds |
| Arena Python subset | **135 passed**: 45 frozen v1 and 90 current v2/domain/API |
| Frontend | **66 passed**: 42 existing Empire/shared tests and 24 Arena tests |
| Production frontend build | Passed |
| Scripted tactical match | **28 commands**, Blue Core victory, turn 3, 2 AP remaining |
| Offline replay | Exact full state, trace and metrics |
| Live HTTP + DOM tactical flow | All 28 commands, every action type, full trace equals headless trace |
| CLI resume from initial snapshot plus commands | Exact expected final snapshot |
| CLI replay of actual HTTP trace | Exact expected final snapshot |
| Original mirrored demo HTTP + DOM smoke | **14 commands**, passed under v2 |
| Frozen v1 original 14-command sequence | Exact historical terminal hash and replay |
| Whitespace / source review | Passed |

Rule coverage includes all requested class/status/AP restrictions, invalid
command atomicity, body occupancy, revive-and-act, straight/diagonal and failed
pushes, modifier combinations across all attacks, atomic multi-downing and own-
team Fireball defeat, LOS for every ranged action, nonblocking entities/bonuses,
strict snapshots, terminal rejection, command round trips, trace tampering and
cross-environment requests. LOS symmetry is checked for all 2,025 endpoint pairs
on the demo board. Legal-action queries are checked against actual execution
for every candidate board/entity target across all four classes in a fixture.

The fixed tactical match includes a POWER Bash push onto WARD, a POWER Snipe
that downs a Mage, Red revival, basic attacks and healing, a four-victim Fireball
that downs its own caster, Blue revival and immediate attack, Finish removal,
SIEGE Core pressure and victory. It records three downing events, two revivals,
one Finish, one push, three actual friendly-fire damage and 30 Core damage.
These are sanity fixtures, not competitive balance measurements.

## Reproducibility hashes

| Artifact | SHA-256 |
| --- | --- |
| V2 initial demo state | `fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d` |
| V2 End Turn (Blue) command | `fdd1266518b21c3d3940e49b473d53b983462840e9b10d6825a925656052b886` |
| V2 tactical final state, headless and HTTP | `dfa08c98197375a6231ef3a8013aaf84afdfdfc47913b669c12974fe4fdf64ec` |
| V2 complete tactical trace | `42585d1fe45943cf0aa127e3f37b312fa297a2974a1fd61a32d88273360c70b7` |
| V2 original demo HTTP flow final state | `4fd2d1bd43063b59212c75052d06f26a92b6bdee28309c85e814121effe3e585` |
| Frozen V1 initial demo state | `879d9e26f1116cb9628d2889f09526c2ccf7f947bd5c0c2a1727df991cd7c800` |
| Frozen V1 End Turn (Blue) command | `ec36997239f1c123371122f3efdd7fd4d5a413a9d953b5cba3d6c4714cbacee1` |
| Frozen V1 original HTTP sequence final state | `ddfef0720614c5170d9c586572fa75295a79897c6b27e4efa41a14ea47664a14` |
| Preserved Empire snapshot regression | `8859a9dbe564c70105c62e9764ef6d857ea22b674049983857f0256ef3f9bb48` |
| Preserved Empire trace regression | `b9f5bc4faf4b13b8aa0262170ec3f7c058dc14b33e2f2bc20758ea98adbb2302` |

The current v2 initial/command hashes and tactical final/trace hashes are pinned
in tests. The original v1 tests retain their original hashes. The full suite ran
the existing Empire/provider/frozen-profile tests unchanged, including its
100-turn-budget heuristic regression (conquest at turn 75, 225 activations).
All provider tests used their existing offline mocks; no model calls were made.

## Preservation and boundaries

Before editing, SHA-256 hashes were captured for **2,341 readable existing
source/artifact files**. Comparison found **zero changes or removals among 2,204
pre-existing `.local` artifacts**, including experiment outputs/archives. Three
pre-existing dependency directories under `.local/docker-validation` remained
unreadable and excluded; they were not edited. The accessible source/test
comparison also confirms no Phase 2 changes to Empire engine, API, provider,
benchmark, regression or browser behavior files. All baseline file changes are
Arena code/tests/UI and the Arena/architecture documentation (plus a narrow
README update). Phase 1's verification report and original assets remain intact.

Generated evidence lives in `.local/arena-phase2-verification/`: initial snapshot,
commands, final snapshot, trace, actual HTTP trace, match report, CLI resume/replay
outputs, baseline hashes and preservation comparison. The supplied scripts
regenerate the match artifacts without any model or benchmark dependency.

The browser inventory returned no app/browser surfaces, so native visual layout
review was unavailable. jsdom + actual HTTP and production build checks passed;
they do not prove visual layout quality. Remote GitHub CI/deployment and Docker
stack jobs were not run. Local Python/Node checks corresponding to CI test/build
stages passed; CI configuration and dependencies were unchanged. Five Python
skips and mocked HTTP ResourceWarnings are pre-existing.

No fundamental state/AP/replay invariant failure or obvious special-ability
invariant break was found. Competitive balance, first-player advantage and
repeated-special strength remain unevaluated. Finite AP does not prevent players
passing forever; external match caps belong in a later benchmark contract.

Before Phase 3, define observations, bounded AP turn sequences, and policy for
invalid later actions (truncate, deterministic repair or replan). The simultaneous
Fireball tie policy is now explicit and covered by tests; changing it later is a
rules-version decision. No Phase 3 implementation was started.
