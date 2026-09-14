# Arena Phase 7A: live Observation V2 tactical-probe results

2026-09-13. Both authorized schedules completed and stopped: **56/56 valid trials,
58 inference requests total, zero repairs, zero fallbacks, zero replay mismatches**.
No full matches, retries, continuations, tuning or source changes occurred.

Observation V2 improves Qwen's observed opening selection and Revive reliability,
but every Qwen probe plan still contains one action. Luna keeps perfect first-action
legality and improves several objectives, while execution truncations double from
4 to 8 and mean executed AP falls. **The results support better explicit action
selection in some cases, not a broad full-turn tactical improvement.**

## Evidence and the controlled comparison

All comparisons here hold `arena-turn-prompt-v2` fixed and vary only
`arena-observation-v1` versus `arena-observation-v2`. “V1/V2” below refers to
**observation**, not prompt. Models are compared against their own control.

- [Qwen V2 run](../.local/arena-phase7a-qwen-observation-v2-probes-20260913-01/summary.json)
- [Luna V2 run](../.local/arena-phase7a-luna-observation-v2-probes-20260913-01/summary.json)
- [Qwen control](../.local/arena-phase6b-qwen-v2-probes-20260913-01/summary.json)
- [Luna control](../.local/arena-phase6b-luna-v2-probes-20260913-01/summary.json)
- [Complete comparison, per-plan memberships, mechanical effects and post-plan states](../.local/arena-phase7a-live-20260913-01/comparison.json)
- [Reproducible offline analyzer](../.local/arena-phase7a-live-20260913-01/analyze.py)
- [Per-plan audit](../.local/arena-phase7a-live-20260913-01/plan-audit.md)
- [Every unique plan hash, frequency, modal plan and resulting state hash](../.local/arena-phase7a-live-20260913-01/plan-variation.md)

Qwen's control stopped at the first Revive trial: eight valid plans, one failed
repair, 19 unstarted intended trials. Its only fully matched completed fixtures
are Finish/Core and Fireball (four trials each). Do not interpret 8/9 versus 28/28
as a balanced aggregate estimate across identical coverage. All Luna fixtures are
matched four-for-four. Fixed repeated samples are not independent playing-strength
measurements; no statistical significance or broad model capability claim is made.

**Intentional instruction limitation:** Prompt V2 was frozen byte-for-byte. Its
per-unit-list wording does not exactly describe V2's flat catalog, so V2 operates
under slightly stale instructions. This is a limitation of the controlled A/B,
not a runtime bug. All results remain included; the caveat does not discard them.

## Request accounting and static reliability

Each new command used one unrepaired preflight plus 28 initial trial requests:
**29/57 allowed requests per model, 58/114 combined**. There were no repair calls
and no unused-budget retries. Both output roots are exactly those authorized.
The built-in strict preflight is separate from trial statistics.

| Metric | Qwen Obs V1 | Qwen Obs V2 | Luna Obs V1 | Luna Obs V2 |
| --- | --- | --- | --- | --- |
| Intended trials | 28 | 28 | 28 | 28 |
| Started trials | 9 | 28 | 28 | 28 |
| Unstarted trials | 19 | 0 | 0 | 0 |
| Valid / executed trials | 8 | 28 | 28 | 28 |
| Failed trials | 1 | 0 | 0 | 0 |
| Requests including preflight | 11 | 29 | 29 | 29 |
| First-response valid | 8 | 28 | 28 | 28 |
| First-response invalid | 1 | 0 | 0 | 0 |
| Repair attempts | 1 | 0 | 0 | 0 |
| Successful repairs | 0 | 0 | 0 | 0 |
| Failed repairs | 1 | 0 | 0 | 0 |
| Provider-boundary failures | 1 | 0 | 0 | 0 |
| Fallbacks | 0 | 0 | 0 | 0 |
| Exact replays, including failed prefixes | 9 | 28 | 28 | 28 |

First-response validity among started trials is Qwen **8/9 (88.89%) -> 28/28
(100%)**, Luna **28/28 -> 28/28 (100%)**. The control's Qwen failure was
`invalid_reference` on initial response and repair, surfaced as `repair_failed`.
It was not a transport failure. Rejected raw output was not retained, so its exact
actor/target cannot be reconstructed. All new accepted calls have requested
provider equal to actual provider and `fallback=false`.

