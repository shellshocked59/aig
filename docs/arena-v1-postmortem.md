# Arena V1 postmortem and V2 research design

Phase 6A · 2026-09-13 · offline analysis only

The frozen contract fails in two distinguishable ways. Qwen's 22 statically accepted full-match plans all start with an already-illegal, out-of-range Ranger attack and execute zero AP. Luna executes substantial action prefixes, but 72 of its 100 accepted full-match plans truncate: 13 rejected actions were legal initially and became illegal, while 59 were illegal initially and never became legal in the executed prefix. Higher planned AP is therefore not evidence of effective tactical control.

The recommended first experiment is a narrowly specified **prompt-only full-turn ablation**, retaining both models, observations, logical plan schema, rules, probe states, static repair behavior, and executor. It tests whether explicit first-action membership and useful-AP wording change behavior. It does not presume prompt wording is the principal cause or promise to solve sequencing.

## Evidence and reproducibility

Primary evidence: [full-match report](../.local/arena-phase5-fullmatches-20260913-01/report.md), [full-match summary](../.local/arena-phase5-fullmatches-20260913-01/summary.json), [probe report](../.local/arena-phase5-continuation-20260913/report.md), [probe comparison](../.local/arena-phase5-continuation-20260913/comparison.json), and [earlier Qwen partial evidence](../.local/arena-qwen-probes-retry-3/summary.json). The earlier partial trials are included once through the unified comparison, not added as extra attempts.

New reproducible analysis: [analyze.py](../.local/arena-phase6a-postmortem-20260913/analyze.py), [analysis.json](../.local/arena-phase6a-postmortem-20260913/analysis.json), and [report renderer](../.local/arena-phase6a-postmortem-20260913/render_report.py). Run from the repository root with `.venv/Scripts/python.exe .local/arena-phase6a-postmortem-20260913/analyze.py`, then the renderer. These local supporting files are under ignored `.local`; the repository documentation deliverable is this document. No commit was made.

The audit reverified all **100 retained trials: 16 full-match prefixes and 84 probe attempts** (28 each for Qwen, Luna, heuristic), including failed attempts. It reconstructed observations through authoritative queries, checked observation hashes, reparsed accepted plans, replayed accepted command prefixes, reproduced each rejection, and counted legal choices before automatic EndTurn. Eleven distinct accepted-Qwen observation hashes also received detached, deterministic heuristic reference plans; this is offline engine computation, not inference. All 1,187 files in the three evidence roots plus the frozen source inventory were SHA-256 identical before and after the audit. The pre-existing AGENTS.md modification was left untouched.

Source baseline: revision `794fca9f46cbfe93d9406200c824033a59b7e812`, source manifest `10dd78b95c732ed6fc1deda9025f293eedfde38916c1287805703cbbb717c9a5`. This audit also uses the exact source bytes listed in the frozen manifest (checked again at final verification).

**Evidence limit:** `benchmark_provider.safe_inference` deliberately drops rejected raw output. Failed calls have `resulting_plan=null`; their attempted action, actor, target and action index cannot be recovered. Saved observations and numeric/error telemetry remain available. Repair text below is reconstructed exactly from frozen source and the persisted error category, not claimed to be a saved HTTP payload. No provider history was fetched.

## 1. V1 hypothesis and frozen architecture

V1 tests whether a model can consume perfect-information Arena facts and produce an entire useful, legal tactical turn within five shared AP. The relevant outcomes are protocol/static acceptance, initial legality, sequential execution, AP utilization, tactical outcomes and match completion. The tests do not isolate model capacity, representation complexity, prompt wording or repair specificity.

Pipeline: authoritative state → immutable canonical `ArenaObservation` → one model full-turn request → static parser (one bounded repair on static rejection) → sequential command execution → truncate on first dynamic rejection → automatic EndTurn unless terminal. Prior successful commands stay committed. Dynamic execution failures do not invoke repair. Benchmark mode never falls back and stops a trial on provider failure. See [observation.py](../backend/aig/arena/ai/observation.py), [provider.py](../backend/aig/arena/ai/provider.py), [validation.py](../backend/aig/arena/ai/validation.py), [executor.py](../backend/aig/arena/ai/executor.py), and [benchmark_provider.py](../backend/aig/arena/benchmark_provider.py).

“Arena AI V1” uses `arena-rules-v2`, `arena-command-v2`, `arena-snapshot-v2`, and `arena-trace-v2`; AI experiment version and engine version are different dimensions. Other frozen IDs are `arena-scenario-v1`, `arena-observation-v1`, `arena-turn-prompt-v1`, `arena-turn-plan-schema-v1`, `arena-benchmark-v1`, `arena-probes-v1`, `arena-heuristic-v1`, `qwen-config-v1`, and `luna-config-v1`.

Qwen profile: `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M`, context 4096, temperature 0, seed 42, maximum output 256, think false, stream false; keep-alive 10m. Luna: `gpt-5.6-luna`, reasoning none, maximum output 512, store false, SDK retries zero. These are the recorded experiment configurations, not general claims about the model families.

### What “accepted plan” means

All 22 Qwen plans pass strict JSON decoding, the logical `ArenaTurnPlan` parser (exact fields, discriminators, coordinates, IDs, schema version, at most five actions and five AP), plus observation-relative static validation: current AP budget, own-team actor ID, class ability membership, target ID existence/ownership/entity restrictions and board-coordinate membership. The benchmark reparses the typed plan and checks provider provenance. This is more than JSON Schema validity; application parsing, rather than a separate general-purpose JSON Schema validator, enforces the logical contract.

Static validation deliberately does not check active/downed status, range, LOS, occupancy or path reachability, because they can change within a sequence. Nor does it require action 1 to belong to the current legal enumeration. The dynamic validator runs only when the executor attempts that action. A plan whose first action fails can still execute EndTurn, which costs zero AP.

Use clearer future reporting labels: `response_parse_valid`, `plan_static_valid`, `first_action_legal`, `executed_action_count`, `ap_executed`, `execution_invalid_truncation`, `terminal_suffix`, and `trial_completed`. Keep the historical “accepted” fields unchanged; do not equate them with executable sequences. An over-five-AP plan can be reported as `schema_validation` by the logical constructor before the later `ap_budget` check; error labels are not a complete defect taxonomy.

## 2. Frozen probe and full-match results

| Probe metric | Qwen | Luna |
|---|---|---|
| Intended attempts | 28 | 28 |
| First-response static valid | 24/28 | 27/28 |
| Repairs successful / attempted | 0/4 | 1/1 |
| Valid / failed trials | 24 / 4 | 28 / 0 |
| Execution-invalid truncations | 4 | 4 |
| Winning Core wins | 0/4 | 4/4 |
| Team Elimination wins | 4/4 | 2/4 |
| Mean planned / executed AP (accepted plans) | 1.17 / 1.00 | 4.04 / 3.36 |
| Fallbacks | 0 | 0 |

| Full-match group | Completed / intended | Outcome |
|---|---|---|
| Qwen self-play | 0/4 | 4 failed repairs |
| Qwen vs heuristic | 0/4 | 4 failed repairs; no terminal result |
| Luna self-play | 2/4 | Red team-elimination wins; 2 failed repairs |
| Luna vs heuristic | 4/4 | Heuristic wins all four, on both sides |

