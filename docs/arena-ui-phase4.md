# Arena UI Phase 4: class visual identity

Phase 4 replaces the small class glyphs with original repository-owned SVG
miniatures. The art direction is a compact carved board piece: dark ink edges,
ivory faces/material highlights, restrained metal and gold, and team-colored
cloth. These are first-pass tactical silhouettes, not final character portraits.
No downloaded assets, generated bitmaps, icon packs, sound or idle loops are used.

## Artwork and composition

| Piece | Dominant silhouette | Ability language |
| --- | --- | --- |
| Knight | Wide armor, closed helmet, large kite shield and upright sword | Short lunge, angular shield impact; Bash has a thicker shield flash and authoritative push |
| Ranger | Light hooded asymmetrical figure with an oversized bow and arrow | Thin directional arrow; Snipe adds aim crosshairs, longer windup and brighter precision line |
| Mage | Pointed hat, triangular robe, conspicuous violet orb staff | Rounded arcane bolt and double-ring impact; Fireball changes to fire color and pulses the exact affected cells |
| Cleric | Sturdy ivory figure, halo, open book and sun staff | Modest gold dotted radiant strike; Heal is green restoration, Revive is a double gold ring with rising light and upright transition |
| Core | Faceted energy crystal held by a two-sided stone shrine | Existing HP, destruction flash, fade and victory sequencing |

`frontend/src/js/arena-unit-visuals.js` owns the `unitVisualRegistry`, the SVG
wrapper `unitVisual(kind)`, and the shared `renderArenaPiece(piece, blueId)`.
The board and lab gallery use that exact piece renderer. The selected panel
uses the same SVG at 92 px; board figures are 64 px inside the existing 126 px
high tiles. Unknown class input resolves to a neutral figure safely.
`arena-icons.js` delegates class/Core requests to this registry and retains
only the original terrain/bonus marks locally.

Each piece layers a team base, artwork, optional class label, ownership, HP and
status. Blue uses a rounded base and circle marker; Red uses an angular base
and diamond marker. Both also retain BLUE/RED text and colored tile borders.
Only the artwork desaturates and slumps when downed. Its class silhouette,
colored base and owner marker remain; dashed tile borders and DOWNED text
reinforce status. Finish still removes the unit after the existing fade.

Selection keeps the white tile outline and adds a white base outline. Class
names appear on hover, keyboard focus or selection; accessible tile names and
titles always identify class, team, position and HP. Normal Arena hides visible
coordinates by default. Development info contains a persistent-per-mount Show
coordinates toggle. Lab boards show coordinates for inspection.

## Actions and effects

`arena-action-icons.js` supplies original line icons for Move, Attack, Heal,
Finish, Revive, Shield Bash, Snipe and Fireball. Action buttons retain text,
authoritative AP costs, disabled legality and focus behavior. AP is displayed
on its own small line. Decorative SVGs are hidden from assistive technology.

`arena-animation.js` registers all four class attacks plus Snipe, Shield Bash,
Fireball, Heal and Revive. These are small wrappers around the existing combat
sequence, not separate engines. They reuse cue, pulse, tracer, lunge, flash,
area, HP, float, status and push primitives. Semantic motifs now also reach the
resolved impact flash, so a generic damage circle does not obscure a shield
impact. The original timings, event ordering, checkpoint semantics and final
state reconciliation remain in place.

Phase 4 CSS stays in `frontend/src/css/arena.css`, scoped to Arena. Shared
materials use `--arena-ink`, `--arena-paper`, `--arena-steel`,
`--arena-leather` and `--arena-gold`. Team colors use `--arena-team-blue` and
`--arena-team-red`. Effects use physical, precision, arcane, heal, revive, fire,
danger and neutral tokens. Motif selectors set `--effect-color`; no gameplay
data chooses an arbitrary effect color.

Reduced motion replaces traveling effects with source/target flashes, omits
the lunge and status rotation, and retains numbers, target feedback and exact
Fireball area. Static downed poses remain. Instant mode skips transient
animation while applying resolved effects. No continuous animation was added.

## Workbench and replacement workflow

The collapsible class gallery shows 16 variants: four classes, both teams,
active-selected and downed. It uses actual piece markup and real styles, with
accessible variant labels. The gallery uses specimen HP values, not balance
claims. The lab retains all prior generic examples and adds Knight Attack,
Ranger Attack, Mage Attack and Cleric Attack. Every ability trigger resets an
authoritative fixture and goes through the live controller/registry/driver.
Speed (0.5x, 1x, 2x) and Instant apply on the next replay; Reset cancels playback.

The only Python edit for Phase 4 is the development fixture generator
`scripts/arena-presentation-fixtures.py`, adding four basic-attack examples
executed by unchanged authoritative commands. It regenerates
`frontend/src/js/arena-lab-fixtures.json`; it does not modify runtime rules.

To replace Ranger artwork, edit the `ranger` entry in `unitVisualRegistry`.
Keep the 64-by-64 viewBox, use shared material/team variables and leave HP,
status and ownership outside the SVG. The board, gallery and selected panel
update together. No Blue/Red duplicate files are necessary.

To replace the Ranger projectile shape, edit `.arena-tracer.arena-precision`
and its arrowhead pseudo-element. Snipe intentionally shares that motif with
its own `.arena-snipe` modifier. To change only basic attack sequencing, replace
`rangerAttack`, or register an override:

```js
const registry = createArenaRegistry()
  .register('attack', newRangerAttack, 'ranger');
mountArena(root, api, { registry });
```

