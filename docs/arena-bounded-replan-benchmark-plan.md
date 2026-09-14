# Luna strict full-turn versus bounded replan: Phase 2 preparation

Status: offline preparation only. **No live inference is authorized or performed.** Adaptive · Replan if blocked remains opt-in. This plan does not change settings, prompts, rules, repairs, or controller behavior.

The research question is whether bounded replanning recovers substantial usable AP after execution truncation while retaining a call count much closer to full-turn than stepwise. AP expenditure is descriptive, not a tactical quality score. Turn-level matched states are the appropriate first experiment; full matches introduce diverging states, compounding provider failures, and less direct cost attribution.

**This is an end-to-end control-mode experiment, not a same-plan counterfactual.** Each live arm independently requests its initial Luna plan. Identical states do not guarantee identical initial plans. Within-bounded AP recovery is directly observed; between-arm AP deltas also reflect model nondeterminism. Historical selection enriches failure boundaries and is not representative of all product turns. Repeated turns from the same source match are correlated; retain source-match grouping and do not claim 42 independent games or population significance.

## Audit of the existing proposal

The implementation report and `.local/arena-bounded-paired-plan.json` describe seven `arena-probes-v1` fixtures × two repetitions × two controls = **14 pairs, 28 intended turns**. The number **84 means the architectural request ceiling**, not 84 intended turns or 42 states. Strict can request twice and bounded four times, hence 14 × (2 + 4). It is already a turn benchmark, not a full-match runner. Ordering is repetition, probe, strict then bounded. There is no preflight. Its v6 failure policy aborts the entire schedule on ordinary provider failure.

The seven fixtures are finish_or_core, fireball_friendly_fire, revive_decision, shield_bash_position, snipe_vs_basic, team_elimination, winning_core_line. Existing fixtures, recipe, runner, smoke artifacts (including failed recovery attempt), implementation report, and historical audit remain unchanged. The old saved source manifest is stale relative to this checkout; it must not be used for a live run.

Do not use that proposal unchanged: the historical V1 probe cohort truncated only 4/28 accepted turns, versus 72/100 in full matches. Retain its frozen contracts, fixtures, executors, and adapter; add only historical selection, reporting, ceilings, and independent-case scheduling in `aig.arena.bounded_replan_comparison`. Its schedule version is `arena-bounded-comparison-schedule-v1`, experiment version `arena-bounded-luna-comparison-v1`. This is explicitly an additive schedule policy over v6 bindings, not a claim that v6 itself now continues failures.

## Frozen contracts

| Item | Binding |
|---|---|
| Strict | arena-control-full-turn-v1 |
| Bounded | arena-control-full-turn-bounded-replan-v1 |
| Base recipe | arena-benchmark-v6; SHA-256 0b38a61ab30290054e6ec0f1d3fec4f77975b8520e34cb34e69b6bab6fce7502 |
| Prompt | arena-turn-prompt-v1; SHA-256 5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7 |
| Observation | arena-observation-v1 |
| Plan schema | arena-turn-plan-schema-v1 |
| Wire schema hash | 00bcb84ee394ded257851a65fc8026a8f7161fc53d231168025554417106a4ea |
| Static repair | Existing category-only full-turn feedback; at most one repair per wave |
| Profile | luna-config-v1 |
| Model | gpt-5.6-luna; reasoning_effort none; max_output_tokens 512; store false; max_retries 0 |
| Transport | Existing OpenAIArenaTurnProvider / Responses adapter, existing JSON-schema wire format and frozen timeout |
| Environment / rules / scenario | arena / arena-rules-v2 / arena-scenario-v1 |
| Frozen probes | arena-probes-v1 |
| New fixture set | arena-bounded-historical-states-v1 |
| Replay | arena-trace-v2 / arena-command-v2 / arena-snapshot-v2 |

V6 also lists qwen-config-v1, but this experiment permits **only OpenAI Luna**. Source revision and dirty status are saved with hashes of all backend Python and benchmark JSON files, the audit script, this plan, and the new tests. Untracked implementation files are included: the Git revision alone is insufficient. No saved identity uses “latest.” Original historical artifacts receive their own SHA-256 inventory.

