from __future__ import annotations

import re
from pathlib import Path

import pymupdf as fitz
import pytest
from aqaecongen import render_pdf
from aqaecongen.cli import generate_package
from aqaecongen.configs import PAPER3_VISUAL_QUESTION_NUMBERS, RULES
from aqaecongen.generator import build_paper
from aqaecongen.render_pdf import _visible_scheme_points
from aqaecongen.syllabus import load_syllabus
from pypdf import PdfReader

from Backend.Core.exam_blueprints import (
    GeneratedQuestion,
    MarkSchemePoint,
    resolve_question_rules,
    validate_generated_paper,
    validate_rule,
)
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.pdf_validation import extract_pdf_evidence

ROOT = Path(__file__).resolve().parents[1]
SYLLABUS = load_syllabus(ROOT / "data" / "syllabus.json")


def test_all_paper_rules_have_exact_candidate_marks_and_syllabus_scope() -> None:
    for rule in RULES.values():
        validate_rule(rule, SYLLABUS.topic_ids)


def test_paper_one_and_two_have_exact_aqa_choice_structure() -> None:
    for paper_id in ("paper_1", "paper_2"):
        rule = RULES[paper_id]
        assert [(s.option_count, s.answer_options, s.option_marks) for s in rule.sections] == [
            (2, 1, 40),
            (3, 1, 40),
        ]
        assert [(q.kind, q.marks, q.command_word) for q in rule.sections[0].questions] == [
            ("calculation", 2, "Calculate"),
            ("data_response", 4, "Explain"),
            ("diagram_analysis", 9, "Explain"),
            ("extended_response", 25, "Discuss"),
        ]
        assert [q.marks for q in rule.sections[1].questions] == [15, 25]


def test_paper_three_has_thirty_mcqs_and_fifty_mark_case_study() -> None:
    rule = RULES["paper_3"]
    assert rule.sections[0].option_count == 30
    assert rule.sections[0].candidate_marks == 30
    assert [(q.kind, q.marks, q.command_word) for q in rule.sections[1].questions] == [
        ("data_interpretation", 10, "Assess"),
        ("essay", 15, "Explain"),
        ("extended_response", 25, "Recommend"),
    ]


def test_paper_three_visual_questions_have_data_bound_diagrams() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
    questions = {
        int(option.questions[0].number): option.questions[0]
        for option in paper.sections[0].options
    }

    for number in PAPER3_VISUAL_QUESTION_NUMBERS:
        question = questions[number]
        context = question.authoring_context
        assert question.source_references == [f"Figure {number}"]
        assert context["visual_kind"] == "economic_shift_diagram"
        assert "correct_effect" not in context
        contract = context["selected_response_contract"]
        assert contract["operation"] == "economic_shift"
        assert contract["inputs"]["curve"] in {"D", "S", "AD", "SRAS"}
        assert contract["inputs"]["direction"] in {"left", "right"}
        assert set(context) == {"visual_kind", "selected_response_contract"}
        assert all(
            term.casefold() in question.prompt.casefold()
            for term in (contract["inputs"]["curve"], contract["inputs"]["direction"])
        )


def test_visual_renderer_consumes_only_the_public_selected_response_contract(monkeypatch) -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
    question = next(
        option.questions[0]
        for option in paper.sections[0].options
        if int(option.questions[0].number) in PAPER3_VISUAL_QUESTION_NUMBERS
    )
    captured: dict[str, object] = {}

    def capture(topic_id: str, number: str, visual: dict[str, object] | None = None):
        captured.update(visual or {})
        return object()

    monkeypatch.setattr(render_pdf, "_economic_diagram", capture)
    render_pdf._mcq_visual(question)
    assert captured == question.authoring_context["selected_response_contract"]["inputs"]


def test_visual_key_is_derived_from_public_shift_not_private_choice() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
    question = next(
        option.questions[0]
        for option in paper.sections[0].options
        if int(option.questions[0].number) in PAPER3_VISUAL_QUESTION_NUMBERS
    )
    raw = question.model_dump(mode="json")
    raw["correct_choice"] = (question.correct_choice + 1) % 4
    solution = IndependentSolver().solve(raw, [])
    assert solution.answer == question.choices[question.correct_choice]
    assert solution.solution_source == "deterministic-candidate-inputs"


