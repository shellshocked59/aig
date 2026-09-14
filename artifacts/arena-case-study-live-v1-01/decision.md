# Batch 1 decision: PASS for continuation unchanged

Batch 1 passed its expenditure/integrity checkpoint. Recommend continuing the frozen benchmark unchanged **only after separate authorization**. Batch 2 and the remaining 270 matches were not run.

All 30 intended matches were started and sealed in frozen order, with five Luna Red and five Luna Blue matches per control. The current 140-file source/runtime contract verifier passed. The batch gate and standalone verifier passed: 30 exact replays, 583 reserved/completed requests, zero pending requests, verified evidence seals, and no fallback. The process exited successfully without resume. No model, profile, prompt, policy, observation, schema, repair, controller, heuristic, rule, schedule, limit, telemetry or analyzer was changed.

The control family behaved mechanically as designed. Bounded made 26 replans in 50 attempted Luna turns, recovered positive AP in 24/26 (45 AP total), and stopped on four second execution invalidities. There was no replan loop. Stepwise had zero execution invalidities. Its 23 naturally observed explicit EndTurns had zero subsequent requests within the same turn; all 67 explicit stops across controls passed that check.

Two repair-exhaustion forfeits were handled according to the frozen contract: MATCH-002 Bounded and MATCH-010 Strict. Both were `repair_failed`, not an observed transport outage. They are Luna losses and part of reliability data. There is no evidence here of pathological infrastructure failure. No extra inference or retry was performed.

The cost qualification is Stepwise duration. MATCH-001 and MATCH-009 each reached 140 requests after 94 started player turns and 46 completed rounds. Both correctly became REQUEST_LIMIT/no-winner results. Those two games account for 280/403 Stepwise requests (69.5%). The other eight Stepwise games used 123 requests total. This is substantial observed cost variation and limit censoring, but the caps worked and Batch 1 used only 583/1,700 requests (34.3%). Keep the limits and report censoring; do not silently redesign or extend those matches.

Measured requests/match were Strict 8.5, Bounded 9.5 and Stepwise 40.3, versus frozen central estimates 11, 17.875 and 31.79. The Stepwise mean was 26.8% above its estimate; aggregate requests were 3.9% below the combined central estimate. Batch tokens were 1,524,963; provider time was 963.222 seconds (16.05 minutes); backend controller time was 1,008.718 seconds. Observed process wall time was at most 1,160.412 seconds (19.34 minutes), including a short completion-observation delay.

At these measured rates, the remaining 270 matches project to 5,247 requests, 13,724,667 tokens and 8,669.001 provider seconds (2.408 hours). All 300 project to 5,830 requests, 15,249,630 tokens and 9,632.223 provider seconds (2.676 hours). These central rates are manageable within the frozen request budget. They do not guarantee completion under a heavier tail; the observed-minimum/maximum sensitivity in the full report is not a confidence interval, and its high endpoint can exceed frozen control/global ceilings. The runner must stop if a cumulative guard is reached. No dollar costs are inferred.

## Early interpretation: n=10/control

Strict: 0 wins, 10 losses including one forfeit. Bounded: 0 wins, 10 losses including one forfeit. Stepwise: 1 win, 7 losses, 2 request-limit nonwins. This is a small sample against the frozen Heuristic V2 on one opening; it does not establish control superiority, equivalence, or absolute skill.

Bounded versus Strict: no observed win difference. Final execution truncations were 4/50 attempted Luna turns versus 26/61; truncation-derived AP was 8 versus 74. Bounded recovered 45 AP at 95 versus 85 total requests. Its requests/turn were 1.900 versus 1.393 (36.4% higher); a lower match-level overhead partly reflects shorter/different trajectories, not equal game quality at equal duration.

Bounded versus Stepwise: 0 versus 1 observed wins. Bounded used 1.900 versus 3.030 requests/turn (37.3% fewer), 5,366.94 versus 7,680.09 tokens/turn (30.1% fewer), and 3.374 versus 4.746 provider seconds/turn (28.9% fewer). Stepwise had zero execution truncations. This is relevant to the selective-recovery hypothesis but does not establish comparable gameplay quality.

Explicit EndTurns were Strict 21, Bounded 23 and Stepwise 23; immediate stops were 1, 0 and 4. Intentional AP left was 32, 25 and 44. Immediate Stepwise stops occurred on four Blue opening turns, with no immediately damaging legal action available; movement opportunities and longer-term strategy are not thereby evaluated. Strict's immediate stop left a damaging option. Stops leaving an immediately legal damaging action occurred 9, 6 and 2 times, respectively; one Strict and one Bounded stop left a one-action enemy-down opportunity. These are tactical observations, not contract defects. None proves a stop was strategically unjustified.

Fireball was common and sometimes harmful. Strict/Bounded/Stepwise casts were 54/61/172; enemy HP damage 82/86/986; friendly HP damage 77/109/57. Empty blasts were 12/14/24 and friendly-only blasts 12/24/6. Actual Fireball enemy downs were 1/2/1 and friendly downs 3/4/1. Stepwise counts are dominated by its longer trajectories and repeated combat/revival, so large totals alone are not evidence of better tactics. All effects were reconstructed mechanically; no LLM judge or tuning was used.

**Decision: PASS for a separately authorized continuation under the existing frozen contract.** Retain the two long-game/request-limit observations and two repair forfeits prominently in later reporting. They justify continued cost and reliability monitoring, not changes to Batch 1 evidence or the fixed controls.
