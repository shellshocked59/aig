# Arena Phase 10B: Ollama schema and context investigation

2026-09-13. **Revised gate: YELLOW. Zero live inference performed.**

For the configured Qwen GGUF on the official Ollama 0.34.0 implementation,
`format` becomes a decoding grammar; its JSON schema is not appended to the
model prompt. The opening request reconstructs to **2,297 input tokens**, with
**1,543 tokens remaining after a 256-token output reserve**. Nine historical
generic-schema opening requests report the same 2,297 tokens.

**The Phase 10A wire-size token estimates were overly conservative because they
counted control metadata that the model does not evaluate.** The prior RED
interpretation is superseded by this investigation, without editing its evidence,
frozen recipe, or runtime contracts. Native grammar acceptance, exact enforcement,
and decoding cost for the new constrained schema remain unmeasured; these keep
the overall pilot gate YELLOW rather than GREEN.

## 1. Scope and installed environment

The question was whether a 19,975-byte opening schema consumes the 4,096-token
context window, independently of the text messages. Authorized work included
metadata requests, source inspection, historical analysis and offline tools.

| Item | Observed value |
| --- | --- |
| Configured endpoint version, `GET /api/version` | 0.34.0 |
| Local `ollama --version` | 0.34.0 |
| Effective model | `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M` |
| `/api/show` format / family | GGUF / `qwen35` |
| Parameters / quantization | 4,326,350,848 / Q4_K_M |
| Model training context metadata | 262,144; **not** the configured request context |
| Effective settings | `num_ctx=4096`, `num_predict=256`, temperature 0, seed 42 |
| Other settings | `think=false`, `stream=false`, keep-alive 10m, timeout 20 seconds |
| `/api/ps` | Empty model list at inspection time |
| Tokenizer metadata | GPT2 byte BPE, `pre=qwen35`, 248,320 tokens, 247,587 merges, no added BOS |

`load_settings().ollama` was checked against committed `Settings().ollama`
defaults; the endpoint and listed model settings match. Credentials and `.env`
contents were not persisted. The sandbox version check failed with WinError
10013; the same read-only check succeeded using approved escalation. Metadata
requests then used those permissions. No model load was requested.

The endpoint is a LAN service. Its executable hash, active GPU/backend library,
server environment overrides and remote logs were not accessible through the
metadata examined. A version string is not a proof of an unmodified binary.
The findings below are strongly version-specific source evidence, corroborated
by retained live telemetry, rather than binary attestation.

## 2. Why Phase 10A was RED

[Phase 10A](arena-constrained-structured-experiment.md) measured canonical HTTP
body sizes. Opening increased from 11,430 to 28,838 bytes when the schema grew
from 2,567 to 19,975 bytes. Dividing the entire constrained body by 4 to 3 yielded
7,210–9,613 estimated input tokens. That was explicitly a conservative gate,
not an observed overflow. This investigation separates message text from schema,
JSON transport escaping, model name, sampling options and other control fields.

## 3. Version-pinned source evidence and request path

