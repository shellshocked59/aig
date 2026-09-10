# Reference Architecture Study

## Executive Summary

Investigated on 2026-09-10. Listing `C:\code` found `aig`, `email-qa`, and `DoLP_v0.762`. The user confirmed that **`email-qa` is the intended Python reference**, originally called zuku-ci in the request. The DoL reference is **`DoLP_v0.762`**, a compiled distribution rather than a source checkout.

The most useful combination is email-qa's explicit module contracts and execution/presentation split, plus DoL's distinction between static definitions, saved state, and rendering resources. AIG should retain one small Python package with ordinary domain modules, plain serializable state, an explicit RNG, and a browser UI that presents results without executing authoritative rules.

The current JavaScript/esbuild/Python direction remains appropriate. Django, Celery, databases, and a communication transport are not needed to adopt these patterns. The next issue should be **#2, Define shared game-state data model**, kept to a short design document and tiny example. Set the vocabulary and ownership before adding state-bearing features.

This study used local source inspection and a read-only review of all eight GitHub issues. Neither reference was changed or executed. No reference code, artwork, or game content is included here. Recommendations are proposals, not implemented systems. “Adopt now” means a convention to apply in the next relevant issue, not an instruction to create empty infrastructure during this study.

## zuku-ci

### Observed architecture and evidence

All paths in this section are relative to `C:\code\email-qa`.

The repository has a Django project package, `config/`, and one application package, `core/`. Its main lifecycle is submission, asynchronous analysis, persistence, and report presentation. `core/email_checks/` is the most useful internal boundary for AIG: small modules export definitions with a common input/result contract, while an explicit registry determines which checks run.

| Concern | Concrete evidence | Observation |
| --- | --- | --- |
| Project/application split | `manage.py`, `config/settings.py`, `config/urls.py`, `core/apps.py`, `core/urls.py` | Framework setup has an obvious home separate from application behavior. This is one Django application, not a collection of independent services. |
| Dependency management | `requirements.txt`, `pyproject.toml`, `package.json` | Python dependencies use bounded version ranges in one requirements file, including development tools. `pyproject.toml` configures Black/Ruff rather than packaging. npm has a lockfile. |
| Domain contracts | `core/email_checks/base.py` | Dataclasses describe parsed inputs, context, results, and check definitions. String enums give statuses stable serialized values; results have an explicit conversion to plain dictionaries. |
| Extension points | `core/email_checks/__init__.py`, individual check modules | A tuple registry holds explicit check definitions. No automatic filesystem plugin discovery is needed. |
| Configuration | `config/env.py`, `config/yaml_loader.py`, `config/yaml/email_checks.yml`, `core/email_checks/config.py` | Environment loading is centralized. Cached YAML loading feeds domain validation that rejects missing/unknown keys and invalid enablement values. |
| Execution | `core/tasks.py:162`, `config/celery.py` | The task accepts a report UUID, loads data, constructs a context, runs checks, and persists results/progress. Celery also schedules log pruning. |
| Persistence | `core/models.py:88`, `core/migrations/` | ORM records use explicit status choices, identifiers, timestamps, JSON results, and relational findings. Execution status and report outcome have separate fields. |
| Presentation | `core/report_presentation.py`, `core/views.py`, `core/templates/core/partials/analysis_output.html` | Stored results are shaped into user-facing sections and summaries rather than directly dumped into the UI. Some presentation orchestration remains in views. |
| Tests | `core/tests/test_email_checks.py`, `test_tasks.py`, `test_report_presentation.py`, `test_homepage_playwright.py`, `pytest.ini` | Tests follow owning concerns. Local builders, direct ORM creation, pytest fixtures supplied by plugins, and monkeypatching are used. No dedicated factory library or custom fixture layer was found in the inspected tests. |
| Logging/errors | `core/watchdog.py`, `core/management/commands/`, `core/tasks.py` | Structured event keys, durations, correlation identifiers, sanitized metadata, and error paths support diagnosis. Logging can persist to the database and a file. |
| Development/CI | `scripts/`, `.githooks/`, `.github/workflows/deploy.yml` | Named wrapper commands are shared between local work and CI. CI performs checks before deployment, then browser checks after deployment. |
| Environment | `compose.yaml`, `Dockerfile` | One application image supports web, worker, and scheduler processes alongside PostgreSQL and Redis. SQLite is available for host-side tests. |
| Documentation | `documentation/docs/architecture.md`, `code-map.md`, `development.md` | Architecture explains the lifecycle; the code map points from symptoms to owning files; development documentation gives a short re-entry workflow. |

