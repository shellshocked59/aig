# Arena UI Phase 6 — board-first HUD

## Follow-up: log-only rail

The latest refinement makes the right rail exclusively a full-height, vertically scrolling Battle Log. Rules & abilities is now a full-width boxed accordion below the entire game layout (including the log on narrow screens). Development info, coordinate controls, the lab link and AI diagnostic disclosures have been removed from the Arena page. The standalone presentation lab remains available at its existing URL. Coordinates remain hidden in Arena; the lab retains its own fixture options.

This supersedes the original sidebar/development descriptions below. Updated frontend tests pass (193 tests), the production build passes, and Chromium checks at 1920 and 900 pixels verify accordion placement/opening and the log-only rail. Screenshots: `artifacts/arena-ui-phase6/rail-refinement/`. No gameplay or backend changes were made.


Phase 6 changes Arena's frontend hierarchy and visual palette. Gameplay, AP costs, abilities, terrain bonuses, balance, heuristics, prompts, schemas, observations, benchmarks, replay, presentation events, and Empire remain unchanged. No new dependencies or artwork were introduced. No model inference or live benchmark was run.

## Design and layout

The previous page spent considerable height on the title/status and placed selected-unit information, small actions, a permanent Board Guide, and the battle log in equally framed sidebar cards. Gold represented both POWER and legal targets. The new direction uses neutral charcoal/slate chrome, restrained borders, existing original miniatures, and distinct interaction colors.

The hierarchy is status, board, command deck, then supporting information:

- Compact Arena heading and environment navigation. Human vs Heuristic V2 is directly available; Other modes collapses V1, local two-player, and experimental Luna access. These controls call existing APIs. New Match retains the current controller mode instead of always switching to Luna. Refresh remains available. Merely opening Arena does not create a match or call a model.
- Status strip prioritizes team turn and remaining AP. Mode and turn number are secondary. One End Turn control sits at the right. AI thinking and sequential action counts occupy the strip; the winner's team colors the terminal state.
- A wider board occupies the primary column. The supporting rail shrinks from 300 to 240 pixels (205 at narrower desktop widths). The app width limit increases from 1480 to 1760. At 1440×1080 the measured board is 1124 pixels wide, compared with roughly 1054 before, and starts much higher on the page.
- One full-width command deck spans both columns below the board. Its left region shows 96-pixel class art, team, ACTIVE/DOWNED, HP and concise stats. Its center contains large icon/name/AP controls with ability accents and readable disabled states. Its right region shows action/AP, targeting instructions and Cancel. Empty selection provides a direct instruction.
- The right rail contains the scrollable log and collapsed Rules & abilities / Development info. AI diagnostics are nested inside Development info. Rail height is bounded by board height, so opening supporting details cannot push the deck down.

Latest log entries have neutral emphasis, a left marker and increased padding. Existing event text and animation synchronization are unchanged. The log remains newest-first and vertically scrollable; no data model or fabricated team attribution was added.

## Palette, typography and spacing

Scoped CSS tokens define background, panel/elevated panel, borders, foreground, muted/disabled text, terrain, selection, targeting and a 4/8/12/16/24 spacing scale. Existing Phase 4 materials and effects retain their tokens. The existing `--arena-text` overlay layer index is deliberately kept separate from the new `--arena-fg` text color.

| Meaning | Treatment |
| --- | --- |
| Blue / Red ownership | Existing blue and coral art, BLUE/RED labels, round/angular bases |
| POWER | Ochre `#bd9c50`, subdued terrain fill |
| WARD | Periwinkle `#8c9ccc`, subdued terrain fill |
| SIEGE | Mauve `#bc87bd`, subdued terrain fill |
| Selected unit/action | Bright neutral white |
| Legal Move | Cyan `#78d9ed` |
| Legal hostile target | Coral `#ff9d8e` |
| Legal support target | Mint `#9aefbd` |
| Fireball impact choice | Orange `#ffb076` |
| Disabled action | Slate, readable label/AP and partially desaturated icon |

