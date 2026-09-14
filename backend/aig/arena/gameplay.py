"""Versioned offline gameplay selection outside the source-frozen research API."""
from fastapi import APIRouter

from aig.arena.application import ArenaSession
from aig.arena.ai.controller import ArenaAiController
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.heuristic_v2 import HeuristicArenaTurnProviderV2


def create_offline_turn_provider(settings=None, provider_name="heuristic", **kwargs):
    """Injectable into simulate(provider_factory=...); no model construction."""
    if provider_name in (None, "heuristic", "heuristic-v1"):
        return HeuristicArenaTurnProvider()
    if provider_name == "heuristic-v2":
        return HeuristicArenaTurnProviderV2()
    raise ValueError("unknown offline Arena provider")


class ArenaGameplaySession(ArenaSession):
    """Keep orchestration frozen; label V2 only in the gameplay public response."""

    def demo(self, *, versus_ai=False, provider="heuristic"):
        with self._lock:
            if versus_ai and provider == "heuristic-v2":
                super().demo(versus_ai=True, provider="heuristic")
                self._ai_controller = ArenaAiController(create_offline_turn_provider(provider_name=provider))
                self._offline_version = provider
            else:
                super().demo(versus_ai=versus_ai, provider="heuristic" if provider == "heuristic-v1" else provider)
                self._offline_version = None
            return self._public_state()

    def _public_state(self):
        result = super()._public_state()
        if getattr(self, "_offline_version", None) == "heuristic-v2":
            result["controllers"] = {p: "heuristic-v2_ai" if c == "heuristic_ai" else c
                                     for p, c in result["controllers"].items()}
        return result


def offline_gameplay_router(session):
    """Register before the frozen generic /demo-ai/{provider} route in web host."""
    router = APIRouter(prefix="/api/arena")

    @router.post("/demo-ai/heuristic-v2")
    def demo_v2():
        return session.demo(versus_ai=True, provider="heuristic-v2")

    @router.post("/demo-ai/heuristic-v1")
    def demo_v1():
        return session.demo(versus_ai=True, provider="heuristic-v1")

    return router
