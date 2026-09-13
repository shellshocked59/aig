# Ollama strategic provider implementation report

This slice adds local Qwen strategic planning, strict response validation, one
repair attempt, controller-level heuristic fallback and Human vs LLM browser play.
It changes no gameplay rules, executor tactics, StrategicPlan fields or snapshots.

## Architecture found and retained

The checkout had 499 Python tests and 26 frontend tests. `StrategicStateBuilder`
returns a detached JSON-compatible TypedDict. `StrategyProvider` is synchronous:
`create_plan(state, previous_plan=None) -> StrategicPlan`. The frozen plan has six
fields. `AiController` owns previous-plan storage, five-global-turn reuse and
target invalidation. `AiOrchestrator` runs activations through `AiExecutor`, which
issues existing commands. `GameSession` owns the in-memory runtime under a lock;
FastAPI exposes it to plain JavaScript. Snapshot schema was and remains v8.

`OllamaStrategyProvider` implements that same contract. It receives only the
compressed strategic state and previous plan, never GameState or command access.
The deterministic executor file and activation result representation are unchanged.
Priorities retain their existing semantics: ordered preferences can include
future unlocks and already-known technologies. The prompt supplies all valid
priority enum options; the executor selects currently legal choices.

## Files changed by this slice

| Files | Change |
| --- | --- |
| `backend/aig/ai/ollama.py` | Injectable HTTP provider, versioned prompt, bounded repair, latest inference trace |
| `backend/aig/ai/plan_schema.py` | Concrete schema, canonical JSON, strict plan and reference validation |
| `backend/aig/ai/ollama_smoke.py` | Opt-in single-plan and short headless live checks |
| `backend/aig/ai/strategy.py`, `backend/aig/ai/__init__.py` | Controlled provider error, provider name and exports |
| `backend/aig/ai/controller.py` | Explicit fallback, provenance summaries and bounded trace history |
| `backend/aig/application.py`, `backend/aig/api.py` | Injected settings, explicit LLM demo and compact API metadata |
| `backend/aig/settings.py`, `.env.example` | Positive finite 20-second timeout default |
| `frontend/src/js/api/game.js`, `frontend/src/js/game.js` | Relative LLM API route and Human vs LLM option |
| `tests/test_ollama.py`, `tests/test_settings.py` | Offline contract, transport, fallback, reuse, API and settings coverage |
| `frontend/tests/api.test.js`, `frontend/tests/game.test.js` | Route, mode and pending AI-turn coverage |
| `README.md`, `docs/architecture.md`, this report | Setup, architecture, debugging and verification documentation |

Pre-existing Laragon-related changes in README and `.env.example` were preserved.
Existing `.gitignore`, `config/` and `docs/laragon.md` changes were not part of this
implementation. No dependency, CI workflow or snapshot schema changes were needed.

## HTTP request and versions

The transport uses standard-library `urllib.request` with an injected requester
for tests, no subprocess and no new dependency. It posts UTF-8 canonical JSON to
`{settings.base_url.rstrip('/')}/api/chat`. The following is the exact top-level
shape, with configuration defaults shown and prompt text abbreviated:

```json
{
  "model": "hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M",
  "stream": false,
  "think": false,
  "keep_alive": "10m",
  "messages": [
    {"role": "system", "content": "<strategy-v1 instructions>"},
    {"role": "user", "content": "CURRENT STATE:\n<canonical JSON>\n\nPREVIOUS PLAN:\n<canonical JSON or null>\n\nPRIORITY OPTIONS:\n<canonical JSON>"}
  ],
  "format": {
    "type": "object",
    "properties": {
      "posture": {"type": "string", "enum": ["expand", "defend", "attack"]},
      "primary_enemy_id": {"type": ["string", "null"], "minLength": 1},
      "target_city_id": {"type": ["string", "null"], "minLength": 1},
      "expansion_priority": {"type": "string", "enum": ["high", "low"]},
      "production_priority": {
        "type": "array", "minItems": 1, "maxItems": 5, "uniqueItems": true,
        "items": {"type": "string", "enum": ["settler", "scout", "warrior", "archer", "spearman"]}
      },
      "research_priority": {
        "type": "array", "minItems": 1, "maxItems": 3, "uniqueItems": true,
        "items": {"type": "string", "enum": ["agriculture", "archery", "bronze_working"]}
      }
    },
    "required": ["posture", "primary_enemy_id", "target_city_id", "expansion_priority", "production_priority", "research_priority"],
    "additionalProperties": false
  },
  "options": {"num_ctx": 4096, "temperature": 0.0, "seed": 42, "num_predict": 256}
}
```

`plan_json_schema()` returns a detached copy of the selected frozen logical schema
(`strategic-plan-schema-v1`). Its constraints are:

| Property | Wire constraint |
| --- | --- |
| `posture` | `expand`, `defend`, `attack` |
| `primary_enemy_id`, `target_city_id` | String of at least one character or null; application checks nonblank IDs and references |
| `expansion_priority` | `high`, `low` |
| `production_priority` | Nonempty unique array of UnitType values, maximum length equal to enum count |
| `research_priority` | Nonempty unique array of Technology values, maximum length equal to enum count |

