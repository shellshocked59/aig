# Arena Phase 9C: expanded Qwen action-ID tactical baseline

Action-ID retained perfect observed validity and replay, but the Revive pilot failure reproduced in all four expanded trials. This matches interpretation B: mechanical validity is preserved on these probes while tactical outcomes regress on Revive. Do not progress immediately to full matches before understanding that tradeoff.

This is a fresh, balanced 28-turn dataset (seven frozen probes × four intended trials), separate from the seven-turn pilot. Only Qwen/Ollama ran. No preflight, replacement trial, Luna inference, full match, ranking, tuning, or profile change occurred.

## Authorization, source freeze, and verification

Git SHA `794fca9f46cbfe93d9406200c824033a59b7e812`; dirty workspace: **True**, including pre-existing implementation work. Frozen backend source manifest: `bd34a1c532b7aad331756d84c713dee2a1b7eb46b012461647adb256b8e8c802`. Git SHA alone does not identify the uncommitted source bytes.

The original command was rejected before inference because the runner required its 280-request theoretical maximum to fit the ceiling. The user then explicitly authorized correcting and validating the two runner behaviors: allow a smaller runtime cap, and continue independent intended trials after ordinary failed selections/provider calls. The 180-request cap was retained. Unknown/integrity errors stop the schedule; exhausted budget preserves a partial turn and prevents later trials. No model-facing or gameplay behavior changed.

The revision is recorded as `orchestrationPolicy=phase9c-bounded-independent-trials-v1` alongside the unchanged frozen contracts. `arena-benchmark-v4` artifact bytes were not redefined. Only `backend/aig/arena/action_id_benchmark.py` changed in backend source; tests were updated. All 31 action-ID tests passed before freezing, including runtime ceiling, failed repair continuation, source/provenance/accounting hard stops, catalog checks, and exact replay. An earlier test invocation caught a source edit during testing; the fixed-source rerun passed.

All 7,500 inventoried pre-existing evidence files retained their exact hashes. Backend source, auxiliary source/tests, and settings match the pre-live inventory. Per-request source guards and per-turn replay/purity/accounting checks were active. Offline verification independently rebuilt every action-ID catalog and replayed all 28 turns, then reverified all 28 historical structured turns. Hash guards detect edits but are not an atomic filesystem lock.

