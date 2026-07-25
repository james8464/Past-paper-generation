from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from Backend.Core.providers import parse_json_object


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "bridge.py"


def run_bridge(*args: str) -> list[dict[str, object]]:
    result = subprocess.run(
        [sys.executable, str(BRIDGE), *args],
        check=True,
        capture_output=True,
        text=True,
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
    result = subprocess.run(
        [
            sys.executable,
            str(BRIDGE),
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
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    files = [Path(str(event["path"])) for event in events if event["type"] == "file"]
    assert files
    assert all(path.parent == tmp_path / "generated" for path in files)


def test_ollama_status_emits_json() -> None:
    events = run_bridge("ollama-status")
    assert events
    assert events[-1]["type"] == "ollama_status"
    assert "installed" in events[-1]


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
    assert files.keys() == {"question_paper", "source_booklet", "mark_scheme"}
    assert all(path.exists() for path in files.values())
    assert not any(event["type"] == "preview_page" for event in events)
    assert all("progress" in event for event in events if event["type"] == "progress")
    assert not (tmp_path / "paper-1-audit.json").exists()
    assert events[-1]["type"] == "done"


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
        assert files.keys() == {"question_paper", "mark_scheme"}
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
        assert files.keys() == {"question_paper", "mark_scheme"}
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
        assert files.keys() == {"question_paper", "mark_scheme"}
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
    assert files.keys() == {"question_paper", "mark_scheme"}
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
