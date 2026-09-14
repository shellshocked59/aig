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

`--prompt-version arena-turn-prompt-v1` explicitly reproduces the established
prompt; `--prompt-version arena-turn-prompt-v2` selects the Phase 6B prompt-only
experiment. Omission, `latest`, and `v1` resolve to concrete V1; `v2` resolves to
concrete V2. Unknown versions fail before provider construction or output creation.
Injected model factories for V2 must accept the `prompt_version` keyword and
expose the same concrete version; a mismatch fails before any request.
The [V2 experiment design](arena-prompt-v2-experiment.md) specifies the next
probe-only run and its stop point. Normal gameplay defaults remain V1.

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
`arena-rules-v2`, `arena-scenario-v1`, the concrete selected prompt version,
`arena-turn-plan-schema-v1`, provider/model/profile and local Git revision/dirty
status. A hash inventory of backend Python and JSON source captures uncommitted
source independently of Git. No GitHub operation is needed. Saved versions never
say `latest`. Baseline model settings identify `qwen-config-v1` / `luna-config-v1`;
runtime overrides get a concrete content-derived configuration ID plus exact
allowlisted inference settings. API keys and credential-bearing settings are
excluded. The source manifest hashes file contents; it does not embed them.

The immutable `arena-benchmark-v1.json` still names the V1 prompt. New manifests
keep that methodology/spec hash and distinguish the base recipe using
`baseRecipePromptVersion`, actual `promptVersion`/`promptHash`, and
`experimentOverrides` (`{"promptVersion":"arena-turn-prompt-v2"}` for V2,
empty for V1). This identifies a prompt override of the frozen recipe, not an
unchanged execution of that recipe. No `arena-benchmark-v2` is introduced.
Plan rows, inference rows and preflight diagnostics carry concrete prompt/schema
versions. Historical files are never updated or made dependent on `latest`.

Observation-only experiments add `--observation-version arena-observation-v2`,
used alongside `--prompt-version arena-turn-prompt-v2`. The observation override
applies to the built-in preflight and every trial; omitted/default/latest remains
`arena-observation-v1`. New manifests also record `observationVersion` and
`baseRecipeObservationVersion`, with `experimentOverrides.observationVersion`
when V2 is selected. Plan/inference/preflight rows carry `observation_version`.
The immutable recipe and probe artifacts retain their V1 observation hashes;
selected V2 observations have their own hashes. Historical manifests without the
field are interpreted as V1 during replay, never as latest. See the
[Phase 7A report](arena-observation-v2-experiment.md) for offline measurements,
future A/B metrics, exact unexecuted commands and request ceilings.

New plan rows also include passive `starting_legality` measurements, repeated in
trial results: `first_action_starting_legal` (null for an empty plan),
`starting_legal_prefix_length`, and `starting_action_membership`. Membership uses
the exact actor, action type and target/destination from the starting observation.
It does not simulate, reject or alter a plan. A later starting-legal action may
fail during execution; a newly legal action can be absent from the starting list.
These measurements are separate from the frozen Phase 5 metrics and behavioral
hashes. They can also be recomputed for historical accepted plans with
`aig.arena.prompt_metrics.starting_legality` without rewriting V1 evidence.

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
.venv/Scripts/python.exe -m aig.arena.benchmark --blue-provider ollama --red-provider ollama --prompt-version arena-turn-prompt-v1 --preflight-only --output .local/arena-qwen-preflight
```

Luna preflight only (one request, zero trials):

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --blue-provider openai --red-provider openai --prompt-version arena-turn-prompt-v1 --preflight-only --output .local/arena-luna-preflight
```

Qwen full-match baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode matches --blue-provider ollama --red-provider ollama --prompt-version arena-turn-prompt-v1 --games 4 --turns 100 --output .local/arena-qwen-matches
```

Luna full-match baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode matches --blue-provider openai --red-provider openai --prompt-version arena-turn-prompt-v1 --games 4 --turns 100 --output .local/arena-luna-matches
```

