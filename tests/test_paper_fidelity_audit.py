from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
import pytest

from tools.paper_fidelity_audit import (
    KNOWN_REFERENCE_MUPDF_DIAGNOSTICS,
    _compact_profile,
    _generated_document,
    _geometry_scores,
    _registered_page_comparison,
    _role_scores,
    _render_page_pixmap,
    classify_page_role,
    profile,
    write_contact_sheets,
    write_worst_page_sheets,
)


@pytest.mark.parametrize(
    ("text", "document_role", "page_number", "expected"),
    [
        ("A-level Economics Mark scheme", "mark_scheme", 1, "cover"),
        ("Explain how a tax affects output.", "question_paper", 4, "question_content"),
        ("Question Answer Mark", "mark_scheme", 4, "mark_scheme_content"),
        ("Additional page, if required", "question_paper", 28, "additional_answer"),
        ("EXTRA ANSWER SPACE", "question_paper", 29, "additional_answer"),
        ("Question 6 continued", "question_paper", 14, "ruled_continuation"),
        ("BLANK PAGE DO NOT WRITE ON THIS PAGE", "question_paper", 6, "intentional_blank"),
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


def test_compact_profile_omits_raster_geometry() -> None:
    value = {
        "pages": 2,
        "word_count": 40,
        "geometry": [{"render_grid": [0, 255]}],
    }

    assert _compact_profile(value) == {"pages": 2, "word_count": 40}


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
