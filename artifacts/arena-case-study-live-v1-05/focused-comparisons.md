# Focused descriptive comparisons through Batch 5 — INTERIM

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

## batch_5

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 5 | 0 | 5 | 0 | 0 | 0 | 24 | 4.8 | 1.5 |
| strict | blue | 5 | 0 | 5 | 0 | 2 | 0 | 31 | 6.2 | 1.24 |
| bounded | red | 5 | 0 | 5 | 0 | 1 | 0 | 58 | 11.6 | 1.52632 |
| bounded | blue | 5 | 0 | 5 | 0 | 5 | 0 | 33 | 6.6 | 2.0625 |
| stepwise | red | 5 | 0 | 4 | 1 | 1 | 1 | 214 | 42.8 | 3.10145 |
| stepwise | blue | 5 | 0 | 5 | 0 | 0 | 0 | 69 | 13.8 | 2.875 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 41 | 55 | 5.5 | 1.34146 | 158274 | 15827.4 | 3860.34146 | 103.60364 | 10.36036 | 2.52692 |
| bounded | 10 | 54 | 91 | 9.1 | 1.68519 | 252722 | 25272.2 | 4680.03704 | 150.63651 | 15.06365 | 2.78957 |
| stepwise | 10 | 93 | 283 | 28.3 | 3.04301 | 724340 | 72434.0 | 7788.60215 | 425.92466 | 42.59247 | 4.57984 |

