import subprocess
from datetime import date

from cspapergen.exam_dates import paper2_exam_date
from cspapergen.generator import build_paper1_blueprint, build_paper2_blueprint
from cspapergen.render_pdf import render_mark_scheme
from cspapergen.syllabus import load_syllabus
from cspapergen.validation import validate_blueprint


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


def test_mark_scheme_cover_uses_exam_series_year(tmp_path, monkeypatch):
    import cspapergen.render_pdf as render_pdf

    class OldDate(date):
        @classmethod
        def today(cls):
            return cls(2024, 6, 18)

    monkeypatch.setattr(render_pdf, "date", OldDate)
    blueprint = build_paper2_blueprint(load_syllabus(), seed=99)
    output = tmp_path / "ms.pdf"

    render_mark_scheme(blueprint, output)

    first_page = subprocess.check_output(["pdftotext", "-layout", "-f", "1", "-l", "1", str(output), "-"], text=True)
    assert f"June {paper2_exam_date().year}" in first_page


def test_paper_2_mark_scheme_matches_measured_page_plan(tmp_path):
    import fitz

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


def test_paper_1_mark_scheme_includes_measured_question_and_solution_pages(tmp_path):
    import fitz

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
        assert "Example Python 3 solution" in document[25].get_text()
        assert "Question 12" in document[40].get_text()
    finally:
        document.close()
