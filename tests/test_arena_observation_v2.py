"""Observation-only experiment: deterministic engine checks and fake transports."""

from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from aig.arena.ai.contracts import (ACTION_TYPES, ArenaTurnPlan, AttackAction, SnipeAction,
                                    action_command, action_from_dict)
from aig.arena.ai.executor import execute_arena_turn
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import (ArenaObservation, OBSERVATION_VERSION as V1, OBSERVATION_V2 as V2,
    action_order, build_observation, observation_facts, resolve_observation_version, simulation_state)
from aig.arena.ai.ollama import OllamaArenaTurnProvider
from aig.arena.ai.openai import OpenAIArenaTurnProvider
from aig.arena.ai.prompts import resolve_prompt
from aig.arena.ai.validation import ArenaProviderError, parse_turn_plan
from aig.arena.benchmark import benchmark, main, read_rows, verify_trial
from aig.arena.benchmark_versions import frozen_probe, manifest, probe_set
from aig.arena.commands import ACTION_COSTS, apply_command
from aig.arena.prompt_metrics import is_starting_legal_action, starting_legality
from aig.arena.scenarios import create_scenario
from aig.arena.snapshots import canonical_json, to_snapshot
from aig.settings import Settings, OllamaSettings, OpenAISettings

PROMPT = "arena-turn-prompt-v2"


