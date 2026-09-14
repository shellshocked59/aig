# Arena Phase 9D: action-ID tactical regression forensics and next representation design

2026-09-13. Offline analysis only. The first Revive choice diverges at decision 1 on identical tactical facts and identical ordered legal actions. Structured chooses Revive, while action-ID chooses the first Attack. This reproduces in all four expanded trials and agrees with the separate action-ID pilot failure. It does not identify which component of the representation change caused the choice.

**Recommendation: Option F, dynamically constrained structured output, as the next separately authorized representation experiment.** Retain Observation V2, Step Prompt V1, and logical ArenaTurnPlan V1. Constrain complete action alternatives in the provider wire schema. This prioritizes the successful structured tactical contract and removes arbitrary reference combinations from schema-valid outputs. It sacrifices the nine-token output target. No implementation, version registration, or live run is included here.

Three corrections to the initial hypotheses matter: both modes use exactly 88 basic attacks and 12 special abilities; canonical V3 entries put `action` before `id`; and Prompt V2 removes the AP-cost sentence as well as changing the response contract. The comparison is not a pure opaque-ID ablation.

## Evidence, scope, and limits

Frozen sources are the directories linked by [structured expanded results](arena-stepwise-expanded-results.md) and [action-ID expanded results](arena-action-id-expanded-results.md):

- `.local/arena-phase7c-qwen-stepwise-probes-20260913-01/summary.json`
- `.local/arena-phase9c-qwen-action-id-expanded-01/summary.json`
- Separate pilot: `.local/arena-phase9b-qwen-action-id-pilot-01/summary.json`.

Derived evidence is in [the Phase 9D directory](../.local/arena-phase9d-action-id-forensics-20260913/). `derived-01/decisions.json` and `decision-ordinals.csv` cover every one of 200 selected actions, across 28 turns per mode. `revive-decisions.json` contains all 36 Revive-fixture decisions across eight trials, complete catalogs, states, hashes, parsed responses, telemetry, and links to reconstructed requests. `revive-catalogs.md` provides readable complete catalogs for every distinct step of trial 1; trials 2–4 repeat these observations and actions, with their separate telemetry preserved in JSON.

**Raw response text was not persisted by either benchmark.** The saved `attempts` retain errors, duration, and token counts; parsed decisions/plans and selected actions survive. Whitespace, raw field order, and the exact original response strings cannot be recovered. No reconstructed response is presented as raw evidence.

The request artifacts are reconstructed canonical client payloads from saved observations, model configuration, keep-alive, hash-checked prompt text, and schema source, rather than captured network bytes or server-tokenized prompts. Contracts and canonical serializer match historical source hashes. The action-ID provider and adapter match their run manifest. The structured provider source has changed between phases; its first-request construction is inferred from the retained contract and current path. The Ollama schema-hook addition reverses exactly to the historical adapter hash via the saved Phase 9A transformation fixture. `request-source-provenance.json` records cross-phase hashes. This limits claims of byte-exact historical transport recovery; it does not limit saved state, choice, catalog, or telemetry comparisons.

## Phase 9B/9C and structured control

The separate Phase 9B action-ID pilot completed 7/7 turns using 25/70 requests, with 25/25 valid first responses and current IDs, zero repairs, and seven recorded exact replays. It spent 28 AP, returned 225 output tokens, and achieved five immediate victories. Its Revive objective is 0/1. Expanded Phase 9C has 0/4, versus structured 4/4. Deterministic repeats demonstrate reproducibility for these observations and profile; they are not four independent stochastic samples of general gameplay.

Both expanded datasets have 28/28 valid turns, 100/100 initially valid decisions, no repairs, provider failures, or authoritative execution defects, and 28/28 exact replays. Mean AP spent is 4/5, median 5/5, full-five-AP rate 57.1%, mean 3.57 decisions/turn, and no explicit EndTurn. Action-ID used 100/180 authorized requests. Structured trial accounting excludes its one preflight (101 historical requests including preflight). No unused allowance was spent in this phase.

## Exact Revive divergence and tactical equality

First state hash: `d0d19ba76aa339d8f114a77b2dbdc9847423f5b896066e3a8a50fb62b9ec3988`.

Blue is active with 5 AP. `actor` is an ACTIVE cleric, 11 HP at (2,2); `ally` is a DOWNED mage, 0/9 HP at (3,2); `enemy` is an ACTIVE knight, 18 HP at (3,3). Both Cores have 30 HP, blue at (0,2), red at (8,2). Board is 9×5 with no blocked or premium tiles. Unit IDs, classes, statuses, positions, HP, Core data, board, rules, action ranges and all remaining non-wrapper observation facts match exactly. Complete snapshot equality also holds.

