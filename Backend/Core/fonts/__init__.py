from __future__ import annotations

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONTS_DIR = Path(__file__).resolve().parent

FONT_CANDIDATES: dict[str, list[tuple[str, int]]] = {
    "ExamSans": [
        (str(_FONTS_DIR / "ExamSans.ttf"), 0),
        (str(_FONTS_DIR / "ExamSans-Regular.ttf"), 0),
        ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 0),
    ],
    "ExamSans-Bold": [
        (str(_FONTS_DIR / "ExamSans-Bold.ttf"), 0),
        ("/System/Library/Fonts/HelveticaNeue.ttc", 1),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1),
    ],
    "ExamSans-Italic": [
        (str(_FONTS_DIR / "ExamSans-Italic.ttf"), 0),
        ("/System/Library/Fonts/HelveticaNeue.ttc", 2),
        ("/System/Library/Fonts/Supplemental/Arial Italic.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 2),
    ],
    "AQAArial": [
        (str(_FONTS_DIR / "AQAArial.ttf"), 0),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 0),
    ],
    "AQAArial-Bold": [
        (str(_FONTS_DIR / "AQAArial-Bold.ttf"), 0),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1),
    ],
    "AQACourier": [
        (str(_FONTS_DIR / "AQACourier.ttf"), 0),
        ("/System/Library/Fonts/Supplemental/Courier New.ttf", 0),
    ],
}


def register_font(font_name: str, fallback: str = "Times-Roman") -> str:
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name
    candidates = FONT_CANDIDATES.get(font_name, [])
    for candidate_path, subfont_index in candidates:
        path = Path(candidate_path)
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(path), subfontIndex=subfont_index))
                return font_name
            except Exception:
                continue
    pdfmetrics.registerFont(TTFont(font_name, fallback))
    return font_name


def register_fonts(*font_names: str, default_fallback: str = "Times-Roman") -> dict[str, str]:
    return {name: register_font(name, fallback=default_fallback) for name in font_names}