Ollama tag `v0.34.0` resolves to commit
`d8ab4b4f0ca24b51d3a46b3bf4f462e58ce66b1f`.
Its [LLAMA_CPP_VERSION](https://github.com/ollama/ollama/blob/v0.34.0/LLAMA_CPP_VERSION)
pins `b10760`, resolved to llama.cpp commit
`0f3a71be15af836d277c9f918adfafb45732677e`.
The [backend build definition](https://github.com/ollama/ollama/blob/v0.34.0/llama/server/CMakeLists.txt)
fetches that revision. All 21 downloaded source files were checked against their
Git tree blob hashes; `sources.json` records immutable URLs and SHA-256 hashes.
No current-HEAD implementation is substituted for these tags.

The native Qwen/Jinja route is:

1. Application adapter constructs system/user messages and a separate `format`.
2. Ollama `ChatHandler` chooses native or rendered chat. Native chat goes through
   `handleNativeChat`, `prepareNativeChatRequest` and
   `truncateNativeChatMessages`.
3. `llamaServerChatRequest` maps `format` through
   `llamaServerChatResponseFormat` into
   `response_format={type:json_schema,json_schema:{name:schema,schema:...}}`.
   Messages remain a separate field. `think=false` becomes the
   `enable_thinking=false` template argument.
4. The internal llama-server chat API extracts this schema separately from the
   messages. `common_chat_templates_apply_jinja` selects the Qwen3-Coder family
   parser by its XML tool markers; this includes Qwen3.5-style templates.
5. `common_chat_params_init_qwen3_coder` renders the prompt with
   `common_chat_template_direct_apply_impl`, then builds a separate PEG response
   parser containing a JSON-schema node. The grammar builder resolves that node
   through `builder.add_schema` and the JSON-schema-to-GBNF converter.
6. The sampler parses the grammar, constrains token candidates and advances the
   grammar state as generated tokens are accepted.

These paths are in [Ollama routes.go](https://github.com/ollama/ollama/blob/v0.34.0/server/routes.go),
[llama_server.go](https://github.com/ollama/ollama/blob/v0.34.0/llm/llama_server.go),
[llama.cpp server-common.cpp](https://github.com/ggml-org/llama.cpp/blob/b10760/tools/server/server-common.cpp),
[chat.cpp](https://github.com/ggml-org/llama.cpp/blob/b10760/common/chat.cpp), and
[peg-parser.cpp](https://github.com/ggml-org/llama.cpp/blob/b10760/common/peg-parser.cpp).
Useful local source anchors: routes.go 2688, 2976, 3074; llama_server.go 2147,
2318; chat.cpp 931, 1162, 3596; peg-parser.cpp 1734.

The alternative Ollama-rendered path also separates these fields:
`chatPrompt`/`renderPrompt` receive messages, tools and thinking controls, **no
format argument**. `Completion` sends its prompt separately from `JsonSchema`.
The older description of Ollama directly calling a Go/CGO `SchemaToGrammar`
function is not the applicable 0.34.0 server boundary.
[Prompt rendering source](https://github.com/ollama/ollama/blob/v0.34.0/server/prompt.go),
[GGUF runner selection](https://github.com/ollama/ollama/blob/v0.34.0/llm/server.go).

Model/version distinctions matter. The pinned llama.cpp DeepSeek V4 path can
expose `response_format` to its template through additional context; the Qwen
path does not. This is not a universal promise about every Ollama backend or
custom template. Tools can also become prompt text, but this request has no
tools. The [official structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs)
separately recommends putting a schema in the prompt for grounding. Our frozen
adapter does not do that, and this investigation does not adopt that suggestion.

## 4. Context, KV occupancy and telemetry

For these Qwen requests, schema bytes contribute **zero prompt tokens** by the
traced path. They do not occupy the model's token/KV context or its input-token
budget. CPU-side grammar data still occupies memory. Grammar constraints can
change generated choices, output length and subsequent observations, so later
requests can differ indirectly; this is distinct from tokenizing the schema.

In 0.34.0, `llamaServerTimings.promptEvalCount()` returns `prompt_n + cache_n`
when the cache count exists, otherwise `prompt_n`. Thus `prompt_eval_count`
includes cached prompt tokens and should not be interpreted as the number of
tokens newly computed in a cold forward pass. It does not count grammar source.
See [timing conversion](https://github.com/ollama/ollama/blob/v0.34.0/llm/llama_server.go#L1504).

## 5. Model template and offline tokenization

Verbose `/api/show` provided the full Jinja template, vocabulary, token types
and BPE merges. The text-only system/user request renders as ChatML role blocks,
then an assistant prefix and the empty thinking block selected by
`enable_thinking=false`. No `format`, `json_schema` or response-format variable
is read by this template. There is no additional model system message in the
observed metadata that needs appending to the supplied system message.

[The offline helper](../scripts/ollama-context-analysis.py) renders that template
using isolated Jinja2, applies the exact Qwen35 pre-tokenization expression from
[llama-vocab.cpp](https://github.com/ggml-org/llama.cpp/blob/b10760/src/llama-vocab.cpp#L382),
then ranked byte BPE using the observed vocabulary/merges. It handles control
and user-defined special tokens and verifies lossless token-to-text round trips.
This is an offline replica, not an invocation of the server tokenizer. Matching
historical counts provide its practical validation. No HTTP body was tokenized
as a proxy for context usage.

| State | Observation bytes | Message-content bytes | Rendered text bytes | Reconstructed input tokens | Headroom after 256 output |
| --- | ---: | ---: | ---: | ---: | ---: |
| Simple Snipe | 3,385 | 4,253 | 4,352 | 1,251 | 2,589 |
| Revive | 3,151 | 4,019 | 4,118 | 1,182 | 2,658 |
| Opening | 6,462 | 7,330 | 7,429 | 2,297 | 1,543 |
| Historical midgame | 3,337 | 4,205 | 4,304 | 1,322 | 2,518 |

Generic and constrained requests have byte-identical messages and identical
rendered prompt hashes. Canonical request and schema sizes reproduce all four
Phase 10A measurements. Prompt text, token IDs, exact request objects and hashes
are retained under `derived/` and `derived-verified/`.

## 6. Historical telemetry and action-ID comparison

The strongest matched comparison is the first Revive state, with equal game
facts and ordered legal actions. Four trials per mode repeat the following:

| Measurement | Structured | Action-ID | Difference |
| --- | ---: | ---: | ---: |
| Canonical request bytes | 7,467 | 5,417 | -2,050 |
| Schema bytes | 2,567 | 125 | -2,442 |
| Observation bytes | 3,151 | 3,613 | +462 |
| Message-content bytes | 4,019 | 4,285 | +266 |
| Rendered prompt bytes | 4,118 | 4,384 | +266 |
| Recorded prompt_eval_count | 1,182 | 1,305 | +123 |
| Reconstructed input tokens | 1,182 | 1,305 | +123 |
| Recorded eval_count | 31 | 9 | -22 |

The schema reduction does not appear as a reduction in evaluated prompt tokens.
The 462-byte observation increase and 196-byte system-prompt decrease explain
the net text increase; the tokenizer reproduces the 123-token increase exactly.
This corroborates the source path, without claiming a schema-only controlled
experiment or attributing tactical differences to one variable.

Across all 36 retained Revive payload reconstructions (16 structured, 20
action-ID), **36/36 reconstructed prompt counts equal the recorded counts**.
After step one, states diverge, so those rows validate reconstruction rather
than provide matched policy comparisons.

Additional history provides nine opening-state matches at **2,297** and nine
midgame matches at **1,322** in Phase 7F/8C stepwise full-match artifacts.
Observation hashes match the Phase 10A representative states. Repeated trials
are not independent state diversity. Historical generic-schema input counts
therefore support the constrained opening estimate without a new model call.

For wider context, Phase 7A full-turn Revive runs recorded 1,626 input / 31
output tokens in four trials, using a different prompt contract. The Empire
baseline contains 80 recorded Ollama attempts with 423–1,198 prompt tokens.
Those samples have different task text and schemas; their complete payloads
were not reconstructed here and they are **not** used to estimate schema cost.
No correlation claim is made from these weaker cross-contract comparisons.
`additional-history.json` preserves locations and telemetry. The precise paired
evidence is in `revive-telemetry.json` and the earlier Phase 9D request artifacts.

## 7. num_ctx, num_predict and truncation

The configured 4,096 is the per-request sequence context, shared by prompt and
generated tokens; it is not 4,096 prompt tokens plus a separate generation
window. `num_predict=256` limits generation, but does not pre-reserve 256 tokens
when Ollama trims messages. Keeping explicit headroom is therefore necessary.

Default chat truncation removes older messages while preserving system messages
and the last message. It can leave an overlong last message. In the native
llama-server route, a completion prompt at or above the slot context is rejected.
In the rendered completion route, Ollama can truncate token sequences when
context shifting is enabled; otherwise an overlong prompt errors. During
generation, enabled/supported context shifting discards older context; with
shifting disabled, generation stops when capacity is exhausted. A successful
HTTP response alone is not proof that all original input was retained.

These are distinct paths, not a guarantee that every model automatically
truncates safely. Active server overrides and hybrid-model memory support were
not observed. No behavior near the limit was tested. The representative opening
is comfortably below all these boundaries.
[Ollama truncation](https://github.com/ollama/ollama/blob/v0.34.0/llm/llama_server.go#L279),
[native context rejection and generation limits](https://github.com/ggml-org/llama.cpp/blob/b10760/tools/server/server-context.cpp).

## 8. Grammar representation and practical cost

JSON Schema is converted into GBNF productions; the native Qwen route additionally
wraps response content in its PEG-derived grammar and accounts for the generation
prefix. `common_sampler_init` creates a grammar sampler, and generated tokens
advance its parse state. Candidate rejection masks logits to negative infinity;
the sampler can initially test a selected token and, if rejected, apply grammar
filtering before resampling. This is a CPU sampling constraint outside the neural
prompt. [Schema converter](https://github.com/ggml-org/llama.cpp/blob/b10760/common/json-schema-to-grammar.cpp),
[sampling](https://github.com/ggml-org/llama.cpp/blob/b10760/common/sampling.cpp),
[grammar state and masks](https://github.com/ggml-org/llama.cpp/blob/b10760/src/llama-grammar.cpp).

The official Python converter at the same pinned llama.cpp revision ran offline:

| State | Legal branches | Schema bytes | Standalone GBNF bytes | Rules |
| --- | ---: | ---: | ---: | ---: |
| Simple | 25 | 8,804 | 21,280 | 270 |
| Revive | 21 | 7,493 | 18,079 | 230 |
| Opening | 54 | 19,975 | 49,248 | 601 |
| Midgame | 11 | 4,215 | 9,951 | 128 |

These are **standalone Python-converter measurements**, not the exact native
Qwen wrapper grammar or its compiled heap footprint. Opening conversion took
about 2.3–4.6 ms in two local runs; this is not an Ollama latency prediction.
There are 55 logical outputs including EndTurn. Whitespace still permits
multiple textual serializations. Fifty-four finite, shallow alternatives are
not by themselves an obvious size blocker, but shared field prefixes may keep
many parse stacks active before branches become distinguishable.

Costs can include JSON parsing/copying, grammar construction and parsing,
CPU memory for rules/stacks, candidate checks and repeated sampler work. Native
prompt sizing itself calls apply-template, so schema processing can also occur
during setup and can repeat while trimming history. Large grammars can increase
setup latency, first-token latency and per-token decoding time. The pinned
sampler also disables incompatible backend sampling when a grammar is present.
The [GBNF guide](https://github.com/ggml-org/llama.cpp/blob/b10760/grammars/README.md)
documents schema-subset limitations and performance pitfalls.

No CPU utilization, native compiled-memory size, first-token latency or native
constrained throughput was measured. C++ compiler acceptance and equivalence to
the exact legal-action language are not proven by the Python conversion.
Phase 10A's application-side equality proof remains necessary but insufficient
to establish server enforcement. These are the material residual uncertainties.

## 9. Decision and proposed one-request experiment — NOT EXECUTED

**YELLOW overall; context fit strongly supported.** RED based on whole-wire
token estimates is no longer justified. GREEN would overstate native grammar
and performance validation. No model/profile/schema changes are proposed.

Propose **one initial opening-state request**, using the retained
`derived/opening-request.json`, with its 54 legal branches, 19,975-byte schema,
28,838-byte canonical body and frozen Qwen settings. Expected prompt count:
2,297; maximum output: 256 tokens. This tests the largest representative schema
with comfortable prompt headroom. It is a provider request, not a played turn.

**Proposed ceiling: exactly one HTTP inference attempt, zero retries, zero
repairs, zero preflights, zero additional probes and zero matches. Current
authorization ceiling remains zero.** A timeout/error consumes the attempt;
preserve the failure and stop. The 20-second existing timeout remains unchanged.
An unloaded model can add startup latency, so a timeout alone does not establish
grammar failure. No rerun is authorized by the proposed ceiling.

After separate authorization, the following concrete command would send that
single payload and save the response in a new directory. **Do not execute it as
part of Phase 10B.** Network execution needs the same approved permissions as the
metadata checks. The SHA-256 locks the canonical request body; no live runner or
benchmark contract was added.

```powershell
@'
import hashlib, http.client, json, time
from pathlib import Path
from urllib.parse import urlsplit
from aig.settings import load_settings
base = Path('.local/arena-phase10b-ollama-context-investigation-20260913')
payload = json.loads((base/'derived/opening-request.json').read_text())
body = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
assert hashlib.sha256(body).hexdigest() == '9a84545dfa926602fcd76bc526e04f8494fb418d482769c59217f64ebb0e829e'
s = load_settings().ollama
assert (s.model,s.context_size,s.max_output_tokens,s.temperature,s.seed,s.think,s.stream,s.keep_alive,s.timeout_seconds) == (payload['model'],4096,256,0.0,42,False,False,'10m',20.0)
u = urlsplit(s.base_url)
assert u.scheme == 'http' and not u.username and u.path in ('','/')
out = Path('.local/arena-phase10b-authorized-opening-one-request-01')
out.mkdir(exist_ok=False)
(out/'request.json').write_bytes(body)
c = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=s.timeout_seconds)
start = time.perf_counter()
try:
    c.request('POST', '/api/chat', body, {'Content-Type':'application/json'})
    response = c.getresponse()
    (out/'response.bin').write_bytes(response.read())
    (out/'status.json').write_text(json.dumps({'http_status':response.status,'seconds':time.perf_counter()-start}))
except Exception as exc:
    (out/'failure.json').write_text(json.dumps({'type':type(exc).__name__,'message':str(exc),'seconds':time.perf_counter()-start}))
    raise
finally:
    c.close()
'@ | .venv/Scripts/python.exe -B -
```

Review HTTP/schema errors, `done_reason`, prompt/eval counts, timings, and exact
current-catalog membership of the parsed result offline. A prompt count of 2,297
with successful schema-constrained output would corroborate context behavior.
Unexpected prompt counts or output outside the allowed set require investigation,
not a retry or constraint relaxation. With `stream=false`, this test measures
whole-response latency and reported timing components, not direct first-token
latency. It does not establish tactical reliability or native grammar equivalence
over all possible outputs.

## 10. Artifacts, verification and sources

Created:

- This report.
- `scripts/ollama-context-analysis.py`, an offline-only helper with socket and
  subprocess denial, immutable-output-directory behavior, payload reproduction,
  lossless tokenizer checks, and assertions against historical token counts.
- `.local/arena-phase10b-ollama-context-investigation-20260913/`: metadata,
  version-pinned sources and inventories, isolated analysis dependencies,
  reconstructed requests/prompts/token IDs, standalone grammars, telemetry,
  preservation baseline and completion verification.

The helper passed twice, with the final run explicitly asserting all 36 Revive
token matches and the midgame anchor. Both runs reproduce the four Phase 10A
request/schema byte pairs. The only new project files are the helper and report;
existing backend, tests, scripts, docs and historical evidence are verified
against the 8,000-file starting inventory. The source-level investigation needs
no application test-suite rerun because model-facing behavior is unchanged.

Reproduce offline into a fresh directory:

```powershell
.venv/Scripts/python.exe -B scripts/ollama-context-analysis.py --output .local/arena-phase10b-offline-repeat
```

Dependencies are isolated beneath the investigation directory: regex 2026.9.10,
Jinja2 3.1.6 and MarkupSafe 3.0.3. Package directory permissions required approved
execution outside the sandbox; the helper's network/subprocess-denial hook was
still active. Application dependencies were not changed.

Network activity was limited to Ollama metadata, official source/docs retrieval,
and isolated analysis-package downloads. **Zero `/api/chat`, zero
`/api/generate`, zero model inference, zero OpenAI/provider inference, zero live
preflights/probes/matches.** References to inference endpoints in source and the
inactive command above are not requests. Fake adapters captured payloads entirely
in memory. No prior evidence or model-facing runtime behavior was changed.

Exact consulted source-file URLs are listed in `sources.json`, including pinned
Ollama server/routes/prompt/template/build files and pinned llama.cpp chat,
server-context/common/task, schema conversion, sampling, grammar, vocabulary,
Unicode and PEG-parser sources. The two source-tree API responses and resolved
commits are retained. Official unversioned docs consulted:
`https://docs.ollama.com/capabilities/structured-outputs`; they are supporting
guidance, not the basis for the version-specific implementation conclusion.
The initial search surfaced other sources; no third-party blog or discussion
was used as evidence. No GitHub CLI repository operation was performed.

**Stop point:** investigation complete. Separate user authorization is required
before executing the proposed one-request opening experiment.
