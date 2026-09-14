# Arena bounded replanning V1 implementation

Implemented as an opt-in control contract. Strict full-turn remains the default. No live inference or model benchmark was run.

## Execution and preservation

`arena-control-full-turn-bounded-replan-v1` is implemented in `backend/aig/arena/ai/bounded_replan.py`. `ArenaBoundedReplanController` uses the existing full-turn provider interface and a small additive `execute_plan_segment` loop. Every action still passes through `ArenaSimulation.execute` (or the presentation wrapper) and the authoritative command engine.

The recovery boundary is after the first command rejection and **before EndTurn**. The frozen `execute_arena_turn` function is never called by the bounded controller and was not edited. No heuristic, observation, plan, prompt, rules, model-profile, action-ID, constrained, stepwise, or Empire implementation was changed. All existing benchmark recipes and historical evidence remain intact.

1. Build Observation V1 from the authoritative state; request a remaining-turn plan.
2. Let the provider perform its existing single static repair, then revalidate the typed result against that observation, including remaining AP.
3. Execute in order. Preserve the successful prefix and discard the rejected action and entire remaining suffix.
4. Only execution rejection with AP remaining permits one fresh planning wave. No failed-plan context is included.
5. Completion (including empty/short plans), a second execution rejection, or zero AP ends the nonterminal turn once. Victory suppresses EndTurn and all further requests.

V1 fixes the execution-replan limit at one; it has no configurable larger limit. Built-in model providers reserve each transport attempt through their existing `before_request` hook. The controller composes/restores an existing hook and rejects a fifth reservation before transport. There are at most two planning waves and one static repair per wave, hence four attempts. Heuristic/custom typed providers have no transport-attempt telemetry; their invocations are represented by planning waves, not fabricated network requests. A custom provider is responsible for honoring the existing bounded provider contract internally.

Static invalidity never consumes the execution-replan allowance. The existing provider owns static repair; the controller never adds another repair loop. A typed custom provider that returns a statically invalid plan receives the normal failure policy, not another execution wave.

`arena-turn-prompt-v1` is reused byte-for-byte. Its description that invalidity ends the turn was written for strict full-turn control and does not literally describe adaptive recovery. This deliberate caveat keeps the comparison about control alone. `action_points_remaining` remains authoritative, including budgets 1–4.

## Failure and AP accounting

Interactive provider/static exhaustion uses the existing Heuristic V1 fallback, planned from the current remaining state. It is a final segment: no further model replan follows fallback, even if that segment rejects. Execution rejection alone never invokes fallback. Request-ceiling/source-mutation failures preserve the prefix without fallback or EndTurn. Unexpected programming exceptions propagate.

The strict v6 experiment disables fallback and preserves the current prefix without EndTurn on provider failure, writes diagnostics, and aborts the remaining schedule. No replacement trials or transport retries are allowed.

AP accounting is captured before EndTurn resets the next player's budget. `ap_spent` equals the sum of committed segment costs. `ap_recovered` is AP committed by the replacement segment after the first rejection, including separately labeled fallback AP if recovery fell back. It is not a claim of better tactics. Model AP and fallback AP are separate; terminal leftover AP and nonterminal unused AP have separate aggregate fields.

## Settings, host, and browser

`ArenaControlSettings` and `CONTROL_VERSIONS` form the additive gameplay registry:

| Setting value | Control |
| --- | --- |
| `full_turn` | `arena-control-full-turn-v1` (default) |
| `bounded_replan` | `arena-control-full-turn-bounded-replan-v1` |
| `stepwise` | `arena-control-stepwise-v1` |

`AIG_ARENA_CONTROL_MODE` is a **process environment** setting for the new host. Do not add it to the existing `.env`: the frozen settings loader intentionally rejects new keys. `load_control_settings(local_file=...)` supports a dedicated optional control file with process environment precedence; application startup uses the process environment. This preserves the old settings file and its hash.

Example opt-in, only when manual model play is separately authorized:

```powershell
$env:AIG_ARENA_CONTROL_MODE = 'bounded_replan'
npm.cmd run dev
```

The current development/Docker entry point is `aig.control_web:create_app`. The original `aig.web:create_app` remains byte-identical and available as the strict historical host. Existing API-only hosting remains unchanged. Restart the development/backend process to load the new host.

