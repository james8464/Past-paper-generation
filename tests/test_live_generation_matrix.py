from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.live_generation_matrix import (
    REGISTRY_PATH,
    _request_identity,
    _sha256,
    matrix_jobs,
    matrix_markdown,
    run_matrix,
)
from tools.live_process import BackendRun


@pytest.fixture(autouse=True)
def model_identity(monkeypatch):
    monkeypatch.setattr(
        "tools.live_generation_matrix._model_digest", lambda *args: "model-digest"
    )


def request_identity(job, *, seed=42, model="gemma4:12b", preview=False):
    return _request_identity(
        job,
        seed=seed,
        model=model,
        provider="ollama",
        ollama_url="http://localhost:11434",
        dry_run=preview,
        command_prefix=["backend"],
        model_digest=None if preview else "model-digest",
    )


def jobs():
    return matrix_jobs(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))


def test_live_matrix_is_derived_from_every_advertised_registry_paper() -> None:
    value = jobs()

    assert len(value) == 21
    assert [job.seed_offset for job in value] == list(range(21))
    assert len({job.id for job in value}) == 21
    assert {job.backend_subject for job in value} == {
        "accounting_aqa",
        "business_aqa",
        "computer_science",
        "computer_science_ocr",
        "economics",
        "economics_aqa",
        "economics_ocr",
    }
    assert all("assessment_package" in job.expected_roles for job in value)


def test_live_matrix_markdown_reports_failures_without_false_success() -> None:
    report = {
        "model": "test:model",
        "summary": {"papers": 1, "passed": 0, "failed": 1},
        "results": [
            {
                "family_id": "test/family",
                "paper": "1",
                "passed": False,
                "duration_seconds": 12.2,
                "errors": ["model rejected the schema"],
            }
        ],
    }

    rendered = matrix_markdown(report)
    assert "0/1 papers passed" in rendered
    assert "model rejected the schema" in rendered


