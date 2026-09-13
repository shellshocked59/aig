# Arena AI: direct tactical turn planning

Arena supports Heuristic, Ollama/Qwen and OpenAI/Luna tactical providers.
Phase 4 integrates model turns; comparative benchmarks remain Phase 5 work.

```text
ArenaState -> ArenaObservation -> ArenaTurnProvider
                                   |-- Heuristic
                                   |-- Ollama / Qwen
                                   `-- OpenAI / Luna
    -> ArenaTurnPlan -> ArenaTurnExecutor -> immutable Arena commands
```

Empire providers choose high-level strategy for a deterministic tactical
executor, with multi-turn plan continuity. Arena providers choose the actual
tactical action sequence for one turn. `create_turn_plan(observation)` is called
**once per AI turn**, with no previous plan. The completed plan is returned
before the real turn begins execution.

## Execution contract: invalid action means truncate and End Turn

**Actions execute sequentially. If an action is invalid, record its index,
payload and engine error, stop the plan, retain all earlier valid actions, and
automatically End Turn if the battle is nonterminal.** Never skip to a later
action, roll back, repair, retry, or ask the provider to replan.

After a successful plan, the executor also issues the normal `ArenaEndTurn`
command, including when zero AP remains or the plan is empty. On victory it
stops immediately and does not End Turn. An ignored suffix records `terminal`
truncation; a winning final action needs no truncation. An invalid action records
`invalid_action`. The executor reports available/spent/unused AP before End Turn
resets the next player's allowance. Unspent terminal AP is included in AI metrics.

Structural plan errors are rejected before executing any action. Five AP is the
static schema budget; a plan that exceeds the *current remaining* AP is rejected
at the first unaffordable action through the same sequential rule. Model adapters
add static validation against remaining AP before returning a plan. Provider
repair and normal-game fallback occur before execution, as described below.

## Observation and local schema

`ArenaObservation` stores canonical JSON text in a frozen dataclass. `to_dict()`
returns a fresh JSON-compatible object; no engine state, mutable nested object,
Empire object or Position is stored inside the observation. `from_dict()` also
recomputes engine facts and rejects inconsistent observation metadata.

The `arena-observation-v1` shape contains:

- `environment`, `rules_version`, `scenario_version`, `turn`, active player, AP,
  player order/identities and winner (null for a plannable turn).
- `own_team` and `enemy_team`, each with `player_id`, Core and sorted units.
  Units include status (active/downed), class, position, HP/max HP, class stats,
  ability costs/ranges and current authoritative legal action options.
- A 9x5 row-major board with terrain and bonuses, plus factual special-damage,
  healing, splash, shove and bonus-modifier metadata.

Legal options describe the observation's initial state only. Enemy/downed units
have empty legal options. Earlier planned actions can change later legality.
There are no threat scores, preferred actions or reasoning fields in observations.

`ArenaTurnPlan` is a frozen dataclass with `schema_version` and an immutable
`actions` tuple. The wire format is:

```json
{
  "schema_version": "arena-turn-plan-schema-v1",
  "actions": [
    {"type": "move", "unit_id": "blue-ranger", "destination": {"x": 3, "y": 2}},
    {"type": "attack", "unit_id": "blue-ranger", "target_id": "red-knight"}
  ]
}
```

Eight explicit variants are Move, Attack, Heal, Finish, Revive, ShieldBash,
Snipe and Fireball. Move has `destination`; Fireball has `target_position`;
other actions have `target_id` (Attack can identify a unit or Core). Each has
`unit_id`. The executor supplies the actor ID. No EndTurn action is accepted.
Positions are strict integer coordinates in the fixed board, IDs are nonblank
strings, unknown/extra fields are rejected, and a plan permits zero to five
actions whose static costs sum to at most five AP.

`turn_plan_schema()` returns a fresh local JSON Schema using `oneOf` and explicit
discriminators. The cost sum is additionally validated by `ArenaTurnPlan`; JSON
Schema's item-count limit alone cannot enforce mixed one/two-AP costs. Both
model adapters report this same logical v1 contract.

## Heuristic baseline

`arena-heuristic-v1` reconstructs a detached ArenaState from observation facts.
At each simulated action it obtains the actual legal options, scores candidates,
applies the chosen immutable command through `apply_command`, and repeats until
AP runs out, victory occurs, or no worthwhile action exists. This is a greedy
planner with exact rule simulation, not a separate combat model or game-tree
search. It cannot mutate the real state.

Lexicographic priorities are explicit in `heuristic.py`:

| Tier | Action preference |
| --- | --- |
| 10000 | Immediate victory; a winning Core attack wins a tie |
| 9000 | Remove all obvious one-basic-attack threats to our Core |
| 800 | Finish an adjacent enemy body |
| 700 | Revive an ally |
| 600 | Down an enemy, including efficient lethal Fireball |
| 500 | Efficient multi-target Fireball |
| 450 | Bash that shoves from a bonus or farther from our Core |
| 350 | Distant Snipe outside basic range |
| 300 | Heal at least three missing HP |
| 250 | Basic unit damage |
| 200 | Core pressure; actual damage favors POWER/SIEGE |
| 100 | Move to a useful attack, support or bonus position |
| 1 | Small heal if otherwise idle |

Finish/Revive/lethal target values rank Cleric, Mage, Ranger, Knight. Lethal ties
prefer lower HP; healing prefers most missing HP, then lowest current HP ratio.
Comparable basic lethal attacks beat two-AP Snipe. The final ties prefer lower
AP cost and canonical action JSON, making IDs and coordinates stable independent
of dictionary/set insertion order. No randomness is used.

Fireball utility is actual enemy damage + 12 per enemy down - twice friendly
damage - 40 per friendly down. It needs positive utility and either two enemy
hits or an enemy down. Nonwinning Fireball with a friendly down is rejected;
small friendly damage can be worthwhile. A terminal enemy victory always beats
the heuristic's ordinary damage tradeoffs; a self-defeating cast is rejected.

Movement evaluates useful attack/support squares and POWER/WARD/SIEGE bonuses,
subtracts route length, and takes the next class-range segment of the engine's
deterministic BFS path. Legal destinations are rechecked against engine queries.
Within-turn visited positions prevent backtracking. Finish is not a remote
movement objective. This heuristic can overextend and has only a narrow one-hit
Core defense check; it is a baseline, not an optimal opponent.

## Controller, browser and headless use

`ArenaAiController.run_turn(simulation)` builds one observation, requests one
plan, runs the sequential executor through `ArenaSimulation.execute`, and returns
`ArenaAiTurnTrace`. Controller identities are explicit `human`, `heuristic_ai`, `ollama_ai`, or `openai_ai`
values in separate session/run configuration. Names and IDs never imply AI.
This preserves byte-for-byte game snapshots and allows the same layout to be
played manually, Human vs Heuristic, or Heuristic vs Heuristic.

`advance_until_human()` runs consecutive AI turns until a human or terminal state.
For AI-only callers it also accepts an explicit `max_ai_turns` safety bound
(default 200); reaching it returns the completed traces with the state still
nonterminal. The headless runner separately reports its global-round bound as
`turn_limit`, never as an in-game draw.

The browser retains **Arena Demo** and adds **Arena Human vs Heuristic**.
`POST /api/arena/demo-ai` assigns Blue to the human and Red to the heuristic.
Human End Turn synchronously executes Red's turn inside the session lock and
returns the resulting human/terminal state. All controls are disabled and
**AI turn...** is displayed while awaiting that request. Gameplay controls also
respect explicit active AI ownership. There are no client-side rules or AI
action animations. DTOs include `controllers` and the latest request's
`ai_turns`; `GET /api/arena/trace` still returns the ordinary command trace.

```sh
python -m aig.arena.simulate
python -m aig.arena.simulate --max-turns 100 --output .local/arena-ai-match.json
python scripts/arena-ai-verify.py
```

The fixed scenario is `arena-scenario-v1`. `--max-turns` counts completed global
rounds, not individual player turns; 100 permits at most 200 player turns.
Output distinguishes global rounds from player turns, prints winner/Core/unit
and tactical metrics, and writes complete evidence with `--output`. Each run
replays its command trace and verifies exact equality. The verification script
records four identical runs, probes and the local JSON Schema under
`.local/arena-phase3-verification/` by default.

For actual HTTP plus DOM verification against an isolated local server:

```sh
python -m uvicorn aig.api:create_app --factory --host 127.0.0.1 --port 8013
node scripts/arena-ai-smoke.mjs http://127.0.0.1:8013
```

## Trace, metrics and replay

`arena-ai-trace-v1` records turn/player, observation hash, provider identity,
plan/schema/hash, attempted actions (AP before/after, execution status/error),
executed commands, invalid action, truncation, AP available/spent/unused, final
active player/winner, and resulting Core/unit summaries. No reasoning is recorded.
AI runtime state and diagnostics never enter snapshots or command-trace schemas.

Per-player match facts include turns taken, AP available/spent/unused and average,
counts for each of eight actions, actual damage dealt/received, healing (including
Revive), downs/revives/finishes, Core/friendly-fire damage, bonus-tile offensive
actions, Bash pushes, Fireball victims, active/downed/removed units, HP/Core HP,
winner, planned/executed/invalid action counts, truncated turns and zero-action
turns. Victory duration records player turns; global rounds are separate.

Existing combat counters retain Phase 2 meanings: damage/downings include
friendlies, separate friendly-fire damage disambiguates them, and bonus usage
counts offensive actions from bonus tiles. Damage received includes friendly
damage suffered. AI unused AP includes terminal leftovers, while the unchanged
command trace counts only AP discarded by End Turn. There is no quality score.

Replay uses `arena-trace-v2` commands alone; no provider is required. Plan
determinism is independently measurable, but recorded commands guarantee match
reproduction. Rules, snapshots, commands and replay retain their v2 versions;
the frozen Arena v1 package and all Empire versions/providers are unchanged.

## Tactical probes and Phase 5 boundary

`create_probe(name)` creates validated, detached fixtures under
`arena-tactical-probes-v1`: `finish_or_core`, `revive_decision`,
`fireball_friendly_fire`, `shield_bash_position`, `snipe_vs_basic`,
`winning_core_line`, and `team_elimination`. Tests check intentional first-action
priorities and complete legal plans. They are not additional gameplay scenarios.

**Finish cannot immediately win a valid Phase 2 battle.** Removing a downed body
does not change active-unit counts, and zero active units already ends the game.
The elimination probe therefore contains an optional adjacent Finish and a
winning attack on the last active enemy; the winning attack must be chosen.

Phase 4 implements both model providers without changing the sequential executor.
No model scoring, comparative benchmark, tournament, prompt tuning or model tuning
is included. Future strict benchmarks must reject runs contaminated by fallback.

See [Phase 3 verification](arena-phase3-verification.md) for results and hashes.

## Model providers (Phase 4)

`create_arena_turn_provider(settings, provider_name)` constructs independent
`OllamaArenaTurnProvider` and `OpenAIArenaTurnProvider` adapters or the existing
heuristic. Providers receive settings at construction and never load environment
variables. A small Arena-only base handles bounded repair and telemetry. Shared
Empire imports are limited to JSON parsing, HTTP transport, error categorization,
usage extraction and immutable model profiles; no Empire planning behavior changed.

`arena-turn-prompt-v1` is frozen in `arena/ai/prompts.py` with an immutable registry
and a SHA-256 regression test. It describes perfect information, ordered actions,
the AP budget/costs, movement/LOS, unit status, basic/special actions, bonuses and
victory. It asks only for a plan, with no reasoning, strategy explanation, priorities,
recommended targets or model-specific coaching. The exact same prompt and complete
canonical `ArenaObservation`, including current legal action options, go to both
models. There is no previous plan, conversation ID or tactical heuristic beneath
a model. One provider invocation occurs per turn; a successful first response uses
one inference request, and static-invalid output may use one additional repair.

Ollama posts canonical compact UTF-8 JSON to the configured `/api/chat` with:

- `model`, `keep_alive`, `stream=false`, `think=false`;
- `messages`: system prompt plus canonical observation;
- `format`: the concrete logical v1 JSON Schema;
- `options`: `num_ctx`, `temperature`, `seed`, `num_predict` from settings.

OpenAI uses the installed official synchronous SDK, explicit injected API key,
configured timeout, `max_retries=0`, and `client.responses.create` with:

- configured `model`, `reasoning.effort`, `max_output_tokens`;
- `instructions`: Arena prompt; `input`: current observation messages;
- `store=false`; no persistent conversation or previous response;
- `text.format`: `type=json_schema`, `name=arena_turn_plan`, `strict=true`.

The OpenAI wire schema replaces disjoint `oneOf` action branches with `anyOf`,
string `const` values with typed single-value enums, and removes schema metadata
and string constraints from the provider subset. It does not alter the logical
`arena-turn-plan-schema-v1`: the authoritative application parser still rejects
missing/extra fields, blank IDs, booleans as coordinates, unknown variants and
mixed-cost AP overflow. The Ollama schema is the original concrete schema.
No live provider acceptance is claimed by offline tests.

### Static invalidity versus execution invalidity

Category A is rejected before commands: malformed JSON (including duplicate keys
and nonfinite values), invalid schema/action variant, unknown actor or target,
wrong team/target class, out-of-board position, unavailable class ability, or AP
overflow. The adapters construct a real `ArenaTurnPlan`; raw dictionaries are never
executed. Errors are fixed sanitized categories, never provider text or tracebacks.

One repair is allowed for Category A. It receives the same observation and schema
plus the concise category and a correction request. The invalid raw text is retained
only in the bounded private trace, not echoed into the repair request. A second
invalid response raises `repair_failed`. Transport, authentication, refusal and
malformed provider envelopes fail immediately with no transport retries.

Category B occurs in the unchanged executor. Status, range, LOS and occupancy can
change during a turn, so adapters do not require every action to appear in the
initial legal options. Revive then act, Move then attack, and Attack then Finish
remain expressible. If a later action fails, the valid prefix stays committed,
the remaining suffix is discarded, and the engine ends the nonterminal turn.
**No second model call, repair, action substitution, reordering or fallback occurs
because of execution truncation.**

`ArenaAiController` catches only sanitized provider failures before execution and
requests a complete heuristic plan for that turn. It then uses the same executor.
This is normal-game fallback, not a strict benchmark policy. Missing OpenAI keys
also fail at this boundary with `authentication_failure`, without an API call.
Unexpected programming exceptions are not silently hidden as heuristic success.

### Inference diagnostics and secrets

Only model turns add an `inference` sidecar to the existing Arena AI turn trace;
pure heuristic trace bytes and hashes stay unchanged. `arena-inference-trace-v1`
records turn/player, requested/actual provider, fallback flag, error category,
model, prompt/schema versions, configuration/profile provenance, observation hash,
validated/resulting plan, retry count and total wall-clock request seconds.

At most two attempt records retain up to 32,768 characters of redacted raw content,
request latency, validation/error category, and allowlisted metrics. OpenAI request
and response IDs are redacted and capped at 200 characters. Reasoning content,
headers, credentials, provider exceptions and complete settings are never recorded.
`last_trace` and returned turn traces are detached copies; a provider retains only
its latest invocation. Browser DTOs omit attempt records entirely and display
executed/invalid actions plus visible fallback provenance, never model reasoning.

Ollama metrics: `prompt_eval_count`, `eval_count`, `prompt_eval_duration`,
`eval_duration`, `total_duration` (provider durations are nanoseconds).
OpenAI metrics: `input_tokens`, `cached_input_tokens`, `output_tokens`,
`reasoning_tokens`, `total_tokens`. Metrics are per attempt; wall-clock seconds
are also summed across attempts. Counts/durations must be nonnegative integers.

The profile is reported as `qwen-config-v1` or `luna-config-v1` only if runtime
inference settings exactly match that frozen profile; otherwise it is null and
the actual allowlisted configuration is recorded. Profiles were not modified.
No benchmark manifest/version or snapshot change is introduced. Inference data
never enters `arena-snapshot-v2` or command replay.

### Settings, browser and headless operation

In the ignored local `.env`, for example:

```dotenv
AIG_STRATEGY_PROVIDER=ollama
AIG_ARENA_TURN_PROVIDER=openai
AIG_OLLAMA_BASE_URL=http://10.0.0.250:11434
OPENAI_API_KEY=your-local-key
```

The committed default for both selectors is `heuristic`. Nonempty process values
override `.env`, then defaults. A key or host alone never selects a model.

The browser preserves Manual and Human vs Heuristic, adding Human vs Qwen,
Human vs OpenAI (Luna), and Human vs Configured AI. The latter resolves only
`AIG_ARENA_TURN_PROVIDER`. Routes are `/api/arena/demo-ai/ollama`, `/openai`, and
`/configured`; the existing `/api/arena/demo-ai` stays heuristic. Human End Turn
waits for Python to finish the AI turn; controls are disabled with `AI turn...`.
JavaScript only calls the Python API.

```powershell
# Offline default even when .env selects an Arena model:
.venv/Scripts/python.exe -m aig.arena.simulate --max-turns 100
# Explicit provider support, for separately authorized manual runs:
.venv/Scripts/python.exe -m aig.arena.simulate --red-provider ollama --blue-provider heuristic --max-turns 1
```

Both `--red-provider` and `--blue-provider` accept `heuristic|ollama|openai` and
default to heuristic. Headless execution uses the normal fallback policy and
records contamination visibly. The existing bound, counters and exact command
replay remain; no comparative experiment/reporting layer was added.

### Manual smoke commands

These opt-in commands make **at most one inference request**, disable repair,
never invoke fallback or execute a battle, and return nonzero on invalid output
or provider failure. The default fixture is `snipe_vs_basic`; `--probe` selects any
of the seven existing tactical probes. Successful output prints the sanitized
plan, AP total, profile/prompt/schema provenance, latency and token metrics.
A configuration failure can stop before any request.

```powershell
.venv/Scripts/python.exe -m aig.arena.ollama_smoke
.venv/Scripts/python.exe -m aig.arena.openai_smoke
```

Neither live smoke was run during Phase 4 implementation. Tests invoke the shared
helper only with fake clients. Real smoke requests require separate authorization.
Frozen output limits remain 256 (Qwen) and 512 (Luna). Offline serialized-size
checks do not prove tokenizer-specific fit, model compliance or server schema
acceptance; those remain explicit live-smoke checks before Phase 5. No profiles
were increased or tuned to address hypothetical failures.