All 56 new trials replayed exactly. The audit additionally reverified the 37
control trials/prefixes: **93 exact replays total**, including the one failed
Qwen control prefix. This covers command trace, final state/hash, AP accounting,
winner and terminal state. No heuristic plan was used as ground truth.

## Primary metric: starting legality and prefix

First-action denominators contain nonempty accepted plans, not failed responses
or unstarted trials. There are no empty accepted plans in either population.

| Metric | Qwen Obs V1 | Qwen Obs V2 | Luna Obs V1 | Luna Obs V2 |
| --- | --- | --- | --- | --- |
| First-action starting-legal | 8/8 (100%) | 28/28 (100%) | 28/28 (100%) | 28/28 (100%) |
| Mean starting-legal prefix | 1 | 1 | 3.036 | 3.25 |
| Median starting-legal prefix | 1 | 1 | 3 | 3 |
| Prefix min–max | 1–1 | 1–1 | 2–5 | 1–5 |
| Mean planned action count | 1 | 1 | 3.429 | 3.429 |
| Full-plan starting-legal | 8/8 (100%) | 28/28 (100%) | 19/28 (67.857%) | 25/28 (89.286%) |
| Execution-invalid truncations | 0 | 0 | 4 | 8 |
| Terminal suffixes (not errors) | 0 | 0 | 7 | 7 |


The matched eight Qwen probe plans remain **8/8 legal**, prefix 1, one planned
action and one executed AP. There is no rate improvement measurable on those
already-perfect fixtures. V2 extends 100% first-action legality across all seven
probes, including previously unstarted Snipe; this is additional coverage.

The **separate opening preflight** changes from initially illegal
`blue-mage attack red-cleric` to starting-legal
`blue-cleric move {x:3,y:4}`. This is one observed opening correction, not a repeated
full-match result. Luna returns the same opening plan in both cells: Ranger Move
to (4,0), then Snipe Red Ranger. Its first action is starting-legal; its second is
absent initially and can be enabled by movement.

Luna's full-plan starting-membership rate rises **67.86% -> 89.29%**, but this is
not dynamic validity. Matching more of the original catalog can encourage reuse
of actions whose targets have subsequently moved or been downed. Prefix measures
are factual adherence measures; later-state actions can be valid without initial
membership, and initial members can become invalid.

## AP utilization and remaining actions

AP statistics below include accepted plans, with terminal leftovers preserved.
Full-five and <=2 rates are given separately for planned and executed AP.

| Metric | Qwen Obs V1 | Qwen Obs V2 | Luna Obs V1 | Luna Obs V2 |
| --- | --- | --- | --- | --- |
| Planned AP mean | 1 | 1.286 | 3.893 | 4.036 |
| Planned AP median | 1 | 1 | 4 | 4 |
| Planned AP min–max | 1–1 | 1–2 | 2–5 | 2–5 |
| Executed AP mean | 1 | 1.286 | 3.107 | 2.714 |
| Executed AP median | 1 | 1 | 4 | 3 |
| Executed AP min–max | 1–1 | 1–2 | 1–5 | 1–5 |
| Unused AP mean | 4 | 3.714 | 1.893 | 2.286 |
| Unused AP median | 4 | 4 | 1 | 2 |
| Unused AP min–max | 4–4 | 3–4 | 0–4 | 0–4 |
| Planned full-5-AP | 0/8 (0%) | 0/28 (0%) | 7/28 (25%) | 11/28 (39.286%) |
| Executed full-5-AP | 0/8 (0%) | 0/28 (0%) | 5/28 (17.857%) | 4/28 (14.286%) |
| Planned <=2 AP | 8/8 (100%) | 28/28 (100%) | 2/28 (7.143%) | 2/28 (7.143%) |
| Executed <=2 AP | 8/8 (100%) | 28/28 (100%) | 10/28 (35.714%) | 11/28 (39.286%) |
| Executed zero-action | 0/8 (0%) | 0/28 (0%) | 0/28 (0%) | 0/28 (0%) |


