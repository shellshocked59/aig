# Arena UI Phase 2: presentation architecture

Phase 2 established the semantic event projection, presentation queue, reducer,
registry, animation driver boundary, cancellation generations, streamed battle
log, reduced-motion/instant options, and presentation lab. It did **not** deliver
the complete, satisfying visual animation set. The earlier Phase 2 report
oversold the prototype effects; its descriptions must not be treated as product
acceptance for movement or combat feedback.

The Phase 3 inspection found basic WAAPI prototypes but important missing behavior:
HP changed only after all feedback, movement recreated a ghost per path segment,
Snipe and Revive were not registered overrides, the native HP meter snapped on
rerender, Fireball used board percentages rather than individual cell geometry,
and there was no visible turn banner or separate Core destruction sequence.
The original browser checks mainly established element presence and final states.

[Phase 3](arena-ui-phase3.md) supplies and verifies the first complete default
animation set. [The engine guide](arena-presentation-engine.md) describes the
current implementation and extension points.

## Retained Phase 2 foundation

- Browser-only `PresentationSimulation` records authoritative action results,
  including heuristic actions, and emits `arena-presentation-events-v1`.
- Authoritative and visual state remain separate. The engine processes semantic
  events sequentially, then reconciles the visual result with the final DTO.
- The registry resolves action/class, action, then generic fallback.
- Event logs appear at event start. Controls remain locked during playback.
- Abort signals and request/queue generations prevent stale commits after reset.
- The lab feeds committed authoritative fixtures through the real controller.
- No clocks or presentation events enter gameplay, replay, or research contracts.

The Phase 2 baseline had 110 passing frontend tests and a historical full Python
run of 1,204 tests (1,199 passed, five platform skips). Those are architectural
baseline results, not evidence that the requested Phase 3 motion was complete.
Historical evidence remains in `.local/arena-ui-phase2/`; new evidence is separate
in `.local/arena-ui-phase3/`.

## Local workflow

```powershell
cd C:\code\aig
npm.cmd run dev
```

Arena: http://127.0.0.1:5173/arena ? choose **Human vs Heuristic ? Offline**.
Lab: http://127.0.0.1:5173/arena/presentation-lab.
No external provider is required.
