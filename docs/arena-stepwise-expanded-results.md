# Arena Phase 7C: expanded stepwise tactical-probe baseline

2026-09-13. Fresh four-trial datasets; the seven-trial pilots remain separate. This report covers the authorized probe experiment only. No full matches, extra inference, tuning, or source changes were performed.

**56/56 completed valid turns; 191/562 authorized requests.** Both datasets replay exactly. The evidence supports a separately authorized stepwise full-match experiment, with material whole-turn inference overhead and the fixed-fixture limits described below.

**Authorization, freeze, and audit**

Git SHA `794fca9f46cbfe93d9406200c824033a59b7e812`; source dirty: **True**, reflecting the pre-existing Phase 7A/7B work. Backend source-manifest SHA-256 `928a39f5163f2f199b81132e74eafaef7889f71aa2926cead886d3dd398fee59` matched the pilot and stayed identical across providers. The manifest includes untracked implementation files; Git SHA alone does not identify these source bytes.

All 5,461 inventoried pre-existing files, including 5,256 historical evidence files, remained byte-identical. The `.env` was hashed without printing its contents. A source/settings watchdog ran during each CLI invocation and verified completed trial command traces. The frozen runner itself also verifies each completed turn before advancing. This external monitoring is not an atomic lock against concurrent edits; no mutation was observed.

The user explicitly accepted the frozen runner’s existing **abort-on-any-failed-trial** behavior after its difference from requested independent-trial semantics was identified. This authorization did not change source or methodology. No failed-trial retry or replacement was added. Both schedules completed, so the abort policy did not reduce this dataset.

Ollama `/api/version` was checked without inference: sandbox access failed with WinError 10013; the escalated read-only check returned HTTP 200, Ollama 0.34.0. The two live CLI schedules then used network-capable execution permissions, sequentially. Exactly one model preflight per provider is separate from trial telemetry. No pricing assumption was supplied; all dollar costs remain unset.

| Contract | Frozen version |
| --- | --- |
| Control | arena-control-stepwise-v1 |
| Prompt | arena-step-prompt-v1 |
| Observation | arena-observation-v2 |
| Schema | arena-turn-plan-schema-v1 (unchanged reuse) |
| Benchmark | arena-benchmark-v2 |
| Probes | arena-probes-v1 |
| Qwen profile | qwen-config-v1 |
| Luna profile | luna-config-v1 |

Qwen model: `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M`; context 4096, seed 42, temperature 0, max output 256, think false, stream false. Luna: `gpt-5.6-luna`; reasoning none, max output 512, transport retries 0, store false. Frozen versions, prompt/probe/recipe hashes, model configurations, and source-file hashes are recorded in every trial manifest.

**Reliability and request accounting**

| Metric | Qwen | Luna |
| --- | --- | --- |
| Requests including preflight / 281 | 101 | 90 |
| Preflight requests | 1 | 1 |
| Initial trial decision requests | 100 | 88 |
| First responses valid | 100 | 87 |
| First responses invalid | 0 | 1 |
| Repairs attempted | 0 | 1 |
| Repairs successful | 0 | 1 |
| Repairs failed | 0 | 0 |
| Failed provider decisions | 0 | 0 |
| Rejected reference/catalog attempts | 0 | 1 |
| Selected gameplay actions | 100 | 88 |
| Current-catalog legal actions | 100 | 88 |
| Authoritative execution failures | 0 | 0 |
| Fallbacks | 0 | 0 |
| Completed / 28 intended | 28 | 28 |
| Failed turns | 0 | 0 |
| Unstarted turns | 0 | 0 |
| Exact replays | 28 | 28 |
| First-response validity | 100.0% | 98.9% |
| Current-action legality | 100.0% | 100.0% |

First-response validity uses all initial trial decisions: Qwen 100/100; Luna 87/88 (98.864%). Current-action legality uses selected nonempty gameplay actions: Qwen 100/100; Luna 88/88. Explicit EndTurn is excluded. “Provider failures” counts decisions still unsuccessful after the bounded repair policy; both providers had zero transport-failure attempts. One Luna initial validation failure is counted separately, not erased by its successful repair. Preflights are excluded from tactical and trial-latency denominators.

Luna’s one repair occurred in Shield Bash Position, trial 2, step 2 (zero-based index 1), with four AP remaining after the first push. Initial response category: `invalid_reference`. The repaired response selected `move(actor → (3,2))`; it matched the current catalog and executed successfully. The frozen category can arise from reference checks or final catalog membership. Because rejected action text and the exact validation stage are not retained, a membership-only rejection count cannot be separated from other invalid-reference rejections; the identifiable combined count is one. No exact rejected actor/target or model intention is inferred. Initial request latency was 1.346s; repair latency was 1.302s. Both requests and their tokens are included in decision and turn totals.

**AP, continuation, and stopping**

