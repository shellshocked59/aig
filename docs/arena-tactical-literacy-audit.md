# Arena tactical literacy audit ? offline preparation

Status: prepared on 2026-09-14. Zero live OpenAI or Ollama inference. No prompt tuning, gameplay changes, control changes, or large benchmark execution.

## Purpose and interpretation

Measure observable mechanical consequences of baseline Luna plans before the proposed 100 strict / 100 bounded / 100 stepwise full matches. This is a selected-state diagnostic, not a representative win-rate sample or an arithmetic examination with explicit verbal answers. Objectives and expected results are evaluator-only: Luna receives the unchanged observation and prompt. Appending questions would change the baseline being measured.

A legal alternative cannot establish misunderstanding. In particular, negative threshold probes show whether a selected action actually downs its target, but cannot establish that Luna believed the action was lethal. Empty and friendly-only Fireballs are consequence diagnostics, not automatic failures when ignored. There is no LLM judge and no hidden reasoning retention.

## Authoritative mechanics map

| Location | Authority |
|---|---|
| `backend/aig/arena/state.py` | `STATS`, HP limits, ACTIVE/DOWNED invariants, 5 shared AP, Core HP 30, rules v2 and scenario v1 |
| `backend/aig/arena/commands.py::attack_damage` | Pure pre-clamp damage; POWER +2, WARD -2 with minimum 1 against units; basic attacks on SIEGE add 4 against Cores |
| `commands.py::validate_command` | Pure ownership, class, status, AP, range and LOS checks |
| `commands.py::apply_command` | Authoritative mutation: damage, healing, revival, removal, push, AP deduction, victory |
| `commands.py::arena_fireball_affected_units` | All ACTIVE units in Chebyshev radius 1, including caster/allies; excludes bodies/Cores |
| `commands.py::resolve_victory` | Zero Core HP or no ACTIVE units defeats a team; simultaneous elimination loses for acting team |
| `commands.py::find_path`, `geometry.py` | BFS movement; Chebyshev range; supercover LOS; terrain corner restrictions |
| `queries.py`, `public_state.py` | Legal action queries reuse validation; actor-grouped serialization, abilities/stats/positions/HP |
| `replay.py::ArenaSimulation`, `replay` | Detached engine execution, command/state hashes, independently verified replay |

No production extraction or refactor was required. Attack damage and legality already have pure functions; full consequences use command execution. The oracle never implements another combat resolver.

Current base Attack damage / range / move range: Knight 6/1/2, Ranger 5/3/3, Mage 6/2/2, Cleric 3/2/2. Shield Bash is 4 damage, range 1, 1 AP; surviving targets push one tile if free. Snipe is 8 damage, range 4, 2 AP. Fireball is 4 damage, cast range 2, radius 1, 2 AP. Heal restores up to 5 HP, capped at maximum, at range 2 for 1 AP. Revive restores exactly 5 HP at range 2 for 2 AP; the revived unit may act immediately. Finish removes an adjacent DOWNED enemy for 1 AP. Move and Attack cost 1 AP. Specials do not target Cores. Damage downs units at zero; bodies remain and occupy tiles. Victory may prevent a later Finish.

POWER applies to all offensive damage, including basic Core attacks. WARD applies only to unit targets. SIEGE applies only to basic Core attacks. Fireball calculates its affected set and damage from the pre-action state before applying all losses. Units and Cores do not block LOS; blocked terrain does. LOS excludes endpoints; Fireball may target a blocked tile. Exact corner crossings check both side tiles. Knight basic attacks do not require ranged LOS.

## What Luna sees: A absent, B ambiguous, C clear

Full-turn baseline: `arena-turn-prompt-v1` plus `arena-observation-v1`. The observation includes unit/Core IDs, HP/max HP, status, positions, class stats, ability ranges/AP costs, legal actions grouped by actor, full board terrain/bonuses, remaining shared AP, numeric `action_rules`, and numeric `bonus_rules`. Prompt V1 explicitly supplies ability damage, Fireball friendly fire, Finish removal, Revive 5 HP/immediate action, shared AP, dynamic legality and victory.

