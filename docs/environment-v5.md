# Environment V5: total war and conquest

Environment V5 adds city capture, historical zero-city elimination and conquest
victory to V4. Every other civilization and the barbarian faction is an enemy
from the start. `are_hostile` derives this from identity and faction kind; there
is no diplomacy state, declaration, peace, alliance or grievance system.

## Capture and economy

`MoveUnit` captures an undefended enemy city on legal entry. Warriors, Scouts and
Spearmen qualify through positive melee strength and absence of ranged strength.
Archers, Settlers and barbarians cannot capture. Any hostile unit on the city
tile blocks entry, including additional stacked defenders. Killing the last
defender does not capture or advance into the city: a subsequent legal move is
required. Cities have no HP, attack, walls or separate attack command.

Movement validates state, terrain, occupancy, the entire path and movement budget
before committing. Hostile cities can be movement destinations, but cannot be
intermediate tiles in a multi-step move; entry must resolve its capture before
another command continues. Normal friendly-city traversal and stacking remain.

Capture preserves city ID, name, position, terrain and resource. Only the center
tile changes owner. Population becomes `max(1, population - 1)`. Stored food and
production reset to zero, and production target becomes null. There is no
occupation, loyalty, razing or capital mechanic. Surrounding ownership is retained.

Unless capture ends the game, the new owner may set production immediately. The
captured city participates in that owner's current EndActivation economy, with
normal city-center resource yields. The former owner receives no further yields
from it. Terminal capture runs no economy or production.

## Elimination and terminal result

`PlayerState.has_ever_owned_city` starts false. Successful founding, setup city
addition and capture set it true. A historical city owner losing its last city
is eliminated immediately, including when the domain's `remove_city` removes it.
Remaining Settlers and military units are removed; the player record and
historical knowledge remain. An inactive opponent's elimination does not advance
the current activation while at least two civilizations survive. Active-player
elimination preserves the existing successor/wrap behavior.

Elimination during a started game leaves `GameResult(winner_player_id,
VictoryType.CONQUEST)` when exactly one civilization remains. Barbarians do not
count and their camps/units remain. Pre-game setup does not declare victory.
`active_player_id` becomes null and gameplay commands, AI activations and system
phases stop. Existing command authorization also blocks economy and research
after victory. State remains inspectable; the public game DTO exposes `terminal`,
`winnerPlayerId`, and `victoryType`. Browser controls stop accepting gameplay
orders and show the winner with “Conquest”.

Snapshot **v12** persists the historical flag and nullable result. Loading is
strict and side-effect free; it does not infer a winner, eliminate players,
refresh movement or run phases. Older snapshots are explicitly rejected. Use
their recorded source revision for historical replay. State validation rejects
false history for a city owner, started live historical owners without cities,
invalid winners/types, multiple survivors with a result, and active terminal games.

## Knowledge and shared execution

Captures update factions that witness entry or see its resulting position.
Witnesses retain the ownership observation even if losing a city removes their
vision source. Hidden third parties retain last-seen ownership until sight
returns. Capturing a remembered city removes it from the captor's enemy memory.
Eliminated factions retain their historical knowledge. Observer state sees truth.
Public scoreboard identities and military strength remain global; they do not
reveal hidden city positions or ownership by city ID.

Planning BFS uses filtered explored terrain, remembered cities and visible enemy
units. Undiscovered cities cannot influence routes. Shared ATTACK execution can
route eligible units into its known city target, including Scouts. Visible
defenders are attacked through existing tactical combat. The executor stops
immediately after terminal capture, with no EndActivation command. The heuristic
planner itself has no new aggression, target-selection or production policy.

## Artifact decisions

| Domain | Current version | Decision |
| --- | --- | --- |
| Environment | environment-v5 | New rules; V1–V4 descriptions preserved |
| Scenario | scenario-v3 | World data unchanged; no redundant V4 alias |
| Prompt | strategy-prompt-v1 | Audited: no invulnerable-city/no-victory claims; unchanged |
| Plan schema | strategic-plan-schema-v1 | ATTACK and target city already suffice |
| Model profiles | luna-config-v1, qwen-config-v1 | Unchanged |
| Benchmark | benchmark-v1 | Additive descriptive metrics; existing report fields retained |
| Snapshot | 12 | Required historical flag and nullable conquest result |

Scenario v3 naturally permits contact and conquest. Terrain, resources, starts
and camps are unchanged. V5 adds factual terminal status, remaining civilization
count, own city count and hostility identities to StrategicState; it does not
add planner conclusions or behavioral coaching. Prompt v1 has **no textual
changes**, and no prompt v2 or plan-schema revision is needed.

The primary future controlled comparison is **Heuristic vs OpenAI/Luna**.
Qwen/Ollama support and all historical measurements remain available.
`qwen-config-v1` was validated through V4 and approached 91.89% of its frozen
4096-token context. Optional manual Qwen V5 runs do not gate V5 acceptance.
Implementation verification makes no live model requests.

## Benchmark observations

Reports add winner, victory type/turn/activation, duration and `turnCapReached`.
No score-based winner is assigned at the cap. Commands record capture and
elimination events, including former/new owner, capture unit type, population
loss, actual food/production reset, canceled target and recapture status.
Per-faction metrics include first capture turn, captures/losses, unit-type mix,
elimination attribution and removed units/Settlers. Existing military, resource,
exploration, provider-purity and barbarian metrics remain.

`attacks_near_city` counts earlier attacks by the captor against the former
owner's units within one tile of the captured city during that trial. This is
spatial observation, not a causal conquest-efficiency score. All captures are
undefended at entry by rule, even when earlier attacks removed defenders.
