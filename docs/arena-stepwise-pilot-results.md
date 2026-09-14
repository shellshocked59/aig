# Arena Phase 7B: authorized stepwise pilot results

2026-09-13. Both authorized pilots completed and stopped: **14/14 valid probe
turns, 50 total inference requests, zero repairs, zero fallback and zero replay
mismatches**. No continuation, replacement trial, four-trial schedule, full match,
source change, prompt adjustment or model/profile change was performed.

**The pilot supports a full-turn sequencing limitation for Qwen and Luna.** Qwen
continues choosing actions after fresh feedback and materially increases AP usage.
Luna's execution failures disappear in these seven turns. Whole-turn latency and
token costs increase substantially. One trial per fixed probe does not establish
general tactical strength, statistical significance or stable future reliability.

## Authorization and evidence

The user authorized the proposed seven-probe, one-trial pilot for each provider,
with a ceiling of 71 requests each, including one unrepaired preflight and bounded
repairs. Both schedules completed below their ceilings; remaining capacity was not
used. Providers ran sequentially to avoid overlapping latency measurements.

- [Qwen summary](../.local/arena-phase7b-qwen-stepwise-pilot-01/summary.json)
- [Luna summary](../.local/arena-phase7b-luna-stepwise-pilot-01/summary.json)
- [Complete offline comparison and preservation verification](../.local/arena-phase7b-live-audit-01/comparison.json)
- [Reproducible offline analyzer](../.local/arena-phase7b-live-audit-01/analyze.py)
- [Implementation and experiment design](arena-stepwise-control-experiment.md)
- [Full-turn Observation V2 control results](arena-observation-v2-probe-results.md)

The read-only Ollama `/api/version` check first hit sandbox `WinError 10013`.
The same check with escalated permissions returned HTTP 200, version `0.34.0`.
Both authorized provider runs then used network-capable permissions. Those two
version checks were not inference requests. No model request was retried after a
failed live run: neither model run failed.

| Provider | Intended / valid turns | Initial trial decisions | Repairs | Preflight | Total / authorized ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen | 7 / 7 | 25 | 0 | 1 | **26 / 71** |
| Luna | 7 / 7 | 23 | 0 | 1 | **24 / 71** |

Qwen's 25 decisions all executed actions. Luna executed 22 actions and explicitly
stopped once. Initial trial responses were valid 25/25 and 23/23 respectively;
selected current actions were catalog members 25/25 and 22/22. All 14 turns
completed without provider failure or catalog-execution defect.

## Frozen comparison

Stepwise uses `arena-benchmark-v2`, `arena-control-stepwise-v1`,
`arena-step-prompt-v1`, `arena-observation-v2`, `arena-turn-plan-schema-v1`,
`arena-probes-v1`, `qwen-config-v1` and `luna-config-v1`.
Full-turn controls use Prompt V2 / Observation V2 / benchmark v1, with the same
models, profiles, probe states and game rules. The step prompt necessarily defines
a different task; this is not a controller-only comparison with identical wording.

The comparison below uses one new turn per probe against the mean of that probe's
four completed Phase 7A full-turn trials. All seven fixtures are represented equally
in each aggregate. Different repetition counts, prior collection time and cache
conditions limit causal claims, especially for latency and cache behavior.

| Probe | Qwen AP: full-turn mean → stepwise | Qwen actions / decisions | Luna AP: full-turn mean → stepwise | Luna actions / decisions |
| --- | ---: | ---: | ---: | ---: |
| Finish or Core | 1.00 → 5 | 5 / 5 | 5.00 → 5 | 5 / 5 |
| Fireball friendly fire | 1.00 → 5 | 5 / 5 | 3.25 → 5 | 3 / 3 |
| Revive decision | 2.00 → 5 | 4 / 4 | 3.00 → 5 | 4 / 4 |
| Shield Bash position | 1.00 → 3 | 3 / 3 | 1.50 → 3 | 3 / 4 |
| Snipe versus basic | 2.00 → 5 | 3 / 3 | 3.50 → 5 | 3 / 3 |
| Team elimination | 1.00 → 1 | 1 / 1 | 1.00 → 1 | 1 / 1 |
| Winning Core line | 1.00 → 4 | 4 / 4 | 1.75 → 5 | 3 / 3 |
| **Mean AP** | **1.29 → 4.00** | | **2.71 → 4.14** | |

Qwen executed multiple actions in six probes; Team Elimination correctly ended
after one winning action. It never explicitly stopped. Its seven unused AP across
the pilot remained because of immediate victories, not rejected actions or an
empty decision. Six probes ended in victory; Snipe consumed all AP without victory.
These victories are mechanical facts, not a new aggregate tactical score.

