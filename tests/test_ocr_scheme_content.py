from __future__ import annotations

import json
from pathlib import Path

import pymupdf
import pytest
from reportlab.pdfgen import canvas

from Backend.Core.assessment_package import _extract_items
from Backend.Core.layout_master import LayoutConformanceError


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "missing",
        "wrong-owner",
        "duplicate",
        "blank",
        "wrong-package",
        "front-orientation",
        "prompt-only",
        "numeric-alternative",
        "wrong-alternative-label",
        "missing-label",
        "labels-complete",
    ],
)
def test_ocr_scheme_checks_credit_per_question_not_reference_page_count(
    tmp_path, mutation
):
    from Backend.Core.ocr_scheme_content import verify_ocr_scheme_content

    questions = [
        {
            "number": "1(a)",
            "prompt": "Give the first result.",
            "marks": 1,
            "mark_scheme": ["8"],
            "structured_mark_scheme": [],
        },
        {
            "number": "1(b)",
            "prompt": "Explain the second result.",
            "marks": 2,
            "mark_scheme": [
                "8",
                "Cost increases as output falls.",
                "A developed causal chain links the market context to incentives and the resulting allocation of resources.",
            ],
            "structured_mark_scheme": [
                {
                    "text": "Cost increases as output falls.",
                    "allow": ["Equivalent reasoning."],
                    "do_not_accept": ["A change in revenue alone."],
                }
            ],
        },
    ]
    if mutation == "prompt-only":
        questions[1]["mark_scheme"].append("second result")
    if mutation in {"numeric-alternative", "wrong-alternative-label"}:
        questions[1]["structured_mark_scheme"][0]["allow"].append("9")
    if mutation in {"missing-label", "labels-complete"}:
        questions[1]["structured_mark_scheme"][0]["do_not_accept"] = [
            "Equivalent reasoning."
        ]
    blueprint = {"sections": [{"options": [{"questions": questions}]}]}
    package = tmp_path / "assessment.json"
    package.write_text(
        json.dumps(
            {
                "subject": "economics_ocr"
                if mutation != "wrong-package"
                else "economics",
                "paper": "1",
                "blueprint": blueprint,
                "items": _extract_items(
                    blueprint, subject="economics_ocr", paper_number="1"
                ),
            }
        )
    )
    path = tmp_path / "scheme.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(594.96, 842.04))
    for i in range(10):
        if i == 2 and mutation != "front-orientation":
            pdf.setPageSize((841.92, 595.32))
        pdf.drawString(50, 500, f"General marking instruction page {i + 1}")
        pdf.showPage()
    pdf.setPageSize((841.92, 595.32))
    pdf.setFont("Helvetica", 11)
    for index, (identifier, text) in enumerate(
        [
            ("1(a)", "8"),
            (
                "1(a)" if mutation == "wrong-owner" else "1(b)",
                "18" if mutation == "missing" else "8",
            ),
            ("1(b)", "Cost increases as output falls."),
            ("1(b)", "Allow: Equivalent reasoning."),
            (
                "1(b)",
                "Do not accept: Equivalent reasoning."
                if mutation == "labels-complete"
                else "Do not accept: A change in revenue alone.",
            ),
        ]
    ):
        y = 515 - index * 50
        pdf.drawString(48, y, identifier)
        pdf.drawString(122, y, text)
        if mutation == "missing" and index == 1:
            pdf.drawString(435, y, "8")  # A tariff is not an answer credit.
    pdf.drawString(48, 265, "1(b)")
    pdf.drawString(122, 265, questions[1]["mark_scheme"][2])
    pdf.drawString(48, 215, "1(b)")
    pdf.drawString(122, 215, questions[1]["prompt"])
    if mutation in {"numeric-alternative", "wrong-alternative-label"}:
        prefix = "Do not accept" if mutation == "wrong-alternative-label" else "Allow"
        pdf.drawString(470, 215, f"{prefix}: 9")
    pdf.showPage()
    if mutation == "blank":
        pdf.drawString(48, 540, "Question Answer Mark Guidance")
        pdf.showPage()
    pdf.setPageSize((595.32, 841.92))
    pdf.drawString(50, 700, "Independent practice material")
    pdf.drawString(
        50, 680, "Not produced, endorsed or approved by any examination board."
    )
    pdf.save()
    if mutation == "duplicate":
        with pymupdf.open(path) as doc:
            doc.fullcopy_page(10, 11)
            doc.saveIncr()
    if mutation not in {None, "numeric-alternative", "labels-complete"}:
        with pytest.raises(LayoutConformanceError):
            verify_ocr_scheme_content(path, package, paper="1", reference_count=30)
    else:
        result = verify_ocr_scheme_content(path, package, paper="1", reference_count=30)
        assert result["actual_page_count"] == 12
        assert result["checked_parts"] == 2
        assert result["complete_printed_credit"] is True


def test_ocr_scheme_policy_changes_only_schemes():
    from Backend.Core.layout_conformance import runtime_page_count_policy

    policy = runtime_page_count_policy("ocr-economics", "mark-scheme", 30, paper="1")
    assert policy["kind"] == "generated-ocr-economics-mark-scheme-content-v1"
    assert (
        runtime_page_count_policy("ocr-economics", "question-paper", 20, paper="1")[
            "kind"
        ]
        == "exact"
    )


def test_ocr_scheme_overflow_retains_landscape_pages_and_final_portrait(tmp_path):
    from ocregen.cli import generate_package

    from Backend.Core.layout_conformance import conform_generated_documents
    from Backend.Core.ocr_scheme_content import verify_ocr_scheme_content

    paths = generate_package(
        output_dir=tmp_path,
        paper="1",
        seed=123,
        dry_run=True,
        syllabus_path=Path("Resources/economics/ocr/generator/data/syllabus.json"),
    )
    result = conform_generated_documents("economics_ocr", "1", paths)["mark_scheme"]
    assert result["actual_page_count"] > result["reference_page_count"]
    with pymupdf.open(paths["mark_scheme"]) as document:
        for index, page in enumerate(document):
            assert (page.rect.width < page.rect.height) == (
                index < 2 or index == len(document) - 1
            )
    assert verify_ocr_scheme_content(
        paths["mark_scheme"],
        paths["assessment_package"],
        paper="1",
        reference_count=result["reference_page_count"],
    )["complete_printed_credit"]
