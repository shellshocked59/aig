# Arena full-turn planning with bounded replanning

Investigation and implementation design, 2026-09-14. **Not implemented or promoted.**

Recommend an explicit third control contract, `arena-control-full-turn-bounded-replan-v1`, with one execution replan per player turn. Keep strict full-turn as the current browser default until offline validation, controlled experiments and manual play establish a benefit. Reuse the existing full-turn provider, plan, observation, static repair and authoritative command engine. The new work is orchestration and trace aggregation, not tactical rules.

The historical evidence supports investigating this, but does not establish replacement-plan success. Luna's original full-match sample would trigger on 72/100 accepted turns; its later Observation V2 probes trigger on 8/28. Qwen's original first-action failures are execution failures, and a fresh observation after zero committed actions is identical: another inference may simply repeat the mistake.

## Scope and evidence

Only repository inspection, local historical execution reproduction, an offline analyzer and documentation were performed. Zero live inference, model benchmarks, endpoint checks, prompt edits or runtime behavior changes occurred. No GitHub operation was needed. No credentials or `.env` contents were printed.

The [audit output](arena-bounded-replan-audit.json) contains cohort summaries, every execution-failure boundary and SHA-256 hashes of the inputs read. The [offline analyzer](../scripts/arena-bounded-replan-audit.py) reproduces all 242 accepted model-plan execution results from saved observations, including rejection reasons, committed commands, AP and terminal results. It checks input hashes again before writing its output. This is local execution of historical plans, not generation of replacement responses or a new benchmark. It does not claim to reverify every whole-match replay or every file under `.local`.

Reproduce from the checkout:

```powershell
.venv/Scripts/python.exe -B scripts/arena-bounded-replan-audit.py
```

The analyzer requires the retained ignored `.local` evidence directories. Its committed JSON provides the results and provenance when those directories are unavailable. Preflight calls, unstarted turns and heuristic turns are excluded from model-turn counts. Failed provider turns are reported separately from accepted plans. Cohorts are never pooled across prompt/observation contracts.

Final verification: 242 accepted plans reproduced; 604 distinct input files hashed and unchanged across analysis; all report file links resolve. The existing `FriendlyFireTests.test_historical_bytes` and `test_browser_actual_baseline_without_inference` passed under `unittest`, confirming their protected source/prompt bytes and the browser's V1 baseline without inference. Git status contains only the three new deliverables listed below; no tracked file was modified. Pytest is not installed in this environment, so the two checks were run with the repository's unittest framework.

Created: `docs/arena-bounded-replan-design.md`, `docs/arena-bounded-replan-audit.json`, and `scripts/arena-bounded-replan-audit.py`.

## 1. Current application architecture

| Boundary | Current implementation and responsibility |
| --- | --- |
| Browser host | [web.py](../backend/aig/web.py): `ArenaWebSession` extends `ArenaGameplaySession`, which extends `ArenaSession`. The web factory replaces the API-only Arena session/routes and adds presentation and observer routes. |
| Session | [application.py](../backend/aig/arena/application.py): `demo` constructs provider/controller; `execute` applies the human command and calls `advance_until_human`, under an `RLock`. |
| Provider selection | [factory.py](../backend/aig/arena/ai/factory.py): `create_arena_turn_provider` selects heuristic/Ollama/OpenAI. Provider identity and control policy are currently not separate browser settings. |
| Full-turn controller | [controller.py](../backend/aig/arena/ai/controller.py): `ArenaAiController.run_turn` builds one observation, requests a plan, handles provider fallback, then executes and produces an `ArenaAiTurnTrace`. |
| Provider interface | `ArenaTurnProvider.create_turn_plan(ArenaObservation) -> ArenaTurnPlan`, declared in `controller.py`. |
| Plan construction | [provider.py](../backend/aig/arena/ai/provider.py): `ModelArenaTurnProvider.create_turn_plan` builds messages, performs inference, parses and optionally repairs. [contracts.py](../backend/aig/arena/ai/contracts.py) constructs immutable actions and `ArenaTurnPlan`. Heuristic providers instead compute plans on detached observation-derived state. |
| Static validation | [validation.py](../backend/aig/arena/ai/validation.py): `parse_turn_plan`, after strict JSON and logical schema parsing. |
| Sequential execution | [executor.py](../backend/aig/arena/ai/executor.py): **function** `execute_arena_turn`, not a class named `ArenaTurnExecutor`. |
| Rules and replay | [commands.py](../backend/aig/arena/commands.py): `validate_command` / `apply_command`; [replay.py](../backend/aig/arena/replay.py): `ArenaSimulation.execute` records only successfully applied commands. |