### Patterns worth adopting now

- **Keep infrastructure outside rule modules.** Preserve `backend/aig` as an importable package. Its future game functions should accept state and inputs explicitly, without Django settings, a database connection, or a task worker. Borrow the `config`/application distinction as a boundary, without creating a Django project.
- **Use small typed contracts.** Begin with dataclasses, enums where helpful, and ordinary functions. Separate runtime state from the dictionary/JSON representation at the boundary. The check context/result pairing is a good model for future command input/result and strategy observation/proposal contracts.
- **Make extension points explicit when they first exist.** A small registry of named callables is sufficient for an initial set of strategy providers or rule handlers. Stable keys should be independent of display names. Do not build a plugin framework in advance.
- **Separate result production from presentation.** Rule code should return structured outcomes; frontend modules choose labels, formatting, and panels. This also lets a headless runner use the same rules.
- **Organize tests by the behavior they protect.** Reuse small fixture builders rather than setting up an application server for a rule test. Begin with focused tests in the first RNG/grid implementation issue.
- **Keep navigation documentation short.** Extend the existing architecture document with ownership pointers as modules appear. A Markdown code map can provide the useful part of the reference documentation without a documentation-site toolchain.

### Patterns worth considering later

- **Validated configuration:** when definitions or provider options exist, load once at the application boundary and fail clearly on unknown IDs or malformed fields. Pass validated configuration into the core. There is no need for an environment loader today.
- **Background work:** if experiments or LLM calls become long-running, use a job wrapper around an ordinary callable. Record job identity, lifecycle, result/error, and elapsed time. Celery is a possible later implementation only if queueing, durable jobs, or multiple workers justify it.
- **Persistence:** saved runs may eventually need IDs, timestamps, and explicit statuses. These concepts work in files as well as ORM records. If a database arrives, store domain state through an adapter; do not make every tile a Django model by default.
- **Structured diagnostics:** use Python's standard logging first, with run ID, turn, seed, command/provider ID, and duration when relevant. Add richer storage or a viewer after there are real diagnostic needs.
- **Shared quality commands:** add pytest and a small lint/format command with substantive Python code. Ruff alone is a reasonable initial lint/format choice; adopting both Ruff and Black is unnecessary for familiarity alone. Put development dependencies in AIG's existing `pyproject.toml` and choose a reproducible development install when that set exists.
- **CI and containers:** a small build/test workflow is useful soon. A multi-service Docker environment is useful only after multiple services actually exist. Keep local commands usable from Windows rather than assuming Bash and `.venv/bin/python`.

### Patterns not appropriate for AIG

- **Inappropriate at this stage:** Django, Celery, Redis, PostgreSQL, a scheduler, a service layer for every entity, or a database-backed logger simply to match the reference stack.
- **Tied to email-qa's requirements:** upload validation, anonymous report access, authentication/preview gating, report retention, IP fingerprints, server-rendered templates, deployment hosts, and log-pruning jobs. These solve that product's workflow.
- **Tied to its operations:** the Docusaurus site, remote restart/deployment machinery, SCSS build, and broad shell-hook system should not become prerequisites for running AIG's menu or Python tests.

### Lessons / potential pitfalls

