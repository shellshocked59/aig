# Arena Phase 10A: dynamically constrained structured stepwise output

2026-09-13. Offline implementation and experiment preparation only. **The Qwen
preparation gate is RED: reliable context fit is not established. No live command
is prepared, and the recommended live request ceiling for this phase is zero.**
This is a conservative gate, not a measured Ollama context-overflow result.

## Hypothesis and frozen control

[Phase 9D](arena-action-id-tactical-regression-analysis.md) found that the first
Revive decision changed on identical underlying states and ordered legal actions:
structured Qwen selected Revive at position 21/21; action-ID selected Attack at
position 1/21. Action-ID reduced output size and eliminated invalid selections in
the probe sample, but did not preserve tactical behavior. Prompt and observation
representation also differed in that comparison, so opaque IDs alone are not an
established cause.

The hypothesis here is that generating a complete semantic action preserves the
structured policy while exact current-action constraints exclude invented
references. It remains untested with a model. Dynamic grammar branches themselves
may change generation probabilities; unchanged messages do not prove unchanged
tactics.

New explicit versions:

| Contract | Version |
| --- | --- |
| Control | `arena-control-stepwise-constrained-structured-v1` |
| Provider wire schema algorithm | `arena-step-legal-action-wire-schema-v1` |
| Frozen benchmark recipe | `arena-benchmark-v5` |
| Observation, unchanged | `arena-observation-v2` |
| Prompt, unchanged | `arena-step-prompt-v1` |
| Logical plan, unchanged | `arena-turn-plan-schema-v1` |
| Repair, unchanged | `arena-step-repair-v1` |
| Probes / profiles, unchanged | `arena-probes-v1`, `qwen-config-v1`, `luna-config-v1` |

V3 already identifies the structured full-match orchestrator; V4 is the action-ID
recipe. Neither is overwritten. The new factory and controller are explicit
library entry points in [constrained.py](../backend/aig/arena/ai/constrained.py).
Normal gameplay, generic structured providers, CLI defaults and all previous
runners remain untouched. The RED gate deliberately withholds a live runner/CLI
for V5; the offline study is runnable independently.

## Exact dynamic wire language

The root object requires exactly `schema_version` and `actions`. Version is the
singleton string enum `arena-turn-plan-schema-v1`. The actions array allows zero
or one item. Its `items.anyOf` contains one branch per complete current legal
action, in the existing Observation V2 order. Every action field and coordinate
has a typed singleton enum. Every object requires all its fields and disallows
additional properties. No branch mixes actors, targets or coordinates from
different actions. No descriptions, titles, action IDs or tactical ordering are
added.

EndTurn is the unique logical empty-array result, conceptually before the action
branches: `{"schema_version":"arena-turn-plan-schema-v1","actions":[]}`. JSON
whitespace/key order are immaterial. Empty catalogs use `maxItems:0` and a vacuous
string item schema; no nonempty array can pass. Duplicate catalog actions fail
before request construction. A zero-AP turn never calls the provider.

The builder is pure and deterministic. Canonical schema serialization uses the
existing sorted-key, compact, ASCII JSON function. SHA-256 identifies the complete
wire schema; the hash includes the ordered exact action set and contract. Both
adapters currently derive identical schemas, so logical wire and provider hashes
are equal. Equal legal catalogs intentionally produce equal hashes, even if other
state facts changed. Observation hashes separately identify those facts.

The logical ArenaTurnPlan schema is not revised. The provider parses through the
unchanged logical parser, then the unchanged zero/one and exact-current-catalog
validator, then authoritative commands. A nonconforming fake/provider response
is rejected through the existing static taxonomy, without coercion. One bounded
Repair V1 request uses the **same schema** and observation. Repair V2 is rejected
for this mode. The frozen structured controller's EndTurn-on-provider-failure
policy is preserved, including its existing domain-defect exceptions.

## Provider support and limits of offline evidence

Ollama receives the dynamic schema in `format` on `/api/chat`; OpenAI receives it
in Responses `text.format.schema`, with `strict:true`. Both use nested `anyOf`,
typed `enum`, strict objects and `maxItems`, a subset already represented by the
checkout's OpenAI transformation. There is no weakening or generic-schema retry.
The OpenAI SDK's installed `_ensure_strict_json_schema` accepts each proof schema
without alteration. Real request construction is exercised with injected fake
transports for both providers, covering valid action, EndTurn, invalid output,
failed repair, successful repair and schema continuity.

