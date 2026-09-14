# Arena case-study benchmark v1

Status: **offline preparation; no live run authorized**. Benchmark ID:
`arena-case-study-benchmark-v1`. The create-only contract is
`backend/aig/arena/benchmark_artifacts/arena-case-study-benchmark-v1.json`.
Its canonical payload SHA-256 binds this document, implementation, source tree,
runtime, schedule, candidate contracts, limits and analysis. It must never be
regenerated in place. Subsequent changes require a new benchmark version and
review. The preparation evidence lives in `artifacts/arena-case-study-preparation-v1/`.

## Questions and interpretation

How does observation/replanning cadence affect full-match gameplay, reliability
and inference cost? The primary contrasts are Bounded minus Strict and Stepwise
minus Bounded. Each Luna arm also has a paired matchup against Heuristic V2.
Useful full-turn intent, stale-state exposure, selective recovery and the cost of
continuous observation are hypotheses, not scoring assumptions. Strict matching
Bounded, Stepwise outperforming both, or the heuristic beating every Luna arm
are equally reportable outcomes. AP consumption and tactical counts are not
quality scores. Similar observed win rates do not demonstrate equivalence or
noninferiority; this study has no equivalence margin or power claim.

## Frozen candidate and comparator

| Component | Exact repository identity |
| --- | --- |
| Rules | `arena-rules-v2` |
| Scenario | `arena-scenario-v1` |
| Policy | `arena-policy-core-v1` |
| Full-turn prompt | `arena-turn-prompt-v6` |
| Stepwise prompt | `arena-step-prompt-v3` |
| Observation | `arena-observation-v4` |
| Semantic schema | `arena-turn-plan-schema-v2` |
| Repair | `arena-candidate-repair-v2` |
| Strict | `arena-control-full-turn-v2` |
| Bounded | `arena-control-full-turn-bounded-replan-v2` |
| Stepwise | `arena-control-stepwise-v2` |
| Model/profile | `gpt-5.6-luna` / `luna-config-v1` |
| Opponent | `arena-heuristic-v2` |

The request's name `arena-action-schema-v2` is a descriptive alias. The actual
validated and transmitted schema ID is `arena-turn-plan-schema-v2`; it is not
renamed. The contract records both to prevent a false binding claim.

Luna configuration: reasoning effort `none`, max output tokens 512, `store=false`,
SDK retries zero; request timeout 20 seconds. No temperature/seed override or
provider preflight inference. Model aliases can change behind a provider service;
this freezes the requested model and profile, not inaccessible server weights.
Record response/request IDs when supplied. Token telemetry missing at the provider
boundary remains null, including failed requests, rather than being imputed zero.

CandidateController, candidate observation/parser, shared policy and Repair V2
are used directly. The schema comparability check normalizes only action
`maxItems` (6 including optional EndTurn versus 1); the resulting schemas must
be identical. Both prompts include exactly the same policy text; wrappers differ
in cardinality and cadence. All arms obtain the same game facts, legal vocabulary,
AP rules and information fields. Their subsequent observations legitimately
differ as trajectories diverge. One static repair per planning wave receives the
rejected semantic output and current diagnostics/observation/AP. There is no
heuristic fallback, transport retry, or repair-until-success.

Strict requests one remaining-turn plan. Invalid execution commits its prefix,
discards the suffix and ends the turn. Bounded permits one replacement plan only
after execution invalidity with AP remaining; replacement invalidity ends the
turn. Stepwise observes after every successful action until AP exhaustion,
EndTurn, failure or victory. EndTurn costs zero, has no reason field, occurs last,
is intentional, and may leave AP. Clean short/empty plans end normally. Neither
short plans nor EndTurn trigger bounded replanning. Victory prevents further calls.

Heuristic V2 is deterministic: sorted actors/actions, stable canonical JSON
tie-breaking, fixed scoring and exact detached simulation; no RNG. Its file and
its V1 tactical-helper dependency have separate SHA-256 bindings, and all engine
dependencies are also source-bound. Memoization of identical observations reuses
the same immutable heuristic plan; it does not change policy. Heuristic exceptions
or invalid actions are integrity defects, never ordinary wins/losses.

## Exactly 300 matches

