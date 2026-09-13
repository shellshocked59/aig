"""Benchmark-only validation and safe diagnostics; no gameplay fallback policy."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import socket
from time import perf_counter
from urllib.error import URLError

from aig.ai.benchmark_metrics import FAILURE_CATEGORIES
from aig.ai.plan_schema import canonical_json, parse_plan
from aig.ai.strategy import StrategicPlan, StrategyProviderError


@dataclass
class ProviderPreflightResult:
    requested_provider: str
    actual_provider: str | None = None
    success: bool = False
    model: str | None = None
    duration_seconds: float = 0.0
    error_category: str | None = None
    sanitized_error: str | None = None
    retry_count: int = 0
    fallback_used: bool = False
    plan_valid: bool = False
    requests: int = 0
    usage: list[dict] = field(default_factory=list)


def failure_category(error, trace):
    if isinstance(error, ValueError):
        return getattr(error, "category", "schema_validation")
    categories = [a.get("error_category") for a in trace.get("attempts", [])]
    category = trace.get("error_category") or next((c for c in reversed(categories) if c), None)
    if category in (*FAILURE_CATEGORIES, "dns_failure", "provider_exception", "provider_mismatch"):
        return category
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, socket.gaierror):
        return "dns_failure"
    if isinstance(reason, TimeoutError):
        return "timeout"
    if isinstance(reason, (ConnectionError, OSError)) or isinstance(error, URLError):
        return "connection_failure"
    return "provider_exception"


class CheckedProvider:
    """Keep provider calls normal; validate provenance before the controller executes.

    Unexpected provider exceptions are diagnostic failures, never serialized reprs.
    The gameplay controller still creates its usual fallback on a sanitized error.
    """

    def __init__(self, provider, name, schema_version):
        self.provider, self.name, self.schema_version = provider, name, schema_version
        self.last_trace = None

    def create_plan(self, state, previous_plan=None):
        self.last_trace = {}
        try:
            plan = self.provider.create_plan(state, previous_plan)
            self.last_trace = deepcopy(getattr(self.provider, "last_trace", None)) or {}
            if not isinstance(plan, StrategicPlan):
                raise ValueError("provider must return a StrategicPlan")
            parse_plan(canonical_json(plan.to_dict()), state, self.schema_version)
            self.last_trace["plan_valid"] = True
            if (self.last_trace.get("fallback_used")
                    or self.last_trace.get("actual_provider", getattr(self.provider, "name", None)) != self.name
                    or getattr(self.provider, "name", None) != self.name):
                self.last_trace["error_category"] = "provider_mismatch"
                raise StrategyProviderError("Provider provenance mismatch")
            return plan
        except Exception as caught:
            if not self.last_trace:
                self.last_trace = deepcopy(getattr(self.provider, "last_trace", None)) or {}
            category = failure_category(caught, self.last_trace)
            self.last_trace.update(error_category=category, error=f"Provider failed ({category}).")
            raise StrategyProviderError(self.last_trace["error"]) from None
        finally:
            self.last_trace = safe_trace(self.last_trace, self.provider)


def safe_trace(trace, provider):
    """Keep telemetry, redact credential echoes, replace free-form error messages."""
    key = getattr(getattr(provider, "settings", None), "api_key", None)

    def clean(value):
        if isinstance(value, dict):
            return {k: ("Provider attempt failed." if k == "error" else clean(v))
                    for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, str) and isinstance(key, str) and key:
            return value.replace(key, "[REDACTED]")
        return value
    return clean(trace)


def preflight(provider, name, state, manifest):
    """One normal planning call, with repair disabled for the one-request budget."""
    result = ProviderPreflightResult(name, model=manifest["model"])
    checked = CheckedProvider(provider, name, manifest["strategicPlanSchemaVersion"])
    repair = getattr(provider, "_repair", None)
    if repair is not None:
        provider._repair = False
    started = perf_counter()
    try:
        checked.create_plan(state)
        result.success = result.plan_valid = True
        result.actual_provider = name
    except StrategyProviderError as error:
        trace = checked.last_trace or {}
        result.error_category = failure_category(error, trace)
        result.sanitized_error = f"Provider failed ({result.error_category})."
        result.fallback_used = bool(trace.get("fallback_used"))
        result.plan_valid = bool(trace.get("plan_valid"))
        result.actual_provider = trace.get("actual_provider")
        if result.actual_provider not in ("heuristic", "ollama", "openai"):
            result.actual_provider = None
    finally:
        if repair is not None:
            provider._repair = repair
    trace = checked.last_trace or {}
    result.duration_seconds = perf_counter() - started
    result.retry_count = trace.get("retry_count", 0)
    result.requests = len(trace.get("attempts", []))
    keys = ("prompt_eval_count", "eval_count", "prompt_eval_duration", "eval_duration", "total_duration",
            "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")
    result.usage = [{k: v for k, v in a.get("metrics", {}).items()
                     if k in keys and type(v) is int and v >= 0} for a in trace.get("attempts", [])]
    return asdict(result)