1. **A task boundary is not automatically a domain boundary.** `analyze_email` is roughly 240 lines and combines loading, rule orchestration, persistence, progress, summaries, and logging. For AIG, keep the simulation callable outside any future task function; let the task adapt it to a job system.
2. **Short database locks do not establish exactly-once execution.** The task's initial `select_for_update()` transaction ends before analysis. This study does not establish duplicate-job safety. If AIG later runs concurrent jobs, validate the expected state revision and prevent applying the same accepted result twice.
3. **Check what quality wrappers actually run.** `scripts/run-pytest.sh` invokes only `core/tests/test_homepage.py`. The local hook and CI call that wrapper, so those commands do not run the full Python suite despite broader documentation. AIG's future default test command should discover the whole intended suite; narrower commands should say so.
4. **Avoid configuration side effects in imports.** `config/settings.py` creates log directories while importing; YAML loading imports Django settings. These choices are understandable in a web application but would complicate importing AIG's rules in a small headless test.
5. **Typing is helpful but not complete isolation.** Frozen dataclasses in the reference contain mutable lists/dictionaries, and several fields use `Any`. Do not treat `frozen=True` as deep immutability or a type hint as serialization validation.
6. **Dependency and environment drift are visible.** Python tooling targets 3.12, CI uses 3.12, and the Docker image uses 3.13. Python ranges do not lock the complete environment. AIG should document and exercise its chosen supported versions when CI is introduced.
7. **The AI module is a placeholder.** `core/email_checks/ai_tests.py` does not execute an AI review. It supports the registry lesson, but is not evidence of a working LLM integration pattern.

## DoL

### Observed architecture and evidence

`C:\code\DoLP_v0.762` contains `Degrees of Lewdity.html` and an `img/` tree. The HTML is 55,746,901 bytes, with 16,133 passage records, 432 passages tagged as widgets, and 231 source-module markers in its main embedded user script. Metadata identifies Tweego 2.1.1 and SugarCube 2.36.1 for this particular build. These are observed artifact metadata, not recommendations about current tool versions.

The distribution retains original source-path comments, allowing a partial reconstruction of organization. Paths beginning `game/` below identify **embedded source markers, not files present in this checkout**. Line numbers refer to the compiled HTML. No build scripts, dependency manifests, source test suite, CI configuration, or contributor documentation are available here; their existence or quality upstream cannot be concluded from this distribution.

| Concern | Evidence in compiled HTML | Observation |
| --- | --- | --- |
| Source organization | Main user script at line 17437; markers for `game/00-framework-tools/`, `game/01-config/`, `game/03-JavaScript/`, `game/04-Variables/`, domain subdirectories | Separate authored modules compile into the distribution. Numeric prefixes expose an ordering convention; exact upstream build rules are unavailable. |
| State and definitions | `game/00-framework-tools/constants-loader.js`, line 21023; `StoryInit`, line 198569 | The constants loader protects definition data. Initialization distinguishes setup variables from loaded story variables; state and temporary variables are widely accessed through shared runtime aliases. |
| Lifecycle | `PassageHeader`, line 198508; `game/03-JavaScript/time.js`, line 69514 | Passage navigation has shared hooks; time advancement has ordered minute/hour/day handling. This is a passage-oriented game, not a 4X turn engine. |
| Save/load | `game/01-config/sugarcubeConfig.js`, line 21627; `game/03-JavaScript/save.js`, line 65378 | Save/load hooks manage metadata and version updates. Local storage, optional IndexedDB behavior, file import/export, and compression/compatibility paths coexist. |
| Migrations | `game/00-framework-tools/02-version/.init.js`, line 17701; `Widgets VersionCheck`, line 198526; `Widgets variablesVersionUpdate`, line 201283 | There is a numbered migration registry as well as extensive legacy compatibility code. One legacy passage alone contains about 248,000 characters and 1,294 conditional blocks. |
| Reusable UI/events | Widget-tagged passages; `game/00-framework-tools/observable.js`, line 21073; `game/03-JavaScript/eventpool.js`, line 51888 | Reusable widgets, subscriptions with unsubscribe behavior, and named weighted event pools reduce repeated authoring. The event pool also supports debug overrides. |
| Entities/world | `game/03-JavaScript/named-npc.js`, line 63775; `Widgets MiniMap`, line 191014 | Entity helpers use name-based lookup and shared state, with legacy aliases still present. The inspected minimap indexes targets by coordinate before drawing cells. This does not establish a general-purpose world/grid model. |
| Rendering/assets | `game/03-JavaScript/00-libs/renderer.js`, line 22446; `game/03-JavaScript/05-renderer/00-canvasmodel.js`, line 30494 | Canvas models compose layers with source-image and processed-layer caches. Rendering options are separate from reusable model definitions. |
| Asset variants | `img/` category directories and `img/imagepacks/`; `game/03-JavaScript/02-Helpers/imagepack-resolver.js`, line 25815 | A resolver maps logical image paths to candidate packs and fallback paths. Assets are distributed separately from the large HTML file. |
| CSS | Embedded engine styles and `twine-user-stylesheet`, line 16384 | Framework chrome has separate style blocks; retained author-source markers include error UI and minimap styling. Complete upstream CSS authoring/build conventions cannot be reconstructed confidently. |
| Developer tools | `debug-menu.js`, line 49187; `event-debug.js`, line 51655; canvas editor modules, lines 43170 and 44615; `scanNaNs`, around line 67209 | Debug controls, targeted event reproduction, render inspection, invalid-number scanning, and performance logging are embedded. Tool presence does not establish automated test coverage. |

