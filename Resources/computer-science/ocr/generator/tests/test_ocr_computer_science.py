from __future__ import annotations

import re
from pathlib import Path

import pymupdf as fitz
import pytest
from ocrcsgen.cli import generate_package
from ocrcsgen.configs import PAPER_1_MARKS, PAPER_2_MARKS, RULES
from ocrcsgen.generator import build_paper
from ocrcsgen.render_pdf import MARK_SCHEME_PAGE_PLANS, STYLES, render_question_paper
from ocrcsgen.syllabus import load_syllabus
from pypdf import PdfReader

from Backend.Core.exam_blueprints import validate_generated_paper, validate_rule

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def test_mark_scheme_typography_matches_reference_scale() -> None:
    assert STYLES["scheme_header"].fontSize == 9.5
    assert STYLES["scheme_small"].fontSize == 9.5
    assert STYLES["scheme_small"].leading == 11


def _flatten(values: list[list[int]]) -> list[int]:
    return [mark for group in values for mark in group]


def test_current_mark_sequences_and_rules() -> None:
    assert sum(_flatten(PAPER_1_MARKS)) == 140
    assert sum(_flatten(PAPER_2_MARKS)) == 140
    assert len(_flatten(PAPER_1_MARKS)) == 41
    assert len(_flatten(PAPER_2_MARKS)) == 40
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)


def test_multi_seed_validity_scope_and_uniqueness() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, 123)
        same = build_paper(rule, SYLLABUS, 123)
        different = build_paper(rule, SYLLABUS, 456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()
        topic_ids = {
            question.topic_id
            for section in first.sections
            for option in section.options
            for question in option.questions
        }
        assert topic_ids == rule.allowed_topic_ids


def test_packages_render_current_page_geometry(tmp_path: Path) -> None:
    for paper, expected_pages, expected_scheme_pages in (
        ("1", 28, 36),
        ("2", 32, 27),
    ):
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=tmp_path / paper,
            seed=123,
        )
        assert paths.keys() == {
            "question_paper",
            "mark_scheme",
            "assessment_package",
        }
        reader = PdfReader(paths["question_paper"])
        assert len(reader.pages) == expected_pages
        assert "A Level Computer Science" in (reader.pages[0].extract_text() or "")
        answer_page = reader.pages[-1] if paper == "1" else reader.pages[-3]
        assert "EXTRA ANSWER SPACE" in (answer_page.extract_text() or "")
        if paper == "2":
            assert "EXTRA ANSWER SPACE" not in (
                reader.pages[-1].extract_text() or ""
            )
        if paper == "1":
            assert "Iteration" in (reader.pages[3].extract_text() or "")
            assert "First technology" in (reader.pages[9].extract_text() or "")
        scheme = PdfReader(paths["mark_scheme"])
        assert len(scheme.pages) == expected_scheme_pages
        assert float(scheme.pages[0].mediabox.height) > float(scheme.pages[0].mediabox.width)
        assert float(scheme.pages[1].mediabox.height) > float(scheme.pages[1].mediabox.width)
        assert all(
            float(page.mediabox.width) > float(page.mediabox.height)
            for page in scheme.pages[2:-1]
        )
        assert float(scheme.pages[-1].mediabox.height) > float(scheme.pages[-1].mediabox.width)


def test_extra_answer_page_uses_open_ocr_rule_grammar(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["question_paper"])
    try:
        page = document[-1]
        rules = [
            span
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip().startswith("...")
        ]
        assert len(rules) == 20
        assert any(
            drawing["rect"].width <= 1 and drawing["rect"].height > 490
            for drawing in page.get_drawings()
        )
        assert "write the question numbers clearly" in page.get_text().replace(
            "\n", " "
        )
    finally:
        document.close()


def test_blank_leaf_matches_ocr_heading_and_message_baselines(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["question_paper"])
    try:
        page = document[1]
        assert page.search_for("BLANK PAGE")[0].y0 == pytest.approx(62, abs=3)
        assert page.search_for("PLEASE DO NOT WRITE ON THIS PAGE")[0].y0 == (
            pytest.approx(416, abs=3)
        )
    finally:
        document.close()


