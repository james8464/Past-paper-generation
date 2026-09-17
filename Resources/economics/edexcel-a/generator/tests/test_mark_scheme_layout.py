from pathlib import Path
from types import SimpleNamespace

import pytest
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.render_pdf import (
    MS_MAX_ROW_HEIGHT,
    _mark_scheme_rows,
    _ms_row_height,
    _one_mark_points,
    _source_backed_mark_scheme_lines,
    render_mark_scheme,
)
from pastpapergen.syllabus import load_syllabus

from Backend.Core.generation_date import formatted_generation_date
from Backend.Core.pdf_text import extract_pdf_text, pdf_font_names
from Backend.Core.pdf_validation import validate_pdf_for_release

ROOT = Path(__file__).resolve().parents[1]


def test_mark_scheme_uses_reference_style_sections(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    first_page = text.split("\f")[0]
    assert "Mark Scheme (Results)" in text
    assert formatted_generation_date() in first_page
    assert "Practice Paper" not in first_page
    assert "General Marking Guidance" in text
    assert "Question" in text
    assert "Answer" in text
    assert "Mark" in text
    assert "Knowledge" in text
    assert "Application" in text
    _assert_complete_contract_scheme(output, blueprint)


def test_mark_scheme_guidance_explains_consistent_awarding(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=42
    )
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    normalized_text = " ".join(text.split())
    assert "valid alternative wording" in text
    assert "same analytical link more than once" in text
    assert "Mark only against the published criteria" in text
    assert "full credit when the response meets the criterion" in normalized_text

    import pymupdf as fitz

    with fitz.open(output) as document:
        for x0, y0, _x1, _y1, block, *_rest in document[2].get_text("blocks"):
            if "General Marking Guidance" in block:
                assert x0 == pytest.approx(84, abs=1)
                assert y0 == pytest.approx(144, abs=3)
                break
        else:
            raise AssertionError("general marking guidance heading not found")


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
    assert "KAA 1-4 marks:" in text
    assert "KAA 13-16 marks:" in text
    assert "Evaluation 7-9 marks:" in text
    assert "0 for no relevant" in text
    assert "Level 5" not in text


def test_source_backed_credit_criteria_render_as_examiner_point_entries():
    syllabus = load_syllabus(ROOT / "data" / "syllabus_seed.json")
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=42
    )

    rows = _mark_scheme_rows(blueprint, syllabus)
    first_answer_lines = next(row["answer_lines"] for row in rows if row["number"] == "1(a)")

    assert any(line.startswith("● AO1 (2 marks):") for line in first_answer_lines)


def test_source_backed_mcq_criteria_keep_reference_bold_and_italic_markers():
    item = SimpleNamespace(
        prompt="Which response is correct?",
        mark_breakdown="AO1 1",
        mark_scheme=[
            "The only correct answer is B",
            "Reject A: the stated condition is not sufficient.",
            "AO1 (1 mark): selects B.",
        ],
    )

    lines = _source_backed_mark_scheme_lines(item)

    assert "The only correct answer is B" in lines
    assert "Reject A: the stated condition is not sufficient." in lines
    assert "● AO1 (1 mark): selects B." in lines


