from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import (
    _difficulty_candidate,
    _generation_prompt,
    _independently_validate_candidate,
    _review_prompt,
    _Task,
    _tasks,
)
from Backend.Core.assessment_contracts import AssessmentContract, EvidenceRecord
from Backend.Core.candidate_identity import candidate_review_content
from Backend.Core.exam_blueprints import GeneratedOption, GeneratedQuestion


class CapturedSolverPrompt(Exception):
    pass


class CaptureSolverClient:
    def generate_json(self, prompt):
        raise CapturedSolverPrompt(prompt)


def solver_prompt(task):
    # Stop at the external-model boundary; source projection and blind-key
    # removal both execute normally.
    with pytest.raises(CapturedSolverPrompt) as captured:
        _independently_validate_candidate(
            task, task.question, client=CaptureSolverClient()
        )
    return str(captured.value)


def solver_payload(task):
    return json.loads(solver_prompt(task).split("\n", 1)[1])


def task_with_source(
    *, context=None, prompt="Use the case evidence to assess the employer."
):
    question = GeneratedQuestion(
        rule_id="source-test",
        number="1",
        marks=6,
        kind="extended_response",
        command_word="assess",
        topic_id="accounting",
        prompt=prompt,
        mark_scheme=["Credit a supported judgement."],
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 2},
        authoring_context=context or {},
    )
    return _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(
            id="case",
            title="Employer",
            questions=[question],
            stimulus=["Extract 1. Revenue is £710000; staff turnover is 19%."],
        ),
        topic=SimpleNamespace(id="accounting", title="Accounting", points=[]),
    )


def model_sources(task):
    writer = _generation_prompt(
        [task],
        subject="Accounting",
        seed=1,
        attempt=1,
        previous_failure="",
    )
    reviewer = _review_prompt([task], [task.question], subject="Accounting")
    return (
        json.loads(writer.split("BLUEPRINT_DATA=", 1)[1])[0]["immutable_source"],
        json.loads(reviewer.split("REVIEW_DATA=", 1)[1])[0]["source"],
        candidate_review_content(_difficulty_candidate(task, task.question))[
            "parent_source"
        ],
    )


def test_accounting_14_2_solver_uses_printed_company_case_not_unprinted_option_extracts():
    syllabus = load_syllabus(
        Path("Resources/accounting/aqa/generator/data/syllabus.json")
    )
    paper = build_paper(RULES["paper_1"], syllabus, 26092840)
    task = next(
        task
        for task in _tasks(paper, {topic.id: topic for topic in syllabus.topics})
        if task.question.number == "14.2"
    )
    assert "Staff turnover is 19%" in task.option.stimulus[1]

    payload = solver_payload(task)
    for source in [payload, *model_sources(task)]:
        text = json.dumps(source)
        assert "19%" not in text
        assert "710000" not in text
        assert "6789600" in text  # Printed revenue needed to recompute profit.
        assert '"supplier_invoice": 3059' in text
        assert '"trade_receivable": 186714' in text
    # The open-response solver receives a code-derived calculation from the
    # public inputs, never the private worked answer or marking points.
    derived = payload["item"]["authoring_context"][
        "independently_derived_context"
    ]
    assert derived["source"] == "deterministic-candidate-inputs"
    assert derived["numeric_results"]["profit_for_year"] == 1_001_495
    assert derived["numeric_results"]["adjusted_marketing_expenses"] == 762_259
    assert derived["numeric_results"]["irrecoverable_debt"] == 168_043
    assert "verified_answers" not in json.dumps(payload)
    assert "observable_mark_points" not in payload["item"]["authoring_context"]
    instructions = payload["item"]["authoring_context"][
        "independent_solver_instructions"
    ]
    assert any("recompute" in instruction.casefold() for instruction in instructions)
    assert any("supplier invoice" in instruction.casefold() for instruction in instructions)
    assert any("irrecoverable debt" in instruction.casefold() for instruction in instructions)
    assert "1,001,495" not in " ".join(instructions)
    assert (
        "Follow every independent_solver_instructions entry" in solver_prompt(task)
    )


def test_self_contained_solver_excludes_contradictory_unrelated_option_data():
    task = task_with_source(
        prompt="Assess whether profit alone establishes financial security."
    )
    payload = solver_payload(task)
    assert payload["sources"] == []
    assert "19%" not in json.dumps(payload)


@pytest.mark.parametrize(
    "context",
    [{}, {"max_prompt_words": 30, "expected_answer_form": "extended_response"}],
)
def test_relevant_case_extract_survives_authoring_metadata_for_every_reviewer(context):
    task = task_with_source(context=context)
    payload = solver_payload(task)
    assert payload["sources"][0]["text"] == task.option.stimulus[0]
    for source in model_sources(task):
        assert "staff turnover is 19%" in json.dumps(source)