Qwen's overall mean rises **1.00 -> 1.286 AP**, entirely through newly completed
two-AP Revive/Snipe fixtures. Its matched Finish/Core and Fireball means remain
1.00; all 28 V2 plans contain exactly one action. This is not improved multi-action
continuation. Luna plans slightly more AP (**3.893 -> 4.036**) but executes less
(**3.107 -> 2.714**).

The engine was replayed only through each planned action, stopping **before
automatic EndTurn** resets AP or changes player. For error-free plans with AP left:

| Metric | Qwen Obs V1 | Qwen Obs V2 | Luna Obs V1 | Luna Obs V2 |
| --- | --- | --- | --- | --- |
| Short error-free plans | 8 | 28 | 19 | 16 |
| Battle already terminal | 0 | 4 | 9 | 9 |
| Legal actions remain | 8 | 24 | 10 | 7 |
| No legal actions remain, nonterminal | 0 | 0 | 0 | 0 |
| Non-move legal actions remain | 8 | 24 | 10 | 7 |


Thus **24/28 Qwen V2 turns stop with legal non-move actions still available**;
four short turns correctly stop at Team Elimination victory. Its Revive plans
leave three AP and newly active Mage actions available. The remaining-action
catalogs/counts and post-plan snapshots are in the comparison JSON. Legal
non-move availability is not a claim that every such choice is useful or optimal.
Truncated plans are excluded from this voluntary-short-stop table: an executor
rejection is not an intentional early stop. No model was queried again.

## Dynamic sequencing audit

Qwen has zero execution-invalid truncations in both retained populations. Luna
has **4/28 (14.29%) -> 8/28 (28.57%)**. Every V2 rejection is at index 1 or 2;
none is the first action. Indices are zero-based.

| Obs | Probe | Trial | Index | Rejected action | Engine reason | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| v1 | fireball_friendly_fire | run-002 | 2 | actor attack enemy2 | invalid target ACTIVE/DOWNED status | Changed legality |
| v1 | shield_bash_position | run-003 | 2 | actor finish enemy | invalid target ACTIVE/DOWNED status | Initially illegal; never enabled |
| v1 | team_elimination | run-001 | 1 | actor attack enemy | target outside action range | Changed legality |
| v1 | team_elimination | run-002 | 1 | actor attack enemy | target outside action range | Changed legality |
| v2 | fireball_friendly_fire | run-002 | 2 | actor attack enemy2 | invalid target ACTIVE/DOWNED status | Changed legality |
| v2 | fireball_friendly_fire | run-003 | 2 | actor attack enemy2 | invalid target ACTIVE/DOWNED status | Changed legality |
| v2 | fireball_friendly_fire | run-004 | 2 | actor attack enemy2 | invalid target ACTIVE/DOWNED status | Changed legality |
| v2 | revive_decision | run-001 | 2 | actor move {'x': 3, 'y': 3} | destination is occupied, blocked, unchanged, or beyond move range | Initially illegal; never enabled |
| v2 | shield_bash_position | run-001 | 1 | actor attack enemy | target outside action range | Changed legality |
| v2 | shield_bash_position | run-002 | 1 | actor attack enemy | target outside action range | Changed legality |
| v2 | shield_bash_position | run-003 | 1 | actor attack enemy | target outside action range | Changed legality |
| v2 | snipe_vs_basic | run-002 | 1 | actor snipe enemy | invalid target ACTIVE/DOWNED status | Changed legality |


In V2, **seven** rejected actions were initially legal: three attacks after
Fireball plus an ally attack had downed `enemy2`; three attacks after Shield Bash
pushed `enemy` outside range; one second Snipe after the first downed `enemy`.
The eighth action, Cleric Move to (3,3) in Revive run-001, was illegal initially
and after every actual prefix: that tile remained occupied by the active enemy.
Revive and the revived Mage's one Attack did not remove it.

The control split was three changed-legality rejections and one initially illegal
Finish. That Finish required a DOWNED target, but two attacks left the Knight at
6 HP. These two initially illegal cases lacked an enabling state change in their
actual prefixes. Model intent is unrecorded: it is not possible to prove what
earlier state change the model expected. The audit records legality/reason after
every actual prefix instead of inventing that intention. All valid earlier actions
stay committed, and no execution-time repair request occurs.

## All seven mechanical probe comparisons

Numbers below are totals across each fixture's four intended repetitions, unless
marked mean AP or unstarted. Preserve objectives separately; ability use is not a
tactical score. A trial can be statically valid and still truncate dynamically.