class ObservationV2Tests(unittest.TestCase):
    def setUp(self):
        for target in ("urllib.request.OpenerDirector.open", "httpx.Client.send",
                       "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("Live network forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def states(self):
        yield create_scenario()
        injured = create_scenario()
        injured.units["blue-cleric"].hp -= 1
        yield injured
        for name in probe_set()["probes"]:
            yield frozen_probe(name)
        record = json.loads((Path(__file__).parent / "fixtures/arena-observation-v1-midgame.json").read_text())
        yield simulation_state(ArenaObservation.from_dict(record["observation"]))

    def provider(self, name, outputs=None):
        outputs = outputs or [canonical_json(ArenaTurnPlan().to_dict())]
        if name == "ollama":
            call = Mock(side_effect=[canonical_json(dict(done=True, message=dict(content=r))) for r in outputs])
            provider = OllamaArenaTurnProvider(OllamaSettings(), requester=call, prompt_version=PROMPT)
        else:
            call = Mock(side_effect=[NS(status="completed", error=None, output=[NS(type="message", role="assistant",
                status="completed", content=[NS(type="output_text", text=r)])]) for r in outputs])
            provider = OpenAIArenaTurnProvider(OpenAISettings(api_key="offline"),
                client=NS(responses=NS(create=call)), prompt_version=PROMPT)
        return provider, call

    def test_versions_and_default_never_promote(self):
        for alias in (None, "", "latest", "v1", V1):
            self.assertEqual(resolve_observation_version(alias), V1)
        for alias in ("v2", V2):
            self.assertEqual(resolve_observation_version(alias), V2)
        for alias in ("unknown", "arena-observation-v999"):
            with self.assertRaises(ValueError):
                build_observation(create_scenario(), version=alias)
        self.assertEqual(build_observation(create_scenario()).version, V1)

    def test_v1_frozen_hashes_and_canonical_bytes(self):
        opening = build_observation(create_scenario())
        self.assertEqual(len(opening.canonical.encode()), 7397)
        self.assertEqual(opening.hash, "d11799c7e917d3353962ca104b87f14b3fc64f6f35b2e9ff169baa7656c48279")
        for name, record in probe_set()["probes"].items():
            self.assertEqual(build_observation(frozen_probe(name)).hash, record["observation_hash"])
        record = json.loads((Path(__file__).parent / "fixtures/arena-observation-v1-midgame.json").read_text())
        state = simulation_state(ArenaObservation.from_dict(record["observation"]))
        self.assertEqual(build_observation(state).canonical, canonical_json(record["observation"]))
        self.assertEqual(build_observation(state).hash, record["observation_hash"])

    def test_v2_lossless_state_and_rule_information(self):
        for state in self.states():
            v1, v2 = build_observation(state), build_observation(state, version=V2)
            # Includes every HP, class, status, position, owner, Core, tile, range and rule.
            self.assertEqual(observation_facts(v2), v1.to_dict())
            self.assertEqual(to_snapshot(simulation_state(v2)), to_snapshot(state))
            self.assertEqual(ArenaObservation.from_dict(v2.to_dict()), v2)
            self.assertEqual(v2.to_dict()["legal_actions_state"], "turn_start")

    def test_deterministic_order_and_hash_pin(self):
        state = create_scenario()
        obs = build_observation(state, version=V2)
        state.units = dict(reversed(list(state.units.items())))
        state.cores = dict(reversed(list(state.cores.items())))
        self.assertEqual(build_observation(state, version=V2).canonical, obs.canonical)
        self.assertEqual(obs.hash, "e018b244179069ebcfcca33a5c8266f2b18bc99c64c2774f6868db466965c08c")
        actions = obs.to_dict()["legal_actions"]
        self.assertEqual(actions, sorted(actions, key=action_order))
        self.assertEqual(len(actions), len({canonical_json(a) for a in actions}))

    def test_every_catalog_action_executes_first_with_exact_ap_at_all_budgets(self):
        covered = set()
        for original in self.states():
            for ap in range(6):
                state = deepcopy(original)
                state.action_points_remaining = ap
                before = to_snapshot(state)
                obs = build_observation(state, version=V2)
                for item in obs.to_dict()["legal_actions"]:
                    action = action_from_dict(item)
                    covered.add(action.type)
                    self.assertEqual(action.to_dict(), item)
                    self.assertIn(action.unit_id, state.units)
                    self.assertEqual(state.units[action.unit_id].owner_id, state.active_player_id)
                    detached = deepcopy(state)
                    apply_command(detached, action_command(action, state.active_player_id))
                    self.assertEqual(ap - detached.action_points_remaining, ACTION_COSTS[action.type])
                    self.assertEqual(to_snapshot(state), before)
        self.assertEqual(covered, set(ACTION_TYPES))

    def test_special_actions_explicit_class_and_shape(self):
        for name, kind, unit_type in (("revive_decision", "revive", "cleric"),
            ("snipe_vs_basic", "snipe", "ranger"), ("shield_bash_position", "shield_bash", "knight"),
            ("fireball_friendly_fire", "fireball", "mage")):
            state = frozen_probe(name)
            actions = build_observation(state, version=V2).to_dict()["legal_actions"]
            selected = [a for a in actions if a["type"] == kind]
            self.assertTrue(selected)
            for action in selected:
                self.assertEqual(state.units[action["unit_id"]].unit_type.value, unit_type)
                self.assertEqual(set(action), {"type", "unit_id", "target_position" if kind == "fireball" else "target_id"})

    def test_representative_illegal_actions_absent(self):
        obs = build_observation(create_scenario(), version=V2)
        for action in [dict(type="attack", unit_id="blue-ranger", target_id="red-cleric"),
                       dict(type="revive", unit_id="blue-ranger", target_id="blue-mage"),
                       dict(type="revive", unit_id="blue-cleric", target_id="blue-mage"),
                       dict(type="finish", unit_id="blue-knight", target_id="red-knight"),
                       dict(type="move", unit_id="blue-knight", destination=dict(x=3, y=1))]:
            self.assertFalse(is_starting_legal_action(obs, action))

    def test_historical_distance_six_attack_and_ranger_completeness(self):
        from aig.arena.geometry import distance
        state = create_scenario()
        self.assertEqual(distance(state.units["blue-ranger"].position, state.units["red-cleric"].position), 6)
        self.assertEqual(state.units["blue-ranger"].stats.attack_range, 3)
        v1, v2 = build_observation(state), build_observation(state, version=V2)
        action = AttackAction("blue-ranger", "red-cleric")
        self.assertFalse(is_starting_legal_action(v2, action))
        options = next(u for u in v1.to_dict()["own_team"]["units"] if u["id"] == action.unit_id)["actions"]
        explicit = [a for a in v2.to_dict()["legal_actions"] if a["unit_id"] == action.unit_id]
        self.assertTrue(explicit)
        self.assertEqual(len(explicit), sum(map(len, options.values())))
        self.assertFalse(options["attack"])
        self.assertFalse(options["snipe"])

    def test_membership_prefix_static_and_dynamic_distinction(self):
        state = frozen_probe("snipe_vs_basic")
        plan = ArenaTurnPlan((SnipeAction("actor", "enemy"), SnipeAction("actor", "enemy")))
        for version in (V1, V2):
            obs = build_observation(state, version=version)
            self.assertEqual(starting_legality(obs, plan), dict(first_action_starting_legal=True,
                starting_legal_prefix_length=2, starting_action_membership=[True, True]))
            mixed = ArenaTurnPlan((AttackAction("actor", "enemy"), SnipeAction("actor", "enemy")))
            self.assertEqual(starting_legality(obs, mixed)["starting_legal_prefix_length"], 0)
            self.assertIsNone(starting_legality(obs, ArenaTurnPlan())["first_action_starting_legal"])
        self.assertEqual(execute_arena_turn(state, plan).to_dict()["invalid_action"]["index"], 1)

    def test_membership_exact_rejects_extra_metadata_and_boolean_coordinates(self):
        obs = build_observation(create_scenario(), version=V2)
        action = next(a for a in obs.to_dict()["legal_actions"] if a["type"] == "move")
        self.assertTrue(is_starting_legal_action(obs, dict(reversed(list(action.items())))))
        self.assertFalse(is_starting_legal_action(obs, dict(action, ap_cost=1)))
        self.assertFalse(is_starting_legal_action(obs, dict(action, destination=dict(x=True, y=0))))

    def test_no_static_validation_or_heuristic_behavior_change(self):
        for state in self.states():
            a, b = build_observation(state), build_observation(state, version=V2)
            heuristic = HeuristicArenaTurnProvider()
            self.assertEqual(heuristic.create_turn_plan(a), heuristic.create_turn_plan(b))
            for actor in state.units.values():
                for kind in ACTION_TYPES:
                    target = {"destination": dict(x=3, y=1)} if kind == "move" else {"target_position": dict(x=3, y=1)} if kind == "fireball" else {"target_id": "red-core"}
                    plan = ArenaTurnPlan((action_from_dict(dict(type=kind, unit_id=actor.id, **target)),))
                    outcomes = []
                    for obs in (a, b):
                        try:
                            outcomes.append(parse_turn_plan(canonical_json(plan.to_dict()), obs))
                        except ArenaProviderError as error:
                            outcomes.append(error.category)
                    self.assertEqual(*outcomes)

    def test_forged_catalog_stats_and_board_rejected(self):
        obs = build_observation(create_scenario(), version=V2)
        changes = [lambda d: d["legal_actions"].append(dict(type="attack", unit_id="blue-ranger", target_id="red-cleric")),
                   lambda d: d["legal_actions"].reverse(),
                   lambda d: d["unit_types"]["ranger"]["stats"].update(damage=900),
                   lambda d: d["board"]["blocked_tiles"].append(dict(x=99, y=99))]
        for change in changes:
            data = obs.to_dict()
            change(data)
            with self.assertRaises(ValueError):
                ArenaObservation.from_dict(data)

    def test_both_providers_serialize_selected_version_and_preserve_repairs(self):
        for name in ("ollama", "openai"):
            payloads = []
            for version in (V1, V2):
                obs = build_observation(create_scenario(), version=version)
                provider, call = self.provider(name, ["invalid", canonical_json(ArenaTurnPlan().to_dict())])
                self.assertEqual(provider.create_turn_plan(obs), ArenaTurnPlan())
                self.assertEqual(provider.last_trace["observation_version"], version)
                self.assertEqual(provider.last_trace["retry_count"], 1)
                selected = []
                for invocation in call.call_args_list:
                    data = json.loads(invocation.args[1]) if name == "ollama" else deepcopy(invocation.kwargs)
                    messages = data["messages"] if name == "ollama" else data["input"]
                    prompt = messages.pop(0)["content"] if name == "ollama" else data.pop("instructions")
                    self.assertEqual(prompt, resolve_prompt(PROMPT)[1])
                    self.assertEqual(messages.pop(0)["content"], "ArenaObservation:\n" + obs.canonical)
                    selected.append(data)
                payloads.append(selected)
            self.assertEqual(*payloads)  # Only observation content differs; feedback/schema/settings frozen.

    def test_manifest_contracts_and_recipe_provenance(self):
        result = manifest(["ollama", "openai"], Settings(), {}, prompt_version=PROMPT, observation_version=V2)
        for key, value in dict(promptVersion=PROMPT, observationVersion=V2, baseRecipeObservationVersion=V1,
            planSchemaVersion="arena-turn-plan-schema-v1", benchmarkVersion="arena-benchmark-v1", probeSetVersion="arena-probes-v1").items():
            self.assertEqual(result[key], value)
        self.assertEqual(result["experimentOverrides"], dict(promptVersion=PROMPT, observationVersion=V2))
        self.assertEqual(result["providers"]["ollama"]["modelConfigVersion"], "qwen-config-v1")
        self.assertEqual(result["providers"]["openai"]["modelConfigVersion"], "luna-config-v1")

    def test_cli_selection_saved_rows_and_replay(self):
        with TemporaryDirectory() as temp:
            for version in (V1, V2):
                made = []
                def factory(settings, name, **kwargs):
                    provider, call = self.provider(name)
                    call.side_effect = None
                    call.return_value = canonical_json(dict(done=True, message=dict(content=canonical_json(ArenaTurnPlan().to_dict()))))
                    made.append(call)
                    return provider
                output = Path(temp) / version
                with redirect_stdout(StringIO()):
                    code = main(["--mode", "probes", "--blue-provider", "ollama", "--prompt-version", PROMPT,
                        "--observation-version", version, "--probe", "revive_decision", "--probe-trials", "1",
                        "--output", str(output)], provider_factory=factory)
                self.assertEqual(code, 0)
                report = json.loads((output / "summary.json").read_text())
                self.assertEqual(report["preflight"][0]["observation_version"], version)
                trial = Path(report["runs"][0]["directory"])
                for filename in ("plans.jsonl", "inference.jsonl"):
                    self.assertEqual(read_rows(trial / filename)[0]["observation_version"], version)
                self.assertEqual(read_rows(trial / "observations.jsonl")[0]["observation"]["schema_version"], version)
                self.assertTrue(verify_trial(trial)["success"])
                saved = json.loads((trial / "manifest.json").read_text())
                saved.pop("observationVersion")
                (trial / "manifest.json").write_text(json.dumps(saved))
                self.assertEqual(verify_trial(trial)["success"], version == V1)

    def test_unknown_version_stops_before_factory_or_output(self):
        with TemporaryDirectory() as temp:
            output = Path(temp) / "new"
            factory = Mock()
            with self.assertRaises(ValueError):
                benchmark(output=output, observation_version="unknown", provider_factory=factory)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                main(["--observation-version", "unknown", "--output", str(output)], provider_factory=factory)
            factory.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