Full-match recorded requests: Qwen 46 (8 preflights + 30 initial calls + 8 repairs); Luna 120 (8 preflights + 102 initial calls + 10 repairs). Luna accepted 100 plans, including eight successful repairs. No fallback, tuning, Qwen–Luna match or source change occurred during V1 collection. Failed prefixes remain in completion denominators and are not counted as competitive losses with terminal winners. All 16 full-match traces replay exactly; replay fidelity establishes deterministic execution, not tactical quality.

## 3. Exact Qwen 22-plan failure taxonomy

**22/22: `target outside action range`.** Every first attempted action is `attack`, every actor is a Ranger, every index is **0 (action 1)**. Fourteen use `blue-ranger → red-cleric`; eight use `red-ranger → blue-cleric`. All 22 were predictable from the starting observation and all 22 were absent from the legal enumeration. All other engine rejection reasons have count zero in this cohort.

Blue Ranger starts at (1,0), Red Cleric at (7,4); the mirrored Red Ranger starts at (7,0), Blue Cleric at (1,4). Chebyshev distance is 6; Ranger basic attack range is 3. Range is the validator's first failing condition, so this taxonomy does not claim LOS would pass if range were ignored. All accepted states expose **54 legal options: 38 Moves and 16 Fireball impact tiles, with zero entity-target options**. Every own-unit Attack list is empty. Full-match accepted plans propose four one-AP attacks; the first fails before any AP is consumed, and the three-action suffix is discarded. Automatic EndTurn advances the game without tactical progress. This is an initial-legality failure, not a later-action dependency failure.

The ledger below covers every accepted plan. “Plan” is the one-based saved inference/plan position within that match; global turn is the engine's zero-based round count. Every row has AP planned/executed 4/0, failure index 0, predictable=yes, enumerated=no.

| Match | Plan | Global turn | Actor → target | Engine reason |
|---|---|---|---|---|
| qwen-self/match-01 | 1 | 0 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-01 | 2 | 0 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-01 | 3 | 1 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-01 | 4 | 1 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-01 | 5 | 2 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-02 | 1 | 0 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-02 | 2 | 0 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-02 | 3 | 1 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-02 | 4 | 1 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-02 | 5 | 2 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-03 | 1 | 0 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-03 | 2 | 0 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-03 | 3 | 1 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-03 | 4 | 1 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-03 | 5 | 2 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-04 | 1 | 0 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-04 | 2 | 0 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-04 | 3 | 1 | blue-ranger → red-cleric | target outside action range |
| qwen-self/match-04 | 4 | 1 | red-ranger → blue-cleric | target outside action range |
| qwen-self/match-04 | 5 | 2 | blue-ranger → red-cleric | target outside action range |
| qwen-vs-heuristic/match-01 | 1 | 0 | blue-ranger → red-cleric | target outside action range |
| qwen-vs-heuristic/match-03 | 1 | 0 | blue-ranger → red-cleric | target outside action range |

Qwen self-play contributes five accepted plans per match (20 total), then an `invalid_reference → invalid_reference` failed repair on call 6. Qwen-vs-heuristic matches 01 and 03 contribute one accepted Qwen plan each, then fail `invalid_ability → invalid_ability`; matches 02 and 04 fail their first Qwen call after the heuristic opening. Static failed outputs are unavailable, so no actor/ability reconstruction is justified for those eight failures.

## 4. Observation populations and complexity

Counts below are **per initial trial planning call**, including failed calls, excluding preflights and repair duplicates. Qwen probes have 28 observations over seven fixed states, Qwen matches 30 over early-game states, Luna matches 102 including later play. Means are call-weighted; repeated deterministic states are not independent task samples. Bytes are UTF-8 canonical compact JSON for the observation alone. Input tokens are recorded `prompt_eval_count` for Qwen and `input_tokens` for Luna, including provider input framing; they are not interchangeable tokenizers or additive byte estimates.

An option is one `(actor, action type, target/destination)` entry. Moves count destinations per actor, so a tile available to two actors counts twice. Entity target IDs count unique IDs appearing in non-position legal options; Fireball positions are reported separately. Enemy and downed unit arrays are empty in the current-player action enumeration.

| Metric: mean (min–max) | Qwen probes n=28 | Qwen matches n=30 | Luna matches n=102 |
|---|---|---|---|
| Observation bytes | 4693.86 (4155–5667) | 7345.93 (7016–7397) | 6752.83 (5386–7448) |
| Recorded input tokens | 2067.14 (1867–2510) | 3037.67 (2847–3067) | 3080.30 (2543–3389) |
| Active units, both teams | 2.43 (2–4) | 7.87 (7–8) | 5.54 (2–8) |
| Downed units, both teams | 0.57 (0–1) | 0.13 (0–1) | 1.68 (0–4) |
| Own active units | 1.14 (1–2) | 3.87 (3–4) | 2.62 (1–4) |
| Units present | 3 (2–4) | 8 (8–8) | 7.22 (5–8) |
| Legal options | 30.86 (19–70) | 50.40 (27–54) | 33.89 (4–58) |
| Move destinations | 24.14 (17–39) | 36.40 (26–38) | 22.58 (4–40) |
| Unique legal entity target IDs | 2 (1–3) | 0.13 (0–1) | 1.54 (0–6) |
| Entity-target action options | 3.14 (2–6) | 0.13 (0–1) | 1.85 (0–9) |
| Fireball tile options | 3.57 (0–25) | 13.87 (0–16) | 9.46 (0–16) |
| Global turn | 0 (0–0) | 0.87 (0–2) | 4.59 (0–13) |
| Own Core HP | 30 (30–30) | 30 (30–30) | 29.32 (18–30) |
| Enemy Core HP | 27 (9–30) | 30 (30–30) | 29.53 (18–30) |

All boards have 45 tiles (9×5). Probes have no blocked tiles and zero or one bonus tile; normal matches have four blocked tiles and six bonuses (two each Power, Ward, Siege). Full Qwen observations average 56.5% more bytes and 46.9% more recorded input tokens than its probes, with roughly three times as many active units. They require coordinating multiple classes and traversing blocked terrain before most attacks are available. Qwen never reaches a real midgame in these traces, so its complexity comparison is explicitly early-game, not a sampled full-game distribution.

**Choice count alone does not explain the failures.** The Fireball Friendly Fire probe has 70 options, more than the 54-option full-match opening, and Qwen executes two attacks in all four trials. The Snipe probe has only 25 options and all four first attacks are out of range; Revive has 21 options and all four calls fail static ability validation. Full-match failed calls include smaller 27-option observations. These are direct counterexamples to a simple monotonic option-count threshold. The observations differ simultaneously in unit count, names, target availability, terrain and required setup; no causal size or capacity effect can be estimated here.

The observed Qwen initial token counts top out at 3,067 of configured 4,096 context tokens; these counts do not demonstrate overflow. They also do not reveal server-side tokenization/truncation internals. No output-budget exhaustion diagnosis is justified from accepted short plans alone. Retain model/profile settings when testing representation changes.

## 5. Qwen low-AP analysis

