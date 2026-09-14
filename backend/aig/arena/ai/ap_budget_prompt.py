"""Immutable AP-only V1 descendant; explicit experimental selection only."""
from hashlib import sha256
from types import MappingProxyType
from aig.arena.ai.prompts import SYSTEM_PROMPT, PROMPT_VERSION as DEFAULT_VERSION
from aig.arena.ai.sequential_prompt import PROMPTS as HISTORICAL_PROMPTS
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.bounded_replan import ArenaBoundedReplanController

PROMPT_VERSION = 'arena-turn-prompt-v5'
ORIGINAL_AP = 'You have up to 5 shared Action Points, bounded by action_points_remaining.'
AP_GUIDANCE = """The observation's action_points_remaining is the complete AP budget for this plan.
Keep a running total of action costs. Before adding each action, ensure its cost
fits within the AP still remaining. The total cost of all planned actions MUST NOT
exceed this budget. You may return a shorter plan if no worthwhile legal action
fits the remaining AP."""
PROMPT = SYSTEM_PROMPT.replace(ORIGINAL_AP, AP_GUIDANCE)
PROMPTS = MappingProxyType({**HISTORICAL_PROMPTS, PROMPT_VERSION: PROMPT})
PROMPT_HASHES = MappingProxyType({v: sha256(p.encode()).hexdigest() for v, p in PROMPTS.items()})


def resolve_prompt(version=None):
    version = DEFAULT_VERSION if version in (None, 'latest') else version
    if version not in PROMPTS:
        raise ValueError('unknown experimental Arena prompt')
    return version, PROMPTS[version]


class OpenAIAPBudgetProvider(OpenAIArenaTurnProvider):
    resolve_prompt = staticmethod(resolve_prompt)


class OllamaAPBudgetProvider(OllamaArenaTurnProvider):
    resolve_prompt = staticmethod(resolve_prompt)


class APBudgetBoundedReplanController(ArenaBoundedReplanController):
    """Only explicit construction differs; frozen control semantics are inherited."""
    def __init__(self, provider, *, fallback=False):
        resolve_prompt(provider.prompt_version)
        self.provider = provider
        self.fallback = fallback
