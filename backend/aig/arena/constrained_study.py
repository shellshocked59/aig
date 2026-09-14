"""Offline Phase 10A proof and payload measurements. No live runner or preflight."""

import argparse
from copy import deepcopy
from itertools import product
import json
from math import ceil
from pathlib import Path
from types import SimpleNamespace as NS

from aig.arena.ai.constrained import (build_arena_step_legal_wire_schema, wire_metadata,
    OllamaArenaConstrainedStepProvider, OpenAIArenaConstrainedStepProvider,
    HeuristicArenaConstrainedStepProvider, ArenaConstrainedStepController,
    CONTROL_VERSION, WIRE_SCHEMA_VERSION)
from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION
from aig.arena.ai.observation import ArenaObservation, OBSERVATION_V2, build_observation
from aig.arena.ai.stepwise import OllamaArenaStepProvider, OpenAIArenaStepProvider, ArenaStepController, HeuristicArenaStepProvider
from aig.arena.benchmark_versions import artifact, frozen_probe, probe_set
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, digest, to_snapshot
from aig.settings import Settings, OpenAISettings

BENCHMARK_VERSION = "arena-benchmark-v5"
HISTORY = ("arena-phase7f-stepwise-reliability-20260913-01",
           "arena-phase8c-qwen-fullmatch-repair-v1-01", "arena-phase8c-qwen-fullmatch-repair-v2-01")


def enumerate_schema(schema):
    """Independent exhaustive interpreter of the emitted finite JSON Schema subset.

    Reject unknown keywords or unbounded languages rather than assume exactness.
    This is offline proof tooling, not a replacement for the domain parser.
    """
    allowed = {"type", "enum", "properties", "required", "additionalProperties", "items", "maxItems", "anyOf"}
    if set(schema) - allowed:
        raise ValueError("unsupported proof keyword")
    if "anyOf" in schema:
        if set(schema) != {"anyOf"} or not schema["anyOf"]:
            raise ValueError("unsupported union")
        return [v for branch in schema["anyOf"] for v in enumerate_schema(branch)]
    kind = schema["type"]
    if kind == "object":
        props = schema["properties"]
        if schema["additionalProperties"] is not False or set(schema["required"]) != set(props):
            raise ValueError("unbounded object")
        return [dict(zip(props, values)) for values in product(*(enumerate_schema(s) for s in props.values()))]
    if kind == "array":
        maximum = schema["maxItems"]
        if maximum not in (0, 1):
            raise ValueError("unsupported array bound")
        return [[]] if maximum == 0 else [[], *[[v] for v in enumerate_schema(schema["items"])]]
    if kind in ("string", "integer") and "enum" in schema:
        expected = str if kind == "string" else int
        if any(type(v) is not expected for v in schema["enum"]):
            raise ValueError("incorrectly typed enum")
        return deepcopy(schema["enum"])
    raise ValueError("unbounded leaf")


def prove_catalog(observation):
    actions = observation.to_dict()["legal_actions"]
    expected = [dict(schema_version=PLAN_SCHEMA_VERSION, actions=[])] + [
        dict(schema_version=PLAN_SCHEMA_VERSION, actions=[a]) for a in actions]
    for kind in ("ollama", "openai"):
        schema = build_arena_step_legal_wire_schema(observation, kind)
        outputs = enumerate_schema(schema)
        if outputs != expected or len({canonical_json(v) for v in outputs}) != len(expected):
            raise AssertionError("wire language differs from ordered legal catalog plus EndTurn")
        # Installed SDK strict transformation must preserve the exact schema.
        if kind == "openai":
            from openai.lib._pydantic import _ensure_strict_json_schema
            derived = deepcopy(schema)
            if _ensure_strict_json_schema(derived, path=(), root=derived) != schema:
                raise AssertionError("SDK strict transformation altered schema")
    return dict(observation_hash=observation.hash, **wire_metadata(observation),
                allowed_outputs=len(expected), exact=True)


