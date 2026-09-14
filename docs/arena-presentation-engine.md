# Arena presentation engine

## Batched AI turns (Phase 5)

The engine derives command groups from existing V1 events. Each gameplay event
and its effects is one action; following victory belongs to that group and stops
the sequence. EndTurn remains separate and is not counted. Returned controller
identity selects AI pacing. Group indices/totals are per player and turn, never
derived from AP spent. No backend contract or decision changes are required.

The same handlers run for humans and AI. AI groups use centralized
`aiActionMinDuration` (1000 ms, including handler time) and
`aiBetweenActionPause` (250 ms), scaled by speed or bypassed in instant mode.
Reduced motion retains pacing. Driver clock waits use abortable timers rather
than relying on an overlay Web Animation. Both engine cancellation and driver
cleanup release waits; generation checks prevent stale effects and commits.

The UI uses a separate presentation actor focus and group counter. Logs reveal
per event; AP and turn remain visual checkpoints until the corresponding handler
completes. Input unlocks only after final reconciliation. Missing batches or
failed synchronization show an actionable warning. The lab's **Play sample AI
turn** runs a real five-command fixture through this same path. See
[Phase 5 diagnosis and verification](arena-ui-phase5.md) for evidence and the
outstanding human visual acceptance check.

Arena presentation is downstream of authoritative commands. Python still resolves
immediately. The web-only `PresentationSimulation` captures successful commands
and projects deterministic `arena-presentation-events-v1` events. It also captures
every automatic heuristic action in execution order. It does not change gameplay,
AI decisions, the research API, replay, snapshots or hashes. Empire has no Arena
presentation events.

## Event contract

Browser command responses keep the original public DTO and add:

```json
{
  "state_hash": "final authoritative hash",
  "presentation": {
    "version": "arena-presentation-events-v1",
    "start_state_hash": "before command",
    "final_state_hash": "after command and automatic AI turn",
    "events": []
  }
}
```

GET/New Match returns current state and historical logs without playback. The
projection's action types are `move`, `attack`, `heal`, `revive`, `finish`,
`shield_bash`, `snipe`, `fireball`, `turn_end`, plus separate terminal `victory`.
Events include sequence, actor ID/class/team/label, origin, target/target ID,
destination/path when appropriate, resolved effects, AP/turn transition, log,
and trace before/after hashes. Victory carries winner and terminal reason.

Effects are `damage`, `core_damage`, `heal`, `downed`, `revived`, `removed`, `move`,
and `push`. They identify entity kind/ID/owner/position and resolved HP, status
or destination. Amounts are actual HP loss/restoration, including clamping.
Fireball preserves all victims, including friendlies. Entity IDs have stable
ordering; each entity's effects are HP, status, then displacement. Movement uses
the existing authoritative pathfinder, not a frontend pathfinder. Event JSON in
the lab exposes complete examples.

No events enter authoritative replay/state hashing. There are no clocks, colors,
art names, random visual IDs or presentation options in this backend contract.

## Visual state and queue

`mountArena` stores the final response as `authoritative` and separately owns the
current visual `state`. Final HP/positions/winner are not rendered prematurely.
`applyPresentationEvent` clones visual state and assigns only resolved values;
it computes no rules, legal actions or damage.

`ArenaPresentationEngine.play`:

1. Cancels old playback and establishes an AbortController and generation.
2. Checks contract version and start-state hash, synchronizing if incompatible.
3. Appends the event log, then awaits its registered handler.
4. Allows optional guarded `commit(effects)` checkpoints during the handler.
   These apply a subset through the same reducer without replacing live DOM.
5. Applies the complete event, renders, and waits the central action gap.
6. Compares visual entity/turn/AP/winner structure against the final DTO, reports
   any mismatch, then adopts the authoritative response and unlocks controls.

Checkpoints solve the concrete Phase 2 blocker: replacing the whole board during
an effect destroys its DOM animations, but waiting until all feedback finishes
makes HP snap late. At impact the checkpoint updates visual state; the driver
updates matching numeric/accessible HP, including the selected-unit panel, and
animates a DOM HP bar. Final event
application is idempotent because effects contain resolved assignments. Custom
handlers may omit checkpoints; their effects then commit at handler completion.

Damage/Heal HP commits at impact. Status, Finish removal and Bash displacement
commit after their visual transition. Fireball HP victims commit in stable event
order and animate together; later status/displacement follows original order.
Authoritative state is never mutated.

Logs append one event at a time, newest first, with latest-line emphasis and
`aria-live="polite"`. Up to 60 recent lines are retained. Gameplay buttons and
board commands lock throughout the queue. AI thinking and AI acting are distinct;
New Match/Refresh remain available during playback. Victory commits after the
lethal action's damage/destruction and the separate victory delay, with the
terminal reason visible. There is no backend sleep.

## Registry and overrides

Resolution order is action+class, action alone, generic fallback.
`createArenaRegistry()` installs real `snipePresentation` and
`revivePresentation` overrides. Snipe has longer aim and a strong straight tracer.
Revive adds advance target glow, a persistent double-ring halo and restorative
beam before HP restoration and a downed-to-active transition. Both share the
same combat/effect primitives with the generic handler.

```js
import { createArenaRegistry, presentEffects } from './arena-animation.js';
const registry = createArenaRegistry();
registry.register('attack', rangerAttack, 'ranger');

async function rangerAttack(event, driver, signal, context) {
  const clear = driver.cue(event, signal);
  try {
    await driver.pulse(event.actor_id, signal);
    await driver.tracer(event.origin, event.target, signal);
    if (!signal.aborted) await presentEffects(event, driver, signal, context);
  } finally { clear(); }
}
```

