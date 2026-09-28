from importlib import import_module
from pathlib import Path

import pymupdf as fitz
import pytest

from Backend.Core.pdf_validation import validate_pdf_for_release


@pytest.mark.parametrize(
    "subject,module,paper_id,label,size",
    [
        ("accounting", "aqaaccountgen", "paper_1", "ACCOUNTING", 27),
        ("business", "aqabizgen", "paper_1", "BUSINESS", 27.96),
        ("economics", "aqaecongen", "paper_1", "Economics", 27.96),
        ("economics", "aqaecongen", "paper_2", "ECONOMICS", 27),
        ("economics", "aqaecongen", "paper_3", "ECONOMICS", 27),
    ],
)
def test_aqa_cover_faces_are_embedded_and_body_fonts_unchanged(
    tmp_path, subject, module, paper_id, label, size
):
    rules = import_module(module + ".configs").RULES
    syllabus = import_module(module + ".syllabus").load_syllabus(
        Path("Resources") / subject / "aqa/generator/data/syllabus.json"
    )
    paper = import_module(module + ".generator").build_paper(
        rules[paper_id], syllabus, 123
    )
    path = tmp_path / "paper.pdf"
    import_module(module + ".render_pdf").render_question_paper(paper, path)
    _check_cover_and_body(path, label, size)


@pytest.mark.parametrize("number", [1, 2])
def test_specialist_cs_cover_uses_same_faces_without_changing_body(tmp_path, number):
    from cspapergen.generator import build_paper1_blueprint, build_paper2_blueprint
    from cspapergen.render_pdf import render_question_paper
    from cspapergen.syllabus import load_syllabus

    if number == 1:
        paper, _ = build_paper1_blueprint(load_syllabus(), seed=123)
    else:
        paper = build_paper2_blueprint(load_syllabus(), seed=123)
    path = tmp_path / "cs.pdf"
    render_question_paper(paper, path)
    _check_cover_and_body(path, "COMPUTER SCIENCE", 27.96)


@pytest.mark.parametrize(
    "subject", ["Accounting", "Business", "Economics", "Computer Science"]
)
def test_shared_mark_scheme_cover_embeds_measured_open_sans_roles(tmp_path, subject):
    from reportlab.platypus import SimpleDocTemplate

    from Backend.Core.exam_cover import CoverProfile, MarkSchemeCover
    from Backend.Core.fonts import register_fonts

    register_fonts("AQAArial", "AQAArial-Bold")
    profile = CoverProfile("aqa", subject, "7136/1", "Paper 1", "2 hours", 80)
    path = tmp_path / "scheme.pdf"
    SimpleDocTemplate(str(path)).build(
        [MarkSchemeCover(profile, font="AQAArial", bold_font="AQAArial-Bold")]
    )
    with fitz.open(path) as document:
        spans = _spans(document[0])
        for text, face in (
            ("A-level", "OpenSans-SemiBold"),
            (subject.upper(), "OpenSans-SemiBold"),
            ("7136/1", "OpenSans-SemiBold"),
            ("Paper 1", "OpenSansRoman-Medium"),
            ("Mark scheme", "OpenSans-SemiBold"),
        ):
            assert next(s for s in spans if s["text"] == text)["font"] == face
        fonts = [font for font in document[0].get_fonts() if "OpenSans" in font[3]]
        assert len(fonts) == 2
        assert all(len(document.extract_font(font[0])[3]) > 1000 for font in fonts)


def _check_cover_and_body(path, subject, size):
    with fitz.open(path) as document:
        page = document[0]
        spans = _spans(page)
        for text, face in (
            ("A-level", "OpenSansRoman-Medium"),
            (subject, "OpenSans-SemiBold"),
        ):
            span = next(s for s in spans if s["text"] == text)
            assert span["font"] == face
            assert span["size"] == pytest.approx(size, abs=0.01)
        used = [font for font in page.get_fonts() if "OpenSans" in font[3]]
        assert len(used) >= 2
        assert all(len(document.extract_font(font[0])[3]) > 1000 for font in used)
        assert all("OpenSans" not in span["font"] for span in _spans(document[1]))
        assert (
            max(span["bbox"][3] for span in spans) <= page.rect.height - 5 * 72 / 25.4
        )
    validate_pdf_for_release(path, subject=subject.casefold())


def _spans(page):
    return [
        s
        for b in page.get_text("dict")["blocks"]
        for line in b.get("lines", [])
        for s in line["spans"]
    ]