def test_generated_validation_rejects_private_key_drift_from_public_contract() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
    question = next(
        option.questions[0]
        for option in paper.sections[0].options
        if option.questions[0].authoring_context.get("selected_response_contract")
    )
    question.correct_choice = (question.correct_choice + 1) % 4
    question.mark_scheme = [
        f"Option {'ABCD'[question.correct_choice]}: {question.choices[question.correct_choice]}."
    ]
    with pytest.raises(ValueError, match="selected-response key"):
        validate_generated_paper(paper, RULES["paper_3"], SYLLABUS.topic_ids)


def _candidate_objectives(paper_id: str) -> dict[str, int]:
    totals = {f"AO{index}": 0 for index in range(1, 5)}
    rule = RULES[paper_id]
    for section in rule.sections:
        for option_index in range(1, section.answer_options + 1):
            for question in resolve_question_rules(section, option_index):
                for objective, marks in question.assessment_objectives.items():
                    totals[objective] += marks
    return totals


def test_actual_tasks_have_explicit_candidate_objective_vectors() -> None:
    assert _candidate_objectives("paper_1") == {
        "AO1": 15,
        "AO2": 22,
        "AO3": 25,
        "AO4": 18,
    }
    assert _candidate_objectives("paper_2") == {
        "AO1": 15,
        "AO2": 22,
        "AO3": 25,
        "AO4": 18,
    }
    assert _candidate_objectives("paper_3") == {
        "AO1": 22,
        "AO2": 24,
        "AO3": 19,
        "AO4": 15,
    }

    mcq = RULES["paper_3"].sections[0]
    mcq_totals = {f"AO{index}": 0 for index in range(1, 5)}
    operations = []
    for option_index in range(1, 31):
        question = resolve_question_rules(mcq, option_index)[0]
        operations.append(question.task_operation)
        for objective, marks in question.assessment_objectives.items():
            mcq_totals[objective] += marks
    assert mcq_totals == {"AO1": 12, "AO2": 14, "AO3": 4, "AO4": 0}
    assert operations.count("transform") == 3
    assert operations.count("analyse") == 15


def test_index_mcqs_have_public_numeric_contract_and_semantically_unique_choices() -> None:
    for seed in (100, 26083134, 26090101):
        paper = build_paper(RULES["paper_3"], SYLLABUS, seed=seed)
        questions = [option.questions[0] for option in paper.sections[0].options]
        numeric = [question for question in questions if question.task_operation == "transform"]
        assert len(numeric) == 3
        for question in numeric:
            contract = question.authoring_context["selected_response_contract"]
            assert contract["operation"] == "index_percentage_increase"
            assert len(set(question.choices)) == 4


def test_each_paper_is_valid_and_seed_changes_content() -> None:
    for rule in RULES.values():
        first = build_paper(rule, SYLLABUS, seed=123)
        same = build_paper(rule, SYLLABUS, seed=123)
        different = build_paper(rule, SYLLABUS, seed=456)
        validate_generated_paper(first, rule, SYLLABUS.topic_ids)
        assert first.model_dump() == same.model_dump()
        assert first.model_dump() != different.model_dump()


def test_verified_examiner_guidance_is_retained_during_ai_authoring() -> None:
    for rule in RULES.values():
        paper = build_paper(rule, SYLLABUS, seed=123)
        written_questions = [
            question
            for section in paper.sections
            for option in section.options
            for question in option.questions
            if question.kind != "multiple_choice"
        ]

        assert written_questions
        assert all(
            question.authoring_context.get("preserve_mark_scheme") is True
            for question in written_questions
        )
        assert all(
            question.authoring_context.get("max_prompt_words")
            == max(12, len(question.prompt.split()) + 2)
            for question in written_questions
        )
        assert all(
            len(question.mark_scheme) >= (18 if question.marks >= 15 else 8)
            for question in written_questions
            if question.marks >= 9
        )


def test_mark_scheme_prints_item_specific_guidance_once_per_question() -> None:
    common = (
        "Marker check: reward a valid alternative route where it demonstrates "
        "the same assessed knowledge or skill."
    )
    specific = (
        "AO3: develop a complete chain from an interest-rate rise through "
        "mortgage costs to household consumption."
    )
    question = GeneratedQuestion(
        rule_id="test",
        number="3",
        marks=4,
        kind="explain",
        command_word="Explain",
        topic_id="monetary-policy",
        prompt="Explain one effect of a rise in interest rates.",
        mark_scheme=["Accurate effect.", common, specific],
        structured_mark_scheme=[
            MarkSchemePoint(text="Accurate effect.", marks=1),
            MarkSchemePoint(text=common, marks=0, credit_type="guidance"),
            MarkSchemePoint(text=specific, marks=0, credit_type="guidance"),
        ],
    )

    assert _visible_scheme_points(question) == ["Accurate effect.", specific]