Current product flow:

```text
human command / explicit observer turn
  -> current authoritative observation
  -> provider create_turn_plan
     -> inference -> static validation -> at most one static repair
     -> sanitized provider failure: interactive heuristic plan
  -> execute_arena_turn
     -> successful command prefix -> first rejection stops suffix
     -> automatic EndTurn unless terminal
  -> public state and complete presentation event batch
  -> browser animation playback
```

The API-only factory in `backend/aig/api.py` still uses `ArenaSession`. The product web host uses `ArenaWebSession`. `gameplay.py` adds Heuristic V2 outside the frozen core; it does not change Luna control. Browser buttons currently offer Human vs Heuristic V2, Human vs OpenAI Luna, and Luna vs Luna observer play. Older `arena-ai.md` UI descriptions include buttons that are no longer the current visible set; backend generic provider routes still exist.

### Exact truncation and EndTurn semantics

`execute_arena_turn` checks the typed plan, reruns its structural invariants and validates state. It captures player and available AP. Each action becomes a command via `action_command` and is submitted to the supplied command sink, normally `simulation.execute`.

On `ValueError`, it records `invalid_action={index, action, reason}`, sets `truncation_reason="invalid_action"`, adds the error to the unsuccessful attempt and breaks. Indices are zero-based and local to the plan. The failed attempt has equal `ap_before`/`ap_after`; no later action is attempted. `plan.actions[index:]` is the complete discarded suffix, including the rejected action. Earlier actions remain committed.

The executor captures unused AP **before** issuing `ArenaEndTurn`. It then unconditionally ends a nonterminal turn, including empty plans, successful short plans and zero-AP turns. EndTurn changes active player and resets AP to five; it is not implicit in spending the last AP. Therefore reading state AP after this executor returns normally reads the next player's budget. A replan cannot safely be added after that return.

After each successful command the executor checks victory. It stops immediately, sends no EndTurn and attempts no later action. `truncation_reason="terminal"` only when planned actions remain; a final-action victory can have no truncation reason. `terminal_result` is the winner ID, including an opponent win from friendly-fire elimination.

## 2. Research control paths are separate

Structured [stepwise.py](../backend/aig/arena/ai/stepwise.py) defines `ArenaStepProvider.create_step` and `ArenaStepController`. Each decision receives freshly rebuilt Observation V2. `parse_step` requires zero or one action and exact current legal-catalog membership, beyond full-turn static validation. Empty means intentional stop; a successful action leads to another decision only with AP remaining and no victory. Five decisions is the safety bound; static repair can double transport attempts.

The controller calls `checked_step`, which bridges to benchmark provenance checking. It has **no interactive heuristic fallback**. Normal failures/empty output end the turn, but `catalog_execution_defect`, `request_ceiling` and `source_mutation` preserve the diagnostic prefix without EndTurn. This research controller should not become the browser orchestration dependency by accident.

Other preserved experiments:

| Control | Contract |
| --- | --- |
| Strict full-turn | `arena-control-full-turn-v1`; benchmark v1, full-turn prompt V1 by default; experiments also select V2 prompt/observation. |
| Structured stepwise | `arena-control-stepwise-v1`; step prompt V1, observation V2, plan schema V1; benchmark v2 probes and v3 full-match recipe. |
| Action-ID stepwise | [action_id.py](../backend/aig/arena/ai/action_id.py): `arena-control-stepwise-action-id-v1`; observation V3, step prompt V2, nullable action-ID schema; benchmark v4. |
| Constrained structured | [constrained.py](../backend/aig/arena/ai/constrained.py): `arena-control-stepwise-constrained-structured-v1`; subclasses step controller, with exact current-action wire-schema branches; benchmark v5. |
| Repair studies | `arena-step-repair-v1` / `arena-step-repair-v2` and action-ID repair contracts are separate. The product full-turn repair is the base provider's category-only feedback, not the stepwise Repair V2 experiment. |

`benchmark.run_suite` routes explicit `control_mode="stepwise"` to the separate runner and rejects incompatible full-turn options. Full-turn trials use `checked_plan` and the executor directly, not the interactive fallback controller. Dedicated full-match, repair, action-ID, constrained and friendly-fire runners have their own policies. Preserve them all.

## 3. Static rejection versus execution rejection

