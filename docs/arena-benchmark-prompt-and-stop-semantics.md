# Arena benchmark candidate: prompts and intentional stop

Implementation and offline preparation only. No live OpenAI or Ollama inference,
no Luna run, no default changes, and no 300-match benchmark. This candidate is
explicitly constructed through new modules; it is not registered in browser,
production provider factories, or historical benchmark runners.

**Evidence and design.** The supplied matched 122-decision evidence is:

| Measure | V1 | V4 | V5 |
|---|---:|---:|---:|
| First-response valid | 104/122 | not separately supplied | 112/122 |
| AP-overbudget / static repairs | 18 | 7 | 10 |
| Later-action failures | 15 | 15 | 13 |
| Stale-DOWNED plans | 15 | reduced; other failures appeared | 10 |
| Mean gameplay actions/accepted plan | 1.500 | 1.471 | 1.496 |
| One-action frequency | 51.64% | 57.02% | 51.24% |
| Mean executed AP | 1.795 | 1.744 | 1.802 |
| Multi-action objectives | 3/6 | 1/6 | 3/6 |
| Witnessed position objectives | 2/2 | 0/2 | 1/2 |

V1 and V5 both achieved 12/12 basic damage/lethal, 6/6 Core and 6/6 WARD.
V5 mean planned AP was 1.959 versus V1's 1.951; V5 DOWNED/Finish was 6/9.
V5 used fewer total tokens despite a longer prompt. These are historical
observations, not candidate results. V4's broad sequencing reminders reduced AP
errors without improving total later-action reliability and coincided with less
multi-action/position success. V5 isolates the useful AP-budget component while
largely preserving V1's plan shape. The evidence supports the statement that the
model was unreliable at maintaining exact multi-action board state across several
state-changing actions; it does not establish an impossibility theorem.

**Current EndTurn contracts discovered.** `ArenaEndTurn(actor_id)` already exists
in `commands.py`, costs zero AP, is valid for the active player in any nonterminal
state (including zero AP), and advances the player/turn through normal game rules.
Its `arena_end_turn` command serialization and replay already exist. EndTurn is
not present in historical `ArenaPlannedAction`, `ACTION_TYPES`, or the V1 model
schema; model legal-action catalogs omit it. `ArenaTurnPlan` accepts zero to five
gameplay actions with total cost at most five. Full-turn execution automatically
ends after a successful plan or invalid-action truncation. Bounded V1 refreshes
only after execution invalidity; clean short/empty plans already do not replan.
Stepwise V1 explicitly describes `actions=[]` as intentional stop and records it
as such. Constrained structured inherits empty-array stopping. The action-ID
experiment instead uses `{"action_id":null}` to stop, and its prompt already owns
`arena-step-prompt-v2`; the new semantic-action step prompt therefore uses V3.
Action IDs select catalog entries rather than a shared semantic object.

**New representation and version boundary.** The opt-in `CandidatePlan` uses
`arena-turn-plan-schema-v2`: the existing gameplay variants plus exactly
`{"type":"end_turn"}`. There is no reason field, unit ID, extra boolean, tactical
narrative, or new game command. The schema permits six array entries so five
one-AP gameplay actions can be followed by zero-AP EndTurn. Application static
validation enforces at most five gameplay actions, AP budget, and at most one
EndTurn in last position. The wire schema bounds shape/cardinality; ordering and
summed cost are enforced locally, as summed cost was in V1. A step has at most one
entry. Empty arrays remain valid but now mean clean completion, not explicit intent.
OpenAI and Ollama adapters share these logical variants; OpenAI uses the existing
typed-enum/anyOf wire transformation. Historical V1 schemas remain unchanged.

Terminal state takes precedence. A plan may syntactically contain a future
EndTurn after an attack that turns out to win, because static validation does not
simulate outcomes. The executor suppresses every suffix command after victory,
including EndTurn. It records no reached explicit stop in that case. EndTurn
after a failed action likewise does not count as intentional. A reached EndTurn
ends normally through `ArenaSimulation.execute`, once only, without a follow-up
provider request. AP is sampled before EndTurn resets the opponent's AP.

