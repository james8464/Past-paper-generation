from pathlib import Path

import pymupdf as fitz
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from Backend.Core.exam_pages import ExamPageProfile, draw_exam_page


def _render(tmp_path: Path, profile: ExamPageProfile) -> fitz.Document:
    path = tmp_path / "page.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setTitle("Exam page geometry")
    draw_exam_page(
        pdf,
        profile,
        width=A4[0],
        height=A4[1],
        font="Helvetica",
        bold_font="Helvetica-Bold",
        page_number=36,
    )
    pdf.save()
    return fitz.open(path)


def _horizontal_lines(page: fitz.Page) -> list[fitz.Rect]:
    return [
        drawing["rect"]
        for drawing in page.get_drawings()
        if drawing["rect"].height <= 1 and drawing["rect"].width > 100
    ]


def test_aqa_additional_page_matches_measured_response_grid(tmp_path: Path) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="aqa",
            code="7127/1",
            heading="Additional page, if required",
            variant="additional",
        ),
    )
    try:
        page = document[0]
        drawings = page.get_drawings()
        grid = next(
            drawing["rect"]
            for drawing in drawings
            if drawing["rect"].width == pytest.approx(478.5, abs=2)
            and drawing["rect"].height > 500
        )
        assert tuple(grid) == pytest.approx((50, 66.5, 528.5, 748.6), abs=2)

        lines = sorted(_horizontal_lines(page), key=lambda rect: rect.y0)
        ruled = [line for line in lines if 95 < line.y0 < 749]
        gaps = [right.y0 - left.y0 for left, right in zip(ruled, ruled[1:])]
        assert len(ruled) >= 25
        assert 24.5 <= sorted(gaps)[len(gaps) // 2] <= 26.5

        text = page.get_text()
        assert "Question\nnumber" in text
        assert "Write the question numbers in the left-hand margin" in text
        assert "Independent practice material" not in text
    finally:
        document.close()


def test_aqa_legal_notice_page_reserves_the_measured_lower_region(
    tmp_path: Path,
) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="aqa",
            code="7127/1",
            heading="Additional page, if required",
            variant="additional",
            legal_notice=True,
        ),
    )
    try:
        page = document[0]
        grid = next(
            drawing["rect"]
            for drawing in page.get_drawings()
            if drawing["rect"].width == pytest.approx(478.5, abs=2)
            and drawing["rect"].height > 400
        )
        assert grid.y1 == pytest.approx(556.3, abs=2)
        assert "Independent practice material" in page.get_text()
    finally:
        document.close()


def test_aqa_continuation_page_matches_open_rule_geometry(tmp_path: Path) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="aqa",
            code="7132/1",
            heading="",
            variant="continuation",
        ),
    )
    try:
        lines = sorted(_horizontal_lines(document[0]), key=lambda rect: rect.y0)
        ruled = [line for line in lines if 70 < line.y0 < 760]
        assert len(ruled) == 27
        assert ruled[0].x0 == pytest.approx(91.2, abs=1)
        assert ruled[0].x1 == pytest.approx(533.0, abs=1)
        assert ruled[0].y0 == pytest.approx(79.5, abs=1)
        assert ruled[-1].y0 == pytest.approx(749.2, abs=1)
    finally:
        document.close()


def test_aqa_additional_page_visually_clears_existing_family_chrome(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cleared-page.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setStrokeColorRGB(1, 0, 0)
    pdf.setLineWidth(4)
    pdf.rect(40, 42, A4[0] - 80, A4[1] - 84, stroke=1, fill=0)
    draw_exam_page(
        pdf,
        ExamPageProfile(
            board="aqa",
            code="7132/1",
            heading="Additional page, if required",
            variant="additional",
        ),
        width=A4[0],
        height=A4[1],
        font="Helvetica",
        bold_font="Helvetica-Bold",
        page_number=29,
    )
    pdf.save()

    document = fitz.open(path)
    try:
        page = document[0]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        # The old left rail is under the white clearing layer. A tolerance is
        # used because the rasteriser anti-aliases the edge of the old stroke.
        red, green, blue = pixmap.pixel(80, 600)
        assert red > 245 and green > 245 and blue > 245
        red, green, blue = pixmap.pixel(400, 84)
        assert red > 245 and green > 245 and blue > 245
    finally:
        document.close()


def test_aqa_blank_page_has_no_response_grid(tmp_path: Path) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="aqa",
            code="7132/2",
            heading="There are no questions printed on this page",
            variant="blank",
        ),
    )
    try:
        page = document[0]
        assert "There are no questions printed on this page" in page.get_text()
        assert not [
            drawing
            for drawing in page.get_drawings()
            if drawing["type"] != "f"
            and drawing["rect"].width > 450
            and drawing["rect"].height > 500
        ]
    finally:
        document.close()


