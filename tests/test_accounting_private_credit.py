from pathlib import Path

import pytest
from aqaaccountgen.cli import ADAPTER
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import _independently_validate_candidate, _tasks
from Backend.Core.independent_solver import IndependentSolver
from tests.support.solver_responses import complete_solver_response


def test_public_and_credit_contract_changes_have_a_new_accounting_identity():
    assert (
        ADAPTER.prompt_version == "ai-assessment-v11-accounting-public-credit-contracts"
    )


@pytest.mark.parametrize("key", ["accounting_source_content", "grouped_level_policy"])
def test_blind_solver_never_receives_accounting_private_credit(key):
    prompts = []

    class Client:
        def generate_json(self, prompt):
            prompts.append(prompt)
            return complete_solver_response(
                {
                    "answer": "Public reasoning",
                    "steps": ["Use public facts."],
                    "mark_points": ["Public reasoning"],
                }
            )

    IndependentSolver(Client()).solve(
        {
            "id": "private-accounting-canary",
            "kind": "explain",
            "marks": 6,
            "assessment_objectives": {"AO1": 6},
            "prompt": "Explain two reasons for using control accounts.",
            "authoring_context": {
                key: {"text": "PRIVATE_CREDIT_CANARY"},
                "source_data": {
                    "credit": "PUBLIC_CREDIT_COLUMN",
                    "nested": [
                        {key: {"text": "NESTED_CREDIT_CANARY"}, "public": "PUBLIC_FACT"}
                    ],
                },
            },
        },
        [],
    )
    assert len(prompts) == 1
    assert "PRIVATE_CREDIT_CANARY" not in prompts[0]
    assert "NESTED_CREDIT_CANARY" not in prompts[0]
    assert "PUBLIC_CREDIT_COLUMN" in prompts[0]
    assert "PUBLIC_FACT" in prompts[0]


@pytest.mark.parametrize(
    "key",
    ["accounting_source_content", "grouped_level_policy", "accounting_marking_policy"],
)
def test_changed_private_credit_policy_is_rejected_before_model_use(key):
    syllabus = load_syllabus(
        Path(__file__).resolve().parents[1]
        / "Resources/accounting/aqa/generator/data/syllabus.json"
    )
    paper = build_paper(RULES["paper_1"], syllabus, 270100)
    task = next(
        task
        for task in _tasks(paper, {topic.id: topic for topic in syllabus.topics})
        if task.question.number == "11"
    )
    candidate = task.question.model_copy(deep=True)
    candidate.authoring_context[key] = "PRIVATE_REPLACEMENT"

    class Client:
        def generate_json(self, _prompt):
            raise AssertionError("changed private marking contract reached the model")

    with pytest.raises(ValueError, match="immutable numeric source contract"):
        _independently_validate_candidate(task, candidate, client=Client())