The existing Luna adapter already uses a JSON-schema Responses format. Preserve it byte-for-byte; do not switch to the separate constrained-output experiment or introduce any new output mechanism. No prompt-v3, action IDs, new repair feedback, Fireball guidance, or stepwise control enters either arm.

Strict requests one plan, executes sequentially, then truncates and EndTurns on first execution invalidity. Bounded preserves the committed prefix, discards the rejected action plus stale suffix, builds a fresh observation, and permits one replacement plan. Replacement success or second invalidity ends the nonterminal turn. No third wave. Clean short/empty plans EndTurn in both arms; unused AP alone never triggers replanning. Terminal actions stop immediately without EndTurn or another request. Provider exhaustion preserves the current state without EndTurn and marks the arm failed.

**Prompt caveat:** prompt-v1 describes normal full-turn strict planning and is not literally a description of adaptive recovery. It remains unchanged in both arms. The fresh observation's `action_points_remaining` is authoritative on a partial turn. This caveat is intentional to isolate control mode.

## Historical evidence and selection

The new audit imports `scripts/arena-bounded-replan-audit.py`, reproduces its existing Luna cohort summaries, and extends the output in a new preparation directory. It audits all **184 accepted historical Luna turns** across four separate cohorts: 100 V1 full-match turns, 28 V1 probes, 28 prompt-v2/Observation V1 probes, and 28 prompt-v2/Observation V2 probes. Only the 100-turn V1 full-match cohort supplies primary historical cases. The other prompt/observation cohorts remain separate context.

For each accepted turn, the audit verifies the observation hash, reconstructs its exact initial state from original commands and command offsets, statically parses the accepted plan, reproduces execution, and checks the original final snapshot. It records path/row/turn/player ID, initial state and observation hashes, planned AP, prefix AP, remaining AP, invalid index/type/reason, suffix lengths, terminal status and replan eligibility. `stale_suffix_length` includes the rejected action; `suffix_after_invalid_length` excludes it. A clean turn has null invalid-boundary fields, not an invented invalidity. Historical input hashes are checked again after analysis.

The V1 full-match cohort has 102 attempted Luna turns, 100 accepted, two failed after repair, 112 actual requests and ten static repairs. Among accepted plans: 72 truncations, all eligible and nonterminal; 28 clean; 260 total executed AP; 219 AP at eligible boundaries (3.042 AP/boundary). These numbers do not predict what a replacement model plan will do.

| Historical characteristic | Counts |
|---|---|
| Invalid index (zero-based) | 0: 6; 1: 29; 2: 32; 3: 4; 4: 1 |
| AP remaining | 1: 2; 2: 18; 3: 33; 4: 13; 5: 6 |
| Cause | target range: 24; Fireball range/board: 16; target status: 11; destination: 11; line of sight: 9; inactive actor: 1 |
| Early versus mid/late truncation | indices 0–1: 35; indices 2–4: 37 |
| High versus low recoverable AP | ≥3: 52; exactly 1: 2; exactly 2: 18 |

Selection is frozen before inference. Deduplicate exact state hashes. Repeat the quota sequence three historically invalid cases then one clean case. First choose among the least represented available phase (early/mid/late); then maximize inverse-frequency coverage of phase, player, invalid index/reason, AP category, unit/downed count, core pressure and currently available action types. Diminish rewards as tags are covered; break ties by SHA-256 of stable source case ID. This uses no simulated replacement success, damage outcome, or tactical score. Phase means thirds of the recorded match's turn-number span, not a claim about semantic game phases or a completed match.

Stage 1 takes the first 12 historical selections and adds frozen Revive and Finish/Core probes. Stage 2 continues the same selection for another 20 historical states, adds the other five frozen probes, and adds three authentic pre-EndTurn states after historical prefixes with respectively 1, 2, and 3 AP remaining. Those boundary states are not made by arbitrarily editing AP. Choose their parents by case-ID hash within each AP group. They have no historical initial-plan truncation label at that new start. Stable `pair-001` through `pair-042` IDs are assigned once; Stage 2 never reruns Stage 1 pairs.

