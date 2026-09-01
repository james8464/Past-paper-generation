from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
import pytest
from ocregen.cli import generate_package
from ocregen.configs import RULES
from ocregen.generator import build_paper
from ocregen.render_pdf import STYLES, _compact_indicative_guidance, render_mark_scheme
from ocregen.syllabus import load_syllabus
from pypdf import PdfReader

from Backend.Core.exam_blueprints import (
    resolve_question_rules,
    validate_generated_paper,
    validate_rule,
)
from Backend.Core.render_transaction import render_pdf_atomically

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def test_mark_scheme_body_scale_matches_reference() -> None:
    assert STYLES["small"].fontSize == 10


def test_mark_scheme_explains_question_specific_credit_checks(tmp_path: Path) -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    output = tmp_path / "mark-scheme.pdf"

    render_mark_scheme(paper, output)

    extracted = " ".join(page.extract_text() or "" for page in PdfReader(output).pages)
    text = " ".join(extracted.split())
    assert "command word and required context" in text
    assert "valid method and units" in text
    assert "best-fit level" in text


def test_all_rules_have_exact_candidate_marks() -> None:
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)


def test_paper_one_and_two_current_mark_sequences() -> None:
    expected = {
        "paper_1": [2, 4, 2, 2, 8, 12],
        "paper_2": [2, 1, 3, 4, 8, 12],
    }
    for paper_id, sequence in expected.items():
        rule = RULES[paper_id]
        assert [question.marks for question in rule.sections[0].questions] == sequence
        assert [(section.option_count, section.answer_options, section.option_marks) for section in rule.sections] == [
            (1, 1, 30), (2, 1, 25), (2, 1, 25)
        ]
    paper_one = build_paper(RULES["paper_1"], SYLLABUS, 123)
    assert [
        question.number
        for question in paper_one.sections[0].options[0].questions
    ] == ["1(a)", "1(b)", "1(c)(i)", "1(c)(ii)", "1(d)", "1(e)"]


def test_paper_three_exact_structure() -> None:
    rule = RULES["paper_3"]
    assert rule.sections[0].option_count == 30
    assert [question.marks for question in rule.sections[1].questions] == [2, 3, 15, 3, 2, 15, 2, 8]


def test_multi_seed_validity_and_uniqueness() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, 123)
        same = build_paper(rule, SYLLABUS, 123)
        different = build_paper(rule, SYLLABUS, 456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()


def test_mcq_choices_are_distinct_and_contextual() -> None:
    for seed in (123, 26090101, 26090103):
        paper = build_paper(RULES["paper_3"], SYLLABUS, seed)
        questions = [option.questions[0] for option in paper.sections[0].options]
        assert all(len(set(question.choices)) == 4 for question in questions)
        assert all("estimated costs and benefits by" not in question.prompt for question in questions)
        numeric = [question for index, question in enumerate(questions, start=1) if index % 5 == 0]
        assert numeric
        assert all(
            question.authoring_context["selected_response_contract"]["operation"]
            == "index_percentage_increase"
            for question in numeric
        )


def _candidate_objectives(paper_id: str) -> dict[str, int]:
    totals = {f"AO{index}": 0 for index in range(1, 5)}
    rule = RULES[paper_id]
    for section in rule.sections:
        for option_index in range(1, section.answer_options + 1):
            for question in resolve_question_rules(section, option_index):
                for objective, marks in question.assessment_objectives.items():
                    totals[objective] += marks
    return totals


def test_clean_ocr_objective_anchors_follow_actual_tasks() -> None:
    assert _candidate_objectives("paper_1") == {
        "AO1": 18,
        "AO2": 20,
        "AO3": 20,
        "AO4": 22,
    }
    assert _candidate_objectives("paper_2") == {
        "AO1": 18,
        "AO2": 20,
        "AO3": 20,
        "AO4": 22,
    }
    assert _candidate_objectives("paper_3") == {
        "AO1": 24,
        "AO2": 22,
        "AO3": 18,
        "AO4": 16,
    }
    mcq = RULES["paper_3"].sections[0]
    totals = {f"AO{index}": 0 for index in range(1, 5)}
    operations = []
    for option_index in range(1, 31):
        question = resolve_question_rules(mcq, option_index)[0]
        operations.append(question.task_operation)
        for objective, marks in question.assessment_objectives.items():
            totals[objective] += marks
    assert totals == {"AO1": 15, "AO2": 7, "AO3": 8, "AO4": 0}
    assert operations.count("transform") == 6


def test_source_calculation_keeps_verified_figures_and_mark_scheme() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, 123)
    calculation = paper.sections[1].options[0].questions[0]
    source_items = [
        question
        for section in paper.sections
        for option in section.options
        for question in option.questions
        if question.source_references
    ]

    assert calculation.rule_id == "extract_1_calc"
    assert source_items
    assert all(
        question.authoring_context["preserve_prompt"] is True
        and question.authoring_context["preserve_mark_scheme"] is True
        for question in source_items
    )


