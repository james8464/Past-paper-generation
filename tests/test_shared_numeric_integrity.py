from __future__ import annotations

import json
from pathlib import Path

import pytest
from aqaaccountgen.configs import RULES
from aqaaccountgen.generator import build_paper
from aqaaccountgen.syllabus import load_syllabus

from Backend.Core.ai_assessment import _independently_validate_candidate, _tasks
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution


class GivenRateClient:
    def generate_json(self, prompt):
        return {
            "steps": ["Return the given standard hourly rate."],
            "answer": "£97",
            "mark_points": ["£97"],
            "evidence_ids": [],
            "alternatives": [],
            "partial_credit_boundaries": [],
            "follow_through_rules": [],
        }


def accounting_tasks(paper_id="paper_2", seed=26083122):
    syllabus = load_syllabus(
        Path(__file__).resolve().parents[1]
        / "Resources/accounting/aqa/generator/data/syllabus.json"
    )
    paper = build_paper(RULES[paper_id], syllabus, seed)
    return _tasks(paper, {topic.id: topic for topic in syllabus.topics})


def test_shared_validation_never_qualifies_given_97_as_three_variances():
    task = next(t for t in accounting_tasks() if t.question.number == "14.2")
    assert task.question.rule_id == "variance_2"
    assert task.question.authoring_context["source_data"] == {
        "standard_hourly_rate": 97,
        "actual_hourly_rate": 99,
        "standard_hours": 11200,
        "actual_hours": 11300,
        "budgeted_fixed_overhead": 110000,
        "actual_fixed_overhead": 112000,
    }
    try:
        solution = _independently_validate_candidate(
            task, task.question, client=GivenRateClient()
        )
    except ValueError:
        return  # Rejection is safe; source-only deterministic recomputation is too.
    assert solution.answer != "£97", (
        "Given input falsely approved as three outputs; copied draft points: "
        f"{solution.mark_points}"
    )
    assert solution.numeric_results["labour_rate_variance"] == -22600
    assert solution.numeric_results["labour_efficiency_variance"] == -9700
    assert solution.numeric_results["fixed_overhead_expenditure_variance"] == -2000


@pytest.mark.parametrize("seed", [123, 26080100, 26083122])
@pytest.mark.parametrize(
    "rule",
    ["contribution", "budget", "variance_1", "variance_2", "costing_1", "costing_3"],
)
def test_all_p2_closed_calculations_are_source_derived_and_exhaustively_reconciled(
    rule, seed
):
    task = next(t for t in accounting_tasks(seed=seed) if t.question.rule_id == rule)
    solution = _independently_validate_candidate(
        task, task.question, client=GivenRateClient()
    )
    assert solution.solution_source == "deterministic-candidate-inputs"
    assert solution.answer_slots
    assert solution.verified_scope == "declared-numeric-outputs-only"
    assert (
        solution.mark_points
        != task.question.authoring_context["observable_mark_points"]
    )
    assert reconcile_solution(solution, task.question).passed
    slots = dict(solution.answer_slots)
    role = next(iter(slots))
    slots[role] = "£97"
    wrong = solution.model_copy(
        update={"answer_slots": slots, "answer": json.dumps(slots, ensure_ascii=False)}
    )
    assert not reconcile_solution(wrong, task.question).passed


@pytest.mark.parametrize(
    "mutation", ["missing", "swapped", "direction", "unit", "copied_points"]
)
def test_real_variance_boundary_rejects_wrong_roles_values_units_and_missing_outputs(
    mutation,
):
    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    solution = IndependentSolver(GivenRateClient()).solve(task.question, [])
    slots = dict(solution.answer_slots)
    assert set(slots) == {
        "labour_rate_variance",
        "labour_efficiency_variance",
        "fixed_overhead_expenditure_variance",
    }
    if mutation == "missing":
        slots.pop("labour_efficiency_variance")
    elif mutation == "swapped":
        slots["labour_rate_variance"], slots["labour_efficiency_variance"] = (
            slots["labour_efficiency_variance"],
            slots["labour_rate_variance"],
        )
    elif mutation == "direction":
        slots["labour_rate_variance"] = "£22,600 favourable"
    elif mutation == "unit":
        slots["labour_rate_variance"] = "22,600 hours adverse"
    else:
        slots["labour_rate_variance"] = "£97"
    bad = solution.model_copy(
        update={
            "answer_slots": slots,
            "answer": json.dumps(slots, ensure_ascii=False),
            "mark_points": task.question.authoring_context["observable_mark_points"],
        }
    )
    assert not reconcile_solution(bad, task.question).passed


