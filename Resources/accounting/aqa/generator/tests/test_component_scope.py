"""Keep component topics attached to the tasks they actually assess."""

import re
from pathlib import Path

import pytest
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus

SYLLABUS = load_syllabus(Path(__file__).resolve().parents[1] / "data/syllabus.json")


@pytest.mark.parametrize(
    ("paper_id", "numbers"),
    [
        ("paper_1", {*range(1, 9), *range(14, 19)}),
        ("paper_2", {*range(1, 4), *range(8, 14), 17, 18}),
    ],
)
def test_declared_scope_matches_aqa_component(paper_id, numbers):
    assert RULES[paper_id].allowed_topic_ids == {
        f"accounting-{number}" for number in numbers
    }


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2"])
def test_mcqs_do_not_repeat_gross_profit_subtraction(paper_id):
    paper = build_paper(RULES[paper_id], SYLLABUS, 270100)
    questions = paper.sections[0].options[0].questions[:10]
    assert sum("What is gross profit?" in question.prompt for question in questions) <= 1
    for question in questions:
        if "gross profit" in question.prompt.casefold():
            assert question.topic_id in {"accounting-6", "accounting-8"}
        if "discounts future cash flows" in question.prompt:
            assert question.topic_id == "accounting-13"


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2"])
def test_bookkeeping_decision_uses_information_systems_topic(paper_id):
    paper = build_paper(RULES[paper_id], SYLLABUS, 270100)
    question = paper.sections[-1].options[0].questions[0]
    assert question.topic_id == "accounting-1"


def test_unavailable_task_topic_cannot_be_relabelled():
    rule = RULES["paper_1"].model_copy(deep=True)
    rule.allowed_topic_ids.remove("accounting-3")
    with pytest.raises(ValueError, match="topic"):
        build_paper(rule, SYLLABUS, 270100)


@pytest.mark.parametrize(
    ("paper_id", "expected_topics"),
    [
        ("paper_1", [3, 8, 5, 8, 8, 6, 6, 3, 16, 18]),
        ("paper_2", [3, 8, 8, 9, 10, 11, 12, 13, 2, 18]),
    ],
)
def test_component_mcqs_bind_actual_task_topics(paper_id, expected_topics):
    for seed in range(20):
        paper = build_paper(RULES[paper_id], SYLLABUS, seed)
        questions = paper.sections[0].options[0].questions[:10]
        assert [question.topic_id for question in questions] == [
            f"accounting-{number}" for number in expected_topics
        ]
        assert len({question.prompt for question in questions}) == 10
        for question in questions:
            assert len(question.choices) == len(set(question.choices)) == 4
            assert question.correct_choice in range(4)
            assert question.choices[question.correct_choice] in " ".join(question.mark_scheme)


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2"])
def test_distinct_calculations_have_correct_keys_and_unique_distractors(paper_id):
    for seed in range(100):
        paper = build_paper(RULES[paper_id], SYLLABUS, seed)
        questions = paper.sections[0].options[0].questions[:10]
        if paper_id == "paper_1":
            gross_profit, premium = questions[6], questions[8]
            revenue, cost = [
                int(value.replace(",", ""))
                for value in re.findall(r"£([\d,]+)", gross_profit.prompt)
            ]
            shares = int(re.search(r"issues ([\d,]+) ordinary", premium.prompt)[1].replace(",", ""))
            expected = [(gross_profit, revenue - cost), (premium, shares * 2)]
        else:
            budget, contribution = questions[3], questions[4]
            opening, receipts, payments = [
                int(value.replace(",", ""))
                for value in re.findall(r"£([\d,]+)", budget.prompt)
            ]
            price, variable, _fixed = [
                int(value) for value in re.findall(r"£(\d+)", contribution.prompt)
            ]
            expected = [
                (budget, opening + receipts - payments),
                (contribution, price - variable),
            ]
        for question, answer in expected:
            assert question.choices[question.correct_choice] == f"£{answer:,}"
            assert len(set(question.choices)) == 4


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2"])
def test_gross_profit_margin_answer_includes_percentage_scale(paper_id):
    paper = build_paper(RULES[paper_id], SYLLABUS, 270100)
    question = paper.sections[0].options[0].questions[1]
    assert question.choices[question.correct_choice] == "Gross profit ÷ revenue × 100"
