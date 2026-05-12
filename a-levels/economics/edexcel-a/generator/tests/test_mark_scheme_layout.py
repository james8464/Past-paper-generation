from pathlib import Path

from pastpapergen.exam_dates import economics_exam_schedule
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import _mark_scheme_rows, _ms_row_height, render_mark_scheme
from pastpapergen.syllabus import load_syllabus


def test_mark_scheme_uses_reference_style_sections(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    first_page = text.split("\f")[0]
    assert "Mark Scheme (Results)" in text
    assert f"Summer {economics_exam_schedule('paper_1').date.year}" in first_page
    assert "Practice Paper" not in first_page
    assert "General Marking Guidance" in text
    assert "Question" in text
    assert "Answer" in text
    assert "Mark" in text
    assert "Knowledge" in text
    assert "Application" in text
    assert _pdf_page_count(output) >= 24


def test_mark_scheme_has_subquestion_tables_mcq_explanations_and_levels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "Question" in text
    assert "Number" in text
    assert "1(a)" in text
    assert "1(b)" in text
    assert "The only correct answer is" in text
    assert "Indicative content" in text
    assert "Level 1" in text
    assert "Level 2" in text
    assert "Level 3" in text
    assert "Level 4" in text
    assert "Level 5" in text


def test_mark_scheme_front_matter_matches_reference_structure(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "Edexcel and BTEC Qualifications" in text
    assert "Pearson: helping people progress, everywhere" in text
    assert "Question Paper Log Number" in text
    assert "Publications Code" in text
    assert "Pearson Education Ltd" in text


def test_mark_scheme_cover_title_uses_reference_scale_and_position(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)
    x0, y0, _x1, y1 = _text_block_bbox(output, "Mark Scheme (Results)")

    assert 285 <= y0 <= 325
    assert y1 - y0 >= 30


def test_mark_scheme_does_not_print_fake_blank_page_labels(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    assert "BLANK PAGE" not in _pdf_text(output)


def test_mark_scheme_calculation_rows_include_specific_working(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=12397218355689870975)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "5% x 1.4 = 7%" in text
    assert "quantity demanded increases by 7%" in text.lower()


def test_mark_scheme_generic_data_calculation_matches_table_values(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=0)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "((88.0 - 74.2) / 74.2) x 100 = 18.6%" in text
    assert "quantity demanded index increased by" in text.lower()
    assert "18.6%." in text
    assert "Value A" not in text


def test_mark_scheme_rows_fit_within_single_page_after_long_extracts():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=12397218355689870975)

    row_heights = [_ms_row_height(row["answer_lines"]) for row in _mark_scheme_rows(blueprint, syllabus)]

    assert max(row_heights) <= 720


def test_mark_scheme_mcq_explanations_are_option_specific(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "does not match" not in text


def test_mark_scheme_includes_question_specific_focus_and_answer_points(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = _blueprint_with_section_b_topic(config, syllabus, "3.4")
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "Question focus:" in text
    assert "Relevant source evidence:" in text
    assert "Valid points may include:" in text
    assert "digital games" in text


def test_mark_scheme_valid_points_are_clean_exam_sentences(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=3005729008840236763)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "●" not in text
    assert ":." not in text
    assert "\n           - Regulation." not in text


def test_mark_scheme_uses_uploaded_note_points_for_extended_questions(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = _blueprint_with_section_b_topic(config, syllabus, "3.4")
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output).lower()
    assert "perfect competition" in text or "contestability" in text


def _pdf_text(path: Path) -> str:
    import subprocess

    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _pdf_page_count(path: Path) -> int:
    import subprocess

    result = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError("Pages not found")


def _text_block_bbox(path: Path, needle: str) -> tuple[float, float, float, float]:
    import fitz

    doc = fitz.open(path)
    try:
        for block in doc[0].get_text("blocks"):
            x0, y0, x1, y1, text, *_ = block
            if needle in text:
                return x0, y0, x1, y1
    finally:
        doc.close()
    raise AssertionError(f"Text block not found: {needle}")


def _blueprint_with_section_b_topic(config, syllabus, topic_id: str):
    for seed in range(500):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        if any(question.section == "B" and question.topic_id == topic_id for question in blueprint.questions):
            return blueprint
    raise AssertionError(f"No Section B blueprint found for topic {topic_id}")
