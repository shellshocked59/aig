# Laragon on Windows

This configuration uses the checkout at `C:\code\aig` and Laragon at
`C:\laragon`. Apache serves the built browser files from `dist/` at
**http://aig.localhost**, with **http://api.aig.localhost** forwarding requests
to FastAPI/Uvicorn on `127.0.0.1:8000`. The frontend virtual host also retains
its `/api/` proxy for same-origin builds. Both hosts accept local clients only. The repository and its
`.env` are outside the document root.

## First-time setup

Run from the repository root in PowerShell:

Set `PUBLIC_API_BASE_URL=http://api.aig.localhost` in the root `.env` for the
separate API hostname. The frontend build reads this public value; Python's
default CORS settings allow `http://aig.localhost`. See [API origins](origins.md)
for production configuration.

```powershell
# Only if .venv does not already exist:
& C:\laragon\bin\python\python-3.13\python.exe -m venv .venv

.venv\Scripts\python.exe -m pip install -e ".[test]"
npm.cmd ci
npm.cmd run build
```

An existing working `.venv` can be reused, including one created with a separately
installed Python 3.11+. Laragon does not need to supply the interpreter. Adjust
the Python path above if your Laragon version differs.

Copy `config/laragon/aig.conf` to
`C:\laragon\etc\apache2\sites-enabled\aig.conf`. If either installation moves,
update the absolute paths in the
configuration and Procfile entry. Keep the filename without an `auto.` prefix:
[Laragon preserves custom virtual hosts with that naming](https://laragon.org/docs/pretty-urls).

Append the `AIG API:` line from `config/laragon/Procfile.example` to
`C:\laragon\usr\Procfile`. This registers the Python backend with Laragon and
starts it when Laragon starts. Restart Laragon to load the entry and Apache
configuration. For manual startup instead, use:

```powershell
.venv\Scripts\python.exe -m uvicorn aig.web:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

Use only one backend process on port 8000. Restarting it discards the in-memory
game. Python source changes require a backend restart.

## Everyday use

### Docker Python with host Apache

Apache can use the Docker API through the `api.aig.localhost` virtual host.
Install the updated `config/laragon/aig.conf` and reload Apache if it currently
only defines the frontend hostname.
Stop the host AIG API process first, then run:

```powershell
npm.cmd run build
docker compose up --build --wait api
Invoke-RestMethod http://api.aig.localhost/api/health
```

Keep Apache running and open **http://aig.localhost/**. Docker publishes Python
on `127.0.0.1:8000` and starts PostgreSQL and Redis as dependencies. Disable the
Laragon `AIG API:` Procfile entry when using Docker regularly to prevent a port
conflict. See [Docker with Apache](docker.md#use-apache-at-aiglocalhost-with-docker-python)
for checks and switching back. Host `npm.cmd run watch` still updates Apache's
`dist/`; the Docker frontend builds a separate directory inside its container.

### Host Python

Start Laragon with Apache enabled and the AIG API process running, then open
**http://aig.localhost**. This hostname works in browsers without editing the
Windows hosts file; this setup uses HTTP.

After frontend edits, run `npm.cmd run build` and refresh the page. For continuous
rebuilds, leave `npm.cmd run watch` running while using the Laragon URL. Node.js
builds JavaScript, CSS, and images; Apache serves the resulting files. There is
no need to run the Node development server when using this URL.

## Local environment and MySQL

The existing `.env` holds AI settings and is loaded by the Python application.
Apache hostnames, document roots, and the Uvicorn port are configured in the two
files above, rather than in `.env`.

Laragon's default MySQL connection is `127.0.0.1:3306`, user `root`, with an empty
password. Docker provides PostgreSQL and Redis plus optional Python clients;
AIG has no database schema or persistence integration yet. MySQL can retain its
local defaults; there is no AIG
database to create and adding database variables would not enable persistence.

## Troubleshooting

- **Arena returns `404 {"detail":"Not Found"}`, but health is OK:** the proxy
  works but the running backend predates Arena. For Docker, run
  `docker compose up -d --build --no-deps api` to install current dependencies
  and recreate only the API. For host Python, update dependencies and restart
  the process using `aig.web:create_app`. Restarting clears in-memory matches.
- **`/arena` is 404 on the frontend host:** install the current `aig.conf` and
  reload Apache. Open **http://aig.localhost/arena** and choose **Human vs Heuristic**.

- **Laragon welcome page:** reload/restart Apache and confirm that `aig.conf` is
  in `sites-enabled` and the URL is `http://aig.localhost`.
- **Missing page or assets:** run `npm.cmd run build`; the document root must
  point to `dist`, not the repository or `frontend/src`.
- **502/503 API errors:** check that the AIG API process is running on port 8000.
  Run the manual command above to see startup errors, after stopping any existing
  AIG API process. Apache errors are in `logs\aig-error.log` inside the active
  Apache installation under `C:\laragon\bin\apache`.
- **404 JSON with `no_game` from `/api/game`:** the proxy works; create a demo in
  the browser to initialize the game.

The API forwarding uses Apache's documented
[reverse proxy configuration](https://httpd.apache.org/docs/2.4/howto/reverse_proxy.html).
