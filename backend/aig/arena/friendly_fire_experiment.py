"""Prepare offline; run one explicitly selected Luna arm only with --live."""
import argparse
import hashlib
import json
from pathlib import Path

from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.arena.ai.friendly_fire_prompt import BEHAVIOR_PROMPTS, PROMPT_VERSION, LunaBehaviorProvider
from aig.arena.ai.prompts import PROMPT_VERSION as OLD_PROMPT
from aig.arena.ai.observation import build_observation, OBSERVATION_VERSION
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.validation import ArenaProviderError, openai_turn_plan_schema
from aig.arena.benchmark_provider import checked_plan
from aig.arena.benchmark_metrics import inference_metrics
from aig.arena.friendly_fire_fixtures import CASES, FIXTURE_VERSION, fixture, analyze_fireball
from aig.arena.commands import ArenaFireball
from aig.arena.replay import ArenaSimulation
from aig.arena.snapshots import canonical_json, to_snapshot, from_snapshot, digest
from aig.settings import Settings, load_settings

VERSION = "arena-luna-fireball-experiment-v1"
ROOT = Path(__file__).resolve().parents[3]


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sources():
    paths = sorted((ROOT / "backend/aig").rglob("*.py"))
    paths += sorted((ROOT / "backend/aig/arena/benchmark_artifacts").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def prepare(path):
    rows = []
    for name in CASES:
        state, command = fixture(name)
        obs = build_observation(state)
        rows.append(dict(name=name, snapshot=to_snapshot(state), observation_hash=obs.hash,
                         illustrative_impact=analyze_fireball(state, command)))
    sizes = {}
    for version in (OLD_PROMPT, PROMPT_VERSION):
        prompt = BEHAVIOR_PROMPTS[version]
        obs = build_observation(from_snapshot(rows[0]["snapshot"]))
        messages = [dict(role="user", content="ArenaObservation:\n" + obs.canonical)]
        sizes[version] = dict(prompt_bytes=len(prompt.encode()),
            luna_input_bytes=len(canonical_json(dict(instructions=prompt, input=messages)).encode()),
            qwen_messages_bytes=len(canonical_json([dict(role="system", content=prompt), *messages]).encode()))
    result = dict(version=VERSION, old_prompt=OLD_PROMPT, new_prompt=PROMPT_VERSION,
        prompt_hashes={v: hashlib.sha256(BEHAVIOR_PROMPTS[v].encode()).hexdigest() for v in (OLD_PROMPT, PROMPT_VERSION)},
        observation_version=OBSERVATION_VERSION, schema_version=PLAN_SCHEMA_VERSION,
        schema_hash=digest(openai_turn_plan_schema()), control_version="arena-control-full-turn-v1",
        model_profile=resolve_model_profile("openai")[0], model_configuration=resolve_model_profile("openai")[1],
        fixture_version=FIXTURE_VERSION, fixture_hash=digest(rows), fixtures=rows,
        trials_per_fixture=4, decisions_per_arm=24, request_ceiling_per_arm=48,
        repair=True, sizes=sizes, source_files=sources())
    path = Path(path)
    if path.exists():
        raise ValueError("preparation artifact already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, result)
    return result


def run(plan_path, prompt_version, output, *, settings=None, provider_factory=LunaBehaviorProvider):
    saved = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if (saved["version"] != VERSION or saved["source_files"] != sources()
            or saved["fixture_hash"] != digest(saved["fixtures"])
            or saved["trials_per_fixture"] != 4 or saved["decisions_per_arm"] != 24
            or saved["request_ceiling_per_arm"] != 48
            or [r["name"] for r in saved["fixtures"]] != list(CASES)):
        raise ValueError("frozen experiment mismatch; prepare and review again")
    if prompt_version not in (OLD_PROMPT, PROMPT_VERSION):
        raise ValueError("unknown arm")
    if saved["prompt_hashes"][prompt_version] != hashlib.sha256(BEHAVIOR_PROMPTS[prompt_version].encode()).hexdigest():
        raise ValueError("prompt mismatch")
    settings = settings or Settings()
    if inference_configuration("openai", settings) != saved["model_configuration"]:
        raise ValueError("requires unchanged luna-config-v1; settings were not modified")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output / "manifest.json", saved | dict(selected_prompt=prompt_version))
    provider = provider_factory(settings.openai, prompt_version=prompt_version, repair=True)
    if provider.configuration() != saved["model_configuration"] or provider.prompt_version != prompt_version:
        raise ValueError("provider mismatch")
    requests = 0
    def boundary():
        nonlocal requests
        if sources() != saved["source_files"]:
            raise ArenaProviderError("source_mutation")
        if requests >= 48:
            raise ArenaProviderError("request_ceiling")
        requests += 1
    provider.before_request = boundary
    report = dict(status="complete", prompt_version=prompt_version, runs=[])
    for trial in range(1, 5):
        for entry in saved["fixtures"]:
            sim = ArenaSimulation(from_snapshot(entry["snapshot"]))
            obs = build_observation(sim.state)
            if obs.hash != entry["observation_hash"]:
                raise ValueError("observation mismatch")
            plan, call = checked_plan(provider, "openai", obs)
            row = dict(fixture=entry["name"], trial=trial, inference=call,
                       first_response_valid=bool(call["attempts"] and not call["attempts"][0]["error_category"]),
                       fireballs=[], action_results=[], alternative_actions=[], execution=None,
                       fireball_chosen=bool(plan and any(a.type == "fireball" for a in plan.actions)))
            if plan is not None:
                def execute(command):
                    effect = analyze_fireball(sim.state, command) if type(command) is ArenaFireball else None
                    sim.execute(command)
                    row["action_results"].append(dict(command_type=type(command).__name__,
                        terminal_result=sim.state.winner_player_id,
                        immediate_win=sim.state.winner_player_id == "blue"))
                    if effect is not None:
                        row["fireballs"].append(effect)
                row["alternative_actions"] = [a.to_dict() for a in plan.actions if a.type != "fireball"]
                row["execution"] = execute_arena_turn(sim.state, plan, execute_command=execute).to_dict()
            row.update(command_trace=sim.trace(), final_snapshot=to_snapshot(sim.state),
                       terminal_result=sim.state.winner_player_id,
                       immediate_win=sim.state.winner_player_id == "blue")
            report["runs"].append(row)
            if plan is None or row["execution"]["invalid_action"]:
                report["status"] = "stopped_on_failure"
            balls = [b for r in report["runs"] for b in r["fireballs"]]
            report["aggregate"] = dict(zero_enemy_fireballs=sum(not b["enemy_ids"] for b in balls),
                friendly_only_fireballs=sum(bool(b["friendly_ids"]) and not b["enemy_ids"] for b in balls),
                friendly_damage=sum(b["friendly_damage"] for b in balls),
                productive_fireballs=sum(b["enemy_damage"] > 0 for b in balls),
                immediate_win_plans=sum(r["immediate_win"] for r in report["runs"]),
                immediate_win_actions=sum(a["immediate_win"] for r in report["runs"] for a in r["action_results"]),
                first_response_valid=sum(r["first_response_valid"] for r in report["runs"]),
                first_response_valid_rate=sum(r["first_response_valid"] for r in report["runs"])/len(report["runs"]))
            report["inference_metrics"] = inference_metrics([r["inference"] for r in report["runs"]], None)
            report["requests"] = requests
            write(output / "summary.json", report)
            if report["status"] != "complete":
                return report
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--prompt", choices=(OLD_PROMPT, PROMPT_VERSION))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--methodology", type=Path, help="Reviewed corrected-methodology manifest")
    args = parser.parse_args()
    if args.live and args.methodology and args.plan and args.prompt and args.output and not args.prepare:
        from aig.arena.friendly_fire_methodology import run_corrected
        result = run_corrected(args.plan, args.methodology, args.prompt, args.output, settings=load_settings())
        return 0 if result["status"] == "complete" else 1
    elif args.prepare and not args.live and not args.methodology:
        prepare(args.prepare)
    elif args.live and args.plan and args.prompt and args.output and not args.prepare:
        result = run(args.plan, args.prompt, args.output, settings=load_settings())
        return 0 if result["status"] == "complete" else 1
    else:
        parser.error("use --prepare PATH offline, or --live --plan PATH --prompt VERSION --output NEW_DIR")


if __name__ == "__main__":
    raise SystemExit(main())