| Metric | Qwen | Luna |
| --- | --- | --- |
| Mean / median AP | 4.000 / 5.0 | 4.000 / 5.0 |
| Min / max AP | 1 / 5 | 1 / 5 |
| Full 5 AP | 57.1% | 64.3% |
| At least 4 AP | 71.4% | 78.6% |
| At most 2 AP | 14.3% | 21.4% |
| Zero-action turns | 0.0% | 0.0% |
| Mean unused AP | 1 | 1 |
| Multiple-decision turns / 28 | 24 | 22 |
| Explicit early ends / 28 | 0 | 0 |
| Explicit early-end rate | 0.0% | 0.0% |
| Early ends with any legal action | 0 | 0 |
| Early ends with non-Move legal action | 0 | 0 |
| AP abandoned by explicit stopping | 0 | 0 |
| Mean decisions / turn | 3.571 | 3.143 |
| Median decisions / turn | 4.000 | 3.000 |
| Min / max decisions | 1 / 5 | 1 / 5 |
| Decisions per AP (total decisions / total AP) | 0.893 | 0.786 |

AP rates use all 28 intended turns per provider because all completed. Unused AP after a terminal victory is not explicit abandonment. “Useful actions remaining” is operationalized conservatively as at least one legal non-Move action; legality alone does not prove tactical usefulness. Any-legal-action counts are also shown so movement opportunities remain visible.

**Qwen explicit early-end records**

None.

**Luna explicit early-end records**

None.

**Action distributions**

| Action | Qwen | Luna |
| --- | --- | --- |
| move | 0 | 4 |
| attack | 88 | 45 |
| heal | 0 | 4 |
| finish | 0 | 3 |
| revive | 4 | 4 |
| shield_bash | 0 | 8 |
| snipe | 8 | 12 |
| fireball | 0 | 8 |
| end_turn | 0 | 0 |

Qwen actions by decision step (EndTurn means an explicit model decision; automatic AP-zero EndTurn is excluded):

| Step | move | attack | heal | finish | revive | shield_bash | snipe | fireball | end_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 20 | 0 | 0 | 4 | 0 | 4 | 0 | 0 |
| 2 | 0 | 20 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| 3 | 0 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Luna actions by decision step (EndTurn means an explicit model decision; automatic AP-zero EndTurn is excluded):

| Step | move | attack | heal | finish | revive | shield_bash | snipe | fireball | end_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 10 | 0 | 0 | 4 | 4 | 6 | 4 | 0 |
| 2 | 4 | 3 | 4 | 1 | 0 | 0 | 6 | 4 | 0 |
| 3 | 0 | 17 | 0 | 2 | 0 | 3 | 0 | 0 | 0 |
| 4 | 0 | 11 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 5 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**All intended turn records**

**Qwen — 28 turns**

| Probe / trial | Completed | Decisions / actions | AP available / spent / unused | Explicit stop | Terminal before AP zero | Repairs / provider failures | Outcome / terminal reason | Replay |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| finish_or_core / 1 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / core_destruction | yes |
| finish_or_core / 2 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / core_destruction | yes |
| finish_or_core / 3 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / core_destruction | yes |
| finish_or_core / 4 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / core_destruction | yes |
| fireball_friendly_fire / 1 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / team_elimination | yes |
| fireball_friendly_fire / 2 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / team_elimination | yes |
| fireball_friendly_fire / 3 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / team_elimination | yes |
| fireball_friendly_fire / 4 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / team_elimination | yes |
| revive_decision / 1 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / team_elimination | yes |
| revive_decision / 2 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / team_elimination | yes |
| revive_decision / 3 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / team_elimination | yes |
| revive_decision / 4 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / team_elimination | yes |
| shield_bash_position / 1 | yes | 3 / 3 | 5 / 3 / 2 | no | yes | 0 / 0 | None / team_elimination | yes |
| shield_bash_position / 2 | yes | 3 / 3 | 5 / 3 / 2 | no | yes | 0 / 0 | None / team_elimination | yes |
| shield_bash_position / 3 | yes | 3 / 3 | 5 / 3 / 2 | no | yes | 0 / 0 | None / team_elimination | yes |
| shield_bash_position / 4 | yes | 3 / 3 | 5 / 3 / 2 | no | yes | 0 / 0 | None / team_elimination | yes |
| snipe_vs_basic / 1 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| snipe_vs_basic / 2 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| snipe_vs_basic / 3 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| snipe_vs_basic / 4 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| team_elimination / 1 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| team_elimination / 2 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| team_elimination / 3 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| team_elimination / 4 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| winning_core_line / 1 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | True / team_elimination | yes |
| winning_core_line / 2 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | True / team_elimination | yes |
| winning_core_line / 3 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | True / team_elimination | yes |
| winning_core_line / 4 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | True / team_elimination | yes |

**Luna — 28 turns**