| Category | Current boundary | Proposed response |
| --- | --- | --- |
| A: invalid provider output | Strict JSON; exact fields/discriminators/types; at most five actions/five AP; current remaining-AP budget; owned actor; class ability; existing target and ownership/entity constraints; board positions. | Existing one static-output repair on the same observation/schema. Never consume an execution-replan slot. |
| B: statically accepted, execution-invalid action | Authoritative status, range, LOS, occupancy, path, current AP and other command preconditions. This includes **action 0** and actions already illegal at planning time. | Discard suffix; preserve prefix; one fresh-state replan when eligible. |
| Provider/infrastructure failure | Authentication, transport, refusal, malformed envelope, etc. | No static repair for these request failures; apply the selected failure policy. |
| Controller/domain defect | Unexpected exception, state corruption, impossible command-accounting mismatch. | Surface diagnostic failure; do not convert arbitrary defects into tactical replanning. |

Category B does **not** prove an initially legal action became illegal. The full-turn parser deliberately does not require first-action catalog membership. Historical rejection classification must separately record `first_action_initially_illegal`, `later_action_initially_illegal`, and `later_action_became_illegal` when reproducible evidence allows it.

AP above five is rejected by `ArenaTurnPlan` construction as `schema_validation`; a plan within five but above current remaining AP is `ap_budget`. A typed fake provider bypasses `parse_turn_plan` in the current interactive controller; the executor only structurally validates and checks AP sequentially. The new controller should explicitly reparse every candidate against its current observation to make fake/custom-provider behavior agree with model behavior. Built-in model providers already perform this validation.

The old benchmark error allowlist omits `transport_failure`, so some transport failures appear as `provider_exception`. Do not treat such failures or recorded request attempts as evidence that Ollama received inference. No connectivity diagnosis was needed or run here.

## 4. Proposed bounded-replan state machine

Use a separate application controller implementing `run_turn(simulation)`, with an immutable resolved policy. Do not add mode conditionals to providers, rules or individual browser actions.

```text
capture player-turn identity, starting AP, command offset
replans_used = 0
if terminal: refuse/stop before observation or provider
if AP == 0: EndTurn once; return

PLAN:
  fresh observation of current state using pinned observation version
  same provider, model, configuration and prompt
  normal static parsing + at most one static repair
  snapshot inference trace immediately
  if provider fails: selected failure policy; no execution-replan loop

EXECUTE SEGMENT:
  for each action, in order:
    stop immediately if terminal
    execute through authoritative simulation command sink
    on expected legality rejection:
      record failed action/index/reason, committed AP, current AP, whole stale suffix
      discard suffix
      if nonterminal and same player and AP > 0 and replans_used < limit:
        replans_used += 1
        go to PLAN
      otherwise: EndTurn once if nonterminal; return
  successful empty/short/full segment: EndTurn once if nonterminal; return
```

Default `max_execution_replans_per_turn=1`. Permit integer 0, 1, 2 for explicit development experiments; reject booleans, negatives and larger values. With limit 0, command outcomes should match strict mode for equivalent accepted inputs/failure policy, although the new trace version differs. Do not infer evidence for two replans from this audit: replacement success is unobserved.

An illegal first replacement action consumes the replacement opportunity despite spending zero AP. With limit one it ends the turn immediately; no third planning invocation, skipped action, heuristic substitution or rollback. The same rule applies to a later second failure. Empty/short replacement success ends the turn with unused AP. Replanning is recovery from execution rejection, not a loop to exhaust AP.

### Where to hook in without breaking source freezes

The semantic hook is **between the executor's rejection break and its automatic EndTurn**. There is no current public suspend/defer-EndTurn result. Simply wrapping `ArenaAiController.run_turn` or calling the existing executor repeatedly is wrong.

If source refactoring were unconstrained, extracting an `execute_plan_segment` primitive and retaining `execute_arena_turn` as the strict wrapper would provide the cleanest reuse. However, [Phase 8A preservation](../tests/fixtures/arena-phase8a-preservation.json) freezes the bytes of the executor, controller, session, factory, settings and API, and later preservation fixtures also protect shared providers/contracts. Updating historical expected hashes to accommodate the feature would erase that protection.

For the first implementation, prefer an **additive segment runner** in a new control module: reproduce the small iteration/attempt-recording boundary, but reuse `action_command`, authoritative `simulation.execute`, costs and state queries unchanged. It contains no movement, targeting, damage or tactical engine. Keep the old executor callable and byte-identical for strict research and parity tests. This modest orchestration duplication is preferable to a command sink that suppresses EndTurn while the old executor falsely records it as executed, or temporarily swapping/rolling back state. A later extraction is a separate source-versioning migration, not required for this mode.

## 5. AP, terminal handling and fallback