The existing collapsed play-mode menu now contains one AI-control select: **Strict Full Turn**, **Adaptive · Replan if blocked**, and **Stepwise · Re-evaluate every action**. It applies on creation, never requests a plan by itself, and configures both human-vs-provider and observer sessions. New Match retains the active match's authoritative control selection. Page loading and session creation perform no inference. The public DTO includes `control_mode` and `control_version`; no research ID is prominently rendered.

Explicit routes use `?control_mode=bounded_replan` on `/api/arena/demo-ai/{provider}` and `/api/arena/observer/demo`. Omitted selection uses the startup default. Sessions are server-owned and shared across tabs, matching existing behavior.

Stepwise uses its existing V2 observation, step prompt, five-decision bound, and strict failure policy. Its trace is adapted to the session container; the frozen controller is unchanged. Selecting stepwise with an offline heuristic label uses the existing stepwise Heuristic V1 provider.

All bounded planning/execution happens within the existing session lock. One HTTP response contains the final state and complete ordered presentation event batch across both waves. The existing AI thinking/acting and sequential animation behavior is unchanged.

## Traces and aggregation

`ArenaBoundedReplanTurnTrace.to_dict()` returns detached data. Its `waves` contain the initial and optional replacement observations/hashes, requested provider, accepted plan and planned AP, independent inference snapshot, transport attempts/static repairs, failed-provider category, optional fallback plan/provider, attempted actions, rejection index/action/reason/current AP, discarded suffix count, committed commands, command offsets, executed/unused AP, and resulting state hash. Raw model output and chain-of-thought are not retained. Browser serialization recursively removes transport attempts and full observations.

The turn adds player/turn/control identity, total commands and AP, AP before recovery, recovered AP, model/fallback AP, model-controlled flag, planning-wave/request/repair counts, fallback usage, terminal result and final state hash. Commands replay independently of provider calls.

`aggregate_turns(traces)` reports model-controlled turns, one-wave turns, replan rate, successful-replan rate, second-rejection rate, AP before recovery, recovered/executed/unused AP, calls/repairs/waves per turn, fallback usage, and inference latency/token totals and per-turn means. Replan-success and second-rejection denominators are turns that requested a replan; replan-rate denominator is all supplied turns. Filter on `model_controlled` and exclude `fallback_used` when comparing pure-model cohorts. Unknown token totals remain null. Latency is recorded provider-request time, not animation or total HTTP elapsed time.

## Offline verification

```powershell
.venv/Scripts/python.exe -B -m unittest tests.test_arena_bounded_replan
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_benchmark demo
npm.cmd test
npm.cmd run build
```

The deterministic demo starts with Snipe, stale Snipe, and stale Attack. The first Snipe downs the target and spends 2 AP. The second action rejects; the entire suffix is discarded. The fresh plan attacks the other target three times, recovering 3 AP: **5 AP executed, 0 unused, 2 fake provider calls, replay verified**. It requires no network.

The new tests cover legal strict-path parity, two-action committed prefixes, state freshness, first-action rejection, empty/short plans, second rejection, initial/replacement terminal victories, zero AP, budgets 1–5, independent static repairs, four-attempt maximum/fifth denial, actual repair exhaustion, initial/replacement fallback and strict failure, determinism/replay, idle session selection, a single ordered web response batch, public trace redaction, recipe preparation, fake paired execution and schedule abort. Frontend tests verify selection, no creation on load/change, API query parameters and New Match preservation.

The frozen Fireball methodology tests now explicitly exclude only the five new backend paths from that experiment's source inventory. This is test isolation only: every original source/hash and source-drift assertion remains, and production methodology validation is unchanged. No historical hash was updated.

Manual visual browser verification could not run: the computer-use browser tool reported that no browser was available. DOM and real ASGI route tests cover the selection flow offline; visual layout remains a manual check before promotion.

## Historical audit and future experiments

The original design, audit JSON, analyzer and live artifacts were preserved. Historical trigger counts justify testing recovery, but do not establish recovery success. The implementation does not rewrite or synthesize historical replacement outcomes.

`arena-benchmark-v6` has its own integrity-checked recipe registry and additive runner. Prepared manifests bind recipe/hash, both control contracts, prompt/hash, Observation V1, logical/wire schema, static repair, frozen model/profile/configuration, rules/scenario, fixed probe snapshots/hashes, repetitions/order, source-file hashes and request ceiling. The schedule is repetition ? fixture ? strict then bounded. There is no preflight and no live action during preparation.