def test_paper_two_extra_leaves_use_headed_continuation_and_blank_roles(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["question_paper"])
    try:
        blank = document[10]
        spans = {
            span["text"].strip(): span
            for block in blank.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        }
        assert spans["11"]["size"] == pytest.approx(11, abs=0.1)
        assert spans["11"]["bbox"][1] == pytest.approx(43.3, abs=1)
        assert spans["Turn over"]["size"] == pytest.approx(10, abs=0.1)
        assert spans["Turn over"]["bbox"][1] == pytest.approx(773.7, abs=1)
        assert spans["Turn over"]["bbox"][2] == pytest.approx(530.1, abs=1)
        for text in ("11", "Turn over"):
            box = blank.search_for(text)[0] + (-2, -2, 2, 2)
            pixels = blank.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                colorspace=fitz.csGRAY,
                clip=box,
                alpha=False,
            )
            assert min(pixels.samples) < 100
        counts = []
        for page_index in range(len(document) - 3, len(document)):
            page = document[page_index]
            counts.append(
                len(
                    [
                        span
                        for block in page.get_text("dict")["blocks"]
                        for line in block.get("lines", [])
                        for span in line.get("spans", [])
                        if span.get("text", "").strip().startswith("...")
                    ]
                )
            )
        assert counts == [25, 27, 0]
    finally:
        document.close()


def test_mark_scheme_cover_does_not_inherit_page_chrome(tmp_path: Path) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["mark_scheme"])
    try:
        text = document[0].get_text()
        assert "H446/02 · Mark scheme" not in text
        assert "Page 1" not in text
    finally:
        document.close()


def test_mark_scheme_preserves_measured_guidance_and_annotation_roles(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )
    pages = PdfReader(paths["mark_scheme"]).pages

    assert "continued" in (pages[3].extract_text() or "").casefold()
    page_six = pages[5].extract_text() or ""
    assert "ANNOTATIONS" in page_six
    assert "Correct response" in page_six
    assert "BLANK PAGE" not in page_six


def test_paper_two_ends_before_extra_space_and_has_a_blank_legal_leaf(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="2",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )
    pages = PdfReader(paths["question_paper"]).pages

    assert "END OF QUESTION PAPER" in (pages[28].extract_text() or "")
    assert "EXTRA ANSWER SPACE" in (pages[29].extract_text() or "")
    assert "BLANK PAGE" in (pages[31].extract_text() or "")
    assert "Independent practice material" in (pages[31].extract_text() or "")


def test_mark_scheme_page_plans_cover_every_part() -> None:
    for paper_id, rule in RULES.items():
        planned = {
            (section_index, question_index)
            for page in MARK_SCHEME_PAGE_PLANS[paper_id]
            for section_index, question_index, _segment, _segment_count in page
        }
        expected = {
            (section_index, question_index)
            for section_index, section in enumerate(rule.sections)
            for question_index, _question in enumerate(section.questions)
        }
        assert planned == expected


def test_every_question_has_board_specific_context_and_marking() -> None:
    for rule in RULES.values():
        paper = build_paper(rule, SYLLABUS, 123)
        questions = [
            question
            for section in paper.sections
            for option in section.options
            for question in option.questions
        ]
        assert all("For part" not in question.prompt for question in questions)
        assert all("Independent case" not in question.prompt for question in questions)
        assert all(question.mark_scheme for question in questions)
        assert all(
            not re.search(r"\bcase \d{4}\b", " ".join(question.mark_scheme).casefold())
            for question in questions
        )
        assert all(
            any("Level " in point for point in question.mark_scheme)
            for question in questions
            if question.marks >= 9
        )


def test_programming_items_allow_reviewed_code_literals() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 26080118)
    programming = next(
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.kind == "programming"
    )

    assert programming.authoring_context["allow_additional_numeric_values"] is True
    assert programming.authoring_context["max_prompt_words"] >= len(programming.prompt.split())
    extended = next(
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.number == "3(c)"
    )
    assert extended.authoring_context["allow_additional_numeric_values"] is True


