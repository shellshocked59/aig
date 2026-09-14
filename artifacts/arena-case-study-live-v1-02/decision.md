# Batch 2 decision: PASS for continuation unchanged

Recommend **Batch 3 only as the next separately authorized scope**: the next frozen ten triplets, 30 matches, under the existing 1,700-request batch ceiling and all current per-control/per-match limits. No further batch was run. Preserve the frozen benchmark and collect more evidence without tuning or replacing failed/capped matches.

## Integrity and expenditure

All 30 intended Batch 2 matches were started and sealed in frozen order, with five Luna Red and five Luna Blue matches per control. Batch 2 consumed **447/1,700 requests**: Strict 64, Bounded 74, Stepwise 309. The current source/runtime verifier, live batch gate and final offline verifier passed. All **60 cumulative matches replayed exactly**, with **1,030 reserved/completed requests and zero pending requests**. There was no fallback, schedule drift, repeated provider request, bounded loop, or post-EndTurn request.

The original Batch 1 directory remains byte-for-byte unchanged: 2,524 original files checked. The continuation directory contains a verified copy of its completed prefix; 2,485 copied immutable evidence/binding files were checked after the run. This allowed the unchanged resume mechanism to start at MATCH-011 Bounded/request 584 while retaining Batch 1's aggregate reports. No within-Batch-2 interruption recovery was needed. The live process exited normally at --through-batch 2.

Both the Batch 2 standalone and cumulative 60-match report/figure views were generated with the frozen analyzer. All candidate contracts, controls, repair behavior, model/profile, heuristic, game rules, opening, schedule, caps, telemetry and statistics remain unchanged. The added reporting scripts only inspect recorded evidence and invoke existing offline functions.

Batch 2 used **1,170,229 tokens**, **748.681 provider seconds (12.48 minutes)** and **795.958 backend controller seconds**. Observed process wall time was at most **1,013.412 seconds (16.89 minutes)**, including initial verification of the copied prefix and a short completion-observation delay. Batch 1 used 583 requests, 1,524,963 tokens, 963.222 provider seconds and at most 1,160.412 wall seconds. These timing measures overlap and must not be added together.

Cumulative usage is **1,030 requests, 2,695,192 tokens and 1,711.903 provider seconds**. At the cumulative observed means:

| Projection | Requests | Tokens | Provider hours |
| --- | ---: | ---: | ---: |
| Remaining 240 matches | 4,120 | 10,780,768 | 1.902 |
| Full 300-match study | 5,150 | 13,475,960 | 2.378 |

Central expenditure remains manageable. The full-study sensitivity obtained by assigning every future game each control's observed minimum/maximum is 1,590–15,590 requests; this is not a confidence interval, and its high end exceeds the 15,000 global ceiling and some arm limits. Existing guards must stop the run if reached. Lower averages can reflect early forfeits, while capped games censor natural duration. No dollars are estimated.

## Increased repair exhaustion is a material qualification

Batch 2 had **7/30 repair-exhaustion forfeits (23.3%)**, versus **2/30 (6.7%)** in Batch 1. Batch 2 counts were Strict 3, Bounded 3 and Stepwise 1; cumulative counts are 4/20, 4/20 and 1/20, respectively. Five Batch 2 forfeits occurred in MATCH-018–020, so temporal clustering is visible rather than averaged away.

All 447 Batch 2 receipts have status `returned`. The exhausted attempts record `invalid_reference` or `schema_validation`, followed by unsuccessful permitted repair. There is no recorded transport outage or evidence-corruption signature here. Exact match/wave/request IDs and categories are in [repair-failure-audit.json](repair-failure-audit.json). This is consequential model-output reliability data; it is not a reason to hide losses, retry matches or tune frozen repair. The frequency merits another single-batch checkpoint. It does not presently identify an infrastructure defect requiring suspension.

## Bounded versus Strict

| Recovery/cost | Batch 2 | Cumulative |
| --- | ---: | ---: |
| Replans | 17 | 43 |
| Replans recovering at least 1 AP | 14/17 (82.4%) | 38/43 (88.4%) |
| AP recovered | 32 | 77 |
| Mean AP recovered/replan | 1.882 | 1.791 |
| Second invalidities/replans | 2/17 (11.8%) | 6/43 (14.0%) |
| Bounded requests | 74 | 169 |
| Strict requests | 64 | 149 |
| Extra Bounded requests | 10 (15.6%) | 20 (13.4%) |
| Bounded requests/Luna turn | 1.682 | 1.798 |
| Strict requests/Luna turn | 1.208 | 1.307 |

