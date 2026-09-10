# Laragon on Windows

This configuration uses the checkout at `C:\code\aig` and Laragon at
`C:\laragon`. Apache serves the built browser files from `dist/` at
**http://aig.localhost**, forwarding `/api/` requests to FastAPI/Uvicorn on
`127.0.0.1:8000`. Both routes accept local clients only. The repository and its
`.env` are outside the document root.

## First-time setup

Run from the repository root in PowerShell:

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
.venv\Scripts\python.exe -m uvicorn aig.api:create_app --factory --host 127.0.0.1 --port 8000 --workers 1
```

Use only one backend process on port 8000. Restarting it discards the in-memory
game. Python source changes require a backend restart.

## Everyday use

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
password. AIG currently has no database driver, database settings, schema, or
persistence integration. MySQL can retain its local defaults; there is no AIG
database to create and adding database variables would not enable persistence.

## Troubleshooting

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
