from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf as fitz
import pytest
from pastpapergen import render_pdf as renderer
from pastpapergen.cli import ADAPTER
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import render_source_booklet
from pastpapergen.syllabus import load_syllabus

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data/syllabus_seed.json")


def _compact(text):
    return re.sub(r"\s+", "", text)


def _extracts(path):
    result = {}
    section = None
    owner = None
    with fitz.open(path) as document:
        for page in document:
            lines = []
            for block in page.get_text("dict")["blocks"]:
                for row in block.get("lines", []):
                    spans = row["spans"]
                    text = "".join(span["text"] for span in spans)
                    # Printed line numbers occupy a separate narrow column;
                    # they are not numerical evidence inside the source prose.
                    if (
                        text.isdigit()
                        and row["bbox"][0] > 480
                        and all(abs(span["size"] - 7.5) < 0.1 for span in spans)
                    ):
                        continue
                    lines.append(text)
            for line in lines:
                section_match = re.search(r"\bSECTION ([AB])\b", line)
                if section_match:
                    section = section_match[1]
                    owner = None
                extract_match = re.fullmatch(r"Extract ([A-F])", line.strip())
                if extract_match:
                    owner = (section, extract_match[1])
                    assert owner not in result, f"Repeated source extract {owner}"
                    result[owner] = []
                elif owner is not None:
                    result[owner].append(line)
    return {key: "\n".join(value) for key, value in result.items()}


@pytest.fixture(params=[42, 123, 26083051])
def paper_three(tmp_path, request):
    assert Path(renderer.__file__).resolve() == ROOT / "pastpapergen/render_pdf.py"
    paper = build_paper_blueprint(
        load_builtin_paper_config("paper_3"), SYLLABUS, request.param
    )
    artifacts = ADAPTER.artifacts(paper, None, SYLLABUS, "3")
    source_artifact = next(
        artifact for artifact in artifacts if artifact.role == "source_booklet"
    )
    path = tmp_path / source_artifact.filename
    source_artifact.renderer(path)
    return paper, path


@pytest.mark.parametrize(
    "section,label", [("A", "B"), ("B", "D"), ("B", "E"), ("B", "F")]
)
def test_published_paper_three_booklet_binds_each_reference_to_its_source(
    paper_three, section, label
):
    paper, path = paper_three
    extracts = _extracts(path)
    assert (section, label) in extracts
    owners = [
        question
        for question in paper.questions
        if question.section == section
        and f"Extract {label}" in question.source_reference
    ]
    assert owners
    for question in owners:
        assert _compact(question.source_text) in _compact(extracts[(section, label)]), (
            question.number
        )


def test_paper_three_booklet_contains_complete_canonical_extracts_and_figures(
    paper_three,
):
    paper, path = paper_three
    assert set(_extracts(path)) == {
        ("A", "A"),
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("B", "E"),
        ("B", "F"),
    }
    with fitz.open(path) as document:
        assert len(document) == 8
        text = "\n".join(page.get_text() for page in document)
    for number in (1, 2, 3):
        assert text.count(f"Figure {number}: illustrative case information") == 1
    for question in paper.questions:
        label = re.search(r"Extract ([A-F])", question.source_reference)[1]
        assert _compact(question.source_text) in _compact(
            _extracts(path)[(question.section, label)]
        )


def test_paper_one_two_booklet_extract_selection_remains_unchanged(tmp_path):
    assert Path(renderer.__file__).resolve() == ROOT / "pastpapergen/render_pdf.py"
    for paper_id in ("paper_1", "paper_2"):
        paper = build_paper_blueprint(load_builtin_paper_config(paper_id), SYLLABUS, 42)
        path = tmp_path / f"{paper_id}.pdf"
        render_source_booklet(paper, SYLLABUS, path)
        assert set(_extracts(path)) == {("B", label) for label in "ABCD"}
        with fitz.open(path) as document:
            assert len(document) == 4


def test_public_paper_three_preview_preserves_blueprint_and_both_source_views(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT.parents[3] / "bridge.py"),
            "generate",
            "--subject",
            "economics",
            "--paper",
            "3",
            "--seed",
            "42",
            "--output",
            str(tmp_path),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    assert events[-1]["type"] == "done"
    files = {
        event["role"]: Path(event["path"])
        for event in events
        if event["type"] == "file"
    }
    paper = build_paper_blueprint(load_builtin_paper_config("paper_3"), SYLLABUS, 42)
    package = json.loads(files["assessment_package"].read_text())
    assert package["blueprint"] == paper.model_dump(mode="json")
    for role in ("source_booklet", "question_paper"):
        extracts = _extracts(files[role])
        for question in paper.questions:
            label = re.search(r"Extract ([A-F])", question.source_reference)[1]
            assert _compact(question.source_text) in _compact(
                extracts[(question.section, label)]
            )