def test_processor_design_item_has_architecture_specific_mark_scheme() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 26080117)
    design = next(
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.kind == "programming" and "processor" in question.prompt.casefold()
    )
    scheme = " ".join(design.mark_scheme).casefold()

    assert "main memory" in scheme
    assert "register" in scheme
    assert "address bus" in scheme
    assert "data bus" in scheme
    assert "control bus" in scheme
    assert "sequence, selection and iteration" not in scheme
    assert "case 9320" not in scheme


def test_low_mark_state_items_keep_verified_wording_and_key() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 26080118)
    state_items = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.command_word.casefold() == "state" and question.marks <= 2
    ]

    assert state_items
    assert all(
        question.authoring_context.get("preserve_prompt") is True
        and question.authoring_context.get("preserve_mark_scheme") is True
        for question in state_items
    )


def test_calculation_enrichment_always_contains_explicit_method_guidance() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 26080117)
    calculations = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.kind == "calculation"
    ]

    assert calculations
    assert all(
        question.authoring_context.get("preserve_prompt") is True
        and question.authoring_context.get("preserve_mark_scheme") is True
        for question in calculations
    )
    assert all(
        any(
            token in " ".join(question.mark_scheme).casefold()
            for token in ("working", "method", "substitution")
        )
        for question in calculations
        if question.marks >= 3
    )


def test_boolean_calculation_parts_are_distinct_and_topic_aligned() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 26080117)
    group = paper.sections[4].options[0].questions
    calculations = [question for question in group if question.kind == "calculation"]

    assert [question.marks for question in calculations] == [1, 1, 2]
    assert len({question.prompt for question in calculations}) == 3
    assert all(
        any(operator in question.prompt for operator in (" OR ", " AND ", " XOR "))
        for question in calculations
    )


def test_data_representation_calculations_are_distinct_and_spec_aligned() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 26080117)
    calculations = [
        question
        for question in paper.sections[3].options[0].questions
        if question.kind == "calculation"
    ]
    prompts = " ".join(question.prompt for question in calculations).casefold()

    assert [question.marks for question in calculations] == [1, 2, 3, 4, 2]
    assert len({question.prompt for question in calculations}) == len(calculations)
    assert "hexadecimal" in prompts
    assert "bitmap" in prompts
    assert "mono sound" in prompts
    assert "overflow" in prompts
    assert "normalised floating-point" in prompts


def test_fetch_decode_execute_questions_apply_distinct_case_evidence() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 26080117)
    questions = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if "fetch-decode-execute cycle" in question.prompt.casefold()
    ]

    assert len(questions) >= 2
    assert len({question.prompt for question in questions}) == len(questions)
    assert all(
        question.authoring_context.get("preserve_prompt") is True
        and question.authoring_context.get("preserve_mark_scheme") is True
        for question in questions
    )


def test_maximum_length_programming_prompt_preserves_paper_two_page_count(
    tmp_path: Path,
) -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 26080118)
    question = paper.sections[5].options[0].questions[2]
    words = ["Develop", "pseudocode", "that", "finds", "one", "appointment", "by", "its", "identifier,", "validates", "every", "input,", "handles", "a", "missing", "record", "safely,", "and", "labels", "all", "variables", "consistently.", "Include", "selection,", "iteration,", "a", "suitable", "data", "structure,", "and", "brief", "comments", "that", "explain", "the", "important", "design", "decisions", "for", "the", "medical", "appointment", "service", "when", "implemented."]
    assert len(words) == 45
    paper.sections[5].options[0].questions[2] = question.model_copy(
        update={"prompt": " ".join(words)}
    )

    output = tmp_path / "paper.pdf"
    render_question_paper(paper, output)
    document = fitz.open(output)
    try:
        assert len(document) == 32
        assert "Question 7" in document[15].get_text()
    finally:
        document.close()
