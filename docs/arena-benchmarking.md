# Controlled Arena tactical benchmarks

`arena-benchmark-v1` measures how well a provider directly selects ordered tactical
actions within five shared AP. Plan legality, AP utilization, truncation and action
order are primary research outcomes. It does not change gameplay or rank providers
with an invented combined score. Empire's long-horizon benchmark remains separate.

## Offline use

From the repository root:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode matches --blue-provider heuristic --red-provider heuristic --games 4 --turns 100 --output .local/arena-heuristic-matches
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider heuristic --probe all --probe-trials 4 --output .local/arena-heuristic-probes
.venv/Scripts/python.exe -m aig.arena.benchmark --mode all --games 4 --probe-trials 4 --output .local/arena-heuristic-all
```

Output must be a new or empty directory. Existing evidence is never overwritten.
The CLI prints requested match/probe counts before constructing providers. Default
providers are heuristic even if application settings select a model. Games and
probe repeats default to four; the CLI requires an explicit output path.

`--mode matches` uses Blue and Red selections. `--mode probes` uses only
`--blue-provider`; specifying a Red provider or side swaps in that mode is an
error. `--mode all` runs matches and then every selected probe for each distinct
selected provider. `--probe` accepts `all` or a fixture name below. Programmatic
`benchmark(..., provider_factory=...)` supports offline fake providers for tests.

## Match methodology and side swaps

Every match constructs the canonical Arena scenario anew and records the exact
initial snapshot/hash. The clean initial comparison is Heuristic/Heuristic,
Qwen/Qwen, and Luna/Luna with the same initial state and turn bound. Later states
can diverge as a consequence of each provider's choices. Cross-provider matches
are also supported without map changes or randomness.

`--side-swap` adds the reverse provider assignment after each requested game.
Thus `--games 4 --side-swap` means eight matches, paired in adjacent run IDs.
Same-provider swaps intentionally repeat the same setup. Every trial records
assignments, first player, per-side outcomes and initial-state hash. No mutable
game state is shared across trials. A provider instance is reused across calls
and trials; production Arena providers are stateless with respect to plans.

`--turns 100` follows the existing Arena convention: 100 **completed global
rounds**, at most 200 player turns. Victory can occur partway through a round.
The harness stops at the existing victory or this benchmark bound. `turn_limit`
is a reporting outcome with no winner/loser, not a new gameplay draw rule.

## Strict provider purity and preflight

Interactive Arena still permits provider failure -> heuristic fallback.
The benchmark calls the provider through its own checked boundary, validates a
typed `ArenaTurnPlan` with the existing static parser, verifies provider identity
and provenance, and only then calls the unchanged executor. It never invokes
the gameplay fallback controller. Model provenance must include attempt evidence.
`--strict-provider` is accepted for clarity; strictness is always enforced.

Before any trial, each distinct live provider makes one real Arena planning
preflight call on the canonical initial observation. Repair is temporarily
disabled and restored afterward. Success requires a valid typed plan, actual
provider equal to requested provider, no fallback and exactly one recorded
request attempt. Matching provider settings and prompt/schema versions are
checked at construction. Heuristic needs no preflight request.

Any preflight failure produces diagnostics, starts zero trials, and exits nonzero.
Both distinct preflights are checked even if one fails. `--preflight-only` runs
these checks and zero trials. Missing credentials or construction failure may
prevent a network request. Request counts describe recorded provider request
attempts; the current adapters do not prove that every failed attempt reached
the remote service.

A trial provider exception, provenance mismatch, fallback or invalid final
static output invalidates that trial and stops the remaining schedule. Completed
commands, observations, accepted plans and failed inference diagnostics are
preserved. Partial command replay is still checked. Invalid-trial telemetry is
retained per trial but excluded from comparative summary distributions.

Static-invalid initial output may use the existing one-repair policy during
trials. Execution-time invalidity preserves the valid command prefix, records
the invalid action/index and discards the suffix, then ends a nonterminal turn.
This is a measured tactical outcome, not a provider purity failure or repair.

## Cold/warm latency and request accounting

Preflight is also warmup. Its `wall_clock_seconds` and individual attempt metrics
live in `summary.json.preflight`, separate from trial distributions. Ollama retains
its existing `keep_alive`; this operational value is recorded in the manifest.
No provider settings are tuned and no extra hidden warmup requests are made.

Trial `inference.jsonl` separates initial inference attempts from repair attempts.
Summary `inference` aggregates valid trials, and `inferenceByMode` separates
matches from probes in combined runs. Distributions report count, total, min,
max, mean and median. p95 uses nearest rank only when there are at least 20
observed samples; otherwise it is null. Missing telemetry has zero samples and
null distribution values, not synthetic zero latency. Heuristic planning time
is available separately; it has zero model inference requests.

All measured requests remain included, including repair calls, latency spikes
and later model reloads. No slow-request deletion or inferred cold-load filtering
occurs. `latency_seconds` includes all trial attempts; initial-request, repair
and complete planning-call distributions are also available. Preflight and trial
token consumption remain separate.

Ollama captures `prompt_eval_count`, `eval_count`, `prompt_eval_duration`,
`eval_duration`, and `total_duration`; provider durations are **nanoseconds** and
wall time is **seconds**. Reports include configured context (4096 in
`qwen-config-v1`) and maximum observed `(prompt + output) / context`, including
repair attempts. OpenAI captures input/cached-input/output/reasoning/total token
counts and existing sanitized request/response IDs. No hidden reasoning or raw
free-form model text is retained in benchmark evidence. Accepted typed plans are
retained exactly. There is no automatic pricing lookup or cost estimate in v1.

## Tactical probes and frozen artifacts

`backend/aig/arena/benchmark_artifacts/arena-probes-v1.json` freezes the exact
Phase 3 snapshots, canonical state hashes and observation hashes. It records the
original fixture identifier `arena-tactical-probes-v1` without changing that
module. Runtime benchmark probes load these frozen snapshots rather than mutable
fixture constructors. Integrity checks pin all three packaged artifact files.
Changes to probe states after this baseline require a new probe-set version.

| Name | Mechanical measurements / objective |
| --- | --- |
| `finish_or_core` | Finishes, Core damage and resulting units/HP; no prescribed correct action |
| `revive_decision` | Ally active at end of plan; revives and resulting HP/state |
| `fireball_friendly_fire` | Enemy/friendly damage, targets hit, downs, resulting HP and winner |
| `shield_bash_position` | Pushes, premium-tile occupancy, damage and resulting state |
| `snipe_vs_basic` | Action sequence, AP, damage and resulting units |
| `winning_core_line` | Immediate victory in this turn |
| `team_elimination` | Immediate victory in this turn |

Every provider receives the same canonical observation for a given probe.
Each repeat runs on an isolated snapshot copy. The observation audit regenerates
the public Arena facts and legal-action enumeration through the existing query
functions, retaining only canonical JSON. No Empire state or settings object
enters an observation. Providers may choose different plans; no LLM judge is used.

Finish cannot newly trigger victory: Arena already wins when the last active
enemy is downed. The preserved valid `team_elimination` probe measures that rule.
The benchmark does not create an impossible nonterminal all-downed enemy team.
For probes without a specified Boolean objective, `objective_achieved` is null.
Damage/HP consequences do not imply a subjective judgment of improvement.

`arena-heuristic-probes-v1.json` freezes heuristic outcomes, metrics and behavioral
hashes. It is regression evidence, not a definition of model correctness.
Repeated Qwen/Luna calls must be explicitly authorized; normal tests use fakes.

## Metrics and interpretation

Per player, each trial records:

- Winner/loser, completed global rounds, player turns and first-player identity.
- AP available/planned/executed/unused, mean use, all-five-AP and zero-action turns.
- Accepted plans, repairs, repaired plans, invalid initial static outputs,
  provider failures, fallback count, execution invalidity, truncation and index.
- Counts of Move, Attack, Heal, Finish, Revive, Shield Bash, Snipe and Fireball.
- Damage dealt/received, healing, friendly fire, downs, revives, finishes, Core
  damage, Shield Bash pushes and Fireball total/friendly targets hit.
- POWER-origin offensive actions, SIEGE Core attacks, WARD-origin unit actions
  and active-unit occupancy on premium tiles at each turn's starting boundary.
- Final Core HP, active/downed/removed units and total remaining unit HP.

`damage_dealt` preserves the engine counter: unit plus Core damage, including
friendly fire. Enemy damage is `damage_dealt - friendly_fire_damage`. Healing
includes HP restored by Revive. Downs count all units downed by the command,
including friendlies. `fireball_targets_hit` counts active affected units, not
damage points. Removed-unit totals compare with that trial's initial roster.
Terminal unused AP is included even when victory prevents End Turn. Truncation
includes a terminally unexecuted plan suffix; execution-invalid count separately
identifies illegal actions. WARD measurements are actions/turn-boundary occupancy,
not wall-clock or continuous occupancy duration. No costly spatial scoring is used.

Repeated deterministic games establish reproducibility, not sample diversity or
statistical playing strength. Side outcomes expose asymmetry without correcting
it. Self-play and cross-provider matches sample different subsequent states.
Probe and match inference distributions should be interpreted separately.

## Provenance, files, hashes and replay

Every run manifest records `arena-benchmark-v1`, `arena-probes-v1`,
`arena-rules-v2`, `arena-scenario-v1`, `arena-turn-prompt-v1`,
`arena-turn-plan-schema-v1`, provider/model/profile and local Git revision/dirty
status. A hash inventory of backend Python and JSON source captures uncommitted
source independently of Git. No GitHub operation is needed. Saved versions never
say `latest`. Baseline model settings identify `qwen-config-v1` / `luna-config-v1`;
runtime overrides get a concrete content-derived configuration ID plus exact
allowlisted inference settings. API keys and credential-bearing settings are
excluded. The source manifest hashes file contents; it does not embed them.

```text
summary.json
report.md
runs/run-001/                 # matches
probes/<name>/<provider>/run-001/
  manifest.json
  initial-snapshot.json
  observations.jsonl
  plans.jsonl
  commands.jsonl
  inference.jsonl
  positions.jsonl
  final-snapshot.json
  verification.json
  result.json
