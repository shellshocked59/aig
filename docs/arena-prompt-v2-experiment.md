# Arena Phase 6B: prompt-only controlled experiment

Implemented offline on 2026-09-13. No live inference, service requests, provider
preflights or model matches were performed. V2 is available for explicit experiments;
normal gameplay and the default/latest Arena prompt remain V1.

## Hypothesis and frozen controls

The [V1 postmortem](arena-v1-postmortem.md) found that all 22 accepted Qwen full-match
plans began with an out-of-range Ranger attack and executed zero AP. Many probe
plans ended after 1–2 AP despite useful legal continuations. Luna's 72 execution
truncations include 59 actions illegal from the starting state and 13 genuinely
sequential failures. Static acceptance does not establish executable legality.

Test whether clearer factual instructions improve initial legality, useful AP
utilization and sequencing. The only model-facing independent variable is the
base prompt: `arena-turn-prompt-v1` versus `arena-turn-prompt-v2`. No inference
results yet establish improvement or justify promoting V2.

| Control | Unchanged concrete identity |
| --- | --- |
| Observation and actor-grouped legal serialization | `arena-observation-v1` |
| Logical plan / provider wire schemas | `arena-turn-plan-schema-v1` |
| Benchmark methodology / fixed probes | `arena-benchmark-v1` / `arena-probes-v1` |
| Qwen model/settings | `qwen-config-v1`: Qwen3.8 4B Q4_K_M, 4096 context, 256 output, temperature 0, seed 42, think/stream false |
| Luna model/settings | `luna-config-v1`: gpt-5.6-luna, reasoning none, 512 output, store false, SDK retries zero |
| Engine / scenario | `arena-rules-v2` / `arena-scenario-v1` |
| Commands / snapshots / replay | `arena-command-v2` / `arena-snapshot-v2` / `arena-trace-v2` |
| Heuristic | `arena-heuristic-v1` |
| Repair | One static-validation repair; unchanged category-only correction message |
| Execution / failure policy | Ordered execution, truncate on rejection; strict benchmark, no fallback, fail fast |

The checked local settings matched both frozen model profiles during implementation.
Before a later authorized run, verify the same profile identities offline if local
settings have changed. Do not tune or substitute settings to accommodate V2.

## Exact semantic intervention

V2 retains V1's perfect information, victory conditions, AP budget, costs,
movement/LOS, downed occupancy, ability damage/ranges, revival, friendly fire,
Core restrictions, bonuses, automatic EndTurn and JSON-only plan contract.

It makes these contract details explicit:

1. Legal options belong to their unit's `actions` group. Copy that unit's `id`
   into `unit_id`; never combine another actor with the option or invent abilities.
2. The first action's type and target/destination must be in that actor's supplied
   starting list. Do not invent an unlisted first target or destination.
3. Lists describe the start of the turn. Account for preceding actions before
   adding the next action; old choices can disappear and new choices can become
   legal. This preserves Move-then-Attack and Revive-then-Act possibilities.
4. Movement changes range/LOS; damage changes status; Finish removes a body;
   Revive activates it; Bash can displace; Fireball can down several units;
   victory ends the turn.
5. Attack targets active enemies or the enemy Core; Snipe/Bash active enemies;
   Finish downed enemies; Heal active friendlies; Revive downed friendlies;
   Fireball a legal position.
6. Do not stop simply because one action succeeded. Include another useful legal
   action when remaining AP and safe sequencing permit it. Unused AP is valid
   when no useful continuation exists.
7. Costs are displayed in two compact groups: Move/Attack/Heal/Finish/Bash 1 AP;
   Revive/Snipe/Fireball 2 AP. V1 already contained these same costs.
8. Return only ArenaTurnPlan, exactly following the same schema, with no reasoning,
   explanation, prose or commentary.

Manual audit and regression checks find no target priorities, Core preference,
Cleric focus, ability ordering, lethal-damage priorities, SIEGE recommendation,
unit-conservation policy or instruction to spend all AP unconditionally. These
are action-contract instructions, not a tactical priority list.

Both versions are frozen in the immutable registry in
[`prompts.py`](../backend/aig/arena/ai/prompts.py). SHA-256 over UTF-8 prompt bytes:

| Prompt | SHA-256 |
| --- | --- |
| V1, unchanged | `5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7` |
| V2 | `5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29` |

## Selection and evidence