### Qwen

| Probe | Observation V1 control | Observation V2 |
| --- | --- | --- |
| Finish/Core | 4 Core Attacks, 24 Core damage; mean AP 1; no Finish/removal or win | Identical mechanics, AP and final states |
| Fireball friendly fire | Mage `actor` Attacks `enemy` once each; 24 enemy damage; no Fireball/friendly damage/down; mean AP 1 | Knight `ally` Attacks `enemy` once each; same damage/AP and final states |
| Revive | First trial invalid initial+repair; no accepted plan, 3 unstarted; exact rejected actor unknown | 4 valid Revives: Cleric `actor` -> `ally`, restored ACTIVE/5 HP each; 4/4 revived; no follow-up action; mean AP 2 |
| Shield Bash | 0 started / 4 intended | Basic Attack each, no Bash/push or premium displacement; 24 damage, zero downs; mean AP 1 |
| Snipe | 0 started / 4 intended | Ranger `actor` Snipes `enemy` each; 4 Snipes, zero basic Attacks; 32 damage, 4 downs; mean AP 2 |
| Winning Core | 0 recorded wins / 4 intended; 0 started | 0/4 wins; attacks `enemy`, 20 unit damage, zero Core damage; mean AP 1 |
| Team Elimination | 0 recorded wins / 4 intended; 0 started | 4/4 immediate wins via basic Attack; 24 damage, 4 downs; mean AP 1; no Finish |

Qwen's matched fixture effects do not improve. Revive changes from a failed first
control attempt to four successful V2 trials; this is the clearest reliability/
objective gain. Newly reached fixtures have no balanced Prompt-V2/Observation-V1
control. Unstarted control trials are not observed tactical failures.

### Luna

| Probe | Observation V1 control | Observation V2 |
| --- | --- | --- |
| Finish/Core | 14 Core Attacks, 2 Finishes/removals, 1 Move; 84 Core damage; mean AP 4.25; 2/4 wins | 20 Core Attacks, no Finish/removal/Move; 120 Core damage; mean AP 5; 4/4 wins |
| Revive | 4 valid plans; 3 Cleric Revives of `ally`, 3/4 ACTIVE afterward; follow-up attacks and one revived-Mage Fireball; mean AP 4.5 | 4 valid plans, 4 correct Cleric `actor` Revives of `ally`, each ACTIVE/5 HP; 4/4 revived; mean AP 3; one subsequent Move truncates |
| Fireball friendly fire | No Fireball; 12 Attacks, 2 Finishes; 60 enemy/0 friendly damage; 4 downs; mean AP 3.5 | 4 Fireballs at (4,2), 5 Attacks, zero Finishes; 58 enemy/8 friendly damage; 4 downs; mean AP 3.25; 3 truncations |
| Shield Bash | No Bash; 11 Attacks, 66 damage, 3 downs/wins; mean AP 2.75; 1 invalid Finish | 3 Bashes/pushes, 3 Attacks, 30 damage, 1 down/win; mean AP 1.5; 3 out-of-range follow-up Attacks |
| Snipe | 8 Snipes, zero basic Attacks; 64 damage, 4 downs; mean AP 4 | 7 Snipes, zero basic Attacks; 56 damage, 4 downs; mean AP 3.5; one repeated-target Snipe truncates |
| Winning Core | 4/4 immediate wins, 36 Core damage; mean AP 1.75 | 4/4 immediate wins, 27 Core damage; mean AP 1.75; three Core destructions and one team-elimination win |
| Team Elimination | 2/4 wins; 2 Bashes then invalid out-of-range Attacks; 20 damage; mean AP 1 | 4/4 wins; 4 basic Attacks; 24 damage, 4 downs; mean AP 1; terminal Finish/other suffixes do not execute |

Each new Fireball hits enemies `enemy` and `enemy2`, plus friendly Knight `ally`
on WARD. Across the four casts: **8 enemy hits, 4 friendly hits, 32 enemy damage,
8 friendly damage from Fireball itself**. Subsequent attacks bring total enemy
damage to 58. There are no Fireballs in the Qwen cell. Luna's control had eight
friendly damage in the *Revive* fixture instead; total friendly damage across all
seven probes stays eight, while its location and sequence change.