There are 100 matched slots, `MATCH-001` through `MATCH-100`, each played once by
Strict, Bounded and Stepwise Luna against Heuristic V2: 100 matched triplets, 300
full matches, and 100 matches per Luna control. The heuristic participates in all
300; it is not a fourth model arm.

Odd slots assign Luna Red; even slots Luna Blue. Every arm receives the same
side assignment and initial snapshot in its slot. Each arm therefore has 50 Red
and 50 Blue games. Blue always starts under the frozen rules. The scenario has
no seed or setup randomness; all snapshots have the same exact hash.

`scenarios.py` only supports this canonical mirrored 9×5 opening. Tactical probes
and damaged midgame states are diagnostic fixtures, not an existing opening
distribution. We choose the canonical scenario plus deterministic side balance;
we do not invent opening diversity. This limits generalization to this starting
position, opponent and collection period. Repetitions sample independent model
responses, not 100 independent maps. Matching means identical starting conditions
and shared profile/policy, never identical initial plans or action sequences.

Ten batches contain ten consecutive slots (30 matches each). Within slot n, use
the fixed three-order rotation: Strict/Bounded/Stepwise, Bounded/Stepwise/Strict,
Stepwise/Strict/Bounded, then repeat. Each arm occupies each order position 33 or
34 times. Each batch has five Red and five Blue slots. No runtime randomization.

## Heuristic-only reference decision

Do not add a new reference cohort to this schedule. The existing offline
`docs/arena-heuristic-v2.md` reports V2/V2 on the same opening: Blue won by Core
destruction after nine player turns, with 30/0 Core damage and 25/20 AP spent.
It demonstrates a terminating deterministic environment and policy-specific
opening asymmetry, not a universal estimate of side bias. Swapping two identical
deterministic policies would reproduce the same game. Another 100 repetitions
would supply no new independent evidence. This reference remains separate from
the 300 primary matches and is not included in inferential analysis.

## Termination and failure decision

Historical full-match orchestration used 100 completed rounds (up to 200 player
turns) and stopped provider-failed matches without assigning a tactical winner.
The candidate controller preserves the exact failing command prefix without
forcing EndTurn. We retain those mechanics and the historical 100-round bound.
The benchmark checks both 200 started player turns and 100 completed rounds;
the first reached ends the game as `TURN_LIMIT`, without an invented winner.
Natural victory on the final permitted turn takes precedence.

For this deployable-agent question, the documented adjudication decision is
**PROVIDER_FORFEIT**: exhausted static repair or a recognized provider/transport
failure ends the match, counts as Luna loss and Heuristic win, and retains the
specific provider category. Infrastructure conditions thus have consequential
agent reliability effects; this is deliberately different from a purely tactical
win-rate denominator. Engine winner remains null and the replayed state is not
mutated to manufacture a victory. No next opponent turn is executed. Transport
failures are not eligible for static repair; only existing static-validation
repair semantics apply. Unclassified exceptions are hard integrity stops.

Budget exhaustion is not a provider failure. A per-match request ceiling yields
`REQUEST_LIMIT` (no winner; a censored nonwin). A per-control, batch or global
ceiling stops the study before reserving/sending another request; the partial
match is not adjudicated as a game. Such an incomplete study is descriptive only.
Do not replenish budgets or add replacement slots after looking at results.

Outcome taxonomy: `CORE_DESTRUCTION`, `TEAM_ELIMINATION`, `PROVIDER_FORFEIT`,
`TURN_LIMIT`, `REQUEST_LIMIT`. Interruptions, source drift, replay/accounting
failures, heuristic exceptions and catalog defects are integrity/incomplete
statuses, not outcome categories. No fallback or automatic rematches.

## Frozen resource limits and estimates

| Scope | Strict | Bounded | Stepwise |
| --- | ---: | ---: | ---: |
| Requests per Luna turn, including repair | 2 | 4 | 10 |
| Requests per match | 50 | 80 | 140 |
| Requests per 10-slot batch/control | 300 | 500 | 900 |
| Requests over 100 matches/control | 3,000 | 5,000 | 9,000 |

Combined batch ceiling: **1,700**. Combined study ceiling: **15,000**, not the
17,000 sum of arm allowances or an architectural maximum. Bounded has at most
one replan per Luna turn and at most 100 per match. Stepwise has at most five
decisions/ten requests per turn; the 140 per-match request bound also caps its
total decisions. Static repair is at most one per wave; no retry on timeout.

