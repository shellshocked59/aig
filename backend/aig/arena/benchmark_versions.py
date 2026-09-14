"""Domain-qualified frozen benchmark/probe artifacts, separate from Empire."""

import hashlib
import json
from pathlib import Path

from aig.ai.experiments import source_provenance
from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.heuristic import HEURISTIC_VERSION
from aig.arena.ai.prompts import PROMPT_VERSION, resolve_prompt
from aig.arena.ai.observation import OBSERVATION_VERSION, resolve_observation_version
from aig.arena.snapshots import digest, from_snapshot
from aig.arena.state import RULES_VERSION, SCENARIO_VERSION

BENCHMARK_VERSION = "arena-benchmark-v1"
PROBE_SET_VERSION = "arena-probes-v1"
ARTIFACTS = Path(__file__).with_name("benchmark_artifacts")
ARTIFACT_HASHES = {
    "arena-benchmark-v5": "3d12f753d809fd58fa316a4d9e9d32cb4318f66ae66f2630604111bb3fa2deee",
    "arena-benchmark-v4": "03b29354aa247e01c84773ffc86bb92a5e3fab029a068a0bd5639816bae7e70b",
    "arena-repair-benchmark-v1": "25f2cad3d7d183911cec5548de7eead01e46fe4494c2cdce22d7b2dea003925e",
    "arena-repair-challenges-v1": "51a77fe1e77b5b8950a4de855184950015a0b94e51447c9a381193812eb47980",
    "arena-benchmark-v3": "c5a9d745faf64644c2e6360fa92e51f1625e48af455cdb668952183e7c97ae2e",
    "arena-benchmark-v2": "e425dc38368a84edba6ca9097f7c81808838097e323d1aaf726a3a66fb8973d6",
    "arena-benchmark-v1": "f5b48fef06883fd09482d399a464b76829cb6fef26ca08a9b5b50c74a473a397",
    "arena-probes-v1": "bd3045c382b598794868008d23c940df3454e66984edfcd4b02f6c67ed4fcec9",
    "arena-heuristic-probes-v1": "3d05cf990597ef542f4340d07a15f39e93886cf23cb452ba621b504c03a8cd26",
}


def artifact(version):
    raw = (ARTIFACTS / (version + ".json")).read_bytes()
    # Text normalization tolerates checkout CRLF without altering canonical content.
    raw = raw.replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != ARTIFACT_HASHES[version]:
        raise ValueError("frozen Arena benchmark artifact integrity failure")
    return json.loads(raw)


def probe_set():
    data = artifact(PROBE_SET_VERSION)
    if data["version"] != PROBE_SET_VERSION or digest(data["probes"]) != data["content_hash"]:
        raise ValueError("frozen Arena probe-set integrity failure")
    return data


def frozen_probe(name):
    record = probe_set()["probes"][name]
    if digest(record["snapshot"]) != record["state_hash"]:
        raise ValueError("frozen Arena probe integrity failure")
    return from_snapshot(record["snapshot"])


def source_manifest():
    root = Path(__file__).resolve().parents[3]
    files = {}
    for path in sorted((root / "backend").rglob("*")):
        if path.is_file() and path.suffix in (".py", ".json") and "__pycache__" not in path.parts:
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(**source_provenance(root), sourceFiles=files, sourceManifestHash=digest(files))


def manifest(names, settings, source, *, prompt_version=PROMPT_VERSION, observation_version=OBSERVATION_VERSION):
    recipe = artifact(BENCHMARK_VERSION)
    prompt_version, prompt = resolve_prompt(prompt_version)
    observation_version = resolve_observation_version(observation_version)
    overrides = {}
    if prompt_version != recipe["prompt"]:
        overrides["promptVersion"] = prompt_version
    if observation_version != OBSERVATION_VERSION:
        overrides["observationVersion"] = observation_version
    providers = {}
    for name in names:
        config = inference_configuration(name, settings)
        profile = None
        if config is not None:
            version, baseline = resolve_model_profile(name)
            profile = version if config == baseline else "arena-model-config-sha256-" + digest(config)
        providers[name] = dict(provider=name, model=config["model"] if config else None,
                               modelConfigVersion=profile, modelConfiguration=config,
                               heuristicVersion=HEURISTIC_VERSION if name == "heuristic" else None)
        if name == "ollama":
            providers[name]["keepAlive"] = settings.ollama.keep_alive
    return dict(environment="arena", benchmarkVersion=BENCHMARK_VERSION,
                controlMode="full-turn", controlVersion="arena-control-full-turn-v1",
                benchmarkSpecHash=ARTIFACT_HASHES[BENCHMARK_VERSION],
                environmentVersion=RULES_VERSION, scenarioVersion=SCENARIO_VERSION,
                promptVersion=prompt_version, promptHash=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                baseRecipePromptVersion=recipe["prompt"],
                observationVersion=observation_version, baseRecipeObservationVersion=OBSERVATION_VERSION,
                experimentOverrides=overrides,
                planSchemaVersion=PLAN_SCHEMA_VERSION,
                probeSetVersion=PROBE_SET_VERSION, probeSetHash=probe_set()["content_hash"],
                providers=providers, **source)
