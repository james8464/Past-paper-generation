"""Answer fields must leave the printed question and marks visible."""

import pymupdf as fitz
import pytest

from Backend.Core.pdf_validation import validate_pdf_for_release


def form_pdf(path, bounds, *, rotation=0, crop=None, value=""):
    with fitz.open() as document:
        page = document.new_page(width=300, height=400)
        document.set_metadata(
            {"title": "Owned answer field", "author": "Keldin", "subject": "Practice"}
        )
        page.insert_text((30, 40), "Question one: owned form", fontsize=10)
        page.insert_text((30, 80), "Explain the result. [4 marks]", fontsize=10)
        field = fitz.Widget()
        field.field_name = "question_1_a"
        field.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        field.rect = fitz.Rect(bounds)
        field.fill_color = (1, 1, 1)
        field.field_value = value
        page.add_widget(field)
        if crop is not None:
            page.set_cropbox(fitz.Rect(crop))
        page.set_rotation(rotation)
        document.save(path)


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("value", ["", "A candidate's answer"])
def test_answer_field_covering_printed_text_is_rejected_unchanged(
    tmp_path, rotation, value
):
    path = tmp_path / "covered-question.pdf"
    form_pdf(path, (25, 65, 240, 200), rotation=rotation, value=value)
    original = path.read_bytes()
    with pytest.raises(ValueError, match=r"answer field.*printed text"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert path.read_bytes() == original


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("value", ["", "A candidate's answer"])
def test_clear_answer_fields_remain_valid_without_modification(
    tmp_path, rotation, value
):
    path = tmp_path / "clear-question.pdf"
    form_pdf(path, (30, 100, 270, 350), rotation=rotation, value=value)
    original = path.read_bytes()
    assert (
        validate_pdf_for_release(path, subject="business", role="mark_scheme")["pages"]
        == 1
    )
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "bounds",
    [
        (-10, 100, 270, 350),
        (30, 100, 310, 350),
        (30, 100, 270, 410),
        (200, -10, 270, 350),
    ],
)
def test_off_page_answer_fields_are_rejected(tmp_path, bounds):
    path = tmp_path / "off-page-field.pdf"
    form_pdf(path, bounds)
    with pytest.raises(ValueError, match=r"answer field.*page box"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("outside", [False, True])
def test_answer_fields_use_cropbox_coordinates(tmp_path, rotation, outside):
    path = tmp_path / "cropped-field.pdf"
    form_pdf(
        path,
        (30, 100, 290 if outside else 240, 350),
        rotation=rotation,
        crop=(20, 20, 280, 380),
    )
    # After cropping the visible width is 260 points; the wider field extends
    # ten points beyond it only when its original right edge exceeds 280.
    if outside:
        with pytest.raises(ValueError, match=r"answer field.*page box"):
            validate_pdf_for_release(path, subject="business", role="mark_scheme")
    else:
        assert (
            validate_pdf_for_release(path, subject="business", role="mark_scheme")[
                "pages"
            ]
            == 1
        )


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_cropped_rotated_fields_still_refuse_covered_question_text(tmp_path, rotation):
    path = tmp_path / "cropped-covered-question.pdf"
    form_pdf(
        path,
        (25, 65, 240, 200),
        rotation=rotation,
        crop=(20, 20, 280, 380),
        value="A candidate's answer",
    )
    original = path.read_bytes()
    with pytest.raises(ValueError, match=r"answer field.*printed text"):
        validate_pdf_for_release(path, subject="business", role="mark_scheme")
    assert path.read_bytes() == original


@pytest.mark.parametrize("inset, rejected", [(0, False), (0.1, False), (1, True)])
def test_field_border_touching_font_bounds_has_a_small_numeric_allowance(
    tmp_path, inset, rejected
):
    path = tmp_path / "touching-field.pdf"
    form_pdf(path, (30, 100, 270, 350))
    with fitz.open(path) as document:
        page = document[0]
        question = page.search_for("Explain the result. [4 marks]")[0]
        widget = page.first_widget
        widget.rect = fitz.Rect(30, question.y1 - inset, 270, 350)
        widget.update()
        document.saveIncr()
    original = path.read_bytes()
    if rejected:
        with pytest.raises(ValueError, match=r"answer field.*printed text"):
            validate_pdf_for_release(path, subject="business", role="mark_scheme")
    else:
        assert (
            validate_pdf_for_release(path, subject="business", role="mark_scheme")[
                "pages"
            ]
            == 1
        )
    assert path.read_bytes() == original
