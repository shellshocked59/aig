# Arena Phase 7A: action-explicit observation experiment

Implemented offline on 2026-09-13. No live inference, external service request,
provider preflight, or live probe/match was performed. Observation V2 is available
only through explicit selection. Normal gameplay and default/latest remain V1.

## Hypothesis and control

The [V1 postmortem](arena-v1-postmortem.md) found 22 accepted Qwen full-match plans
whose first action was Ranger Attack Cleric at distance 6, outside range 3 and
absent from the starting legal options. V1 groups targets/destinations beneath
units, requiring the provider to associate an actor and reconstruct a plan action.
Luna also repeatedly chose initially illegal actions, separately from failures
caused by earlier actions changing legality.

[Phase 6B](arena-prompt-v2-probe-results.md) did not establish a broad improvement:
Qwen still chose an initially illegal opening action and its accepted probe plans
executed only one AP; Luna improved validity and Revive outcomes but retained four
truncations and reduced mean executed AP from 3.36 to 3.11. Do not create prompt V3
or tune either model in response.

The next controlled hypothesis is that complete, copyable, actor-explicit legal
actions reduce initially illegal selections. This implementation proves catalog
correctness and information preservation, not that either model will obey it.

| Variable | Control | Experiment |
| --- | --- | --- |
| Observation | `arena-observation-v1` | `arena-observation-v2` |
| Prompt, held fixed | `arena-turn-prompt-v2` | `arena-turn-prompt-v2` |
| Logical action schema | `arena-turn-plan-schema-v1` | Same |
| Methodology / probe states | `arena-benchmark-v1` / `arena-probes-v1` | Same |
| Models | `qwen-config-v1`, `luna-config-v1` | Same |
| Engine / scenario | `arena-rules-v2` / `arena-scenario-v1` | Same |
| Control / repair | One full-turn plan; ordered execution; truncate on rejection; one static repair | Same |
| Heuristic | `arena-heuristic-v1` | Same |

**Frozen-prompt limitation:** Prompt V2 literally says legal actions are grouped
under each unit's `actions`. That wording does not describe the V2 layout. It is
preserved byte-for-byte to respect the specified observation-only intervention.
V2 labels its catalog with `legal_actions_state: "turn_start"`; it adds no new
system/user instruction or repair feedback. A negative result must be interpreted
with this representation/prompt mismatch visible. This phase does not establish
that the frozen prompt is an ideal instruction for the flat layout.

## Exact representation

The immutable `ArenaObservation` type accepts two concrete versions. The builder
resolves `version=` using the project's existing version conventions. Explicit V1,
`v1`, `latest`, omitted/empty versions all resolve to V1; explicit V2 or `v2` selects
V2. Unknown versions fail before benchmark output creation or provider construction.

V2 retains the V1 environment/rules/scenario versions, turn, active player, AP,
winner, player identities/names, own/enemy teams, Core records and every unit's
ID, owner, class, position, status, HP and max HP. Action damage/effect rules and
bonus rules remain identical, with no tactical commentary or scores.

Changes from V1:

1. Remove per-unit `actions` wrappers, including empty arrays for enemies/downed
   units. Add one top-level `legal_actions` array and its `turn_start` state label.
2. Every legal entry is the exact output of the existing schema-v1 action variant's
   `to_dict()`. There are no action IDs, `ap_cost`, priorities, ranks or extra fields.
3. Replace repeated per-unit `stats` and `abilities` with shared
   `unit_types[class].stats` and `unit_types[class].action_ranges`. The latter
   retains factual class/range knowledge for actions unavailable now but potentially
   enabled later, including enemy abilities. It is not a second catalog of available
   choices. There are no repeated per-action AP costs; Prompt V2 already supplies
   them. All metadata comes from the existing public-state/domain queries.
4. Replace 45 verbose floor/bonus tile records with board width/height,
   `default_tile: {"terrain":"floor","bonus":null}`, and readable coordinate
   arrays `blocked_tiles`, `power`, `ward`, `siege`. Arrays are row-major, y then x.
   This preserves the entire board; it is not an opaque encoding.

