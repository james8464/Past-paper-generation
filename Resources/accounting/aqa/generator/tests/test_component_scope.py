# Keep component topics attached to the tasks they actually assess.

import re
from decimal import Decimal
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
    assert (
        sum("What is gross profit?" in question.prompt for question in questions) <= 1
    )
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
            assert question.choices[question.correct_choice] in " ".join(
                question.mark_scheme
            )


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2"])
def test_distinct_calculations_have_correct_keys_and_unique_distractors(paper_id):
    for seed in range(100):
        paper = build_paper(RULES[paper_id], SYLLABUS, seed)
        questions = paper.sections[0].options[0].questions[:10]
        if paper_id == "paper_1":
            # Independent public-input arithmetic, not the production resolver.
            carriage, sale_return, journal, premium = questions[5:9]
            values = [
                {
                    name: Decimal(value)
                    for name, value in question.authoring_context[
                        "selected_response_contract"
                    ]["inputs"].items()
                }
                for question in (carriage, sale_return, journal, premium)
            ]
            c, s, j, p = values
            gross_profit = c["revenue"] - (
                c["opening_inventory"]
                + c["purchases"]
                - c["purchase_returns"]
                + c["carriage_inwards"]
                - c["closing_inventory"]
            )
            restored_cost = s["sale_or_return_selling_price"] / (
                1 + s["markup_percent_on_cost"] / 100
            )
            corrected_profit = (
                s["revenue"]
                - s["sale_or_return_selling_price"]
                - (
                    s["opening_inventory"]
                    + s["purchases"]
                    - s["closing_inventory_excluding_return"]
                    - restored_cost
                )
            )
            net_premium = (
                p["shares_issued"]
                * (p["issue_price_pence"] - p["nominal_value_pence"])
                / 100
                - p["issue_costs"]
            )
            amount = f"£{j['credit_sale']:,.0f}"
            assert journal.choices[journal.correct_choice] == (
                f"Debit trade receivables {amount}; credit cash {amount}"
            )
            assert len(set(journal.choices)) == 4
            expected = [
                (carriage, gross_profit),
                (sale_return, corrected_profit),
                (premium, net_premium),
            ]
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
            assert question.choices[question.correct_choice] == f"£{answer:,.0f}"
            assert len(set(question.choices)) == 4


@pytest.mark.parametrize("paper_id", ["paper_1", "paper_2"])
def test_gross_profit_margin_answer_includes_percentage_scale(paper_id):
    paper = build_paper(RULES[paper_id], SYLLABUS, 270100)
    question = paper.sections[0].options[0].questions[1]
    assert question.choices[question.correct_choice] == "Gross profit ÷ revenue × 100"
