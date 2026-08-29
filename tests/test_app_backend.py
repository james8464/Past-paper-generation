from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from Backend.Core.events import GenerationUpdate, progress_emitter
from Backend.Core.generation import checkpoint_path_for_job, handle_generate
from Backend.Core.mlx_setup import MLXModelSetupRequired
from Backend.Core.paths import absolute_user_path
from Backend.Core.providers import _safe_provider_detail, parse_json_object

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "bridge.py"


def run_bridge(
    *args: str,
    cwd: Path | None = None,
) -> list[dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(BRIDGE), *args],
        check=False,
        capture_output=True,
        cwd=cwd,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            f"bridge exited with {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def run_bridge_raw(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BRIDGE), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_relative_output_is_resolved_from_callers_working_directory(tmp_path: Path) -> None:
    events = run_bridge(
        "generate",
        "--subject",
        "economics_aqa",
        "--paper",
        "1",
        "--output",
        "generated",
        "--dry-run",
        "--seed",
        "123",
        cwd=tmp_path,
    )
    files = [Path(str(event["path"])) for event in events if event["type"] == "file"]
    assert files
    assert all(path.parent == tmp_path / "generated" for path in files)


def test_checkpoint_path_is_stable_and_outside_transaction_staging(
    tmp_path: Path,
) -> None:
    request = Namespace(
        subject="economics_aqa",
        paper="2",
        seed=123,
        provider="ollama",
        model="gemma4:12b",
    )

    first = checkpoint_path_for_job(request, tmp_path)
    second = checkpoint_path_for_job(request, tmp_path)

    assert first == second
    assert first.parent == tmp_path / ".papercreator-checkpoints"
    assert first.suffix == ".json"
    assert "gemma4" not in first.name


def test_structured_item_progress_emits_truthful_units(
    capsys: pytest.CaptureFixture[str],
) -> None:
    callback = progress_emitter()

    callback(
        GenerationUpdate(
            stage="review",
            message="Reviewing question 3",
            item_id="0/0/2",
            completed_units=2,
            total_units=12,
            attempt=1,
        )
    )

    event = json.loads(capsys.readouterr().out)
    assert event["stage"] == "review"
    assert event["item_id"] == "0/0/2"
    assert event["completed_units"] == 2
    assert event["total_units"] == 12
    assert event["attempt"] == 1
    assert event["progress"] == pytest.approx(0.08 + (2 / 12) * 0.70)


def test_output_path_preserves_sandbox_style_symlink(tmp_path: Path) -> None:
    target = tmp_path / "real-downloads"
    target.mkdir()
    sandbox_alias = tmp_path / "container-downloads"
    sandbox_alias.symlink_to(target, target_is_directory=True)

    assert absolute_user_path(sandbox_alias) == sandbox_alias

    events = run_bridge(
        "generate",
        "--subject",
        "economics_aqa",
        "--paper",
        "1",
        "--output",
        str(sandbox_alias),
        "--dry-run",
        "--seed",
        "123",
    )
    files = [Path(str(event["path"])) for event in events if event["type"] == "file"]
    assert files
    assert all(path.parent == sandbox_alias for path in files)
    assert all(path.exists() for path in files)


def test_ollama_status_emits_json() -> None:
    events = run_bridge("ollama-status")
    assert events
    assert events[-1]["type"] == "ollama_status"
    assert "installed" in events[-1]


def test_bundle_check_loads_every_advertised_generator() -> None:
    events = run_bridge("bundle-check")
    status = events[-1]
    assert status["type"] == "bundle_status"
    assert status["healthy"] is True
    assert status["errors"] == []
    assert len(status["generators"]) == 7