def test_mark_scheme_front_matter_matches_reference_structure(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    normalised = " ".join(text.split())
    assert "Unofficial practice qualification material" in text
    assert "Independent practice material" in text
    assert "Question Paper Log Number" in text
    assert "Publications Code" in text
    assert "not produced, endorsed or approved" in normalised
    assert "Pearson or any exam board" in normalised


def test_mark_scheme_qualification_page_uses_reference_text_inset(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=42
    )
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    import pymupdf as fitz

    with fitz.open(output) as document:
        for x0, y0, _x1, _y1, block, *_rest in document[1].get_text("blocks"):
            if "Unofficial practice qualification material" in block:
                assert x0 == pytest.approx(57, abs=1)
                assert y0 == pytest.approx(96, abs=3)
                break
        else:
            raise AssertionError("qualification heading not found")


def test_mark_scheme_cover_uses_reference_serif_face(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)
    assert any("Tinos" in name for name in pdf_font_names(output))


def test_mark_scheme_table_uses_reference_content_inset(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(
        load_builtin_paper_config("paper_1"), syllabus, seed=42
    )
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    import pymupdf as fitz

    with fitz.open(output) as document:
        for page in document:
            for x0, y0, _x1, _y1, text, *_rest in page.get_text("blocks"):
                if "Question\nNumber" in text:
                    assert x0 == pytest.approx(86, abs=1)
                    assert y0 == pytest.approx(90, abs=2)
                    return
    raise AssertionError("mark-scheme table header not found")


def test_mark_scheme_uses_reference_italic_face_for_mcq_distractors(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    assert any("Verdana-Italic" in name for name in pdf_font_names(output))


@pytest.mark.parametrize(
    ("paper_id", "expected_x", "expected_y"),
    [
        ("paper_1", 56.7, 304.0),
        ("paper_2", 37.0, 264.4),
        ("paper_3", 42.5, 297.8),
    ],
)
def test_mark_scheme_cover_title_uses_paper_specific_reference_position(
    tmp_path,
    paper_id,
    expected_x,
    expected_y,
):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config(paper_id)
    blueprint = build_paper_blueprint(config, syllabus, seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)
    _x0, y0, _x1, y1 = _text_block_bbox(output, "Mark Scheme (Results)")

    assert _x0 == pytest.approx(expected_x, abs=1)
    assert y0 == pytest.approx(expected_y, abs=1)
    assert y1 - y0 >= 27.5


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
    config.sections[0].part_command_words[0] = ["calculate", "mcq"]
    blueprint = _blueprint_with_section_a_calculation(config, syllabus, "elasticity_data_table")
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "Working: -1.4 × (-5)" in text
    assert "Quantity-demanded percentage change: 7.0%" in text


def test_mark_scheme_generic_data_calculation_matches_table_values(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    config.sections[0].part_command_words[0] = ["calculate", "mcq"]
    blueprint = _blueprint_with_section_a_calculation(config, syllabus, "data_table")
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = " ".join(_pdf_text(output).split())
    assert "Working: (88.0 − 74.2) ÷ 74.2 × 100" in text
    assert "Quantity-index percentage increase: 18.6%" in text
    assert "Value A" not in text


def test_mark_scheme_rows_fit_within_single_page_after_long_extracts():
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=12397218355689870975)

    row_heights = [_ms_row_height(row["answer_lines"]) for row in _mark_scheme_rows(blueprint, syllabus)]

    assert max(row_heights) <= MS_MAX_ROW_HEIGHT


@pytest.mark.parametrize("paper_id,seed", [("paper_1", 42), ("paper_1", 26080122), ("paper_2", 42), ("paper_3", 42)])
def test_contract_scheme_pagination_preserves_all_credit_without_filler(tmp_path, paper_id, seed):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    blueprint = build_paper_blueprint(load_builtin_paper_config(paper_id), syllabus, seed=seed)
    output = tmp_path / "ms.pdf"
    render_mark_scheme(blueprint, syllabus, output)
    _assert_complete_contract_scheme(output, blueprint)
    validate_pdf_for_release(output, subject="economics",
        paper_number=paper_id[-1], role="mark_scheme")


def _assert_complete_contract_scheme(output, blueprint):
    import pymupdf as fitz
    with fitz.open(output) as document:
        # Reference publications may contain deliberately empty diagram pages.
        # These original contracts do not: never pad a new scheme to that count.
        assert all(page.get_text().strip() for page in document)
        text = " ".join(" ".join(page.get_text() for page in document).split())
    for question in blueprint.questions:
        for item in question.parts or [question]:
            for point in item.mark_scheme:
                assert " ".join(point.split()) in text, (question.number, point)
    assert text.count("Allocation:") == sum(len(q.parts) or 1 for q in blueprint.questions)


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
    assert "Indicative content:" in text
    assert "unrecoverable development costs" in text
    assert "distribution network" in text
    assert "not additive" in text


def test_mark_scheme_valid_points_are_clean_exam_sentences(tmp_path):
    syllabus = load_syllabus(Path("data/syllabus_seed.json"))
    config = load_builtin_paper_config("paper_1")
    blueprint = build_paper_blueprint(config, syllabus, seed=3005729008840236763)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, syllabus, output)

    text = _pdf_text(output)
    assert "● ●" not in text
    assert "● :" not in text
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


def test_short_mark_scheme_prioritises_points_relevant_to_question_and_source() -> None:
    question = SimpleNamespace(
        prompt="Explain the likely relationship between the two goods.",
        source_text=(
            "The cross elasticity of demand is positive, and the price of one good "
            "has increased."
        ),
        indicative_content=[],
        mark_scheme=[
            "Cross elasticity of demand measures the responsiveness of demand for "
            "one good to a change in the price of another."
        ],
    )
    topic = SimpleNamespace(
        id="1.2.1",
        title="Demand",
        points=["Demand curves", "Price elasticity of demand"],
    )

    points = _one_mark_points(question, topic, limit=4)

    assert any("cross elasticity" in point.casefold() for point in points)
    assert any("quantity consumers are willing and able" in point for point in points)


def _pdf_text(path: Path) -> str:
    return extract_pdf_text(path)


def _pdf_page_count(path: Path) -> int:
    import subprocess

    result = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError("Pages not found")


def _text_block_bbox(path: Path, needle: str) -> tuple[float, float, float, float]:
    import pymupdf as fitz

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


def _blueprint_with_section_a_calculation(config, syllabus, stimulus_kind: str):
    # Select the requested valid variant directly. Unrelated latent templates
    # deliberately fail closed rather than supply missing numeric inputs.
    config.sections[0].stimulus_slots[0] = [stimulus_kind]
    for seed in range(1000):
        blueprint = build_paper_blueprint(config, syllabus, seed=seed)
        for question in blueprint.questions:
            if question.section == "A" and question.stimulus_kind == stimulus_kind and any(part.command_word == "calculate" for part in question.parts):
                return blueprint
    raise AssertionError(f"No Section A calculation found for stimulus {stimulus_kind}")
