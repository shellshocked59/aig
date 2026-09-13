"""Domain-qualified frozen benchmark/probe artifacts, separate from Empire."""

import hashlib
import json
from pathlib import Path

from aig.ai.experiments import source_provenance
from aig.ai.model_profiles import inference_configuration, resolve_model_profile
from aig.arena.ai.contracts import PLAN_SCHEMA_VERSION
from aig.arena.ai.heuristic import HEURISTIC_VERSION
from aig.arena.ai.prompts import PROMPT_VERSION
from aig.arena.snapshots import digest, from_snapshot
from aig.arena.state import RULES_VERSION, SCENARIO_VERSION

BENCHMARK_VERSION = "arena-benchmark-v1"
PROBE_SET_VERSION = "arena-probes-v1"
ARTIFACTS = Path(__file__).with_name("benchmark_artifacts")
ARTIFACT_HASHES = {
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


def manifest(names, settings, source):
    artifact(BENCHMARK_VERSION)
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
                benchmarkSpecHash=ARTIFACT_HASHES[BENCHMARK_VERSION],
                environmentVersion=RULES_VERSION, scenarioVersion=SCENARIO_VERSION,
                promptVersion=PROMPT_VERSION, planSchemaVersion=PLAN_SCHEMA_VERSION,
                probeSetVersion=PROBE_SET_VERSION, probeSetHash=probe_set()["content_hash"],
                providers=providers, **source)
