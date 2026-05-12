from pathlib import Path
import re

from pastpapergen.exam_dates import formatted_economics_exam_date
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import render_source_booklet
from pastpapergen.syllabus import load_syllabus


def test_source_booklet_for_paper_1_only_uses_section_b(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "source.pdf"

    render_source_booklet(blueprint, syllabus, output)
    pdf_bytes = output.read_bytes()

    assert b"Source Booklet" in pdf_bytes
    assert b"Paper" in pdf_bytes
    assert b"reference" in pdf_bytes
    assert b"Sources for use with SECTION B" in pdf_bytes
    assert b"Extract A" in pdf_bytes
    assert b"Extract D" in pdf_bytes
    assert b"SECTION C" not in pdf_bytes
    assert _pdf_page_count(output) == 4


def test_source_booklet_has_figure_extracts_and_source_attributions(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "source.pdf"

    render_source_booklet(blueprint, syllabus, output)
    text = _pdf_text(output)

    assert "Extract A" in text
    assert "Extract B" in text
    assert "Extract C" in text
    assert "Extract D" in text
    assert "Source: adapted from public reports and economic data" in text
    assert "constructed economic data" not in text


def test_source_booklet_extracts_have_reference_style_line_numbers(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "source.pdf"

    render_source_booklet(blueprint, syllabus, output)
    text = _pdf_text(output)

    assert re.search(r"\b5\b", text)
    assert re.search(r"\b10\b", text)


def test_source_booklet_for_paper_3_uses_both_sections(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_3")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "source.pdf"

    render_source_booklet(blueprint, syllabus, output)
    pdf_bytes = output.read_bytes()

    assert b"Sources for use with SECTION A" in pdf_bytes
    assert b"Sources for use with SECTION B" in pdf_bytes


def _pdf_page_count(path: Path) -> int:
    import subprocess

    result = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError("Pages not found")


def _pdf_text(path: Path) -> str:
    import subprocess

    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_source_cover_uses_date_panel_not_mock_examination_label(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "source.pdf"

    render_source_booklet(blueprint, syllabus, output)
    first_page = _pdf_text(output).split("\f")[0]

    assert "Mock Examination" not in first_page


def test_paper_2_source_cover_uses_official_date_and_session(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_2")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "source.pdf"

    render_source_booklet(blueprint, syllabus, output)
    first_page = _pdf_text(output).split("\f")[0]

    assert formatted_economics_exam_date("paper_2") in first_page
    assert "Afternoon (Time: 2 hours)" in first_page