@pytest.mark.parametrize(
    "cue", ["extracts", "charts", "figures", "tables", "sources", "appendices", "cases"]
)
def test_plural_source_references_retain_relevant_option_material(cue):
    task = task_with_source(prompt=f"Using the {cue}, assess the firm's performance.")
    assert solver_payload(task)["sources"][0]["text"] == task.option.stimulus[0]
    for source in model_sources(task):
        assert source["stimulus"] == task.option.stimulus


@pytest.mark.parametrize(
    "board,package,paper_id,numbers",
    [
        ("ocr", "ocregen", "paper_2", ["1(a)"]),
        ("aqa", "aqaecongen", "paper_1", ["2", "3", "4", "6", "7", "8"]),
        ("aqa", "aqaecongen", "paper_2", ["2", "3", "4", "6", "7", "8"]),
    ],
)
def test_real_economics_extract_questions_share_all_printed_sources(
    board, package, paper_id, numbers
):
    rules = import_module(f"{package}.configs").RULES
    syllabus = import_module(f"{package}.syllabus").load_syllabus(
        Path(f"Resources/economics/{board}/generator/data/syllabus.json")
    )
    paper = import_module(f"{package}.generator").build_paper(
        rules[paper_id], syllabus, 26092840
    )
    tasks = {
        task.question.number: task
        for task in _tasks(paper, {topic.id: topic for topic in syllabus.topics})
    }
    for number in numbers:
        task = tasks[number]
        assert "extracts" in task.question.prompt.casefold()
        assert len(task.option.stimulus) == (3 if board == "ocr" else 4)
        assert [source["text"] for source in solver_payload(task)["sources"]][
            : len(task.option.stimulus)
        ] == task.option.stimulus
        for source in model_sources(task):
            assert source["stimulus"] == task.option.stimulus


def test_explicit_item_evidence_is_not_replaced_by_same_id_option_material():
    task = task_with_source(context={"candidate_source": {"revenue": 250000}})
    task.question.source_references = ["extract-1"]
    task.question.contract = AssessmentContract(
        item_id="source-test",
        marks=6,
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 2},
        evidence=[
            EvidenceRecord(id="extract-1", text="Printed source: revenue is £250000.")
        ],
        allowed_evidence_ids={"extract-1"},
    )
    payload = solver_payload(task)
    assert len(payload["sources"]) == 1
    assert payload["sources"][0]["id"] == "extract-1"
    assert payload["sources"][0]["text"] == "Printed source: revenue is £250000."
    for source in model_sources(task):
        assert "Printed source: revenue is" in json.dumps(source)
        assert "710000" not in json.dumps(source)


def test_conflicting_explicit_evidence_cannot_replace_printed_option_stimulus():
    task = task_with_source(prompt="Use Extract 1 to assess the firm's performance.")
    task.question.source_references = ["extract-1"]
    task.question.contract = AssessmentContract(
        item_id="source-test",
        marks=6,
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 2},
        evidence=[EvidenceRecord(id="extract-1", text="Revenue is £250000.")],
        allowed_evidence_ids={"extract-1"},
    )
    with pytest.raises(ValueError, match=r"Conflicting.*extract-1"):
        solver_payload(task)
    with pytest.raises(ValueError, match=r"Conflicting.*extract-1"):
        model_sources(task)


def test_relevant_chart_values_reach_blind_solver_not_only_writer():
    task = task_with_source(prompt="Use the chart to assess the change in revenue.")
    task.option.stimulus = []
    task.option.chart_title = "Revenue by year"
    task.option.chart_labels = ["Previous", "Current"]
    task.option.chart_values = [20, 35]
    payload = solver_payload(task)
    assert payload["sources"]
    chart = json.loads(payload["sources"][0]["text"])
    assert chart["chart_labels"] == ["Previous", "Current"]
    assert chart["chart_values"] == [20, 35]


def test_conflicting_explicit_evidence_cannot_replace_printed_chart():
    task = task_with_source(prompt="Use the chart to assess the change in revenue.")
    task.option.stimulus = []
    task.option.chart_labels = ["Previous", "Current"]
    task.option.chart_values = [20, 35]
    task.question.contract = AssessmentContract(
        item_id="source-test",
        marks=6,
        assessment_objectives={"AO1": 2, "AO2": 2, "AO3": 2},
        evidence=[EvidenceRecord(id="case:chart", text="Revenue fell to zero.")],
        allowed_evidence_ids={"case:chart"},
    )
    with pytest.raises(ValueError, match=r"Conflicting.*case:chart"):
        solver_payload(task)


def test_source_projection_does_not_bypass_assessment_contract_validation():
    task = task_with_source(context={"assessment_contract": {"evidence": []}})
    with pytest.raises(ValueError):
        _independently_validate_candidate(
            task, task.question, client=CaptureSolverClient()
        )