V2 legal actions equal the underlying V3 legal actions **as ordered lists of complete objects**, ignoring only ID wrappers and the observation version tag for comparison of the full observations. Actions themselves have no fields ignored. All 200 actual decision states additionally regenerate equal V2/V3 catalogs offline. This checks later legality without pretending the two policy trajectories remain the same.

| Mode | Selected complete action | ID / equivalent ID | Ordinal / size | AP cost | Observation hash |
| --- | --- | --- | --- | --- | --- |
| structured | `{"target_id":"ally","type":"revive","unit_id":"actor"}` | A21 | 21/21 | 2 | `52a7fa2ed56b339b7c1025a9030ada6c59591a381f1722f68a9378f141485cf5` |
| action_id | `{"target_id":"enemy","type":"attack","unit_id":"actor"}` | A01 | 1/21 | 1 | `2e061f89d0a9c1b64faf21cd0cc52c8fcbb80e10141fdb408ba91de184a8482b` |

Revive is already legal at decision 1: `A21`, ordinal 21 of 21, one option, with exactly one Attack before it. The selected Attack is `A01`, ordinal 1 of 21, cleric `actor` targeting `enemy`, cost 1 AP. Revive targets `ally` from the same actor and costs 2 AP. Both IDs have length 3; numeric positions are 1 and 21.

Structured executes Revive followed by three attacks by the revived mage. Action-ID executes five attacks by the cleric. It selects `A01` at every decision in all four trials (20/20). That is also the only Attack option and therefore the first Attack option. Revive remains `A21` at steps 1–4 (AP 5,4,3,2); at step 5 only 1 AP remains and Revive is no longer legal. These facts cannot separate a preference for first entries, attack semantics, the actor, or the ID string.

Only the initial state is shared between the two Revive trajectories within each matched trial. Divergence begins **after** the differing first choice. The full state-hash cross-join finds no later common decision state. Structured Revive unlocks a new actor and 25 Fireball choices at steps 2–3; the ID path never unlocks that catalog. Same step numbers after decision 1 are not matched tactical states.

| Mode | Step | AP before → after | Selected action | Ordinal / size | State hash before | State hash after gameplay action |
| --- | --- | --- | --- | --- | --- | --- |
| structured | 1 | 5 → 3 | `{"target_id":"ally","type":"revive","unit_id":"actor"}` | 21/21 | `d0d19ba76aa339d8f114a77b2dbdc9847423f5b896066e3a8a50fb62b9ec3988` | `482be6ef6053dd1ed786228b6c552e23408ab1bc843f462a1cc6dff46ade120b` |
| structured | 2 | 3 → 2 | `{"target_id":"enemy","type":"attack","unit_id":"ally"}` | 22/69 | `482be6ef6053dd1ed786228b6c552e23408ab1bc843f462a1cc6dff46ade120b` | `6acf5616d44247e261702d4407bfd748e366e81e2390e898dbe766fa1a5d64e0` |
| structured | 3 | 2 → 1 | `{"target_id":"enemy","type":"attack","unit_id":"ally"}` | 22/69 | `6acf5616d44247e261702d4407bfd748e366e81e2390e898dbe766fa1a5d64e0` | `cbb49fde2bf1d98813bdc0ab7814bda1c4c48fe7c4c1b3e9747fe8674e0e4ee9` |
| structured | 4 | 1 → 0 | `{"target_id":"enemy","type":"attack","unit_id":"ally"}` | 22/44 | `cbb49fde2bf1d98813bdc0ab7814bda1c4c48fe7c4c1b3e9747fe8674e0e4ee9` | `7c7e0a3a5a50a7f72619c866221376005d56e5b562f048f536087c67c0849e7b` |
| action_id | 1 | 5 → 4 | `{"target_id":"enemy","type":"attack","unit_id":"actor"}` | 1/21 | `d0d19ba76aa339d8f114a77b2dbdc9847423f5b896066e3a8a50fb62b9ec3988` | `48dce56082425a84214b24b5bfb47f4fb48ff0b9c6871f6b21ff319ef6b6d17d` |
| action_id | 2 | 4 → 3 | `{"target_id":"enemy","type":"attack","unit_id":"actor"}` | 1/21 | `48dce56082425a84214b24b5bfb47f4fb48ff0b9c6871f6b21ff319ef6b6d17d` | `be9947539ff96f267f1a1a8e3c92e5d8a9485b8603134d5581bb86c9db6298a4` |
| action_id | 3 | 3 → 2 | `{"target_id":"enemy","type":"attack","unit_id":"actor"}` | 1/21 | `be9947539ff96f267f1a1a8e3c92e5d8a9485b8603134d5581bb86c9db6298a4` | `a41ef6299fd26f186d0275ccc576caedfc19da2b9b2f18f72cd88110eebf5b3c` |
| action_id | 4 | 2 → 1 | `{"target_id":"enemy","type":"attack","unit_id":"actor"}` | 1/21 | `a41ef6299fd26f186d0275ccc576caedfc19da2b9b2f18f72cd88110eebf5b3c` | `bdabf3570cecc9b89699636d488563d362b80570244ac3748fab603d433f1b1b` |
| action_id | 5 | 1 → 0 | `{"target_id":"enemy","type":"attack","unit_id":"actor"}` | 1/20 | `bdabf3570cecc9b89699636d488563d362b80570244ac3748fab603d433f1b1b` | `019f705f9a3efed0c30b0ee5c111118e08c84649543696473e7dd1a45cef7bf3` |