Terrain uses quiet fills and thin borders; interaction targets use inset rings and dots. Targeting instructions and accessible tile labels identify the action, so color is not the sole cue. Blocked ruins retain their hatch. No tiles or legal target sets are changed.

System typography replaces the large serif Arena title. Unit class and turn/AP have stronger hierarchy; secondary text is smaller and muted. The deck uses one frame with internal dividers rather than nested cards. Ability information remains accessible by hover, keyboard focus or its information button. No fake keyboard shortcuts were added.

## Responsive behavior

Tested Chromium viewports: 2560×1440, 1920×1080, 1440×1080, 1080×900 and 900×900. Board cells use a height bound based on viewport height. All tested boards fit within the visible viewport and unit art/HP fit their cells without document overflow. The complete deck also fits at the three larger desktop sizes.

Below 1250 pixels the context occupies a second deck row. Below 980 pixels the rail moves below the deck. Below 700 pixels the deck stacks and actions wrap; the board retains an internal horizontal scroller. This is not a portrait-phone redesign. Short or narrow laptop windows can require vertical scrolling to see the full command deck.

## Presentation and accessibility verification

The presentation engine and animation driver are unchanged. The lab automatically consumes the shared board/deck; its existing gallery, speed, instant and AI-turn demos remain available.

`arena-hud-geometry.mjs` measures source/target centers for Ranger Attack, Fireball and Heal at 1920, 1440, 1080 and 900 pixels. All centers were within one pixel of the corresponding tile center. Every visible Fireball area matched a real cell's dimensions and center. A resize during Move reconciled to the expected destination and left no effects behind. This checks post-resize reconciliation and fresh geometry; it does not claim continuous retargeting of an already travelling projectile during every resize frame.

The existing temporal lab review exercises all fixture effects, HP/floating-text timing, moving ghosts, projectile presence, nine-cell Fireball impact, down/revive, finish, victory, interruption/cancellation, reduced motion and instant mode. No errors occurred. New HUD tests additionally check passive/disabled controls during V1/V2 sequential playback and restoration afterward. Real local Heuristic V2 playback was reviewed in Chromium.

Text contrast checks cover foreground, muted text, disabled labels and the three terrain colors, with at least 4.5:1 for the checked pairs. This is a targeted check rather than a full accessibility audit. Buttons retain names, AP text, aria-pressed, focus-visible outlines, and native semantics. Selected artwork has a team/class accessible label. Keyboard activation and Cancel work, with focus restored after rerender. Coordinates remain hidden by default and the development toggle works.

## Visual assessment

| Review question | Finding |
| --- | --- |
| Does the board dominate? | Yes: it starts higher, gains horizontal room, and has quieter surrounding chrome. |
| Does the deck feel like a game HUD? | Yes: contiguous identity, ability tray and targeting context replace sidebar form controls. |
| Are abilities easier to scan? | Yes: larger icons, stable action names, separate AP lines and clear selected states. |
| Is selected-unit identity stronger? | Yes: enlarged existing art sits beside team, class, HP and status. |
| Is the rail less cluttered? | Yes: log first, with rules and all diagnostics collapsed. |
| Are terrain and interaction colors separate? | Yes: subdued gold/periwinkle/mauve terrain versus white/cyan/coral/mint/orange interactions. |
| Are ownership cues still strong? | Yes: original team art, text, bases and tile edges remain. |
| Do animations align? | Yes in measured fresh/post-resize scenarios and reviewed playback; continuous in-flight resize retargeting is not claimed. |
| Understandable without a permanent guide? | Yes: explicit deck instructions, named terrain tooltips and the accessible Rules disclosure explain the board. |

## Evidence and reproduction

Evidence is in `artifacts/arena-ui-phase6/`, separate from Phase 4. Key screenshots: `before.png`, `default.png`, `selected-mage.png`, `selected-knight.png`, `selected-ranger.png`, `selected-cleric.png`, `target-move.png`, `target-attack.png`, `target-heal.png`, `target-fireball.png`, `ai-turn.png`, `downed.png`, `victory.png`, and `selected-mage-900.png`. Lab effect images and temporal samples are under `lab/`. JSON reports record viewport geometry, errors, overlay measurements and contrast ratios.

