# Arena turn prompt: AP budgeting only

Prepared 2026-09-14. **V5 is frozen for an explicitly authorized future rerun. Zero live OpenAI or Ollama inference during preparation. V1 remains default; the 300-match benchmark remains unstarted.**

## Evidence and hypothesis

Inspected the preserved baseline results, sequential prompt design, V4 complete-report.md, comparison.json, supplemental.json and its calculation script. The primary comparison reuses V1 evidence, not a new V1 run. V4 is context for interpretation, not the baseline to which V5 is tuned.

| Metric | V1 observed | V4 observed | V5 AP-only |
|---|---:|---:|---|
| Requested decisions | 122 | 122 | 122 intended; not run |
| First-response valid | 104/122 (85.25%) | 115/122 (94.26%) | Pending |
| AP-overbudget first responses / repairs | 18 / 18 | 7 / 7 | Pending |
| Exhausted repairs | 0 | 1 | Pending |
| Actions per accepted plan | 1.500 | 1.471 | Pending |
| One-action frequency | 51.64% | 57.02% | Pending |
| Mean executed AP | 1.795 | 1.744 | Pending |
| Multi-action objectives | 3/6 | 1/6 | Pending |
| Witnessed position objectives | 2/2 | 0/2 | Pending |
| Stale-DOWNED-target plans | 15 | 11 | Pending |
| All later-action failures | 15 | 15 | Pending |
| Execution-invalid plans | 17 | 19 | Pending |
| Truncation-derived unused AP | 21 | 27 | Pending |

V4 reduced AP violations and repair demand, but four stale-target failures became Shield Bash push/range failures. It did not improve aggregate later-action failures. Some multi-action and position objectives regressed. V4 therefore remains experimental rather than selected for the case study.

Hypothesis: preserve V1's more aggressive multi-action behavior while reducing AP bookkeeping errors. Sequential-state recovery remains the responsibility of the strict, bounded-replan and stepwise control comparison. This is a hypothesis, not a result.

## Version, ancestry and exact semantic diff

`arena-turn-prompt-v5` was the next unused prompt ID. It branches **directly from V1**, never V4. Implementation is `backend/aig/arena/ai/ap_budget_prompt.py`; snapshot is `tests/fixtures/arena-turn-prompt-v5.txt`. The registry imports old entries for selection, but constructs V5 exclusively from V1 `SYSTEM_PROMPT`.

Replace exactly this V1 sentence:

> You have up to 5 shared Action Points, bounded by action_points_remaining.

with:

> The observation's action_points_remaining is the complete AP budget for this plan.
> Keep a running total of action costs. Before adding each action, ensure its cost
> fits within the AP still remaining. The total cost of all planned actions MUST NOT
> exceed this budget. You may return a shorter plan if no worthwhile legal action
> fits the remaining AP.

Reversing this replacement reproduces V1 byte-for-byte. No other sentence changes. Shorter plans are tied to remaining AP affordability, not uncertain continuation. The prompt was frozen before running offline fixtures; fixture results did not change its wording.

No V4-only state simulation, HP/status propagation, updated-board LOS, Shield Bash reassessment, terminal simulation or uncertainty-stop guidance was copied. No tactics, target priorities, combinations, damage-specific wording/examples, Fireball preferences, reasoning, AP ledger, notes or output fields were added. V1's pre-existing mechanics and sequencing sentences remain intact.

V5 SHA-256: `6b86be79d29a9287768ef447f8c3d817a583f959e62430e9cdf4a059bf111b81`.

| Preserved prompt | SHA-256 |
|---|---|
| V1 | `5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7` |
| V2 | `5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29` |
| V3 | `5a517164a8f799b2f5e9b2f9a56103fb61e4ef690d2b7e6efd53412b08dce182` |
| V4 | `ede7f2defc81aa099fd8d1e2e4acbdd948389790101afc3d4b75c05342b16b35` |

Source revision: `0999120892df07ee709c59e3f2596801cb025711`. The worktree was already dirty; exact source-file hashes in the binding, not HEAD alone, identify the experiment.

## Size and cost

| Prompt | UTF-8 bytes | Approximate tokens (bytes/4..bytes/3) |
|---|---:|---:|
| V1 | 1,730 | 433?577 |
| V4 | 3,609 | 903?1,203 |
| V5 | 2,005 | 502?669 |

V5 minus V1: +275 bytes (+15.90%), approximately +69?92 tokens/request. V5 minus V4: -1,604 bytes (-44.44%), approximately -401?535 tokens/request (rounded size endpoints differ by 401?534). These are offline estimates, not measured model tokenization. Per-probe prompt+observation+schema measurements are frozen in the binding.

