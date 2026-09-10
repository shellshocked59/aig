"""Stateless OpenAI strategic planning; execution and fallback belong elsewhere."""

from copy import deepcopy
from time import perf_counter

from openai import (
    APIConnectionError, APIError, APIResponseValidationError, APIStatusError,
    APITimeoutError, AuthenticationError, NotFoundError, OpenAI,
    PermissionDeniedError, RateLimitError,
)

from aig.ai.ollama import PROMPT_VERSION, SYSTEM_PROMPT
from aig.ai.plan_schema import PLAN_SCHEMA_VERSION, canonical_json, parse_plan, plan_json_schema
from aig.ai.strategy import StrategicPlan, StrategicState, StrategyProviderError
from aig.settings import OpenAISettings
from aig.state import Technology, UnitType

OPENAI_SCHEMA_VERSION = "strategic-plan-openai-v1"


def openai_plan_json_schema() -> dict:
    """Use documented Structured Outputs constraints; keep parse_plan unchanged.

    uniqueItems and minLength are outside the documented supported properties.
    Uniqueness and nonblank IDs are still enforced by the application parser.
    """
    schema = plan_json_schema()
    for rule in schema["properties"].values():
        rule.pop("uniqueItems", None)
        rule.pop("minLength", None)
    return schema


def public_configuration(settings: OpenAISettings) -> dict:
    """Never serialize credentials through asdict/vars."""
    return dict(model=settings.model, timeout_seconds=settings.timeout_seconds,
                max_output_tokens=settings.max_output_tokens,
                reasoning_effort=settings.reasoning_effort, max_retries=0)


def api_failure_category(error: APIError) -> str:
    if isinstance(error, AuthenticationError):
        return "authentication_failure"
    if isinstance(error, PermissionDeniedError):
        return "permission_denied"
    if isinstance(error, NotFoundError):
        return "model_not_available"
    if isinstance(error, RateLimitError):
        return "rate_limit"
    if isinstance(error, APITimeoutError):
        return "timeout"
    if isinstance(error, APIConnectionError):
        return "connection_failure"
    if isinstance(error, APIResponseValidationError):
        return "malformed_openai_response"
    return "api_error"


def usage_metrics(response) -> dict:
    usage = getattr(response, "usage", None)
    values = {key: getattr(usage, key, None)
              for key in ("input_tokens", "output_tokens", "total_tokens")}
    values["cached_input_tokens"] = getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", None)
    values["reasoning_tokens"] = getattr(getattr(usage, "output_tokens_details", None), "reasoning_tokens", None)
    return {key: value for key, value in values.items() if type(value) is int and value >= 0}