All 24 accepted probe plans are short (planned AP ≤2). They contain only basic Attacks: 28 proposed attacks, 24 executed. Failed Revive trials supply no accepted-plan AP sample. Replaying to the instant before automatic EndTurn gives **A terminal: 4; B no legal actions: 0; C legal actions remain: 20**.

Category C must be subdivided: **16/24 accepted plans finish their supplied sequence while useful legal actions remain; 4/24 are forced to stop by the executor's first-action rejection.** The latter are not voluntary provider stops. The 16 normal short sequences consist of Finish/Core, Fireball, Shield Bash and Winning Core probes (four each). Their remaining options include factual opportunities to damage an enemy/Core or finish a body; they are not merely arbitrary Moves. This does not assert that spending all AP is always optimal.

Every accepted Qwen probe is listed below. A zero legal count in a terminal state reflects the game ending; it is not exhaustion of tactical possibilities in a continuing battle. The complete path, plan and remaining legal targets for each row are retained in `analysis.json`.

| Trial | Probe / retained run | Planned / executed / left AP | Legal / non-Move options left | Class / stop |
|---|---|---|---|---|
| Q-P01 | finish_or_core / run-001 | 1 / 1 / 4 | 19 / 2 | C legal actions remain |
| Q-P02 | finish_or_core / run-002 | 1 / 1 / 4 | 19 / 2 | C legal actions remain |
| Q-P03 | finish_or_core / run-003 | 1 / 1 / 4 | 19 / 2 | C legal actions remain |
| Q-P04 | finish_or_core / run-004 | 1 / 1 / 4 | 19 / 2 | C legal actions remain |
| Q-P05 | fireball_friendly_fire / run-001 | 2 / 2 / 3 | 70 / 31 | C legal actions remain |
| Q-P06 | fireball_friendly_fire / run-002 | 2 / 2 / 3 | 70 / 31 | C legal actions remain |
| Q-P07 | fireball_friendly_fire / run-003 | 2 / 2 / 3 | 70 / 31 | C legal actions remain |
| Q-P08 | fireball_friendly_fire / run-004 | 2 / 2 / 3 | 70 / 31 | C legal actions remain |
| Q-P09 | shield_bash_position / run-001 | 1 / 1 / 4 | 24 / 2 | C legal actions remain |
| Q-P10 | shield_bash_position / run-002 | 1 / 1 / 4 | 24 / 2 | C legal actions remain |
| Q-P11 | shield_bash_position / run-003 | 1 / 1 / 4 | 24 / 2 | C legal actions remain |
| Q-P12 | shield_bash_position / run-004 | 1 / 1 / 4 | 24 / 2 | C legal actions remain |
| Q-P13 | snipe_vs_basic / run-001 | 1 / 0 / 5 | 25 / 3 | C legal actions remain (executor rejection) |
| Q-P14 | snipe_vs_basic / run-002 | 1 / 0 / 5 | 25 / 3 | C legal actions remain (executor rejection) |
| Q-P15 | snipe_vs_basic / run-003 | 1 / 0 / 5 | 25 / 3 | C legal actions remain (executor rejection) |
| Q-P16 | snipe_vs_basic / run-004 | 1 / 0 / 5 | 25 / 3 | C legal actions remain (executor rejection) |
| Q-P17 | team_elimination / run-001 | 1 / 1 / 4 | 0 / 0 | A terminal |
| Q-P18 | team_elimination / run-002 | 1 / 1 / 4 | 0 / 0 | A terminal |
| Q-P19 | team_elimination / run-003 | 1 / 1 / 4 | 0 / 0 | A terminal |
| Q-P20 | team_elimination / run-004 | 1 / 1 / 4 | 0 / 0 | A terminal |
| Q-P21 | winning_core_line / run-001 | 1 / 1 / 4 | 35 / 4 | C legal actions remain |
| Q-P22 | winning_core_line / run-002 | 1 / 1 / 4 | 35 / 4 | C legal actions remain |
| Q-P23 | winning_core_line / run-003 | 1 / 1 / 4 | 35 / 4 | C legal actions remain |
| Q-P24 | winning_core_line / run-004 | 1 / 1 / 4 | 35 / 4 | C legal actions remain |

In Finish/Core, a further Core attack and Finish remain; in Fireball, both active enemy targets remain attackable; in Shield Bash, basic Attack and Shield Bash remain; in Winning Core, the enemy Core remains attackable while Qwen attacked an enemy unit instead. In Snipe, basic Attack on `enemy2` and Snipe on `enemy`/`enemy2` were legal even though the attempted basic Attack on `enemy` was not. Four terminal Team Elimination probes legitimately stop after one AP. Mean unused AP of 4 therefore combines successful terminal efficiency, normal early stopping, and execution failure; it cannot be read as a single behavioral trait.

## 6. Luna repair failures and execution taxonomy

The two self-play failures are fully localized in time, but not to a rejected action. The retained category `invalid_ability` means some action named an ability absent from its own actor's class abilities. Such an actor/type pair cannot appear in the legal enumeration. This is a class-membership contradiction at category level; the exact actor, action, target and index were discarded, so they remain **unknown**, including whether the same wrong ability was repeated in repair.

| Match | Failed call / global turn / side | Initial → repair category | Input tokens initial / repair | Action, actor, target, index |
|---|---|---|---|---|
| luna-self/match-03 | 27 / 13 / Blue | invalid_ability → invalid_ability | 2815 / 2846 | Not persisted |
| luna-self/match-04 | 18 / 8 / Red | invalid_ability → invalid_ability | 2695 / 2726 | Not persisted |

Both receive exactly: `Previous output failed validation (invalid_ability). Return a corrected ArenaTurnPlan using the same observation and schema. No reasoning or commentary.` It names the category but does not specifically describe the offending class/action defect. See `inference.jsonl` lines 27 and 18 respectively and the corresponding `observations.jsonl` rows.

Across full matches, Luna has **72/100 accepted-plan execution-invalid truncations**: self-play 60/85, heuristic matchups 12/15. Completed self-play alone has 30/42. Failed static calls are additional and excluded from these accepted-plan denominators. There are 6 rejections at index 0, 29 at index 1, 32 at index 2, 4 at index 3 and 1 at index 4. Thus “later in the plan” alone is not proof an earlier action caused the illegality.

| Exact engine reason | Self-play | vs heuristic | Total | Initially legal → illegal |
|---|---|---|---|---|
| target outside action range | 21 | 3 | 24 | 0 |
| impact outside Fireball range/board | 12 | 4 | 16 | 0 |
| invalid target ACTIVE/DOWNED status | 9 | 2 | 11 | 10 |
| destination is occupied, blocked, unchanged, or beyond move range | 10 | 1 | 11 | 2 |
| actor must own an ACTIVE unit | 1 | 0 | 1 | 1 |
| blocked line of sight | 7 | 2 | 9 | 0 |

The **13 directly demonstrated sequencing failures** are ten attacks/Shield Bashes on targets downed by the prefix, two Moves into a tile occupied by the prefix, and one Finish by a Mage downed by its own preceding Fireball. Eleven occur in self-play and two versus heuristic. All 13 rejected actions appear in starting legal options. The other 59 are absent initially and remain illegal after every executed prefix; 56 keep the same rejection reason and three change reasons (two revived actors still lack range; one initially distant target becomes downed). Initial absence alone would not be wrong for a properly enabled later action, but these prefixes never enable it.

