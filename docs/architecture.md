# Architecture

The manually playable browser slice implements this runtime boundary:

```text
Browser UI (plain JavaScript / HTML / CSS / esbuild)
    -> HTTP/JSON via same-origin /api development proxy
Python application API (FastAPI / Uvicorn)
    -> application GameSession
Engine commands / public query model
    -> deterministic GameState
```

The browser never mutates engine state directly and never performs pathfinding,
combat, economy, production-unlock, or research-prerequisite rules. It never
contacts Ollama or any other external service. Each action waits for a returned
authoritative state before rendering. AI, heuristic controllers, and LLM strategy
remain future work. No HTTP imports were added to engine modules.

## Single-game application and HTTP contract

`aig.api:create_app` loads centralized settings once and creates one
`application.GameSession`. The session holds a nullable `GameState` and an
application city counter. There is intentionally one in-memory game per running
process: no database, authentication, cookies, accounts, persistence, background
runner, or network multiplayer. Use one Uvicorn worker. Restarting the process
loses the game. Browser tabs share it, with explicit refresh and no push updates.

An `RLock` serializes reads, reset, start, command application, city allocation,
and DTO construction. Responses contain detached collections assembled while the
lock is held. Game rules and atomic rejection remain responsibilities of existing
`create_game`, `start_game`, and `apply_command`; the service only orchestrates.

| Route | Behavior |
| --- | --- |
| `GET /api/game` | Current public state; 404 `no_game` before creation |
| `POST /api/game/demo` | Replace the game using `create_game(demo_game_setup())`; return pre-game state |
| `POST /api/game/start` | Call the real `start_game`; return started state; repeated start is 409 |
| `POST /api/game/commands` | Validate a discriminated JSON payload, construct an immutable command, apply it, and return state |

Command payloads use the following explicit contract. No payload accepts an actor
ID. The service reads `active_player_id` inside the same lock as command execution;
the command layer still checks the actor and entity ownership. Extra fields,
unknown commands, invalid enums, missing fields, and non-integer coordinates
(including booleans) are rejected. `EliminatePlayer` is not exposed.

| `type` | Other JSON fields | Engine command |
| --- | --- | --- |
| `move_unit` | `unitId`, integer `x`, integer `y` | `MoveUnit(actor, unitId, Position(x, y))` |
| `attack_unit` | `attackerUnitId`, `targetUnitId` | `AttackUnit` |
| `found_city` | `settlerUnitId`, `name` | `FoundCity`, with server-allocated city ID |
| `set_city_production` | `cityId`, `unitType` (unit value or null) | `SetCityProduction` |
| `set_research` | `technology` (technology value or null) | `SetResearch` |
| `end_activation` | none | `EndActivation` |

Malformed requests return 422 `invalid_request`; rejected gameplay returns 422
`invalid_command`; lifecycle failures return 409 `invalid_state`. Errors have
`{"error": "code", "message": "Useful explanation"}`. Unexpected exceptions are
logged and return a generic 500 without traceback details. Failed commands rely
on the existing engine's validation-before-mutation semantics. The application
does not simulate rollback or run a second copy of the rules.

City allocation tries `city-1`, `city-2`, etc., skips existing live city IDs, and
advances the application counter only after successful founding. Reset replaces
the state and counter together. It uses neither timestamps nor UUIDs and never
changes the engine's unit allocator or snapshot v8. This is sufficient because
the application supports no persistence/import/replay. Any later session loading
or replay feature must explicitly preserve the counter or recorded allocated IDs;
it cannot treat this ephemeral counter as persisted engine state.

## Public read model

`public_state.py` explicitly assembles a game-oriented DTO distinct from persistence
snapshots. It exposes no seed, snapshot schema version, unit allocation counter,
settings, or private implementation objects. IDs are strings, coordinates and
counters are integers, optional targets/owners use JSON null, and enum values use
lowercase strings (`bronze_working` for that technology). Arrays are deterministically
ordered: players/units/cities by ID, tiles by y then x, choices in engine enum order.

| Object | Fields |
| --- | --- |
| `game` | `turn`, `activePlayerId`, `status` (`pre_game` or `started` for this demo) |
| `players[]` | `id`, `controller`, `eliminated`, `gold`, `scienceStored`, `researchTarget`, `researchedTechnologies`, `availableResearch: [{technology, cost}]`, `researchCost`, `researchRemaining` |
| `map` | `width`, `height`, `origin: {x, y}`, `tiles: [{x, y, terrain, ownerId}]` |
| `units[]` | `id`, `ownerId`, `type`, `x`, `y`, `hp`, `movesRemaining`, `maxMovement`, `attackRange` |
| `cities[]` | `id`, `ownerId`, `name`, `x`, `y`, `population`, `foodStored`, `productionStored`, `productionTarget`, `availableProduction: [{unitType, cost}]`, `productionCost`, `productionRemaining` |

Costs, remaining amounts, available technologies, unit unlocks, movement allowances,
and attack ranges come from engine queries or enum properties. The client does not
contain duplicate stat tables. Terminal/conquest UI semantics remain outside this
demo: no HTTP command eliminates a faction and unit deaths do not eliminate it.

## Browser implementation

The established JavaScript/HTML/CSS/esbuild stack is preserved. `js/api/game.js`
centralizes relative `fetch('/api/game…')` requests and structured error handling.
`js/game.js` mounts a DOM view with event delegation, keeping only returned public
state, local selections, pending/error/notice state, and the city-name draft.
`js/presentation.js` maps enum strings to sprites and faction IDs A/B to stable
amber/blue identities. The project does not use TypeScript or a component framework.

