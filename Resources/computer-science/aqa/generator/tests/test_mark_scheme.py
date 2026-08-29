from cspapergen.generator import build_paper1_blueprint, build_paper2_blueprint
from cspapergen.render_pdf import render_mark_scheme
from cspapergen.syllabus import load_syllabus
from cspapergen.validation import validate_blueprint

from Backend.Core.generation_date import GENERATION_DATE_ENV
from Backend.Core.pdf_text import extract_pdf_text


def test_every_part_has_specific_marking_guidance():
    blueprint = build_paper2_blueprint(load_syllabus(), seed=99)

    for question in blueprint.questions:
        for part in question.parts:
            assert part.marking.points
            assert part.marking.ao
            assert any(";" in point for point in part.marking.points)


def test_validation_rejects_missing_part_mark_scheme():
    blueprint = build_paper2_blueprint(load_syllabus(), seed=99)
    question = blueprint.questions[0]
    broken_part = question.parts[0].model_copy(update={"marking": question.parts[0].marking.model_copy(update={"points": []})})
    broken_question = question.model_copy(update={"parts": [broken_part, *question.parts[1:]]})
    broken = blueprint.model_copy(update={"questions": [broken_question, *blueprint.questions[1:]]})

    try:
        validate_blueprint(broken, load_syllabus())
    except ValueError as error:
        assert "has no marking guidance" in str(error)
    else:
        raise AssertionError("validate_blueprint accepted missing marking guidance")


def test_mark_scheme_cover_uses_generation_date(tmp_path, monkeypatch):
    monkeypatch.setenv(GENERATION_DATE_ENV, "2024-06-18")
    blueprint = build_paper2_blueprint(load_syllabus(), seed=99)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    first_page = extract_pdf_text(output, first_page=1, last_page=1)
    assert "June 2024" in first_page


def test_mark_scheme_cover_uses_shared_measured_title_grid(tmp_path):
    import pymupdf as fitz
    import pytest

    blueprint = build_paper2_blueprint(load_syllabus(), seed=99)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        page = document[0]
        assert page.search_for("PAPER")[0].x0 == pytest.approx(46.8, abs=2)
        assert page.search_for("A-level")[0].y0 == pytest.approx(160.3, abs=3)
        assert page.search_for("Mark scheme")[0].y0 == pytest.approx(308.7, abs=3)
    finally:
        document.close()


def test_paper_2_mark_scheme_matches_measured_page_plan(tmp_path):
    import pymupdf as fitz

    blueprint = build_paper2_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        assert document.page_count == 35
        starts = {
            1: 6,
            2: 9,
            3: 12,
            4: 14,
            5: 15,
            6: 16,
            7: 20,
            8: 24,
            9: 26,
            10: 27,
            11: 28,
            12: 30,
            13: 33,
            14: 35,
        }
        for question, page_number in starts.items():
            assert f"{question:02d}" in document[page_number - 1].get_text()
    finally:
        document.close()


def test_paper_2_mark_scheme_keeps_reference_like_specific_content_density(
    tmp_path,
):
    import pymupdf as fitz

    blueprint = build_paper2_blueprint(load_syllabus(), seed=26080116)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        words = sum(len(page.get_text("words")) for page in document)
        assert words >= 4_500

        text = " ".join(page.get_text() for page in document).casefold()
        assert text.count("apply the guidance specifically") == 0
        assert text.count("credit precise technical terminology") <= 1
    finally:
        document.close()


def test_paper_1_mark_scheme_includes_measured_question_and_solution_pages(tmp_path):
    import pymupdf as fitz

    blueprint, _context = build_paper1_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        assert document.page_count == 41
        starts = {
            1: 6,
            2: 7,
            3: 7,
            4: 10,
            5: 13,
            6: 14,
            7: 16,
            8: 16,
            9: 17,
            10: 20,
            11: 22,
            12: 24,
        }
        for question, page_number in starts.items():
            assert f"{question:02d}" in document[page_number - 1].get_text()
        for page_index in (17, 18):
            continuation = document[page_index].get_text()
            assert "09" in continuation
            assert len(continuation.split()) > 20
        assert "VALIDATION TEST EVIDENCE" in document[17].get_text()
        assert "LOWER BOUNDARY" in document[17].get_text()
        assert "DUPLICATE IDENTIFIER" in document[18].get_text()
        assert "8 passed" in document[18].get_text()
        for page_index in (17, 18):
            fills = [
                drawing.get("fill")
                for drawing in document[page_index].get_drawings()
            ]
            assert any(
                fill is not None and max(fill) < 0.08
                for fill in fills
            )
        assert "Example Python 3 solution" in document[25].get_text()
        assert "Question 12" in document[40].get_text()
    finally:
        document.close()


def test_paper_1_mark_scheme_renders_question_specific_answer_artifacts(tmp_path):
    import pymupdf as fitz

    blueprint, _context = build_paper1_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        assert "Alternative valid matrix" in document[7].get_text()
        assert "Call" in document[8].get_text()
        assert "Mark range" in document[9].get_text()
        assert "Example evidence" in document[11].get_text()
    finally:
        document.close()
