# Arena Phase 7B: stepwise tactical control

2026-09-13. Offline implementation and preparation only. No Ollama, OpenAI,
external-service calls, model preflights, model probes or live full matches were
run. Tests use fake providers; the reference uses the deterministic local
heuristic. Live execution requires separate authorization.

## Motivation and controls

[Phase 7A](arena-observation-v2-probe-results.md) obtained 28/28 valid Qwen plans
with legal first actions and no repairs, but every plan still contained one action.
Luna had eight execution truncations; seven involved legality changed by earlier
actions. See the [V1 postmortem](arena-v1-postmortem.md) and
[Prompt V2 results](arena-prompt-v2-probe-results.md).

Compare each model against its own full-turn Prompt V2 / Observation V2 control.
Stepwise changes feedback frequency and the prompt needed to define that task;
this is not a controller-only change with identical instructions. State information,
complete legal catalog, rules, seven `arena-probes-v1` fixtures, `qwen-config-v1`
and `luna-config-v1` stay fixed. Repeated fixed states do not establish general
playing strength. Stepwise remains a separate experimental mode.

## Architecture and contracts

| Dimension | Full-turn experiment | Stepwise experiment |
| --- | --- | --- |
| Control | `arena-control-full-turn-v1` | `arena-control-stepwise-v1` |
| Methodology | `arena-benchmark-v1` | `arena-benchmark-v2` |
| Prompt | `arena-turn-prompt-v2` | `arena-step-prompt-v1` |
| Observation | `arena-observation-v2` | `arena-observation-v2` |
| Schema | `arena-turn-plan-schema-v1` | Same unchanged schema |
| Decision | 0..5 actions within five AP | Zero or one action |
| Feedback | After planned sequence | After every executed action |

`ArenaTurnPlan` already accepts an empty tuple, serialized as `actions=[]`.
No new schema is necessary. In stepwise mode zero actions explicitly ends the
turn; one executes then observes again; multiple actions fail static validation.
Schema v1 itself still permits five actions. Stepwise additionally requires exact
canonical JSON membership in the current `legal_actions` catalog. Wrong actors,
reconstructed targets, range violations and stale actions are rejected without
approximate matching. Model output is never silently sliced.

The separate `ArenaStepProvider.create_step(observation)` protocol has Ollama,
OpenAI and heuristic implementations in [stepwise.py](../backend/aig/arena/ai/stepwise.py).
Model step providers deliberately reject `create_turn_plan`. They reuse existing
transport, extraction, settings, telemetry, redaction, schema transport and bounded
repair code. The shared base gained three dispatch hooks: prompt resolution,
parsing and repair feedback. Their full-turn defaults preserve prior behavior and
repair text. No transport code was copied. Full-turn adapter, executor, controller
and heuristic files are unchanged by this phase.

The immutable, separate `STEP_PROMPTS` registry contains `arena-step-prompt-v1`.
It requests one action now, copied as a complete catalog entry, describes fresh
feedback and the empty stop form, supplies factual AP costs, and requests no
reasoning. It has no tactical priorities or instruction to spend all AP. The
frozen V2 label `legal_actions_state=turn_start` remains intact; the step prompt
explains that the catalog belongs to the current observation.

`ArenaStepController` builds V2, requests and validates one decision, executes one
command through `ArenaSimulation.execute`, then rebuilds V2. One- and two-AP costs
update before the next request. AP zero ends locally without a call. Empty output
executes `ArenaEndTurn` and retains pre-EndTurn unused AP. Victory stops immediately
without further calls or EndTurn. At most five decisions occur per turn, including
an explicit stop decision; positive action costs make a sixth call unnecessary.

Static invalidity permits one repair on the same observation, with factual feedback
requiring zero or one complete current-catalog action. Failed repair ends the turn,
without fallback, and aborts the schedule. A catalog-member execution rejection is
`catalog_execution_defect`: preserve the exact command prefix and stop without
further commands. It is a harness/domain defect, not model sequencing failure.
V2 retains the known `transport_failure` category instead of V1's historical
allowlist masking. Browser orchestration and gameplay defaults remain unchanged.

## Benchmark, trace and replay

[stepwise_benchmark.py](../backend/aig/arena/stepwise_benchmark.py) implements probes
only, selected by `--control-mode stepwise --mode probes`. Incompatible prompt,
observation, model profile, match or side-swap options fail before inference.
Existing V1 commands retain their defaults. Future manifests explicitly record
control identity; historical manifests are not rewritten. The new v2 recipe is an
independently integrity-checked JSON artifact.