### Patterns worth adopting now

- **Separate definitions, mutable game state, and UI state.** Chassis definitions describe a type; a particular unit references that type and records its changing state; selection/highlighting belongs to the browser. This avoids saving asset caches or DOM-related values in game snapshots.
- **Establish an explicit state-change boundary.** Rendering, opening a panel, saving, and reloading should not advance AIG's turn or consume simulation randomness. A future command executor should own legal state changes, with rendering receiving the result.
- **Version serialized state from its first example.** Start with a small schema version separate from the application's release version. Plan one load/validation/migration path instead of compatibility checks scattered across screens.
- **Use stable definition and entity IDs.** Lookup by IDs supports references, diagnostics, and future data changes; display names should remain editable. Do not derive a unit's identity from its sprite filename or localized label.
- **Keep source modular and output portable.** AIG already has this distinction. Continue authoring small JS modules and bundling them for the browser rather than editing the generated output or relying on browser module loading over `file://`.

### Patterns worth considering later

- **Declarative catalogs and registries:** useful for terrain, equipment, technologies, buildings, and doctrines. DoL's constants and named lookups illustrate the value, though much of its definition data contains executable JavaScript; AIG should start with a narrower data contract.
- **Layered sprites:** later compose chassis, equipment, faction colors, and damage indicators from AIG-owned assets. An explicit layer order and shared anchor convention matter more initially than a large renderer.
- **Measured caching:** cache immutable source images and derived render layers when profiling warrants it. The coordinate index in the minimap is a small example of avoiding repeated scans. Keep derived caches out of authoritative saves.
- **Debugging alongside each system:** fixed scenarios, forced provider responses, a state inspector, and command/turn logs make failures reproducible. Add each tool with the behavior it diagnoses; a general debug console can wait.
- **Screen lifecycle cleanup:** explicit setup/teardown for event handlers helps as views grow. Use direct callbacks first; introduce shared subscriptions only when multiple consumers need them.
- **Local save export/import:** when save/load becomes an issue, keep a user-controlled file path available for transferring saves and reproducing bugs. Browser storage can be an additional convenience, not the sole copy or a promise about portability between file locations.
- **Extensibility:** asset resolution and explicit registries can support variants later. Do not promise a mod API until IDs, definitions, and compatibility behavior have stabilized.

### Patterns not appropriate for AIG

- **Inappropriate for this design:** making Twine/SugarCube passage execution the owner of AIG's simulation, relying on global variables for all state access, or triggering migrations from screen rendering.
- **Premature:** a custom observable framework, generalized weighted event framework, multi-layer animation editor, save compression dictionaries, extensive history snapshots, or a runtime mod loader.
- **Tied to DoL's requirements:** narrative passage conventions, its entity categories, content-specific time rules, art-pack catalogs, custom legacy decompression, and compatibility with its existing player saves. AIG should not inherit these concepts merely because the distribution is large.

### Lessons / technical debt to avoid