Each new Shield Bash pushes `enemy` from (3,2) POWER to (4,2), with no bonus.
That is three successful premium-tile displacements, each followed by an Attack
that is now out of range. The fourth trial uses three basic Attacks and wins.
The effects are correctly executed; the provider's subsequent plan is wrong.

All Luna V2 Revives use the correct Cleric and target `ally`. Runs 001/003 then
execute an Attack by the revived Mage; runs 002/004 execute a Cleric Attack.
Run 001 next tries the occupied Move and discards its final Cleric Attack.
Qwen never adds an action after its Revive. Exact ordered plans, actor classes,
target positions, pushes, hits and per-action effects are retained in the JSON.

## Action distribution and plan variation

Executed action totals (planned distributions, including rejected and terminal
suffix actions, are separately retained in the JSON):

| Metric | Qwen Obs V1 | Qwen Obs V2 | Luna Obs V1 | Luna Obs V2 |
| --- | --- | --- | --- | --- |
| attack | 8 | 20 | 54 | 41 |
| finish | 0 | 0 | 4 | 0 |
| fireball | 0 | 0 | 1 | 4 |
| move | 0 | 0 | 1 | 0 |
| revive | 0 | 4 | 3 | 4 |
| shield_bash | 0 | 0 | 2 | 3 |
| snipe | 0 | 4 | 9 | 8 |


Variation below counts distinct complete accepted-plan hashes / distinct final
state hashes among those accepted plans. Failed/unstarted control rows remain
explicit in the detailed appendix. A difference in plans is not itself failure.

| Probe | Qwen V1 | Qwen V2 | Luna V1 | Luna V2 |
| --- | --- | --- | --- | --- |
| finish_or_core | 1 / 1 | 1 / 1 | 3 / 3 | 1 / 1 |
| fireball_friendly_fire | 1 / 1 | 1 / 1 | 3 / 3 | 2 / 2 |
| revive_decision | 0 / 0 | 1 / 1 | 3 / 3 | 3 / 2 |
| shield_bash_position | 0 / 0 | 1 / 1 | 3 / 2 | 3 / 2 |
| snipe_vs_basic | 0 / 0 | 1 / 1 | 2 / 1 | 2 / 2 |
| team_elimination | 0 / 0 | 1 / 1 | 3 / 2 | 3 / 1 |
| winning_core_line | 0 / 0 | 1 / 1 | 3 / 2 | 2 / 2 |


Qwen has one unique V2 plan per fixture, repeated four times. Luna's V2 modal
frequencies are Finish/Core 4/4, Fireball 3/4, Revive 2/4, Shield Bash 2/4,
Snipe 3/4, Team Elimination 2/4, Winning Core 3/4. Distinct Luna V2 plans yield
identical final states in Revive, Shield Bash and Team Elimination; some suffix
differences never execute. The [variation appendix](../.local/arena-phase7a-live-20260913-01/plan-variation.md)
provides every exact hash, count, modal action sequence and unique state hash for
both models and both observations, rather than just the counts above.

## Qwen tokens, context and local lifecycle

The opening input count is **3,317 -> 2,741**, a **576-token (17.37%) reduction**.
Within 4,096 context, reserving 256 output tokens leaves **523 -> 1,099 tokens**.
That is 576 more tokens of measured reserved headroom, substantially better than
the offline 3,005–3,083 input / 757–835 headroom estimate. Offline byte ratios were
only estimates; actual tokenization is the stronger evidence.

The largest observed V2 occupancy, including preflight and actual output, is
**2,778/4,096 = 67.82%** (2,741 input + 37 output), leaving 1,318 tokens after
actual output. Minimum headroom after reserving the full output allowance is
**1,099**. The control opening occupied 3,351/4,096 = 81.81%, with 745 tokens
after actual output. Neither cell records a context-limit failure.

Preflight latency is reported separately: control **12.760 s**, V2 **12.222 s**
per request. V2 preflight server total is 12.168 s, prompt evaluation 1.631 s,
generation 1.383 s. Remaining overhead may include model loading, but a separate
load-duration counter is not persisted, so cold loading is not proven. Preflight
is excluded from the following 28 V2 trial-request distributions; p95 is nearest
rank and shown only for at least 20 samples.

