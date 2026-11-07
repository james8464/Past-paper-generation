"""Public variance facts, not a model's answer, own this bounded choice."""

from copy import deepcopy

import pytest

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _candidate_question,
    _validate_checkpoint_item,
)
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.subjects import accounting_selected_response as accounting
from Backend.Core.subjects.selected_response import solve_selected_response
from tests.test_accounting_paper_two_source_choices import NoModelClient, selected_task

RETAINED_STEM = (
    "A business buys a quantity of material that is below the standard amount "
    "used for production. If the price paid per unit is higher than the "
    "standard price, what type of variance will be recorded?"
)


def facts(**changes):
    return {
        "variance": "price",
        "quantity_basis": "purchased",
        "quantity": "positive",
        "comparison": "below",
        **changes,
    }


def public_item(**changes):
    contract = accounting.accounting_selected_response_contract(
        "material_variance_classification", facts(**changes)
    )
    return {
        "kind": "multiple_choice",
        "marks": 1,
        "subject": "accounting_aqa",
        "prompt": accounting.material_variance_prompt(contract),
        "choices": [
            "Favourable",
            "Adverse",
            "Zero",
            "Not measurable without the selling price",
        ],
        "authoring_context": {"selected_response_contract": contract},
    }


def test_retained_unsupported_rewrite_cannot_replace_public_price_task():
    task = selected_task("06", seed=270100)
    candidate = _candidate_question(
        task,
        {
            "prompt": RETAINED_STEM,
            "choices": [
                "An adverse material usage variance",
                "A favourable material usage variance",
                "An adverse material price variance",
                "A favourable material price variance",
            ],
            "correct_choice": 1,
            "mark_scheme": [
                {
                    "text": "A favourable material usage variance",
                    "marks": 1,
                    "assessment_objective": "AO1",
                    "credit_type": "answer",
                }
            ],
            "has_single_valid_choice": True,
        },
        client=NoModelClient(),
        policy=GenerationPolicy(),
    )
    assert candidate.prompt == task.question.prompt
    assert candidate.choices == task.question.choices
    assert candidate.correct_choice == task.question.correct_choice
    assert candidate.mark_scheme == task.question.mark_scheme


@pytest.mark.parametrize(
    "variance,basis",
    [("price", "purchased"), ("price", "consumed"), ("usage", "consumed")],
)
@pytest.mark.parametrize(
    "comparison,answer",
    [("below", "Favourable"), ("equal", "Zero"), ("above", "Adverse")],
)
def test_classification_uses_explicit_target_role_and_comparison(
    variance, basis, comparison, answer
):
    item = public_item(variance=variance, quantity_basis=basis, comparison=comparison)
    solved = solve_selected_response(item)
    assert solved["answer"] == answer
    assert len(solved["steps"]) >= 2
    assert IndependentSolver(NoModelClient()).solve(item, []).answer == answer


def test_purchases_are_insufficient_to_establish_usage():
    # Retained counterexample: standard100kg, purchases90kg, opening20kg and
    # consumption110kg satisfy purchases<standard but imply adverse usage.
    contract = accounting.accounting_selected_response_contract(
        "material_variance_classification", facts(variance="usage")
    )
    with pytest.raises(ValueError, match="consumption"):
        accounting.derive_accounting_choice(contract)


@pytest.mark.parametrize(
    "changes",
    [
        {"variance": "both"},
        {"quantity": "unknown"},
        {"comparison": "unknown"},
        {"quantity_basis": "inventory"},
    ],
)
def test_missing_or_ambiguous_fact_domains_refuse(changes):
    with pytest.raises(ValueError):
        item = public_item(**changes)
        solve_selected_response(item)


@pytest.mark.parametrize(
    "prompt",
    [RETAINED_STEM, "A business uses less material. Select its price variance."],
)
def test_visible_wording_cannot_diverge_from_declared_facts(prompt):
    item = public_item()
    item["prompt"] = prompt
    with pytest.raises(ValueError, match="visible wording"):
        solve_selected_response(item)


@pytest.mark.parametrize(
    "mutation",
    ["changed_fact", "missing_answer", "semantic_duplicate", "wrong_subject"],
)
def test_contract_and_choice_mutations_fail_closed(mutation):
    item = public_item()
    if mutation == "changed_fact":
        item["authoring_context"]["selected_response_contract"]["inputs"][
            "comparison"
        ] = "above"
    elif mutation == "missing_answer":
        item["choices"][0] = "Unrelated"
    elif mutation == "semantic_duplicate":
        item["choices"][1] = "favourable"
    else:
        item["subject"] = "economics"
    with pytest.raises(ValueError):
        solve_selected_response(item)


