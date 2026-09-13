# Arena: Phase 2 rules and Phase 4 tactical AI

Arena is Agent Strategy's small, perfect-information tactical environment beside
Empire. The default rules are `arena-rules-v2`. Players manually issue immutable
commands against an authoritative deterministic Python engine. Phase 3 adds an
immutable observation/turn-plan contract and deterministic heuristic opponent;
Phase 4 adds direct Ollama/Qwen and OpenAI/Luna tactical providers.
See [Arena AI architecture](arena-ai.md).
Empire's state, rules, providers, snapshots and experiment registry are separate.

## Board and shared AP

The board is 9 columns by 5 rows, with origin `(0, 0)` at the top left. Every tile,
unit and Core is visible. Two teams have one of each class and a 30-HP Core.

| Class | Max HP | Basic damage | Attack range | Move range |
| --- | ---: | ---: | ---: | ---: |
| Knight | 18 | 6 | 1 | 2 |
| Ranger | 10 | 5 | 3 | 3 |
| Mage | 9 | 6 | 2 | 2 |
| Cleric | 11 | 3 | 2 | 2 |

All action ranges use Chebyshev distance: `max(abs(dx), abs(dy))`. Movement range
counts traversable steps. Each team turn has **5 shared AP**. Units may act
repeatedly and revived units may act immediately if enough AP remains.

| Action | Class | AP | Target / range | Effect |
| --- | --- | ---: | --- | --- |
| Move | Any active unit | 1 | Free tile, within class move range | Follow a legal path |
| Attack | Any active unit | 1 | Active enemy unit or enemy Core, class range | Class damage |
| Heal | Active Cleric | 1 | Active friendly unit, range 2 | Restore 5 HP, capped at max |
| Finish | Any active unit | 1 | Downed enemy, adjacent (distance 1) | Remove body |
| Shield Bash | Active Knight | 1 | Active enemy unit, adjacent | 4 damage, then attempt shove |
| Snipe | Active Ranger | 2 | Active enemy unit, range 4 | 8 damage |
| Fireball | Active Mage | 2 | Board position, range 2 | 4 damage in radius 1, friendly fire |
| Revive | Active Cleric | 2 | Downed friendly unit, range 2 | Active again at 5 HP |
| End Turn | Active player | 0 | None | Switch player, restore 5 AP |

Invalid commands consume **zero AP** and mutate nothing, including trace entries.
AP never goes negative. Zero AP does not end the turn automatically. End Turn is
explicit and increments the global turn only on the Red-to-Blue wrap. No RNG,
accuracy rolls, critical hits, retaliation, cooldowns or per-unit action history.

## Downed units, revival and victory

`ArenaUnit.status` is explicitly `UnitStatus.ACTIVE` or `UnitStatus.DOWNED`, encoded
as `"active"` or `"downed"`. Active units require positive HP. Lethal unit damage
sets HP to 0 and status to DOWNED, leaving identity, ownership and position intact.
A body occupies its tile, blocks movement/transit, and persists across turns.
Downed units cannot act. Basic attacks, Bash and Snipe cannot target bodies;
Fireball ignores them, even when the impact tile contains one.

Finish removes an adjacent enemy body without damage, movement or retaliation.
It is the only explicit removal action; it needs no LOS and cannot be ranged.
A Cleric may Revive a friendly body within range 2 and LOS for 2 AP, restoring
exactly 5 HP in place. Heal cannot revive. Heal works only on active friendlies,
including the Cleric itself; full-HP targets are invalid. Neither action targets
a Core. Downed Clerics cannot act or revive themselves.

A team loses immediately when its Core reaches 0 HP **or it has zero ACTIVE
units**, regardless of remaining bodies. One active unit of any class prevents
unit elimination; four bodies with no active ally are an immediate loss.
The final action spends its AP, sets `winner_player_id`, clears
`active_player_id`, and does not advance the turn. All further commands,
including End Turn, are rejected.

Fireball may defeat its own team. If it downs both teams' last active units in
one atomic action, **the casting team loses**. The opposing player is recorded
as winner even if its units are also downed. Both Cores remain alive in this
simultaneous-elimination case. The persisted winner records the result; replay
recomputes it from the casting actor. There is no draw state or automatic cap.

Finish always runs the victory check. It cannot newly cause elimination in a
valid nonterminal state: removing a downed body does not reduce the active-unit
count, and zero-active states have already ended. This follows the requested
immediate zero-active rule rather than delaying defeat until bodies are removed.

## Specials and board bonuses

Shield Bash applies damage on the target's **original** tile. If the target is
downed, it remains there. Otherwise the push destination is
`target + (target - knight)`, including diagonal adjacency. Push succeeds only
when the destination is in bounds, floor, unoccupied by any unit/body, and not a
Core tile. A failed push still deals damage. The Knight stays in place. No chain
push or Core target. Shove checks the destination; the terrain corner rule below
applies to Move steps, not displacement.

Snipe requires LOS, costs 2 AP, and has no prerequisite about earlier movement.
It cannot target a Core.