Evidence for estimating—not guaranteeing—resource use:
`docs/arena-bounded-replan-benchmark-plan.md` records historical Strict 112
requests over 102 attempted turns, and historical Stepwise 89/28 = 3.179 requests
per turn, 156,005 tokens and 136.236 provider seconds. Bounded Stage 1 context is
approximately 1.786 requests/turn. The final 24-turn candidate validation used
37 requests, six successful repairs and one bounded replan, but the selected
short-turn fixtures do not estimate full-game length. The V2/V2 reference takes
nine player turns; historical Qwen full games often took eleven. Consequently
we use **5 / 10 / 20 Luna turns per match**, not a falsely precise forecast.

Assumptions low/central/high: repair rates .05/.10/.20; bounded replan rates
.10/.625/.80; Stepwise decisions 2.5/2.89/4.0 per turn. Requests/turn equal
`1+repair` for Strict, `(1+replan)*(1+repair)` for Bounded, and
`decisions*(1+repair)` for Stepwise. Per-request input tokens are 1,800/2,300/3,500,
output tokens 50/100/180, and provider seconds 1.5/2.5/5. These are conservative
planning assumptions anchored in the recorded telemetry, not measurements of
candidate full matches. No dollars or frozen pricing assumption is supplied.

| Central estimate for 100 games | Requests/game | Requests | Input tokens | Output tokens | Total tokens | Provider hours |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Strict | 11 | 1,100 | 2,530,000 | 110,000 | 2,640,000 | .764 |
| Bounded | 17.875 | 1,787.5 | 4,111,250 | 178,750 | 4,290,000 | 1.241 |
| Stepwise | 31.79 | 3,179 | 7,311,700 | 317,900 | 7,629,600 | 2.208 |
| Combined | — | 6,066.5 | 13,952,950 | 606,650 | 14,559,600 | 4.213 |

Fractional requests are expectations, not executable budgets. Complete low and
high per-arm token/request/time tables are machine-readable in the contract's
`estimates`. Low total: 2,415 requests, 4,467,750 tokens, 1.006 provider hours.
High total: 16,320 requests, 60,057,600 tokens, 22.667 provider hours, exceeding
the study ceiling. This is intentional cost protection, not a promise to finish
in a high-consumption regime. Per-match ceilings accommodate ordinary long games
but may censor pathological ones. Report censoring explicitly. The timeout-only
ceiling is 83.33 provider hours at 15,000 × 20 seconds, not an expected runtime.
Actual elapsed time adds heuristic calculation, controller work, disk writes,
replay and integrity checks. Backend time is measured around each controller
turn, provider latency around requests; browser animation is excluded.

## Metrics and first-class baseline reporting

All matches retain both sides' mechanical metrics and a matchup label. Never
pool “Heuristic win rate” across different controls as a primary statistic.
For each matchup show Luna and heuristic wins/losses/limits, rates, side strata,
player turns, completed/started rounds, terminal mechanism, Core damage
dealt/received/remaining HP, active/downed/removed units, downs inflicted and
received, finishes, revivals, healing, AP executed, and action counts. Provider
forfeits also count as heuristic wins but remain distinct from engine victories.

Heuristic requests, input/output/total tokens, provider latency and backend model
thinking time are exactly zero. Heuristic computation time is separately recorded;
zero inference is not zero computation. Heuristic has no semantic intentional
EndTurn; short plans are `CLEAN_PLAN_COMPLETE`, terminal leftovers `TERMINAL`.

Luna reliability: attempted/completed turns, requests per attempted/completed turn
and match, first-response validity with numerator/denominator, repairs and
success/failure, provider failures, initial execution invalidities, invalid action
index/AP, execution truncations, stop counts, tokens (including cached/reasoning
counts when supplied), provider latency and backend controller time. Primary
first-response validity includes transport failures as unsuccessful responses;
raw per-attempt diagnostics permit a static-output-only secondary view.

Bounded: replan count/rate, AP at replan, recovered AP distribution, replacement
repair, static replacement invalidity, second execution invalidity and its rate
over replans. Stepwise: decisions per turn, explicit EndTurn decisions, requests
per completed turn, current-catalog execution invalidities (hard defects).