def test_seeded_q06_visible_content_and_budget_are_unchanged():
    question = selected_task("06", seed=270100).question
    context = question.authoring_context
    assert (
        context["source_data"]
        == context["selected_response_contract"]["inputs"]
        == facts()
    )
    assert context["preserve_prompt"] is True
    assert context["preserve_mark_scheme"] is True
    assert (
        question.prompt
        == "A business buys a positive quantity of material below the standard price. What is the material price variance?"
    )
    assert set(question.choices) == {
        "Favourable",
        "Adverse",
        "Zero",
        "Not measurable without the selling price",
    }
    assert question.marks == 1 and question.assessment_objectives == {"AO1": 1}
    public = deepcopy(question.model_dump(mode="json"))
    for key in ("correct_choice", "mark_scheme", "structured_mark_scheme"):
        public.pop(key)
    assert (
        solve_selected_response(public)["answer"]
        == question.choices[question.correct_choice]
    )


@pytest.mark.parametrize("number", ["04", "05"])
def test_existing_price_independent_operations_are_unchanged(number):
    question = selected_task(number).question
    assert question.authoring_context["selected_response_contract"]["operation"] in {
        "cash_budget_balance",
        "contribution_per_unit",
    }
    assert (
        IndependentSolver(NoModelClient())
        .solve(question.model_dump(mode="json"), [])
        .answer
        == question.choices[question.correct_choice]
    )


def test_retained_rewrite_is_not_resumed_from_checkpoint():
    task = selected_task("06")
    retained = task.question.model_copy(update={"prompt": RETAINED_STEM})
    with pytest.raises(ValueError, match="immutable preserved prompt"):
        _validate_checkpoint_item(task, retained)


def test_wrong_private_key_cannot_override_public_variance_truth():
    item = selected_task("06").question.model_dump(mode="json")
    item["correct_choice"] = (item["correct_choice"] + 1) % 4
    solution = IndependentSolver(NoModelClient()).solve(item, [])
    assert solution.answer == "Favourable"
    assert not reconcile_solution(solution, item).passed


@pytest.mark.parametrize(
    "field", ["variance", "quantity_basis", "quantity", "comparison"]
)
def test_incomplete_public_facts_refuse(field):
    item = public_item()
    del item["authoring_context"]["selected_response_contract"]["inputs"][field]
    with pytest.raises(ValueError):
        solve_selected_response(item)


@pytest.mark.parametrize("quantity", ["zero", "negative", 0, True])
def test_nonpositive_or_mistyped_quantity_domain_refuses(quantity):
    with pytest.raises(ValueError):
        solve_selected_response(public_item(quantity=quantity))


@pytest.mark.parametrize("mutation", ["extra_fact", "wrong_unit"])
def test_unknown_fact_or_output_domain_refuses(mutation):
    item = public_item()
    contract = item["authoring_context"]["selected_response_contract"]
    if mutation == "extra_fact":
        contract["inputs"]["actual_consumption"] = "invented"
    else:
        contract["unit"] = "GBP"
    with pytest.raises(ValueError):
        solve_selected_response(item)


def test_older_item_cache_is_refused_without_rewriting_retained_bytes(tmp_path):
    from aqaaccountgen.cli import ADAPTER

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        CheckpointMismatch,
        identity_for_blueprint,
    )

    question = selected_task("06", seed=270100).question
    current_blueprint = {
        "paper_id": "paper_2",
        "seed": 270100,
        "questions": [question.model_dump(mode="json")],
    }
    old_blueprint = deepcopy(current_blueprint)
    context = old_blueprint["questions"][0]["authoring_context"]
    for field in (
        "preserve_prompt",
        "preserve_mark_scheme",
        "selected_response_contract",
        "source_data",
    ):
        context.pop(field)
    current = identity_for_blueprint(
        current_blueprint,
        provider="ollama",
        model="fixture",
        prompt_version=ADAPTER.prompt_version,
    )
    old = identity_for_blueprint(
        old_blueprint,
        provider="ollama",
        model="fixture",
        prompt_version="ai-assessment-v14-accounting-level-contracts",
    )
    assert current != old
    path = tmp_path / "retained.json"
    AssessmentCheckpointStore(path, old).save_payload("06", {"original": "retained"})
    before = path.read_bytes()
    with pytest.raises(CheckpointMismatch):
        AssessmentCheckpointStore(path, current)
    assert path.read_bytes() == before
