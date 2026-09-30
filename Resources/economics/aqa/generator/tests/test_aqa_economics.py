from __future__ import annotations

import random
import re
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pymupdf as fitz
import pytest
from aqaecongen import generator as aqa_generator
from aqaecongen import render_pdf
from aqaecongen.cli import generate_package
from aqaecongen.configs import PAPER3_VISUAL_QUESTION_NUMBERS, RULES
from aqaecongen.generator import build_paper
from aqaecongen.level_policy import level_guidance, level_rows
from aqaecongen.render_pdf import _visible_scheme_points, render_question_paper
from aqaecongen.syllabus import load_syllabus
from aqaecongen.written_tasks import PROFILES
from pypdf import PdfReader
from reportlab.graphics.shapes import Drawing

from Backend.Core.assessment_package import _extract_items
from Backend.Core.assessment_quality import assert_distinct_items
from Backend.Core.exam_blueprints import (
    GeneratedQuestion,
    MarkSchemePoint,
    resolve_question_rules,
    validate_generated_paper,
    validate_rule,
)
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.pdf_validation import extract_pdf_evidence
from Backend.Core.subjects.selected_response import solve_selected_response

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


def test_aqa_economics_level_policy_matches_published_tariff_bands() -> None:
    assert [row.mark_range for row in level_rows(9)] == ["7–9", "4–6", "1–3", "0"]
    assert [row.mark_range for row in level_rows(15)] == [
        "11–15",
        "6–10",
        "1–5",
        "0",
    ]
    assert [row.mark_range for row in level_rows(25)] == [
        "21–25",
        "16–20",
        "11–15",
        "6–10",
        "1–5",
        "0",
    ]

    fifteen_mark_guidance = " ".join(level_guidance(15)).casefold()
    assert "analysis" in fifteen_mark_guidance
    assert "evaluation" not in fifteen_mark_guidance
    assert "judgement" not in fifteen_mark_guidance


def test_generated_written_questions_keep_the_tariff_specific_level_policy() -> None:
    expected_ranges = {
        9: {"7–9", "4–6", "1–3"},
        10: {"8–10", "4–7", "1–3"},
        15: {"11–15", "6–10", "1–5"},
        25: {"21–25", "16–20", "11–15", "6–10", "1–5"},
    }
    for rule in RULES.values():
        paper = build_paper(rule, SYLLABUS, seed=26092842)
        for section in paper.sections:
            for option in section.options:
                for question in option.questions:
                    if question.marks not in expected_ranges:
                        continue
                    assert question.authoring_context["level_policy_id"] == (
                        f"aqa-economics-{question.marks}-mark"
                    )
                    guidance = " ".join(question.mark_scheme)
                    assert expected_ranges[question.marks] <= {
                        row.mark_range for row in level_rows(question.marks)
                    }
                    assert all(
                        mark_range in guidance
                        for mark_range in expected_ranges[question.marks]
                    )
                    if question.marks == 15:
                        assert "evaluation" not in guidance.casefold()
                        assert "judgement" not in guidance.casefold()


def test_written_tasks_are_topic_specific_and_do_not_use_vague_outcome_stems() -> None:
    forbidden = (
        "outcomes associated with",
        "most effective way to improve outcomes",
        "could affect firms, households and wider economic outcomes",
    )
    for paper_id, seed in (("paper_1", 26092842), ("paper_2", 26092843)):
        paper = build_paper(RULES[paper_id], SYLLABUS, seed=seed)
        questions = [
            question
            for section in paper.sections
            for option in section.options
            for question in option.questions
        ]
        combined = " ".join(question.prompt for question in questions).casefold()
        assert all(phrase not in combined for phrase in forbidden)
        for question in questions:
            if question.marks < 4:
                continue
            focus_terms = question.authoring_context.get("task_focus_terms")
            assert isinstance(focus_terms, list) and focus_terms
            assert any(term.casefold() in question.prompt.casefold() for term in focus_terms)
            assert question.authoring_context.get("item_specific_mark_scheme") is True
            scheme = " ".join(question.mark_scheme).casefold()
            assert "demonstrate precise knowledge of" not in scheme
            assert "where it is relevant to the question" not in scheme