**Prompt synthesis and wording audit.** `arena-policy-core-v1` is composed with
`arena-turn-prompt-v6` or `arena-step-prompt-v3`. Strict and bounded use the exact
same full-turn prompt. The shared core contains the objective, authoritative
observation/catalog use, legal identifiers, current AP as the entire budget,
running cost accounting, generic game rules, useful action selection, and explicit
stopping without AP-filling actions. Several useful actions are expressly allowed.

| Wording category | Decision |
|---|---|
| A: game/output contract | Retain victory, identifiers, costs/ranges from observation, movement/LOS/status/target rules, output-only contract. |
| B: useful guidance | Retain V5's complete remaining-AP budget and running total. Support multiple worthwhile actions and explicit stops. |
| C: historical/redundant | Remove duplicate fixed damage/restoration numerals already supplied by observations; remove automatic-only stop wording. |
| D: tactical policy | Add no target priorities, Core/bonus strategies, Fireball preferences, class combos, or lethal policy. |
| E: broad state simulation | Exclude V4's transition checklist, DOWNED propagation reminders, positional/LOS simulation instructions, and Shield Bash sequencing advice. |

The ordinary Shield Bash push rule is retained as a game fact, not a sequencing
reminder. The full-turn wrapper requests zero to five gameplay actions, optionally
followed by EndTurn. The step wrapper requests one next action or EndTurn and
explains the refreshed observation after a successful step. Both use the same
common core. No damage arithmetic or probability assumptions are taught; if game
damage later becomes variable, its new rule representation must be versioned in
the observation. This prompt does not assume exact fixed damage values.

| Prompt | Characters / UTF-8 bytes | SHA-256 |
|---|---:|---|
| V1 | 1730 / 1730 | `5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7` |
| V4 | 3609 / 3609 | `ede7f2defc81aa099fd8d1e2e4acbdd948389790101afc3d4b75c05342b16b35` |
| V5 | 2005 / 2005 | `6b86be79d29a9287768ef447f8c3d817a583f959e62430e9cdf4a059bf111b81` |
| V6 candidate | 2046 / 2046 | `39c88e2287589b943d9a9b3e9f9e9a4feaa19036a18e5f922eb7e362d27ae5c6` |
| Step V1 | 850 / 850 | `791f842d479527929f504c505254cd2d21dee668b2550f31cad5e7458b572d5f` |
| Step V3 candidate | 2052 / 2052 | `95845aca75bbdb17a0cc36f91f8c13cb2288699c886fa43c87a4eb85dee6d1d5` |

These are measured string sizes, not estimated token counts. Candidate stepwise
gets more game guidance than historical Step V1; historical results therefore
must not be presented as a matched candidate arm.

**Observation and schema comparability.** Historical full-turn defaults to
`arena-observation-v1` with actor-grouped legal options and per-unit metadata.
Historical stepwise requires `arena-observation-v2`, which compacts unit-type
metadata and board tiles and exposes complete semantic actions. `observation_facts`
losslessly expands it back to V1 game facts. V3 adds action IDs; it is not selected.
The candidate's separate `arena-observation-v4` binding wraps V2, adds the legal
zero-AP stop action and cost map, and labels the catalog `current_observation`
instead of the potentially misleading `turn_start`. The same bytes are sent at
the same starting state in every arm. No hidden state or tactical scores are added.
Tests check equality across arms and round-trip equality of V1/V2 facts.

All three arms use the same semantic gameplay variants, stop vocabulary, static
references, AP limits, and exact first-action membership check against the current
catalog. This first-action check is new for candidate full-turn and symmetric
across candidate controls. Full-turn later actions remain subject to execution
validation; future legal actions need not be in the starting catalog. Stepwise
checks every decision as a first action because each receives new state. We do
not use a dynamically constrained wire schema in one arm or IDs in another.

**Control abstraction.** A shared `CandidateController` is explicitly selected as:

| Mode | Candidate control ID | Refresh schedule |
|---|---|---|
| strict | `arena-control-full-turn-v2` | Observe once; commit plan until stop/completion/invalidity/victory. |
| bounded | `arena-control-full-turn-bounded-replan-v2` | Same; refresh once only on execution invalidity with remaining AP. |
| stepwise | `arena-control-stepwise-v2` | Refresh after every successful gameplay action if AP remains. |

