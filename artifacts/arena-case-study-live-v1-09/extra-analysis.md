# Additional descriptive evidence through Batch 8 — INTERIM

These are arithmetic summaries of frozen result fields and saved validators. They add no model judge, hypothesis tests or changes to official categories. Paired differences compare independent Luna trajectories sharing a frozen slot/side.

## batch_6

| comparison | field | pairs | sum_difference | mean_difference | median_difference | positive | zero | negative | differences |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded minus strict | requests | 10 | 76 | 7.6 | 2.0 | 6 | 2 | 2 | [44, 7, 0, 0, 1, 24, -7, 3, 7, -3] |
| bounded minus strict | player_turns | 10 | 90 | 9 | 2.0 | 5 | 1 | 4 | [80, 5, 0, -3, -3, 25, -16, 4, 9, -11] |
| bounded minus strict | core_damage_dealt | 10 | 27 | 2.7 | 0.0 | 2 | 8 | 0 | [0, 0, 0, 0, 0, 18, 0, 9, 0, 0] |
| bounded minus strict | enemy_units_downed | 10 | 2 | 0.2 | 0.0 | 2 | 7 | 1 | [-2, 0, 0, 0, 0, 3, 0, 0, 1, 0] |
| bounded minus strict | finish | 10 | 3 | 0.3 | 0.0 | 3 | 7 | 0 | [1, 0, 0, 0, 0, 1, 0, 0, 1, 0] |
| stepwise minus bounded | requests | 10 | 279 | 27.9 | 9.0 | 9 | 0 | 1 | [91, 2, 25, 11, 7, -12, 6, 133, 5, 11] |
| stepwise minus bounded | player_turns | 10 | 99 | 9.9 | 3.0 | 6 | 1 | 3 | [3, 0, 15, 7, 3, -18, -1, 82, -1, 9] |
| stepwise minus bounded | core_damage_dealt | 10 | -27 | -2.7 | 0.0 | 0 | 8 | 2 | [0, 0, 0, 0, 0, -18, 0, -9, 0, 0] |
| stepwise minus bounded | enemy_units_downed | 10 | 48 | 4.8 | 0.0 | 4 | 4 | 2 | [43, -1, 4, 0, 0, -1, 0, 1, 0, 2] |
| stepwise minus bounded | finish | 10 | -1 | -0.1 | 0.0 | 2 | 5 | 3 | [-1, 0, 1, 0, 0, -1, 0, 1, -1, 0] |

Diagnostic grouping: `{"strict": {"AP": 1, "Range": 2, "Fireball range/board (not disambiguated)": 2}, "bounded": {"Fireball range/board (not disambiguated)": 1, "LOS": 3, "Range": 1}, "stepwise": {}, "all": {"AP": 1, "Fireball range/board (not disambiguated)": 3, "Range": 3, "LOS": 3}}`. Categories preserve diagnostic ambiguity: Fireball range/board and occupied/blocked/unchanged/out-of-range movement cannot be uniquely separated from those messages.

| batch | match_id | control | side | tag | official_category | validator_messages | response_received |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | MATCH-052-strict | strict | blue | AP | schema_validation | [null] | True |
| 6 | MATCH-053-bounded | bounded | red | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 6 | MATCH-053-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 6 | MATCH-054-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 6 | MATCH-055-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 6 | MATCH-056-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 6 | MATCH-058-bounded | bounded | blue | Range | invalid_reference | ["target outside action range"] | True |
| 6 | MATCH-058-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 6 | MATCH-059-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 6 | MATCH-060-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |

## batch_7

| comparison | field | pairs | sum_difference | mean_difference | median_difference | positive | zero | negative | differences |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded minus strict | requests | 10 | 7 | 0.7 | 2.5 | 7 | 0 | 3 | [2, -3, 8, 4, -3, 2, 3, 9, -23, 8] |
| bounded minus strict | player_turns | 10 | -40 | -4 | 0.0 | 5 | 0 | 5 | [-1, -9, 7, 4, -10, -4, 1, 13, -45, 4] |
| bounded minus strict | core_damage_dealt | 10 | 0 | 0 | 0.0 | 0 | 10 | 0 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] |
| bounded minus strict | enemy_units_downed | 10 | -3 | -0.3 | -0.5 | 4 | 1 | 5 | [0, -2, 1, 1, -2, -3, 2, 2, -1, -1] |
| bounded minus strict | finish | 10 | 0 | 0 | 0.0 | 0 | 10 | 0 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] |
| stepwise minus bounded | requests | 10 | 496 | 49.6 | 11.5 | 10 | 0 | 0 | [11, 11, 128, 5, 62, 12, 131, 2, 133, 1] |
| stepwise minus bounded | player_turns | 10 | 292 | 29.2 | 7.0 | 8 | 0 | 2 | [5, 9, 80, 3, 38, 3, 79, -6, 87, -6] |
| stepwise minus bounded | core_damage_dealt | 10 | 30 | 3 | 0.0 | 1 | 9 | 0 | [0, 0, 0, 0, 0, 30, 0, 0, 0, 0] |
| stepwise minus bounded | enemy_units_downed | 10 | 131 | 13.1 | 1.5 | 7 | 1 | 2 | [2, 0, 43, -1, 3, 1, 40, 1, 44, -2] |
| stepwise minus bounded | finish | 10 | 2 | 0.2 | 0.0 | 2 | 8 | 0 | [1, 0, 0, 0, 1, 0, 0, 0, 0, 0] |