Stepwise request distribution: `{"matches": 10, "capped": 1, "cap_rate": 0.1, "capped_request_share": 0.49469964664310956, "mean_including_caps": 28.3, "mean_excluding_caps": 15.88888888888889, "median": 15.5, "sorted_requests": [11, 14, 14, 15, 15, 16, 17, 17, 24, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 9, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 0, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 1, "stepwise_cap_other_two_natural": 1, "stepwise_cap_other_two_finish": 1, "provider_forfeit_difference": 7}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

| slot | side | outcomes | causes | requests | player_turns | core_damage | enemy_downs | finishes | revives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-041 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [5, 8, 16] | [7, 10, 11] | [0, 0, 0] | [0, 1, 3] | [0, 0, 0] | [2, 0, 0] |
| MATCH-042 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [11, 2, 14] | [15, 1, 10] | [0, 0, 0] | [2, 0, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-043 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "PROVIDER_FORFEIT"] | [7, 7, 24] | [11, 10, 14] | [0, 0, 0] | [1, 1, 4] | [0, 0, 0] | [2, 0, 1] |
| MATCH-044 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [6, 8, 15] | [10, 9, 10] | [0, 5, 0] | [1, 3, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-045 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [5, 14, 17] | [7, 16, 11] | [0, 0, 0] | [0, 3, 2] | [0, 1, 1] | [3, 3, 0] |
| MATCH-046 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [3, 3, 14] | [3, 3, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-047 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [4, 10, 140] | [5, 13, 94] | [0, 0, 0] | [0, 3, 44] | [0, 0, 0] | [0, 3, 25] |
| MATCH-048 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [7, 4, 15] | [12, 3, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [1, 0, 0] |
| MATCH-049 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [3, 19, 17] | [7, 29, 11] | [0, 0, 0] | [0, 1, 3] | [0, 1, 0] | [0, 22, 0] |
| MATCH-050 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 16, 11] | [7, 11, 8] | [0, 0, 0] | [1, 3, 0] | [0, 0, 0] | [0, 0, 0] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-047-stepwise | 47 | 140 | 1 | 2 | 25 | 44 | 0 | 107 | 44 | 26 | 0 |

## cumulative

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 25 | 0 | 25 | 0 | 2 | 0 | 133 | 5.32 | 1.33 |
| strict | blue | 25 | 0 | 25 | 0 | 8 | 0 | 214 | 8.56 | 1.32099 |
| bounded | red | 25 | 0 | 25 | 0 | 3 | 0 | 225 | 9.0 | 1.73077 |
| bounded | blue | 25 | 0 | 25 | 0 | 14 | 0 | 183 | 7.32 | 1.96774 |
| stepwise | red | 25 | 1 | 16 | 8 | 1 | 8 | 1496 | 59.84 | 3.07819 |
| stepwise | blue | 25 | 1 | 24 | 0 | 3 | 0 | 329 | 13.16 | 2.9375 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 50 | 262 | 347 | 6.94 | 1.32443 | 974125 | 19482.5 | 3718.03435 | 646.77883 | 12.93558 | 2.46862 |
| bounded | 50 | 223 | 408 | 8.16 | 1.8296 | 1143654 | 22873.08 | 5128.49327 | 717.49693 | 14.34994 | 3.21748 |
| stepwise | 50 | 598 | 1825 | 36.5 | 3.05184 | 4623631 | 92472.62 | 7731.82441 | 2835.63322 | 56.71266 | 4.74186 |

Stepwise request distribution: `{"matches": 50, "capped": 8, "cap_rate": 0.16, "capped_request_share": 0.6136986301369863, "mean_including_caps": 36.5, "mean_excluding_caps": 16.785714285714285, "median": 16.0, "sorted_requests": [2, 2, 4, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 17, 17, 18, 18, 21, 22, 24, 24, 24, 28, 36, 36, 42, 140, 140, 140, 140, 140, 140, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 40, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 2, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 8, "stepwise_cap_other_two_natural": 6, "stepwise_cap_other_two_finish": 8, "provider_forfeit_difference": 22}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

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
| MATCH-041 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [5, 8, 16] | [7, 10, 11] | [0, 0, 0] | [0, 1, 3] | [0, 0, 0] | [2, 0, 0] |
| MATCH-042 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [11, 2, 14] | [15, 1, 10] | [0, 0, 0] | [2, 0, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-043 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "PROVIDER_FORFEIT"] | [7, 7, 24] | [11, 10, 14] | [0, 0, 0] | [1, 1, 4] | [0, 0, 0] | [2, 0, 1] |
| MATCH-044 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [6, 8, 15] | [10, 9, 10] | [0, 5, 0] | [1, 3, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-045 | red | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [5, 14, 17] | [7, 16, 11] | [0, 0, 0] | [0, 3, 2] | [0, 1, 1] | [3, 3, 0] |
| MATCH-046 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [3, 3, 14] | [3, 3, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-047 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [4, 10, 140] | [5, 13, 94] | [0, 0, 0] | [0, 3, 44] | [0, 0, 0] | [0, 3, 25] |
| MATCH-048 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [7, 4, 15] | [12, 3, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [1, 0, 0] |
| MATCH-049 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [3, 19, 17] | [7, 29, 11] | [0, 0, 0] | [0, 1, 3] | [0, 1, 0] | [0, 22, 0] |
| MATCH-050 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 16, 11] | [7, 11, 8] | [0, 0, 0] | [1, 3, 0] | [0, 0, 0] | [0, 0, 0] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-001-stepwise | 47 | 140 | 0 | 2 | 44 | 44 | 0 | 88 | 44 | 45 | 0 |
| MATCH-009-stepwise | 47 | 140 | 2 | 2 | 26 | 44 | 0 | 105 | 44 | 28 | 0 |
| MATCH-015-stepwise | 46 | 140 | 3 | 2 | 4 | 43 | 0 | 125 | 43 | 5 | 0 |
| MATCH-021-stepwise | 47 | 140 | 0 | 1 | 0 | 44 | 1 | 132 | 44 | 1 | 0 |
| MATCH-031-stepwise | 47 | 140 | 2 | 2 | 0 | 44 | 0 | 132 | 44 | 1 | 0 |
| MATCH-033-stepwise | 47 | 140 | 2 | 1 | 43 | 41 | 1 | 42 | 42 | 46 | 0 |
| MATCH-037-stepwise | 47 | 140 | 0 | 2 | 28 | 44 | 0 | 104 | 44 | 29 | 0 |
| MATCH-047-stepwise | 47 | 140 | 1 | 2 | 25 | 44 | 0 | 107 | 44 | 26 | 0 |

Complete nonterminal Core/unit states and hashes: [cap-details.json](cap-details.json). AP/stop distributions and frozen Wilson/paired outputs are in the main reports. No model judge, hidden reasoning or causal explanation is inferred from these counts.
