# Focused descriptive comparisons through Batch 8 — INTERIM

## batch_6

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 5 | 0 | 5 | 0 | 2 | 0 | 25 | 5.0 | 1.08696 |
| strict | blue | 5 | 0 | 5 | 0 | 3 | 0 | 23 | 4.6 | 1.4375 |
| bounded | red | 5 | 0 | 5 | 0 | 2 | 0 | 70 | 14.0 | 1.2069 |
| bounded | blue | 5 | 0 | 5 | 0 | 3 | 0 | 54 | 10.8 | 2.07692 |
| stepwise | red | 5 | 0 | 4 | 1 | 0 | 1 | 204 | 40.8 | 3.04478 |
| stepwise | blue | 5 | 0 | 4 | 1 | 0 | 1 | 199 | 39.8 | 3.06154 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 39 | 48 | 4.8 | 1.23077 | 136359 | 13635.9 | 3496.38462 | 93.22719 | 9.32272 | 2.39044 |
| bounded | 10 | 84 | 124 | 12.4 | 1.47619 | 310758 | 31075.8 | 3699.5 | 227.3238 | 22.73238 | 2.70624 |
| stepwise | 10 | 132 | 403 | 40.3 | 3.05303 | 998721 | 99872.1 | 7566.06818 | 572.60764 | 57.26076 | 4.33794 |