Trial files are `manifest.json`, `turn.json`, `command-trace.json`,
`final-snapshot.json`, `verification.json` and `result.json`. Manifests include
source revision/dirty state, source-file inventory/hash, recipe, prompt,
observation/schema, model/profile, probe identity and optional pricing hash.

Every detached step includes trial, player turn/index, AP before/after, complete
observation/hash/version, legal count, requested/actual provider, model, prompt and
schema versions, accepted decision, selected action/current membership, explicit
stop, first-response validity, repair success/count, sanitized attempts, latency,
tokens/cache counts, command index, resulting state hash and terminal status.
Rejected arbitrary model text and chain-of-thought are not persisted. Rejected
responses have null accepted decisions; errors and numeric telemetry remain.

Turn aggregates contain requested steps, executed action sequence/count, available,
spent and unused AP, explicit stop, failures, repairs, requests and latency.
Summary reliability includes failed turns; valid-turn comparisons are separate.
Tactical outcomes reuse Revive, Winning Core and Team Elimination predicates.
Other probes retain mechanical facts without invented binary objectives or a
weighted tactical score.

Replay uses only executed commands. Verification independently checks every command,
metric and state hash, then reconstructs per-step observations, memberships,
command associations, AP and EndTurn boundaries with no provider. Failed prefixes
also replay. Tampered observations, selected actions, command indices or AP fail.

## Latency, tokens and cost

Compare **total provider latency and tokens/cost per player turn**, with per-decision
values alongside. Repairs count toward both; preflight stays separate. Record
calls/requests per turn and AP, repair rates/success, first validity, turn failure,
selected-current legality and early stopping. Ollama occupancy uses actual reported
input/output and the unchanged context size. No context/cache optimization is added.

Luna cached/uncached input, output and estimated cost sum every attempt in each
decision and turn. Missing usage remains null. `--pricing PATH` accepts exactly:
`model`, `as_of` (ISO date), `source`, `input_usd_per_million`,
`cached_input_usd_per_million`, and `output_usd_per_million`. Rates must be finite,
nonnegative and model-matched. Cost is
`(uncached*input_rate + cached*cached_rate + output*output_rate)/1e6`.
Completed-turn cost distributions exclude failed turns, whose evidence remains.

No frozen Arena pricing existed and external lookups are forbidden in this phase.
No real Luna price is invented. Supply explicit dated pricing before a live run
intended to report dollar estimates; otherwise cost is explicitly null. Cost tests
use synthetic rates. There is no automatic pricing lookup.

## Offline heuristic reference

The adapter runs the unchanged detached full-turn heuristic on current state,
takes its first action and reconsiders after execution. Its per-plan visited-position
history resets, so this is a distinct deterministic reference, not a claim of
identical full-turn behavior or a retuned policy.

The [retained final baseline](../.local/arena-phase7b-preparation/heuristic-baseline-final/summary.json)
has seven exact replays and zero provider requests, repairs or failures.

| Probe | AP used / unused | Actions / decisions | Existing objective |
| --- | ---: | ---: | --- |
| Finish or Core | 5 / 0 | 5 / 5 | No binary objective |
| Fireball friendly fire | 5 / 0 | 4 / 4 | No binary objective |
| Revive decision | 5 / 0 | 4 / 4 | Ally active |
| Shield Bash position | 5 / 0 | 5 / 5 | No binary objective |
| Snipe versus basic | 5 / 0 | 4 / 4 | No binary objective |
| Team elimination | 1 / 4 | 1 / 1 | Victory |
| Winning Core line | 1 / 4 | 1 / 1 | Victory |

Totals: 24 actions/decisions, 27 AP, eight unused AP due to two immediate victories.
Exact sequences/hashes are retained in artifacts. The frozen full-turn reference
is not replaced.

## Future live commands — not executed

Recommend **one trial per probe per provider first**, then review continuation/AP,
legality, tactical outcomes and whole-turn latency/tokens/cost. Heuristic behavior
shows a material request multiplier (24 decisions across seven turns), but does not
predict either model's request count.

| Per-provider schedule | Max initial trial calls | Including repairs | Including one unrepaired preflight |
| --- | ---: | ---: | ---: |
| 7 probes × 1 trial | 35 | 70 | **71** |
| 7 probes × 4 trials | 140 | 280 | **281** |

Both-provider ceilings: **142** for the pilot; **562** for four trials. The runner
rejects a schedule exceeding `--request-ceiling` before provider construction,
aborts on the first failed preflight/turn, and does not reuse capacity for retries,
continuations or replacement trials.