| Category | Stage 1: 14 pairs | Full design: 42 pairs |
|---|---:|---:|
| Historical early truncation | 4 | 12 |
| Historical mid/late truncation | 5 | 12 |
| Historical clean controls | 3 | 8 |
| Frozen probes, no assigned historical label | 2 | 7 |
| Historical partial-state starts, no assigned label | 0 | 3 |
| High recoverable AP among labeled truncations | 6 | 15 |
| Low recoverable AP among labeled truncations | 2 | 2 |
| Exactly 2 recoverable AP | 1 | 7 |
| Historical phase early / mid / late | 4 / 4 / 4 | 10 / 11 / 11 |
| Initial AP | 14 at 5 AP | 39 at 5 AP; one each at 1, 2, 3 AP |
| Blue / red starts | 7 / 7 | 23 / 19 |

The pilot covers invalid indices 0–4 and five of six historical causes; full selection covers all six. Unit counts range 3–8 in the pilot and 2–8 overall. DOWNED states, available Revive/Finish/Snipe/Fireball/Shield Bash actions and core pressure are recorded. Full design includes each named tactical probe once. The rare low-AP and inactive-actor cases are deliberately represented by the same coverage rule, not by selecting only favorable recovery outcomes. Detailed distributions and exact snapshots are in selection.json.

## Pairing, metrics and interpretation

Each pair instantiates two detached simulations from exactly the same snapshot. The saved plan binds pair ID, initial state/observation hashes, player, AP, all contract IDs, rules/scenario and source manifest. Order is deterministic: strict pair-001, bounded pair-001, strict pair-002, bounded pair-002, etc. Independent provider instances use the same adapter/configuration in both arms. Interleaving reduces collection-time confounds without randomization.

Every arm preserves accepted plans, observations/hashes, safe per-attempt telemetry, execution attempts, command trace, final snapshot and state hash. No raw model prose or hidden reasoning is saved. Reliability includes initial first-response validity (over attempted initial responses), wave-specific static invalidity, repair attempts/successes, provider failures, completed turns and terminal outcomes. A failed/unstarted arm remains visible; headline started-turn denominators and scheduled/unstarted counts are explicit. Unknown token fields stay null rather than becoming zero.

Initial and replacement execution invalidity are separate metrics. Initial metrics include planned AP/action count, first invalid action/index/reason, AP before failure, AP remaining and discarded suffix. Replacement metrics include fresh observation hash/AP, planned/executed AP, replan trigger/success, static repair and second invalidity. Replan success means an accepted replacement that completes without execution rejection (including a short or empty replacement); separately report recovered AP so “success” is not mistaken for useful action expenditure. Second-invalid and replan-success rates use requested replacement waves as denominators.

**AP recovered = replacement AP actually committed after the first strict-equivalent truncation boundary in that bounded arm.** It is zero on replacement provider failure or rejection before any successful replacement action. It is not the paired AP delta, a counterfactual claim about the strict arm's independently generated plan, or evidence of tactical optimality.

Turn totals record AP available/executed/unused, committed commands, terminal result and final hash. Report clean `short_plan_unused_AP`, replacement short-plan leftover AP, final truncation-derived leftover AP, failed-provider leftover AP and terminal leftover AP separately. Normal replay combat metrics preserve damage, friendly damage, downs/revives/finishes, core pressure, pushes and action/AP counts. Fireball quality is not a primary objective.

Headlines compare mean actual attempts, executed AP, unused AP, initial truncation rate, completion/provider-failure rate, provider latency, backend thinking time and tokens per started turn. Bounded adds replan rate/success, recovered AP per replan and second-invalid rate. Category strata are separate; do not pool selected states into a representative product failure-rate estimate. The paired JSON contains all per-arm metrics/final hashes plus extra requests, AP, token and latency deltas and per-player tactical state differences. The Markdown table provides readable AP/request/replan/delta rows; there is no opaque quality score.

Calls per turn counts all actual transport attempts, including static repairs and failed attempts. Strict has one initial wave plus at most one static repair: max two. Bounded has two waves, each with at most one static repair: max four. Static repair is never counted as a replan. A durable reservation ledger is written before each transport; accepted, failed and ceiling-denied traces must reconcile with it. A denial does not create a transport attempt. A process crash is not a completed experiment and cannot be resumed or interpreted as zero spending.

