# Guaranteed bounded recovery smoke

Preparation is offline only. No OpenAI or Ollama calls, preflight, paired benchmark,
full match, or extra turn are part of preparation. Live execution requires separate
authorization for the exact command below, with a hard ceiling of **two Luna attempts**.

The previous normal Luna smoke already established real initial planning. This
diagnostic scripts the initial provider wave to guarantee execution invalidity,
then delegates the partial turn to the configured real OpenAI ArenaTurnProvider.
It tests recovery mechanics and provider compatibility, not tactical quality or
the frequency with which Luna produces self-invalidating plans.

## Frozen fixture and committed prefix

Uses `frozen_probe('snipe_vs_basic')` from `arena-probes-v1`, unchanged:
blue Ranger `actor` at (1,2), red Mage `enemy` at (5,2), ACTIVE with 8 HP,
and red Knight `enemy2` at (2,1). Initial AP is 5.

The normal parsed ArenaTurnPlan contains:

1. Snipe `actor` -> `enemy` (2 AP).
2. Snipe `actor` -> `enemy` (2 AP).
3. Attack `actor` -> `enemy2` (1 AP).

All actions are individually legal at the starting state; references, abilities,
schema, ownership, and the 5-AP total pass normal static validation. Static
validation intentionally does not simulate status changes through the sequence.

The first Snipe commits, changing the Mage from ACTIVE/8 HP to DOWNED/0 HP.
The second Snipe is rejected with **`invalid target ACTIVE/DOWNED status`**.
The rejected action spends no AP. Exactly 2 AP have been spent and 3 remain.
The controller discards two stale actions including the rejected action; the
strictly unattempted suffix is one action. No EndTurn precedes recovery.

The fresh observation retains all positions and all other unit state. Its actor
action catalog removes `enemy` from Snipe targets. Attack and Snipe against
`enemy2` remain available. Attack against the Mage was already out of range;
Finish against the Mage remains absent because it is out of range.

| Observation | SHA-256 |
| --- | --- |
| Initial | `ffa311c4814951210c385ee9ec044a20f2b0ca6f0bf4b9855796b053c4017448` |
| Recovery, 3 AP | `912307622e37807b66705c9cdacbcb25f5f0c62aa852fb670e09c11722c962f9` |

## Delegation and bounds

`ScriptedFirstWaveThenDelegateProvider` is diagnostic tooling in
`backend/aig/arena/bounded_replan_recovery_smoke.py`. It returns the scripted plan
at the ordinary provider abstraction for wave 1. The unchanged controller parses
the plan again and executes through ArenaSimulation's authoritative command sink.
Wave 2 calls the existing delegate's `create_turn_plan` with the controller's
fresh ArenaObservation. The real delegate retains `arena-turn-prompt-v1`, normal
schema/static validation, remaining-AP validation, and one normal static repair.

The wrapper inherits the model provider marker so the controller installs its
existing request accounting hook. It forwards that hook to the delegate and adds
an independent two-attempt reservation limit before transport. Wave 1 has zero
reservations. Wave 2 permits one request plus one static repair; a third
reservation is rejected. The wrapper also rejects a third planning wave.
Hooks are restored afterward. SDK configuration retains `max_retries=0`.

The frozen profile is `luna-config-v1`: `gpt-5.6-luna`, reasoning `none`,
512 output tokens, store false, zero SDK retries. The live runner checks the
configured profile, prompt version, enabled repair, and source hashes. Before
each request it verifies the entire expected observation and committed command
prefix. No inference is used to create or verify the fixture.

Fallback is disabled only for this diagnostic. Exhausted static repair fails the
smoke and preserves the prefix without EndTurn, following existing controller
behavior. Execution invalidity triggers execution replanning, not static repair.
A second execution invalidity ends the turn with no further plan. Victory skips
EndTurn. The ordinary controller's `model_ap_executed` includes the scripted
prefix because the wrapper carries the model marker; use `ap_recovered` for AP
executed from Luna's replacement, and per-wave request counts for inference.

## Offline verification

Run from `C:\code\aig`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_arena_bounded_replan*.py' -v
```

24 tests passed (16 existing plus 8 diagnostic). New tests block socket connections
and use a fake transport inside the real OpenAI provider validation/repair loop.
They cover starting legality, committed prefix, exact fresh observation delivered
in the prompt, suffix discard, no early EndTurn, 3-AP acceptance and 4-AP rejection,
one static repair, exhausted repair and transport failure, refusal of a third
reservation, second execution invalidity, terminal replacement, exact command
replay, artifact production, and refusal to rerun an existing live evidence root.
The terminal edge test lowers Knight HP only in its offline test copy; the live
fixture remains unchanged.

Preparation evidence is under `.local/arena-recovery-preparation/`. The preserved
file inventory includes all pre-existing tracked/untracked nonignored files and
the prior `.local/arena-bounded-luna-smoke-01/` evidence. Byte hashes are compared
after preparation. Production controller, strict full-turn, stepwise, executor,
contracts, observation, prompt, profiles, heuristics, Arena gameplay, Empire,
and both existing bounded-replan design/implementation documents are untouched.

## Artifacts and future command

Offline preparation creates the new root with:

```powershell
.\.venv\Scripts\python.exe -m aig.arena.bounded_replan_recovery_smoke prepare --output .local/arena-bounded-luna-recovery-smoke-01
```

`manifest.json` freezes sources, profile, fixture observation hashes and scripted
plan. `initial-state.json`, `scripted-plan.json`, `initial-execution.json`, and
`replan-observation.json` contain offline expected evidence. `preparation.json`
explicitly labels it offline, with zero live requests. No live result is claimed.

**Prepared future live command; do not execute without authorization:**

```powershell
.\.venv\Scripts\python.exe -m aig.arena.bounded_replan_recovery_smoke run --output .local/arena-bounded-luna-recovery-smoke-01 --live
```

This performs one scripted initial wave and one real partial-turn Luna planning
wave, at most two provider attempts including static repair. No preflight, other
retry, full match, extra turn, or benchmark follows it. A source mismatch requires
new preparation and review. An exclusive `live-started.json` prevents reruns;
failed evidence is preserved and a separately authorized retry needs a new root.

Live output adds `luna-inference.jsonl` (sanitized provider trace),
`replacement-plan.json`, `command-trace.jsonl`, `commands.json` (repository-native
replay envelope), `final-state.json`, `offline-verification.json`, and `report.json`.
The actual recovery observation is saved before transport and checked against
the offline expected observation. Final/partial command evidence is saved even
if an unexpected runner failure occurs after controller entry.

A pass requires the expected invalidity/prefix, exactly one replan, exact fresh
observation, one or two provider attempts with no fallback, an accepted replacement
within 3 AP executing at least one action, correct turn termination, unchanged
sources, and exact replay including final state. An empty replacement fails.
The report distinguishes a later replacement execution invalidity from a clean
completion (`stronger_pass`); terminal victory is also a clean completion.
No particular tactical choice is required. A live result is still pending.
