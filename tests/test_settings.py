"""Settings precedence and parsing contracts, independent of developer setup."""

from dataclasses import FrozenInstanceError, asdict
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aig.settings import DEFAULT_LOCAL_FILE, OllamaSettings, load_settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.local_file = Path(directory.name) / ".env"

    def load(self, environ=None):
        return load_settings(
            local_file=self.local_file, environ={} if environ is None else environ,
        )

    def write_local(self, contents):
        self.local_file.write_text(contents, encoding="utf-8")

    def test_committed_defaults_without_local_setup(self):
        self.assertEqual(asdict(self.load().ollama), {
            "base_url": "http://10.0.0.250:11434",
            "model": "hf.co/empero-ai/Qwen3.8-4B-Distill-GGUF:Q4_K_M",
            "context_size": 4096,
            "temperature": 0.0,
            "seed": 42,
            "max_output_tokens": 256,
            "keep_alive": "10m",
            "think": False,
            "stream": False,
        })
        self.assertIs(type(self.load().ollama.temperature), float)

    def test_ai_defaults_and_environment_local_precedence(self):
        self.assertEqual(asdict(self.load().ai), {'replan_interval': 5, 'max_actions': 256})
        self.write_local('AIG_AI_REPLAN_INTERVAL=3\nAIG_AI_MAX_ACTIONS=100\n')
        self.assertEqual(self.load().ai.replan_interval, 3)
        self.assertEqual(self.load({'AIG_AI_MAX_ACTIONS': '40'}).ai.max_actions, 40)
        self.assertEqual(self.load({'AIG_AI_MAX_ACTIONS': ''}).ai.max_actions, 100)

    def test_ai_settings_require_positive_integers(self):
        for name in ('AIG_AI_REPLAN_INTERVAL', 'AIG_AI_MAX_ACTIONS'):
            for value in ('0', '-1', '1.5', 'true'):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, name):
                    self.load({name: value})

    def test_all_fields_follow_precedence_and_empty_environment_fallback(self):
        cases = [
            ("base_url", "http://localhost:11434", "http://other:11434"),
            ("model", "local-model", "environment-model"),
            ("context_size", 2048, 8192),
            ("temperature", 0.5, 0.0),
            ("seed", 7, 0),
            ("max_output_tokens", 128, 512),
            ("keep_alive", "5m", "0"),
            ("think", True, False),
            ("stream", True, False),
        ]
        for field, local, environment in cases:
            with self.subTest(field=field):
                name = f"AIG_OLLAMA_{field.upper()}"
                self.write_local(f"{name}={local}\n")
                self.assertEqual(getattr(self.load().ollama, field), local)
                self.assertEqual(getattr(self.load({name: ""}).ollama, field), local)
                actual = getattr(self.load({name: str(environment)}).ollama, field)
                self.assertEqual(actual, environment)
                self.assertIs(type(actual), type(environment))
                self.write_local("")
                self.assertEqual(
                    getattr(self.load({name: ""}).ollama, field),
                    getattr(OllamaSettings(), field),
                )

    def test_local_file_syntax_and_partial_override(self):
        self.write_local(
            '\ufeff# Developer settings\n\n'
            ' AIG_OLLAMA_BASE_URL = "http://localhost:11434" \n'
            "AIG_OLLAMA_MODEL='model=tag#literal'\n"
            'UNRELATED_SETTING=ignored\n'
            'AIG_OLLAMA_SEED=6\nAIG_OLLAMA_SEED=7\n'
        )
        settings = self.load().ollama
        self.assertEqual(settings.base_url, "http://localhost:11434")
        self.assertEqual(settings.model, "model=tag#literal")
        self.assertEqual(settings.seed, 7)
        self.assertEqual(settings.context_size, 4096)

    def test_boolean_spellings(self):
        for spelling in ("true", "1", "yes", "on", " TRUE "):
            with self.subTest(spelling=spelling):
                self.assertIs(self.load({"AIG_OLLAMA_THINK": spelling}).ollama.think, True)
        for spelling in ("false", "0", "no", "off", " FALSE "):
            with self.subTest(spelling=spelling):
                self.assertIs(self.load({"AIG_OLLAMA_STREAM": spelling}).ollama.stream, False)

    def test_invalid_effective_values_name_the_setting(self):
        cases = [
            ("CONTEXT_SIZE", "lots"), ("CONTEXT_SIZE", "0"),
            ("MAX_OUTPUT_TOKENS", "-1"), ("SEED", "1.5"),
            ("TEMPERATURE", "warm"), ("TEMPERATURE", "nan"),
            ("TEMPERATURE", "inf"), ("TEMPERATURE", "-0.1"),
            ("THINK", "maybe"), ("STREAM", "2"),
            ("BASE_URL", "   "), ("MODEL", "   "), ("KEEP_ALIVE", "   "),
        ]
        for suffix, raw in cases:
            name = f"AIG_OLLAMA_{suffix}"
            with self.subTest(name=name, raw=raw):
                self.write_local("")
                with self.assertRaisesRegex(ValueError, name):
                    self.load({name: raw})
                self.write_local(f'{name}="{raw}"\n')
                with self.assertRaisesRegex(ValueError, name):
                    self.load()

    def test_empty_local_value_is_invalid_but_environment_can_override_it(self):
        self.write_local('AIG_OLLAMA_MODEL=""\n')
        with self.assertRaisesRegex(ValueError, "AIG_OLLAMA_MODEL"):
            self.load()
        self.assertEqual(self.load({"AIG_OLLAMA_MODEL": "valid"}).ollama.model, "valid")

    def test_malformed_local_file_is_reported(self):
        for contents in ("broken line", "=missing-key", "AIG_OLLAMA_MODLE=typo",
                         'AIG_OLLAMA_MODEL="unclosed'):
            with self.subTest(contents=contents):
                self.write_local(contents)
                with self.assertRaisesRegex(ValueError, r"\.env:1:"):
                    self.load()

    def test_nonmissing_file_errors_are_not_hidden(self):
        with self.assertRaises(OSError):
            load_settings(local_file=self.local_file.parent, environ={})

    def test_process_environment_is_read_without_mutation(self):
        self.write_local("AIG_OLLAMA_SEED=7\nAIG_OLLAMA_THINK=true\n")
        with patch.dict(os.environ, {"AIG_OLLAMA_SEED": "0"}, clear=True):
            before = dict(os.environ)
            settings = load_settings(local_file=self.local_file)
            self.assertEqual(settings.ollama.seed, 0)
            self.assertTrue(settings.ollama.think)
            self.assertEqual(dict(os.environ), before)

    def test_explicit_environment_mapping_replaces_process_environment(self):
        with patch.dict(os.environ, {"AIG_OLLAMA_MODEL": "ambient"}):
            self.assertEqual(self.load().ollama.model, OllamaSettings().model)

    def test_reloading_reads_changes_and_previous_settings_stay_immutable(self):
        self.write_local("AIG_OLLAMA_SEED=7\n")
        first = self.load()
        self.write_local("AIG_OLLAMA_SEED=8\n")
        self.assertEqual(self.load().ollama.seed, 8)
        self.assertEqual(first.ollama.seed, 7)
        with self.assertRaises(FrozenInstanceError):
            first.ollama.seed = 9
        with self.assertRaises(FrozenInstanceError):
            first.ollama = OllamaSettings()

    def test_local_loading_can_be_disabled(self):
        self.assertEqual(load_settings(local_file=None, environ={}).ollama, OllamaSettings())

    def test_default_local_path_is_anchored_to_checkout(self):
        self.assertEqual(DEFAULT_LOCAL_FILE, Path(__file__).resolve().parents[1] / ".env")

    def test_committed_example_matches_defaults(self):
        example = Path(__file__).resolve().parents[1] / ".env.example"
        self.assertEqual(load_settings(local_file=example, environ={}).ollama, OllamaSettings())


if __name__ == "__main__":
    unittest.main()
