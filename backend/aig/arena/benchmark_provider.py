"""Strict Arena benchmark boundary. Never invokes gameplay fallback."""

from copy import deepcopy
from math import isfinite
from time import perf_counter

from aig.arena.ai.contracts import ArenaTurnPlan
from aig.arena.ai.heuristic import HEURISTIC_VERSION
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.snapshots import canonical_json

METRIC_KEYS = (
    "prompt_eval_count", "eval_count", "prompt_eval_duration", "eval_duration", "total_duration",
    "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens",
)
ERRORS = frozenset(("malformed_json", "schema_validation", "ap_budget", "invalid_reference",
                    "invalid_ability", "repair_failed", "authentication_failure", "timeout",
                    "connection_failure", "dns_failure", "malformed_envelope", "refusal",
                    "provider_mismatch", "provider_exception", "configuration_failure",
                    "rate_limit", "server_error", "context_limit"))


def safe_inference(trace):
    """Persist numeric telemetry and protocol facts only; omit arbitrary raw model text."""
    trace = trace if isinstance(trace, dict) else {}
    result = {k: trace.get(k) if trace.get(k) in ("heuristic", "ollama", "openai") else None
              for k in ("requested_provider", "actual_provider")}
    result["fallback_used"] = bool(trace.get("fallback_used"))
    result["error_category"] = trace.get("error_category") if trace.get("error_category") in ERRORS else None
    result["attempts"] = []
    for attempt in trace.get("attempts", []):
        if not isinstance(attempt, dict):
            continue
        metrics = {k: v for k, v in attempt.get("metrics", {}).items()
                   if k in METRIC_KEYS and type(v) is int and v >= 0}
        seconds = attempt.get("wall_clock_seconds")
        row = dict(metrics=metrics, wall_clock_seconds=seconds if type(seconds) in (int, float)
                   and isfinite(seconds) and seconds >= 0 else None,
                   error_category=attempt.get("error_category") if attempt.get("error_category") in ERRORS else None)
        # Existing provider adapters redact these identifiers before exposing last_trace.
        for key in ("request_id", "response_id"):
            value = attempt.get(key)
            if isinstance(value, str) and len(value) <= 200:
                row[key] = value
        result["attempts"].append(row)
    return result


def checked_plan(provider, name, observation, *, preflight=False):
    """Return (typed plan or None, diagnostics). A preflight permits one request."""
    repair = getattr(provider, "repair", None)
    if preflight and repair is not None:
        provider.repair = False
    started = perf_counter()
    plan = None
    error = None
    valid = False
    try:
        candidate = provider.create_turn_plan(observation)
        if type(candidate) is not ArenaTurnPlan:
            raise ArenaProviderError("schema_validation")
        plan = parse_turn_plan(canonical_json(candidate.to_dict()), observation)
        valid = True
    except Exception as caught:
        category = caught.category if isinstance(caught, ArenaProviderError) else "provider_exception"
        error = category if category in ERRORS else "provider_exception"
    finally:
        elapsed = perf_counter() - started
        if preflight and repair is not None:
            provider.repair = repair
    try:
        raw = deepcopy(getattr(provider, "last_trace", None)) or {}
        if not isinstance(raw, dict):
            raise ValueError()
    except Exception:
        raw = {}
        error = error or "provider_exception"
    diagnostic = safe_inference(raw)
    secret = getattr(getattr(provider, "settings", None), "api_key", None)
    if secret:
        for attempt in diagnostic["attempts"]:
            for key in ("request_id", "response_id"):
                if key in attempt:
                    attempt[key] = attempt[key].replace(secret, "[REDACTED]")
    identity = getattr(provider, "name", None)
    if name == "heuristic" and identity == HEURISTIC_VERSION:
        identity = "heuristic"
    actual = raw.get("actual_provider", identity)
    if (identity != name or actual != name
            or raw.get("fallback_used") or raw.get("requested_provider", name) != name):
        error = error or "provider_mismatch"
    if name != "heuristic" and not diagnostic["attempts"]:
        error = error or "provider_mismatch"  # Live provenance needs request evidence.
    diagnostic.update(requested_provider=name, actual_provider=actual if actual in
                      ("heuristic", "ollama", "openai") else None,
                      plan_valid=valid, success=valid and error is None,
                      error_category=error, wall_clock_seconds=elapsed,
                      provider_requests=len(diagnostic["attempts"]),
                      repair_requests=max(0, len(diagnostic["attempts"]) - 1),
                      resulting_plan=plan.to_dict() if plan else None)
    if preflight and diagnostic["provider_requests"] != 1:
        diagnostic.update(success=False, error_category="provider_mismatch")
    return (plan if diagnostic["success"] else None), diagnostic