The action-ID fifth gameplay action hash precedes automatic EndTurn. The persisted final snapshot includes that EndTurn; its hash is therefore different. Replay verification includes the automatic command.

| Mode | Step | Move | Attack | Heal | Finish | Revive | Shield Bash | Snipe | Fireball | Total | Revive ID / ordinal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| structured | 1 | 19 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 21 | A21/21 |
| structured | 2 | 41 | 2 | 1 | 0 | 0 | 0 | 0 | 25 | 69 | none |
| structured | 3 | 41 | 2 | 1 | 0 | 0 | 0 | 0 | 25 | 69 | none |
| structured | 4 | 41 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 44 | none |
| action_id | 1 | 19 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 21 | A21/21 |
| action_id | 2 | 19 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 21 | A21/21 |
| action_id | 3 | 19 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 21 | A21/21 |
| action_id | 4 | 19 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 21 | A21/21 |
| action_id | 5 | 19 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 20 | none |

## Catalog-order analysis across all 28 turns per mode

Ordinal is 1-based. Percentile = 100 × (ordinal−1)/(catalog size−1); a singleton is defined as 0. These are decision-weighted summaries, not average turn ranks. Complete row-level denominators and selections are in `decision-ordinals.csv`. Catalog ordering is actor ID, action type, target ID, then destination/target y and x; it is not a tactical ranking.

| Mode | Decisions | Mean percentile | Median percentile | First entry | First quarter | Last quarter |
| --- | --- | --- | --- | --- | --- | --- |
| structured | 100 | 29.344 | 0.000 | 56 | 56 | 12 |
| action_id | 100 | 16.580 | 0.000 | 80 | 80 | 12 |

| Probe | Structured n | ID n | Structured mean / median % | ID mean / median % | Structured first | ID first |
| --- | --- | --- | --- | --- | --- | --- |
| finish_or_core | 20 | 20 | 0.000 / 0.000 | 0.000 / 0.000 | 20 | 20 |
| fireball_friendly_fire | 20 | 20 | 64.601 / 68.116 | 23.731 / 0.000 | 0 | 12 |
| revive_decision | 16 | 20 | 52.650 / 39.860 | 0.000 / 0.000 | 0 | 20 |
| shield_bash_position | 12 | 12 | 0.000 / 0.000 | 0.000 / 0.000 | 12 | 12 |
| snipe_vs_basic | 12 | 12 | 66.667 / 100.000 | 65.278 / 95.833 | 4 | 4 |
| team_elimination | 4 | 4 | 0.000 / 0.000 | 0.000 / 0.000 | 4 | 4 |
| winning_core_line | 16 | 12 | 0.000 / 0.000 | 33.333 / 0.000 | 16 | 8 |

| Mode | Action type | n | Mean / median percentile |
| --- | --- | --- | --- |
| structured | attack | 88 | 19.709 / 0.000 |
| structured | revive | 4 | 100.000 / 100.000 |
| structured | snipe | 8 | 100.000 / 100.000 |
| action_id | attack | 88 | 5.393 / 0.000 |
| action_id | snipe | 12 | 98.611 / 100.000 |

The mean selected percentile drops 12.765 percentage points, and first-entry selection rises 24 points. Both modes already have a median at the first entry. Action-ID still makes 12 last-quarter selections, including `A24` and `A35` Snipes. This rejects an absolute “always first/low ID” account. The extra first-entry choices concentrate in Revive and Fireball, while Winning Core moves in the opposite direction. Actor/type sorting confounds position with semantics, and earlier choices change later catalogs and decision counts. Correlation cannot establish that explicit identifiers caused positional bias. A future order-permutation or ID-label ablation would be needed; none was run.

An additional cross-join on identical state hashes within each matched probe/trial finds 72 shared decision states, with different choices in 24: Fireball 12, Revive 4, Snipe 4, Winning Core 4. All 28 paired initial snapshots are identical. `matched-state-decisions.json` preserves these rows; this confirms policy differences at identical states without attributing them to any particular representation component.

## Observation presentation

The exact canonical form of the same first-state Revive entry is:

```json
{"target_id":"ally","type":"revive","unit_id":"actor"}
```

