from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pymupdf
import pytest
from pastpapergen import render_pdf
from pastpapergen.generator import build_paper_blueprint
from pastpapergen.paper_configs import load_builtin_paper_config
from pastpapergen.syllabus import load_syllabus
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import getAscent
from reportlab.pdfgen.canvas import Canvas


def _crosses_top_frame(span, top):
    left, glyph_top, right, glyph_bottom = span["bbox"]
    return (
        span["text"].strip(". ")
        and right > 60
        and left < 535
        and glyph_bottom > top - 20
        and glyph_top < top + 3
    )


def test_top_frame_check_includes_deliberately_wide_prompt():
    stream = BytesIO()
    pdf = Canvas(stream, pagesize=A4)
    pdf.setFont(render_pdf.FONT_REGULAR, render_pdf.BODY_FONT_SIZE_PT)
    pdf.drawString(76, render_pdf.ANSWER_PAGE_START_Y, "Wide prompt " * 15)
    pdf.save()
    with pymupdf.open(stream=stream.getvalue(), filetype="pdf") as document:
        span = document[0].get_text("dict")["blocks"][0]["lines"][0]["spans"][0]
        assert span["bbox"][2] > 535
        top = A4[1] - render_pdf.ANSWER_FRAME_Y - render_pdf.ANSWER_FRAME_H + 0.8
        assert _crosses_top_frame(span, top)


def test_top_frame_body_check_keeps_blank_rule_origin_separate():
    span = {"text": "." * 276, "bbox": (42.5, 33.1, 550.7, 39.9)}
    assert not _crosses_top_frame(span, 34.7)


def test_paper_three_choice_instruction_stays_inside_content_margins():
    stream = BytesIO()
    pdf = Canvas(stream, pagesize=A4)
    choices = [
        SimpleNamespace(number=f"2({label})", prompt="Evaluate one effect.", marks=25)
        for label in ("d", "e")
    ]
    with patch.object(
        render_pdf,
        "_draw_centred_instruction_line",
        wraps=render_pdf._draw_centred_instruction_line,
    ) as draw_instruction:
        render_pdf._draw_paper_3_choice_header(
            pdf, choices, render_pdf.ANSWER_PAGE_START_Y
        )
    lines = [call.args[3] for call in draw_instruction.call_args_list]
    assert " ".join(lines) == (
        "Indicate which question you are answering by marking a cross in the box "
        "{box}. If you change your mind, put a line through the box {box} and then "
        "indicate your new question with a cross {box}."
    )
    assert sum(line.count(render_pdf.CROSS_BOX_TOKEN) for line in lines) == 3
    pdf.save()
    with pymupdf.open(stream=stream.getvalue(), filetype="pdf") as document:
        assert (
            sum(
                abs(path["rect"].width - 8) < 0.01
                and abs(path["rect"].height - 8) < 0.01
                for path in document[0].get_drawings()
            )
            == 3
        )
        spans = [
            span
            for block in document[0].get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line["spans"]
        ]
        start = next(
            span["origin"][1]
            for span in spans
            if span["text"].startswith("Indicate which question")
        )
        stop = next(
            span["origin"][1]
            for span in spans
            if span["text"] == "Chosen question number:"
        )
        instruction = [span for span in spans if start <= span["origin"][1] < stop]
        assert all(
            span["bbox"][0] >= 76 - 0.01 and span["bbox"][2] <= A4[0] - 76 + 0.01
            for span in instruction
        ), instruction