def test_aqa_do_not_write_blank_matches_measured_diagonal_shell(
    tmp_path: Path,
) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="aqa",
            code="7136/3",
            heading="There are no questions printed on this page",
            variant="blank",
            legal_notice=True,
            do_not_write=True,
        ),
    )
    try:
        page = document[0]
        text = page.get_text()
        assert "DO NOT WRITE ON THIS PAGE" in text
        assert "Independent practice material" in text
        diagonal = next(
            drawing["rect"]
            for drawing in page.get_drawings()
            if 420 < drawing["rect"].width < 430
            and 600 < drawing["rect"].height < 620
        )
        assert tuple(diagonal) == pytest.approx((114, 54, 538.6, 662.1), abs=3)
    finally:
        document.close()


def test_ocr_additional_page_matches_open_dotted_rule_geometry(
    tmp_path: Path,
) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="ocr",
            code="H446/01",
            heading="EXTRA ANSWER SPACE",
            variant="additional",
            legal_notice=True,
        ),
    )
    try:
        page = document[0]
        drawings = page.get_drawings()
        rules = sorted(
            (
                drawing["rect"]
                for drawing in drawings
                if drawing["rect"].height <= 1
                and drawing["rect"].width == pytest.approx(495.4, abs=2)
                and 120 < drawing["rect"].y0 < 650
            ),
            key=lambda rect: rect.y0,
        )
        assert len(rules) == 20
        assert rules[0].y0 == pytest.approx(137.1, abs=1)
        assert rules[-1].y0 == pytest.approx(631.2, abs=1)
        guide = next(
            drawing["rect"]
            for drawing in drawings
            if drawing["rect"].width <= 1 and drawing["rect"].height > 490
        )
        assert tuple(guide) == pytest.approx((106.3, 137.1, 106.3, 632.1), abs=1)

        text = page.get_text()
        assert "EXTRA ANSWER SPACE" in text
        assert "write the question numbers clearly in the margin" in text.replace(
            "\n", " "
        )
        assert "Independent practice material" in text
    finally:
        document.close()


@pytest.mark.parametrize(
    ("legal_notice", "expected_lines", "expected_last_y"),
    [(False, 27, 761.7), (True, 22, 631.7)],
)
def test_ocr_continuation_page_uses_full_open_rule_field(
    tmp_path: Path,
    legal_notice: bool,
    expected_lines: int,
    expected_last_y: float,
) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="ocr",
            code="H446/02",
            heading="",
            variant="continuation",
            legal_notice=legal_notice,
        ),
    )
    try:
        page = document[0]
        rules = sorted(
            (
                drawing["rect"]
                for drawing in page.get_drawings()
                if drawing["rect"].height <= 1
                and drawing["rect"].width == pytest.approx(495.4, abs=2)
                and drawing["dashes"] != "[] 0"
                and 70 < drawing["rect"].y0 < 780
            ),
            key=lambda rect: rect.y0,
        )
        assert len(rules) == expected_lines
        assert rules[0].y0 == pytest.approx(85.7, abs=1)
        assert rules[-1].y0 == pytest.approx(expected_last_y, abs=1)
        assert "write the question numbers clearly" not in page.get_text()
    finally:
        document.close()


def test_ocr_blank_page_has_only_declared_messages_and_no_answer_table(
    tmp_path: Path,
) -> None:
    document = _render(
        tmp_path,
        ExamPageProfile(
            board="ocr",
            code="H460/02",
            heading="BLANK PAGE",
            variant="blank",
            do_not_write=True,
        ),
    )
    try:
        page = document[0]
        text = page.get_text()
        assert "BLANK PAGE" in text
        assert "PLEASE DO NOT WRITE ON THIS PAGE" in text
        assert page.search_for("BLANK PAGE")[0].y0 == pytest.approx(62, abs=3)
        assert page.search_for("PLEASE DO NOT WRITE ON THIS PAGE")[0].y0 == (
            pytest.approx(416, abs=3)
        )
        assert not [
            drawing
            for drawing in page.get_drawings()
            if drawing["type"] != "f"
            and drawing["rect"].width > 450
            and drawing["rect"].height > 500
        ]
    finally:
        document.close()