The SDK transformation is **not a server schema-acceptance validator**. No local
JSON Schema package, Qwen tokenizer, server grammar compiler or server prompt dump
was available. The independent finite-language interpreter rejects unsupported
proof keywords/unbounded schemas and exhaustively enumerates the emitted schema
language. Its proof establishes the local JSON Schema semantics, not remote
compiler fidelity, schema size limits or model behavior. Those provider support
questions remain gated; a future provider rejection must stop that provider's
experiment without relaxing exactness.

## Offline exactness, Revive and historical evidence

The study exhaustively compares every logical schema output to the ordered
catalog plus one EndTurn. There are no missing or extra logical actions. Tests
also mutate actors, target IDs, action types, coordinates, fields, array lengths
and independently valid field combinations. They cover Move, Attack, Heal,
Finish, Revive, Shield Bash, Snipe, Fireball and Core attacks.

The final study contains 36 state proof records, 22 distinct schemas and 1,405
enumerated outputs across those records, with 24 heuristic decisions across the
seven probes. Repeated state records are not independent state coverage.

The exact Phase 9D Revive starting observation is hash
`52a7fa2ed56b339b7c1025a9030ada6c59591a381f1722f68a9378f141485cf5`.
All 21 actions are allowed, including the historical Revive at 21/21 and Attack
at 1/21. Illegal enemy/self Heal and stale-reference patterns are excluded.

Historical Phase 7F/8C observations are rebuilt through authoritative observation
queries and hash checked. The 18 invalid-reference attempts include 12 retained
parsed Phase 8C rejections; all 12 are excluded. They include enemy Heal
`blue-cleric -> red-cleric` and illegal self Heal `blue-cleric -> blue-cleric`.
The six Phase 7F attempts have no retained parsed output; no exact historical
response is claimed for them. Synthetic stale references are marked synthetic.
Frozen repair challenges additionally exercise the reconstructed failure states.
The historical invalid attempts collapse to one unique failed observation, so
this historical exclusion evidence has limited state diversity.

All seven heuristic probe turns have exactly identical underlying actions,
commands, AP use, outcomes and replay traces in generic and constrained modes.
Every selected heuristic action is in the schema. Tests exercise fresh schemas
after movement, downing, Revive, Shield Bash and a Fireball that changes statuses,
and reject actions made stale by those changes. A harmless action can leave the
legal set unchanged; rebuilding need not always change its hash.

## Request sizes and context gate

Canonical UTF-8 request-body sizes, excluding HTTP headers. Observation bytes and
model-facing messages are identical between the paired requests. OpenAI request
sizes refer to the serialized SDK keyword payload; network encoding overhead is
not measured. No actual inference token count was collected in Phase 10A.

| State | Legal actions | Observation bytes | Generic Ollama schema | Constrained schema | Generic Ollama request | Constrained Ollama request |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Simple Snipe probe | 25 | 3,385 | 2,567 | 8,804 | 7,753 | 13,990 |
| Revive probe | 21 | 3,151 | 2,567 | 7,493 | 7,467 | 12,393 |
| Opening full-match state | 54 | 6,462 | 2,567 | 19,975 | 11,430 | 28,838 |
| Historical midgame, turn 4 | 11 | 3,337 | 2,567 | 4,215 | 7,679 | 9,327 |

OpenAI's generic schema is 2,209 bytes. The constrained schema is identical to
Ollama's. Generic/constrained OpenAI request sizes respectively are 7,372/13,967
(simple), 7,086/12,370 (Revive), 11,049/28,815 (opening), and 7,298/9,304 (midgame).

The unchanged Qwen profile has `num_ctx=4096` and output reserve 256. A coarse
whole-request byte/4 to byte/3 sensitivity calculation gives:

| State | Estimated constrained input tokens | Remaining after 256 output |
| --- | ---: | ---: |
| Simple | 3,498–4,664 | −824 to 342 |
| Revive | 3,099–4,131 | −291 to 741 |
| Opening | 7,210–9,613 | −5,773 to −3,370 |
| Midgame | 2,332–3,109 | 731 to 1,508 |

These are **not Qwen tokenizer counts**. Schema is a separate `format` field and
may operate only as an output grammar. The same historical Revive generic request
used 1,182 measured input tokens, far below its whole-wire estimate of 1,867–2,489.
The historical midgame anchor is 1,322 tokens. If schema is grammar-only and the
rendered prompt is unchanged, their headrooms would remain 2,658 and 2,518. If
additional schema text enters context, adding schema-byte deltas/4..3 to those
anchors yields 2,414–2,824 and 1,734–1,872 input tokens respectively. Neither
conditional estimate establishes the opening-state fit or compiler cost.