def test_written_references_match_rendered_figure() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 123)
    prompts = [question.prompt for question in paper.sections[0].options[0].questions]
    assert all("Table 1" not in prompt for prompt in prompts)
    assert any("Figure 1" in prompt for prompt in prompts)


def test_relationship_questions_align_knowledge_and_application_marks() -> None:
    paper = build_paper(RULES["paper_2"], SYLLABUS, 26080120)
    questions = {
        question.number: question
        for section in paper.sections
        for option in section.options
        for question in option.questions
    }

    three_mark = questions["1(c)"]
    awarded_three = [point for point in three_mark.structured_mark_scheme if point.marks]
    assert [point.assessment_objective for point in awarded_three] == [
        "AO1",
        "AO2",
        "AO2",
    ]
    assert "expected relationship" in awarded_three[0].text.casefold()
    assert "130.0" in awarded_three[2].text
    assert "173.1" in awarded_three[2].text
    assert "whether" in awarded_three[2].text.casefold()

    four_mark = questions["1(d)"]
    awarded_four = [point for point in four_mark.structured_mark_scheme if point.marks]
    assert [point.assessment_objective for point in awarded_four] == [
        "AO1",
        "AO2",
        "AO2",
        "AO2",
    ]
    assert all("limits of the comparison" not in point.text.casefold() for point in awarded_four)


def test_all_packages_render_reference_page_geometry(tmp_path: Path) -> None:
    expected_scheme_pages = {"1": 30, "2": 33, "3": 32}
    for paper, expected_pages in (("1", 20), ("2", 20), ("3", 28)):
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
        assert len(PdfReader(paths["question_paper"]).pages) == expected_pages
        cover = PdfReader(paths["question_paper"]).pages[0].extract_text() or ""
        assert "A Level Economics" in cover
        if paper in {"1", "2"}:
            question_pages = PdfReader(paths["question_paper"]).pages
            assert "Figure 2" in (question_pages[2].extract_text() or "")
            if paper == "1":
                assert "Section B starts on the next page" in (
                    question_pages[8].extract_text() or ""
                )
                assert "Section B:" in (
                    question_pages[9].extract_text() or ""
                )
                assert "Section C starts on the next page" in (
                    question_pages[12].extract_text() or ""
                )
                assert "Section C:" in (
                    question_pages[13].extract_text() or ""
                )
                assert "END OF QUESTION PAPER" in (
                    question_pages[16].extract_text() or ""
                )
                assert "EXTRA ANSWER SPACE" in (
                    question_pages[17].extract_text() or ""
                )
            else:
                assert "Section B:" in (
                    question_pages[8].extract_text() or ""
                )
                assert "Section C starts on the next page" in (
                    question_pages[11].extract_text() or ""
                )
                assert "Section C:" in (
                    question_pages[12].extract_text() or ""
                )
                assert "END OF QUESTION PAPER" in (
                    question_pages[15].extract_text() or ""
                )
                assert "EXTRA ANSWER SPACE" in (
                    question_pages[16].extract_text() or ""
                )
                assert "BLANK PAGE" in (question_pages[17].extract_text() or "")
        scheme = PdfReader(paths["mark_scheme"])
        assert len(scheme.pages) == expected_scheme_pages[paper]
        assert scheme.pages[0].mediabox.height > scheme.pages[0].mediabox.width
        assert scheme.pages[2].mediabox.width > scheme.pages[2].mediabox.height
        assert scheme.pages[-1].mediabox.height > scheme.pages[-1].mediabox.width
        assert "continued" in (scheme.pages[3].extract_text() or "").casefold()
        page_six = scheme.pages[5].extract_text() or ""
        assert "ANNOTATION CONVENTIONS" in page_six
        assert "BLANK PAGE" not in page_six


