# Extract PDF text and font names using the bundled Python PDF library.

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz


# Extract stable reading-order text without a Poppler CLI dependency.
def extract_pdf_text(
    path: Path,
    *,
    first_page: int = 1,
    last_page: int | None = None,
) -> str:

    document = fitz.open(path)
    try:
        start = max(0, first_page - 1)
        stop = min(
            document.page_count,
            last_page if last_page is not None else document.page_count,
        )
        return "\f".join(
            document[index].get_text("text", sort=False) for index in range(start, stop)
        )
    finally:
        document.close()


# Return the font families actually used by visible text spans.
def pdf_font_names(path: Path) -> set[str]:

    document = fitz.open(path)
    try:
        return {
            str(span.get("font", ""))
            for page in document
            for block in page.get_text("dict").get("blocks", [])
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip()
        }
    finally:
        document.close()
