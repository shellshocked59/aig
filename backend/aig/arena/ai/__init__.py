"""Arena tactical AI with an independent one-turn provider contract."""

from aig.arena.ai.contracts import ArenaTurnPlan, ArenaPlannedAction, PLAN_SCHEMA_VERSION
from aig.arena.ai.observation import ArenaObservation, build_observation
from aig.arena.ai.executor import ArenaTurnExecutionResult, execute_arena_turn
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.controller import ArenaAiController, ArenaTurnProvider, ArenaControllerType
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.factory import create_arena_turn_provider

__all__ = ["ArenaTurnPlan", "ArenaPlannedAction", "PLAN_SCHEMA_VERSION", "ArenaObservation",
           "build_observation", "ArenaTurnExecutionResult", "execute_arena_turn",
           "HeuristicArenaTurnProvider", "ArenaAiController", "ArenaTurnProvider", "ArenaControllerType",
           "OllamaArenaTurnProvider", "OpenAIArenaTurnProvider", "create_arena_turn_provider"]
