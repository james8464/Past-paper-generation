from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pastpapergen.cli import generate_package


def test_cli_dry_run_creates_paper_package(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pastpapergen",
            "--paper",
            "1",
            "--seed",
            "99",
            "--syllabus",
            "data/syllabus_seed.json",
            "--out",
            str(tmp_path),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "paper-1-question-paper.pdf").read_bytes().startswith(b"%PDF")
    assert (tmp_path / "paper-1-source-booklet.pdf").read_bytes().startswith(b"%PDF")
    assert (tmp_path / "paper-1-mark-scheme.pdf").read_bytes().startswith(b"%PDF")

    audit = json.loads((tmp_path / "paper-1-audit.json").read_text(encoding="utf-8"))
    assert audit["paper_code"] == "9EC0/01"
    assert audit["seed"] == 99
    assert audit["total_marks"] == 100
    assert audit["syllabus_source"].startswith("Pearson Edexcel")
    assert audit["questions"]


def test_generate_package_without_seed_records_random_run_seed(tmp_path, monkeypatch):
    monkeypatch.setattr("pastpapergen.cli.secrets.randbits", lambda bits: 123456789)

    generate_package(
        paper="1",
        syllabus_path=Path("data/syllabus_seed.json"),
        output_dir=tmp_path,
        seed=None,
        model="qwen2.5:14b",
        ollama_url="http://localhost:11434",
        dry_run=True,
    )

    audit = json.loads((tmp_path / "paper-1-audit.json").read_text(encoding="utf-8"))
    assert audit["seed"] == 123456789


def test_generate_package_reports_rendering_progress(tmp_path):
    events = []

    generate_package(
        paper="1",
        syllabus_path=Path("data/syllabus_seed.json"),
        output_dir=tmp_path,
        seed=99,
        model="qwen2.5:14b",
        ollama_url="http://localhost:11434",
        dry_run=True,
        progress=events.append,
    )

    assert events == [
        "Loading syllabus",
        "Using seed 99",
        "Building paper blueprint",
        "Using built-in draft questions",
        "Validating paper",
        "Rendering question paper",
        "Rendering source booklet",
        "Rendering mark scheme",
        "Writing audit file",
        "Done",
    ]
