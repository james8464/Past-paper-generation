"""Closed Accounting choices are derived from public multi-step cases."""

from copy import deepcopy

import pytest

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _candidate_question,
    _independently_validate_candidate,
)
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.subjects.selected_response import solve_selected_response
from tests.test_shared_numeric_integrity import accounting_tasks


@pytest.mark.parametrize("number", ["06", "07", "08", "09"])
def test_four_paper_one_choices_have_source_owned_multi_step_contracts(number):
    task = next(
        task
        for task in accounting_tasks("paper_1", 270100)
        if task.question.number == number
    )
    question = task.question
    context = question.authoring_context
    contract = context["selected_response_contract"]
    assert contract["version"] == "accounting-selected-response-v1"
    assert context["preserve_prompt"] is True
    assert context["source_data"] == contract["inputs"]
    public_item = question.model_dump(mode="json")
    # Neither a private key nor a worked scheme is needed by the arithmetic route.
    public_item.pop("correct_choice")
    public_item.pop("mark_scheme")
    public_item.pop("structured_mark_scheme")
    solved = solve_selected_response(public_item)
    assert solved["answer"] == question.choices[question.correct_choice]
    assert len(solved["steps"]) >= 2
    canonical = IndependentSolver().solve(public_item, [])
    assert canonical.solution_source == "deterministic-candidate-inputs"
    assert canonical.answer == solved["answer"]


@pytest.mark.parametrize("number", ["06", "07", "08", "09"])
def test_writer_cannot_replace_accounting_source_choices_or_key(number):
    task = next(
        task
        for task in accounting_tasks("paper_1", 270100)
        if task.question.number == number
    )
    original = task.question

    class Client:
        provider = "test"
        model = "fixture"

    candidate = _candidate_question(
        task,
        {"prompt": original.prompt, "choices": ["forged"] * 4, "correct_choice": 3},
        client=Client(),
        policy=GenerationPolicy(),
    )
    assert candidate.prompt == original.prompt
    assert candidate.choices == original.choices
    assert candidate.correct_choice == original.correct_choice


PUBLIC_CASES = [
    (
        "carriage_gross_profit",
        "GBP",
        {
            "revenue": "240000",
            "opening_inventory": "18000",
            "purchases": "146000",
            "purchase_returns": "4000",
            "carriage_inwards": "3000",
            "carriage_outwards": "5000",
            "closing_inventory": "22000",
        },
        ["£99,000", "£102,000", "£94,000", "£95,000"],
        "£99,000",
    ),
    (
        "sale_or_return_gross_profit",
        "GBP",
        {
            "revenue": "240000",
            "opening_inventory": "18000",
            "purchases": "146000",
            "closing_inventory_excluding_return": "22000",
            "sale_or_return_selling_price": "12000",
            "markup_percent_on_cost": "20",
        },
        ["£98,000", "£96,000", "£86,000", "£108,000"],
        "£96,000",
    ),
    (
        "credit_sale_correction",
        "entry_pair",
        {"credit_sale": "7500"},
        [
            "Debit cash £7,500; credit trade receivables £7,500",
            "Debit trade receivables £7,500; credit cash £7,500",
            "Debit trade receivables £7,500; credit sales £7,500",
            "Debit sales £7,500; credit trade receivables £7,500",
        ],
        "Debit trade receivables £7,500; credit cash £7,500",
    ),
    (
        "net_share_premium",
        "GBP",
        {
            "shares_issued": "80000",
            "nominal_value_pence": "50",
            "issue_price_pence": "175",
            "issue_costs": "2500",
        },
        ["£100,000", "£97,500", "£137,500", "£40,000"],
        "£97,500",
    ),
]


def item_for(case):
    operation, unit, inputs, choices, _ = case
    return {
        "kind": "multiple_choice",
        "marks": 1,
        "subject": "accounting_aqa",
        "choices": list(choices),
        "authoring_context": {
            "selected_response_contract": {
                "version": "accounting-selected-response-v1",
                "subject": "accounting",
                "operation": operation,
                "inputs": dict(inputs),
                "unit": unit,
            }
        },
    }