Examples: self-play match-02 plan 5 moves the Mage to (3,2), casts Fireball, then tries to move the Knight onto that occupied tile. Match-02 plan 10 casts Fireball with the Red Mage and then attempts its Finish after the caster is downed. Versus-heuristic match-01 plans 9 and 11 each attack a target twice, down it, then attempt another Attack. Appendix B lists all 72 truncations; snapshots and legality after every prefix are in `analysis.json`.

Probe contrast: Luna's four execution-invalid cases include three genuinely changed range failures: Shield Bash Position run-003 and Team Elimination runs 002/004 use Shield Bash then Attack at index 1 after the push. Fireball Friendly Fire run-003 rejects Move at index 4, and that destination was already illegal initially. The other five probe truncations are terminal suffixes, not failures. The small probe set contains a higher proportion of clear sequencing errors than the full-match corpus; it does not support treating all full-match failures as sequencing alone.

## 7. Luna versus heuristic: mechanical comparison

All figures here cover only the four completed head-to-head matches. They are trace outcomes, not inferred model reasoning. “Units downed” counts downing events and can count a revived unit again; “removed” means Finish removals. Healing includes HP restored by Revive, matching the frozen replay metric.

| Metric | Luna | Heuristic |
|---|---|---|
| Accepted turns | 15 | 17 |
| AP planned | 73 | 82 |
| AP executed | 42 | 82 |
| Executed AP / turn | 2.80 | 4.82 |
| Unused AP | 33 | 3 |
| Unit damage | 75 | 165 |
| Core damage | 0 | 60 |
| Healing including Revive | 15 | 49 |
| Downing events inflicted | 7 | 15 |
| Finishes / opposing units removed | 0 | 5 |
| Revives | 3 | 5 |
| Friendly-fire damage | 0 | 0 |
| Invalid truncations | 12 | 0 |

| Executed action | Luna | Heuristic |
|---|---|---|
| move | 12 | 18 |
| attack | 6 | 38 |
| heal | 0 | 5 |
| finish | 0 | 5 |
| revive | 3 | 5 |
| shield_bash | 0 | 0 |
| snipe | 4 | 3 |
| fireball | 5 | 0 |

| Match | Luna side | Terminal / winner | Player turns / global round | Final Core Luna / H | Active survivors Luna / H | Downed Luna / H | Removed Luna / H |
|---|---|---|---|---|---|---|---|
| match-01 | blue | team elimination / red | 12 / 5 | 30 / 30 | 0 / 2 | 2 / 2 | 2 / 0 |
| match-02 | red | Core destruction / blue | 5 / 2 | 0 / 30 | 2 / 4 | 1 / 0 | 1 / 0 |
| match-03 | blue | team elimination / red | 10 / 4 | 30 / 30 | 0 / 4 | 2 / 0 | 2 / 0 |
| match-04 | red | Core destruction / blue | 5 / 2 | 0 / 30 | 2 / 4 | 2 / 0 | 0 / 0 |

In matches 01/03, heuristic Red wins by team elimination after 12/10 player turns. Its active survivors are Knight+Mage in 01 and all four classes in 03; Luna has none. In matches 02/04, heuristic Blue destroys the Core after five player turns and retains all four units active; Luna retains Cleric+Ranger active in both, demonstrating that unit survival alone is not sufficient.

Repeatable supported differences:

- Luna plans 73 AP but executes 42 (57.5%); heuristic plans and executes 82. Their planned AP/turn is similar (4.87 vs 4.82), while execution differs sharply (2.80 vs 4.82). All four matchups have Luna truncations; heuristic has none.
- Luna casts five Fireballs for 10 AP, hitting only one active-unit target in total. Four Fireballs therefore hit no active unit. There is zero friendly-fire damage in this matchup; the poor return here is empty-area casting, not friendly fire. Heuristic casts none.
- Heuristic uses five Finishes, five Heals and five Revives; Luna uses no Finish or Heal and three Revives. Luna supplies no persistent removals, and heuristic revives five times. The traces establish this difference, not a causal claim that adding Finish alone would win.
- As Blue, heuristic repeatedly exploits Siege for four Core attacks per match, delivering 30 Core damage each time; Luna deals zero Core damage across all four. Heuristic has eight Siege Core attacks versus zero for Luna. Both sides have four Power attacks across the series; broad “heuristic dominates every premium tile” is unsupported. Ward-action counts are 13 versus 1, which measure actions on Ward, not continuous control.
- Against Blue heuristic, Luna deals no damage in either short match. Against Red heuristic it deals 45 and 30 unit damage, but loses all active units. Movement without eventual productive action should be diagnosed per prefix; these totals do not establish intent or a universal movement defect.

Across all Luna full-match prefixes (including self-play), the separate friendly-fire finding is 33 Fireballs, 39 active-unit hits, 18 friendly hits and 62 friendly damage. Do not import that aggregate into the zero-friendly-fire head-to-head subset.

## 8. Heuristic as a reference

[heuristic.py](../backend/aig/arena/ai/heuristic.py) reconstructs a detached simulation from the same observation. It enumerates legality after every simulated action, simulates candidates using authoritative commands, scores their actual consequences, commits a selected action to its detached state, and repeats while AP and a nonterminal battle remain. Tie breaking is deterministic: lexicographic utility, AP cost, then canonical action JSON. It can stop when no positively scored candidate remains. Its greedy utility is explicit, not optimal search or ground truth.

On all five distinct accepted-Qwen full-match observation hashes, the offline heuristic spends five legal AP. Its mirrored opening is Ranger Move to the central Siege approach, a second Move to the opposing Siege tile, then three Attacks. For Blue at turn 0 the exact sequence is Move (3,2), Move (5,2), Attack red-mage, Attack red-mage, Attack red-knight. The second Move and attacks depend on the first Move; this is a concrete example of why a static starting-state catalog cannot encode every useful later action.

On the six accepted-Qwen probe states, corresponding deterministic plans use five AP in Finish/Core, Fireball, Shield Bash and Snipe, and one terminal AP in Winning Core and Team Elimination. The existing frozen heuristic reference also covers Revive and spends five AP there. The audit replays all 28 saved heuristic probe attempts.

Robust legality comes from engine simulation and repeated enumeration; priorities determine which legal sequence it selects. An LLM has factual rules but no command simulator inside its V1 request. This distinguishes a rule/selection problem from external state-simulation support. Do not put the heuristic's utility tiers, opening sequence, class preferences or probe solutions into an LLM prompt. Its performance is a useful executable reference, not proof that it knows optimal tactics.

## 9. ArenaObservation V1 design audit

Exact top-level shape: `schema_version`, `environment`, `rules_version`, `scenario_version`, `turn`, `active_player_id`, `action_points_remaining`, `winner_player_id`, `players`, `board`, `action_rules`, `bonus_rules`, `own_team`, `enemy_team`.

