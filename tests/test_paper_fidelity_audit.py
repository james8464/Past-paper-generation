from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
import pytest

from tools.paper_fidelity_audit import (
    KNOWN_REFERENCE_MUPDF_DIAGNOSTICS,
    ROLE_WEIGHTS,
    PageEvidence,
    PageRoleMatcher,
    _compact_profile,
    _document_page_roles,
    _font_family,
    _generated_document,
    _geometry_scores,
    _grid_dimensions,
    _metric_callout,
    _reference_peers,
    _registered_page_comparison,
    _render_page_pixmap,
    _role_matches,
    _role_scores,
    classify_page_role,
    profile,
    validate_thresholds,
    write_contact_sheets,
    write_worst_page_sheets,
)


def test_open_metric_compatible_fonts_match_reference_families() -> None:
    assert _font_family("Arimo-Bold") == _font_family("Arial-BoldMT")
    assert _font_family("Tinos-Italic") == _font_family("TimesNewRomanPS-ItalicMT")


def _threshold_report(
    *,
    overall: float = 0.700,
    cover: float = 0.600,
) -> dict:
    document = {
        "comparison": {"overall": overall},
        "role_scores": {"cover": {"overall": cover}},
    }
    return {
        "schema_version": 3,
        "families": {
            "example-family": {
                "question_paper": document,
                "mark_scheme": document,
            }
        },
    }


def _thresholds() -> dict:
    document = {
        "minimum": 0.700,
        "roles": {"cover": 0.600},
    }
    return {
        "schema_version": 1,
        "audit_schema_version": 3,
        "families": {
            "example-family": {
                "question_paper": document,
                "mark_scheme": document,
            }
        },
    }


def test_threshold_gate_reports_missing_family() -> None:
    report = _threshold_report()
    report["families"] = {}

    errors = validate_thresholds(report, _thresholds())

    assert errors == [
        "example-family/question_paper/document: expected >= 0.700; observed missing"
    ]


def test_threshold_gate_rejects_six_tenths_point_document_regression() -> None:
    errors = validate_thresholds(_threshold_report(overall=0.694), _thresholds())

    assert errors == [
        "example-family/question_paper/document: expected >= 0.700; observed 0.694",
        "example-family/mark_scheme/document: expected >= 0.700; observed 0.694",
    ]


def test_threshold_gate_reports_failed_page_role() -> None:
    errors = validate_thresholds(_threshold_report(cover=0.599), _thresholds())

    assert errors == [
        "example-family/question_paper/cover: expected >= 0.600; observed 0.599",
        "example-family/mark_scheme/cover: expected >= 0.600; observed 0.599",
    ]


def test_threshold_gate_accepts_report_at_minimums() -> None:
    assert validate_thresholds(_threshold_report(), _thresholds()) == []


def test_threshold_gate_rejects_unqualified_report_family() -> None:
    thresholds = _thresholds()
    thresholds["families"] = {}

    assert validate_thresholds(_threshold_report(), thresholds) == [
        "example-family/question_paper/document: "
        "expected configured minimum; observed unqualified"
    ]


@pytest.mark.parametrize(
    ("text", "document_role", "page_number", "expected"),
    [
        ("A-level Economics Mark scheme", "mark_scheme", 1, "cover"),
        ("Explain how a tax affects output.", "question_paper", 4, "question_content"),
        ("Question Answer Mark", "mark_scheme", 4, "mark_scheme_content"),
        ("Additional page, if required", "question_paper", 28, "additional_answer"),
        ("EXTRA ANSWER SPACE", "question_paper", 29, "additional_answer"),
        ("Question 6 continued", "question_paper", 14, "ruled_continuation"),
        (
            "Extract F continued " + "economic evidence and analysis " * 30,
            "question_paper",
            4,
            "question_content",
        ),
        (
            "MARKING INSTRUCTIONS CONTINUED",
            "mark_scheme",
            4,
            "mark_scheme_content",
        ),
        (
            (
                "Annotation conventions. Blank page means the annotation used when "
                "there is no candidate response. Correct response, omission mark, "
                "benefit of doubt, error carried forward, repeat, too vague. "
            )
            * 3,
            "mark_scheme",
            6,
            "mark_scheme_content",
        ),
        (
            "BLANK PAGE DO NOT WRITE ON THIS PAGE",
            "question_paper",
            6,
            "intentional_blank",
        ),
        ("END OF QUESTION PAPER", "question_paper", 16, "end_page"),
    ],
)
def test_page_role_classification(
    text: str,
    document_role: str,
    page_number: int,
    expected: str,
) -> None:
    assert (
        classify_page_role(
            text,
            document_role=document_role,
            page_number=page_number,
        )
        == expected
    )


