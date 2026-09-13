# Comparative strategy benchmarks

The next controlled experiment freezes V5 and compares explicit prompt v1/v2
selections with the same Luna configuration. See [prompt-v2](prompt-v2.md) for
the contract, reproduction commands, historical context, and measurement results.

## Environment V5 conquest measurements

The current primary comparison target is Heuristic vs Luna; Qwen V5 is optional.
Use `--environment-version v5 --scenario-version v3`. V3 world data already permits
conquest; the separate four-civilization scenario is documented in [Scenario V4](scenario-v4.md). Prompt/schema/model profiles stay
v1; benchmark-v1 gains additive capture/elimination/victory fields.

`metrics` includes `winnerPlayerId`, `victoryType`, `victoryTurn`,
`victoryActivation`, `gameDurationTurns`, and `turnCapReached`. Terminal victory
stops commands and all remaining phases immediately. A capped game has no winner.
Command outcomes include `conquest_events`; totals retain `city_capture_events`
and `civilization_eliminations`. Per-faction fields record captures/losses, first
capture, unit types, population loss, actual food/production resets, canceled
production, recaptures, and elimination attribution with unit/Settler cleanup.
See [metric definitions](environment-v5.md#benchmark-observations) and
[offline verification](environment-v5-verification.md).

Four-run offline verification (two paired trials):

```powershell
.\.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b heuristic --games 2 --turns 100 --environment-version v5 --scenario-version v3 --output .local/v5-new-run
```

Live model comparison requires separate authorization. Existing strict provider
preflight and purity safeguards remain in force; no live V5 measurements were
made during implementation. Historical environments must run at their recorded
source revision. This runtime explicitly rejects them as execution targets.


Current defaults are **environment-v5 / scenario-v4**, with snapshot v12 and
unchanged prompt, plan-schema, model-profile and benchmark-v1 versions. See
[Environment V4](environment-v4.md) for camp rules, local threats, spawn/clear
measurements, lifecycle and fog boundaries. V1/V2/V3 results remain historical;
the current engine cannot emulate their prior rule versions.

Offline V4 verification (no model requests):

```powershell
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b heuristic --games 2 --turns 100 --environment-version v4 --scenario-version v3 --output .local\environment-v4-comparison
```

V4 adds per-faction camp discovery/sighting/clear timestamps and counts, Scout
attribution, barbarian combat damage/kills/losses, Settler movement/deaths, camp
Gold, and observer spawn/skip/cap measurements. Existing production, expansion,
economy and resource-yield metrics remain. DEFEND activations record visible
civilization threats, visible barbarian threats, or neither; simultaneous kinds
can count in both visible categories. System phases have `system_phase=true`, no
plan/provider fields, and ordinary replayable commands. Civilization activation
counts exclude the system phase. Command outcomes include `barbarian_events`.

Each replan reports canonical StrategicState UTF-8 bytes and marginal barbarian
field bytes. These are not token estimates. Qwen stays at its frozen 4096 context;
Luna is the hosted target. Context overflow in later authorized Qwen trials is
experimental data, not grounds to silently change its profile.

## Experiment artifacts and provenance

Artifact domains evolve independently; snapshot schema **v11** is separate from all
of them. The current environment is V4 and scenario is V3; prompt/schema/profiles
retain their V1 artifacts. The original baseline mappings below remain historical:

| Identifier | Frozen content / meaning |
| --- | --- |
| `environment-v1` | Original deterministic full-information rules/information environment; metadata, not an engine compatibility switch |
| `environment-v2` | Historical fog, exploration and knowledge-safe planning rules |
| `environment-v3` | Historical discoverable resource economy |
| `environment-v4` | Local barbarian camps, Warriors, replacements and camp Gold |
| `scenario-v3` | Scenario V2 terrain/resources/starts plus three fixed camps and Warriors |
| `scenario-v4` | Fixed 16x12 four-civilization total-war map, 18 resources and five camps |
| `scenario-v1` | Original 12 by 10 map, seed 42, starts A `(2,2)` and B `(9,7)`, faction order and setup; benchmark controls both factions with AI |
| `strategy-prompt-v1` | Exact original strategic instructions shared by Ollama and OpenAI |
| `strategic-plan-schema-v1` | Original six-field logical plan contract and enum values |
| `qwen-config-v1` | Qwen model/inference settings below |
| `luna-config-v1` | Luna model/inference settings below |
| `benchmark-v1` | Existing paired benchmark format, with additive per-run experiment metadata |

`aig.versions.resolve_version()` uses explicit registries and centralized latest
pointers. `None`, empty string and `latest` resolve to the current concrete latest
ID. `v1` and domain-qualified IDs select history explicitly. Unknown or wrong-domain
IDs fail before a benchmark starts. Reports record concrete IDs, never `latest`.

The CLI adds `--environment-version`, `--scenario-version`, `--prompt-version`,
`--plan-schema-version`, `--qwen-config-version`, and `--luna-config-version`.
The existing `--scenario human-vs-ai` name remains accepted. For example, offline:

```sh
python -m aig.ai.benchmark \
  --environment-version v2 --scenario-version v1 --prompt-version v1 \
  --plan-schema-version v1 --provider-a heuristic --provider-b heuristic \
  --turns 100 --output benchmark-results/versioned-heuristic
```

`AIG_STRATEGY_PROMPT_VERSION` selects instructions in normal application play and
smoke commands too. Non-empty process values override `.env`; an empty process
value falls through to `.env`, and an empty/absent local value means latest.
Invalid versions fail at provider construction (or benchmark resolution), outside
inference repair/fallback. An explicit CLI prompt selection overrides the setting;
CLI `latest` or an empty CLI string explicitly chooses latest. No gameplay scenario
environment variable is needed: browser/demo aliases follow latest, while the
benchmark and `scenario_setup(version)` allow explicit selection.

The V1 prompt's first line remains literally `Prompt version: strategy-v1` to
preserve request bytes. Its canonical trace/manifest ID is `strategy-prompt-v1`.
`ollama.SYSTEM_PROMPT` and `PROMPT_VERSION` remain compatibility exports, with
`PROMPT_VERSION` now canonical. OpenAI's existing `strategic-plan-openai-v1` wire
adapter still removes provider-incompatible constraints; both providers report
the same logical `strategic-plan-schema-v1`. Schema calls return detached copies.

### Frozen profiles and runtime overrides

| Setting | `qwen-config-v1` | `luna-config-v1` |
| --- | --- | --- |
| Provider | `ollama` | `openai` |
| Model | `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M` | `gpt-5.6-luna` |
| Context size | 4096 | provider default |
| Temperature | 0.0 | not sent |
| Seed | 42 | not sent |
| Maximum output tokens | 256 | 512 |
| Think / stream | false / false | not sent |
| Reasoning effort | not sent | `none` |
| Store / SDK retries | not applicable | false / 0 |

Ordinary runtime settings remain usable. Omitted profile flags resolve the latest
profile for comparison with effective inference settings: matching settings record
its concrete ID; any difference records `modelConfigVersion: null` and the exact
effective `modelConfiguration`. Terminal output calls this a custom configuration.
This does not silently relabel modified settings as a preserved baseline.

An **explicit** `--qwen-config-version v1` or `--luna-config-version v1` supplies
the frozen inference values, overriding ordinary model tuning settings. Explicit
empty/latest profile flags pin the current latest profile in the same way.
Connection settings and secrets remain runtime inputs. Timeout and Ollama
`keep_alive` affect operations and timing, not profile identity; effective values
remain in report `configuration`. Ollama's endpoint is runtime metadata, with URL
credentials, query and fragment removed from diagnostics. Neither profile stores
an endpoint, API key, authorization header or client object. The heuristic needs
no model profile; its implementation is identified by source revision.

### Manifest and source provenance

Each `summary.json` run has an `experiment` object, associating all files under
its existing `directory` with one manifest. `run_trial()` also returns a manifest.
The shared configuration and existing trace paths remain backward-compatible;
there is no per-line manifest duplication. Example for the Luna profile:

```json
{
  "environmentVersion": "environment-v1",
  "scenarioVersion": "scenario-v1",
  "strategyPromptVersion": "strategy-prompt-v1",
  "strategicPlanSchemaVersion": "strategic-plan-schema-v1",
  "benchmarkVersion": "benchmark-v1",
  "provider": "openai",
  "modelConfigVersion": "luna-config-v1",
  "model": "gpt-5.6-luna",
  "modelConfiguration": {
    "model": "gpt-5.6-luna",
    "reasoning_effort": "none",
    "max_output_tokens": 512,
    "store": false,
    "max_retries": 0
  },
  "sourceRevision": null,
  "sourceDirty": null
}
```

When local Git is available, these last two fields hold the actual full commit
SHA and a boolean dirty status, including untracked, non-ignored files. Git is
queried once per paired benchmark from the source checkout, without shell command
interpolation or a GitHub API call. Missing Git, absent checkout metadata or a
failed query produces null values and does not prevent library/benchmark use.
An installed package nested in an unrelated repository does not claim its revision.

`canonical_json(manifest)` provides sorted, compact deterministic non-secret JSON.
No new identity hash is needed: source timestamps, temporary paths and secrets
are excluded. Existing initial/final-state, command, strategic-state and plan
hashes do not include the new manifest, and remain unchanged. Inference traces
record resolved prompt and logical schema IDs, so their diagnostic bytes change.

Versioned experiment artifacts remain selectable where practical. Historical
game-engine behavior is reproduced through the recorded source revision rather
than by accumulating compatibility branches throughout game logic. Environment
metadata identifies the experimental environment; source revision identifies its
exact implementation. Selecting `environment-v1` labels the run and does not load
old rules. A dirty SHA alone cannot recreate uncommitted changes: preserve those
changes separately when exact reproduction is needed. Model aliases, server
versions and remote inference may also change independently of local source.

To introduce V2, leave V1 payloads untouched, add real V2 content to the relevant
registry, test explicit V1 still resolves, then move only that domain's latest
pointer. An `environment-v2` experiment may still use `scenario-v1`, prompt V1,
schema V1 and either model profile V1. There are no fake V2 entries or historical
game-rule branches. Existing baseline files remain untouched; see the committed
[baseline mapping](baselines.md).

## Harness behavior

The `benchmark-v1` harness measures what changes when `StrategyProvider` changes.
Each pair runs the fixed `human-vs-ai` demo twice, freshly created and started,
with **both factions controlled by the selected provider** in each run. A is
executed before B in each pair. This is a comparison of two autonomous simulations,
not a heuristic faction competing directly against an Ollama faction.

Initial snapshots must hash identically. Map, faction order, executor, pathfinding,
combat, production, research, action budget and plan reuse interval are shared.
Providers and controllers are recreated for every trial. Settings use the normal
environment → `.env` → committed defaults resolution. Effective settings are saved.
The scenario stores game seed 42 but uses no randomness; pair IDs distinguish
repetitions, and there is no synthetic seed option. The Ollama seed is a separate,
unchanged model option.

The current game has no city capture or victory condition, so these benchmarks
measure strategic behavior and execution outcomes rather than complete-game win rate.
Do not tune the LLM prompt before saving a baseline benchmark if the goal is to
compare prompt revisions later.

## Running

From the repository root, with the package installed as described in the README:

```powershell
# Offline, two pairs of identical heuristic runs (the default providers).
.venv\Scripts\python.exe -m aig.ai.benchmark --games 2 --turns 100 --output benchmark-results\heuristic

# Explicit opt-in to real LAN inference; five pairs, ten simulations in total.
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b ollama --games 5 --turns 100 --scenario human-vs-ai --output benchmark-results\qwen-baseline
```

Use `python` in place of the Windows venv path on other installations. `--games`
counts pairs, `--turns` counts global turns per run (two activations per global
turn in this scenario). Both must be positive. Output must be a new or empty
directory; existing reports are never overwritten. The default output is
`benchmark-results`, ignored by Git. The CLI prints outcome deltas, provider
purity, request counts, mean inference time, peak prompt tokens and repeatability.

Selecting `ollama` or `openai` explicitly enables network requests. Automated tests
use fake providers/transports. Controlled benchmarks default to **strict provider
purity**. Normal interactive gameplay, including Human vs Ollama/OpenAI, retains
controller fallback: provider failure -> heuristic plan -> gameplay continues.

Controlled benchmarks resolve artifacts/configuration, preflight all distinct live
providers, and require valid requested-provider plans with no fallback before any
trial starts. Preflight uses the normal `StrategyProvider.create_plan` path and a
`StrategicStateBuilder` view of the active faction in the normal started scenario.
It applies the resolved prompt, schema, model profile and environment, then checks
the returned `StrategicPlan` with `parse_plan`, including strategic references and
provider provenance. Heuristic needs no network preflight.

Preflight disables repair for **one HTTP/API attempt per distinct live provider**.
Missing credentials can fail construction with zero requests. Every requested live
provider is checked even when an earlier one fails; neither side starts unless all
pass. Trial providers and controllers are fresh instances. Trials retain the normal
one-repair policy and provider request payload semantics.

After preflight, a strict trial failure invalidates the trial, preserves partial
traces, stops **before executing fallback commands**, and aborts all remaining
trials. Command replay verifies the completed prefix before reporting; replay
success cannot make an invalid model trial valid. Invalid pairs have no deltas.
Unexpected engine/action-limit errors still abort without a completed report.

`--allow-provider-fallback` permits continued fallback after successful preflight.
Such runs remain `fallback_contaminated`, `validModelTrial: false` and
`pureProviderRun: false`, and the CLI returns nonzero. It never bypasses preflight.
A reused fallback plan counts as reuse, not another fallback invocation.

### Preflight-only command and report fields

This is an explicit network action; run only when live preflight is authorized:

```powershell
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a ollama --provider-b openai --environment-version v2 --scenario-version v1 --prompt-version v1 --plan-schema-version v1 --qwen-config-version v1 --luna-config-version v1 --preflight-only --output .local\provider-preflight-v2
```

Each provider prints PASS/FAIL, model, latency, request count, available usage and
sanitized diagnostics. Trials started is zero. Exit status is 0 if all preflights
pass (including heuristic-only), 1 for preflight/trial failure or contamination,
and 2 for invalid CLI configuration. Use a new/empty output path for each attempt.

The additive report fields retain `benchmark-v1`; no frozen artifact registry,
snapshot, prompt, schema, scenario or model profile is revised. Historical reports
without these fields must never be assumed to have passed preflight.

- `status`: `preflight_failed`, `preflight_passed`, `completed`, `trial_failed`, or
  `fallback_contaminated`; `strictProviderMode` records the execution policy.
- `experiments`: resolved manifests keyed by requested provider, including source
  revision and concrete artifact IDs even if preflight fails.
- `preflight`: serializable results with `requested_provider`, `actual_provider`,
  `success`, `model`, `duration_seconds`, `error_category`, `sanitized_error`,
  `retry_count`, `fallback_used`, `plan_valid`, `requests`, and `usage` per attempt.
  Only available numeric usage fields are retained: Ollama prompt/generation token
  and duration counters; OpenAI input/cached/output/reasoning/total token counters.
- `trialsStarted`, `validModelTrials`, `invalidModelTrials`, `pureProviderRuns`:
  individual simulations, including heuristic controls, not pairs or preflights.
- `runs[].validModelTrial`, `status`, `aborted`, `replay`: distinguish valid results
  from an invalid trial's saved final snapshot of its stopped prefix.
- `requestAccounting`: `preflightRequests`, `trialProviderRequests`, `repairRequests`
  (separate `preflight`/`trials` maps), and `fallbackPlans`, keyed by provider.
  Trial requests include repair attempts; repairs are a subset, not extra requests
  to add again. Preflights never enter trial inference counts. Request counters
  represent attempted transport calls, not confirmed remote receipt.

Failed preflight writes only diagnostic `summary.json`, with zero trials/valid/
invalid runs, empty runs/comparison/repeatability, and all preflight manifests.
It creates no trial directories, final states or fake provider comparisons.

Diagnostics preserve connection, timeout, DNS when exposed, HTTP/API,
authentication, permission/model access, rate-limit, malformed envelope/JSON,
schema/reference, refusal/incomplete/empty output, repair and fallback categories.
Ollama retains coarse `transport_failure`/`non_2xx` where no finer cause is exposed.
Benchmark checks also report `provider_mismatch`, `provider_exception`, and
`configuration_failure`. Raw exception representations, authorization headers and
secret settings are excluded. Free-form errors are replaced by safe diagnostics;
OpenAI credential echoes are redacted. See [baseline status](baselines.md) for the
preserved failed V2 infrastructure experiment with zero valid LLM trials.

`openai` is also an explicit provider choice, independent of
`AIG_STRATEGY_PROVIDER`. Configure `OPENAI_API_KEY` on the backend first. Its
default cloud model is `gpt-5.6-luna`; no pricing is embedded in provider logic.

```powershell
# Explicit cloud opt-in: two pairs, four simulations total.
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b openai --games 2 --turns 100 --output benchmark-results\luna
```

OpenAI follows the same preflight and strict purity enforcement. Inference records include
configured and returned model IDs, response/request IDs, and available input,
cached input, output, reasoning, and total token counts for each attempt.
`inference.openai_usage` in the summary adds per-counter statistics and totals,
including repair requests. Missing usage is omitted from samples; a null total
means unavailable. Cached input and reasoning are subsets of input and output,
respectively, not extra tokens to add. These counters support future cost reports
with explicit pricing dates; incomplete coverage cannot establish full cost.
Existing Ollama token/timing fields remain unchanged. See the
[provider contract and one-request smoke command](openai-provider.md).

## Files and versioned report contract

```text
summary.json
runs/pair-0001-a-heuristic/
  initial-state.json
  final-state.json
  plans.jsonl
  commands.jsonl
  activations.jsonl
  inference.jsonl
runs/pair-0001-b-ollama/
  ...
```

`benchmarkVersion` is `benchmark-v1`, independent of snapshot, plan-schema and
prompt versions. Objects below use exact wire names; additional metrics require
deliberate report-version compatibility decisions. JSON contains no NaN/Infinity.

| `summary.json` field | Type and meaning |
| --- | --- |
| `benchmarkVersion`, `scenario` | Strings identifying report contract and fixed scenario |
| `configuration` | Object: `games`, `turns`, `mode`, `providers` (`a`/`b`), shared `ai`, effective `ollama` or null, `gameSeed`, `scenarioUsesRandomness`, `turnOrder`, `executionOrder`, `promptVersion`, `planSchemaVersion` |
| `runs` | Array in pair/slot execution order |
| `runs[].runId`, `pair`, `slot`, `provider`, `directory` | String ID, one-based pair, `a`/`b`, requested provider, report-relative path |
| `runs[].pureProviderRun`, `fallbackCount` | Boolean and integer; failed provider calls using the heuristic are explicit |
| `runs[].metrics`, `players` | Whole-world metrics and player-ID-to-metrics objects |
| `runs[].inference` | Request/failure counts, token/context and timing statistics |
| `runs[].hashes` | SHA-256 strings: `initial_state`, `final_state`, `commands`, `plans` |
| `runs[].traces`, `snapshots` | Named filenames relative to the run directory |
| `comparison` | One object per pair: IDs, `deltaDirection` (`B minus A`), `initialStatesEqual`, `pureProviderRuns`, `fallbackCounts`, `deltas`, `playerDeltas`, `hashesEqual`, `equivalentStateReplans` |
| `repeatability` | `a`/`b` objects with provider, trial count, `measured`, `hashesIdentical`, `allPureProviderRuns`; identical flags are null for a single trial |

`deltas` and `playerDeltas` subtract A from B for scalar numerical metrics;
`inference_time_seconds` subtracts summed request wall time. No weighted score or
“better” label is assigned. `equivalentStateReplans` matches `(player_id,
StrategicState hash)`, then counts identical and different output plans. Once
simulations diverge, same-turn states are **not** assumed equivalent.

## Gameplay and planning measurements

Counts are integers; averages may be fractional. Whole-world counts sum all
factions; `players` keeps asymmetry visible. An activation is one faction's turn.
Trace turns, global activation indices and per-player activation indices start
at zero. `global_turns_completed` and `activations_completed` are completion counts.

| Metrics | Definition |
| --- | --- |
| `final_city_count`, `total_population`, `final_gold`, `final_science_stored` | Final live state totals |
| `technologies_researched`, `research_completions` | Final known technologies (including starting Agriculture), and count of new faction-technology completions |
| `cities_founded`, `cities_founded_at` | Successful founding count and `{city_id, player_id, turn, activation, player_activation}` events |
| `settlers_produced`, `unused_settlers`, `units_produced_by_type`, `units_remaining_by_type` | New units created by economy, surviving Settlers, and type counts; initial units are not production |
| `final_production_stored` | Final generic production stockpile; no production is labeled wasted |
| `activations_with_no_production_target` | Activations with at least one owned city missing a target **immediately before EndActivation** |
| `city_activations_without_production_target` | Number of such city observations |
| `city_activations_without_target_with_production` | Such observations with positive stored production or incoming production yield |
| `production_generated_without_target` | Production yield accumulated during those observations; it remains stored |
| `activations_without_research_target_with_choices` | Pre-EndActivation observations with no research target and at least one available technology |
| `final_military_strength` | Sum of `max(combat_strength, ranged_strength or 0) * hp // 100` for surviving non-Settlers, matching strategic-state strength semantics |
| `attacks_executed`, `combat_commands`, `movement_commands`, `commands` | Successful AttackUnit, AttackUnit, MoveUnit, and all command counts (including EndActivation) |
| `kills`, `unit_losses`, `damage_dealt` | Actual HP removed and deaths at each attack; retaliation credited to the defender; overkill capped to actual HP, founding consumes no combat loss |
| `idle_movable_units`, `idle_movable_combat_units` | Sum of living owned units with movement remaining immediately before economy; combat excludes Settlers |
| `activations_ending_with_movable_combat_units` | Count of activations with at least one such combat unit |
| `combat_distance_to_target_tiles` | Descriptive statistics over unit-activation samples of Chebyshev distance to the current plan's live target city; missing targets contribute no samples |
| `commands_per_activation`, `movement_commands_per_activation`, `attacks_executed_per_activation` | Command count divided by completed activations |
| `plans_created`, `provider_calls`, `plans_reused` | New resulting plans, calls to the requested provider (not repair HTTP requests), and activations reusing a plan |
| `plan_changes`, `target_changes` | Exact plan inequality and enemy-ID/target-city-ID pair inequality between consecutive created plans for the same faction; initial plans are not changes |
| `posture_changes`, `production_priority_changes`, `research_priority_changes` | Exact field/list inequality at replan |
| `posture_counts`, `plan_age_turns` | Posture counts over all activations, and statistics of the executed plan's age (new plans have age zero) |
| `invalidated_plans`, `fallback_count` | Replans caused by `invalid_target`, and failed provider calls replaced by heuristic plans |
| `wall_clock_seconds` | Run time including planning, execution, observations and streaming traces; excludes initial/final snapshot file writes |

Target/unset/idle measurements happen before economy and incoming-player movement
refresh. Completing production or research legitimately clears a target; that is
not counted as pre-economy inactivity. Idle units can be deliberately holding a
position. Distances describe target-city proximity, not path distance or tactical
goals selected internally by the executor.

## Trace contracts and hashes

Every JSONL line is one canonical JSON object, UTF-8, sorted keys, compact
separators, preserved Unicode and one LF. Entity arrays follow stable ID ordering;
priority arrays retain their meaningful preference order. Snapshot and strategic
state hashes use the same canonical JSON without a trailing LF. Trace hashes are
SHA-256 over the exact JSONL bytes including LFs, never Python repr. The benchmark
hash format differs from the older `simulate` hash formatting; its original
baseline hashes remain tested separately.

* `plans.jsonl`: one row per replan, including `activation`, `turn`, `player_id`,
  requested/actual provider, `previous_plan`, `new_plan`, `replan_reason`, old
  `plan_age_turns` (null initially), full input `strategic_state`, its SHA-256,
  and `fallback_used`. Plan hashes include provider provenance. Per-output-plan
  hashes are used internally for equivalent-state comparisons.
  `previous_plan` is the actual provider input: null after `invalid_target`,
  otherwise a still-valid plan (including valid expired/event-triggered plans).
  Invalidations add `invalidated_previous_plan` separately for diagnostics and
  historical change/elimination metrics; it is never model input. The offline
  knowledge audit now validates previous-plan references as well as new/reused
  plans and reconstructed StrategicState. Historical traces may fail this stricter
  check; preserve them unchanged. Corrected plan-trace hashes differ without
  requiring a benchmark/schema/prompt version change.
* `commands.jsonl`: one row per successful command, with global `activation`,
  `player_activation`, `turn`, `player_id`, `command` (`type` plus dataclass
  arguments), and `outcome`. Outcomes contain attack damage/deaths, founding
  events, or pre-economy idle/target/production observations and newly produced
  units. Other successful commands have an empty outcome. Commands plus the
  initial snapshot can be replayed with the normal command API.
* `activations.jsonl`: one row per completed activation: index, turn, player,
  executed plan, reuse flag, executed-plan age, actual provider, fallback
  provenance and command count.
* `inference.jsonl`: one row per Ollama planning call (or other failed provider
  call), with activation, turn, player, strategic hash, provider provenance,
  model/settings/version metadata when available, retry/fallback/error fields
  and `attempts`. Each attempt contains raw output `raw_content`, reported
  `metrics`, `wall_clock_seconds`, and optional error/category. No message
  thinking, hidden reasoning or prompt message arrays are retained. Heuristic
  success produces no inference rows.

Traces stream to disk at each observation, independently of the runtime's bounded
64-entry debug buffer. Timing data is excluded from deterministic state, command
and plan hashes. Repeated Ollama trials may differ; the report preserves those
differences. Even with identical hashes, inference latencies may differ.

## Inference statistics and failures

`inference.tokens.prompt_eval_count` and `.eval_count` report
`{samples, min, max, mean, median}` over API-reported values, including repair
attempts. Missing metrics produce no samples, not invented zeros or estimates.
Empty distributions have null statistics. `maximum_prompt_tokens` and
`maximum_prompt_context_percent` use the maximum reported prompt count divided
by the effective `context_size` (4096 by default). This is **prompt occupancy**,
not a claim about combined prompt/output memory or unreported truncation.

`inference.timings` has the same statistics for `request_wall_clock_seconds`,
`ollama_total_seconds`, `prompt_eval_seconds`, and `generation_seconds`.
Ollama's `total_duration`, `prompt_eval_duration` and `eval_duration` remain raw
nanoseconds in attempt `metrics`; summaries convert them to seconds.
`request_wall_clock_total_seconds` sums request durations; heuristic runs have
zero requests and summed inference time, null context/token/timing distributions.
Wall time includes transport; Ollama timing describes server-reported work.

`requests`, `retries`, `repair_success_count`, `fallback_count`,
`schema_invalid_responses`, and `malformed_responses` are explicit counts.
`failures` always includes every category:

| Category | Counted event |
| --- | --- |
| `transport_failure` | Connection/HTTP-read/decoding failure other than timeout/non-2xx |
| `timeout` | Direct TimeoutError or URLError wrapping TimeoutError |
| `non_2xx` | HTTP error status |
| `malformed_ollama_envelope` | Invalid envelope JSON, missing content, unsuccessful/incomplete envelope |
| `malformed_json_content` | Invalid JSON inside message.content, including duplicate/nonfinite/deeply nested JSON |
| `schema_validation` | Plan field/type/enum/priority contract failure |
| `invalid_strategic_references` | Structurally valid plan references unavailable enemy/city or mismatched ownership |
| `repair_failed` | A retry was attempted and the planning call still fell back |
| `heuristic_fallback` | Controller supplied a heuristic plan after provider failure |

Attempt failures and invocation outcomes are separate dimensions: one failed
call can contribute to an attempt category, repair failure and fallback. They
must not be added together as a total failed-request count. Repair success means
the second attempt supplied a valid plan, not merely that HTTP succeeded.

## Limitations and verification

The scenario is fixed and small; repetitions test reproducibility, not a broad
distribution of game situations. A-then-B execution and model warm-up/cache/load
can affect timing. The full strategic state changes after plans affect execution;
equivalent-state matches can therefore become rare. There is no counterfactual
replanning of every state, separate probe suite, winner score or statistical
significance claim. All-faction totals can conceal faction-specific effects;
inspect `players` and `playerDeltas`.

The executor currently gates expansion at fewer than two owned cities, finishes
existing production orders and supplies military-shortage priorities itself.
These shared constraints limit how much plans can change behavior. StrategicState
does not expose map tiles, production/science stockpile detail for all cities, or
context truncation information. These contracts and the prompt are unchanged.

Automated tests use synthetic observations and injected transports, including
repair/fallback categories, exact timing/token fixtures, trace completeness,
canonical bytes, copied initialization and command equivalence to `simulate`.
The existing 100-turn baseline is pinned to:

```text
snapshot_sha256: 002a14bb4681f14c6715173f6f82cf57d95cfd3d14bf9a86dfd693ece21f472e
trace_sha256:    30d0a56152bb4ab1b279c1aaf8c04480f4af8d721d54ce420bfbe12dfe790a42
```

The only runtime additions are optional command observations and diagnostic
failure categories. Gameplay decisions, prompt/repair wording, validation rules,
model options, plan reuse and fallback policy remain unchanged. Real LAN runs
are separate opt-in commands and never a CI prerequisite.


## Environment V2 exploration measurement

New per-faction facts are `explored_tile_count`, `map_explored_percent`,
`tiles_newly_revealed`, `tiles_newly_revealed_by_scouts`,
`scout_movement_commands`, `discovered_enemy_city_count`, `first_contacts`
(enemy city/unit, each with zero-based global turn and activation index),
`visibility_at_replans` (visible enemy military strength and nearest visible
combat-unit distance), and `significant_discovery_replans`. Initial sight counts
as explored but is excluded from newly revealed command totals. Scout attribution
counts new coordinates from Scout movement and Scout production sight; shared
already explored tiles never count twice. First-contact observers sample initial
state and every command for all factions, including the inactive faction.
There is no synthetic exploration-quality score. Economy, expansion, combat,
production, research, plan churn and inference metrics remain available.

Every current engine run records `environment-v2` and concrete scenario, prompt,
schema, model-profile (or explicit custom/not-applicable metadata), benchmark and
source-revision fields. Historical `environment-v1` still resolves as provenance
metadata, but the current benchmark rejects running under its label: use the
recorded V1 source revision and frozen archives to reproduce V1. Runtime V1
emulation is not implemented. Pair comparisons explicitly report both environment
versions and `environmentChanged`; cross-environment deltas must not be interpreted
as an isolated provider effect.

The fixed scenario-v1 map and starting positions are unchanged. See
[Environment V2 verification](environment-v2.md) for the offline 100-turn heuristic
result, replay hashes and preservation checks. Qwen/Luna were not run for this slice.

## Four-civilization Scenario V4 measurements

Select `--scenario-version v4 --environment-version v5 --turns 150`. The scenario
has A-D plus the system barbarian phase. Benchmark slots a/b designate two entire
all-faction trials, not player A versus player B: each selected provider controls
all four normal factions in its trial. Mixed providers within a single game are
not currently exposed by this harness. Scenario data never selects a provider.

Per-player metrics and world totals retain all prior fields. Additions include:

- `captures_by_victim_civ`, `losses_by_capturing_civ`, `rivals_eliminated`.
- `distinct_primary_enemies_selected`, `primary_enemy_switches`, `target_city_switches`.
- `targeting_activations_by_rival` counts each activation using a target, including
  reused plans and a partial terminal activation. It is not wall time or plan count.
- `consecutive_plans_same_primary_enemy` and its mean count consecutive newly
  created plans, excluding null targets; null breaks a streak. Switch counters
  compare consecutive new plans and include changes to/from null. Initial selection
  is not a switch. Reused plans do not increment these counters.
- `eliminated_target_transitions` counts replans changing away from a primary
  enemy whose elimination is public in that replan's supplied state.
- `multi_front_visibility_at_replans` records visible rival IDs, strength grouped
  by owner, and own cities with military units of two or more rivals within three
  Chebyshev tiles. This geometric proximity is not a claim of attack legality.
  Barbarians remain separately measured. No hidden tactical information is used.

World conquest fields add `elimination_order`, `eliminations_by_killer_civ`,
`surviving_city_count`, `rivals_eliminated_by_winner`, and
`rivals_eliminated_by_other_civs`. Winner-related counts are null without victory.
Capture events retain former/new owner, city ID, turn, activation and recapture
history across arbitrary owners. Event coordinates can be recovered by city ID
from snapshots; no arbitrary geographic front labels or strategic quality score
are imposed. Abandonment is not inferred: switches are reported directly because
capture, elimination and changing knowledge can all cause a target to change.

Comparisons use the intersection of player IDs and flag `playerRosterChanged`,
so comparison with a historical two-player report does not dereference missing
players. Old reports remain unchanged. New fields are additive under benchmark-v1.

The world maximum of simultaneously visible enemy civilizations is the maximum
across players, not the sum of their maxima.

The old V4 file-hash fixture predates addition of prompt v2 to `prompts.py`.
Its test now checks the historical V1 payload hash rather than the entire
extensible registry file. Both V1 and V2 payload hashes are independently pinned
in `test_scenario_v4.py`; no historical fixture or prompt was rewritten.
