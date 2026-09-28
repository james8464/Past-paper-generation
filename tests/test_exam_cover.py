from pathlib import Path

import pymupdf as fitz
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from Backend.Core.exam_cover import CoverProfile, MarkSchemeCover, QuestionPaperCover
from Backend.Core.fonts import register_fonts

FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
register_fonts(FONT, FONT_BOLD)


def _render(tmp_path: Path, board: str) -> fitz.Document:
    path = tmp_path / f"{board}-cover.pdf"
    profile = CoverProfile(
        board=board,
        subject="Accounting" if board == "aqa" else "Economics",
        code="7127/1" if board == "aqa" else "H460/01",
        paper_title=(
            "Paper 1: Financial Accounting" if board == "aqa" else "Microeconomics"
        ),
        duration="2 hours",
        total_marks=80,
    )
    document = SimpleDocTemplate(str(path), pagesize=A4)
    document.build(
        [
            MarkSchemeCover(
                profile,
                font=FONT,
                bold_font=FONT_BOLD,
            )
        ]
    )
    return fitz.open(path)


def _bbox(page: fitz.Page, text: str) -> fitz.Rect:
    return page.search_for(text)[0]


def test_aqa_mark_scheme_cover_matches_measured_title_grid(tmp_path: Path) -> None:
    document = _render(tmp_path, "aqa")
    try:
        page = document[0]
        assert _bbox(page, "PAPER").x0 == pytest.approx(46.8, abs=2)
        assert _bbox(page, "PAPER").y0 == pytest.approx(86, abs=4)
        assert _bbox(page, "CREATOR").y1 == pytest.approx(134, abs=4)
        assert _bbox(page, "A-level").x0 == pytest.approx(46.8, abs=2)
        spans = [
            s
            for b in page.get_text("dict")["blocks"]
            for line in b.get("lines", [])
            for s in line["spans"]
        ]
        for text, baseline in (
            ("A-level", 190.28),
            ("Paper 1", 294.56),
            ("Mark scheme", 323.6),
        ):
            span = next(s for s in spans if s["text"].startswith(text))
            assert span["origin"][1] == pytest.approx(baseline, abs=0.2)

        rule = next(
            drawing["rect"]
            for drawing in page.get_drawings()
            if drawing["rect"].width > 500 and drawing["rect"].height <= 1
        )
        assert tuple(rule) == pytest.approx((41.9, 147.6, 552.9, 147.6), abs=2)
        rules = [d for d in page.get_drawings() if d["rect"].width > 500]
        assert any(
            d["rect"].y0 == pytest.approx(305.66, abs=0.2)
            and d["width"] == pytest.approx(3)
            for d in rules
        )
        assert any(
            d["rect"].y0 == pytest.approx(360.44, abs=0.2)
            and d["width"] == pytest.approx(0.48)
            for d in rules
        )

        bars = [
            drawing["rect"]
            for drawing in page.get_drawings()
            if drawing["type"] == "f" and 740 < drawing["rect"].y0 < 790
        ]
        assert bars
        assert min(rect.x0 for rect in bars) == pytest.approx(47.9, abs=2)
        assert max(rect.x1 for rect in bars) == pytest.approx(224.6, abs=8)
    finally:
        document.close()


def test_ocr_mark_scheme_cover_matches_measured_title_grid(tmp_path: Path) -> None:
    document = _render(tmp_path, "ocr")
    try:
        page = document[0]
        assert _bbox(page, "PAPER").x0 == pytest.approx(59.5, abs=2)
        assert _bbox(page, "PAPER").y0 == pytest.approx(35, abs=4)
        assert _bbox(page, "CREATOR").y1 == pytest.approx(82, abs=4)
        assert _bbox(page, "GCE").x0 == pytest.approx(59.5, abs=2)
        assert _bbox(page, "GCE").y0 == pytest.approx(146.7, abs=3)
        assert _bbox(page, "Economics").y0 == pytest.approx(200.1, abs=3)
        assert _bbox(page, "H460/01").y0 == pytest.approx(243.1, abs=3)
        assert _bbox(page, "A Level").y0 == pytest.approx(293.7, abs=3)
        assert _bbox(page, "Mark Scheme for").y0 == pytest.approx(346.9, abs=3)
    finally:
        document.close()