```json
{"action":{"target_id":"ally","type":"revive","unit_id":"actor"},"id":"A21"}
```

V3 adds one nesting level and 22 ASCII bytes per entry for these three-character IDs. `action`, **not `id`**, is first under the sorted-key serializer. Semantic fields begin ten characters later because of `"action":{`; they are not preceded by the ID value. The surrounding `legal_actions` array follows `environment` and precedes `legal_actions_state` in canonical JSON. Both versions use the same array position and unchanged order; full surrounding text is in the reconstructed requests.

The initial Revive catalog grows from 1,290 to 1,752 bytes (+35.8%), with the same 21 options. Observation size grows from 3,151 to 3,613 bytes (+14.7%). More wrapper syntax may affect scanning, but that is a hypothesis. Flattening would remove 11 bytes per entry relative to V3 while retaining the ID. Under current sorted keys a flattened entry would put `id` before `target_id`, `type`, and `unit_id`; “flat” does not automatically mean “type first.”

## Prompt comparison: every changed instruction

Both complete prompts are saved in `derived-01/*-prompt.txt`. A = needed for the contract; B = incidental wording; C = potentially behavior-shaping. Categories can overlap. Neither prompt explicitly recommends Revive, Attack, or a strategic priority, but that narrow neutrality does not establish equal tactical information or equal attention.

| V1 → V2 difference | Class | Assessment |
| --- | --- | --- |
| “deterministic fantasy tactics battle” → “deterministic tactical battle” | B | Genre wording removed. |
| “single best legal action … from supplied ArenaObservation” → “single action … NOW” | B,C | Removes best/legal qualifier and explicit observation reference; legal catalog instruction remains. |
| Current AP is action_points_remaining → absent | C | Removes explicit pointer to AP field. |
| Copy complete action / do not reconstruct actor-target combination → return one listed action_id, do not create or modify IDs, do not reconstruct unit/target IDs, coordinates or action fields | A,C | Necessary response mapping, but stronger attention to identifiers and prohibition on semantic field generation. |
| Catalog describes current observation including legal_actions_state=turn_start → every currently legal action listed with deterministic ID and complete semantics; IDs current-only | A,B,C | Current-state meaning retained, stale turn_start clarification lost, locality of IDs added. |
| Engine executes exactly that action and supplies fresh updated observation → after execution receive fresh observation and new catalog | A,B | Same stepwise loop; catalog refresh made explicit. |
| ArenaTurnPlan, exactly one action or actions=[], retain schema_version → action_id or {"action_id":null}, required schema | A | Necessary output and stopping contract replacement. |
| Move/Attack/Heal/Finish/Shield Bash 1 AP; Revive/Snipe/Fireball 2 AP → absent | C | Removes explicit action-cost grounding; this is not required by the ID contract. |
| Do not plan later actions → absent | C | Removes explicit horizon instruction, although NOW and refresh loop still imply stepwise choice. |
| Do not explain reasoning or add commentary → return only required schema; do not explain reasoning | B | Output-only restriction retained. |

The cost reminder is particularly material: V2/V3 compact observations preserve legal options, ranges, and effect facts, but do not attach per-action AP costs to catalog entries. AP-sensitive legality is encoded by presence/absence, which is weaker than explicit cost information for planning a continuation. Prompt V2 is therefore not a pure contract-only rewrite. Its removal of AP facts and “best” is an alternative explanation that must remain alongside nesting, schema, and opaque-output hypotheses. No prompt was changed here.

## Provider schemas and semantic context

Historical Qwen used Ollama `format=turn_plan_schema()` (2,567 canonical bytes), a complete eight-action union under `actions`, with schema_version and maxItems=5. The stepwise application parser separately restricts the result to zero or one action. Action-ID uses a 125-byte object with one required nullable string `action_id`; no enum constrains it to current IDs. Current-ID membership is checked in the application. Thus neither an arbitrary valid ID nor full-match reliability is guaranteed by that tiny schema alone.

Each structured action name—move, attack, heal, finish, revive, shield_bash, snipe, fireball—appears once as a schema discriminator. The ID schema has none of these names. “Repeated semantic grounding” here means one extra occurrence per type across the schema, in addition to message occurrences, not many schema occurrences of Revive. Byte/4 estimates are 641.75 and 31.25 respectively. These are coarse size heuristics, not Qwen token counts or measured schema tokenization.

The following diagnostic uses case-normalized substring counts in the reconstructed canonical client payload (messages plus `format` and configuration). For example `heal` includes `heal_amount`/`healing` and `attack` includes `attack_range`; `legal_actions` includes `legal_actions_state`. Message-only counts are also given because the saved evidence does not prove that the server exposed schema text as natural-language model context.

