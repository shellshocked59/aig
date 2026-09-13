"""Non-secret baseline inference profiles, independent of runtime hosts."""

from dataclasses import replace
from types import MappingProxyType
from urllib.parse import urlsplit, urlunsplit

from aig.versions import LATEST_LUNA_CONFIG_VERSION, LATEST_QWEN_CONFIG_VERSION, resolve_version


QWEN_CONFIGS = MappingProxyType({"qwen-config-v1": MappingProxyType(dict(
    model="hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M", context_size=4096,
    temperature=0.0, seed=42, max_output_tokens=256, think=False, stream=False,
))})
LUNA_CONFIGS = MappingProxyType({"luna-config-v1": MappingProxyType(dict(
    model="gpt-5.6-luna", reasoning_effort="none", max_output_tokens=512,
    store=False, max_retries=0,
))})


def public_ollama_configuration(config):
    """Runtime metadata, including endpoint but excluding URL credentials/query."""
    try:
        url = urlsplit(config.base_url)
        host = url.hostname or ""
        if ":" in host:
            host = f"[{host}]"
        if url.port is not None:
            host += f":{url.port}"
        endpoint = urlunsplit((url.scheme, host, url.path, "", ""))
    except ValueError:
        endpoint = None
    return dict(model=config.model, context_size=config.context_size,
                temperature=config.temperature, seed=config.seed,
                max_output_tokens=config.max_output_tokens, think=config.think, stream=config.stream,
                base_url=endpoint, timeout_seconds=config.timeout_seconds, keep_alive=config.keep_alive)


def resolve_model_profile(provider, requested=None):
    if provider == "ollama":
        available, latest = QWEN_CONFIGS, LATEST_QWEN_CONFIG_VERSION
    elif provider == "openai":
        available, latest = LUNA_CONFIGS, LATEST_LUNA_CONFIG_VERSION
    else:
        raise ValueError(f"no model profile for provider {provider!r}")
    version = resolve_version(requested, available=available, latest=latest)
    return version, dict(available[version])


def inference_configuration(provider, settings):
    """Explicit allowlists: never serialize complete secret-bearing settings."""
    if provider == "ollama":
        config = settings.ollama
        return dict(model=config.model, context_size=config.context_size,
                    temperature=config.temperature, seed=config.seed,
                    max_output_tokens=config.max_output_tokens, think=config.think, stream=config.stream)
    if provider == "openai":
        config = settings.openai
        return dict(model=config.model, reasoning_effort=config.reasoning_effort,
                    max_output_tokens=config.max_output_tokens, store=False, max_retries=0)
    if provider == "heuristic":
        return None
    raise ValueError(f"unknown provider: {provider}")


def apply_model_profile(settings, provider, requested=None):
    """Explicit benchmark selection pins inference values, retaining operations/secrets."""
    _, values = resolve_model_profile(provider, requested)
    # These are fixed provider protocol settings, not runtime tuning fields.
    values = {k: v for k, v in values.items() if k not in ("store", "max_retries")}
    return replace(settings, **{provider: replace(getattr(settings, provider), **values)})
