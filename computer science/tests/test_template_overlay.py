import subprocess
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from cspapergen.cli import generate_package
from cspapergen.exam_dates import formatted_paper2_exam_date, paper2_exam_date
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
    expected_date = formatted_paper2_exam_date()
    assert expected_date in first_page
    assert "Tuesday 18 June 2024" not in first_page
    assert f"IB/G/Jun{paper2_exam_date():%y}/G4003/E12" in first_page
    assert "IB/G/Jun24/G4003/E12" not in first_page


def test_mark_scheme_template_overlay_replaces_reference_year(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=44, dry_run=True, template_overlay=True)

    first_pages = subprocess.check_output(
        ["pdftotext", "-layout", "-f", "1", "-l", "5", str(paths["mark_scheme"]), "-"],
        text=True,
    )

    assert f"June {paper2_exam_date():%Y}" in first_pages
    assert f"JUNE {paper2_exam_date():%Y}" in first_pages
    assert "June 2024" not in first_pages
    assert "JUNE 2024" not in first_pages
    assert f"Copyright © {paper2_exam_date():%Y} AQA" in first_pages


def test_question_paper_template_overlay_uses_generated_inner_pages(tmp_path):
    generated = tmp_path / "generated.pdf"
    reference = tmp_path / "reference.pdf"
    templated = tmp_path / "templated.pdf"
    _two_page_pdf(generated, header_x=300, body_x=300, footer_x=300)
    _two_page_pdf(reference, header_x=55, body_x=55, footer_x=55)

    apply_question_paper_template(generated, templated, reference_pdf=reference)

    assert _dark_pixels(templated, (55, 31, 115, 41)) < 20
    assert _dark_pixels(templated, (300, 31, 360, 41)) > 250
    assert _dark_pixels(templated, (300, 151, 360, 161)) > 250
    assert _dark_pixels(templated, (55, 151, 115, 161)) < 20
    assert _dark_pixels(templated, (55, 801, 115, 811)) < 20
    assert _dark_pixels(templated, (300, 801, 360, 811)) > 250
    assert _dark_pixels(templated, (490, 801, 550, 811)) > 250


def test_question_paper_template_overlay_removes_clipped_left_artifact(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=6311719426104587507, dry_run=True)

    assert _dark_pixels(paths["question_paper"], (46, 103, 64, 119)) < 200


def test_question_paper_template_overlay_has_no_reference_turn_over_bleed(tmp_path):
    paths = generate_package(output_dir=tmp_path, seed=680685491133987222, dry_run=True)

    text = subprocess.check_output(
        ["pdftotext", "-layout", "-f", "3", "-l", "3", str(paths["question_paper"]), "-"],
        text=True,
    )
    assert "Turn over for the next question" not in text


def _two_page_pdf(path, *, header_x: int, body_x: int, footer_x: int) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.drawString(55, 405, "Tuesday 18 June 2024")
    pdf.showPage()
    pdf.rect(header_x, 800, 60, 10, stroke=0, fill=1)
    pdf.rect(body_x, 680, 60, 10, stroke=0, fill=1)
    pdf.rect(footer_x, 30, 60, 10, stroke=0, fill=1)
    pdf.rect(490, 30, 60, 10, stroke=0, fill=1)
    pdf.showPage()
    pdf.save()


def _dark_pixels(path, rect: tuple[int, int, int, int]) -> int:
    import fitz

    doc = fitz.open(path)
    try:
        pixmap = doc[1].get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(*rect), colorspace=fitz.csGRAY)
        return sum(1 for value in pixmap.samples if value < 32)
    finally:
        doc.close()