def test_distribution_contexts_are_economies_not_unrelated_industries() -> None:
    paper = build_paper(RULES["paper_1"], SYLLABUS, seed=26092842)
    distribution_option = next(
        option
        for section in paper.sections
        for option in section.options
        if option.questions[0].topic_id == "4.1.7"
    )
    combined = " ".join(
        [distribution_option.title, *distribution_option.stimulus]
        + [question.prompt for question in distribution_option.questions]
    ).casefold()
    assert all(industry not in combined for industry in aqa_generator.INDUSTRIES)
    diagram_question = next(
        question
        for question in distribution_option.questions
        if question.kind == "diagram_analysis"
    )
    assert "income inequality" in diagram_question.prompt.casefold()


def test_each_written_source_is_built_around_its_topic_specific_case() -> None:
    for topic in SYLLABUS.topics:
        profile = PROFILES[topic.id]
        extracts = aqa_generator._stimulus(
            topic,
            "Testland",
            1234,
            [100.0, 102.0, 99.0, 104.0, 106.0],
            random.Random(42),
            expanded=False,
            task_profile=profile,
        )
        combined = " ".join(extracts)
        assert profile.source_evidence in combined
        assert profile.data_mechanism in combined
        assert profile.recommendation in combined
        assert "largest participants account" not in combined.casefold()
        assert "explains the observed outcome" not in combined.casefold()


def test_written_diagram_contract_binds_prompt_scheme_and_renderer(monkeypatch) -> None:
    captured: list[dict[str, object]] = []

    def capture(
        topic_id: str,
        number: str,
        visual: dict[str, object] | None = None,
    ) -> Drawing:
        captured.append(dict(visual or {}))
        return Drawing(100, 50)

    monkeypatch.setattr(render_pdf, "_economic_diagram", capture)
    for paper_id, seed in (("paper_1", 26092842), ("paper_2", 26092843)):
        paper = build_paper(RULES[paper_id], SYLLABUS, seed=seed)
        diagrams = [
            question
            for section in paper.sections
            for option in section.options
            for question in option.questions
            if question.kind == "diagram_analysis"
        ]
        assert diagrams
        for question in diagrams:
            contract = question.authoring_context["written_diagram_contract"]
            assert contract["cause"].casefold() in question.prompt.casefold()
            assert contract["effect"].casefold() in " ".join(question.mark_scheme).casefold()
            before = len(captured)
            render_pdf._scheme_question_page(
                question,
                segment=2,
                segment_count=2,
            )
            assert captured[before] == contract


def test_written_diagram_renderer_prints_the_declared_economic_structure() -> None:
    required_by_kind = {
        "ppf_shift": {"PPF1", "PPF2"},
        "lorenz_shift": {"Line of equality", "Lorenz 1", "Lorenz 2"},
        "externality": {"MSC", "MPC", "MSB", "Qm", "Q*"},
        "market_shift": {"E1", "E2"},
        "labour_market_shift": {"DL1", "DL2", "SL", "E1", "E2"},
        "aggregate_shift": {"E1", "E2"},
    }
    for topic_id, profile in PROFILES.items():
        contract = profile.diagram_contract
        drawing = render_pdf._economic_diagram(topic_id, "3", contract)
        labels = {
            item.text
            for item in drawing.contents
            if hasattr(item, "text") and isinstance(item.text, str)
        }
        assert contract["x_axis"] in labels
        assert contract["y_axis"] in labels
        assert required_by_kind[contract["visual_kind"]] <= labels


def test_item_specific_schemes_do_not_duplicate_text_as_ao_labels() -> None:
    for rule in RULES.values():
        paper = build_paper(rule, SYLLABUS, seed=26092842)
        for section in paper.sections:
            for option in section.options:
                for question in option.questions:
                    if not question.authoring_context.get("item_specific_mark_scheme"):
                        continue
                    awarded = [
                        point
                        for point in question.structured_mark_scheme
                        if point.marks > 0
                    ]
                    assert len({point.text for point in awarded}) == len(awarded)
                    assert all("[AO" not in point.text for point in awarded)
                    assert {
                        objective: sum(
                            point.marks
                            for point in awarded
                            if point.assessment_objective == objective
                        )
                        for objective in question.assessment_objectives
                    } == question.assessment_objectives
                    assert question.authoring_context["observable_mark_points"] == [
                        point.text for point in awarded
                    ]


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
        assert contract["inputs"]["curve"] in {"D", "S", "AD", "SRAS", "LRAS"}
        assert contract["inputs"]["direction"] in {"left", "right"}
        assert set(context) == {"visual_kind", "selected_response_contract"}
        assert f"{contract['inputs']['curve']} curve".casefold() not in question.prompt.casefold()
        assert f"to the {contract['inputs']['direction']}" not in question.prompt.casefold()

        changed = deepcopy(question.model_dump(mode="json"))
        changed_inputs = changed["authoring_context"]["selected_response_contract"]["inputs"]
        changed_inputs["direction"] = (
            "left" if changed_inputs["direction"] == "right" else "right"
        )
        changed_solution = solve_selected_response(changed)
        assert changed_solution is not None
        assert changed_solution["answer"] != question.choices[question.correct_choice]


