# Arena UI Phase 3: first default animation set

Phase 3 implements actual movement and combat feedback on the existing Phase 2
presentation architecture. It does not change Arena rules, heuristic behavior,
backend timing, AI research or Empire, and does not start the final-art phase.

## What Phase 2 had, and what was missing

Phase 2 had the authoritative event projection, visual reducer, sequential queue,
registry, driver boundary, log synchronization, cancellation generations,
reduced-motion/instant options and fixture lab. The earlier report overstated
its visual completeness. Inspection found basic prototype effects, but HP waited
until all feedback ended, paths recreated a ghost for each segment, HP meters
snapped on rerender, all actions used the generic fallback, and turn/Core
termination had no distinct visual effect. The original browser checks mostly
proved element presence and final state rather than actual motion.

Phase 3 keeps the architecture. The one necessary extension is an optional,
generation-guarded semantic checkpoint: HP can commit at impact without replacing
the board DOM while its animations are active. Final event reduction remains
idempotent and the authoritative final DTO remains the source of truth.

## Implemented behavior

| Event | Visible sequence |
| --- | --- |
| Move | One highlighted, lifted ghost follows the full authoritative path; the source stays hidden; destination commits at completion. Works for all four classes. |
| Basic Attack | Actor ring/action label and windup, directional tracer, target ring, impact/shake, negative amount and HP tween. Knight adds a small directional lunge. |
| Damage | Reusable hit/number/bar feedback shared by Attack, Snipe, Bash, Fireball and Core hits. Numeric/accessible HP and the selected panel update at impact. |
| Downed | Damage, DOWNED label, desaturation/slump, then persistent downed body/badge. |
| Heal | Source cue, green connection, target restorative pulse, +N and rising HP. |
| Revive | Registered override: advance glow and double halo, source beam, +N, REVIVE, then body stands up into active styling. |
| Finish | Decisive flash, FINISHED, shrink/fade, then permanent board removal. |
| Snipe | Registered override with longer aim and wider, brighter straight tracer; shared damage primitives. |
| Shield Bash | Impact and damage complete before one-tile ghost push. No push is invented when the event has none. |
| Fireball | Mage cue/travel, impact flash, measured 3×3 cell pulses and all affected victims' numbers/HP together, including friendlies. |
| Core damage | Hit flash/shake, damage number and HP tween. Zero HP then gets CORE DESTROYED, flash/fade and final cracked/dim treatment. |
| Turn | Brief BLUE TURN / RED TURN banner; AI acting status remains visible during its queue. |
| Victory | Separate delayed victory event after lethal feedback; winner and terminal cause remain visible. |

Source and target cues persist through impact/status feedback, so the log is
supplemental. Log lines still append at event start, with stronger latest-line
highlight. All action/selection commands remain locked during playback; New
Match and Refresh can interrupt it.

## Driver, timing and lab

`ArenaAnimationDriver` owns cues, pulses, movement, tracer/lunge, hit/flash, HP
animation, floating text, status transition, fade, Fireball cells, destruction,
turn banner and abortable clocks. `presentEffects` is the shared victim helper.
`createArenaRegistry` installs `snipePresentation` and `revivePresentation` with
resolution action/class → action → generic. See the
[engine guide](arena-presentation-engine.md) for an override example.

Cell geometry is measured from the rendered board each time. The pointer-free
absolute overlay does not affect layout. Board-local CSS variables establish
layer order. Cancellation removes every transient node/animation and restores
captured source-node styles; stale promises cannot commit to a new game.

Baseline timing is centralized in `ARENA_TIMINGS`: movement 110ms/tile clamped
to 220–480ms; windup 110ms (Snipe 220, Revive/Fireball 180); tracer 150ms;
impact 180ms; HP tween 240ms; damage float 360ms; heal float 420ms; status 360ms;
push 210ms; Fireball area 360ms; action gap 55ms; turn banner 300ms; victory delay
260ms. Impact, bar and amounts overlap. Real reviewed AI playback was about 3.6s
for four actions including Move, Revive, Heal and Attack, plus turn transitions.

The lab's twelve authoritative fixtures replay through the exact same controller
and handlers as real Arena. Each button auto-resets. Reset fixture interrupts;
0.5x / 1x / 2x speed and Instant are development-only controls. No fixture or
backend contract changes were needed.

Reduced motion replaces travel with short source/target flashes, keeps amounts
spatially still, omits animated status rotation, and retains status text and
Fireball cells. Instant skips waits and overlays while executing semantic updates.

## Verification

Final frontend run: **138 passed**, including **28 new animation tests**.
Full Python suite: **1,204 tests in 333.721s; 1,199 passed, five existing
platform-specific skips, zero failures/errors**. Production build: **passed**.
All three Chromium scripts: **passed**, with no presentation console errors.

The final small frontend correction synchronizes selected-panel HP/status with
board feedback. After that correction, frontend tests and build passed again,
the 15 Python presentation tests passed again, and the real-game browser review
asserted selected-panel HP matches the impact value. Backend code was unchanged.
Full-suite sources were held stable during execution to preserve frozen guards.
No provider inference or live benchmark is part of these commands.

```powershell
npm.cmd test
npm.cmd run build
.venv\Scripts\python.exe -m unittest discover -s tests -v
# With npm.cmd run dev running:
node scripts/arena-presentation-lab-smoke.mjs
node scripts/arena-presentation-smoke.mjs
node scripts/arena-animation-smoke.mjs
```

