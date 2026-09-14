# Luna vs Heuristic V2 — Batch 1 report

**Decision: PASS for a separately authorized continuation unchanged.** All 30 intended matches are sealed; 30 exact replays and 583 requests reconcile with zero pending requests. Batch 2 was not run. Detailed reasons and early interpretation: [decision.md](decision.md).

Descriptive expenditure/integrity batch only. Intended sample: 10 matches per control, 30 total; one canonical opening. No confirmatory tests, absolute skill rating, or declaration of a winning control. Wilson intervals below describe a small sample. Limits are nonwins; provider forfeits are losses.

## Execution

Only Batch 1 was authorized and executed. The prepared live command was run with network execution permission; no inference preflight, focused-validation rerun, model change, or benchmark-source change was made. No resume was used.

```powershell
.venv/Scripts/python.exe -B -m aig.arena.case_study verify
.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 1 --authorize-live arena-case-study-benchmark-v1
.venv/Scripts/python.exe -B -m aig.arena.case_study verify --output artifacts/arena-case-study-live-v1-01
.venv/Scripts/python.exe -B -m aig.arena.case_study analyze --output artifacts/arena-case-study-live-v1-01
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-01/supplemental-audit.py
.venv/Scripts/python.exe -B artifacts/arena-case-study-live-v1-01/build-batch-report.py
```

The last two scripts create supplemental derived reporting from saved evidence. They do not alter the frozen runner, analyzer, contract, telemetry, or sealed match artifacts and make no provider calls.

| Binding | SHA-256 / value |
| --- | --- |
| contract_sha256 | dadc3c3e13c91d4ac7f0178d7753111471af423c2c1268bd4f05b53d6a134792 |
| contract_file_sha256 | 16c4c2efd6996fa06887a4f856623804e8a092707946742a686cd2dbf5e24e3e |
| schedule_sha256 | e044dd24aa962e4f9cd6a1dd09eabc19f8b19688e987ada7ba7521ba7d9562fc |
| batch_1_schedule_sha256 | cea3be4a6006a0ff910a953503750189c354aea86db6dc3ae4a2a38d2352542b |
| source_manifest_sha256 | 4e7f301fda779e06a00f7445f6b5a9ecefc125dfc9257a8905935bcff41de31d |
| source_files | 140 |

Batch manifest is the first 30 entries of `contract.json` / `schedule.json`, MATCH-001 through MATCH-010, under the contract hash above. The batch-specific hash is the canonical hash of that exact slice; it is an additional audit digest, not a replacement contract.

| Control | Intended | Started | Sealed/adjudicated | Forfeits | No-result | Red/Blue sealed |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 10 | 10 | 1 | 0 | {"red": 5, "blue": 5} |
| bounded | 10 | 10 | 10 | 1 | 0 | {"red": 5, "blue": 5} |
| stepwise | 10 | 10 | 10 | 0 | 2 | {"red": 5, "blue": 5} |

Forfeits and request/turn-limit results are included in the sealed/adjudicated counts; they are not additional matches. Unsealed/integrity-interrupted matches are not fabricated outcomes.

## Integrity

The current case-study source/runtime verifier passed before the live command. The historical focused whole-inventory verifier was not changed or used as the new benchmark authority. Frozen model/profile: gpt-5.6-luna / luna-config-v1; policy arena-policy-core-v1; full-turn prompt arena-turn-prompt-v6; step prompt arena-step-prompt-v3; observation arena-observation-v4; schema arena-turn-plan-schema-v2; repair arena-candidate-repair-v2; rules arena-rules-v2; scenario arena-scenario-v1; opponent arena-heuristic-v2. Exact configuration, prompt/schema and dependency hashes are in the verified copied contract.

Standalone integrity result: `{"success": true, "completed_matches": 30, "replay_verified": 30, "completed_requests": 583, "reserved_requests": 583, "pending_requests": 0}`. The verifier covers exact command replay, control observations, deterministic heuristic replay, metric recomputation, request receipts/bindings, schedule/side prefix, seals and zero fallback. Supplemental audit independently replays saved turns and reconciles request purposes. No completed live request was rerun.

## Requests and control mechanics