Diagnostic grouping: `{"strict": {"LOS": 2}, "bounded": {"LOS": 3, "Range": 1}, "stepwise": {}, "all": {"LOS": 5, "Range": 1}}`. Categories preserve diagnostic ambiguity: Fireball range/board and occupied/blocked/unchanged/out-of-range movement cannot be uniquely separated from those messages.

| batch | match_id | control | side | tag | official_category | validator_messages | response_received |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | MATCH-061-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-062-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-064-bounded | bounded | blue | Range | invalid_reference | ["target outside action range"] | True |
| 7 | MATCH-064-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-065-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-068-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |

## batch_8

| comparison | field | pairs | sum_difference | mean_difference | median_difference | positive | zero | negative | differences |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded minus strict | requests | 10 | -4 | -0.4 | 3.5 | 7 | 1 | 2 | [5, 4, 1, 6, 3, -29, 0, -2, 4, 4] |
| bounded minus strict | player_turns | 10 | -34 | -3.4 | 0.0 | 4 | 3 | 3 | [3, 0, 0, 9, -2, -44, 0, -9, 3, 6] |
| bounded minus strict | core_damage_dealt | 10 | 10 | 1 | 0.0 | 1 | 9 | 0 | [0, 0, 0, 10, 0, 0, 0, 0, 0, 0] |
| bounded minus strict | enemy_units_downed | 10 | 2 | 0.2 | 0.0 | 3 | 6 | 1 | [1, 1, 0, 0, 0, 1, 0, 0, -1, 0] |
| bounded minus strict | finish | 10 | 0 | 0 | 0.0 | 0 | 10 | 0 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] |
| stepwise minus bounded | requests | 10 | 342 | 34.2 | 11.5 | 10 | 0 | 0 | [7, 1, 13, 5, 130, 14, 25, 10, 131, 6] |
| stepwise minus bounded | player_turns | 10 | 196 | 19.6 | 5.5 | 7 | 1 | 2 | [0, -2, 9, -2, 86, 4, 12, 7, 81, 1] |
| stepwise minus bounded | core_damage_dealt | 10 | -10 | -1 | 0.0 | 0 | 9 | 1 | [0, 0, 0, -10, 0, 0, 0, 0, 0, 0] |
| stepwise minus bounded | enemy_units_downed | 10 | 96 | 9.6 | 2.0 | 7 | 2 | 1 | [1, -2, 3, 0, 43, 2, 3, 2, 44, 0] |
| stepwise minus bounded | finish | 10 | 1 | 0.1 | 0.0 | 1 | 9 | 0 | [0, 0, 0, 0, 0, 0, 1, 0, 0, 0] |

Diagnostic grouping: `{"strict": {"Range": 1, "LOS": 1, "Fireball range/board (not disambiguated)": 1}, "bounded": {"Range": 1, "Fireball range/board (not disambiguated)": 1, "Ambiguous move validation": 1}, "stepwise": {}, "all": {"Range": 2, "LOS": 1, "Fireball range/board (not disambiguated)": 2, "Ambiguous move validation": 1}}`. Categories preserve diagnostic ambiguity: Fireball range/board and occupied/blocked/unchanged/out-of-range movement cannot be uniquely separated from those messages.

| batch | match_id | control | side | tag | official_category | validator_messages | response_received |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | MATCH-073-bounded | bounded | red | Range | invalid_reference | ["target outside action range"] | True |
| 8 | MATCH-073-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 8 | MATCH-074-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 8 | MATCH-078-bounded | bounded | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 8 | MATCH-080-bounded | bounded | blue | Ambiguous move validation | invalid_reference | ["destination is occupied, blocked, unchanged, or beyond move range"] | True |
| 8 | MATCH-080-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |

## cumulative

