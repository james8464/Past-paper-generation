import json
from argparse import Namespace
from hashlib import sha256

import pytest


def _passed_result(tmp_path):
    identity = {
        "implementation": "implementation-sha",
        "reference_index_sha256": "reference-sha",
        "model": "gemma4:12b",
        "model_digest": "model-sha",
        "seed": 270100,
    }
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifacts = {}
    for role, filename in (
        ("question_paper", "sujet.pdf"),
        ("mark_scheme", "corrige.pdf"),
        ("assessment_package", "assessment.json"),
    ):
        content = role.encode()
        (bundle / filename).write_bytes(content)
        artifacts[role] = {
            "file": filename,
            "sha256": sha256(content).hexdigest(),
        }
    manifest = bundle / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "assessment": "fr-bac-general-nsi-written-2027",
                "status": "unreviewed_draft",
                "identity": {
                    "implementation_sha256": identity["implementation"],
                    "model": identity["model"],
                    "model_digest": identity["model_digest"],
                    "seed": identity["seed"],
                },
                "artifacts": artifacts,
            }
        )
    )
    result = tmp_path / "result.json"
    result.write_text(
        json.dumps(
            {
                "status": "passed",
                "identity": identity,
                "artifacts": {
                    "manifest": "bundle/manifest.json",
                    "manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
                },
            }
        )
    )
    return result, identity, bundle


def test_french_benchmark_plan_has_thirty_exercises_per_model():
    from tools.french_nsi_benchmark import build_plan

    plan = build_plan(["gemma4:12b", "ministral-3:8b"], base_seed=270100, papers=10)
    assert len(plan) == 20
    assert len({(item.model, item.seed) for item in plan}) == 20
    assert all(item.exercise_count == 3 for item in plan)
    assert sum(item.exercise_count for item in plan if item.model == "gemma4:12b") == 30


def test_french_benchmark_resume_requires_exact_identity(tmp_path):
    from tools.french_nsi_benchmark import accepted_result

    result, identity, _ = _passed_result(tmp_path)
    assert accepted_result(result, identity)
    assert not accepted_result(result, {**identity, "implementation": "changed"})


def test_french_benchmark_resume_rejects_modified_artifact(tmp_path):
    from tools.french_nsi_benchmark import accepted_result

    result, identity, bundle = _passed_result(tmp_path)
    (bundle / "sujet.pdf").write_bytes(b"changed paper")
    assert not accepted_result(result, identity)


def test_french_benchmark_resume_rejects_modified_manifest(tmp_path):
    from tools.french_nsi_benchmark import accepted_result

    result, identity, bundle = _passed_result(tmp_path)
    manifest = bundle / "manifest.json"
    value = json.loads(manifest.read_text())
    value["identity"]["model_digest"] = "different-model"
    manifest.write_text(json.dumps(value))
    assert not accepted_result(result, identity)


def test_french_benchmark_stops_before_model_call_for_corrupt_passed_result(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    reference_index = tmp_path / "references.sqlite"
    reference_index.write_bytes(b"reference index")
    output = tmp_path / "output"
    item_root = output / "runs" / "gemma4-12b" / "model-sha" / "270100"
    item_root.mkdir(parents=True)
    result, identity, bundle = _passed_result(item_root)
    value = json.loads(result.read_text())
    value["identity"]["reference_index_sha256"] = sha256(
        reference_index.read_bytes()
    ).hexdigest()
    result.write_text(json.dumps(value))
    (bundle / "sujet.pdf").write_bytes(b"changed paper")

    monkeypatch.setattr(
        benchmark, "implementation_identity", lambda: identity["implementation"]
    )
    monkeypatch.setattr(
        benchmark, "model_identity", lambda *_: identity["model_digest"]
    )
    monkeypatch.setattr(benchmark, "hardware_record", lambda: {})

    def unexpected_model_call(*_args, **_kwargs):
        pytest.fail("The model must not rerun over a corrupted passed result")

    monkeypatch.setattr(benchmark, "run_backend", unexpected_model_call)
    args = Namespace(
        reference_index=reference_index,
        output=output,
        models="gemma4:12b",
        base_seed=270100,
        papers_per_model=1,
        timeout_seconds=30,
        ollama_url="http://localhost:11434",
        retry_failed=False,
    )
    with pytest.raises(ValueError, match=r"preuve.*intégrité"):
        benchmark.run_plan(args)


def test_french_benchmark_summary_preserves_repairs_and_failures(tmp_path):
    from tools.french_nsi_benchmark import summarize_run
    from tools.live_process import BackendRun

    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text(
        json.dumps(
            {
                "failed_attempts": [
                    {"exercise_id": "1", "attempt": 1, "error": "invalid SQL"}
                ]
            }
        )
    )
    failed = summarize_run(
        BackendRun(1, False, '{"type":"error","message":"refusé"}\n', "", 1234),
        elapsed_seconds=8.5,
        checkpoint=checkpoint,
        artifact_manifest=None,
    )
    assert failed["status"] == "failed"
    assert failed["repair_attempts"] == 1
    assert failed["first_pass"] is False
    assert failed["error"] == "refusé"

    passed = summarize_run(
        BackendRun(0, False, '{"type":"done"}\n', "", 4321),
        elapsed_seconds=12.0,
        checkpoint=checkpoint,
        artifact_manifest=tmp_path / "manifest.json",
    )
    assert passed["status"] == "passed"
    assert passed["repair_attempts"] == 1
    assert passed["first_pass"] is False
    assert passed["peak_backend_rss_bytes"] == 4321