Per-attempt latency and input/cached-input/output/reasoning/total token counts aggregate to wave and turn. `backend_thinking_seconds` measures orchestration through full server-side control resolution, including source/accounting guards, separately from summed provider latency and offline artifact/replay verification. Browser animations are excluded. Paired deltas retain both time measures. Unknown token telemetry propagates to null sums. No frozen dated Luna pricing assumption is configured; `pricing` and estimated dollars stay null. Do not invent prices.

## Request estimates and ceilings

Baseline static-repair rate is 10/102 = 0.0980 per attempted historical initial wave. A broad budget scenario uses the accepted-turn historical truncation rate 0.72 (conservative simplification: ignores initial provider exhaustion suppressing some replans), and assumes the same repair rate on replacements. For N pairs: strict expected N×1.0980; bounded N×1.72×1.0980; total N×2.72×1.0980. Nondeterminism, stratification, partial AP and different replacement repair rates make this a budgeting scenario, not a forecast or inference result.

| Scope | Base requests if no replan/repair | Expected strict | Expected bounded | Expected total | Architectural max strict / bounded / total | Recommended hard ceilings strict / bounded / total |
|---|---:|---:|---:|---:|---|---|
| Stage 1: 14 pairs, 28 turns | 28 | 15.37 | 26.44 | 41.81 | 28 / 56 / 84 | **18 / 32 / 50** |
| Stage 2: 28 additional pairs, 56 turns | 56 | 30.75 | 52.88 | 83.62 | 56 / 112 / 168 | 36 / 64 / 100 |
| Both stages: 42 pairs, 84 turns | 84 | 46.12 | 79.32 | 125.44 | 84 / 168 / 252 | 54 / 96 / 150 |

The base count is the normal no-extra-wave minimum for a completed scheduled dataset; integrity stops or denied budgets can leave fewer actual attempts and unstarted cases. A label-based sensitivity calculation for the pilot (nine historical triggers, plus 2×4/28 probe triggers, with the same repair rate) gives about 40.94 total requests. Neither calculation guarantees those cases will truncate again.

The pilot ceiling permits four strict repair attempts above 14 base calls; bounded permits all 14 initial calls, all 14 replans, plus four repairs, or more repairs when fewer replans occur. It leaves useful headroom above the historical budget scenario while preventing escalation to the architectural maximum. Each arm and the total are guarded before every attempt, including repairs. Hitting any ceiling preserves partial state and stops the schedule; no automatic budget extension, retries, or replacement trials.

## Replay, purity and stopping

Every committed command passes through the unchanged authoritative simulation. Replay reconstructs the initial snapshot and verifies each command/hash/combat metric plus the exact final state. Check completed, truncated, second-invalid, terminal and provider-failed partial states equally. Invalid commands are logged as attempted actions and are not committed replay entries. Provider failure retains a prefix without EndTurn. No heuristic fallback is constructed by the live runner.

Ordinary recognized transport, authentication, envelope or exhausted static-repair failures mark that arm failed, preserve evidence and continue the next independent arm/pair. No retry-until-success. A source/evidence drift, wrong provider, fallback contamination, contract mismatch, request-accounting mismatch, replay mismatch, unexpected execution/programming error or unclassified provider failure is a hard stop. Provider accounting and version checks run on failed calls too. Source/evidence guards run before requests; final checks run after resolution. Output roots are create-only, with no resume/overwrite behavior.

## Frozen stepwise context

Use only existing Phase 7C Luna evidence and `docs/arena-stepwise-expanded-results.md`. The frozen 28-turn cohort used 89 requests (3.179 per turn), executed 112 AP (4.00/turn), completed 28/28 turns with zero selected-action execution failures, and used one static repair. Total provider latency was 136.236 seconds (4.866/turn), tokens 156,005 (5,571.607/turn). Initial first-response validity was 87/88 decisions. No dollars were configured. Preflight is excluded.

This is contextual: stepwise used different observations/prompts, seven repeated probes, and current-action decisions rather than historical full-match states. It cannot establish a causal paired improvement or a “percentage of stepwise benefit recovered” for this dataset. The relevant product comparison is whether bounded attempts/turn remain much nearer approximately one full-turn call than the historical 3.179 stepwise calls, while AP/reliability improve. Do not run stepwise live here.