Prepare a one-turn Luna smoke (4-request ceiling) and a paired seven-probe comparison with two repetitions (28 turns, 84-request ceiling):

```powershell
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_benchmark prepare --output .local/arena-bounded-smoke-plan.json
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_benchmark prepare --paired --probe all --repetitions 2 --output .local/arena-bounded-paired-plan.json
```

**Proposed only; require separate live authorization:**

```powershell
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_benchmark run --plan .local/arena-bounded-smoke-plan.json --output .local/arena-bounded-luna-smoke-01 --live
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_benchmark run --plan .local/arena-bounded-paired-plan.json --output .local/arena-bounded-luna-paired-01 --live
```

The smoke may not trigger recovery; do not add calls to force it. Use a new output directory for each separately authorized attempt. Source changes invalidate prepared plans and require preparation/review again. The runner rejects profile overrides rather than silently changing settings. Ordinary failures abort; they are retained with unstarted counts and replayable commands.

Recommended next step: authorize only the four-attempt smoke after reviewing this implementation. Then review its evidence before authorizing the 84-attempt paired schedule. A later, separately frozen study can select replayable historical Luna truncation states for better trigger coverage. Later full matches should compare strict/bounded/stepwise against unchanged heuristic opponents with side swaps; stepwise necessarily uses a different prompt/observation contract. Full-match execution is not added to this v6 probe runner.

Promotion should weigh AP recovery, requests, latency, tokens/cost, match completion, pathological loops and manual play/animation quality. Bounded replanning remains opt-in.

## Changed-file inventory

Added:

- `backend/aig/arena/ai/bounded_replan.py`: segment execution, controller, detached traces and aggregation.
- `backend/aig/arena/control_settings.py`: immutable mode settings and version registry.
- `backend/aig/control_web.py`: additive session, recursive public trace filtering and current host routes.
- `backend/aig/arena/benchmark_artifacts/arena-benchmark-v6.json`: concrete frozen recipe.
- `backend/aig/arena/bounded_replan_benchmark.py`: recipe integrity, offline demo/preparation and gated probe runner.
- `tests/test_arena_bounded_replan.py`: 16 offline orchestration/integration/benchmark tests.
- `docs/arena-bounded-replan-implementation.md`: this report.

Updated:

- `frontend/src/js/arena.js`: collapsed selector and session/reset control forwarding.
- `frontend/src/js/api/arena.js`: explicit control query and rejection of an older host that silently ignores adaptive selection.
- `frontend/tests/arena.test.js`: three control-selection/API compatibility tests.
- `scripts/dev.mjs` and `Dockerfile`: current host entry point.
- `tests/test_arena_fireball_methodology.py`: original experiment source-scope isolation only.
- `docs/arena-ai.md` and `docs/arena-benchmarking.md`: links to the new opt-in control and recipe.

The three investigation files already present in the worktree were not modified by this implementation. No commits or GitHub operations were performed.

## Verification evidence

The 31 combined new-control and repair-fullmatch tests pass, including the two source-mutation-sensitive checks rerun after backend edits stopped. The 19 isolated Fireball methodology tests pass. All 116 hashes in the Fireball preservation fixture match unchanged files. Frontend: 197 tests pass; production build passes. `git diff --check` is clean after removing trailing blank lines in documentation.

Prepared offline artifacts exist at `.local/arena-bounded-smoke-plan.json` (4-attempt ceiling) and `.local/arena-bounded-paired-plan.json` (84-attempt ceiling), with matching source manifests. The demo trace is `.local/bounded-replan-offline-demo.json`. No provider endpoint checks, live provider requests, or live benchmark runs occurred.

Final broad regression: 1,274 tests ran, with five expected skips and one concurrent-edit source-guard failure. That guard also watches frontend files and detected the final API compatibility edit while the suite was running. With all source edits stopped, the affected full-match module passed all 11 tests; its specific ceiling test also passed directly with exit code 0. Thus all observed failures are resolved, but the broad run itself is not represented as a single all-green invocation. Logs: `.local/bounded-replan-regression-final.log`, `.local/bounded-replan-fullmatch-final.log`, `.local/bounded-replan-final-targeted.log`, and `.local/bounded-replan-frontend-final.log`.
