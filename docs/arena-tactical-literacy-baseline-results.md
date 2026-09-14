# Luna tactical-literacy audit: live baseline

Run: `.local/arena-luna-tactical-literacy-01`, 2026-09-14. User authorized only the frozen focused audit. No prompt tuning, control changes, full matches, retries, or request-budget extension occurred.

**Recommendation: address AP budgeting and post-DOWNED sequencing before committing to the 300-match case study.** This baseline demonstrates repeated plan inconsistencies, not a general inability to do damage arithmetic. Preserve these results and version any subsequent representation change explicitly.

## Spending and completion

The hard ceiling stopped the run at **140 requests: 122 initial decisions plus 18 static repairs**. All 122 decisions that reached the provider produced accepted plans. All 18 repairs succeeded; their first responses failed `ap_budget` validation. First-response static validity was 104/122 (85.2%). No transport failure or exhausted repair occurred among actual requests.

Four scheduled decisions received no request: `03-POSITION-002`, `03-POSITION-003`, `03-POSITION-004`, `03-REVIVE-004`. The frozen runner records the first as a `provider failure` row with zero attempts, and reports 123 completed rows / 3 unstarted. **Actual model coverage is 122/126 decisions; the ceiling-denial row is not a Luna failure.** The stop surfaced through the runner's generic `provider_exception`/RuntimeError path; the reservation ledger and zero-attempt telemetry establish budget denial. Do not interpret it as source drift or a network problem.

Tokens: **342,189 input** (251,243 cached), **6,686 output**, **348,875 total**, zero reasoning tokens. Provider request time totaled **165.98 seconds**. Dollar cost is not calculated because no frozen pricing model exists.

## Main findings

1. **AP arithmetic is a repeated observable problem.** Eighteen initial responses (14.8%) exceeded the available AP. `AP-002` and `MULTI-004` required repair in all three repeats. A typical rejected plan was Snipe (2 AP) + Attack (1 AP) under a 2 AP observation. The unchanged contract explicitly gives both costs and remaining AP, so this is not missing input. Repairs corrected AP, but did not always yield coherent subsequent execution.
2. **Post-DOWNED sequencing failed 15 times.** Five fixtures failed in all three repeats: `POWER-002`, `DOWNED-003`, and `FIREBALL-005/007/008`. Each selected an Attack after an earlier Attack had already DOWNED that target. This is direct state-transition/sequence inconsistency. In `POWER-002`, the first action actually downs the target; the illegal second Attack prevents a full-plan pass. Do not describe that result simply as failed POWER arithmetic.
3. **Current legal-action/LOS adherence failed twice.** Both attempted `POSITION-003` decisions selected Snipe through blocked LOS, despite its absence from the current legal action list. The third repetition was not requested. The literal frozen label is ?arithmetic/rule-inconsistent,? but the observed defect is legality/LOS, not arithmetic.
4. **Basic damage and Core outcomes have positive evidence.** The four single-action probes met their outcome predicates in all 12 trials; both witnessed Core-winning fixtures succeeded in all six. The two-action Snipe + Attack objective succeeded in 3/3. Conversely, the two-basic-Attack lethal opportunity was missed in 3/3: Luna selected a nonlethal Snipe. That legal preference does not prove it misunderstood lethal arithmetic.
5. **No Fireball was selected in any of the 24 Fireball-probe decisions.** The category's 9/18 witness-based success rate reflects alternative basic attacks; all nine failures were stale Attack suffixes. The run therefore does **not** establish Fireball-area or friendly-fire comprehension. No Heal was selected either. Revive was selected three times, but the revived unit was not subsequently used; immediate revived-unit action comprehension remains untested by those outputs.

## Frozen objective rates

These are outcome-predicate rates, not category comprehension certificates. Denominators include completed records with frozen satisfying witnesses. Diagnostic-only/no-witness fixtures are excluded. AP competence is measured separately through initial-response validation above.