def test_instruction_wrapper_refuses_one_word_wider_than_the_frame():
    pdf = Canvas(BytesIO(), pagesize=A4)
    with pytest.raises(ValueError, match="Instruction word does not fit"):
        render_pdf._wrap_centred_instruction_lines(pdf, "W" * 80, 100)


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2", "paper_3"])
def test_all_first_content_lines_clear_answer_frame(tmp_path, paper_id):
    assert (
        Path(render_pdf.__file__).resolve().parent.parent == Path(__file__).parents[1]
    )
    syllabus = load_syllabus(Path(__file__).parents[1] / "data/syllabus_seed.json")
    blueprint = build_paper_blueprint(
        load_builtin_paper_config(paper_id), syllabus, seed=42
    )
    output = tmp_path / f"{paper_id}.pdf"
    render_pdf.render_question_paper(blueprint, output)

    collisions = []
    expected_pages, affected_rule_counts = {
        "paper_1": (32, {19: 24, 22: 24, 27: 21}),
        "paper_2": (36, {5: 21, 17: 24, 23: 24, 26: 24, 31: 21}),
        "paper_3": (36, {6: 24, 7: 24, 9: 24, 12: 16, 22: 24, 23: 24, 25: 24, 28: 15}),
    }[paper_id]
    with pymupdf.open(output) as document:
        assert len(document) == expected_pages
        for page_number, page in enumerate(document, start=1):
            if page_number == 1:
                continue
            frame = next(
                path
                for path in page.get_drawings()
                if abs(path["rect"].width - render_pdf.ANSWER_FRAME_W) < 0.1
                and abs(path["rect"].height - render_pdf.ANSWER_FRAME_H) < 0.1
            )
            top = frame["rect"].y0 + frame["width"] / 2
            spans = [
                span
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line["spans"]
            ]
            rules = [
                span
                for span in spans
                if span["text"].strip() and not span["text"].strip(".")
            ]
            if page_number in affected_rule_counts:
                # One fewer rule is the measured cost of clearing the frame;
                # do not regain it by drawing through the prompt or footer.
                assert (
                    sum(len(rule["text"]) // 276 for rule in rules)
                    == (affected_rule_counts[page_number])
                )
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        left, glyph_top, right, _glyph_bottom = span["bbox"]
                        if _crosses_top_frame(span, top):
                            collisions.append((page_number, span["text"], span["bbox"]))
                        if (
                            span["text"].strip(". ")
                            and right > 60
                            and left < 535
                            and glyph_top < 120
                            and span["size"] >= 8
                        ):
                            assert not any(
                                pymupdf.Rect(span["bbox"]).intersects(
                                    pymupdf.Rect(rule["bbox"])
                                )
                                for rule in rules
                            ), (page_number, span)
    assert not collisions, collisions


@pytest.mark.parametrize("question_number", ["", "6(a)"])
def test_continuation_caption_does_not_move_writing_grid(question_number):
    pdf = Canvas(BytesIO(), pagesize=A4)
    start = render_pdf.ANSWER_PAGE_START_Y
    with (
        patch.object(render_pdf, "_draw_answer_lines_until", return_value=90) as draw,
        patch.object(pdf, "drawString", wraps=pdf.drawString) as draw_text,
    ):
        render_pdf._draw_continuation_lines(pdf, 76, start, question_number)
    assert draw.call_args.args[2] == start - (28 if question_number else 0)
    if question_number:
        caption_y = draw_text.call_args.args[1]
        assert caption_y + getAscent(render_pdf.FONT_ITALIC, 8) <= 805
    else:
        draw_text.assert_not_called()


@pytest.mark.parametrize(
    ("font", "size"),
    [
        (render_pdf.FONT_REGULAR, render_pdf.BODY_FONT_SIZE_PT),
        (render_pdf.FONT_BOLD, render_pdf.BODY_FONT_SIZE_PT),
        (render_pdf.FONT_BOLD, 10),
        (render_pdf.FONT_ITALIC, 8),
    ],
)
def test_content_inset_clears_actual_font_ascent_and_frame_stroke(font, size):
    top = render_pdf.ANSWER_FRAME_Y + render_pdf.ANSWER_FRAME_H
    baseline = render_pdf._answer_content_y(
        render_pdf.ANSWER_PAGE_START_Y + 6, font_size=size
    )
    assert baseline + getAscent(font, size) <= top - 3 - 1.6 / 2


@pytest.mark.parametrize("start", [787.0, 750.0, 600.0])
def test_valid_lower_prompt_baseline_is_not_changed(start):
    pdf = Canvas(BytesIO(), pagesize=A4)
    with patch.object(pdf, "drawString") as draw:
        render_pdf._draw_question_prompt(pdf, "6(a)", "Explain one effect.", 76, start)
    assert all(call.args[1] == start for call in draw.call_args_list)
