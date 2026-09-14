# Focused descriptive comparisons through Batch 4 — INTERIM

## batch_4

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 5 | 0 | 5 | 0 | 1 | 0 | 21 | 4.2 | 1.4 |
| strict | blue | 5 | 0 | 5 | 0 | 1 | 0 | 33 | 6.6 | 1.375 |
| bounded | red | 5 | 0 | 5 | 0 | 1 | 0 | 52 | 10.4 | 2.16667 |
| bounded | blue | 5 | 0 | 5 | 0 | 2 | 0 | 33 | 6.6 | 1.83333 |
| stepwise | red | 5 | 0 | 2 | 3 | 0 | 3 | 480 | 96.0 | 3.01887 |
| stepwise | blue | 5 | 0 | 5 | 0 | 0 | 0 | 65 | 13.0 | 2.82609 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 39 | 54 | 5.4 | 1.38462 | 155616 | 15561.6 | 3990.15385 | 106.61146 | 10.66115 | 2.73363 |
| bounded | 10 | 42 | 85 | 8.5 | 2.02381 | 237784 | 23778.4 | 5661.52381 | 160.28269 | 16.02827 | 3.81625 |
| stepwise | 10 | 182 | 545 | 54.5 | 2.99451 | 1346955 | 134695.5 | 7400.85165 | 814.73514 | 81.47351 | 4.47657 |

