# Arena turn prompt: sequential planning and AP discipline

Prepared 2026-09-14. Implementation and offline validation only. **Zero live OpenAI or Ollama requests. V4 is experimental; product defaults remain V1. The 300-match benchmark has not started.**

## Evidence and scope

The preserved [baseline report](arena-tactical-literacy-baseline-results.md) and [information audit](arena-tactical-literacy-audit.md) identify 18 AP-overbudget first responses, 15 accepted plans with attacks on targets DOWNED earlier in the same plan, and two blocked-LOS attempts. All 18 static repairs succeeded. All 122 accepted plans replayed exactly. Basic single-action damage objectives succeeded in 12/12 decisions and witnessed Core objectives in 6/6. These findings support a narrow sequencing intervention, not a claim of broad arithmetic incompetence. Legal alternative choices cannot establish misunderstood damage.

No Fireball was selected in the baseline. Fireball comprehension remains unresolved. This revision does not incorporate V3's Fireball preferences, tune abilities, change target priority, positioning, tile valuation, heuristics, or mechanics.

## Version, ancestry and selection

`arena-turn-prompt-v3` was already consumed by `ai/friendly_fire_prompt.py`, a separate opt-in Fireball experiment. The next clean ID is **`arena-turn-prompt-v4`**. It branches directly from V1: replace its one AP-budget sentence and insert `SEQUENCE_GUIDANCE` immediately before the unchanged output contract. Reversing those two edits reproduces V1 exactly.

Implementation: `backend/aig/arena/ai/sequential_prompt.py`. Its immutable mapping extends the separate experimental registry with V4 while leaving the historical V1/V2 registry and V3 source untouched. Exact prompt text is snapshotted in `tests/fixtures/arena-turn-prompt-v4.txt`. Source-file hashes and prompt hashes are frozen in `artifacts/arena-sequential-planning/binding-v1.json`.

| Prompt | SHA-256 of UTF-8 prompt text |
|---|---|
| V1 | `5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7` |
| V2 | `5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29` |
| V3 | `5a517164a8f799b2f5e9b2f9a56103fb61e4ef690d2b7e6efd53412b08dce182` |
| V4 | `ede7f2defc81aa099fd8d1e2e4acbdd948389790101afc3d4b75c05342b16b35` |

Explicit experimental APIs are `OpenAISequentialProvider(..., prompt_version="arena-turn-prompt-v4")` and `OllamaSequentialProvider(...)`. Both inherit transport, parsing, schema, telemetry and single static repair. Omitting the prompt still selects V1, as does `latest`. The normal provider factory and UI remain unchanged; use these experimental providers for V4.

Strict full-turn uses the existing `checked_plan` boundary and sequential executor. `ExperimentalBoundedReplanController(provider, fallback=False)` permits the explicit experimental binding and inherits the exact frozen `ArenaBoundedReplanController.run_turn` method. Only construction differs: the original constructor pins V1 and remains untouched. The control version, one execution replan, remaining-AP observation, four-request per-turn cap, and execution semantics are unchanged. The new literacy recipe itself uses strict single decisions, never bounded replanning.

Stepwise has its own `arena-step-prompt-v1` and observation contract. It is unchanged; V4 is a full-turn prompt. No normal benchmark recipe is promoted or rewritten. The separate versioned recipe is `arena-sequential-literacy-v1`.

## Exact semantic diff from V1

