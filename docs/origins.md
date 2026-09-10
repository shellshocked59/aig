# Frontend and API origins

| Environment | Frontend | Python API |
| --- | --- | --- |
| Local Apache | `http://aig.localhost` | `http://api.aig.localhost` |
| Production target | `https://www.agentstrategy.online` | `https://api.agentstrategy.online` |

API routes keep their `/api` prefix: for example,
`http://api.aig.localhost/api/health` and
`https://api.agentstrategy.online/api/game`. A request to the API root `/`
returns 404 because the API does not serve a homepage.

## Local setup

Set these values in the root `.env`:

```ini
PUBLIC_API_BASE_URL=http://api.aig.localhost
AIG_HTTP_CORS_ORIGINS=http://aig.localhost
```

The build script loads `.env` without overriding existing shell variables and
embeds only `PUBLIC_API_BASE_URL` in the JavaScript bundle. Rebuild with
`npm.cmd run build`, or restart `npm.cmd run watch` after changing the value.
The value must be an HTTP(S) origin without a path; one trailing slash is
normalized away. Leave it empty to use same-origin `/api/...` requests instead.

Install [the Apache virtual hosts](../config/laragon/aig.conf) at
`C:\laragon\etc\apache2\sites-enabled\aig.conf` and reload Apache. Both API
hostnames (the dedicated host and the frontend's compatibility proxy) reach
`127.0.0.1:8000`. This can be host Python or the published Docker API, with only
one using that port at a time. See [Docker development](docker.md).

The Node development URL `http://127.0.0.1:5173` normally uses a same-origin API
proxy. If you use it with a non-empty public API origin, add that frontend origin
to `AIG_HTTP_CORS_ORIGINS` too, separated by a comma, and restart Python.

## Production configuration

Set this in the environment that builds the static frontend:

```ini
PUBLIC_API_BASE_URL=https://api.agentstrategy.online
```

Deploy the resulting `dist/` to the static host at
`https://www.agentstrategy.online`. Set this in the Python runtime environment:

```ini
AIG_HTTP_CORS_ORIGINS=https://www.agentstrategy.online
```

Configure the production reverse proxy for `api.agentstrategy.online` to send
requests to Python while retaining their `/api/...` paths. TLS certificates and
DNS for both domains belong to the deployment setup; these repository settings
do not provision DNS or certificates. The [deployment workflow](deployment.md)
publishes the application after CI passes. The local Apache `Require local`
configuration and development Compose file are for local use.

CORS permits explicit frontend origins, GET/POST methods, and JSON Content-Type
preflights. Wildcards, paths, and trailing slashes in CORS origins are rejected.
It does not implement authentication or separate player sessions. The current
game still uses one shared in-memory match per Python process.
