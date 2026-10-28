# V32 integrity runs must never become evidence of live model generation

import json
from argparse import Namespace
from hashlib import sha256

import pytest


@pytest.mark.parametrize(
    "identity", [None, [], {}, {"prompt_version": "fr-nsi-written-2027-v999"}]
)
def test_unknown_provenance_never_awards_model_success(tmp_path, identity):
    from tools.french_nsi_benchmark import summarize_run
    from tools.live_process import BackendRun

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"identity": identity}))
    result = summarize_run(
        BackendRun(0, False, "", "", 0),
        elapsed_seconds=1,
        checkpoint=tmp_path / "checkpoint.json",
        artifact_manifest=manifest,
    )
    assert result["model_used"] is None
    assert result["qualification_kind"] == "unverified"
    assert result["first_pass"] is False


@pytest.fixture
def published(tmp_path, monkeypatch):
    from Backend.Core.france import runtime
    from tests.test_nsi_pipeline import ControlledTwoOutageFrenchClient, make_index
    from tools import french_nsi_benchmark as benchmark
    from tools.live_process import BackendRun

    index = tmp_path / "references.sqlite"
    make_index(index)
    monkeypatch.setattr(runtime, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(
        runtime, "FrenchOllamaClient", lambda **_: ControlledTwoOutageFrenchClient()
    )
    output = tmp_path / "output"
    assert (
        runtime.handle_generate_assessment(
            Namespace(
                assessment=benchmark.ASSESSMENT,
                reference_index=index,
                output=str(output),
                seed=270100,
                model="fixture",
                ollama_url="http://localhost:11434",
                allow_remote=False,
                large_print=False,
            )
        )
        == 0
    )
    (bundle,) = output.glob("nsi-*")
    manifest = bundle / "manifest.json"
    data = json.loads(manifest.read_text())
    identity = {
        "implementation": data["identity"]["implementation_sha256"],
        "reference_index_sha256": data["reference_index_sha256"],
        "model": "fixture",
        "model_digest": "fixture-digest",
        "seed": 270100,
    }
    result = benchmark.summarize_run(
        BackendRun(0, False, "", "", 1000),
        elapsed_seconds=1,
        checkpoint=next((output / ".keldin-checkpoints").glob("*.json")),
        artifact_manifest=manifest,
    )
    result.update(
        identity=identity,
        artifacts={
            "manifest": "manifest.json",
            "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
        },
    )
    path = bundle / "result.json"
    path.write_text(json.dumps(result))
    return path, identity, data, result


def test_whole_case_benchmark_is_not_a_model_first_pass(published):
    from tools.french_nsi_benchmark import accepted_result

    path, identity, _, result = published
    assert result["model_used"] is False
    assert result["qualification_kind"] == "application_owned_integrity"
    assert result["first_pass"] is False
    assert result["execution_first_pass"] is True
    assert accepted_result(
        path, identity, expected_prompt_version="fr-nsi-written-2027-v32"
    )
    assert not accepted_result(
        path, identity, expected_prompt_version="fr-nsi-written-2027-v31"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("model_used", True),
        ("model_used", 0),
        ("generation_origin", "model_assisted"),
    ],
)
def test_whole_case_benchmark_rejects_forged_manifest_provenance(
    published, field, value
):
    from tools.french_nsi_benchmark import accepted_result

    path, identity, manifest, result = published
    manifest[field] = value
    source = path.parent / "manifest.json"
    source.write_text(json.dumps(manifest))
    result["artifacts"]["manifest_sha256"] = sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(result))
    assert not accepted_result(path, identity)


def test_whole_case_benchmark_rechecks_pdf_even_after_hashes_are_updated(published):
    import pymupdf

    from tools.french_nsi_benchmark import accepted_result

    path, identity, manifest, result = published
    subject = path.parent / manifest["artifacts"]["question_paper"]["file"]
    with pymupdf.open(subject) as pdf:
        pdf[0].insert_text((80, 780), "UNEXPECTED ANSWER")
        pdf.saveIncr()
    manifest["artifacts"]["question_paper"]["sha256"] = sha256(
        subject.read_bytes()
    ).hexdigest()
    source = path.parent / "manifest.json"
    source.write_text(json.dumps(manifest))
    result["artifacts"]["manifest_sha256"] = sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(result))
    assert not accepted_result(path, identity)


def test_run_plan_resumes_verified_application_owned_artifacts(
    published, tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark
    from tools.live_process import BackendRun

    path, identity, _, _ = published
    args = Namespace(
        reference_index=tmp_path / "references.sqlite",
        output=tmp_path / "benchmark",
        models="fixture",
        base_seed=270100,
        papers_per_model=1,
        timeout_seconds=30,
        ollama_url="http://localhost:11434",
        retry_failed=False,
    )
    monkeypatch.setattr(
        benchmark, "implementation_identity", lambda: identity["implementation"]
    )
    monkeypatch.setattr(benchmark, "model_identity", lambda *_: "fixture-digest")
    monkeypatch.setattr(benchmark, "hardware_record", lambda: {})
    calls = []

    def backend(command, **kwargs):
        calls.append(command)
        event = {
            "type": "file",
            "role": "package_manifest",
            "path": str(path.parent / "manifest.json"),
        }
        return BackendRun(0, False, json.dumps(event), "", 1000)

    monkeypatch.setattr(benchmark, "run_backend", backend)
    assert benchmark.run_plan(args) == 0
    assert benchmark.run_plan(args) == 0
    assert len(calls) == 1
    report = json.loads((args.output / "benchmark-summary.json").read_text())
    assert report["application_owned_integrity_passes"] == 1
    assert report["model_first_passes"] == 0
    assert report["educational_qualification"] == "not_run"