The map is a small CSS grid with semantic terrain and piece buttons (siblings,
never nested buttons). Selected owned units submit destination moves. Enemy clicks
retain the attacker and expose explicit target buttons, including full enemy
stacks; Python decides range and legality. A stack count and tile roster make all
friendly units selectable. Cities show an original sprite, name, population, and
owner, with a compact production panel. Research and End Turn act on the active
faction. Pre-game inspection is allowed but gameplay controls are inactive.
All mutation controls disable while waiting; there is no optimistic simulation.

`frontend/src/assets/sprites.png` is the only raster asset: a 256×192 RGBA atlas
with twelve 64×64 cells (six terrains, five units, one city). It was generated as
original pixel art using the built-in image tool, then reduced with nearest-neighbor
sampling. The [asset notes](../frontend/src/assets/README.md) record its layout and
prompt. CSS uses atlas positions and pixelated scaling; esbuild copies the PNG
under a content-hashed filename. No runtime assets or fonts come from the internet.

`npm run dev` uses esbuild's static server behind a small Node HTTP proxy on
127.0.0.1:5173: `/api` goes to Python on 127.0.0.1:8000; other paths go to esbuild.
This is development-only hosting. `npm run build` and `npm run watch` retain their
existing build roles. Sources watch automatically; browser refresh is manual.

Python unittest API tests use FastAPI's in-process TestClient and HTTPX, including
real command effects, deterministic/reset behavior, invalid-state atomicity,
concurrent session access, fault injection, and blocked outbound service calls.
Frontend tests use the Node test runner with jsdom for rendering, selections,
payloads, controls, errors, and pending-state behavior. CI retains the original
install/build/unittest sequence and adds the test extra plus `npm test`.

## Application settings

