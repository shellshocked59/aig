# OpenAI strategic planning

`OpenAIStrategyProvider` is a synchronous strategic planner. It receives only
`StrategicState` and an optional prior `StrategicPlan`. The deterministic executor
still chooses legal commands, movement paths, and combat actions. No gameplay,
plan semantics, Qwen options, or snapshot fields change; snapshots remain v8.

```text
GameState -> StrategicStateBuilder -> StrategyProvider
                                      |-- Heuristic
                                      |-- Ollama
                                      `-- OpenAI -> Responses API
          StrategicPlan -> deterministic executor -> existing commands
```

## SDK and request contract

The official `openai>=2,<3` SDK is a normal backend runtime dependency, verified
offline with version 2.54.0. This keeps development and production installation
the same: existing `pip install .[infrastructure]` in the production image includes
the SDK. No key is needed to install, import, start the API, or use other modes.
Construction requires the explicitly resolved `OpenAISettings.api_key`:

```python
client = OpenAI(api_key=settings.api_key,
                timeout=settings.timeout_seconds, max_retries=0)
response = client.responses.create(
    model=settings.model,
    instructions=SYSTEM_PROMPT,
    input=messages,
    reasoning={"effort": settings.reasoning_effort},
    max_output_tokens=settings.max_output_tokens,
    text={"format": {"type": "json_schema", "name": "strategic_plan",
                     "strict": True, "schema": openai_plan_json_schema()}},
    store=False,
)
```

Both providers resolve the shared frozen `strategy-prompt-v1` artifact from
`ai/prompts.py`; its instruction text retains the original `strategy-v1` label.
The canonical current state, previous plan (`null` when absent),
and priority options have identical content; an offline comparison test pins
that equivalence. Each request is self-contained. There is no conversation,
`previous_response_id`, streaming, tools, temperature, seed, or hidden SDK retry.

The provider derives `strategic-plan-openai-v1` from the existing
`strategic-plan-schema-v1` schema, retaining all six required fields, enums,
nullable IDs, array bounds, and `additionalProperties: false`. It omits only
`uniqueItems` and `minLength`, which are not in the documented supported-property
list. This is a wire compatibility adaptation, not a change to the application
contract. `parse_plan` still enforces unique priorities, nonblank IDs, allowed
values, exact properties, valid JSON, and enemy/city references against the input
state. The original schema and parser are unchanged.

The request syntax and schema subset were checked on 2026-09-10 against the
[Responses Python reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create),
[Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs),
and [Python SDK reference](https://developers.openai.com/api/reference/python).
The configured default `gpt-5.6-luna` supports Responses, Structured Outputs, and
reasoning effort `none`, per its
[official model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna).
The provider always passes the configured model; account/model access still needs
an authorized live test.

## Validation and failure policy

Only a completed response without an error is eligible. Messages must also be
completed assistant messages with valid text content; refusals and malformed
content are rejected even when another message contains valid plan text. The
SDK's `output_text` helper extracts text across output items. JSON goes through
the existing parser and strategic-reference
validation before a `StrategicPlan` is returned.

Malformed JSON, schema failures, and invalid references get one repair request.
It supplies the same state/options and concise validation feedback using the
existing Ollama repair wording. A second invalid plan raises
`StrategyProviderError`. Refusal, incomplete/failed response, malformed envelope,
empty output, and SDK/API errors fail immediately; they are not repairable plan
validation failures. SDK `max_retries=0` prevents hidden transport retries.
Unreadable HTTP JSON (including invalid encoding or excessive nesting) is also
translated to a sanitized `malformed_openai_response` failure: the SDK can raise
decoding errors before constructing a response or wrapping them in `APIError`.

Failure categories distinguish authentication, permission, model not available
(HTTP 404), rate limit, timeout, connection failure, other API errors, malformed
response, refusal, incomplete response, empty output, malformed JSON, schema
validation, and invalid strategic references. HTTP status and request ID are
retained where available; server error bodies, headers, and SDK exception chains
are excluded from outward errors. Missing credentials are a selection error
(`provider_not_available`, HTTP 503), preserving any existing game.

Inference fallback stays in `AiController`. It records requested provider
`openai`, actual provider `heuristic`, and fallback used. Successful plans record
actual provider `openai` with no fallback. Reused plans retain their provenance.

## Diagnostics and benchmarks

The provider retains only its latest invocation; the existing orchestrator keeps
at most 64 inference traces. Records include state, prior/resulting plans,
configured/returned model, prompt/schema versions, turn, faction, attempts,
locally measured request duration, retries, and provenance. Raw text is redacted
for accidental key echoes and capped at 32,768 characters per attempt. Refusal
text, reasoning content, SDK objects, headers, and credentials are not retained.

Each attempt captures available nonnegative token counts: `input_tokens`,
`cached_input_tokens` (SDK `input_tokens_details.cached_tokens`), `output_tokens`,
`reasoning_tokens` (SDK `output_tokens_details.reasoning_tokens`), and
`total_tokens`. Missing counts remain missing. Reasoning tokens are a subset of
output tokens; cached tokens are a subset of input tokens. Do not add them twice.

Benchmark `inference.jsonl` retains model IDs, response/request IDs, usage,
latency, validation failures and fallback provenance. It excludes full prompts
and settings objects. `summary.json` adds `openai_usage` statistics and totals
across all attempts, including repairs. `samples` indicates coverage: absent
usage cannot be treated as a known zero cost. Ollama metric names and timing
calculations are preserved. There are no fabricated server timings or hardcoded
prices. Future reporting can apply explicitly dated model pricing to these counts.

## Explicit use

Set `OPENAI_API_KEY` in the ignored local `.env` or the existing server
`/var/www/tca/aig/.env.production`. `AIG_STRATEGY_PROVIDER=openai` selects OpenAI
for **Human vs Configured AI**. **Human vs OpenAI** always selects it explicitly.
Hot-seat, Human vs Heuristic AI, and Human vs LLM (Ollama) retain their meanings.
The browser talks only to Python `/api/...` and never receives the key.

After authorizing live inference, the following smoke command makes exactly one
request with validation, no repair, and no heuristic fallback. It prints a small
JSON result with plan/error, token usage, and wall-clock latency, and returns a
nonzero exit status on failure. Normal tests and CI never run it.

```powershell
.venv\Scripts\python.exe -m aig.ai.openai_smoke
```

The initial cloud baseline uses the existing paired benchmark semantics: two
pairs, with each provider controlling both factions in its own 100-turn run.
Explicit benchmark choices ignore `AIG_STRATEGY_PROVIDER`. Fallback-contaminated
runs are marked `pureProviderRun: false` and displayed as `MIXED`.

```powershell
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b openai --games 2 --turns 100 --output benchmark-results\luna
```

Implementation validation is offline with fake SDK clients and the real SDK
using an in-memory HTTP transport for request serialization, response decoding,
HTTP failures, retry counts, and controller fallback. Live smoke and
baseline measurements remain separate, explicitly authorized actions.