| Mechanical question | Full-turn V1 classification | Basis / limitation |
|---|---|---|
| Basic and exact Snipe lethal | C | Explicit damage and HP; zero-HP down consequence is inferable from ACTIVE/DOWNED language but not stated as a formal transition table |
| Multi-action damage/AP | C | Costs, remaining AP and action ordering are explicit; lists describe current legality |
| POWER/WARD/SIEGE amounts | B | Numeric fields +2/-2/+4/minimum 1 exist; names do not explicitly bind attacker vs target tile, all specials, or exclusion of Core WARD |
| Core lethal/victory | C for ordinary damage; B for tile interactions | HP and win condition explicit |
| Fireball friendly damage | C for friendly-fire inclusion; B for exact footprint | Prompt includes caster/allies and ACTIVE only, but ?within one tile? does not name Chebyshev distance |
| DOWNED vs removed/Revive | C | Bodies occupy tiles, cannot act; Finish removes, Revive restores and allows action |
| Heal clamping | B | HP/max HP and amount given; cap not explicit in prompt |
| Shield Bash push | B | Says pushes when destination free; omits surviving-target condition and exact vector for diagonal adjacency |
| Current range/LOS legality | C | Authoritative current legal choices supplied |
| Later range/LOS after movement | B / A details | Distance metric ambiguous; exact supercover/endpoints and entity nonblocking rules absent (A) |
| Fireball simultaneous team elimination | C | Casting team loses explicitly |

V2 retains these numeric facts, compacts class stats/ranges, and flattens legal actions with explicit actors. V3 wraps that catalog in action IDs. Neither adds missing geometric semantics. Stepwise uses `arena-step-prompt-v1` plus Observation V2: its short prompt gives costs and selection instructions but omits the full-turn prose explaining victory, Finish removal, immediate revived action, and several consequences. Numeric action rules survive in V2; that is not the same information contract. Those omitted prose consequences are A for stepwise, not evidence of a Luna arithmetic defect.

Recommendation: test the current full-turn baseline as-is, preserving B/A flags. It is sufficiently informative for a useful baseline, but the audit cannot certify all later-state geometry or explain tactical intent. Do not generalize this baseline directly to stepwise. No fixes are included here.

## Oracle and future ranges

`mechanics_oracle.py` executes a fresh snapshot with `ArenaSimulation`, checks actual transitions between actions, and independently replays every committed command. Illegal actions produce an indexed failure without mutation; terminal victory stops evaluation and records ignored suffix length. Output includes affected entities, HP before/after, damage/healing bounds, ACTIVE/DOWNED/removed status, positions, friendly/enemy loss, AP, winner, final snapshot/hash and replay trace.

Damage means **effective HP loss**, including HP clamping, not nominal overkill. Finish removal is not recorded as damage. Current damage/healing/HP bounds have equal minimum and maximum. Per-step cumulative losses are computed from executed transitions, never nominal damage sums. Unchanged entities are omitted from `affected`; for example an empty Fireball has no affected entries.

`Bounds(6,9).lethal(5/8/10)` yields guaranteed / possible / impossible. `possible` includes guaranteed; the classification string distinguishes possible-only. HP bounds reverse damage endpoints. No probability is inferred from a range. A future engine adapter must return authoritative joint outcome branches for sequences, preserving correlations, state-dependent legality and terminal branches; marginal damage intervals alone cannot resolve those sequences. This change provides the bounds vocabulary and tests, not fictional ranged gameplay or a stochastic engine. Probabilities are intentionally absent.

## Probes, objectives and confounds

42 fixtures cover all ten requested categories; two additional consequences cover Bash push and Heal clamping. Valid detached states use one principal actor/target and a distant enemy reserve to avoid accidental team victory before Finish. They are valid fixtures rather than claims about naturally reached match frequencies. State setup HP thresholds are calibrated through authoritative resolution where appropriate; complete expected transitions are frozen. Any subsequent rules/source drift fails verification instead of silently recomputing the benchmark.

Predicates accept any legal plan achieving the target down/removal/revival/HP/Core outcome, not an exact action spelling. Fireball positive objectives also cap friendly HP loss at the reference consequence. The suite stores reference witnesses, their first actions, AP costs and objective existence evidence. These lists are **not exhaustive**. `minimum_ap_reference` is the cheapest listed witness; `minimum_ap_global` is deliberately null. No global optimality solver or claim of impossible global lethal is made when a candidate fails. `impossible_reference_actions` records the exact authoritative rejection, not a proof about every alternative.

Both first-action objective satisfaction and full-plan satisfaction are evaluated. Reference-prefix consistency is positive-only evidence: an unlisted prefix is null, not incorrect. A later illegal suffix is reported even if an earlier action attained the objective. Terminal suffixes are ignored by engine semantics. AP/negative/control probes remain descriptive when a satisfying witness is absent.

## Frozen inventory

| Category | Count |
|---|---:|
| LETHAL | 4 |
| MULTI | 4 |
| AP | 6 |
| POWER | 2 |
| WARD | 2 |
| CORE | 4 |
| DOWNED | 4 |
| REVIVE | 4 |
| FIREBALL | 8 |
| POSITION | 4 |