def test_paper_three_visual_questions_have_distinct_candidate_visible_stems() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=123)
    visual_questions = [
        option.questions[0]
        for option in paper.sections[0].options
        if int(option.questions[0].number) in PAPER3_VISUAL_QUESTION_NUMBERS
    ]

    assert_distinct_items(
        [
            {"id": question.number, "prompt": question.prompt}
            for question in visual_questions
        ],
        threshold=0.84,
        context="paper three visual MCQs",
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
    assert operations.count("transform") == 6
    assert operations.count("analyse") == 12

    exact_operations = {
        number: resolve_question_rules(mcq, number)[0].task_operation
        for number in (1, 3, 7, 11, 17)
    }
    assert exact_operations == {
        1: "transform",
        3: "transform",
        7: "analyse",
        11: "analyse",
        17: "transform",
    }

    generated = build_paper(RULES["paper_3"], SYLLABUS, seed=26090101)
    exported = {
        int(item["id"].split("@", 1)[0]): item["task_operation"]
        for item in _extract_items(
            generated.model_dump(mode="json"), subject="Economics", paper_number="3"
        )
            if int(item["id"].split("@", 1)[0]) in exact_operations
        }
    assert exported == exact_operations


def test_index_mcqs_have_public_numeric_contract_and_semantically_unique_choices() -> None:
    for seed in (100, 26083134, 26090101):
        paper = build_paper(RULES["paper_3"], SYLLABUS, seed=seed)
        questions = [option.questions[0] for option in paper.sections[0].options]
        numeric = [
            question
            for question in questions
            if question.authoring_context.get("selected_response_contract", {}).get(
                "operation"
            )
            in {
                "index_percentage_increase",
                "index_percentage_decrease",
                "index_percentage_change",
            }
        ]
        assert len(numeric) == 3
        assert {
            question.authoring_context["selected_response_contract"]["operation"]
            for question in numeric
        } == {
            "index_percentage_increase",
            "index_percentage_decrease",
            "index_percentage_change",
        }
        for question in numeric:
            assert len(set(question.choices)) == 4
            operation = question.authoring_context["selected_response_contract"]["operation"]
            if operation == "index_percentage_change":
                assert all(choice.endswith("%") for choice in question.choices)
                malformed = question.model_dump(mode="json")
                malformed["choices"][0] = malformed["choices"][0].removesuffix("%")
                with pytest.raises(ValueError, match="percent units"):
                    solve_selected_response(malformed)
                wrong_unit = question.model_dump(mode="json")
                wrong_unit["authoring_context"]["selected_response_contract"]["unit"] = "index"
                with pytest.raises(ValueError, match="format policy"):
                    solve_selected_response(wrong_unit)


def test_applied_mcqs_project_one_typed_source_into_prompt_key_and_solver() -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26090101)
    questions = {
        int(option.questions[0].number): option.questions[0]
        for option in paper.sections[0].options
    }
    mutations = {
        1: ("secondary_after", "60", "20 units of product Y"),
        3: ("quantity_after", "75", "Total expenditure falls"),
        7: ("poorest_share_after", "10", "Income inequality rises"),
        11: (
            "interest_rate_after",
            "2",
            "Credit-financed consumption and investment strengthen",
        ),
        17: (
            "export_elasticity",
            "0.1",
            "The trade balance is more likely to worsen",
        ),
    }

    for number, (field, value, expected) in mutations.items():
        question = questions[number]
        raw = question.model_dump(mode="json")
        contract = raw["authoring_context"]["selected_response_contract"]
        assert question.source_dependency == "stem"
        assert all(str(source_value) in question.prompt for source_value in contract["inputs"].values())

        source = aqa_generator.APPLIED_SOURCE_BY_NUMBER[number]
        changed_source = source.model_copy(update={field: Decimal(value)})
        projection = aqa_generator.project_applied_mcq(changed_source)
        changed = {
            **raw,
            "prompt": projection.prompt,
            "choices": projection.choices,
            "correct_choice": projection.correct_choice,
            "authoring_context": projection.authoring_context,
        }
        changed_solution = solve_selected_response(changed)
        assert changed_solution is not None
        assert changed_solution["answer"] == expected
        assert projection.choices[projection.correct_choice] == expected
        assert projection.prompt != question.prompt
        assert str(value) in projection.prompt


