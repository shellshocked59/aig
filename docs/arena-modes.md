# Arena play and observer modes

The public mode menu contains exactly:

- Human vs Heuristic (existing heuristic-v2 implementation; version hidden)
- Human vs OpenAI Luna
- OpenAI Luna vs OpenAI Luna

The active mode appears in the menu summary and status strip. No V1/V2, local two-player, Qwen or configured-provider choices are exposed. Existing API capabilities remain available.

Observer matches use OpenAI controllers for both seats and the existing provider/controller pipeline. Creating a match initializes the provider but makes no inference request. **Next AI turn** explicitly runs one turn, returning the existing presentation batch for sequential animation. Human commands are disabled and rejected by the server. There is no automatic full-match loop; New Match preserves observer mode.

The web-only session adds `POST /api/arena/observer/demo` and `POST /api/arena/observer/turn`. The frozen Arena API, controller, prompts, observations, schemas, replay, combat and heuristic implementations are unchanged. Existing provider fallback behavior is preserved. This is a follow-up beyond the earlier frontend-only Phase 6 scope.

Restart `npm.cmd run dev` after this backend change (stop the current process with Ctrl+C, then run it again). Python does not hot-reload in that command.

Validation: 193 frontend tests, 2 observer API tests, 6 Arena UI tests and 15 presentation tests passed. Production build and whitespace checks passed. Real Chromium verified the three labels, idle creation, one explicit turn request, input lock during animation, and the next team's ready state. Browser responses came from a TestClient-generated fake-provider fixture; no paid model calls were made. Evidence: `artifacts/arena-ui-phase6/observer-{menu,playing,ready}.png` and `observer-fixture.json`.

## Actual local-site backend (2026-09-14)

The user's Apache site is `http://aig.localhost/arena`, with `.env` setting the built bundle's API origin to `http://api.aig.localhost`. Apache proxies that API host to the Docker service on port 8000. It is separate from `npm run dev` on port 5173. Restarting the latter does not refresh the Docker backend.

The observer 404 was resolved with `docker compose restart api`: the source was already bind-mounted but the Python process had not reloaded it. Rebuilt the frontend with `npm.cmd run build`, then verified the actual header selection in real Chromium on `aig.localhost`: POST to `api.aig.localhost/api/arena/observer/demo` returned 200, both controllers were `openai_ai`, no alert was shown, and no AI turns were requested. Screenshot: `artifacts/arena-ui-phase6/observer-apache-creation.png`. All 194 frontend tests pass. The missing-route message now identifies the configured backend and includes both Docker and dev-server restart instructions.

For this Apache workflow, use `npm.cmd run build` for frontend changes and `docker compose restart api` for bind-mounted Python changes. A dependency/image change may require rebuilding the API image. Always verify through the actual page/API origins before declaring a local-site issue fixed.