Catalog shapes use the actual schema's `target_id`, not `target_unit_id`:

```json
{"type":"move","unit_id":"blue-knight","destination":{"x":2,"y":1}}
{"type":"attack","unit_id":"actor","target_id":"enemy2"}
{"type":"revive","unit_id":"actor","target_id":"ally"}
{"type":"fireball","unit_id":"actor","target_position":{"x":3,"y":2}}
```

These illustrate shapes across different fixtures, not a proposed plan. Heal,
Finish, Shield Bash and Snipe use the same `type/unit_id/target_id` structure.

Catalog order is ascending **unit ID, action discriminator, target ID, position y,
position x**, with empty target ID / -1 position sentinels where inapplicable.
It never uses tactical desirability. Object keys use existing sorted canonical
JSON; SHA-256 remains the existing canonical digest. Unit/Core input dictionary
insertion order cannot change bytes/hash. No gameplay commands or executor change.

`observation_facts()` losslessly expands V2 for existing internal static validation
and detached simulation. AP metadata is recovered from existing `ACTION_COSTS`.
This expanded view is never sent to models. Tests compare the entire expanded
object with V1, so preservation includes information beyond a selected field list.
`ArenaObservation.from_dict()` reconstructs state and regenerates the selected
contract, rejecting forged metadata, catalogs or ordering.

## Starting legality and execution

Catalog entries mean legal **as the first action from the observed state**, at
the observed AP budget. They do not promise continued legality after earlier
actions. Damage, movement, revival, displacement and victory retain their current
sequential effects. Later actions may be absent initially yet become executable.

The pure `is_starting_legal_action(observation, planned_action)` checks exact
canonical catalog membership for V2 and equivalent actor-specific membership for
V1. It rejects unknown/extra fields. It is used only for passive benchmark metrics;
neither static acceptance nor execution requires membership.

`starting_legality` keeps its existing fields: first-action membership (null for
empty plans), a membership vector for all planned actions, and prefix length ending
at the first nonmember. Full-plan starting legality is `all(membership)`; report
empty plans separately. Two Snipes can both be starting-legal while the second
fails after the first downs its target. A Revive-then-Act sequence may be valid
despite the second action being absent initially. Neither is a metric bug.

## Offline reconstruction and sizes

Reproduction, with a new output filename:

```powershell
.venv/Scripts/python.exe scripts/arena-observation-study.py --history .local/arena-phase5-fullmatches-20260913-01 --output .local/arena-phase7a-study-repeat.json
```

The script constructs/invokes no model provider and refuses to overwrite
an existing result. [Complete reconstruction evidence](../.local/arena-phase7a-verification/reconstruction.json)
contains sources, V1/V2 hashes, catalog counts, execution checks and token estimates
for all seven frozen probes and all **153 stored full-match observations** (including
heuristic turns and failed-call observations). It reconstructs each stored V1 row
and checks its historical hash before projecting V2.

| State | V1 bytes | V2 bytes | Delta | Reduction | Actions / explicit actors |
| --- | ---: | ---: | ---: | ---: | ---: |
| Finish/Core, simple probe | 4,555 | 3,029 | -1,526 | 33.50% | 19 / 19 |
| Fireball friendly fire | 5,667 | 6,297 | +630 | -11.12% | 70 / 70 |
| Revive | 4,581 | 3,151 | -1,430 | 31.22% | 21 / 21 |
| Shield Bash | 4,155 | 2,923 | -1,232 | 29.65% | 24 / 24 |
| Snipe | 4,603 | 3,385 | -1,218 | 26.46% | 25 / 25 |
| Team Elimination | 4,560 | 3,038 | -1,522 | 33.38% | 22 / 22 |
| Winning Core | 4,736 | 4,010 | -726 | 15.33% | 35 / 35 |
| Opening / historical Qwen failure | 7,397 | 6,462 | -935 | 12.64% | 54 / 54 |
| Midgame, Luna self match 01, observation 11, turn 5 Blue | 5,947 | 3,519 | -2,428 | 40.83% | 15 / 15 |