Disjoint unused-AP reasons are `INTENTIONAL_END_TURN`, `CLEAN_PLAN_COMPLETE`,
`EXECUTION_TRUNCATION`, `PROVIDER_FAILURE`, `TERMINAL`. Failure-derived unused AP
is truncation plus provider-failure AP; annotate budget-denied decisions separately
using their error category. The frozen controller's generic `PROVIDER_FAILURE`
stop bucket also covers denied budgets; `request_limit_unused_ap` identifies that
portion and is subtracted from failure-derived AP. `provider_failures` excludes
budget denial; `request_limit_decisions` reports it separately.
Recovered AP is not unused AP. Do not call all
leftover AP waste, or treat intentional stopping as tactical necessity.

Objective tactical counts: basic attacks, Core attacks/damage, Snipe, Shield Bash,
Fireball, Finish, Revive, Heal, Move, enemy unit damage, friendly unit damage,
friendly/enemy Fireball damage, empty/friendly-only/mixed/enemy-only Fireballs.
Fireball target classes use ACTIVE affected units immediately before execution,
including caster/friendlies, excluding DOWNED units and Cores, under unchanged
engine geometry. HP loss is capped actual damage. No Fireball tuning. Historical
`units_downed` counts all affected units; the new friend/enemy/received counts
make attribution explicit. Commands, observations and snapshots support further
audits without further inference.

## Prespecified statistical plan

Report exact outcome counts and Wilson 95% intervals for binary win probabilities,
overall and by Luna side, separately for each agent/matchup. Draw/turn/request
limits are nonwins, not half wins. Forfeits count as Luna losses. The primary
denominator is all 100 completed scheduled slots per arm; stopped/incomplete
arms are never silently omitted or filled. Partial batches have descriptive
summaries only. Report tactical-only natural-victory results as an explicitly
selected secondary subset, alongside reliability, never as a replacement headline.

The two planned paired tests use win/nonwin indicators within slots: exact
two-sided McNemar tests, with Holm adjustment across Bounded–Strict and
Stepwise–Bounded. Publish discordant pair counts and the full win/loss/limit
cross-table, forfeit and limit exposure, and side strata. No decisive-only pair
filtering. This estimates a binary win-probability contrast and does not test the
entire multinomial result distribution. Slots pair starting side/opening and
nearby service conditions; they do not supply shared model randomness. Conditional
independent inference samples are assumed. Serial provider outages/load can
violate that assumption; report batch/time context and temper inference rather
than asserting that 100 copies represent scenario diversity.

Effect sizes: paired win-rate differences, requests/turn and tokens/turn ratios,
backend-time/turn ratio, and median within-slot player-turn difference. Use 10,000
matched-slot percentile bootstrap resamples stratified by side (50 Red/50 Blue),
NumPy seed 5914, for effect intervals; preserve whole paired rows in every draw.
This is sampling uncertainty conditional on this opening and collection period.
No bootstrapping individual turns as independent units. Zero denominators and
missing telemetry yield null ratios, not infinities or zero. No significance
tests on heuristic-vs-heuristic repetition, no arbitrary composite score, no
post-hoc sample expansion or stopping on favorable effects.
If every observed paired win difference is identical, the empirical bootstrap
degenerates. The analyzer flags this; a zero-width empirical interval is not
zero population uncertainty or evidence of equivalence. Keep the nondegenerate
Wilson win-rate intervals and discordant counts visible.

## Resume, journals, integrity and artifacts

One exclusive OS file lock prevents concurrent writers. OS locks release on
process exit, including crashes. Run roots bind fake/live mode and contract hash;
they cannot be reused across modes. Reservations are written with exclusive
creation and fsync before each request, and count toward all ceilings even if
delivery is uncertain. Each request has a payload (observation/schema/prompt),
reservation and safe receipt with provider IDs, usage and response hash/semantic
output. No hidden reasoning or rejected free-form prose is stored. Frozen repair
traces contain the sanitized rejected decision and exact diagnostics.

Each completed player turn is a durable checkpoint with an authoritative detached
trace. Resume reconstructs the state from saved commands and continues only if
all reservations belong to committed turns. A reservation or response without a
committed turn **blocks automatic resume**: no resend, no inferred non-billing,
and no automatic discard. Preserve the directory; explicitly review/recover its
evidence under a separate resolution. Exactly-once remote inference cannot be
guaranteed after a crash; this design guarantees refusal to automatically duplicate
an uncertain request. Completed sealed arms are never rerun automatically.