def test_correct_number_in_wrong_published_role_is_rejected():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    raw = task.question.model_dump(mode="json")
    for point in raw["structured_mark_scheme"]:
        point["text"] = point["text"].replace("£22,600", "£9,700")
    raw["mark_scheme"] = [
        text.replace("£22,600", "£9,700") for text in raw["mark_scheme"]
    ]
    with pytest.raises(ValueError, match="reconciliation"):
        _independently_validate_candidate(
            task, task.question.model_validate(raw), client=GivenRateClient()
        )


def test_draft_points_are_expectations_not_independent_work():
    solution = IndependentSolver(GivenRateClient()).solve(
        {
            "id": "open",
            "prompt": "Explain a possible decision.",
            "authoring_context": {"observable_mark_points": ["secret draft point"]},
        },
        [],
    )
    assert solution.mark_points == ["£97"]
    assert solution.examiner_expectations == ["secret draft point"]


def test_unsupported_calculation_is_not_silently_semantic():
    with pytest.raises(ValueError, match=r"numeric.*contract"):
        IndependentSolver(GivenRateClient()).solve(
            {
                "id": "unsupported",
                "kind": "calculation",
                "prompt": "Calculate all outputs.",
                "authoring_context": {"observable_mark_points": ["£97"]},
            },
            [],
        )


def test_priority_is_a_requested_closed_output_not_unchecked_prose():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_3")
    solution = IndependentSolver(GivenRateClient()).solve(task.question, [])
    # Candidate inputs: Product A 118/29, Product B 118/34; A has priority.
    assert solution.answer_slots["ranked_first"] == "Product A"
    raw = task.question.model_dump(mode="json")
    raw["mark_scheme"] = [
        text.replace("Ranking: Product A", "Ranking: Product B")
        for text in raw["mark_scheme"]
    ]
    assert not reconcile_solution(solution, raw).passed


def test_legacy_canonical_numeric_solution_cannot_replay_approval():
    from Backend.Core.independent_solver import CanonicalSolution

    old = CanonicalSolution(item_id="variance_2", answer="£97", mark_points=["£97"])
    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    assert not reconcile_solution(old, task.question).passed


def test_expression_recomputation_has_no_model_work_or_draft_points():
    from Backend.Core.numeric_integrity import percentage_change_context

    item = {
        "id": "percentage",
        "kind": "calculation",
        "prompt": "Calculate the percentage change from 100 to 105, to one decimal place.",
        "authoring_context": percentage_change_context(100, 105),
    }
    solution = IndependentSolver(GivenRateClient()).solve(item, [])
    assert solution.answer_slots == {"percentage_change": "5.0%"}
    assert solution.numeric_results == {"percentage_change": 5}
    assert "Return the given" not in str(solution.steps)
    assert reconcile_solution(solution, {"mark_scheme": ["Answer: 5.0%."]}).passed
    assert not reconcile_solution(
        solution, {"mark_scheme": ["Inputs: 5.0%. Answer: 100%."]}
    ).passed


def test_percentage_contract_locks_requested_direction_to_candidate_prompt():
    from aqaecongen.configs import RULES as ECON_RULES
    from aqaecongen.generator import build_paper as build_economics
    from aqaecongen.syllabus import load_syllabus as load_economics

    syllabus = load_economics(
        Path(__file__).resolve().parents[1]
        / "Resources/economics/aqa/generator/data/syllabus.json"
    )
    paper = build_economics(ECON_RULES["paper_1"], syllabus, 26083122)
    task = next(
        t
        for t in _tasks(paper, {topic.id: topic for topic in syllabus.topics})
        if t.question.kind == "calculation"
    )
    changed = task.question.model_copy(
        update={"prompt": task.question.prompt.replace("2024 to 2028", "2028 to 2024")}
    )
    assert changed.prompt != task.question.prompt
    with pytest.raises(ValueError, match="immutable"):
        _independently_validate_candidate(task, changed, client=GivenRateClient())


