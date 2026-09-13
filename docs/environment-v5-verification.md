# Environment V5 implementation and verification

The V5 implementation is ready for a separately authorized Heuristic vs Luna
comparison. No live OpenAI or Ollama request was made. Existing uncommitted V4,
provider and benchmark work was retained; no commit, deployment or GitHub
operation was performed.

## Implementation report

| Area | Result |
| --- | --- |
| Total war | Identity/faction-kind helper; every other civilization and barbarians are hostile; no diplomacy state |
| Capture flow | Existing MoveUnit validates state, occupancy, path and budget before committing movement, capture and cleanup |
| Eligible units | Warrior, Scout, Spearman; derived from melee strength and absence of ranged strength |
| Defenders | All hostile occupants must be removed; killing the final defender alone never captures |
| Population | `max(1, old_population - 1)` on every capture/recapture |
| Food | Stored food resets to zero |
| Production | Stored production resets to zero; target clears |
| City identity | ID, name, location, terrain and resource preserved |
| Tile ownership | Center changes immediately; surrounding ownership retained |
| Fog | Witnesses learn the new owner; hidden third parties keep last-seen owner; observer sees truth |
| Historical ownership | Required persistent boolean `has_ever_owned_city`; set by founding/addition/capture |
| Elimination | Last-city loss eliminates historical owners immediately, regardless of remaining Settlers/military |
| Cleanup | Units and activation-order entry removed; historical player and knowledge retained |
| Victory | Persistent `GameResult` with winner and `VictoryType.CONQUEST`; exactly one normal survivor |
| Terminal lifecycle | No active player, subsequent commands, economy, research, production or barbarian activation |
| Barbarians | Cannot capture, do not count toward victory, existing camps/units remain at victory |
| Shared executor | ATTACK routes eligible units into known target cities and stops immediately at victory |
| Heuristic | No planner policy or aggression changes |
| Prompt | v1 audited and unchanged; no contradictory claims; no v2 needed |
| Plan schema | v1 unchanged; existing ATTACK/target city fields suffice |
| Scenario | v3 unchanged; natural contact/capture makes a redundant v4 unnecessary |
| Benchmark | v1 retained; additive victory/capture/elimination observations |
| Snapshot | v11 → v12; required flag/result; strict side-effect-free loading; older schemas rejected |

Full rule and metric definitions are in [Environment V5](environment-v5.md).
Captured cities can receive new orders and participate in the captor's current
EndActivation economy unless capture ends the game. Enemy cities cannot be
intermediate steps in a multi-tile command: each entry resolves its capture
before a subsequent command can continue. These are explicit lifecycle choices,
not unresolved ambiguities.

## Files changed for this slice

Domain and persistence: `backend/aig/state.py`, `movement.py`, `combat.py`,
`economy.py`, `barbarians.py`, `knowledge.py`, `public_state.py`, `snapshots.py`,
and `versions.py`.

AI and measurement: `backend/aig/ai/knowledge_planning.py`, `executor.py`,
`strategy.py`, `simulate.py`, `benchmark.py`, `benchmark_metrics.py`, and new
`conquest_metrics.py`. No provider, prompt, model-profile or scenario data was
changed for V5.

Browser: `frontend/src/js/game.js` and `frontend/tests/game.test.js`.

Tests: new `tests/test_conquest.py`; existing activation, AI, API, barbarian,
benchmark-preflight, city, combat, command, economy, experiment-version,
knowledge, movement, Ollama, OpenAI, production, research, resource and state
tests were updated for the new snapshot fields and intentional V5 behavior.
All existing test cases remain, with behavior-specific names updated where
appropriate. Historical scenario hash tests project away the new snapshot fields
and keep their original expected world-data hashes.

Documentation: `README.md`, `docs/architecture.md`, `docs/benchmarking.md`,
`docs/environment-v5.md`, and this report. `docs/baselines.md` is included in
historical preservation manifests, so its original bytes remain intact; V5
measurement status is recorded here instead.

## Verification results

