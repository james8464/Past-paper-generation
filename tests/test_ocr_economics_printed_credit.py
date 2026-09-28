from pathlib import Path

import pymupdf as fitz
from ocregen.configs import RULES
from ocregen.generator import build_paper
from ocregen.render_pdf import render_mark_scheme
from ocregen.syllabus import load_syllabus

from Backend.Core.exam_blueprints import MarkSchemePoint


def test_ocr_guidance_retains_distinct_labels_when_credit_wording_is_identical(
    tmp_path,
):
    syllabus = load_syllabus(
        Path("Resources/economics/ocr/generator/data/syllabus.json")
    )
    paper = build_paper(RULES["paper_1"], syllabus, 123)
    question = paper.sections[0].options[0].questions[0]
    wording = "The curve shifts right"
    question.mark_scheme = [wording]
    question.structured_mark_scheme = [
        MarkSchemePoint(text=wording, marks=1, alternatives=[wording], allow=[wording]),
        MarkSchemePoint(
            text="Another credit", marks=1, do_not_accept=[wording], ignore=[wording]
        ),
    ]
    path = tmp_path / "labelled-credit.pdf"
    render_mark_scheme(paper, path)
    with fitz.open(path) as document:
        text = " ".join(" ".join(page.get_text().split()) for page in document)
        for prefix in ("Accept", "Allow", "Do not accept", "Ignore"):
            assert f"{prefix}: {wording}" in text


def test_ocr_economics_prints_all_credit_at_reference_body_size(tmp_path):
    syllabus = load_syllabus(
        Path("Resources/economics/ocr/generator/data/syllabus.json")
    )
    paper = build_paper(RULES["paper_1"], syllabus, 123)
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(paper, path)
    with fitz.open(path) as document:
        text = "".join("".join(page.get_text().split()) for page in document)
        for section in paper.sections:
            for option in section.options:
                for question in option.questions:
                    for point in question.mark_scheme:
                        assert "".join(point.split()) in text, (question.number, point)
        spans = [
            s
            for p in list(document)[10:-1]
            for b in p.get_text("dict")["blocks"]
            for line in b.get("lines", [])
            for s in line["spans"]
        ]
        credit = [s for s in spans if "credit" in s["text"].casefold()]
        assert credit and all(abs(s["size"] - 11) < 0.1 for s in credit)


def test_ocr_long_credit_expands_pages_without_clipping_or_repeated_padding(tmp_path):
    syllabus = load_syllabus(
        Path("Resources/economics/ocr/generator/data/syllabus.json")
    )
    paper = build_paper(RULES["paper_1"], syllabus, 123)
    baseline = tmp_path / "baseline.pdf"
    render_mark_scheme(paper, baseline)
    question = paper.sections[0].options[0].questions[2]
    points = [
        f"Distinct extended credit {i:03d}: explain the effect on incentives, costs and output in this market."
        for i in range(120)
    ]
    question.mark_scheme = points
    output = tmp_path / "long.pdf"
    render_mark_scheme(paper, output)
    with fitz.open(baseline) as before, fitz.open(output) as after:
        assert len(after) > len(before)
        text = "".join("".join(page.get_text().split()) for page in after)
        assert all("".join(point.split()) in text for point in points)
        for page in after:
            if "Distinct extended credit" in page.get_text():
                assert question.number in page.get_text()