| Classification | Addition / replacement |
|---|---|
| AP budgeting | Replace “up to 5 shared Action Points” guidance with the observation's complete remaining budget, an explicit total-cost limit, affordability checks and subtraction before another action. No fixed AP total in this behavioral instruction. |
| Sequential state propagation | Start at the current authoritative observation, including partial turns. Treat the plan as state transitions. Check actor/ability/target, check and subtract AP, apply supplied consequences to HP/status/occupancy/positions, then choose the next action. Current options can disappear and new options can emerge. |
| ACTIVE/DOWNED handling | A unit DOWNED earlier is no longer an ACTIVE target for Attack/Snipe/Shield Bash; DOWNED actors cannot act. Finish is permitted when legal and remains optional. |
| Other clarification: removal/revival | Finished units cannot be later actors/targets and no longer occupy their tiles. Revive changes DOWNED to ACTIVE and permits later same-turn action. |
| Position/range/LOS reassessment | Movement and surviving-target Shield Bash pushes require updated-board range, adjacency, target availability and LOS checks. Add concise authoritative geometry facts absent/ambiguous in the audit: Chebyshev range, center-to-center supercover excluding endpoints, both side cells at exact corner crossings, terrain blocking and entity nonblocking. These are legality facts, not new Fireball behavior. |
| Terminal/stop behavior | Append nothing after a game-ending action. Use AP productively when a coherent legal continuation exists; spending every AP is unnecessary, and uncertain continuations may be omitted. |
| Other clarification | Derive consequences from supplied mechanics rather than memorized combinations; first action must appear in its actor's current legal list. |

**New tactical preferences: none.** No fixed-damage examples or preferred combos were added. V1's existing ability numbers and current deterministic-game description remain intact. The new planning guidance does not assert that damage is always exact, invent random damage, or introduce probability semantics; it derives consequences from the supplied mechanics, allowing a later mechanics contract to describe ranges.

Exact AP wording:

> The observation's action_points_remaining is the complete AP budget for this plan.
> The total cost of your returned actions MUST NOT exceed it. Keep a running remaining
> budget: confirm an action is affordable and subtract its cost before adding another.

Exact central sequencing wording:

> Treat the plan as a sequence of state transitions, not independent starting options.
> For each action in order: check actor, ability and target legality in the current
> imagined state; check and subtract AP; apply the supplied mechanical consequences
> to HP, status, occupancy and positions; only then choose the next action.

Exact stopping balance:

> Use AP productively when a coherent legal continuation exists. You need not spend
> every AP: stop with a shorter legal plan when later legality is uncertain.

## Output and repair contracts

No observation or schema changes were required. The output remains only `ArenaTurnPlan` V1, zero to five actions, with no reasoning/calculation/predicted-state fields. There is no chain-of-thought request. The engine retains automatic EndTurn behavior.

Static validation checks schema, total AP, ownership, references and abilities. It deliberately does **not** simulate status, occupancy, range or LOS across a plan. The main provider's repair message gives the category (including `ap_budget`) and asks for a corrected plan with the same observation/schema. It does not give stale-DOWNED or blocked-LOS repair feedback because those are execution failures, outside static repair. This is consistent with the architecture and the successful 18/18 baseline repairs; neither parser nor repair was changed. V4's base prompt is naturally present on both first and repair requests, but the repair feedback, count and mechanism are identical.

## Prompt and context size

Measurements use the existing offline bytes/4 to bytes/3 approximation from `constrained_study.py`; these are **not measured model tokens**. No tokenizer download or provider request was made. Context estimates concatenate prompt, observation with its label, and the unchanged compact OpenAI wire schema. They exclude chat framing and provider-specific schema processing. All 42 fixture measurements are in the binding.

| Payload | V1 bytes | V4 bytes | V1 approximate tokens | V4 approximate tokens |
|---|---:|---:|---:|---:|
| Prompt | 1,730 | 3,609 | 433–577 | 903–1,203 |
| LETHAL-001 prompt + observation + schema | 8,591 | 10,470 | 2,148–2,864 | 2,618–3,490 |
| AP-004 prompt + observation + schema | 8,585 | 10,464 | 2,147–2,862 | 2,616–3,488 |

The prompt grows by 1,879 bytes (108.6%); estimated incremental input is about 470–627 tokens/request. Across all fixtures, complete measured context is 8,558–9,688 bytes under V1 and 10,437–11,567 under V4. This is a meaningful input increase; any repair savings must be assessed against it. No context-fit guarantee is inferred for Ollama from this approximation.

## Matched rerun and budget

