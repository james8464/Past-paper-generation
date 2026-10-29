# Open-response repairs must use public case facts, never the private marking key.

from copy import deepcopy

import pytest

from Backend.Core.ai_assessment import _independently_validate_candidate
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.subjects.accounting import derive_accounting_open_response_context
from tests.support.solver_responses import complete_solver_response
from tests.test_shared_numeric_integrity import accounting_tasks


def company_item():
    item = next(
        task.question.model_dump()
        for task in accounting_tasks("paper_1", 270100)
        if task.question.number == "14.2"
    )
    item["mark_scheme"] = ["PRIVATE_MARKING_CANARY"]
    item["authoring_context"]["verified_answers"] = ["PRIVATE_ANSWER_CANARY"]
    derived = derive_accounting_open_response_context(item)
    assert derived["numeric_results"]["profit_for_year"] == 1_701_298
    required = {
        "profit_for_year": derived["numeric_results"]["profit_for_year"],
        "irrecoverable_debt": derived["numeric_results"]["irrecoverable_debt"],
        "supplier_invoice": item["authoring_context"]["referenced_question_data"][
            "company_statement"
        ]["adjustment_source_data"]["supplier_invoice"],
    }
    return item, required


def response(values):
    facts = [f"{role}: £{value:,.0f}" for role, value in values.items()]
    return complete_solver_response(
        {
            "answer": "These figures inform employee pay and job-security judgements. "
            + "; ".join(facts),
            "steps": facts,
            "mark_points": ["Profit is not evidence of available cash."],
        }
    )


@pytest.mark.parametrize(
    "missing", ["profit_for_year", "irrecoverable_debt", "supplier_invoice"]
)
def test_missing_public_numeric_evidence_gets_one_blind_solver_repair(missing):
    item, required = company_item()

    class Client:
        def __init__(self):
            self.prompts = []

        def generate_json(self, prompt):
            self.prompts.append(prompt)
            values = (
                required
                if len(self.prompts) == 2
                else {key: value for key, value in required.items() if key != missing}
            )
            return response(values)

    client = Client()
    original = deepcopy(item)
    solution = IndependentSolver(client).solve(item, [])
    assert len(client.prompts) == 2
    assert "PUBLIC_NUMERIC_EVIDENCE_FINDINGS" in client.prompts[1]
    assert missing in client.prompts[1]
    assert all("PRIVATE_MARKING_CANARY" not in prompt for prompt in client.prompts)
    assert all("PRIVATE_ANSWER_CANARY" not in prompt for prompt in client.prompts)
    assert item == original
    assert solution.solution_source == "independent-model"
    assert solution.verified_scope == "semantic-review-only"
    assert "1,701,298" in solution.answer


def test_repeated_omission_fails_closed_after_two_solver_calls():
    item, _ = company_item()

    class Client:
        calls = 0

        def generate_json(self, prompt):
            self.calls += 1
            return response({})

    client = Client()
    with pytest.raises(GenerationEvidenceError, match="numeric evidence") as failure:
        IndependentSolver(client).solve(item, [])
    assert client.calls == 2
    assert len(failure.value.details["attempts"]) == 2
    assert set(failure.value.details["attempts"][0]["missing_roles"]) == {
        "profit_for_year",
        "irrecoverable_debt",
        "supplier_invoice",
    }
    assert "PRIVATE_MARKING_CANARY" not in str(failure.value.details)


def test_incorrect_figure_does_not_count_as_the_required_profit():
    item, required = company_item()

    class Client:
        def generate_json(self, prompt):
            return response(
                {**required, "profit_for_year": required["profit_for_year"] + 1}
            )

    with pytest.raises(GenerationEvidenceError, match="numeric evidence"):
        IndependentSolver(Client()).solve(item, [])


def test_numbers_hidden_only_in_mark_points_do_not_complete_the_reviewed_answer():
    item, required = company_item()

    class Client:
        def generate_json(self, prompt):
            result = response({})
            result["mark_points"] = response(required)["steps"]
            return result

    with pytest.raises(ValueError, match="numeric evidence"):
        IndependentSolver(Client()).solve(item, [])


def test_complete_public_numeric_working_does_not_trigger_a_repair():
    item, required = company_item()

    class Client:
        calls = 0

        def generate_json(self, prompt):
            self.calls += 1
            return response(required)

    client = Client()
    IndependentSolver(client).solve(item, [])
    assert client.calls == 1


@pytest.mark.parametrize(
    "field", ["referenced_question_data", "independent_solver_instructions"]
)
def test_writer_cannot_replace_the_public_inputs_or_solver_instructions(field):
    task = next(
        task
        for task in accounting_tasks("paper_1", 270100)
        if task.question.number == "14.2"
    )
    context = deepcopy(task.question.authoring_context)
    context[field] = {} if field == "referenced_question_data" else []
    candidate = task.question.model_copy(update={"authoring_context": context})

    class Client:
        def generate_json(self, prompt):
            raise AssertionError("Changed public evidence reached the solver")

    with pytest.raises(ValueError, match="changed immutable numeric source contract"):
        _independently_validate_candidate(task, candidate, client=Client())