| ID | Probe | AP | Objective | Reference outcome |
|---|---|---:|---|---|
| LETHAL-001 | exact | 2 | down | legal |
| LETHAL-002 | overkill | 2 | down | legal |
| LETHAL-003 | one-above | 2 | hp_at_most | legal |
| LETHAL-004 | nonlethal | 2 | hp_at_most | legal |
| MULTI-001 | two-attacks | 2 | down | legal |
| MULTI-002 | snipe-attack | 3 | down | legal |
| MULTI-003 | ap-short | 2 | down | rejected at 1 |
| MULTI-004 | down-stale-attack | 2 | down | rejected at 1 |
| AP-001 | 1-AP-attack | 1 | diagnostic | legal |
| AP-002 | 2-AP-attack+attack | 2 | diagnostic | legal |
| AP-003 | 3-AP-attack+attack+attack | 3 | diagnostic | legal |
| AP-004 | 4-AP-snipe+snipe | 4 | diagnostic | legal |
| AP-005 | 5-AP-snipe+snipe+attack | 5 | diagnostic | legal |
| AP-006 | 5-AP-snipe+snipe+snipe | 5 | diagnostic | rejected at 2 |
| POWER-001 | snipe | 2 | down | legal |
| POWER-002 | attack | 2 | down | legal |
| WARD-001 | snipe | 2 | hp_at_most | legal |
| WARD-002 | attack | 2 | hp_at_most | legal |
| CORE-001 | siege-False-hp-9 | 1 | win | legal |
| CORE-002 | siege-True-hp-9 | 1 | win | terminal blue |
| CORE-003 | siege-False-hp-5 | 1 | win | terminal blue |
| CORE-004 | siege-True-hp-10 | 1 | win | legal |
| DOWNED-001 | down | 1 | down | legal |
| DOWNED-002 | finish | 1 | removed | legal |
| DOWNED-003 | down-finish | 2 | removed | legal |
| DOWNED-004 | short-down-finish | 1 | removed | rejected at 1 |
| REVIVE-001 | revive | 2 | revived | legal |
| REVIVE-002 | revive-act | 3 | revived | legal |
| REVIVE-003 | revive-short | 1 | revived | rejected at 0 |
| FIREBALL-001 | enemy-only | 2 | hp_at_most | legal |
| FIREBALL-002 | mixed | 2 | hp_at_most | legal |
| FIREBALL-003 | friendly-only | 2 | diagnostic | legal |
| FIREBALL-004 | empty | 2 | diagnostic | legal |
| FIREBALL-005 | enemy-down | 2 | hp_at_most | legal |
| FIREBALL-006 | friendly-down | 2 | hp_at_most | legal |
| FIREBALL-007 | ward | 2 | hp_at_most | legal |
| FIREBALL-008 | power | 2 | hp_at_most | legal |
| POSITION-001 | out-of-range | 3 | down | rejected at 0 |
| POSITION-002 | move-snipe | 3 | down | legal |
| POSITION-003 | blocked-los | 3 | down | rejected at 0 |
| POSITION-004 | bash-push | 1 | diagnostic | legal |
| REVIVE-004 | heal-clamp | 1 | hp_at_least | legal |

## Reporting taxonomy and denominators

- Correct mechanical recognition: legal plan satisfies the frozen outcome predicate. This does not prove verbal arithmetic comprehension.
- Legal but missed opportunity: a satisfying reference witness exists, but the legal selected plan does not achieve the objective. Tactical preference remains a possible explanation.
- Arithmetic/rule-inconsistent: first selected action fails authoritative execution. Information A/B/C is retained; `reasoning_failure_inferred=false` prevents equating illegal action with demonstrated arithmetic misunderstanding.
- Execution-sequence failure: a later selected action becomes illegal; keep committed prefix and indexed failure.
- Static invalidity: provider output fails schema/reference/AP validation, including exhausted static repair.
- Provider failure: transport/refusal/envelope failures; no fallback.
- Ambiguous tactical choice: no objective or no satisfying reference witness establishes an opportunity.

`results.json` reports each repetition. `summary.json` gives category counts and objective satisfaction rates only where frozen witnesses establish an opportunity. Provider/static/execution failures stay in those scheduled completed-trial denominators; unstarted trials remain separately visible. No Tactical IQ or opaque composite. Per-trial execution records provide actual friendly damage, down/removal counts, AP and terminal evidence, enabling mechanics-specific analysis without reading intent into plans. Repaired outputs are distinguishable through per-attempt telemetry and schema-shaped outputs.

## Bindings, freeze and drift

Suite `arena-tactical-literacy-v1`; oracle `arena-mechanics-oracle-v1`; fixture `arena-literacy-fixtures-v1`; rules `arena-rules-v2`; scenario `arena-scenario-v1`; prompt `arena-turn-prompt-v1`; observation `arena-observation-v1`; schema `arena-turn-plan-schema-v1`; profile `luna-config-v1`.