Every segment starts with actual current AP; never allocate a fresh five AP or subtract planned AP. Successful command costs alone spend AP; rejected commands spend zero. Capture `ap_unused` before the single final EndTurn. Total turn AP executed equals start AP minus pre-EndTurn/terminal AP, and equals the sum of committed action costs. Segment totals must sum to that total. Terminal leftover AP should be labeled separately from nonterminal unused AP in aggregates.

`ArenaObservation` V1 already serializes current `action_points_remaining` and reconstructs it losslessly; V2/V3 do too. Rebuilding recalculates current legal options. Its hash can legitimately remain unchanged after an action-0 rejection. Keep the same active player and round throughout replans; never build an observation after victory. A terminal command stops before any remaining action, replan or EndTurn, whether the winner is the acting team or its opponent.

Current product fallback catches `ArenaProviderError` and uses `HeuristicArenaTurnProvider` V1. It does not fall back on execution invalidity. Preserve that distinction in the new mode:

* Interactive provider/static-repair failure, initial or replacement: build a heuristic V1 plan from the **current remaining state**, commit it as a final fallback segment and then end if nonterminal. Mark the entire turn mixed-provider. Never restart the original turn or re-enter model replanning after fallback.
* Exhausted execution-replan budget: preserve the valid prefix and end, without fallback.
* Strict experiment: provider failure records a failed trial and preserves the prefix according to the new explicitly frozen runner policy; no heuristic. Request ceiling/source/replay defects hard-stop. Specify whether ordinary provider failure aborts the remaining schedule in the new recipe; do not inherit this accidentally.

Keep fallback version explicit; the browser's separate Heuristic V2 button does not make V2 the current Luna fallback. Report model-executed and fallback-executed AP separately. Unexpected programming exceptions remain visible.

## 6. Prompt and observation compatibility

Verified browser chain: `ArenaWebSession.observer_demo` / Human vs OpenAI -> `demo(provider="openai")` -> full-turn factory -> `OpenAIArenaTurnProvider` default -> **`arena-turn-prompt-v1` and `arena-observation-v1`**. No browser prompt override is currently passed. `tests/test_arena_friendly_fire.py::FriendlyFireTests::test_browser_actual_baseline_without_inference` explicitly covers this. Environment strategy-prompt selection is an Empire setting and does not change the Arena prompt.

Exact V1 wording in [prompts.py](../backend/aig/arena/ai/prompts.py):

> You have up to 5 shared Action Points, bounded by action_points_remaining.

Therefore no AP wording or schema change is required for remaining AP 1–4. `ArenaTurnPlan` is still a maximum-five-AP container; observation-relative parsing supplies the smaller bound. Reuse the full-turn prompt unchanged in the first strict-versus-bounded comparison, pinning its hash, to isolate control policy.

There is a semantic caveat: V1 also says an illegal action truncates the plan and ends the turn. That remains a conservative planning instruction but is no longer a literal description of recovery in the bounded mode. Document this deliberate frozen-prompt ablation; do not claim the text perfectly describes the new controller. If later product wording must describe recovery exactly, add a distinct prompt (for example `arena-turn-prompt-bounded-replan-v1`) replacing only that sentence with “An illegal action discards the remaining plan; prior actions remain committed. The controller may request a new plan from the updated observation.” Keep AP wording and tactical content unchanged, and evaluate it separately.

Each replan should initially receive fresh state **only**, without the failed plan, stale suffix or prior conversation. The base provider already builds fresh message lists per invocation and OpenAI uses no previous-response linkage. Static repair within that invocation remains same-state feedback. No chain-of-thought request is needed. Adding factual rejection context later is another explicit experiment: it could help action-0 repetition but changes the input contract.

Fireball behavior tuning remains an orthogonal prompt axis. A future behavior prompt can be injected through a provider factory/registry extension while retaining the identical bounded controller. Never silently attach current friendly-fire experimental prompts or wire constraints to this investigation.

## 7. Request bounds and telemetry

With R execution replans and one static repair per planning invocation:

```text
planning invocations <= 1 + R
static repairs <= 1 + R
model request attempts <= 2 * (1 + R)
```

For R=1: normally one request, two when replanning without static repair, **at most four attempts** with both static repairs. For R=0/2 the respective maxima are two/six. A provider request failure exits that invocation immediately; transport retries stay zero. Heuristic fallback adds no model calls.

Use the base provider's existing `before_request` hook to reserve budget before each attempt, including repairs. Add a turn-scoped budget and, in research, a run-wide budget including separately counted preflights. Denied reservations are not requests and must not trigger fallback or repeated reservation loops in strict research. Bind hooks through an additive provider wrapper/factory; do not edit the frozen provider loop. Test initial + repair + replan + repair explicitly.

