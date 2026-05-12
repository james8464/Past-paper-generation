import subprocess
from datetime import date

from cspapergen.exam_dates import paper2_exam_date
from cspapergen.generator import build_paper2_blueprint
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
