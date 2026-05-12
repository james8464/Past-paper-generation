from __future__ import annotations

import time
from pathlib import Path

from app_bridge.events import emit, emit_progress
from app_bridge.paths import PREVIEW_CACHE


def emit_preview_pages(role: str, pdf_path: Path) -> None:
    try:
        import fitz
    except Exception:
        return

    run_dir = PREVIEW_CACHE / str(int(time.time() * 1000))
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        document = fitz.open(pdf_path)
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.45, 0.45), alpha=False)
            image_path = run_dir / f"{pdf_path.stem}-page-{page_index + 1}.png"
            pixmap.save(image_path)
            emit(
                "preview_page",
                role=role,
                page=page_index + 1,
                path=str(image_path),
                source_pdf=str(pdf_path),
            )
    except Exception as error:
        emit_progress(f"Could not create preview pages: {error}", stage="preview")