`players[]` contains `{id,name}`. `board` contains width, height and 45 `{x,y,terrain,bonus}` tiles. Each team contains `{player_id,core,units}`. Core has `{id,owner_id,x,y,hp,max_hp}`. Unit has `{id,owner_id,x,y,hp,unit_type,max_hp,status,stats,abilities,actions}`. Stats are `{hp,damage,attack_range,move_range,heal_amount,heal_range}`. Each supported ability maps to `{ap_cost,range}`. Every unit's `actions` object has eight keys: move, attack, heal, finish, revive, shield_bash, snipe and fireball. Move and Fireball arrays contain `{x,y}` objects; other arrays contain target-ID strings.

Legal actions are already grouped by unit. **Individual options do not contain actor IDs**: the model must carry the enclosing unit ID into its plan. Destinations and targets are explicitly enumerated, with no ranking. Empty arrays for unsupported/unavailable abilities, enemy actors and bodies create repetition. An empty enemy action list reflects whose turn it is, not permanent enemy inability.

The model cross-references the unit enclosing an action list, that unit's class and abilities, target IDs elsewhere, coordinates/terrain, and action rules. Cost is explicit in ability metadata and the system prompt, but not repeated on each legal option. Class ownership is explicit per unit's ability map, yet the universal eight-key action object can obscure that distinction. This is a possible representation burden, not evidence the model actually misread a particular field.

Redundancy includes team ownership plus per-entity owner IDs, base max HP in both stats.hp and max_hp, ability ranges repeated from stats, coordinate objects repeated across Moves/Fireballs, empty eight-action objects, and some rules repeated in prompt/metadata. Units are not duplicated in a separate flat list; `build_observation` removes that public-state list when forming teams. No hidden state is needed for deterministic reconstruction.

Byte contributions below use standalone compact subtree sizes; punctuation and enclosing key names are allocated to the residual so components sum to total. Unit facts exclude `actions`; rules contain `action_rules` plus `bonus_rules`. Prompt and schemas are separate wire components, not included in observation totals. The representative midgame is the middle accepted turn (14 of 26) of Luna self-play match-03, global turn 6, with five active and three downed units.

| Component / context | Simple Finish/Core probe | Luna midgame |
|---|---|---|
| Board | 2057 | 2081 |
| Action + bonus rules | 292 | 292 |
| Unit facts / stats / abilities | 1047 | 2810 |
| Legal-action objects | 550 | 1372 |
| Core / team / metadata / punctuation residual | 609 | 668 |
| Total observation | 4555 | 7223 |
| System prompt | 1730 | 1730 |
| Logical/Ollama schema | 2567 | 2567 |
| OpenAI wire schema | 2209 | 2209 |
| Legal options / Move destinations | 19 / 17 | 42 / 25 |
| Recorded initial input tokens (different providers) | 1988 | 3268 |

Board/static rules account for about half the simple observation; unit facts and legal-action objects grow in normal matches. In the selected midgame legal objects are 19.0% of observation bytes, unit facts 38.9%, board 28.8%. The full-match initial observation is already 7,397 bytes; Luna observations range 5,386–7,448 and often shrink as units are removed. There is no evidence of unbounded history accumulation: each initial call is stateless and sends current facts. Compacting only action options would leave substantial repeated unit and board metadata.

## 10. ArenaTurnPlan schema audit

[contracts.py](../backend/aig/arena/ai/contracts.py) defines `{schema_version,actions[]}`, with eight discriminator branches. Each action has exactly `type`, `unit_id`, and one of `target_id`, `destination:{x,y}`, or `target_position:{x,y}`. There are no optional/null fields in the plan, no explanations, no EndTurn action and no additional properties. Zero through five actions are permitted. The deepest data path is root → actions array → action object → coordinate object → scalar; this is modest nesting rather than an unusually deep schema.

Potential small-model burdens are selecting one of eight branches, repeating arbitrary actor/target strings, preserving actor ownership from the containing observation unit, choosing the correct target representation and field name, distinguishing class-specific abilities, and budgeting mixed one/two-AP actions. JSON Schema does not encode a state-specific ID enum, class/ability relationship, total AP sum or dynamic legality. A syntactically valid arbitrary target string is not necessarily a legal action. Coordinates have bounds, but path/occupancy/LOS remain application facts.

Ollama receives the 2,567-byte logical schema with `oneOf` and `const`. OpenAI receives a 2,209-byte transformed schema using disjoint `anyOf` and typed singleton enums, with metadata/minLength/pattern removed; the same logical parser still enforces original constraints. This adapter distinction is already part of frozen V1 and is a confound when attributing differences solely to model capability. The schema is fairly compact structurally; the 22 accepted Qwen plans demonstrate that serialization alone is not their principal execution failure. Neither a larger schema nor a simpler schema is proven to fix it.

## 11. Repair-system audit

Each static rejection permits one correction using the same observation/schema and system prompt, plus a user message containing only the category. The rejected assistant output is **not included in the repair conversation**, even though it exists transiently before safe logging. The system makes a second stateless request; it cannot identify “the previous output” from an assistant message that was never sent. This makes the wording under-specified, but the error category is not fabricated.

The feedback supplies no action index, actor ID/class, attempted ability, target, precise validation detail or selected legal alternatives. The original observation still contains factual legal lists, but those are not targeted repair guidance. There is no repair for dynamic execution truncation.

Observed static-repair examples: Qwen Revive probes fail `invalid_ability → invalid_ability` four times; Qwen self-play fails `invalid_reference → invalid_reference` four times; Qwen heuristic matchups fail `invalid_ability → invalid_ability` four times. Luna's Snipe probe repairs `schema_validation` successfully into two Snipes. In full matches Luna repairs 8/10 static failures successfully; its two failures retain `invalid_ability` on both attempts. Successful static repair still does not guarantee execution legality.

Assessment: **B (too vague) is directly supported at defect-localization level. C is partly applicable to the “previous output” wording without that output in context**, not to the correctness of its category. A (specific feedback ignored) is unsupported: the feedback is not action-specific, and rejected responses are missing. D (overwhelmed by the full observation/schema) is a plausible hypothesis, not a demonstrated cause. The two failed Luna repairs add only 31 input tokens each while retaining the much larger original context; Qwen's recorded counts do not establish context overflow.

Future diagnostic-only logging should retain a bounded structured defect record: stage, action index, actor/class, action type, target form and exact validator category; rejected structured plans may be retained only under an explicit safe-data policy. Such logging can run identically in both arms without changing feedback. A **more specific repair prompt** is a separate experimental variable; do not quietly combine it with the first prompt-only experiment or retrofit V1 artifacts.

## 12. What V1 demonstrated, and what it did not establish

V1 demonstrated deterministic observation/command reconstruction, strict provider provenance, no fallback, bounded repair, static/execution separation, reproducible truncation, and meaningful differences between nominal AP plans and actual execution. Qwen sometimes executes useful probe actions and terminal wins; Luna can use multiple action types and complete matches; the heuristic is the strongest observed full-match reference. The failure results are informative rather than invalid data.

V1 did not establish broad model rankings, the optimal tactic for every state, general Qwen/Gemma/Luna capability, a causal observation-size threshold, prompt optimality, the benefit of larger local models, or expected stepwise performance. Four repeated attempts per probe/match are a small, partly deterministic sample. Side effects, self-play dynamics, failed-run censoring, distinct provider schemas/token budgets and state-distribution differences limit inference. Greater AP use alone is not success: empty Fireballs spend AP without damage, while a one-AP terminal win is efficient.

