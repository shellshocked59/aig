# Batch 4 continuation checkpoint — INTERIM

Batch 4 completed all 30 scheduled matches. The runner's frozen gate passed; the separate full-prefix verification and prior-root preservation results are recorded in [Batch 4 gate](batch-4-gate.md). That mechanical gate, rather than tactical results, determines continuation to the already authorized Batch 5.

| Control | Wins / losses / no-result | Requests | Repair-exhaustion forfeits |
| --- | --- | --- | --- |
| Strict | 0 / 10 / 0 | 54 | 2 |
| Bounded | 0 / 10 / 0 | 85 | 3 |
| Stepwise | 0 / 7 / 3 | 545 | 0 |

Total requests: **684/1,700**. Total tokens: **1,740,355**. Provider time: **1,081.63 seconds (18.03 minutes)**. Process wall time: **1,468.70 seconds (24.48 minutes)**, including initial prefix verification and observed completion, excluding later reporting. These measurements are not additive.

The five exhausted repairs follow counts of 2, 7 and 8 in earlier batches. Four repaired outputs failed static range/LOS constraints; one exceeded available AP. The official categories remain invalid_reference (four) and schema_validation (one). This is a lower count than Batch 3, but failure frequency remains material and varies by batch. [Repair evidence](repair-forensics.md) retains both initial and repaired structured outputs, validator diagnostics, actors/targets, turn/AP and transport evidence.

Bounded recovered **37 AP across 23 replans**, with three second execution invalidities and seven replacement repairs. It used 31 more requests than Strict (+57.41%) in this batch. The mechanism is continuing to recover AP, but both arms lost all ten matches; no match-outcome improvement follows from recovery alone. Per-turn and per-match comparisons are retained separately in the reports.

Stepwise capped MATCH-031, MATCH-033 and MATCH-037 at 140 requests each. Those games consumed **420/545 (77.06%)** of its requests this batch. This is stronger long-tail exposure than the previous batch, under the same cap and schedule. Each cap retains a no-result and nonterminal engine state. It does not authorize a retry or an increased limit.

Batch 4 added **62 explicit EndTurns**, for 240 cumulatively. The saved-command audit found zero requests after any explicit stop within its turn. Legal tactical mistakes remain data.

**Proceed to Batch 5 only after the linked gate reports PASS**, under the user's existing two-stage authorization. Keep every frozen binding and limit unchanged. Stop after Batch 5; Batch 6 is not authorized. The halfway interpretation and next authorization recommendation belong to the Batch 5 report.

[Batch 4 report](batch-4-report.md) · [Cumulative through Batch 4](cumulative-batches-1-4-report.md) · [Focused comparisons](focused-comparisons.md) · [Figures](figures.md)
