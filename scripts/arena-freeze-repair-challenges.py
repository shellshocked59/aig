"""Offline, explicit fixture construction from retained Phase 7D/7F commands.

Run once when freezing a NEW dataset; refuses to overwrite the current artifact.
Injected decisions are representative, never claimed to be recovered responses.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def offline(event, args):
    if event in ("socket.connect", "socket.getaddrinfo", "subprocess.Popen"):
        raise RuntimeError("fixture construction is offline")


sys.addaudithook(offline)
from aig.arena.ai.observation import build_observation, OBSERVATION_V2, observation_facts
from aig.arena.ai.stepwise import parse_step, STEP_PROMPT
from aig.arena.ai.repair import feedback, REPAIR_V1
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import from_snapshot, to_snapshot, command_from_dict, digest, canonical_json


def main():
    d = ".local/arena-phase7d-stepwise-fullmatch-pilot-20260913-02"
    f = ".local/arena-phase7f-stepwise-reliability-20260913-01"
    selections = [
        ("qwen-early", f, "qwen/run-001", "early Qwen stopping state"),
        ("qwen-later", d, "qwen-self/run-001", "later Qwen stopping state; 1 AP"),
        ("luna-failure", d, "luna-self/run-001", "Luna stopping state; downed unit"),
        ("downed-revive", f, "luna/run-001", "turn 4; historical current legal revive option"),
        ("midgame", d, "luna-vs-heuristic/run-001", "turn 6 midgame stopping state"),
        ("low-ap", d, "qwen-self/run-002", "second Qwen 1 AP stopping state"),
    ]
    challenges = []
    for index, (cid, directory, mid, rationale) in enumerate(selections):
        summary = json.loads((ROOT/directory/"summary.json").read_text())
        match = next(m for m in summary["matches"] if m["match_id"] == mid)
        for ti, turn in enumerate(match["turns"], 1):
            failed = next((s for s in turn.get("steps", []) if
                           (any(a["type"] == "revive" for a in s["observation"]["legal_actions"])
                            if cid == "downed-revive" else not s["success"])), None)
            if failed is not None:
                break
        assert failed is not None
        trace_path = Path(directory)/mid/"turns"/f"turn-{ti:04d}"/"command-trace.json"
        raw = (ROOT/trace_path).read_bytes()
        trace = json.loads(raw)
        sim = ArenaSimulation(from_snapshot(trace["initial_snapshot"]))
        for step in turn["steps"]:
            obs = build_observation(sim.state, version=OBSERVATION_V2)
            assert obs.to_dict() == step["observation"] and obs.hash == step["observation_hash"]
            if step is failed:
                break
            if step["command_index"] is not None:
                sim.execute(command_from_dict(trace["entries"][step["command_index"]]["command"]))
        facts = observation_facts(obs)
        catalog = obs.to_dict()["legal_actions"]
        action = dict(next((a for a in catalog if "target_id" in a), catalog[0]))
        if index % 3 == 0:
            action["unit_id"] = facts["enemy_team"]["units"][0]["id"]
        elif "target_id" in action:
            action["target_id"] = "missing-target" if index % 3 == 1 else facts["own_team"]["core"]["id"]
        else:
            action["unit_id"] = "missing-unit"
        decision = dict(schema_version="arena-turn-plan-schema-v1", actions=[action])
        try:
            parse_step(canonical_json(decision), obs)
        except ArenaProviderError as error:
            assert error.category == "invalid_reference"
            diagnostic = error.diagnostic.to_dict()
        else:
            raise AssertionError("injection must fail")
        challenges.append(dict(id=cid, snapshot=to_snapshot(sim.state), state_hash=digest(to_snapshot(sim.state)),
            observation=obs.to_dict(), observation_hash=obs.hash, invalid_decision=decision,
            expected_failure=diagnostic, historical=dict(source=trace_path.as_posix(),
            source_sha256=hashlib.sha256(raw).hexdigest(), match_id=mid, player_turn=ti,
            step_index=failed["step_index"], provider=failed["requested_provider"], rationale=rationale),
            limitation="Representative injected invalid decision; original rejected output unavailable."))
    data = dict(version="arena-repair-challenges-v1", challenges=challenges, content_hash=digest(challenges))
    target = ROOT/"backend/aig/arena/benchmark_artifacts/arena-repair-challenges-v1.json"
    with target.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(data, indent=2, sort_keys=True)+"\n")
    fixture = dict(repair_version=REPAIR_V1, feedback=feedback(REPAIR_V1, "invalid_reference"),
                   feedback_sha256=hashlib.sha256(feedback(REPAIR_V1, "invalid_reference").encode()).hexdigest(),
                   step_prompt_sha256=hashlib.sha256(STEP_PROMPT.encode()).hexdigest(),
                   request_shape=[{"role": "user", "content": "ArenaObservation:\n<unchanged observation.canonical>"},
                                  {"role": "user", "content": feedback(REPAIR_V1, "invalid_reference")}])
    with (ROOT/"tests/fixtures/arena-step-repair-v1.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(fixture, indent=2, sort_keys=True)+"\n")
    print(data["content_hash"])


if __name__ == "__main__":
    main()
