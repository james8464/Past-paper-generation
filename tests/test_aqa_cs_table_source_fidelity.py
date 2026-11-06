"""Owned table-source and review-identity controls, not paper qualification."""

import hashlib
import json
from copy import deepcopy
from io import BytesIO
from unittest.mock import patch

import pytest
from cspapergen import render_pdf
from cspapergen.cli import ADAPTER
from cspapergen.generator import build_paper1_blueprint
from cspapergen.models import Stimulus
from cspapergen.syllabus import load_syllabus
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from Backend.Core import computer_science_authoring as review
from Backend.Core.model_review import ReviewResult

LONG_HEADER = "Current state including whether it is initial or accepting"
LONG_CELL = "Owned complete value with its final qualifier retained"


@pytest.mark.parametrize("kind", ["table", "bitgrid", "packet", "truth_table", "fsm"])
def test_candidate_projection_retains_all_complete_table_strings(kind):
    source = Stimulus(
        kind=kind,
        headers=[LONG_HEADER, "Input"],
        rows=[[LONG_CELL, "1"]],
    )
    before = source.model_dump(mode="json")
    projected = render_pdf.candidate_stimulus_data(source)
    assert projected["headers"] == source.headers
    assert projected["rows"] == source.rows
    assert source.model_dump(mode="json") == before


def test_whole_header_wraps_at_measured_width_without_prefix_loss():
    source = Stimulus(kind="table", headers=[LONG_HEADER, "Input0", "Input1"])
    before = source.model_dump(mode="json")
    pdf = Canvas(BytesIO(), pagesize=render_pdf.AQA_A4)
    with patch.object(pdf, "drawString", wraps=pdf.drawString) as draw:
        bottom = render_pdf._draw_table(pdf, source, 118, 700)
    lines = [call.args[2] for call in draw.call_args_list if call.args[0] == 122]
    assert " ".join(lines) == LONG_HEADER
    assert len(lines) > 1
    assert all(stringWidth(line, render_pdf.FONT_BOLD, 8) <= 130 - 8 for line in lines)
    assert 700 - bottom > 20 + 8
    assert source.model_dump(mode="json") == before


def test_whole_body_cell_wraps_without_changing_its_source_value():
    source = Stimulus(
        kind="table",
        headers=["State", "Input0", "Input1"],
        rows=[[LONG_CELL, "1", "2"]],
    )
    before = source.model_dump(mode="json")
    pdf = Canvas(BytesIO(), pagesize=render_pdf.AQA_A4)
    with patch.object(pdf, "drawString", wraps=pdf.drawString) as draw:
        render_pdf._draw_table(pdf, source, 118, 700)
    lines = [
        call.args[2]
        for call in draw.call_args_list
        if call.args[0] == 122 and call.args[1] <= 666
    ]
    assert " ".join(lines) == LONG_CELL
    assert all(stringWidth(line, render_pdf.FONT, 8) <= 130 - 8 for line in lines)
    assert source.model_dump(mode="json") == before


def test_existing_single_line_table_keeps_its_geometry():
    source = Stimulus(kind="table", headers=["State", "Input"], rows=[["S0", "1"]])
    pdf = Canvas(BytesIO(), pagesize=render_pdf.AQA_A4)
    with (
        patch.object(pdf, "rect", wraps=pdf.rect) as rect,
        patch.object(pdf, "drawString", wraps=pdf.drawString) as text,
    ):
        bottom = render_pdf._draw_table(pdf, source, 118, 700)
    assert bottom == 652
    assert [call.args for call in rect.call_args_list] == [
        (118, 680, 390, 20),
        (118, 680, 195, 20),
        (313, 680, 195, 20),
        (118, 660, 195, 20),
        (313, 660, 195, 20),
    ]
    assert [call.args for call in text.call_args_list] == [
        (122, 686, "State"),
        (317, 686, "Input"),
        (122, 666, "S0"),
        (317, 666, "1"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        Stimulus(kind="table", headers=["W" * 100, "Input"]),
        Stimulus(kind="table", headers=["State", "Input"], rows=[["W" * 100, "1"]]),
        Stimulus(kind="table", headers=["State"], rows=[["value"] for _ in range(80)]),
        Stimulus(kind="table", headers=[], rows=[["unheaded value"]]),
        Stimulus(kind="table", headers=["State"], rows=[["value", "extra value"]]),
    ],
)
def test_unsupported_table_refuses_before_any_ink(source):
    pdf = Canvas(BytesIO(), pagesize=render_pdf.AQA_A4)
    with (
        patch.object(
            pdf, "rect", side_effect=AssertionError("table drew before admission")
        ),
        patch.object(
            pdf, "drawString", side_effect=AssertionError("text drew before admission")
        ),
        pytest.raises(ValueError),
    ):
        render_pdf._draw_table(pdf, source, 118, 700)


@pytest.mark.parametrize("kind", ["table", "fsm"])
def test_table_height_is_reserved_before_drawing_the_stimulus(kind):
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=42)
    source = Stimulus(
        kind=kind,
        title="Owned table",
        headers=["Row", "Input"],
        rows=[[str(index), "value"] for index in range(8)],
    )
    pdf = Canvas(BytesIO(), pagesize=render_pdf.AQA_A4)
    state = render_pdf._QuestionRenderState(2, 200, blueprint)
    result = render_pdf._render_stimulus(pdf, source, state)
    assert result.page == 3
    assert result.y >= render_pdf.BOTTOM


def legacy_review_digest(question):
    """The pre-repair digest deliberately had no candidate-source policy."""
    content = deepcopy(question)
    for field in review.REVIEW_FIELDS:
        content.pop(field, None)
    for part in content["parts"]:
        part.pop("difficulty_evidence", None)
        part.pop("open_credit_review", None)
    sql_version = (
        review.SQL_VALIDATION_VERSION
        if isinstance((content.get("stimulus") or {}).get("sql_contract"), dict)
        else "none"
    )
    return hashlib.sha256(
        json.dumps(
            {
                "credit_policy": review.CREDIT_POLICY_VERSION,
                "sql_validation": sql_version,
                "content": content,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def test_cropped_projection_review_cannot_be_reused_as_a_complete_source_review():
    blueprint, _ = build_paper1_blueprint(load_syllabus(), seed=42)
    question = blueprint.questions[5].model_dump(mode="json")
    question["stimulus"]["headers"][0] = LONG_HEADER
    digest = legacy_review_digest(question)
    stored = deepcopy(question)
    stored.update(
        provenance="reviewed-fixed",
        content_review=ReviewResult(approved=True).model_dump(mode="json"),
        reviewed_content_sha256=digest,
        reviewed_blueprint_sha256=digest,
    )
    with pytest.raises(ValueError, match="stale"):
        review.validate_question_review(stored, question, required=True)


def test_current_cs_checkpoint_identity_moves_past_the_cropped_source_policy():
    assert ADAPTER.prompt_version.startswith("aqa-computer-science-v16-")
