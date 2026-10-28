"""Accounting reviewers must receive the same cases as the candidate."""

import json
from pathlib import Path

import pymupdf
import pytest
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.render_pdf import render_question_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import (
    _difficulty_candidate,
    _generation_prompt,
    _independently_validate_candidate,
    _review_prompt,
    _task_source,
    _tasks,
)
from Backend.Core.independent_solver import IndependentSolver
from tests.support.solver_responses import complete_solver_response

SYLLABUS = Path(__file__).resolve().parents[1] / (
    "Resources/accounting/aqa/generator/data/syllabus.json"
)


def paper_and_tasks(seed=270100):
    syllabus = load_syllabus(SYLLABUS)
    paper = build_paper(RULES["paper_1"], syllabus, seed)
    return paper, {
        task.question.number: task
        for task in _tasks(paper, {topic.id: topic for topic in syllabus.topics})
    }


def test_paper_one_does_not_publish_unprinted_generic_section_extracts():
    paper, _ = paper_and_tasks()
    assert all(
        not option.stimulus for section in paper.sections for option in section.options
    )
    # Consuming the former planning draws keeps existing seed-to-case arithmetic.
    statement = paper.sections[1].options[0].questions[0].authoring_context
    assert statement["source_data"]["revenue"] == 9_273_600
    assert statement["adjustment_source_data"]["supplier_invoice"] == 3_568


@pytest.mark.parametrize("number", ["15.3", "16", "17"])
def test_all_model_stages_receive_only_the_printed_owned_case(number):
    _, tasks = paper_and_tasks()
    task = tasks[number]
    source = task.question.authoring_context["candidate_source"]
    expected_title = source.get("business", source.get("label"))
    assert _task_source(task)["title"] == expected_title
    assert expected_title

    writer = _generation_prompt(
        [task], subject="accounting", seed=270100, attempt=1, previous_failure=""
    )
    reviewer = _review_prompt([task], [task.question], subject="accounting")
    demand = json.dumps(_difficulty_candidate(task, task.question).review_content)

    class Client:
        prompt = ""

        def generate_json(self, prompt):
            self.prompt = prompt
            return complete_solver_response(
                {
                    "answer": "The published evidence supports a conditional judgement.",
                    "mark_points": ["Apply the stated circumstances and limitations."],
                }
            )

    client = Client()
    IndependentSolver(client).solve(task.question.model_dump(), [])
    for model_context in (writer, reviewer, demand, client.prompt):
        assert expected_title in model_context
        assert "Extract 1." not in model_context
        assert "customer survey response rate" not in model_context
        assert "Five-year accounting index" not in model_context
    if number == "15.3":
        assert "Bracken Retail" not in client.prompt
        assert task.question.authoring_context["preserve_prompt"] is True
        assert all(name in task.question.prompt for name in ("Alex", "Morgan", "Riley"))
        references = task.question.authoring_context["referenced_question_data"]
        assert set(references) == {"partnership_1", "partnership_2"}
        assert "verified_answers" not in json.dumps(references)


@pytest.mark.parametrize("seed", [270100, 17, 270101])
def test_independent_system_and_shareholder_cases_use_distinct_entities(seed):
    _, tasks = paper_and_tasks(seed)
    trader = tasks["16"].question.authoring_context["candidate_source"]
    company = tasks["17"].question.authoring_context["candidate_source"]
    assert trader["business"] != company["business"]
    assert trader["business_form"] == "sole trader"
    assert company["business_form"] == "company"
    assert company["business"] in tasks["17"].question.prompt


def test_every_system_case_narrative_fact_is_printed_from_the_public_source(tmp_path):
    paper, tasks = paper_and_tasks()
    source = tasks["16"].question.authoring_context["candidate_source"]
    assert "spreadsheets" in source["recordkeeping"]
    assert "continue" in source["decision"]
    target = tmp_path / "question.pdf"
    render_question_paper(paper, target)
    with pymupdf.open(target) as document:
        printed = " ".join(" ".join(page.get_text().split()) for page in document)
    for fact in (source["recordkeeping"], source["decision"]):
        assert " ".join(fact.split()) in printed
    assert (
        tasks["17"].question.authoring_context["candidate_source"]["business"]
        in printed
    )


def test_printed_decision_narratives_follow_their_public_contract(tmp_path):
    paper, tasks = paper_and_tasks()
    system = tasks["16"].question.authoring_context["candidate_source"]
    shareholder = tasks["17"].question.authoring_context["candidate_source"]
    system["recordkeeping"] = (
        "The owner maintains public-source records in a handwritten day book."
    )
    system["decision"] = (
        "The owner must compare the three public-source recordkeeping alternatives."
    )
    shareholder["investment_context"] = (
        "The public-source investor is comparing the stated investment and its uncertainty."
    )
    target = tmp_path / "owned-cases.pdf"
    render_question_paper(paper, target)
    with pymupdf.open(target) as document:
        printed = " ".join(" ".join(page.get_text().split()) for page in document)
    for fact in (
        system["recordkeeping"],
        system["decision"],
        shareholder["investment_context"],
    ):
        assert fact in printed


def test_changed_candidate_case_is_rejected_before_independent_solving():
    _, tasks = paper_and_tasks()
    task = tasks["17"]
    candidate = task.question.model_copy(deep=True)
    candidate.authoring_context["candidate_source"]["business"] = (
        "Unprinted replacement"
    )

    class Client:
        def generate_json(self, _prompt):
            raise AssertionError("altered public case reached the independent solver")

    with pytest.raises(ValueError, match="immutable numeric source contract"):
        _independently_validate_candidate(task, candidate, client=Client())