| Measurement | Min | Max | Mean | Median | p95 |
| --- | --- | --- | --- | --- | --- |
| Input tokens | 1539 | 2574 | 1783.571 | 1626 | 2574 |
| Output tokens | 30 | 31 | 30.571 | 31 | 31 |
| Input + output | 1569 | 2605 | 1814.143 | 1657 | 2605 |
| Context occupancy (%) | 38.306 | 63.599 | 44.291 | 40.454 | 63.599 |
| Headroom after reserved 256 | 1266 | 2301 | 2056.429 | 2214 | 2301 |
| Request seconds | 1.404 | 2.879 | 1.731 | 1.472 | 2.78 |
| Prompt evaluation seconds | 0.137 | 1.112 | 0.317 | 0.159 | 0.927 |
| Generation seconds | 1.144 | 1.294 | 1.209 | 1.207 | 1.286 |
| Server total seconds | 1.397 | 2.877 | 1.724 | 1.469 | 2.772 |


Per-fixture V2 Qwen input counts: Finish/Core 1,588; Fireball 2,574; Revive 1,626;
Shield Bash 1,539; Snipe 1,695; Team Elimination 1,578; Winning Core 1,885.
Matched control counts are Finish/Core 2,238 and Fireball 2,760. Revive control's
initial/repair counts are 2,253/2,284. Although Fireball's V2 observation grew
630 bytes, its measured input shrank 186 tokens: byte size alone did not predict
tokenization. Do not compare Qwen's different-coverage grand means as a paired gain.

All V2 probe outputs use 30–31 tokens, preflight 37, far below the unchanged cap
256. No output reaches that cap. The trace does not retain provider finish/done
reasons, so there is no direct output-truncation flag; cap proximity is only a
proxy. No profile, keep-alive, context size, temperature, seed or output limit was
changed. Warm latency differences are descriptive and may include device/cache
conditions; they are not a causal speed benchmark.

## Luna tokens, cache and latency

The following distributions cover all 28 V2 trial requests, excluding preflight.

| Measurement | Min | Max | Mean | Median | p95 |
| --- | --- | --- | --- | --- | --- |
| Input tokens | 1860 | 2893 | 2101.286 | 1940 | 2893 |
| Cached input | 0 | 2890 | 1573.714 | 1899 | 2890 |
| Uncached input | 3 | 2893 | 527.571 | 3 | 2204 |
| Output tokens | 52 | 101 | 76.214 | 75.5 | 99 |
| Reasoning tokens | 0 | 0 | 0 | 0 | 0 |
| Total tokens | 1926 | 2969 | 2177.5 | 2001 | 2969 |
| Request seconds | 0.961 | 2.382 | 1.351 | 1.28 | 1.815 |


Luna trial totals: input **73,776 -> 58,836**; cached input **55,269 -> 44,064**;
uncached input **18,507 -> 14,772**; output **2,098 -> 2,134**; reasoning **0 -> 0**;
total tokens **75,874 -> 60,970**. Weighted cache ratio stays effectively unchanged:
**74.915% -> 74.893%**. Mean input falls **2,634.857 -> 2,101.286** tokens (20.25%).
Trial request latency mean/median/p95 changes **1.524/1.440/2.191 s ->
1.351/1.280/1.815 s**. Full control/V2 min/max/means/medians/p95 and totals are
retained in the JSON. Cache state, service conditions and plan variation limit
causal latency interpretation.

Luna preflight is separate: control **2.947 s**, 3,616 input + 66 output; V2
**3.215 s**, 3,058 input + 66 output. Both have zero cached input/reasoning tokens.
No cost is estimated: Arena's existing benchmark has no frozen pricing/cost
estimator, and no new pricing assumption was introduced.

## Frozen provenance, preservation and exact execution

Both live runs record:

- `arena-turn-prompt-v2`, hash `5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29`
- `arena-observation-v2`, with per-observation hashes; base recipe observation V1
- `arena-turn-plan-schema-v1`, `arena-benchmark-v1`, `arena-probes-v1`
- `arena-rules-v2`, `arena-scenario-v1`, frozen `qwen-config-v1` / `luna-config-v1`
- Git SHA `794fca9f46cbfe93d9406200c824033a59b7e812`, dirty checkout true
- Backend source manifest hash `d28b17489be03a5f3e3f3a86e1e18a76aed557f04eb25ad663fec689cacb0516`