Qwen tactical probe baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider ollama --prompt-version arena-turn-prompt-v1 --probe all --probe-trials 4 --output .local/arena-qwen-probes
```

Luna tactical probe baseline:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider openai --prompt-version arena-turn-prompt-v1 --probe all --probe-trials 4 --output .local/arena-luna-probes
```

Later head-to-head comparisons can use `--blue-provider ollama --red-provider
openai --side-swap`. No live baseline or tuning is part of Phase 5 implementation.

## Stepwise benchmark v2 (Phase 7B)

Full-turn experiments remain `arena-benchmark-v1`. Explicit
`--control-mode stepwise --mode probes` selects `arena-benchmark-v2`,
`arena-control-stepwise-v1`, `arena-step-prompt-v1`, Observation V2 and the unchanged
plan schema/probes/model profiles. V2 currently supports probes only; it controls
the remainder of one player turn, rebuilding observations after each action.
New manifests record control mode/version. Historical files are not rewritten.

Offline reference command (no external inference):

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --control-mode stepwise --mode probes --blue-provider heuristic --probe all --probe-trials 1 --output .local/arena-stepwise-offline-reference
```

V2 stores per-decision observations, accepted decisions, current legality, AP,
telemetry, repairs and state hashes in each `turn.json`. Command-only replay and
independent step-boundary verification remain authoritative. Failed turns stop the
schedule and remain in reliability denominators, without heuristic fallback.
Catalog-member execution failures are harness/domain defects, not model sequencing.

Compare total latency/tokens/cost per player turn as well as per decision. Explicit
dated `--pricing` JSON enables Luna cost estimates; missing pricing/usage remains
null. `--request-ceiling` rejects schedules above the supplied theoretical bound
before provider construction. Seven probes at one trial require at most 71 requests
per model including preflight/repairs; four trials require at most 281.

See [Phase 7B experiment](arena-stepwise-control-experiment.md) for exact proposed
commands, reference results, pricing format and the live authorization stop point.

## Phase 8A repair experiment preparation

The separately versioned `arena-step-repair-v2` adds factual rejected-decision diagnostics. Normal stepwise defaults remain `arena-step-repair-v1`; historical manifests without `repairVersion` mean V1. The dedicated `python -m aig.arena.repair_benchmark` measures one repair inference per fixed invalid response using `arena-repair-challenges-v1`, not tactical gameplay or first-response validity. No live A/B has been run. See [repair V2 experiment preparation](arena-repair-v2-experiment.md) for safe evidence capture, offline tests, provenance, request ceilings, and the prepared Qwen commands awaiting authorization.

## Experimental action-ID probes

The separate aig.arena.action_id_benchmark entry point uses arena-benchmark-v4, because arena-benchmark-v3 already identifies the frozen structured full-match orchestrator. It keeps arena-probes-v1 and model profiles unchanged, has no preflight or full-match mode, and enforces per-attempt request accounting. See [Phase 9A](arena-action-id-control-experiment.md) for offline replay results and the prepared seven-turn, 70-request Qwen pilot. Live execution requires separate authorization.

Phase 10A freezes `arena-benchmark-v5` for exact constrained structured control.
Its executable preparation entry point is the offline-only
`python -m aig.arena.constrained_study --output NEW_DIRECTORY`. V1–V4 remain
unchanged. The Qwen context preparation gate is RED; no live runner or command is
prepared. See [Phase 10A](arena-constrained-structured-experiment.md) for exactness
proofs, fake-adapter support, request sizes and the inactive future pilot bound.

## Bounded-replan recipe v6

The additive module aig.arena.bounded_replan_benchmark provides an offline demo, preparation, and explicitly gated live probe runner for strict-versus-bounded control. Previous recipes and runners are unchanged. See [the implementation and proposed commands](arena-bounded-replan-implementation.md) for the four-request smoke and 84-request paired schedule. Both use frozen full-turn prompt/observation V1 and no fallback; no live run has been authorized or performed here.
