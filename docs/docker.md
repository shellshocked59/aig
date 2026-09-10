# Docker development

Install Docker with the Compose v2 plugin (Docker Desktop using Linux containers
on Windows). From the repository root:

```sh
docker compose up --build --wait
docker compose ps
```

Open **http://127.0.0.1:5173**. Host Python and Node installations are unnecessary.
The first run downloads images and installs dependencies. The four services are:

| Service | Runtime | Address inside Compose |
| --- | --- | --- |
| `web` | Node 24, esbuild watch server and API proxy | `web:5173` |
| `api` | Python 3.11, FastAPI/Uvicorn, one worker | `api:8000` |
| `postgres` | PostgreSQL 17 | `postgres:5432` |
| `redis` | Redis 8 with append-only persistence | `redis:6379` |

The frontend and API publish host ports, both bound to localhost by default.
Browser requests to `/api/...` reach Python through the frontend proxy; host
Apache can also reach the published API port directly. PostgreSQL and
Redis have health checks; the API waits for both, and the frontend waits for the
API. `/api/health` reports that the API is serving without creating a game or
contacting a model provider. Database health is checked separately.

## Configuration

The root `.env` is optional. Copy `.env.example` if you want to change defaults.
Compose explicitly passes supported AI variables to Python, with shell variables
taking precedence over `.env`. Empty values inherit Python defaults. The file is
neither copied into images nor mounted into containers. Compose uses its own
dotenv parser, so prefer the simple `NAME=value` format supported by local AIG.
For literal dollar signs in `.env` values, use single quotes to prevent Compose
interpolation.

| Variable | Default | Purpose |
| --- | --- | --- |
| `WEB_BIND` | `127.0.0.1:5173` | Host address and port, e.g. `127.0.0.1:5174` if local dev already uses 5173 |
| `API_BIND` | `127.0.0.1:8000` | Published Python address used by the Laragon Apache proxy |
| `PUBLIC_API_BASE_URL` | empty (same origin) | Public API origin embedded by the frontend build |
| `AIG_HTTP_CORS_ORIGINS` | `http://aig.localhost` | Comma-separated frontend origins permitted by Python |
| `POSTGRES_DB` | `aig` | Initial database |
| `POSTGRES_USER` | `aig` | Initial database user |
| `POSTGRES_PASSWORD` | `aig-dev` | Local development password |
| `AIG_OLLAMA_*`, `AIG_AI_*` | Python defaults | Existing model and AI settings |
| `OPENAI_API_KEY` | unset | Optional cloud credential, Python API runtime only |
| `AIG_OPENAI_*` | Python defaults | Model, timeout, output limit, and reasoning effort |