Existing inference traces retain only the latest invocation. Copy `last_trace` after **every** initial/replacement/failure call before the next invocation overwrites it. Existing `attempts`, `retry_count`, wall time, prompt/schema/configuration/observation provenance and token metrics are reusable. Some recorded attempts precede local credential failures and are not network calls. Report `planning_invocations`, `request_attempts` and, if instrumented at transport dispatch, `transport_requests` distinctly; historical comparisons below use retained attempt counts.

New suggested `arena-bounded-replan-turn-trace-v1`, with ordered `segments` and stable player-turn ID `(match_id, player_id, turn, starting_command_index)`:

| Level | Required fields |
| --- | --- |
| Turn | Control version, limit, provider/fallback policy, start/end command offsets, starting AP, total model/fallback executed AP, unused AP, terminal result, stop reason, elapsed time. |
| Segment | Index and initial/replan/fallback purpose; fresh observation/hash/version; plan/hash; planned AP; AP before/after; inference snapshot; attempts and static repairs; provider/config/prompt provenance; commands and committed action count. |
| Failure boundary | Failed action, local index and turn action offset, rejection reason/category, AP spent before failure, AP remaining, discarded suffix, eligibility and why a replan was/was not started. |
| Aggregate turn counters | Initial requests, initial repairs, replan invocations/requests/repairs, execution-invalid count, first invalid index, replacement AP planned/executed, second invalidity, total provider attempts. |

Keep runtime-only control metadata outside `arena-snapshot-v2` and command replay. Public DTOs need recursive allowlisting: today's `_public_state` only strips `inference.attempts` at one level. Nested segments must not expose raw content, credentials, rejection echoes or model reasoning. Expose concise control/fallback/AP summaries and normal action events.

Primary metric: sum of request attempts divided by **started model-assigned player turns**, including failed/fallback-contaminated starts. Also publish a pure-model subset and successful-turn subset, with denominators. Do not divide by global round counter or number of actions. Preflights and unstarted turns are separate.

Aggregate requests/turn; fraction needing replans; distribution of one/two/three/four requests; repairs separately from replans; percent replacement segments accepted/executable; repeat-invalidity rate; mean AP executed and terminal/nonterminal unused AP; tokens/cache usage, total provider seconds and end-to-end turn latency. “One request” must not mean “one planning invocation with an uncounted repair.”

Define local AP recovered as model AP committed after the first execution rejection, excluding fallback. Historical AP remaining is merely an upper opportunity bound, not recovered AP. Actual match-level improvement requires new trajectories. Price token totals only with a dated explicit pricing artifact; unknown usage or prices remain null. Cache-sensitive dollar savings cannot be inferred from request counts alone.

## 8. Historical trigger and request estimates

Counts below were recalculated from retained `plans.jsonl`, `inference.jsonl`, saved observations and manifests, not inferred from prose reports. Zero-based invalid-action indices and AP distributions are retained in the audit JSON. “No B” refers to accepted plans only; failed static output is not a clean executed turn.

| Cohort | Started model turns | Accepted | No B | B / eligible replans | Static repairs | Existing attempts | Attempts with one extra per eligible boundary |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna V1 full matches, prompt/obs V1 | 102 | 100 | 28 | 72 | 10 | 112 | 184 |
| Luna V1 probes, prompt/obs V1 | 28 | 28 | 24 | 4 | 1 | 29 | 33 |
| Luna Phase 6B probes, prompt V2/obs V1 | 28 | 28 | 24 | 4 | 0 | 28 | 32 |
| Luna Phase 7A probes, prompt V2/obs V2 | 28 | 28 | 20 | 8 | 0 | 28 | 36 |
| Qwen V1 full matches, prompt/obs V1 | 30 | 22 | 0 | 22 | 8 | 38 | 60 |
| Qwen Phase 6B probes, prompt V2/obs V1 | 9 | 8 | 8 | 0 | 1 | 10 | 10 |
| Qwen Phase 7A probes, prompt V2/obs V2 | 28 | 28 | 28 | 0 | 0 | 28 | 28 |

Qwen Phase 6B is a partial collection, not 28 completed turns. The eight Qwen and two Luna full-match provider failures are `repair_failed`, separate from execution rejection. Full-match evidence includes retained failed/limited prefixes; these counts are not a census of completed matches.

### Luna full-match details

Trigger rate: **72% of accepted turns**, or 72/102 = **70.59% of all started model turns**. Invalid indices: `{0:6, 1:29, 2:32, 3:4, 4:1}`. AP remaining at rejection: `{1:2, 2:18, 3:33, 4:13, 5:6}`. All 72 boundaries were nonterminal with positive AP. Total AP there: **219**, compared with 260 AP actually executed across the 100 accepted plans.

