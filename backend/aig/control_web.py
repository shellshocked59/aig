"""Current gameplay host; source-frozen aig.web remains available for research."""
from copy import deepcopy
from typing import Literal

from fastapi import APIRouter
from aig.web import ArenaWebSession, create_app as frozen_create_app
from aig.arena.api import arena_router
from aig.arena.gameplay import offline_gameplay_router
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController
from aig.arena.ai.controller import ArenaAiTurnTrace, ArenaControllerType
from aig.arena.ai.stepwise import ArenaStepController, create_arena_step_provider
from aig.arena.control_settings import CONTROL_VERSIONS, load_control_settings

ControlMode = Literal['full_turn', 'bounded_replan', 'stepwise']


class GameplayStepController:
    """Adapt only the trace container; frozen step execution/failure policy is intact."""
    def __init__(self, provider):
        self.controller = ArenaStepController(provider)

    def run_turn(self, simulation):
        return ArenaAiTurnTrace(self.controller.run_turn(simulation))


def public_trace(value):
    """Recursive removal covers nested waves and stepwise transport records."""
    if isinstance(value, dict):
        return {k: public_trace(v) for k, v in value.items()
                if k not in ('attempts', 'raw_content', 'rejected_decision', 'observation')}
    if isinstance(value, list):
        return [public_trace(v) for v in value]
    return deepcopy(value)


class ArenaControlWebSession(ArenaWebSession):
    def __init__(self, settings=None, *, control_settings=None):
        super().__init__(settings)
        self.control_settings = control_settings or load_control_settings()
        self.control_mode = self.control_settings.mode

    def demo(self, *, versus_ai=False, provider='heuristic', control_mode=None):
        mode = control_mode or self.control_settings.mode
        if mode not in CONTROL_VERSIONS:
            raise ValueError('unknown Arena control mode')
        with self._lock:
            # Construction only: superclass never requests a plan during demo.
            super().demo(versus_ai=versus_ai, provider=provider)
            if versus_ai and mode == 'bounded_replan':
                self._ai_controller = ArenaBoundedReplanController(self._ai_controller.provider)
            elif versus_ai and mode == 'stepwise':
                name = self._settings.ai.arena_turn_provider if provider == 'configured' else provider
                if name in ('heuristic-v1', 'heuristic-v2'):
                    name = 'heuristic'
                self._ai_controller = GameplayStepController(create_arena_step_provider(self._settings, name))
            self.control_mode = mode
            return self._public_state()

    def observer_demo(self, control_mode: ControlMode | None = None):
        with self._lock:
            self.demo(versus_ai=True, provider='openai', control_mode=control_mode)
            self._controllers = {p.id: ArenaControllerType.OPENAI_AI for p in self._simulation.state.players}
            return self._public_state()

    def _public_state(self):
        result = super()._public_state()
        result.update(control_mode=self.control_mode, control_version=CONTROL_VERSIONS[self.control_mode])
        result['ai_turns'] = [public_trace(t) for t in result['ai_turns']]
        return result


def create_app():
    app = frozen_create_app()
    app.router.routes[:] = [route for route in app.router.routes
        if not (getattr(route, 'path', '').startswith('/api/arena')
                or getattr(getattr(route, 'original_router', None), 'prefix', '').startswith('/api/arena'))]
    session = app.state.arena_session = ArenaControlWebSession(app.state.settings)
    router = APIRouter(prefix='/api/arena')

    @router.post('/demo-ai/{provider}')
    def demo_ai(provider: Literal['heuristic', 'heuristic-v1', 'heuristic-v2', 'openai', 'ollama', 'configured'],
                control_mode: ControlMode | None = None):
        return session.demo(versus_ai=True, provider=provider, control_mode=control_mode)

    router.add_api_route('/observer/demo', session.observer_demo, methods=['POST'])
    router.add_api_route('/observer/turn', session.observer_turn, methods=['POST'])
    # Before the existing static mount and frozen generic routes.
    existing = list(app.router.routes)
    app.router.routes.clear()
    app.include_router(router)
    app.include_router(offline_gameplay_router(session))
    app.include_router(arena_router(session))
    app.router.routes.extend(existing)
    return app