To replace Revive styling, edit `.arena-revive` motif rules. To replace its
sequence, change `revivePresentation` or register
`registry.register('revive', newRevivePresentation)`. Keep the abort signal,
driver-owned transient nodes and `presentEffects` checkpoints. Never calculate
healing or revive legality in the visual handler. See the
[engine guide](arena-presentation-engine.md) for the primitive lifecycle.

## Verification and evidence

Phase 4 file inventory (separate from pre-existing Phase 3 changes):

- Added `frontend/src/js/arena-unit-visuals.js`,
  `frontend/src/js/arena-action-icons.js`,
  `frontend/tests/arena-visuals.test.js`,
  `scripts/arena-visual-identity-smoke.mjs`, and this document.
- Updated `frontend/src/js/arena.js`, `arena-icons.js`, `arena-animation.js`,
  `arena-presentation-lab.js`, `arena-lab-fixtures.json`, and
  `frontend/src/css/arena.css`.
- Updated `frontend/tests/arena.test.js`, `arena-animation.test.js` and
  `arena-presentation.test.js` to scope board assertions separately from the
  gallery and exercise class-specific override precedence.
- Updated `scripts/arena-presentation-fixtures.py`,
  `scripts/arena-presentation-lab-smoke.mjs`, and
  `docs/arena-presentation-engine.md`.

Production build: **passed** (`npm.cmd run build`).

Python preservation/regression verification: **1,199 passed across the full run
and targeted rerun; five platform skips**. The full `unittest discover -s tests
-v` run executed 1,204 tests in 437.498 seconds: 1,197 passed, five skipped and
two failed. Those two tests freeze the auxiliary frontend/scripts source tree
and overlapped final UI edits. With source edits stopped, both passed unchanged
on an isolated rerun in 5.688 seconds:

```powershell
.venv\Scripts\python.exe -m unittest tests.test_arena_action_id.ActionIdTests.test_benchmark_and_replay_tampering tests.test_arena_fullmatch.FullMatchTests.test_independent_failures_continue_all_eight_no_retries -v
```

The initial output is preserved in `python-tests.log`; the successful rerun is
in `python-guard-rerun.log`. No test, source guard, gameplay code or research
contract was weakened to obtain the rerun result.

Frontend: **171 passed**. Coverage includes five piece assets, both teams,
selection, downed identity, unknown fallback, all eight action icons,
authoritative AP/disabled behavior, coordinate toggling, all nine specialized
handlers under reduced motion and the shared-renderer gallery. Existing
selection, action, Core damage/destruction, cancellation and reconciliation
tests also pass.

Real Chrome/Chromium review uses the local app, not mock screenshots:

- `scripts/arena-presentation-lab-smoke.mjs`: all 16 fixtures, temporal HP and
  multi-victim feedback, cancellation, reduced motion, instant and no stale
  transforms or transient nodes.
- `scripts/arena-visual-identity-smoke.mjs`: gallery, selected class examples,
  nine specialized effects, reduced-motion replay and tile-fit measurements at
  900, 1280, 1440 and 1920 px viewport widths. No document overflow.
- `scripts/arena-presentation-smoke.mjs`: real manual actions and Human vs
  Heuristic offline play, including an AI attack/Heal/Revive sequence, Core
  victory, action locking and 900 px layout. No browser errors.

Screenshots and machine-readable results are under `.local/arena-ui-phase4/`:

- `arena-desktop.png`, `arena-heuristic.png`, `arena-winner.png`
- `class-design-sheet.png`, `selected-{knight,ranger,mage,cleric}.png`
- `downed-mage.png`, `arena-downed.png`
- `effect-{knight-attack,shield-bash,ranger-attack,snipe,mage-attack,fireball,cleric-attack,heal,revive}.png`
- `arena-ai-{attack,heal,revive}.png`, `lab-{900,1280,1440,1920}.png`
- `presentation-temporal-review.json`, `visual-identity-review.json`,
  `browser-smoke.json`, `heuristic-turn-frames.json`
- `frontend-tests.log`, `python-tests.log`, `build.log`

Visual inspection found the four active silhouettes distinguishable without
permanent class labels. Team ownership and downed class identity remain visible.
This is an implementation review, not a first-time-player usability study.
The board remains compact, HP is readable, bonus marks remain visible, and the
Core reads as a structure rather than a humanoid piece.

## Scope and limitations

Gameplay, heuristic decisions, replay contracts, Empire, AI research contracts
and historical evidence were not changed by this phase. Pre-existing Phase 3
working-tree changes were retained. No live provider requests or benchmark runs
were made. Regression tests use their existing isolated fake-provider fixtures.

The pieces are deliberately simple flat vectors with a fixed stance; they do
not turn toward targets or animate individual limbs. Projectiles use stylized
traces with shaped heads rather than a particle system. Downed art is a rotated
class silhouette rather than a separate prone drawing. Board terrain is still
the prior simple treatment. Very small/mobile layouts remain outside scope;
the existing horizontally scrollable board remains available. Speed changes
apply on replay, not halfway through an effect.

The recommended next gameplay task is a separate heuristic evaluation of
advancement and contesting board bonuses versus turtling. No heuristic or sound
work is started here.

## Launch

```powershell
cd C:\code\aig
npm.cmd run dev
```

Arena: http://127.0.0.1:5173/arena

Choose **Human vs Heuristic - Offline** for the offline opponent.

Lab: http://127.0.0.1:5173/arena/presentation-lab

An existing development server was already running on port 5173 during this
task and was reused; it was not stopped or replaced.