def test_economics_dry_run_generates_expected_files(tmp_path: Path) -> None:
    events = run_bridge(
        "generate",
        "--subject",
        "economics",
        "--paper",
        "1",
        "--output",
        str(tmp_path),
        "--dry-run",
        "--seed",
        "123",
    )
    files = {event["role"]: Path(str(event["path"])) for event in events if event["type"] == "file"}
    assert files.keys() == {
        "question_paper",
        "source_booklet",
        "mark_scheme",
        "assessment_package",
        "package_manifest",
    }
    assert all(path.exists() for path in files.values())
    assert not any(event["type"] == "preview_page" for event in events)
    assert all("progress" in event for event in events if event["type"] == "progress")
    assert not (tmp_path / "paper-1-audit.json").exists()
    assert events[-1]["type"] == "done"
    manifest = json.loads(files["package_manifest"].read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert manifest["generator"]["content_mode"] == "ai-assisted"
    assert manifest["request"]["seed"] == 123
    assert manifest["evidence"]["difficulty_independently_verified"] is False
    assert manifest["evidence"]["qualification_levels"] == {
        "engineering_validated": True,
        "visually_calibrated": True,
        "empirically_calibrated": False,
    }
    assessment = json.loads(
        files["assessment_package"].read_text(encoding="utf-8")
    )
    assert assessment["form_id"].startswith("economics-1-")
    assert (
        manifest["evidence"]["assessment_validation"]["form_id"]
        == assessment["form_id"]
    )
    reference_demand = manifest["evidence"]["reference_demand"]
    assert reference_demand == assessment["reference_demand"]
    assert reference_demand["passed"] is True
    assert reference_demand["empirical_equivalence_claimed"] is False
    assert manifest["inputs"]["reference_demand_profile_sha256"]
    assert set(manifest["outputs"]) == {
        "question_paper",
        "source_booklet",
        "mark_scheme",
        "assessment_package",
    }
    assert all(output["sha256"] for output in manifest["outputs"].values())


def test_protocol_v2_envelopes_every_backend_event(tmp_path: Path) -> None:
    events = run_bridge(
        "generate",
        "--subject",
        "economics_aqa",
        "--paper",
        "1",
        "--output",
        str(tmp_path),
        "--dry-run",
        "--seed",
        "123",
    )
    assert events[0]["type"] == "hello"
    assert events[0]["capabilities"] == [
        "cancel",
        "eta",
        "manifest",
        "transactional-output",
    ]
    assert all(event["protocol"] == 2 for event in events)
    assert [event["event_id"] for event in events] == list(
        range(1, len(events) + 1)
    )
    assert all(event["timestamp"] for event in events)


def test_aqa_economics_all_papers_generate_expected_files(tmp_path: Path) -> None:
    for paper in ("1", "2", "3"):
        output = tmp_path / paper
        events = run_bridge(
            "generate",
            "--subject",
            "economics_aqa",
            "--paper",
            paper,
            "--output",
            str(output),
            "--dry-run",
            "--seed",
            "123",
        )
        files = {
            event["role"]: Path(str(event["path"]))
            for event in events
            if event["type"] == "file"
        }
        expected = (
            {"question_paper", "source_booklet", "mark_scheme"}
            if paper == "3"
            else {"question_paper", "mark_scheme"}
        )
        expected.add("assessment_package")
        expected.add("package_manifest")
        assert files.keys() == expected
        assert all(path.exists() for path in files.values())
        assert events[-1]["type"] == "done"


def test_ocr_economics_all_papers_generate_expected_files(tmp_path: Path) -> None:
    for paper in ("1", "2", "3"):
        output = tmp_path / paper
        events = run_bridge(
            "generate",
            "--subject",
            "economics_ocr",
            "--paper",
            paper,
            "--output",
            str(output),
            "--dry-run",
            "--seed",
            "123",
        )
        files = {
            event["role"]: Path(str(event["path"]))
            for event in events
            if event["type"] == "file"
        }
        assert files.keys() == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
            "package_manifest",
        }
        assert all(path.exists() for path in files.values())
        assert events[-1]["type"] == "done"