Fireball targets a **position**, which can be empty, occupied by a friendly,
active enemy or body, or contain blocked terrain/a Core. Its radius-1 square is
the impact tile plus eight neighbors, clipped to the board. It damages every
ACTIVE combat unit in that area, **including allies and the caster**, but never
bodies or Cores. LOS is checked only from the Mage to impact, not separately to
victims. All victims and their damage are calculated from pre-action state;
damage is then applied to everyone before a single victory check. Caster death
cannot interrupt the blast or change its POWER modifier.

| Tile | Exact v2 interaction |
| --- | --- |
| POWER | +2 damage to Attack, Bash, Snipe and every Fireball victim |
| WARD | -2 incoming unit damage from those actions; minimum damage 1 per victim |
| SIEGE | +4 damage only to basic Attack against an enemy Core |

For basic Core attacks: class damage + POWER if standing on POWER + SIEGE if
standing on SIEGE. A tile has at most one bonus, so those bonuses never stack in
the current board model. WARD does not mitigate Core damage. Heal, Revive and
Finish ignore bonuses. Special abilities cannot damage Cores. HP loss is clamped
at zero; metrics count actual loss, not overkill.

## Movement and line of sight

Arena owns eight-direction BFS with tie order N, NE, E, SE, S, SW, W, NW. Every
step costs one movement distance; the complete move costs one AP. Units, bodies,
Cores and blocked terrain prevent entry and transit. A diagonal Move step is
illegal if **either** adjoining orthogonal terrain cell is BLOCKED. Adjacent
entities do not block the corner itself beyond normal occupancy. A destination
may still be reachable by a longer legal path within the unit's range. The same
`can_step` helper controls BFS and authoritative Move validation.

`arena_line_of_sight(board, start, end)` uses integer center-to-center supercover
traversal. Every intersected intermediate terrain cell is checked. At an exact
grid-corner crossing both touched orthogonal side cells are checked, so either
wall blocks the ray. Integer cross products avoid rounding and provide symmetric
results in every direction. Endpoints themselves do not obstruct the ray;
out-of-bounds endpoints are rejected. Thus a Fireball may impact a blocked tile.
Units, bodies, Cores and bonus tiles never obstruct LOS.

LOS applies to Ranger/Mage/Cleric basic attacks (including against Cores), Heal,
Revive, Snipe and Fireball impact. Knight Attack, Bash and all adjacent Finish
actions require adjacency without a LOS check. No cover system or height model.

## Scenario and versions

The original mirrored deployment and board remain `arena-scenario-v1`:

```text
     0 1 2 3 4 5 6 7 8
  0  . R . . P . . R .
  1  . K . # . # . K .
  2  C . W S . S W . C
  3  . M . # . # . M .
  4  . H . . P . . H .
```

`K/R/M/H`: Knight/Ranger/Mage/Cleric; `C`: Core; `P/W/S`: POWER/WARD/SIEGE;
`#`: BLOCKED. Blue moves first. Arbitrary validated tactical fixtures may supply
other board contents/rosters; snapshots store their full board.

| Contract | Default | Explicit historical package |
| --- | --- | --- |
| Rules | arena-rules-v2 | arena-rules-v1 |
| Snapshot | arena-snapshot-v2 | arena-snapshot-v1 |
| Command | arena-command-v2 | arena-command-v1 |
| Trace | arena-trace-v2 | arena-trace-v1 |
| Scenario layout | arena-scenario-v1 | arena-scenario-v1 |

`aig.arena.v1` preserves the Phase 1 implementation and original hash tests.
Use its `from_snapshot`, `replay`, commands and simulation explicitly for old
artifacts. The default v2 loader and API reject v1 contracts, and vice versa;
there is no automatic migration or silent reinterpretation. Empire snapshot v12
and its `environment-vN` experiment versions are untouched.

Snapshots persist full board, identities, positions, status, HP, Core HP, player
order, AP, turn and winner. They never persist class/ability stats, LOS or legal
actions. Strict loading rejects extra/missing fields, duplicate IDs, inconsistent
HP/status, unsupported versions and invalid state, without lifecycle effects.
Canonical JSON uses sorted keys, compact separators and ASCII escaping; SHA-256
hashes UTF-8 bytes. Entity arrays sort by ID; board/player order is semantic.
Traces include the initial snapshot and versioned commands with command hashes,
before/after state hashes and action counters. Replay verifies every field.

## Queries, API and browser

`queries.py` exposes pure `legal_actions`, `abilities`, `arena_legal_moves`,
`arena_attackable_targets`, `arena_finishable_targets`, `arena_revivable_targets`
and `arena_fireball_targets`. Domain results use Positions/IDs, not browser
formatting. Geometry, action-cost, active-team and Fireball-victim helpers are
also available through that module. Legal queries use the same pure
`validate_command` as execution, including AP, ownership, class, range and LOS.

The detached public DTO includes `status`, HP/max HP, AP, class stats,
`abilities: {action: {ap_cost, range}}` and authoritative `actions` lists. Enemy,
downed, terminal and AP-ineligible units have no legal actions. Class abilities
remain described when unavailable so the UI can explain them.