| Term | Structured payload | ID payload | Structured messages | ID messages | Structured schema | ID schema |
| --- | --- | --- | --- | --- | --- | --- |
| revive | 5 | 3 | 4 | 3 | 1 | 0 |
| downed | 1 | 1 | 1 | 1 | 0 | 0 |
| attack | 9 | 7 | 8 | 7 | 1 | 0 |
| heal | 10 | 8 | 9 | 8 | 1 | 0 |
| snipe | 3 | 1 | 2 | 1 | 1 | 0 |
| fireball | 4 | 2 | 3 | 2 | 1 | 0 |
| action_id | 0 | 4 | 0 | 2 | 0 | 2 |
| legal_actions | 4 | 3 | 4 | 3 | 0 | 0 |
| cleric | 2 | 2 | 2 | 2 | 0 | 0 |

The first Revive request has 1,182 measured input tokens and 31 output tokens in structured mode, versus 1,305 and 9 for action-ID. Yet reconstructed client payload bytes decrease from 7,467 to 5,417 because the schema shrinks. Wire bytes, grammar constraints, message text, and evaluated prompt tokens are different quantities. Schema textual grounding is plausible only conditionally on how Ollama converts `format` to constraints/context; no server-side prompt dump or tokenizer evidence was saved. The extra Revive message occurrence in V1 comes from the AP-cost sentence. These counts are contextual evidence, not a quality score.

## Action distribution and special abilities

| Action | Structured count / rate | ID count / rate |
| --- | --- | --- |
| move | 0 / 0% | 0 / 0% |
| attack | 88 / 88% | 88 / 88% |
| heal | 0 / 0% | 0 / 0% |
| finish | 0 / 0% | 0 / 0% |
| revive | 4 / 4% | 0 / 0% |
| shield_bash | 0 / 0% | 0 / 0% |
| snipe | 8 / 8% | 12 / 12% |
| fireball | 0 / 0% | 0 / 0% |

Special abilities here mean Revive, Shield Bash, Snipe, and Fireball. Both modes use 12/100 (12%): structured 4 Revives + 8 Snipes, ID 12 Snipes. Both spend 24/112 AP (21.43%) on these abilities. Neither uses Fireball or Shield Bash in these fixtures; their absence in ID is not a new regression. There is no aggregate shift toward basic attacks or away from special abilities. There is a redistribution of ability type, actor, and target.

## All seven tactical outcomes

Each row below is the per-trial result, repeated in all four trials of each mode. “Objective” is the saved probe predicate, with — meaning absent rather than failure. Classification uses the recorded objective/victory/terminal result as outcome; it also reports state-level differences explicitly. All final units remain at their initial positions in both modes. Total damage is the benchmark `damage_dealt` metric, including Core damage; it must not be added to Core damage again.

### finish_or_core — SAME OUTCOME / SAME MECHANISM

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | — | True / core_destruction | 5 | 30 / 30 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) |
| action_id | — | True / core_destruction | 5 | 30 / 30 | attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core); attack(actor → red-core) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 18; body: downed 0; enemy: active 11 | `de5262583125edae050b90bd74454784057bb5090ae6656e5b635408dcefc2d9` |
| action_id | actor: active 18; body: downed 0; enemy: active 11 | `de5262583125edae050b90bd74454784057bb5090ae6656e5b635408dcefc2d9` |

### fireball_friendly_fire — SAME OUTCOME / DIFFERENT MECHANISM

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | — | True / team_elimination | 5 | 27 / 0 | attack(ally → enemy); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy2); attack(ally → enemy2) |
| action_id | — | True / team_elimination | 5 | 27 / 0 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(ally → enemy2); attack(ally → enemy2) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 9; ally: active 18; enemy: downed 0; enemy2: downed 0 | `8c7363b05332345b2ad7320c9c91dd85cc79bff3c7f6f95f9e2b8dbf719e4e13` |
| action_id | actor: active 9; ally: active 18; enemy: downed 0; enemy2: downed 0 | `8c7363b05332345b2ad7320c9c91dd85cc79bff3c7f6f95f9e2b8dbf719e4e13` |

### revive_decision — DIFFERENT OUTCOME

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | True | True / team_elimination | 5 | 18 / 0 | revive(actor → ally); attack(ally → enemy); attack(ally → enemy); attack(ally → enemy) |
| action_id | False | False / nonterminal | 5 | 15 / 0 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 11; ally: active 5; enemy: downed 0 | `7c7e0a3a5a50a7f72619c866221376005d56e5b562f048f536087c67c0849e7b` |
| action_id | actor: active 11; ally: downed 0; enemy: active 3 | `fadfaa08a3339d7221c77b348c88e8693eea8fe519acc5caae44ea7b161a865e` |