def test_ocr_computer_science_all_papers_generate_expected_files(
    tmp_path: Path,
) -> None:
    for paper in ("1", "2"):
        output = tmp_path / paper
        events = run_bridge(
            "generate",
            "--subject",
            "computer_science_ocr",
            "--paper",
            paper,
            "--output",
            str(output),
            "--dry-run",
            "--seed",
            "123",
        )
        files = {
            event["role"]: Path(str(event["path"]))
            for event in events
            if event["type"] == "file"
        }
        assert files.keys() == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
            "package_manifest",
        }
        assert all(path.exists() for path in files.values())
        assert events[-1]["type"] == "done"


def test_aqa_business_all_papers_generate_expected_files(tmp_path: Path) -> None:
    for paper in ("1", "2", "3"):
        output = tmp_path / paper
        events = run_bridge(
            "generate",
            "--subject",
            "business_aqa",
            "--paper",
            paper,
            "--output",
            str(output),
            "--dry-run",
            "--seed",
            "123",
        )
        files = {
            event["role"]: Path(str(event["path"]))
            for event in events
            if event["type"] == "file"
        }
        expected = (
            {"question_paper", "source_booklet", "mark_scheme"}
            if paper == "3"
            else {"question_paper", "mark_scheme"}
        )
        expected.add("assessment_package")
        expected.add("package_manifest")
        assert files.keys() == expected
        assert all(path.exists() for path in files.values())
        assert events[-1]["type"] == "done"


def test_aqa_accounting_all_papers_generate_expected_files(tmp_path: Path) -> None:
    for paper in ("1", "2"):
        output = tmp_path / paper
        events = run_bridge(
            "generate",
            "--subject",
            "accounting_aqa",
            "--paper",
            paper,
            "--output",
            str(output),
            "--dry-run",
            "--seed",
            "123",
        )
        files = {
            event["role"]: Path(str(event["path"]))
            for event in events
            if event["type"] == "file"
        }
        assert files.keys() == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
            "package_manifest",
        }
        assert all(path.exists() for path in files.values())
        assert events[-1]["type"] == "done"


def test_cs_dry_run_generates_expected_files_without_audit(tmp_path: Path) -> None:
    events = run_bridge(
        "generate",
        "--subject",
        "computer_science",
        "--paper",
        "2",
        "--output",
        str(tmp_path),
        "--dry-run",
        "--seed",
        "123",
    )
    files = {event["role"]: Path(str(event["path"])) for event in events if event["type"] == "file"}
    assert files.keys() == {
        "question_paper",
        "mark_scheme",
        "assessment_package",
        "package_manifest",
    }
    assert all(path.exists() for path in files.values())
    assert not any(path.name.endswith("audit.json") for path in tmp_path.iterdir())
    assert events[-1]["type"] == "done"


def test_cs_paper1_dry_run_generates_on_screen_package(tmp_path: Path) -> None:
    events = run_bridge(
        "generate",
        "--subject",
        "computer_science",
        "--paper",
        "1",
        "--output",
        str(tmp_path),
        "--dry-run",
        "--seed",
        "123",
    )
    files = {event["role"]: Path(str(event["path"])) for event in events if event["type"] == "file"}
    assert files.keys() == {
        "question_paper",
        "preliminary_material",
        "electronic_answer_document",
        "skeleton_program",
        "data_file",
        "mark_scheme",
        "assessment_package",
        "package_manifest",
    }
    assert all(path.exists() for path in files.values())
    assert events[-1]["type"] == "done"


def test_missing_hosted_provider_key_returns_json_error(tmp_path: Path) -> None:
    result = run_bridge_raw(
        "generate",
        "--subject",
        "economics",
        "--paper",
        "1",
        "--output",
        str(tmp_path),
        "--provider",
        "openai",
        "--model",
        "gpt-4.1",
    )
    assert result.returncode == 2
    events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert events[-1]["type"] == "error"
    assert "API key" in str(events[-1]["message"])