def test_paper_three_finishes_on_the_reference_page_roles(tmp_path: Path) -> None:
    paths = generate_package(
        paper="3",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["question_paper"]).pages
    assert "Section B" in (pages[15].extract_text() or "")
    assert "Fig. 1.1" in (pages[15].extract_text() or "")
    assert all(
        number in (pages[16].extract_text() or "")
        for number in ("31", "32")
    )
    assert "Extract 2" in (pages[19].extract_text() or "")
    assert "Fig. 2.1" in (pages[19].extract_text() or "")
    assert "Question 34" not in (pages[19].extract_text() or "")
    assert "34" in (pages[20].extract_text() or "")
    assert "35" in (pages[20].extract_text() or "")
    assert "36*" in (pages[21].extract_text() or "")
    assert "Question 36 continued" in (pages[22].extract_text() or "")
    assert "Extract 3" in (pages[23].extract_text() or "")
    assert "Fig. 3.1" in (pages[23].extract_text() or "")
    assert "37" in (pages[23].extract_text() or "")
    assert "38" in (pages[24].extract_text() or "")
    assert "END OF QUESTION PAPER" in (pages[24].extract_text() or "")
    assert "EXTRA ANSWER SPACE" in (pages[25].extract_text() or "")
    assert "EXTRA ANSWER SPACE" not in (pages[26].extract_text() or "")
    assert "DO NOT WRITE ON THIS PAGE" in (pages[27].extract_text() or "")

    rendered = fitz.open(paths["question_paper"])
    assert all(
        len(rendered[page_index].get_drawings()) >= 12
        for page_index in (15, 19, 23)
    )


def test_extra_answer_page_uses_open_ocr_rule_grammar(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["question_paper"])
    try:
        page = document[17]
        rules = [
            span
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip().startswith("...")
        ]
        assert len(rules) == 25
        assert any(
            drawing["rect"].width <= 1 and drawing["rect"].height > 490
            for drawing in page.get_drawings()
        )
    finally:
        document.close()


def test_section_transition_blank_matches_ocr_message_baselines(
    tmp_path: Path,
) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["question_paper"])
    try:
        page = document[8]
        assert page.search_for("BLANK PAGE")[0].y0 == pytest.approx(62, abs=3)
        assert page.search_for("DO NOT WRITE ON THIS PAGE")[0].y0 == (
            pytest.approx(397, abs=3)
        )
        assert page.search_for("Section B starts on the next page")[0].y0 == (
            pytest.approx(436, abs=3)
        )
        for text in ("9", "Turn over"):
            box = page.search_for(text)[0] + (-2, -2, 2, 2)
            pixels = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                colorspace=fitz.csGRAY,
                clip=box,
                alpha=False,
            )
            assert min(pixels.samples) < 100
    finally:
        document.close()