Mean frozen probe bytes: **4,693.86 -> 3,690.43**, a 21.38% reduction. Mean over
the 153 historical match observations: **6,924.98 -> 5,370.64**, a 22.45% reduction.
**Zero of 153 match observations grew.** Fireball is the important exception among
probes: 70 complete action objects outweigh the saved wrappers/board metadata.
Its V2 observation is still smaller than the V2 opening, but its larger request
must remain visible in the future context/behavior analysis. No legal entries or
state facts were removed to force a size win.

Representative deterministic V2 hashes:

| State | SHA-256 |
| --- | --- |
| Simple Finish/Core | `dc2e48570dcca212d78f31f0cac10173d7407f7164cbe98b6a7e8e58492752e2` |
| Revive | `52a7fa2ed56b339b7c1025a9030ada6c59591a381f1722f68a9378f141485cf5` |
| Opening / Qwen distance-6 failure | `e018b244179069ebcfcca33a5c8266f2b18bc99c64c2774f6868db466965c08c` |
| Midgame | `b366e7ea70e6fbf84183bea376585733078a260c0a902bd5a768b85133a84dc2` |

All **6,270 catalog entries** across those 160 samples were parsed through the
schema-v1 action constructor, converted to an existing Arena command, applied to
a fresh detached copy, and verified to consume exactly the domain AP cost. Tests
also cover every AP budget 0..5, all eight action types (including an injured-unit
Heal fixture), blocked moves, invalid Finish/Revive, wrong-class abilities, and
out-of-range attacks. These are finite offline invariants, not an exhaustive proof
over every possible Arena state; production enumeration uses the same authoritative
queries/validator as command execution.

All **22 historical Qwen accepted failures** were reconstructed. Each attempted
Ranger Attack Cleric at distance 6 is absent from V2. All actual Ranger choices are
explicit and exactly equal in count/content to V1's legal choices. In these states
Ranger has legal Moves, but no legal Attack or Snipe; the audit does not invent one.
Separate Snipe fixtures verify explicit legal Ranger attacks and special actions.
This structurally exposes the correct choices without proving model compliance.

## Qwen request and context assessment

[Fake-transport request measurements and V1 comparison](../.local/arena-phase7a-verification/request-size-and-v1-preservation.json)
hold prompt, schema, options and repair feedback fixed. Current local inference
settings matched both frozen model profiles; no setting or `.env` was changed.

| Serialized request | Observation V1 | Observation V2 |
| --- | ---: | ---: |
| Opening Ollama request bytes | 14,617 | 13,452 |
| Opening OpenAI SDK argument bytes | 14,236 | 13,071 |
| Midgame Ollama request bytes | 12,847 | 9,915 |
| Midgame OpenAI SDK argument bytes | 12,466 | 9,534 |

OpenAI measurements are local argument serialization, not HTTP capture. Escaping
means serialized request-byte deltas differ from observation-byte deltas. The
opening Ollama request shrinks 1,165 bytes (7.97%). No exact Qwen tokenizer is
installed locally (`tiktoken`, `transformers`, `tokenizers`, `sentencepiece` absent);
no package/model download or external tokenizer service was used.

Use the observed Prompt-V2/Observation-V1 opening **3,317 input tokens** as an
anchor, then estimate the signed observation character delta at 3..4 characters
per token. Prompt/schema/framing stay constant. Within 4,096 context, reserving
the unchanged 256 output tokens:

| V2 state | Estimated input tokens | Estimated remaining context |
| --- | ---: | ---: |
| Opening | 3,005–3,083 | 757–835 |
| Midgame | 2,024–2,348 | 1,492–1,816 |
| Simple Finish/Core | 1,861–2,225 | 1,615–1,979 |
| Revive | 1,902–2,256 | 1,584–1,938 |
| Fireball (largest probe) | 2,950–3,042 | 798–890 |

Opening headroom rises an estimated **234–312 tokens** from 523. These are rough
character-based estimates, especially across different fixtures, not tokenizer
counts or proof of server-side fit. Repair feedback uses additional context.
Fireball's V1-to-V2 growth corresponds to roughly 158–210 additional tokens under
the same approximation. Keep actual token telemetry and stop on context failures;
do not increase context/output allowances or automatically retry.

