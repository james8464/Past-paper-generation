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
            assert all(point.strip() for point in part.marking.points)
            assert sum(part.marking.assessment_objectives.values()) == part.marks


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


def test_paper_2_mark_scheme_contains_each_question_without_padding(tmp_path):
    import pymupdf as fitz

    blueprint = build_paper2_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        text = " ".join(" ".join(page.get_text().split()) for page in document)
        for question in blueprint.questions:
            assert f"{question.number:02d}" in text
        assert "Indicative content continued" not in text
        assert text.count("The control unit sends a memory-read signal") == 1
        assert text.count("Final answer =") >= 1
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
        text = " ".join(page.get_text() for page in document).casefold()
        assert text.count("apply the guidance specifically") == 0
        assert text.count("credit precise technical terminology") <= 1
        assert text.count("do not award the same technical point more than once") <= 1
        for page in list(document)[5:]:
            for block in page.get_text("blocks"):
                if block[4].strip().isdigit():
                    continue
                assert block[1] >= 30
                assert block[3] <= 780
    finally:
        document.close()


def test_paper_1_mark_scheme_has_content_driven_rows_without_repeated_padding(tmp_path):
    import pymupdf as fitz

    blueprint, _context = build_paper1_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        assert document.page_count < 41
        text = "\n".join(page.get_text() for page in document)
        assert "Indicative content continued" not in text
        assert "Example solution guidance continued" not in text
        assert text.count("Example Python 3 solution") == 5
        for question in blueprint.questions:
            assert f"{question.number:02d}" in text
        for page in list(document)[5:]:
            body = page.get_text().replace("MARK SCHEME", "").strip()
            assert len(body.split()) > 10
    finally:
        document.close()


def test_paper_1_mark_scheme_renders_question_specific_answer_artifacts(tmp_path):
    import pymupdf as fitz

    blueprint, _context = build_paper1_blueprint(load_syllabus(), seed=42)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    document = fitz.open(output)
    try:
        text = "\n".join(page.get_text() for page in document)
        assert "Alternative valid matrix" in text
        assert "Call" in text
        assert "Mark range" in text
        assert "Expected: requirement satisfied" not in text
        solution_heading = next(
            page.search_for("Question 04: Example Python 3 solution")[0]
            for page in document
            if page.search_for("Question 04: Example Python 3 solution")
        )
        assert solution_heading.x0 <= 50
        assert solution_heading.y0 <= 110
    finally:
        document.close()