Both provider constructors accept `prompt_version`, resolved through the shared
registry. There are no provider forks or arbitrary prompt-file loads. The selected
base prompt is automatically reused during repair, with identical observation,
schema and correction feedback. Model traces record the concrete selection.

The CLI adds `--prompt-version`. V1 is explicitly selectable and remains the
default. New experiment/trial manifests record the concrete prompt and its hash,
unchanged benchmark/probe/schema/rules/scenario and model profiles, source revision,
dirty state and backend source inventory/hash. Plans, inference rows and preflight
diagnostics carry the concrete prompt/schema versions.

The frozen benchmark JSON still names V1. `benchmarkSpecHash` continues to identify
that immutable base artifact; `baseRecipePromptVersion` records V1 and
`experimentOverrides={"promptVersion":"arena-turn-prompt-v2"}` marks V2 runs.
V1 uses empty overrides. No benchmark-v2, historical manifest overwrite or moving
historical `latest` reference is introduced.

## Preregistered probe comparisons

Compare **Qwen V1 versus Qwen V2**, and separately **Luna V1 versus Luna V2**.
Cross-provider ranking is secondary. Use the frozen unified V1 probe comparison
in `.local/arena-phase5-continuation-20260913/comparison.json`; it already includes
the earlier Qwen partial evidence once. Keep the seven unchanged probes and four
intended attempts per probe (28 per provider). Preserve failed runs and report
unstarted intended trials separately; fail-fast does not guarantee 28 completions.

| Dimension | Readouts and denominators |
| --- | --- |
| Reliability | First-response static validity, repair attempts/success, failed trials; include all started attempts and show intended count 28; preflight separate |
| AP | Planned/executed/unused AP; full-5-AP and <=2-AP rates for both planned and executed AP among accepted plans; show accepted-plan sample count |
| Initial contract | First-action starting-legal rate among nonempty accepted plans; report empty plans separately, not as legal first actions |
| Starting prefix | Number of consecutive starting-list members from action zero, stopping at first nonmember; empty prefix 0; distribute over accepted plans |
| Dynamic sequencing | Execution-invalid truncation rate, invalid action index and rejection reason; distinguish terminal suffixes from errors |
| Probe outcomes | Preserve Phase 5 Winning Core, Team Elimination, Revive, Fireball, Shield Bash, Snipe and Finish/Core metrics and complete action sequences |

`starting_legality` is passive measurement in new plan/result rows. It matches the
actor, type and exact target/destination against the original observation; it does
not change the parser, executor or legality rules. Use the same helper on frozen V1
observations and accepted plans offline without rewriting them. Later actions may
be absent initially and valid after preceding actions, or present initially and
invalid later. Prefix length is therefore contract evidence, not an execution score.
Rejected raw output remains unavailable under the unchanged repair/evidence policy;
do not invent starting-legality measurements for failed responses.

The generic benchmark summary retains its existing valid-trial-only distributions.
The future A/B analysis must additionally use per-trial inference artifacts to
include failures and repairs in reliability denominators. Preserve terminal AP
leftovers and distinguish intentional early stops from execution-forced stops.
There is no single aggregate pass/fail score. Material gains in legality, validity,
AP or objectives are useful only alongside examination of regressions elsewhere.

## Offline request size and Qwen headroom

The representative full-match opening observation has 7,397 UTF-8 bytes and hash
`d11799c7e917d3353962ca104b87f14b3fc64f6f35b2e9ff169baa7656c48279`.
Requests were captured using fake transports and the unchanged default profiles.

| Measurement | V1 | V2 |
| --- | ---: | ---: |
| Prompt characters / UTF-8 bytes | 1,730 | 2,846 |
| Prompt + canonical observation bytes | 9,127 | 10,243 |
| Complete Ollama serialized request bytes | 13,485 | 14,617 |
| Canonical OpenAI SDK argument JSON bytes | 13,104 | 14,236 |

OpenAI size is local argument serialization, not a captured HTTP body. Request
bytes include schema/options/framing and are not tokenizer counts. V2 adds 1,116
prompt characters; JSON escaping makes the request delta 1,132 bytes.

No exact model tokenizer was used offline. A rough 3–4 characters/token estimate
adds 279–372 tokens. Anchoring to the frozen Qwen maximum initial input of 3,067
tokens gives roughly 3,346–3,439 input tokens, leaving **401–494 tokens after
reserving the unchanged 256-token output allowance** within 4,096. Extra repair
text reduces that margin. This suggests reasonable initial-request headroom and
no obvious overflow; it is not proof of tokenizer-specific fit or server behavior.
Actual V2 input counts remain unknown until authorized collection. Stop on observed
context-limit failure; do not change `qwen-config-v1` or automatically retry.