def test_scalar_numeric_prose_has_no_number_membership_approval():
    from Backend.Core.independent_solver import CanonicalSolution

    old = CanonicalSolution(item_id="old", answer="£97", mark_points=["£97"])
    assert not reconcile_solution(
        old, {"mark_scheme": ["Rate £97; final answer £22,600 adverse."]}
    ).passed


@pytest.mark.parametrize(
    "field", ["solution_integrity_version", "independent_solution_steps"]
)
def test_saved_difficulty_evidence_does_not_fill_missing_integrity_defaults(field):
    from Backend.Core.model_review import (
        DifficultyReviewResult,
        validate_saved_difficulty_evidence,
    )

    evidence = DifficultyReviewResult(
        approved=True,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        target_profile_fingerprint="current",
        estimated_minutes=1,
        solution_integrity_version="closed-numeric-v2",
    ).model_dump()
    evidence.pop(field)
    with pytest.raises(ValueError, match="incomplete"):
        validate_saved_difficulty_evidence(
            evidence, {"reference_profile_fingerprint": "current"}, item_id="old"
        )


def test_old_canonical_cannot_be_rebranded_by_a_new_difficulty_review():
    from Backend.Core.model_review import require_difficulty_review

    with pytest.raises(ValueError, match="incompatible canonical"):
        require_difficulty_review(
            GivenRateClient(),
            item_id="old",
            subject="Accounting",
            target={},
            candidate={},
            specification={},
            canonical_solution={"answer": "£97", "steps": ["Return given rate"]},
        )


def test_shared_boundary_rejects_source_prompt_divergence():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    changed = task.question.model_copy(
        update={"prompt": task.question.prompt.replace("£97", "£98")}
    )
    with pytest.raises(ValueError, match=r"numeric|prompt|immutable"):
        _independently_validate_candidate(task, changed, client=GivenRateClient())


def test_checkpoint_resume_rejects_changed_preserved_numeric_prompt():
    from Backend.Core.ai_assessment import _validate_checkpoint_item

    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    changed = task.question.model_copy(
        update={"prompt": task.question.prompt.replace("£97", "£98")}
    )
    with pytest.raises(ValueError, match=r"immutable.*prompt"):
        _validate_checkpoint_item(task, changed)


@pytest.mark.parametrize("suffix", ["", ":closed-numeric-v1"])
def test_real_family_adapter_invalidates_pre_numeric_integrity_checkpoint(
    tmp_path, suffix
):
    from dataclasses import replace

    from aqaaccountgen.cli import ADAPTER

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        CheckpointMismatch,
        identity_for_blueprint,
    )
    from Backend.Core.family_adapter import run_family_adapter

    syllabus_path = (
        Path(__file__).resolve().parents[1]
        / "Resources/accounting/aqa/generator/data/syllabus.json"
    )
    syllabus = ADAPTER.load_syllabus(syllabus_path)
    paper = ADAPTER.build(ADAPTER.load_rule("paper_2"), syllabus, 26083122)
    identity = identity_for_blueprint(
        paper,
        provider="ollama",
        model="test",
        prompt_version=ADAPTER.prompt_version + suffix,
    )
    checkpoint_path = tmp_path / "old-checkpoint.json"
    AssessmentCheckpointStore(checkpoint_path, identity).save_payload("old", {})

    def must_not_resume(*args):
        raise AssertionError("stale checkpoint reached authoring")

    with pytest.raises(CheckpointMismatch, match="prompt_version"):
        run_family_adapter(
            replace(ADAPTER, improve=must_not_resume),
            paper="paper_2",
            syllabus_path=syllabus_path,
            output_dir=tmp_path / "output",
            seed=26083122,
            model="test",
            dry_run=False,
            client=GivenRateClient(),
            checkpoint_path=checkpoint_path,
        )