def test_role_scores_aggregate_final_page_measurements() -> None:
    pages = [
        {
            "page": 1,
            "role": "cover",
            "overall": 0.8,
            "registered_masked_render": 0.9,
            "registered_text_layout": 0.7,
            "stable_area": 0.95,
        },
        {
            "page": 2,
            "role": "question_content",
            "overall": 0.6,
            "registered_masked_render": 0.92,
            "registered_text_layout": 0.5,
            "stable_area": 0.4,
        },
        {
            "page": 3,
            "role": "question_content",
            "overall": 0.7,
            "registered_masked_render": 0.94,
            "registered_text_layout": 0.6,
            "stable_area": 0.5,
        },
    ]

    scores = _role_scores(pages)

    assert scores["cover"] == {
        "pages": 1,
        "overall": 0.8,
        "registered_masked_render": 0.9,
        "registered_text_layout": 0.7,
        "stable_area": 0.95,
    }
    assert scores["question_content"]["pages"] == 2
    assert scores["question_content"]["overall"] == 0.65
    assert scores["question_content"]["registered_masked_render"] == 0.93


def test_page_role_matcher_uses_role_before_page_sequence() -> None:
    references = [
        PageEvidence(index=0, role="cover", content_box=(0.1, 0.1, 0.9, 0.9)),
        PageEvidence(
            index=1, role="additional_answer", content_box=(0.1, 0.2, 0.9, 0.8)
        ),
        PageEvidence(
            index=2, role="question_content", content_box=(0.1, 0.15, 0.9, 0.85)
        ),
    ]
    generated = PageEvidence(
        index=1,
        role="question_content",
        content_box=(0.11, 0.15, 0.89, 0.85),
    )

    match = PageRoleMatcher.match(generated, references)

    assert match.reference_index == 2
    assert match.role == "question_content"


def test_role_matching_produces_unique_reference_pairs() -> None:
    generated = [
        PageEvidence(0, "cover", (0.1, 0.1, 0.9, 0.9)),
        PageEvidence(1, "question_content", (0.1, 0.15, 0.9, 0.85)),
        PageEvidence(2, "additional_answer", (0.1, 0.2, 0.9, 0.8)),
    ]
    references = [
        PageEvidence(0, "cover", (0.1, 0.1, 0.9, 0.9)),
        PageEvidence(1, "additional_answer", (0.1, 0.2, 0.9, 0.8)),
        PageEvidence(2, "question_content", (0.1, 0.15, 0.9, 0.85)),
    ]

    matches = _role_matches(generated, references)

    assert [(item.generated_index, item.reference_index) for item in matches] == [
        (0, 0),
        (1, 2),
        (2, 1),
    ]


def test_role_matching_reserves_exact_roles_before_fallback_matching() -> None:
    generated = [
        PageEvidence(0, "ruled_continuation", (0.1, 0.1, 0.9, 0.9)),
        PageEvidence(1, "additional_answer", (0.1, 0.1, 0.9, 0.9)),
    ]
    references = [
        PageEvidence(0, "additional_answer", (0.1, 0.1, 0.9, 0.9)),
        PageEvidence(1, "question_content", (0.1, 0.1, 0.9, 0.9)),
    ]

    matches = _role_matches(generated, references)
    by_generated = {match.generated_index: match for match in matches}

    assert by_generated[1].reference_index == 0
    assert by_generated[0].reference_index == 1


