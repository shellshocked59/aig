# Arena Phase 4 implementation and verification

Implementation completed locally on 2026-09-13, using offline transports and SDK
clients only. No live Ollama/OpenAI request, full model match, benchmark harness,
GitHub operation, deployment or commit was performed. Existing uncommitted Phase
1–3 work was treated as the baseline.

## Files added and changed

Added under `backend/aig/arena/ai/`:

| File | Responsibility |
| --- | --- |
| `prompts.py` | Immutable `arena-turn-prompt-v1` registry and resolver |
| `validation.py` | Static plan validation, sanitized Arena error, OpenAI wire schema |
| `provider.py` | Arena-only one-repair policy and bounded detached telemetry |
| `ollama.py` | `OllamaArenaTurnProvider`, injectable `/api/chat` transport |
| `openai.py` | `OpenAIArenaTurnProvider`, synchronous Responses SDK adapter |
| `factory.py` | Independent centralized Arena provider selection |

Also added `backend/aig/arena/smoke.py`, `ollama_smoke.py`, `openai_smoke.py`,
`tests/test_arena_providers.py`, and this report.

Changed relative to the Phase 3 checkout:

- `backend/aig/arena/ai/controller.py`, `__init__.py`: model exports, explicit
  controller identities, pre-execution fallback and inference provenance.
- `backend/aig/arena/application.py`, `api.py`: settings injection, model/configured
  modes, runtime controller, sanitized browser summaries.
- `backend/aig/arena/simulate.py`: independent Red/Blue provider flags with offline
  defaults and injectable factory; existing replay/counters retained.
- `backend/aig/settings.py`, `.env.example`: independent Arena selector, default heuristic.
- `backend/aig/api.py`: pass application settings to ArenaSession.
- `frontend/src/js/api/arena.js`, `frontend/src/js/arena.js`: explicit modes,
  pending controls and action/fallback summaries.
- `frontend/tests/arena.test.js`: five provider-mode/pending/summary tests.
- `tests/test_settings.py`: expected default settings includes new Arena field.
- `README.md`, `docs/arena-ai.md`, `docs/arena.md`, `docs/ollama-provider.md`,
  `docs/openai-provider.md`: Phase 4 operation and architecture.

## Delivered behavior

Architecture: `ArenaObservation -> ArenaTurnProvider (Heuristic / Ollama / OpenAI)
-> ArenaTurnPlan -> ArenaTurnExecutor`. Models directly choose the tactical
sequence; no heuristic tactical planner runs beneath an accepted model plan.
The provider invocation has no previous plan, and returns the typed plan before
any engine command executes.

`arena-turn-prompt-v1` is the same compact factual prompt for both models: ordered
execution, current/five shared AP budget, supplied IDs/positions/legal options,
action costs, range/stat references, movement/LOS, active/downed status,
Finish/Revive, special damage/friendly fire, bonus references and victory rules.
It asks only for the schema, without strategy explanation, reasoning, priorities
or model-specific coaching. The exact text is in `arena/ai/prompts.py`.
Its UTF-8 SHA-256 is
`5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7`;
an immutable registry and regression test freeze it.

Ollama sends canonical compact JSON to configured `POST /api/chat`, with model,
`stream=false`, `think=false`, keep-alive, context, temperature, seed and output
limit from injected settings, system/observation messages, and the concrete v1
schema in `format`. The transport is injectable for offline tests.

OpenAI uses the installed official synchronous `OpenAI` SDK with explicit key,
configured timeout and zero SDK retries. `responses.create` receives model,
reasoning effort, maximum output tokens, `store=false`, Arena instructions,
observation input, and strict `text.format` JSON Schema. It uses no conversation
or previous response ID. Response envelopes/refusals/completion are checked
before text is parsed, and hidden reasoning is never retained.

Both report `arena-turn-plan-schema-v1`. OpenAI's derived schema uses `anyOf` for
the disjoint action variants, typed singleton enums instead of `const`, and omits
metadata/string constraints from its wire subset. The original parser remains
authoritative for the unchanged logical contract, including strict fields,
coordinates, types and AP sum.

Static validation rejects malformed/duplicate/nonfinite JSON, bad schemas/action
variants, nonexistent actor/targets, wrong team/target class, invalid class ability,
unknown/out-of-board positions and excessive AP. It constructs a real
`ArenaTurnPlan`; no raw dictionaries execute. Status, range, LOS and occupancy
are left to sequential execution because earlier actions can change them.

One additional request may repair malformed/static-invalid output, using the same
observation/schema and a sanitized category. Raw invalid text is not echoed;
there is no traceback or reasoning request. A second invalid response fails as
`repair_failed`. Transport/authentication/envelope/refusal failures do not retry.

Execution invalidity never repairs or triggers fallback. The unchanged executor
keeps earlier commands, records the invalid action, truncates the suffix and ends
a nonterminal turn. A test with two Snipes against one target proves that after
the first downs it, the second truncates with only one model request and exact
command replay. Revive-then-act plans from the existing probe also pass validation.

The controller catches provider errors before execution, selects a complete
heuristic fallback plan for that turn, and passes it through the same executor.
Requested/actual provider, fallback flag and failure category remain visible.
Missing OpenAI credentials use this same fallback boundary with no SDK request.
No accepted model actions are corrected, skipped or reordered.

## Telemetry, settings and user interfaces