Pass a registry to `mountArena(root, api, { registry })`, or add registration in
`createArenaRegistry()` to share it with real Arena and the lab. Handlers receive
`(event, driver, signal, { commit })`. Existing three-argument handlers still work.
Never calculate HP, infer combat from final-state differences, or retain a global
checkpoint callback. Each callback checks queue generation and abort status.

## Driver, geometry and transient ownership

`ArenaAnimationDriver` owns all DOM/WAAPI mechanics:

- Actor pulse and persistent source/target rings with action labels.
- One movement ghost following the complete authoritative path, with the source
  hidden throughout. Duration is clamped by path length. All classes share it.
- Directional tracer; Knight additionally lunges toward the target.
- Target hit flash/shake, damage/heal floating text and HP tween.
- Downed slump/desaturation, Revive glow/stand-up, Finish fade/shrink.
- Core hit and separate destruction text, flash/fade and final cracked treatment.
- Fireball impact and individually measured cells in its 3×3 area.
- Brief team-turn banner, abortable delays and cleanup.

Stable `data-unit-id`/`data-core-id` and tile x/y attributes resolve geometry from
actual cells relative to `.arena-overlay`. CSS custom dimensions use
`style.setProperty`. A resize during travel may shift its endpoint temporarily;
final rendering restores exact placement and subsequent effects remeasure.
No screen coordinates survive between primitives.

The absolute overlay never participates in layout and has `pointer-events:none`.
Local board layer variables order pieces, effects, text and banners. Numbers
rise/fade above targets. Source/target cues remain visible through impact.
The HP bar uses ordinary DOM width animation while a native meter retains its
accessible semantic value. No art/glyph dependency, canvas or particle engine is
introduced.

`clear()` cancels owned animations, removes transient nodes and runs cleanup.
Cleanup captures the original DOM node, so an old movement handler cannot change
a replacement entity from a newer match. WAAPI transforms are cancelled at
completion; source visibility and stable styles are restored.

## Central timings

Baseline milliseconds in `ARENA_TIMINGS`:

| Setting | ms |
| --- | ---: |
| movePerTile / moveMin / moveMax | 110 / 220 / 480 |
| attackWindup / snipeWindup / reviveWindup | 110 / 220 / 180 |
| projectileDuration / impactDuration | 150 / 180 |
| hpDuration | 240 |
| floatTextDuration / healFloatDuration | 360 / 420 |
| statusTransition / pushDuration | 360 / 210 |
| fireballWindup / fireballImpact | 180 / 360 |
| betweenActionDelay | 55 |
| turnTransition / victoryDelay | 300 / 260 |

`moveDuration` (320ms) is retained for compatibility; real movement uses clamped
path timing. `duration` scales named and calculated durations by `speed`.
Impact, HP tween and floating amounts overlap instead of accumulating waits.
An observed four-action heuristic turn (Move, Revive, Heal, Attack) took 3.6s,
including turn transitions. This is an observation, not a strict timing test.

The driver accepts `speed`, `instant`, `reducedMotion` and timing overrides.
Instant skips all waits/transient overlays but executes semantic updates.
Reduced motion is read when mounted: movement uses a pulse, tracer travel becomes
source/target flashes, numbers stay still, status transitions omit rotation,
and Fireball cells remain indicated. Final static downed styling is retained.

## Cancellation and recovery

Reset/New Match, Refresh, lab reset/replay, and environment switches abort the
queue. Every checkpoint and final commit checks generation and AbortSignal.
Separate request generations prevent an old HTTP response overwriting new state.
Custom handler errors are reported and the resolved event is still applied.
Returning to Arena after an abandoned server request waits for it to settle,
then reads fresh state. Destroy prevents rendering into another route.
Full route navigation discards the previous document; Chromium checks navigation
during playback in both directions. No animation data remains in the new route.

## Presentation lab

Phase 4 adds class-specific attack handlers for Knight, Ranger, Mage and Cleric,
plus Shield Bash, Fireball and Heal overrides alongside Snipe and Revive. All use
the existing `combatPresentation` sequence and driver primitives. A semantic
motif is carried through source/target cues, travel and resolved impact feedback;
it does not affect damage, legality or event ordering.

To replace only Ranger attack presentation, register a handler with the class
argument (the registry API is `register(type, handler, actorClass)`):

```js
createArenaRegistry().register('attack', newRangerAttack, 'ranger');
```

Pass that registry through `mountArena(..., { registry })`, or change the default
entry in `createArenaRegistry`. Change `revivePresentation` or register
`registry.register('revive', newRevivePresentation)` for Revive. Preserve
`presentEffects(event, driver, signal, context, motif)` to retain authoritative
HP/status checkpoints. Class artwork lives separately in
`arena-unit-visuals.js`; see [Phase 4](arena-ui-phase4.md) for replacement steps.

The lab now also includes four class Attack fixtures and a collapsible gallery
of all four classes in Blue/Red, active-selected and downed states. Gallery and
board call the same `renderArenaPiece`; the selected panel uses `unitVisual`.

Open http://127.0.0.1:5173/arena/presentation-lab. Choose Move, Attack, Snipe, Heal,
Revive, Down, Finish, Shield Bash, Fireball, Core damage, Victory or Turn. Every
button restores a known authoritative fixture and plays through the same real
controller, engine, registry and driver. Repeat any demo without manual setup.
Reset fixture cancels active effects. Speed selects 0.5x, 1x or 2x; Instant skips
waits. These controls stay in the lab. Event JSON exposes the exact batch.

The lab performs no API requests or inference. Its committed fixtures come from
authoritative executions. Regenerate when intentionally adding examples or changing a contract:

```powershell
.venv\Scripts\python.exe scripts/arena-presentation-fixtures.py
```

Phase 3 did not alter the fixtures or contract. See
[Phase 3 verification](arena-ui-phase3.md) for tests, evidence and limitations.