No arm uses heuristic fallback. Each decision permits the existing single static
repair with the same observation. Provider failure preserves the committed prefix
without automatic EndTurn, uniformly across candidate arms. A future match runner
must mark this as a failed trial; it must not silently call another turn on that
prefix. Recovery has a four-request ceiling (two decisions, each with one repair),
strict has two, stepwise at most ten for a five-AP turn. Existing provider hooks are
composed before sends and restored after the turn, including failures.

Unavoidable control differences are output cardinality, wrapper explanation,
number/timing of observations and calls, and therefore occasions for repair.
Full-turn can append EndTurn after spending all AP; stepwise never issues an extra
zero-AP decision. That difference affects zero-leftover labels, not intentional
unused AP. The architecture is sufficiently separated for matched candidate
trials; this is not yet a frozen or authorized 300-match runner.

**Unused-AP taxonomy and telemetry.** `arena-candidate-turn-trace-v1` records
available/executed/remaining AP, stop reason and flags, actions, command indices,
observations/hashes, inference attempts, repair/request counts, tokens, and final
state hash. Each turn's leftover belongs to exactly one bucket:

| Stop reason | Meaning |
|---|---|
| `INTENTIONAL_END_TURN` | The explicit action was reached and executed. |
| `CLEAN_PLAN_COMPLETE` | A valid empty/short/full plan completed without explicit stop. |
| `EXECUTION_TRUNCATION` | Execution rejected a planned action; no successful recovery ended the turn. |
| `PROVIDER_FAILURE` | No usable plan after allowed repair, including static rejection or transport failure. |
| `TERMINAL` | Game victory ended execution before remaining AP was used. |

Exact provider error categories retain static-versus-transport detail. A recovered
truncation is still counted as an execution-invalidity event, but its final leftover
is attributed to the final stop reason, preventing double-counting. If replacement
provider inference fails, leftover is provider-failure AP and the triggering
execution-invalidity event remains visible. Clean full-budget plans have the same
completion reason with zero AP leftover; `clean_short_plan` requires positive AP.

Bounded telemetry separates planned versus reached first EndTurn, clean initial
completion, invalidity-triggered refresh, AP at refresh, replacement explicit stop
or clean short completion, recovered AP and second invalidity. Stepwise records
explicit-stop decisions, gameplay actions before stop, calls and remaining AP.
EndTurn is excluded from gameplay action counts and AP spent. Aggregation partitions
unused AP, counts failures even when recovered, and exposes requests/turn and
truncation AP loss/turn. OpenAI and Ollama token fields are normalized; unavailable
usage stays null. `backend_thinking_seconds` means observed backend request wall
time, including transport, not extracted reasoning or pure model compute time.

**Offline validation.** Deterministic tests cover strict/bounded Attack+Move+EndTurn
(5 AP available, 2 spent, 3 intentional leftover), no replan on explicit or clean
completion, invalidity-triggered recovery, replacement EndTurn, second invalidity,
EndTurn ordering/extra-field rejection, terminal suffix suppression, stepwise stop
and full-budget request bounds, zero AP, six-entry plans, partial AP rejection,
provider failures, repairs, hook restoration, both fake provider wire formats,
shared observations, AP aggregation, fixtures and outcome evaluation. Every
controller test case runs `replay(simulation.trace())` and compares the full trace.
Six response fixtures cover productive multi-action, intentional stop, full AP,
partial AP, replacement partial AP, and stepwise stop. They are examples of valid
responses, not model results or recommended tactics.

The full Arena regression passed **556 tests in 434.641 seconds**. The final
candidate-only suite passed **27 tests**, including the final V3 step-prompt
binding and version-collision assertion, after that metadata correction.
Results are recorded in `arena-candidate-offline-tests.json` and its log. Four historical
test harnesses exclude only the exact additive candidate files from their frozen
source scopes; all original source hashes and runtime integrity guards remain
enforced. The offline test guard permits Windows loopback event-loop plumbing but
forbids external connections, Ollama's standard port, and live OpenAI SDK calls.

**Prepared focused validation, not executed.** The immutable preparation artifact
is `arena-candidate-focused-validation-v1.json`, with source, snapshot, prompt,
observation and configuration bindings. It references eight unchanged snapshots:

| Frozen probe | Available AP | Purpose |
|---|---:|---|
| AP-001 | 1 | Small budget compliance |
| AP-003 | 3 | Partial budget and plan shape |
| AP-005 | 5 | Full budget and multiple actions |
| MULTI-001 | 2 | Witnessed multi-action objective |
| DOWNED-003 | 2 | Down/Finish continuation |
| POSITION-002 | 3 | Witnessed move/action objective |
| CORE-002 | 1 | Terminal leftover precedence |
| FIREBALL-003 | 2 | Stop/alternative-action judgment in a friendly-only area case |

Run one repetition in fixed probe order, strict then bounded then stepwise, using
the same frozen `luna-config-v1` configuration. This is 24 short turn trials, not
24 full matches. The **hard ceiling is 86 requests**: strict 8×2=16, bounded 8×4=32,
stepwise 2×(1+3+5+2+2+3+1+2)=38. At most 43 primary decisions and 43 static repairs;
zero preflight requests, transport retries, fallback, or extra replacement trials.
Actual requests may be lower due to stops, victories, or failures. There is no
implicit authorization to spend this budget.

Review first-response/AP compliance by budget; explicit stops and their board
outcomes; gameplay action counts/one-action rates; and paired tactical outcomes.
EndTurn declares intent but does not prove that stopping was good play. The
friendly-only case has other legal possibilities and does not prescribe stopping.
Assess stops against opportunities/outcomes, not AP maximization. This small suite
can screen for gross regressions; it cannot establish statistical equivalence to
V5 or a universal optimal stop policy. The historical mechanics evaluator is
reused for committed gameplay with EndTurn excluded; failure/stop telemetry stays
separate. No all-122 model rerun is proposed.

The preparation module has only an offline verification entry point:

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m aig.arena.candidate_validation
.venv/Scripts/python.exe -m unittest discover -s tests -p test_arena_benchmark_candidate.py -q
```

There is intentionally no live execution CLI here. A separately approved runner
must persist the pre-send request ledger, enforce this exact schedule/budget and
source binding, create a new output directory, and retain failed artifacts.

**Implications for the case study.** Compare bounded versus strict on wins,
execution failures/truncations, provider failures, truncation-derived AP loss,
requests, latency and tokens. Compare bounded versus stepwise on whether matched
outcomes/reliability can be attained with fewer calls. Report a Pareto/efficiency
frontier, never an opaque composite score. Headline match quality comes from wins,
Core damage, units downed/finished, match length and tactical outcomes. AP usage
is descriptive. Future paired match summaries can join these turn aggregates
with existing replay outcome metrics to report win rate versus requests/turn and
backend request time, execution-failure rate versus requests/turn, truncation AP
loss versus requests/turn, and intentional versus failure-derived unused AP.

Before 300 matches: decide whether to authorize the focused check; evaluate its
stopping/plan-shape behavior; freeze the candidate policy/control/schema/observation
family and model settings; add a new matched full-match schedule and runner binding
with failure adjudication, replay checks, provenance and budget ledger; then obtain
separate authorization for the actual 100/100/100 run. Old benchmark V1–V6 artifacts
are not retargeted, and historical evidence is not relabeled as candidate evidence.

**Files and preservation.** New production files are `ai/benchmark_candidate.py`,
`ai/candidate_control.py`, and `candidate_validation.py` under `backend/aig/arena`.
Added artifacts are the focused validation JSON, response fixture JSON, candidate
tests, exact test-scope helper, this report, preservation audit and offline test
results. Modified existing files are only the four test harnesses for AP budgeting,
sequential prompting, tactical literacy and Fireball methodology. The user's
pre-existing dirty work is preserved. No historical production module, prompt,
game mechanic, heuristic, Empire source, model configuration, or default changed.

`arena-candidate-preservation.json` records the initial 423-file tracked/untracked
inventory, the intentional test-only differences, and an evidence inventory/check.
An independent prior preservation inventory covers 13,943 historical evidence files
and matches byte-for-byte. The current evidence inventory covers 13,842 Arena/Qwen
files, including V5 evidence created after that prior inventory; its capture timing
is recorded explicitly rather than presented as a start-of-task snapshot.
Historical run guards still reject new source inventories outside their frozen
bindings. This deliberate protection is not relaxed for live execution.

Zero live inference occurred. The 300-match benchmark remains unstarted.