Reasons: range 24, Fireball range/board 16, ACTIVE/DOWNED status 11, movement legality 11, LOS 9, inactive actor 1. These are engine failure reasons, not tactical quality scores. The [prior postmortem](arena-v1-postmortem.md) further classified 13 rejected actions as initially legal then invalidated and 59 as initially illegal and never made legal; the new trigger policy covers both and must not label all 72 as self-invalidating sequences.

Holding each saved turn boundary fixed, existing attempts are 112/102 = **1.098/turn**. Add 72 fresh planning attempts: **1.804/turn**. If every one also needs a static repair, **2.510/turn**. Initial static repairs are already included. Ignoring all repair/failure overhead and conditioning only on accepted starts yields 1 + 72/100 = **1.72 planning invocations/turn**.

These are local counterfactual counts, not a predicted full-match trajectory: recovered actions change later observations, victories, total turns and failure rates. They do not support promising 1.2–1.5 calls/turn for current browser V1.

### Probe estimates and comparison with stepwise

Luna V1 probes: invalid indices `{1:3, 4:1}`, AP `{1:1, 4:3}`; 13 AP opportunity; projected **1.179 attempts/turn**, or 1.321 if every replan repairs. Phase 6B: indices `{1:2, 2:2}`, AP `{3:2, 4:2}`; 14 AP opportunity; **1.143–1.286** attempts/turn. Phase 7A: indices `{1:4, 2:4}`, AP `{2:4, 3:1, 4:3}`; 23 AP opportunity; **1.286–1.571** attempts/turn. The latter's trigger rate is **28.57%**.

The analyzer separately reads Phase 7C stepwise turn traces: Luna **89 attempts / 28 turns = 3.179** (88 decisions + one repair), Qwen **100 / 28 = 3.571**, excluding preflights. Both executed 112 AP. Comparing Luna's matched-fixture Phase 7A local projection of 36–44 attempts to the later observed stepwise 89 suggests **50.6–59.6% fewer attempts** if the replacement request assumptions hold. This is a request-volume scenario, not measured hybrid performance or a dollar/latency saving. Stepwise necessarily uses a different prompt and changes within-turn feedback. Collection time and replacement effectiveness remain uncontrolled. See [expanded stepwise results](arena-stepwise-expanded-results.md).

### Qwen interpretation

All 22 accepted V1 match plans fail at action index 0, range rejection, with **five AP remaining and zero AP spent**. These are Category B, not static-output failures; the other eight failed invocations are Category A repair exhaustion. The proposed mode would request 22 replans, but the unchanged observation and deterministic configuration give no reason to assume recovery. Its local count becomes **2.000–2.733 attempts/started turn**, with 110 AP opportunity and no demonstrated recovered AP.

Conversely Phase 7A Qwen has zero execution failures and only 36 AP executed over 28 turns. Short accepted plans are the limitation there. The proposed invalidity-only trigger deliberately does nothing to those short turns. Do not sell bounded replanning as a general solution to Qwen's low AP use.

## 9. Settings and browser design

Keep provider and control as separate axes. Proposed external values follow existing benchmark hyphenation:

```text
AIG_ARENA_CONTROL_MODE=full-turn|full-turn-bounded-replan|stepwise
AIG_ARENA_MAX_EXECUTION_REPLANS_PER_TURN=1
```

Resolved immutable policy contains mode, control version and an applicable limit. Strict mode resolves to zero; stepwise has no execution-replan limit. Reject an explicitly supplied limit for a non-bounded mode rather than silently ignoring it. Expose 0/1/2 only to development configuration; normal Adaptive UI needs no numeric control. Stepwise remains development-only until a product-safe implementation exists; declaring a value does not justify wiring the research runner into gameplay.

Current settings precedence in [settings.py](../backend/aig/settings.py) is nonempty process environment > local `.env` > committed defaults. `AIG_ARENA_TURN_PROVIDER` is separate from Empire. `/demo-ai/configured` resolves that selector; explicit provider routes override it, and `/demo-ai` remains heuristic. There is currently no control setting, prompt setting or session override for Arena control.

Because `settings.py` and base APIs are source-frozen, implement new gameplay configuration loading in an additive module at the web boundary. Initially support process environment and explicit session payload, documenting that scope. **Do not put unknown `AIG_` keys into the existing `.env`: its loader rejects them.** If `.env` parity is required, a new gameplay settings loader must parse/filter its own keys and feed legacy keys through the unchanged loader with equivalent precedence; this needs dedicated validation, not a quiet change to the frozen settings file. A separate gameplay config file is another simpler opt-in during experimentation.