@pytest.mark.parametrize(
    "code,title_y,session_y", [("7136/1", 290.3, 350.54), ("7136/3", 296.33, 356.57)]
)
def test_aqa_economics_scheme_cover_rules_follow_its_compact_title_grid(
    tmp_path, code, title_y, session_y
):
    path = tmp_path / "economics-scheme-cover.pdf"
    profile = CoverProfile("aqa", "Economics", code, "Paper booklet", "2 hours", 80)
    SimpleDocTemplate(str(path), pagesize=A4).build(
        [MarkSchemeCover(profile, font=FONT, bold_font=FONT_BOLD)]
    )
    with fitz.open(path) as document:
        page = document[0]
        rules = [d for d in page.get_drawings() if d["rect"].width > 500]
        assert any(
            d["rect"].y0 == pytest.approx(title_y + 11.1, abs=0.2)
            and d["width"] == pytest.approx(3)
            for d in rules
        )
        assert any(
            d["rect"].y0 == pytest.approx(session_y + 10.62, abs=0.2)
            and d["width"] == pytest.approx(0.48)
            for d in rules
        )


@pytest.mark.parametrize(
    "candidate_fields,left,title_baseline", [(True, 41.04, 311.2), (False, 48.0, 150.0)]
)
def test_aqa_question_cover_anchors_to_paper_not_story_margins(
    tmp_path, candidate_fields, left, title_baseline
):
    """Frame padding must not displace the identity block or candidate grid."""
    path = tmp_path / "question-cover.pdf"
    profile = CoverProfile(
        "aqa",
        "Economics",
        "7136/1",
        "Paper 1  Markets and market failure",
        "2 hours",
        80,
        candidate_fields=candidate_fields,
    )
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=72).build(
        [QuestionPaperCover(profile, font=FONT, bold_font=FONT_BOLD)]
    )
    with fitz.open(path) as document:
        spans = [
            s
            for b in document[0].get_text("dict")["blocks"]
            for line in b.get("lines", [])
            for s in line["spans"]
        ]
        title = next(s for s in spans if s["text"] == "A-level")
        assert title["origin"] == pytest.approx((left, title_baseline), abs=1.5)
        bars = [
            d["rect"]
            for d in document[0].get_drawings()
            if d["type"] == "f" and d["rect"].height > 20 and d["rect"].width < 2
        ]
        if candidate_fields:
            assert bars and all(bar.y0 > 775 for bar in bars)
        else:
            assert not bars


@pytest.mark.parametrize("paper_number", [1, 2])
def test_economics_booklet_cover_has_source_rules_and_readable_footer_code(
    tmp_path, paper_number
):
    path = tmp_path / "booklet-cover.pdf"
    profile = CoverProfile(
        "aqa",
        "Economics",
        f"7136/{paper_number}",
        "Paper booklet",
        "2 hours",
        80,
        candidate_fields=False,
        subject_label="Economics" if paper_number == 1 else "ECONOMICS",
    )
    SimpleDocTemplate(str(path), pagesize=A4).build(
        [QuestionPaperCover(profile, font=FONT, bold_font=FONT_BOLD)]
    )
    with fitz.open(path) as document:
        page = document[0]
        spans = [
            s
            for b in page.get_text("dict")["blocks"]
            for line in b.get("lines", [])
            for s in line["spans"]
        ]
        assert any(s["text"] == profile.subject_label for s in spans)
        code = next(s for s in spans if s["text"] == f"7136/{paper_number}")
        assert code["size"] == pytest.approx(20.04, abs=0.1)
        # Replacement font descenders need 1.2pt more clearance than the source.
        assert code["origin"][1] == pytest.approx(823.2, abs=0.2)
        assert max(s["bbox"][3] for s in spans) <= page.rect.height - 5 * 72 / 25.4
        rules = [
            d["rect"]
            for d in page.get_drawings()
            if d["rect"].width > 490 and d["rect"].height <= 1
        ]
        assert any(r.y0 == pytest.approx(119.52, abs=0.6) for r in rules)
        assert any(r.y0 == pytest.approx(762.35, abs=0.2) for r in rules)