def test_each_package_renders_readable_pdfs(tmp_path: Path) -> None:
    for paper in ("1", "2", "3"):
        output = tmp_path / paper
        paths = generate_package(
            paper=paper,
            syllabus_path=ROOT / "data" / "syllabus.json",
            output_dir=output,
            seed=123,
        )
        expected = (
            {"question_paper", "source_booklet", "mark_scheme"}
            if paper == "3"
            else {"question_paper", "mark_scheme"}
        )
        expected.add("assessment_package")
        assert paths.keys() == expected
        for path in (value for value in paths.values() if value.suffix == ".pdf"):
            reader = PdfReader(path)
            assert len(reader.pages) >= 2
            cover = reader.pages[0].extract_text() or ""
            assert "A-level" in cover
            assert "economics" in cover.casefold()
        assert len(PdfReader(paths["question_paper"]).pages) == (44 if paper == "3" else 8)
        print_evidence = extract_pdf_evidence(
            paths["question_paper"],
            non_printable_margin_mm=5.0,
        )
        assert all(page["safe_print"] for page in print_evidence["pages"])
        assert len(PdfReader(paths["mark_scheme"]).pages) == (
            11 if paper == "3" else 21
        )
        if paper == "3":
            assert len(PdfReader(paths["source_booklet"]).pages) == 8
            final_page = PdfReader(paths["question_paper"]).pages[-1].extract_text() or ""
            assert "DO NOT WRITE ON THIS PAGE" in final_page
            assert "Independent practice material" in final_page
            blueprint = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
            assert [q.number for q in blueprint.sections[1].options[0].questions] == [
                "31",
                "32",
                "33",
            ]
            mcqs = [
                option.questions[0]
                for option in blueprint.sections[0].options
            ]
            assert len({question.prompt for question in mcqs}) == 30
            assert all("Practice scenario" not in question.prompt for question in mcqs)
        else:
            blueprint = build_paper(RULES[f"paper_{paper}"], SYLLABUS, seed=123)
            question_pages = PdfReader(paths["question_paper"]).pages
            assert "Highest recorded index" in (question_pages[1].extract_text() or "")
            assert "Extract C" in (question_pages[2].extract_text() or "")
            assert "continued" in (question_pages[2].extract_text() or "").casefold()
            assert "source insert" not in (question_pages[2].extract_text() or "")
            final_page = question_pages[7].extract_text() or ""
            assert "There are no questions printed on this page" in final_page
            assert "Independent practice information" in final_page
            assert "DO NOT WRITE ON THIS PAGE" not in final_page
            scheme_pages = PdfReader(paths["mark_scheme"]).pages
            scheme_text = "\n".join(page.extract_text() or "" for page in scheme_pages)
            printed_marks = [
                int(value)
                for value in re.findall(r"\((\d{1,2})\)\s*$", scheme_text, re.MULTILINE)
            ]
            expected_marks = [
                question.marks
                for section in blueprint.sections
                for option in section.options
                for question in option.questions
            ]
            assert printed_marks == expected_marks
            scheme_page = scheme_pages[4].extract_text() or ""
            assert all(label in scheme_page for label in ("Question", "Answer", "Mark"))
            with fitz.open(paths["mark_scheme"]) as scheme_document:
                body_sizes = [
                    round(float(span["size"]), 1)
                    for block in scheme_document[4].get_text("dict")["blocks"]
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                    if len(str(span.get("text", "")).strip()) >= 4
                ]
            assert max(set(body_sizes), key=body_sizes.count) >= 11
            levels_page = scheme_pages[3].extract_text() or ""
            assert "Levels of response" in levels_page
            assert "Highest" in levels_page


def test_paper_three_mark_scheme_fits_long_reference_guidance(tmp_path: Path) -> None:
    paths = generate_package(
        paper="3",
        syllabus_path=ROOT / "data" / "syllabus.json",
        output_dir=tmp_path,
        seed=26083024,
    )

    mark_scheme = PdfReader(paths["mark_scheme"])
    scheme_text = "\n".join(page.extract_text() or "" for page in mark_scheme.pages)

    assert len(mark_scheme.pages) == 11
    assert scheme_text.count("Marker check:") <= 1
    assert "A justified recommendation that follows" in scheme_text
