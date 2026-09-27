from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from Backend.Core.layout_conformance import REGISTRY_PATH
from Backend.Core.layout_master import (
    LayoutConformanceError,
    PageCountPolicy,
    Rect,
    TextSlot,
    conform_pdf_to_box_template,
    draw_text_slot,
    load_layout_master,
)
from tools.build_layout_masters import write_layout_master


def _sample_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(595.32, 841.92))
    for page in range(2):
        pdf.setFont("Helvetica", 11)
        pdf.drawString(50, 790, f"Question {page + 1}")
        pdf.line(40, 40, 555, 40)
        pdf.drawCentredString(297.66, 20, str(page + 1))
        pdf.showPage()
    pdf.save()


@pytest.mark.parametrize("mutation", [None, "missing-credit", "blank-padding", "missing-package"])
def test_content_driven_cs_scheme_requires_complete_credit(tmp_path, mutation):
    import pymupdf
    from cspapergen.cli import generate_package

    from Backend.Core.layout_conformance import conform_generated_documents

    paths = generate_package(output_dir=tmp_path, seed=26092701, dry_run=True)
    if mutation == "missing-package":
        paths.pop("assessment_package")
    elif mutation:
        with pymupdf.open(paths["mark_scheme"]) as document:
            if mutation == "missing-credit":
                page = next(page for page in document if "Final answer = 24.72 MiB" in page.get_text())
                for rect in page.search_for("Final answer = 24.72 MiB"):
                    page.add_redact_annot(rect)
                page.apply_redactions()
            else:
                document.new_page(width=595.32, height=841.92)
            document.saveIncr()
    if mutation:
        with pytest.raises(LayoutConformanceError, match=r"requires|omits|padding"):
            conform_generated_documents("computer_science", "2", paths)
    else:
        result = conform_generated_documents("computer_science", "2", paths)["mark_scheme"]
        assert result["checked_parts"] > 30
        assert result["actual_page_count"] < result["reference_page_count"]


def test_content_driven_cs_paper1_scheme_checks_every_assessed_part(tmp_path):
    from cspapergen.cli import generate_package

    from Backend.Core.layout_conformance import (
        _aqa_cs_printed_credit,
        runtime_page_count_policy,
    )

    paths = generate_package(output_dir=tmp_path, paper="1", seed=42, dry_run=True)
    result = _aqa_cs_printed_credit(
        paths["mark_scheme"], paths["assessment_package"], reference_count=41,
        paper="1",
    )
    assert runtime_page_count_policy("aqa-computer-science", "mark-scheme", 41, paper="1")["kind"] == result["policy"]
    assert result["checked_parts"] > 12
    assert result["checked_credit_statements"] > result["checked_parts"]
    assert result["actual_page_count"] < 41


@pytest.mark.parametrize("mutation", ["filler", "changed-code"])
def test_cs_paper1_reference_solution_cannot_be_replaced(tmp_path, mutation):
    import pymupdf
    from cspapergen.cli import generate_package

    from Backend.Core.layout_conformance import conform_generated_documents

    paths = generate_package(output_dir=tmp_path, paper="1", seed=42, dry_run=True)
    with pymupdf.open(paths["mark_scheme"]) as document:
        page = next(page for page in document if "Question 04: Example Python 3 solution" in page.get_text())
        if mutation == "filler":
            page.add_redact_annot(page.rect)
            page.apply_redactions()
            page.insert_text((43, 95), "Question 04: Example Python 3 solution\n" + "Unrelated filler\n" * 11)
        else:
            rect = page.search_for("return sum(results) / len(results)")[0]
            page.add_redact_annot(rect)
            page.apply_redactions()
            page.insert_text((rect.x0, rect.y1), "return 0")
        document.saveIncr()
    with pytest.raises(LayoutConformanceError, match="reference solution"):
        conform_generated_documents("computer_science", "1", paths)