The read-only Ollama `/api/version` check encountered sandbox WinError 10013; the escalated check returned HTTP 200, Ollama 0.34.0. The authorized live command used that permitted network context. These GET checks were not inference requests.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.action_id_benchmark --provider ollama --probe all --probe-trials 4 --request-ceiling 180 --output .local/arena-phase9c-qwen-action-id-expanded-01
```

| Contract | Structured baseline | Action-ID |
| --- | --- | --- |
| controlVersion | arena-control-stepwise-v1 | arena-control-stepwise-action-id-v1 |
| observationVersion | arena-observation-v2 | arena-observation-v3 |
| promptVersion | arena-step-prompt-v1 | arena-step-prompt-v2 |
| planSchemaVersion | arena-turn-plan-schema-v1 | arena-step-action-id-schema-v1 |
| repairVersion | — | arena-action-id-repair-v1 |
| benchmarkVersion | arena-benchmark-v2 | arena-benchmark-v4 |
| probeSetVersion | arena-probes-v1 | arena-probes-v1 |
| environmentVersion | arena-rules-v2 | arena-rules-v2 |
| scenarioVersion | arena-scenario-v1 | arena-scenario-v1 |

Qwen profile remained `qwen-config-v1`: `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M`, context 4096, max output 256, temperature 0, seed 42, think/stream false. Model configuration and every matched initial probe snapshot were verified equal across datasets.

## Reliability and AP

| Metric | Structured / 28 turns | Action-ID / 28 turns |
| --- | --- | --- |
| Completed / failed | 28 / 0 | 28 / 0 |
| First responses | 100 | 100 |
| Schema-valid first responses | 100/100 (100.0%) | 100/100 (100.0%) |
| Valid current choice on first response | 100/100 (100.0%) | 100/100 (100.0%) |
| invalid_action_id events | not applicable | 0 |
| Repairs attempted / succeeded / failed | 0 / 0 / 0 | 0 / 0 / 0 |
| Provider failures | 0 | 0 |
| Authoritative execution failures | 0 | 0 |
| Exact command replays | 28 | 28 |
| Trial requests (incl. repairs) | 100 | 100 / 180 |
| Separate historical preflight | 1 | 0 |
| AP mean / median | 4.000 / 5.0 | 4.000 / 5.0 |
| AP min / max | 1 / 5 | 1 / 5 |
| Mean unused AP | 1 | 1 |
| Full 5 AP | 16/28 (57.1%) | 16/28 (57.1%) |
| At least 4 AP | 20/28 (71.4%) | 20/28 (71.4%) |
| At most 2 AP | 4/28 (14.3%) | 4/28 (14.3%) |
| Zero-action turns | 0/28 (0.0%) | 0/28 (0.0%) |
| Explicit EndTurn | 0/28 (0.0%) | 0/28 (0.0%) |
| AP abandoned by explicit EndTurn | 0 | 0 |
| Decisions mean / median | 3.571 / 4.0 | 3.571 / 3.0 |
| Decisions min / max | 1 / 5 | 1 / 5 |
| Decisions per AP | 0.893 | 0.893 |

Matching 100% validity does not establish a reliability improvement over the already-perfect structured baseline. No repairs occurred, so repair success under live conditions remains unmeasured. All actual providers matched Ollama, with zero fallback. All unused AP was left after terminal victories; no explicit EndTurn abandoned AP. No rejected-ID/repair or early-EndTurn records exist in this run.

## All seven probes and per-trial outcomes

| Probe | Structured wins / 4 | ID wins / 4 | Structured objective / 4 | ID objective / 4 | ID terminal mechanisms |
| --- | --- | --- | --- | --- | --- |
| finish_or_core | 4 | 4 | not defined | not defined | {'core_destruction': 4} |
| fireball_friendly_fire | 4 | 4 | not defined | not defined | {'team_elimination': 4} |
| revive_decision | 4 | 0 | 4 | 0 | {'nonterminal': 4} |
| shield_bash_position | 4 | 4 | not defined | not defined | {'team_elimination': 4} |
| snipe_vs_basic | 0 | 0 | not defined | not defined | {'nonterminal': 4} |
| team_elimination | 4 | 4 | 4 | 4 | {'team_elimination': 4} |
| winning_core_line | 4 | 4 | 4 | 4 | {'team_elimination': 4} |

The frozen winning-core objective means victory; a team-elimination win does not demonstrate Core targeting. Ability-use counts and objective success remain distinct.

| Probe | Damage per trial: structured / ID | Downs: structured / ID | AP: structured / ID |
| --- | --- | --- | --- |
| finish_or_core | 30 / 30 | 0 / 0 | 5 / 5 |
| fireball_friendly_fire | 27 / 27 | 2 / 2 | 5 / 5 |
| revive_decision | 18 / 15 | 1 / 0 | 5 / 5 |
| shield_bash_position | 18 / 18 | 1 / 1 | 3 / 3 |
| snipe_vs_basic | 18 / 21 | 1 / 1 | 5 / 5 |
| team_elimination | 6 / 6 | 1 / 1 | 1 / 1 |
| winning_core_line | 18 / 18 | 1 / 1 | 4 / 4 |

Within each dataset, these mechanical outcomes were identical across all four trials of each probe. Damage includes Core damage. Snipe selected a different first target and dealt 21 rather than 18 total damage; Revive dealt 15 rather than 18 and downed no enemy. Winning Core used Attack → Snipe → Attack instead of four Attacks, while retaining a team-elimination win. Team Elimination won immediately with one Attack in all trials and used no Finish.

### finish_or_core

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A01, A01, A01, A01, A01 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | 5 | True / core_destruction | — |
| 2 | A01, A01, A01, A01, A01 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | 5 | True / core_destruction | — |
| 3 | A01, A01, A01, A01, A01 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | 5 | True / core_destruction | — |
| 4 | A01, A01, A01, A01, A01 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | 5 | True / core_destruction | — |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 5 | 30 | 0 / 0 | 0 / 0 | none | actor: active 18; body: downed 0; enemy: active 11 |
| 2 | 0 / 5 | 30 | 0 / 0 | 0 / 0 | none | actor: active 18; body: downed 0; enemy: active 11 |
| 3 | 0 / 5 | 30 | 0 / 0 | 0 / 0 | none | actor: active 18; body: downed 0; enemy: active 11 |
| 4 | 0 / 5 | 30 | 0 / 0 | 0 / 0 | none | actor: active 18; body: downed 0; enemy: active 11 |

Historical structured modal resolved sequence: attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core).

### fireball_friendly_fire

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A01, A01, A01, A47, A22 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(ally → enemy2); attack(ally → enemy2) | 5 | True / team_elimination | — |
| 2 | A01, A01, A01, A47, A22 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(ally → enemy2); attack(ally → enemy2) | 5 | True / team_elimination | — |
| 3 | A01, A01, A01, A47, A22 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(ally → enemy2); attack(ally → enemy2) | 5 | True / team_elimination | — |
| 4 | A01, A01, A01, A47, A22 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(ally → enemy2); attack(ally → enemy2) | 5 | True / team_elimination | — |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 0 | 0 | 27 / 0 | 2 / 0 | none | actor: active 9; ally: active 18; enemy: downed 0; enemy2: downed 0 |
| 2 | 0 / 0 | 0 | 27 / 0 | 2 / 0 | none | actor: active 9; ally: active 18; enemy: downed 0; enemy2: downed 0 |
| 3 | 0 / 0 | 0 | 27 / 0 | 2 / 0 | none | actor: active 9; ally: active 18; enemy: downed 0; enemy2: downed 0 |
| 4 | 0 / 0 | 0 | 27 / 0 | 2 / 0 | none | actor: active 9; ally: active 18; enemy: downed 0; enemy2: downed 0 |

Fireball usage: **0/4**. Fireball target, friendly/enemy hits, Fireball damage, and Fireball downs are therefore not applicable (zero uses), rather than evidence of successful Fireball targeting. All selected basic attacks and their follow-up order are listed above; step-level damage/downs are in analysis.json.
Historical structured modal resolved sequence: attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2).

### revive_decision

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A01, A01, A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 5 | False / nonterminal | False |
| 2 | A01, A01, A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 5 | False / nonterminal | False |
| 3 | A01, A01, A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 5 | False / nonterminal | False |
| 4 | A01, A01, A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 5 | False / nonterminal | False |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 0 | 0 | 15 / 0 | 0 / 0 | none | actor: active 11; ally: downed 0; enemy: active 3 |
| 2 | 0 / 0 | 0 | 15 / 0 | 0 / 0 | none | actor: active 11; ally: downed 0; enemy: active 3 |
| 3 | 0 / 0 | 0 | 15 / 0 | 0 / 0 | none | actor: active 11; ally: downed 0; enemy: active 3 |
| 4 | 0 / 0 | 0 | 15 / 0 | 0 / 0 | none | actor: active 11; ally: downed 0; enemy: active 3 |

Revive was used in **0/4** trials. No Cleric/target pair was selected for revival. In every trial the Cleric `actor` attacked `enemy` five times; `ally` remained DOWNED. The historical structured sequence revived `ally` using `actor`, then used the revived ally for follow-up attacks and won. Structured expanded: **4/4**; action-ID pilot: **0/1**; action-ID expanded: **0/4**. The observed pilot failure reproduced under the fixed configuration.
Historical structured modal resolved sequence: revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy).

### shield_bash_position

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 3 | True / team_elimination | — |
| 2 | A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 3 | True / team_elimination | — |
| 3 | A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 3 | True / team_elimination | — |
| 4 | A01, A01, A01 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | 3 | True / team_elimination | — |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 18; enemy: downed 0 |
| 2 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 18; enemy: downed 0 |
| 3 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 18; enemy: downed 0 |
| 4 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 18; enemy: downed 0 |

Shield Bash usage: **0/4**. No target, push, or premium displacement was selected. The next fresh-state decisions were basic attacks as listed above. This probe won without demonstrating Shield Bash use.
Historical structured modal resolved sequence: attack(actor → enemy); attack(actor → enemy); attack(actor → enemy).

### snipe_vs_basic

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A24, A24, A01 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | 5 | False / nonterminal | — |
| 2 | A24, A24, A01 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | 5 | False / nonterminal | — |
| 3 | A24, A24, A01 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | 5 | False / nonterminal | — |
| 4 | A24, A24, A01 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | 5 | False / nonterminal | — |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 0 | 0 | 21 / 0 | 1 / 0 | none | actor: active 10; enemy: downed 0; enemy2: active 5 |
| 2 | 0 / 0 | 0 | 21 / 0 | 1 / 0 | none | actor: active 10; enemy: downed 0; enemy2: active 5 |
| 3 | 0 / 0 | 0 | 21 / 0 | 1 / 0 | none | actor: active 10; enemy: downed 0; enemy2: active 5 |
| 4 | 0 / 0 | 0 | 21 / 0 | 1 / 0 | none | actor: active 10; enemy: downed 0; enemy2: active 5 |


| Trial | Snipe | Attack | Move |
| --- | --- | --- | --- |
| 1 | 2 | 1 | 0 |
| 2 | 2 | 1 | 0 |
| 3 | 2 | 1 | 0 |
| 4 | 2 | 1 | 0 |

Historical structured modal resolved sequence: snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2).

### team_elimination

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A01 | attack(actor → enemy) | 1 | True / team_elimination | True |
| 2 | A01 | attack(actor → enemy) | 1 | True / team_elimination | True |
| 3 | A01 | attack(actor → enemy) | 1 | True / team_elimination | True |
| 4 | A01 | attack(actor → enemy) | 1 | True / team_elimination | True |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 0 | 0 | 6 / 0 | 1 / 0 | none | actor: active 18; body: downed 0; enemy: downed 0 |
| 2 | 0 / 0 | 0 | 6 / 0 | 1 / 0 | none | actor: active 18; body: downed 0; enemy: downed 0 |
| 3 | 0 / 0 | 0 | 6 / 0 | 1 / 0 | none | actor: active 18; body: downed 0; enemy: downed 0 |
| 4 | 0 / 0 | 0 | 6 / 0 | 1 / 0 | none | actor: active 18; body: downed 0; enemy: downed 0 |

Historical structured modal resolved sequence: attack(actor → enemy).

### winning_core_line

| Trial | IDs | Resolved actions | AP | Victory / terminal | Objective |
| --- | --- | --- | --- | --- | --- |
| 1 | A01, A35, A01 | attack(actor → enemy); snipe(actor → enemy); attack(actor → enemy) | 4 | True / team_elimination | True |
| 2 | A01, A35, A01 | attack(actor → enemy); snipe(actor → enemy); attack(actor → enemy) | 4 | True / team_elimination | True |
| 3 | A01, A35, A01 | attack(actor → enemy); snipe(actor → enemy); attack(actor → enemy) | 4 | True / team_elimination | True |
| 4 | A01, A35, A01 | attack(actor → enemy); snipe(actor → enemy); attack(actor → enemy) | 4 | True / team_elimination | True |


| Trial | Finish / Core attacks | Core damage | Unit damage / friendly damage | Downs / finishes | Removed IDs | Final units (status, HP) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 10; body: downed 0; enemy: downed 0 |
| 2 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 10; body: downed 0; enemy: downed 0 |
| 3 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 10; body: downed 0; enemy: downed 0 |
| 4 | 0 / 0 | 0 | 18 / 0 | 1 / 0 | none | actor: active 10; body: downed 0; enemy: downed 0 |

Historical structured modal resolved sequence: attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy).

## Sequence variation and ID selection

| Probe | Unique ID hashes / 4 | Unique resolved hashes / 4 | Unique final states | Modal resolved frequency | Structured unique resolved / final |
| --- | --- | --- | --- | --- | --- |
| finish_or_core | 1 | 1 | 1 | 4/4 | 1 / 1 |
| fireball_friendly_fire | 1 | 1 | 1 | 4/4 | 1 / 1 |
| revive_decision | 1 | 1 | 1 | 4/4 | 1 / 1 |
| shield_bash_position | 1 | 1 | 1 | 4/4 | 1 / 1 |
| snipe_vs_basic | 1 | 1 | 1 | 4/4 | 1 / 1 |
| team_elimination | 1 | 1 | 1 | 4/4 | 1 / 1 |
| winning_core_line | 1 | 1 | 1 | 4/4 | 1 / 1 |

Each per-probe modal resolved sequence is shown in the trial tables above; full sequence hashes and frequencies are in analysis.json. Explicit EndTurn, if present, is included as null in sequence hashes. ID strings are local to their current catalogs and are not global action names.

| Probe / trial | Catalog sizes by step | Selected ordinals (1-based) |
| --- | --- | --- |
| finish_or_core / 1 | 19, 19, 19, 19, 19 | 1, 1, 1, 1, 1 |
| finish_or_core / 2 | 19, 19, 19, 19, 19 | 1, 1, 1, 1, 1 |
| finish_or_core / 3 | 19, 19, 19, 19, 19 | 1, 1, 1, 1, 1 |
| finish_or_core / 4 | 19, 19, 19, 19, 19 | 1, 1, 1, 1, 1 |
| fireball_friendly_fire / 1 | 70, 70, 70, 68, 43 | 1, 1, 1, 47, 22 |
| fireball_friendly_fire / 2 | 70, 70, 70, 68, 43 | 1, 1, 1, 47, 22 |
| fireball_friendly_fire / 3 | 70, 70, 70, 68, 43 | 1, 1, 1, 47, 22 |
| fireball_friendly_fire / 4 | 70, 70, 70, 68, 43 | 1, 1, 1, 47, 22 |
| revive_decision / 1 | 21, 21, 21, 21, 20 | 1, 1, 1, 1, 1 |
| revive_decision / 2 | 21, 21, 21, 21, 20 | 1, 1, 1, 1, 1 |
| revive_decision / 3 | 21, 21, 21, 21, 20 | 1, 1, 1, 1, 1 |
| revive_decision / 4 | 21, 21, 21, 21, 20 | 1, 1, 1, 1, 1 |
| shield_bash_position / 1 | 24, 24, 24 | 1, 1, 1 |
| shield_bash_position / 2 | 24, 24, 24 | 1, 1, 1 |
| shield_bash_position / 3 | 24, 24, 24 | 1, 1, 1 |
| shield_bash_position / 4 | 24, 24, 24 | 1, 1, 1 |
| snipe_vs_basic / 1 | 25, 24, 23 | 24, 24, 1 |
| snipe_vs_basic / 2 | 25, 24, 23 | 24, 24, 1 |
| snipe_vs_basic / 3 | 25, 24, 23 | 24, 24, 1 |
| snipe_vs_basic / 4 | 25, 24, 23 | 24, 24, 1 |
| team_elimination / 1 | 22 | 1 |
| team_elimination / 2 | 22 | 1 |
| team_elimination / 3 | 22 | 1 |
| team_elimination / 4 | 22 | 1 |
| winning_core_line / 1 | 35, 35, 35 | 1, 35, 1 |
| winning_core_line / 2 | 35, 35, 35 | 1, 35, 1 |
| winning_core_line / 3 | 35, 35, 35 | 1, 35, 1 |
| winning_core_line / 4 | 35, 35, 35 | 1, 35, 1 |


| Probe | First entry | First quarter | Last quarter | Mean normalized ordinal |
| --- | --- | --- | --- | --- |
| finish_or_core | 20/20 | 20/20 | 0/20 | 0.000 |
| fireball_friendly_fire | 12/20 | 12/20 | 0/20 | 0.237 |
| revive_decision | 20/20 | 20/20 | 0/20 | 0.000 |
| shield_bash_position | 12/12 | 12/12 | 0/12 | 0.000 |
| snipe_vs_basic | 4/12 | 4/12 | 8/12 | 0.653 |
| team_elimination | 4/4 | 4/4 | 0/4 | 0.000 |
| winning_core_line | 8/12 | 8/12 | 4/12 | 0.333 |

Normalized ordinal is (ordinal − 1)/(catalog size − 1), with a singleton assigned 0. These selections cluster toward the beginning in several fixtures, but ordering also groups action semantics. This descriptive evidence cannot establish tactical bias or a causal ordering effect; catalog ordering was unchanged.

## Output efficiency and input/context cost

| Metric | Structured | Action-ID |
| --- | --- | --- |
| Schema canonical UTF-8 bytes | 2567 | 125 |
| Input tokens (prompt_eval_count) | 147016 | 157312 |
| Output tokens (eval_count) | 3052 | 900 |
| Total input + output tokens | 150068 | 158212 |
| Output tokens / decision mean | 30.520 | 9 |
| Output tokens / decision median | 30.000 | 9.000 |
| Output tokens / decision min–max | 30–32 | 9–9 |
| Generated output tokens / tactical turn | 109 | 32.143 |
| Input + output tokens / tactical turn | 5359.571 | 5650.429 |
| Maximum prompt tokens | 2138 | 2645 |
| Maximum actual prompt + output occupancy | 2168 / 4096 (52.93%) | 2654 / 4096 (64.79%) |
| Minimum actual headroom, tokens | 1928 | 1442 |
| Minimum headroom reserving full 256 output tokens | 1702 | 1195 |

Output tokens fell **70.5%** on the balanced datasets; input tokens changed **+7.0%**. The structured baseline used 101 requests including its one historical preflight; matched trial comparisons exclude that preflight and use 100 requests. Different selected actions and decision counts change subsequent observations, so totals are not a pure measurement of representation overhead. Schema bytes are canonical schema size, not tokenizer counts. Live repair context was not exercised.
Total input-plus-output tokens changed **+5.4%**; the smaller output did not reduce total context traffic.

| Prompt tokens / decision | Structured | Action-ID |
| --- | --- | --- |
| min | 1094 | 1241 |
| max | 2138 | 2645 |
| mean | 1470.160 | 1573.120 |
| median | 1251.000 | 1305.000 |
| p95 | 2138 | 2645 |


| Actual prompt + output tokens / request | Structured | Action-ID |
| --- | --- | --- |
| min | 1124 | 1250 |
| max | 2168 | 2654 |
| mean | 1500.680 | 1582.120 |
| median | 1283.000 | 1314.000 |
| p95 | 2168 | 2654 |


## Latency

Durations below are seconds. Ollama duration fields were converted from nanoseconds. Decision wall time sums provider-attempt wall latencies; per-turn latency sums those decisions. No repair occurred, so decision and request denominators coincide. Local guard/controller overhead is excluded.

| Metric | Dataset | Min | Max | Mean | Median | p95 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Decision wall | Structured | 1.058 | 2.610 | 1.683 | 1.527 | 2.369 | 168.341 |
| Decision wall | Action-ID | 0.384 | 10.257 | 1.096 | 0.834 | 1.812 | 109.649 |
| Prompt evaluation | Structured | 0.131 | 1.040 | 0.298 | 0.151 | 0.987 | 29.764 |
| Prompt evaluation | Action-ID | 0.134 | 1.301 | 0.323 | 0.150 | 0.937 | 32.282 |
| Output evaluation | Structured | 0.840 | 0.930 | 0.877 | 0.872 | 0.915 | 87.662 |
| Output evaluation | Action-ID | 0.170 | 0.209 | 0.185 | 0.187 | 0.196 | 18.471 |
| Ollama total duration | Structured | 1.056 | 2.585 | 1.676 | 1.522 | 2.367 | 167.622 |
| Ollama total duration | Action-ID | 0.362 | 10.210 | 1.087 | 0.825 | 1.785 | 108.735 |


| Per-turn provider wall time | Min | Max | Mean | Median | p95 | Total |
| --- | --- | --- | --- | --- | --- | --- |
| Structured | 1.058 | 12.417 | 6.012 | 6.066 | 10.206 | 168.341 |
| Action-ID | 0.384 | 15.971 | 3.916 | 3.863 | 10.057 | 109.649 |


| Probe / trial | Structured provider seconds | ID provider seconds | ID prompt / output tokens |
| --- | --- | --- | --- |
| finish_or_core / 1 | 10.206 | 15.971 | 6254 / 45 |
| finish_or_core / 2 | 7.605 | 4.241 | 6254 / 45 |
| finish_or_core / 3 | 7.624 | 4.038 | 6254 / 45 |
| finish_or_core / 4 | 7.350 | 3.820 | 6254 / 45 |
| fireball_friendly_fire / 1 | 12.417 | 10.057 | 12407 / 45 |
| fireball_friendly_fire / 2 | 7.907 | 4.664 | 12407 / 45 |
| fireball_friendly_fire / 3 | 7.889 | 4.262 | 12407 / 45 |
| fireball_friendly_fire / 4 | 7.899 | 4.259 | 12407 / 45 |
| revive_decision / 1 | 9.314 | 7.680 | 6500 / 45 |
| revive_decision / 2 | 6.577 | 4.192 | 6500 / 45 |
| revive_decision / 3 | 6.025 | 3.919 | 6500 / 45 |
| revive_decision / 4 | 5.995 | 3.906 | 6500 / 45 |
| shield_bash_position / 1 | 5.913 | 4.180 | 3725 / 27 |
| shield_bash_position / 2 | 4.712 | 2.542 | 3725 / 27 |
| shield_bash_position / 3 | 4.285 | 2.389 | 3725 / 27 |
| shield_bash_position / 4 | 4.334 | 2.338 | 3725 / 27 |
| snipe_vs_basic / 1 | 6.396 | 4.640 | 4150 / 27 |
| snipe_vs_basic / 2 | 4.701 | 2.946 | 4150 / 27 |
| snipe_vs_basic / 3 | 4.499 | 2.519 | 4150 / 27 |
| snipe_vs_basic / 4 | 4.535 | 2.536 | 4150 / 27 |
| team_elimination / 1 | 1.899 | 1.296 | 1265 / 9 |
| team_elimination / 2 | 1.107 | 0.388 | 1265 / 9 |
| team_elimination / 3 | 1.058 | 0.398 | 1265 / 9 |
| team_elimination / 4 | 1.077 | 0.384 | 1265 / 9 |
| winning_core_line / 1 | 8.590 | 4.779 | 5027 / 27 |
| winning_core_line / 2 | 6.362 | 2.601 | 5027 / 27 |
| winning_core_line / 3 | 6.106 | 2.357 | 5027 / 27 |
| winning_core_line / 4 | 5.955 | 2.345 | 5027 / 27 |

Measured total provider latency fell 34.9%. The slowest action-ID request took 10.26s; it remains included rather than discarded as an outlier.
Historical and current runs were collected at different times, without randomized interleaving or matched cache/load state. Smaller output does not guarantee lower total latency. Prompt evaluation, model loading, service load, and differing action sequences prevent causal attribution of any latency difference to representation alone. Per-decision counts and all four latency measures are retained in decision-telemetry.tsv and analysis.json; per-turn totals are in analysis.json.

## Interpretation and stop point

The replicated evidence supports mechanical legality and exact execution on these 28 turns: every returned nonempty ID was current, every accepted action executed, and every trace replayed. It does **not** establish tactical equivalence: Revive is 0/4 versus the structured control’s 4/4. The one-trial failure was not merely an isolated observation in this expanded fixed-seed dataset. A causal claim about representation alone remains premature because prompt/observation contracts and collection time also differ; repeated deterministic fixtures are not independent samples from general gameplay.

Mean/median AP remained 4/5, and the winning-core and team-elimination victory patterns persisted. The output contract is substantially smaller, but there is no observed reliability gain over the perfect structured probe baseline. Repair behavior and long-match reliability remain untested here. Full-match testing should **not proceed immediately** until the Revive tradeoff is understood in a separately specified and authorized investigation. No further live work was performed; the remaining request allowance is unused.

## Artifacts

| Artifact | Location |
| --- | --- |
| Live immutable evidence | .local/arena-phase9c-qwen-action-id-expanded-01/summary.json |
| Detailed verified comparison | .local/arena-phase9c-live-audit-01/analysis.json |
| Decision token/latency rows | .local/arena-phase9c-live-audit-01/decision-telemetry.tsv |
| Source/settings/evidence freeze | .local/arena-phase9c-live-audit-01/before.json |
| Live evidence file hashes | .local/arena-phase9c-live-audit-01/live-evidence-inventory.json |
| Command and log | .local/arena-phase9c-live-audit-01/command.txt; cli.log |
| Authorized change and test record | .local/arena-phase9c-live-audit-01/authorized-changes.json; validation.txt |
| Offline analyzer and renderer | .local/arena-phase9c-live-audit-01/analyze.py; report.py |
| Historical structured dataset | .local/arena-phase7c-qwen-stepwise-probes-20260913-01/summary.json |
| Separate historical pilot | .local/arena-phase9b-qwen-action-id-pilot-01/summary.json |
| Pre-authorization blocker | .local/arena-phase9c-blocker-audit-01/report.md |