| Category | Satisfied / frozen denominator | Interpretation |
|---|---:|---|
| Single-action damage | 12/12 | Same Snipe choice can satisfy both lethal and nonlethal damage predicates; does not demonstrate explicit boundary classification |
| Multi-action | 3/6 | Snipe + Attack succeeds; two-Attack lethal line missed legally |
| POWER | 3/6 | Three failures are illegal suffixes after successful initial down |
| WARD | 6/6 | Outcomes satisfy predicates; nonlethal Snipe choice alone does not prove WARD understanding |
| Core | 6/6 | Both witnessed winning objectives achieved |
| DOWNED/Finish | 6/9 | Standalone Finish succeeds; Down + Finish replaced by stale Attack in 3/3 |
| Revive/Heal | 3/8 | Legal alternatives remain preference-sensitive; final Heal repetition unrequested |
| Fireball | 9/18 | Alternative attacks only; no actual Fireball choices |
| Position | 2/3 in frozen summary | Only 2 actual witnessed decisions, both successful; denominator includes one no-request ceiling-denial row |

Literal classification counts: 56 correct mechanical recognition, 8 legal missed opportunities, 41 ambiguous tactical choices, 15 sequence failures, 2 first-action rule inconsistencies, 1 zero-request ceiling-denial record. All 17 execution-invalid plans preserve their valid committed prefixes. These classes must not be collapsed into a model arithmetic score.

## Integrity and artifacts

Frozen bindings: `arena-tactical-literacy-v1`, `arena-mechanics-oracle-v1`, `arena-literacy-fixtures-v1`, rules v2 / scenario v1, `arena-turn-prompt-v1`, Observation V1, plan schema V1, `luna-config-v1` (`gpt-5.6-luna`, reasoning none, max output 512, store false, SDK retries 0).

Suite payload SHA-256: `57ece3f65fc3f11d71f3f45bc528c52abc753d0843d604268697db3584a2a317`.

All 122 accepted-plan traces independently replayed. Saved starting states/observations match frozen fixtures and observation hashes. Offline re-evaluation reproduces every stored mechanics evaluation. Source hashes still match; 140 ledger reservations reconcile exactly with 140 recorded attempts. All 116 historical preservation hashes remain unchanged. No production or frozen-suite source was modified during the run.

Run artifacts retain the original summary, failure row, suite, per-attempt schema-shaped outputs, telemetry, parsed plans, execution traces and replay checks. Interpretation corrections above are additive and do not rewrite the frozen results.

Detailed artifacts:

- `.local/arena-luna-tactical-literacy-01-analysis/report.md`: category and all 42 per-probe rows, plus exact failure actions.
- `.local/arena-luna-tactical-literacy-01-analysis/analysis.json`: verified machine-readable analysis and first-response errors.
- `.local/arena-luna-tactical-literacy-01-analysis/evidence-hashes.json`: immutable run-file hash inventory.
- `.local/arena-luna-tactical-literacy-01-analysis/analyze.py`: offline reproduction of integrity checks and descriptive aggregates.

## Interpretation limits and next decision

The frozen predicates accept equivalent outcomes rather than insisting on an ability. This avoids false failures but means these states did not isolate every requested competency: Fireball and revived-unit action knowledge remain unresolved, and threshold choices do not expose beliefs. The original suite and scoring remain frozen; do not revise them retrospectively to improve or worsen these results. Any future explicit-question/ability-specific diagnostic would be a separately versioned instrument, not a rerun of the same baseline.

The evidence is sufficient to prioritize AP budgeting and dynamic target-status representation before a large benchmark. A new prompt/observation version and a separately authorized comparison on these same frozen probes would test whether those repeated failures improve. This run does not authorize that change, additional inference, completing the four omitted requests, or the 300-match benchmark.

Approximate run elapsed time from manifest to final summary timestamps: **172.6 seconds** (includes local orchestration; provider time reported separately).