| Probe / trial | Completed | Decisions / actions | AP available / spent / unused | Explicit stop | Terminal before AP zero | Repairs / provider failures | Outcome / terminal reason | Replay |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| finish_or_core / 1 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| finish_or_core / 2 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| finish_or_core / 3 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| finish_or_core / 4 | yes | 5 / 5 | 5 / 5 / 0 | no | no | 0 / 0 | None / core_destruction | yes |
| fireball_friendly_fire / 1 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| fireball_friendly_fire / 2 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| fireball_friendly_fire / 3 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| fireball_friendly_fire / 4 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| revive_decision / 1 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / nonterminal | yes |
| revive_decision / 2 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / nonterminal | yes |
| revive_decision / 3 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / nonterminal | yes |
| revive_decision / 4 | yes | 4 / 4 | 5 / 5 / 0 | no | no | 0 / 0 | True / nonterminal | yes |
| shield_bash_position / 1 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | None / team_elimination | yes |
| shield_bash_position / 2 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 1 / 0 | None / team_elimination | yes |
| shield_bash_position / 3 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | None / team_elimination | yes |
| shield_bash_position / 4 | yes | 4 / 4 | 5 / 4 / 1 | no | yes | 0 / 0 | None / team_elimination | yes |
| snipe_vs_basic / 1 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| snipe_vs_basic / 2 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| snipe_vs_basic / 3 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| snipe_vs_basic / 4 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | None / nonterminal | yes |
| team_elimination / 1 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| team_elimination / 2 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| team_elimination / 3 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| team_elimination / 4 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / team_elimination | yes |
| winning_core_line / 1 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | True / core_destruction | yes |
| winning_core_line / 2 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / core_destruction | yes |
| winning_core_line / 3 | yes | 3 / 3 | 5 / 5 / 0 | no | no | 0 / 0 | True / core_destruction | yes |
| winning_core_line / 4 | yes | 1 / 1 | 5 / 1 / 4 | no | yes | 0 / 0 | True / core_destruction | yes |

**Sequence variation**

Turn-sequence hash = SHA-256 of canonical JSON for the ordered executed gameplay actions, including actor and target/position fields. Explicit stopping is reported separately. Final-state hashes include the full saved snapshot, including automatic turn-end state. Variation is descriptive, not a defect; identical outcomes here mean the same objective predicate, winner, and victory mechanism, not identical damage or positions.

Qwen

| Probe | Unique sequences / 4 | Modal frequency | Unique final states | Different sequences, same outcome | Most common sequence |
| --- | --- | --- | --- | --- | --- |
| finish_or_core | 1 | 4 | 1 | no | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) |
| fireball_friendly_fire | 1 | 4 | 1 | no | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2) |
| revive_decision | 1 | 4 | 1 | no | revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) |
| shield_bash_position | 1 | 4 | 1 | no | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) |
| snipe_vs_basic | 1 | 4 | 1 | no | snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2) |
| team_elimination | 1 | 4 | 1 | no | attack(actor → enemy) |
| winning_core_line | 1 | 4 | 1 | no | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) |

Luna

| Probe | Unique sequences / 4 | Modal frequency | Unique final states | Different sequences, same outcome | Most common sequence |
| --- | --- | --- | --- | --- | --- |
| finish_or_core | 3 | 2 | 2 | yes | attack(actor → red-core); attack(actor → red-core); finish(actor → body); attack(actor → red-core); attack(actor → red-core) |
| fireball_friendly_fire | 2 | 3 | 1 | yes | fireball(actor → (4,2)); fireball(actor → (4,2)); shield_bash(ally → enemy2) |
| revive_decision | 1 | 4 | 1 | no | revive(actor → ally); heal(actor → ally); attack(ally → enemy); attack(ally → enemy) |
| shield_bash_position | 2 | 3 | 1 | yes | shield_bash(actor → enemy); move(actor → (3,2)); attack(actor → enemy); attack(actor → enemy) |
| snipe_vs_basic | 1 | 4 | 1 | no | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) |
| team_elimination | 1 | 4 | 1 | no | attack(actor → enemy) |
| winning_core_line | 2 | 2 | 2 | yes | snipe(actor → enemy); snipe(actor → enemy); attack(actor → red-core) |

Full sequence and final-state hashes, including frequencies and each turn’s hash, are retained in `analysis.json`; all trial sequences are shown below.

**Mechanical results for the seven frozen probes**

**finish_or_core**

Qwen: 4/4 immediate wins; mean AP 5.00; terminal mechanisms {'core_destruction': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 30; total damage 30; friendly damage 0; downs 0; removed 0; core_destruction |
| 2 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 30; total damage 30; friendly damage 0; downs 0; removed 0; core_destruction |
| 3 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 30; total damage 30; friendly damage 0; downs 0; removed 0; core_destruction |
| 4 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 30; total damage 30; friendly damage 0; downs 0; removed 0; core_destruction |

| Trial | Action counts | Core attacked? |
| --- | --- | --- |
| 1 | {'attack': 5} | yes |
| 2 | {'attack': 5} | yes |
| 3 | {'attack': 5} | yes |
| 4 | {'attack': 5} | yes |

Luna: 1/4 immediate wins; mean AP 5.00; terminal mechanisms {'nonterminal': 3, 'core_destruction': 1}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(actor → red-core); attack(actor → red-core); finish(actor → body); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 24; total damage 24; friendly damage 0; downs 0; removed 1; nonterminal |
| 2 | attack(actor → red-core); finish(actor → body); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 24; total damage 24; friendly damage 0; downs 0; removed 1; nonterminal |
| 3 | attack(actor → red-core); attack(actor → red-core); finish(actor → body); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 24; total damage 24; friendly damage 0; downs 0; removed 1; nonterminal |
| 4 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) | AP 5; Core damage 30; total damage 30; friendly damage 0; downs 0; removed 0; core_destruction |

