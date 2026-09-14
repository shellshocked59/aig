"""Arena-only bounded pre-execution repair and detached inference telemetry."""

from copy import deepcopy
from time import perf_counter

from aig.ai.model_profiles import resolve_model_profile
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.prompts import PROMPT_VERSION, resolve_prompt
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan


class ModelArenaTurnProvider:
    prompt_version = PROMPT_VERSION
    schema_version = PLAN_SCHEMA_VERSION

    def __init__(self, settings, *, repair=True, secrets=(), prompt_version=PROMPT_VERSION):
        self.prompt_version, self.system_prompt = self.resolve_prompt(prompt_version)
        self.settings = settings
        self.repair = repair
        self._secrets = tuple(s for s in secrets if s)
        self._last_trace = None

    resolve_prompt = staticmethod(resolve_prompt)

    def _safe(self, value):
        if isinstance(value, str):
            for secret in self._secrets:
                value = value.replace(secret, "[REDACTED]")
            return value[:32768]
        if isinstance(value, dict):
            return {self._safe(k): self._safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._safe(v) for v in value]
        return value

    @property
    def last_trace(self):
        return deepcopy(self._safe(self._last_trace))

    def parse_plan(self, raw, observation):
        return parse_turn_plan(raw, observation)

    def repair_feedback(self, category):
        return (f"Previous output failed validation ({category}). Return a corrected "
                "ArenaTurnPlan using the same observation and schema. No reasoning or commentary.")

    def create_turn_plan(self, observation):
        facts = observation.to_dict()
        version, baseline = resolve_model_profile(self.name)
        configuration = self.configuration()
        trace = dict(version="arena-inference-trace-v1", turn=facts["turn"],
                     player_id=facts["active_player_id"], requested_provider=self.name,
                     actual_provider=None, fallback_used=False, model=self.settings.model,
                     model_config_version=version if configuration == baseline else None,
                     model_configuration=configuration, prompt_version=self.prompt_version,
                     schema_version=self.schema_version, observation_hash=observation.hash,
                     observation_version=observation.version,
                     attempts=[], retry_count=0, error_category=None, resulting_plan=None,
                     wall_clock_seconds=0.0)
        self._last_trace = trace
        if hasattr(self, "repair_version"):
            trace["repair_version"] = self.repair_version
        messages = [{"role": "user", "content": "ArenaObservation:\n" + observation.canonical}]
        for attempt in range(2 if self.repair else 1):
            # Optional experiment boundary; denied requests are not attempts.
            before_request = getattr(self, "before_request", None)
            if before_request is not None:
                try:
                    before_request()
                except ArenaProviderError as error:
                    trace["error_category"] = error.category
                    for previous in trace["attempts"]:
                        if "rejected_decision" in previous:
                            previous["rejected_decision"]["repair_result"] = "not_attempted"
                    raise
            trace["retry_count"] = attempt
            record = dict(raw_content=None, metrics={})
            trace["attempts"].append(record)
            started = perf_counter()
            try:
                raw = self.request(messages, record)
            except ArenaProviderError as error:
                trace["error_category"] = record["error_category"] = error.category
                for previous in trace["attempts"]:
                    if "rejected_decision" in previous:
                        previous["rejected_decision"]["repair_result"] = "failed"
                raise ArenaProviderError(error.category) from None
            finally:
                record["wall_clock_seconds"] = perf_counter() - started
                trace["wall_clock_seconds"] += record["wall_clock_seconds"]
            record["raw_content"] = self._safe(raw)
            try:
                if len(raw) > 32768:
                    raise ArenaProviderError("schema_validation")
                plan = self.parse_plan(raw, observation)
            except ArenaProviderError as error:
                record["error_category"] = error.category
                evidence_hook = getattr(self, "rejection_evidence", None)
                if evidence_hook is not None:
                    record["raw_content"] = None
                    record["rejected_decision"] = evidence_hook(raw, observation, error)
                    record["rejected_decision"]["repair_result"] = "failed" if attempt or not self.repair else "pending"
                if attempt == 1 or not self.repair:
                    trace["error_category"] = "repair_failed" if attempt else error.category
                    for previous in trace["attempts"]:
                        if "rejected_decision" in previous:
                            previous["rejected_decision"]["repair_result"] = "failed" if attempt else "not_attempted"
                    raise ArenaProviderError(trace["error_category"]) from None
                # Same observation/schema, no raw output echo or exception text.
                messages = [*messages, {"role": "user", "content":
                    self.repair_feedback(error.category)}]
                if evidence_hook is not None:
                    messages = self.repair_messages(observation, error, record["rejected_decision"])
                continue
            for previous in trace["attempts"]:
                if "rejected_decision" in previous:
                    previous["rejected_decision"]["repair_result"] = "succeeded"
            trace.update(actual_provider=self.name, resulting_plan=plan.to_dict())
            return plan
        raise AssertionError("unreachable")
