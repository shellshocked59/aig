# Arena Phase 6B: authorized V2 probe results

2026-09-13. Both authorized schedules have stopped. **40 inference requests total**:
Qwen 11, Luna 29. No retries, continuations, full matches, profile changes, prompt
revisions or gameplay source changes were made during collection.

**The observed results do not establish a broad prompt-V2 improvement.** Qwen still
produces one-action turns and an initially illegal opening action, and fails the
first Revive trial after repair. Luna improves first-response validity and Revive
outcomes, but has unchanged execution-truncation frequency and lower mean executed
AP. These small, repeated fixed-state samples do not isolate model capability or
justify promoting V2 as the gameplay default.

## Evidence and request accounting

| Provider | Intended trials | Started | Valid / failed | Unstarted | Preflight / initial / repair requests | Total |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| Qwen | 28 | 9 | 8 / 1 | 19 | 1 / 9 / 1 | 11 |
| Luna | 28 | 28 | 28 / 0 | 0 | 1 / 28 / 0 | 29 |

Each schedule was authorized for at most 57 requests. Unused request capacity is
not used for retries or replacement trials. Qwen's exit status was `trial_failed`;
Luna's was `complete`. Both used the existing strict benchmark preflight, which
checks static acceptance and provider provenance, not dynamic execution legality.
No fallback occurred.

- [Qwen run summary](../.local/arena-phase6b-qwen-v2-probes-20260913-01/summary.json)
- [Luna run summary](../.local/arena-phase6b-luna-v2-probes-20260913-01/summary.json)
- [Reproducible offline comparison](../.local/arena-phase6b-live-20260913-01/analyze.py)
- [Detailed comparison, accepted plans, telemetry and metrics](../.local/arena-phase6b-live-20260913-01/comparison.json)
- [Frozen V1 probe comparison](../.local/arena-phase5-continuation-20260913/comparison.json)

V1 Qwen's 28 attempts were previously collected through separately authorized
continuations. V2 stopped at its first failed trial. Consequently, overall Qwen
V1/V2 percentages have different fixture coverage and must not be interpreted as
a controlled aggregate gain. The matched completed fixtures are examined below.

## Frozen controls and preservation

Both run manifests record `arena-turn-prompt-v2`, its frozen hash and explicit
override of the original recipe, alongside `arena-benchmark-v1`, `arena-probes-v1`,
`arena-turn-plan-schema-v1`, `arena-rules-v2`, `arena-scenario-v1`, their model
profile, source revision/dirty state and source inventory. Qwen uses
`qwen-config-v1`; Luna uses `luna-config-v1`. The only model-facing experimental
change from V1 is the base prompt. Observation serialization, wire schemas,
profiles, repair feedback, executor, rules and heuristic remain unchanged.

All **84 inventoried backend source files** and **1,436 inventoried prior evidence
files** were byte-identical before and after collection. The preservation results
are in the comparison JSON; inventories are `source-before.json` and
`evidence-before.json` in the same local analysis directory. All **93 retained
trials** used for comparison replayed exactly: 56 historical model probe attempts
plus 37 V2 attempts, including failed-trial prefixes. Accepted observations were
reconstructed through authoritative queries, and saved V2 membership measurements
were independently recomputed. Historical artifacts were read, never rewritten.

Before inference, a read-only Ollama `/api/version` check failed inside the sandbox
with socket `WinError 10013`, then returned HTTP 200 / version 0.34.0 outside it.
Both authorized inference commands used escalated execution permissions. Those
two version checks are not inference requests. No inference request was repeated
to work around connectivity, and the Qwen trial failure below was a validation
failure with returned token telemetry, not this sandbox connectivity issue.

## Qwen: matched fixtures show no contract/AP improvement

| Matched fixture | V1 | V2 |
| --- | --- | --- |
| Finish/Core, four trials each | Four one-AP Core attacks; 24 total Core damage | Identical actions, AP and Core damage |
| Fireball friendly fire, four trials each | Two basic attacks per plan; 2 AP and 12 damage per trial | One basic attack per plan; 1 AP and 6 damage per trial |
| First-action starting legality on those eight plans | 8/8 | 8/8 |
| Mean planned / executed AP on those eight plans | 1.50 / 1.50 | 1.00 / 1.00 |
| Mean starting-legal prefix length on those eight plans | 1.50 | 1.00 |
| Execution truncations on those eight plans | 0/8 | 0/8 |

All eight accepted V2 plans leave four AP unused; none is terminal. The added
continuation instruction did not increase useful turn length in these fixtures.
Neither version casts Fireball in the Fireball fixture.

The ninth trial, `revive_decision/run-001`, returns `invalid_reference` on both
initial and repair attempts and ends with `repair_failed`. V1 failed all four
Revive attempts with `invalid_ability`. Rejected raw output remains unavailable
under the frozen evidence policy, so the exact invalid V2 actor/target cannot be
reconstructed. There is no accepted plan or AP/membership sample for that trial.
The remaining three Revive trials and all Shield Bash, Snipe, Team Elimination
and Winning Core trials were not started.

