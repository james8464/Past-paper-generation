import json


def test_french_benchmark_plan_has_thirty_exercises_per_model():
    from tools.french_nsi_benchmark import build_plan

    plan = build_plan(["gemma4:12b", "ministral-3:8b"], base_seed=270100, papers=10)
    assert len(plan) == 20
    assert len({(item.model, item.seed) for item in plan}) == 20
    assert all(item.exercise_count == 3 for item in plan)
    assert sum(item.exercise_count for item in plan if item.model == "gemma4:12b") == 30


def test_french_benchmark_resume_requires_exact_identity(tmp_path):
    from tools.french_nsi_benchmark import accepted_result

    result = tmp_path / "result.json"
    result.write_text(
        json.dumps(
            {
                "status": "passed",
                "identity": {"implementation": "abc", "model_digest": "model"},
                "artifacts": {"manifest": "bundle/manifest.json"},
            }
        )
    )
    (tmp_path / "bundle").mkdir()
    (tmp_path / "bundle" / "manifest.json").write_text("{}")

    assert accepted_result(
        result, {"implementation": "abc", "model_digest": "model"}
    )
    assert not accepted_result(
        result, {"implementation": "changed", "model_digest": "model"}
    )


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
