"""Canonical experiment manifests; provenance never enters gameplay hashes."""

from pathlib import Path
import subprocess

from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.ai.plan_schema import PLAN_SCHEMAS
from aig.ai.prompts import resolve_prompt
from aig.scenarios import SCENARIOS
from aig.versions import (
    BENCHMARKS, ENVIRONMENTS, LATEST_BENCHMARK_VERSION, LATEST_ENVIRONMENT_VERSION,
    LATEST_PLAN_SCHEMA_VERSION, LATEST_SCENARIO_VERSION, resolve_version,
)


def source_provenance(directory=None):
    """Best-effort local Git metadata from this source checkout, never the caller's cwd."""
    directory = Path(directory) if directory is not None else Path(__file__).resolve().parents[3]
    unknown = dict(sourceRevision=None, sourceDirty=None)
    try:
        def git(*args):
            return subprocess.run(["git", "-C", str(directory), *args], check=True,
                                  capture_output=True, text=True, timeout=5).stdout.strip()
        # An installed package inside an unrelated repository must not claim its SHA.
        if Path(git("rev-parse", "--show-toplevel")).resolve() != directory.resolve():
            return unknown
        revision = git("rev-parse", "HEAD")
        dirty = bool(git("status", "--porcelain", "--untracked-files=normal"))
        return dict(sourceRevision=revision, sourceDirty=dirty)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return unknown


def experiment_manifest(*, provider, settings, environment_version=None, scenario_version=None,
                        prompt_version=None, plan_schema_version=None, model_config_version=None,
                        source=None):
    prompt, _ = resolve_prompt(settings.ai.strategy_prompt_version if prompt_version is None else prompt_version)
    inference = inference_configuration(provider, settings)
    model_version = None
    if inference is not None:
        selected, profile = resolve_model_profile(provider, model_config_version)
        if inference == profile:
            model_version = selected
    elif model_config_version not in (None, "", "latest"):
        raise ValueError("heuristic has no model configuration profile")
    return dict(
        environmentVersion=resolve_version(environment_version, available=ENVIRONMENTS,
                                           latest=LATEST_ENVIRONMENT_VERSION),
        scenarioVersion=resolve_version(scenario_version, available=SCENARIOS, latest=LATEST_SCENARIO_VERSION),
        strategyPromptVersion=prompt,
        strategicPlanSchemaVersion=resolve_version(plan_schema_version, available=PLAN_SCHEMAS,
                                                  latest=LATEST_PLAN_SCHEMA_VERSION),
        benchmarkVersion=resolve_version(None, available=BENCHMARKS, latest=LATEST_BENCHMARK_VERSION),
        provider=provider, modelConfigVersion=model_version,
        model=inference["model"] if inference else None, modelConfiguration=inference,
        **(source_provenance() if source is None else {
            "sourceRevision": source["sourceRevision"], "sourceDirty": source["sourceDirty"]}),
    )