Python: **779 tests discovered, 774 passed, 5 skipped**. The five deployment
tests require Linux bash/flock and are skipped on Windows. Eighteen new V5 tests
cover capture eligibility/reset/atomicity, multiple defenders, recapture,
fog witnesses and hidden memory, history/result validation, terminal commands
and direct economy/spawning, executor capture, metrics, turn cap and offline
terminal replay. Existing provider tests use fake transports. Existing
secret-canary checks continue to pass.

Frontend: **40/40 tests passed**, including the conquest winner message and
disabled terminal controls. `npm.cmd run build` succeeded. No UI redesign.

Additional secret scan: **92 source/document/generated files checked**, with
no configured API key, long provider key or private-key marker found. Scan output
contains no credential values. This is a scoped scan, not a claim about every
private file in the workspace.

Frozen-artifact checks: **2,028 manifest entries checked**, no missing files or
hash mismatches (the manifests overlap). V1, failed V2, V3 and preserved V4
artifacts remain unchanged. The latest V4 retry archive also passes ZIP integrity
and its recorded SHA-256:

`6a27d3c0d9a1f9d5033a8529e2a4a49b58960135077d5f7ec886cc0f8a8bbec3`

Its 85 entries remain intact. Prompt v1, plan schema v1 and Qwen/Luna profiles
pass their existing exact-payload preservation tests. Environment V1–V4 registry
descriptions and scenario V1–V3 world data remain unchanged.

## Four deterministic headless trials

Environment v5 / Scenario v3, heuristic on every normal faction, 100-turn cap,
two paired trials (four complete runs). Provider transports were patched to
reject network requests. All four runs produced the same result:

| Observation | Per run |
| --- | --- |
| Winner | A, Conquest |
| Victory | Global turn 75, activation index 225 (zero-based) |
| Turn cap reached | False |
| Civilizations contact | First visible enemy-unit contact on turn 23 |
| First city capture | Turn 34 |
| Captures | 5: 2 Warrior and 3 Scout |
| Recaptures | 3 |
| Eliminations | B on turn 75, attributed to A |
| Cleanup in these runs | 0 units/Settlers remaining for elimination to remove |
| Population lost through capture | 3 |
| Stored food reset | 60 total |
| Stored production reset | 54 total |
| Production targets canceled | 5 |
| Normal-faction attacks / kills | 52 / 18 |
| Live provider requests / fallbacks | 0 / 0 |
| Command replay | Passed in all four runs |

Direct tests separately verify cleanup of surviving military and Settlers,
multiple defending units, barbarian exclusion and no commands after terminal
capture. The natural benchmark's zero cleanup count is not evidence that cleanup
was skipped: B had no units left.

All four canonical hash sets match:

| Artifact | SHA-256 |
| --- | --- |
| Initial state | `670399c38bb05b8ea42f5770d36519f5a9342629fe12dd84434a4a6de0f5420a` |
| Final state | `0a539a9e3ea59bbbb81a313f062474e6bb5a133a67801b20be4be9895ef123d2` |
| Commands | `def9d747a0bafaff9ed7b17373d03cc9d2ce5945b4e0ef35fd3c5527a041b27b` |
| Plans | `ea43648af8e41e911a7478ca7baaa394bd18f47c0ba29eae213c4f65475ffdbb` |

Local evidence is under `.local/benchmark-environment-v5-offline-20260911/`,
with `summary.json`, initial/final snapshots and command/plan/inference/activation
traces. Additional checks are saved in `.local/v5-preservation.json`,
`.local/v5-secret-scan.json`, `.local/v5-tests-accepted.log`, and the V5 frontend
test/build logs. Saved terminal traces were replayed again after adding explicit
terminal guards. Historical runtime hashes are not expected to equal V5 hashes;
their saved artifacts and world-data projections remain unchanged.

## Readiness and limits

Environment V5 is ready for controlled Heuristic vs Luna comparison.

Luna V5 remains unmeasured. Qwen V5 is optional; its code and frozen profile remain
available, and its historical validation extends through V4. The four identical
heuristic runs establish determinism for this fixed scenario, not diversity of
outcomes or comparative model quality. No live benchmarking, diplomacy, city HP
or Environment V6 work was performed.