@pytest.mark.parametrize("paper_number", [1, 2])
def test_economics_booklet_cover_uses_external_answers_and_actual_section_choices(
    tmp_path, paper_number
):
    from aqaecongen.configs import RULES
    from aqaecongen.generator import build_paper
    from aqaecongen.render_pdf import render_question_paper
    from aqaecongen.syllabus import load_syllabus

    syllabus = load_syllabus(
        Path("Resources/economics/aqa/generator/data/syllabus.json")
    )
    paper = build_paper(RULES[f"paper_{paper_number}"], syllabus, 123)
    path = tmp_path / "economics-booklet.pdf"
    render_question_paper(paper, path)
    with fitz.open(path) as document:
        text = " ".join(document[0].get_text().split())
        assert "spaces provided" not in text
        assert "Write your answers in the separate answer booklet." in text
        for section in paper.sections:
            assert f"Section {section.id}: {section.instructions}" in text


def test_aqa_cs_on_screen_cover_does_not_reserve_handwritten_identity_area(tmp_path):
    from cspapergen.generator import build_paper1_blueprint
    from cspapergen.render_pdf import _cover_page
    from cspapergen.syllabus import load_syllabus
    from reportlab.pdfgen.canvas import Canvas

    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=42)
    path = tmp_path / "on-screen-cover.pdf"
    pdf = Canvas(str(path), pagesize=(595.32, 841.92))
    _cover_page(pdf, blueprint)
    pdf.save()
    with fitz.open(path) as document:
        page = document[0]
        assert "Candidate signature" not in page.get_text()
        assert "For Examiner's Use" not in page.get_text()
        assert "Fill in the boxes" not in page.get_text()
        assert page.search_for("A-level")[0].y0 < 140
        assert "Electronic Answer Document" in page.get_text()
        session = page.search_for(blueprint.session)[0]
        time = page.search_for("Time allowed")[0]
        assert time.x0 > session.x1 + 5


def test_ocr_question_cover_uses_ocr_identity_and_materials_grid(tmp_path):
    profile = CoverProfile(
        "ocr",
        "Computer Science",
        "H446/02",
        "Algorithms and programming",
        "2 hours 30 minutes",
        140,
        materials=(
            "You may use a ruler (cm/mm).",
            "You may use an HB pencil.",
            "No calculators are permitted.",
        ),
        instructions=("Answer all questions.",),
    )
    path = tmp_path / "ocr-question-cover.pdf"
    SimpleDocTemplate(str(path), pagesize=A4).build(
        [QuestionPaperCover(profile, font=FONT, bold_font=FONT_BOLD)]
    )
    with fitz.open(path) as document:
        page = document[0]
        assert "Candidate signature" not in page.get_text()
        assert "No calculators are permitted" in page.get_text()
        assert "Algorithms and programming" in page.get_text()
        assert page.search_for("A Level Computer Science")[0].x0 == pytest.approx(
            94.96, abs=1
        )
        name = page.search_for("First name(s)")[0]
        assert 410 < name.y0 < 425
        materials = [
            d["rect"]
            for d in page.get_drawings()
            if 220 < d["rect"].width < 225 and 115 < d["rect"].height < 122
        ]
        assert len(materials) == 1


@pytest.mark.parametrize("module_name", ["ocrcsgen.render_pdf", "ocregen.render_pdf"])
def test_ocr_cover_template_does_not_overlay_body_page_furniture(tmp_path, module_name):
    import importlib
    from types import SimpleNamespace

    from reportlab.pdfgen.canvas import Canvas

    renderer = importlib.import_module(module_name)
    path = tmp_path / "chrome.pdf"
    pdf = Canvas(str(path), pagesize=A4)
    pdf.drawString(95, 761, "PAPER CREATOR")
    renderer._chrome(pdf, SimpleNamespace(page=1), "H446/02", "Question paper")
    pdf.save()
    with fitz.open(path) as document:
        assert document[0].get_text().strip() == "PAPER CREATOR"
