# Scenario V4 offline verification

Four heuristic trials (two paired runs) completed on 2026-09-11, with a cap of
150 global turns. Every trial reached conquest at turn 90, activation 396. C won
with five cities, 26 population and 250 military strength. Each trial had eight
captures, three eliminations, 191 attacks, 73 created plans and 234 plan reuses.
All four initial-state, final-state, command and plan hashes match. No model
requests, repairs or fallback plans occurred. Runtime was about ten seconds of
simulation per trial on this machine, excluding replay and report overhead.

Artifacts: `.local/scenario-v4-final-verification/summary.json` and `runs/` (ignored local
outputs). Reproduction command is in [Scenario V4](scenario-v4.md). The source
revision was `dad2e55c15196e045ac95bbde2d69b2a905a7910` with a dirty working tree;
that revision alone does not identify this implementation. Source file hashes
are saved beside the local verification report.

| Elimination order | Victim | Killer | Turn |
| --- | --- | --- | --- |
| 1 | A | C | 38 |
| 2 | D | C | 86 |
| 3 | B | C | 90 |

C personally eliminated all three rivals in these trials. Separate regression
coverage verifies that conquest also works when another civilization eliminates
a rival first. Captures were distributed A:0, B:1, C:5, D:2; losses A:1, B:2,
C:1, D:4. The city `ai-city-unit-34` changed owners D -> B -> D -> C -> D -> C
at turns 61, 65, 66, 77, 84. Its final capture was followed by D's original city
at turn 86 and B's city at turn 90. Three captures were recaptures.

| Player | Distinct primary rivals | Enemy switches | City switches | Mean consecutive new plans per same-rival streak | Maximum simultaneously visible rivals |
| --- | --- | --- | --- | --- | --- |
| A | C, D | 3 | 1 | 1.5 | 1 |
| B | C, D | 4 | 3 | 5.0 | 1 |
| C | A, B, D | 6 | 7 | 3.6 | 2 |
| D | B, C | 7 | 3 | 2.8 | 2 |

Switches include transitions to/from null and exclude the initial plan. Targeting
activation counts: A targets C:10/D:5; B targets C:18/D:47; C targets A:23/B:9/D:38;
D targets B:17/C:43. C had two replans transitioning from an eliminated primary
enemy. C had one and D had two replan samples with military units of multiple
rivals within three tiles of an own city.

Primary-target sequences (turn: target):

- A: 0:null, 17:C, 27:null, 34:D.
- B: 0:null, 16:D, 21:null, 31:D, 73:C.
- C: 0:null, 16:A, 39:null, 44:D, 61:B, 66:D, 87:B.
- D: 0:null, 16:B, 21:null, 26:B, 36:null, 41:C, 64:B, 66:C.

These are factual switches, including returns to previous rivals. No strategic
quality score or judgment that a switch was unnecessary is assigned. The heuristic
was not tuned to finish weaker enemies or to force victory. Its only candidate
selection change rejects publicly eliminated owners; plan validation, cached-plan invalidation and executor
target use enforce the same rule, including city targets with a null primary enemy. Historical city records remain in knowledge,
StrategicState, public state and the filtered map for fog-consistent occupancy.

Initial tactical contact was absent for every player. C eventually explored all
192 tiles; A/B/D explored 57.8125%/52.0833%/80.7292%. All five camps were cleared,
with the existing total 125 Gold reward. Six Warriors spawned beyond the five
initial camp Warriors; maximum concurrent barbarian units was six. Spawn behavior,
unit limits, resources and fog rules were validated without modification.

`scripts/audit-benchmark-knowledge.py` replayed each of the four runs independently.
Per run, it verified all 73 exact StrategicState replan payloads, all 307 normal
activation plan references (including reused plans), visible enemy/barbarian unit
positions and discovered resource positions, intermediate elimination snapshot
round-trips, authoritative state validation, and the final snapshot. No invalid
dead-target reference occurred at an activation boundary. Targets may naturally
be captured or eliminated during the activation that executes their plan.

| Deterministic artifact | SHA-256, identical across all four runs |
| --- | --- |
| Initial state | `29d27b3fb50dd5a4ad2b11319eb81af29d532f826c890db908abce9649f62688` |
| Final state | `d246cfb5e6fd2c4edad643e221177cc6f8c49be97680db6a1b72f80744117e45` |
| Commands | `8f274409746ee08302daa536e7a285c530747df56a0571759844106a90909f76` |
| Plans | `dd74d70381af016cb35c0d6b6e9b5a8aeb6718d056b0cf1c703f45a15271520e` |

Versions: environment-v5 (unchanged latest), scenario-v4 (promoted after offline
verification), strategy-prompt-v1 (unchanged default), strategy-prompt-v2 (unchanged
experimental option), strategic-plan-schema-v1, luna-config-v1, qwen-config-v1,
benchmark-v1 and snapshot schema 12. No environment-v6 or new mechanics exist.

Validation: baseline 780 Python tests, one pre-existing failure and five skips;
full post-promotion suite 793 Python tests, five skips. Subsequent focused checks
passed all 13 scenario tests and 67 AI tests after the final cache/aggregation refinements. Frontend increased from 40 to 42 passing tests;
build passed, including the existing secret-exclusion build test. Normal tests use
mock transports and made no live model requests. Frozen scenario V1-V3 canonical
setup hashes, prompt V1/V2 payload hashes, plan schema, model profiles and preserved
reports/archives pass regression checks. The pre-existing failure was the V4
fixture hashing the whole prompt registry before the additive V2 definition;
its historical V1 payload is now checked instead. Baseline-document checks hash
the exact historical bytes preceding the appended V4 section. No historical
fixture digest was changed and neither prompt was edited.