def test_unheaded_extra_leaf_uses_continuation_rule_count(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    document = fitz.open(paths["question_paper"])
    try:
        page = document[18]
        rules = [
            span
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
            if span.get("text", "").strip().startswith("...")
        ]
        assert len(rules) == 27
        assert "write the question numbers clearly" not in page.get_text()
    finally:
        document.close()


def test_full_response_leaves_use_reference_dot_text_grammar(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    with fitz.open(paths["question_paper"]) as document:
        for page_index in (10, 11, 14, 15):
            page = document[page_index]
            rules = [
                span
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line.get("spans", [])
                if span.get("text", "").strip().startswith("...")
            ]
            assert len(rules) == 27
            assert all(len(rule["text"]) == 155 for rule in rules)


def test_paper_three_questions_share_bound_extract_and_figure_data() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, 26080100)
    option = paper.sections[1].options[0]

    for question in option.questions:
        context = question.authoring_context
        assert context["extract_text"]
        assert all(
            concept in context["extract_text"]
            for concept in context["bound_concepts"]
        )
        figure = context["figure"]
        primary = figure["series"][0]["values"]
        assert f"{float(primary[0]):g}" in context["extract_text"]
        assert f"{float(primary[-1]):g}" in context["extract_text"]
        assert f"Extract {figure['number'].split('.')[0]}" in question.source_references


def test_mark_scheme_uses_dense_ocr_tables_and_guidance_pages(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=123,
    )

    pages = PdfReader(paths["mark_scheme"]).pages
    assert "PREPARATION FOR MARKING" in (pages[2].extract_text() or "")
    assert "LEVELS OF RESPONSE" in (pages[9].extract_text() or "")
    question_page = pages[10].extract_text() or ""
    assert all(heading in question_page for heading in ("Question", "Answer", "Mark", "Guidance"))
    assert "Diagram guidance for 1(b)" in question_page
    data_page = pages[11].extract_text() or ""
    assert "x 100 =" in data_page
    assert "index points" in data_page
    assert "Worked calculation" not in data_page
    objectives_page = pages[-2].extract_text() or ""
    assert all(heading in objectives_page for heading in ("AO1", "AO2", "AO3", "AO4", "TOTAL"))

    rendered = fitz.open(paths["mark_scheme"])
    assert len(rendered[10].get_drawings()) >= 30
    diagram_text = rendered[20].get_text().casefold()
    assert "diagram guidance" in diagram_text
    assert "contestability" in diagram_text
    assert "labour" not in diagram_text
    assert len(rendered[20].get_drawings()) >= 20


def test_business_objectives_use_cost_and_revenue_diagrams(tmp_path: Path) -> None:
    paths = generate_package(
        paper="1",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=1,
    )

    diagram_page = PdfReader(paths["mark_scheme"]).pages[20].extract_text() or ""
    assert "Profit maximisation: MC = MR" in diagram_page
    assert "Revenue maximisation: MR = 0" in diagram_page
    assert "Entry increases competitive supply" not in diagram_page


def test_long_short_answer_scheme_terminates_without_losing_points(
    tmp_path: Path,
) -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    section = paper.sections[0]
    option = section.options[0]
    questions = list(option.questions)
    target = questions[2]
    marking_points = [
        f"Overflow evidence point {index:02d}: credit this distinct valid reason."
        for index in range(1, 19)
    ]
    questions[2] = target.model_copy(update={"mark_scheme": marking_points})
    option = option.model_copy(update={"questions": questions})
    section = section.model_copy(update={"options": [option]})
    paper = paper.model_copy(
        update={"sections": [section, *paper.sections[1:]]}
    )
    output = tmp_path / "long-mark-scheme.pdf"

    result = render_pdf_atomically(
        output,
        lambda temporary: render_mark_scheme(paper, temporary),
        role="mark scheme",
        timeout_seconds=5,
    )

    text = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)
    assert result.elapsed_seconds < 5
    assert result.pages == 30
    assert all(point in text for point in marking_points)


def test_compact_guidance_terminates_when_generated_points_are_exhausted() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, 123)
    question = paper.sections[0].options[0].questions[4]
    question = question.model_copy(
        update={"mark_scheme": ["One concise valid indicative point."]}
    )

    flowables = _compact_indicative_guidance(question, 12)

    assert flowables
