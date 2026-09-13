"""Ollama strategic planning only: no GameState, commands, or tactical rules."""

from copy import deepcopy
from http.client import HTTPException
import socket
from time import perf_counter
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from aig.ai.plan_schema import PLAN_SCHEMAS, canonical_json, parse_plan, plan_json_schema, strict_json
from aig.ai.model_profiles import public_ollama_configuration
from aig.ai.prompts import resolve_prompt
from aig.ai.strategy import StrategicPlan, StrategicState, StrategyProviderError
from aig.settings import OllamaSettings
from aig.versions import LATEST_PLAN_SCHEMA_VERSION, resolve_version

# Public compatibility exports; V1 content retains its original strategy-v1 label.
PROMPT_VERSION, SYSTEM_PROMPT = resolve_prompt()
METRICS = ("prompt_eval_count", "eval_count", "prompt_eval_duration", "eval_duration", "total_duration")


def transport_failure_category(error: Exception) -> str:
    """Preserve transport distinctions without changing retry/fallback policy."""
    if isinstance(error, HTTPError):
        category = {401: "authentication_failure", 403: "permission_denied",
                    404: "model_not_available", 429: "rate_limit"}.get(error.code)
        if category:
            return category
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, socket.gaierror):
        return "dns_failure"
    if isinstance(reason, ConnectionError):
        return "connection_failure"
    if isinstance(error, HTTPError) or (
            isinstance(error, StrategyProviderError) and str(error).startswith("Ollama HTTP status")):
        return "non_2xx"
    if isinstance(error, TimeoutError) or (
            isinstance(error, URLError) and isinstance(error.reason, TimeoutError)):
        return "timeout"
    return "transport_failure"


def post_json(url: str, body: bytes, timeout: float) -> str:
    """Small injectable standard-library transport. No subprocess or new dependency."""
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        if not 200 <= response.status < 300:
            raise StrategyProviderError(f"Ollama HTTP status {response.status}")
        return response.read().decode("utf-8")


class OllamaStrategyProvider:
    name = "ollama"

    def __init__(self, settings: OllamaSettings, *,
                 requester: Callable[[str, bytes, float], str] = post_json,
                 prompt_version=None, plan_schema_version=None, repair: bool = True):
        # Preserve settings parsing compatibility, but never enable reasoning or streaming.
        if settings.think or settings.stream:
            raise ValueError("Ollama strategic planning requires AIG_OLLAMA_THINK=false and AIG_OLLAMA_STREAM=false")
        self.prompt_version, self.system_prompt = resolve_prompt(prompt_version)
        self.schema_version = resolve_version(plan_schema_version, available=PLAN_SCHEMAS,
                                              latest=LATEST_PLAN_SCHEMA_VERSION)
        self.settings = settings
        self.requester = requester
        self._repair = repair
        self._last_trace: dict | None = None

    @property
    def last_trace(self) -> dict | None:
        return deepcopy(self._last_trace)

    def create_plan(self, state: StrategicState,
                    previous_plan: StrategicPlan | None = None) -> StrategicPlan:
        settings = self.settings
        state_json = canonical_json(state)
        previous_json = canonical_json(previous_plan.to_dict() if previous_plan else None)
        schema = plan_json_schema(self.schema_version)
        options = {field: schema["properties"][field]["items"]["enum"]
                   for field in ("production_priority", "research_priority")}
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"CURRENT STATE:\n{state_json}\n\nPREVIOUS PLAN:\n{previous_json}"
             f"\n\nPRIORITY OPTIONS:\n{canonical_json(options)}"},
        ]
        trace = dict(turn=state["turn"], player_id=state["player_id"],
                     strategic_state=deepcopy(state), previous_plan=previous_plan.to_dict() if previous_plan else None,
                     resulting_plan=None, requested_provider=self.name, actual_provider=None,
                     model=settings.model, model_configuration=public_ollama_configuration(settings),
                     prompt_version=self.prompt_version, schema_version=self.schema_version,
                     system_content=self.system_prompt, serialized_state=state_json,
                     serialized_previous_plan=previous_json, attempts=[], retry_count=0,
                     fallback_used=False, wall_clock_seconds=0.0)
        self._last_trace = trace  # Only the latest invocation is retained by the provider.
        for attempt in range(2 if self._repair else 1):
            trace["retry_count"] = attempt
            payload = dict(model=settings.model, stream=settings.stream, think=settings.think,
                           keep_alive=settings.keep_alive, messages=messages, format=plan_json_schema(self.schema_version),
                           options=dict(num_ctx=settings.context_size, temperature=settings.temperature,
                                        seed=settings.seed, num_predict=settings.max_output_tokens))
            record = dict(messages=deepcopy(messages), raw_content=None, metrics={})
            trace["attempts"].append(record)
            started = perf_counter()
            try:
                raw = self.requester(settings.base_url.rstrip("/") + "/api/chat",
                                     canonical_json(payload).encode("utf-8"), settings.timeout_seconds)
            except (OSError, URLError, HTTPException, UnicodeError, StrategyProviderError) as error:
                record["error_category"] = transport_failure_category(error)
                if isinstance(error, HTTPError):
                    reason = f"Ollama HTTP status {error.code}"
                else:
                    reason = "Ollama request failed (connection, timeout, or unreadable HTTP response)"
                trace["error"] = record["error"] = reason
                raise StrategyProviderError(reason) from error
            finally:
                record["wall_clock_seconds"] = perf_counter() - started
                trace["wall_clock_seconds"] += record["wall_clock_seconds"]
            category = "malformed_ollama_envelope"
            try:
                response = strict_json(raw)
                if isinstance(response, dict):
                    record["metrics"] = {k: response[k] for k in METRICS
                                         if type(response.get(k)) is int and response[k] >= 0}
                if not isinstance(response, dict) or not isinstance(response.get("message"), dict):
                    raise ValueError("Ollama response requires message.content")
                content = response["message"].get("content")
                if not isinstance(content, str):
                    raise ValueError("Ollama message.content must be a string")
                record["raw_content"] = content  # Never retain message.thinking.
                if response.get("done") is not True or response.get("error"):
                    raise ValueError("Ollama response did not complete successfully")
                category = "schema_validation"
                plan = parse_plan(content, state, self.schema_version)
            except (ValueError, RecursionError) as error:
                reason = str(error)[:300] if isinstance(error, ValueError) else "JSON nesting is too deep"
                record["error"] = reason
                record["error_category"] = getattr(error, "category", category)
                if attempt == 1 or not self._repair:
                    trace["error"] = reason
                    label = "two invalid responses" if self._repair else "an invalid plan"
                    raise StrategyProviderError(f"Ollama returned {label}: {reason}") from error
                # Repair feedback stays concise; exact invalid output is in the detached trace.
                messages = [*messages, {"role": "user", "content":
                    f"Your previous response was invalid: {reason}. Return a corrected StrategicPlan "
                    "using the same schema and only valid supplied IDs/options."}]
                continue
            trace["resulting_plan"] = plan.to_dict()
            trace["actual_provider"] = self.name
            return plan
        raise AssertionError("unreachable")