Bounded remains near Strict in **total requests per intended match**, but it used 37.6% more requests per attempted Luna turn cumulatively. Different match durations and early forfeits affect the match-level comparison. Cumulative final execution truncations were 6/94 Bounded turns versus 46/114 Strict turns; truncation-derived AP was 12 versus 124. Recovery works mechanically, but **both controls are 0 wins/20 losses**, including four forfeits each. This does not establish that recovering AP improves game outcomes or that both controls have equal underlying performance.

## Stepwise caps and comparison

Batch 2 had **1/10 Stepwise capped matches**, MATCH-015, which stopped at 140 requests after 92 started player turns and 45 completed rounds. It received no winner. Its 140 requests were **45.3% of Batch 2 Stepwise volume**. Cumulatively, **3/20 Stepwise matches (15%)** hit the cap; their 420 requests account for **59.0% of 712 Stepwise requests**. All three occurred with Luna Red. That side concentration is descriptive at a small sample, not evidence of a general causal side effect.

The other 17 Stepwise matches used 292 requests total. The cap therefore remains important protection against long games. These results remain interpretable as the performance of a capped deployable controller; they cannot establish the uncapped win rate of the three stopped games. Do not increase the cap or manufacture a winner.

Cumulatively Bounded used **1.798 vs 3.096 requests/turn** for Stepwise (41.9% fewer), **5,031 vs 7,874 tokens/turn** (36.1% fewer), and **3.160 vs 4.957 provider seconds/turn** (36.3% fewer). Stepwise had zero execution truncations but only two wins versus Bounded's zero, with three nonwins censored by the request limit. The evidence does not establish comparable game quality or a winning control.

## Outcomes, EndTurn and tactical evidence remain interim

| Control | Batch 2 W/L/no-result | Cumulative W/L/no-result | Cumulative Wilson 95% win interval |
| --- | --- | --- | --- |
| Strict | 0/10/0 | 0/20/0 | 0–16.1% |
| Bounded | 0/10/0 | 0/20/0 | 0–16.1% |
| Stepwise | 1/8/1 | 2/15/3 | 2.8–30.1% |

Losses include forfeits; limits remain nonwins in win-rate denominators. The heuristic record is reported separately by opponent control: 20/0/0 versus Strict, 20/0/0 versus Bounded, and 15/2/3 versus Stepwise. It continues to win most observed matchups. This is conditional on one canonical opening, fixed rules, frozen controls and this service period, not an absolute heuristic skill rating.

Across 20 matched triplets: 15 have loss/loss/loss for Strict/Bounded/Stepwise, three loss/loss/limit, and two loss/loss/win. There are no Strict-loss/Bounded-win or Bounded-win/Stepwise-loss triplets. No confirmatory paired tests are run on this interim cohort.

Batch 2 explicit EndTurns were Strict 21, Bounded 18 and Stepwise 20; immediate stops were 0, 0 and 6. Cumulative explicit stops are 42/41/43 and immediate stops 1/0/10. All **126 observed explicit EndTurns** have zero subsequent requests in their turn. Batch 2 intentional AP left was 28/14/46; cumulative 60/39/90. The supplemental engine audit found immediately legal damaging actions at 4/1/3 Batch 2 stops, cumulatively 13/7/5. These are potentially questionable tactical choices, not mechanical contract failures or proof that another action was preferable.

Fireball, Snipe and Shield Bash effects were reconstructed from engine transitions, without a model judge. Batch 2 Fireball enemy/friendly damage was Strict 72/42, Bounded 86/90, Stepwise 794/111. Long Stepwise trajectories and repeated unit down/revive cycles inflate event totals; raw damage, casts and AP do not form a quality score. Detailed hit/down/displacement counts, AP taxonomy, side strata, per-match hashes and paired cost/length differences are in the two full reports and machine-readable audit.

**PASS for a separately authorized Batch 3 under the unchanged contract.** Preserve repair exhaustion, request-limit censoring and temporal/side patterns as benchmark data. Do not authorize the remaining 240 implicitly, tune controls, or claim superiority at n=20/control.