1. **Content volume is not proof of loose coupling.** Shared widgets and catalogs help authors, but state writes, presentation, and navigation are still intertwined in inspected passages. AIG can keep explicit imports and inputs from the beginning.
2. **Lifecycle ambiguity becomes save complexity.** `StoryInit` warns that it runs before loaded state exists. `PassageHeader` invokes version checks. The version-check widget preserves/restores RNG position because update work can otherwise affect event selection. AIG should load, migrate, validate, and then render in a defined order.
3. **Multiple generations of compatibility code accumulate.** The numbered migration registry coexists with large legacy widgets; `npc-compressor.js` is retained for old saves. Define a modest compatibility policy instead of promising every prototype save will work forever.
4. **Saving should not perform gameplay work.** DoL's save hook calls other update functions and mutates several copies of save statistics/history. AIG should serialize a stable snapshot; recording save metadata must not change legal game outcomes.
5. **Compression and caches have interaction costs.** The save module explicitly notes that its compression and delta encoding can increase size when combined. Start with inspectable JSON and add optimization only after measurements justify it.
6. **Evidence limits matter.** This review found debug tools and source hints, not an inspectable automated testing or localization pipeline. Text exists inside UI/passage code, but that does not prove upstream localization support is absent. No localization framework is recommended on this evidence.

## Recommended AIG Direction

The existing `frontend/src/js/main.js` only wires About, `scripts/build.mjs` produces a classic bundle and CSS with relative paths, and `backend/aig/__init__.py` is only a package marker. `pyproject.toml` already supports package discovery and has no runtime dependencies. `.github/` contains an issue template, not CI. There is no reason to replace this scaffold.

Grow toward the following shape **only as owning issues add real code**. Keep existing HTML, CSS, build, README, and packaging files; this is not a request to create all listed paths now.

```text
frontend/src/js/
  main.js                  composition and initial screen wiring
  screens/                 add with the second screen
  ui/                      add only when a control is actually reused
backend/aig/
  game/
    state.py               runtime state types as needed
    grid.py                logical grid from issue #4
    rng.py                 deterministic RNG from issue #3
  serialization.py         add with the first actual encode/decode issue
tests/
  test_grid.py
  test_rng.py
docs/
scripts/
```

Keep **one Python distribution**, with rule modules inside `aig.game`. Later add `game/simulation.py` for turn orchestration and `aig/ai/` for strategy contracts/providers when those issues arrive. Split movement, combat, or economy into domain modules only when they exist; no separate package, Django app, or service per entity. Avoid generic `utils.py` collections when a helper belongs beside its domain.

The intended dependency direction is: an application runner wires a provider and the game core together; providers consume an explicit observation and propose objectives; deterministic code validates and executes legal actions. The game core should not import provider clients, UI code, settings loaders, or task frameworks. A later LLM response is a proposal associated with a state revision, not permission to mutate state directly. Record accepted proposals to reproduce runs; a seed alone cannot reproduce a fresh LLM response.

Python types and JSON are related but distinct. Keep one documented contract and shared tiny fixtures rather than two hand-maintained catalogs of rules. Use a small state module initially; split it by domain if it becomes difficult to navigate. Keep frontend-only state, such as an open panel or selected tile, separate from simulation state.

For frontend growth, use screen modules with explicit mount/cleanup or show/hide behavior. Extract reusable controls after actual duplication. Keep CSS organized by screen/component once needed. A screen displays state and produces an input/proposal; it does not secretly advance simulation. Continue testing the built output over `file://`.

When original artwork first arrives, use `frontend/src/assets/` with small categories such as `tiles/`, `units/`, and `ui/`. Store logical art references separately from simulation statistics. Add build copying/bundling in that asset issue; the current script does not copy an arbitrary asset tree. Spritesheet packing, renderer choice, and layered assembly can wait.

The Python/JavaScript communication mechanism remains provisional. A transport-neutral serialized fixture does not select HTTP, WebSockets, Django, Flask, FastAPI, Pyodide, or any other runtime arrangement.

## Data-Driven Game Definitions

**Recommendation for the first real definition issue:** use a repository-level `data/definitions/` directory as the single authored source for shared, static definitions. Begin with one small JSON file per implemented domain, not empty files for a full imagined game. Later domains could include `terrain.json`, `chassis.json`, `components.json`, `technologies.json`, `buildings.json`, and `doctrines.json`.