Choose **method A: the exact 122 decision slots that actually reached V1's provider**, in the original repetition/probe order. The frozen 42 states, three-repeat schedule identities, predicates, reference witnesses, oracle, scoring, observation V1, plan schema V1, rules/scenario, Luna model and `luna-config-v1` remain unchanged. The preserved baseline is the comparison arm; no new V1 requests.

Exclude `03-POSITION-002`, `03-POSITION-003`, `03-POSITION-004`, and `03-REVIVE-004`. The first has a historical zero-attempt ceiling-denial row, not model evidence. All four remain preserved and explicitly listed, not silently treated as failures or supplemented. In particular, matched POSITION objective coverage is 2/2 rather than the historical runner summary's 2/3. This is cohort analysis, not rewriting historical scoring/evidence.

`sequential_literacy.py` verifies every original frozen source hash, permits only its two named additive modules, and pins their exact hashes in a separate create-only binding. The original suite and `tactical_literacy.verify` remain frozen and correctly reject the larger current source inventory. Use the new binding's verifier for the new experiment. Historical tests scope out only these named additions; no runtime historical guard is weakened.

The changed experimental factors are prompt text/version, additive orchestration/metadata, the explicitly selected matched cohort and a larger **160-request ceiling** to reduce repeat truncation risk. There are no changes to individual decision mechanics or scoring. This ceiling is preparation for future authorization, not permission to run now.

| Budget item | Prepared value |
|---|---:|
| Intended decisions / first requests | 122 |
| Expected static repairs at V1's 18/122 rate | 18 |
| Expected total requests | 140 |
| Hard ceiling, all attempts included | 160 |
| Capacity above first requests | 38 repairs |
| Architectural maximum without ceiling | 244 (not authorized by this recipe) |
| Expected total tokens, same request count plus estimated prompt delta | about 414,675–436,655 |
| Ceiling scenario at 160 requests | about 473,914–499,034 tokens |

The empirical reference is 348,875 tokens / 140 requests, 165.98 provider seconds and 172.6 elapsed seconds. At 140 requests, unchanged request latency gives about **166 provider seconds / 173 elapsed seconds**; a simple token-proportional sensitivity estimate gives about **197–208 provider seconds / 205–216 elapsed seconds**. At 160 requests those scenarios are about 190 seconds at historical request latency or 225–237 seconds under token scaling. These are rough scenarios, not latency guarantees: caching, response lengths and queueing may change. Allow several minutes; timeout-heavy runs can be longer. No dollar price is invented. The model's output cap remains 512 tokens/request.

Hard policy: no preflight, inference retries, execution replans, heuristic fallback or replacement trials. Preserve failed intended decisions, allow the existing single static repair and continue later independent probes after recognized transport/refusal/static failures. Stop at the request ceiling or integrity/unclassified failures. Reserve durably before transport, verify source/provider bindings on every attempt, recheck at completion, exactly replay every accepted plan, and retain states/observations/parsed attempt outputs/telemetry/execution/results and evidence hashes. Output directories must be new; no overwrite or resume.

## Analysis and interpretation

The prepared comparison re-evaluates saved accepted plans with the unchanged oracle, verifies replay and observations, reconciles request ledgers, and rejects altered evidence or scripted data passed as live evidence. It reports first-response validity and static categories, AP overruns, repairs, stale-DOWNED and LOS plans, other sequential failures and indices, AP before truncation, planned/executed AP, unused AP, plan lengths, one/zero-action frequencies, terminal suffixes, category predicates/classifications, tokens and provider latency, and both prompt/context sizes.

Plan-shape denominators are accepted plans. Static-quality denominators are requested decisions; unrequested slots stay visible. Short means planned AP below available AP. Clean unused AP excludes execution-invalid and terminal plans. Empty plans represent intentional EndTurn; the schema has no explicit EndTurn action. Per-decision records permit inspecting mixed-AP fixture effects rather than equating every one-action plan with timidity. Missing token telemetry is counted explicitly and must not be interpreted as zero measured usage.