```

Plans retain observation hash, typed plan, AP, static validation, repair count,
provider/profile and execution/truncation details. `inference_index` joins a plan
to its call telemetry; failed calls may have an observation but no accepted plan.
`command_start`/`command_end` locate its exact command-result rows. No chain of
thought is stored. Commands are the authoritative deterministic replay evidence.

SHA-256 hashes use canonical JSON arrays/objects (not JSONL newline bytes): initial
and final snapshots, observation trace, plan array, behavioral plan trace,
command array, full command trace and player-turn/AP boundaries. Behavioral
hashes exclude timers, request IDs, model profiles and repair telemetry. The
behavioral plan projection is explicit in `run_trial`; raw plan rows can contain
different provenance while producing identical gameplay hashes.

Every completed trial and failed-trial prefix is read back from disk and replayed
with the unchanged command replay engine. This checks every command result,
state hash and combat/AP counter, final snapshot and winner. An independent
fresh execution of the saved plans checks observation equality, attempted
actions/truncation, command boundaries and terminal AP. Replay failure marks the
trial invalid and aborts the schedule. `verify_trial(Path(...))` is available
for later offline verification of a saved trial directory.

## Live commands: authorization required before execution

No live provider request was made during implementation. These six commands are
prepared for a separate authorization decision. Each baseline command includes
its own preflight; earlier standalone preflight does not bypass it. Full matches
can be long: four games permit up to 800 planning calls at the default bound,
plus repairs, although victory normally stops earlier. All-probe runs make 28
trial planning calls plus preflight and possible repairs.

Qwen preflight only (one request, zero trials):

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --blue-provider ollama --red-provider ollama --preflight-only --output .local/arena-qwen-preflight
```

Luna preflight only (one request, zero trials):

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --blue-provider openai --red-provider openai --preflight-only --output .local/arena-luna-preflight
```

Qwen full-match baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode matches --blue-provider ollama --red-provider ollama --games 4 --turns 100 --output .local/arena-qwen-matches
```

Luna full-match baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode matches --blue-provider openai --red-provider openai --games 4 --turns 100 --output .local/arena-luna-matches
```

Qwen tactical probe baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider ollama --probe all --probe-trials 4 --output .local/arena-qwen-probes
```

Luna tactical probe baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider openai --probe all --probe-trials 4 --output .local/arena-luna-probes
```

Later head-to-head comparisons can use `--blue-provider ollama --red-provider
openai --side-swap`. No live baseline or tuning is part of Phase 5 implementation.