The runner captures source provenance before its preflight; the pre-live inventory
additionally freezes existing file bytes. All **84 backend source files** match
both run manifests and remain unchanged. All **4,655 inventoried pre-existing
files**, including **4,490 historical evidence/support files**, are byte-identical.
The source manifest differs from the control because Phase 7A implemented the
observation contract, as expected; no source changed between these two live runs.
No gameplay, validation, executor, provider, heuristic, repair, prompt or model
configuration change was made during collection or analysis. The runner wrote new
trial artifacts during collection; offline analysis/report files were added after
both schedules stopped. Previous evidence and postmortems were not rewritten.

Before Qwen inference, a read-only `/api/version` check failed in the sandbox with
WinError 10013, then succeeded outside it (HTTP 200, Ollama 0.34.0). These two
checks were not inference requests. Both authorized commands used the necessary
execution permissions. There was no repeated failed inference attempt.

Executed exactly once each, with console logs in the new analysis directory:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider ollama --prompt-version arena-turn-prompt-v2 --observation-version arena-observation-v2 --probe all --probe-trials 4 --strict-provider --output .local/arena-phase7a-qwen-observation-v2-probes-20260913-01
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider openai --prompt-version arena-turn-prompt-v2 --observation-version arena-observation-v2 --probe all --probe-trials 4 --strict-provider --output .local/arena-phase7a-luna-observation-v2-probes-20260913-01
```

No runtime tests/build rerun was needed because runtime source did not change;
the verification here is exact replay, independent action-by-action reconstruction,
metric/membership recomputation and source/evidence hashes. Rejected-output capture
remains unchanged, and no hidden reasoning is collected.

## Answers and next decision

1. **Qwen first-action legality:** the opening preflight improves from illegal to
   legal. Matched probes stay 8/8; V2 achieves 28/28 across broader coverage.
   This is promising transfer of explicit selection, not a measured increase on
   the matched probe rate or proof over full matches.
2. **Qwen static validity:** observed reliability improves: the failing Revive
   fixture now passes four times and the complete schedule needs no repair.
   Preserve the control's incomplete-coverage limitation.
3. **Qwen AP execution:** no matched-fixture improvement. The overall increase
   comes from new two-AP special actions, while one-action turns persist and
   24/28 stop with non-move legal choices available.
4. **Luna starting legality:** first actions remain perfect; full-plan starting
   membership improves. These gains do not establish better causal sequencing.
5. **Luna truncation:** no improvement; it doubles to eight, seven caused by
   changes from previously legal states. Full-turn sequencing remains a clear defect.
6. **Objectives:** Qwen Revive reliability improves; Luna improves Revive 3/4 ->
   4/4, Team Elimination 2/4 -> 4/4 and Finish/Core wins 2/4 -> 4/4. Luna Winning
   Core stays 4/4; Qwen V2 Winning Core is 0/4 with no started control comparison.
7. **Regressions:** Luna has more truncations, lower executed AP, weaker Shield
   Bash/Snipe results and new friendly damage in the Fireball fixture. These are
   observed cell differences, not proof that flat JSON alone caused each one.
8. **Qwen context headroom:** yes, materially improved on the same opening,
   from 523 to 1,099 tokens after reserving output. This did not solve low AP use.
9. **Full-match testing:** the evidence does not support promotion or a broad
   claim of better full-match tactics. A separately scoped Qwen V2 full-match
   feasibility check could now test whether the opening correction transfers,
   but the preregistered useful-AP improvement gate is not met on matched fixtures.
   I would not automatically launch general full-match comparison from these results.
10. **Dominant remaining problem:** for Luna, actual-prefix analysis directly
    identifies sequential planning. Qwen shows failure to continue beyond one
    action; its ability to sequence remains largely untested by those plans.
    These results make control/continuation experiments more informative than
    further JSON reformatting, without implementing or claiming that stepwise
    control or replanning will necessarily fix them.

**Stop:** both authorized tactical-probe schedules and the offline report are
complete. No full matches, Qwen-vs-Luna, prompt/observation V3, action IDs, stepwise
control, bounded replanning, larger models or tuning were run or implemented.
