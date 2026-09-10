"""Read-only production API, CORS, and database checks, run inside the API image."""

import json
import os
from urllib.request import Request, urlopen

import psycopg
import redis


origin = os.environ["AIG_HTTP_CORS_ORIGINS"].split(",")[0].strip()
with urlopen(Request("http://127.0.0.1:8000/api/health", headers={"Origin": origin}), timeout=5) as response:
    assert json.load(response) == {"status": "ok"}
    assert response.headers["X-AIG-Revision"] == os.environ["AIG_RELEASE_SHA"]
    assert response.headers["Access-Control-Allow-Origin"] == origin
with urlopen(Request("http://127.0.0.1:8000/api/game/commands", method="OPTIONS", headers={
    "Origin": origin, "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}), timeout=5) as response:
    assert response.status == 200
    assert response.headers["Access-Control-Allow-Origin"] == origin
with psycopg.connect(connect_timeout=5) as connection:
    assert connection.execute("SELECT 1").fetchone() == (1,)
with redis.Redis.from_url(os.environ["REDIS_URL"], socket_connect_timeout=5, socket_timeout=5) as client:
    assert client.ping()
print("Production API, CORS, PostgreSQL, and Redis passed.")
