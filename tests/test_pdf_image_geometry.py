"""Owned PDF images must not silently lose candidate-visible content."""

import pymupdf as fitz
import pytest

from Backend.Core.pdf_validation import (
    compare_page_evidence,
    extract_pdf_evidence,
    validate_pdf_for_release,
)


def image_pdf(
    path,
    bounds,
    *,
    page_size=(200, 200),
    rotation=0,
    crop=None,
    text=True,
    text_position=(20, 30),
):
    with fitz.open() as document:
        page = document.new_page(width=page_size[0], height=page_size[1])
        document.set_metadata(
            {"title": "Owned image geometry", "author": "Keldin", "subject": "Practice"}
        )
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 600, 600), False)
        image.clear_with(255)
        image.set_rect(fitz.IRect(100, 100, 500, 500), (0, 0, 0))
        page.insert_image(fitz.Rect(bounds), pixmap=image, keep_proportion=False)
        if text:
            page.insert_text(text_position, "Owned image geometry", fontsize=10)
        if crop is not None:
            page.set_cropbox(fitz.Rect(crop))
        page.set_rotation(rotation)
        document.save(path)


def test_partly_off_page_high_resolution_image_is_rejected_without_modification(
    tmp_path,
):
    path = tmp_path / "cropped-owned-image.pdf"
    image_pdf(path, (-20, 50, 80, 150))
    original = path.read_bytes()
    with fitz.open(path) as document:
        info = document[0].get_image_info()[0]
        assert info["bbox"] == pytest.approx((-20, 50, 80, 150))
        assert info["width"] / (100 / 72) == 432
    with pytest.raises(ValueError, match=r"image.*outside.*page"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "bounds", [(20, 50, 180, 150), (0, 50, 200, 150), (-0.0001, 50, 200.0001, 150)]
)
@pytest.mark.parametrize("text", [False, True])
def test_inside_boundary_and_float_noise_images_remain_valid(tmp_path, bounds, text):
    path = tmp_path / "valid-image.pdf"
    image_pdf(path, bounds, text=text)
    original = path.read_bytes()
    assert (
        validate_pdf_for_release(path, subject="business", role="mark_scheme")["pages"]
        == 1
    )
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "bounds",
    [(-20, 50, 80, 150), (120, 50, 220, 150), (50, -20, 150, 80), (50, 120, 150, 220)],
)
@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_non_background_image_outside_any_edge_is_rejected(tmp_path, bounds, rotation):
    path = tmp_path / "outside-image.pdf"
    image_pdf(path, bounds, rotation=rotation)
    original = path.read_bytes()
    with pytest.raises(ValueError, match=r"image.*outside.*page"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert path.read_bytes() == original


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_rotated_rectangular_page_uses_unrotated_content_geometry(tmp_path, rotation):
    path = tmp_path / "rotated-inside.pdf"
    image_pdf(
        path,
        (20, 160, 180, 250),
        page_size=(200, 300),
        rotation=rotation,
        text_position=(20, 275),
    )
    original = path.read_bytes()
    report = validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert report["pages"] == 1
    page = extract_pdf_evidence(path)["pages"][0]
    assert page["page_box"] == pytest.approx((0, 0, 200, 300))
    assert page["safe_print"] is True
    assert path.read_bytes() == original


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("outside", [False, True])
def test_nonzero_cropbox_is_respected_independently_of_mediabox(
    tmp_path, rotation, outside
):
    path = tmp_path / "cropped-page.pdf"
    bounds = (30, 100, 130, 200) if outside else (70, 100, 230, 200)
    image_pdf(
        path,
        bounds,
        page_size=(300, 300),
        crop=(50, 50, 250, 250),
        rotation=rotation,
        text_position=(70, 80),
    )
    original = path.read_bytes()
    if outside:
        with pytest.raises(ValueError, match=r"image.*outside.*page"):
            validate_pdf_for_release(path, subject="business", role="mark_scheme")
    else:
        assert (
            validate_pdf_for_release(path, subject="business", role="mark_scheme")[
                "pages"
            ]
            == 1
        )
        assert extract_pdf_evidence(path)["pages"][0]["safe_print"] is True
    assert path.read_bytes() == original


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("bounds", [(0, 0, 200, 200), (-20, -20, 220, 220)])
def test_existing_full_bleed_background_heuristic_remains_valid(
    tmp_path, rotation, bounds
):
    path = tmp_path / "background.pdf"
    image_pdf(path, bounds, rotation=rotation)
    original = path.read_bytes()
    assert (
        validate_pdf_for_release(path, subject="business", role="mark_scheme")["pages"]
        == 1
    )
    assert extract_pdf_evidence(path)["pages"][0]["safe_print"] is True
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "bounds",
    [
        (float("nan"), 10, 80, 150),
        (0, 10, float("inf"), 150),
        (20, 50, 20, 150),
        (80, 50, 20, 150),
    ],
)
def test_malformed_reported_image_geometry_is_refused(tmp_path, monkeypatch, bounds):
    path = tmp_path / "invalid-image.pdf"
    image_pdf(path, (20, 50, 180, 150))
    original = path.read_bytes()
    real = fitz.Page.get_image_info

    def malformed(page, *args, **kwargs):
        images = real(page, *args, **kwargs)
        return [{**image, "bbox": bounds} for image in images]

    monkeypatch.setattr(fitz.Page, "get_image_info", malformed)
    with pytest.raises(ValueError, match="invalid image geometry"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert path.read_bytes() == original


@pytest.mark.parametrize("dimension", ["width", "height"])
@pytest.mark.parametrize("value", [0, -1, True, float("nan"), float("inf")])
def test_invalid_pixel_dimensions_are_refused_before_dpi(
    tmp_path, monkeypatch, dimension, value
):
    path = tmp_path / "invalid-pixels.pdf"
    image_pdf(path, (20, 50, 180, 150))
    original = path.read_bytes()
    real = fitz.Page.get_image_info

    def malformed(page, *args, **kwargs):
        return [{**image, dimension: value} for image in real(page, *args, **kwargs)]

    monkeypatch.setattr(fitz.Page, "get_image_info", malformed)
    with pytest.raises(ValueError, match="invalid image geometry"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert path.read_bytes() == original


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_background_bleed_is_preserved_on_an_offset_cropbox(tmp_path, rotation):
    path = tmp_path / "cropped-background.pdf"
    image_pdf(
        path,
        (20, 20, 280, 280),
        page_size=(300, 300),
        crop=(50, 50, 250, 250),
        rotation=rotation,
        text_position=(70, 80),
    )
    original = path.read_bytes()
    assert (
        validate_pdf_for_release(path, subject="business", role="mark_scheme")["pages"]
        == 1
    )
    assert extract_pdf_evidence(path)["pages"][0]["safe_print"] is True
    assert path.read_bytes() == original


@pytest.mark.parametrize("crop", [None, (50, 50, 250, 250)])
def test_portrait_print_evidence_matches_prior_page_rect_basis(
    tmp_path, monkeypatch, crop
):
    from Backend.Core import pdf_validation

    path = tmp_path / "portrait-evidence.pdf"
    image_pdf(
        path,
        (70, 100, 230, 200) if crop else (20, 50, 180, 150),
        page_size=(300, 300) if crop else (200, 200),
        crop=crop,
        text_position=(70, 80) if crop else (20, 30),
    )
    current = extract_pdf_evidence(path)
    monkeypatch.setattr(pdf_validation, "_unrotated_page_box", lambda page: page.rect)
    assert extract_pdf_evidence(path) == current


def test_rotated_reference_comparison_and_print_policy_share_coordinate_basis(tmp_path):
    from tools.paper_fidelity_audit import PrintProfile, _print_policy_failures

    source = tmp_path / "source.pdf"
    normal = tmp_path / "normal-marks.pdf"
    rotated = tmp_path / "rotated-marks.pdf"
    image_pdf(
        source, (20, 160, 180, 250), page_size=(200, 300), text_position=(20, 275)
    )
    with fitz.open(source) as document:
        document[0].insert_text((130, 275), "[3 marks]", fontsize=10)
        document.save(normal)
        document[0].set_rotation(90)
        document.save(rotated)
    original = {path: path.read_bytes() for path in (normal, rotated)}
    for path in (normal, rotated):
        assert (
            validate_pdf_for_release(path, subject="business", role="mark_scheme")[
                "pages"
            ]
            == 1
        )
    normal_evidence, rotated_evidence = (
        extract_pdf_evidence(normal),
        extract_pdf_evidence(rotated),
    )
    assert normal_evidence["schema_version"] == rotated_evidence["schema_version"] == 2
    assert normal_evidence["pages"][0]["mark_positions"]
    assert (
        normal_evidence["pages"][0]["mark_positions"]
        == rotated_evidence["pages"][0]["mark_positions"]
    )
    assert all(
        score == 1.0
        for score in compare_page_evidence(
            rotated_evidence["pages"][0], normal_evidence["pages"][0]
        ).values()
    )
    profile = PrintProfile(
        dpi=300,
        scale_percent=100,
        non_printable_margin_mm=4.2,
        monochrome=True,
        minimum_rule_pt=0.2,
        minimum_contrast_ratio=4.5,
        minimum_reading_order_score=0.95,
        require_embedded_fonts=False,
        require_tags=False,
    )
    assert _print_policy_failures(normal_evidence, profile) == []
    assert _print_policy_failures(rotated_evidence, profile) == []
    assert all(path.read_bytes() == data for path, data in original.items())