| Resource | V1 observed | V4 observed | V5 |
|---|---:|---:|---|
| Initial requests | 122 | 122 | 122 intended |
| Repair requests | 18 | 7 | 7?18 planning scenario |
| Total requests | 140 | 129 | 129?140 expected; 160 ceiling |
| Input tokens | 342,189 | 365,251 | Pending |
| Cached input tokens | 251,243 | 299,697 | Pending |
| Output tokens | 6,686 | 6,007 | Pending |
| Total tokens | 348,875 | 371,258 | Pending |
| Provider latency | 165.98 s | 159.57 s | Pending |
| Backend elapsed | 172.58 s | 167.64 s | Pending |

The V4 total increased by 22,383 tokens despite 11 fewer repairs. V5's smaller overhead may offset repair savings, but actual telemetry is required. No pricing or dollar conclusion is assumed.

Budget derivation: the inherited reservation guard counts every transport attempt, including the sole optional static repair. 122 initials leave capacity for 38 repairs under the **160 hard ceiling**. The unconstrained architecture could use 244 requests; the frozen recipe does not authorize that. No preflight, retry, fallback, replan or replacement decision is permitted. The 7?18 repair range is a scenario bracket from V4/V1, not a confidence interval or evidence about V5.

Using V1's 348,875/140 total tokens per request plus 69?92 estimated extra prompt tokens:

| Requests | Estimated total tokens | Provider seconds, request scaling | Provider seconds, token scaling | Backend seconds, token scaling |
|---|---:|---:|---:|---:|
| 129 | 330,364?333,331 | 152.9 | 157.2?158.6 | 163.4?164.9 |
| 140 | 358,535?361,755 | 166.0 | 170.6?172.1 | 177.4?179.0 |
| 160 ceiling | 409,754?413,434 | 189.7 | 194.9?196.7 | 202.7?204.5 |

Allow several minutes; caching, queueing, output length and timeouts can change these estimates. Machine-readable ingredients are in `artifacts/arena-ap-budgeting/budget.json`.

The analysis reports repairs avoided versus 18, extra prompt tokens per request, approximate aggregate prompt overhead across all candidate requests, and actual aggregate token change. It also reports repairs avoided divided by the approximate extra prompt tokens as raw descriptive ingredients, never a universal efficiency score. Saved telemetry separately exposes input, cached input, output, total tokens and missing-usage counts.

## Contracts and controls

Explicit providers: `OpenAIAPBudgetProvider(..., prompt_version="arena-turn-prompt-v5")` and `OllamaAPBudgetProvider(...)`. Omitted version and `latest` remain V1. Normal factories, browser defaults and model profiles are untouched. No inference was used to check either adapter.

Strict binding: `arena-control-full-turn-v1`, through unchanged `checked_plan` and authoritative executor. Bounded binding: `APBudgetBoundedReplanController(provider, fallback=False)` with `arena-control-full-turn-bounded-replan-v1`; its `run_turn` is the identical inherited method. Tests bind observations with 1, 2, 3, 4 and 5 AP and exercise partial-AP recovery. No bounded controller semantics change.

The V1 ArenaTurnPlan schema, validation and single repair feedback/policy remain unchanged. Model plan ? static validation ? optional single repair ? authoritative execution. A >5 AP plan is already rejected at schema construction; partial-budget overruns within the five-AP envelope retain `ap_budget` validation. No weakening or recategorization was made. Stepwise prompts and behavior are untouched; the final three-arm comparability audit remains pending.

## Frozen matched methodology and integrity

The separate immutable recipe is `arena-ap-budget-literacy-v1`, with create-only `artifacts/arena-ap-budgeting/binding-v1.json`. The new runner is an additive adaptation of the frozen sequential runner. Historical runtime guards remain unchanged and will reject the larger source inventory; use the V5 verifier for this experiment.

Exactly the same 122 V1-requested slots, observations, original order and three-repeat identities are frozen. Excluded: `03-POSITION-002`, `03-POSITION-003`, `03-POSITION-004`, `03-REVIVE-004`. No new probes or filled historical slots. Same `arena-tactical-literacy-v1`, predicates, witnesses, oracle, schema, rules, scenario, `gpt-5.6-luna` / `luna-config-v1`, reasoning none, output cap 512, store false and zero SDK retries. Strict single decisions only, no heuristic fallback.

The binding pins old and new source hashes, all prompt hashes, schema, ancestry, source revision, cohort, model configuration, original V1 evidence, V4 binding, V4 evidence and V4 analysis inventory. The verifier requires every original V4 source unchanged and allows exactly the two named new production modules. Per-attempt source/provider/configuration/repair checks and durable reservations are inherited. New output directories only; no overwrite/resume. Recognized failed decisions remain visible; integrity failures stop execution.

Primary output `comparison.json` / `report.md` compares matched V1 vs V5. Additional `three-way.json` / `three-way.md` independently replays V4 alongside V1/V5, checks ledgers and provenance, and reports all frozen categories, plan shape, AP waste, indexed execution failures, range/Bash failures, costs and timing. Scripted outputs are explicitly diagnostic and rejected as live evidence. Incomplete cohorts cannot support a matched improvement claim.