The V2 opening preflight returns one action:
`blue-mage -> attack -> red-cleric`. It is absent from the Mage's starting legal
list. This is the same first-action contract failure category as V1's Ranger
attack, with a different actor. It was statically accepted; the preflight does
not execute it. This observation is kept separate from probe rates and is not a
V2 full-match result.

For completeness, whole retained populations are V1 24/28 first-response valid,
20/24 first-action starting-legal, four execution truncations, four unsuccessful
repairs; V2 8/9 first-response valid, 8/8 starting-legal, zero truncations and one
unsuccessful repair. **The apparent legality/truncation improvement is not evidence
of improvement on comparable fixtures:** the V1 Snipe failures have no V2 samples.
All accepted plans in both populations use at most two planned/executed AP, and
neither population contains a full-five-AP turn.

## Luna: complete within-model comparison

Both columns cover the same seven probes with four trials each. AP, prefix and
execution statistics use the 28 accepted plans. First-action membership uses the
28 nonempty accepted plans; there are no empty plans. Preflights are excluded.

| Metric | Luna V1 | Luna V2 |
| --- | ---: | ---: |
| First-response static validity | 27/28 | 28/28 |
| Repairs attempted / successful | 1 / 1 | 0 / 0 |
| Failed trials | 0/28 | 0/28 |
| First-action starting-legal | 28/28 | 28/28 |
| Mean starting-legal prefix length | 3.57 | 3.04 |
| Mean planned AP | 4.04 | 3.89 |
| Mean executed AP | 3.36 | 3.11 |
| Mean unused AP | 1.64 | 1.89 |
| Planned full-five-AP plans | 12/28 (42.9%) | 7/28 (25.0%) |
| Executed full-five-AP turns | 10/28 (35.7%) | 5/28 (17.9%) |
| Plans with <=2 planned AP | 0/28 | 2/28 (7.1%) |
| Turns with <=2 executed AP | 8/28 (28.6%) | 10/28 (35.7%) |
| Execution-invalid truncations | 4/28 (14.3%) | 4/28 (14.3%) |

Prefix membership describes the unchanged starting list, not subsequent dynamic
legality. A smaller prefix need not imply a worse sequence. Similarly, low
executed AP can reflect victory; terminal leftovers remain included and are not
automatically evidence of an early-stop defect.

Luna V2's four dynamic rejections are:

- Fireball fixture: action index 2, basic Attack on `enemy2`, incompatible target
  ACTIVE/DOWNED status.
- Shield Bash fixture: action index 2, Finish on `enemy`, incompatible target
  ACTIVE/DOWNED status.
- Team Elimination fixture: two plans reject at index 1, basic Attack on `enemy`,
  target outside action range.

All indices are zero-based. These remain measured executor outcomes, with no
dynamic repairs. V1 had one invalid Move at index 4 and three range rejections at
index 1; the number of truncations is unchanged although the errors differ.

## Luna probe outcomes and tradeoffs

| Fixture, four trials each | V1 | V2 |
| --- | --- | --- |
| Winning Core | 4/4 wins; 36 total Core damage | 4/4 wins; 36 total Core damage |
| Team Elimination | 2/4 wins; two range truncations | 2/4 wins; two range truncations |
| Revive | Ally active in 1/4; one Revive | Ally active in 3/4; three Revives |
| Fireball friendly fire | No Fireballs; 84 damage, four downs, no Finishes | No Fireballs; 60 damage, four downs, two Finishes |
| Shield Bash position | One Bash/push; 58 damage; three downs | No Bash/push; 66 damage; three downs |
| Snipe versus basic | Eight Snipes; 64 damage; four downs | Eight Snipes; 64 damage; four downs |
| Finish/Core | 120 Core damage; no Finishes | 84 Core damage; two Finishes |

Damage and action counts in this table are totals across each fixture's four
trials, not a tactical score. V2 also casts one Fireball in the **Revive** fixture,
hits three active units, and inflicts eight friendly-fire damage there. No
friendly-fire damage is recorded in the corresponding V1 fixture. More Revives
and Finishes coexist with damage/AP tradeoffs; neither ability use nor AP spent
alone establishes superior tactics. Full per-player Phase 5 metrics and ordered
plans are retained in the comparison JSON.

## Observed Qwen context usage

The V2 opening preflight reports **3,317 input + 34 output tokens**. The same
opening observation under the frozen V1 prompt had reported 3,067 input tokens:
the observed input increase is 250, versus the earlier rough 279–372 estimate.
With the configured 4,096 context and 256 output allowance, the V2 opening leaves
**523 tokens after reserving the complete output allowance**. The failed Revive
initial/repair calls report 2,253/2,284 input tokens and 33/34 output tokens.
No context-limit error was observed. These counts do not prove server-side
truncation internals, but do not support diagnosing this failure as overflow.
No context/output settings were changed.

## Stop point

Collection and offline analysis are complete for the two authorized commands.
Qwen's partial schedule remains partial. No full-match experiment is launched,
and V2 is not promoted to normal gameplay. The evidence supports retaining the
mixed/negative result rather than assuming prompt clarity solved the observed
contract problems. Any Qwen continuation, new prompt, structural intervention or
full-match evaluation requires a separate decision and authorization.
