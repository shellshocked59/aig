# Arena Phase 3 implementation and verification

Verified locally on 2026-09-13. Phase 3 implements Arena tactical observation,
turn-plan, provider, sequential execution, heuristic, browser orchestration and
headless evaluation facts. No Arena model providers or Phase 4 work were added.

## Files added and changed

This checkout already contained uncommitted Phase 1/2 work. It was preserved;
no reset, commit, GitHub operation or deployment was performed.

| Added | Purpose |
| --- | --- |
| `backend/aig/arena/ai/__init__.py` | Arena AI exports |
| `backend/aig/arena/ai/contracts.py` | Frozen discriminated actions, plan validation and local schema |
| `backend/aig/arena/ai/observation.py` | Immutable canonical facts and detached state reconstruction |
| `backend/aig/arena/ai/executor.py` | Sequential validation, truncation and automatic End Turn |
| `backend/aig/arena/ai/heuristic.py` | Deterministic priorities and exact simulated planning |
| `backend/aig/arena/ai/controller.py` | Provider protocol, explicit controller identities, orchestration and AI traces |
| `backend/aig/arena/ai/metrics.py` | Per-match/player tactical and plan-quality counters |
| `backend/aig/arena/ai/probes.py` | Seven validated tactical fixtures |
| `backend/aig/arena/simulate.py` | Bounded AI-vs-AI CLI with exact replay |
| `tests/test_arena_ai.py` | 45 contract/tactical/controller/metrics tests |
| `tests/test_arena_ai_api.py` | Six actual HTTP/session tests |
| `scripts/arena-ai-verify.py` | Four identical runs, probe traces and local schema export |
| `scripts/arena-ai-smoke.mjs` | Actual HTTP and DOM Human-vs-AI battle |
| `docs/arena-ai.md`, this report | Contract, scoring, operation and verification documentation |

| Changed | Purpose |
| --- | --- |
| `backend/aig/arena/application.py` | Sidecar controller configuration, synchronous AI turns, detached response diagnostics |
| `backend/aig/arena/api.py` | `POST /api/arena/demo-ai` |
| `frontend/src/js/api/arena.js` | AI demo client route |
| `frontend/src/js/arena.js` | AI mode entry, pending status and disabled controls |
| `frontend/tests/arena.test.js` | Five AI browser/client tests; manual tests retained |
| `docs/arena.md`, `README.md` | Current Arena AI architecture and launch commands |

No Arena state, combat, pathfinding, LOS, query, scenario, snapshot or command
replay module was changed. All existing Empire source/test/provider/version
files were preserved.

## Delivered contracts

The architecture is `ArenaState -> ArenaObservation -> ArenaTurnProvider ->
ArenaTurnPlan -> sequential executor -> immutable Arena commands`.

`ArenaObservation` is frozen canonical JSON text with detached `to_dict()` output.
It includes environment/rules/scenario versions, turn/AP/player identities,
own/enemy Core and unit facts (active/downed, HP, positions, class/stats), the
full board, ability costs/ranges, legal options and factual special/bonus rules.
The initial scenario observation is **7,397 UTF-8 bytes**. It contains neither
engine objects nor subjective scores. The heuristic reconstructs a new state
from these facts; no live state reference is supplied to the provider.

`arena-turn-plan-schema-v1` contains `schema_version` and zero to five typed
gameplay actions. Move/Fireball have explicit positions; other actions have
target IDs. Strict decoding rejects missing/extra fields, unknown action types,
invalid IDs/coordinates and total AP over five. A local discriminated JSON Schema
is available; the runtime validator additionally enforces the mixed-cost sum.
There is no reasoning field, actor override or provider-supplied End Turn.

`ArenaTurnProvider.create_turn_plan(observation) -> ArenaTurnPlan` has one call
per AI turn and no previous plan. `arena-heuristic-v1` scores each next action
on detached state, applies it through the actual engine and returns the entire
bounded sequence before real execution. It has no random choices or independent
combat simulator. Stable scores, AP costs and canonical action ordering break ties.