### shield_bash_position — SAME OUTCOME / SAME MECHANISM

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | — | True / team_elimination | 3 | 18 / 0 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) |
| action_id | — | True / team_elimination | 3 | 18 / 0 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 18; enemy: downed 0 | `6825c17222fd0cb32c6080f177608eb2dd0b1fb2e0700cc21e8a70035a3a082e` |
| action_id | actor: active 18; enemy: downed 0 | `6825c17222fd0cb32c6080f177608eb2dd0b1fb2e0700cc21e8a70035a3a082e` |

### snipe_vs_basic — SAME OUTCOME / DIFFERENT MECHANISM

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | — | False / nonterminal | 5 | 18 / 0 | snipe(actor → enemy2); snipe(actor → enemy2); attack(actor → enemy2) |
| action_id | — | False / nonterminal | 5 | 21 / 0 | snipe(actor → enemy); snipe(actor → enemy2); attack(actor → enemy2) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 10; enemy: active 8; enemy2: downed 0 | `95c6a0aab559dbab3bab91cd9b172a0bff56b9ddd8b6ef75b81049ec73d9ec98` |
| action_id | actor: active 10; enemy: downed 0; enemy2: active 5 | `84a7c71b883426ca0b849f2fc723adc30e2d0af882f0b9bf4fd764079bc39310` |

### team_elimination — SAME OUTCOME / SAME MECHANISM

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | True | True / team_elimination | 1 | 6 / 0 | attack(actor → enemy) |
| action_id | True | True / team_elimination | 1 | 6 / 0 | attack(actor → enemy) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 18; body: downed 0; enemy: downed 0 | `fa297e8a8b3e19d095fdf5ac9b62bd300565d663e3f6e5866beca7c07f761799` |
| action_id | actor: active 18; body: downed 0; enemy: downed 0 | `fa297e8a8b3e19d095fdf5ac9b62bd300565d663e3f6e5866beca7c07f761799` |

### winning_core_line — SAME OUTCOME / DIFFERENT MECHANISM

| Mode | Objective | Victory / mechanism | AP | Total / Core damage | Sequence |
| --- | --- | --- | --- | --- | --- |
| structured | True | True / team_elimination | 4 | 18 / 0 | attack(actor → enemy); attack(actor → enemy); attack(actor → enemy); attack(actor → enemy) |
| action_id | True | True / team_elimination | 4 | 18 / 0 | attack(actor → enemy); snipe(actor → enemy); attack(actor → enemy) |

| Mode | Final units: status HP | Final state hash |
| --- | --- | --- |
| structured | actor: active 10; body: downed 0; enemy: downed 0 | `5f5ea40fbdac6b0e15824110d40503ead4c09c2789e3a5defdbf08d57ccfc497` |
| action_id | actor: active 10; body: downed 0; enemy: downed 0 | `5f5ea40fbdac6b0e15824110d40503ead4c09c2789e3a5defdbf08d57ccfc497` |

Revive is the only changed saved objective/victory result. Snipe is additionally a **different tactical final state**: structured downs the knight and leaves the mage on 8 HP; ID downs the mage and leaves the knight on 5 HP. Both remain nonterminal with one enemy active. Under a definition that treats any changed enemy state as outcome, Snipe also counts as DIFFERENT OUTCOME; it must not be called tactically equivalent. Fireball changes attacking actor but reaches the same final snapshot. Winning Core adds Snipe, reducing decisions from four to three at unchanged 4 AP and the same team-elimination final state. Four of seven resolved sequences differ; two of seven final states differ. Revive is therefore part of a broader policy change, without evidence of a general special-ability suppression.

## Hypotheses: evidence and limits

1. **Catalog position/actor ordering:** supported descriptively by 80% versus 56% first-entry selections, Revive last versus Attack first, and a changed Fireball actor. Against a simple rule: high-ordinal Snipes persist and Winning Core adds a final-entry Snipe. Requires a controlled order/label intervention for causality.
2. **Opaque-ID semantic loss:** consistent with losing Revive while selecting a symbol. Against a universal loss: Snipe use increases, the full action semantics remain in every V3 entry, and two unchanged victory mechanisms remain intact. Prompt, nesting, schema, and output changes co-vary, so opacity is not isolated.
3. **Prompt attention and missing AP grounding:** directly observed wording/fact changes. They may affect how immediate damage is weighed against a two-AP enabling action. No evidence identifies the model's reasoning; this explanation has not been tested independently.
4. **Schema semantic reinforcement:** structured schema names all eight types; ID schema names none. Backend grammar processing can influence output distributions even if not printed into the prompt. Whether the schema acts as natural-language grounding is unknown from client artifacts.
5. **Generative semantic commitment:** structured output must generate `type`, actor and target; ID output generates a symbol. Requiring semantic generation may affect choice formation, but does not prove deeper reasoning. ID+type is a clean separate hypothesis test with a new mismatch failure mode.
6. **Mechanical/fixture mismatch:** evidence against it is strong—identical initial snapshots, complete ordered action equality, authoritative replay, and regenerated observations at every step. Collection conditions remain a confound for timing and possibly serving behavior; fixed profile and deterministic repeats do not randomize them away.

