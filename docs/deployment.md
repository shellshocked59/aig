# Production deployment

`App CI and Deploy` runs the initial tests, development image tests, and
production image checks. After all three jobs pass, pushes to `main` deploy the
tested commit. A manual workflow run on `main` does the same. Pull requests and
manual runs on other branches only test. Deployments are serialized and newer
pushes do not interrupt an active main-branch workflow.

## Server layout

The server already has a clone at **`/var/www/tca/aig`**. AIG uses the same SSH
server as email-qa, with its own Compose project `aig-production`, containers,
and PostgreSQL/Redis volumes. Nothing in the AIG deployment script restarts or
removes email-qa services.

```text
HTTPS www.agentstrategy.online -> load balancer -> Apache :80 -> /var/www/tca/aig/dist
HTTPS api.agentstrategy.online -> load balancer -> Apache :80 -> 127.0.0.1:18080 -> Docker Python :8000
```

The load balancer's port 80 is the Apache listener. Port 18080 is AIG's internal
Python upstream; the original choice of 8002 was already occupied on the server.
The existing Apache
vhosts must use the document root and proxy target above; the deployment does
not overwrite them or change the load balancer. Compare them with
[the reference vhosts](../config/apache/aig.conf). Keep the production Host
header when forwarding from the load balancer.

If Apache already uses a different internal Python port, set `PROD_API_BIND`
in `/var/www/tca/aig/.env.production`, for example `127.0.0.1:8012`, to match it.
When moving from the old 8002 default, update both `ProxyPass` and
`ProxyPassReverse` in the existing API vhost to `http://127.0.0.1:18080/`, then
validate and reload Apache (`sudo apachectl configtest && sudo systemctl reload httpd`
on this server). If `.env.production` explicitly sets `PROD_API_BIND`, update it
to `127.0.0.1:18080` or remove that override to use the new default. Confirm 18080
is available with `sudo ss -ltnp 'sport = :18080'` before redeploying. The workflow
does not edit Apache configuration. PostgreSQL and Redis use internal container
ports without host bindings, so they do not need different port numbers.

The repository's `dist` path becomes a symlink to a versioned static release.
Apache must be allowed to follow that symlink. On an SELinux-enforcing host,
ensure the checkout's static release directories have an Apache-readable
content context and Apache is permitted to connect to the API upstream.

The SSH user needs write access to the checkout, Git read access to its origin,
and access to Docker with Compose and BuildKit. The script tries `docker`, then
`sudo -n docker`, matching the existing server's passwordless-sudo approach.
It also needs Bash, Git, `flock`, and standard GNU file utilities. No host Node
or application Python installation is needed to build and run AIG.

## GitHub configuration

The following repository secrets already existed when this workflow was added:

| Secret | Purpose |
| --- | --- |
| `DEPLOY_HOST` | SSH hostname/address of the server |
| `DEPLOY_USER` | SSH user |
| `DEPLOY_SSH_PRIVATE_KEY` | Private key authorized for that user |
| `DEPLOY_PORT` | SSH port; defaults to 22 when absent |

Optional `DEPLOY_KNOWN_HOSTS` pins the trusted SSH host key using normal
`known_hosts` entries, including `[host]:port` for a nonstandard SSH port. When
provided, strict host verification is enabled. Otherwise the workflow uses
`accept-new`, as email-qa does. Values are written to private runner-temporary
files and removed afterward. Never commit private keys.

The optional repository **variable** `DEPLOY_PATH` overrides the default
`/var/www/tca/aig`. The older `DEPLOY_CHECK_URL` secret is not used: public checks
explicitly verify the two AIG domains above. The job reports to the GitHub
`production` environment; any existing protection rules for that environment
still apply.

## What happens on deployment

1. The runner sends the tested deployment script over SSH with its commit SHA.
2. The script locks the checkout, rejects tracked server edits, fetches `main`,
   and verifies the requested commit belongs to it. It checks out that exact
   commit in detached-HEAD mode. It rejects an older run replacing a recorded
   newer release.
3. On the first deployment, it creates `.env.production` with a random database
   password and owner-only permissions. Existing credentials are preserved.
   Production frontend/API origins have committed defaults; extra AI settings
   may be configured through the variables listed in `compose.prod.yaml`.
4. Docker builds the static frontend for `https://api.agentstrategy.online`
   into `.deploy/releases/`. It builds the API runtime image, which uses an
   installed Python package, an unprivileged runtime user, and no source mounts
   or test dependencies.
5. Compose starts PostgreSQL, Redis, and one API worker, waits for health, then
   checks the API, CORS, and database connections. PostgreSQL and Redis are not
   published to host ports. No database migrations exist yet.
6. After those checks pass, it switches the `dist` symlink to the new static
   release and records `.deploy/current-sha`. A pre-existing real `dist`
   directory is preserved under `.deploy/dist-before-*`.
7. GitHub checks public HTTPS: the frontend's `release.json`, HTML and assets,
   the API's health/revision header, and JSON CORS preflight. A routing error,
   stale frontend/API revision, or failed check makes deployment red.

This performs HTTP checks without browser integration. Production AI-provider
integration remains separate work; no model server or provider API key is
provisioned by deployment. The current game still uses one shared in-memory
match, so API replacement resets it. PostgreSQL/Redis data volumes are retained.

## Operations and failures

On the server, from the checkout:

```sh
sudo docker compose --env-file .env.production --env-file .deploy/release.env -p aig-production -f compose.prod.yaml ps
sudo docker compose --env-file .env.production --env-file .deploy/release.env -p aig-production -f compose.prod.yaml logs --tail=100 api
```

An unsuccessful frontend build leaves the previous release serving. Failed API
checks prevent the frontend switch, but API replacement may already have
happened; there is no automatic API rollback. A failed public check also fails
the job without silently undoing the release. Inspect the logs and fix/redeploy.
The checkout may already be at the attempted commit after a failed build.

Old frontend releases are retained for diagnosis and manual recovery; remove
unused releases only after confirming they are not the target of `dist`.
Never run `down --volumes` on `aig-production` as routine deployment cleanup.