Luna spent 29 AP across seven turns, with six unused AP. Four were left by the
immediate Team Elimination win; two were left by an explicit empty decision after
Shield Bash → Move → Shield Bash. At that stop, 23 legal Move actions remained,
with no currently legal non-Move actions. Fresh state therefore does not guarantee
the model will choose further setup moves. No tactical policy was changed to
encourage more AP use.

The previous Luna full-turn sample had eight execution truncations across 28 turns;
this stepwise pilot had zero across seven. Qwen had zero in both samples. Stepwise
requires current catalog membership, so accepted-action legality is partly a
contract guarantee; zero repairs/failures additionally shows both models complied
on their first responses in this pilot.

## Tactical outcomes and an important predicate distinction

Both models revived the ally, won Team Elimination, and recorded a victory in
Winning Core line. Qwen previously recorded zero victories in four full-turn
Winning Core line trials; Luna previously won all four.

**Qwen won Winning Core line by team elimination, not by destroying the Core.**
It attacked the enemy Knight four times; the enemy Core remained at 9 HP. The
unchanged frozen probe predicate accepts any victory. This result meets that
predicate but does not demonstrate choosing the winning Core attack.

Luna used Snipe → Snipe → Core attack and destroyed the Core (0 HP). This was a
five-AP win; it does not show a more efficient winning line than its full-turn
control. Revive success and Team Elimination success were already perfect in the
Phase 7A sample for both models and remain successful here.

Do not interpret improved AP use alone as stronger tactics. The clearest Qwen
finding is that its former one-action behavior disappears with fresh feedback.
The clearest Luna finding is compliant, executable step-by-step control without
the previous multi-action invalidations. Objective improvements are narrower.

## Whole-turn latency, tokens and caching

All values below exclude preflight and include all trial requests. No repairs
occurred. Time is total provider request wall time **per player turn**, not one
stepwise request compared with an entire full-turn request.

| Mean per turn | Qwen full-turn | Qwen stepwise | Luna full-turn | Luna stepwise |
| --- | ---: | ---: | ---: | ---: |
| Total provider seconds | 1.73 | **8.03** | 1.35 | **5.09** |
| Input tokens | 1,783.57 | **5,250.57** | 2,101.29 | **5,626.00** |
| Output tokens | 30.57 | **109.00** | 76.21 | **128.71** |
| Decisions | 1 | 3.57 | 1 | 3.29 |

Whole-turn latency increased **4.64× for Qwen** and **3.77× for Luna**. Input
tokens increased **2.94×** and **2.68×**, respectively; output tokens increased
3.57× and 1.69×. These are observed pilot ratios, not projected service guarantees.
Per-decision telemetry remains in each turn and the summary distributions.

Trial totals:

- Qwen: **36,754 input, 763 output** tokens. Ollama cache-token counts are not
  reported by this adapter, so cached/uncached totals remain unknown.
- Luna: **39,382 input, 901 output**, with **zero cached input tokens**; all
  39,382 input tokens were uncached. The prior full-turn sample included cached
  input, so token-volume ratios alone cannot establish a dollar-cost ratio.

The separate Qwen preflight used 2,297 input / 37 output tokens and approximately
11.75 seconds at the checked provider boundary. Luna's preflight used 2,623 input /
47 output, zero cached input, and approximately 3.95 seconds. Preflight latency may
include cold-start effects and is not included in tactical-turn comparisons.

No dated Luna pricing file was available; **dollar cost remains null**. No price
was fabricated or looked up. The retained complete token/cache telemetry supports
a later explicitly priced calculation without rerunning inference.

## Replay, provenance and preservation

Offline analysis independently reverified all **14 new stepwise trials** and all
**56 matched historical full-turn trials**. Each command trace, per-step
observation, selected action, AP transition and final snapshot reproduced exactly.
Both new manifests' source-file hashes match the current backend. Every selected
model action met current-catalog validation; no engine/query inconsistency appeared.

The pre-run inventory covered **5,290 existing files**, including **5,164 existing
evidence files**. Every inventoried file remained SHA-256 identical after both runs
and offline analysis. New pilot directories, this new results report and the new
offline audit directory are additive. No historical evidence or implementation
file was modified. No new regression tests/build were needed because source did
not change; command replay was the validation for this data-collection phase.

## Stop point

The authorized pilot is finished. No additional inference is running. The results
justify reviewing stepwise control as a separate benchmark mode, with its material
whole-turn latency/token penalty and the narrow tactical predicate caveat above.
Four-trial runs, continuations, tuning and full matches remain unexecuted and
require separate authorization.