## Efficiency and long-match relevance

Structured output totals 3,052 tokens; action-ID 900 (−70.5%). Input totals 147,016 versus 157,312 (+7.0%); combined totals 150,068 versus 158,212 (+5.4%). Different trajectories change later observations, so whole-dataset totals are not a pure encoding-overhead measurement. Mean latency/turn is 6.012 versus 3.916 seconds, collected under different load/cache/run conditions; no causal speedup is established.

Structured probes were already 100% valid. ID probes therefore establish no observed reliability improvement over that control. Rare invalid_reference failures in long structured matches remain the real target, and action-ID has not been tested there. Its schema still admits arbitrary strings; application-side ID membership and repair remain necessary. A representation should first pass a tactical gate before separately authorized full matches. No full-match request is justified by these probe validity rates alone.

## Design options A–F and offline validation

| Option | Assessment | Offline validation before any live use |
| --- | --- | --- |
| A: current action-ID → matches | Smallest operational change, low output; known Revive loss and unproven long-match gain. Reject as immediate next step. | Existing replay, catalog equality, ID membership/error paths, budgets; cannot prove tactics or match reliability offline. |
| B: flat semantic action-ID | Smallest observation-only change; removes nesting and some bytes, retains ID output/schema. Does not restore AP wording, semantic generation, or schema grounding. Useful isolated alternative, but weaker fit to priority 1. | Bijection to V2/V3, stable ordinals and IDs, flatten/unflatten losslessness, serialized key order, request size, fake response resolution, identical heuristic commands. |
| C: semantic ID labels | Adds type cues to selection string; labels can bias action types and increase output length. Useful explicit label experiment, not neutral indexing. | Unique deterministic labels, collision/width checks, exact resolver mapping, token estimates and size, rename invariance of heuristic choices. |
| D: ID + action type | Adds small semantic commitment; mismatch handling adds a failure surface and larger schema. Cannot assume type-first generation under canonical order. | Check every valid pair; reject all mismatched type/ID pairs and stale IDs; fake wire shape, output length, resolution equality. |
| E: full action + ID | Redundant semantic output with consistency check; restores reference-string generation and nearly all output overhead. Low appeal. | Exact equality validation, reject inconsistent/cross-catalog pairs, round-trip coverage, request/output size. |
| F: dynamically constrained structured output | Retains V2, V1 prompt and semantic generation; prevent invalid actor-target-coordinate combinations by representing complete legal alternatives. Larger dynamic schema/output. Preferred for preservation of tactical behavior. | Exact legal-language equality, exhaustively validate catalog actions, reject cross-products and stale references, verify commands/AP/replays with fakes, schema size limits and provider-wire subset checks. |

Fake-provider tests verify local schema construction and consumption, not actual Ollama/OpenAI schema support, constrained-decoding behavior, or tactical quality. None of these proposed variants was implemented or exercised here.

### Serious feasibility assessment for Option F

Independent enums for valid actors, targets, x and y are **insufficient**: they admit illegal actor-target pairs and coordinate cross-products. The preferred design constrains an entire action alternative: fixed action type, actor, and correlated target/position. A nested union of exact complete object branches can represent the current legal language; lossless grouping is permissible only when equivalence is proven. Preserve the logical ArenaTurnPlan V1 parser and exact catalog membership check as the authority.

Retain the root object with `schema_version` and `actions`. Restrict the provider-facing array to at most one action, permit `actions=[]`, and use exact current-catalog alternatives for its item. Empty-catalog handling must explicitly admit only the empty action array rather than produce an empty/invalid union. Do not silently fall back to unconstrained schema. Coordinates require typed numeric singleton constraints; the current OpenAI transform's string-const conversion cannot simply be reused for integers.

**Ollama:** the local adapter already passes JSON Schema through `format`, with `oneOf` action variants and constants. A dynamic schema needs access to the current observation; today's zero-argument `output_schema()` hook is not enough on its own. This is a design for a separately versioned provider/control path, not a trivial settings change. Exact branches may make grammar compilation, context/latency, or supported-keyword limits relevant. Actual server acceptance and decoding must be verified in a later authorized phase.

**OpenAI strict Structured Output:** the existing local adapter uses a root object, required properties, `additionalProperties:false`, and a transform from `oneOf` to nested `anyOf` and typed enums. Exact action branches can conceptually use the same style, but branch overlap, nesting, branch/property/enum limits, array constraints, and numeric singleton support require current official-documentation and eventual service validation. Keep unions below the root and preserve correlation across fields. No claim of current acceptance by a specific OpenAI model is made from local code or a fake client. The requested offline scope prevented fetching current official documentation or contacting either service.