OpenAI planning uses **Browser -> Python API -> OpenAI**. Both API image targets
install the official SDK as a normal runtime dependency. Setting a key alone does
not select OpenAI: use `AIG_STRATEGY_PROVIDER=openai` for configured AI or the
explicit Human vs OpenAI demo. Rebuild API images after updating dependencies.
Put `OPENAI_API_KEY=<your key>` in the ignored root `.env`.
All five [OpenAI settings](../README.md#optional-openai-configuration)
are passed only to `api`, never `web` or build arguments. Production uses the
existing `/var/www/tca/aig/.env.production` described in the
[deployment guide](deployment.md#optional-openai-configuration).

The API receives standard libpq variables (`PGHOST`, `PGPORT`, `PGDATABASE`,
`PGUSER`, `PGPASSWORD`) and `REDIS_URL=redis://redis:6379/0`. Its image installs
the optional Python `infrastructure` extra: Psycopg and redis-py. These services
and clients are ready for future storage/cache work; gameplay does not currently
read or write either service. There are no application migrations or background
worker jobs yet.

Ollama runs externally for development. The existing LAN default remains
`http://10.0.0.250:11434`. For a server running on the Docker host, set
`AIG_OLLAMA_BASE_URL=http://host.docker.internal:11434`; the server must accept
connections from Docker. Compose includes the host gateway mapping for Linux.
Hot-seat and heuristic play need no model service. Production provider
integration is separate from this development stack.

Run `docker compose up -d` after changing `.env` so affected containers are
recreated; `docker compose restart` alone does not apply new environment values.
PostgreSQL initialization variables apply only when its data volume is empty.
Changing them later does not rename the stored database/user or change its
password; update the existing database explicitly when retaining data.

## Use Apache at aig.localhost with Docker Python

The [Laragon configuration](../config/laragon/aig.conf) serves the host `dist/`
directory at `aig.localhost` and proxies `api.aig.localhost` to
`127.0.0.1:8000`. Install the updated configuration and reload Apache once to
enable the API virtual host. Set `PUBLIC_API_BASE_URL=http://api.aig.localhost`
in the root `.env` before building. The frontend then calls the separate API
hostname, including its existing `/api/...` paths. See [API origins](origins.md)
for the equivalent production settings.

1. Stop the host AIG API process in Laragon (or its terminal). Disable its
   `AIG API:` Procfile entry if switching to Docker for everyday use, so Laragon
   does not start a competing Python process on port 8000. Keep Apache running.
2. Build the host assets and start the API plus PostgreSQL and Redis:

   ```powershell
   npm.cmd run build
   docker compose up --build --wait api
   ```

3. Verify the published API and Apache proxy, then open **http://aig.localhost/**:

   ```powershell
   docker compose ps api
   Invoke-RestMethod http://127.0.0.1:8000/api/health
   Invoke-RestMethod http://api.aig.localhost/api/health
   docker compose logs --tail=20 api
   ```

Both health requests should return `status: ok`, with requests visible in the
Docker API logs. The API port must show as published by the running container;
a successful page load alone does not prove Python is running in Docker.
Starting the API automatically starts its PostgreSQL and Redis dependencies.
The Docker frontend is unnecessary for this workflow. Continue using
`npm.cmd run watch` on the host when editing frontend assets: the Docker web
service builds its own container-local `dist/`, which Apache does not serve.

To use a different host API port, set `API_BIND` in `.env` and update the
`ProxyPass` and `ProxyPassReverse` destinations in both installed Apache virtual
hosts to match, then reload Apache. To return to host Python, stop the Docker API
before starting the Laragon backend. Switching backends loses the in-memory game.

## Editing and checking

Source directories are mounted read-only into containers. Edit files normally
on the host. The frontend watches HTML, JavaScript, CSS, and sprites; refresh the
browser after a rebuild. Python reload is deliberately disabled because each
restart discards the current in-memory match. Apply backend changes with:

```sh
docker compose restart api
```

After changing `package.json`, `package-lock.json`, or `pyproject.toml`, run
`docker compose up --build --wait` again. Dependencies live inside the images,
so Windows `node_modules` and `.venv` never replace Linux dependencies.

```sh
docker compose logs -f web api
docker compose exec -T web npm test
docker compose exec -T web npm run build
docker compose exec -T api python -m unittest discover -s tests -v
docker compose exec -T api python scripts/docker-smoke.py
```

CI combines `compose.yaml` with `compose.ci.yaml` to remove the API and frontend
source mounts. It checks the actual containers have zero mounts, then runs the
smoke check and both test suites using only files copied into the images.
The published API health check tests the Docker port, not Apache or a browser.
Local development continues to use the source mounts in `compose.yaml`.

To reproduce CI beside your running development stack in PowerShell:

```powershell
$env:API_BIND = "127.0.0.1:18000"
$env:WEB_BIND = "127.0.0.1:15173"
docker compose --env-file .env.example -p aig-ci -f compose.yaml -f compose.ci.yaml up --build --wait
docker compose --env-file .env.example -p aig-ci -f compose.yaml -f compose.ci.yaml exec -T api python scripts/docker-smoke.py
docker compose --env-file .env.example -p aig-ci -f compose.yaml -f compose.ci.yaml exec -T api python -m unittest discover -s tests -v
docker compose --env-file .env.example -p aig-ci -f compose.yaml -f compose.ci.yaml exec -T web npm test
docker compose --env-file .env.example -p aig-ci -f compose.yaml -f compose.ci.yaml down --volumes
Remove-Item Env:API_BIND, Env:WEB_BIND
```

Use a fresh PowerShell terminal for these temporary port overrides. The
`down --volumes` command deletes only the disposable `aig-ci` database/cache volumes.

The smoke check fetches the page, assets, health endpoint and game endpoint
through the frontend, then runs PostgreSQL `SELECT 1` and Redis `PING` from
Python. It does not create/reset a game or modify stored data. CI runs it against
a fresh stack without `.env` or a model server.

For interactive database/cache access (commands work in PowerShell too):

```sh
docker compose exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose exec redis redis-cli
docker compose exec api python
```

In the Python shell, `psycopg.connect()` uses the provided `PG*` environment
variables; `redis.Redis.from_url(os.environ["REDIS_URL"])` uses the Redis URL.

## Stopping and data

```sh
docker compose down
```

This keeps named volumes `postgres-data` and `redis-data`. The game itself still
lives in one API process, is shared by all browser tabs, and is lost on restart.
Run one API replica with one worker until persistence/session isolation exists.

To intentionally delete all Docker database/cache data, use
`docker compose down --volumes`. This is a reset, not a routine shutdown.

This development stack uses source mounts, a frontend development server, and
local database credentials. Production uses the separate `compose.prod.yaml`
and runtime/static-export image targets; see [deployment](deployment.md).
