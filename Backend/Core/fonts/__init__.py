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
    "ExamMarkScheme": [
        (str(_FONTS_DIR / "ExamMarkScheme.ttf"), 0),
        ("/System/Library/Fonts/Supplemental/Verdana.ttf", 0),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", 0),
    ],
    "ExamMarkScheme-Bold": [
        (str(_FONTS_DIR / "ExamMarkScheme-Bold.ttf"), 0),
        ("/System/Library/Fonts/Supplemental/Verdana Bold.ttf", 0),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
    ],
}


def _standard_fallback(font_name: str, fallback: str) -> str:
    if "Courier" in font_name or font_name.endswith("Mono"):
        family = "Courier"
    elif fallback.startswith("Helvetica"):
        family = "Helvetica"
    else:
        family = "Times"

    if font_name.endswith("Bold"):
        return f"{family}-Bold"
    if font_name.endswith("Italic"):
        return f"{family}-Oblique" if family != "Times" else "Times-Italic"
    return family if family != "Times" else "Times-Roman"


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
    # Standard PDF fonts are face names, not TTF file paths. Register an alias
    # so renderers can keep using their semantic font name on non-macOS hosts.
    fallback_name = _standard_fallback(font_name, fallback)
    pdfmetrics.registerFont(pdfmetrics.Font(font_name, fallback_name, "WinAnsiEncoding"))
    return font_name


def register_fonts(*font_names: str, default_fallback: str = "Times-Roman") -> dict[str, str]:
    registered = {name: register_font(name, fallback=default_fallback) for name in font_names}
    families: dict[str, dict[str, str]] = {}
    for name in registered:
        if name.endswith("-BoldItalic"):
            family, role = name.removesuffix("-BoldItalic"), "boldItalic"
        elif name.endswith("-Bold"):
            family, role = name.removesuffix("-Bold"), "bold"
        elif name.endswith("-Italic"):
            family, role = name.removesuffix("-Italic"), "italic"
        else:
            family, role = name, "normal"
        families.setdefault(family, {})[role] = name

    for family, roles in families.items():
        normal = roles.get("normal") or next(iter(roles.values()))
        pdfmetrics.registerFontFamily(
            family,
            normal=normal,
            bold=roles.get("bold", normal),
            italic=roles.get("italic", normal),
            boldItalic=roles.get("boldItalic", roles.get("bold", normal)),
        )
    return registered