Sealed-match requests: **583 / 1,700**. Reservations and any pending requests are reported by the integrity result above. Per-control batch limits remain Strict 300, Bounded 500, Stepwise 900.

| Control | Requests | Requests/match | Requests/Luna turn | Completed Luna turns | First-response valid/decisions | Repairs success/attempts |
| --- | --- | --- | --- | --- | --- | --- |
| strict | 85 | 8.500 | 1.393 | 60 | 37/61 | 23/24 |
| bounded | 95 | 9.500 | 1.900 | 49 | 57/76 | 18/19 |
| stepwise | 403 | 40.300 | 3.030 | 131 | 371/387 | 16/16 |

| Request purpose | strict | bounded | stepwise |
| --- | --- | --- | --- |
| initial_planning | 61 | 50 | 0 |
| repair | 24 | 12 | 16 |
| bounded_replacement_planning | 0 | 26 | 0 |
| bounded_replacement_repair | 0 | 7 | 0 |
| stepwise_decisions | 0 | 0 | 387 |

Purpose counts are disjoint. Stepwise decisions above exclude repair calls; the repair row includes Stepwise decision repairs and initial-wave full-turn repairs. Bounded replacement repairs have their own row.

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Attempted Luna turns | 61 | 50 | 133 |
| Execution truncations | 26 | 4 | 0 |
| Initial execution-invalid turns | 26 | 26 | 0 |
| Bounded replans | 0 | 26 | 0 |
| Replacement repairs | 0 | 7 | 0 |
| Replacement first-response invalidities | 0 | 7 | 0 |
| AP recovered | 0 | 45 | 0 |
| Second execution invalidities | 0 | 4 | 0 |
| Decisions | 61 | 76 | 389 |
| Provider failures | 1 | 1 | 0 |

Bounded replan rate: 0.520; positive-AP recoveries: 24/26. AP at replan: [2, 3, 3, 1, 3, 2, 2, 4, 4, 4, 2, 2, 4, 3, 2, 4, 2, 2, 2, 3, 1, 4, 2, 2, 2, 2]; AP recovered per replan: [2, 3, 2, 1, 0, 2, 2, 2, 3, 1, 2, 2, 3, 1, 2, 2, 2, 2, 1, 2, 0, 1, 2, 2, 2, 1]. Second-invalidity rate: 0.154.

Stepwise decisions/attempted turn: 2.925; requests/completed turn: 3.061; actions/turn: 2.737.

Execution invalidity categories: `{"strict": {"target outside action range": 17, "destination is occupied, blocked, unchanged, or beyond move range": 2, "blocked line of sight": 4, "impact outside Fireball range/board": 2, "invalid target ACTIVE/DOWNED status": 1}, "bounded": {"target outside action range": 15, "blocked line of sight": 5, "impact outside Fireball range/board": 6, "invalid target ACTIVE/DOWNED status": 3, "destination is occupied, blocked, unchanged, or beyond move range": 1}, "stepwise": {}}`. Exact action indexes, AP and actions remain in match results.

## Game outcomes

| Control | Wins | Losses (incl. forfeit) | Forfeits | No-result | Win rate / intended 10 | Wilson 95% (sealed sample) | Terminal causes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 0 | 10 | 1 | 0 | 0.000 | [0, 0.2775327998628892] | {"CORE_DESTRUCTION": 4, "TEAM_ELIMINATION": 5, "PROVIDER_FORFEIT": 1} |
| bounded | 0 | 10 | 1 | 0 | 0.000 | [0, 0.2775327998628892] | {"TEAM_ELIMINATION": 8, "PROVIDER_FORFEIT": 1, "CORE_DESTRUCTION": 1} |
| stepwise | 1 | 7 | 0 | 2 | 0.100 | [0.017876213095072896, 0.4041500267952385] | {"REQUEST_LIMIT": 2, "CORE_DESTRUCTION": 7, "TEAM_ELIMINATION": 1} |