def test_raw_model_numbers_are_not_described_as_verified_results():
    class WorkingClient:
        def generate_json(self, prompt):
            return {
                "answer": "A reasonable explanation.",
                "mark_points": ["Explanation"],
                "numeric_results": {"unverified": 27.9},
                "calculation_details": {"rate": 999},
            }

    with pytest.raises(ValueError, match="invalid solver response envelope"):
        IndependentSolver(WorkingClient()).solve(
            {"id": "explanation", "prompt": "Explain a possible decision."}, []
        )


def test_abc_checks_every_asserted_intermediate_without_rounding_into_final():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver(GivenRateClient()).solve(task.question, [])
    assert solution.answer_slots == {
        "setup_rate": "£741.57/setup",
        "purchase_order_rate": "£225.49/order",
        "setup_overhead": "£20,764.04",
        "purchase_order_overhead": "£9,921.57",
        "total_overhead": "£30,685.61",
        "overhead_per_unit": "£27.90/unit",
    }
    for correct in (
        "£741.57",
        "£225.49",
        "£20,764.04",
        "£9,921.57",
        "£30,685.61",
        "£27.90",
    ):
        raw = task.question.model_dump(mode="json")
        raw["mark_scheme"] = [
            line.replace(correct, "£999.99") for line in raw["mark_scheme"]
        ]
        assert not reconcile_solution(solution, raw).passed, correct


@pytest.mark.parametrize("rule", ["costing_1", "costing_3"])
def test_monetary_output_rounding_is_explicit_for_candidate(rule):
    task = next(t for t in accounting_tasks() if t.question.rule_id == rule)
    assert "two decimal places" in task.question.prompt


def test_published_unit_cannot_contradict_output_role():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver(GivenRateClient()).solve(task.question, [])
    raw = task.question.model_dump(mode="json")
    raw["mark_scheme"] = [
        line.replace("£27.90.", "£27.90 per hour.") for line in raw["mark_scheme"]
    ]
    assert not reconcile_solution(solution, raw).passed


@pytest.mark.parametrize(
    "suffix",
    [
        " million.",
        "m.",
        " billion.",
        " thousand.",
        "e6.",
        "E+06.",
        " × 10^6.",
        " × 10⁶.",
        " * 10**6.",
        "⁶.",
        " USD.",
        " dollars.",
        " pence.",
        " euros.",
        "%.",
        " (million).",
        " per unit million.",
        " per unit per hour.",
        ".000",
        ",000",
    ],
)
def test_published_numeric_token_cannot_hide_scale_currency_or_exponent(suffix):
    from Backend.Core.numeric_integrity import check_published_outputs

    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver().solve(task.question, [])
    check = next(c for c in solution.numeric_checks if c.role == "overhead_per_unit")
    line = f"Overhead cost per unit: £30,685.61 ÷ 1,100 = £27.90{suffix}"
    assert check_published_outputs([check], line)
    raw = task.question.model_dump(mode="json")
    raw["mark_scheme"] = [
        text.replace("£27.90.", f"£27.90{suffix}") for text in raw["mark_scheme"]
    ]
    assert not reconcile_solution(solution, raw).passed


@pytest.mark.parametrize(
    "suffix",
    [
        ".",
        ";",
        ",",
        "",
        "\n",
        " per unit.",
        "/unit.",
        " (own figure).",
        " per unit (own figure).",
    ],
)
def test_published_numeric_result_allows_genuine_punctuation_and_declared_unit(suffix):
    from Backend.Core.numeric_integrity import check_published_outputs

    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver().solve(task.question, [])
    check = next(c for c in solution.numeric_checks if c.role == "overhead_per_unit")
    line = f"Overhead cost per unit: £30,685.61 ÷ 1,100 = £27.90{suffix}"
    assert not check_published_outputs([check], line)