Model turns add an `arena-inference-trace-v1` sidecar containing turn/player,
requested/actual provider, fallback/error, model/configuration, profile ID when
matching, prompt/schema versions, observation hash, resulting typed plan,
repair count, total request latency and up to two attempt records. Attempt raw
content is redacted and capped at 32,768 characters; IDs are capped at 200.
Traces are detached, latest-invocation/session-turn data, outside snapshots.
Browser summaries omit raw attempt records and display actions and fallback.

Ollama captures prompt/eval token counts, prompt/eval/total durations in provider
nanoseconds. OpenAI captures input, cached input, output, reasoning and total token
counts, plus safe response/request IDs. Both record request wall-clock seconds.
Token metrics remain per attempt so repair consumption is visible. Exceptions,
headers, hidden reasoning, full settings and API keys are excluded. Canary tests
cover diagnostics, repr/errors, API DTO/snapshot and smoke output; a separate
production-build scan also passed.

`AIG_ARENA_TURN_PROVIDER=heuristic|ollama|openai` defaults to heuristic, independent
of `AIG_STRATEGY_PROVIDER`. Nonempty process environment overrides local `.env`,
then defaults. Connection/key settings alone do not choose a model. Existing
`qwen-config-v1` and `luna-config-v1` values are unchanged; runtime overrides are
recorded as actual configuration with null profile ID rather than falsely claiming
frozen-profile compliance.

Manual and Human vs Heuristic are preserved. Browser modes add Human vs Qwen,
Human vs OpenAI (Luna), and Human vs Configured AI. All requests go through Python;
End Turn displays `AI turn...` and disables controls until Python returns. Routes
include `/api/arena/demo-ai/{ollama|openai|configured}`.

Headless `--red-provider` and `--blue-provider` accept all three providers,
defaulting to heuristic even if `.env` selects a model. Fake providers exercised
both sides with exact command replay. This is normal-game orchestration with
fallback provenance, not a comparative benchmark or strict experimental run.

## Preservation and verification

Baseline suite: **991 tests: 986 passed, five existing skips**; **71 frontend tests
passed**. Added coverage includes **34 Python provider tests** with parameterized
provider/probe/error cases and **five frontend tests**. The existing settings test
was updated only for the added default field.

Final Python suite: **1,025 tests: 1,020 passed, five existing skips**, in 130.401
seconds. This includes all preserved Empire and Arena regression tests.
Frontend: **76 passed, zero failures**. Production frontend build: **passed**.
No test made a live inference request; new provider tests guard both network paths.

All five Phase 3 heuristic hashes are unchanged:

| Artifact | SHA-256 |
| --- | --- |
| Plans | `5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c` |
| Commands | `88328e37527ddb68abf63b091613f7c1282a4581ebe72da394511838b3e6f0ae` |
| Final state | `01720d448acca31206574e16fa3182ffc5c2a40e033e89d5043d56fb21939f2a` |
| Command trace | `6b7c60fbb3d8dcd8451e0692bd764135a5c1b31c5abd35dbcc1101042b6f4f5d` |
| AI traces | `9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1` |

The unchanged heuristic match ends with Red winning after ten player turns;
replay is exact. Baseline inventory contains 2,364 readable backend/test/docs/local
files, including **2,228 pre-existing local artifacts**, with zero local artifact
changes/removals. All Empire AI provider/prompt/schema/profile source files,
Arena frozen v1 code, current rules/state/observation/plan schema/heuristic/executor,
commands, scenarios, snapshots and replay files are unchanged. Only settings
injection touches the shared application path. No snapshot bump was required:
`arena-rules-v2`, `arena-snapshot-v2`, `arena-command-v2`, `arena-observation-v1`
and `arena-turn-plan-schema-v1` retain their current values.

Evidence lives in `.local/arena-phase4-verification/`: baseline inventory, before/
after Python logs, frontend/build logs, preservation comparison, representative
sizes and heuristic regression hashes. Existing dependency paths that were not
readable were excluded from the inventory and not modified.

## Remaining opt-in verification before Phase 5

A representative five-Move JSON plan is **398 bytes**. Initial observation is
**7,397 bytes**, prompt **1,730 bytes**, and concrete logical schema **2,567 bytes**.
Limits remain Qwen 256 output tokens/context 4096 and Luna 512 output tokens.
These byte counts are not tokenizer measurements. Without a locally available
model tokenizer or authorized live request, comfortable output/context fit and
provider schema acceptance remain unverified. There is no demonstrated need to
change a frozen profile; any observed insufficiency must be reported before
profile changes. No model/profile/prompt tuning occurred.

Finish cannot newly cause victory under the existing immediate zero-active rule;
Phase 3's valid `team_elimination` probe remains the replacement for an impossible
immediate-Finish-win state. No new logical contract or snapshot issue was found.

Exact opt-in commands, from `C:\code\aig`:

```powershell
.venv/Scripts/python.exe -m aig.arena.ollama_smoke
.venv/Scripts/python.exe -m aig.arena.openai_smoke
```

Each uses the default `snipe_vs_basic` probe, disables repair/fallback, makes at
most one inference request, validates a typed plan, and prints plan/AP plus
sanitized latency/token metrics. A configuration failure can prevent the request.
Neither command was run live. Live smoke authorization is the next decision;
Phase 5 and full model matches remain outside this work.
