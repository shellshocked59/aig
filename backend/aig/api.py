"""Thin local HTTP boundary. Run with uvicorn aig.api:create_app --factory."""

import logging
from typing import Annotated, Literal

from fastapi import Body, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictInt

from aig.application import ApplicationError, GameSession
from aig.commands import AttackUnit, EndActivation, MoveUnit, SetCityProduction, SetResearch
from aig.settings import load_settings
from aig.state import Position, Technology, UnitType

logger = logging.getLogger(__name__)


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MovePayload(Payload):
    type: Literal["move_unit"]
    unitId: str
    x: StrictInt
    y: StrictInt


class AttackPayload(Payload):
    type: Literal["attack_unit"]
    attackerUnitId: str
    targetUnitId: str


class FoundPayload(Payload):
    type: Literal["found_city"]
    settlerUnitId: str
    name: str


class ProductionPayload(Payload):
    type: Literal["set_city_production"]
    cityId: str
    unitType: UnitType | None


class ResearchPayload(Payload):
    type: Literal["set_research"]
    technology: Technology | None


class EndPayload(Payload):
    type: Literal["end_activation"]


CommandPayload = Annotated[
    MovePayload | AttackPayload | FoundPayload | ProductionPayload | ResearchPayload | EndPayload,
    Body(discriminator="type"),
]


def create_app() -> FastAPI:
    # Loading settings is explicit at startup, never in the engine or on requests.
    app = FastAPI(title="Aether, Iron & Glory", docs_url=None, redoc_url=None)
    app.state.settings = load_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app.state.settings.http.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    session = GameSession(app.state.settings.ai, ollama_settings=app.state.settings.ollama)
    app.state.session = session

    @app.exception_handler(ApplicationError)
    async def application_error(request: Request, exc: ApplicationError):
        status = {"no_game": 404, "invalid_state": 409, "invalid_command": 422}[exc.code]
        return JSONResponse(status_code=status, content={"error": exc.code, "message": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        issues = [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        return JSONResponse(status_code=422, content={
            "error": "invalid_request", "message": "; ".join(issues),
        })

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("Unexpected application error", exc_info=exc)
        return JSONResponse(status_code=500, content={
            "error": "server_error", "message": "Unexpected server error. See the backend log.",
        })

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/game")
    def get_game():
        return session.current()

    @app.post("/api/game/demo")
    def create_demo():
        return session.demo()

    @app.post("/api/game/demo/ai")
    def create_ai_demo():
        return session.demo(versus_ai=True)

    @app.post("/api/game/demo/llm")
    def create_llm_demo():
        return session.demo(versus_ai=True, provider="ollama")

    @app.post("/api/game/start")
    def start():
        return session.start()

    @app.post("/api/game/commands")
    def command(payload: CommandPayload):
        if isinstance(payload, MovePayload):
            return session.execute(lambda actor: MoveUnit(actor, payload.unitId, Position(payload.x, payload.y)))
        if isinstance(payload, AttackPayload):
            return session.execute(lambda actor: AttackUnit(actor, payload.attackerUnitId, payload.targetUnitId))
        if isinstance(payload, FoundPayload):
            return session.found_city(payload.settlerUnitId, payload.name)
        if isinstance(payload, ProductionPayload):
            return session.execute(lambda actor: SetCityProduction(actor, payload.cityId, payload.unitType))
        if isinstance(payload, ResearchPayload):
            return session.execute(lambda actor: SetResearch(actor, payload.technology))
        return session.execute(EndActivation)

    return app
