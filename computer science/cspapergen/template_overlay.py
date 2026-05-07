from __future__ import annotations

import shutil
import ssl
import urllib.request
from urllib.error import URLError
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CACHE = PROJECT_ROOT / "data" / "templates" / "reference"
LOCAL_REFERENCE_DIR = Path.home() / "Downloads" / "CS paper 2"

REFERENCE_URLS = {
    "question_paper": "https://pmt.physicsandmathstutor.com/download/Computer-Science/A-level/Past-Papers/AQA/Paper-2/June%202024%20QP%20-%20Paper%202%20AQA%20Computer%20Science%20A-level.pdf",
    "mark_scheme": "https://pmt.physicsandmathstutor.com/download/Computer-Science/A-level/Past-Papers/AQA/Paper-2/June%202024%20MS%20-%20Paper%202%20AQA%20Computer%20Science%20A-level.pdf",
}

REFERENCE_NAMES = {
    "question_paper": "aqa-7517-paper-2-2024-qp.pdf",
    "mark_scheme": "aqa-7517-paper-2-2024-ms.pdf",
}

REFERENCE_PATTERNS = {
    "question_paper": ("*2024*QP*Paper*2*.pdf", "*QP*Paper*2*.pdf", "*Paper 2*.pdf"),
    "mark_scheme": ("*2024*MS*Paper*2*.pdf", "*MS*Paper*2*.pdf", "*Mark*Scheme*2*.pdf"),
}

QP_CONTENT_RECT = (46, 92, 571, 785)
QP_FIRST_CONTENT_RECT = QP_CONTENT_RECT
QP_FOOTER_RECT = (40, 785, 520, 842)
MS_CONTENT_RECT = (0, 35, 595, 790)
MS_FOOTER_RECT = (0, 790, 595, 842)
WATERMARK_RECTS = (
    (468, 0, 595, 42),
    (468, 800, 595, 842),
)


def ensure_reference_pdf(kind: str, reference_dir: Path | None = None) -> Path:
    if kind not in REFERENCE_URLS:
        raise ValueError(f"Unknown template kind: {kind}")

    local = _find_local_reference(kind, reference_dir)
    if local:
        return local

    REFERENCE_CACHE.mkdir(parents=True, exist_ok=True)
    target = REFERENCE_CACHE / REFERENCE_NAMES[kind]
    if not target.exists():
        _download_reference(REFERENCE_URLS[kind], target)
    return target


def apply_question_paper_template(generated_pdf: Path, output_pdf: Path, *, reference_pdf: Path | None = None) -> None:
    reference = reference_pdf or ensure_reference_pdf("question_paper")
    _apply_template(generated_pdf, output_pdf, reference_pdf=reference, content_rect=QP_CONTENT_RECT, footer_rect=QP_FOOTER_RECT, first_content_rect=QP_FIRST_CONTENT_RECT)


def apply_mark_scheme_template(generated_pdf: Path, output_pdf: Path, *, reference_pdf: Path | None = None) -> None:
    reference = reference_pdf or ensure_reference_pdf("mark_scheme")
    _apply_template(generated_pdf, output_pdf, reference_pdf=reference, content_rect=MS_CONTENT_RECT, footer_rect=MS_FOOTER_RECT)


def _find_local_reference(kind: str, reference_dir: Path | None) -> Path | None:
    search_dirs = [path for path in [reference_dir, LOCAL_REFERENCE_DIR] if path and path.exists()]
    for directory in search_dirs:
        for pattern in REFERENCE_PATTERNS[kind]:
            matches = sorted(directory.glob(pattern), reverse=True)
            if matches:
                return matches[0]
    return None


def _download_reference(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with target.open("wb") as output:
                shutil.copyfileobj(response, output)
    except URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise
        with urllib.request.urlopen(request, timeout=60, context=ssl._create_unverified_context()) as response:
            with target.open("wb") as output:
                shutil.copyfileobj(response, output)


def _apply_template(
    generated_pdf: Path,
    output_pdf: Path,
    *,
    reference_pdf: Path,
    content_rect: tuple[int, int, int, int],
    footer_rect: tuple[int, int, int, int],
    first_content_rect: tuple[int, int, int, int] | None = None,
) -> None:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for AQA template overlay. Run `python -m pip install -e .`.") from exc

    generated_pdf = Path(generated_pdf)
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output_pdf.with_suffix(".template-tmp.pdf") if generated_pdf.resolve() == output_pdf.resolve() else output_pdf

    generated = fitz.open(str(generated_pdf))
    reference = fitz.open(str(reference_pdf))
    output = fitz.open()
    content = fitz.Rect(*content_rect)
    first_content = fitz.Rect(*(first_content_rect or content_rect))
    footer = fitz.Rect(*footer_rect)

    try:
        for page_index in range(generated.page_count):
            generated_page = generated[page_index]
            page = output.new_page(width=generated_page.rect.width, height=generated_page.rect.height)
            if page_index == 0:
                page.show_pdf_page(page.rect, generated, page_index)
                continue

            reference_index = min(page_index, reference.page_count - 1)
            page_content = first_content if page_index == 1 else content
            page.show_pdf_page(page.rect, reference, reference_index)
            _whiteout(page, page_content, fitz)
            _whiteout(page, footer, fitz)
            for rect in WATERMARK_RECTS:
                _whiteout(page, fitz.Rect(*rect), fitz)
            page.show_pdf_page(page_content, generated, page_index, clip=page_content)
            page.show_pdf_page(footer, generated, page_index, clip=footer)

        output.save(str(temp_output), garbage=4, deflate=True)
    finally:
        output.close()
        reference.close()
        generated.close()

    if temp_output != output_pdf:
        temp_output.replace(output_pdf)


def _whiteout(page, rect, fitz) -> None:
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