Add a web-only match-creation options route/payload, for example `POST /api/arena/gameplay/demo` with provider/match mode and `control={mode,max_execution_replans_per_turn}`. Keep existing routes and omitted options on strict defaults. Browser session override > gameplay environment/default. Resolve and freeze policy at match creation, return a sanitized `ai_control` DTO, and retain it on New Match and observer resets. Avoid mid-turn/global mutable selection.

The current server stores one shared Arena session on `app.state`; this is per-match configuration on that server session, **not per authenticated user or independent browser tab**. True multi-session isolation is separate work. A single mode for both model-controlled observer sides is adequate initially; per-side control belongs in explicit research assignments.

Suggested labels: **Adaptive — Replan when blocked**, **Fast — Plan the whole turn**, **Careful — Re-evaluate after each action**. Initially place Adaptive under experimental settings and Careful under Development; strict stays selected. Fast is a description of request strategy, not a latency guarantee. Keep version IDs in diagnostics, not the main play UI.

## 10. Browser latency and presentation

`ArenaWebSession.execute` captures event offset, calls the entire underlying execution, then returns `presentation.events`. `observer_turn` similarly runs exactly one full AI turn before returning. Frontend `arena.js::run` awaits the response before `engine.play(presentation, authoritative)`. Controls show “AI thinking…” during the wait and “AI acting” during playback. No inference is driven by animation frames or separate per-action browser requests.

Bounded replanning can therefore happen entirely server-side. The response contains one coherent action sequence spanning all successful segments and one final EndTurn, with no failed-action animation. Replan latency increases waiting before **any** animation, including the human command event in a combined response. The session lock is held across inference today; two planning calls and possible repairs lengthen that hold.

Measure total waiting and p95 latency alongside provider seconds. Do not implement streaming for the first experiment. Later incremental playback would need a separate synchronization/cancellation design. Existing request-generation checks protect UI presentation against stale responses but do not undo server-side committed commands; do not add automatic whole-turn retries after a browser timeout.

## 11. Versioning and implementation sequence

Preserve current control IDs, prompt hashes, model profiles, observation/plan schemas, rules, commands, snapshots, replay and frozen benchmark recipes v1–v5. Source preservation fixtures and methodology manifests also pin bytes; semantic equivalence alone is insufficient. Do not rewrite historical manifests, failures, source hashes or golden expectations.

Use `arena-control-full-turn-bounded-replan-v1` and a separately frozen recipe, provisionally **`arena-benchmark-v6`** (next available numbered recipe in this checkout). A new benchmark version is necessary because planning count, failure handling, turn telemetry and request ceilings change. Add a new registry/runner entry point if extending the frozen registry would invalidate preservation. Record control, limit, static-repair policy, fallback policy, prompt and observation hashes, model configuration, source manifest and run-level ceilings. Do not relabel results as benchmark v1 or stepwise v2.

Likely future files, with preferred additive boundaries:

| Work | Files |
| --- | --- |
| New policy, segment execution, turn aggregation | New `backend/aig/arena/ai/bounded_replan.py` and optionally `control.py`; reuse contracts/observation/commands, retain existing executor/controller unchanged. |
| Product factory/config/session extension | New gameplay control/config module; integrate through `gameplay.py` and `web.py`, auditing their own applicable freezes before edits. Avoid modifying frozen `factory.py`, `application.py`, `api.py`, `settings.py`. |
| Research runner and recipe | New `bounded_replan_benchmark.py`, additive recipe v6 and provenance/verification support. Preserve existing runner semantics. |
| UI options and DTO | `frontend/src/js/api/arena.js`, `frontend/src/js/arena.js`, relevant frontend tests; maintain event playback engine. |
| Metrics | New turn/segment metrics module using existing inference numeric fields; new nested public trace sanitization. |
| Tests/docs | New bounded controller/API/benchmark tests, existing preservation/parity tests, this design and a later implementation report. |

Implementation order: freeze the explicit contract and budgets; implement offline controller/segment primitive; verify strict parity and replay; add provider accounting/failure policy and DTO sanitization; add experimental gameplay/session selection; add separate benchmark recipe; only then consider live validation. Existing provider repair, plan schema and prompts need no changes for the initial ablation.

## 12. Deterministic offline test plan

Use scripted fake providers and fake transports; block network. Existing tests in `test_arena_ai.py`, `test_arena_providers.py`, `test_arena_stepwise.py`, `test_arena_observation_v2.py`, `test_arena_observer.py` and presentation/playback suites supply fixtures and baseline assertions. Add meaningful behavioral cases:

