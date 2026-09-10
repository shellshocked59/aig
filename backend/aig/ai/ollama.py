"""Ollama strategic planning only: no GameState, commands, or tactical rules."""

from copy import deepcopy
from dataclasses import asdict
from http.client import HTTPException
from time import perf_counter
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from aig.ai.plan_schema import PLAN_SCHEMA_VERSION, canonical_json, parse_plan, plan_json_schema, strict_json
from aig.ai.strategy import StrategicPlan, StrategicState, StrategyProviderError
from aig.settings import OllamaSettings
from aig.state import Technology, UnitType

PROMPT_VERSION = "strategy-v1"
SYSTEM_PROMPT = """Prompt version: strategy-v1
You are the high-level strategic planner for one faction in a small deterministic
turn-based empire game. Choose a strategy using only the supplied state/options.
You do not control individual movement or combat. A deterministic executor carries
out your plan. Use only supplied enemy player/city IDs and priority options.
Priorities are ordered preferences; future unlocks and known research are allowed.
The executor selects currently legal options. Preserve a sensible previous plan
unless the situation justifies changing it. Return only the StrategicPlan JSON
required by the schema, with all six fields. Do not explain your answer."""
METRICS = ("prompt_eval_count", "eval_count", "prompt_eval_duration", "eval_duration", "total_duration")


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
                 requester: Callable[[str, bytes, float], str] = post_json):
        # Preserve settings parsing compatibility, but never enable reasoning or streaming.
        if settings.think or settings.stream:
            raise ValueError("Ollama strategic planning requires AIG_OLLAMA_THINK=false and AIG_OLLAMA_STREAM=false")
        self.settings = settings
        self.requester = requester
        self._last_trace: dict | None = None

    @property
    def last_trace(self) -> dict | None:
        return deepcopy(self._last_trace)

    def create_plan(self, state: StrategicState,
                    previous_plan: StrategicPlan | None = None) -> StrategicPlan:
        settings = self.settings
        state_json = canonical_json(state)
        previous_json = canonical_json(previous_plan.to_dict() if previous_plan else None)
        options = {"production_priority": [v.value for v in UnitType],
                   "research_priority": [v.value for v in Technology]}
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CURRENT STATE:\n{state_json}\n\nPREVIOUS PLAN:\n{previous_json}"
             f"\n\nPRIORITY OPTIONS:\n{canonical_json(options)}"},
        ]
        trace = dict(turn=state["turn"], player_id=state["player_id"],
                     strategic_state=deepcopy(state), previous_plan=previous_plan.to_dict() if previous_plan else None,
                     resulting_plan=None, requested_provider=self.name, actual_provider=None,
                     model=settings.model, model_configuration=asdict(settings),
                     prompt_version=PROMPT_VERSION, schema_version=PLAN_SCHEMA_VERSION,
                     system_content=SYSTEM_PROMPT, serialized_state=state_json,
                     serialized_previous_plan=previous_json, attempts=[], retry_count=0,
                     fallback_used=False, wall_clock_seconds=0.0)
        self._last_trace = trace  # Only the latest invocation is retained by the provider.
        for attempt in range(2):
            trace["retry_count"] = attempt
            payload = dict(model=settings.model, stream=settings.stream, think=settings.think,
                           keep_alive=settings.keep_alive, messages=messages, format=plan_json_schema(),
                           options=dict(num_ctx=settings.context_size, temperature=settings.temperature,
                                        seed=settings.seed, num_predict=settings.max_output_tokens))
            record = dict(messages=deepcopy(messages), raw_content=None, metrics={})
            trace["attempts"].append(record)
            started = perf_counter()
            try:
                raw = self.requester(settings.base_url.rstrip("/") + "/api/chat",
                                     canonical_json(payload).encode("utf-8"), settings.timeout_seconds)
            except (OSError, URLError, HTTPException, UnicodeError, StrategyProviderError) as error:
                if isinstance(error, HTTPError):
                    reason = f"Ollama HTTP status {error.code}"
                else:
                    reason = "Ollama request failed (connection, timeout, or unreadable HTTP response)"
                trace["error"] = record["error"] = reason
                raise StrategyProviderError(reason) from error
            finally:
                record["wall_clock_seconds"] = perf_counter() - started
                trace["wall_clock_seconds"] += record["wall_clock_seconds"]
            try:
                response = strict_json(raw)
                if not isinstance(response, dict) or not isinstance(response.get("message"), dict):
                    raise ValueError("Ollama response requires message.content")
                content = response["message"].get("content")
                if not isinstance(content, str):
                    raise ValueError("Ollama message.content must be a string")
                record["raw_content"] = content  # Never retain message.thinking.
                record["metrics"] = {k: response[k] for k in METRICS
                                     if type(response.get(k)) is int and response[k] >= 0}
                if response.get("done") is not True or response.get("error"):
                    raise ValueError("Ollama response did not complete successfully")
                plan = parse_plan(content, state)
            except (ValueError, RecursionError) as error:
                reason = str(error)[:300] if isinstance(error, ValueError) else "JSON nesting is too deep"
                record["error"] = reason
                if attempt == 1:
                    trace["error"] = reason
                    raise StrategyProviderError(f"Ollama returned two invalid responses: {reason}") from error
                # Repair feedback stays concise; exact invalid output is in the detached trace.
                messages = [*messages, {"role": "user", "content":
                    f"Your previous response was invalid: {reason}. Return a corrected StrategicPlan "
                    "using the same schema and only valid supplied IDs/options."}]
                continue
            trace["resulting_plan"] = plan.to_dict()
            trace["actual_provider"] = self.name
            return plan
        raise AssertionError("unreachable")