def test_reference_peers_select_same_paper_across_at_least_three_years(
    tmp_path: Path,
) -> None:
    paths = [tmp_path / f"AQA-71271-QP-JUN{year}.PDF" for year in (22, 23, 24, 25)]
    for path in paths:
        path.touch()
    (tmp_path / "AQA-71272-QP-JUN25.PDF").touch()
    (tmp_path / "AQA-71271-MS-JUN25.PDF").touch()

    peers = _reference_peers(paths[-1], maximum=3)

    assert paths[-1] in peers
    assert len(peers) == 3
    assert all("71271-QP" in path.name for path in peers)


def test_structural_grid_dimensions_are_derived_from_page_size_and_dpi() -> None:
    assert _grid_dimensions(width=612, height=792, dpi=12) == (102, 132)


def test_versioned_role_weights_cover_every_semantic_page_role() -> None:
    assert set(ROLE_WEIGHTS) >= {
        "cover",
        "question_content",
        "mark_scheme_content",
        "additional_answer",
        "ruled_continuation",
        "intentional_blank",
        "end_page",
    }
    assert all(
        sum(weights.values()) == pytest.approx(1) for weights in ROLE_WEIGHTS.values()
    )


def test_pdf_role_classifier_recognises_ruled_answer_pages(tmp_path: Path) -> None:
    path = tmp_path / "answer.pdf"
    document = fitz.open()
    cover = document.new_page(width=595, height=842)
    cover.insert_text((50, 50), "Question paper")
    answer = document.new_page(width=595, height=842)
    answer.insert_text((50, 50), "Write your answer below")
    for y in range(100, 760, 28):
        answer.draw_line((50, y), (545, y), width=0.35)
    document.save(path)
    document.close()

    assert _document_page_roles(path, "question_paper")[1] == "ruled_continuation"


def test_pdf_role_classifier_counts_thin_answer_rectangles(tmp_path: Path) -> None:
    path = tmp_path / "boxed-answer-lines.pdf"
    document = fitz.open()
    document.new_page(width=595, height=842).insert_text((50, 50), "Question paper")
    answer = document.new_page(width=595, height=842)
    answer.insert_text((50, 50), "Question 6 Explain your answer using the context.")
    for y in range(100, 760, 28):
        answer.draw_rect(fitz.Rect(50, y, 545, y + 0.2), width=0.2)
    document.save(path)
    document.close()

    assert _document_page_roles(path, "question_paper")[1] == "ruled_continuation"


def test_pdf_role_classifier_counts_extracted_dotted_answer_lines(
    tmp_path: Path,
) -> None:
    path = tmp_path / "dotted-answer-lines.pdf"
    document = fitz.open()
    document.new_page(width=595, height=842).insert_text((50, 50), "Question paper")
    answer = document.new_page(width=595, height=842)
    answer.insert_textbox(
        fitz.Rect(50, 50, 545, 780),
        "Turn over\n" + ("." * 100 + "\n") * 24,
        fontsize=8,
    )
    document.save(path)
    document.close()

    assert _document_page_roles(path, "question_paper")[1] == "ruled_continuation"


def test_pdf_role_classifier_keeps_marked_question_pages_as_content(
    tmp_path: Path,
) -> None:
    path = tmp_path / "marked-question-with-answer-lines.pdf"
    document = fitz.open()
    document.new_page(width=595, height=842).insert_text((50, 50), "Question paper")
    answer = document.new_page(width=595, height=842)
    answer.insert_text(
        (50, 50),
        "1 (b) Examine one likely externality using a diagram. (8)",
    )
    for y in range(100, 760, 28):
        answer.draw_rect(fitz.Rect(50, y, 545, y + 0.2), width=0.2)
    document.save(path)
    document.close()

    assert _document_page_roles(path, "question_paper")[1] == "question_content"


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
    page.insert_text(
        (90, 130), "Question 1  Explain the effect of a change in demand.", fontsize=11
    )
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