@pytest.mark.parametrize("case", PUBLIC_CASES)
def test_public_fixtures_recompute_without_an_answer_key(case):
    result = solve_selected_response(item_for(case))
    assert result["answer"] == case[-1]
    assert result["mark_points"] == [case[-1]]


@pytest.mark.parametrize(
    "mutation",
    [
        "bool",
        "nonfinite",
        "extra_input",
        "missing_input",
        "wrong_unit",
        "extra_field",
        "wrong_subject",
        "unknown_operation",
        "duplicate_choice",
        "missing_answer",
    ],
)
def test_invalid_public_contracts_fail_closed(mutation):
    item = item_for(PUBLIC_CASES[0])
    contract = item["authoring_context"]["selected_response_contract"]
    if mutation == "bool":
        contract["inputs"]["revenue"] = True
    elif mutation == "nonfinite":
        contract["inputs"]["revenue"] = "NaN"
    elif mutation == "extra_input":
        contract["inputs"]["private_answer"] = "99000"
    elif mutation == "missing_input":
        del contract["inputs"]["revenue"]
    elif mutation == "wrong_unit":
        contract["unit"] = "GBPm"
    elif mutation == "extra_field":
        contract["answer"] = "£99,000"
    elif mutation == "wrong_subject":
        item["subject"] = "economics_aqa"
    elif mutation == "unknown_operation":
        contract["operation"] = "model_answer"
    elif mutation == "duplicate_choice":
        item["choices"][1] = item["choices"][0]
    else:
        item["choices"][0] = "£101,000"
    with pytest.raises(ValueError):
        solve_selected_response(item)


def test_generic_selected_response_contracts_are_not_reclassified_as_accounting():
    item = item_for(PUBLIC_CASES[0])
    item["authoring_context"]["selected_response_contract"] = {
        "version": "selected-response-v1",
        "operation": "index_percentage_increase",
        "inputs": {"base": "100", "rate_percent": "10"},
        "rows": [],
        "unit": "index",
        "decimal_places": 1,
    }
    item["choices"] = ["110.0", "100.0", "90.0", "10.0"]
    assert solve_selected_response(deepcopy(item))["answer"] == "110.0"


@pytest.mark.parametrize("number", ["06", "07", "08", "09"])
def test_public_choice_solver_does_not_consult_private_marking_or_request_a_model(
    number,
):
    task = next(
        task
        for task in accounting_tasks("paper_1", 270100)
        if task.question.number == number
    )
    item = task.question.model_dump(mode="json")
    expected = item["choices"][item["correct_choice"]]
    item["correct_choice"] = (item["correct_choice"] + 1) % 4
    item["mark_scheme"] = ["PRIVATE_MARKING_CANARY"]
    item["structured_mark_scheme"] = []

    class Client:
        def generate_json(self, _prompt):
            raise AssertionError(
                "closed public arithmetic must not request a model answer"
            )

    solution = IndependentSolver(Client()).solve(item, [])
    assert solution.answer == expected
    assert not reconcile_solution(solution, item).passed
    assert "PRIVATE_MARKING_CANARY" not in str(solution.model_dump())


def test_changed_public_choice_contract_is_rejected_before_solving():
    task = next(
        task
        for task in accounting_tasks("paper_1", 270100)
        if task.question.number == "09"
    )
    candidate = task.question.model_copy(deep=True)
    candidate.authoring_context["selected_response_contract"]["operation"] = (
        "carriage_gross_profit"
    )

    class Client:
        def generate_json(self, _prompt):
            raise AssertionError("mutated public operation reached a model")

    with pytest.raises(ValueError, match="immutable numeric source contract"):
        _independently_validate_candidate(task, candidate, client=Client())


def test_choice_construction_varies_without_changing_later_case_arithmetic():
    generated = [
        accounting_tasks("paper_1", seed) for seed in (270100, 270101, 17, 0, -1)
    ]
    for number in ("06", "07", "08", "09"):
        questions = [
            next(task.question for task in tasks if task.question.number == number)
            for tasks in generated
        ]
        assert len({question.prompt for question in questions}) == len(questions)
        for question in questions:
            assert (
                solve_selected_response(question.model_dump(mode="json"))["answer"]
                == question.choices[question.correct_choice]
            )