@pytest.mark.parametrize(
    "mutation",
    [None, "missing-short-credit", "embedded-short-credit", "signed-short-credit",
     "decimal-short-credit", "fraction-short-credit", "spaced-sign-short-credit", "expression-short-credit",
     "valid-signed-answer", "valid-decimal-answer", "valid-fraction-answer",
     "duplicate-row", "duplicate-page", "wrong-question", "duplicate-levels"],
)
def test_cs_credit_belongs_to_one_assessed_row_with_valid_levels_continuation(tmp_path, mutation):
    import pymupdf

    from Backend.Core.assessment_package import _extract_items
    from Backend.Core.layout_conformance import _aqa_cs_printed_credit

    # Two assessed parts deliberately share a short answer. Global text presence
    # cannot establish that both parts actually printed their credit.
    blueprint = {"questions": [{"number": 11, "parts": [
        {"label": "1", "prompt": "Give the first result.", "marks": 1,
         "marking": {"ao": "AO2", "points": ["8;"]}},
        {"label": "2", "prompt": "Explain the second result.", "marks": 3,
         "marking": {"ao": "AO2", "points": ["8;"],
                     "accept": ["Equivalent working."],
                     "levels": ["Level 1: a justified result."]}},
    ]}]}
    wrong_numbers = {
        "embedded-short-credit": "18;",
        "signed-short-credit": "-8;",
        "decimal-short-credit": "0.8;",
        "fraction-short-credit": "1/8;",
        "spaced-sign-short-credit": "- 8;",
        "expression-short-credit": "2 + 8;",
    }
    valid_numbers = {
        "valid-signed-answer": "-8;",
        "valid-decimal-answer": "0.8;",
        "valid-fraction-answer": "1/8;",
    }
    if mutation in wrong_numbers:
        blueprint["questions"][0]["parts"][1]["marking"]["accept"] = [wrong_numbers[mutation]]
    elif mutation in valid_numbers:
        blueprint["questions"][0]["parts"][1]["marking"]["points"] = [valid_numbers[mutation]]
    package = tmp_path / "assessment.json"
    package.write_text(json.dumps({
        "subject": "computer_science", "paper": "2", "blueprint": blueprint,
        "items": _extract_items(blueprint, subject="computer_science", paper_number="2"),
    }), encoding="utf-8")
    path = tmp_path / "scheme.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(595.32, 841.92))
    for page in range(5):
        pdf.drawString(52, 710, f"General guidance {page + 1}")
        pdf.showPage()

    def row(question, part, y, lines, *, continuation=False):
        pdf.setFont("Helvetica", 11)
        pdf.drawString(52, y, question)
        pdf.drawString(86, y, part)
        pdf.drawString(125, y, "Extended response levels" if continuation else "All marks AO2")
        for index, line in enumerate(lines, 1):
            pdf.drawString(125, y - 15 * index, line)

    row("11", "1", 672, ["8;"])
    second_lines = ["A. Equivalent", "working."]
    if mutation in wrong_numbers:
        second_lines = ["A. " + wrong_numbers[mutation]]
    elif mutation != "missing-short-credit":
        second_lines.insert(0, valid_numbers.get(mutation, "8;"))
    row("12" if mutation == "wrong-question" else "11", "2", 580, second_lines)
    if mutation == "duplicate-row":
        row("11", "1", 450, ["8;"])
    pdf.showPage()
    row("11", "", 672, ["Level 1: a justified result."], continuation=True)
    if mutation == "duplicate-levels":
        row("11", "", 580, ["Level 1: a justified result."], continuation=True)
    pdf.save()
    if mutation == "duplicate-page":
        with pymupdf.open(path) as document:
            document.fullcopy_page(5)
            document.saveIncr()

    if mutation and mutation not in valid_numbers:
        with pytest.raises(LayoutConformanceError, match=r"omits|duplicate|unassessed|continuation"):
            _aqa_cs_printed_credit(path, package, reference_count=24)
    else:
        result = _aqa_cs_printed_credit(path, package, reference_count=24)
        assert result["checked_parts"] == 2
        assert result["checked_credit_statements"] == 4
        assert result["actual_page_count"] == 7


