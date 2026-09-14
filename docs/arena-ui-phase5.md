# Arena UI Phase 5 — readable AI turn playback

## Local-site diagnosis confirmed (2026-09-14)

The user subsequently saw the explicit missing-animation-sequence warning on
their local site. `npm.cmd run build` uses `.env`'s public origin
`http://api.aig.localhost`; this is the Docker API on port 8000, not the separate
`npm.cmd run dev` backend checked earlier. The running Docker backend predated
the presentation changes and its public state had no `state_hash`.

Built the frontend and ran
`docker compose up -d --build --no-deps --wait api`. The API became healthy.
An offline V2 EndTurn through the actual `api.aig.localhost` Apache host now
returns `arena-presentation-events-v1`, a state hash, and six ordered events:
Blue EndTurn, Move, Snipe, Move, Move, Red EndTurn. Apache's served JavaScript
hash matches the rebuilt bundle. The site was left at a fresh V2 match.
Evidence: `artifacts/arena-phase5/local-built-start.json`,
`local-built-response.json`, and `local-ready-state.json`.

This identifies the stale backend on the user's actual site as the cause of
the missing-sequence warning. Rebuilding frontend assets or restarting the
separate 5173 dev server alone cannot update that Docker process. Use
<http://aig.localhost/arena> and refresh after rebuilding.

## Diagnosis and evidence

The user reports that End Turn shows all AI results at once, with no visible
animation. Browser tooling was unavailable; the user subsequently clarified that
a preview was not needed to investigate this symptom. A Chromium/manual visual
review has **not** been performed, and the exact trigger in the user's browser
has not been established.

Direct inspection of the running HTTP response found seven ordered V1 events:
Blue EndTurn, five Red commands, Red EndTurn. Each command already carries its
own resolved effects, before/after AP, state hashes and turn transition. The
frontend stores the final response separately and normally awaits each handler.
There is no demonstrated backend flattening or normal-path early final-state
commit. The original move timings were only 220–480 ms and the event gap 55 ms.

One concrete clock defect was found: every delay used an opacity Web Animation
on the overlay. Without `Element.animate`, `animate()` returned immediately, so
both effects and delays collapsed and the entire queue could drain without a
readable pause. Clock waits now use cancellable timers independently of DOM and
Web Animations support. This failure mode is reproduced by the DOM tests; it is
not proof that the user's browser lacked Web Animations.

A separate stale runtime was confirmed: the server on 5173 rejected
`/demo-ai/heuristic-v2` as an unknown provider although current source implements
it. The identified dev process was restarted using `npm.cmd run dev`; current
V2 HTTP requests now succeed. Whether that stale runtime caused the user's exact
animation symptom is unproven. Missing batches and state/version mismatch
fallbacks now show an actionable UI message instead of only a silent snap or a
console warning. They synchronize safely; they cannot manufacture absent events.

## Playback design

No backend changes or contract version bump. `actionGroups()` derives local
groups from `arena-presentation-events-v1`: one executed gameplay event is one
group, with all nested effects and any following victory event. EndTurn is a
separate transition, excluded from the action count. Grouping stops at victory.
Player/turn and returned controller identity select AI pacing; no heuristic or
model implementation is special-cased. Snipe costs two AP but counts once.

`ARENA_TIMINGS.aiActionMinDuration = 1000` ms includes existing animation time.
The engine waits only for the remainder, then uses
`aiBetweenActionPause = 250` ms. Normal short commands therefore occupy about
1.25 seconds. Existing human timings remain unchanged. Speed scales both
durations; instant bypasses them. Reduced motion retains readable group timing
while using the existing reduced-motion effects.

The UI shows thinking while awaiting HTTP and acting during playback. Gameplay
groups show `Action i / n`, actor and command. An amber actor outline follows
the acting unit and survives the action checkpoint and pause, independently of
human selection. Existing source/target effects are reused; no art was added.

The event reducer commits HP at impact, then status/displacement and final
event transition. AP follows that event's resolved checkpoint. Red remains the
visual active player until its EndTurn handler completes. Logs append when
their event starts, including terminal feedback only after the causing action.
The final authoritative DTO is reconciled after the queue. Input stays locked
through the queue and the transition. New Match and route cancellation abort
the handler, minimum wait, inter-action pause and all future groups. Timer
cleanup removes abort listeners and resolves waiting work without stale commits.

## Lab and reproducibility

