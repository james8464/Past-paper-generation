from reportlab.pdfbase import pdfmetrics

from Backend.Core.fonts import register_font


def test_missing_font_uses_registered_standard_font_alias() -> None:
    font_name = "TestMissingFont-Bold"

    assert register_font(font_name) == font_name
    assert pdfmetrics.getFont(font_name).face.name == "Times-Bold"