Files changed for this slice (separate from pre-existing dirty checkout changes):

- `backend/aig/scenarios.py`, `backend/aig/versions.py`.
- `backend/aig/ai/strategy.py`, `plan_schema.py`, `controller.py`, `executor.py`, `simulate.py`.
- `backend/aig/ai/benchmark.py`, `benchmark_metrics.py`, `conquest_metrics.py`, new `multifront_metrics.py`.
- `frontend/src/js/game.js`, `presentation.js`, `frontend/src/css/main.css`.
- `tests/test_scenario_v4.py`, `test_barbarians.py`, `test_resources.py`, `test_experiment_versions.py`.
- Historical two-player fixtures in `tests/test_benchmark.py`, `test_benchmark_preflight.py`,
  `test_knowledge.py`, `test_openai.py`, `test_provider_selection.py` now explicitly select V3.
- `frontend/tests/game.test.js`, `scripts/audit-benchmark-knowledge.py`.
- `docs/scenario-v4.md`, `scenario-v4-verification.md`, `benchmarking.md`, `baselines.md`.

The public DTO, capture rules, elimination rules, turn-order machinery and
StrategicState collections already support arbitrary civilization IDs. UI-only
A/B assumptions in colors, legend and status copy were removed. The smoke simulator
now accepts explicit scenario selection and respects global turn caps even after
roster shrinkage. Cross-scenario benchmark comparisons use shared player IDs and
flag differing rosters. Snapshot representation did not change.

Limits for interpreting future experiments: the harness assigns one provider to
all normal factions per trial; mixed providers in one match are not exposed.
The planner schema intentionally selects one primary enemy/city at a time. Enemy
military strength retains its existing aggregate plus public per-civilization
metrics. Known hidden cities can retain an eliminated historical owner; the global
civilization list identifies that owner as eliminated, and validation rejects it.
Four identical trials establish reproducibility, not balance or independent win
rate evidence. Multi-front proximity samples are descriptive, not tactical attack
predictions. Browser launch remains the two-player V3 demo, while engine/benchmark
APIs and the explicit smoke-simulator flag expose V4.

Scenario V4 is ready for controlled Luna prompt-v1 vs prompt-v2 comparison.
No live comparison or prompt promotion was performed.

## Previous-plan contract correction (2026-09-11)

The subsequent offline prompt-comparison prerequisite check found that activation
196 (turn 39, C) passed its invalid A/`ai-city-unit-1` plan to the provider even
though the controller had selected `invalid_target`. The earlier audit checked
new/reused plans and StrategicState, but missed provider previous-plan context.
The historical reports and runs above remain unchanged.

The source correction clears that context before primary/fallback invocation and
retains the old plan only as `invalidated_previous_plan` diagnostics. Valid expired
or significant-event plans retain continuity. Benchmark change and eliminated-target
metrics use the diagnostic copy, preserving their factual definitions. The knowledge
audit now validates supplied previous plans and rejects the preserved faulty trace.

Four new offline heuristic trials are saved under
`.local/previous-plan-fix/simulations/`, with detailed audits in
`.local/previous-plan-fix/verification.json`. Each reproduces turn 39 with
`previous_plan: null` and reaches C's conquest at turn 90, activation 396.
All gameplay metrics, eight captures, three eliminations, 73 replans and 234 reuses
match the preserved trial. Each independent command replay verifies all 73
StrategicState and provider previous-plan inputs, 307 activation knowledge
boundaries, visible units/resources, elimination snapshot round-trips and final state.

Initial-state, final-state and command hashes remain exactly those in the table
above. The corrected plan-trace hash is identical across all four new trials:
`6a6574263969c09fbe9eb5f33514f580ca7070c236bdf42eb83fd94219c0bfa7`.
The trace hash changes because previous input and invalidation diagnostics are now
separate; gameplay, prompts, scenario/environment/model versions and snapshot v12
do not change. Public eliminated-player records and fog-consistent historical city
facts remain valid StrategicState data; they are not previous-plan instructions.

Focused tests also cover B eliminating A before C replans, a third-party capture
while A survives, removed/unseen targets, valid periodic/contact continuity,
heuristic fallback, both frozen prompts through fake OpenAI/Ollama transports,
and no provider call after terminal conquest. No live model calls occurred and
the heuristic verification blocked external connections. A fresh offline
verification/authorization cycle may begin; no live comparison was resumed.

Validation for this correction: baseline 793 Python tests (five skips); final
805 tests (five skips), including 12 new regression methods with provider/event/
reference subcases. Frontend: 42 passing tests and successful build before and
after. The final suite's external-connection guard recorded zero attempts (the
Windows standard-library internal socketpair remains permitted). All 2,152
pre-existing local artifacts and all frozen fixture files retain their pre-fix
digests; the configured-secret scan found no leaks. Source SHA remains
`dad2e55c15196e045ac95bbde2d69b2a905a7910`, dirty before and after; before/after
status and content manifests are saved in `.local/previous-plan-fix/`.