@pytest.mark.parametrize(
    "suffix",
    [
        " (own figure) per hour.",
        " to £50.00 per unit.",
        " and £50.00 per unit.",
        ". per hour.",
        "; million.",
        ", £50.00 per unit.",
        ") million.",
        " (own figure). Accept £97 per unit.",
        "\nper hour.",
        "\nAccept £97 per unit.",
    ],
)
def test_shared_boundary_rejects_unchecked_remainder_of_numeric_result(suffix):
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    raw = task.question.model_dump(mode="json")
    raw["mark_scheme"] = [
        text.replace("£27.90.", f"£27.90{suffix}") for text in raw["mark_scheme"]
    ]
    with pytest.raises(ValueError, match="reconciliation"):
        _independently_validate_candidate(
            task, task.question.model_validate(raw), client=GivenRateClient()
        )


@pytest.mark.parametrize("field", ["alternatives", "allow"])
@pytest.mark.parametrize(
    "alternative",
    [
        "Accept £97 per unit.",
        "Accept £27.90 per hour.",
        "Accept £27.90 per unit to £50.00 per unit.",
        "Accept £27.90 per unit (own figure) per hour.",
        "Accept £0.0279m/unit.",
    ],
)
def test_shared_boundary_rejects_wrong_unconditional_numeric_alternatives(
    field, alternative
):
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    raw = task.question.model_dump(mode="json")
    point = next(
        p
        for p in raw["structured_mark_scheme"]
        if p["text"].startswith("Overhead cost per unit:")
    )
    point[field] = [alternative]
    with pytest.raises(ValueError, match="reconciliation"):
        _independently_validate_candidate(
            task, task.question.model_validate(raw), client=GivenRateClient()
        )


@pytest.mark.parametrize(
    "alternative",
    [
        "Accept £27.9 per unit.",
        "Accept £27.90/unit.",
        "Accept 2790p per unit.",
        "Accept £0.0000279m/unit.",
    ],
)
def test_equivalent_numeric_alternatives_are_bound_to_the_point_role(alternative):
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    raw = task.question.model_dump(mode="json")
    point = next(
        p
        for p in raw["structured_mark_scheme"]
        if p["text"].startswith("Overhead cost per unit:")
    )
    point["alternatives"] = [alternative]
    solution = _independently_validate_candidate(
        task, task.question.model_validate(raw), client=GivenRateClient()
    )
    assert solution.answer_slots["overhead_per_unit"] == "£27.90/unit"


def test_conditional_follow_through_is_not_an_unconditional_numeric_alternative():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver().solve(task.question, [])
    raw = task.question.model_dump(mode="json")
    raw["follow_through_rules"] = [
        "If own total overhead is £106,700, allow £97 per unit for dividing it consistently by 1,100."
    ]
    assert reconcile_solution(solution, raw).passed
    raw["alternatives"] = ["Accept £97 per unit."]
    assert not reconcile_solution(solution, raw).passed


def test_top_level_numeric_alternative_must_name_and_match_its_output_role():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver().solve(task.question, [])
    raw = task.question.model_dump(mode="json")
    raw["alternatives"] = ["overhead_per_unit: £27.9/unit"]
    assert reconcile_solution(solution, raw).passed
    raw["alternatives"] = ["setup_rate: £27.9/setup"]
    assert not reconcile_solution(solution, raw).passed


@pytest.mark.parametrize("unit", ["kg", "GBP/hour", "USD", "unknown"])
def test_unsupported_numeric_unit_contract_never_becomes_dimensionless(unit):
    from Backend.Core.numeric_integrity import NUMBER

    item = {
        "id": "unsupported-unit",
        "kind": "calculation",
        "authoring_context": {
            "calculation_expression": "mass",
            "calculation_variables": {"mass": 3},
            "calculation_input_units": {"mass": unit},
            "calculation_output": {
                "role": "mass",
                "unit": unit,
                "decimal_places": 1,
                "scheme_pattern": rf"^Mass: (?P<value>{NUMBER})",
            },
        },
    }
    with pytest.raises(ValueError, match="unit"):
        IndependentSolver().solve(item, [])


