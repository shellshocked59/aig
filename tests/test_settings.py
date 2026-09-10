"""Settings precedence and parsing contracts, independent of developer setup."""

from dataclasses import FrozenInstanceError, asdict
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from aig.settings import DEFAULT_LOCAL_FILE, AiSettings, OllamaSettings, OpenAISettings, load_settings


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
            "timeout_seconds": 20.0,
        })
        self.assertIs(type(self.load().ollama.temperature), float)

    def test_ai_defaults_and_environment_local_precedence(self):
        self.assertEqual(asdict(self.load().ai), {'replan_interval': 5, 'max_actions': 256, 'strategy_provider': 'heuristic'})
        self.write_local('AIG_AI_REPLAN_INTERVAL=3\nAIG_AI_MAX_ACTIONS=100\n')
        self.assertEqual(self.load().ai.replan_interval, 3)
        self.assertEqual(self.load({'AIG_AI_MAX_ACTIONS': '40'}).ai.max_actions, 40)
        self.assertEqual(self.load({'AIG_AI_MAX_ACTIONS': ''}).ai.max_actions, 100)

    def test_ai_settings_require_positive_integers(self):
        for name in ('AIG_AI_REPLAN_INTERVAL', 'AIG_AI_MAX_ACTIONS'):
            for value in ('0', '-1', '1.5', 'true'):
                with self.subTest(name=name, value=value), self.assertRaisesRegex(ValueError, name):
                    self.load({name: value})

    def test_strategy_provider_defaults_precedence_and_optional_key(self):
        self.assertEqual(self.load().ai.strategy_provider, 'heuristic')
        self.assertEqual(self.load({'AIG_STRATEGY_PROVIDER': ''}).ai.strategy_provider, 'heuristic')
        for provider in ('heuristic', 'ollama', 'openai'):
            with self.subTest(provider=provider):
                self.write_local(f'AIG_STRATEGY_PROVIDER={provider}\n')
                self.assertEqual(self.load().ai.strategy_provider, provider)
                self.assertIsNone(self.load().openai.api_key)
                self.assertEqual(self.load({'AIG_STRATEGY_PROVIDER': ''}).ai.strategy_provider, provider)
                self.assertEqual(self.load({'AIG_STRATEGY_PROVIDER': 'heuristic'}).ai.strategy_provider,
                                 'heuristic')

    def test_strategy_provider_rejects_invalid_values_without_normalizing_case(self):
        for provider in ('unknown', 'OLLAMA', 'Heuristic', ' ollama ', '', '   '):
            with self.subTest(provider=provider):
                self.write_local(f'AIG_STRATEGY_PROVIDER="{provider}"\n')
                with self.assertRaisesRegex(ValueError, 'AIG_STRATEGY_PROVIDER'):
                    self.load()
                if provider:
                    with self.assertRaisesRegex(ValueError, 'AIG_STRATEGY_PROVIDER'):
                        self.load({'AIG_STRATEGY_PROVIDER': provider})
                with self.assertRaisesRegex(ValueError, 'AIG_STRATEGY_PROVIDER'):
                    AiSettings(strategy_provider=provider)
                self.assertEqual(self.load({'AIG_STRATEGY_PROVIDER': 'heuristic'}).ai.strategy_provider,
                                 'heuristic')

    def test_provider_configuration_does_not_select_provider(self):
        self.write_local('OPENAI_API_KEY=sk-FAKE-selector-canary\n'
                         'AIG_OLLAMA_BASE_URL=http://ollama.example.test:11434\n')
        settings = self.load()
        self.assertIsNotNone(settings.openai.api_key)
        self.assertEqual(settings.ollama.base_url, 'http://ollama.example.test:11434')
        self.assertEqual(settings.ai.strategy_provider, 'heuristic')

    def test_cors_origins_follow_precedence_and_parse_explicit_origins(self):
        self.assertEqual(self.load().http.allowed_origins, ('http://aig.localhost',))
        self.write_local('AIG_HTTP_CORS_ORIGINS=https://www.agentstrategy.online\n')
        self.assertEqual(self.load().http.allowed_origins, ('https://www.agentstrategy.online',))
        self.assertEqual(self.load({'AIG_HTTP_CORS_ORIGINS': ''}).http.allowed_origins,
                         ('https://www.agentstrategy.online',))
        self.assertEqual(self.load({'AIG_HTTP_CORS_ORIGINS': 'http://aig.localhost, http://127.0.0.1:5173'}).http.allowed_origins,
                         ('http://aig.localhost', 'http://127.0.0.1:5173'))

    def test_cors_rejects_wildcards_paths_and_malformed_origins(self):
        for value in ('*', 'https://*.example.com', 'null', 'https://example.com/path',
                      'https://example.com/', 'https://example.com?query=1',
                      'https://user:password@example.com', 'file:///tmp',
                      'http://aig.localhost,', 'http://bad host'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'AIG_HTTP_CORS_ORIGINS'):
                self.load({'AIG_HTTP_CORS_ORIGINS': value})

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
            ("timeout_seconds", 12.5, 30.0),
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
            ("TIMEOUT_SECONDS", "0"), ("TIMEOUT_SECONDS", "-1"),
            ("TIMEOUT_SECONDS", "nan"), ("TIMEOUT_SECONDS", "inf"), ("TIMEOUT_SECONDS", "slow"),
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
        self.assertEqual(load_settings(local_file=example, environ={}).ai, AiSettings())
        self.assertEqual(load_settings(local_file=example, environ={}).ollama, OllamaSettings())
        self.assertEqual(load_settings(local_file=example, environ={}).openai, OpenAISettings())

    def test_openai_defaults_and_missing_key(self):
        settings = self.load().openai
        self.assertIsNone(settings.api_key)
        self.assertEqual(settings.model, "gpt-5.6-luna")
        self.assertEqual(settings.timeout_seconds, 20.0)
        self.assertIs(type(settings.timeout_seconds), float)
        self.assertEqual(settings.max_output_tokens, 512)
        self.assertEqual(settings.reasoning_effort, "none")
        self.assertEqual(load_settings(local_file=None, environ={}).openai, settings)

    def test_openai_environment_local_and_default_precedence(self):
        cases = (
            ("api_key", "OPENAI_API_KEY", "sk-FAKE-local-only", "sk-FAKE-process-only"),
            ("model", "AIG_OPENAI_MODEL", "gpt-5.6-luna", "custom-model"),
            ("timeout_seconds", "AIG_OPENAI_TIMEOUT_SECONDS", 12.5, 30.0),
            ("max_output_tokens", "AIG_OPENAI_MAX_OUTPUT_TOKENS", 128, 1024),
            ("reasoning_effort", "AIG_OPENAI_REASONING_EFFORT", "low", "max"),
        )
        for field_name, name, local, environment in cases:
            with self.subTest(name=name):
                self.write_local(f'{name}="{local}"\n')
                self.assertEqual(getattr(self.load().openai, field_name), local)
                self.assertEqual(getattr(self.load({name: ""}).openai, field_name), local)
                actual = getattr(self.load({name: str(environment)}).openai, field_name)
                self.assertEqual(actual, environment)
                self.assertIs(type(actual), type(environment))
                self.write_local("")
                self.assertEqual(getattr(self.load({name: ""}).openai, field_name),
                                 getattr(OpenAISettings(), field_name))

    def test_openai_empty_local_key_is_unset(self):
        for value in ("", '""', "''", "   "):
            with self.subTest(value=value):
                self.write_local(f"OPENAI_API_KEY={value}\n")
                self.assertIsNone(self.load().openai.api_key)
                self.assertIsNone(self.load({"OPENAI_API_KEY": ""}).openai.api_key)
        self.assertIsNone(OpenAISettings(api_key="").api_key)

    def test_openai_whitespace_follows_existing_string_conventions(self):
        self.write_local("OPENAI_API_KEY=sk-FAKE-local-only\n")
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            self.load({"OPENAI_API_KEY": "   "})
        self.write_local('OPENAI_API_KEY="   "\n')
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            self.load()
        self.write_local("AIG_OPENAI_MODEL=  custom-model  \n")
        self.assertEqual(self.load().openai.model, "custom-model")
        self.assertEqual(self.load({"AIG_OPENAI_MODEL": " model "}).openai.model, " model ")

    def test_openai_api_key_has_no_aig_alias(self):
        self.assertIsNone(self.load({"AIG_OPENAI_API_KEY": "sk-FAKE-ignored"}).openai.api_key)
        self.write_local("AIG_OPENAI_API_KEY=sk-FAKE-ignored\n")
        with self.assertRaisesRegex(ValueError, "unknown setting AIG_OPENAI_API_KEY") as caught:
            self.load()
        self.assertNotIn("sk-FAKE-ignored", str(caught.exception))

    def test_openai_invalid_effective_values_name_the_setting_without_the_key(self):
        fake_key = "sk-FAKE-settings-secret-canary"
        cases = {
            "MODEL": ("   ",),
            "TIMEOUT_SECONDS": ("0", "-1", "nan", "inf", "-inf", "slow", "true", " "),
            "MAX_OUTPUT_TOKENS": ("0", "-1", "1.5", "true", "nan", "inf", " "),
            "REASONING_EFFORT": ("minimal", "auto", "HIGH", " "),
        }
        for suffix, values in cases.items():
            name = f"AIG_OPENAI_{suffix}"
            for value in values:
                for from_file in (False, True):
                    with self.subTest(name=name, value=value, from_file=from_file):
                        self.write_local(f'OPENAI_API_KEY={fake_key}\n' +
                                         (f'{name}="{value}"\n' if from_file else ""))
                        with self.assertRaisesRegex(ValueError, name) as caught:
                            self.load({} if from_file else {name: value})
                        self.assertNotIn(fake_key, str(caught.exception))
        self.write_local(f'OPENAI_API_KEY="{fake_key}\n')
        with self.assertRaisesRegex(ValueError, "unmatched quote for OPENAI_API_KEY") as caught:
            self.load()
        self.assertNotIn(fake_key, str(caught.exception))

    def test_openai_direct_construction_validation(self):
        cases = {
            "api_key": (True, 123, "   "),
            "model": (None, 1, "", "   "),
            "timeout_seconds": (True, None, "20", 0, -1, float("nan"), float("inf")),
            "max_output_tokens": (True, None, "512", 1.5, 0, -1),
            "reasoning_effort": (None, [], "minimal", "HIGH", ""),
        }
        for name, values in cases.items():
            for value in values:
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    OpenAISettings(**{name: value})

    def test_openai_all_supported_reasoning_efforts(self):
        for effort in ("none", "low", "medium", "high", "xhigh", "max"):
            with self.subTest(effort=effort):
                self.assertEqual(self.load({"AIG_OPENAI_REASONING_EFFORT": effort}).openai.reasoning_effort,
                                 effort)

    def test_openai_loading_does_not_mutate_environment_or_cache_credentials(self):
        self.write_local("OPENAI_API_KEY=sk-FAKE-first\n")
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            before = dict(os.environ)
            first = load_settings(local_file=self.local_file)
            self.assertEqual(first.openai.api_key, "sk-FAKE-first")
            self.assertEqual(dict(os.environ), before)
            self.write_local("OPENAI_API_KEY=sk-FAKE-second\n")
            self.assertEqual(load_settings(local_file=self.local_file).openai.api_key, "sk-FAKE-second")
            self.assertEqual(first.openai.api_key, "sk-FAKE-first")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-FAKE-ambient"}):
            self.assertIsNone(load_settings(local_file=None, environ={}).openai.api_key)
        with self.assertRaises(FrozenInstanceError):
            first.openai.api_key = "replacement"
        with self.assertRaises(FrozenInstanceError):
            first.openai = OpenAISettings()

    def test_openai_key_is_absent_from_nested_representations(self):
        key = "sk-FAKE-repr-secret-canary"
        settings = self.load({"OPENAI_API_KEY": key})
        self.assertEqual(settings.openai.api_key, key)
        for rendered in (repr(settings), str(settings), repr(settings.openai), str(settings.openai)):
            self.assertNotIn(key, rendered)
            self.assertNotIn("api_key", rendered)


if __name__ == "__main__":
    unittest.main()