**RED is therefore a conservative preparation decision under uncertainty.** The
opening wire-size estimate is far over budget, and the local evidence cannot
prove that realistic requests fit reliably. This does not establish that Ollama
actually tokenizes the 19,975-byte schema into context. Do not increase `num_ctx`,
alter `qwen-config-v1`, assert measured overflow, or prepare Qwen live commands
based on this study. Repair also adds message text; an initial request at the
limit would not have sufficient repair margin. Full semantic output should have
similar token cost to structured control, not action-ID's nine-token output.

## Traces, preservation and reproducibility

Constrained step traces add control mode/version, logical schema version, wire
version/hash, provider-derived hash, schema byte size, legal-action count, Repair
V1 provenance and command result. Existing selected structured action,
current-catalog membership, attempts, repair outcome and command index remain.
Provider traces record wire provenance even on validation/repair failure. Full
schemas are stored once per hash in offline debug artifacts, not in every step.
No endpoint, headers, credentials or environment contents enter the new schema
metadata. Canary tests cover invalid references, requests, repairs and traces.

Reproduce the offline study in a **new** output directory:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.constrained_study --output .local/arena-phase10a-offline-repeat
```

This entry point installs a network/subprocess-denial audit hook and uses only
fake transports and deterministic heuristic turns. It performs no live probes,
preflights, full matches, connectivity requests or model inference. Study output
includes exact schemas, heuristic command traces, proof records, historical
exclusions and paired request-size measurements.

Task artifacts are under [the Phase 10A directory](../.local/arena-phase10a-offline/).
The completed study is [results-final/study.json](../.local/arena-phase10a-offline/results-final/study.json);
the earlier `results/` directory is retained rather than overwritten.
The task-start inventory covers existing backend, tests, scripts, documentation
and local historical evidence. A final preservation report identifies the only
permitted existing-file changes: the V5 registry entry and two documentation
links. All frozen contracts, V1–V4 recipes, action-ID files, game rules, model
profiles, historical evidence and Empire files remain byte-identical. The
source-preservation test normalizes CRLF for checkout portability; the separate
task audit compares exact original bytes without normalization.
The complete inventory checked 7,929 existing files, including 7,712 historical
evidence files; only the three explicitly permitted existing files changed.

Validation: the full Python suite reports **1,182 tests, OK, 5 skipped** (1,177
executed). Phase 10A adds 15 test methods with parametrized loops covering both
providers and all seven probes. The focused suite is rechecked after making its
preservation fixture portable across checkout line endings. Frontend files were
not changed, so no frontend test or build was run. Existing fake HTTP-error
fixtures emit ResourceWarnings; the full test transcript still concludes OK.
The final focused run passed all 15 tests with zero failures, errors or skips.

Files added:

- [Constrained providers, builder and controller](../backend/aig/arena/ai/constrained.py)
- [Offline proof and request measurement entry point](../backend/aig/arena/constrained_study.py)
- [V5 recipe](../backend/aig/arena/benchmark_artifacts/arena-benchmark-v5.json)
- [Regression tests](../tests/test_arena_constrained.py)
- [Frozen source-content baseline](../tests/fixtures/arena-phase10a-preservation.json)
- This experiment report.

Existing files changed: [benchmark registry](../backend/aig/arena/benchmark_versions.py),
[Arena AI documentation](arena-ai.md), and [benchmarking documentation](arena-benchmarking.md).
The V5 recipe SHA-256 is
`3d12f753d809fd58fa316a4d9e9d32cb4318f66ae66f2630604111bb3fa2deee`.
New `.local` artifacts include the task manifest, before/final preservation
inventories, two retained study runs, validation summary and test transcripts.

## Future gate and stop point

No constrained Qwen pilot command is prepared at RED. Current live ceiling: **0**.
Before reconsidering it, obtain separately authorized offline evidence of the
exact Ollama version's schema-to-grammar/prompt behavior and relevant tokenizer,
or design a separately versioned, smaller exact representation. Grouping shared
fields can reduce duplication but requires another explicit design and exact-set
proof; it must never create illegal actor/target cross products. Replacing full
actions with IDs or adding IDs alongside actions is a different experiment.

Only after context/support are acceptable and authorization is explicit, the
proposed first experiment is Qwen only, seven frozen probes × one trial, no
preflight and no full matches. Its theoretical ceiling is **70 requests**:
seven turns × at most five decisions × one initial plus one repair. This is an
inactive design bound in V5, not current authorization. A YELLOW gate should
receive a smaller separately specified pilot rather than assume all seven fit.

Compare Revive, all seven action sequences against structured and action-ID
history, schema acceptance, initial validity, repairs, actual prompt/output
tokens and context headroom. Seven turns establish neither rare-error rates nor
full-match reliability. Any later 28-turn probes or full matches require a new
decision and authorization. Phase 10A stops at this offline result.