def test_every_advertised_generator_requires_a_model_outside_preview(
    tmp_path: Path,
) -> None:
    result = run_bridge_raw(
        "generate",
        "--subject",
        "economics_aqa",
        "--paper",
        "1",
        "--output",
        str(tmp_path),
        "--provider",
        "openai",
        "--model",
        "",
    )

    assert result.returncode == 2
    events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert events[-1]["type"] == "error"
    assert events[-1]["code"] == "invalid_request"
    assert "Choose a model" in str(events[-1]["message"])


def test_bad_output_path_returns_json_error(tmp_path: Path) -> None:
    bad_output = tmp_path / "not-a-folder"
    bad_output.write_text("x")
    result = run_bridge_raw(
        "generate",
        "--subject",
        "economics",
        "--paper",
        "1",
        "--output",
        str(bad_output),
        "--dry-run",
    )
    assert result.returncode == 2
    events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert events[-1]["type"] == "error"
    assert "output folder" in str(events[-1]["message"])


def test_generation_reports_a_structured_mlx_setup_request(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def missing_model(*_args, **_kwargs):
        raise MLXModelSetupRequired("Approve setup again to restore it.")

    monkeypatch.setattr("Backend.Core.generation._invoke_plugin", missing_model)
    request = Namespace(
        output=str(tmp_path),
        api_key="",
        model="mlx-community/test-model",
        subject="economics",
        paper="1",
        provider="apple",
        dry_run=False,
        seed=123,
    )

    assert handle_generate(request) == 1
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[-1]["type"] == "error"
    assert events[-1]["code"] == "mlx_setup_required"


def test_backend_crash_is_structured_and_removes_staging_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    def crash(*_args, **_kwargs):
        raise RuntimeError("renderer process stopped unexpectedly")

    monkeypatch.setattr("Backend.Core.generation._invoke_plugin", crash)
    request = Namespace(
        output=str(tmp_path),
        api_key="",
        model="gemma4:12b",
        subject="economics",
        paper="1",
        provider="ollama",
        dry_run=False,
        seed=123,
    )

    assert handle_generate(request) == 1
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert events[-1]["code"] == "generation_failed"
    assert "renderer process stopped unexpectedly" in events[-1]["message"]
    assert not list(tmp_path.glob(".papercreator-*"))


def test_benchmark_emits_samples_and_verdict(tmp_path: Path) -> None:
    events = run_bridge("benchmark", "--duration", "1", "--output", str(tmp_path))
    assert any(event["type"] == "benchmark_metric" for event in events)
    assert any(event["type"] == "benchmark_sample" for event in events)
    sample = next(event for event in events if event["type"] == "benchmark_sample")
    assert "memory_pressure_percent" in sample
    assert "swap_used_gb" in sample
    assert "disk_free_gb" in sample
    assert "small_file_ms" in sample
    assert "pdf_pages_per_s" in sample
    metric_names = {event.get("name") for event in events if event["type"] == "benchmark_metric"}
    assert {"Memory Pressure", "Swap Used", "Output Free Space", "PDF Render", "Small-file Latency"} <= metric_names
    assert events[-1]["type"] == "benchmark_done"
    assert 0 <= float(events[-1]["score"]) <= 1


def test_hosted_json_parser_accepts_markdown_wrapped_json() -> None:
    assert parse_json_object('```json\n{"ok": true}\n```') == {"ok": True}
    assert parse_json_object('Here is the object:\n{"ok": true}\nDone.') == {"ok": True}


def test_hosted_json_parser_rejects_oversized_response() -> None:
    with pytest.raises(ValueError, match="1 MB"):
        parse_json_object('{"value":"' + ("x" * 1_048_576) + '"}')


def test_provider_error_detail_is_bounded_and_redacted() -> None:
    value = _safe_provider_detail(
        "Authorization: Bearer secret-token " + ("detail " * 200)
    )
    assert "secret-token" not in value
    assert len(value) <= 500
