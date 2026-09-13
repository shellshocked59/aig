# Preserved baseline artifact mapping

The original saved heuristic, Qwen and Luna experiments share these independent
artifact versions. This mapping describes their original content; it does not
retroactively claim a new source revision for old runs.

| Domain | Original baseline artifact |
| --- | --- |
| Rules/information environment | `environment-v1` |
| Deterministic starting setup | `scenario-v1` |
| Strategic instructions | `strategy-prompt-v1` |
| Logical six-field plan contract | `strategic-plan-schema-v1` |
| Paired benchmark report format | `benchmark-v1` |

| Baseline | Provider | Model profile | Existing local directory |
| --- | --- | --- | --- |
| Heuristic | `heuristic` | none | `.local/benchmark-heuristic-baseline/` |
| Qwen | `ollama` | `qwen-config-v1` | `.local/benchmark-qwen-baseline/` |
| Luna | `openai` | `luna-config-v1` | `.local/benchmark-luna-baseline/` |

The Qwen and Luna settings were checked against their existing
`.local/qwen-baseline-provenance.json` and `.local/luna-baseline-provenance.json`.
Those sidecars record per-source-file hashes; do not substitute this implementation's
Git revision for the source used in those experiments. Both baselines used a
five-turn replan interval and an action limit of 256. Original operational settings
were a 20-second timeout and, for Qwen, `keep_alive="10m"` and the local LAN endpoint.
The endpoint is runtime host metadata, not part of `qwen-config-v1`.

Existing ZIP SHA-256 values at the time this mapping was added:

```text
benchmark-qwen-baseline.zip  79b77fca96eeea183f4caf30748db076ca690deae59716a991d221df8cfb4101
benchmark-luna-baseline.zip  f21dd59c0004e10db46d94d67ee50791e0670b6567687e8eaef31994e3cce823
```

Saved reports, traces, provenance sidecars and ZIPs remain byte-for-byte untouched.
Do not rewrite verified archives merely to attach new manifest fields. Keep raw
outputs in ignored `.local/` or `benchmark-results/`; commit small metadata such
as this mapping instead. No cloud or Ollama benchmark was rerun for this mapping.

See [experiment selection and provenance](benchmarking.md#experiment-artifacts-and-provenance)
for the exact profiles and new report fields.

## Current measurement status

| Environment | Heuristic | Qwen | Luna |
| --- | --- | --- | --- |
| V1 | measured | measured | measured |
| V2 | measured | **UNMEASURED** | **UNMEASURED** |

The preserved `.local/benchmark-environment-v2/report.md` and
`.local/benchmark-environment-v2-failed-comparison.zip` are the **Environment V2
failed live-provider comparison**, an infrastructure-failure artifact. Valid LLM
trials: **0**. All 164 requested provider calls failed (82 Ollama transport failures,
82 OpenAI connection failures), and four fallback-only simulations completed.
They describe heuristic behavior and provide no evidence about Qwen or Luna model
behavior. Successful replay does not establish provider purity or model validity.
The artifact includes the measured V2 heuristic control under `heuristic/`.

These saved reports, traces, archives and all V1 baselines remain untouched. The
benchmark preflight/purity change does not reinterpret or rerun them. New controlled
experiments must pass every requested live-provider preflight and remain pure
throughout their trials; see [benchmark lifecycle](benchmarking.md).

Environment V2 Qwen and Luna remain unmeasured pending successful authorized provider preflight.

## Scenario V4 (Environment V5)

The latest scenario is now the deterministic four-civilization `scenario-v4`.
Environment V5, snapshot v12, default strategy-prompt-v1, strategic-plan-schema-v1,
luna-config-v1, qwen-config-v1 and benchmark-v1 remain current. Prompt v2 remains
experimental and independently selectable. The browser demo stays on scenario-v3.

See [scenario layout](scenario-v4.md) and [offline verification](scenario-v4-verification.md).
All preserved V1-V3 setup payloads, both prompt payloads, historical reports and
archives remain unchanged. No live inference was run for this slice.
