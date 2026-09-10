"""Verify public HTTPS routing and the frontend release, without changing a game."""

import argparse
import json
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("revision")
args = parser.parse_args()
frontend = "https://www.agentstrategy.online"
api = "https://api.agentstrategy.online"

with urlopen(frontend + "/release.json?revision=" + args.revision, timeout=20) as response:
    assert json.load(response)["revision"] == args.revision, "Public frontend is serving a different release"
with urlopen(frontend + "/", timeout=20) as response:
    assert b"Aether, Iron &amp; Glory" in response.read(), "Unexpected frontend page"
for asset in ("/assets/main.js", "/assets/main.css"):
    with urlopen(frontend + asset + "?revision=" + args.revision, timeout=20) as response:
        assert response.status == 200 and response.read(), "Missing frontend asset"
with urlopen(Request(api + "/api/health", headers={"Origin": frontend}), timeout=20) as response:
    assert json.load(response) == {"status": "ok"}
    assert response.headers["X-AIG-Revision"] == args.revision, "Public API is serving a different release"
    assert response.headers["Access-Control-Allow-Origin"] == frontend, "Incorrect production CORS origin"
with urlopen(Request(api + "/api/game/commands", method="OPTIONS", headers={
    "Origin": frontend, "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}), timeout=20) as response:
    assert response.status == 200
    assert response.headers["Access-Control-Allow-Origin"] == frontend
print("Public frontend release, assets, API health, and CORS passed.")