Prompt version: `strategy-v1`. Plan schema version: `strategic-plan-schema-v1`.
The 4096-token context remains intentional for the target 6 GB GPU. The request
uses the schema-valued `format` supported by the official [Ollama chat API](https://docs.ollama.com/api/chat)
and [structured output documentation](https://docs.ollama.com/capabilities/structured-outputs).

## Validation, repair and failure

Successful HTTP is followed by strict top-level JSON and completed message
validation, extraction of string `message.content`, strict inner JSON parsing,
wire-field/type/enum validation, construction of the existing StrategicPlan, then
enemy/player/city and target-ownership checks. Unknown fields, invented enums,
duplicate properties, non-finite numbers and duplicate priorities are rejected.
Nullable targets remain valid. Enemies must occur as owners in supplied enemy
city/unit records; the compressed state has no separate player roster.

Malformed envelopes, JSON, schemas or references permit one additional request
with concise correction feedback and the same schema. A second invalid result
raises `StrategyProviderError`. Connection, timeout, non-success HTTP and unreadable
HTTP responses fail immediately. Neither flow leaks a traceback into prompts.

`AiController` catches controlled failures and invokes the heuristic using the
same state and previous plan. Requested `ollama` and actual `heuristic` remain
explicit, with `fallbackUsed=true`. Fallback plans execute normally and are reused
for the normal interval. A valid young plan causes no request; expired, missing,
rewound or invalid-target plans replan. No executor redesign was required.

`AIG_OLLAMA_TIMEOUT_SECONDS=20` is finite and positive. This is the HTTP client's
blocking socket timeout, not a whole-turn deadline; a repair has its own timeout.
Settings keep non-empty process environment > optional root `.env` > defaults.
Parsing still accepts boolean overrides, but this provider rejects configurations
enabling thinking or streaming before it can issue a request.

## Telemetry and browser behavior

Each inference trace includes state, previous/final plan, exact system content,
serialized inputs and messages for every attempt, raw message content, model and
settings, prompt/schema versions, retries, local request seconds, plus available
Ollama `prompt_eval_count`, `eval_count`, `prompt_eval_duration`, `eval_duration`
and `total_duration`. Ollama durations retain their nanosecond units. Missing
metrics are omitted. Hidden reasoning is never retained.

The controller adds game seed, turn, faction, replan reason, previous plan age,
requested/actual provider and fallback. The provider retains one invocation;
`session.ai.inference_traces` returns detached copies of at most 64 replans.
These records and all provider runtime state are excluded from GameState and v8
snapshots. Reset clears controller history.

The browser offers Hot-seat, Human vs Heuristic AI and Human vs LLM. The LLM
button selects `/api/game/demo/llm`; all browser traffic stays under `/api/...`.
The response's explicit `aiProviders` map identifies the selected provider by
player ID. End Turn disables controls and displays **AI turn...** until Python
completes the AI activation and returns to the human.

`aiActivations` includes plan/command sequence plus requested/actual provider,
model, fallback, duration, retries, reuse, replan reason and plan age. On reuse,
duration/retries are zero while original plan provenance remains visible. Prompt
bodies are available only in backend debugging records, not the ordinary HUD.

## Verification results

Normal tests use mocked requesters/transports and require no Ollama service:

- Python: **531 tests passed**, preserving the original suite and adding 32 tests
  with parameterized subcases for request fields and malformed responses.
- Frontend: **27 tests passed**; `npm.cmd run build` passed.
- `git diff --check` passed.
- Two offline 100-turn heuristic simulations match. An additional direct
  comparison against the original HEAD controller produced identical complete
  simulation results: 200 activations, 3 cities, 20 created units, 94 moves and
  20 attacks. Final state and command-trace hashes are unchanged:

```text
snapshot_sha256: 002a14bb4681f14c6715173f6f82cf57d95cfd3d14bf9a86dfd693ece21f472e
trace_sha256:    30d0a56152bb4ab1b279c1aaf8c04480f4af8d721d54ce420bfbe12dfe790a42
```

Opt-in real-local results on the configured Qwen model:

| Check | Result |
| --- | --- |
| Single representative plan | Valid StrategicPlan, 4.427 seconds wall time, 0 repairs |
| Prompt / generated tokens | 427 / 82 |
| Prompt evaluation / generation | 0.256 / 1.835 seconds |
| Ollama total duration | 4.397 seconds |
| Heuristic-A vs Qwen-B, seed 42, 10 global turns | Valid after every activation |
| Actual Qwen replans / reused plans | 2 / 8 |
| HTTP requests / repairs / fallbacks | 2 / 0 / 0 |
| Mean request and planning duration in simulation | 1.801 seconds |

Commands: `python -m aig.ai.ollama_smoke` and `python -m aig.ai.ollama_smoke --turns 10`.
The first sandboxed attempt could not reach the LAN; the authorized network-enabled
run succeeded. Live checks are not imported into or run by CI. Browser behavior
was verified through API integration and DOM tests, not a manual visual browser run.

## Comparative experiment readiness

No architectural blocker was found for beginning heuristic-versus-LLM experiments.
Both providers now feed the same plan type and deterministic executor, and fallback
provenance is explicit. The live run demonstrates integration and reuse, not model
superiority or long-match inference determinism. Context growth beyond the short
smoke match has not been measured; the current compressed entity lists are not
token-budgeted. For longer experiments, consume/export trace records during the
run because only the latest 64 replans are retained. No model tuning or new game
systems were added.

Arena Phase 4 also uses these connection/model settings through an independent
`OllamaArenaTurnProvider`. `AIG_ARENA_TURN_PROVIDER=ollama` selects Arena's configured
opponent without changing Empire selection. Arena's prompt and tactical plan
schema are separate; see [Arena AI](arena-ai.md#model-providers-phase-4) for its
repair, fallback, telemetry and opt-in one-request smoke command.