| Control | Player turns total / median / range | Completed rounds total / median / range | Luna turns |
| --- | --- | --- | --- |
| strict | [124, 9.5, [5, 33]] | [56, 4.0, [2, 16]] | 61 |
| bounded | [101, 10.0, [3, 18]] | [42, 4.0, [1, 8]] | 50 |
| stepwise | [267, 10.5, [7, 94]] | [125, 4.5, [3, 46]] | 133 |

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Core damage dealt | 0 | 0 | 30 |
| Core damage received | 145 | 80 | 221 |
| Enemy unit damage | 204 | 209 | 1500 |
| Friendly unit damage | 77 | 109 | 57 |
| Enemy downs inflicted | 10 | 16 | 101 |
| Friendly downs inflicted | 3 | 4 | 1 |
| Downs received | 35 | 40 | 90 |
| Finishes | 1 | 2 | 1 |
| Finishes received | 8 | 11 | 8 |
| Revives | 5 | 6 | 71 |

## AP and EndTurn semantics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| AP available | 305 | 250 | 665 |
| AP executed | 182 | 204 | 610 |

| Unused AP reason | strict | bounded | stepwise |
| --- | --- | --- | --- |
| INTENTIONAL_END_TURN | 32 | 25 | 44 |
| CLEAN_PLAN_COMPLETE | 6 | 5 | 0 |
| EXECUTION_TRUNCATION | 74 | 8 | 0 |
| PROVIDER_FAILURE | 5 | 3 | 6 |
| TERMINAL | 6 | 5 | 5 |

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Request-limit AP within generic failure bucket | 0 | 0 | 6 |

| Adjusted AP category | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Actual provider-failure AP | 5 | 3 | 0 |

The controller generic PROVIDER_FAILURE bucket includes request-budget-denied AP; subtract the separately reported request-limit AP to obtain provider-failure AP. Intentional AP is not automatically waste. Terminal AP is separate.

| Control | Explicit stops | Immediate stops | AP left distribution | Actions before distribution | Stops with legal damaging option | Stops with available down | Requests after stop |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 21 | 1 | {"0": 2, "5": 1, "1": 12, "2": 3, "3": 3} | {"4": 1, "0": 1, "2": 15, "1": 3, "3": 1} | 9 | 1 | 0 |
| bounded | 23 | 0 | {"2": 4, "0": 6, "1": 11, "3": 2} | {"2": 10, "3": 12, "1": 1} | 6 | 1 | 0 |
| stepwise | 23 | 4 | {"1": 16, "5": 4, "3": 2, "2": 1} | {"2": 17, "0": 4, "1": 2} | 2 | 0 | 0 |

“Legal damaging option” means an immediately executable catalog action in a detached simulation caused positive enemy unit/Core HP loss at the saved stop state. This flags potentially premature stops; it does not establish that taking the action was strategically preferable. No LLM judge was used. All opportunities, actions, AP and turn identifiers are in supplemental-audit.json.

Stepwise explicit EndTurn was observed and all observed stops have zero subsequent wave/request in the same turn.

## Fireball mechanics

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Casts | 54 | 61 | 172 |
| Empty blasts | 12 | 14 | 24 |
| Friendly-only blasts | 12 | 24 | 6 |
| Enemy-only blasts | 20 | 14 | 133 |
| Mixed blasts | 10 | 9 | 9 |

| Fireball effect | strict | bounded | stepwise |
| --- | --- | --- | --- |
| enemy_units_hit | 31 | 23 | 247 |
| friendly_units_hit | 24 | 37 | 18 |
| enemy_damage | 82 | 86 | 986 |
| friendly_damage | 77 | 109 | 57 |
| enemy_downs | 1 | 2 | 1 |
| friendly_downs | 3 | 4 | 1 |

Hit counts include repeated exposure across casts, using ACTIVE units before each cast. Damage is actual capped HP loss. Heuristic Fireball records are separately retained in supplemental-audit.json.

## Resources and projections

| Metric | strict | bounded | stepwise |
| --- | --- | --- | --- |
| Input tokens | 227793 | 260651 | 1003755 |
| Cached input tokens (subset of input) | 105371 | 111221 | 174111 |
| Output tokens | 7371 | 7696 | 17697 |
| Reasoning tokens (subset of output) | 0 | 0 | 0 |
| Total tokens | 235164 | 268347 | 1021452 |
| Provider latency seconds | 163.298 | 168.708 | 631.216 |
| Backend controller thinking seconds | 170.826 | 177.072 | 660.819 |