def test_applied_source_mutation_reaches_rendered_candidate_text_and_key(
    monkeypatch, tmp_path: Path
) -> None:
    source = aqa_generator.APPLIED_SOURCE_BY_NUMBER[1]
    changed = source.model_copy(update={"secondary_after": Decimal("60")})
    monkeypatch.setitem(aqa_generator.APPLIED_SOURCE_BY_NUMBER, 1, changed)

    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26090101)
    question = paper.sections[0].options[0].questions[0]
    assert "falls from 80 to 60 units" in question.prompt
    assert question.choices[question.correct_choice] == "20 units of product Y"
    assert solve_selected_response(question.model_dump(mode="json"))["answer"] == (
        "20 units of product Y"
    )

    output = tmp_path / "mutated-applied-source.pdf"
    render_question_paper(paper, output)
    with fitz.open(output) as document:
        text = " ".join(page.get_text() for page in document)
    assert "falls from 80 to 60 units" in text
    assert "falls from 80 to 68 units" not in text


@pytest.mark.parametrize(
    "primary,secondary",
    [("Product A", "Product B"), ("product X", "product Z"),
     ("product Xylophone", "product Yard"), ("", "")],
)
def test_opportunity_cost_rejects_stem_labels_inconsistent_with_options(
    primary, secondary
):
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26092844)
    item = paper.sections[0].options[0].questions[0].model_dump(mode="json")
    assert solve_selected_response(item)["answer"] == "12 units of product Y"
    item["prompt"] = item["prompt"].replace("product X", primary).replace(
        "product Y", secondary
    )
    with pytest.raises(ValueError, match="product labels"):
        solve_selected_response(item)


def test_opportunity_cost_accepts_case_and_whitespace_variants_of_public_labels():
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26092844)
    item = paper.sections[0].options[0].questions[0].model_dump(mode="json")
    item["prompt"] = item["prompt"].replace("product X", "PRODUCT  X").replace(
        "product Y", "Product\nY"
    )
    assert solve_selected_response(item)["answer"] == "12 units of product Y"


@pytest.mark.parametrize("primary,secondary,error", [
    ("Product A", "Product B", "required source or visual term"),
    ("Product Xylophone", "Product Yard", "product labels"),
])
def test_ai_parser_rejects_product_rename_before_model_review(primary, secondary, error):
    from types import SimpleNamespace

    from Backend.Core.ai_assessment import GenerationPolicy, _candidate_question, _tasks

    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26092844)
    task = _tasks(paper, {topic.id: topic for topic in SYLLABUS.topics})[0]
    raw = {"prompt": (
        f"A production switch increases {primary} output from 20 to 30 units, "
        f"while {secondary} falls from 80 to 68 units. Which option gives the "
        "output forgone for the extra 10 units?"
    )}
    with pytest.raises(ValueError, match=error):
        _candidate_question(
            task, raw, client=SimpleNamespace(provider="test", model="test"),
            policy=GenerationPolicy(),
        )


def test_independent_validation_rejects_product_rename_without_calling_model():
    from Backend.Core.ai_assessment import _independently_validate_candidate, _tasks

    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26092844)
    task = _tasks(paper, {topic.id: topic for topic in SYLLABUS.topics})[0]
    candidate = task.question.model_copy(update={
        "prompt": task.question.prompt.replace("product X", "Product A").replace(
            "product Y", "Product B"
        )
    })
    with pytest.raises(ValueError, match="product labels"):
        _independently_validate_candidate(task, candidate, client=None)