| Format | Fit for AIG |
| --- | --- |
| JSON | Preferred initial interchange/catalog format: plain data and compatible with both languages. Comments are unavailable, so explanations belong in adjacent documentation. |
| YAML | Consider only if authoring larger catalogs benefits enough to justify a parser and stricter type validation. email-qa shows useful validation conventions, not a reason to add YAML today. |
| Python definitions | Suitable for small internal constants and executable rule functions. Poor as the sole shared catalog if the browser must duplicate values or parse Python. |
| JavaScript definitions | Suitable for UI-only presentation configuration. Avoid making authoritative game definitions inaccessible to Python. |

Definitions should have stable IDs, explicit units for quantities, and validated references. Runtime entities should reference definition IDs rather than copy whole templates. Validate duplicate IDs, missing references, invalid ranges, and unknown fields when loading/building a catalog. Keep executable behavior in code; do not introduce formulas, embedded scripts, or a custom rule language in the first data files.

For browser usage, include required definitions in the build rather than fetching adjacent JSON at runtime over `file://`. Python can read the same authored data through an explicit loader. Installed-package distribution of those files is a later packaging decision; avoid depending silently on the shell's working directory.

The first save contract should distinguish schema version, rules/content version, state, and RNG continuation information. A map seed starts a sequence; it does not by itself describe its current position. Decide exact RNG encoding after selecting the algorithm in issue #3. Initially, reject unsupported versions with a clear message. Add a migration only when there is a real old fixture to migrate; do not implement a migration framework speculatively.

Save plain values and IDs, not Python pickle, object prototypes, DOM objects, render caches, or callable functions. On load, parse and validate a candidate state before replacing the current state. When rules/definition values change, record which version a save expects rather than silently assuming the newest catalog preserves the same outcomes.

## Testing Strategy

Adopt pytest as a development dependency with the first substantive Python implementation, likely #3. Start with a flat `tests/` directory matching modules and small fixture-building functions. Introduce `conftest.py`, subdirectories, or a factory library only when reuse justifies them. Tests should import the installed `aig` package, not rely on ad hoc path modifications.

| Area | First useful checks | Later extension |
| --- | --- | --- |
| Python rules/grid | Bounds, neighbors, invalid dimensions, explicit validation failures | Legal commands, ownership, resource conservation, and domain invariants as rules arrive |
| Determinism | Known sequence for the chosen RNG contract; independent instances; reproducible seeds | Identical starting state and recorded accepted commands produce identical results; render/save operations leave RNG state unchanged |
| Serialization | Round trip, malformed data, unsupported schema, invalid references | Old-fixture migrations, continued RNG sequence after load, definition-version mismatch |
| AI | Stub providers with valid/invalid proposals; observation unchanged by provider execution | Timeout/unavailable handling, stale proposals, legal fallback behavior; live LLM experiments remain opt-in |
| Frontend | Actual `file://` build loads; About and future setup navigation work; input validation and keyboard focus | A small Playwright suite, plus pure JS tests where non-DOM logic exists |

For deterministic simulation, compare semantic state or a defined canonical representation rather than arbitrary JSON key ordering. Pin algorithm/rules assumptions for known-answer fixtures. Model outputs need recorded fixtures; do not assert that live LLM calls repeat byte-for-byte.

A small future CI workflow should run `npm ci`, the build, and the intended Python test suite, adding browser smoke checks once the UI grows. Keep expensive experiments separate from routine checks. Do not require Redis, PostgreSQL, a model download, or a web server for core tests. This documentation-only investigation required no build or test execution in either reference.

## Decisions We Should Make Soon

1. **State ownership and vocabulary, in #2:** one game-state root, entity versus definition IDs, player/faction terminology, references, coordinate convention, and which values are browser-only. Keep cities/units skeletal; no rules or speculative field catalog.
2. **Initial snapshot envelope, in #6:** schema version, naming/numeric conventions, a minimal example, validation responsibility, and explicit rejection of unsupported versions. Make it consistent with #2 without choosing transport.
3. **RNG guarantee, in #3:** seed types, algorithm/version scope, explicit instance ownership, and what continuation information will eventually be saved. Test the chosen guarantee.
4. **Python test entry point, with #3 or #4:** use a development dependency group/extra and a command that discovers the actual suite. Create real module/test paths as part of that issue.
5. **Temporary setup choices, before #1 implementation:** allowed map sizes and faction limits, input validation, and alignment with #2's terminology. These remain prototype UI constraints.