| Case | Assertions |
| --- | --- |
| Legal five-AP plan | One invocation, zero replans, five AP committed, one EndTurn. |
| Mid-plan failure | Two successful commands remain; rejected action and every suffix action absent from replay; fresh observation reflects movement/damage and remaining AP; second provider invocation executes replacement. |
| Initial action 0 invalid | Zero AP spent, same observation hash allowed, one replan; no assumption that new state must differ. |
| Replacement action 0/later invalid | Correct prefix retained, budget consumed, no third invocation at R=1, one EndTurn and two distinct failures recorded. |
| Initial/replacement static invalidity | Existing repair receives same segment observation; it does not increment execution-replan count. Four-attempt worst case accepted; fifth reservation denied. |
| Provider failure | Initial and replacement transport/static exhaustion; interactive V1 fallback starts from current AP; strict fails without contamination; no execution-triggered heuristic. |
| Empty/short initial or replacement | One final EndTurn, exact unused AP, no “fill AP” request. |
| Terminal | Core destruction, last ACTIVE elimination, friendly-fire opponent win and victory before stale suffix; no EndTurn or later call. |
| Zero AP | No request, one nonterminal EndTurn; segment failure at zero AP cannot replan. |
| Limits 0/1/2 | Command parity with strict for limit zero; exact invocation/repair ceilings; reject invalid config combinations. |
| AP and state | Remaining AP 1–4 observation roundtrip and static rejection above remaining budget; failed command leaves state hash unchanged; all segment AP reconciles before EndTurn reset. |
| Telemetry | Preserve both inference snapshots, distinct repair/replan counters, command offsets, initial/replacement/fallback provenance, secrets/raw text absent from browser DTOs. |
| Determinism/replay | Repeat fake-provider turns yield identical commands; replay only committed commands to identical final snapshot/counters independent of inference traces. |
| Browser/session | Both human-vs-Luna and observer opt-in selection; one event batch; blocked controls; New Match preserves policy; omitted options strict; two tabs documented as one shared session. |
| Frozen compatibility | Existing byte/hash fixtures and strict full-turn/stepwise tests unchanged; no golden hash updates to hide drift. |

## 13. Future experiments and default migration

First compare strict and bounded with identical full-turn prompt, observation, model/profile, repair setting, scenario and probe fixtures. Use prompt/observation V1 for the browser baseline; a separate V2/V2 cohort can connect to the Phase 7A/7C evidence. Do not pool them.

Stepwise must use its frozen step prompt and Observation V2: **a three-way comparison with the exact same prompt is incompatible with the existing stepwise contract**. Present strict-versus-bounded as the control-only ablation, and stepwise as a separate feedback/task-contract comparison. Match model/settings, rules, probe states and full-match assignments; disclose the prompt/observation differences. Do not redefine stepwise to satisfy a nominal “same prompt” condition.

Freeze the future recipe before collection: predetermined probe repetitions, side-swapped match schedules, explicit turn/run request ceilings, preflight counts, transport retries zero, static repair one, R=1, no fallback, trial-failure/abort rules and preservation requirements. Report completion, failures/unstarted trials, executed AP, requests per started turn, trigger/recovery rates, latency/tokens/cache/cost where known, and tactical outcomes. Preserve all failures; no replacement trials or opportunistic retries.

Conservative rollout, each live stage separately authorized:

1. Complete fake/offline controller, accounting, presentation and replay checks; deterministic heuristic/fake match exercises with no model construction.
2. One explicitly bounded Luna smoke **turn**, with a ceiling of four attempts if both repairs are enabled. If no natural rejection occurs, it validates only the non-replan path; do not force extra live calls to hit coverage already supplied offline.
3. Small frozen tactical-probe comparison, then a modest predetermined Luna-vs-Heuristic side-swapped schedule. For future Qwen failures follow workspace read-only connectivity diagnosis before interpreting very fast failures; that diagnosis does not authorize retries.
4. Explicit manual browser observer and human play, checking waiting time, animation coherence and fallback visibility.
5. Consider promoting Adaptive for new Luna gameplay matches only if it recovers useful AP/tactical outcomes at acceptable request/latency cost without accounting/replay failures. Retain strict selection and research defaults permanently; do not migrate existing sessions silently.

**Recommendation:** bounded replanning is a reasonable candidate for the normal playable Luna mode, especially for committed-prefix failures. It is not ready for promotion based on historical trigger counts alone. No implementation or live validation is authorized by this report. Stop here.