| comparison | field | pairs | sum_difference | mean_difference | median_difference | positive | zero | negative | differences |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded minus strict | requests | 80 | 140 | 1.75 | 2.0 | 52 | 7 | 21 | [8, -8, 1, 4, 6, -13, 5, 2, 1, 4, -12, 8, -1, -4, 3, 3, 7, 2, 1, 3, 1, -28, 1, -4, 9, -1, 1, -3, -4, 2, 9, 2, 11, 2, 11, -2, 0, 3, 0, -5, 3, -9, 0, 2, 9, 0, 6, -3, 16, 12, 44, 7, 0, 0, 1, 24, -7, 3, 7, -3, 2, -3, 8, 4, -3, 2, 3, 9, -23, 8, 5, 4, 1, 6, 3, -29, 0, -2, 4, 4] |
| bounded minus strict | player_turns | 80 | -74 | -0.925 | 0.0 | 36 | 12 | 32 | [7, -18, 1, -4, 5, -23, 2, 0, 2, 5, -28, 2, 1, -7, 0, 0, 4, 2, 5, 2, -2, -49, 0, -9, 4, -7, -1, -2, -7, 0, 6, 0, 8, 0, 8, -6, -3, 2, -2, -9, 3, -14, -1, -1, 9, 0, 8, -9, 22, 4, 80, 5, 0, -3, -3, 25, -16, 4, 9, -11, -1, -9, 7, 4, -10, -4, 1, 13, -45, 4, 3, 0, 0, 9, -2, -44, 0, -9, 3, 6] |
| bounded minus strict | core_damage_dealt | 80 | 42 | 0.525 | 0.0 | 4 | 76 | 0 | [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 18, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0] |
| bounded minus strict | enemy_units_downed | 80 | 23 | 0.2875 | 0.0 | 31 | 32 | 17 | [1, -1, 0, 0, 2, 1, 1, 1, 0, 1, -1, 3, 0, 0, 0, -1, 1, 0, 0, 0, 0, -2, 0, -1, 2, 0, -2, 1, -2, -1, 1, 1, 3, 1, 3, 0, 0, 1, 0, -1, 1, -2, 0, 2, 3, 0, 3, 0, 1, 2, -2, 0, 0, 0, 0, 3, 0, 0, 1, 0, 0, -2, 1, 1, -2, -3, 2, 2, -1, -1, 1, 1, 0, 0, 0, 1, 0, 0, -1, 0] |
| bounded minus strict | finish | 80 | 10 | 0.125 | 0.0 | 11 | 68 | 1 | [-1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] |
| stepwise minus bounded | requests | 80 | 2534 | 31.675 | 11.0 | 73 | 0 | 7 | [124, 9, 9, 3, 6, 2, 3, 12, 133, 7, 17, -3, 18, 11, 132, -7, 26, 10, 15, 16, 134, -4, 31, 11, 16, 6, 9, -1, 14, 6, 129, 10, 126, 3, 2, 5, 136, 3, 35, 11, 8, 12, 17, 7, 3, 11, 130, 11, -2, -5, 91, 2, 25, 11, 7, -12, 6, 133, 5, 11, 11, 11, 128, 5, 62, 12, 131, 2, 133, 1, 7, 1, 13, 5, 130, 14, 25, 10, 131, 6] |
| stepwise minus bounded | player_turns | 80 | 1349 | 16.8625 | 4.5 | 55 | 5 | 20 | [76, 7, 1, -1, -1, 0, -1, 2, 83, 0, 5, -4, 5, 5, 82, -9, 7, 5, 4, 8, 89, -7, 16, 7, 6, 3, 1, -2, 9, 0, 86, 9, 81, -2, -4, 2, 90, -2, 17, 5, 1, 9, 4, 1, -5, 7, 81, 7, -18, -3, 3, 0, 15, 7, 3, -18, -1, 82, -1, 9, 5, 9, 80, 3, 38, 3, 79, -6, 87, -6, 0, -2, 9, -2, 86, 4, 12, 7, 81, 1] |
| stepwise minus bounded | core_damage_dealt | 80 | 18 | 0.225 | 0.0 | 2 | 74 | 4 | [0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -18, 0, -9, 0, 0, 0, 0, 0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 0, -10, 0, 0, 0, 0, 0, 0] |
| stepwise minus bounded | enemy_units_downed | 80 | 626 | 7.825 | 1.0 | 43 | 19 | 18 | [42, 0, 2, 0, 0, -1, 0, 1, 42, -1, 1, -3, 2, 0, 42, -1, 4, 0, 3, 1, 44, 0, 3, 1, 2, -1, 2, -1, 3, 2, 43, 0, 39, -2, -1, -1, 44, -3, 0, 0, 2, 1, 3, -2, -1, 0, 41, 0, 2, -3, 43, -1, 4, 0, 0, -1, 0, 1, 0, 2, 2, 0, 43, -1, 3, 1, 40, 1, 44, -2, 1, -2, 3, 0, 43, 2, 3, 2, 44, 0] |
| stepwise minus bounded | finish | 80 | 9 | 0.1125 | 0.0 | 14 | 59 | 7 | [0, 0, 0, 0, 1, -1, -1, 0, 0, 0, 2, -1, 1, 0, 0, 0, 2, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 1, 0, 0, -1, 0, 1, -1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0] |