## Decisions We Should Explicitly Defer

- Python/browser transport and execution location, including all server and embedded-Python choices.
- Django, Celery, a database, distributed jobs, authentication, multiplayer, and deployment topology.
- Complete simultaneous/sequential turn policy, tactical execution, combat/economy abstractions, and a full technology graph before a first simulation slice needs them.
- Live LLM integration, provider scheduling, prompts, model selection, and a production provider/plugin framework.
- Canvas versus DOM versus WebGL for the eventual map; layered mech renderer, sprite atlases, and art pipeline.
- Full catalogs of equipment/technologies/doctrines, a data editor, scripting, mods, and localization infrastructure.
- IndexedDB versus other convenience storage, autosave/history, compression, complete replay tooling, and long-term save compatibility promises.
- Large documentation sites, container stacks, dedicated observability services, broad test matrices, and property-testing frameworks before concrete use cases exist.

## Suggested Backlog Adjustments

Reviewed `docs/backlog.md` and GitHub issues #1-#8 on 2026-09-10; all eight were open and their scopes matched the local backlog. **No issues were created, edited, or reordered.**

| Existing issue | Proposed adjustment |
| --- | --- |
| [#2 Define shared game-state data model](https://github.com/shellshocked59/aig/issues/2) | **Next.** Add explicit separation of definitions, runtime state, and UI state. Decide IDs and coordinates. Keep the five requested entities minimal, with no implementation classes or rules. No further split is necessary if this remains a short document/example. |
| [#6 Define frontend/backend game-state interchange format](https://github.com/shellshocked59/aig/issues/6) | Follow #2; remove the need to design against an unfinished model. Narrow the first task to a versioned snapshot and validation contract. Split detailed command/result semantics into a later small issue when the first legal action exists; a placeholder command example may remain clearly provisional. |
| [#3 Implement deterministic seeded RNG in Python](https://github.com/shellshocked59/aig/issues/3) | First small Python implementation after the model decisions. Include the lightweight test setup here and document continuation/reproducibility requirements. Do not implement a second browser RNG or save system. |
| [#4 Implement basic square-grid map model](https://github.com/shellshocked59/aig/issues/4) | Follow #2's coordinate contract. It does not depend on random generation, so #3 is not a technical prerequisite. Keep it logical and unrendered. |
| [#1 Add New Game setup screen](https://github.com/shellshocked59/aig/issues/1) | Can proceed after #2 settles terminology. Use one small screen module and temporary form state; no game creation or transport. It can precede #3/#4 if visible UI progress is preferred. |
| [#5 Render a static tile grid in the browser](https://github.com/shellshocked59/aig/issues/5) | Use a tiny fixture consistent with #2/#6, bundled at build time. Keep it separate from generation. It need not wait for a Python connection or full simulation. |
| [#7 Define initial war-machine chassis model](https://github.com/shellshocked59/aig/issues/7) | Keep as a short design note; defer component catalogs, balancing, and implementation until a unit slice needs them. Do not enlarge it into a mech subsystem specification. |
| [#8 Define StrategyProvider architecture](https://github.com/shellshocked59/aig/issues/8) | Preserve the observation/proposal/validation boundary now in architecture notes. Tackle the detailed issue when a minimal state and legal action can support a concrete example; keep heuristic/LLM implementations out of scope. |

Only two additional small tasks appear justified, and neither needs to block #2:

- **Implement a minimal state JSON round trip:** after #6 and the first actual state types, encode/decode one fixture and test malformed data, unsupported versions, and unchanged state on failed load. This is separate from a save UI, browser storage, transport, or a generalized migration engine.
- **Add a small build/test CI workflow:** after #3 creates a real Python suite, run the existing frontend build and all intended Python tests using documented commands. Add browser checks with the next meaningful UI increment; no deployment stack.

One conservative order is **#2 -> #6 (snapshot scope) -> #3 -> #4**, with **#1** available after #2 and **#5** after the shared fixture is defined. Keep #7 conceptual and #8 grounded in the first executable rules. The order is a recommendation for discussion, not a change to GitHub.