## Offline verification and artifact structure

Dedicated fake-transport tests exercise pairing, clean/short turns, fresh recovery, second invalidity, per-wave repair, failures followed by later independent pairs, partial replay, ceiling denial before transport, source drift, wrong provider, accounting corruption, replay mismatch, terminal initial/replacement wins, AP recovery and token/latency totals. They override transport in the real provider class so existing static parsing/repair behavior is exercised. Socket connects are forbidden in this suite and the dry-run CLI.

The historical dry run uses the recorded accepted plan as the first response in both arms when available, followed by a deterministic single currently legal action for the fake replacement. Probe/partial-state cases also use that scripted action. This secondary **offline policy replay** verifies evidence structure and mechanics only; scripted replacement AP, tokens and timings are not model-quality predictions. Mock tokens are explicitly synthetic. It does not change either live arm's independent initial requests.

Preparation root: `.local/arena-bounded-luna-comparison-preparation-02/` contains historical-audit.json, selection.json, stage1-plan.json, stage2-plan.json. A fresh live root `.local/arena-bounded-luna-comparison-01/` is reserved by these instructions and must not exist before execution. The runner creates plan.json, request-ledger.jsonl, strict/pair-NNN/{turn.json,commands.json,final-snapshot.json}, bounded/pair-NNN equivalents, report.json, comparison.json and report.md. Stage 2 uses a distinct new root and only pair-015 onward. Offline roots are distinct and labeled OFFLINE SCRIPTED POLICY REPLAY.

Exact offline preparation and verification commands (PowerShell, checkout root):

```powershell
.venv/Scripts/python.exe -B -m unittest tests.test_arena_bounded_replan_comparison tests.test_arena_bounded_replan tests.test_arena_bounded_replan_recovery_smoke
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_comparison prepare --output .local/arena-bounded-luna-comparison-preparation-02
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_comparison dry-run --plan .local/arena-bounded-luna-comparison-preparation-02/stage1-plan.json --output .local/arena-bounded-luna-comparison-offline-01
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_comparison dry-run --plan .local/arena-bounded-luna-comparison-preparation-02/stage2-plan.json --output .local/arena-bounded-luna-comparison-offline-02
```

Do not rerun preparation over an existing root. Source changes invalidate plans; prepare into a new numbered root and review that concrete plan. Check validation evidence separately from this frozen document to avoid changing its source hash after preparation.

**Future Stage 1 command — not executed; requires separate explicit authorization for 28 intended turns with 18 strict / 32 bounded / 50 total attempts:**

```powershell
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_comparison run --plan .local/arena-bounded-luna-comparison-preparation-02/stage1-plan.json --output .local/arena-bounded-luna-comparison-01 --live
```

Future Stage 2 command, also unexecuted and separately authorized only after Stage 1 review:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.bounded_replan_comparison run --plan .local/arena-bounded-luna-comparison-preparation-02/stage2-plan.json --output .local/arena-bounded-luna-comparison-02 --live
```

## Recommendation and promotion evidence

Authorize only Stage 1 after reviewing the prepared plan and offline validation. Fourteen pairs supply direct enriched failure-boundary evidence and clean controls without repeating the already-passed mechanical smokes. Expand to the remaining 28 frozen pairs only if replay/accounting/purity are exact, intended failures/unstarted cases are honestly retained, enough execution boundaries occurred to evaluate recovery, and calls/latency/tokens remain worth investigating. A low trigger count is informative: do not add ad hoc states or repeat until favorable. Changes require a separately frozen design and authorization.

Promotion to normal playable Luna control would need consistent paired AP improvement, fewer severely truncated turns, useful recovered AP across causes/phases, calls far below stepwise, acceptable added backend waiting time and token load, and no tactical/combat deterioration. Inspect terminal leftover AP separately so rapid wins are not punished. This small enriched turn experiment alone cannot establish match quality or population significance; follow with separately authorized matched full-game evaluation, clustered uncertainty analysis and manual play/animation assessment. Do not change defaults based solely on AP expenditure or one arbitrary threshold. Adaptive remains opt-in throughout preparation and collection.
