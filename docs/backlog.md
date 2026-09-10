# Initial development backlog

These eight tasks are future work and were created as [GitHub issues #1–#8](https://github.com/shellshocked59/aig/issues). The titles and bodies below preserve the initial issue-ready backlog; use the GitHub issues for ongoing discussion and status.

## 1. Add New Game setup screen

GitHub: [#1](https://github.com/shellshocked59/aig/issues/1)

Create a small setup screen reached from the main menu with map seed, map size, and number of factions. Choose and document temporary defaults and input bounds.

Acceptance criteria:

- [ ] New Game opens the setup screen and a Back control returns to the menu.
- [ ] The three inputs have labels and validate empty/invalid values.
- [ ] A valid submission displays the selected configuration with a clear message that generation is not implemented.
- [ ] The built screen works over `file://` without network requests.

Out of scope: game generation, maps, persistence, and backend integration.

## 2. Define shared game-state data model

GitHub: [#2](https://github.com/shellshocked59/aig/issues/2)

Document a minimal proposed data model for game, player, tile, city, and unit. Keep this focused on the entities and relationships, ready for frontend/backend serialization.

Acceptance criteria:

- [ ] List each entity's fields, types, identifiers, and relationships.
- [ ] Include one small JSON example covering all five entities.
- [ ] Explain ownership and references without relying on language-specific objects.
- [ ] Record unresolved questions explicitly.

Out of scope: gameplay rules, implementation classes, transport, and full serialization validation. Issue 6 covers the interchange contract.

## 3. Implement deterministic seeded RNG in Python

GitHub: [#3](https://github.com/shellshocked59/aig/issues/3)

Add a small random-number abstraction in `backend/aig/` suitable for future procedural generation. Avoid module-global random state.

Acceptance criteria:

- [ ] Define supported seed values and a minimal integer/selection API.
- [ ] Document the algorithm and the scope of reproducibility guarantees.
- [ ] Test repeatable sequences for a fixed seed, independent instances, and input bounds using lightweight tests.

Out of scope: terrain generation, AI randomness, and a browser RNG implementation.

## 4. Implement basic square-grid map model

GitHub: [#4](https://github.com/shellshocked59/aig/issues/4)

Create a small logical rectangular tile grid in Python with an explicit coordinate convention.

Acceptance criteria:

- [ ] Construct a grid from positive width and height and access tiles by coordinate.
- [ ] Define cardinal-neighbor lookup without wrapping.
- [ ] Test dimensions, invalid coordinates, corners, and edges.
- [ ] Keep tile contents minimal; align with the shared model if it is available.

Out of scope: rendering, terrain generation, pathfinding, movement rules, and cities.

## 5. Render a static tile grid in the browser

GitHub: [#5](https://github.com/shellshocked59/aig/issues/5)

Add a small standalone grid preview using fixed local data and temporary colors or placeholder assets. Keep it separate from starting a real game.

Acceptance criteria:

- [ ] Display a fixed square-tile grid with visibly distinct placeholder tile types.
- [ ] Include a way to reach the preview and return to the menu.
- [ ] Keep the preview usable at narrow browser widths.
- [ ] Verify the build loads directly from disk without fetching JSON or remote assets.

Out of scope: procedural generation, gameplay, backend integration, camera systems, and final art.

## 6. Define frontend/backend game-state interchange format

GitHub: [#6](https://github.com/shellshocked59/aig/issues/6)

Document a proposed serialization contract using the entity model from issue 2 as input. If that issue is unfinished, use a clearly marked minimal fixture and record assumptions instead of expanding the model here.

Acceptance criteria:

- [ ] Define a versioned JSON envelope for a state snapshot and a proposed player command.
- [ ] Include example payloads and specify field naming, identifier encoding, and coordinate representation.
- [ ] Describe validation ownership and handling of malformed data or unsupported versions.
- [ ] Describe a possible file-based experimental exchange without choosing or implementing a server.

Out of scope: transport implementation, gameplay rules, networking, and duplicating the entity-design document.

## 7. Define initial war-machine chassis model

GitHub: [#7](https://github.com/shellshocked59/aig/issues/7)

Write a short design note describing the intended MVP chassis roles: Scout, Line, Brawler, and Missile/LRM.

Acceptance criteria:

- [ ] Explain each chassis's intended role and tradeoffs.
- [ ] Describe future tonnage limits and interchangeable equipment conceptually.
- [ ] Mark balancing values and unresolved equipment questions as provisional.

Out of scope: implementation, mech designer UI, final stats, equipment catalog, and combat.

## 8. Define StrategyProvider architecture

GitHub: [#8](https://github.com/shellshocked59/aig/issues/8)

Document the future separation between strategic objectives and deterministic legal action execution.

Acceptance criteria:

- [ ] Sketch provider input/output with one small illustrative objective.
- [ ] Explain how deterministic code validates proposals and handles invalid or unavailable provider output.
- [ ] Describe heuristic and local-LLM providers as possible future implementations.
- [ ] Explain where reproducibility and logging will matter without implementing them.

Out of scope: provider code, model installation, Ollama integration, prompts, and AI gameplay.