```powershell
cd C:\code\aig
npm.cmd run dev
```

Arena: http://127.0.0.1:5173/arena

Presentation lab: http://127.0.0.1:5173/arena/presentation-lab

The server was already running on port 5173 during this review. The initial launch detected that occupied port; review reused the existing local server. The browser connector was unavailable, so the repository's installed Playwright with real headless Chrome supplied screenshots and DOM/geometry checks.

```powershell
npm.cmd test
npm.cmd run build
.venv\Scripts\python.exe -m unittest discover -s tests
node scripts/arena-hud-smoke.mjs
node scripts/arena-hud-geometry.mjs
$env:ARENA_EVIDENCE_DIR='artifacts/arena-ui-phase6/lab'
node scripts/arena-presentation-lab-smoke.mjs
```

The HUD smoke script resets local Arena, uses only local/manual and offline heuristic modes, blocks model-provider creation routes, and leaves a fresh V2 match. The geometry/lab checks use authoritative local fixtures. No Phase 4 evidence was overwritten.

## Files and remaining scope

Changed: `frontend/src/js/arena.js`, `frontend/src/css/arena.css`, `frontend/tests/arena.test.js`, `frontend/tests/arena-ai-playback.test.js`. Added: the two HUD browser scripts, this document and the evidence directory. Phase 5 documentation has a short link to this later browser review; its historical results remain intact.

Remaining rough edges: narrower/shorter windows may scroll vertically; tooltips retain the existing explanatory text; the battle log has plain event text rather than rich inline damage styling; opening a disclosure does not persist through all action rerenders. No mobile overhaul or theme system was added. The next smallest useful pass is manual-play polish of short-window deck density and tooltip/disclosure behavior, before any balance or heuristic changes. Phase 6 does not automatically continue into that work.

## Final validation results

- Frontend: **193/193 passed**, zero failures (`frontend-tests.txt`).
- Python: the full unittest discovery ran **1,220 tests in 380.831 seconds**, with 1,213 passes, five platform skips, one failure and one error. Both unsuccessful tests reported `source_mutation` because the frozen inventory overlapped frontend edits: `ActionIdTests.test_expanded_schedule_below_theoretical_ceiling` and `RepairFullMatchTests.test_two_explicit_arms_and_offline_comparison`.
- With all source edits stopped, the unchanged action-ID guard passed in **11.948 seconds** (`python-guard-confirmed.txt`) and the unchanged repair comparison passed in **68.788 seconds** (`python-repair-guard-rerun.txt`), both with process exit code zero. Thus **1,215 distinct Python tests passed across the full run and targeted reruns, with five skips**. The initial failed run is preserved in `python-tests.txt`; no guards or backend tests were changed. These tests use fake providers, not live inference.
- Production build: passed. Whitespace check: `git diff --check` passed.
- Real Chrome: five viewport sizes, all four class selections, four targeting modes, downed/victory, local controls, real offline V2 playback, reset and coordinate toggle passed.
- Temporal lab: **16 fixture effects**, cancellation, reduced motion and instant mode passed with no browser/presentation errors.
- Geometry: **12 action/viewport combinations**, resize reconciliation and keyboard checks passed. Checked contrast ratios range from **5.69:1 to 13.71:1**.
- Preservation: `git diff --exit-code` confirmed no changes under `backend/` or `tests/`, nor to the presentation engine, animation driver, lab controller, class artwork, action icons, Empire controller or shared main CSS.

PowerShell initially wrapped unittest's stderr output as shell error records; the two final guard confirmations capture stdout/stderr through Python's subprocess API so the actual successful process exit codes are verified. Pytest is not installed; the project's unittest runner supplied the results above.

## Later mode simplification and observer mode

The subsequent [Arena modes update](arena-modes.md) replaces the earlier menu with Human vs Heuristic, Human vs OpenAI Luna, and OpenAI Luna vs OpenAI Luna. It adds web-only observer endpoints and one-turn-at-a-time playback. Earlier statements here about unchanged backend files describe the original UI phase, before that follow-up.