Source revision `0999120892df07ee709c59e3f2596801cb025711` had pre-existing worktree changes. The frozen manifest's 77 file hashes, not commit ID alone, identify the evaluated implementation. Suite payload SHA-256: `57ece3f65fc3f11d71f3f45bc528c52abc753d0843d604268697db3584a2a317`. Snapshots and observations have individual hashes. Verification checks frozen reference outcomes and replay. The runner checks source hashes before every transport attempt and at completion. The create-only freeze command refuses an existing suite; future changes require a separately versioned artifact.

## Repetitions and budget

Recommend three independent decisions per fixture: **42 ? 3 = 126 intended requests** before repairs. Order is repetition then frozen fixture order. No preflight, inference retry, execution replan, match, fallback, or replacement trial. Each decision uses the production adapter's existing at-most-one static repair. Architectural maximum is 252 requests; the enforced hard ceiling is **140**, including repairs and failures. Ceiling exhaustion preserves partial results and stops; unused capacity is not permission for extra trials.

Stage 1 strict telemetry (`.local/arena-bounded-luna-comparison-01-analysis/report.md`) recorded 14 decisions, 15 requests, one repair, 44,409 total tokens, and 1.722073 provider seconds/request. This gives a budgeting scenario of 9 repairs, 135 total requests, approximately **400,000 total tokens and 233 provider seconds**. The older 10/102 repair rate gives about 12.35 repairs, 138.35 requests, 410,000 tokens and 238 provider seconds at the same request averages. At 140 requests the Stage 1 token scenario is about 414,500 tokens and 241 provider seconds. These are extrapolations, not guarantees; smaller fixtures, caching, queueing and errors can differ. Allow roughly **5?10 minutes elapsed** in ordinary service conditions; timeout-heavy runs can take longer. The profile caps output at 512 tokens/request (71,680 at the ceiling); input tokens have no separate hard cap here. No frozen pricing model exists, so dollar estimates remain absent.

The pinned Luna profile is `gpt-5.6-luna`, reasoning `none`, maximum output 512, `store=false`, SDK retries 0. Runtime credentials/timeouts come from existing settings; secrets are not stored.

## Exact commands and artifacts

Offline verification:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.tactical_literacy verify
```

Prepared future live command ? **not executed; requires user authorization**:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.tactical_literacy run --suite arena-tactical-literacy-v1 --provider openai --output .local/arena-luna-tactical-literacy-01 --live
```

The output directory must not exist. It contains manifest, frozen suite, durable request reservations, per-probe starting state/observation, schema-shaped provider attempt outputs, parsed plan, telemetry, execution/trace, mechanics evaluation/classification, replay verification, per-probe results and category summary. Malformed model prose is omitted; no chain-of-thought is retained. Failures and unstarted counts remain visible. Source/provider/accounting/unclassified errors stop the schedule. No automatic resume or overwrite.

Offline scripted artifacts are in `.local/arena-luna-tactical-literacy-offline-01`: 126 scripted cases, zero provider requests. These validate plumbing and scoring, not model quality; intentionally invalid reference sequences remain invalid in these results.

## Validation and preservation

Final validation: **140 tests passed together** (14 new audit tests plus 126 existing engine/AI/Fireball tests), after source edits stopped. The frozen suite verifies and all 126 offline scripted trials have replay-verified execution with zero provider requests. `git diff --check` passes. An earlier run correctly encountered historical source-scope guards while additive modules were being introduced; the final combined run is clean.

The dedicated tests block socket connects and use fake transport to exercise the real provider parser, static repair, durable reservations, ceiling denial before transport, replay, suite/source corruption, range semantics, modifiers, AP, partial turns, equivalent plans, Fireball, team/Core terminal transitions, Finish, Revive and Heal. Historical Fireball tests retain every original hash and use an explicit test-only exclusion list for unrelated newly added modules/artifacts. Production historical drift guards are unchanged.

The pre-existing checkout was dirty. Existing work was retained. Preservation checks compare 480 tracked/historical files, including Stage 1 artifacts, plus the legacy Fireball preservation manifest. The only intended existing-file change is the additive test scope in `tests/test_arena_fireball_methodology.py`. No engine/provider/prompt/observation/control/profile source was edited.

## Decision after an authorized baseline

Inspect category patterns across all three repeats. Repeated constrained lethal/AP errors, modifier failures or harmful Fireball consequences warrant examining the associated A/B/C information classification before changing a prompt. Legal alternatives alone do not demonstrate inability to calculate. Missing rule information is a representation finding; it must not be pooled with mechanical reasoning failures. Diagnostic-only states have no automatic pass/fail.

Do not treat this selected suite as an automatic readiness gate for all 300 matches. If systematic baseline failures justify a representation revision, create a new prompt/observation version and rerun these same frozen states/predicates with an explicitly versioned comparison binding. Preserve V1 evidence. Only then freeze the eventual case-study configuration and separately authorize the large benchmark. This task stops at preparation and requests authorization only for the focused Luna audit.
