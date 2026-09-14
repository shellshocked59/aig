# Arena UI Phase 1

Arena is playable locally with one command and no model service. This phase adds
launching, readable controls, and battle feedback; it does not change game rules.

## Launch on Windows

One-time setup from PowerShell (Python 3.11+ and Node 24+, or Node 22.13+):

```powershell
cd C:\code\aig
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
npm.cmd ci
```

Everyday launch:

```powershell
cd C:\code\aig
npm.cmd run dev
```

Open **http://127.0.0.1:5173/arena** and choose **Human vs Heuristic · Offline**.
You control Blue; Red is the deterministic heuristic. **Local Match / Manual**
lets you control both teams. Stop with Ctrl+C. Frontend changes rebuild; refresh
the browser to see them. Restart the command after Python changes.

The launcher owns a Python web host on a free loopback port and the frontend on
5173. It waits for health, reports startup failures, and shuts down its children
when stopped. It leaves existing port-8000 sessions alone. Local preview uses
its own API even when a deployment origin is configured in `.env`.
If 5173 is occupied, stop the previous frontend terminal before retrying.
No Docker, database, Redis, Ollama, or OpenAI key is required for these modes.
Matches are in memory and shared by browsers using the same backend process.

On Linux/macOS use `.venv/bin/python` and `npm`. The advanced two-terminal
workflow remains `.venv\Scripts\python.exe -m aig.web` followed by
`npm.cmd run dev:frontend`. After `npm.cmd run build`, the Python web host
also serves `/arena` directly on port 8000. An absent build returns a readable
503 with the build command. The original `aig.api:create_app` remains API-only.

## What prevented convenient preview

Previously `npm run dev` started only esbuild and an API proxy, so it required a
separate Uvicorn command. Visiting Python's port displayed no game page. The
root frontend opened Empire, and Arena required a second entry and creation
step. Documentation offered several launch paths without an Arena-first quick
start. Arena also placed provider buttons, raw action summaries, and long rules
above or alongside the board without a clear play hierarchy.

The default command now owns both processes. `/arena` selects Arena directly;
the root view also opens Arena by default, with Arena first in the header.
Empire remains available from the header and directly at `/empire`.
The two safe modes are prominent. Experimental model modes remain collapsed
and require an explicit choice; loading or refreshing the page performs reads
only and never starts inference.

## Screen and controls

| Area | Behavior |
| --- | --- |
| Header | Agent Strategy / Arena, manual and heuristic modes, New Match, Refresh; collapsed experimental choices |
| Turn bar | Mode, human ownership, active team, turn, remaining AP out of 5, prominent End Turn |
| Board | 45 DOM buttons in a 9×5 grid; 126px-tall desktop tiles; horizontally scrollable on very small screens |
| Units and Cores | Original SVGs, class labels, BLUE/RED ownership labels, team borders, numeric HP and HP meters |
| Downed units | DOWNED badge, faded rotated icon, dashed border, zero HP; bodies remain visible |
| Terrain | Distinct POWER/WARD/SIEGE tiles with labels; striped ruins with an impassable-terrain icon; concise board legend |
| Selection | White outline; inspect any unit during a human turn; choosing another owned active unit cancels the current targeting mode unless it is a legal target |
| Actions | Explicit buttons with server-provided AP costs; unavailable actions disabled; all classes and specials retained |
| Targets | Gold outlines and accessible legal-target descriptions from backend action queries; Fireball uses impact tiles |
| Right panel | Selected-unit details/actions, board guide, battle log; rules, development metadata, and AI details collapsed |
| AI | End Turn shows AI turn status and disables human controls until the real result returns |
| Log | Latest 60 successful commands, newest first, including human and AI actions, actual damage/healing and downed/revived/finished counts |
| Victory | Large winner banner, Core destroyed or Team eliminated reason, disabled gameplay; New Match preserves the current mode |
| Errors | Readable API/creation/command errors; state retained on rejection and Refresh remains available |
| Accessibility | Actual buttons, visible keyboard focus, pressed states, class/team/status text and useful tile titles/ARIA labels |

No client-side legality or damage prediction was introduced. All positions,
targets, costs, damage, HP, AP, and wins come from Python. The human sees the
completed heuristic turn and its log; action animation is a later phase.

