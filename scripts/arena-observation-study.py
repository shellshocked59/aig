"""Offline V1/V2 reconstruction only. No provider or network code is invoked."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from aig.arena.ai.contracts import action_command, action_from_dict
from aig.arena.ai.observation import (ArenaObservation, OBSERVATION_V2, build_observation,
                                      observation_facts, simulation_state)
from aig.arena.ai.prompts import resolve_prompt
from aig.arena.benchmark_versions import frozen_probe, probe_set
from aig.arena.commands import ACTION_COSTS, apply_command
from aig.arena.geometry import distance
from aig.arena.prompt_metrics import is_starting_legal_action
from aig.arena.snapshots import canonical_json, to_snapshot


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def measure(state, label, source):
    v1 = build_observation(state)
    v2 = build_observation(state, version=OBSERVATION_V2)
    assert observation_facts(v2) == v1.to_dict()
    assert to_snapshot(simulation_state(v2)) == to_snapshot(state)
    assert ArenaObservation.from_dict(v2.to_dict()) == v2
    actions = v2.to_dict()["legal_actions"]
    for item in actions:
        action = action_from_dict(item)
        detached = deepcopy(state)
        apply_command(detached, action_command(action, state.active_player_id))
        assert state.action_points_remaining - detached.action_points_remaining == ACTION_COSTS[action.type]
    a, b = len(v1.canonical.encode("utf-8")), len(v2.canonical.encode("utf-8"))
    prompt = resolve_prompt("arena-turn-prompt-v2")[1]
    # A transparent heuristic, not a model tokenizer. Anchor to observed opening input.
    # V1 opening has 7397 ASCII bytes; prompts, schema and framing remain fixed.
    estimated = sorted(round(3317 + (b - 7397) / divisor) for divisor in (3, 4))
    return dict(label=label, source=source, turn=state.turn, player=state.active_player_id,
                v1_bytes=a, v2_bytes=b, delta_bytes=b-a, reduction_percent=round(100*(a-b)/a, 2),
                legal_action_count=len(actions), explicit_actor_count=sum("unit_id" in x for x in actions),
                first_action_execution_checks=len(actions), v1_hash=v1.hash, v2_hash=v2.hash,
                prompt_plus_observation_bytes=len(prompt.encode())+b,
                estimated_qwen_input_tokens=estimated,
                estimated_context_after_256_output=[3840-estimated[1], 3840-estimated[0]])


def study(history):
    probes = [measure(frozen_probe(name), name, "arena-probes-v1:" + name)
              for name in probe_set()["probes"]]
    matches, failures = [], []
    for path in sorted(history.rglob("observations.jsonl")):
        plans = rows(path.with_name("plans.jsonl"))
        for index, row in enumerate(rows(path)):
            v1 = ArenaObservation.from_dict(row["observation"])
            assert v1.hash == row["observation_hash"]
            state = simulation_state(v1)
            result = measure(state, path.relative_to(history).as_posix() + f":{index+1}",
                             path.as_posix() + f":{index+1}")
            matches.append(result)
            if index >= len(plans) or plans[index]["provider_type"] != "ollama":
                continue
            action = action_from_dict(plans[index]["plan"]["actions"][0])
            v2 = build_observation(state, version=OBSERVATION_V2)
            actor, target = state.units[action.unit_id], state.units[action.target_id]
            ranger_options = [a for a in v2.to_dict()["legal_actions"] if a["unit_id"] == actor.id]
            assert action.type == "attack" and actor.unit_type.value == "ranger"
            assert target.unit_type.value == "cleric" and distance(actor.position, target.position) == 6
            assert not is_starting_legal_action(v2, action)
            original_options = next(u for u in v1.to_dict()["own_team"]["units"] if u["id"] == actor.id)["actions"]
            assert len(ranger_options) == sum(map(len, original_options.values()))
            failures.append(dict(source=result["source"], attempted=action.to_dict(), absent=True,
                                 distance=6, attack_range=actor.stats.attack_range,
                                 ranger_actions=ranger_options, v2_hash=v2.hash))
    return dict(observation_version=OBSERVATION_V2, prompt_version="arena-turn-prompt-v2",
                token_estimate_method="No local tokenizer installed. Opening input anchor 3317; signed observation character delta / 3..4. Fixed schema/prompt/framing. Approximate, excludes repair; not proof of fit.",
                probes=probes, matches=matches, qwen_failures=failures,
                summary=dict(probe_mean_v1_bytes=sum(p["v1_bytes"] for p in probes)/len(probes),
                             probe_mean_v2_bytes=sum(p["v2_bytes"] for p in probes)/len(probes),
                             historical_observations=len(matches), qwen_failures=len(failures),
                             catalog_execution_checks=sum(r["first_action_execution_checks"] for r in probes+matches),
                             larger_match_observations=sum(r["delta_bytes"] > 0 for r in matches)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.history.is_dir() or not list(args.history.rglob("observations.jsonl")):
        parser.error("history must contain stored full-match observations")
    if args.output.exists():
        parser.error("output must be new; historical evidence is never overwritten")
    result = study(args.history)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(canonical_json(result["summary"]))


if __name__ == "__main__":
    main()
