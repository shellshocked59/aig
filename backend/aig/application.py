"""One in-memory game. Orchestration only; the engine owns every rule."""

from collections.abc import Callable
from threading import RLock

from aig.ai import AiOrchestrator, StrategyProvider
from aig.commands import Command, FoundCity, apply_command
from aig.public_state import public_state
from aig.scenarios import demo_game_setup, human_vs_ai_demo_setup
from aig.settings import AiSettings
from aig.setup import create_game, start_game
from aig.state import ControllerType, GameState


class ApplicationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class GameSession:
    """Serialize reads, reset, start, ID allocation and commands under one lock.

    Each response is detached while the lock is held. A failed engine command
    relies on engine atomicity and never advances the application city counter.
    The counter and game reset together; there is no loading/replay API.
    """

    def __init__(self, ai_settings: AiSettings = AiSettings(),
                 strategy_provider: StrategyProvider | None = None) -> None:
        self._state: GameState | None = None
        self._next_city_id = 1
        self._lock = RLock()
        self._ai_settings = ai_settings
        self._strategy_provider = strategy_provider
        self._reset_ai()

    def _reset_ai(self) -> None:
        self.ai = AiOrchestrator(self._strategy_provider,
                                 replan_interval=self._ai_settings.replan_interval,
                                 max_actions=self._ai_settings.max_actions)

    def _public_state(self) -> dict:
        result = public_state(self._require_game())
        if self.ai.latest_results:
            result["aiActivations"] = [r.to_dict() for r in self.ai.latest_results]
        return result

    def _require_game(self) -> GameState:
        if self._state is None:
            raise ApplicationError("no_game", "Create a New Demo Game first.")
        return self._state

    def current(self) -> dict:
        with self._lock:
            return self._public_state()

    def demo(self, *, versus_ai: bool = False) -> dict:
        with self._lock:
            self._state = create_game(human_vs_ai_demo_setup() if versus_ai else demo_game_setup())
            self._next_city_id = 1
            self._reset_ai()
            return self._public_state()

    def start(self) -> dict:
        with self._lock:
            state = self._require_game()
            try:
                start_game(state)
            except ValueError as exc:
                raise ApplicationError("invalid_state", str(exc)) from exc
            self.ai.advance_until_human(state)
            return self._public_state()

    def execute(self, make_command: Callable[[str], Command]) -> dict:
        with self._lock:
            state = self._require_game()
            if state.active_player_id is None:
                raise ApplicationError("invalid_command", "Start the game before issuing commands.")
            if state.active_controller is not ControllerType.HUMAN:
                raise ApplicationError("invalid_command", "The active faction is controlled by AI.")
            try:
                apply_command(state, make_command(state.active_player_id))
            except ValueError as exc:
                raise ApplicationError("invalid_command", str(exc)) from exc
            self.ai.advance_until_human(state)
            return self._public_state()

    def advance_until_human(self) -> dict:
        with self._lock:
            self.ai.advance_until_human(self._require_game())
            return self._public_state()

    def run_active_ai_activation(self):
        with self._lock:
            return self.ai.run_active_ai_activation(self._require_game())

    def found_city(self, settler_unit_id: str, name: str) -> dict:
        with self._lock:
            state = self._require_game()
            candidate = self._next_city_id
            while f"city-{candidate}" in state.cities:
                candidate += 1
            result = self.execute(lambda actor: FoundCity(
                actor, settler_unit_id, f"city-{candidate}", name,
            ))
            self._next_city_id = candidate + 1
            return result