Proposed pilot commands from `C:\code\aig`, after separate authorization:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --control-mode stepwise --mode probes --blue-provider ollama --prompt-version arena-step-prompt-v1 --observation-version arena-observation-v2 --probe all --probe-trials 1 --request-ceiling 71 --output .local/arena-phase7b-qwen-stepwise-pilot-01
.venv/Scripts/python.exe -m aig.arena.benchmark --control-mode stepwise --mode probes --blue-provider openai --prompt-version arena-step-prompt-v1 --observation-version arena-observation-v2 --probe all --probe-trials 1 --request-ceiling 71 --output .local/arena-phase7b-luna-stepwise-pilot-01
```

For a priced Luna report, append `--pricing .local/arena-phase7b-luna-pricing.json`
after supplying the dated model-matched file. None has been fabricated or fetched.
Without that flag, dollar costs are explicitly null.

Prepared four-trial commands, **not recommended as the initial run**:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --control-mode stepwise --mode probes --blue-provider ollama --prompt-version arena-step-prompt-v1 --observation-version arena-observation-v2 --probe all --probe-trials 4 --request-ceiling 281 --output .local/arena-phase7b-qwen-stepwise-28-01
.venv/Scripts/python.exe -m aig.arena.benchmark --control-mode stepwise --mode probes --blue-provider openai --prompt-version arena-step-prompt-v1 --observation-version arena-observation-v2 --probe all --probe-trials 4 --request-ceiling 281 --output .local/arena-phase7b-luna-stepwise-28-01
```

Ollama's prior sandbox socket restriction does not authorize inference. Follow
workspace connectivity guidance only when live work is authorized; use new output
roots and preserve failures. No connectivity diagnostic or model preflight was
performed in Phase 7B.

## Stop point

The next boundary is authorization for the proposed live pilot. No action IDs,
new probes, prompt v3, observation v3, tactical heuristics, model judges or
full-turn replanning were added. Normal gameplay and Empire remain unchanged.

## Files and verification

Added:

- `backend/aig/arena/ai/stepwise.py`: separate providers, prompt registry, exact
  membership validation and bounded controller.
- `backend/aig/arena/stepwise_benchmark.py`: probe runner, detached evidence,
  command/step replay verification, reliability/usage/cost accounting.
- `backend/aig/arena/benchmark_artifacts/arena-benchmark-v2.json`: frozen v2 recipe.
- `tests/test_arena_stepwise.py`: 24 offline test methods covering zero/one/many
  actions, stale/wrong actions, all four feedback mechanics, AP/terminal/stop,
  repair success/failure, provenance contamination, execution defects, determinism,
  both fake transports, schema preservation, replay tampering, CLI, request bounds,
  versions/profiles and synthetic cost/caching/missing-usage behavior.
- This experiment report.

Changed existing files: `ai/provider.py` adds behavior-preserving full-turn hooks;
`benchmark.py` dispatches the explicit mode and CLI options;
`benchmark_versions.py` registers v2 and records future control identity;
`docs/arena-ai.md` and `docs/arena-benchmarking.md` document the opt-in path.
All pre-existing uncommitted Phase 7A changes were retained.

Validation: **1,102 Python tests, 1,097 passing and five skipped**; the new 24-test
suite also passed independently after final trace-verification changes. Frontend:
**76/76 tests pass**; production build succeeds (JavaScript, CSS and sprite assets,
plus generated index). No frontend source changes. Existing frozen Phase 3 heuristic
hash regressions and V1/V2 prompt/observation tests remain passing. Historical
full-turn regression tests use offline heuristic/fake providers only.

The pre-work SHA-256 inventory covered 5,252 existing files. Exactly the five
existing files listed above changed; 5,247 remained byte-identical, including
**all 5,068 existing evidence files**. Protected schema, full-turn adapters,
controller/executor/heuristic, observation, prompt, model-profile, domain and Empire
sources stayed unchanged. Shared provider dispatch hooks changed source bytes but
preserve the frozen full-turn semantics and default repair message.

- [Preservation audit](../.local/arena-phase7b-preparation/preservation-after.json)
- [Frozen contract hashes](../.local/arena-phase7b-preparation/frozen-contract-verification.json)
- [Python test log](../.local/arena-phase7b-preparation/python-tests-final.log)
- [New offline tests](../.local/arena-phase7b-preparation/stepwise-tests-final.log)
- [Frontend test log](../.local/arena-phase7b-preparation/frontend-tests.log)

Unchanged prompt hashes:

```text
arena-turn-prompt-v1 5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7
arena-turn-prompt-v2 5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29
```

New step prompt SHA-256:
`791f842d479527929f504c505254cd2d21dee668b2550f31cad5e7458b572d5f`.
