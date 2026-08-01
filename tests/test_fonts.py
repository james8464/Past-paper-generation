from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from Backend.Core.fonts import register_font, register_fonts


def test_missing_font_uses_registered_standard_font_alias() -> None:
    font_name = "TestMissingFont-Bold"

    assert register_font(font_name) == font_name
    assert pdfmetrics.getFont(font_name).face.name == "Times-Bold"


def test_fallback_family_supports_bold_paragraph_markup() -> None:
    register_fonts("TestFallbackFamily", "TestFallbackFamily-Bold")

    paragraph = Paragraph(
        "<b>Section A</b>",
        ParagraphStyle("fallback", fontName="TestFallbackFamily"),
    )

    assert paragraph.frags[0].fontName == "TestFallbackFamily-Bold"