Priorities cover immediate victory, removal of obvious one-hit Core threats,
Finish, Revive, lethal damage, efficient Fireball, positional Bash, distant Snipe,
meaningful Heal, army/Core pressure and BFS movement to useful bonus/support/
attack positions. Class values prefer Cleric/Mage/Ranger/Knight. Fireball scoring
permits small friendly damage and penalizes/rejects nonwinning friendly downs.
See [the complete scoring table and formulas](arena-ai.md#heuristic-baseline).

**Invalid action => record error, truncate suffix, preserve valid prefix,
End Turn if nonterminal.** No rollback, skip, retry or repair occurs. Successful
empty/partial/full-AP plans also End Turn through the command boundary. Victory
stops immediately without End Turn; ignored suffixes record terminal truncation.

`ArenaAiController` returns detached `arena-ai-trace-v1` diagnostics with
observation/provider/plan hashes, attempted/executed actions, AP before/after,
errors/truncation, resulting units/Core HP and winner. These are not snapshots.
Replay uses unchanged `arena-trace-v2` commands and requires no provider.

Explicit human/heuristic controller identity lives in session/run configuration.
The same mirrored scenario supports manual and AI modes with identical initial
game snapshots. Human End Turn runs AI synchronously under the session lock,
then returns to the human or terminal state. The browser displays **AI turn...**
and disables controls while pending. Existing manual mode remains available.

The headless command is:

```sh
python -m aig.arena.simulate --max-turns 100 --output .local/arena-ai-match.json
```

The bound counts completed global rounds (at most 200 player turns for 100).
Exceeding it produces a `turn_limit` simulation result, not a game draw. CLI
output includes raw tactical and plan-quality metrics, not a weighted score.

Metrics cover turns, AP available/spent/unused/average, all eight action counts,
actual dealt/received/healed damage, downs/revives/finishes, Core and friendly-fire
damage, bonus-tile attacks, Bash pushes, Fireball victims, planned/executed/
invalid actions, truncations, zero-action turns, active/downed/removed counts,
HP/Core HP, winner and player turns to victory. Existing Phase 2 counters retain
their original semantics; AI unused AP additionally includes terminal leftovers.

## Automated and integration verification

| Check | Result |
| --- | --- |
| Full Python suite | **991 tests: 986 passed, 5 existing skips** |
| Added Python tests | **51 passed** (45 domain/AI plus six HTTP) |
| Preserved Arena tests | **135 passed**, including 45 frozen v1 tests |
| Frontend suite | **71 passed**, including five new AI tests |
| Production frontend build | Passed |
| Fixed-scenario baseline | Four identical complete AI-vs-AI matches |
| Tactical probes | All seven valid, expected first choices, legal full plans |
| Simulation bound | Explicit nonterminal `turn_limit`, tested at one global round |
| Command replay | Exact for every baseline and HTTP fixture |
| HTTP + DOM | Complete human-pass/heuristic battle; pending/disabled controls, victory, manual reset |
| Preservation | Zero changed/removed among 2,214 pre-existing local artifacts |

The full suite used `.venv/Scripts/python.exe`; frontend used `npm.cmd` to avoid
the local PowerShell script policy. An initial PowerShell stderr redirection
reported a native-command error despite unittest's `OK`; verification was
repeated with Python subprocess capture to check the actual process exit code.
Existing offline provider tests used their mocks; no live model calls were made.

The live HTTP/DOM battle used an isolated loopback API on port 8013. A human who
passes lost to Red at global turn 2 after **16 commands**. The resulting HTTP
trace exactly equaled an independently run headless trace and replayed exactly.
Final state hash:
`d0027890e7d5ce8eecef0e2958fff501121e6c94a8d23c3aa4b90965726a15d4`.
These are DOM/HTTP functional checks, not visual layout review.

## Heuristic baseline results

Each of four independent matches ended with **Red victory by team elimination**,
after **10 player turns**, four completed global rounds and **52 commands**.
There were 43 planned/executed gameplay actions and nine End Turns. All eight
action types appeared. No invalid action, truncated turn, zero-action turn or
simulation turn limit occurred.

| Metric | Blue | Red |
| --- | ---: | ---: |
| Player turns | 5 | 5 |
| AP available / spent / unused | 25 / 25 / 0 | 25 / 23 / 2 |
| Planned and executed actions | 24 | 19 |
| Move / Attack / Heal / Finish | 11 / 8 / 0 / 1 | 1 / 7 / 6 / 1 |
| Revive / Bash / Snipe / Fireball | 0 / 3 / 0 / 1 | 2 / 0 / 1 / 1 |
| Damage dealt / healing | 50 / 0 | 48 / 35 |
| Active / downed / removed | 0 / 3 / 1 | 3 / 0 / 1 |
| Final unit HP / Core HP | 0 / 30 | 33 / 30 |

The match did not stalemate. Blue's early Ranger advance illustrates greedy
overextension; Red's healing/revival mattered. Four identical runs verify
reproducibility, not balance, first-player advantage or broad playing strength.
No randomness or arbitrary tuning was added to force a result.

| Canonical artifact | SHA-256, identical across all four runs |
| --- | --- |
| Plan array | `5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c` |
| Command array | `88328e37527ddb68abf63b091613f7c1282a4581ebe72da394511838b3e6f0ae` |
| Final snapshot | `01720d448acca31206574e16fa3182ffc5c2a40e033e89d5043d56fb21939f2a` |
| Complete command trace | `6b7c60fbb3d8dcd8451e0692bd764135a5c1b31c5abd35dbcc1101042b6f4f5d` |
| AI trace array | `9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1` |

## Tactical probes and preservation

| Probe | Verified first choice |
| --- | --- |
| Finish or Core | Finish nearby downed Mage before nonwinning Core pressure |
| Revive decision | Revive Mage; that Mage can act later in the same plan |
| Fireball friendly fire | Hit two enemies while accepting two WARD-reduced friendly damage |
| Shield Bash position | Push enemy off POWER |
| Snipe versus basic | Snipe distant lethal Mage; basic attack wins comparable close lethal test |
| Winning Core line | Immediately destroy Core using the SIEGE modifier |
| Team elimination | Down last active enemy, taking victory before optional Finish |

**Finish cannot newly cause victory under Phase 2's immediate zero-active rule.**
The valid elimination fixture tests that rule instead of creating an impossible
nonterminal all-downed team. This is the only requested probe that required a
semantic correction; no game rules changed.

Before changes, hashes were captured for 2,359 readable source/artifact files,
including 2,214 pre-existing `.local` files. None of those local artifacts were
changed or removed. The source comparison confirms unchanged Arena combat,
geometry, state, snapshot, scenario and replay modules; frozen v1 code; and
Empire engine/provider/version sources and tests. Root README and frontend test
files were outside that hash inventory; their intended edits are listed above.
Inaccessible pre-existing dependency paths were excluded and not edited.

The full suite retains the pinned Empire snapshot hash
`8859a9dbe564c70105c62e9764ef6d857ea22b674049983857f0256ef3f9bb48`
and trace hash
`b9f5bc4faf4b13b8aa0262170ec3f7c058dc14b33e2f2bc20758ea98adbb2302`.
Arena v2 initial-state and Phase 2 tactical trace regression hashes remain
`fc18d7148a49316f9801e0899c2abd6a5863b450f22999a63c7d704e67ce269d`
and `42585d1fe45943cf0aa127e3f37b312fa297a2974a1fd61a32d88273360c70b7`.
Frozen Arena v1 regression tests also pass. Snapshot/command/rules/trace versions
were not bumped; no AI data was persisted into gameplay state.

Generated evidence is under `.local/arena-phase3-verification/`: four complete
match reports, verification summary, probe observations/plans/traces, local JSON
Schema, actual HTTP trace and comparison, test logs, baseline hashes and
preservation comparison. The two added scripts reproduce the match/probe and
HTTP/DOM evidence. Remote CI, Docker stack and deployment were not run.

Before Phase 4, model schema-error and transport-error policies still need their
own implementation. The tactical interface, five-AP structural bound and
invalid-later-action truncation contract are settled. No model prompt, provider
integration, repair/fallback system or model benchmark was introduced.
