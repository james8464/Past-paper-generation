from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph

from Backend.Core.fonts import register_font, register_fonts


def test_cover_fonts_use_real_open_sans_without_changing_body_aliases() -> None:
    register_fonts(
        "ExamCover-Medium", "ExamCover-SemiBold", "AQAArial", "AQAArial-Bold"
    )
    assert pdfmetrics.getFont("ExamCover-Medium").face.name == b"OpenSansRoman-Medium"
    assert pdfmetrics.getFont("ExamCover-SemiBold").face.name == b"OpenSans-SemiBold"
    assert pdfmetrics.getFont("AQAArial").face.name == b"Arimo-Regular"
    assert pdfmetrics.getFont("AQAArial-Bold").face.name == b"Arimo-Bold"


def test_cover_title_widths_match_measured_open_sans_reference() -> None:
    import pytest

    register_fonts("ExamCover-Medium", "ExamCover-SemiBold")
    # Source PDF advances differ slightly from upstream3.003, below0.3pt.
    assert pdfmetrics.stringWidth(
        "A-level", "ExamCover-Medium", 27.96
    ) == pytest.approx(88.439, abs=0.3)
    assert pdfmetrics.stringWidth(
        "Economics", "ExamCover-SemiBold", 27.96
    ) == pytest.approx(143.569, abs=0.3)


def test_missing_font_uses_registered_standard_font_alias() -> None:
    font_name = "TestMissingFont-Bold"

    assert register_font(font_name) == font_name
    assert pdfmetrics.getFont(font_name).face.name == "Helvetica-Bold"


def test_fallback_family_supports_bold_paragraph_markup() -> None:
    register_fonts("TestFallbackFamily", "TestFallbackFamily-Bold")

    paragraph = Paragraph(
        "<b>Section A</b>",
        ParagraphStyle("fallback", fontName="TestFallbackFamily"),
    )

    assert paragraph.frags[0].fontName == "TestFallbackFamily-Bold"
