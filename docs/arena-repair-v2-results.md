# Arena Phase 8B: authorized Qwen repair V1/V2 comparison

Qwen repaired **8/24 (33.3%)** fixed invalid responses under `arena-step-repair-v1` and **20/24 (83.3%)** under `arena-step-repair-v2`: a **50 percentage point** improvement on the frozen schedule. All accepted decisions executed successfully on detached state. This supports preparing a separately authorized model-versus-heuristic full-match replication. It does not establish tactical improvement or justify automatic V2 promotion.

## Authorization and execution

The user authorized the two prepared arms with “go ahead” after reviewing the Phase 8A stop point. Exactly **48 Qwen repair requests** were executed: V1 first, then V2, four trials for each of six challenge IDs. Both arms completed. There were zero initial decision inferences, inference preflights, retries, replacement trials, Luna calls, full matches, or tactical probes.

A read-only Ollama `/api/version` check initially failed with sandbox `PermissionError [WinError 10013]`. The escalated read-only check returned HTTP 200, version `0.34.0`. Both authorized inference commands used escalated execution permissions. These two connectivity checks were not model inference requests and consumed none of the 48-request repair budget.

Executed commands:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.repair_benchmark --provider ollama --repair-version arena-step-repair-v1 --challenge all --trials 4 --request-ceiling 24 --strict-provider --output .local/arena-phase8b-qwen-repair-v1-01
.venv/Scripts/python.exe -B -m aig.arena.repair_benchmark --provider ollama --repair-version arena-step-repair-v2 --challenge all --trials 4 --request-ceiling 24 --strict-provider --output .local/arena-phase8b-qwen-repair-v2-01
```

## Fixed conditions

Both manifests use `arena-repair-benchmark-v1`, `arena-repair-challenges-v1`, `arena-step-prompt-v1`, `arena-observation-v2`, `arena-turn-plan-schema-v1`, and `qwen-config-v1`. The model is `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M`; context size 4096, temperature 0.0, seed 42, output limit 256, `think=false`, `stream=false`, keep-alive 10m.

The saved manifests are identical except for `repairVersion`. The exact challenge states, observations, injected invalid decisions, validation failures, schema, profile, and source hashes were held fixed. The rejected-output evidence policy is identical across arms. No source or settings changes were made during execution, and V1 remains the normal gameplay default.

## Results

| Metric | Repair V1 | Repair V2 |
| --- | ---: | ---: |
| Repair requests | 24 | 24 |
| Parsed and schema-valid responses | 24/24 | 24/24 |
| Valid repairs, including EndTurn | 8/24 | 20/24 |
| Valid nonempty catalog actions | 8/24 | 12/24 |
| Explicit EndTurn | 0/24 | 8/24 |
| Successful detached executions | 8/8 accepted | 20/20 accepted |
| Invalid-reference repairs | 16 | 4 |
| Transport/provider stops | 0 | 0 |
| Total observed request latency | 48.830 s | 29.584 s |
| Mean observed request latency | 2.035 s | 1.233 s |
| Median observed request latency | 1.441 s | 1.085 s |
| Output tokens | 848 | 676 |
| Input tokens reported by Ollama | 46,828 | 50,876 |

Latency includes all attempts. V1's first request took 11.675 seconds, so its higher mean includes a substantial initial-load/order effect; V1 always ran before V2. V2 also generated fewer tokens partly because it selected EndTurn. These observations do not isolate an intrinsic latency advantage of richer feedback. Token telemetry was present for every response; no pricing estimate or external pricing lookup was used.

| Challenge ID | V1 success | V2 success | V2 accepted decision |
| --- | ---: | ---: | --- |
| `qwen-early` | 0/4 | 4/4 | EndTurn |
| `qwen-later` | 0/4 | 4/4 | `blue-cleric` move to (0, 0) |
| `luna-failure` | 0/4 | 0/4 | None |
| `downed-revive` | 4/4 | 4/4 | EndTurn |
| `midgame` | 4/4 | 4/4 | `blue-knight` attack `red-mage` |
| `low-ap` | 0/4 | 4/4 | `blue-cleric` move to (0, 0) |

V1 selected `blue-cleric` attack `red-mage` on `downed-revive`, and the same attack as V2 on `midgame`. Each successful challenge/arm produced one unique decision across its four trials; no within-arm action variation was observed. Across all successful rows, V1 produced two distinct nonempty action objects; V2 produced two distinct nonempty action objects plus EndTurn. The challenge names denote historical state provenance; **all responses here came from Qwen**, including the Luna-derived states.

V1 failed the early and Luna-derived failure challenges by healing an opposing unit. Its two low-AP challenge IDs returned a move absent from the current catalog. V2 fixed both low-AP challenge IDs to exact catalog moves and ended the early challenge's turn. Its remaining failure was a self-heal by `red-cleric` absent from the current legal catalog, repeated on all four `luna-failure` trials. Thus V2 changed that failure from a target-ownership mismatch to a catalog mismatch without achieving legality. All 20 failed repairs were `invalid_reference`; none failed parsing or schema validation.

## Limits and interpretation

The original Phase 7D/7F rejected outputs were never retained. These injected invalid decisions are representative constructions from real historical states, not recovered originals. The result measures **repair success given a fixed invalid response**, not normal first-response validity, match survival, AP efficiency, or tactical quality.

The post-run audit identified a dataset limitation: `qwen-later` and `low-ap`, though drawn from separate historical matches, have identical snapshots, observations, injected decisions, and validation failures. The frozen six-ID schedule therefore contains **five unique repair problems**, with the low-AP problem counted twice. The original six-ID denominator and artifacts are preserved; no replacements or extra inference were performed. As a descriptive sensitivity check, retaining just one of those duplicate IDs gives V1 **8/20 (40%)** versus V2 **16/20 (80%)**, a 40-point increase. This is not a new experiment.

The temperature-0, seed-42 repetitions also yielded identical decisions within each challenge/arm. The 24 trials must not be treated as 24 independent diverse problems or used to make a broad significance claim. There were two uniquely improved problems (early failure and low AP), two unchanged successful problems, and one unchanged unsuccessful problem.

Eight V2 successes were EndTurn. Four of those replaced invalid V1 decisions; four replaced valid V1 actions on the downed/revive state. EndTurn is explicitly a valid repair under both contracts, so these count in the primary metric. Valid nonempty decisions increased from 8 to 12 overall, but legality recovery must not be interpreted as better tactical choices. This benchmark deliberately does not score those choices.

## Verification and artifacts

Offline post-run validation confirmed all 48 saved trial records match their per-trial files, challenge inputs, expected failures, and request counts. All **28 accepted decisions** were revalidated, re-executed on detached snapshots, and reproduced their saved resulting-state hashes and AP costs. All 20 rejected parsed decisions reproduced their recorded validation diagnostics. Source manifests match before, between, and after the arms. All **1,118 historical Phase 7D/7F evidence files** remain unchanged.

Evidence:

- [V1 summary](../.local/arena-phase8b-qwen-repair-v1-01/summary.json), with its manifest, 24 trial files, and source-after manifest.
- [V2 summary](../.local/arena-phase8b-qwen-repair-v2-01/summary.json), with the same artifact structure.
- [Comparison analysis](../.local/arena-phase8b-repair-comparison-01/analysis.json).
- [Run artifact SHA-256 inventory](../.local/arena-phase8b-repair-comparison-01/evidence-sha256.json).
- Source-before/source-after snapshots in `.local/arena-phase8b-repair-comparison-01`.

No implementation was changed in Phase 8B; the Phase 8A test result remains 1,122 tests with zero failures/errors and five skipped. This phase added live evidence and performed the offline checks above rather than rerunning unrelated tests. No frontend changes or build occurred.

## Recommendation and stop point

The observed improvement is substantial enough to justify **preparing a separately authorized Qwen model-versus-heuristic Repair V1/V2 full-match replication**, while explicitly measuring repair frequency, recovery, EndTurn choices, completion, and replay. Hold the existing tactical prompt, observation, rules, model/profile, and stepwise execution fixed. Do not promote V2 yet, run Luna A/B, add repairs, tune tactics, or silently replace the frozen challenge dataset. Any future challenge-set revision should have a new version and remove the duplicate problem.

The authorized 48-request repair A/B is complete. No further inference was made.
