"""Phase 7B: offline stepwise feedback, adapter reuse and evidence tests."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import json
import unittest
from unittest.mock import Mock, patch

from aig.arena.ai.contracts import (ArenaTurnPlan, AttackAction, FinishAction, ShieldBashAction,
    ReviveAction, FireballAction, SnipeAction, ArenaPosition, action_from_dict, turn_plan_schema)
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.ai.observation import ArenaObservation, build_observation, OBSERVATION_V2
from aig.arena.ai.stepwise import (ArenaStepController, HeuristicArenaStepProvider, OllamaArenaStepProvider,
    OpenAIArenaStepProvider, STEP_PROMPT_VERSION, STEP_PROMPT, STEP_PROMPTS, parse_step, checked_step)
from aig.arena.ai.validation import ArenaProviderError
from aig.arena.benchmark import benchmark, main
from aig.arena.benchmark_versions import frozen_probe, artifact, probe_set
from aig.arena.replay import ArenaSimulation, replay
from aig.arena.snapshots import canonical_json, to_snapshot
from aig.arena.stepwise_benchmark import (benchmark_stepwise, verify_stepwise_trial, decision_usage, validate_pricing)
from aig.settings import Settings, OpenAISettings
from aig.state import Position


def raw(*actions):
    return canonical_json(ArenaTurnPlan(tuple(actions)).to_dict())


class Scripted:
    name = "heuristic"
    def __init__(self, *plans):
        self.plans = list(plans)
        self.observations = []

    def create_step(self, observation):
        self.observations.append(observation)
        value = self.plans.pop(0) if self.plans else ArenaTurnPlan()
        return value(observation) if callable(value) else value


class FakeOllama(OllamaArenaStepProvider):
    def __init__(self, settings=None, outputs=()):
        self.outputs = list(outputs)
        self.messages = []
        super().__init__((settings or Settings()).ollama)

    def request(self, messages, record):
        self.messages.append(deepcopy(messages))
        record["metrics"] = dict(prompt_eval_count=100, eval_count=10)
        if self.outputs:
            value = self.outputs.pop(0)
            if isinstance(value, Exception):
                raise value
            return value
        observation = ArenaObservation(messages[0]["content"].removeprefix("ArenaObservation:\n"))
        return canonical_json(HeuristicArenaStepProvider().create_step(observation).to_dict())


class StepwiseTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for target in ("urllib.request.OpenerDirector.open", "httpx.Client.send", "openai.resources.responses.Responses.create"):
            guard = patch(target, side_effect=AssertionError("live inference forbidden"))
            guard.start()
            self.addCleanup(guard.stop)

    def obs(self, name="snipe_vs_basic"):
        return build_observation(frozen_probe(name), version=OBSERVATION_V2)

    def test_zero_one_many_and_unchanged_schema(self):
        obs = self.obs()
        self.assertEqual(parse_step(raw(), obs), ArenaTurnPlan())
        action = SnipeAction("actor", "enemy")
        self.assertEqual(parse_step(raw(action), obs).actions, (action,))
        with self.assertRaises(ArenaProviderError):
            parse_step(raw(action, action), obs)
        self.assertEqual(turn_plan_schema()["properties"]["actions"]["maxItems"], 5)
        self.assertEqual(len(ArenaTurnPlan((action, action)).actions), 2)

    def test_exact_catalog_wrong_actor_range_and_reconstruction(self):
        obs = self.obs()
        for action in (AttackAction("actor", "enemy"), AttackAction("enemy", "actor"), SnipeAction("enemy2", "enemy")):
            with self.subTest(action=action), self.assertRaises(ArenaProviderError):
                parse_step(raw(action), obs)
        for a in obs.to_dict()["legal_actions"]:
            self.assertEqual(parse_step(raw(action_from_dict(a)), obs).actions[0].to_dict(), a)

    def test_v1_rejected_before_request(self):
        provider = FakeOllama()
        with self.assertRaises(ArenaProviderError):
            provider.create_step(build_observation(frozen_probe("snipe_vs_basic")))
        self.assertEqual(provider.messages, [])

    def test_prompt_task_and_registry(self):
        self.assertEqual(STEP_PROMPTS[STEP_PROMPT_VERSION], STEP_PROMPT)
        for phrase in ("NOW", "fresh updated observation", "one complete action", "actions=[]", "Do not plan later", "action_points_remaining"):
            self.assertIn(phrase, STEP_PROMPT)
        for phrase in ("attack Core first", "Finish first", "use all AP", "prefer lethal", "focus healer"):
            self.assertNotIn(phrase, STEP_PROMPT)
        with self.assertRaises(TypeError):
            STEP_PROMPTS[STEP_PROMPT_VERSION] = "changed"
        with self.assertRaises(TypeError):
            FakeOllama().create_turn_plan(self.obs())

    def test_attack_down_then_finish_fresh_feedback(self):
        state = frozen_probe("fireball_friendly_fire")
        state.units["enemy2"].hp = 1
        state.units["actor"].position = Position(3, 3)
        attack, finish = AttackAction("actor", "enemy2"), FinishAction("actor", "enemy2")
        def next_step(obs):
            self.assertNotIn(attack.to_dict(), obs.to_dict()["legal_actions"])
            self.assertIn(finish.to_dict(), obs.to_dict()["legal_actions"])
            with self.assertRaises(ArenaProviderError):
                parse_step(raw(attack), obs)
            return ArenaTurnPlan((finish,))
        provider = Scripted(ArenaTurnPlan((attack,)), next_step)
        sim = ArenaSimulation(state)
        turn = ArenaStepController(provider).run_turn(sim)
        self.assertIsNone(turn["error_category"])
        self.assertNotIn("enemy2", sim.state.units)
        self.assertEqual([o.to_dict()["action_points_remaining"] for o in provider.observations], [5, 4, 3])
        self.assertEqual(len(set(o.hash for o in provider.observations)), 3)
        self.assertEqual(replay(sim.trace()).trace(), sim.trace())

    def test_shield_bash_updates_position_and_range(self):
        sim = ArenaSimulation(frozen_probe("shield_bash_position"))
        attack = AttackAction("actor", "enemy")
        def after(obs):
            enemy = obs.to_dict()["enemy_team"]["units"][0]
            self.assertEqual((enemy["x"], enemy["y"]), (4, 2))
            self.assertNotIn(attack.to_dict(), obs.to_dict()["legal_actions"])
            return ArenaTurnPlan()
        turn = ArenaStepController(Scripted(ArenaTurnPlan((ShieldBashAction("actor", "enemy"),)), after)).run_turn(sim)
        self.assertEqual(turn["ap_executed"], 1)

    def test_revive_updates_catalog_and_two_ap(self):
        revive = ReviveAction("actor", "ally")
        def after(obs):
            facts = obs.to_dict()
            self.assertEqual(facts["action_points_remaining"], 3)
            self.assertEqual(next(u for u in facts["own_team"]["units"] if u["id"] == "ally")["status"], "active")
            self.assertNotIn(revive.to_dict(), facts["legal_actions"])
            self.assertTrue(any(a["unit_id"] == "ally" for a in facts["legal_actions"]))
            return ArenaTurnPlan()
        t = ArenaStepController(Scripted(ArenaTurnPlan((revive,)), after)).run_turn(ArenaSimulation(frozen_probe("revive_decision")))
        self.assertEqual((t["ap_executed"], t["ap_unused"]), (2, 3))

    def test_fireball_updates_downed_targets(self):
        state = frozen_probe("fireball_friendly_fire")
        state.units["enemy2"].hp = 4
        def after(obs):
            self.assertEqual(next(u for u in obs.to_dict()["enemy_team"]["units"] if u["id"] == "enemy2")["status"], "downed")
            self.assertNotIn(AttackAction("actor", "enemy2").to_dict(), obs.to_dict()["legal_actions"])
            return ArenaTurnPlan()
        turn = ArenaStepController(Scripted(ArenaTurnPlan((FireballAction("actor", ArenaPosition(4, 1)),)), after)).run_turn(ArenaSimulation(state))
        self.assertIsNone(turn["error_category"])
        self.assertEqual(turn["steps_requested"], 2)

    def test_zero_ap_local_end_no_request(self):
        state = frozen_probe("finish_or_core")
        state.action_points_remaining = 0
        p = Scripted()
        sim = ArenaSimulation(state)
        t = ArenaStepController(p).run_turn(sim)
        self.assertEqual(t["steps_requested"], 0)
        self.assertEqual(p.observations, [])
        self.assertEqual(sim.trace()["entries"][0]["command"]["type"], "arena_end_turn")

    def test_explicit_end_and_terminal_stop(self):
        sim = ArenaSimulation(frozen_probe("finish_or_core"))
        t = ArenaStepController(Scripted()).run_turn(sim)
        self.assertTrue(t["explicit_early_end"])
        self.assertEqual(t["ap_unused"], 5)
        sim = ArenaSimulation(frozen_probe("team_elimination"))
        t = ArenaStepController(Scripted(ArenaTurnPlan((AttackAction("actor", "enemy"),)))).run_turn(sim)
        self.assertEqual(t["steps_requested"], 1)
        self.assertEqual(t["terminal"], "blue")
        self.assertEqual(len(sim.trace()["entries"]), 1)

    def test_max_five_decisions_no_extra_end_request(self):
        t = ArenaStepController(HeuristicArenaStepProvider()).run_turn(ArenaSimulation(frozen_probe("finish_or_core")))
        self.assertEqual((t["steps_requested"], t["actions_executed"], t["ap_unused"]), (5, 5, 0))

    def test_repair_success_and_factual_feedback(self):
        p = FakeOllama(outputs=[raw(SnipeAction("actor", "enemy"), SnipeAction("actor", "enemy")), raw()])
        plan, trace = checked_step(p, "ollama", self.obs())
        self.assertEqual(plan, ArenaTurnPlan())
        self.assertEqual((trace["provider_requests"], trace["repair_requests"]), (2, 1))
        self.assertIn("zero or one action", p.messages[-1][-1]["content"])
        self.assertEqual(p.messages[0][0], p.messages[1][0])

    def test_repair_failure_no_fallback_or_third_call(self):
        p = FakeOllama(outputs=["{}", "{}", raw()])
        sim = ArenaSimulation(frozen_probe("snipe_vs_basic"))
        t = ArenaStepController(p).run_turn(sim)
        self.assertEqual(t["error_category"], "repair_failed")
        self.assertEqual(t["actions_executed"], 0)
        self.assertEqual(len(p.messages), 2)
        self.assertEqual(t["provider_failures"], 1)

    def test_preflight_no_repair_and_transport_category(self):
        p = FakeOllama(outputs=["{}"])
        plan, call = checked_step(p, "ollama", self.obs(), preflight=True)
        self.assertIsNone(plan)
        self.assertEqual(call["provider_requests"], 1)
        self.assertTrue(p.repair)
        p = FakeOllama(outputs=[ArenaProviderError("transport_failure")])
        _, call = checked_step(p, "ollama", self.obs())
        self.assertEqual(call["error_category"], "transport_failure")

    def test_contaminated_provider_rejected(self):
        p = FakeOllama()
        original = p.create_step
        def contaminated(obs):
            result = original(obs)
            p._last_trace["fallback_used"] = True
            return result
        p.create_step = contaminated
        t = ArenaStepController(p).run_turn(ArenaSimulation(frozen_probe("finish_or_core")))
        self.assertEqual(t["error_category"], "provider_mismatch")
        self.assertEqual(t["actions_executed"], 0)

    def test_catalog_execution_failure_is_harness_defect(self):
        sim = ArenaSimulation(frozen_probe("team_elimination"))
        with patch.object(sim, "execute", side_effect=ValueError("engine bug")):
            t = ArenaStepController(HeuristicArenaStepProvider()).run_turn(sim)
        self.assertEqual(t["error_category"], "catalog_execution_defect")
        self.assertEqual(sim.trace()["entries"], [])
        self.assertEqual(t["steps"][0]["execution_error"], "catalog_execution_defect")

    def test_heuristic_deterministic_first_action_on_current_state(self):
        for name in probe_set()["probes"]:
            with self.subTest(probe=name):
                obs = self.obs(name)
                p = HeuristicArenaStepProvider()
                self.assertEqual(p.create_step(obs), p.create_step(obs))
                self.assertEqual(p.create_step(obs).actions, HeuristicArenaTurnProvider().create_turn_plan(obs).actions[:1])

    def test_both_real_adapters_use_fake_transport_and_same_schema(self):
        secret = "sk-stepwise-canary"
        request = Mock(return_value=canonical_json(dict(done=True, message=dict(content=raw()), prompt_eval_count=5, eval_count=2)))
        p = OllamaArenaStepProvider(Settings().ollama, requester=request)
        self.assertEqual(p.create_step(self.obs()), ArenaTurnPlan())
        payload = json.loads(request.call_args.args[1])
        self.assertEqual(payload["format"], turn_plan_schema())
        self.assertEqual(payload["messages"][0]["content"], STEP_PROMPT)
        response = NS(status="completed", error=None, id="resp-test", _request_id="req-test",
            output=[NS(type="reasoning", summary=[secret]), NS(type="message", role="assistant", status="completed",
                content=[NS(type="output_text", text=raw())])],
            usage=NS(input_tokens=100, output_tokens=10, total_tokens=110,
                input_tokens_details=NS(cached_tokens=20), output_tokens_details=NS(reasoning_tokens=0)))
        create = Mock(return_value=response)
        p = OpenAIArenaStepProvider(OpenAISettings(api_key=secret), client=NS(responses=NS(create=create)))
        _, call = checked_step(p, "openai", self.obs())
        self.assertTrue(call["success"])
        self.assertEqual(create.call_args.kwargs["instructions"], STEP_PROMPT)
        self.assertNotIn(secret, canonical_json(call))
        self.assertEqual(call["attempts"][0]["metrics"]["cached_input_tokens"], 20)

    def test_offline_baseline_all_probes_exact_replay_and_versions(self):
        report = benchmark(control_mode="stepwise", mode="probes", output=self.root/"baseline", probe_trials=1)
        self.assertEqual((report["validTrials"], report["providerRequestsIncludingPreflight"]), (7, 0))
        exp = report["experiment"]
        self.assertEqual(exp["benchmarkVersion"], "arena-benchmark-v2")
        self.assertEqual(exp["controlVersion"], "arena-control-stepwise-v1")
        self.assertEqual(exp["promptVersion"], STEP_PROMPT_VERSION)
        self.assertEqual(exp["observationVersion"], OBSERVATION_V2)
        self.assertEqual(exp["probeSetVersion"], "arena-probes-v1")
        self.assertTrue(exp["sourceFiles"])
        self.assertEqual(artifact("arena-benchmark-v1")["prompt"], "arena-turn-prompt-v1")
        self.assertEqual(artifact("arena-benchmark-v2")["max_decisions_per_turn"], 5)
        for r in report["runs"]:
            self.assertTrue(verify_stepwise_trial(r["directory"])["success"])

    def test_tampered_step_or_commands_fail_verification(self):
        report = benchmark_stepwise(output=self.root/"r", probe="finish_or_core", probe_trials=1)
        directory = Path(report["runs"][0]["directory"])
        original = json.loads((directory/"turn.json").read_text())
        for key, value in (("observation_hash", "wrong"), ("ap_after", 999), ("selected_action", None),
                           ("command_index", 4), ("selected_current_legal", False), ("legal_action_count", 999)):
            with self.subTest(key=key):
                row = deepcopy(original)
                row["steps"][0][key] = value
                (directory/"turn.json").write_text(json.dumps(row))
                self.assertFalse(verify_stepwise_trial(directory)["success"])

    def test_fake_model_benchmark_stops_on_failed_turn_preserves_prefix(self):
        factory = lambda settings, name: FakeOllama(settings, [raw(), raw(FinishAction("actor", "body")), "{}", "{}"])
        report = benchmark_stepwise(output=self.root/"r", blue_provider="ollama", probe="finish_or_core",
            probe_trials=4, provider_factory=factory)
        self.assertEqual(report["status"], "trial_failed")
        self.assertEqual(report["trialsStarted"], 1)
        self.assertEqual(report["providerRequestsIncludingPreflight"], 4)
        self.assertEqual(report["runs"][0]["turn"]["actions_executed"], 1)
        self.assertTrue(report["runs"][0]["verification"]["success"])
        self.assertEqual(report["experiment"]["providers"]["ollama"]["modelConfigVersion"], "qwen-config-v1")

    def test_request_ceiling_configuration_and_output_preservation(self):
        factory = Mock(side_effect=AssertionError("must not construct provider"))
        with self.assertRaises(ValueError):
            benchmark_stepwise(output=self.root/"r", blue_provider="ollama", probe_trials=1,
                request_ceiling=70, provider_factory=factory)
        factory.assert_not_called()
        report = benchmark_stepwise(output=self.root/"r", blue_provider="ollama", probe_trials=1,
            request_ceiling=71, provider_factory=lambda s,n: FakeOllama(s))
        self.assertEqual(report["experiment"]["theoreticalRequestCeiling"], 71)
        self.assertLessEqual(report["providerRequestsIncludingPreflight"], 71)
        self.assertEqual(report["firstResponseValidRate"], 1)
        self.assertEqual(report["selectedCurrentLegalRate"], 1)
        self.assertEqual(report["turnsWithoutProviderFailure"], 7)
        with self.assertRaises(ValueError):
            benchmark_stepwise(output=self.root/"r")

    def test_cli_selection_and_default_preservation(self):
        from contextlib import redirect_stdout
        from io import StringIO
        with redirect_stdout(StringIO()):
            code = main(["--control-mode", "stepwise", "--mode", "probes", "--probe", "team_elimination",
                "--probe-trials", "1", "--output", str(self.root/"cli")])
        self.assertEqual(code, 0)
        with self.assertRaises(ValueError):
            benchmark(control_mode="stepwise", mode="matches", output=self.root/"bad")
        for kwargs in (dict(prompt_version="arena-turn-prompt-v2"), dict(observation_version="arena-observation-v1")):
            with self.assertRaises(ValueError):
                benchmark(control_mode="stepwise", mode="probes", output=self.root/"bad", **kwargs)

    def test_explicit_costs_repairs_caching_and_missing_usage(self):
        pricing = dict(model=Settings().openai.model, as_of="2026-09-13", source="synthetic test rates",
            input_usd_per_million=2, cached_input_usd_per_million=1, output_usd_per_million=4)
        validate_pricing(pricing, Settings().openai.model)
        row = dict(requested_provider="openai", attempts=[dict(metrics=dict(input_tokens=100, cached_input_tokens=20, output_tokens=10))]*2)
        usage = decision_usage(row, pricing)
        self.assertEqual(usage["uncached_input_tokens"], 160)
        self.assertAlmostEqual(usage["estimated_cost_usd"], .00044)
        row["attempts"].append(dict(metrics={}))
        self.assertIsNone(decision_usage(row, pricing)["estimated_cost_usd"])
        with self.assertRaises(ValueError):
            validate_pricing(dict(pricing, input_usd_per_million=float("nan")), Settings().openai.model)


if __name__ == "__main__":
    unittest.main()