Per-match finalization stores initial state, manifest/control/side binding,
per-turn observations, plans and attempts/repairs/replans, AP reasons and telemetry,
command trace, final state, adjudicated and engine winner, metrics, request-file
hash inventory, exact replay verification and a create-only seal. Incomplete
finalization can finish offline if existing files exactly match reconstruction.
Snapshots and commands remain the source of truth, not presentation events.

After every batch and on resume: verify source/runtime/contract/schedule hashes,
completed schedule prefix and counts, exact command replay (including boundaries
and partial failure prefixes), replay control observations/semantics, deterministic
heuristic plan, request coverage/receipts/hashes, zero fallback, model/profile/
prompt/schema/repair bindings, metrics recomputation and artifact seals. Any
integrity failure stops subsequent matches. Batch gate records bind completed
match seals. A successful gate permits continuation only through the explicitly
authorized `--through-batch` scope.
Each batch replays its 30 matches and rechecks the sealed evidence and request
hashes of all earlier verified batches against their gates. Resume and standalone
verification/analysis replay the entire completed prefix. This avoids quadratic
reexecution of unchanged history while retaining complete replay coverage.

Aggregate `benchmark-manifest.json`, copied `contract.json`, `schedule.json`,
`results.jsonl`, `match-index.json`, `request-ledger.json`, `integrity.json`,
`analysis.json`, `plot-data.csv` and `case-study-report.md` are provided. Aggregate
views are rebuildable; evidence and seals are create-only. Analysis is offline,
rechecking integrity before reading results. File SHA-256 plus canonical payload
hashes protect different layers; retain both.

## Analysis figures and preparation validation

Pinned matplotlib generates PNG and SVG: win rates with Wilson CIs; win rate
against requests/turn, tokens/turn and backend time/turn; match-length distribution;
failure AP; stop-reason AP stack; bounded recovery; static repair; side outcomes;
and an additional truncation/AP-loss versus requests frontier. Heuristic points
at zero inference are labeled by matchup and identified as a different architecture.
Raw per-match CSV and complete machine-readable metrics accompany figures.

The required 300-match deterministic dry run uses a fake transport beneath the
real repair/parser/controller, the complete canonical schedule and actual
Heuristic V2 turns. Network socket/SDK guards prohibit inference. Synthetic token
counts and outcomes are visibly labeled fixtures. Focused tests separately cover
replan/repair, explicit stops, provider forfeits, request ceilings, natural Core and
elimination victories, turn limits, interrupted resume, no duplicate requests,
tamper rejection, source guard, aggregation and batch gates. The full dry run
tests artifacts, scaling, replay and plots; it is not Luna validation evidence.

## Exact commands (PowerShell, workspace root)

Verify the frozen preparation offline:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
```

Reproduce the offline dry run in a **new** output root, then analyze:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study dry-run --output artifacts/arena-case-study-dry-run-reproduction-01 --through-batch 10
.venv/Scripts/python.exe -B -m aig.arena.case_study analyze --output artifacts/arena-case-study-dry-run-reproduction-01
```

Future live command, **not authorized or executed by preparation**:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 1 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B -m aig.arena.case_study verify --output artifacts/arena-case-study-live-v1-01
.venv/Scripts/python.exe -B -m aig.arena.case_study analyze --output artifacts/arena-case-study-live-v1-01
```

After separate authorization for the remaining batches, resume the same root:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 10 --authorize-live arena-case-study-benchmark-v1
```

Reissuing the first command resumes its incomplete authorized prefix; it does not
authorize more than batch 1 or allow duplicate completed arms. There is no live
preflight request. Configure the exact already-frozen profile and timeout; mismatch
stops before inference. Sandbox network permissions may require escalation at
future execution, but that is not supplied or assumed by this preparation.

Recommend authorizing **only the first 30-match batch, up to 1,700 requests**.
Prior tactical validation is sufficient to stop tuning; full-game duration and
total expenditure remain uncertain. Inspect integrity and cost feasibility,
not whether the desired winner emerged. Continue the remaining frozen 270 games
under separate authorization without changing arms, policies or sample selection.
If costs force a new design, preserve v1 and report the incomplete cohort rather
than quietly changing limits. No more pilot expansion or prompt tuning is part
of this plan.
