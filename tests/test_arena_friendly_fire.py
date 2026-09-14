import hashlib
import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aig.arena.ai.friendly_fire_prompt import BEHAVIOR_PROMPTS, GUIDANCE, PROMPT, PROMPT_VERSION, LunaBehaviorProvider
from aig.arena.ai.prompts import PROMPTS, SYSTEM_PROMPT, resolve_prompt
from aig.arena.ai.contracts import ArenaTurnPlan, action_from_dict
from aig.arena.ai.observation import build_observation
from aig.arena.ai.heuristic import HeuristicArenaTurnProvider
from aig.arena.commands import ArenaFireball
from aig.arena.friendly_fire_fixtures import CASES, fixture, analyze_fireball
from aig.arena.friendly_fire_experiment import prepare, run, ROOT
from aig.arena.snapshots import canonical_json, to_snapshot, from_snapshot, digest
from aig.state import Position
from aig.arena.state import UnitStatus, Board, Tile, Bonus
from aig.settings import Settings
from aig.web import ArenaWebSession


class OfflineLuna(LunaBehaviorProvider):
    def request(self, messages, record):
        record["metrics"] = dict(input_tokens=100, output_tokens=20)
        return canonical_json(ArenaTurnPlan().to_dict())


class FriendlyFireTests(unittest.TestCase):
    def test_historical_bytes(self):
        frozen = json.loads((ROOT / "tests/fixtures/arena-friendly-fire-preservation.json").read_text())
        for path, expected in frozen["files"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), expected, path)
        for version, expected in frozen["prompts"].items():
            self.assertEqual(hashlib.sha256(PROMPTS[version].encode()).hexdigest(), expected)

    def test_browser_actual_baseline_without_inference(self):
        session = ArenaWebSession(Settings())
        session.observer_demo()
        self.assertEqual(session._ai_controller.provider.prompt_version, "arena-turn-prompt-v1")
        self.assertEqual(build_observation(session._simulation.state).version, "arena-observation-v1")

    def test_registry_default_and_contract(self):
        self.assertEqual(resolve_prompt()[0], "arena-turn-prompt-v1")
        self.assertEqual(PROMPT.replace(GUIDANCE, ""), SYSTEM_PROMPT)
        self.assertEqual(BEHAVIOR_PROMPTS[PROMPT_VERSION], PROMPT)
        old = LunaBehaviorProvider(Settings().openai, client=object())
        new = LunaBehaviorProvider(Settings().openai, client=object(), prompt_version=PROMPT_VERSION)
        self.assertEqual(old.configuration(), new.configuration())
        self.assertEqual(old.output_schema(), new.output_schema())
        self.assertEqual(old.schema_version, new.schema_version)

    def test_semantics_and_no_policy(self):
        for phrase in ("FIREBALL HAS FRIENDLY FIRE", "all 8 adjacent tiles", "3x3", "Chebyshev radius 1",
                       "ACTIVE", "including allies", "DOWNED units and Cores are not damaged",
                       "not categorically", "avoid\ndamaging only your own team"):
            self.assertIn(phrase, GUIDANCE)
        for phrase in ("always", "never sacrifice", "prioritize", "only when two", "never friendly fire"):
            self.assertNotIn(phrase, GUIDANCE.lower())
        self.assertNotIn("exactly one action", PROMPT)

    def test_six_legal_impacts_and_purity(self):
        expected = [(0, 0), (0, 1), (2, 0), (2, 1), (1, 1), (2, 1)]
        for name, counts in zip(CASES, expected):
            state, cmd = fixture(name)
            before = to_snapshot(state)
            effect = analyze_fireball(state, cmd)
            self.assertEqual((len(effect["enemy_ids"]), len(effect["friendly_ids"])), counts)
            self.assertEqual(to_snapshot(state), before)
            self.assertTrue(build_observation(state).to_dict())
            self.assertTrue(HeuristicArenaTurnProvider().create_turn_plan(build_observation(state)).actions)

    def test_bad_and_winning_trades(self):
        bad = analyze_fireball(*fixture("bad_trade"))
        self.assertEqual(bad["friendly_downs"], ["ally"])
        self.assertEqual(bad["enemy_downs"], [])
        win = analyze_fireball(*fixture("winning_trade"))
        self.assertTrue(win["immediate_win"])
        self.assertGreater(win["friendly_damage"], 0)

    def test_downed_and_core_immune(self):
        state, cmd = fixture("mixed_blast")
        state.units["ally"].hp = 0
        state.units["ally"].status = UnitStatus.DOWNED
        effect = analyze_fireball(state, cmd)
        self.assertNotIn("ally", effect["friendly_ids"])
        self.assertFalse(set(state.cores) & set(effect["enemy_ids"] + effect["friendly_ids"]))

    def test_bonus_and_clamped_damage(self):
        state, cmd = fixture("bad_trade")
        tiles = list(state.board.tiles)
        tiles[2*9+2] = Tile(bonus=Bonus.POWER)
        tiles[2*9+4] = Tile(bonus=Bonus.WARD)
        state.board = Board(tuple(tiles))
        effect = analyze_fireball(state, cmd)
        self.assertEqual(effect["enemy_damage"], 4)
        self.assertEqual(effect["friendly_damage"], 2)

    def test_illegal_rejected(self):
        state, cmd = fixture("empty_blast")
        state.action_points_remaining = 1
        with self.assertRaises(ValueError):
            analyze_fireball(state, cmd)

    def test_caster_and_simultaneous_elimination(self):
        state, cmd = fixture("winning_trade")
        state.units.pop("ally")
        state.units["mage"].position = Position(3, 2)
        state.units["mage"].hp = 4
        effect = analyze_fireball(state, cmd)
        self.assertEqual(effect["friendly_downs"], ["mage"])
        self.assertEqual(effect["terminal_result"], "red")

    def test_core_inside_blast_immune(self):
        state, _ = fixture("clean_cluster")
        state.units["mage"].position = Position(6, 2)
        core = state.cores["red-core"]
        command = ArenaFireball("blue", "mage", core.position)
        effect = analyze_fireball(state, command)
        self.assertEqual(effect["enemy_ids"], [])
        self.assertIsNone(effect["terminal_result"])

    def test_frozen_fixture_hash(self):
        saved = json.loads((ROOT/"artifacts/arena-luna-friendly-fire/plan-v1.json").read_text())
        self.assertEqual(digest(saved["fixtures"]), "15bdcaa96cc34e349db440154a6eec2d105cf5748c6f38abbab82a81d34614ce")
        for row in saved["fixtures"]:
            state, _ = fixture(row["name"])
            self.assertEqual(to_snapshot(state), row["snapshot"])
            self.assertEqual(build_observation(state).hash, row["observation_hash"])

    def test_offline_arm_and_sizes(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/"plan.json"
            plan = prepare(path)
            sizes = list(plan["sizes"].values())
            delta = sizes[1]["prompt_bytes"] - sizes[0]["prompt_bytes"]
            self.assertGreater(delta, 0)
            self.assertEqual(sizes[1]["luna_input_bytes"]-sizes[0]["luna_input_bytes"],
                             sizes[1]["qwen_messages_bytes"]-sizes[0]["qwen_messages_bytes"])
            report = run(path, PROMPT_VERSION, Path(directory)/"arm", provider_factory=OfflineLuna)
            self.assertEqual(len(report["runs"]), 24)
            self.assertEqual(report["requests"], 24)
            self.assertEqual(report["status"], "complete")
            with self.assertRaises(FileExistsError):
                run(path, PROMPT_VERSION, Path(directory)/"arm", provider_factory=OfflineLuna)

    def test_fail_fast_preserves_failed_trial(self):
        class Invalid(OfflineLuna):
            def request(self, messages, record):
                return "invalid"
        with TemporaryDirectory() as directory:
            path = Path(directory)/"plan.json"
            prepare(path)
            report = run(path, PROMPT_VERSION, Path(directory)/"arm", provider_factory=Invalid)
            self.assertEqual(len(report["runs"]), 1)
            self.assertEqual(report["requests"], 2)
            self.assertEqual(report["status"], "stopped_on_failure")

    def test_cast_metrics_at_execution_boundary(self):
        class Caster(OfflineLuna):
            def request(self, messages, record):
                record["metrics"] = dict(input_tokens=100, output_tokens=20)
                action = action_from_dict(dict(type="fireball", unit_id="mage", target_position=dict(x=4, y=2)))
                return canonical_json(ArenaTurnPlan((action,)).to_dict())
        with TemporaryDirectory() as directory:
            path = Path(directory)/"plan.json"
            prepare(path)
            report = run(path, PROMPT_VERSION, Path(directory)/"arm", provider_factory=Caster)
            self.assertEqual(report["status"], "complete")
            self.assertEqual(report["aggregate"]["immediate_win_actions"], 4)
            self.assertEqual(report["aggregate"]["productive_fireballs"], 24)
            self.assertTrue(all(r["fireball_chosen"] for r in report["runs"]))
            self.assertEqual(report["inference_metrics"]["provider_requests"], 24)

    def test_live_cli_loads_settings_and_returns_failure(self):
        from aig.arena.friendly_fire_experiment import main
        with patch("sys.argv", ["experiment", "--live", "--plan", "plan.json", "--prompt",
                                PROMPT_VERSION, "--output", "unused"]), \
             patch("aig.arena.friendly_fire_experiment.load_settings", return_value=Settings()) as load, \
             patch("aig.arena.friendly_fire_experiment.run", return_value={"status": "stopped_on_failure"}) as fake:
            self.assertEqual(main(), 1)
            load.assert_called_once()
            self.assertEqual(fake.call_args.kwargs["settings"], Settings())

    def test_frozen_plan_mutation_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)/"plan.json"
            plan = prepare(path)
            plan["fixtures"][0]["snapshot"]["action_points_remaining"] = 2
            path.write_text(json.dumps(plan))
            with self.assertRaises(ValueError):
                run(path, PROMPT_VERSION, Path(directory)/"arm", provider_factory=OfflineLuna)
