"""Application settings: non-empty process environment > local .env > defaults.

Call load_settings() at the application boundary and pass its immutable result
to consumers. Importing this module performs no file or environment loading.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
import math
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit


StrategyProviderName = Literal["heuristic", "ollama", "openai"]


@dataclass(frozen=True)
class OllamaSettings:
    """Committed development defaults for local strategic planning."""

    base_url: str = "http://10.0.0.250:11434"
    model: str = "hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M"
    context_size: int = 4096
    temperature: float = 0.0
    seed: int = 42
    max_output_tokens: int = 256
    keep_alive: str = "10m"
    think: bool = False
    stream: bool = False
    timeout_seconds: float = 20.0

    def __post_init__(self) -> None:
        if (isinstance(self.timeout_seconds, bool)
                or not isinstance(self.timeout_seconds, (int, float))
                or not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0):
            raise ValueError("AIG_OLLAMA_TIMEOUT_SECONDS must be a finite positive number")


@dataclass(frozen=True)
class OpenAISettings:
    """Optional backend credentials and defaults for cloud strategic planning.

    Never serialize this object with asdict()/vars(): repr=False only protects
    representations. Traces must explicitly allowlist non-secret fields.
    Configuring a key does not select a provider or require network access.
    """

    api_key: str | None = field(default=None, repr=False)
    model: str = "gpt-5.6-luna"
    timeout_seconds: float = 20.0
    max_output_tokens: int = 512
    reasoning_effort: str = "none"

    def __post_init__(self) -> None:
        if self.api_key == "":
            object.__setattr__(self, "api_key", None)
        if self.api_key is not None and (
                not isinstance(self.api_key, str) or not self.api_key.strip()):
            raise ValueError("OPENAI_API_KEY must be a nonblank string when set")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("AIG_OPENAI_MODEL must be a nonblank string")
        if (isinstance(self.timeout_seconds, bool)
                or not isinstance(self.timeout_seconds, (int, float))
                or not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0):
            raise ValueError("AIG_OPENAI_TIMEOUT_SECONDS must be a finite positive number")
        if type(self.max_output_tokens) is not int or self.max_output_tokens <= 0:
            raise ValueError("AIG_OPENAI_MAX_OUTPUT_TOKENS must be a positive integer")
        if self.reasoning_effort not in ("none", "low", "medium", "high", "xhigh", "max"):
            raise ValueError("AIG_OPENAI_REASONING_EFFORT must be none, low, medium, high, xhigh, or max")


@dataclass(frozen=True)
class AiSettings:
    replan_interval: int = 5
    max_actions: int = 256
    strategy_provider: StrategyProviderName = "heuristic"
    strategy_prompt_version: str = "latest"

    def __post_init__(self) -> None:
        if self.strategy_provider not in ("heuristic", "ollama", "openai"):
            raise ValueError("AIG_STRATEGY_PROVIDER must be heuristic, ollama, or openai")
        for name in ("replan_interval", "max_actions"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"AIG_AI_{name.upper()} must be a positive integer")


@dataclass(frozen=True)
class HttpSettings:
    cors_origins: str = "http://aig.localhost"

    def __post_init__(self) -> None:
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                    or parsed.path or parsed.query or parsed.fragment
                    or parsed.username is not None or parsed.password is not None
                    or any(character.isspace() for character in origin)
                    or "*" in origin):
                raise ValueError("AIG_HTTP_CORS_ORIGINS must list explicit HTTP(S) origins without paths")

    @property
    def allowed_origins(self) -> tuple[str, ...]:
        return tuple(origin.strip() for origin in self.cors_origins.split(","))


@dataclass(frozen=True)
class Settings:
    ollama: OllamaSettings = OllamaSettings()
    ai: AiSettings = AiSettings()
    http: HttpSettings = HttpSettings()
    openai: OpenAISettings = OpenAISettings()


_SETTING_GROUPS = (("ollama", OllamaSettings), ("ai", AiSettings),
                   ("http", HttpSettings), ("openai", OpenAISettings))


def _environment_name(group: str, field_name: str) -> str:
    if group == "ai" and field_name in ("strategy_provider", "strategy_prompt_version"):
        return f"AIG_{field_name.upper()}"
    # Deliberate exception: there is no AIG_OPENAI_API_KEY alias.
    if group == "openai" and field_name == "api_key":
        return "OPENAI_API_KEY"
    return f"AIG_{group.upper()}_{field_name.upper()}"


# Relative to this checkout, never to the shell's current working directory.
DEFAULT_LOCAL_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_settings(
    *,
    local_file: Path | None = DEFAULT_LOCAL_FILE,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Read fresh settings without mutating os.environ or caching results.

    A missing local file is normal; None disables local loading. An explicit
    environment mapping replaces os.environ (use {} for isolated defaults).
    Malformed effective values raise ValueError naming the setting.
    """
    environment = os.environ if environ is None else environ
    local = {} if local_file is None else _read_local_file(local_file)
    groups = {}
    for group, kind in _SETTING_GROUPS:
        defaults = kind()
        values = {}
        for field in fields(defaults):
            name = _environment_name(group, field.name)
            default = getattr(defaults, field.name)
            raw = environment.get(name) or local.get(name)
            if name == "AIG_STRATEGY_PROMPT_VERSION" and raw == "":
                raw = None
            if name == "OPENAI_API_KEY" and raw == "":
                raw = None
            values[field.name] = default if raw is None else _parse_value(name, raw, default)
        groups[group] = kind(**values)
    return Settings(**groups)


def _read_local_file(path: Path) -> dict[str, str]:
    try:
        contents = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {}

    known = {_environment_name(group, field.name)
             for group, kind in _SETTING_GROUPS for field in fields(kind)}
    values = {}
    for number, raw_line in enumerate(contents.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ValueError(f"{path}:{number}: expected NAME=value")
        if key not in known:
            if key.startswith("AIG_"):
                raise ValueError(f"{path}:{number}: unknown setting {key}")
            continue
        value = value.strip()
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"{path}:{number}: unmatched quote for {key}")
            value = value[1:-1]
        values[key] = value
    return values


def _parse_value(
    name: str, raw: str, default: str | int | float | bool | None,
) -> str | int | float | bool:
    if isinstance(default, bool):
        value = raw.strip().lower()
        if value in {"true", "1", "yes", "on"}:
            return True
        if value in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"{name} must be true/false, 1/0, yes/no, or on/off")
    if isinstance(default, int):
        try:
            value = int(raw)
        except ValueError as error:
            raise ValueError(f"{name} must be an integer") from error
        if name in {"AIG_OLLAMA_CONTEXT_SIZE", "AIG_OLLAMA_MAX_OUTPUT_TOKENS"} and value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return value
    if isinstance(default, float):
        try:
            value = float(raw)
        except ValueError as error:
            raise ValueError(f"{name} must be a finite nonnegative number") from error
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite nonnegative number")
        return value
    if not raw.strip():
        raise ValueError(f"{name} must be a nonblank string")
    return raw