## Exact next live commands — not executed

Run from `C:\code\aig` only after separate authorization. These commands are
**probes only**, with the benchmark's existing single unrepaired opening-state
preflight per provider. No additional standalone preflight is needed.

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider ollama --prompt-version arena-turn-prompt-v2 --probe all --probe-trials 4 --strict-provider --output .local/arena-phase6b-qwen-v2-probes-20260913-01
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider openai --prompt-version arena-turn-prompt-v2 --probe all --probe-trials 4 --strict-provider --output .local/arena-phase6b-luna-v2-probes-20260913-01
```

Each command schedules 28 trial calls. With one initial request and at most one
repair per trial, plus one unrepaired preflight, the conservative ceiling is
**57 requests per provider, 114 combined**. Without repairs the complete schedule
uses 29 each. Failure aborts the schedule, so actual counts may be smaller; these
are ceilings, not permission to spend unused calls on retries or continuations.

Output paths must be unused. Preserve failed artifacts. Any retry/continuation or
extra provider request requires separate authorization. The workspace's documented
Ollama sandbox connectivity procedure applies after a similar fast transport
failure; diagnosis does not authorize more inference. Do not attribute a rapid
permission failure to model ability or change profiles/restart models on that basis.

Stop after probe collection and inspect within-model A/B results. Do not launch
V2 full matches without separate authorization. Observation redesign, stepwise
control, dynamic replanning, richer repair feedback and balance/model tuning are
outside Phase 6B.

## Offline implementation and verification

Changed provider selection in `ai/provider.py`, `ai/ollama.py`, `ai/openai.py`,
registered V2 in `ai/prompts.py`, and extended `benchmark.py` and
`benchmark_versions.py`. Added `prompt_metrics.py` and
`tests/test_arena_prompt_v2.py`. Updated `arena-ai.md`, `arena-benchmarking.md`,
and added this document. The existing AGENTS.md modification and untracked V1
postmortem were preserved.

The ten new tests cover frozen hashes/defaults/aliases, unknown versions, factual
markers and neutrality, both fake provider payloads including unchanged repairs,
factory selection, manifests/recipe distinction, CLI propagation to saved evidence,
pre-request mismatch rejection, and initial versus dynamic legality/empty plans.

Local verification artifacts are under `.local/arena-phase6b-verification/`:
request sizes, test/build logs, Phase 3 hashes, a fresh 32-trial heuristic baseline,
and the before/after preservation inventory. These files are new evidence; no
existing V1 evidence is overwritten.

| Verification | Result |
| --- | --- |
| Python suite | 1,062 total: **1,057 passed, five existing skips**, 129.574 seconds |
| New prompt experiment tests | 10 passed; real inference transports guarded |
| Frontend suite / production build | **76 passed**, zero failures / build passed |
| Fresh Phase 5 offline baseline | **32/32 valid**: four matches plus four repetitions of each of seven probes |
| Phase 3 | All five pinned plan/command/state/trace hashes unchanged |
| Frozen Phase 5 probes | Complete hashes, metrics and objective outcomes unchanged |
| Before/after inventory | 3,946 files checked; only the eight intended existing source/docs files changed; none removed |
| Historical local artifacts | **3,770 files byte-identical**, none removed |
| Empire / frozen Arena sources | Unchanged; existing regression tests and hashes passed |
| V1 prompt and benchmark/probe/profile artifacts | Preserved; frozen integrity/hash tests passed |
| Live inference / external service calls | **None** |

Phase 3 full AI trace remains
`9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1`;
plan array remains
`5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c`.
All five hashes are in `phase3-hashes.json`. Empire snapshot/trace pins remain
`8859a9dbe564c70105c62e9764ef6d857ea22b674049983857f0256ef3f9bb48` and
`b9f5bc4faf4b13b8aa0262170ec3f7c058dc14b33e2f2bc20758ea98adbb2302`.

Reproduce offline tests with `.venv/Scripts/python.exe -m unittest discover -s tests`,
`npm.cmd test`, and `npm.cmd run build`. The local `audit.py` captures fake request
sizes and generates fresh baseline artifacts; use a new output location when
repeating its baseline. No live experiment is authorized by these results.