Stepwise request distribution: `{"matches": 10, "capped": 2, "cap_rate": 0.2, "capped_request_share": 0.6947890818858561, "mean_including_caps": 40.3, "mean_excluding_caps": 15.375, "median": 15.0, "sorted_requests": [11, 12, 12, 14, 15, 15, 17, 27, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 8, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 0, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 2, "stepwise_cap_other_two_natural": 1, "stepwise_cap_other_two_finish": 2, "provider_forfeit_difference": 8}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

| slot | side | outcomes | causes | requests | player_turns | core_damage | enemy_downs | finishes | revives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-051 | red | ["loss", "loss", "limit"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [5, 49, 140] | [11, 91, 94] | [0, 0, 0] | [3, 1, 44] | [0, 1, 0] | [0, 84, 27] |
| MATCH-052 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [3, 10, 12] | [3, 8, 8] | [0, 0, 0] | [1, 1, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-053 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [2, 2, 27] | [2, 2, 17] | [0, 0, 0] | [0, 0, 4] | [0, 0, 1] | [0, 0, 1] |
| MATCH-054 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [6, 6, 17] | [8, 5, 12] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [1, 0, 0] |
| MATCH-055 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "TEAM_ELIMINATION"] | [3, 4, 11] | [7, 4, 7] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 1] |
| MATCH-056 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [3, 27, 15] | [3, 28, 10] | [0, 18, 0] | [1, 4, 3] | [0, 1, 0] | [0, 2, 1] |
| MATCH-057 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [13, 6, 12] | [26, 10, 9] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-058 | blue | ["loss", "loss", "limit"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "REQUEST_LIMIT"] | [4, 7, 140] | [3, 7, 89] | [0, 9, 0] | [1, 1, 2] | [0, 0, 1] | [0, 0, 0] |
| MATCH-059 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [2, 9, 14] | [2, 11, 10] | [0, 0, 0] | [0, 1, 1] | [0, 1, 0] | [0, 4, 0] |
| MATCH-060 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [7, 4, 15] | [12, 1, 10] | [0, 0, 0] | [1, 1, 3] | [0, 0, 0] | [0, 0, 1] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-051-stepwise | 47 | 140 | 2 | 2 | 27 | 44 | 0 | 104 | 44 | 29 | 0 |
| MATCH-058-stepwise | 45 | 140 | 6 | 39 | 0 | 0 | 1 | 0 | 2 | 3 | 0 |

## batch_7

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 5 | 0 | 5 | 0 | 0 | 0 | 52 | 10.4 | 1.13043 |
| strict | blue | 5 | 0 | 5 | 0 | 2 | 0 | 30 | 6.0 | 1.36364 |
| bounded | red | 5 | 0 | 5 | 0 | 2 | 0 | 39 | 7.8 | 1.77273 |
| bounded | blue | 5 | 0 | 5 | 0 | 2 | 0 | 50 | 10.0 | 1.92308 |
| stepwise | red | 5 | 0 | 2 | 3 | 0 | 3 | 504 | 100.8 | 3.01796 |
| stepwise | blue | 5 | 1 | 4 | 0 | 0 | 0 | 81 | 16.2 | 3.0 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 68 | 82 | 8.2 | 1.20588 | 229193 | 22919.3 | 3370.48529 | 141.66632 | 14.16663 | 2.08333 |
| bounded | 10 | 48 | 89 | 8.9 | 1.85417 | 248890 | 24889.0 | 5185.20833 | 166.13159 | 16.61316 | 3.46107 |
| stepwise | 10 | 194 | 585 | 58.5 | 3.01546 | 1502645 | 150264.5 | 7745.59278 | 804.63122 | 80.46312 | 4.14758 |

Stepwise request distribution: `{"matches": 10, "capped": 3, "cap_rate": 0.3, "capped_request_share": 0.717948717948718, "mean_including_caps": 58.5, "mean_excluding_caps": 23.571428571428573, "median": 19.5, "sorted_requests": [13, 15, 15, 16, 17, 22, 67, 140, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 6, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 1, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 3, "stepwise_cap_other_two_natural": 3, "stepwise_cap_other_two_finish": 3, "provider_forfeit_difference": 5}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

| slot | side | outcomes | causes | requests | player_turns | core_damage | enemy_downs | finishes | revives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-061 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 6, 17] | [7, 6, 11] | [0, 0, 0] | [0, 0, 2] | [0, 0, 1] | [0, 0, 0] |
| MATCH-062 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [7, 4, 15] | [10, 1, 10] | [0, 0, 0] | [3, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-063 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [4, 12, 140] | [7, 14, 94] | [0, 0, 0] | [0, 1, 44] | [0, 0, 0] | [0, 0, 33] |
| MATCH-064 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 8, 13] | [3, 7, 10] | [0, 0, 0] | [1, 2, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-065 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "TEAM_ELIMINATION"] | [8, 5, 67] | [16, 6, 44] | [0, 0, 0] | [2, 0, 3] | [0, 0, 1] | [3, 0, 2] |
| MATCH-066 | blue | ["loss", "loss", "win"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [8, 10, 22] | [14, 10, 13] | [0, 0, 30] | [4, 1, 2] | [0, 0, 0] | [0, 0, 0] |
| MATCH-067 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [6, 9, 140] | [12, 13, 92] | [0, 0, 0] | [1, 3, 43] | [0, 0, 0] | [0, 3, 3] |
| MATCH-068 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [4, 13, 15] | [3, 16, 10] | [0, 0, 0] | [0, 2, 3] | [0, 0, 0] | [0, 2, 0] |
| MATCH-069 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [30, 7, 140] | [52, 7, 94] | [0, 0, 0] | [1, 0, 44] | [0, 0, 0] | [0, 0, 0] |
| MATCH-070 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [7, 15, 16] | [12, 16, 10] | [0, 0, 0] | [4, 3, 1] | [0, 0, 0] | [0, 0, 0] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-063-stepwise | 47 | 140 | 1 | 2 | 33 | 44 | 0 | 99 | 44 | 34 | 0 |
| MATCH-067-stepwise | 46 | 140 | 2 | 1 | 3 | 43 | 2 | 125 | 43 | 4 | 0 |
| MATCH-069-stepwise | 47 | 140 | 0 | 2 | 0 | 44 | 0 | 132 | 44 | 1 | 0 |

## batch_8

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 5 | 0 | 5 | 0 | 1 | 0 | 23 | 4.6 | 1.21053 |
| strict | blue | 5 | 0 | 5 | 0 | 2 | 0 | 55 | 11.0 | 1.34146 |
| bounded | red | 5 | 0 | 5 | 0 | 1 | 0 | 36 | 7.2 | 1.8 |
| bounded | blue | 5 | 0 | 5 | 0 | 2 | 0 | 38 | 7.6 | 1.72727 |
| stepwise | red | 5 | 0 | 3 | 2 | 0 | 2 | 342 | 68.4 | 3.0 |
| stepwise | blue | 5 | 0 | 5 | 0 | 0 | 0 | 74 | 14.8 | 2.96 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 10 | 60 | 78 | 7.8 | 1.3 | 205853 | 20585.3 | 3430.88333 | 124.87361 | 12.48736 | 2.08123 |
| bounded | 10 | 42 | 74 | 7.4 | 1.7619 | 208636 | 20863.6 | 4967.52381 | 131.83177 | 13.18318 | 3.13885 |
| stepwise | 10 | 139 | 416 | 41.6 | 2.99281 | 1055229 | 105522.9 | 7591.57554 | 572.54908 | 57.25491 | 4.11906 |

Stepwise request distribution: `{"matches": 10, "capped": 2, "cap_rate": 0.2, "capped_request_share": 0.6730769230769231, "mean_including_caps": 41.6, "mean_excluding_caps": 17, "median": 16.5, "sorted_requests": [9, 14, 14, 16, 16, 17, 21, 29, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 8, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 0, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 2, "stepwise_cap_other_two_natural": 2, "stepwise_cap_other_two_finish": 2, "provider_forfeit_difference": 4}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

| slot | side | outcomes | causes | requests | player_turns | core_damage | enemy_downs | finishes | revives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-071 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [5, 10, 17] | [10, 13, 13] | [0, 0, 0] | [1, 2, 3] | [0, 0, 0] | [0, 2, 1] |
| MATCH-072 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [4, 8, 9] | [8, 8, 6] | [0, 0, 0] | [1, 2, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-073 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [2, 3, 16] | [2, 2, 11] | [0, 0, 0] | [0, 0, 3] | [0, 0, 0] | [0, 0, 0] |
| MATCH-074 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [3, 9, 14] | [3, 12, 10] | [0, 10, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-075 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [7, 10, 140] | [10, 8, 94] | [0, 0, 0] | [1, 1, 44] | [0, 0, 0] | [0, 0, 44] |
| MATCH-076 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "TEAM_ELIMINATION"] | [36, 7, 21] | [54, 10, 14] | [0, 0, 0] | [1, 2, 4] | [0, 0, 0] | [0, 0, 1] |
| MATCH-077 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [4, 4, 29] | [7, 7, 19] | [0, 0, 0] | [0, 0, 3] | [0, 0, 1] | [0, 2, 2] |
| MATCH-078 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [8, 6, 16] | [12, 3, 10] | [0, 0, 0] | [1, 1, 3] | [0, 0, 0] | [0, 0, 1] |
| MATCH-079 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [5, 9, 140] | [10, 13, 94] | [0, 0, 0] | [1, 0, 44] | [0, 0, 0] | [0, 4, 26] |
| MATCH-080 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 8, 14] | [3, 9, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 1, 0] |

| match_id | luna_turns | requests | repairs | end_turns | luna_revives | heuristic_revives | luna_heals | heuristic_heals | luna_enemy_downs | heuristic_enemy_downs | luna_core_damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MATCH-075-stepwise | 47 | 140 | 1 | 2 | 44 | 44 | 0 | 88 | 44 | 45 | 0 |
| MATCH-079-stepwise | 47 | 140 | 2 | 2 | 26 | 44 | 0 | 105 | 44 | 28 | 0 |

## cumulative

| control | side | matches | wins | losses | no_results | forfeits | caps | requests | requests_per_match | requests_per_luna_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | red | 40 | 0 | 40 | 0 | 5 | 0 | 233 | 5.825 | 1.23936 |
| strict | blue | 40 | 0 | 40 | 0 | 15 | 0 | 322 | 8.05 | 1.3361 |
| bounded | red | 40 | 0 | 40 | 0 | 8 | 0 | 370 | 9.25 | 1.6087 |
| bounded | blue | 40 | 0 | 40 | 0 | 21 | 0 | 325 | 8.125 | 1.94611 |
| stepwise | red | 40 | 1 | 25 | 14 | 1 | 14 | 2546 | 63.65 | 3.05276 |
| stepwise | blue | 40 | 2 | 37 | 1 | 3 | 1 | 683 | 17.075 | 2.98253 |

| control | matches | luna_turns | provider_requests | provider_requests_per_match | provider_requests_per_turn | total_tokens | total_tokens_per_match | total_tokens_per_turn | provider_latency_seconds | provider_latency_seconds_per_match | provider_latency_seconds_per_turn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strict | 80 | 429 | 555 | 6.9375 | 1.29371 | 1545530 | 19319.125 | 3602.63403 | 1006.54595 | 12.58182 | 2.34626 |
| bounded | 80 | 397 | 695 | 8.6875 | 1.75063 | 1911938 | 23899.225 | 4815.96474 | 1242.78408 | 15.5348 | 3.13044 |
| stepwise | 80 | 1063 | 3229 | 40.3625 | 3.03763 | 8180226 | 102252.825 | 7695.41486 | 4785.42116 | 59.81776 | 4.50181 |

Stepwise request distribution: `{"matches": 80, "capped": 15, "cap_rate": 0.1875, "capped_request_share": 0.6503561474140601, "mean_including_caps": 40.3625, "mean_excluding_caps": 17.369230769230768, "median": 16.0, "sorted_requests": [2, 2, 4, 9, 11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 17, 17, 17, 17, 17, 18, 18, 21, 21, 22, 22, 24, 24, 24, 27, 28, 29, 36, 36, 42, 67, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140]}`. Uncapped games include provider forfeits; caps censor natural length. The empirical sorted distribution is descriptive, not an additional inferential test.

Matched-triplet classification counts (some categories overlap): `{"all_three_lose": 62, "all_three_win": 0, "strict_only_win": 0, "bounded_only_win": 0, "stepwise_only_win": 3, "strict_bounded_win": 0, "bounded_stepwise_win": 0, "strict_stepwise_win": 0, "mixed_no_result": 15, "stepwise_cap_other_two_natural": 12, "stepwise_cap_other_two_finish": 15, "provider_forfeit_difference": 39}`. Natural termination excludes forfeits and limits; “finish” here includes forfeits. Order in the table is Strict / Bounded / Stepwise.

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
| MATCH-051 | red | ["loss", "loss", "limit"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [5, 49, 140] | [11, 91, 94] | [0, 0, 0] | [3, 1, 44] | [0, 1, 0] | [0, 84, 27] |
| MATCH-052 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [3, 10, 12] | [3, 8, 8] | [0, 0, 0] | [1, 1, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-053 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [2, 2, 27] | [2, 2, 17] | [0, 0, 0] | [0, 0, 4] | [0, 0, 1] | [0, 0, 1] |
| MATCH-054 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [6, 6, 17] | [8, 5, 12] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [1, 0, 0] |
| MATCH-055 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "TEAM_ELIMINATION"] | [3, 4, 11] | [7, 4, 7] | [0, 0, 0] | [0, 0, 0] | [0, 0, 0] | [0, 0, 1] |
| MATCH-056 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [3, 27, 15] | [3, 28, 10] | [0, 18, 0] | [1, 4, 3] | [0, 1, 0] | [0, 2, 1] |
| MATCH-057 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [13, 6, 12] | [26, 10, 9] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-058 | blue | ["loss", "loss", "limit"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "REQUEST_LIMIT"] | [4, 7, 140] | [3, 7, 89] | [0, 9, 0] | [1, 1, 2] | [0, 0, 1] | [0, 0, 0] |
| MATCH-059 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "TEAM_ELIMINATION", "TEAM_ELIMINATION"] | [2, 9, 14] | [2, 11, 10] | [0, 0, 0] | [0, 1, 1] | [0, 1, 0] | [0, 4, 0] |
| MATCH-060 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [7, 4, 15] | [12, 1, 10] | [0, 0, 0] | [1, 1, 3] | [0, 0, 0] | [0, 0, 1] |
| MATCH-061 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 6, 17] | [7, 6, 11] | [0, 0, 0] | [0, 0, 2] | [0, 0, 1] | [0, 0, 0] |
| MATCH-062 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [7, 4, 15] | [10, 1, 10] | [0, 0, 0] | [3, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-063 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [4, 12, 140] | [7, 14, 94] | [0, 0, 0] | [0, 1, 44] | [0, 0, 0] | [0, 0, 33] |
| MATCH-064 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 8, 13] | [3, 7, 10] | [0, 0, 0] | [1, 2, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-065 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "TEAM_ELIMINATION"] | [8, 5, 67] | [16, 6, 44] | [0, 0, 0] | [2, 0, 3] | [0, 0, 1] | [3, 0, 2] |
| MATCH-066 | blue | ["loss", "loss", "win"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [8, 10, 22] | [14, 10, 13] | [0, 0, 30] | [4, 1, 2] | [0, 0, 0] | [0, 0, 0] |
| MATCH-067 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [6, 9, 140] | [12, 13, 92] | [0, 0, 0] | [1, 3, 43] | [0, 0, 0] | [0, 3, 3] |
| MATCH-068 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [4, 13, 15] | [3, 16, 10] | [0, 0, 0] | [0, 2, 3] | [0, 0, 0] | [0, 2, 0] |
| MATCH-069 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [30, 7, 140] | [52, 7, 94] | [0, 0, 0] | [1, 0, 44] | [0, 0, 0] | [0, 0, 0] |
| MATCH-070 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [7, 15, 16] | [12, 16, 10] | [0, 0, 0] | [4, 3, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-071 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "CORE_DESTRUCTION"] | [5, 10, 17] | [10, 13, 13] | [0, 0, 0] | [1, 2, 3] | [0, 0, 0] | [0, 2, 1] |
| MATCH-072 | blue | ["loss", "loss", "loss"] | ["CORE_DESTRUCTION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [4, 8, 9] | [8, 8, 6] | [0, 0, 0] | [1, 2, 0] | [0, 0, 0] | [0, 0, 0] |
| MATCH-073 | red | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [2, 3, 16] | [2, 2, 11] | [0, 0, 0] | [0, 0, 3] | [0, 0, 0] | [0, 0, 0] |
| MATCH-074 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [3, 9, 14] | [3, 12, 10] | [0, 10, 0] | [1, 1, 1] | [0, 0, 0] | [0, 0, 0] |
| MATCH-075 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [7, 10, 140] | [10, 8, 94] | [0, 0, 0] | [1, 1, 44] | [0, 0, 0] | [0, 0, 44] |
| MATCH-076 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "TEAM_ELIMINATION"] | [36, 7, 21] | [54, 10, 14] | [0, 0, 0] | [1, 2, 4] | [0, 0, 0] | [0, 0, 1] |
| MATCH-077 | red | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "CORE_DESTRUCTION", "CORE_DESTRUCTION"] | [4, 4, 29] | [7, 7, 19] | [0, 0, 0] | [0, 0, 3] | [0, 0, 1] | [0, 2, 2] |
| MATCH-078 | blue | ["loss", "loss", "loss"] | ["TEAM_ELIMINATION", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [8, 6, 16] | [12, 3, 10] | [0, 0, 0] | [1, 1, 3] | [0, 0, 0] | [0, 0, 1] |
| MATCH-079 | red | ["loss", "loss", "limit"] | ["TEAM_ELIMINATION", "TEAM_ELIMINATION", "REQUEST_LIMIT"] | [5, 9, 140] | [10, 13, 94] | [0, 0, 0] | [1, 0, 44] | [0, 0, 0] | [0, 4, 26] |
| MATCH-080 | blue | ["loss", "loss", "loss"] | ["PROVIDER_FORFEIT", "PROVIDER_FORFEIT", "CORE_DESTRUCTION"] | [4, 8, 14] | [3, 9, 10] | [0, 0, 0] | [1, 1, 1] | [0, 0, 0] | [0, 1, 0] |

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
| MATCH-051-stepwise | 47 | 140 | 2 | 2 | 27 | 44 | 0 | 104 | 44 | 29 | 0 |
| MATCH-058-stepwise | 45 | 140 | 6 | 39 | 0 | 0 | 1 | 0 | 2 | 3 | 0 |
| MATCH-063-stepwise | 47 | 140 | 1 | 2 | 33 | 44 | 0 | 99 | 44 | 34 | 0 |
| MATCH-067-stepwise | 46 | 140 | 2 | 1 | 3 | 43 | 2 | 125 | 43 | 4 | 0 |
| MATCH-069-stepwise | 47 | 140 | 0 | 2 | 0 | 44 | 0 | 132 | 44 | 1 | 0 |
| MATCH-075-stepwise | 47 | 140 | 1 | 2 | 44 | 44 | 0 | 88 | 44 | 45 | 0 |
| MATCH-079-stepwise | 47 | 140 | 2 | 2 | 26 | 44 | 0 | 105 | 44 | 28 | 0 |

Complete nonterminal Core/unit states and hashes: [cap-details.json](cap-details.json). AP/stop distributions and frozen Wilson/paired outputs are in the main reports. No model judge, hidden reasoning or causal explanation is inferred from these counts.
