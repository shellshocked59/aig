"""Playable web host around the frozen API; no model calls at startup.

Run ``python -m aig.web`` after ``npm run build``, or use ``npm run dev``.
"""
from pathlib import Path

from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from aig.api import create_app as create_api_app
from aig.arena.api import arena_router
from aig.arena.gameplay import ArenaGameplaySession, offline_gameplay_router
from aig.arena.presentation import PresentationSimulation, VERSION, terminal_reason
from aig.arena.snapshots import state_hash


class ArenaWebSession(ArenaGameplaySession):
    """Add browser presentation while retaining the session's locked execution."""

    def demo(self, **kwargs):
        with self._lock:
            super().demo(**kwargs)
            self._simulation = PresentationSimulation(self._simulation)
            return self._public_state()

    def execute(self, command):
        with self._lock:
            simulation = self._require_game()
            if not isinstance(simulation, PresentationSimulation):
                self._simulation = simulation = PresentationSimulation(simulation)
            start = state_hash(simulation.state)
            offset = len(simulation.presentation_events)
            result = super().execute(command)
            result["presentation"] = dict(version=VERSION, start_state_hash=start,
                final_state_hash=state_hash(simulation.state), events=simulation.presentation_events[offset:])
            return result

    def _public_state(self):
        result = super()._public_state()
        events = getattr(self._simulation, "presentation_events", [])
        result["battle_log"] = [e["log"] for e in events[-60:]]
        result["terminal_reason"] = terminal_reason(self._simulation.state)
        result["state_hash"] = state_hash(self._simulation.state)
        return result


def create_app():
    app = create_api_app()
    # Keep Empire, error handlers, health, and all Arena payload/route contracts.
    # Replace only the Arena session with the presentation subclass. The original
    # API factory remains byte-for-byte frozen for research and API-only hosting.
    app.router.routes[:] = [route for route in app.router.routes
                            if not (getattr(route, "path", "").startswith("/api/arena")
                                    or getattr(getattr(route, "original_router", None), "prefix", "") == "/api/arena")]
    app.state.arena_session = ArenaWebSession(app.state.settings)
    app.include_router(offline_gameplay_router(app.state.arena_session))
    app.include_router(arena_router(app.state.arena_session))
    dist = Path(__file__).resolve().parents[2] / "dist"

    @app.get("/")
    @app.get("/arena")
    @app.get("/arena/")
    @app.get("/arena/presentation-lab")
    @app.get("/empire")
    @app.get("/empire/")
    def game_page():
        if not (dist / "index.html").is_file():
            return JSONResponse(status_code=503, content={"error": "frontend_missing",
                "message": "Frontend assets are missing. Run npm run build, or use npm run dev for local preview."})
        return FileResponse(dist / "index.html", headers={"Cache-Control": "no-store"})

    app.mount("/assets", StaticFiles(directory=dist / "assets", check_dir=False), name="assets")
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("aig.web:create_app", factory=True, host="127.0.0.1", port=8000)