| Route | Purpose |
| --- | --- |
| GET /api/environments | Empire/Arena selection |
| GET /api/arena | Current public DTO |
| POST /api/arena/demo | Reset only Arena to the mirrored scenario |
| POST /api/arena/demo-ai | Same board, Human Blue vs Heuristic Red |
| POST /api/arena/commands | Apply a strict v2 command |
| GET /api/arena/trace | Detached v2 replay trace |

The existing locked Arena session and router remain separate from Empire. New
command types are `arena_finish`, `arena_revive`, `arena_shield_bash`,
`arena_snipe`, `arena_fireball`. Example:

```json
{"schema_version":"arena-command-v2","type":"arena_fireball","actor_id":"blue","unit_id":"blue-mage","target_position":{"x":4,"y":3}}
```

Move uses `destination`; other unit actions use `target_id`. End Turn includes
only schema/type/actor. Invalid payloads/actions return 4xx with unchanged state
and trace. No API snapshot injection endpoint was added.

The browser retains original Arena fantasy icons and uses explicit left-click
buttons per class, AP cost labels, server-highlighted targets and a DOWNED badge
with a faded/rotated icon. Fireball selects a highlighted impact tile and displays
friendly-fire/radius guidance; it has no hover splash preview. No browser game
legality, right-click requirement, new art or Empire UI redesign was added.

## Metrics and headless verification

State metrics include active (`living_units`) and downed counts, HP, Core HP,
turns, remaining AP and winner. Per-actor trace metrics include AP used/discarded,
AP spent by action type, basic attacks, actual damage/healing, units downed,
revived and finished, friendly-fire damage, Core damage, bonus-tile attacks,
Bash pushes and Fireball targets hit. `damage_dealt` includes friendly damage;
`units_downed` includes friendly downings; `healing_done` includes restored Revive
HP. The separate friendly-fire counter disambiguates total damage. A bonus-tile
attack means any offensive action started on any bonus tile, including WARD,
whether or not that tile enhanced it. Fireball hits count pre-action active
victims. Terminal unspent AP is not counted as discarded. No quality score.

```sh
python -m aig.arena
python -m aig.arena --commands commands.json
python -m aig.arena --snapshot initial.json --commands commands.json
python -m aig.arena --replay trace.json
python scripts/arena-phase2-smoke.py
```

The CLI prints `snapshot`, `inspection` (public state including legal actions),
`metrics` and `trace`. Save the appropriate member as an input file. The smoke
script writes a custom tactical fixture, its fixed 28 commands, final snapshot,
trace and match report to `.local/arena-phase2-verification/`. It verifies exact
offline replay through a Core victory with every action type. It never selects
actions or runs AI. Resume/replay the resulting files with the CLI above.

For a real HTTP plus browser-controller integration, in separate terminals:

```sh
python scripts/arena-phase2-smoke.py --serve 8012
node scripts/arena-phase2-smoke.mjs http://127.0.0.1:8012
```

The first command seeds an isolated loopback API in-process with the fixture;
it does not add a production route. The second clicks DOM controls against it
and checks the full HTTP trace against the headless trace. Restart the fixture
server before repeating. Existing `scripts/arena-smoke.mjs` still exercises the
mirrored demo. Both use jsdom and do not substitute for visual layout review.

See [Phase 2 verification](arena-phase2-verification.md) for exact counts/hashes
and [frozen Phase 1 verification](arena-phase1-verification.md) for history.

## Phase 3 AI boundary

Balance and first-player advantage remain unmeasured; specified values are the
baseline. Repeated special use is intentional under shared AP. Passing forever
is still possible; a future benchmark needs an explicit external turn cap.
Sessions remain in-memory, with manual and Human vs Heuristic/Qwen/OpenAI modes and no
persistence UI or multiplayer. Headless AI runs have an external round bound.

Phase 3 uses `ArenaObservation -> ArenaTurnProvider -> ArenaTurnPlan -> executor`
with one provider call per turn, bounded by five AP. Commands validate sequentially:
an invalid action truncates the remaining plan, retains earlier actions, and
automatically End Turns if nonterminal. Successful plans also End Turn; terminal
plans stop immediately. No execution-time repair/replan occurs. Runtime plans/controllers/traces
remain outside snapshots. Command replay is independent of the provider.

The deterministic heuristic simulates its complete plan on detached state using
the actual rules. `python -m aig.arena.simulate` runs Heuristic vs Heuristic;
`python scripts/arena-ai-verify.py` checks four matches and tactical probes.
See [AI contracts, priorities and metrics](arena-ai.md) and
[Phase 3 verification](arena-phase3-verification.md). Phase 4 adds the two model
providers, one static-output repair, and explicit normal-game heuristic fallback.
No model benchmark, combat mechanic, map or class was added.
`AIG_ARENA_TURN_PROVIDER=heuristic|ollama|openai` independently selects Arena
Configured AI; explicit browser buttons select Qwen or OpenAI (Luna).
See [Phase 4 verification](arena-phase4-verification.md) and the opt-in smoke commands
in [Arena AI](arena-ai.md#manual-smoke-commands).
