# Arena Phase 9B: authorized Qwen action-ID pilot

The seven-turn pilot completed with **25/25 valid first responses, 25/25 current
legal IDs, zero repairs and seven exact replays**. It used 25 of the authorized
70 requests. No preflight, extra trials, full matches, Luna/OpenAI inference,
fallback, model/profile change or automatic promotion occurred.

This establishes initial Ollama schema compatibility and successful action-ID
execution on these probes. It does **not** establish improved reliability: the
historical structured-stepwise pilot also had 25/25 valid first responses. Repair
reliability remains unmeasured because no repairs were triggered. Tactical quality
must remain separate: this run failed the Revive objective that the historical
structured run achieved.

## Authorization and execution

The user authorized the prepared seven probes at one trial each, with 70 requests
including repairs, by replying “yes authorized.” The exact command executed was:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.action_id_benchmark --provider ollama --probe all --probe-trials 1 --request-ceiling 70 --output .local/arena-phase9b-qwen-action-id-pilot-01
```

A read-only `/api/version` check using the current settings hit sandbox
WinError 10013. The escalated check returned HTTP 200 and Ollama 0.34.0. The pilot
then used the same permitted execution context. Neither connectivity check was
inference. There were no retries or replacement runs.

Contracts remained `arena-control-stepwise-action-id-v1`, `arena-observation-v3`,
`arena-step-prompt-v2`, `arena-step-action-id-schema-v1`,
`arena-action-id-repair-v1`, `arena-benchmark-v4`, `arena-probes-v1` and
`qwen-config-v1`. Benchmark V3 still identifies the frozen structured full-match
orchestrator. Qwen remained `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M`,
context 4096, temperature 0, seed 42, maximum output 256, think/stream false.

## Outcomes and historical control

Comparison uses the existing Phase 7B Qwen structured-stepwise pilot, without
rerunning it. Probe initial snapshots, game/scenario, model and model configuration
match. Representation contracts and collection times differ; this is not a
contemporaneous randomized comparison. Control counts below exclude its one
preflight, which raised that historical run's total to 26 requests.

| Metric | Structured Phase 7B | Action-ID Phase 9B |
| --- | ---: | ---: |
| Completed / intended turns | 7/7 | 7/7 |
| First responses valid | 25/25 | 25/25 |
| Trial requests | 25 | 25 |
| Repairs | 0 | 0 |
| Executed actions | 25 | 25 |
| Executed AP | 28 | 28 |
| Mean / median AP | 4 / 5 | 4 / 5 |
| Explicit EndTurn | 0 | 0 |
| Immediate victories | 6 | 5 |
| Revive objective achieved | Yes | No |
| Input tokens | 36,754 | 39,328 |
| Output tokens | 763 | 225 |
| Mean output tokens / decision | 30.52 | 9 |
| Summed request latency | 56.20 s | 49.53 s |
| Maximum observed context occupancy | 52.93% | 64.79% |

Output tokens fell 70.5%; input tokens rose 7.0%. Different selected actions alter
subsequent observations, so aggregate input differences are not solely wrapper
overhead. Mean/median action-ID request latency was 1.98/1.60 seconds, with the
first request taking 10.07 seconds. Cache/load and collection-time differences
prevent attributing the latency difference solely to representation.

Maximum Qwen input was 2,645 tokens; every output used 9 tokens. Reported maximum
occupancy is (2,645 + 9) / 4,096. Reserving the full unchanged 256 output tokens
instead leaves 1,195 tokens of headroom at that maximum input. No context failure
occurred, but no live repair context was exercised.

| Probe | AP | Decisions | Selected IDs in order | Outcome |
| --- | ---: | ---: | --- | --- |
| finish_or_core | 5 | 5 | A01, A01, A01, A01, A01 | Core destroyed; victory |
| fireball_friendly_fire | 5 | 5 | A01, A01, A01, A47, A22 | Basic attacks; victory |
| revive_decision | 5 | 5 | A01, A01, A01, A01, A01 | Five actor attacks; no Revive, no victory |
| shield_bash_position | 3 | 3 | A01, A01, A01 | Basic attacks; victory |
| snipe_vs_basic | 5 | 3 | A24, A24, A01 | Two Snipes and an attack; no immediate victory |
| team_elimination | 1 | 1 | A01 | One attack; victory |
| winning_core_line | 4 | 3 | A01, A35, A01 | Attack, Snipe, attack on enemy; victory |

IDs are local: a repeated string may resolve to a different action after the
catalog refresh. The winning-core probe's victory came from attacking the enemy
unit, not from choosing a Core attack. Its existing objective metric counts victory;
it should not be interpreted as proof of Core targeting.

Three complete command traces match the historical control exactly: finish_or_core,
shield_bash_position and team_elimination. The other four differ. In Revive, the
historical run revived its ally and won; the action-ID run repeatedly attacked with
the actor and left the ally downed. This single observation is a reason to monitor
tactical outcomes, not proof of a systematic representation-induced degradation.

## Verification and artifacts

Independent offline verification rebuilt every current catalog, checked ID-to-action
resolution and command association, and replayed all seven final snapshots exactly.
The 25 recorded attempts reconcile with the request budget; all attempt categories
are successful. There were no provider failures, unknown IDs or execution defects.

Backend source, auxiliary source and settings hashes match the before-run inventory.
All **7,458 pre-existing evidence files** in that inventory retain exact byte hashes.
No runtime implementation changed in this live phase. Phase 9A's accepted Python
result remains 1,163 tests run, five skipped; no frontend/build files were touched.

- [Pilot summary and telemetry](../.local/arena-phase9b-qwen-action-id-pilot-01/summary.json)
- [Independent verification and per-probe historical comparison](../.local/arena-phase9b-live-audit-01/verification.json)
- [Before-run source/settings/evidence inventory](../.local/arena-phase9b-live-audit-01/before.json)
- [Historical structured pilot](arena-stepwise-pilot-results.md)
- [Frozen action-ID preparation](arena-action-id-control-experiment.md)

Stop after this authorized pilot. The remaining request allowance is unused.
No larger probe schedule, repair experiment or full match is authorized, and normal
gameplay defaults remain unchanged.
