"""Stateless Ollama tactical turns; no Empire planning or fallback."""

from http.client import HTTPException
from urllib.error import URLError

from aig.ai.ollama import METRICS, post_json, transport_failure_category
from aig.ai.plan_schema import strict_json
from aig.ai.strategy import StrategyProviderError
from aig.arena.ai.contracts import turn_plan_schema
from aig.arena.ai.provider import ModelArenaTurnProvider
from aig.arena.ai.prompts import PROMPT_VERSION
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.snapshots import canonical_json


class OllamaArenaTurnProvider(ModelArenaTurnProvider):
    name = "ollama"
    output_schema = staticmethod(turn_plan_schema)

    def __init__(self, settings, *, requester=post_json, repair=True, secrets=(), prompt_version=PROMPT_VERSION):
        if settings.think or settings.stream:
            raise ValueError("Arena Ollama requires think=false and stream=false")
        super().__init__(settings, repair=repair, secrets=secrets, prompt_version=prompt_version)
        self.requester = requester

    def configuration(self):
        return {key: getattr(self.settings, key) for key in (
            "model", "context_size", "temperature", "seed", "max_output_tokens", "think", "stream")}

    def request(self, messages, record):
        s = self.settings
        payload = dict(model=s.model, stream=False, think=False, keep_alive=s.keep_alive,
                       messages=[{"role": "system", "content": self.system_prompt}, *messages],
                       format=self.output_schema(), options=dict(num_ctx=s.context_size,
                       temperature=s.temperature, seed=s.seed, num_predict=s.max_output_tokens))
        try:
            raw = self.requester(s.base_url.rstrip("/") + "/api/chat",
                                 canonical_json(payload).encode("utf-8"), s.timeout_seconds)
        except (OSError, URLError, HTTPException, UnicodeError, StrategyProviderError) as error:
            raise ArenaProviderError(transport_failure_category(error)) from None
        try:
            response = strict_json(raw)
            if (type(response) is not dict or response.get("done") is not True
                    or response.get("error") or type(response.get("message")) is not dict
                    or not isinstance(response["message"].get("content"), str)):
                raise ValueError()
            record["metrics"] = {k: response[k] for k in METRICS
                                 if type(response.get(k)) is int and response[k] >= 0}
            return response["message"]["content"]
        except (ValueError, TypeError, RecursionError):
            raise ArenaProviderError("malformed_envelope") from None
