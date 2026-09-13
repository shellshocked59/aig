# Scenario V4: four-civilization total war

Scenario V4 is a fixed 16 by 12 map for Environment V5. It stresses target
selection, target persistence, multiple fronts, expansion versus conquest, and
barbarian pressure. It adds no gameplay rules. Environment V5, snapshot v12,
strategic-plan-schema-v1, benchmark-v1 and model profiles remain unchanged.
Prompt v1 stays the default; both frozen prompt v1 and v2 are compatible.

Coordinates are zero-based, with x increasing east and y increasing south.

| Civilization | Start | Normal turn order |
| --- | --- | --- |
| A | (2, 2), northwest | 1 |
| B | (13, 2), northeast | 2 |
| C | (2, 9), southwest | 3 |
| D | (13, 9), southeast | 4 |

The existing barbarian system phase follows D. Each normal civilization starts
with one Settler and one Warrior. The scenario uses manual controller setup;
the benchmark changes every normal controller to AI and assigns its externally
selected provider. No provider, target or turn cap is embedded in the artifact.
The browser demo remains the preserved two-player V3 setup.

The terrain is hand-authored in `SCENARIO_V4_ROWS` in `backend/aig/scenarios.py`.
Grassland/plains provide settlement space, forests/hills interrupt direct routes,
short northern/southern mountain ridges and a small southwest-central lake create
local detours. Multiple central and edge land routes remain open. The connectivity
test traverses all passable land with the engine's eight-neighbor movement geometry:
all starts and all passable tiles belong to one component. Minimum start separation
is seven Chebyshev tiles; initial vision sees no rival units or cities.

| Resource | Positions |
| --- | --- |
| Wheat | (2,2), (13,2), (2,9), (13,9) |
| Cattle | (3,1), (12,1), (3,10), (12,10) |
| Iron | (4,4), (11,4), (5,7), (9,7) |
| Gems | (7,3), (8,8) |
| Spices | (6,4), (9,4), (5,8), (10,8) |

Every start has local food resources; production/luxury resources invite travel
inward. No start sees all five types. Natural terrain asymmetry is intentional;
this layout is not a claim of equal win rates.

Camps 1-5 are at (4,4), (11,4), (4,7), (11,7), (8,5), respectively. Four distribute
pressure around the inner quadrants; one occupies the center. Existing Warrior
spawning, bounded units, controller, and +25 Gold clear reward are unchanged.

All six normal-civilization pairs are hostile; barbarians are hostile to every
civilization and excluded from conquest participation. Victory still requires
one surviving normal civilization, regardless of who eliminated the other three.

Generic compatibility fixes exclude publicly eliminated owners from heuristic
city candidates and reject dead references in plan validation. Historical fog
records and public fog semantics remain intact, including unknown ownership of
hidden captured cities. No tactical target-selection preference was added.
The UI now has stable A-D colors and a roster-generated map legend.

Canonical setup SHA-256 (`canonical_hash(asdict(scenario_setup('v4')))`):
`efa7b8c38d6174dee7679391395110940d8b6cfaf75aabfaca727727b1ece5f9`.
Regression tests independently pin V1-V3 setups and both prompt payloads.

Reproduce four deterministic offline trials (two pairs):

```powershell
.\.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b heuristic --games 2 --turns 150 --environment-version v5 --scenario-version v4 --prompt-version v1 --plan-schema-version v1 --output .local/scenario-v4-final-verification
```

See `scenario-v4-verification.md` for measured results and limitations. No live
Luna/OpenAI/Ollama inference is part of this implementation.