| Overall Batch 1 resource | Total | Per intended match |
| --- | --- | --- |
| provider_requests | 583 | 19.433 |
| input_tokens | 1492199 | 49,739.967 |
| cached_input_tokens | 390703 | 13,023.433 |
| output_tokens | 32764 | 1,092.133 |
| reasoning_tokens | 0 | 0.000 |
| total_tokens | 1524963 | 50,832.100 |
| provider_latency_seconds | 963.222 | 32.107 |
| backend_thinking_seconds | 1,008.718 | 33.624 |

| Control | Tokens/match | Observed requests/match | Frozen central estimate | Observed/estimate |
| --- | --- | --- | --- | --- |
| strict | 23,516.400 | 8.500 | 11 | 0.773 |
| bounded | 26,834.700 | 9.500 | 17.875 | 0.531 |
| stepwise | 102,145.200 | 40.300 | 31.790 | 1.268 |

Provider latency and backend controller time overlap and must not be added as independent costs. Unknown provider telemetry remains unknown, not zero. No dollar pricing is frozen. Process wall-clock duration is recorded in execution-timing.json when available.

Live process elapsed wall time: at most 1160.412 seconds (19.34 minutes), measured from process start to observed successful completion; includes a short observation delay. Start UTC: 2026-09-14T13:55:14.5492481Z; completion observed UTC: 2026-09-14T14:14:34.9607496Z. Offline post-run verification/analysis is excluded.

| Control | Summed match evidence elapsed seconds | Active control seconds (both players) | Tokens/Luna turn | Cached input tokens/match |
| --- | --- | --- | --- | --- |
| strict | 198.058 | 184.027 | 3,855.148 | 10,537.100 |
| bounded | 198.112 | 185.294 | 5,366.940 | 11,122.100 |
| stepwise | 728.019 | 688.500 | 7,680.090 | 17,411.100 |

Per-control elapsed is the sum of each match manifest-to-seal file timestamp interval. It includes match execution and finalization/replay but excludes between-match gaps and batch gates; it is not a separate process stopwatch. Precise evidence-span durations are retained per match in supplemental-audit.json.

| provider_requests | Remaining 90/control central | All 100/control central | Observed per-match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- |
| strict | 765.000 | 850.000 | [4, 26] | [360, 2340] | [445, 2425] |
| bounded | 855.000 | 950.000 | [4, 16] | [360, 1440] | [455, 1535] |
| stepwise | 3,627.000 | 4,030.000 | [12, 140] | [1080, 12600] | [1483, 13003] |

Combined provider_requests: remaining 270 central **5,247.000**; total 300 central **5,830.000**. Remaining sensitivity [1800, 16380]; total sensitivity [2383, 16963].

| total_tokens | Remaining 90/control central | All 100/control central | Observed per-match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- |
| strict | 2,116,476.000 | 2,351,640.000 | [10688, 66117] | [961920, 5950530] | [1197084, 6185694] |
| bounded | 2,415,123.000 | 2,683,470.000 | [12719, 43667] | [1144710, 3930030] | [1413057, 4198377] |
| stepwise | 9,193,068.000 | 10,214,520.000 | [28899, 351155] | [2600910, 31603950] | [3622362, 32625402] |

Combined total_tokens: remaining 270 central **13,724,667.000**; total 300 central **15,249,630.000**. Remaining sensitivity [4707540, 41484510]; total sensitivity [6232503, 43009473].

| provider_latency_seconds | Remaining 90/control central | All 100/control central | Observed per-match min/max | Remaining sensitivity | All 100 sensitivity |
| --- | --- | --- | --- | --- | --- |
| strict | 1,469.682 | 1,632.979 | [7.109847999934573, 42.251198099926114] | [639.8863199941115, 3802.6078289933503] | [803.1842650938197, 3965.9057740930584] |
| bounded | 1,518.372 | 1,687.080 | [7.185890700027812, 29.19422550010495] | [646.7301630025031, 2627.4802950094454] | [815.4381962023326, 2796.188328209275] |
| stepwise | 5,680.947 | 6,312.163 | [18.72352769988356, 216.68082660034997] | [1685.1174929895205, 19501.274394031498] | [2316.333829690353, 20132.49073073233] |