def test_compact_profile_omits_raster_geometry() -> None:
    value = {
        "pages": 2,
        "word_count": 40,
        "geometry": [{"render_grid": [0, 255]}],
    }

    assert _compact_profile(value) == {"pages": 2, "word_count": 40}


def test_metric_callout_names_print_resolution_comparison_dimensions() -> None:
    label = _metric_callout(
        {
            "structural_overall": 0.61,
            "perceptual_overall": 0.72,
            "print_overall": 0.83,
            "print_scores": {
                "baseline": 0.74,
                "glyph_bbox": 0.69,
                "rule_count": 0.91,
            },
        }
    )

    assert label == (
        "Structure 61.0% • Perceptual 72.0% • Print 83.0% • "
        "Baseline 74.0% • Glyphs 69.0% • Rules 91.0%"
    )


def test_contact_sheets_make_visual_review_artifacts(tmp_path: Path) -> None:
    generated_path = tmp_path / "generated.pdf"
    reference_path = tmp_path / "reference.pdf"
    for path, x in ((generated_path, 92), (reference_path, 86)):
        document = fitz.open()
        page = document.new_page()
        page.insert_text((x, 130), "Practice question", fontsize=11)
        document.save(path)
        document.close()

    outputs = write_contact_sheets(
        generated_path,
        reference_path,
        tmp_path / "comparison",
        dpi=72,
    )

    assert len(outputs) == 1
    assert outputs[0].suffix == ".png"
    assert outputs[0].stat().st_size > 0


def test_worst_page_sheets_select_reported_page(tmp_path: Path) -> None:
    generated_path = tmp_path / "generated.pdf"
    reference_path = tmp_path / "reference.pdf"
    for path, second_page_x in ((generated_path, 98), (reference_path, 82)):
        document = fitz.open()
        document.new_page().insert_text((90, 130), "Cover", fontsize=11)
        document.new_page().insert_text(
            (second_page_x, 130),
            "Weakest page",
            fontsize=11,
        )
        document.save(path)
        document.close()
    report = {
        "families": {
            "example": {
                role: {
                    "generated_path": str(generated_path),
                    "reference_path": str(reference_path),
                    "worst_pages": [{"page": 2}],
                }
                for role in ("question_paper", "mark_scheme")
            }
        }
    }

    outputs = write_worst_page_sheets(report, tmp_path, dpi=72)

    assert len(outputs) == 1
    assert outputs[0].name == "worst-overview-01-02.png"
    assert outputs[0].stat().st_size > 0


def test_generated_document_falls_back_to_nested_transaction_output(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "backend-subject" / "paper-1"
    nested.mkdir(parents=True)
    expected = nested / "paper-1-question-paper.pdf"
    expected.touch()

    assert (
        _generated_document(
            tmp_path / "canonical-family",
            expected.name,
            search_root=tmp_path,
        )
        == expected
    )


def test_registered_comparison_masks_variable_question_wording() -> None:
    reference = fitz.open()
    reference_page = reference.new_page()
    reference_page.insert_text((72, 70), "A-level Economics", fontsize=16)
    reference_page.insert_text(
        (72, 170),
        "Explain how a tax can affect market output.",
        fontsize=11,
    )
    reference_page.draw_line((72, 220), (520, 220), width=0.8)

    generated = fitz.open()
    generated_page = generated.new_page()
    generated_page.insert_text((76, 74), "A-level Economics", fontsize=16)
    generated_page.insert_text(
        (76, 174),
        "Assess how a subsidy can alter producer incentives.",
        fontsize=11,
    )
    generated_page.draw_line((76, 224), (524, 224), width=0.8)

    comparison = _registered_page_comparison(
        reference_page,
        generated_page,
        dpi=96,
    )

    assert comparison["registered_masked_render"] >= 0.95
    assert comparison["registered_text_layout"] >= 0.90
    assert comparison["stable_area"] < 1
    assert comparison["registration_points"][0] == pytest.approx(-4, abs=2)
    assert comparison["registration_points"][1] == pytest.approx(-4, abs=2)
    reference.close()
    generated.close()
