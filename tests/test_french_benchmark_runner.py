import json
from argparse import Namespace
from dataclasses import asdict
from hashlib import sha256

import pytest

from Backend.Core.education_context import NSI_2027
from Backend.Core.france.graph_tree_prose import (
    PROSE_CONTRACT_VERSION,
    prose_catalogue_digest,
)
from Backend.Core.france.pipeline import CLOSED_PROSE_PROMPT_VERSION


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
    manifest_identity = {
        "assessment": asdict(NSI_2027),
        "prompt_version": CLOSED_PROSE_PROMPT_VERSION,
        "prose_contract_version": PROSE_CONTRACT_VERSION,
        "prose_catalogue_sha256": prose_catalogue_digest(),
        "implementation_sha256": identity["implementation"],
        "seed": identity["seed"],
        "provider": "ollama",
        "model": identity["model"],
        "model_digest": identity["model_digest"],
        "reference_digest": "selected-reference-sha",
        "blueprint": [],
        "originality_history_digest": "history-sha",
    }
    artifacts = {}
    for role, filename in (
        ("question_paper", "sujet.pdf"),
        ("mark_scheme", "corrige.pdf"),
        ("assessment_package", "assessment.json"),
    ):
        content = (
            json.dumps(
                {
                    "assessment_policy": "fr-bac-general-nsi-written-2027",
                    "identity": manifest_identity,
                }
            ).encode()
            if role == "assessment_package"
            else role.encode()
        )
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
                "identity": manifest_identity,
                "artifacts": artifacts,
                "large_print": False,
                "teacher_review": "not_run",
                "empirical_calibration": "not_run",
                "visual_calibration": "not_run",
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


def _one_paper_args(tmp_path):
    reference_index = tmp_path / "references.sqlite"
    reference_index.write_bytes(b"reference index")
    return Namespace(
        reference_index=reference_index,
        output=tmp_path / "output",
        models="gemma4:12b",
        base_seed=270100,
        papers_per_model=1,
        timeout_seconds=30,
        ollama_url="http://localhost:11434",
        retry_failed=False,
    )


def _no_model_call(monkeypatch, benchmark):
    monkeypatch.setattr(
        benchmark, "implementation_identity", lambda: "implementation-sha"
    )
    monkeypatch.setattr(benchmark, "model_identity", lambda *_: "model-sha")
    monkeypatch.setattr(benchmark, "hardware_record", lambda: {})

    def unexpected_model_call(*_args, **_kwargs):
        pytest.fail("The model must not run while prior evidence is inconsistent")

    monkeypatch.setattr(benchmark, "run_backend", unexpected_model_call)


def _write_session(args):
    args.output.mkdir(exist_ok=True)
    (args.output / "session.json").write_text(
        json.dumps(
            {
                "identity": {
                    "schema_version": 1,
                    "assessment": "fr-bac-general-nsi-written-2027",
                    "implementation": "implementation-sha",
                    "reference_index_sha256": sha256(
                        args.reference_index.read_bytes()
                    ).hexdigest(),
                    "models": {"gemma4:12b": "model-sha"},
                    "base_seed": 270100,
                    "papers_per_model": 1,
                }
            }
        )
    )


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


def test_french_benchmark_resume_rejects_missing_v12_prose_identity(tmp_path):
    from tools.french_nsi_benchmark import accepted_result

    result, identity, bundle = _passed_result(tmp_path)
    manifest = bundle / "manifest.json"
    manifest_value = json.loads(manifest.read_text())
    manifest_value["identity"].pop("prose_contract_version")
    manifest.write_text(json.dumps(manifest_value))
    package = bundle / "assessment.json"
    package_value = json.loads(package.read_text())
    package_value["identity"].pop("prose_contract_version")
    package.write_text(json.dumps(package_value))
    manifest_value["artifacts"]["assessment_package"]["sha256"] = sha256(
        package.read_bytes()
    ).hexdigest()
    manifest.write_text(json.dumps(manifest_value))
    result_value = json.loads(result.read_text())
    result_value["artifacts"]["manifest_sha256"] = sha256(
        manifest.read_bytes()
    ).hexdigest()
    result.write_text(json.dumps(result_value))
    assert not accepted_result(result, identity)


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


def test_french_benchmark_resume_rejects_wrong_assessment_even_with_new_hash(
    tmp_path,
):
    from tools.french_nsi_benchmark import accepted_result

    result, identity, bundle = _passed_result(tmp_path)
    manifest = bundle / "manifest.json"
    value = json.loads(manifest.read_text())
    value["identity"]["assessment"]["id"] = "other-assessment"
    manifest.write_text(json.dumps(value))
    result_value = json.loads(result.read_text())
    result_value["artifacts"]["manifest_sha256"] = sha256(
        manifest.read_bytes()
    ).hexdigest()
    result.write_text(json.dumps(result_value))

    assert not accepted_result(result, identity)


