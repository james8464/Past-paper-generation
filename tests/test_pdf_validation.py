from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
from PIL import Image
from reportlab.pdfgen import canvas

from Backend.Core.pdf_validation import (
    GlyphMetric,
    _normalise_font,
    _validate_typography_profile,
    compare_page_evidence,
    extract_pdf_evidence,
    validate_pdf_for_release,
)


def test_metric_compatible_open_fonts_share_reference_family_identity() -> None:
    assert _normalise_font("Arimo-Bold") == _normalise_font("Arial-BoldMT")
    assert _normalise_font("Tinos-Italic") == _normalise_font(
        "TimesNewRomanPS-ItalicMT"
    )


@pytest.mark.parametrize(
    "name", ["OpenSans-Medium", "OpenSans-SemiBold", "ABCDEF+OpenSansRoman-Medium"]
)
def test_open_sans_weights_and_static_instance_share_family_identity(name):
    assert _normalise_font(name) == "opensans"
    assert _normalise_font("OpenSans-CondensedSemiBold") != "opensans"


def test_measured_profile_accepts_genuine_open_sans_cover_faces():
    result = _validate_typography_profile(
        subject="economics_aqa",
        role="question_paper",
        font_characters=Counter(
            {
                "Arimo-Regular": 10000,
                "OpenSansRoman-Medium": 200,
                "OpenSans-SemiBold": 50,
            }
        ),
        font_sizes=Counter({11.0: 10000, 27.0: 100, 7.0: 50}),
        filename="question-paper.pdf",
    )
    # The stored dominant-eight profile contains Arial only. The two actual
    # generated families are Arial and Open Sans, not three weight aliases.
    assert result["font_family_overlap"] == 0.5
    assert result["uses_standard_pdf_fallback"] is False


def test_open_sans_normalisation_does_not_admit_unrelated_cover_families():
    with pytest.raises(ValueError, match="family overlap"):
        _validate_typography_profile(
            subject="economics_aqa",
            role="question_paper",
            font_characters=Counter(
                {
                    "Arimo-Regular": 10000,
                    "UnrelatedSans-Medium": 200,
                    "UnrelatedSerif-Bold": 50,
                }
            ),
            font_sizes=Counter({11.0: 10000, 27.0: 100, 7.0: 50}),
            filename="question-paper.pdf",
        )


def test_print_evidence_compares_metric_compatible_font_names() -> None:
    scores = compare_page_evidence(
        {"font_names": ["Arimo-Regular", "Arimo-Bold"]},
        {"font_names": ["ArialMT", "Arial-BoldMT"]},
    )

    assert scores["font_identity"] == 1.0


def test_image_only_page_is_not_reported_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "image-only.pdf"
    pdf = canvas.Canvas(str(path), pagesize=(200, 200))
    pdf.setTitle("Image-only release validation")
    image = Image.new("RGB", (200, 200), "white")
    pdf.drawInlineImage(image, 64, 64, width=72, height=72)
    pdf.save()

    result = validate_pdf_for_release(path, subject="business")

    assert result["pages"] == 1
    assert result["minimum_image_dpi"] == 200


def test_standard_pdf_font_is_recorded_as_controlled_ci_fallback() -> None:
    result = _validate_typography_profile(
        subject="economics_aqa",
        role="question_paper",
        font_characters=Counter({"Times-Roman": 120, "Times-Bold": 20}),
        font_sizes=Counter({11.0: 100, 7.0: 40}),
        filename="question-paper.pdf",
    )

    assert result is not None
    assert result["uses_standard_pdf_fallback"] is True
    assert result["font_family_overlap"] == 1.0


def _release_canvas(path: Path) -> canvas.Canvas:
    pdf = canvas.Canvas(str(path), pagesize=(200, 200))
    pdf.setTitle("Release artifact")
    pdf.setAuthor("Paper Creator")
    pdf.setSubject("Independent practice material")
    return pdf


