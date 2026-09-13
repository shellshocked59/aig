"""Independent locked Arena session with synchronous, ephemeral AI orchestration."""

from threading import RLock

from aig.application import ApplicationError
from aig.arena.public_state import public_state
from aig.arena.replay import ArenaSimulation
from aig.arena.ai.controller import ArenaAiController, ArenaControllerType, advance_until_human, controller_setup
from aig.arena.ai.factory import create_arena_turn_provider
from aig.settings import Settings


class ArenaSession:
    def __init__(self, settings=None):
        self._simulation = None
        self._lock = RLock()
        self._controllers = {}
        self._ai_traces = ()
        self._settings = settings if settings is not None else Settings()
        self._ai_controller = None

    def _require_game(self):
        if self._simulation is None:
            raise ApplicationError("no_game", "Create an Arena Demo first.")
        return self._simulation

    def _public_state(self):
        result = public_state(self._require_game().state)
        result["controllers"] = {p.id: self._controllers.get(p.id, ArenaControllerType.HUMAN).value
                                 for p in self._simulation.state.players}
        result["ai_turns"] = [t.to_dict() for t in self._ai_traces]
        # The public response exposes action/provenance summaries, not raw model text.
        for trace in result["ai_turns"]:
            if "inference" in trace:
                trace["inference"] = {k: v for k, v in trace["inference"].items() if k != "attempts"}
        return result

    def demo(self, *, versus_ai=False, provider="heuristic"):
        with self._lock:
            name = self._settings.ai.arena_turn_provider if provider == "configured" else provider
            ai = ArenaAiController(create_arena_turn_provider(self._settings, name)) if versus_ai else None
            self._simulation = ArenaSimulation()
            self._controllers = controller_setup(self._simulation.state, "human_vs_" + name if versus_ai else "manual")
            self._ai_controller = ai
            self._ai_traces = ()
            return self._public_state()

    def current(self):
        with self._lock:
            return self._public_state()

    def execute(self, command):
        with self._lock:
            simulation = self._require_game()
            if self._controllers.get(simulation.state.active_player_id, ArenaControllerType.HUMAN) is not ArenaControllerType.HUMAN:
                raise ApplicationError("invalid_command", "The active Arena player is controlled by AI.")
            try:
                simulation.execute(command)
            except ValueError as error:
                raise ApplicationError("invalid_command", str(error)) from error
            controllers = self._controllers or controller_setup(simulation.state)
            self._ai_traces = advance_until_human(simulation, controllers, controller=self._ai_controller)
            return self._public_state()

    def trace(self):
        with self._lock:
            return self._require_game().trace()
