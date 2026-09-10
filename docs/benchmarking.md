# Comparative strategy benchmarks

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

Selecting `ollama` explicitly enables network requests. There is no auto-discovery
or model call in normal tests. The existing provider still repairs an invalid
response once and falls back through the controller on an expected failure.
Fallback runs finish, but `pureProviderRun: false`, `fallbackCount`, comparison
purity and terminal `MIXED` markers prevent treating them as successful pure LLM
trials. A reused fallback plan counts as reuse, not another fallback invocation.
Unexpected engine/action-limit errors abort the CLI; partial trace files are not
a completed report and no `summary.json` is written.

`openai` is also an explicit provider choice, independent of
`AIG_STRATEGY_PROVIDER`. Configure `OPENAI_API_KEY` on the backend first. Its
default cloud model is `gpt-5.6-luna`; no pricing is embedded in provider logic.

```powershell
# Explicit cloud opt-in: two pairs, four simulations total.
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b openai --games 2 --turns 100 --output benchmark-results\luna
```

OpenAI follows the same pure/MIXED fallback reporting. Inference records include
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