| Trial | Action counts | Core attacked? |
| --- | --- | --- |
| 1 | {'attack': 4, 'finish': 1} | yes |
| 2 | {'attack': 4, 'finish': 1} | yes |
| 3 | {'attack': 4, 'finish': 1} | yes |
| 4 | {'attack': 5} | yes |

**fireball_friendly_fire**

Qwen: 4/4 immediate wins; mean AP 5.00; terminal mechanisms {'team_elimination': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2) | AP 5; Core damage 0; total damage 27; friendly damage 0; downs 2; removed 0; team_elimination |
| 2 | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2) | AP 5; Core damage 0; total damage 27; friendly damage 0; downs 2; removed 0; team_elimination |
| 3 | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2) | AP 5; Core damage 0; total damage 27; friendly damage 0; downs 2; removed 0; team_elimination |
| 4 | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2) | AP 5; Core damage 0; total damage 27; friendly damage 0; downs 2; removed 0; team_elimination |

No Fireball used; the complete subsequent choices are shown in the sequences above.

Luna: 0/4 immediate wins; mean AP 5.00; terminal mechanisms {'nonterminal': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | fireball(actor → (4,2)); fireball(actor → (4,2)); shield_bash(ally → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 4; downs 1; removed 0; nonterminal |
| 2 | fireball(actor → (4,2)); fireball(actor → (4,2)); shield_bash(ally → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 4; downs 1; removed 0; nonterminal |
| 3 | fireball(actor → (4,2)); fireball(actor → (4,2)); attack(actor → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 4; downs 1; removed 0; nonterminal |
| 4 | fireball(actor → (4,2)); fireball(actor → (4,2)); shield_bash(ally → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 4; downs 1; removed 0; nonterminal |

| Trial / step | Target | Enemies / friendlies hit (IDs) | Enemy / friendly damage | Downs | Subsequent choices |
| --- | --- | --- | --- | --- | --- |
| 1 / 1 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | fireball(actor → (4,2)); shield_bash(ally → enemy2) |
| 1 / 2 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | shield_bash(ally → enemy2) |
| 2 / 1 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | fireball(actor → (4,2)); shield_bash(ally → enemy2) |
| 2 / 2 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | shield_bash(ally → enemy2) |
| 3 / 1 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | fireball(actor → (4,2)); attack(actor → enemy2) |
| 3 / 2 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | attack(actor → enemy2) |
| 4 / 1 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | fireball(actor → (4,2)); shield_bash(ally → enemy2) |
| 4 / 2 | {'x': 4, 'y': 2} | ['enemy', 'enemy2'] / ['ally'] | 8 / 2 | 0 | shield_bash(ally → enemy2) |

**revive_decision**

Qwen: 4/4 immediate wins; mean AP 5.00; terminal mechanisms {'team_elimination': 4}. Frozen objective successes: 4/4.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 2 | revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 3 | revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 4 | revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |

| Trial | Revive / correct Cleric / target | Final unit states | Follow-up actions |
| --- | --- | --- | --- |
| 1 | actor / True / ally | actor=active(11 HP); ally=active(5 HP); enemy=downed(0 HP) | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) |
| 2 | actor / True / ally | actor=active(11 HP); ally=active(5 HP); enemy=downed(0 HP) | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) |
| 3 | actor / True / ally | actor=active(11 HP); ally=active(5 HP); enemy=downed(0 HP) | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) |
| 4 | actor / True / ally | actor=active(11 HP); ally=active(5 HP); enemy=downed(0 HP) | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) |

Luna: 0/4 immediate wins; mean AP 5.00; terminal mechanisms {'nonterminal': 4}. Frozen objective successes: 4/4.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | revive(actor → ally); heal(actor → ally); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 12; friendly damage 0; downs 0; removed 0; nonterminal |
| 2 | revive(actor → ally); heal(actor → ally); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 12; friendly damage 0; downs 0; removed 0; nonterminal |
| 3 | revive(actor → ally); heal(actor → ally); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 12; friendly damage 0; downs 0; removed 0; nonterminal |
| 4 | revive(actor → ally); heal(actor → ally); attack(ally → enemy); attack(ally → enemy) | AP 5; Core damage 0; total damage 12; friendly damage 0; downs 0; removed 0; nonterminal |

| Trial | Revive / correct Cleric / target | Final unit states | Follow-up actions |
| --- | --- | --- | --- |
| 1 | actor / True / ally | actor=active(11 HP); ally=active(9 HP); enemy=active(6 HP) | heal(actor → ally); attack(ally → enemy); attack(ally → enemy) |
| 2 | actor / True / ally | actor=active(11 HP); ally=active(9 HP); enemy=active(6 HP) | heal(actor → ally); attack(ally → enemy); attack(ally → enemy) |
| 3 | actor / True / ally | actor=active(11 HP); ally=active(9 HP); enemy=active(6 HP) | heal(actor → ally); attack(ally → enemy); attack(ally → enemy) |
| 4 | actor / True / ally | actor=active(11 HP); ally=active(9 HP); enemy=active(6 HP) | heal(actor → ally); attack(ally → enemy); attack(ally → enemy) |

**shield_bash_position**

Qwen: 4/4 immediate wins; mean AP 3.00; terminal mechanisms {'team_elimination': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 3; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 2 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 3; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 3 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 3; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 4 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 3; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |

No Shield Bash used.

Luna: 4/4 immediate wins; mean AP 4.00; terminal mechanisms {'team_elimination': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | shield_bash(actor → enemy); move(actor → (3,2)); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 2 | shield_bash(actor → enemy); move(actor → (3,2)); attack(actor → enemy); shield_bash(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 3 | shield_bash(actor → enemy); move(actor → (3,2)); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 4 | shield_bash(actor → enemy); move(actor → (3,2)); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |

| Trial / step | Target | Position before → after | Push / premium displacement | Next decision after updated observation |
| --- | --- | --- | --- | --- |
| 1 / 1 | enemy | {'x': 3, 'y': 2} → {'x': 4, 'y': 2} | True / True | move(actor → (3,2)) |
| 2 / 1 | enemy | {'x': 3, 'y': 2} → {'x': 4, 'y': 2} | True / True | move(actor → (3,2)) |
| 2 / 4 | enemy | {'x': 4, 'y': 2} → {'x': 4, 'y': 2} | False / False | terminal/AP exhausted |
| 3 / 1 | enemy | {'x': 3, 'y': 2} → {'x': 4, 'y': 2} | True / True | move(actor → (3,2)) |
| 4 / 1 | enemy | {'x': 3, 'y': 2} → {'x': 4, 'y': 2} | True / True | move(actor → (3,2)) |

**snipe_vs_basic**

Qwen: 0/4 immediate wins; mean AP 5.00; terminal mechanisms {'nonterminal': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; nonterminal |
| 2 | snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; nonterminal |
| 3 | snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; nonterminal |
| 4 | snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; nonterminal |

| Trial | Action counts | Core attacked? |
| --- | --- | --- |
| 1 | {'snipe': 2, 'attack': 1} | no |
| 2 | {'snipe': 2, 'attack': 1} | no |
| 3 | {'snipe': 2, 'attack': 1} | no |
| 4 | {'snipe': 2, 'attack': 1} | no |

Luna: 0/4 immediate wins; mean AP 5.00; terminal mechanisms {'nonterminal': 4}. No frozen binary objective is assigned to this fixture.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 0; downs 1; removed 0; nonterminal |
| 2 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 0; downs 1; removed 0; nonterminal |
| 3 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 0; downs 1; removed 0; nonterminal |
| 4 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) | AP 5; Core damage 0; total damage 21; friendly damage 0; downs 1; removed 0; nonterminal |

| Trial | Action counts | Core attacked? |
| --- | --- | --- |
| 1 | {'snipe': 2, 'attack': 1} | no |
| 2 | {'snipe': 2, 'attack': 1} | no |
| 3 | {'snipe': 2, 'attack': 1} | no |
| 4 | {'snipe': 2, 'attack': 1} | no |

**team_elimination**

Qwen: 4/4 immediate wins; mean AP 1.00; terminal mechanisms {'team_elimination': 4}. Frozen objective successes: 4/4.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |
| 2 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |
| 3 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |
| 4 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |

Luna: 4/4 immediate wins; mean AP 1.00; terminal mechanisms {'team_elimination': 4}. Frozen objective successes: 4/4.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |
| 2 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |
| 3 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |
| 4 | attack(actor → enemy) | AP 1; Core damage 0; total damage 6; friendly damage 0; downs 1; removed 0; team_elimination |

**winning_core_line**

Qwen: 4/4 immediate wins; mean AP 4.00; terminal mechanisms {'team_elimination': 4}. Frozen objective successes: 4/4.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 2 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 3 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |
| 4 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) | AP 4; Core damage 0; total damage 18; friendly damage 0; downs 1; removed 0; team_elimination |

Luna: 4/4 immediate wins; mean AP 3.00; terminal mechanisms {'core_destruction': 4}. Frozen objective successes: 4/4.

| Trial | Complete step sequence | Mechanical facts |
| --- | --- | --- |
| 1 | snipe(actor → enemy); snipe(actor → enemy); attack(actor → red-core) | AP 5; Core damage 9; total damage 25; friendly damage 0; downs 0; removed 0; core_destruction |
| 2 | attack(actor → red-core) | AP 1; Core damage 9; total damage 9; friendly damage 0; downs 0; removed 0; core_destruction |
| 3 | snipe(actor → enemy); snipe(actor → enemy); attack(actor → red-core) | AP 5; Core damage 9; total damage 25; friendly damage 0; downs 0; removed 0; core_destruction |
| 4 | attack(actor → red-core) | AP 1; Core damage 9; total damage 9; friendly damage 0; downs 0; removed 0; core_destruction |

Winning Core counts **winning the turn** as its primary outcome, with Core destruction and team elimination separated. Qwen’s pilot won this fixture by team elimination; that pilot is not reclassified as Core destruction. Team Elimination similarly counts the immediate team-elimination win, even if basic Attack rather than Finish provides the final action. The fixture name is not an action requirement.

**Telemetry: trial decisions and whole tactical turns**

Distributions use observed telemetry, never inferred pricing. Durations ending `_duration` are Ollama-reported nanoseconds; wall latency is seconds. Each decision sums all its request attempts, including repair if present. Turn values sum decisions. p95 is the existing nearest-rank benchmark definition and is unset for fewer than 20 observations. Totals include all trial attempts and exclude preflight. Cache ratio is total cached input / total input. Qwen context occupancy is reported input plus output tokens divided by configured 4096; it is a telemetry measure, not a measurement of hidden model memory.

**Qwen preflight, separate from trials**

| Metric | Value |
| --- | --- |
| latency_seconds | 11.674 |
| input_tokens | 2297 |
| output_tokens | 37 |
| total_tokens | 2334 |
| prompt_eval_count | 2297 |
| eval_count | 37 |
| prompt_eval_duration | 1360755000 |
| eval_duration | 1217735000 |
| total_duration | 11629887249 |

The frozen telemetry does not record a separate load_duration. Preflight wall/total duration is shown separately; cold-load time cannot be isolated from it. No cold-start inference was added.

Qwen per decision:

| Metric | N | Min | Max | Mean | Median | p95 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| latency_seconds | 100 | 1.058 | 2.610 | 1.683 | 1.527 | 2.369 | 168.341 |
| input_tokens | 100 | 1094 | 2138 | 1470.160 | 1251.000 | 2138 | 147016 |
| output_tokens | 100 | 30 | 32 | 30.520 | 30.000 | 32 | 3052 |
| total_tokens | 100 | 1124 | 2168 | 1500.680 | 1283.000 | 2168 | 150068 |
| prompt_eval_count | 100 | 1094 | 2138 | 1470.160 | 1251.000 | 2138 | 147016 |
| eval_count | 100 | 30 | 32 | 30.520 | 30.000 | 32 | 3052 |
| prompt_eval_duration | 100 | 131035000 | 1039656000 | 297637859.990 | 150768000.000 | 987369000 | 29763785999 |
| eval_duration | 100 | 839532000 | 929678000 | 876616300 | 872172000.000 | 915142000 | 87661630000 |
| total_duration | 100 | 1055889213 | 2584766407 | 1676220617 | 1522330281.000 | 2366837538 | 167622061700 |

Qwen per turn:

| Metric | N | Min | Max | Mean | Median | p95 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| latency_seconds | 28 | 1.058 | 12.417 | 6.012 | 6.066 | 10.206 | 168.341 |
| input_tokens | 28 | 1134 | 10064 | 5250.571 | 5719.000 | 10064 | 147016 |
| output_tokens | 28 | 30 | 155 | 109 | 120.000 | 155 | 3052 |
| total_tokens | 28 | 1164 | 10216 | 5359.571 | 5874.000 | 10216 | 150068 |
| prompt_eval_count | 28 | 1134 | 10064 | 5250.571 | 5719.000 | 10064 | 147016 |
| eval_count | 28 | 30 | 155 | 109 | 120.000 | 155 | 3052 |
| prompt_eval_duration | 28 | 135801000 | 4860382000 | 1062992357.107 | 599755000.000 | 3528698000 | 29763785999 |
| eval_duration | 28 | 842713000 | 4449588000 | 3130772500 | 3479693500.000 | 4441429000 | 87661630000 |
| total_duration | 28 | 1055889213 | 12381854325 | 5986502203.571 | 6048261512.000 | 10176644024 | 167622061700 |

Maximum context occupancy: 52.9%; minimum remaining headroom: 1928 tokens of 4096.

| Context occupancy (fraction) | N | Min | Max | Mean | Median | p95 |
| --- | --- | --- | --- | --- | --- | --- |
| Per decision | 100 | 0.274 | 0.529 | 0.366 | 0.313 | 0.529 |
| Peak within each turn | 28 | 0.275 | 0.529 | 0.368 | 0.313 | 0.529 |

**Luna preflight, separate from trials**

| Metric | Value |
| --- | --- |
| latency_seconds | 4.172 |
| input_tokens | 2623 |
| output_tokens | 47 |
| total_tokens | 2670 |
| cached_input_tokens | 0 |
| uncached_input_tokens | 2623 |
| reasoning_tokens | 0 |

Luna per decision:

| Metric | N | Min | Max | Mean | Median | p95 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| latency_seconds | 88 | 0.921 | 5.033 | 1.548 | 1.376 | 2.648 | 136.236 |
| input_tokens | 88 | 1383 | 2841 | 1732.614 | 1546.000 | 2460 | 152470 |
| output_tokens | 88 | 38 | 81 | 40.170 | 39.000 | 45 | 3535 |
| total_tokens | 88 | 1422 | 2922 | 1772.784 | 1585.000 | 2503 | 156005 |
| cached_input_tokens | 88 | 0 | 2784 | 1232.011 | 1461.500 | 2455 | 108417 |
| uncached_input_tokens | 88 | 3 | 2460 | 500.602 | 3.000 | 1933 | 44053 |
| reasoning_tokens | 88 | 0 | 0 | 0 | 0.000 | 0 | 0 |

Luna per turn:

| Metric | N | Min | Max | Mean | Median | p95 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| latency_seconds | 28 | 0.973 | 8.015 | 4.866 | 5.633 | 7.884 | 136.236 |
| input_tokens | 28 | 1462 | 8332 | 5445.357 | 5708.000 | 8332 | 152470 |
| output_tokens | 28 | 38 | 199 | 126.250 | 131.000 | 195 | 3535 |
| total_tokens | 28 | 1500 | 8485 | 5571.607 | 5867.000 | 8485 | 156005 |
| cached_input_tokens | 28 | 0 | 8320 | 3872.036 | 4678.000 | 8320 | 108417 |
| uncached_input_tokens | 28 | 3 | 8332 | 1573.321 | 12.000 | 7167 | 44053 |
| reasoning_tokens | 28 | 0 | 0 | 0 | 0.000 | 0 | 0 |

Cache ratio: 71.1%; cached input 108,417; uncached input 44,053; tokens per tactical turn 5571.61. Dollar cost: **unset**.

**Full-turn controls versus separate pilot and expanded baseline**

The historical full-turn control is Phase 7A Prompt V2 + Observation V2, four trials per fixture. Pilot has one trial per fixture. Expanded stepwise has four fresh trials per fixture. Datasets are not merged. The step prompt changes the decision task as well as feedback frequency, so this is not a controller-only comparison with identical instructions. Different collection times, service load, cache conditions, and the fixed seven-state distribution limit causal and general-strength claims.

| Provider | Dataset | Turns | Mean AP | Requests / turn | Seconds / turn | Tokens / turn | Initial validity | Execution failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen | full_turn | 28 | 1.286 | 1.000 | 1.731 | 1814.143 | 100.0% | 0 |
| qwen | pilot | 7 | 4 | 3.571 | 8.028 | 5359.571 | 100.0% | 0 |
| qwen | expanded stepwise | 28 | 4 | 3.571 | 6.012 | 5359.571 | 100.0% | 0 |
| luna | full_turn | 28 | 2.714 | 1.000 | 1.351 | 2177.500 | 100.0% | 8 |
| luna | pilot | 7 | 4.143 | 3.286 | 5.091 | 5754.714 | 100.0% | 0 |
| luna | expanded stepwise | 28 | 4 | 3.179 | 4.866 | 5571.607 | 98.9% | 0 |

Qwen expanded/full-turn multipliers: requests **3.57×**; provider latency per turn **3.47×**; tokens per turn **2.95×**. Additional provider time: 4.28s/turn.

| qwen objective | Full-turn / 4 | Pilot / 1 | Expanded / 4 |
| --- | --- | --- | --- |
| revive_decision | 4 | 1 | 4 |
| winning_core_line | 0 | 1 | 4 |
| team_elimination | 4 | 1 | 4 |

| qwen AP by probe | Full-turn mean | Expanded mean | Full-turn immediate wins / 4 | Expanded immediate wins / 4 |
| --- | --- | --- | --- | --- |
| finish_or_core | 1 | 5 | 0 | 4 |
| fireball_friendly_fire | 1 | 5 | 0 | 4 |
| revive_decision | 2 | 5 | 0 | 4 |
| shield_bash_position | 1 | 3 | 0 | 4 |
| snipe_vs_basic | 2 | 5 | 0 | 0 |
| team_elimination | 1 | 1 | 4 | 4 |
| winning_core_line | 1 | 4 | 0 | 4 |

Luna expanded/full-turn multipliers: requests **3.18×**; provider latency per turn **3.60×**; tokens per turn **2.56×**. Additional provider time: 3.51s/turn.

| luna objective | Full-turn / 4 | Pilot / 1 | Expanded / 4 |
| --- | --- | --- | --- |
| revive_decision | 4 | 1 | 4 |
| winning_core_line | 4 | 1 | 4 |
| team_elimination | 4 | 1 | 4 |

| luna AP by probe | Full-turn mean | Expanded mean | Full-turn immediate wins / 4 | Expanded immediate wins / 4 |
| --- | --- | --- | --- | --- |
| finish_or_core | 5 | 5 | 4 | 1 |
| fireball_friendly_fire | 3.250 | 5 | 0 | 0 |
| revive_decision | 3 | 5 | 0 | 0 |
| shield_bash_position | 1.500 | 4 | 1 | 4 |
| snipe_vs_basic | 3.500 | 5 | 0 | 0 |
| team_elimination | 1 | 1 | 4 | 4 |
| winning_core_line | 1.750 | 3 | 4 | 4 |

Static validity and execution legality are separate: the full-turn controller can accept a statically valid plan whose later action becomes illegal after an earlier action. A full-turn execution failure count is not the same denominator as stepwise selected-current-action legality. All modes retain exact command replay, including any executed prefixes.

**Offline heuristic reference**

The preserved Phase 7B offline stepwise heuristic reference has 7/7 replayed turns, 24 decisions, 27 AP spent (3.857 AP/turn), and Revive, Winning Core, and Team Elimination objective success. It was not rerun or tuned. It is a deterministic reference, not tactical ground truth. Its 3.429 decisions/turn illustrate stepwise decision multiplicity; its zero provider requests do not estimate model inference cost.

**Interpretation and next experiment**

General reliability remains bounded by 28 turns per model on seven fixed states; repeated observations within a fixture and within a turn are not independent gameplay samples. Zero failed turns establishes success on this dataset, not a zero population failure rate; Luna’s one repaired initial rejection remains part of the reliability evidence. Four repetitions make variation visible but are too few to estimate its distribution precisely.

1. **Is Qwen’s multi-action improvement reproducible?** Yes on these fixtures: 24/28 turns used multiple decisions, mean AP stayed 4.00, and every fixture produced the same action sequence across its four trials. The four one-decision Team Elimination turns won immediately. This supports the feedback/continuation interpretation, not a general claim about model ability.

2. **Does Qwen consistently use most AP?** Yes when the battle continues: 71.4% of turns spent at least four AP, 57.1% spent all five, and no AP was abandoned by explicit stopping. All 28 unused AP occurred after terminal wins. Spending all five would have been unnecessary in those wins.

3. **Did Qwen static/repair failures materially decrease?** No further decrease is measurable against the proper Prompt V2 + Observation V2 full-turn control: both have 100% first-response validity and zero repairs. Stepwise preserves that reliability over 100 decisions and adds continuation. Earlier V1 Revive probes failed initial and repaired ability validation four times; the Prompt V2 / Observation V1 schedule then failed its first Revive trial. Observation V2 had already restored 4/4 correct Revives before stepwise. The new gain is reliable follow-up after revival, not a newly demonstrated static-validity improvement attributable solely to stepwise.

4. **Does Luna’s sequential-invalid problem remain solved?** It remains absent in this expanded sample: zero authoritative execution failures in 88 selected current-catalog actions across 28 turns. The full-turn control had eight truncations, seven specifically caused by earlier actions changing legality. This supports progressing to a broader test, not declaring the failure impossible in full matches.

5. **Did Luna tactical outcome quality improve?** The evidence is mixed. AP execution rose from 2.71 to 4.00, and Shield Bash Position immediate wins improved from 1/4 to 4/4. Revive, Winning Core, and Team Elimination were already 4/4 in the control. Finish/Core immediate wins changed from 4/4 to 1/4. See the mechanical tables for friendly damage, displacement, and other outcomes; legality and additional AP do not imply broadly better tactical quality.

6. **How much additional latency?** The whole-turn comparison above reports both measured multipliers and added seconds, with preflight excluded. Qwen’s expanded mean is lower than its pilot despite identical decision/token counts; collection-time conditions therefore matter. No causal service-speed or cache conclusion follows from these datasets alone.

7. **How many extra requests/tokens?** Use the per-turn multiplier table, not single-request latency. Stepwise repeatedly sends the current observation; successful continuation carries a substantial token/request increase. Qwen made 100 initial trial requests with no repairs; Luna made 88 initial trial requests plus one repair. Most overhead therefore comes from ordinary decision multiplicity, with Luna’s correction included. Tokenizers differ across providers; compare each model to its own historical control. Dollar costs remain unset.

8. **Robust enough for full-match testing?** Yes as an experiment-entry gate: perfect observed current-action legality, exact replay, no provider failures, reproducible Qwen continuation, and absent Luna sequencing failures satisfy the stated probe gate. This is not evidence of full-match reliability. Longer games, more actors, context growth, and match-level request consumption are untested under this control.

9. **Preserve full-turn planning?** Yes. It remains the harder control condition, measuring within-turn state tracking and sequencing with fewer inference opportunities. Keep its errors and lower cost visible rather than replacing or pooling its evidence with stepwise results.

10. **Next phase?** Recommend a separately specified and authorized **stepwise full-match experiment**, same-provider self-play and each provider against the frozen heuristic. Define match budgets and failure/abort semantics before inference. Bounded full-turn replanning remains a later architecture comparison; this successful probe gate does not justify adding it now. No full matches or other next-phase experiments were run.

The current frozen stepwise runner supports probes only. Full-match testing therefore needs a separately reviewed implementation and frozen experiment specification before live authorization; these results do not make a full-match command available or authorize that work.

**Artifact locations and reproducibility**

| Artifact | Location |
| --- | --- |
| Unified report | docs/arena-stepwise-expanded-results.md |
| Qwen frozen evidence | .local/arena-phase7c-qwen-stepwise-probes-20260913-01/ |
| Luna frozen evidence | .local/arena-phase7c-luna-stepwise-probes-20260913-01/ |
| Offline analysis, all turn/step details | .local/arena-phase7c-audit-20260913-01/analysis.json |
| Offline analyzer | .local/arena-phase7c-audit-20260913-01/analyze.py |
| Report renderer | .local/arena-phase7c-audit-20260913-01/report.py |
| Source manifest / contracts | audit directory: source-before.json / contracts-before.json |
| Preservation manifest | audit directory: preservation-before.json |
| Exact commands / logs / watchdog verdicts | audit directory: {qwen,luna}-command.json / -cli.log / -guard.json |
| Pilot report | docs/arena-stepwise-pilot-results.md |
| Full-turn control report | docs/arena-observation-v2-probe-results.md |
| Offline heuristic evidence | .local/arena-phase7b-preparation/heuristic-baseline-final/summary.json |

Each trial retains manifest.json, turn.json, command-trace.json, final-snapshot.json, verification.json, and result.json. The only new files are Phase 7C evidence, offline audit/reporting helpers, and this results report. Source, profiles, prompts, observations, schemas, gameplay, historical evidence, and benchmark behavior remain frozen. No broad regression suite was rerun: this is data collection without source edits; exact replay plus preservation verification are the relevant checks.