def captured_request(observation, kind, constrained):
    """Exercise real adapters exclusively through injected in-memory transports."""
    captured = []
    raw = canonical_json(ArenaTurnPlan().to_dict())
    if kind == "ollama":
        def request(url, body, timeout):
            captured.append(json.loads(body))  # Never persist URL or headers.
            return canonical_json(dict(done=True, message=dict(content=raw)))
        cls = OllamaArenaConstrainedStepProvider if constrained else OllamaArenaStepProvider
        provider = cls(Settings().ollama, requester=request)
    elif kind == "openai":
        def request(**kwargs):
            captured.append(kwargs)
            return NS(status="completed", error=None, id=None, _request_id=None, usage=None,
                output=[NS(type="message", role="assistant", status="completed",
                           content=[NS(type="output_text", text=raw)])])
        cls = OpenAIArenaConstrainedStepProvider if constrained else OpenAIArenaStepProvider
        provider = cls(OpenAISettings(api_key="offline-canary-secret"), client=NS(responses=NS(create=request)))
    else:
        raise ValueError("unknown provider")
    provider.create_step(observation)
    assert len(captured) == 1
    assert "offline-canary-secret" not in canonical_json(captured)
    return captured[0]


def measure(observation, label, historical_input_tokens=None):
    size = lambda v: len(canonical_json(v).encode("utf-8"))
    result = dict(label=label, observation_hash=observation.hash,
        observation_bytes=len(observation.canonical.encode()),
        legal_action_count=len(observation.to_dict()["legal_actions"]), providers={})
    for kind in ("ollama", "openai"):
        requests = {mode: captured_request(observation, kind, mode == "constrained")
                    for mode in ("generic", "constrained")}
        rows = {}
        for mode, request in requests.items():
            schema = request["format"] if kind == "ollama" else request["text"]["format"]["schema"]
            rows[mode] = dict(schema_bytes=size(schema), request_bytes=size(request), schema_hash=digest(schema))
            if kind == "ollama":
                low, high = ceil(size(request)/4), ceil(size(request)/3)
                rows[mode].update(unanchored_input_token_estimate=[low, high],
                    headroom_after_256_output=[4096-256-high, 4096-256-low])
        message_key = "messages" if kind == "ollama" else "input"
        assert requests["generic"][message_key] == requests["constrained"][message_key]
        rows["message_bytes_unchanged"] = True
        result["providers"][kind] = rows
    result["historical_generic_input_tokens"] = historical_input_tokens
    if historical_input_tokens is not None:
        result["if_schema_is_grammar_only_headroom"] = 4096-256-historical_input_tokens
        delta = result["providers"]["ollama"]["constrained"]["schema_bytes"] - result["providers"]["ollama"]["generic"]["schema_bytes"]
        result["if_schema_text_is_added_input_estimate"] = [historical_input_tokens+ceil(delta/4), historical_input_tokens+ceil(delta/3)]
    return result