Matched V1 reference: 104/122 first responses valid (85.25%), 18/122 repaired (14.75%), 17 execution-invalid plans, 183 planned actions, 238 planned AP, 219 executed AP, 13 clean unused AP, 63 one-action plans, zero empty plans, and 11 plans with planned AP below the initial budget. Requests per accepted decision: 140/122 = 1.14754. The report includes repair requests avoided versus these 18 repairs. An incomplete candidate cohort must not be claimed as an improvement based on fewer errors or requests.

A promising result combines materially fewer AP and stale-target failures with stable or improved validity, no increase in LOS failures, useful AP execution, no large shift toward empty/short plans, and broadly preserved damage/Core outcomes. Inspect category and per-slot results; no arbitrary composite threshold or strategic-strength conclusion. Fireball remains unresolved without actual selections. The potential writeup is that a narrow state-transition/AP instruction improved observed planning consistency **only if the rerun supports it**.

The 100 strict / 100 bounded / 100 stepwise case study remains deferred. No model-strength conclusion, default promotion or authorization for those matches follows from offline tests.

## Commands

Offline verification:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.sequential_literacy verify
```

Exact future live command, **prepared but not executed; requires a separate live authorization**:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.sequential_literacy run --suite arena-tactical-literacy-v1 --prompt arena-turn-prompt-v4 --provider openai --binding artifacts/arena-sequential-planning/binding-v1.json --output .local/arena-luna-tactical-literacy-prompt-v4-01 --live
```

Exact future offline comparison command (baseline path and 122 cohort slots are frozen in the binding):

```powershell
.venv/Scripts/python.exe -B -m aig.arena.sequential_literacy compare --binding artifacts/arena-sequential-planning/binding-v1.json --candidate .local/arena-luna-tactical-literacy-prompt-v4-01 --output .local/arena-luna-tactical-literacy-prompt-v4-01-analysis
```

Reproducible scripted plumbing check, using a fresh output name each time:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.sequential_literacy dry-run --output .local/arena-sequential-preparation/scripted-03
.venv/Scripts/python.exe -B -m aig.arena.sequential_literacy compare --candidate .local/arena-sequential-preparation/scripted-03 --output .local/arena-sequential-preparation/scripted-03-analysis --scripted
```

Scripted reference sequences include deliberately invalid examples. These are orchestration/contract fixtures, never model-response tests or V4 success evidence.

## Validation and preservation

Focused tests cover exact hashes and V1 ancestry, snapshot, registry/defaults, both fake provider payloads including repair, partial AP 1–4, 3-AP overbudget rejection, DOWNED/stale Attack and Snipe, Finish removal, Revive followed by revived action, movement enabling range, movement blocking later LOS, Bash pushing a target out of adjacency, terminal suffixes, intentional short/empty plans, strict execution, bounded partial-AP recovery, replay, baseline analysis, independent failed decisions and source-drift denial before transport. Sockets are forbidden in the new tests.

Results: **516 Arena regression tests passed**, plus **13 final focused tests passed** after the final comparison-manifest safeguard; **197 frontend tests passed**. The final scripted binding ran 122 independent decisions with zero provider requests and 122 verified replays; its comparison is explicitly diagnostic-only. Final artifacts are `.local/arena-sequential-preparation/scripted-02` and `scripted-02-analysis`. The earlier development binding/scripted-01 artifacts remain preserved separately and are not the final run binding. The broad regression preceded the last analysis-only safeguard; the final focused suite and scripted comparison validate that final change.

The pre-change inventory covers 11,516 existing files, including all baseline, bounded Stage 1, prior control, model-profile and Empire source/evidence files found in backend/frontend/tests/docs/artifacts/.local. All remain byte-identical except two intentional test-only source-scope additions: `tests/test_arena_fireball_methodology.py` and `tests/test_arena_tactical_literacy.py`. No existing production source, old prompt, model config, mechanics, observation, schema, repair, control, heuristic, UI or historical result document changed. The prior dirty worktree is preserved.

Preservation inventory/result: `.local/arena-sequential-preparation/preservation-before.json` and `preservation-result.json`. Baseline integrity additionally uses its pre-existing 1,111-file hash inventory. Final test counts and offline artifact verification are recorded in `artifacts/arena-sequential-planning/validation.json`.