Combined provider_latency_seconds: remaining 270 central **8,669.001**; total 300 central **9,632.223**. Remaining sensitivity [2971.733975986135, 25931.362518034293]; total sensitivity [3934.9562909865053, 26894.584833034663].

Central projections scale each control’s observed mean. Sensitivity holds observed Batch 1 fixed and assigns every future match that control’s observed minimum or maximum; it is not a confidence or prediction interval. It can be wide with long/request-limited games and optimistic after early forfeits. If Batch 1 is incomplete, these are conditional rate extrapolations only; the actual remaining schedule exceeds 270 and must not be mislabeled as collected data.

## Paired descriptive comparisons

`{"comparison": "bounded-strict", "pairs": 10, "win_gains": 0, "win_losses": 0, "win_rate_difference": 0.0, "exact_mcnemar_p": null, "outcome_cross_table": {"loss/loss": 10}, "provider_forfeit_pairs": 2, "limit_pairs": 0, "median_paired_player_turn_difference": 1.5, "provider_requests_per_turn_ratio": 1.3635294117647059, "total_tokens_per_turn_ratio": 1.3921490534265448, "backend_thinking_seconds_per_turn_ratio": 1.264609943592909, "win_difference_bootstrap_95": null}`

`{"comparison": "stepwise-bounded", "pairs": 10, "win_gains": 1, "win_losses": 0, "win_rate_difference": 0.1, "exact_mcnemar_p": null, "outcome_cross_table": {"limit/loss": 2, "loss/loss": 7, "win/loss": 1}, "provider_forfeit_pairs": 1, "limit_pairs": 2, "median_paired_player_turn_difference": 0.5, "provider_requests_per_turn_ratio": 1.5947764147210133, "total_tokens_per_turn_ratio": 1.4309998296168598, "backend_thinking_seconds_per_turn_ratio": 1.4029760949131183, "win_difference_bootstrap_95": null}`

Positive bounded-minus-strict outcome differences, recovered AP and reduced truncation would be consistent with selective recovery, but do not establish the hypothesis. Compare request, token, and time overhead alongside outcomes. Stepwise-minus-bounded ratios reverse when interpreting bounded relative to stepwise. This small conditional sample cannot establish equivalence or superiority.

## Matched triplets

Every row below uses the frozen shared opening and corresponding Luna side. Requests and Luna turns are separate. Combat columns report Luna effects. Exact per-match AP taxonomy, terminal cause, hashes and all metrics are also provided in supplemental-audit.json and sealed result files.

