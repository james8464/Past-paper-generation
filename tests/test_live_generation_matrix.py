from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.live_generation_matrix import (
    REGISTRY_PATH,
    matrix_jobs,
    matrix_markdown,
    run_matrix,
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
        return subprocess.CompletedProcess(command, -5, "", "")

    monkeypatch.setattr("tools.live_generation_matrix.subprocess.run", trapped)

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
                path.write_text(json.dumps({"reference_demand": {
                    "passed": demand_passed,
                    "failed_checks": [] if demand_passed else ["mark_weighted_demand_distribution"],
                }}), encoding="utf-8")
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
                json.dumps({"type": "file", "role": "package_manifest", "path": str(package)}),
                json.dumps({"type": "done"}),
            ]
        )
        stdout = "\n".join(events)
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr("tools.live_generation_matrix.subprocess.run", complete)

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
        "papers": 1, "passed": int(bool(demand_passed)), "failed": int(not demand_passed)
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
        payload = {"reference_demand": {"passed": True}} if role == "assessment_package" else {}
        path.write_text(json.dumps(payload), encoding="utf-8")
        files[role] = str(path)
    (run_dir / "events.jsonl").write_text("{\"type\":\"done\"}\n", encoding="utf-8")
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
    }
    result_path = run_dir / "matrix-result.json"
    result_path.write_text(json.dumps(previous), encoding="utf-8")

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("resume regenerated an already passing paper")

    monkeypatch.setattr("tools.live_generation_matrix.subprocess.run", unexpected_call)

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