Diagnostic grouping: `{"strict": {"Range": 6, "Fireball range/board (not disambiguated)": 7, "LOS": 6, "AP": 1}, "bounded": {"LOS": 13, "AP": 4, "Ambiguous move validation": 2, "Fireball range/board (not disambiguated)": 5, "Range": 5}, "stepwise": {"Range": 3, "LOS": 1}, "all": {"LOS": 20, "Range": 14, "AP": 5, "Ambiguous move validation": 2, "Fireball range/board (not disambiguated)": 12}}`. Categories preserve diagnostic ambiguity: Fireball range/board and occupied/blocked/unchanged/out-of-range movement cannot be uniquely separated from those messages.

| batch | match_id | control | side | tag | official_category | validator_messages | response_received |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MATCH-002-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 1 | MATCH-010-strict | strict | blue | Range | invalid_reference | ["target outside action range"] | True |
| 2 | MATCH-014-bounded | bounded | blue | AP | schema_validation | [null] | True |
| 2 | MATCH-016-stepwise | stepwise | blue | Range | invalid_reference | ["target outside action range"] | True |
| 2 | MATCH-018-bounded | bounded | blue | Ambiguous move validation | invalid_reference | ["destination is occupied, blocked, unchanged, or beyond move range"] | True |
| 2 | MATCH-018-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 2 | MATCH-019-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 2 | MATCH-020-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 2 | MATCH-020-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 3 | MATCH-022-stepwise | stepwise | blue | Range | invalid_reference | ["target outside action range"] | True |
| 3 | MATCH-022-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 3 | MATCH-024-bounded | bounded | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 3 | MATCH-026-bounded | bounded | blue | Range | invalid_reference | ["target outside action range"] | True |
| 3 | MATCH-028-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 3 | MATCH-028-stepwise | stepwise | blue | Range | invalid_reference | ["target outside action range"] | True |
| 3 | MATCH-028-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 3 | MATCH-029-bounded | bounded | red | AP | schema_validation | [null] | True |
| 4 | MATCH-031-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 4 | MATCH-032-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 4 | MATCH-032-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 4 | MATCH-037-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 4 | MATCH-040-bounded | bounded | blue | AP | schema_validation | [null] | True |
| 5 | MATCH-042-bounded | bounded | blue | AP | schema_validation | [null] | True |
| 5 | MATCH-042-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 5 | MATCH-043-stepwise | stepwise | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 5 | MATCH-044-bounded | bounded | blue | Range | invalid_reference | ["target outside action range"] | True |
| 5 | MATCH-045-bounded | bounded | red | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 5 | MATCH-046-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 5 | MATCH-046-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 5 | MATCH-048-bounded | bounded | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 5 | MATCH-050-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 6 | MATCH-052-strict | strict | blue | AP | schema_validation | [null] | True |
| 6 | MATCH-053-bounded | bounded | red | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 6 | MATCH-053-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 6 | MATCH-054-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 6 | MATCH-055-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 6 | MATCH-056-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 6 | MATCH-058-bounded | bounded | blue | Range | invalid_reference | ["target outside action range"] | True |
| 6 | MATCH-058-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 6 | MATCH-059-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 6 | MATCH-060-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-061-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-062-bounded | bounded | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-064-bounded | bounded | blue | Range | invalid_reference | ["target outside action range"] | True |
| 7 | MATCH-064-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-065-bounded | bounded | red | LOS | invalid_reference | ["blocked line of sight"] | True |
| 7 | MATCH-068-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 8 | MATCH-073-bounded | bounded | red | Range | invalid_reference | ["target outside action range"] | True |
| 8 | MATCH-073-strict | strict | red | Range | invalid_reference | ["target outside action range"] | True |
| 8 | MATCH-074-strict | strict | blue | LOS | invalid_reference | ["blocked line of sight"] | True |
| 8 | MATCH-078-bounded | bounded | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |
| 8 | MATCH-080-bounded | bounded | blue | Ambiguous move validation | invalid_reference | ["destination is occupied, blocked, unchanged, or beyond move range"] | True |
| 8 | MATCH-080-strict | strict | blue | Fireball range/board (not disambiguated) | invalid_reference | ["impact outside Fireball range/board"] | True |

All statistical inference remains governed by the frozen analysis plan. These supplementary differences are descriptive and do not attribute AP recovery or tactical quality causally to a control.
