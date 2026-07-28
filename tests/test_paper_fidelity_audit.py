from pathlib import Path
from unittest.mock import patch

import fitz
import pytest

from tools.paper_fidelity_audit import (
    KNOWN_REFERENCE_MUPDF_DIAGNOSTICS,
    _generated_document,
    _geometry_scores,
    _render_page_pixmap,
    profile,
)


def test_generated_document_supports_app_per_paper_directories(tmp_path: Path):
    nested = tmp_path / "paper-1" / "question.pdf"
    nested.parent.mkdir()
    nested.touch()

    assert _generated_document(tmp_path, "question.pdf") == nested


def test_render_similarity_is_independent_of_pdf_primitive_type(tmp_path: Path):
    vector_path = tmp_path / "vector.pdf"
    image_path = tmp_path / "image.pdf"

    vector = fitz.open()
    page = vector.new_page()
    page.draw_rect(fitz.Rect(60, 80, 535, 760), width=0.7)
    page.insert_text((90, 130), "Question 1  Explain the effect of a change in demand.", fontsize=11)
    page.draw_line((90, 190), (500, 190), width=0.7)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    vector.save(vector_path)
    vector.close()

    raster = fitz.open()
    page = raster.new_page()
    page.insert_image(page.rect, pixmap=pixmap)
    raster.save(image_path)
    raster.close()

    vector_profile = profile(vector_path)
    image_profile = profile(image_path)
    scores = _geometry_scores(
        vector_profile["geometry"],
        image_profile["geometry"],
    )

    assert scores["render_placement"] >= 0.80


def test_render_diagnostics_are_tolerated_only_for_reference_papers():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((90, 130), "Static examination content", fontsize=11)

    with patch.object(
        fitz.TOOLS,
        "mupdf_warnings",
        return_value="premature end of data in flate filter",
    ):
        with pytest.raises(RuntimeError, match="premature end"):
            _render_page_pixmap(page, page.rect.width, page.rect.height, frozenset())
        pixmap = _render_page_pixmap(
            page,
            page.rect.width,
            page.rect.height,
            frozenset(KNOWN_REFERENCE_MUPDF_DIAGNOSTICS),
        )

    assert pixmap.width > 0
    document.close()