def test_layout_master_preserves_coordinates_without_reference_text(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    output = tmp_path / "master.json"
    _sample_pdf(source)

    write_layout_master(
        source,
        output,
        family="test-family",
        paper="1",
        document_role="question-paper",
    )

    raw = output.read_text(encoding="utf-8")
    master = load_layout_master(output)
    assert master.page_count == 2
    assert master.pages[0].media_box == Rect(0, 0, 595.32, 841.92)
    assert master.recurring_furniture
    assert '"text"' not in raw
    assert "Question 1" not in raw


def test_fixed_text_slot_rejects_overflow() -> None:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(200, 200))
    slot = TextSlot(
        rect=Rect(10, 10, 40, 20),
        font_name="Helvetica",
        font_size=11,
        leading=13,
    )

    with pytest.raises(LayoutConformanceError):
        draw_text_slot(pdf, 200, slot, "This text cannot fit")


def test_page_count_policy_is_exact_unless_a_measured_range_is_declared() -> None:
    exact = PageCountPolicy.exact(24)
    variable = PageCountPolicy.range(20, 28)

    assert exact.accepts(24)
    assert not exact.accepts(23)
    assert variable.accepts(20)
    assert variable.accepts(26)
    assert not variable.accepts(29)


def test_runtime_registry_covers_every_supported_paper() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    expected = {
        "accounting_aqa:1",
        "accounting_aqa:2",
        "business_aqa:1",
        "business_aqa:2",
        "business_aqa:3",
        "economics_aqa:1",
        "economics_aqa:2",
        "economics_aqa:3",
        "computer_science:1",
        "computer_science:2",
        "computer_science_ocr:1",
        "computer_science_ocr:2",
        "economics_ocr:1",
        "economics_ocr:2",
        "economics_ocr:3",
        "economics:1",
        "economics:2",
        "economics:3",
    }

    assert set(registry["papers"]) == expected
    assert registry["copyrighted_text_included"] is False
    assert all(
        record["question-paper"]["page_count"] > 0
        and record["question-paper"]["page_count_policy"]["kind"] == "exact"
        and len(record["question-paper"]["page_boxes"])
        == record["question-paper"]["page_count"]
        and all(
            set(boxes) == {"media", "crop", "trim", "bleed", "art"}
            for boxes in record["question-paper"]["page_boxes"]
        )
        for record in registry["papers"].values()
    )


def test_box_conformance_preserves_vector_drawings(tmp_path: Path) -> None:
    import pymupdf as fitz

    path = tmp_path / "drawing.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(595.28, 841.89))
    pdf.setTitle("Metadata survives conformance")
    pdf.line(50, 50, 500, 50)
    pdf.save()

    conform_pdf_to_box_template(
        path,
        {
            "media": [0, 0, 595.32, 841.92],
            "crop": [0, 0, 595.32, 841.92],
            "trim": [0, 0, 595.32, 841.92],
            "bleed": [0, 0, 595.32, 841.92],
            "art": [0, 0, 595.32, 841.92],
        },
    )

    document = fitz.open(path)
    try:
        assert document[0].get_drawings()
        assert document.metadata["title"] == "Metadata survives conformance"
    finally:
        document.close()


def test_box_conformance_is_no_op_when_boxes_already_match(
    tmp_path: Path,
) -> None:
    path = tmp_path / "already-conformant.pdf"
    _sample_pdf(path)
    boxes = {
        "media": [0, 0, 595.32, 841.92],
        "crop": [0, 0, 595.32, 841.92],
        "trim": [0, 0, 595.32, 841.92],
        "bleed": [0, 0, 595.32, 841.92],
        "art": [0, 0, 595.32, 841.92],
    }
    conform_pdf_to_box_template(path, boxes)
    first_digest = hashlib.sha256(path.read_bytes()).hexdigest()

    conform_pdf_to_box_template(path, boxes)

    assert hashlib.sha256(path.read_bytes()).hexdigest() == first_digest
