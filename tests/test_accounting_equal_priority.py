"""An equal scarce-resource return must not be described as higher."""

from __future__ import annotations

from copy import deepcopy

import pytest

from Backend.Core.ai_assessment import _validate_checkpoint_item
from Backend.Core.assessment_checkpoints import identity_for_blueprint
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from tests.test_shared_numeric_integrity import accounting_tasks

TIE_RANKING = (
    "Ranking: Equal priority because both products earn the same contribution "
    "per scarce hour; this criterion alone does not favour either product."
)


def costing_task(seed):
    return next(
        task
        for task in accounting_tasks("paper_2", seed)
        if task.question.rule_id == "costing_3"
    )


def test_real_seed_45_equal_returns_have_no_false_higher_product_claim():
    question = costing_task(45).question
    facts = question.authoring_context["source_data"]
    assert facts == {
        "product_a_contribution": 135,
        "product_a_scarce_hours": 36,
        "product_b_contribution": 120,
        "product_b_scarce_hours": 32,
    }
    assert (
        question.authoring_context["verified_answers"]["ranked_first"]
        == "Equal priority"
    )
    assert TIE_RANKING in question.mark_scheme
    assert not any("higher contribution" in line for line in question.mark_scheme)


def test_rank_guidance_matches_independent_exact_cross_products_across_seeds():
    observed = set()
    for seed in range(100):
        question = costing_task(seed).question
        facts = question.authoring_context["source_data"]
        left = facts["product_a_contribution"] * facts["product_b_scarce_hours"]
        right = facts["product_b_contribution"] * facts["product_a_scarce_hours"]
        expected = (
            "Product A"
            if left > right
            else "Product B"
            if right > left
            else "Equal priority"
        )
        observed.add(expected)
        assert (
            question.authoring_context["verified_answers"]["ranked_first"] == expected
        )
        ranking = next(
            line for line in question.mark_scheme if line.startswith("Ranking:")
        )
        assert ranking == (
            TIE_RANKING
            if left == right
            else f"Ranking: {expected} should be produced first because it has the higher contribution per scarce hour."
        )
    assert observed == {"Product A", "Product B", "Equal priority"}


def test_old_contradictory_tie_scheme_cannot_be_restored_as_current_verified_work():
    current = costing_task(45)
    old = deepcopy(current.question)
    old.mark_scheme = [
        "Ranking: Equal priority should be produced first because it has the higher contribution per scarce hour."
        if line.startswith("Ranking:")
        else line
        for line in old.mark_scheme
    ]
    with pytest.raises(ValueError, match="verified marking guidance"):
        _validate_checkpoint_item(current, old)
    args = {"provider": "ollama", "model": "fixture", "prompt_version": "fixture"}

    def paper(question):
        return {
            "paper_id": "paper_2",
            "seed": 45,
            "questions": [question.model_dump(mode="json")],
        }

    assert identity_for_blueprint(paper(old), **args) != identity_for_blueprint(
        paper(current.question), **args
    )


@pytest.mark.parametrize("seed", [45, 26080100])
def test_correct_tie_reconciles_but_original_false_higher_claim_is_rejected(seed):
    question = costing_task(seed).question
    solution = IndependentSolver().solve(question, [])
    assert reconcile_solution(solution, question).passed
    wrong = question.model_dump(mode="json")
    for index, line in enumerate(wrong["mark_scheme"]):
        if line.startswith("Ranking:"):
            wrong["mark_scheme"][index] = (
                "Ranking: Equal priority should be produced first because it has the higher contribution per scarce hour."
            )
    assert not reconcile_solution(solution, wrong).passed
