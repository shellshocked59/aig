"""Playable web host around the frozen API; no model calls at startup.

Run ``python -m aig.web`` after ``npm run build``, or use ``npm run dev``.
"""
from pathlib import Path

from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from aig.api import create_app as create_api_app
from aig.arena.api import arena_router
from aig.arena.application import ArenaSession
from aig.arena.battle_log import battle_log


class ArenaWebSession(ArenaSession):
    """Add browser presentation while retaining the session's locked execution."""

    def _public_state(self):
        result = super()._public_state()
        result["battle_log"] = battle_log(self._simulation.trace())
        result["terminal_reason"] = None
        if result["winner_player_id"] is not None:
            result["terminal_reason"] = ("Core destroyed" if any(c["hp"] == 0 for c in result["cores"])
                                         else "Team eliminated")
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
    app.include_router(arena_router(app.state.arena_session))
    dist = Path(__file__).resolve().parents[2] / "dist"

    @app.get("/")
    @app.get("/arena")
    @app.get("/arena/")
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
