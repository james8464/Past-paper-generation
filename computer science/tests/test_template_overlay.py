import subprocess
from datetime import date

from cspapergen.cli import generate_package
from cspapergen.generator import build_paper2_blueprint
from cspapergen.render_pdf import render_question_paper
from cspapergen.syllabus import load_syllabus
from cspapergen.template_overlay import apply_question_paper_template


def test_question_paper_template_overlay_writes_a4_pdf(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=44, dry_run=True)
    templated = tmp_path / "templated.pdf"

    apply_question_paper_template(paths["question_paper"], templated, reference_pdf=paths["question_paper"])

    output = subprocess.check_output(["pdfinfo", str(templated)], text=True)
    assert "Page size:       595.32 x 841.92 pts (A4)" in output
    assert templated.stat().st_size > 0


def test_question_paper_template_overlay_replaces_reference_cover_date(tmp_path, monkeypatch):
    import cspapergen.render_pdf as render_pdf

    class OldDate(date):
        @classmethod
        def today(cls):
            return cls(2024, 6, 18)

    blueprint = build_paper2_blueprint(load_syllabus(), seed=44)
    generated = tmp_path / "generated.pdf"
    reference = tmp_path / "reference.pdf"
    templated = tmp_path / "templated.pdf"

    render_question_paper(blueprint, generated)
    monkeypatch.setattr(render_pdf, "date", OldDate)
    render_question_paper(blueprint, reference)

    apply_question_paper_template(generated, templated, reference_pdf=reference)

    first_page = subprocess.check_output(["pdftotext", "-layout", "-f", "1", "-l", "1", str(templated), "-"], text=True)
    expected_date = f"{date.today():%A} {date.today().day} {date.today():%B %Y}"
    assert expected_date in first_page
    assert "Tuesday 18 June 2024" not in first_page
