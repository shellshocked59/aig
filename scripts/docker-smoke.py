"""Read-only stack check: docker compose exec -T api python scripts/docker-smoke.py."""

import json
import os
from urllib.error import HTTPError
from urllib.request import urlopen

import psycopg
import redis


def main():
    base = "http://web:5173"
    with urlopen(base + "/", timeout=10) as response:
        assert b"Aether, Iron &amp; Glory" in response.read()
    for asset in ("/assets/main.js", "/assets/main.css"):
        with urlopen(base + asset, timeout=10) as response:
            assert response.status == 200 and response.read()
    with urlopen(base + "/api/health", timeout=10) as response:
        assert json.load(response) == {"status": "ok"}
    # A fresh process has no game. Also allow an already-running match, without
    # creating/resetting one when a developer checks their stack.
    try:
        with urlopen(base + "/api/game", timeout=10) as response:
            assert "game" in json.load(response)
    except HTTPError as error:
        with error:
            assert error.code == 404 and json.load(error)["error"] == "no_game"
    # libpq reads PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD from Compose.
    with psycopg.connect(connect_timeout=5) as connection:
        assert connection.execute("SELECT 1").fetchone() == (1,)
    with redis.Redis.from_url(
        os.environ["REDIS_URL"], socket_connect_timeout=5, socket_timeout=5
    ) as client:
        assert client.ping()
    print("Frontend, API proxy, PostgreSQL, and Redis are reachable.")


if __name__ == "__main__":
    main()