The defensible limitation is a **combination**: directly observed initial selection failures and multi-step state-update failures; demonstrably unspecific repair; plausible prompt/representation burdens interacting with constrained model profiles. No causal ranking among model capacity, prompt clarity and observation complexity is possible without controlled ablations. For Qwen specifically, all 22 failures happen before sequential execution can test later-plan quality.

## 13. V2 design options (design only)

### A. Prompt-only full-turn experiment

Keep observation V1, schema V1 and the full-turn contract. Add factual instructions that the first action must match the actor's supplied current options, later actions must be legal after preceding actions, and remaining AP should be used when useful while permitting empty/short/terminal plans. V1 already explains sequential execution and costs; the intervention should tighten the first-action membership and useful-AP language, not claim to introduce missing sequential rules. Do not encode priorities, desired probe outcomes, heuristic examples or rewards for merely spending five AP.

Pros: smallest interpretable intervention; directly targets Qwen's ignored empty Attack lists and normal probe early stopping. Cons: cannot give the model an exact simulator, and both model capacity and representation burden remain. Preserve existing repair wording to avoid a second variable.

### B. Compact observation, same full-turn plan

Create a lossless factual model-facing `arena-observation-v2`: class metadata once, compact board encoding, separate state from class facts, omit redundant ownership and empty enemy action arrays where unambiguous, and keep actor ownership explicit. Preserve complete legal options, ranges and costs without ranking or pruning. Avoid removing all enemy ability information just because it is not the enemy's turn. An adapter should decode to equivalent facts, with exact option-set equivalence and deterministic canonical hashes.

Pros: addresses measured board/unit repetition and actor cross-referencing. Cons: a representation change has many coupled details; fewer bytes may mean less readable data. Freeze the specification before testing. Keep A's prompt semantics fixed and use one fixed prompt compatible with both representations, recording any unavoidable syntax adjustment separately. Do not claim an observation-only comparison if instructional semantics also change.

### C. Action-catalog output

Assign deterministic observation-local candidate IDs to legal `(actor,type,target)` actions. A first-action-only catalog can eliminate ID/coordinate reconstruction for that choice; a hybrid schema could use a catalog ID first and ordinary actions for later steps. It still asks the model to simulate later legality and has a more complex mixed output schema.

A static starting-state catalog is insufficient for a general full-turn plan: movement enables attacks and new destinations, revival enables actors, pushing changes range, damage enables Finish. Repeating a initially legal ID can also become illegal. Broad semantic templates cover later actions but lose the “catalog means legal” guarantee. A dynamic catalog requires executing or simulating between choices, or enumerating a state-dependent tree; that is an additional control/compute contract, not a free representation change.

Pros: clean candidate selection when limited to one state. Cons: catalog size, ID staleness and later-action coverage. Best evaluated as a schema ablation within an already-established stepwise mode, or explicitly as a first-action hybrid; do not casually replace full-turn output with a list of starting-state IDs. A genuinely changed logical output requires `arena-turn-plan-schema-v2` (or a separately named step-action schema).

### D. Separate stepwise mode

Observe → choose one action → execute → observe again until AP exhausted, terminal, explicit stop or bounded failure. First compare with the same observation representation and action fields, changing only the one-action control protocol; do not simultaneously introduce catalogs. Record `arena-control-stepwise-v1`, distinct from `arena-control-full-turn-v1`.

This asks whether the model chooses good tactics with authoritative feedback between actions, rather than whether it plans a whole turn. Legality may improve, but there is no guarantee it stops choosing initially illegal actions. A five-AP turn can require up to five action requests instead of one, plus a bounded explicit-stop or repair policy. Specify invalid-choice behavior, request cap and remaining-AP stop semantics before any run; do not allow unlimited retries. Measure latency and tokens per turn and match as well as per request. The changed sampling/control methodology warrants `arena-benchmark-v2`; unchanged probe states can remain `arena-probes-v1`.

### E. Full-turn plan with replan on execution rejection

Commit the successful prefix; on invalid action request a new plan using updated state and remaining AP. Bound replans per turn (for example one), forbid replaying the committed prefix, and end the turn if the replan also fails. Use `arena-control-replan-v1` and separately declared methodology. This tests adaptive recovery, not V1 static repair or one-shot planning. Pros: feedback only when needed; cons: mixes full-turn planning with variable extra inference, affects latency and can mask initial failure unless first-pass metrics remain primary. Evaluate after A and D, not bundled into either.

## 14. Recommended experiment matrix and next experiment

The following are proposed studies, not implemented versions or authorized live runs. Freeze each cell's inputs, manifests, decision rules and request budget before collection.

| Order / study | Comparator | Only meaningful intervention | Keep fixed / principal measurement |
|---|---|---|---|
| 1 / A | V1 control vs prompt V2 | System prompt wording | Both frozen models, V1 state/schema/repair/control; first-action legality + normal early stops |
| 2 / B | Selected fixed full-turn prompt on observation V1 vs V2 | Observation representation | Same models/schema/control/repair; legality, AP, outcome, input size |
| 3 / D | Chosen full-turn cell vs stepwise cell | Feedback/control granularity | Same state representation/action fields/profile; decision quality, failures, per-turn cost |
| 4 / C (optional) | Fixed stepwise cell without vs with candidate IDs | Action representation | Same state information/control; ID/legality errors and token costs |
| 5 / E (optional) | Fixed full-turn cell vs bounded replan cell | Recovery policy | Same profile/prompt/observation; first-pass quality and recovery separately |
| Later model axis | Same fixed cell on Qwen 4B vs another local model | Model capability/profile | Keep contract/prompts/states; new explicit model profile, never coupled to A/B |

**First experiment specification:** retain Qwen 4B as the constrained baseline and Luna as a second fixed profile; compare system prompt V1 with a short, preregistered prompt V2 patch. Start with the unchanged seven probes and their existing intended-attempt structure. Include all intended attempts in static-validity/completion denominators and keep preflights separate. Retain fail-fast collection behavior and existing one-repair policy; no provider fallback or dynamic retry. Avoid repeatedly revising the prompt after inspecting the same probe outcomes.

Because probes do not capture the empty-Attack-list opening failure, a later frozen diagnostic state suite should also include saved full-match starting observations and a held-out subset of saved later states. Give that *new methodology/suite* its own ID and label it diagnostic replay-state planning, not a V1 full-match result. Present the original probe comparison separately so this addition cannot masquerade as an unchanged benchmark. This is a proposal for subsequent separately authorized inference, not work performed here.

Primary readouts: static acceptance; first-action membership and dynamic legality; exact initial-vs-later failure categories; executed AP and planned/executed gap; normal provider stops with useful options remaining versus executor-forced stops; probe terminal outcomes. Secondary: full-turn execution validity, damage/Core outcomes, repair success and token/latency cost. Report intention-to-test denominators and accepted-plan denominators side by side; don't reward useless AP expenditure. Improvement must preserve tactical outcomes and repair reliability, not merely generate longer plans.

