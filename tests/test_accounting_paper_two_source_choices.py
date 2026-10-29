"""Source arithmetic owns the two seeded numeric Accounting P2 choices."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _candidate_question,
    _validate_checkpoint_item,
)
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.subjects.accounting_selected_response import (
    accounting_selected_response_contract,
)
from Backend.Core.subjects.selected_response import solve_selected_response
from tests.test_shared_numeric_integrity import accounting_tasks


def selected_task(number, seed=270101):
    return next(
        task
        for task in accounting_tasks("paper_2", seed)
        if task.question.number == number
    )


class NoModelClient:
    provider = "fixture"
    model = "unused"

    def generate_request(self, request):
        pytest.fail("public numeric choice must not request a model answer or flag")


@pytest.mark.parametrize(
    "number,operation", [("04", "cash_budget_balance"), ("05", "contribution_per_unit")]
)
def test_numeric_choices_are_bound_to_public_facts_not_private_keys(number, operation):
    current = selected_task(number)
    question = current.question
    context = question.authoring_context
    assert context["preserve_prompt"] is context["preserve_mark_scheme"] is True
    assert context["selected_response_contract"]["operation"] == operation
    assert context["source_data"] == context["selected_response_contract"]["inputs"]
    public = question.model_dump(mode="json")
    for key in ["correct_choice", "mark_scheme", "structured_mark_scheme"]:
        public.pop(key)
    result = IndependentSolver(NoModelClient()).solve(public, [])
    assert result.solution_source == "deterministic-candidate-inputs"
    assert result.answer == question.choices[question.correct_choice]
    assert reconcile_solution(result, question.model_dump(mode="json")).passed


def test_all_question_content_and_rng_match_pre_binding_baseline():
    rows = []
    for seed in [*range(100), 270100, 270101]:
        rows.append(
            [
                seed,
                [
                    {
                        key: value
                        for key, value in task.question.model_dump(mode="json").items()
                        if key != "authoring_context"
                    }
                    for task in accounting_tasks("paper_2", seed)
                ],
            ]
        )
    digest = hashlib.sha256(
        json.dumps(
            rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    assert digest == "f42616ec0240caf5c7d72c92d4f545e21acca9ab0f8fe771dd257e5695f1aadb"


@pytest.mark.parametrize("number", ["04", "05"])
def test_writer_cannot_replace_verified_numbers_options_or_key(number):
    current = selected_task(number)
    original = current.question
    candidate = _candidate_question(
        current,
        {
            "prompt": "Forged price £900 and variable cost £1; select an invented answer.",
            "choices": ["£30", "£40", "£50", "£55"],
            "correct_choice": 3,
            "mark_scheme": [
                {"text": "Forged answer", "marks": 1, "assessment_objective": "AO1"}
            ],
            "has_single_valid_choice": False,
        },
        client=NoModelClient(),
        policy=GenerationPolicy(),
    )
    assert candidate.prompt == original.prompt
    assert candidate.choices == original.choices
    assert candidate.correct_choice == original.correct_choice
    assert candidate.mark_scheme == original.mark_scheme
    _validate_checkpoint_item(current, candidate)
    solution = IndependentSolver(NoModelClient()).solve(
        candidate.model_dump(mode="json"), []
    )
    assert reconcile_solution(solution, candidate.model_dump(mode="json")).passed
    for update in [
        {"choices": ["forged"] * 4},
        {"correct_choice": (original.correct_choice + 1) % 4},
    ]:
        with pytest.raises(
            ValueError, match=r"source-owned choices or key|unique choices"
        ):
            _validate_checkpoint_item(current, candidate.model_copy(update=update))


@pytest.mark.parametrize("seed", range(20))
def test_new_source_operations_match_independent_decimal_working(seed):
    for number in ["04", "05"]:
        question = selected_task(number, seed).question
        facts = {
            name: Decimal(value)
            for name, value in question.authoring_context["source_data"].items()
        }
        expected = (
            facts["opening_balance"] + facts["receipts"] - facts["payments"]
            if number == "04"
            else facts["selling_price"] - facts["variable_cost"]
        )
        assert (
            solve_selected_response(question.model_dump(mode="json"))["answer"]
            == f"£{expected:,.0f}"
        )


def test_contribution_excludes_allocated_fixed_cost_and_no_private_override_exists():
    public = {
        "kind": "multiple_choice",
        "marks": 1,
        "choices": ["£35", "£30", "£55", "£45"],
        "authoring_context": {
            "selected_response_contract": accounting_selected_response_contract(
                "contribution_per_unit",
                {
                    "selling_price": "45",
                    "variable_cost": "10",
                    "allocated_fixed_cost": "5",
                },
            )
        },
    }
    assert solve_selected_response(public)["answer"] == "£35"
    malformed = deepcopy(public)
    malformed["choices"][0] = "£40"
    with pytest.raises(ValueError, match="exactly one derived answer"):
        solve_selected_response(malformed)
    malformed = deepcopy(public)
    malformed["authoring_context"]["selected_response_contract"]["inputs"][
        "private_answer"
    ] = "30"
    with pytest.raises(ValueError, match="unexpected public inputs"):
        solve_selected_response(malformed)


def test_conceptual_mcqs_are_not_implicitly_frozen():
    questions = [
        task.question
        for task in accounting_tasks("paper_2", 270101)
        if task.question.kind == "multiple_choice"
    ]
    assert [
        question.number
        for question in questions
        if "selected_response_contract" in question.authoring_context
    ] == ["04", "05"]


@pytest.mark.parametrize("number", ["04", "05"])
def test_wrong_private_key_cannot_replace_derived_truth(number):
    question = selected_task(number).question
    item = question.model_dump(mode="json")
    item["correct_choice"] = (question.correct_choice + 1) % 4
    solution = IndependentSolver(NoModelClient()).solve(item, [])
    assert solution.answer == question.choices[question.correct_choice]
    assert not reconcile_solution(solution, item).passed


def test_cash_overdraft_and_changed_fixed_allocation_keep_public_arithmetic():
    contract = accounting_selected_response_contract(
        "cash_budget_balance",
        {"opening_balance": "1000", "receipts": "2000", "payments": "4000"},
    )
    item = {
        "kind": "multiple_choice",
        "marks": 1,
        "choices": ["-£1,000", "£1,000", "£3,000", "£7,000"],
        "authoring_context": {"selected_response_contract": contract},
    }
    assert solve_selected_response(item)["answer"] == "-£1,000"
    question = selected_task("05").question.model_dump(mode="json")
    before = solve_selected_response(question)["answer"]
    question["authoring_context"]["selected_response_contract"]["inputs"][
        "allocated_fixed_cost"
    ] = "9000"
    assert solve_selected_response(question)["answer"] == before