Means and one/zero-action frequencies use accepted plans. Per-intended execution uses all 122 slots. Short means planned AP below available AP. Clean unused AP excludes terminal and invalid execution; truncation unused AP uses available AP minus committed AP. Indexed failures remain individually available. Historical elapsed uses manifest-to-summary timestamps; V5 additionally records monotonic elapsed after manifest creation through final verification, excluding process startup. Neither is pure provider latency.

## Interpretation and future case study

Promising: materially fewer than 18 AP overruns, improved first-pass validity and reduced repair demand, while plan length stays near V1, executed AP stays near/above V1, one-action frequency does not materially rise, MULTI stays closer to V1 than V4, POSITION avoids the V4 regression, and damage/Core/WARD strengths remain intact. Do **not** require fewer stale-state failures.

Reject as final benchmark candidate if AP improvement is weak, plan length or executed AP drops materially, single-action plans rise, multi-action/objective outcomes regress like V4, or overhead outweighs repair savings. These are descriptive criteria, not invented numerical thresholds or a composite score. Fireball-category objectives remain outcomes, not evidence of Fireball comprehension when no Fireballs are selected.

If supported by future evidence, the case study can distinguish explicit AP prompting from control architecture's stale-state recovery. This preparation selects no winner, changes no default and starts none of the 100 strict / 100 bounded / 100 stepwise matches.

## Exact commands

Run from `C:\code\aig` in PowerShell. Offline verification:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.ap_budget_literacy verify --binding artifacts/arena-ap-budgeting/binding-v1.json
```

**Future live command ? prepared only, NOT executed:**

```powershell
.venv/Scripts/python.exe -B -m aig.arena.ap_budget_literacy run --suite arena-tactical-literacy-v1 --prompt arena-turn-prompt-v5 --provider openai --binding artifacts/arena-ap-budgeting/binding-v1.json --output .local/arena-luna-tactical-literacy-prompt-v5-01 --live
```

**Future offline analysis command ? emits both matched V1/V5 and three-way reports:**

```powershell
.venv/Scripts/python.exe -B -m aig.arena.ap_budget_literacy compare --binding artifacts/arena-ap-budgeting/binding-v1.json --candidate .local/arena-luna-tactical-literacy-prompt-v5-01 --output .local/arena-luna-tactical-literacy-prompt-v5-01-analysis
```

Offline scripted plumbing uses `dry-run` and `compare --scripted` with separate output paths. It never measures V5 ability. The next live run must be separately authorized. Stop after preparation.

## Files and validation

Added production files: `backend/aig/arena/ai/ap_budget_prompt.py` and `backend/aig/arena/ap_budget_literacy.py`. Added snapshot/test: `tests/fixtures/arena-turn-prompt-v5.txt` and `tests/test_arena_ap_budget_prompt.py`. Added documentation: this file. Added frozen artifacts: `artifacts/arena-ap-budgeting/binding-v1.json`, `budget.json` and `validation.json`.

Only three pre-existing files changed during this task: `tests/test_arena_fireball_methodology.py`, `tests/test_arena_tactical_literacy.py`, and `tests/test_arena_sequential_prompt.py`. Each scopes historical tests around explicitly named additive modules. Historical runtime verifiers and evidence remain untouched; the new verifier independently requires all historical source bytes.

Preservation inventory: `.local/arena-ap-budgeting-preparation/preservation-before.json` and `preservation-result.json`. Of 14,268 pre-existing inventoried files, 14,265 remain byte-identical, three are the intentional test-scope changes, and none are missing. This includes V1/V4 literacy evidence, bounded Stage 1, prior smokes, stepwise evidence, profiles, game rules and Empire. Existing unrelated dirty work is preserved.

Final focused suite: **10 tests passed**, with sockets forbidden. It checks exact V1 ancestry and all historical prompt hashes, AP-only semantic/snapshot constraints, fake OpenAI/Ollama wire equality except prompt including repair, unchanged defaults/schema/repair/controller methods, strict/bounded AP 1?5 and partial recovery replay, independent failure/accounting and source-drift denial, frozen cohort tamper rejection, historical analysis reproduction, and three-way scripted generation/provenance rejection.

Scripted final artifacts: `.local/arena-ap-budgeting-preparation/scripted-01` and `scripted-01-analysis`. All 122 scripted slots replayed; provider ledger is empty. This is plumbing validation, never model evidence. The final V5 verifier passed with 122 matched slots. The development binding is preserved separately in `.local/arena-ap-budgeting-preparation/development-binding.json`; only the artifact binding named in the commands is the final recipe.

The repository uses unittest; pytest is not installed. Test command:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -p 'test_arena*.py' -q
.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_arena_ap_budget_prompt.py -q
```

Full Arena regression: **528 tests passed in 394.318 seconds**. Final focused suite: **10 tests passed in 40.688 seconds**. Final source/evidence preservation and binding verification passed after regression completion. No live inference occurred. Preparation is ready for the separately authorized matched rerun; V1 remains default.
