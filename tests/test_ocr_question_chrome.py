from pathlib import Path

import pymupdf
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from Backend.Core.reportlab_theme import OCRAnswerLines, OCRComputerScienceAnswerLines


@pytest.mark.parametrize("factory,legacy_spacing", [(OCRAnswerLines, 6), (OCRComputerScienceAnswerLines, 4.7)])
def test_ocr_rulings_use_source_dark_dot_glyphs_and_pitch_without_growing_area(tmp_path, factory, legacy_spacing):
    output = tmp_path / "rulings.pdf"
    lines = factory(12)
    canvas = Canvas(str(output), pagesize=A4)
    lines.drawOn(canvas, 72, 100)
    canvas.save()
    with pymupdf.open(output) as pdf:
        spans = [s for b in pdf[0].get_text("dict")["blocks"] if "lines" in b for line in b["lines"] for s in line["spans"] if s["text"].count(".") > 100]
    # Source OCR 2024 CS2 p29 / Economics1 p17: Arial 11, #231f20,
    # full-stop advances ~3.056pt and 26.004pt baseline pitch.
    assert len(spans) >= 5
    assert all(s["size"] == pytest.approx(11) and s["color"] == 0x231F20 for s in spans)
    assert (spans[0]["bbox"][2] - spans[0]["bbox"][0]) / len(spans[0]["text"]) == pytest.approx(3.056, abs=.01)
    assert abs(spans[1]["origin"][1] - spans[0]["origin"][1]) == pytest.approx(26, abs=.05)
    assert lines.height == pytest.approx(12 * legacy_spacing * mm)


@pytest.mark.parametrize("family,paper_id", [("cs", "paper_1"), ("cs", "paper_2"), ("economics", "paper_1"), ("economics", "paper_2"), ("economics", "paper_3")])
def test_end_of_question_page_does_not_instruct_candidate_to_turn_over(tmp_path, family, paper_id):
    if family == "cs":
        from ocrcsgen import configs, generator, render_pdf, syllabus
        root = Path("Resources/computer-science/ocr/generator")
    else:
        from ocregen import configs, generator, render_pdf, syllabus
        root = Path("Resources/economics/ocr/generator")
    paper = generator.build_paper(configs.RULES[paper_id], syllabus.load_syllabus(root / "data/syllabus.json"), 123)
    output = tmp_path / "question-paper.pdf"
    render_pdf.render_question_paper(paper, output)
    with pymupdf.open(output) as pdf:
        pages = [page.get_text() for page in pdf]
    final = [text for text in pages if "END OF QUESTION PAPER" in text]
    assert len(final) == 1
    assert "Turn over" not in final[0]
    assert any("Turn over" in text for text in pages[2:5])