def test_duplicate_text_at_the_same_position_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(40, 150, "Question 1")
    pdf.drawString(40, 150, "Question 1")
    pdf.save()

    with pytest.raises(ValueError, match=r"overlapping text.*page 1"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")


def test_page_with_only_a_folio_is_rejected_as_content_free(tmp_path: Path) -> None:
    path = tmp_path / "folio-only.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(100, 10, "1")
    pdf.save()

    with pytest.raises(ValueError, match="page 1 has too little content"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")


def test_ruled_answer_page_is_not_treated_as_content_free(tmp_path: Path) -> None:
    path = tmp_path / "answer-page.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(20, 180, "Answer")
    for y in range(30, 170, 12):
        pdf.line(20, y, 180, y)
    pdf.save()

    result = validate_pdf_for_release(path, subject="business", role="mark_scheme")

    page = result["layout_metrics"]["pages"][0]
    assert page["characters"] == len("Answer")
    assert page["vector_objects"] >= 10
    assert page["text_occupancy"] > 0
    assert page["overlapping_text_pairs"] == 0


def test_layout_metrics_record_each_page(tmp_path: Path) -> None:
    path = tmp_path / "metrics.pdf"
    pdf = _release_canvas(path)
    pdf.drawString(20, 170, "A complete first page")
    pdf.showPage()
    pdf.drawString(20, 170, "A complete second page")
    pdf.save()

    result = validate_pdf_for_release(path, subject="business", role="mark_scheme")

    metrics = result["layout_metrics"]
    assert len(metrics["pages"]) == 2
    assert metrics["median_text_occupancy"] > 0
    assert metrics["overlapping_text_pairs"] == 0


def test_pdf_evidence_records_unembedded_standard_font_and_glyph_metrics(
    tmp_path: Path,
) -> None:
    path = tmp_path / "font-evidence.pdf"
    pdf = _release_canvas(path)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(20, 170, "A complete examination question")
    pdf.save()

    evidence = extract_pdf_evidence(path)

    assert evidence["fonts"][0]["embedded_name"] == "Helvetica"
    assert evidence["fonts"][0]["embedded"] is False
    glyph = evidence["pages"][0]["glyphs"][0]
    assert glyph["baseline"] == pytest.approx(30.0)
    assert glyph["advance"] > 0
    assert len(glyph["bbox"]) == 4


def test_pdf_evidence_ignores_font_resources_that_never_print_text(
    tmp_path: Path,
) -> None:
    path = tmp_path / "unused-font-resource.pdf"
    pdf = _release_canvas(path)
    pdf.setFont("Times-Roman", 11)
    pdf.drawString(20, 170, "Only the selected serif face is printed")
    pdf.save()

    evidence = extract_pdf_evidence(path)

    assert [item["embedded_name"] for item in evidence["fonts"]] == ["Times-Roman"]


def test_print_evidence_ignores_decorative_bleed_and_fill_only_edges(
    tmp_path: Path,
) -> None:
    path = tmp_path / "decorative-bleed.pdf"
    pdf = _release_canvas(path)
    pdf.setFillColorRGB(0.08, 0.08, 0.08)
    pdf.rect(0, 0, 200, 200, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.drawString(20, 170, "High contrast")
    pdf.save()

    page = extract_pdf_evidence(path, non_printable_margin_mm=5.0)["pages"][0]

    assert page["safe_print"] is True
    assert page["minimum_rule_width"] is None
    assert page["monochrome_minimum_contrast"] >= 4.5


def test_print_evidence_ignores_text_fully_occluded_by_later_artwork(
    tmp_path: Path,
) -> None:
    path = tmp_path / "occluded-text.pdf"
    pdf = _release_canvas(path)
    pdf.setFillColorRGB(0.8, 0.8, 0.8)
    pdf.drawString(20, 170, "Superseded template label")
    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(15, 160, 170, 25, fill=1, stroke=0)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.drawString(20, 140, "Visible release content")
    pdf.save()

    page = extract_pdf_evidence(path)["pages"][0]

    assert page["monochrome_minimum_contrast"] >= 4.5


def test_print_evidence_detects_rule_loss_spacing_and_mark_displacement(
    tmp_path: Path,
) -> None:
    reference_path = tmp_path / "reference.pdf"
    generated_path = tmp_path / "generated.pdf"
    reference = _release_canvas(reference_path)
    reference.drawString(20, 170, "Question 1")
    reference.drawString(170, 170, "[4]")
    for y in (130, 110, 90):
        reference.setLineWidth(0.35)
        reference.line(20, y, 180, y)
    reference.save()
    generated = _release_canvas(generated_path)
    generated.drawString(20, 170, "Question 1")
    generated.drawString(150, 160, "[4]")
    for y in (130, 100):
        generated.setLineWidth(0.1)
        generated.line(20, y, 180, y)
    generated.save()

    comparison = compare_page_evidence(
        extract_pdf_evidence(generated_path)["pages"][0],
        extract_pdf_evidence(reference_path)["pages"][0],
    )

    assert comparison["minimum_rule_width"] < 0.5
    assert comparison["rule_count"] < 1
    assert comparison["answer_line_spacing"] < 1
    assert comparison["mark_box_placement"] < 1


def test_print_evidence_detects_baseline_glyph_and_leading_drift(
    tmp_path: Path,
) -> None:
    reference_path = tmp_path / "reference.pdf"
    generated_path = tmp_path / "generated.pdf"
    reference = _release_canvas(reference_path)
    reference.setFont("Helvetica", 11)
    reference.drawString(20, 170, "First line")
    reference.drawString(20, 155, "Second line")
    reference.save()
    generated = _release_canvas(generated_path)
    generated.setFont("Helvetica", 14)
    generated.drawString(24, 165, "First line")
    generated.drawString(24, 140, "Second line")
    generated.save()

    comparison = compare_page_evidence(
        extract_pdf_evidence(generated_path)["pages"][0],
        extract_pdf_evidence(reference_path)["pages"][0],
    )

    assert comparison["baseline"] < 1
    assert comparison["glyph_bbox"] < 1
    assert comparison["leading"] < 1


def test_print_evidence_reports_reading_order_tags_margin_and_monochrome(
    tmp_path: Path,
) -> None:
    path = tmp_path / "print-policy.pdf"
    pdf = _release_canvas(path)
    pdf.setFillColorRGB(0.85, 0.85, 0.85)
    pdf.drawString(1, 1, "Content clipped by an ordinary printer margin")
    pdf.setFillColorRGB(0, 0, 0)
    pdf.drawString(20, 100, "Earlier logical block")
    pdf.drawString(20, 170, "Later logical block")
    pdf.save()

    evidence = extract_pdf_evidence(path, non_printable_margin_mm=5.0)
    page = evidence["pages"][0]

    assert evidence["tagged"] is False
    assert page["safe_print"] is False
    assert page["reading_order_score"] < 1
    assert page["monochrome_minimum_contrast"] < 4.5


def test_glyph_metric_contract_is_immutable() -> None:
    metric = GlyphMetric(
        font_file=None,
        embedded_name="Helvetica",
        baseline=42.0,
        bbox=(1.0, 2.0, 3.0, 4.0),
        advance=2.0,
        line_height=12.0,
    )

    with pytest.raises(AttributeError):
        metric.baseline = 1.0  # type: ignore[misc]