## Selection, provenance and observability

Both existing model providers serialize the explicitly built observation directly:

```python
observation = build_observation(state, version="arena-observation-v2")
provider.create_turn_plan(observation)  # provider constructed with prompt_version="arena-turn-prompt-v2"
```

No separate provider implementation or settings profile exists. The shared model
trace records `observation_version`; the same selected observation is reused in
repair. Normal controllers continue to call the V1-default builder.

The benchmark adds `--observation-version`, resolved before execution. It applies
to the built-in preflight and every trial observation. New experiment/trial
manifests record concrete `observationVersion` and `baseRecipeObservationVersion`;
V2 adds `experimentOverrides.observationVersion` alongside the prompt override.
They retain prompt/hash, plan-schema, benchmark/probe/hash, rules/scenario, frozen
model profile/configuration, source revision/dirty status and backend source hashes.
Plan/inference/preflight rows also carry the concrete observation version; saved
observation objects carry `schema_version` and their own canonical hash.

The immutable benchmark recipe and probe-state artifacts are unchanged. Their
historical V1 observation hashes remain V1 hashes. Replay selects the manifest's
observation version; historical manifests lacking the field mean **V1**, never a
moving latest pointer. No old manifest or evidence is rewritten.

**Rejected-output capture is unchanged.** The provider's in-memory trace already
retains bounded, configured-secret-redacted content after envelope extraction;
`safe_inference` deliberately omits arbitrary text from persisted evidence. A
malformed response may mix prose/reasoning with JSON, and indiscriminately saving
that string would not meet the requested no-reasoning guarantee. This secondary
capture change is deferred; rejected raw output remains unavailable in saved
benchmark evidence. No prompt, repair, transport, error category or deterministic
behavioral hash projection was changed for observability.

## Future A/B metrics and interpretation

Compare Prompt V2 / Observation V1 against Prompt V2 / Observation V2 **within each
model**. Do not compare Qwen's partial Phase 6B schedule as if it had complete
coverage. Report matched fixtures and all intended/started/unstarted denominators.

- Primary: first-action starting-legal rate among nonempty accepted plans; report
  empty plans separately. Audit the built-in opening preflight separately from probes.
- Starting prefix: mean prefix length and full-plan starting-legal rate, keeping
  membership separate from dynamic execution.
- Static validity: first-response validity, repair attempts/success, failed trials,
  including failures rather than only valid-trial summary distributions.
- Dynamic sequencing: execution truncations, invalid index, exact rejection reason;
  separate initially illegal actions, changed legality and terminal suffixes.
- AP: planned/executed/unused AP, full-five-AP rate and <=2-AP rate, with accepted
  sample count and terminal leftovers visible.
- Objectives: retain every existing probe metric, action sequence and outcome;
  no new aggregate tactical score or heuristic ranking.

If legality, Qwen validity and executed AP materially improve without unacceptable
outcome regressions, request separate authorization for Observation V2 full-match
testing before changing control mode. If initial legality improves but sequential
truncation remains high, stepwise control or bounded replanning is the next likely
independent experiment. If initial legality does not improve, action-ID selection
or stepwise control may be worth testing, with the frozen-prompt mismatch taken
into account. Those changes are not implemented here and require new decisions.
Full-turn planning remains one inference per planned turn; changing to repeated
state feedback would change a much larger variable than this representation test.

## Exact next live commands — not executed

