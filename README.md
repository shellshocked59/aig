# Aether, Iron & Glory

The repository now supports two research environments: **Empire**, the existing
long-horizon strategy experiment, and **Arena**, a separate deterministic 9x5
fantasy tactics game with perfect information and five shared AP per turn.
Empire's heuristic/Qwen/Luna experiments remain preserved. Arena includes
downed units, Finish/Revive, class specials, obstacle LOS, and direct tactical
turn providers: Heuristic, Ollama/Qwen and OpenAI/Luna (Phase 4).

**Play Arena locally:** after the one-time setup under [Running Locally](#running-locally),
run `npm.cmd run dev` in PowerShell and open **http://127.0.0.1:5173/arena**.
Choose **Human vs Heuristic** to play Blue, or **Local Match / Manual**
to control both teams. Select a unit, choose an action, and click a gold target.
**End Turn** lets the opponent act; **New Match** resets the current mode.
No model service, API key, Docker, database, or paid request is needed.
The app shell also has an **Arena** entry. Model modes are tucked
under **Experimental AI** and require an explicit selection.
See [Arena UI Phase 1](docs/arena-ui-phase1.md) for controls and verification.

`AIG_ARENA_TURN_PROVIDER` selects the configured Arena opponent independently of
Empire's `AIG_STRATEGY_PROVIDER`; both default to heuristic. AI turns run after End Turn.
Model actions are bounded to five AP, with one static-output repair and visible
heuristic fallback on provider failure. See [Arena AI](docs/arena-ai.md) for
opt-in smoke commands and [Phase 4 verification](docs/arena-phase4-verification.md). Run
`python -m aig.arena.simulate --max-turns 100` for deterministic AI vs AI, or
`python scripts/arena-ai-verify.py` for four identical matches and tactical probes.
See [Arena rules](docs/arena.md) and [Arena AI contracts](docs/arena-ai.md).

Arena Phase 5 adds controlled matches and frozen tactical probes with strict
provider purity, separate warmup latency, and offline replay verification:

```powershell
.venv/Scripts/python.exe -m aig.arena.benchmark --mode matches --games 4 --output .local/arena-heuristic-matches
.venv/Scripts/python.exe -m aig.arena.benchmark --mode probes --probe all --probe-trials 4 --output .local/arena-heuristic-probes
```

These commands use only the offline heuristic. See [Arena benchmarking](docs/arena-benchmarking.md)
for metrics, interpretation, and the separately authorized live-provider commands.

Current Empire runtime: **Environment V5 / Scenario V3 / snapshot v12**. Permanent total
war, undefended city capture and zero-city elimination now permit conquest
victory. Fog, resources, barbarians and frozen planner/model artifacts remain.
The primary future comparison is Heuristic vs Luna.
See [V5 rules and artifact decisions](docs/environment-v5.md) and
[V5 verification](docs/environment-v5-verification.md).

AIG is an experimental turn-based 4X strategy project. Its intended combination is:

- Classic tile-based empire strategy.
- Customizable fantasy war machines.
- AI-driven strategic opponents.

## Project Goals

Investigate whether an LLM can serve as a high-level strategy provider while conventional software handles deterministic game rules, movement, combat, and validation. The project is intentionally being developed incrementally, through small issues and experiments.

## Architecture Direction

The browser uses plain JavaScript, HTML, CSS, and esbuild. A thin FastAPI application exposes the deterministic Python engine through HTTP/JSON. The browser talks only to the Python API; all gameplay rules remain in the independently usable engine. Heuristic and local Ollama strategic providers share the same deterministic executor. See [architecture notes](docs/architecture.md).

```text
frontend/src/      Browser UI, API client, styles, and original local sprite atlas
frontend/tests/    Node test runner + jsdom interaction/client tests
backend/aig/       Engine, snapshots, settings, application session, and HTTP API
tests/            Python unittest engine/application/API tests
scripts/build.mjs  esbuild build/watch and development server with API proxy
docs/             Architecture and initial issue backlog
.github/          GitHub Actions CI and small-task issue template
dist/             Generated browser-ready output (not committed)
```

## Current Status

AI experiments now record independent environment, scenario, prompt, plan-schema,
model-profile and benchmark versions plus source revision/dirty status. See
[artifact selection and provenance](docs/benchmarking.md#experiment-artifacts-and-provenance)
and the [preserved heuristic/Qwen/Luna baseline mapping](docs/baselines.md).
`AIG_STRATEGY_PROMPT_VERSION` defaults to latest; explicit `v1` pins the original
instructions. Benchmark reports always record concrete resolved identifiers.

Prototype 0.0.1 is manually playable in the browser: create/start the fixed two-faction demo, found cities, move and fight with units, choose production and research, then continue hot-seat play or face the conventional heuristic AI in Human vs Heuristic AI. The sprite map has six terrain types, five unit types, and city labels. The engine uses snapshot schema v12. Human vs LLM adds local Ollama planning; Human vs OpenAI adds cloud planning. There is no procedural map generation, city HP/combat, authentication, multiplayer networking, or persistence UI. Undefended cities can be captured.

## Continuous Integration

[App CI](.github/workflows/ci.yml) runs on pull requests, pushes to `main`, and manual dispatches from GitHub Actions. It uses an Ubuntu runner with Node.js 24 and Python 3.11 (the minimum supported Python version), caches npm downloads, and runs:

```sh
npm ci
npm run build
npm test
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
```

Any failed check fails its job. New pull-request runs cancel older runs; main-branch workflows finish without being interrupted during deployment. Test jobs require no repository secrets, `.env` file, or Ollama service. The Docker Stack job removes application source mounts and checks both test suites from the images. Production Images checks the static frontend and production API/database stack. The published API port checks do not run Apache, and browser integration tests remain deferred.

After all checks pass on `main`, the workflow deploys the tested commit over SSH
to `/var/www/tca/aig` and verifies the public frontend/API release, assets,
health, and CORS. See [production deployment](docs/deployment.md) for the existing
SSH secrets, Apache/load-balancer routing, and server prerequisites.

## Running Locally

With Docker Desktop running Linux containers, start the Python API, frontend,
PostgreSQL, and Redis from the repository root:

```sh
docker compose up --build --wait
```

Open **http://127.0.0.1:5173**. No host Python/Node installation or `.env` file is
required. See [Docker development](docs/docker.md) for configuration, tests,
database access, and shutdown. Ollama stays external and optional. PostgreSQL
and Redis are available for development; game persistence is not implemented.

For Laragon on Windows, see [the Laragon setup](docs/laragon.md): Apache serves
`dist/` at `http://aig.localhost` and exposes Python at `http://api.aig.localhost`.
See [frontend/API origins](docs/origins.md) for local configuration and the
production targets `www.agentstrategy.online` / `api.agentstrategy.online`.

Install Python 3.11+ and Node.js 24+ (or Node.js 22.13+ on the 22.x line). Run these commands from the repository root.

Windows PowerShell setup (no environment activation required):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
npm.cmd ci
```

Start everything with one command:

```powershell
cd C:\code\aig
npm.cmd run dev
```

Open **http://127.0.0.1:5173/arena**, then choose **Human vs Heuristic**.
Keep the terminal running; stop with **Ctrl+C**. The launcher starts its own Python
backend on a free loopback port, waits for health, and starts the frontend watch
server on port 5173. Existing Python sessions on port 8000 are left alone.
Local preview uses its own same-origin API even if `.env` contains deployment
origins. Frontend edits rebuild automatically; refresh the browser to see them.
Restart the command after Python edits. Sessions are in memory and local users
share the same Arena match within one backend process.

If port 5173 is occupied, stop your previous frontend terminal and retry.
Missing dependencies or startup failures are printed in the terminal. An API
connection failure is also shown in the game, with **Refresh** available to retry.

For an existing backend or Docker, the original two-process workflow remains:

```powershell
# Terminal 1
.venv\Scripts\python.exe -m aig.web
# Terminal 2
npm.cmd run dev:frontend
```

The standalone frontend proxy forwards `/api` to port 8000 by default;
`API_HOST`/`API_PORT` and `PUBLIC_API_BASE_URL` retain their existing meanings
in this advanced workflow. After `npm.cmd run build`, FastAPI can also serve
**http://127.0.0.1:8000/arena** directly. Missing assets return an actionable
build instruction. `/` opens Arena by default; `/empire` opens Empire directly.

On macOS/Linux, create `.venv` with `python3 -m venv .venv`, then use
`.venv/bin/python` instead of `.venv\Scripts\python.exe` and `npm` instead of
`npm.cmd` in the commands above. The `[test]` extra installs HTTPX2 and a compatible Starlette for API tests;
`pip install -e .` alone installs the runtime application.

`npm run dev` launches Python and builds/watches JavaScript, CSS, imported PNGs, and HTML. Refresh
the browser after edits. `npm run build` produces ignored `dist/` output;
`npm run watch` rebuilds without starting a server. The playable game requires
HTTP and Python, so opening `dist/index.html` with `file://` is no longer supported.

Run local checks with `npm.cmd test`, `npm.cmd run build`, and
`.venv\Scripts\python.exe -m unittest discover -s tests -v`. Python tests include
every Python example below. The engine modules remain standard-library-only;
FastAPI and Uvicorn are confined to the application boundary.

### Browser controls

1. **New Demo Game · Hot-seat** or **Human vs Heuristic AI** creates the pre-game state. **Start Game**
   begins Amber League (faction A). Azure Union (faction B) acts next.
2. Click a unit sprite or its roster button. Click another terrain tile to attempt
   movement. Python validates the path and remaining movement; errors appear
   above the map. Click an enemy while your unit is selected, then choose an
   explicit **Attack** target. Enemy stacks list each possible target.
3. Select a Settler, enter a city name in its panel, and press **Found City**.
   The server assigns the ID. Click a city to inspect population, food, and
   production; use **City production** to select, switch, or clear a target.
4. Use **Research target** to select, switch, or clear research for the active
   faction. Available choices and costs come from Python. Stored production and
   science remain when changing targets.
5. **End Turn** resolves the current faction's economy and advances one activation.
   Hot-seat passes control to the next faction; Human vs AI runs the opponent and
   returns to your next turn. The global turn begins
   at 0 and increments after both factions act. Production/research complete at
   activation end; completed targets clear and need a new choice.

Click a tile without an owned unit selected to inspect it. Stacked units can be
selected from the tile panel; stacks over two show a count button. **Esc** or
**Clear selection** stops issuing movement from the selected unit. **Refresh**
fetches the current state. **Reset Demo** immediately discards the current match.

The application intentionally holds one game in memory per process. Restarting
Python loses the match; run one worker. Multiple browser tabs share the same game
and do not synchronize automatically (use Refresh). This is a desktop demo with
scrolling at narrow widths, simple sprites, clipped long city labels (full names
in titles/details), and no animations, path preview, city combat, or victory
screen. Water/mountains remain impassable under the existing engine rules.

## Play the deterministic demo

Choose **Human vs Configured AI** to use `AIG_STRATEGY_PROVIDER` from backend
settings (default `heuristic`). **Human vs Heuristic AI** always selects heuristic;
**Human vs LLM** always selects Ollama. Hot-seat stays human-only. After creation,
the game header displays the resolved provider using the existing mode labels.

For an autonomous opponent, choose **Human vs Heuristic AI**, then **Start Game**.
You control Amber (A); the heuristic controls Azure (B). Found your first city,
choose production and research, move or attack, then press **End Turn**. The
backend completes B's activation synchronously and returns to your next turn.
Controls disable and **AI turn...** appears while the request is pending.
The map updates once with the final result. **New Demo Game · Hot-seat** (or
**Reset Demo · Hot-seat**) keeps both factions manually controlled. Choosing any
scenario replaces the current match. All modes use the existing local startup commands.

The AI founds cities, researches Archery then Bronze Working, builds a small
military before another Settler, defends against nearby superior forces, and
moves/fights toward enemy cities. It stops nearby because city combat and victory
conditions do not exist yet. All AI actions use existing commands. Heuristic
mode needs no network services. Its operational provider summary appears in the optional
`aiActivations` field returned by `/api/game`; plans and command traces remain
backend-only to preserve fog. See [AI architecture](docs/architecture.md#deterministic-heuristic-ai).

Choose **Human vs LLM** for the same game with Qwen providing only strategic
plans for Azure (B). Python contacts the configured Ollama server; the browser
continues using only `/api/...`. The default model is
`hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M` at
`http://10.0.0.250:11434`, intentionally using a 4096-token context.
Ollama is optional: **Hot-seat** and **Human vs Heuristic AI** remain available.

Plans use JSON Schema plus local validation. Invalid output gets one repair
attempt; network failures or exhausted repairs fall back to the heuristic.
The default HTTP timeout is 20 seconds per request. A repair can add another
request. Plans remain reusable for five global turns, including fallback plans.
Keep `AIG_OLLAMA_THINK=false` and `AIG_OLLAMA_STREAM=false`; the provider rejects
configurations enabling either. The timeout must be finite and positive.

The optional `aiActivations` response includes `requestedProvider`,
`actualProvider`, `fallbackUsed`, `model`, `durationSeconds`, and `retryCount`.
Discovery reasons, plans, and command coordinates are backend-only.
`aiProviders` explicitly maps AI player IDs to the selected provider, independent
of display names. Detailed, detached traces are available in Python through
`session.ai.inference_traces` (latest 64 replans), never in the ordinary HUD or
snapshots. On reuse, duration/retries are zero while plan provider/fallback
provenance remains visible.

Opt-in live checks, excluded from CI and normal tests:

```powershell
.venv\Scripts\python.exe -m aig.ai.ollama_smoke
.venv\Scripts\python.exe -m aig.ai.ollama_smoke --turns 10
```

The first validates one plan without mutating a game. The second validates each
activation of a disposable heuristic-A versus Ollama-B match and reports replans,
reuse, timings, retries and fallbacks. Exit status is nonzero for planning failure
or any simulation fallback. Both load normal environment and `.env` settings.
See the [provider implementation and validation report](docs/ollama-provider.md).

Run a reproducible headless heuristic-vs-heuristic game from the repository root:

```powershell
.venv\Scripts\python.exe -m aig.ai.simulate --turns 100
```

This validates state after every activation and prints command counts, technologies,
and final snapshot/trace hashes. Environment V2 adds fog of war, persistent terrain
and city discovery, Scout exploration, and the same information boundary for all
providers. Global military strength remains visible; enemy deployments require sight.
The fixed scenario, prompt, schema and model profiles remain V1. Snapshot v9 stores
knowledge; v8 saves are explicitly unsupported. See [Environment V2 results and
architecture](docs/environment-v2.md) for verification and replay details.

`demo_game_setup()` supplies a fixed 12 by 10 square-grid map with grassland,
plains, forest, hills, mountains and water. Both factions use manual human
controllers. Starts are explicit and separated; each faction receives a Settler
then a Warrior, allocated in turn order. There are no starting cities.

```python
from aig.commands import EndActivation, FoundCity, SetCityProduction, SetResearch, apply_command
from aig.scenarios import demo_game_setup
from aig.setup import create_game, start_game
from aig.state import Technology, UnitType

setup = demo_game_setup()
state = create_game(setup)
assert state.active_player_id is None and state.turn == 0
start_game(state)
assert state.active_player_id == "A" and state.turn == 0

# Use real founding, production and research commands for both factions.
for actor in setup.turn_order:
    settler = next(u for u in state.units.values()
                   if u.owner_id == actor and u.unit_type is UnitType.SETTLER)
    city_id = f"city-{actor}"
    apply_command(state, FoundCity(actor, settler.id, city_id, f"Capital {actor}"))
    apply_command(state, SetCityProduction(actor, city_id, UnitType.WARRIOR))
    apply_command(state, SetResearch(actor, Technology.ARCHERY))
    apply_command(state, EndActivation(actor))

from aig.barbarians import BarbarianController
BarbarianController().execute(state)  # Applications process this system phase automatically.
assert state.active_player_id == "A" and state.turn == 1
assert all(state.players[p].science_stored == 1 for p in state.civilization_ids)
state.validate()
```

New factions know Agriculture. Archery costs 15 science and unlocks Archers;
Bronze Working costs 20 and unlocks Spearmen. Both require Agriculture, which
unlocks Settlers; Warriors and Scouts are always available. City population at
the start of owner economy supplies science, so growth affects next activation's
science. The generic science stockpile accumulates even without a target.
`SetResearch(actor_id, technology)` switches targets without losing science;
`None` clears the target and preserves storage. An affordable target completes
only during owner `EndActivation`, retaining overflow and clearing the target.

`aig.research` provides pure `technology_cost`, `technology_prerequisites`,
`available_technologies`, `research_remaining` and `unit_is_unlocked` queries.
Current target and stored science are directly available as
`PlayerState.research_target` and `PlayerState.science_stored`. Snapshots use
schema v9 and preserve exact pre-game or mid-activation research state; old
schema versions are rejected, with no implicit migration.

See [setup/start](docs/architecture.md#deterministic-game-setup-and-start) and
[research rules](docs/architecture.md#tiny-ancient-era-research). The backend is
used by the browser and the command-driven heuristic AI through the application layer.

## Lower-level backend examples

Snapshot conversion uses ordinary JSON data:

```python
import json
from aig.state import ControllerType, GameConfig, GameState, PlayerState
from aig.snapshots import from_snapshot, to_snapshot

state = GameState(
    config=GameConfig(seed=42, debug_mode=False),
    players={
        "ai-1": PlayerState("ai-1", ControllerType.AI),
        "ai-2": PlayerState("ai-2", ControllerType.AI),
    },
    turn_order=["ai-1", "ai-2"],
    active_player_id="ai-1",
)
restored = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
assert restored == state
```

Controllers request changes through immutable commands. For an active game:

```python
from aig.commands import EndActivation, apply_command

apply_command(state, EndActivation(actor_id="ai-1"))
assert state.active_player_id == "ai-2"
```

`apply_command()` returns `None` on success and raises `ValueError` for invalid requests. Only the current live faction may issue commands. `EliminatePlayer(actor_id, target_player_id)` also exists as an infrastructure/test command; commands do not automatically finish activations. See the [command boundary](docs/architecture.md#controller-command-boundary) for responsibilities and self-elimination behavior.

For a minimal headless movement and combat example, build explicit tiles and submit commands:

```python
import json
from aig.commands import AttackUnit, EndActivation, MoveUnit, apply_command
from aig.snapshots import from_snapshot, to_snapshot
from aig.state import (
    ControllerType, GameConfig, GameMap, GameState, PlayerState,
    Position, TileState, UnitType,
)

state = GameState(
    GameConfig(42),
    players={p: PlayerState(p, ControllerType.HUMAN) for p in ("A", "B")},
    turn_order=["A", "B"], active_player_id="A",
    game_map=GameMap(4, 3),
    tiles={Position(x, y): TileState(Position(x, y))
           for y in range(3) for x in range(4)},
)
scout = state.add_unit("A", UnitType.SCOUT, Position(0, 0))
warrior = state.add_unit("B", UnitType.WARRIOR, Position(3, 2))
apply_command(state, MoveUnit("A", scout.id, Position(2, 0)))
assert scout.moves_remaining == 0  # The rules chose a two-step route.
saved = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
assert saved.units[scout.id].moves_remaining == 0  # Loading does not refill.
apply_command(state, EndActivation("A"))
apply_command(state, MoveUnit("B", warrior.id, Position(2, 1)))
apply_command(state, EndActivation("B"))
assert state.turn == 1 and state.active_player_id == "A"
assert scout.moves_remaining == 2

apply_command(state, AttackUnit("A", scout.id, warrior.id))
assert (scout.hp, warrior.hp) == (60, 80)  # Melee damage and retaliation.
assert scout.moves_remaining == 1
saved = from_snapshot(json.loads(json.dumps(to_snapshot(state))))
assert (saved.units[scout.id].hp, saved.units[scout.id].moves_remaining) == (60, 1)
```

All eight adjacent directions cost one movement point. Friends may stack; water, mountains, enemy units and enemy cities block travel. Over-budget or unreachable requests fail without mutation. Saves use schema v9 with player research state, a required nullable city production target, player gold, city food/production stores and all previous state; v1 through v8 saves are explicitly rejected without migration. Loading preserves exact pre-game and mid-activation state without starting play, collecting yields/science, growing cities, completing research/production or refreshing movement. See [movement rules](docs/architecture.md#land-movement-and-deterministic-pathfinding) for allowances and path tie-breaking.

`AttackUnit(actor_id, attacker_unit_id, target_unit_id)` targets one enemy and costs 1 movement. Melee units retaliate and a surviving attacker advances after killing the last enemy unit on a tile only if no enemy city blocks entry. Archers fire at Chebyshev distance 1 or 2 without retaliation, movement or line-of-sight checks. Settlers are temporarily destroyed instead of captured. Unit deaths do not eliminate factions. See [combat rules](docs/architecture.md#deterministic-unit-combat) for stats and deterministic damage.

For Settler founding, continue the example above during A's activation:

```python
from aig.commands import FoundCity

settler = state.add_unit("A", UnitType.SETTLER, Position(0, 0))
apply_command(state, MoveUnit("A", settler.id, Position(1, 0)))
apply_command(state, FoundCity("A", settler.id, "city-a-1", "New Hope"))
city = state.get_city("city-a-1")
assert city.position == Position(1, 0) and city.population == 1
assert settler.id not in state.units
assert state.tiles[city.position].owner_id == "A"
assert state.active_player_id == "A" and state.turn == 1
assert from_snapshot(to_snapshot(state)) == state
```

Founding requires at least 1 remaining Settler movement and an unowned or same-owner grassland, plains, forest or hills tile without a city. IDs are explicit and unique among live cities; names must be nonblank and may repeat. Founding consumes the Settler and claims only the center, leaving friendly stacked units and terrain intact. All city centers must be at least Chebyshev distance 3 apart, including cities owned by the same faction. Borders are deferred. Enemy cities block movement and melee advance even after their last defender dies. Explicit elimination removes live cities and units but retains historical tile ownership; removing a city alone never eliminates its owner. See [city rules](docs/architecture.md#live-cities-and-settler-founding).

Cities work their center for free plus one surrounding radius-1 tile per population. The automatic governor favors food, production, gold, then lower y/x; mountains and missing tiles are unavailable, while water is workable. Centers supply at least 2 food and 1 production. Working tiles does not claim them.

`EndActivation` resolves the outgoing owner's cities in city ID order before advancing and refreshing incoming movement. Cities consume 2 food per population, store surplus (deficits floor storage at zero), and grow for `10 + 5 * population` food. New citizens work next activation. Production accumulates in each city, then completes one affordable unit target and retains overflow; gold accumulates in its owner's treasury and has no spending yet. Explicit elimination aborts economy for that activation. See [economy rules](docs/architecture.md#city-yields-and-owner-end-economy).

Continue the founding example to collect the new city's first economy:

```python
assert (city.food_stored, city.production_stored) == (0, 0)
apply_command(state, EndActivation("A"))
assert (city.food_stored, city.production_stored) == (2, 1)
assert state.active_player_id == "B"
assert from_snapshot(to_snapshot(state)) == state
```

Choose a single city production target through `SetCityProduction(actor_id, city_id, unit_type)`. Warrior and Scout cost 20, Archer and Spearman 30, and Settler 40. Selection enforces the technology unlocks described above. Switching targets preserves the entire generic production stockpile; passing `None` clears the target and also preserves storage. Selection spends no movement or production and does not advance activation. Completion happens only after new production is added during `EndActivation`, clears the target and preserves overflow. There are no buildings, queues or automatic repeats.

Continue the economy example to build a Warrior using terrain production:

```python
from aig.commands import SetCityProduction
from aig.production import production_cost, production_remaining

apply_command(state, EndActivation("B"))  # A becomes active again.
apply_command(state, SetCityProduction("A", city.id, UnitType.WARRIOR))
assert production_cost(city.production_target) == 20
assert production_remaining(city) == 19  # One production was already stored.
produced_id = f"unit-{state.next_unit_id}"
while city.production_target is not None:
    apply_command(state, EndActivation("A"))
    if city.production_target is not None:
        apply_command(state, EndActivation("B"))

produced = state.units[produced_id]
assert produced.unit_type is UnitType.WARRIOR
assert (produced.owner_id, produced.position) == ("A", city.position)
assert (produced.hp, produced.moves_remaining) == (100, 0)
assert city.production_stored == 0 and production_remaining(city) is None
assert from_snapshot(to_snapshot(state)) == state
apply_command(state, EndActivation("B"))
assert produced.moves_remaining == UnitType.WARRIOR.movement_allowance
```

Produced units stack with friendly units on the city center. The existing collision-safe `next_unit_id` allocator is shared with setup, and cities complete in ascending city ID order. Units start with zero movement and refresh normally on their owner's next activation. See [production rules](docs/architecture.md#city-production-targets-and-unit-construction).

## Application settings

`backend/aig/settings.py` defines immutable `Settings`, `AiSettings`, `OllamaSettings`, and
`OpenAISettings` objects and committed provider defaults. Load them
explicitly when starting a caller or application:

```python
from aig.settings import load_settings

settings = load_settings()
print(settings.ollama.base_url)  # http://10.0.0.250:11434 by default
```

Each setting resolves in this order: **non-empty process environment variable →
optional developer-local `.env` → committed Python default**. An environment
value of `""` is treated as absent for every setting. Zero and false are valid
overrides. Normal development requires no local file.

| Environment / `.env` name | Committed default |
| --- | --- |
| `AIG_STRATEGY_PROVIDER` | `heuristic` (options: `heuristic`, `ollama`, `openai`) |
| `AIG_AI_REPLAN_INTERVAL` | `5` global turns |
| `AIG_AI_MAX_ACTIONS` | `256` commands per AI activation |
| `AIG_OLLAMA_BASE_URL` | `http://10.0.0.250:11434` |
| `AIG_OLLAMA_MODEL` | `hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M` |
| `AIG_OLLAMA_CONTEXT_SIZE` | `4096` |
| `AIG_OLLAMA_TEMPERATURE` | `0.0` |
| `AIG_OLLAMA_SEED` | `42` |
| `AIG_OLLAMA_MAX_OUTPUT_TOKENS` | `256` |
| `AIG_OLLAMA_KEEP_ALIVE` | `10m` |
| `AIG_OLLAMA_THINK` | `false` |
| `AIG_OLLAMA_STREAM` | `false` |
| `AIG_OLLAMA_TIMEOUT_SECONDS` | `20.0` |

The LAN address is an intentional, non-secret default for explicitly selected
Ollama play. Configuring it does not select Ollama or cause a network request.
Create an ignored `.env` at the repository root with only the desired overrides,
or copy `.env.example` as a starting point:

```ini
AIG_OLLAMA_BASE_URL=http://localhost:11434
```

For a higher-priority override in PowerShell:

```powershell
$env:AIG_OLLAMA_BASE_URL = "http://localhost:11434"
```

The local file accepts UTF-8 `NAME=value` lines, blank lines, full-line `#`
comments, and optional matching single/double quotes around values. The last
duplicate key wins. Shell expansion, interpolation, `export`, and inline comments
are unsupported; values are literal. Unrelated names are ignored, while unknown
`AIG_` names in the file raise an error to catch typos. Empty local values are
invalid if selected, except the optional `OPENAI_API_KEY`; omit tuning settings
to inherit their defaults. Whitespace-only process
values are invalid rather than treated as absent.

Integers and floats are parsed explicitly; context/output limits must be positive,
and temperature must be finite and nonnegative. Booleans accept `true/false`,
`1/0`, `yes/no`, and `on/off`, ignoring case and surrounding whitespace. Invalid
effective values raise `ValueError` naming the setting. Host, model, and keep-alive
are nonblank strings; loading does not check server availability or model support.

The default `.env` path is anchored to this source checkout, independent of the
working directory. For another installation/location, supply
`load_settings(local_file=Path("/path/to/.env"))` using `pathlib.Path`.
`local_file=None` disables local loading; `environ={}` ignores process variables
for isolated tests. Each call reads fresh settings without changing `os.environ`.
Keep the returned object and pass its Ollama settings to `OllamaStrategyProvider(settings.ollama)`.
Application settings are separate from per-game `GameConfig` and snapshots.
Ollama is optional: Hot-seat and Human vs Heuristic AI work without a model server.

The two `AIG_AI_*` settings are positive integers. Plans are reused until the
interval expires or their target becomes invalid. The command limit includes
`EndActivation`; exceeding it raises a development error rather than hanging.
Applied commands remain committed if an unexpected AI error occurs. These are
application controls and do not alter engine rules or snapshot contents.

### Selecting the normal application strategy provider

`settings.ai.strategy_provider` chooses **which provider normal application AI
play uses**. Provider-specific settings describe **how that provider works**:

| Setting | Purpose |
| --- | --- |
| `AIG_STRATEGY_PROVIDER` | Select the normal application provider |
| `AIG_OLLAMA_*` | Configure Ollama; does not select it |
| `OPENAI_API_KEY` / `AIG_OPENAI_*` | Configure OpenAI; does not select it |

The selector accepts exactly lowercase `heuristic`, `ollama`, or `openai`.
It follows the same non-empty process environment > root `.env` > committed
default precedence. Empty process values fall through; invalid effective values
(including uppercase names or empty local values) raise a clear `ValueError`.
The committed default stays `heuristic`, so a fresh checkout makes no external
AI requests and needs no credentials or model server.

```ini
# Local development using LAN Ollama
AIG_STRATEGY_PROVIDER=ollama
```

```ini
# Hosted/cloud deployment
AIG_STRATEGY_PROVIDER=openai
OPENAI_API_KEY=...
```

Loading settings with `openai` succeeds even without a key. Selecting
**Human vs Configured AI** constructs `OpenAIStrategyProvider`; a missing key
returns HTTP 503 (`provider_not_available`) and preserves the current game.
Startup, hot-seat, and explicit heuristic/Ollama demos remain available.
**Human vs OpenAI** (`POST /api/game/demo/openai`) explicitly selects the cloud
provider regardless of the configured default.

`GameSession.demo(versus_ai=True)` resolves the configured provider at the
application boundary; an explicit `provider=` overrides it. Browser configured
play uses `POST /api/game/demo/configured`; existing `/demo/ai` and `/demo/llm`
retain their explicit heuristic and Ollama contracts. Ollama keeps its existing
construction, retry, heuristic inference fallback, plan reuse, and tracing.
Both Compose files pass the selector only to the API at runtime; restart the
backend after changing it. Benchmark `--provider-a` / `--provider-b` choices
remain independent of this setting, with both still defaulting to heuristic.

### Optional OpenAI configuration

The cloud boundary is **Browser -> Python API -> OpenAI**. The official
`openai>=2,<3` Python SDK is a normal backend runtime dependency, installed in
both Docker API images. Cloud inference is optional unless selected. Setting a
key does not select OpenAI; Human vs LLM still uses Ollama, and heuristic/Ollama
startup needs no OpenAI key. The browser never receives the key.

For development, put this in the ignored root `.env`:

```ini
OPENAI_API_KEY=<your key>
```

| Environment / `.env` name | `settings.openai` field | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | `api_key: str \| None` | `None` |
| `AIG_OPENAI_MODEL` | `model: str` | `gpt-5.6-luna` |
| `AIG_OPENAI_TIMEOUT_SECONDS` | `timeout_seconds: float` | `20.0` |
| `AIG_OPENAI_MAX_OUTPUT_TOKENS` | `max_output_tokens: int` | `512` |
| `AIG_OPENAI_REASONING_EFFORT` | `reasoning_effort: str` | `none` |

`OPENAI_API_KEY` is the deliberate exception to `AIG_*`; there is no
`AIG_OPENAI_API_KEY` alias. Non-empty process environment wins over the local
file and defaults. An empty process key falls through to the file; an empty or
missing local key resolves to `None`. Whitespace-only process values and quoted
local values are invalid, matching existing string validation; unquoted local
values are stripped by the env-file reader. The provider requires a
key only when explicitly selected.

The model must be nonblank, timeout finite and positive, and output limit a
positive integer. Reasoning effort accepts exactly `none`, `low`, `medium`,
`high`, `xhigh`, and `max`, as documented for
[GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna).
Loading performs no model-availability check. No temperature or seed is configured.

Both Compose files pass these variables only to the Python API at runtime.
Production uses the existing `/var/www/tca/aig/.env.production`; see
[deployment configuration](docs/deployment.md#optional-openai-configuration).
Local env files are excluded from Git and Docker build context. Keys never belong
in frontend environment, build arguments, generated JavaScript, DTOs, or snapshots.
The key is hidden from `repr(settings)` and `repr(settings.openai)`, but
`dataclasses.asdict()` and `vars()` would still include it: do not serialize whole
settings objects. Diagnostics explicitly select non-secret fields.

## Comparative AI benchmarks

OpenAI uses the same `strategy-v1` instructions and application plan validator
as Ollama, with strict Responses Structured Outputs, one invalid-plan repair,
SDK retries disabled, and existing heuristic fallback. See the
[OpenAI provider contract](docs/openai-provider.md) for schema compatibility,
sanitized failure categories, token tracing, and deployment details.

Explicit live commands (never run by tests or CI):

```powershell
.venv\Scripts\python.exe -m aig.ai.openai_smoke
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b openai --games 2 --turns 100 --output benchmark-results\luna
```

Run paired simulations from identical copies of the fixed demo. Each selected
provider controls both factions in its own run; shared rules and executor stay
the same. The default is entirely offline:

```powershell
.venv\Scripts\python.exe -m aig.ai.benchmark --games 2 --turns 100 --output benchmark-results\heuristic
```

Explicitly opt into a heuristic vs Ollama paired benchmark:

```powershell
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a heuristic --provider-b ollama --games 5 --turns 100 --output benchmark-results\qwen-baseline
```

Reports use `benchmark-v1`: JSON metrics/deltas, canonical hashes, separate
plan/command/inference traces, fallback accounting, token/context statistics and
timing. No city capture or victory condition exists, so these measure behavior
and execution outcomes rather than win rate. Save a baseline before tuning the
prompt. See [benchmark methodology and metric definitions](docs/benchmarking.md).

## Roadmap

The [initial backlog](docs/backlog.md) records the original eight tasks: New Game setup, state modeling, seeded RNG, a logical grid, static grid rendering, serialization, chassis concepts, and strategy-provider design. Foundational state modeling and snapshot conversion now exist; the backlog is not a list of implemented features. Development should proceed through individual GitHub issues.

## License

[MIT](LICENSE), copyright 2026 Aether, Iron & Glory contributors.
