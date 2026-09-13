"""Environment-specific routes; Empire payloads never enter Arena rules."""

from fastapi import APIRouter

from aig.application import ApplicationError
from aig.arena.application import ArenaSession
from aig.arena.snapshots import command_from_dict


def arena_router(session: ArenaSession):
    router = APIRouter(prefix="/api/arena")

    @router.get("")
    def current():
        return session.current()

    @router.post("/demo")
    def demo():
        return session.demo()

    @router.post("/demo-ai")
    def demo_ai():
        return session.demo(versus_ai=True)

    @router.post("/demo-ai/{provider}")
    def demo_provider(provider: str):
        if provider not in ("heuristic", "ollama", "openai", "configured"):
            raise ApplicationError("invalid_command", "Unknown Arena provider.")
        return session.demo(versus_ai=True, provider=provider)

    @router.post("/commands")
    def command(payload: dict):
        try:
            request = command_from_dict(payload)
        except (ValueError, TypeError) as error:
            raise ApplicationError("invalid_command", str(error)) from error
        return session.execute(request)

    @router.get("/trace")
    def trace():
        return session.trace()

    return router