Run only after explicit authorization, from `C:\code\aig`, with unused output
directories. Each schedules seven frozen probes times four intended trials; fail
fast can leave later trials unstarted. No full matches or extra standalone
preflights are authorized by this document.

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider ollama --prompt-version arena-turn-prompt-v2 --observation-version arena-observation-v2 --probe all --probe-trials 4 --strict-provider --output .local/arena-phase7a-qwen-observation-v2-probes-20260913-01
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --blue-provider openai --prompt-version arena-turn-prompt-v2 --observation-version arena-observation-v2 --probe all --probe-trials 4 --strict-provider --output .local/arena-phase7a-luna-observation-v2-probes-20260913-01
```

Each command includes one unrepaired opening preflight plus 28 trial initial calls
and at most one repair per trial: **57 requests per provider, 114 combined**.
Without repairs, a completed schedule uses 29 each. These ceilings do not authorize
retries, replacement trials, continuations, or use of unspent requests elsewhere.
Preserve failed artifacts and stop on failure. The workspace Ollama connectivity
procedure applies to future sandbox transport failures, but no connectivity check
or inference was performed in this phase.

**Stop point:** offline implementation/verification only. Request authorization
before either live command. Do not run V2 full matches, tune profiles, revise
prompts, or implement action IDs, stepwise control or replanning.

## Files and verification

Added `tests/test_arena_observation_v2.py` (16 tests), the provenance-labeled
`tests/fixtures/arena-observation-v1-midgame.json`,
`scripts/arena-observation-study.py`, and this document. Updated observation
construction/expansion, static validation's input view, passive membership metrics,
model trace provenance, benchmark selection/replay/manifests, and the two reference
documents. Existing Phase 6B edits were treated as the baseline, not discarded.

Verification logs and before/after inventories are in
`.local/arena-phase7a-verification/`. The original pre-edit V1 builder was compared
byte-for-byte with the current builder on **162 samples**, including all 153 saved
full-match observations, the opening, seven probes and the selected midgame.
Frozen probe hashes, the opening V1 hash and the saved midgame bytes are also
regression tests. V1 opening remains 7,397 bytes / SHA-256
`d11799c7e917d3353962ca104b87f14b3fc64f6f35b2e9ff169baa7656c48279`.

Both prompt byte hashes remain:

- V1: `5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7`
- V2: `5281b87501c4958949c640fe86675ef02b6349010fc0893287dd5aba2a30ed29`

The new tests cover version/default resolution, V1/V2 hash pins, lossless facts,
ordering, exact action shapes/AP execution, all specials, illegal-action absence,
the historical Qwen defect, passive metrics, unchanged static validation and
heuristic plans, forged facts, both fake provider payloads/repairs, CLI propagation,
manifest controls, historical V1 fallback and early unknown-version failure.

| Final verification | Result |
| --- | --- |
| Python suite | **1,078 total; 1,073 passed, five existing platform skips**, 150.766 seconds |
| New observation tests | **16 passed**, with live transport guards |
| Frontend tests / production build | **76 passed**, zero failures / passed |
| V1 byte identity against pre-edit builder | **162/162** samples |
| Catalog first-command execution / AP checks | **6,270/6,270** in historical reconstruction, plus tests over AP 0..5 and injured Heal |
| Phase 3 | All five pinned hashes identical to Phase 6B baseline |
| Phase 5 offline baseline | Existing tests preserve four-match hashes and two repetitions of each frozen probe's hashes, metrics and outcomes |
| Preservation inventory | 4,660 pre-existing files checked; only eight intended existing files changed; none removed |
| Historical evidence, including Phase 5/6A/6B | **4,480 files byte-identical**, none removed |
| Empire | **39 backend files byte-identical**; frontend source unchanged; existing regression suite passed |
| Frozen Arena rules, commands, executor, prompts, schema, heuristic and artifacts | Byte-identical to the pre-edit checkout |
| Rejected-output persistence | Unchanged; deferred |
| Live inference / external service requests | **Zero** |

Full inventories and the five Phase 3 hashes are in
[preservation.json](../.local/arena-phase7a-verification/preservation.json) and
[phase3-hashes.json](../.local/arena-phase7a-verification/phase3-hashes.json).
The Phase 3 AI trace remains
`9a516d715155f2c66126a26fce5b1e91edb0cd20ada4b76f08caa9bb6190b4a1`;
plan array remains
`5aee176a981a7df5eaca150e79c6f3998b55de684322ec9fb7b9f76d0fa4397c`.
Verification commands were `.venv/Scripts/python.exe -m unittest discover -s tests`,
`npm.cmd test`, and `npm.cmd run build`. Model calls in tests/request measurement
used fakes; engine simulation/replay remained offline. Both prepared live output
directories were absent at the stop point. No GitHub operation or commit was made.
