"""Preview certification requires notice glyphs after overlapping raster artwork."""

import pymupdf as fitz
import pytest

from Backend.Core.preview_presentation import (
    PREVIEW_NOTICE,
    PREVIEW_PRESENTATION,
    _notice_raster_order_unverifiable,
    validate_preview_pdf,
)


def fixture(path, position="later", style="white"):
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((40, 80), PREVIEW_NOTICE, fontsize=10)
        page.insert_text((40, 160), "Owned body content is unchanged.", fontsize=10)
        bounds = page.search_for(PREVIEW_NOTICE)[0] + fitz.Rect(-2, -2, 2, 2)
        if position == "outside":
            bounds = fitz.Rect(40, 220, 350, 250)
        alpha = style in {"transparent", "translucent"}
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 600, 60), alpha)
        if alpha:
            value = 0 if style == "transparent" else 64
            image.set_rect(image.irect, (value, value, value, value))
        else:
            image.clear_with(0 if style == "black" else 255)
            if style == "patterned":
                image.set_rect(fitz.IRect(100, 0, 300, 60), (0, 0, 0))
        page.insert_image(
            bounds, pixmap=image, keep_proportion=False, overlay=position != "before"
        )
        if alpha:
            assert page.get_images(full=True)[0][1] > 0, (
                "Fixture needs a real image mask"
            )
        document.save(path)


@pytest.mark.parametrize(
    "style", ["white", "black", "patterned", "transparent", "translucent"]
)
@pytest.mark.parametrize("position", ["before", "outside", "later"])
def test_raster_notice_order_is_structural_not_an_opacity_guess(
    tmp_path, position, style
):
    path = tmp_path / "owned-preview.pdf"
    fixture(path, position, style)
    original = path.read_bytes()
    if position == "later":
        with pytest.raises(ValueError, match="notice visibility cannot be verified"):
            validate_preview_pdf(path)
    else:
        assert validate_preview_pdf(path) == {
            "policy": PREVIEW_PRESENTATION,
            "first_page_notice": True,
        }
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "bounds",
    [(0, 0, float("nan"), 100), (0, 0, float("inf"), 100), (0, 0, 0, 0), (1, 2)],
)
@pytest.mark.parametrize("position", ["before", "later"])
def test_only_relevant_raster_geometry_must_be_verifiable(
    tmp_path, monkeypatch, bounds, position
):
    path = tmp_path / "geometry.pdf"
    fixture(path, position)
    original_log = fitz.Page.get_bboxlog

    def malformed_raster(page):
        return [
            (kind, bounds if kind == "fill-image" else rectangle)
            for kind, rectangle in original_log(page)
        ]

    monkeypatch.setattr(fitz.Page, "get_bboxlog", malformed_raster)
    if position == "later":
        with pytest.raises(ValueError, match="notice visibility cannot be verified"):
            validate_preview_pdf(path)
    else:
        assert validate_preview_pdf(path)["first_page_notice"] is True


@pytest.mark.parametrize("sequence", [None, True, -1, 999, 1.5])
def test_unknown_notice_sequence_cannot_certify_overlapping_raster(tmp_path, sequence):
    path = tmp_path / "sequence.pdf"
    fixture(path, "later")
    with fitz.open(path) as document:
        span = document[0].get_texttrace()[0]
        artwork = document[0].get_bboxlog()
        assert not _notice_raster_order_unverifiable(span, artwork[:-1])
        assert _notice_raster_order_unverifiable({**span, "seqno": sequence}, artwork)


@pytest.mark.parametrize("artwork", [[()], [None], [("fill-image",)]])
def test_unsupported_artwork_is_a_controlled_refusal(tmp_path, monkeypatch, artwork):
    path = tmp_path / "unsupported.pdf"
    fixture(path, "later")
    monkeypatch.setattr(fitz.Page, "get_bboxlog", lambda _page: artwork)
    with pytest.raises(ValueError, match="notice visibility cannot be verified"):
        validate_preview_pdf(path)


def test_raster_order_analysis_has_an_event_limit(tmp_path, monkeypatch):
    path = tmp_path / "bounded.pdf"
    fixture(path, "before")
    original = path.read_bytes()
    monkeypatch.setattr(
        fitz.Page, "get_bboxlog", lambda _page: [("fill-image", (1, 1, 2, 2))] * 10_001
    )
    with pytest.raises(ValueError, match="notice visibility cannot be verified"):
        validate_preview_pdf(path)
    assert path.read_bytes() == original


def test_raster_order_policy_is_distinct_from_historical_certificate():
    assert PREVIEW_PRESENTATION == "uk-layout-preview-v2-raster-order"