class OpenAIStrategyProvider:
    name = "openai"

    def __init__(self, settings: OpenAISettings, *, client=None, repair: bool = True):
        if not settings.api_key:
            raise StrategyProviderError("OpenAI requires OPENAI_API_KEY when selected.")
        self.settings = settings
        self._client = client if client is not None else OpenAI(
            api_key=settings.api_key, timeout=settings.timeout_seconds, max_retries=0)
        self._repair = repair  # The explicit one-request smoke command disables repair.
        self._last_trace: dict | None = None

    def _safe(self, value):
        """Redact accidental credential echoes before retaining diagnostic data."""
        if isinstance(value, str):
            return value.replace(self.settings.api_key, "[REDACTED]")
        if isinstance(value, dict):
            return {self._safe(k): self._safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._safe(v) for v in value]
        return value

    @property
    def last_trace(self) -> dict | None:
        return deepcopy(self._last_trace)

    def create_plan(self, state: StrategicState,
                    previous_plan: StrategicPlan | None = None) -> StrategicPlan:
        state_json = canonical_json(state)
        previous_json = canonical_json(previous_plan.to_dict() if previous_plan else None)
        options = {"production_priority": [v.value for v in UnitType],
                   "research_priority": [v.value for v in Technology]}
        # Same versioned instructions, state, prior plan, and options as Ollama.
        messages = [{"role": "user", "content":
                     f"CURRENT STATE:\n{state_json}\n\nPREVIOUS PLAN:\n{previous_json}"
                     f"\n\nPRIORITY OPTIONS:\n{canonical_json(options)}"}]
        trace = self._safe(dict(
            turn=state["turn"], player_id=state["player_id"], strategic_state=deepcopy(state),
            previous_plan=previous_plan.to_dict() if previous_plan else None,
            resulting_plan=None, requested_provider=self.name, actual_provider=None,
            model=self.settings.model, model_configuration=public_configuration(self.settings),
            prompt_version=PROMPT_VERSION, schema_version=PLAN_SCHEMA_VERSION,
            provider_schema_version=OPENAI_SCHEMA_VERSION, system_content=SYSTEM_PROMPT,
            serialized_state=state_json, serialized_previous_plan=previous_json,
            attempts=[], retry_count=0, fallback_used=False, wall_clock_seconds=0.0))
        self._last_trace = trace
        for attempt in range(2 if self._repair else 1):
            trace["retry_count"] = attempt
            record = dict(messages=self._safe(deepcopy(messages)), raw_content=None, metrics={})
            trace["attempts"].append(record)
            started = perf_counter()
            try:
                response = self._client.responses.create(
                    model=self.settings.model, instructions=SYSTEM_PROMPT, input=messages,
                    reasoning={"effort": self.settings.reasoning_effort},
                    max_output_tokens=self.settings.max_output_tokens,
                    text={"format": {"type": "json_schema", "name": "strategic_plan",
                                     "strict": True, "schema": openai_plan_json_schema()}},
                    store=False,
                )
            except APIError as error:
                category = api_failure_category(error)
                if isinstance(error, APIStatusError):
                    record["http_status"] = error.status_code
                request_id = getattr(error, "request_id", None)
                if isinstance(request_id, str):
                    record["request_id"] = self._safe(request_id)[:200]
                self._fail(trace, record, category, f"OpenAI request failed ({category}).")
            finally:
                record["wall_clock_seconds"] = perf_counter() - started
                trace["wall_clock_seconds"] += record["wall_clock_seconds"]

            record["metrics"] = usage_metrics(response)
            for field, attribute in (("response_id", "id"), ("request_id", "_request_id"), ("model", "model")):
                value = getattr(response, attribute, None)
                if isinstance(value, str):
                    record[field] = self._safe(value)[:200]
            status = getattr(response, "status", None)
            if status != "completed" or getattr(response, "error", None):
                category = "incomplete_response" if status == "incomplete" else "malformed_openai_response"
                self._fail(trace, record, category, "OpenAI response did not complete successfully.")
            # Inspect typed content only for refusals. Text extraction uses the SDK helper.
            output = getattr(response, "output", None)
            if not isinstance(output, list):
                self._fail(trace, record, "malformed_openai_response", "OpenAI response has malformed output.")
            for item in output:
                if getattr(item, "type", None) == "message":
                    content = getattr(item, "content", None)
                    if not isinstance(content, list):
                        self._fail(trace, record, "malformed_openai_response", "OpenAI response has malformed content.")
                    if any(getattr(part, "type", None) == "refusal" for part in content):
                        self._fail(trace, record, "refusal", "OpenAI refused the strategic-plan request.")
            try:
                raw = response.output_text
            except (AttributeError, TypeError):
                self._fail(trace, record, "malformed_openai_response", "OpenAI response has unreadable output.")
            if not isinstance(raw, str):
                self._fail(trace, record, "malformed_openai_response", "OpenAI output text must be a string.")
            record["raw_content"] = self._safe(raw)[:32768]
            if not raw.strip():
                self._fail(trace, record, "empty_output", "OpenAI returned empty output.")
            try:
                plan = parse_plan(raw, state)
            except (ValueError, RecursionError) as error:
                reason = self._safe(str(error))[:300] if isinstance(error, ValueError) else "JSON nesting is too deep"
                category = getattr(error, "category", "schema_validation")
                record.update(error=reason, error_category=category)
                if attempt == 1 or not self._repair:
                    self._fail(trace, record, category, f"OpenAI returned an invalid plan: {reason}")
                messages = [*messages, {"role": "user", "content":
                    f"Your previous response was invalid: {reason}. Return a corrected StrategicPlan "
                    "using the same schema and only valid supplied IDs/options."}]
                continue
            trace["resulting_plan"] = self._safe(plan.to_dict())
            trace["actual_provider"] = self.name
            return plan
        raise AssertionError("unreachable")

    @staticmethod
    def _fail(trace: dict, record: dict, category: str, reason: str):
        trace["error"] = record["error"] = reason
        record["error_category"] = category
        # SDK exceptions may contain headers/body/configuration; suppress their chain.
        raise StrategyProviderError(reason) from None