| Slot | Side | Control | Outcome/cause | Player turns/rounds | Requests/Luna turns | AP executed; unused I/C/X/P/T | Core dealt/received | Enemy downs/Finish/Revive | Final state hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-001 | red | strict | loss/CORE_DESTRUCTION | 11/5 | 8/5 | 12; 0/0/13/0/0 | 0/30 | 1/1/0 | 4137bf08bcd3c276f4b61cb4e91860c155f17293dbbeb3396a8c0a3897335bb1 |
| MATCH-001 | red | bounded | loss/TEAM_ELIMINATION | 18/8 | 16/9 | 37; 6/0/1/0/1 | 0/15 | 2/0/0 | 9e1d6d8856be427c587cd21d17076722eeb6d6ca8ed6913cf96b6a804ce9ac47 |
| MATCH-001 | red | stepwise | limit/REQUEST_LIMIT | 94/46 | 140/47 | 232; 2/0/0/1/0 | 0/18 | 44/0/44 | dfa39cdbc2aaacf72499db1212dd3beaee614a8b3ae92a2c7da68e50105bbef6 |
| MATCH-002 | blue | strict | loss/TEAM_ELIMINATION | 21/10 | 12/11 | 29; 12/0/11/0/3 | 0/0 | 2/0/0 | 8840d8e4fb865f614b27c4e5a367ca9d825a3f010f68e4380a7d2cbed17e745f |
| MATCH-002 | blue | bounded | loss/PROVIDER_FORFEIT | 3/1 | 4/2 | 7; 0/0/0/3/0 | 0/0 | 1/0/0 | e0217d3afc1feb10fde3e67ac7bb4f0440acfc52fe7c50ce81d5c21a72828db4 |
| MATCH-002 | blue | stepwise | loss/CORE_DESTRUCTION | 10/4 | 13/5 | 13; 12/0/0/0/0 | 0/30 | 1/0/0 | 630c70acca8b8f66c2c1601db2ee8fa9deb78a3afa493431f9e204f2895ca772 |
| MATCH-003 | red | strict | loss/TEAM_ELIMINATION | 9/4 | 6/4 | 13; 1/0/6/0/0 | 0/0 | 1/0/2 | 6989d7f26bba06449809a535ce93820e4f8ec05bda5a2c174435a9cb3e80f768 |
| MATCH-003 | red | bounded | loss/TEAM_ELIMINATION | 10/4 | 7/5 | 17; 5/0/0/0/3 | 0/0 | 1/0/0 | f2f53cb1c67b228e3f181480461e9633af4aa6cf803faf9c08c4021f8db1e493 |
| MATCH-003 | red | stepwise | loss/CORE_DESTRUCTION | 11/5 | 16/5 | 24; 1/0/0/0/0 | 0/30 | 3/0/0 | cd8751d4e7780a5b961c75719b4311ef5f8d975b1207e056840a29b26a6c5a89 |
| MATCH-004 | blue | strict | loss/TEAM_ELIMINATION | 12/5 | 8/6 | 22; 2/1/5/0/0 | 0/15 | 1/0/0 | 30733168b5679b1dcb228bd7fe3b237068e63599a0380c15e38bb87a5d29f7a4 |
| MATCH-004 | blue | bounded | loss/TEAM_ELIMINATION | 8/3 | 12/4 | 14; 4/0/2/0/0 | 0/0 | 1/0/0 | 1f6efb7be975777850adcffae6099b787633e85e648068cd82468e34e45ade73 |
| MATCH-004 | blue | stepwise | win/CORE_DESTRUCTION | 7/3 | 15/4 | 14; 2/0/0/0/4 | 30/0 | 1/0/0 | a0b03604c518808ab021118078c94b4422474b2c5707eaa8537f89efe2beefe2 |
| MATCH-005 | red | strict | loss/CORE_DESTRUCTION | 7/3 | 4/3 | 11; 2/2/0/0/0 | 0/30 | 0/0/3 | c5d8f58675ae4bc3ae30544e13169e6c95f9a69e3473c3e4c3543f7cd12920ba |
| MATCH-005 | red | bounded | loss/TEAM_ELIMINATION | 12/5 | 10/6 | 29; 0/0/0/0/1 | 0/15 | 2/0/3 | 99fd244b014bd5efba51b5a8b646c94d88367191b740fe5d7ffd1f9dc817b204 |
| MATCH-005 | red | stepwise | loss/CORE_DESTRUCTION | 11/5 | 16/5 | 24; 1/0/0/0/0 | 0/30 | 2/1/0 | 1437bfd8b6b9199d40b42b61ef9a252a750e012f0fafc1da20491237c954aba7 |
| MATCH-006 | blue | strict | loss/TEAM_ELIMINATION | 33/16 | 26/17 | 55; 14/3/10/0/3 | 0/0 | 1/0/0 | 71550616ea60841abe25e92bcb74d1ec9efceff018ceb464d75e94a557d6dadd |
| MATCH-006 | blue | bounded | loss/TEAM_ELIMINATION | 10/4 | 13/5 | 20; 2/1/2/0/0 | 0/0 | 2/1/0 | 7eb1c54a5637995a32241b5905709f19dfa6e4efb73ff82049decc5f9cee111b |
| MATCH-006 | blue | stepwise | loss/CORE_DESTRUCTION | 10/4 | 15/5 | 17; 8/0/0/0/0 | 0/30 | 1/0/0 | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |
| MATCH-007 | red | strict | loss/TEAM_ELIMINATION | 7/3 | 4/3 | 8; 1/0/6/0/0 | 0/10 | 0/0/0 | ab50ee66a77f533eab8c0034407e8e20e2461e86a85de932d2f6ccd6269a596e |
| MATCH-007 | red | bounded | loss/CORE_DESTRUCTION | 9/4 | 9/4 | 17; 2/1/0/0/0 | 0/30 | 1/1/0 | 67b44626028493b42e86b1007a381f62cada3552508befc1231a1c92b7ab329e |
| MATCH-007 | red | stepwise | loss/TEAM_ELIMINATION | 8/3 | 12/4 | 17; 2/0/0/0/1 | 0/5 | 1/0/0 | f8dc815981f09fa7d27d50daee9e419e59fce44f321bbb9876041f54ec294a59 |
| MATCH-008 | blue | strict | loss/CORE_DESTRUCTION | 10/4 | 7/5 | 13; 0/0/12/0/0 | 0/30 | 1/0/0 | dfdca7bef66800e6b7abf59a0edacc1de64271c94143fa8bb4654161857c1b9a |
| MATCH-008 | blue | bounded | loss/TEAM_ELIMINATION | 10/4 | 9/5 | 16; 3/3/3/0/0 | 0/0 | 2/0/0 | 2b4664c7d629c2a439affcc13da3372c90f4fe0b7da4f5a7bb395794596c5182 |
| MATCH-008 | blue | stepwise | loss/CORE_DESTRUCTION | 12/5 | 21/6 | 24; 6/0/0/0/0 | 0/30 | 3/0/1 | 20d0c27aa2e8c152f495ce36736ba335e689dbcbf40607c54ac8e3a3cc64ad5d |
| MATCH-009 | red | strict | loss/CORE_DESTRUCTION | 9/4 | 6/4 | 9; 0/0/11/0/0 | 0/30 | 2/0/0 | 0691d5213a6486826c0d9c626234bd3ec531461c5afb5c6e8cf0d2cd3baee7c9 |
| MATCH-009 | red | bounded | loss/TEAM_ELIMINATION | 11/5 | 7/5 | 25; 0/0/0/0/0 | 0/15 | 2/0/3 | 4a55a81299e93b50a50fb3758133d6fbd4a1bc785dbc8f905cc18cd99331b2ee |
| MATCH-009 | red | stepwise | limit/REQUEST_LIMIT | 94/46 | 140/47 | 228; 2/0/0/5/0 | 0/18 | 44/0/26 | 7a6f5f92df9f3bd1ee6ad2a9f3f163e6ce4b9ef037f91dccf341f62183be1045 |
| MATCH-010 | blue | strict | loss/PROVIDER_FORFEIT | 5/2 | 4/3 | 10; 0/0/0/5/0 | 0/0 | 1/0/0 | e07574029ad1d9b0c59a6d457e1c5bbe9ff68d4032edc6d4bd6c75f2c0746588 |
| MATCH-010 | blue | bounded | loss/TEAM_ELIMINATION | 10/4 | 8/5 | 22; 3/0/0/0/0 | 0/5 | 2/0/0 | b5486ef6bbe03f644f6c6f30c98651029a82558a27c33ceb05326ee71bb96034 |
| MATCH-010 | blue | stepwise | loss/CORE_DESTRUCTION | 10/4 | 15/5 | 17; 8/0/0/0/0 | 0/30 | 1/0/0 | d0428918f2c8449304c23023cdc56739aab96844a785fe85c60019be0e39bf6c |

## Decision

**PASS for continuation unchanged, subject to separate authorization.** Integrity, replay, ledger, termination and stop mechanics all passed. Two repair-exhaustion forfeits and two correctly capped Stepwise request-limit games are visible data. The two long Stepwise games used 280/403 Stepwise requests; retain this cost-tail and censoring qualification. Total expenditure was manageable. See [decision.md](decision.md) for the full reasoning, bounded comparisons, and preliminary tactical interpretation. Batch 2 and the remaining 270 matches were not started.

Prepared outputs: case-study-report.md, analysis.json, plot-data.csv, and 11 PNG/SVG figures in plots/. Figures are partial-cohort descriptive views; n is at most 10 per control, not the completed 100-per-control study.