Before authorizing full matches, require demonstrated executable opening behavior and no unresolved static-contract defect in the scoped diagnostics, with the exact gate set in advance. Then use the same four intended matches and side assignments against heuristic for each compared cell, rather than run Qwen–Luna now. This document sets no live budget or authorization. A null result for A is useful evidence to proceed to B; it is not permission for unlimited prompt tuning.

Keep local model upgrades a later independent axis: current Qwen 4B, a larger Qwen or locally available Gemma-class candidate only after availability/memory feasibility is established in a separate task. No model inventory or GPU capacity claim is made here; no profiles changed.

### Version IDs and the frozen recipe caveat

For A, the only new **model-facing version** should be `arena-turn-prompt-v2`. Keep `arena-observation-v1`, `arena-turn-plan-schema-v1`, `qwen-config-v1`, `luna-config-v1`, rules/scenario, heuristic and unchanged probe-state IDs. Do not add a plan-schema V2 merely because a prompt changed.

There is an implementation caveat: the immutable `arena-benchmark-v1.json` embeds `prompt: arena-turn-prompt-v1`, and current benchmark/provider wiring uses module-level prompt constants. It is not already a generic configurable V2 runner. Future implementation must preserve its bytes and truthfully record a separate experiment manifest (proposed `arena-experiment-prompt-ablation-v1`) referencing V1 methodology plus the explicit prompt override. Do not silently relabel a V2-prompt run as the exact frozen V1 recipe. If the future manifest cannot distinguish recipe from methodology, use a distinct experiment recipe ID; this alone does not require changing benchmark methodology.

For B, introduce `arena-observation-v2`; preserve the logical plan schema and model profiles. The frozen probe artifact includes V1 observation hashes as well as state hashes: keep it immutable, retain state-set identity, and store V2 observation hashes separately under their observation version. Do not overwrite expected hashes or create `arena-probes-v2` unless the actual probe states change.