`backend/aig/settings.py` owns frozen `Settings` and `OllamaSettings` dataclasses,
committed development defaults, and the explicit `load_settings()` boundary.
For each `AIG_OLLAMA_*` value, a non-empty process environment override takes
priority over the optional root `.env`, which takes priority over the Python
default. `.env` is ignored; `.env.example` documents all supported names. See the
[settings guide](../README.md#application-settings) for defaults, parsing, and use.

This adapts `email-qa`'s central Python defaults and small local environment-file
loader. That project loads `env/env` into `os.environ` without replacing non-empty
process values; its restart script fills missing values from `env/env.example`
and merges `env/.env`. AIG needs only one optional local file, with no restart
script or generated settings copy. The standard-library loader resolves into a
typed object without mutating the environment or reading configuration at import.
Unlike the reference's individual environment getters, empty process strings
consistently fall through, and invalid boolean spellings fail explicitly.

The API factory calls `load_settings()` once per application instance. It creates
no provider and makes no Ollama calls. A future provider would receive `settings.ollama`.
The deterministic engine does not read application settings; `GameConfig` remains
per-game state and application settings are not serialized in snapshots. This
layer adds no network calls, provider implementation, gameplay options, or runtime
dependencies. `tests/test_settings.py` uses temporary files and isolated
environment mappings to verify defaults, precedence, parsing, and immutability.

## Authoritative state and snapshots

`backend/aig/state.py` defines standard-library dataclasses without framework dependencies. `GameConfig` holds an integer seed and a `debug_mode` boolean (default `False`); it is immutable configuration for one game, not a catalog of static game definitions. `GameState` and its player, tile, city, and unit records are mutable. `Terrain`, `UnitType` and `Technology` define the current static land-unit rules.

Players, cities, and directly constructed units use caller-supplied, non-empty string IDs, unique within each collection. Dictionary keys must match entity IDs. References use IDs rather than entity objects; IDs should remain stable for an entity's lifetime. City and unit owners must reference existing players; live city and unit owners must not be eliminated. Tiles use immutable integer `Position(x, y)` keys, and city/unit positions must reference existing tiles.

`GameState.game_map` is an immutable `GameMap(width, height, origin=Position(0, 0))` defining finite square-grid bounds without wrapping. Coordinates increase eastward and southward. An explicit origin accommodates the earlier contract's negative coordinates. The default `GameMap(0, 0)` supports empty roster-only states; otherwise both dimensions must be positive integers. `GameState.tiles` remains the single authoritative tile dictionary. Tiles must be inside bounds; missing tiles inside the rectangle are unavailable for placement or travel. There is no map generation. `TileState(position, terrain=Terrain.GRASSLAND, owner_id=None)` stores terrain and optional ownership. A non-null owner must reference a known player, including an eliminated historical player. Tile ownership alone does not restrict unit movement.

`GameState.add_unit(owner_id, unit_type, position)` is a setup/rules API returning a live `UnitState`. It checks bounds, terrain, live ownership and hostile occupancy before assigning `unit-N` from the persisted `next_unit_id` counter. It skips caller-supplied IDs already in use and advances the counter only on success; generated IDs are not reused after removal. `UnitState(id, owner_id, position, unit_type=UnitType.WARRIOR, *, moves_remaining=..., hp=100)` retains the earlier positional API. Omitted movement starts at the type's allowance; new units start at 100 HP. Explicit movement and HP are strictly validated. Setup placement is not a player command. Production shares its internal allocator but explicitly starts units with zero movement.

Controllers are `human` or `ai`. AI-only and mixed human/AI games use the same state contract; no human player is required.

`backend/aig/snapshots.py` defines `Snapshot`, a JSON-compatible dictionary contract, plus explicit `to_snapshot(state)` and `from_snapshot(data)` conversions. Version 8 contains `schema_version`, `config` (including `seed` and `debug_mode`), `turn`, `turn_order`, `active_player_id`, `game_map` (width, height, origin), `next_unit_id`, and arrays of `players`, `tiles`, `cities`, and `units`. Each player contains `id`, `controller`, the required boolean `eliminated`, non-negative integer `gold` and `science_stored`, nullable `research_target`, and a `researched_technologies` array of technology strings sorted by value. Each tile contains `position`, `terrain` and required nullable `owner_id`; each city contains `id`, `owner_id`, `position`, `name`, `population`, `food_stored`, `production_stored` and nullable `production_target` (a unit type string or null); each unit contains `id`, `owner_id`, `position`, `unit_type`, `moves_remaining` and `hp`. Derived combat stats, range, maximum HP, unit production costs and production remaining are not serialized. Coordinates are `{ "x": integer, "y": integer }` objects. Consumers resolve the active controller through `active_player_id` and the player's `controller`; it is not duplicated in the snapshot. Python exposes the same lookup as a read-only `GameState.active_controller` property. Entity arrays are canonicalized by ID, and tiles by `(y, x)`; array order carries no gameplay meaning. `turn_order` explicitly determines faction activation order and is preserved exactly. No separate rules version is declared.

Conversion creates detached data and revalidates mutable state. Loading rejects unsupported schema versions, missing/unknown fields, invalid types, duplicate IDs/coordinates, dangling references, illegal terrain/occupancy, invalid movement and invalid HP with `ValueError`. It performs no coercion, clamping or migration. Versions 1 through 7 are rejected explicitly before checking the v8 shape. The loader never supplies missing state, resolves economy, collects gold/production/science, completes research, starts the game, consumes food, grows cities, completes production, heals units, refreshes movement, or restarts an activation. Food, production, gold and science must be non-negative integers, rejecting booleans and floats. City spacing is validated on load; invalid saves are never repaired. Direct mutations can temporarily invalidate state; callers can use `state.validate()`, and snapshot export always validates it.

The movement slice started from a checkout with schema v2 and 64 tests, which lacked the previously planned map/terrain and live-unit placement slices. Version 3 therefore adds those minimal prerequisites together with movement. Existing `TileState`, `UnitState`, city records and activation APIs remain; the earlier elimination test that retained units now requires live-unit cleanup.

The combat slice started from schema v3 and 121 passing tests (57 movement/pathfinding tests). Version 4 adds required current HP to unit records. Mid-activation saves preserve damage and spent movement exactly; snapshot copies and deep copies have independent mutable unit state.

The city slice started from schema v4 and 180 passing tests. The existing city records lacked names, populations and gameplay constraints, and tiles lacked ownership. Version 5 adds required city name/population and nullable tile ownership, with strict live-city validation. There is still no replay log or separate gameplay-rules version.

The economy slice started from schema v5 and 252 passing tests, matching the preceding audit. Version 6 adds required player gold and city food/production stores and intentionally enforces minimum city spacing. Terrain yields, worked assignments, center/total yields and growth costs are derived, never serialized. Detached snapshot copies and deep copies preserve independent player gold, city stores and population. There is still no replay log or separate gameplay-rules version.

The production slice started from schema v6 and 300 passing tests. Version 7 adds required nullable city `production_target`, preserving the existing generic production store and `next_unit_id`. Unknown targets and missing fields are rejected without repair. Mid-build and already-affordable targets restore exactly without spawning units or allocating IDs. Costs and remaining production are derived static/query values.

Save and client consumers initially share this snapshot contract. Conversion lives outside the domain models so separate save, client, or observer contracts can be added later. `SnapshotEnvelope` permits optional JSON-compatible `observer_data` beside a snapshot; only the nested snapshot is restored into game state. It supplies no diagnostics, filtering, or debug behavior. UI state and AI/debug observations are not authoritative entity fields.

## Sequential faction activations

`players` is the historical roster: each player represents one faction and remains present after elimination. `PlayerState.eliminated` defaults to `False` and must be a boolean. `turn_order` is the live activation roster, containing every non-eliminated player exactly once, with no eliminated players, unknown IDs, or duplicates. The order is supplied explicitly, never inferred from dictionary insertion order or sorted during conversion. An active player must exist, be live, and appear in that order.

`turn` is the global game turn, initially zero. `GameState.finish_activation()` is the low-level transition that selects the next faction in the current live order. It does not resolve economy; normal play uses `EndActivation` to collect the outgoing faction's economy first. If the active faction is last, it increments `turn` once and activates the first faction. It derives the position using `turn_order.index(active_player_id)` on each call; no separate active index is stored. Factions activate strictly sequentially, and callers must fully resolve actions before advancing. Simultaneous action resolution is out of scope.

For example, `{ "turn": 12, "turn_order": ["player-1", "player-2", "player-3"], "active_player_id": "player-2" }` describes player-2's activation within global turn 12. Player-3 follows on the same global turn; after player-3 finishes, player-1 activates on global turn 13. There is no separate round counter, completed-player list, or action queue.

`GameState.eliminate_player(player_id)` marks the player eliminated and removes its entry from `turn_order`, preserving the order of survivors. The player record and historical tile ownership remain intact; all of the player's live units and cities are removed. Unknown or malformed IDs raise `ValueError`; repeating elimination of an already eliminated player is a no-op. Both state operations validate before mutation and reject invalid input state without repairing it.

Eliminating another faction leaves the active player and global turn unchanged while at least two survive. For `[A, B, C, D]` with B active, eliminating C leaves `[A, B, D]`, so finishing B activates D. Eliminating both C and D leaves `[A, B]`, so finishing B wraps to A and increments `turn`. Removing A leaves `[B, C, D]`, so finishing B still activates C despite the shifted list positions.

Eliminating the active faction aborts its activation immediately, without resolving economy or changing its retained gold, science or research. With at least two survivors, its successor occupies the removed slot; if the removed slot was last, `turn` increments once and the first survivor activates. Eliminating the active faction therefore does not require a subsequent `finish_activation()` call for that faction.

With zero or one surviving faction, there is no next activation: `active_player_id` and `active_controller` are `None`. Elimination that reaches this terminal condition leaves `turn` unchanged, even when eliminating the active final faction. The remaining survivor stays in `turn_order` and may itself be eliminated, leaving an empty live roster and the historical players intact. Validation forbids an active player with fewer than two survivors. Calling `finish_activation()` without an active player raises `ValueError` without changing state, preventing repeated self-activation. This rule applies to one-player construction as well; no winner is recorded.

Pre-game construction still permits `turn == 0` and `active_player_id is None` with any valid roster, including an empty one. Eliminating players before play does not start an activation. With two or more survivors, a positive global turn requires an active player; terminal states permit no active player at any nonnegative turn. There is no separate phase field; `start_game()` validates these pre-game semantics and requires at least two live factions.

Whenever `start_game()`, `finish_activation()` or active-player elimination selects a faction, the shared internal `_begin_activation(player_id)` restores all that faction's live units to their type's movement allowance. This includes wrapping to a new global turn. Other factions' units are not refreshed. Repeated elimination, inactive-player elimination, pre-game elimination and terminal elimination do not create a new activation or refill budgets. Self-elimination selects and refreshes its successor exactly once.

Snapshots preserve elimination flags, `turn`, the exact live `turn_order`, `active_player_id`, and spent movement, so loading halfway through an activation restores it without advancing, restarting or refilling. Construction validates supplied movement without refreshing it; `create_game()` leaves the active player unset and newly placed units begin with full budgets. `start_game()` explicitly begins play. Export and import detach mutable data. There is no general turn executor, autoplay, or observer UI in this slice.

## Controller command boundary

Controllers submit commands. Rules/state code performs mutations.

```text
StrategyProvider / Human UI
            |
         Command
            |
    apply_command()
            |
     GameState rules
```

`backend/aig/commands.py` provides frozen dataclasses `EndActivation(actor_id)`, `EliminatePlayer(actor_id, target_player_id)`, `MoveUnit(actor_id, unit_id, destination: Position)`, `AttackUnit(actor_id, attacker_unit_id, target_unit_id)`, `FoundCity(actor_id, settler_unit_id, city_id, city_name)`, `SetCityProduction(actor_id, city_id, unit_type: UnitType | None)` and `SetResearch(actor_id, technology: Technology | None)`, their `Command` union, and `apply_command(state, command)`. IDs must be non-empty strings. Future human UI, heuristic AI, and Ollama-backed controllers should produce these requests instead of directly assigning authoritative state. State fields remain mutable and rules APIs remain usable internally for setup and execution.

Execution validates state and accepts only supported command types. The actor must exist, must not be eliminated, and must be the current active faction, regardless of controller type. All commands are rejected in pre-game states with no activation and in terminal games. Actor validation always precedes the requested state operation, including a repeated target elimination.

`EndActivation` validates first, calls `economy.resolve_player_economy(state, actor_id)` for the outgoing faction, then calls `GameState.finish_activation()` exactly once. The transition refreshes incoming movement after economy finishes. `EliminatePlayer` delegates to `GameState.eliminate_player()` and is currently an infrastructure/test command, with no combat justification or additional authorization rule. An already eliminated target remains an idempotent no-op when the actor is still eligible. Commands do not automatically end an activation: eliminating another faction leaves the activation unchanged unless the game becomes terminal. Self-elimination is special because the existing state operation already selects the successor and handles turn wrapping; the command handler must not call `finish_activation()` afterward.

`MoveUnit` additionally requires an existing unit owned by the actor. It delegates to `movement.move_unit(state, unit_id, destination)`, which validates the destination, computes the full legal shortest path and checks its cost against remaining movement. Only then does it commit the final position and deduct the cost. It never partially executes an over-budget request or automatically ends activation. Moving to the current position is rejected, including with zero movement remaining.

`AttackUnit` requires an existing attacker owned by the actor and names one explicit enemy target, including when enemies are stacked. It delegates to `combat.attack_unit(state, attacker_unit_id, target_unit_id)`. Controllers express intent; the reusable rules executor owns combat legality and resolution. A future LLM-directed executor must use these rules for damage, adjacency, range and resolution rather than asking the LLM to calculate them.

Successful execution mutates the supplied state and returns `None`. Malformed command construction, unsupported commands, invalid actors/targets, and invalid state raise descriptive `ValueError`s before mutation. There is no event or result hierarchy. Command execution is deterministic, without randomness, timestamps or shared mutable execution state. Commands are not persisted; resulting state round-trips through snapshot schema version 8.

## Live cities and Settler founding

`CityState(id, owner_id, position, *, name, population=1, food_stored=0, production_stored=0, production_target=None)` is a small mutable live entity in `GameState.cities`, keyed by explicit city ID. IDs are caller-supplied nonblank strings, unique among live cities; no city counter, randomness or automatic name generation exists. Names are required nonblank strings, need not be unique, and preserve the supplied spelling and whitespace after validation using `strip()`. Population is a persistent integer at least 1, rejecting booleans/floats and invalid values without clamping. Founding always starts at population 1 with zero food and production stores and no production target. Setup and snapshots can supply larger populations and non-negative stores. Economy can grow population; starvation and population loss are deferred.

Cities require known, non-eliminated owners and existing in-bounds grassland, plains, forest or hills tiles. Mountains and water are illegal. Exactly one city may occupy a tile, and all city centers must be at least Chebyshev distance 3 apart: `max(abs(dx), abs(dy)) >= 3`. Distances 1 and 2, including diagonals, are illegal even for the same owner; distance 3 is legal. Shared placement checks enforce this for founding, setup, state validation and loading. Friendly units may share a city tile under the existing unlimited friendly-stacking rules; the city does not count as a unit. A city and an enemy unit cannot share a tile, whether created through setup, direct state mutation or snapshot loading.

`get_city(city_id)` returns the live city and raises `ValueError` for malformed or unknown IDs. `city_at(position)` returns the live city or `None`. `add_city(city)` validates the supplied state/entity and placement before insertion, returning the same live entity; it does not consume units or claim tiles. Setup authors supply tile ownership separately. City ownership and tile ownership remain separate persistent fields; only founding couples them in this slice. `remove_city(city_id)` validates first and raises `ValueError` for an unknown ID, including repeated removal. Removal does not alter units, tile ownership, faction status or activation.

`FoundCity(actor_id, settler_unit_id, city_id, city_name)` is frozen and has no destination: the city is founded at the Settler's current position. `apply_command()` first requires a known, live, active actor and an existing owned Settler. The reusable `cities.found_city()` executor requires type `SETTLER`, at least 1 remaining movement, an unused valid city ID/name, legal city terrain, spacing and occupancy, and an unowned or same-owner center tile. Another faction's tile is rejected even if its owner has been eliminated. Invalid state or requests raise `ValueError` before any mutation.

On success, the rules add the city with population 1, remove only the Settler and assign the center tile's `owner_id` to the founder. No separate movement deduction is needed because the unit is consumed. Friendly stacked units retain their position, HP and movement. Founding does not end activation, increment the global turn, refresh units or heal them; other units may continue acting. Forest/hills terrain and all unrelated ownership remain unchanged.

Only the center is claimed. The MVP now deliberately replaces the former adjacent-city rule with minimum center distance 3, preventing radius-1 workable areas from overlapping. Working surrounding tiles does not claim them. Border expansion, buildings, city HP, city combat and capture remain deferred.

Own cities are passable; every other owner's city blocks placement, movement and BFS, which can route around it when possible. `MoveUnit` never attacks or captures cities. `AttackUnit` accepts unit IDs only. A defender on its own city is attacked with normal unit damage/retaliation; its death leaves the city and tile ownership intact. Melee advance remains blocked by the enemy city after the final defender dies. Ranged attacks still never advance and have no city defense or line-of-sight modifier.

Explicit player elimination removes all owned live cities and units, retaining the historical player and tile ownership. Existing active-player succession, movement refresh and turn wrapping remain unchanged. Removing the last city, founding with the final unit or having zero cities never automatically eliminates a faction. City snapshots are ordered by city ID ascending, and preserve name, population, food/production stores, production target, owner and position alongside player gold, tiles and damaged/spent units. Loading has no gameplay side effects, and deep copies and snapshot copies have independent mutable cities, units and tiles.

## City yields and owner-end economy

`backend/aig/economy.py` owns immutable `Yields(food=0, production=0, gold=0)`, static terrain yields, pure city queries and the economy executor. Components are non-negative integers, rejecting booleans and floats. Addition is component-wise; `sum(values, Yields())` supplies an empty zero total, and ordinary `sum(values)` also works for nonempty collections. Static values are derived from `Terrain`; tile records never persist or cache them.

| Terrain | Food | Production | Gold |
| --- | --- | --- | --- |
| Grassland | 2 | 0 | 0 |
| Plains | 1 | 1 | 0 |
| Forest | 1 | 2 | 0 |
| Hills | 0 | 2 | 0 |
| Mountains | 0 | 0 | 0 |
| Water | 1 | 0 | 1 |

The city center is always worked for free, with component minimums `max(base_food, 2)` and `max(base_production, 1)` and unchanged base gold. Grassland/plains centers yield 2F/1P, forest/hills 2F/2P. Underlying terrain stays unchanged; founding on water or mountains remains illegal.

Each population point can work one surrounding tile within Chebyshev radius 1, up to the available count. The free center does not consume a citizen slot. `workable_positions(state, city)` returns surrounding existing, in-bounds, non-mountain positions in ascending `(y, x)` order. Sparse maps retain their existing meaning: missing tiles are unavailable. Water is workable even though land units cannot enter it. Tile ownership and unit occupancy do not restrict working, and working never claims land. Minimum center spacing prevents overlapping radius-1 areas without cross-city arbitration.

`worked_positions(state, city)` selects surroundings by descending food, then production, then gold, then ascending y, then x. Thus grassland beats forest on food. It excludes the free center. `city_center_yields(state, city)` and `city_yields(state, city)` report the center and total yields respectively. Queries validate state and require its live city object, matching pathfinding's live-unit convention. Returned position lists are fresh; assignments are never stored. Every resolution recomputes them from current terrain and population.

`PlayerState.gold` defaults to zero. City `food_stored` and `production_stored` default to zero and are keyword-only like population. All three counters must be non-negative integers, with no caps, coercion or silent repair. Production is a generic stockpile spent on the single selected unit target described below. Gold has no spending yet; maintenance, queues and buildings remain deferred.

`resolve_player_economy(state, player_id)` validates a live owner, computes results for its cities in **city ID ascending order**, prepares any completed units, then commits the city fields, new units, allocator counter and aggregated treasury. It mutates existing records in place and returns `None`, preserving references held by callers. All calculations finish before the first assignment; no callbacks or intermediate events run during commit. The function owns no actor authorization, activation transition or movement refresh. Controllers must use `apply_command`; internal rules/tests can resolve a live owner independently.

For each city, select tiles and calculate all yields using the population at the start of its resolution. Apply food consumption of `2 * population`: `food_stored = max(0, food_stored + total_food - consumption)`. A deficit consumes stored food down to zero, with no starvation or population loss. Then, while stored food covers `growth_cost(population) = 10 + 5 * population`, subtract that cost and increment population. Multiple growth is allowed and surplus carries over. New citizens affect working and consumption next activation, never the current resolution. Add the pre-growth total production to city storage, complete its target if affordable, then add total gold to the owner's treasury.

The normal lifecycle is explicit:

```text
player actions (including FoundCity and SetCityProduction)
    -> EndActivation: validate state and active actor
    -> resolve outgoing owner's terrain yields and food/growth
    -> add production, complete affordable targets, collect gold
    -> add starting-population science, complete at most one research target
    -> advance activation once
    -> refresh incoming owner's movement
```

A newly founded city exists immediately at population 1 with zero stores and participates when its owner ends that same activation. Owners with no cities collect nothing. Invalid `EndActivation` requests cause no economic mutation. Economy is not attached to `finish_activation()` or `_begin_activation()`: active-player elimination removes its cities/units and selects/refills the successor without collecting for either faction or double-advancing. Snapshot loading only restores exact mid-activation values, even when stored food already exceeds a growth threshold.

There are no resources, improvements, rivers, roads, terrain variants, manual citizens, culture borders, culture, faith, housing or happiness in this slice. The browser exposes the existing economy; AI remains future work.

## City production targets and unit construction

A city has one keyword-only `production_target: UnitType | None = None`. There is no queue, building construction or automatic repeat production. All five current unit types are producible once their technology requirements are met. Their costs are read-only properties derived from `UnitType`, consistent with movement and combat stats:

| Unit type | Production cost |
| --- | --- |
| Warrior | 20 |
| Scout | 20 |
| Archer | 30 |
| Spearman | 30 |
| Settler | 40 |

`backend/aig/production.py` exposes pure `production_cost(unit_type)` and `production_remaining(city)` queries. Remaining production is `None` without a target, otherwise `max(0, cost - production_stored)`. A zero shortfall does not trigger construction. Queries contain no presentation strings and do not mutate state.

The frozen command `SetCityProduction(actor_id, city_id, unit_type)` selects a target; passing `None` clears it. `apply_command()` validates the state, active game, known live active actor, live city ownership, requested `UnitType` and owner technology unlock before mutation. Runtime strings are not accepted as domain unit types. Setting, switching or clearing spends no movement or production and changes neither turn nor activation. **The stockpile is generic**: switching Warrior to Archer with 17 stored retains all 17; clearing also retains all 17. Selecting an already-affordable target waits until owner economy.

Inside the existing `EndActivation` economy, each outgoing owner's city adds that activation's production after food/growth, then checks its target. If affordable, subtract the cost, prepare one unit at the city center and clear the target, retaining all overflow. Thus Archer with 27 stored and 8 new production leaves 5. Each city completes at most one unit per resolution, even with a huge stockpile. A later command chooses the next target. Gold still resolves and activation advances exactly once afterward. `FoundCity -> SetCityProduction -> EndActivation` is legal in one activation, with no founding delay or special production rule.

Produced units belong to the city's owner, appear on its center with 100 HP and existing type-derived stats, and start with **zero movement**. They receive normal movement through the existing refresh when their owner next becomes active. Setup `add_unit()` and ordinary `UnitState` construction retain their full initial movement semantics. Friendly stacking has no limit; existing hostile-city occupancy invariants remain enforced.

Setup and economy both use `GameState._prepare_unit()`, the shared internal implementation of the existing collision-skipping `unit-N` allocator. Production does not accept a caller-provided unit ID. Economy processes cities in **ascending city ID string order** (for example, `city-10` before `city-2`), carrying the planned counter forward so simultaneous completions have deterministic IDs regardless of dictionary insertion order. Explicit occupied IDs are skipped and the persisted `next_unit_id` advances only on success. Copies own independent counters.

Economy validates the whole state and prepares every city's results and spawns before committing any assignments. Placement validation and unit construction can fail without leaving food, growth, stockpiles, targets, gold, units, IDs or activation partially changed. Preparation does not mutate state; commit has no further fallible rule calls, callbacks or events. This extends the existing compute-then-commit economy without a transaction framework. Eliminating the active player still aborts economy, removes its cities and units, and advances once; removed cities cannot produce. Loading and copying never complete targets.

## Land movement and deterministic pathfinding

Movement uses eight adjacent square-grid directions, with no wrapping. Every step costs exactly 1, including diagonals; there are no terrain-specific costs or square-root diagonal costs. A diagonal checks its entered tile and may pass between blocked orthogonal neighbors. All current unit types may enter grassland, plains, forest and hills. Mountains and water are impassable; there is no embarkation.

| Unit type | Movement allowance |
| --- | --- |
| Settler | 2 |
| Scout | 2 |
| Warrior | 1 |
| Archer | 1 |
| Spearman | 1 |

The immutable base allowance is derived by `UnitType.movement_allowance`; it is not duplicated on live units. `UnitState.moves_remaining` is a persistent per-activation integer in `[0, movement_allowance]`. Booleans, floats, negative values and values above the allowance are rejected. A unit at zero cannot move, while other units may still act.

Friendly units may stack without a limit: a unit may pass through and stop on friendly stacks. Enemy units and enemy cities block both paths and destinations. Own cities allow normal friendly stacking and do not count as units. Only same-owner cities are friendly; there are no alliances. Placement, state validation and movement enforce the same land passability and hostile co-location rules. `MoveUnit` never implicitly attacks; it rejects enemy destinations. There are no intermediate-tile events, so multi-step movement resolves atomically.

`backend/aig/movement.py` isolates `find_path(state, unit, destination) -> list[Position] | None`. It takes a live unit from the supplied state and returns both endpoints, or `None` for an unreachable, missing, impassable, enemy-occupied or out-of-bounds destination. Its path to the current position is `[unit.position]`. Invalid state, a non-live unit or malformed input raises `ValueError`. It does not mutate state, enforce actor activation, or limit paths to the current movement budget, so callers can also inspect longer routes.

The implementation uses breadth-first search because all edges cost 1. Neighbors are always visited in **N, NE, E, SE, S, SW, W, NW** order. A FIFO queue and first-visit predecessor links choose a stable shortest path; dictionary/set iteration never chooses neighbors. Every entered tile is checked for bounds, terrain, hostile units and enemy cities through `GameState.can_enter()`. Future variable costs can replace this isolated BFS with Dijkstra/A* without changing destination-based command intent.

Pathfinding is deterministic executor infrastructure, not controller strategy. A future UI, heuristic controller or LLM-directed executor can reuse it without supplying every intermediate tile. It contains no AI/LLM logic, combat resolution, zones of control, fog, borders or roads. City occupancy is an entry restriction, without city combat or capture.

## Deterministic unit combat

Combat stats are read-only properties derived from `UnitType`, following the existing movement-allowance convention. They are not duplicated on `UnitState`.

| Unit type | Combat strength | Ranged strength | Attack range |
| --- | --- | --- | --- |
| Settler | 0 | None | 0 (cannot attack) |
| Scout | 10 | None | 1 |
| Warrior | 20 | None | 1 |
| Spearman | 25 | None | 1 |
| Archer | 10 | 20 | 2 |

Every live unit, including Settlers, stores integer `hp` in `[1, 100]`; `MAX_UNIT_HP` is 100. Booleans, floats and out-of-range HP are rejected, never clamped. New units begin at 100. Lethal damage removes units from `GameState.units`; dead units are never retained with nonpositive HP. Activation refresh restores movement only, without healing.

Range uses Chebyshev distance, `max(abs(dx), abs(dy))`, and must be between 1 and the attacker's range. Scout, Warrior and Spearman can attack any of the eight adjacent tiles. Archer uses ranged attacks at distance 1 or 2, including diagonals, with no separate melee attack mode. There is no line-of-sight check in the MVP: Archers can fire over friendly or enemy units, forest, hills, mountains, water and missing intermediate tiles. Later LOS rules must explicitly refine this behavior.

`calculate_damage(attacking_strength, defending_strength)` returns `max(10, min(50, 30 + attacking_strength - defending_strength))`. There is no RNG, HP-based strength scaling, terrain defense, unit-type counter, or other modifier. For example, 20 vs 20 deals 30; 25 vs 20 deals 35; 10 vs 20 deals 20.

Melee uses each unit's normal combat strength for damage and retaliation. Both sides deal full damage from the pre-combat state even if either receives lethal damage, so both may die. Retaliation does not spend the defender's movement and still happens when its movement is zero. An Archer defending against melee uses its normal strength of 10 for defense and retaliation. Ranged attacks use the Archer's ranged strength against the target's normal combat strength, receive no retaliation, and never move the Archer, even after a kill.

Every attack costs exactly 1 movement point. Zero movement prevents attacking; a Scout with 2 remaining can attack and retain 1 for another move or attack. There is no separate action budget. Attacks leave the active player, global turn and activation order unchanged, including when all units have spent their movement. They never call `finish_activation()` or infer faction elimination from unit death. Explicit player elimination continues to remove all of that player's remaining live units.

An attack affects only its chosen target; there is no splash damage or automatic escort selection. After a melee kill, a surviving attacker advances onto the target tile only if the destination is otherwise legally enterable. `can_enter(..., excluding_unit_id=target.id)` evaluates the prospective entry before mutation, excluding only the defeated target. Another hostile unit or an enemy city prevents advance. This advance is included in the single movement-point attack cost. Remaining enemy stack members are unaffected and continue blocking movement. Friendly stacking remains legal, and hostile co-location remains invalid.

Settlers cannot attack. As a temporary MVP rule, any valid enemy attack destroys a Settler immediately at any HP, without retaliation. A melee attacker advances after destroying a lone Settler if the tile has no enemy city; a ranged attacker stays in place. Civilian capture can replace this rule later.

Resolution is atomic at the synchronous rules/command boundary. State and actor validation precede attacker ownership, target, attack capability, movement and range checks. All checks finish before mutation. The executor computes both damages, resulting HP/deaths, spent movement and any advance from the pre-combat state, then commits only assignments/removals with no further fallible rules, callbacks or intermediate events. Invalid commands leave the entire supplied state unchanged. Like movement, the internal executor validates game rules while actor authorization remains in `apply_command()`; controllers must use that boundary.

The economy and production slices implement terrain yields, automatic working, food/growth, generic production storage, single-target unit construction and gold income. Research and explicit game setup/start complete the first-playable backend milestone, now exposed through the browser application without extra game rules. Buildings, repeat production, purchases, maintenance and AI remain outside this slice. Later conquest work must define capture/destruction and automatic elimination while preserving the single-successor activation transition. Infrastructure `EliminatePlayer` is not exposed to the browser. Decide a rules-version compatibility policy before changing static stats independently of the snapshot shape.


## Tiny Ancient-era research

The research/setup slice starts from 340 passing tests and snapshot v7.
`Technology` is a `StrEnum` in `state.py`, with exactly three static rules:

| Technology | Science cost | Prerequisites | Unit unlock |
| --- | --- | --- | --- |
| AGRICULTURE | 0 (already known at normal creation) | None | SETTLER |
| ARCHERY | 15 | AGRICULTURE | ARCHER |
| BRONZE_WORKING | 20 | AGRICULTURE | SPEARMAN |

WARRIOR and SCOUT are always unlocked. Technology costs and immutable prerequisite
sets are derived enum properties; `research.py` exposes `technology_cost`,
`technology_prerequisites`, `available_technologies`, `research_remaining` and
`unit_is_unlocked`. Available options are a tuple in enum declaration order.
Current target and stored science are directly readable player fields. Remaining
science is `None` without a target, otherwise `max(0, cost - science_stored)`.
Queries are pure and contain no frontend labels or formatting.

`PlayerState` adds integer `science_stored >= 0`, nullable `research_target`, and
`researched_technologies: frozenset[Technology]`, defaulting to Agriculture alone.
Booleans, floats, non-enum values, an already-known target, and unmet target
prerequisites are rejected. The immutable collection cannot hold duplicates;
loading checks duplicate array entries before constructing it. Exceptional
manually assembled states may have no technologies, allowing prerequisite rules
to be exercised without changing normal faction defaults.

The frozen `SetResearch(actor_id, technology)` command requires a valid active
activation and known, live, current actor. Non-null targets must be enum values,
unresearched and prerequisite-satisfied. `None` clears the target. Setting,
switching and clearing preserve all generic science, movement, city production
and activation state. Selection never immediately completes research, even when
already affordable. Science continues accumulating without a target.

Each live owned city contributes its population at the start of economy
resolution. Two cities of population 3 and 2 contribute 5 science. A city growing
from 2 to 3 contributes 2 now and 3 on its next owner activation, matching existing
worked-tile yield timing. `resolve_player_economy()` computes science inside the
existing prepare/commit path, alongside city results and pending produced units.
No second resolution system is introduced. The exact normal command order is:

```text
validate EndActivation and outgoing actor
    -> for each outgoing city in ascending city ID order:
         capture starting population science and worked-tile yields
         compute food/consumption, growth, production and at most one unit
         accumulate gold
    -> add science; if target is affordable, subtract cost, add technology,
       clear target and retain overflow (at most one technology)
    -> commit prepared city/unit/allocator/gold/science/research results
    -> advance activation exactly once
    -> refresh incoming faction movement through _begin_activation()
```

All fallible preparation occurs before mutation. No target is selected
automatically. Technologies cannot be lost through gameplay, so previously
selected production targets remain valid. `SetCityProduction` enforces unlocks;
low-level placement remains usable for explicit scenario/test units.
Elimination never calls economy: active elimination removes cities/units and
selects exactly one successor without generating science or completing research;
inactive elimination resolves no research for either player.

Snapshot v8 adds exactly the three persistent player research fields. Technology
strings serialize in ascending value order, independent of frozenset iteration.
Costs, prerequisites, unlock tables, income and available options are never
serialized. All earlier fields remain, including `next_unit_id`. Loading and
copying preserve pre-game, mid-research and already-affordable state without
starting play, collecting science, completing research/production or refreshing
movement. Strict v8 loading rejects earlier schemas instead of migrating them.

## Deterministic game setup and start

`setup.py` provides frozen `PlayerSetup(id, controller, starting_position)` and
`GameSetup(config, game_map, tiles, players, turn_order)` dataclasses. Players and
turn order are tuples; tiles are an immutable tuple of `(Position, Terrain)`
pairs. This matches the existing split between immutable `GameMap` bounds and
live tile records, without sharing mutable `TileState` objects with new games.
The seed is retained as configuration; setup uses no randomness.

Normal setup requires at least two unique player IDs. Turn order must contain
every player exactly once, with no unknown entries. Each explicit start must be
in bounds, have a tile, and be grassland, plains, forest or hills. Water,
mountains, missing tiles, duplicate starts and starts at Chebyshev distance less
than 3 are rejected. Diagonal distance uses `max(abs(dx), abs(dy))`. No replacement
position is searched for. Negative map origins and sparse maps retain their
existing semantics; all supplied tiles must be unique and in bounds.

`create_game(setup) -> GameState` is the supported application-level creation
entry point. It returns detached mutable state at turn 0 with no active player,
no cities and an explicit live turn order. Fresh players have zero gold/science,
no research target and Agriculture. Tiles begin unowned. In exactly turn-order
sequence it calls the existing `add_unit()` allocator for one Settler followed
by one Warrior at each faction's starting tile. Both have full HP and normal
initial movement. Friendly stacking is legal. A two-player fresh game allocates
`unit-1` through `unit-4` and leaves `next_unit_id == 5`. Repeated identical setups
produce identical IDs and snapshots. There is no separate allocator.

`start_game(state) -> None` validates the whole pre-game state, turn 0, no active
player, and a valid order of at least two live factions. It calls the existing
`_begin_activation(turn_order[0])`, refreshing only that faction's units. It does
not increment turn, collect economy/science, or complete research/production.
Calling it twice fails without mutation. All gameplay commands reject pre-game
states and are usable subject to their normal rules after start. The global
turn stays 0 until the first full activation cycle completes; established
elimination/terminal semantics continue to apply.

`scenarios.demo_game_setup()` is the committed, hand-authored 12 by 10
square-grid demo. Literal rows fix all six terrain types, obstacles and land
routes. A starts at (2, 2), B at (9, 7), both using `ControllerType.HUMAN` until
actual AI exists. Starts permit immediate `FoundCity` through real Settler rules.
The scenario remains stable unless its source is intentionally revised. There
is no procedural generation, server, UI, AI provider or autonomous loop here.
`tests/test_setup.py` exercises a complete two-faction opening, research/unit
completion, deterministic snapshots, and every README Python example.
