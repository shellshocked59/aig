# Arena Phase 7D full-match preparation

The user authorized this preparation after the frozen V2 runner rejected full matches. The new `arena-benchmark-v3` artifact amends orchestration explicitly; historical V1/V2 artifacts, probes and their entry points remain unchanged.

## Experiment contract

The dedicated runner is `python -m aig.arena.fullmatch_benchmark --output <new-directory>` with `backend` on `PYTHONPATH`. It schedules exactly two Qwen self-play, two Luna self-play, then two side-swapped Qwen-versus-heuristic and two side-swapped Luna-versus-heuristic matches. It never schedules Qwen versus Luna or replacement attempts. Existing nonempty or empty output roots are rejected to avoid overwriting evidence.

The full-match bound is the frozen V1 bound: 100 completed global rounds. Models retain `arena-control-stepwise-v1`, `arena-step-prompt-v1`, `arena-observation-v2`, `arena-turn-plan-schema-v1`, `qwen-config-v1` and `luna-config-v1`. Rules remain `arena-rules-v2`; scenario remains `arena-scenario-v1`. The explicit heuristic opponent uses its existing full-turn policy.

One preflight per model is included in its cumulative 400-request ceiling. The budget gates each actual transport attempt, including repair, before it starts. No repair policy is changed: the existing single repair is available while budget remains. A denied request is not counted as a transport attempt. If a repair is denied, the initial invalid response remains in evidence and the match stops as `request_ceiling`, not `repair_failed`. A denied decision can appear as a trace boundary with zero attempts; analysis must distinguish boundaries from sent requests.

At a mid-turn budget stop, AP, active player and command prefix remain as recorded; no automatic EndTurn is added. Later matches for that model remain unstarted, while the other model can continue. Ordinary failed repairs stop that match and preserve its evidence; later independently scheduled matches proceed. Failed preflight disables that provider without retry.

Purity violations, catalog execution defects, source mutation, replay mismatch and controller safety defects stop the whole schedule. Backend source and auxiliary frontend/script/test/configuration files are hashed; `.env` is hashed without recording its contents. Checks run at player-turn boundaries and before each transport attempt. This is detection at checkpoints, not an atomic filesystem lock; a change during an in-flight request may be detected at the following boundary.

## Evidence and verification

The root retains the manifest, before/after backend source manifests, auxiliary source manifest, settings file hash, preflights, cumulative request counts and all intended match statuses. Each started match retains its manifest, full command trace, final or partial snapshot, result and verification. Every model turn also retains its detached V2 turn evidence; the existing verifier is explicitly allowed to recognize the new partial-prefix stop categories when called from the V3 runner. Heuristic turns are independently regenerated and executed using the frozen policy. Full-match replay checks every command's recorded metrics and state hash, all turn boundaries and the final stopping snapshot.

The CLI writes raw evidence and `summary.json`. The detailed comparative research report remains a post-run analysis task; no dollar pricing is supplied or invented. No live model calls were made during preparation.

## Offline validation

Tests cover a complete simulated model-versus-heuristic battle, exact replay, observation tampering, a turn-limit result, failed repair preservation, mid-turn request exhaustion, repair denial at the ceiling, source-guard denial, independent-match continuation, cross-provider hard stop, per-provider ceiling isolation, and the frozen V2 contract. Existing stepwise probe tests exercise unchanged probe behavior and provider transport/repair semantics. Network calls are forbidden by mocks during the new tests.

The initial blocked attempt remains separately preserved at `.local/arena-phase7d-stepwise-fullmatch-pilot-20260913-01/`. A future live pilot must use a new root.