Stepwise request distribution: `{"matches": 10, "capped": 3, "cap_rate": 0.3, "capped_request_share": 0.7706422018348624, "mean_including_caps": 54.5, "mean_excluding_caps": 17.857142857142858, "median": 17.0, "sorted_requests": [11, 11, 13, 14, 16, 18, 42, 140, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 7, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 0, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 3, "stepwise_cap_other_two_natural": 1, "stepwise_cap_other_two_finish": 3, "provider_forfeit_difference": 4}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

| slot | side | outcomes | causes | requests | player_turns | core_damage | enemy_downs | finishes | revives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-031 | red | ["loss", "loss", "limit"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [2, 11, 140] | [2, 8, 94] | [0, 0, 0] | [0, 1, 44] | [0, 0, 0] | [0, 0, 0] |
| MATCH-032 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [2, 4, 14] | [1, 1, 10] | [0, 0, 0] | [0, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-033 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [3, 14, 140] | [5, 13, 94] | [0, 0, 0] | [0, 3, 42] | [0, 1, 1] | [0, 2, 43] |
| MATCH-034 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "TEAM_ELIMINATION"] | [6, 8, 11] | [10, 10, 8] | [0, 0, 0] | [1, 2, 0] | [0, 0, 0] | [0, 0, 1] |
| MATCH-035 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [5, 16, 18] | [7, 15, 11] | [0, 0, 0] | [0, 3, 2] | [0, 1, 1] | [0, 3, 0] |
| MATCH-036 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [8, 6, 11] | [12, 6, 8] | [0, 0, 0] | [1, 1, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-037 | red | ["loss", "loss", "limit"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "REQUEST_LIMIT"] | [4, 4, 140] | [7, 4, 94] | [0, 0, 0] | [0, 0, 44] | [0, 0, 0] | [0, 0, 28] |
| MATCH-038 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [7, 10, 13] | [10, 12, 10] | [0, 0, 0] | [3, 4, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-039 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [7, 7, 42] | [12, 10, 27] | [0, 0, 0] | [1, 1, 1] | [0, 0, 1] | [0, 0, 0] |
| MATCH-040 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [10, 5, 16] | [14, 5, 10] | [0, 0, 0] | [2, 1, 1] | [0, 0, 0] | [0, 0, 0] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-031-stepwise | 47 | 140 | 2 | 2 | 0 | 44 | 0 | 132 | 44 | 1 | 0 |
| MATCH-033-stepwise | 47 | 140 | 2 | 1 | 43 | 41 | 1 | 42 | 42 | 46 | 0 |
| MATCH-037-stepwise | 47 | 140 | 0 | 2 | 28 | 44 | 0 | 104 | 44 | 29 | 0 |

## cumulative

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 20 | 0 | 20 | 0 | 2 | 0 | 109 | 5.45 | 1.29762 |
| strict | blue | 20 | 0 | 20 | 0 | 6 | 0 | 183 | 9.15 | 1.33577 |
| bounded | red | 20 | 0 | 20 | 0 | 2 | 0 | 167 | 8.35 | 1.81522 |
| bounded | blue | 20 | 0 | 20 | 0 | 9 | 0 | 150 | 7.5 | 1.94805 |
| stepwise | red | 20 | 1 | 12 | 7 | 0 | 7 | 1282 | 64.1 | 3.07434 |
| stepwise | blue | 20 | 1 | 19 | 0 | 3 | 0 | 260 | 13.0 | 2.95455 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 40 | 221 | 292 | 7.3 | 1.32127 | 815851 | 20396.275 | 3691.63348 | 543.17519 | 13.57938 | 2.45781 |
| bounded | 40 | 169 | 317 | 7.925 | 1.87574 | 890932 | 22273.3 | 5271.78698 | 566.86042 | 14.17151 | 3.3542 |
| stepwise | 40 | 505 | 1542 | 38.55 | 3.05347 | 3899291 | 97482.275 | 7721.36832 | 2409.70856 | 60.24271 | 4.7717 |

Stepwise request distribution: `{"matches": 40, "capped": 7, "cap_rate": 0.175, "capped_request_share": 0.6355382619974059, "mean_including_caps": 38.55, "mean_excluding_caps": 17.03030303030303, "median": 16.0, "sorted_requests": [2, 2, 4, 11, 11, 12, 12, 13, 13, 13, 14, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 18, 18, 21, 22, 24, 24, 28, 36, 36, 42, 140, 140, 140, 140, 140, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 31, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 2, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 7, "stepwise_cap_other_two_natural": 5, "stepwise_cap_other_two_finish": 7, "provider_forfeit_difference": 15}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

| slot | side | outcomes | causes | requests | player_turns | core_damage | enemy_downs | finishes | revives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-001 | red | ["loss", "loss", "limit"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [8, 16, 140] | [11, 18, 94] | [0, 0, 0] | [1, 2, 44] | [1, 0, 0] | [0, 0, 44] |
| MATCH-002 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [12, 4, 13] | [21, 3, 10] | [0, 0, 0] | [2, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-003 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [6, 7, 16] | [9, 10, 11] | [0, 0, 0] | [1, 1, 3] | [0, 0, 0] | [2, 0, 0] |
| MATCH-004 | blue | ["loss", "loss", "win"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [8, 12, 15] | [12, 8, 7] | [0, 0, 30] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-005 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [4, 10, 16] | [7, 12, 11] | [0, 0, 0] | [0, 2, 2] | [0, 0, 1] | [3, 3, 0] |
| MATCH-006 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [26, 13, 15] | [33, 10, 10] | [0, 0, 0] | [1, 2, 1] | [0, 1, 0] | [0, 0, 0] |
| MATCH-007 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "TEAM_ELIMINATION"] | [4, 9, 12] | [7, 9, 8] | [0, 0, 0] | [0, 1, 1] | [0, 1, 0] | [0, 0, 0] |
| MATCH-008 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [7, 9, 21] | [10, 10, 12] | [0, 0, 0] | [1, 2, 3] | [0, 0, 0] | [0, 0, 1] |
| MATCH-009 | red | ["loss", "loss", "limit"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [6, 7, 140] | [9, 11, 94] | [0, 0, 0] | [2, 2, 44] | [0, 0, 0] | [0, 3, 26] |
| MATCH-010 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [4, 8, 15] | [5, 10, 10] | [0, 0, 0] | [1, 2, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-011 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [19, 7, 24] | [38, 10, 15] | [0, 0, 0] | [2, 1, 2] | [0, 0, 2] | [3, 0, 1] |
| MATCH-012 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [7, 15, 12] | [12, 14, 10] | [0, 0, 0] | [1, 4, 1] | [0, 1, 0] | [0, 0, 0] |
| MATCH-013 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [7, 6, 24] | [9, 10, 15] | [0, 0, 0] | [1, 1, 3] | [0, 0, 1] | [0, 0, 0] |
| MATCH-014 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [8, 4, 15] | [12, 5, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-015 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [5, 8, 140] | [10, 10, 92] | [0, 0, 0] | [1, 1, 43] | [0, 0, 0] | [0, 0, 4] |
| MATCH-016 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "PROVIDER_FORFEIT"] | [6, 9, 2] | [10, 10, 1] | [0, 0, 0] | [2, 1, 0] | [0, 0, 0] | [0, 1, 0] |
| MATCH-017 | red | ["loss", "loss", "win"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "TEAM_ELIMINATION"] | [3, 10, 36] | [7, 11, 18] | [0, 0, 0] | [0, 1, 5] | [0, 1, 3] | [0, 1, 0] |
| MATCH-018 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "TEAM_ELIMINATION"] | [4, 6, 16] | [3, 5, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-019 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [2, 3, 18] | [2, 7, 11] | [0, 0, 0] | [0, 0, 3] | [0, 0, 1] | [0, 3, 0] |
| MATCH-020 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "TEAM_ELIMINATION"] | [3, 6, 22] | [3, 5, 13] | [0, 0, 0] | [1, 1, 2] | [0, 0, 1] | [0, 0, 2] |
| MATCH-021 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [5, 6, 140] | [7, 5, 94] | [0, 0, 0] | [0, 0, 44] | [0, 0, 0] | [0, 0, 0] |
| MATCH-022 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "PROVIDER_FORFEIT"] | [36, 8, 4] | [57, 8, 1] | [0, 0, 0] | [3, 1, 1] | [0, 0, 0] | [2, 1, 0] |
| MATCH-023 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [4, 5, 36] | [7, 7, 23] | [0, 0, 0] | [0, 0, 3] | [0, 0, 1] | [0, 0, 6] |
| MATCH-024 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [8, 4, 15] | [12, 3, 10] | [0, 0, 0] | [1, 0, 1] | [0, 0, 0] | [1, 0, 0] |
| MATCH-025 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [3, 12, 28] | [7, 11, 17] | [0, 0, 0] | [0, 2, 4] | [0, 0, 1] | [0, 3, 1] |
| MATCH-026 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [8, 7, 13] | [14, 7, 10] | [0, 0, 0] | [2, 2, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-027 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [6, 7, 16] | [11, 10, 11] | [0, 0, 0] | [3, 1, 3] | [0, 0, 0] | [0, 0, 0] |
| MATCH-028 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "PROVIDER_FORFEIT"] | [6, 3, 2] | [5, 3, 1] | [0, 0, 0] | [0, 1, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-029 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [6, 2, 16] | [9, 2, 11] | [0, 0, 0] | [2, 0, 3] | [0, 0, 0] | [0, 0, 0] |
| MATCH-030 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [7, 9, 15] | [10, 10, 10] | [0, 0, 0] | [2, 1, 3] | [0, 0, 0] | [0, 1, 1] |
| MATCH-031 | red | ["loss", "loss", "limit"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [2, 11, 140] | [2, 8, 94] | [0, 0, 0] | [0, 1, 44] | [0, 0, 0] | [0, 0, 0] |
| MATCH-032 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [2, 4, 14] | [1, 1, 10] | [0, 0, 0] | [0, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-033 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [3, 14, 140] | [5, 13, 94] | [0, 0, 0] | [0, 3, 42] | [0, 1, 1] | [0, 2, 43] |
| MATCH-034 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "TEAM_ELIMINATION"] | [6, 8, 11] | [10, 10, 8] | [0, 0, 0] | [1, 2, 0] | [0, 0, 0] | [0, 0, 1] |
| MATCH-035 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [5, 16, 18] | [7, 15, 11] | [0, 0, 0] | [0, 3, 2] | [0, 1, 1] | [0, 3, 0] |
| MATCH-036 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [8, 6, 11] | [12, 6, 8] | [0, 0, 0] | [1, 1, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-037 | red | ["loss", "loss", "limit"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "REQUEST_LIMIT"] | [4, 4, 140] | [7, 4, 94] | [0, 0, 0] | [0, 0, 44] | [0, 0, 0] | [0, 0, 28] |
| MATCH-038 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [7, 10, 13] | [10, 12, 10] | [0, 0, 0] | [3, 4, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-039 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [7, 7, 42] | [12, 10, 27] | [0, 0, 0] | [1, 1, 1] | [0, 0, 1] | [0, 0, 0] |
| MATCH-040 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [10, 5, 16] | [14, 5, 10] | [0, 0, 0] | [2, 1, 1] | [0, 0, 0] | [0, 0, 0] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-001-stepwise | 47 | 140 | 0 | 2 | 44 | 44 | 0 | 88 | 44 | 45 | 0 |
| MATCH-009-stepwise | 47 | 140 | 2 | 2 | 26 | 44 | 0 | 105 | 44 | 28 | 0 |
| MATCH-015-stepwise | 46 | 140 | 3 | 2 | 4 | 43 | 0 | 125 | 43 | 5 | 0 |
| MATCH-021-stepwise | 47 | 140 | 0 | 1 | 0 | 44 | 1 | 132 | 44 | 1 | 0 |
| MATCH-031-stepwise | 47 | 140 | 2 | 2 | 0 | 44 | 0 | 132 | 44 | 1 | 0 |
| MATCH-033-stepwise | 47 | 140 | 2 | 1 | 43 | 41 | 1 | 42 | 42 | 46 | 0 |
| MATCH-037-stepwise | 47 | 140 | 0 | 2 | 28 | 44 | 0 | 104 | 44 | 29 | 0 |

Complete nonterminal Core/unit states and hashes: [cap-details.json](cap-details.json). AP/stop distributions and frozen Wilson/paired outputs are in the main reports. No model judge, hidden reasoning or causal explanation is inferred from these counts.