New frontend tests exercise real default handlers, registered overrides,
impact-time checkpoints, HP/number/bar synchronization, continuous path movement,
all class glyphs, delayed Finish removal, Bash ordering/no fake push, Fireball
friendly victims/stable order, Core destruction before victory, stale checkpoint
cancellation, CSS geometry, WAAPI abort cleanup, speed and instant/reduced motion.
Existing tests retain queue sequencing, streamed logs, input locking, reset and
route/request cancellation coverage.

Chromium acceptance passed all twelve lab fixtures, checking positions over
multiple animation frames rather than just ghost existence, intermediate HP-bar
widths, resolved HP while amounts are visible, measured area width, all Fireball
victims together, and Core destruction before victory. Final entities/logs match
the authoritative fixture for every demo. Repeated reset leaves no transient DOM
or active WAAPI animations. Reduced motion and Instant retain semantic results.

Real Arena acceptance covered manual movement/attacks/heal/Snipe/Core victory,
then Human vs Heuristic · Offline. The actual AI sequence was Cleric movement,
Revive, Heal, Ranger Attack; logs arrived with actions and input unlocked at the
end. Additional Chromium checks interrupted New Match during Move, Attack,
Fireball and the heuristic queue, resized during movement, switched environments
and returned, and navigated Arena → lab → Arena during playback. No presentation
console errors or stale effects remained. A 900px viewport had no document
horizontal overflow.

Representative frames were visually inspected: Attack, DOWNED, Revive, Fireball,
Core victory, and the real AI's Revive/Heal/Attack. Frame samples additionally
prove movement and temporal order. This is automated Chromium exercise with
image/frame review, not a separate user-conducted playtest or video recording.

**UX assessment:** Yes — with the log ignored, movement, attack source/target,
damage, heal, downed and revive are distinguishable. Source action rings and
spatial tracers show who caused the effect; the target pulse, amount and status
show its consequence. The real heuristic turn demonstrated move/revive/heal/attack;
lethal/downed feedback was also checked with authoritative lab and real Snipe.

## Evidence

All evidence is local and ignored under `.local/arena-ui-phase3/`:

- `presentation-temporal-review.json`: RAF samples for all twelve lab effects.
- `heuristic-turn-frames.json`: actual authoritative AI events and per-frame
  source/target/position/HP/log/control observations.
- `browser-smoke.json`, `interruption-review.json`: real game and cancellation results.
- `lab-attack-playing.png`, `lab-revive-playing.png`, `lab-down-playing.png`,
  `lab-fireball-playing.png`, `lab-move-playing.png`, `lab-shield-bash-playing.png`.
- `arena-ai-revive.png`, `arena-ai-heal.png`, `arena-ai-attack.png`,
  `arena-ai-acting.png`, `arena-winner.png`, `arena-narrow.png`.
- `frontend-tests.log`, `python-tests.log`, `python-presentation-final.log`,
  `build.log`, `browser-game.log`.
- `preservation.json`: 164 protected tracked backend, test and Empire files have
  unchanged normalized content relative to HEAD.

Screenshots alone do not prove motion; the RAF samples and temporal assertions
are the motion evidence. No video dependency was added.

## Files in this phase

Changed (including extension of existing uncommitted Phase 2 files):

- `frontend/src/js/arena-animation.js`: default effects, ownership, measured
  geometry, centralized timings, actual Snipe/Revive registry overrides.
- `frontend/src/js/arena-presentation.js`: guarded optional effect checkpoints.
- `frontend/src/js/arena.js`: preserve live DOM at checkpoints, render HP bars and synchronize selected-panel values.
- `frontend/src/css/arena.css`: animation primitives, HP track, readable cues,
  measured effects, local layers, Core destruction and log highlight.
- `frontend/src/js/arena-presentation-lab.js`: development speed selection.
- `scripts/arena-presentation-lab-smoke.mjs`: RAF/geometry/HP assertions and broader cancellation.
- `scripts/arena-presentation-smoke.mjs`: real heuristic temporal evidence/frames.
- `docs/arena-ui-phase2.md`, `docs/arena-presentation-engine.md`: corrected baseline and current guide.

Added: `frontend/tests/arena-animation.test.js`,
`scripts/arena-animation-smoke.mjs`, and this report.

The workspace already contained uncommitted Phase 2 changes in backend/web,
environment routing, tests and build scripts. They were preserved; Phase 3 adds
no backend edits. Protected gameplay, stats, AP, legality, Core/downed/revive/
finish rules, heuristic, providers, prompts, observations, schemas, benchmark
artifacts, snapshots/replays and Empire behavior remain unchanged. No model
inference, benchmark run, backend sleep or major class-art work was performed.

## Limitations and next priorities

The art remains placeholder glyphs. Tracers, pulses and status labels are simple
DOM effects designed for replacement. Movement has no class-specific walk cycle;
a resize mid-tween can cause a brief endpoint adjustment. Reduced motion is read
on driver creation, so refresh/remount after changing the operating-system setting.
Multi-victim status transitions are presented in stable event order and can make
a heavily lethal Fireball take longer than a normal action. The lab has the Bash
push example; no-push behavior is verified in tests rather than a separate button.

Phase 4 could improve Knight/Ranger/Mage/Cleric silhouettes, team variants,
Core art and richer projectiles/Revive art. Sound can follow separately. None of
that work is started here.

## Launch

```powershell
cd C:\code\aig
npm.cmd run dev
```

Arena: **http://127.0.0.1:5173/arena**

Choose **Human vs Heuristic · Offline**.

Presentation Lab: **http://127.0.0.1:5173/arena/presentation-lab**