## API and preservation

`aig.web` wraps the existing application and installs the existing Arena router
with an `ArenaWebSession` subclass. The subclass retains the original session
lock, commands, AI orchestration, and result handling. Only browser responses
gain `battle_log: [{id, text}]` and nullable `terminal_reason`.
Summaries derive from successful replay entries and initial piece labels, never
provider text. The original API factory and Arena session remain byte-for-byte
unchanged because the research preservation checks freeze those source files.

Empire routes, rules, and presentation are retained. Docker's development web
container uses `dev:frontend` and its development API uses `aig.web`; the existing
production API launcher is unchanged. No deployment was performed.
No model inference, new benchmark run, schema/prompt/provider change, balance
change, or historical artifact update was made. Existing research working-tree
changes were left intact. Frozen-source tests are retained without new exceptions.

## Files

Added:

- `scripts/dev.mjs`: one-command process launcher.
- `backend/aig/web.py`: playable host and browser session presentation.
- `backend/aig/arena/battle_log.py`: bounded summaries of successful trace entries.
- `tests/test_arena_ui.py`: web routes, presentation, preservation, and isolation tests.
- `scripts/arena-ui-smoke.mjs`: real Chromium/manual/heuristic smoke and screenshots.
- `docs/arena-ui-phase1.md`: this report.

Changed:

- `package.json`, `scripts/build.mjs`, `Dockerfile`: launch scripts and stable routes.
- `frontend/src/index.html`: absolute asset URLs for direct routes.
- `frontend/src/js/environments.js`: direct Arena route and visible shell entry.
- `frontend/src/js/arena.js`, `frontend/src/css/arena.css`: screen, controls, targets, logs, and states.
- `frontend/tests/arena.test.js`: eight new UI tests and updated entry-label assertions.
- `README.md`, `docs/architecture.md`: exact launch instructions.

## Verification

Run the standard checks:

```powershell
npm.cmd test
npm.cmd run build
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend: **84 tests passed**, including eight new UI tests. Production bundle:
**passed (exit 0)**. Python: **1,188 tests completed in 406.460 seconds, 1,183
passed and 5 skipped**, with no failures or errors. The skips are Linux-only
deployment checks on Windows. Six new web/API tests cover the presentation host.
The final full run includes the unchanged research preservation checks.

Real local Chromium smoke passed: direct route, 45 cells, unit selection, legal
targets, Move, unit/Core Attack, Heal, Snipe/downed state, End Turn, Core victory,
mode-preserving reset, heuristic response, AI loading/disabled controls, battle
log, and no document overflow at 900px. The loading check briefly delays delivery
of the real backend response; it does not substitute state or mock the AI.
External browser requests are blocked by the smoke harness. No browser JS errors.

The desktop, downed, heuristic, and 900px screenshots were visually inspected.
The board and actions are readable, icons render, and panels do not overlap.
The sidebar can extend below the board; optional rules/details are collapsed.
Screenshots are real local captures, stored under `.local/arena-ui-phase1/`:
`arena-desktop.png`, `arena-downed.png`, `arena-winner.png`,
`arena-heuristic.png`, and `arena-narrow.png`. Machine-readable browser results
are in `browser-smoke.json`; the final Python run is in `python-tests.log`.
Frontend and build output are in `frontend-tests.log` and `build.log`.
The one-command launcher was started, stopped, and restarted successfully;
port-conflict diagnostics and child cleanup were checked. The test server was
stopped after verification, leaving port 5173 free for the user's launch.

Optional browser smoke setup (requires installed Chrome; use `ARENA_BROWSER=msedge`
for installed Edge):

```powershell
npm.cmd install --prefix .local/arena-ui-tools --no-save playwright
# Keep npm.cmd run dev running in another terminal.
node scripts/arena-ui-smoke.mjs
```

This resets Arena only on the supplied local origin. It uses no external model
provider. Playwright stays in ignored local tooling, outside product dependencies.

## Next visual priorities

Phase 2 should focus on movement/action sequencing, damage/heal feedback,
clearer class silhouettes, and a more atmospheric original board treatment.
None of that work or further AI experimentation is started by Phase 1.