Worst-case exact unions scale with legal catalog size, including many Move/Fireball positions, and duplicate observation data. Large battle catalogs may make F unattractive. This risk is real: low context overhead and the ID output saving are sacrificed. Before proposing any live run, measure a frozen corpus including large legal catalogs and reject F if it cannot fit the profile's context/schema budget. For Qwen's 4,096 context, retain the full 256-token output reserve and report actual tokenizer measurements when an offline matching tokenizer is available. Bytes/4 cannot certify fit.

## Recommended next experiment and proposed versioning

Choose **F only** for the next candidate. The evidence makes retaining the structured prompt's AP facts and explicit semantic generation more compelling than assuming nesting alone caused Revive loss. F changes the provider constraint language while preserving those successful baseline inputs and output meaning. This is a prioritization judgment, not a prediction that F will restore every selected action. Constrained grammar itself can change policy.

Proposed names, not created or registered:

- `arena-control-stepwise-constrained-structured-v1` for the isolated control path.
- `arena-step-legal-action-wire-schema-v1` for deterministic current-catalog schema generation and its provider transforms; persist the generated schema hash for each decision.
- Retain `arena-observation-v2`, `arena-step-prompt-v1`, `arena-turn-plan-schema-v1`, `qwen-config-v1`, game rules and heuristic.
- Retain `arena-step-repair-v1` wording/behavior where compatible; any change to repair messages or repair constraints requires its own explicit version and comparison rather than silently altering V1.
- For comparability with Phase 9C's independent-trial orchestration, propose `arena-benchmark-v5` as a separately frozen recipe binding the new control and wire schema. The new identifier records a different executable experiment contract, not a claim that the seven probes or scoring changed. Reuse `arena-probes-v1`; preserve all old benchmark recipes.

If B is chosen later instead, the appropriate separate names would be `arena-observation-v4`, `arena-control-stepwise-action-id-flat-v1`, unchanged `arena-step-action-id-schema-v1`, and unchanged `arena-step-prompt-v2` only when deliberately isolating flattening. Restoring the lost AP wording at the same time would require a new prompt version and would prevent interpretation as a nesting-only ablation. This is an alternative design description, not a second recommended experiment.

Before live authorization for F: prove exact legal-language equality, reject every invalid reference combination in a fixed adversarial corpus, exercise zero/one-action and empty-catalog cases, compare schema/request/token size, capture fake payloads for both adapters, and prove authoritative command/replay equivalence. Preserve original option order and avoid tactical ranking or added hints. Freeze these results and the proposed request budget for review. A future tactical gate should require Revive recovery across the frozen four repeats and inspect all seven sequences/outcomes for new regressions, with particular attention to Snipe target selection. Passing would support a separately authorized long-match reliability study, not prove it.

## Preservation and verification

All 311 JSON artifacts in the two referenced expanded evidence directories parse. The historical verifier and independent replay succeed for 56/56 trials; final snapshots and mechanical metrics match. Saved observations and state hashes match authoritative execution at all 200 decisions; V2 and underlying V3 ordered catalogs are equal at every reconstructed state. Prompt hashes match all trial manifests.

The task-start inventory covers 7,872 existing files under backend, docs, scripts, tests and traversable `.local` files, plus AGENTS.md, `.env`, and pyproject.toml. All inventoried bytes remain unchanged. Existing dirty source and untracked work were preserved; no runtime packages, frozen versions, historical results, game rules, heuristic, or Empire source were changed. The inventory is a byte comparison, not a filesystem lock, and excludes generated Python caches. Unrelated inaccessible `.local/docker-validation` content was not read or modified.

An initial offline analysis assertion incorrectly required cross-phase provider source identity; it stopped before completing derivation. Its two partial prompt/schema files remain at the directory root, separate from the completed `derived-01` results. Cross-phase differences are now explicitly recorded rather than confused with task-time preservation. No historical artifacts were replaced.

`analyze.py` and `report.py` are local analysis scripts. Runtime network connections were blocked during replay analysis; no provider factory, preflight, tactical probe runner, full-match runner, repair benchmark, or live inference path was called. **Zero live Ollama/OpenAI inference and zero network requests occurred.** No full Python suite was rerun because runtime packages were untouched.

Files created: this report; the new Phase 9D directory containing task-start/final preservation records, the two analysis scripts, complete 200-decision JSON/CSV data, all 36 reconstructed Revive request payloads, full Revive state/catalog/telemetry records, request metrics and source provenance, two prompt texts and schemas, readable catalog appendix, replay verification, and final artifact inventory. The next representation remains a recommendation only.