def study(history, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write = lambda name, data: (output/name).write_text(json.dumps(data, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    recipe = artifact(BENCHMARK_VERSION)
    proofs, equivalence, failures, historical = [], [], [], []
    schemas = {}
    def proof(obs):
        row = prove_catalog(obs)
        schemas[row["wire_schema_hash"]] = build_arena_step_legal_wire_schema(obs)
        proofs.append(row)
    for name in probe_set()["probes"]:
        generic, constrained = ArenaSimulation(frozen_probe(name)), ArenaSimulation(frozen_probe(name))
        gt = ArenaStepController(HeuristicArenaStepProvider()).run_turn(generic)
        ct = ArenaConstrainedStepController(HeuristicArenaConstrainedStepProvider()).run_turn(constrained)
        assert generic.trace() == constrained.trace()
        assert gt["action_sequence"] == ct["action_sequence"]
        assert replay(constrained.trace()).trace() == constrained.trace()
        for row in ct["steps"]:
            obs = ArenaObservation.from_dict(row["observation"])
            proof(obs)
            assert row["decision"] in enumerate_schema(build_arena_step_legal_wire_schema(obs))
        equivalence.append(dict(probe=name, steps=len(ct["steps"]), command_trace_hash=digest(constrained.trace()), identical=True))
        write(name+"-heuristic.json", dict(turn=ct, command_trace=constrained.trace(), final_snapshot=to_snapshot(constrained.state)))
    for root in HISTORY:
        paths = sorted((history/root).rglob("turn.json"))
        if not paths:
            raise ValueError("missing required historical evidence")
        for path in paths:
            turn = json.loads(path.read_text(encoding="utf-8"))
            for index, row in enumerate(turn.get("steps", [])):
                if row.get("requested_provider") != "ollama":
                    continue
                obs = ArenaObservation.from_dict(row["observation"])
                assert obs.hash == row["observation_hash"]
                historical.append((obs, row, path, index))
                invalid = [a for a in row["attempts"] if a.get("error_category") == "invalid_reference"]
                if not invalid:
                    continue
                proof(obs)
                language = {canonical_json(v) for v in enumerate_schema(build_arena_step_legal_wire_schema(obs))}
                for attempt in invalid:
                    parsed = attempt.get("rejected_decision", {}).get("parsed_decision")
                    if parsed is not None:
                        assert canonical_json(parsed) not in language
                    # Explicit synthetic pattern where historical raw/parsed text was not saved.
                    stale = dict(schema_version=PLAN_SCHEMA_VERSION, actions=[dict(type="heal", unit_id="blue-cleric", target_id="stale-nonexistent")])
                    assert canonical_json(stale) not in language
                    failures.append(dict(source=path.as_posix(), step_index=index, observation_hash=obs.hash,
                        historical_parsed_decision=parsed, retained_pattern_excluded=parsed is not None,
                        synthetic_stale_reference_excluded=True))
    revive = build_observation(frozen_probe("revive_decision"), version=OBSERVATION_V2)
    historic_revive = json.loads((history/"arena-phase9d-action-id-forensics-20260913/derived-01/revive-decisions.json").read_text(encoding="utf-8"))[0]
    assert revive.hash == historic_revive["observation_hash"]
    assert historic_revive["action"] == revive.to_dict()["legal_actions"][-1]
    proof(revive)
    mid = next(v for v in historical if v[0].to_dict()["turn"] >= 4)
    proof(build_observation(ArenaSimulation().state, version=OBSERVATION_V2))
    proof(mid[0])
    measurements = [measure(build_observation(frozen_probe("snipe_vs_basic"), version=OBSERVATION_V2), "simple-probe"),
        measure(revive, "revive", historic_revive["telemetry"][0]["metrics"]["prompt_eval_count"]),
        measure(build_observation(ArenaSimulation().state, version=OBSERVATION_V2), "opening"),
        dict(**measure(mid[0], "historical-midgame", mid[1]["attempts"][0]["metrics"].get("prompt_eval_count")), source=mid[2].as_posix(), step_index=mid[3])]
    for schema_hash, schema in schemas.items():
        write("schema-"+schema_hash+".json", schema)
    result = dict(benchmark_version=BENCHMARK_VERSION, recipe=recipe, control_version=CONTROL_VERSION,
        wire_schema_version=WIRE_SCHEMA_VERSION, proofs=proofs, heuristic_equivalence=equivalence,
        historical_failures=failures, measurements=measurements,
        revive=dict(observation_hash=revive.hash, historical_revive_allowed=True, canonical_position=21, legal_actions=21),
        context_gate="RED" if any(m["providers"]["ollama"]["constrained"]["headroom_after_256_output"][0] < 0 for m in measurements if m["label"] in ("opening", "historical-midgame")) else "YELLOW",
        context_gate_basis="Conservative preparation gate, not measured model overflow. Request bytes/3..4 include out-of-band schema; schema-to-prompt token effect unknown. No local Qwen tokenizer/server prompt evidence. Reliable fit is not established.",
        live_requests=0, live_command_prepared=False,
        summary=dict(proof_states=len(proofs), unique_schemas=len(schemas), heuristic_probe_turns=len(equivalence),
                     historical_invalid_attempts=len(failures), retained_parsed_rejections=sum(f["retained_pattern_excluded"] for f in failures)))
    write("study.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=Path(".local"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Enforce offline execution, including accidental future transport additions.
    import sys
    def offline(event, args):
        if event in ("socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"):
            raise RuntimeError("Phase 10A forbids network and subprocesses")
    sys.addaudithook(offline)
    result = study(args.history, args.output)
    print(canonical_json(dict(result["summary"], context_gate=result["context_gate"], live_requests=0)))


if __name__ == "__main__":
    main()