def test_live_matrix_reports_backend_signal_exit_without_event_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    job = jobs()[0]

    def trapped(command, **_kwargs):
        return BackendRun(-5, False, "", "", 1000)

    monkeypatch.setattr("tools.live_generation_matrix.run_backend", trapped)

    report = run_matrix(
        [job],
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=42,
        timeout_seconds=30,
        dry_run=False,
        resume=False,
    )

    errors = report["results"][0]["errors"]
    assert errors == ["backend terminated by signal SIGTRAP (5)"]
    assert "SIGTRAP" in (tmp_path / "matrix-report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("demand_passed", [True, False, None])
def test_live_matrix_writes_per_paper_and_aggregate_qualification_manifests(
    tmp_path: Path,
    monkeypatch,
    demand_passed,
) -> None:
    job = jobs()[0]

    def complete(command, **_kwargs):
        run_dir = Path(command[command.index("--output") + 1])
        package = run_dir / "package.json"
        role_paths: dict[str, Path] = {}
        for role in job.expected_roles:
            suffix = ".json" if role == "assessment_package" else ".pdf"
            path = run_dir / f"{role.replace('_', '-')}{suffix}"
            path.write_bytes(b"{}" if suffix == ".json" else b"%PDF-test")
            if role == "assessment_package" and demand_passed is not None:
                path.write_text(
                    json.dumps(
                        {
                            "reference_demand": {
                                "passed": demand_passed,
                                "failed_checks": []
                                if demand_passed
                                else ["mark_weighted_demand_distribution"],
                            }
                        }
                    ),
                    encoding="utf-8",
                )
            role_paths[role] = path
        package.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "generator": {"version": "1.2.3"},
                    "inputs": {
                        "assessment_schema": "assessment:v3",
                        "assessment_package_schema": 1,
                        "syllabus_sha256": "b" * 64,
                        "layout_profile_sha256": "c" * 64,
                    },
                }
            ),
            encoding="utf-8",
        )
        events = [
            json.dumps({"type": "file", "role": role, "path": str(path)})
            for role, path in role_paths.items()
        ]
        events.extend(
            [
                json.dumps(
                    {"type": "file", "role": "package_manifest", "path": str(package)}
                ),
                json.dumps({"type": "done"}),
            ]
        )
        stdout = "\n".join(events)
        return BackendRun(0, False, stdout, "", 1000)

    monkeypatch.setattr("tools.live_generation_matrix.run_backend", complete)

    report = run_matrix(
        [job],
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=42,
        timeout_seconds=30,
        dry_run=False,
        resume=False,
    )

    result = report["results"][0]
    manifest_path = Path(result["qualification_manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    aggregate = json.loads(
        (tmp_path / "qualification-run-manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["generator_id"] == job.family_id
    assert manifest["paper_id"] == job.paper
    assert manifest["seed"] == 42
    assert manifest["model"]["name"] == "gemma4:12b"
    assert manifest["gate_results"]["generation"] == "passed"
    assert manifest["gate_results"]["reference_demand"] == (
        "passed" if demand_passed else "failed"
    )
    assert manifest["gate_results"]["visual"] == "not_run"
    assert {artifact["role"] for artifact in manifest["artifacts"]} == (
        set(job.expected_roles) | {"package_manifest"}
    )
    assert aggregate["paper_manifests"][0]["sha256"]
    assert aggregate["summary"] == {
        "papers": 1,
        "passed": int(bool(demand_passed)),
        "failed": int(not demand_passed),
    }
    if not demand_passed:
        assert result["errors"]


def test_resume_backfills_qualification_evidence_without_regenerating(
    tmp_path: Path,
    monkeypatch,
) -> None:
    job = jobs()[0]
    run_dir = tmp_path / job.backend_subject / f"paper-{job.paper}"
    run_dir.mkdir(parents=True)
    files: dict[str, str] = {}
    for role in (*job.expected_roles, "package_manifest"):
        path = run_dir / f"{role}.json"
        payload = (
            {"reference_demand": {"passed": True}}
            if role == "assessment_package"
            else {}
        )
        path.write_text(json.dumps(payload), encoding="utf-8")
        files[role] = str(path)
    (run_dir / "events.jsonl").write_text('{"type":"done"}\n', encoding="utf-8")
    previous = {
        "id": job.id,
        "family_id": job.family_id,
        "backend_subject": job.backend_subject,
        "paper": job.paper,
        "title": job.title,
        "detail": job.detail,
        "seed": 99,
        "model": "gemma4:12b",
        "provider": "ollama",
        "preview": False,
        "duration_seconds": 10,
        "return_code": 0,
        "timed_out": False,
        "passed": True,
        "missing_roles": [],
        "missing_files": [],
        "errors": [],
        "files": files,
        "request_identity": request_identity(job, seed=99),
        "artifact_sha256": {role: _sha256(Path(path)) for role, path in files.items()},
        "events_sha256": _sha256(run_dir / "events.jsonl"),
    }
    result_path = run_dir / "matrix-result.json"
    result_path.write_text(json.dumps(previous), encoding="utf-8")

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("resume regenerated an already passing paper")

    monkeypatch.setattr("tools.live_generation_matrix.run_backend", unexpected_call)

    report = run_matrix(
        [job],
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=99,
        timeout_seconds=30,
        dry_run=False,
        resume=True,
    )

    manifest = Path(report["results"][0]["qualification_manifest"])
    assert manifest.is_file()
    assert (tmp_path / "qualification-run-manifest.json").is_file()


@pytest.mark.parametrize(
    "changed", ["model", "seed", "preview", "runtime", "artifact", "role", "events"]
)
def test_resume_never_reuses_a_different_generation_request(
    tmp_path, monkeypatch, changed
):
    job = jobs()[0]
    run_dir = tmp_path / job.backend_subject / f"paper-{job.paper}"
    run_dir.mkdir(parents=True)
    files = {}
    for role in (*job.expected_roles, "package_manifest"):
        path = run_dir / f"{role}.json"
        path.write_text(json.dumps({"reference_demand": {"passed": True}}))
        files[role] = str(path)
    (run_dir / "events.jsonl").write_text('{"type":"done"}\n')
    previous = {
        "id": job.id,
        "family_id": job.family_id,
        "paper": job.paper,
        "seed": 42,
        "model": "gemma4:12b",
        "provider": "ollama",
        "preview": False,
        "passed": True,
        "files": files,
        "errors": [],
        "duration_seconds": 1,
    }
    previous[changed] = {"model": "different:model", "seed": 100, "preview": True}.get(
        changed
    )
    previous["request_identity"] = request_identity(
        job,
        seed=previous["seed"],
        model=previous["model"],
        preview=previous["preview"],
    )
    previous["artifact_sha256"] = {
        role: _sha256(Path(path)) for role, path in files.items()
    }
    previous["events_sha256"] = _sha256(run_dir / "events.jsonl")
    if changed == "runtime":
        previous["request_identity"]["runtime_sha256"] = "stale-source"
    elif changed == "artifact":
        Path(files["question_paper"]).write_text("modified after qualification")
    elif changed == "role":
        files.pop("question_paper")
    elif changed == "events":
        (run_dir / "events.jsonl").write_text('{"type":"progress"}\n')
    (run_dir / "matrix-result.json").write_text(json.dumps(previous))
    monkeypatch.setattr(
        "tools.live_generation_matrix.run_backend",
        lambda command, **kwargs: BackendRun(1, False, "", "fresh attempt", 1000),
    )
    report = run_matrix(
        [job],
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=42,
        timeout_seconds=30,
        dry_run=False,
        resume=True,
    )
    assert report["results"][0]["passed"] is False
    assert "fresh attempt" in report["results"][0]["errors"][0]


def test_matrix_persists_completed_routes_before_starting_the_next(
    tmp_path, monkeypatch
):
    selected = jobs()[:2]

    def fail(command, **kwargs):
        if command[command.index("--paper") + 1] == selected[1].paper:
            report = json.loads((tmp_path / "matrix-report.json").read_text())
            assert report["complete"] is False
            assert [item["id"] for item in report["results"]] == [selected[0].id]
        return BackendRun(1, False, "", "intentional fixture failure", 1000)

    monkeypatch.setattr("tools.live_generation_matrix.run_backend", fail)
    report = run_matrix(
        selected,
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=42,
        timeout_seconds=30,
        dry_run=False,
        resume=False,
    )
    assert report["complete"] is True
    assert report["summary"]["failed"] == 2


def test_starting_a_retry_invalidates_old_success_before_launch(tmp_path, monkeypatch):
    job = jobs()[0]
    run_dir = tmp_path / job.backend_subject / f"paper-{job.paper}"
    run_dir.mkdir(parents=True)
    result_path = run_dir / "matrix-result.json"
    result_path.write_text(json.dumps({"passed": True}))
    report_path = tmp_path / "matrix-report.json"
    report_path.write_text(
        json.dumps({"complete": True, "results": [{"passed": True}]})
    )

    def check_state(command, **kwargs):
        assert json.loads(result_path.read_text())["passed"] is False
        assert json.loads(result_path.read_text())["status"] == "running"
        assert json.loads(report_path.read_text())["complete"] is False
        assert json.loads(report_path.read_text())["results"] == []
        return BackendRun(1, False, "", "fixture", 1000)

    monkeypatch.setattr("tools.live_generation_matrix.run_backend", check_state)
    run_matrix(
        [job],
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=42,
        timeout_seconds=30,
        dry_run=False,
        resume=False,
    )


@pytest.mark.parametrize("drift", ["model", "runtime", "artifact", "unknown_model"])
def test_final_matrix_rechecks_earlier_evidence(tmp_path, monkeypatch, drift):
    selected = jobs()[:2]
    current = {
        "model": None if drift == "unknown_model" else "original-model",
        "runtime": "original-source",
    }
    first_question = []
    monkeypatch.setattr(
        "tools.live_generation_matrix._model_digest", lambda *args: current["model"]
    )
    monkeypatch.setattr(
        "tools.live_generation_matrix._runtime_sha256",
        lambda: current["runtime"],
        raising=False,
    )

    def complete(command, *, run_dir, **kwargs):
        paper = command[command.index("--paper") + 1]
        job = next(item for item in selected if item.paper == paper)
        lines = []
        for role in (*job.expected_roles, "package_manifest"):
            path = run_dir / f"{role}.json"
            path.write_text(json.dumps({"reference_demand": {"passed": True}}))
            lines.append(json.dumps({"type": "file", "role": role, "path": str(path)}))
            if role == "question_paper" and job == selected[0]:
                first_question.append(path)
        lines.append('{"type":"done"}')
        if job == selected[1]:
            if drift == "model":
                current["model"] = "replacement-model"
            elif drift == "runtime":
                current["runtime"] = "changed-source"
            elif drift == "artifact":
                first_question[0].write_text("tampered")
        return BackendRun(0, False, "\n".join(lines), "", 1000)

    monkeypatch.setattr("tools.live_generation_matrix.run_backend", complete)
    report = run_matrix(
        selected,
        output_root=tmp_path,
        command_prefix=["backend"],
        model="gemma4:12b",
        provider="ollama",
        ollama_url="http://localhost:11434",
        base_seed=42,
        timeout_seconds=30,
        dry_run=False,
        resume=False,
    )
    assert report["complete"] is True
    assert report["results"][0]["passed"] is False
    assert report["results"][0]["errors"]
