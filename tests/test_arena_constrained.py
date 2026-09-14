"""Phase 10A finite-language proof, fake transports and frozen-control regression."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

from aig.arena.ai.constrained import (ArenaConstrainedStepController, HeuristicArenaConstrainedStepProvider,
    OllamaArenaConstrainedStepProvider, OpenAIArenaConstrainedStepProvider,
    build_arena_step_legal_wire_schema, wire_metadata, create_constrained_step_provider,
    CONTROL_VERSION, WIRE_SCHEMA_VERSION, resolve_control_version, resolve_wire_schema_version)
from aig.arena.ai.contracts import ArenaTurnPlan, PLAN_SCHEMA_VERSION, ACTION_TYPES, action_from_dict, action_command
from aig.arena.ai.observation import ArenaObservation, OBSERVATION_V2, build_observation
from aig.arena.ai.stepwise import ArenaStepController, HeuristicArenaStepProvider, STEP_PROMPT, parse_step
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark_versions import artifact, frozen_probe, probe_set
from aig.arena.constrained_study import enumerate_schema, prove_catalog, captured_request, measure
from aig.arena.repair_benchmark import challenge_set
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, digest
from aig.settings import Settings, OpenAISettings
from aig.state import Position


def plan(*actions):
    return dict(schema_version=PLAN_SCHEMA_VERSION, actions=list(actions))


class ConstrainedTests(unittest.TestCase):
    def setUp(self):
        for target in ("urllib.request.OpenerDirector.open", "httpx.Client.send", "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("live inference forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def obs(self, name="revive_decision"):
        return build_observation(frozen_probe(name), version=OBSERVATION_V2)

    def language(self, obs, kind="ollama"):
        return {canonical_json(v) for v in enumerate_schema(build_arena_step_legal_wire_schema(obs, kind))}

    def provider(self, kind, outputs, *, repair=True):
        requests = []
        values = iter(outputs)
        if kind == "ollama":
            def request(url, body, timeout):
                payload = json.loads(body)
                requests.append(payload)
                value = next(values)
                if callable(value):
                    value = value(payload)
                return canonical_json(dict(done=True, message=dict(content=value)))
            p = OllamaArenaConstrainedStepProvider(Settings().ollama, requester=request, repair=repair,
                                                 secrets=("canary-secret",))
        else:
            def request(**payload):
                requests.append(payload)
                value = next(values)
                if callable(value):
                    value = value(payload)
                return NS(status="completed", error=None, id="test", _request_id="test", usage=None,
                    output=[NS(type="message", role="assistant", status="completed",
                               content=[NS(type="output_text", text=value)])])
            p = OpenAIArenaConstrainedStepProvider(OpenAISettings(api_key="canary-secret"),
                client=NS(responses=NS(create=request)), repair=repair)
        return p, requests

    def test_versions_and_frozen_recipe_hashes(self):
        self.assertEqual(resolve_control_version(), CONTROL_VERSION)
        self.assertEqual(resolve_wire_schema_version(), WIRE_SCHEMA_VERSION)
        with self.assertRaises(ValueError):
            resolve_control_version("arena-control-stepwise-v1")
        with self.assertRaises(ValueError):
            resolve_wire_schema_version("arena-turn-plan-schema-v1")
        for i in range(1, 6):
            self.assertEqual(artifact(f"arena-benchmark-v{i}")["version"], f"arena-benchmark-v{i}")
        recipe = artifact("arena-benchmark-v5")
        self.assertEqual(recipe["control_version"], CONTROL_VERSION)
        self.assertEqual(recipe["wire_schema"], WIRE_SCHEMA_VERSION)
        self.assertEqual(recipe["schema"], PLAN_SCHEMA_VERSION)
        self.assertEqual(recipe["repair"], "arena-step-repair-v1")
        self.assertEqual(hashlib.sha256(STEP_PROMPT.encode()).hexdigest(), "791f842d479527929f504c505254cd2d21dee668b2550f31cad5e7458b572d5f")

    def test_frozen_control_source_preservation(self):
        root = Path(__file__).resolve().parents[1]
        inventory = json.loads((root/"tests/fixtures/arena-phase10a-preservation.json").read_text())
        for path, expected in inventory.items():
            # Portable source-content baseline; the separate task audit checks
            # exact original bytes, including workspace line endings.
            raw = (root/path).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected, path)

    def test_exact_finite_language_all_probe_steps_and_heuristic_equivalence(self):
        variants = set()
        for name in probe_set()["probes"]:
            with self.subTest(probe=name):
                generic, constrained = ArenaSimulation(frozen_probe(name)), ArenaSimulation(frozen_probe(name))
                gt = ArenaStepController(HeuristicArenaStepProvider()).run_turn(generic)
                ct = ArenaConstrainedStepController(HeuristicArenaConstrainedStepProvider()).run_turn(constrained)
                self.assertEqual(generic.trace(), constrained.trace())
                self.assertEqual(gt["action_sequence"], ct["action_sequence"])
                self.assertEqual(gt["ap_executed"], ct["ap_executed"])
                self.assertEqual(replay(constrained.trace()).trace(), constrained.trace())
                for row in ct["steps"]:
                    obs = ArenaObservation.from_dict(row["observation"])
                    self.assertTrue(prove_catalog(obs)["exact"])
                    variants.update(a["type"] for a in obs.to_dict()["legal_actions"])
                    self.assertIn(canonical_json(row["decision"]), self.language(obs))
                    self.assertEqual(row["wire_schema_hash"], digest(build_arena_step_legal_wire_schema(obs)))
                    self.assertEqual(row["command_result"], constrained.trace()["entries"][row["command_index"]])
        # Revive restores a wounded ally, exposing Heal on the next observation.
        self.assertEqual(variants, set(ACTION_TYPES))

    def test_deterministic_order_and_detached_schema(self):
        obs = self.obs()
        original = obs.canonical
        first = build_arena_step_legal_wire_schema(obs)
        second = build_arena_step_legal_wire_schema(obs, "openai")
        self.assertEqual(canonical_json(first), canonical_json(second))
        outputs = enumerate_schema(first)
        self.assertEqual(outputs, [plan(), *[plan(a) for a in obs.to_dict()["legal_actions"]]])
        first["properties"].clear()
        self.assertEqual(build_arena_step_legal_wire_schema(obs), second)
        self.assertEqual(obs.canonical, original)

    def test_revive_historical_boundary_and_reference_exclusion(self):
        obs = self.obs()
        self.assertEqual(obs.hash, "52a7fa2ed56b339b7c1025a9030ada6c59591a381f1722f68a9378f141485cf5")
        actions = obs.to_dict()["legal_actions"]
        self.assertEqual(len(actions), 21)
        self.assertEqual(actions[-1], dict(type="revive", unit_id="actor", target_id="ally"))
        language = self.language(obs)
        for action in actions:
            self.assertIn(canonical_json(plan(action)), language)
        for target in ("enemy", "actor", "arbitrary-stale-target"):
            self.assertNotIn(canonical_json(plan(dict(type="heal", unit_id="actor", target_id=target))), language)

    def test_adversarial_mutations_and_all_cross_combinations(self):
        for name in probe_set()["probes"]:
            obs = self.obs(name)
            catalog = obs.to_dict()["legal_actions"]
            language = self.language(obs)
            for action in catalog:
                mutations = []
                for key, value in (("unit_id", "canary-secret"), ("type", "invented"), ("extra", 1)):
                    mutations.append(dict(action, **{key: value}))
                for key in ("destination", "target_position"):
                    if key in action:
                        mutations.extend(dict(action, **{key: p}) for p in ({"x": 99, "y": 0}, {"x": True, "y": 0}, {"x": 0}, {"x": 0, "y": 0, "z": 0}))
                if "target_id" in action:
                    mutations.append(dict(action, target_id="nonexistent"))
                for mutation in mutations:
                    self.assertNotIn(canonical_json(plan(mutation)), language)
                self.assertNotIn(canonical_json(plan(action, action)), language)
                self.assertNotIn(canonical_json(dict(actions=[action])), language)
            # Recombining individually valid fields is accepted iff the whole action is legal.
            for a, b in product_actions(catalog):
                mixed = dict(a, unit_id=b["unit_id"])
                self.assertEqual(canonical_json(plan(mixed)) in language, mixed in catalog)
                if "target_id" in a and "target_id" in b:
                    mixed = dict(a, target_id=b["target_id"])
                    self.assertEqual(canonical_json(plan(mixed)) in language, mixed in catalog)

    def test_duplicate_catalog_fails_and_empty_allows_only_endturn(self):
        facts = self.obs().to_dict()
        facts["legal_actions"].append(facts["legal_actions"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_arena_step_legal_wire_schema(ArenaObservation(canonical_json(facts)))
        facts["legal_actions"] = []
        obs = ArenaObservation(canonical_json(facts))
        for kind in ("ollama", "openai"):
            self.assertEqual(enumerate_schema(build_arena_step_legal_wire_schema(obs, kind)), [plan()])
            p, requests = self.provider(kind, [canonical_json(plan())])
            self.assertEqual(p.create_step(obs), ArenaTurnPlan())
            self.assertEqual(len(requests), 1)

    def test_ap_and_no_provider_call_at_zero(self):
        state = frozen_probe("revive_decision")
        state.action_points_remaining = 1
        obs = build_observation(state, version=OBSERVATION_V2)
        self.assertFalse(any(a["type"] in ("revive", "fireball", "snipe") for a in obs.to_dict()["legal_actions"]))
        self.assertTrue(prove_catalog(obs)["exact"])
        state.action_points_remaining = 0
        p, requests = self.provider("ollama", [])
        turn = ArenaConstrainedStepController(p).run_turn(ArenaSimulation(state))
        self.assertEqual(turn["steps_requested"], 0)
        self.assertEqual(requests, [])

    def test_provider_valid_actions_and_endturn(self):
        obs = self.obs()
        for kind in ("ollama", "openai"):
            for action in (None, obs.to_dict()["legal_actions"][-1]):
                expected = plan(action) if action else plan()
                p, requests = self.provider(kind, [canonical_json(expected)])
                self.assertEqual(p.create_step(obs).to_dict(), expected)
                request = requests[0]
                schema = request["format"] if kind == "ollama" else request["text"]["format"]["schema"]
                self.assertEqual(schema, build_arena_step_legal_wire_schema(obs, kind))
                self.assertEqual(p.last_trace["wire_schema_hash"], digest(schema))
                if kind == "openai":
                    self.assertTrue(request["text"]["format"]["strict"])
                with self.assertRaises(ValueError):
                    p.output_schema()

    def test_invalid_fake_response_repair_same_schema_and_secret_safety(self):
        obs = self.obs()
        invalid = canonical_json(plan(dict(type="heal", unit_id="actor", target_id="canary-secret")))
        for kind in ("ollama", "openai"):
            p, requests = self.provider(kind, [invalid, canonical_json(plan())])
            turn = ArenaConstrainedStepController(p).run_turn(ArenaSimulation(frozen_probe("revive_decision")))
            self.assertEqual(turn["repair_requests"], 1)
            self.assertTrue(turn["steps"][0]["repair_succeeded"])
            key = "format" if kind == "ollama" else "text"
            self.assertEqual(requests[0][key], requests[1][key])
            self.assertNotIn("canary-secret", canonical_json(turn))
            self.assertNotIn("canary-secret", canonical_json(p.last_trace))
            self.assertNotIn("canary-secret", canonical_json(requests))
            messages = requests[1]["messages"][1:] if kind == "ollama" else requests[1]["input"]
            self.assertIn("Copy one complete action", messages[-1]["content"])
            self.assertNotIn("Rejected decision and factual diagnostic", messages[-1]["content"])

    def test_invalid_output_no_repair_and_failed_repair(self):
        for kind in ("ollama", "openai"):
            p, requests = self.provider(kind, ["{}"], repair=False)
            with self.assertRaises(ArenaProviderError) as error:
                p.create_step(self.obs())
            self.assertEqual(error.exception.category, "schema_validation")
            self.assertEqual(len(requests), 1)
            p, requests = self.provider(kind, ["{}", "{}"])
            with self.assertRaises(ArenaProviderError) as error:
                p.create_step(self.obs())
            self.assertEqual(error.exception.category, "repair_failed")
            self.assertEqual(len(requests), 2)

    def test_repair_v2_and_generic_provider_cannot_enter_mode(self):
        with self.assertRaises(ValueError):
            OllamaArenaConstrainedStepProvider(Settings().ollama, repair_version="arena-step-repair-v2")
        with self.assertRaises(ValueError):
            ArenaConstrainedStepController(HeuristicArenaStepProvider())
        self.assertIsInstance(create_constrained_step_provider(Settings(), "heuristic"), HeuristicArenaConstrainedStepProvider)
        with self.assertRaises(ValueError):
            build_arena_step_legal_wire_schema(build_observation(frozen_probe("revive_decision")))

    def test_fresh_schemas_after_move_down_revive_bash_fireball_and_stale_rejection(self):
        cases = [("revive_decision", "move"), ("revive_decision", "revive"),
                 ("shield_bash_position", "shield_bash"), ("fireball_friendly_fire", "fireball"),
                 ("fireball_friendly_fire", "attack")]
        for name, kind in cases:
            state = frozen_probe(name)
            if kind == "attack":
                state.units["enemy2"].hp = 1
                state.units["actor"].position = Position(3, 3)
            if kind == "fireball":
                state.units["enemy2"].hp = 4
            obs = build_observation(state, version=OBSERVATION_V2)
            action = next(a for a in obs.to_dict()["legal_actions"] if a["type"] == kind and
                (kind != "attack" or a.get("target_id") == "enemy2") and
                (kind != "fireball" or a.get("target_position") == {"x": 4, "y": 1}))
            p, requests = self.provider("ollama", [canonical_json(plan(action)), canonical_json(plan())])
            turn = ArenaConstrainedStepController(p).run_turn(ArenaSimulation(state))
            self.assertEqual(len(requests), 2)
            self.assertNotEqual(requests[0]["format"], requests[1]["format"])
            for index, row in enumerate(turn["steps"]):
                self.assertEqual(row["wire_schema_hash"], digest(requests[index]["format"]))
            after = ArenaObservation(canonical_json(turn["steps"][1]["observation"]))
            stale = next(a for a in obs.to_dict()["legal_actions"] if a not in after.to_dict()["legal_actions"])
            self.assertNotIn(canonical_json(plan(stale)), self.language(after))
            with self.assertRaises(ArenaProviderError):
                parse_step(canonical_json(plan(stale)), after)

    def test_historical_failure_challenges_and_known_patterns(self):
        count = 0
        for challenge in challenge_set()["challenges"]:
            if challenge["historical"]["provider"] != "ollama":
                continue
            obs = ArenaObservation.from_dict(challenge["observation"])
            self.assertTrue(prove_catalog(obs)["exact"])
            self.assertNotIn(canonical_json(challenge["invalid_decision"]), self.language(obs))
            if challenge["id"] == "qwen-early":
                for target in ("red-cleric", "blue-cleric", "stale-target"):
                    self.assertNotIn(canonical_json(plan(dict(type="heal", unit_id="blue-cleric", target_id=target))), self.language(obs))
            count += 1
        self.assertGreater(count, 0)

    def test_request_measurements_and_unchanged_message_contract(self):
        for obs, label in ((self.obs("snipe_vs_basic"), "simple"), (self.obs(), "revive"),
                           (build_observation(ArenaSimulation().state, version=OBSERVATION_V2), "opening")):
            row = measure(obs, label)
            for kind in ("ollama", "openai"):
                self.assertTrue(row["providers"][kind]["message_bytes_unchanged"])
                first = captured_request(obs, kind, True)
                self.assertEqual(first, captured_request(obs, kind, True))
            self.assertEqual(row["providers"]["ollama"]["generic"]["schema_bytes"], 2567)


def product_actions(actions):
    return ((a, b) for a in actions for b in actions)


if __name__ == "__main__":
    unittest.main()
