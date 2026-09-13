"""Independent experiment domains and their explicit latest pointers."""

from collections.abc import Mapping
from types import MappingProxyType


LATEST_ENVIRONMENT_VERSION = "environment-v5"
RUNTIME_ENVIRONMENT_VERSION = "environment-v5"
LATEST_SCENARIO_VERSION = "scenario-v4"
LATEST_STRATEGY_PROMPT_VERSION = "strategy-prompt-v1"
LATEST_PLAN_SCHEMA_VERSION = "strategic-plan-schema-v1"
LATEST_QWEN_CONFIG_VERSION = "qwen-config-v1"
LATEST_LUNA_CONFIG_VERSION = "luna-config-v1"
LATEST_BENCHMARK_VERSION = "benchmark-v1"


def resolve_version(requested=None, *, available: Mapping, latest: str) -> str:
    """Return a registered concrete ID; accept short vN and qualified IDs.

    The domain comes from the explicit latest pointer, never a filename.
    Registries contain immutable historical payloads; moving latest changes
    only the default selection, not explicit historical selections.
    """
    if latest not in available:
        raise ValueError(f"latest version {latest!r} is not registered")
    domain = latest.rsplit("-v", 1)[0]
    selected = latest if requested in (None, "", "latest") else requested
    if (isinstance(selected, str) and selected not in available
            and selected.startswith("v") and "-v" in latest):
        selected = f"{domain}-{selected}"
    if not isinstance(selected, str) or selected not in available:
        raise ValueError(f"unknown {domain} version {requested!r}; available: {', '.join(available)}")
    return selected


# Environment IDs describe information/rules, not runtime engine dispatch.
ENVIRONMENTS = MappingProxyType({
    "environment-v5": "Environment V4 plus permanent total war, melee city capture, historical zero-city elimination and conquest victory.",
    "environment-v4": "Environment V3 plus discoverable barbarian camps, local deterministic Warriors, bounded spawning and camp gold rewards.",
    "environment-v3": "Environment V2 fog and exploration plus static discoverable map resources and additive worked-tile yields.",
    "environment-v2": "Fog of war, persistent exploration and knowledge-safe planning; Chebyshev sight without LOS blocking.",
    "environment-v1": "Original deterministic full-information environment; no fog of war.",
})
BENCHMARKS = MappingProxyType({"benchmark-v1": "Paired same-state all-faction benchmark report"})
