"""Application-boundary provider selection, independent of Empire settings."""

from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider

PROVIDER_NAMES = ("heuristic", "ollama", "openai")


def create_arena_turn_provider(settings, provider_name=None, **kwargs):
    name = settings.ai.arena_turn_provider if provider_name is None else provider_name
    if name == "heuristic":
        return HeuristicArenaTurnProvider()
    if name not in PROVIDER_NAMES:
        raise ValueError("unknown Arena turn provider")
    kind = OllamaArenaTurnProvider if name == "ollama" else OpenAIArenaTurnProvider
    return kind(getattr(settings, name), secrets=(settings.openai.api_key,), **kwargs)