For D/E, methodology changes (request opportunities, feedback, recovery, cost denominators), so `arena-benchmark-v2` is warranted with explicit control-mode IDs and manifests. Reserve `arena-turn-plan-schema-v2` for actual logical full-turn output changes (e.g. C's hybrid catalog); a separate one-action protocol may instead use `arena-step-action-schema-v1`. Reserve a separate version for targeted repair feedback, proposed `arena-repair-feedback-v2`, only when that later intervention is actually implemented.

**Preserve forever:** `arena-turn-prompt-v1`, `arena-observation-v1`, `arena-turn-plan-schema-v1`, `arena-benchmark-v1`, `arena-probes-v1`, `arena-heuristic-probes-v1`, `arena-heuristic-v1`, `qwen-config-v1`, `luna-config-v1`, existing engine/scenario versions and all V1 live evidence. Future source/experiment hashes should change honestly with future implementations; nothing is retroactively rebased. The IDs in this section are proposals, not registry entries created by this task.

## 15. Deliverables and verification

Created `docs/arena-v1-postmortem.md` and the three local analysis/support outputs linked above. No runtime, provider, prompt, schema, model profile or frozen artifact was modified. No V2 implementation, live inference, provider preflight, network connectivity probe, model restart, model inventory query, or Qwen–Luna match occurred. Work stops at this postmortem/design recommendation.

## Appendix A. Probe row provenance

The numbered rows in section 5 map to these exact saved trial directories. Each contains observations, inference, plans, command traces and initial/final snapshots.

| Row | Saved trial directory |
|---|---|
| Q-P01 | [.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-001](../.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-001/plans.jsonl) |
| Q-P02 | [.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-002](../.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-002/plans.jsonl) |
| Q-P03 | [.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-003](../.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-003/plans.jsonl) |
| Q-P04 | [.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-004](../.local/arena-qwen-probes-retry-3/probes/finish_or_core/ollama/run-004/plans.jsonl) |
| Q-P05 | [.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-001](../.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-001/plans.jsonl) |
| Q-P06 | [.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-002](../.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-002/plans.jsonl) |
| Q-P07 | [.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-003](../.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-003/plans.jsonl) |
| Q-P08 | [.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-004](../.local/arena-qwen-probes-retry-3/probes/fireball_friendly_fire/ollama/run-004/plans.jsonl) |
| Q-P09 | [.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-001](../.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-001/plans.jsonl) |
| Q-P10 | [.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-002](../.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-002/plans.jsonl) |
| Q-P11 | [.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-003](../.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-003/plans.jsonl) |
| Q-P12 | [.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-004](../.local/arena-phase5-continuation-20260913/ollama-shield_bash_position-continuation-1/probes/shield_bash_position/ollama/run-004/plans.jsonl) |
| Q-P13 | [.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-001](../.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-001/plans.jsonl) |
| Q-P14 | [.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-002](../.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-002/plans.jsonl) |
| Q-P15 | [.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-003](../.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-003/plans.jsonl) |
| Q-P16 | [.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-004](../.local/arena-phase5-continuation-20260913/ollama-snipe_vs_basic-continuation-1/probes/snipe_vs_basic/ollama/run-004/plans.jsonl) |
| Q-P17 | [.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-001](../.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-001/plans.jsonl) |
| Q-P18 | [.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-002](../.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-002/plans.jsonl) |
| Q-P19 | [.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-003](../.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-003/plans.jsonl) |
| Q-P20 | [.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-004](../.local/arena-phase5-continuation-20260913/ollama-team_elimination-continuation-1/probes/team_elimination/ollama/run-004/plans.jsonl) |
| Q-P21 | [.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-001](../.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-001/plans.jsonl) |
| Q-P22 | [.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-002](../.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-002/plans.jsonl) |
| Q-P23 | [.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-003](../.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-003/plans.jsonl) |
| Q-P24 | [.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-004](../.local/arena-phase5-continuation-20260913/ollama-winning_core_line-continuation-1/probes/winning_core_line/ollama/run-004/plans.jsonl) |

## Appendix B. Every Luna full-match execution truncation

All indices below are zero-based. “Initial legal” means the exact actor/type/target action was in starting legal enumeration and passed the starting-state command validator. “No” actions never became legal anywhere in their executed prefix. Abbreviations map to the exact engine reasons in section 6. Full-match paths resolve beneath `.local/arena-phase5-fullmatches-20260913-01/{match}/runs/run-001/`; plan numbers index saved plan/inference rows for these accepted prefixes.

| Match | Plan | Index | Rejected action | Reason | Initial legal |
|---|---|---|---|---|---|
| luna-self/match-01 | 2 | 1 | red-knight attack blue-ranger | range | no |
| luna-self/match-01 | 3 | 2 | blue-mage fireball {'x': 6, 'y': 2} | Fireball range/board | no |
| luna-self/match-01 | 4 | 2 | red-knight shield_bash blue-ranger | target status | yes |
| luna-self/match-01 | 5 | 1 | blue-mage fireball {'x': 6, 'y': 2} | Fireball range/board | no |
| luna-self/match-01 | 6 | 1 | red-mage fireball {'x': 3, 'y': 2} | Fireball range/board | no |
| luna-self/match-01 | 9 | 1 | blue-knight shield_bash red-cleric | range | no |
| luna-self/match-01 | 10 | 2 | red-mage fireball {'x': 4, 'y': 2} | Fireball range/board | no |
| luna-self/match-01 | 16 | 1 | red-cleric attack blue-knight | target status | yes |
| luna-self/match-01 | 17 | 2 | blue-cleric attack red-cleric | target status | yes |
| luna-self/match-01 | 18 | 3 | red-knight attack blue-cleric | range | no |
| luna-self/match-01 | 19 | 1 | blue-cleric attack red-mage | target status | yes |
| luna-self/match-02 | 1 | 2 | blue-mage fireball {'x': 6, 'y': 1} | Fireball range/board | no |
| luna-self/match-02 | 2 | 1 | red-knight attack blue-ranger | range | no |
| luna-self/match-02 | 3 | 2 | blue-mage fireball {'x': 7, 'y': 2} | Fireball range/board | no |
| luna-self/match-02 | 4 | 2 | red-knight shield_bash blue-ranger | target status | yes |
| luna-self/match-02 | 5 | 2 | blue-knight move {'x': 3, 'y': 2} | move destination | yes |
| luna-self/match-02 | 8 | 2 | red-mage attack blue-mage | target status | yes |
| luna-self/match-02 | 9 | 1 | blue-knight move {'x': 4, 'y': 2} | move destination | no |
| luna-self/match-02 | 10 | 1 | red-mage finish blue-mage | actor inactive | yes |
| luna-self/match-02 | 11 | 1 | blue-knight attack red-cleric | range | no |
| luna-self/match-02 | 12 | 1 | red-ranger snipe blue-knight | range | no |
| luna-self/match-02 | 13 | 1 | blue-knight shield_bash red-cleric | range | no |
| luna-self/match-02 | 14 | 2 | red-ranger attack blue-knight | range | no |
| luna-self/match-02 | 15 | 1 | blue-cleric revive blue-mage | LOS | no |
| luna-self/match-02 | 16 | 2 | red-knight attack blue-knight | range | no |
| luna-self/match-02 | 17 | 2 | blue-knight move {'x': 5, 'y': 2} | move destination | no |
| luna-self/match-02 | 18 | 2 | red-knight move {'x': 5, 'y': 2} | move destination | no |
| luna-self/match-02 | 19 | 0 | blue-cleric revive blue-knight | LOS | no |
| luna-self/match-02 | 20 | 2 | red-ranger attack blue-core | range | no |
| luna-self/match-02 | 21 | 4 | blue-cleric move {'x': 8, 'y': 2} | move destination | no |
| luna-self/match-03 | 2 | 1 | red-cleric revive red-ranger | range | no |
| luna-self/match-03 | 4 | 2 | red-knight attack blue-ranger | target status | no |
| luna-self/match-03 | 5 | 1 | blue-knight attack red-mage | range | no |
| luna-self/match-03 | 6 | 0 | red-mage fireball {'x': 1, 'y': 2} | Fireball range/board | no |
| luna-self/match-03 | 7 | 1 | blue-knight attack red-core | range | no |
| luna-self/match-03 | 8 | 1 | red-knight attack blue-knight | range | no |
| luna-self/match-03 | 9 | 2 | blue-knight move {'x': 3, 'y': 2} | move destination | yes |
| luna-self/match-03 | 10 | 1 | red-cleric revive red-ranger | range | no |
| luna-self/match-03 | 11 | 2 | blue-cleric revive blue-mage | LOS | no |
| luna-self/match-03 | 12 | 1 | red-knight attack blue-knight | range | no |
| luna-self/match-03 | 13 | 1 | blue-knight move {'x': 4, 'y': 2} | move destination | no |
| luna-self/match-03 | 14 | 0 | red-mage fireball {'x': 3, 'y': 2} | Fireball range/board | no |
| luna-self/match-03 | 15 | 2 | blue-knight move {'x': 4, 'y': 1} | move destination | no |
| luna-self/match-03 | 16 | 1 | red-knight finish blue-mage | range | no |
| luna-self/match-03 | 17 | 0 | blue-cleric revive blue-mage | LOS | no |
| luna-self/match-03 | 18 | 1 | red-cleric revive red-ranger | range | no |
| luna-self/match-03 | 19 | 2 | blue-cleric revive blue-mage | LOS | no |
| luna-self/match-03 | 20 | 1 | red-knight attack blue-knight | range | no |
| luna-self/match-03 | 21 | 3 | blue-cleric revive blue-ranger | LOS | no |
| luna-self/match-04 | 1 | 2 | blue-mage fireball {'x': 7, 'y': 2} | Fireball range/board | no |
| luna-self/match-04 | 2 | 1 | red-knight attack blue-ranger | range | no |
| luna-self/match-04 | 3 | 2 | blue-mage fireball {'x': 7, 'y': 2} | Fireball range/board | no |
| luna-self/match-04 | 4 | 2 | red-knight shield_bash blue-ranger | target status | yes |
| luna-self/match-04 | 5 | 1 | blue-mage fireball {'x': 7, 'y': 2} | Fireball range/board | no |
| luna-self/match-04 | 6 | 1 | red-mage fireball {'x': 3, 'y': 2} | Fireball range/board | no |
| luna-self/match-04 | 9 | 2 | blue-cleric revive blue-mage | LOS | no |
| luna-self/match-04 | 11 | 2 | blue-knight move {'x': 6, 'y': 2} | move destination | no |
| luna-self/match-04 | 12 | 1 | red-cleric attack blue-cleric | target status | yes |
| luna-self/match-04 | 13 | 0 | blue-knight move {'x': 6, 'y': 2} | move destination | no |
| luna-self/match-04 | 14 | 3 | red-cleric revive red-ranger | range | no |
| luna-vs-heuristic/match-01 | 1 | 2 | blue-mage fireball {'x': 7, 'y': 2} | Fireball range/board | no |
| luna-vs-heuristic/match-01 | 5 | 3 | blue-mage fireball {'x': 6, 'y': 2} | Fireball range/board | no |
| luna-vs-heuristic/match-01 | 7 | 2 | blue-cleric revive blue-ranger | range | no |
| luna-vs-heuristic/match-01 | 9 | 2 | blue-mage attack red-ranger | target status | yes |
| luna-vs-heuristic/match-01 | 11 | 2 | blue-mage attack red-cleric | target status | yes |
| luna-vs-heuristic/match-02 | 2 | 2 | red-mage fireball {'x': 1, 'y': 2} | Fireball range/board | no |
| luna-vs-heuristic/match-02 | 4 | 0 | red-ranger snipe blue-ranger | LOS | no |
| luna-vs-heuristic/match-03 | 1 | 2 | blue-mage fireball {'x': 7, 'y': 2} | Fireball range/board | no |
| luna-vs-heuristic/match-03 | 5 | 2 | blue-mage move {'x': 3, 'y': 3} | move destination | no |
| luna-vs-heuristic/match-03 | 7 | 2 | blue-cleric revive blue-ranger | range | no |
| luna-vs-heuristic/match-04 | 2 | 1 | red-ranger snipe blue-ranger | LOS | no |
| luna-vs-heuristic/match-04 | 4 | 1 | red-cleric revive red-knight | range | no |