def test_checkpoint_replay_rejects_product_rename():
    from Backend.Core.ai_assessment import _tasks, _validate_checkpoint_item

    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26092844)
    task = _tasks(paper, {topic.id: topic for topic in SYLLABUS.topics})[0]
    _validate_checkpoint_item(task, task.question)
    candidate = task.question.model_copy(update={
        "prompt": task.question.prompt.replace("product X", "Product A").replace(
            "product Y", "Product B"
        )
    })
    with pytest.raises(ValueError, match="product labels"):
        _validate_checkpoint_item(task, candidate)


def test_missing_typed_applied_source_prevents_candidate_artifact(monkeypatch) -> None:
    monkeypatch.delitem(aqa_generator.APPLIED_SOURCE_BY_NUMBER, 1)
    with pytest.raises(ValueError, match="missing applied candidate source"):
        build_paper(RULES["paper_3"], SYLLABUS, seed=26090101)


def test_paper_three_mcq_tariffs_and_long_choices_have_clear_geometry(
    tmp_path: Path,
) -> None:
    paper = build_paper(RULES["paper_3"], SYLLABUS, seed=26090108)
    output = tmp_path / "paper-three-layout.pdf"
    render_question_paper(paper, output)

    with fitz.open(output) as document:
        page_six = document[5]
        blocks = page_six.get_text("blocks")
        note = next(block for block in blocks if "Do not write" in block[4])
        first_tariff = next(block for block in blocks if "[1 mark]" in block[4])
        first_choice = next(block for block in blocks if block[4].startswith("A\n83.2"))
        frame_top = min(
            drawing["rect"].y0
            for drawing in page_six.get_drawings()
            if drawing["rect"].width > 480 and drawing["rect"].height > 600
        )
        assert note[3] <= frame_top - 2
        assert page_six.rect.width - note[2] >= 8 * 72 / 25.4
        assert first_choice[1] - first_tariff[3] >= 18

        words = page_six.get_text("words")
        another = next(word for word in words if word[4] == "another")
        answer_boundary = min(
            drawing["rect"].x0
            for drawing in page_six.get_drawings()
            if drawing["rect"].x0 > 480 and drawing["rect"].height > 80
        )
        assert answer_boundary - another[2] >= 12 * 72 / 25.4

        page_thirty = document[24]
        blocks = page_thirty.get_text("blocks")
        prompt = next(block for block in blocks if "percentage\nchange" in block[4])
        tariff = next(block for block in blocks if "[1 mark]" in block[4])
        choice = next(block for block in blocks if block[4].startswith("A\n5.0%"))
        assert choice[1] - max(prompt[3], tariff[3]) >= 18


def _semantic_mcq_signature(question: GeneratedQuestion) -> tuple[object, ...]:
    contract = question.authoring_context.get("selected_response_contract")
    if contract:
        inputs = contract["inputs"]
        operation = contract["operation"]
        if operation == "economic_shift":
            return (operation, inputs["curve"], inputs["direction"], inputs["scope"])
        return (operation,)
    normalized = re.sub(r"\b(?:19|20)\d{2}\b", "", question.prompt.casefold())
    normalized = re.sub(r"\b\d+(?:\.\d+)?\b", "", normalized)
    return ("prompt", " ".join(normalized.split()))


def test_paper_three_has_no_semantically_repeated_mcq_tasks_across_seeds() -> None:
    for seed in (123, 26090101, 26090102, 26090103):
        paper = build_paper(RULES["paper_3"], SYLLABUS, seed=seed)
        questions = [option.questions[0] for option in paper.sections[0].options]
        signatures = [_semantic_mcq_signature(question) for question in questions]
        assert len(signatures) == len(set(signatures)) == 30


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
        for question in written_questions:
            if question.marks < 9:
                continue
            substantive = [
                point
                for point in question.mark_scheme
                if not point.startswith(("Level ", "Levels-based"))
                and not point.startswith(("Marker check:", "Do not award"))
            ]
            assert len(substantive) >= 4
            assert question.authoring_context.get("observable_mark_points")


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
            assert all(mark_range in levels_page for mark_range in ("7–9", "21–25"))
            assert "Highest" not in levels_page
            essay_levels_page = scheme_pages[14].extract_text() or ""
            assert all(
                mark_range in essay_levels_page
                for mark_range in ("11–15", "21–25")
            )


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
    assert "A justified recommendation on" in scheme_text
