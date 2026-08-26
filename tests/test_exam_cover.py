from pathlib import Path

import pymupdf as fitz
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from Backend.Core.exam_cover import CoverProfile, MarkSchemeCover
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
            "Paper 1: Financial Accounting"
            if board == "aqa"
            else "Microeconomics"
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
        assert _bbox(page, "A-level").y0 == pytest.approx(160.3, abs=3)
        assert _bbox(page, "Paper 1").y0 == pytest.approx(277.4, abs=3)
        assert _bbox(page, "Mark scheme").y0 == pytest.approx(308.7, abs=3)

        rule = next(
            drawing["rect"]
            for drawing in page.get_drawings()
            if drawing["rect"].width > 500 and drawing["rect"].height <= 1
        )
        assert tuple(rule) == pytest.approx((41.9, 147.6, 552.9, 147.6), abs=2)

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