def test_french_benchmark_resume_rejects_package_identity_mismatch(
    tmp_path,
):
    from tools.french_nsi_benchmark import accepted_result

    result, identity, bundle = _passed_result(tmp_path)
    package = bundle / "assessment.json"
    package_value = json.loads(package.read_text())
    package_value["identity"]["prompt_version"] = "another-prompt"
    package.write_text(json.dumps(package_value))
    manifest = bundle / "manifest.json"
    manifest_value = json.loads(manifest.read_text())
    manifest_value["artifacts"]["assessment_package"]["sha256"] = sha256(
        package.read_bytes()
    ).hexdigest()
    manifest.write_text(json.dumps(manifest_value))
    result_value = json.loads(result.read_text())
    result_value["artifacts"]["manifest_sha256"] = sha256(
        manifest.read_bytes()
    ).hexdigest()
    result.write_text(json.dumps(result_value))

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
    _write_session(args)
    with pytest.raises(ValueError, match=r"preuve.*intégrité"):
        benchmark.run_plan(args)


def test_french_benchmark_preserves_malformed_session_before_model_call(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    args = _one_paper_args(tmp_path)
    args.output.mkdir()
    session = args.output / "session.json"
    session.write_text("{")
    _no_model_call(monkeypatch, benchmark)

    with pytest.raises(ValueError, match=r"session.*intégrité"):
        benchmark.run_plan(args)
    assert session.read_text() == "{"


def test_french_benchmark_rejects_missing_session_with_prior_evidence(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    args = _one_paper_args(tmp_path)
    (args.output / "runs").mkdir(parents=True)
    _no_model_call(monkeypatch, benchmark)

    with pytest.raises(ValueError, match=r"session.*intégrité"):
        benchmark.run_plan(args)
    assert not (args.output / "session.json").exists()


def test_french_benchmark_preserves_malformed_result_before_model_call(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    args = _one_paper_args(tmp_path)
    item_root = args.output / "runs" / "gemma4-12b" / "model-sha" / "270100"
    item_root.mkdir(parents=True)
    _write_session(args)
    result = item_root / "result.json"
    result.write_text("{")
    _no_model_call(monkeypatch, benchmark)

    with pytest.raises(ValueError, match=r"résultat.*intégrité"):
        benchmark.run_plan(args)
    assert result.read_text() == "{"


def test_french_benchmark_preserves_empty_result_before_model_call(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    args = _one_paper_args(tmp_path)
    item_root = args.output / "runs" / "gemma4-12b" / "model-sha" / "270100"
    item_root.mkdir(parents=True)
    _write_session(args)
    result = item_root / "result.json"
    result.write_text("{}")
    _no_model_call(monkeypatch, benchmark)

    with pytest.raises(ValueError, match=r"résultat.*intégrité"):
        benchmark.run_plan(args)
    assert result.read_text() == "{}"


def test_french_benchmark_rejects_missing_result_with_prior_attempt(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    args = _one_paper_args(tmp_path)
    item_root = args.output / "runs" / "gemma4-12b" / "model-sha" / "270100"
    (item_root / "attempt-001").mkdir(parents=True)
    _write_session(args)
    _no_model_call(monkeypatch, benchmark)

    with pytest.raises(ValueError, match=r"résultat.*intégrité"):
        benchmark.run_plan(args)
    assert (item_root / "attempt-001").is_dir()


def test_french_benchmark_rejects_failed_result_from_other_identity(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark

    args = _one_paper_args(tmp_path)
    item_root = args.output / "runs" / "gemma4-12b" / "model-sha" / "270100"
    item_root.mkdir(parents=True)
    _write_session(args)
    (item_root / "result.json").write_text(
        json.dumps({"status": "failed", "identity": {"model_digest": "other"}})
    )
    _no_model_call(monkeypatch, benchmark)

    with pytest.raises(ValueError, match=r"résultat.*intégrité"):
        benchmark.run_plan(args)


def test_french_benchmark_rejects_fresh_invalid_artifacts_before_pass(
    tmp_path, monkeypatch
):
    from tools import french_nsi_benchmark as benchmark
    from tools.live_process import BackendRun

    args = _one_paper_args(tmp_path)
    monkeypatch.setattr(
        benchmark, "implementation_identity", lambda: "implementation-sha"
    )
    monkeypatch.setattr(benchmark, "model_identity", lambda *_: "model-sha")
    monkeypatch.setattr(benchmark, "hardware_record", lambda: {})

    def fake_backend(_command, *, cwd, run_dir, timeout_seconds):
        manifest = run_dir / "manifest.json"
        manifest.write_text("{}")
        event = json.dumps(
            {"type": "file", "role": "package_manifest", "path": str(manifest)}
        )
        return BackendRun(0, False, event + "\n", "", 1024)

    monkeypatch.setattr(benchmark, "run_backend", fake_backend)
    with pytest.raises(ValueError, match=r"artefacts.*intégrité"):
        benchmark.run_plan(args)

    result = (
        args.output / "runs" / "gemma4-12b" / "model-sha" / "270100" / "result.json"
    )
    assert json.loads(result.read_text())["status"] == "failed"


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
