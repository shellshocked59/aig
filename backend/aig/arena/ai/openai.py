"""Official synchronous Responses SDK adapter for direct Arena tactical actions."""

from openai import OpenAI, APIError

from aig.ai.openai import api_failure_category, usage_metrics
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.prompts import SYSTEM_PROMPT
from aig.arena.ai.validation import ArenaProviderError, openai_turn_plan_schema


class OpenAIArenaTurnProvider(ModelArenaTurnProvider):
    name = "openai"

    def __init__(self, settings, *, client=None, repair=True, secrets=()):
        super().__init__(settings, repair=repair, secrets=(*secrets, settings.api_key))
        # Missing credentials fail on the turn boundary, where normal fallback lives.
        self._client = client
        if client is None and settings.api_key:
            self._client = OpenAI(api_key=settings.api_key, timeout=settings.timeout_seconds, max_retries=0)

    def configuration(self):
        return dict(model=self.settings.model, reasoning_effort=self.settings.reasoning_effort,
                    max_output_tokens=self.settings.max_output_tokens, store=False, max_retries=0)

    def request(self, messages, record):
        if not self.settings.api_key or self._client is None:
            raise ArenaProviderError("authentication_failure")
        try:
            response = self._client.responses.create(
                model=self.settings.model, instructions=SYSTEM_PROMPT, input=messages,
                reasoning={"effort": self.settings.reasoning_effort},
                max_output_tokens=self.settings.max_output_tokens, store=False,
                text={"format": dict(type="json_schema", name="arena_turn_plan", strict=True,
                                     schema=openai_turn_plan_schema())})
        except APIError as error:
            request_id = getattr(error, "request_id", None)
            if isinstance(request_id, str):
                record["request_id"] = self._safe(request_id)[:200]
            raise ArenaProviderError(api_failure_category(error)) from None
        except (ValueError, RecursionError):
            raise ArenaProviderError("malformed_envelope") from None
        record["metrics"] = usage_metrics(response)
        for key, attribute in (("response_id", "id"), ("request_id", "_request_id")):
            value = getattr(response, attribute, None)
            if isinstance(value, str):
                record[key] = self._safe(value)[:200]
        if getattr(response, "status", None) != "completed" or getattr(response, "error", None):
            raise ArenaProviderError("malformed_envelope")
        output = getattr(response, "output", None)
        if not isinstance(output, list):
            raise ArenaProviderError("malformed_envelope")
        texts = []
        for item in output:
            kind = getattr(item, "type", None)
            if kind == "reasoning":
                continue  # Never retain hidden reasoning, even if returned by SDK.
            if (kind != "message" or getattr(item, "role", None) != "assistant"
                    or getattr(item, "status", None) != "completed"
                    or not isinstance(getattr(item, "content", None), list)):
                raise ArenaProviderError("malformed_envelope")
            for part in item.content:
                if getattr(part, "type", None) == "refusal":
                    raise ArenaProviderError("refusal")
                if getattr(part, "type", None) != "output_text" or not isinstance(getattr(part, "text", None), str):
                    raise ArenaProviderError("malformed_envelope")
                texts.append(part.text)
        if not texts:
            raise ArenaProviderError("malformed_envelope")
        return "".join(texts)