`Play sample AI turn` uses a real fixed V1 opening response: Ranger Move, Move,
Attack Mage, Attack Mage (Downed), Attack Knight. It uses the same Arena
controller, driver, action counter and engine. The start includes Blue EndTurn
and the batch ends with Red EndTurn. Existing speed/instant controls apply.

Regenerate both V1 and V2 command fixtures:

```powershell
.venv/Scripts/python.exe scripts/arena-ai-playback-fixtures.py
```

V2's opening example executes four commands, Move/Snipe/Move/Move, spending
five AP. This guards against a hard-coded five-action counter.

## Verification

Live HTTP through the real frontend and real pacing clock, in JSDOM without
Web Animations, produced:

| Provider | Commands | Response-to-unlock duration | Result |
| --- | --- | --- | --- |
| Heuristic V1 | 5 | 6.618 s | Ordered checkpoints; input locked; no warnings |
| Heuristic V2 | 4 | 5.294 s | Ordered checkpoints; input locked; no warnings |

These are measured fallback playback timings, **not** visual browser timings.
The full animation path can take longer for multi-stage effects. Evidence lives
in `artifacts/arena-phase5/timing-review.json`, with per-frame status, actor,
AP/turn text and lock observations; `*-live.json` retains authoritative inputs
and responses. There are no screenshots because browser access was unavailable.

Run the offline live check (resets Arena on the local test server):

```powershell
node scripts/arena-ai-playback-check.mjs
```

Targeted tests cover both actual provider batches, counters, multi-AP actions,
deferred handler order, AP/turn/log checkpoints, selection versus actor focus,
terminal truncation, cancellation during action 2 and both waits, instant lab
completion, speed, reduced motion and missing-batch feedback. Full test outputs
are in `artifacts/arena-phase5/frontend-tests.txt` and `python-tests.txt`.

Final results: **185 frontend tests passed**; production build and
`git diff --check` passed. The Python `unittest discover -s tests` run executed
1,220 tests in 357.801 seconds: 1,214 passed, five platform skips and one failure.
`test_expanded_schedule_below_theoretical_ceiling` detected source mutation while
final frontend edits overlapped its frozen source inventory. With all source
edits stopped, that unchanged test passed in 11.010 seconds; output is preserved
in `python-guard-rerun.txt`. Thus 1,215 distinct Python tests passed across the
full run and targeted rerun, with five skips. No guard was weakened. The runner
is unittest; pytest is not installed. The separate 20-file frozen-source hash
inventory matches completely (`preservation.json`). No actual model provider
calls were made by the fake-provider regression test.

No production backend, rules, heuristic V1/V2, execution, replay, research
contracts, benchmark artifacts or Empire source was edited for Phase 5. Existing
uncommitted Phase 1–4/V2 work was retained. No model inference or live benchmarking
was run. Fixture generation executes only offline heuristics.

## Launch and remaining acceptance

```powershell
cd C:\code\aig
npm.cmd run dev
```

Arena: <http://127.0.0.1:5173/arena>

Lab: <http://127.0.0.1:5173/arena/presentation-lab>

Refresh the browser after rebuilding. Python in this development command does
not hot reload; restart it after backend source changes.

The sequence is now demonstrably separated in timed frontend checkpoints, even
without visual animation support. The human question “can I recount the five
actions I just saw?” still needs a person viewing the updated real game. Do not
label this as a passed Chromium visual review. The next priority is confirming
that original no-animation symptom in the user's refreshed client and inspecting
any visible playback warning if it persists; no heuristic tuning is warranted.

## Phase 5 files

Modified: `frontend/src/js/arena-presentation.js`, `arena-animation.js`,
`arena.js`, `arena-presentation-lab.js`, `frontend/src/css/arena.css`, and
`docs/arena-presentation-engine.md`.

Added: this document, `frontend/src/js/arena-ai-playback-fixtures.json`,
`frontend/tests/arena-ai-playback.test.js`,
`scripts/arena-ai-playback-fixtures.py`, and
`scripts/arena-ai-playback-check.mjs`. Runtime evidence is under
`artifacts/arena-phase5/`.

## Later Chromium review

[Phase 6](arena-ui-phase6.md) subsequently verified the shared presentation engine in real Chromium, including sequential offline AI playback, temporal lab effects, overlay geometry, cancellation, reduced motion and instant mode. Its evidence is under `artifacts/arena-ui-phase6/`. The earlier browser limitation above describes the Phase 5 run, not the current verification status.