def test_pre_round1_numeric_provenance_cannot_replay_weaker_acceptance():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "costing_1")
    solution = IndependentSolver().solve(task.question, [])
    old = solution.model_copy(update={"integrity_version": "closed-numeric-v1"})
    assert not reconcile_solution(old, task.question).passed


@pytest.mark.parametrize(
    ("unit", "printed"),
    [
        ("GBP", "£3.0"),
        ("GBPm", "£3.0m"),
        ("GBP/unit", "£3.0/unit"),
        ("GBP/kg", "£3.0 per kg"),
        ("GBP/setup", "£3.0/setup"),
        ("GBP/order", "£3.0/order"),
        ("GBP/scarce hour", "£3.0 per scarce hour"),
        ("%", "3.0%"),
        ("1", "3.0"),
    ],
)
def test_current_supported_units_are_checked_as_complete_quantities(unit, printed):
    from Backend.Core.numeric_integrity import (
        MONEY,
        NUMBER,
        CheckedNumericOutput,
        check_published_outputs,
    )

    number = MONEY if unit.startswith("GBP") else rf"(?P<value>{NUMBER})"
    check = CheckedNumericOutput(
        role="result",
        unit=unit,
        decimal_places=1,
        value="3",
        scheme_pattern=rf"^Result: {number}",
    )
    assert not check_published_outputs([check], f"Result: {printed}.")
    assert check_published_outputs([check], f"Result: {printed} per hour.")


def test_incomplete_serialized_numeric_checks_cannot_shrink_required_outputs():
    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    solution = IndependentSolver(GivenRateClient()).solve(task.question, [])
    raw = solution.model_dump(mode="json")
    role = "labour_efficiency_variance"
    raw["answer_slots"].pop(role)
    raw["numeric_results"].pop(role)
    raw["response_slots"].remove(role)
    raw["numeric_checks"] = [
        check for check in raw["numeric_checks"] if check["role"] != role
    ]
    raw["answer"] = json.dumps(raw["answer_slots"], ensure_ascii=False)
    bad = solution.model_validate(raw)
    assert not reconcile_solution(bad, task.question).passed


def test_p1_computed_adjustments_are_individually_verified():
    task = next(
        t
        for t in accounting_tasks("paper_1")
        if t.question.rule_id == "company_statement"
    )
    solution = IndependentSolver().solve(task.question, [])
    expected = {
        "inventory_write_down": 28409,
        "irrecoverable_debt": 196198,
        "new_debenture_interest": 46242,
        "earlier_debenture_interest": 97327,
    }
    for role, value in expected.items():
        assert solution.numeric_results[role] == value
    assert reconcile_solution(solution, task.question).passed


@pytest.mark.parametrize(
    "field", ["solution_source", "verified_scope", "integrity_version"]
)
def test_saved_numeric_provenance_cannot_be_filled_by_defaults(field):
    task = next(t for t in accounting_tasks() if t.question.rule_id == "variance_2")
    solution = IndependentSolver().solve(task.question, [])
    raw = solution.model_dump(mode="json")
    raw.pop(field)
    assert not reconcile_solution(solution.model_validate(raw), task.question).passed


@pytest.mark.parametrize("module", ["aqaecongen", "ocregen", "aqabizgen"])
def test_chart_percentage_shared_families_have_independent_typed_contracts(module):
    import importlib

    generator = importlib.import_module(f"{module}.generator")
    configs = importlib.import_module(f"{module}.configs")
    syllabus_module = importlib.import_module(f"{module}.syllabus")
    path = Path(generator.__file__).parents[1] / "data/syllabus.json"
    syllabus = syllabus_module.load_syllabus(path)
    for rule in configs.RULES.values():
        paper = generator.build_paper(rule, syllabus, 26083122)
        for task in _tasks(paper, {topic.id: topic for topic in syllabus.topics}):
            if task.question.kind == "calculation":
                solution = _independently_validate_candidate(
                    task, task.question, client=GivenRateClient()
                )
                assert set(solution.answer_slots) in (
                    {"percentage_change"},
                    {"current_assets", "current_ratio"},
                    {"capital_employed", "operating_profit"},
                )
                assert solution.solution_source == "deterministic-candidate-inputs"
