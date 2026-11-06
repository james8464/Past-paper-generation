"""Variance direction and currency tokens share the closed-output boundary."""

from dataclasses import replace
from pathlib import Path

import pytest

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.numeric_integrity import (
    MONEY,
    NUMERIC_INTEGRITY_VERSION,
    CheckedNumericOutput,
    check_numeric_alternatives,
    check_published_outputs,
)

OLD_VERSION = "closed-numeric-v3-exact-floating"


def variance(value, *, unit="GBP", places=2):
    scale = "m" if unit == "GBPm" else ""
    return CheckedNumericOutput(
        role="owned_variance",
        unit=unit,
        decimal_places=places,
        scheme_pattern=rf"^Variance: {MONEY}{scale}\s+(?P<direction>favourable|adverse|nil)",
        sign="variance",
        value=value,
    )


@pytest.mark.parametrize("value", ["0", "-0", "0.004", "-0.004"])
@pytest.mark.parametrize("unit", ["GBP", "GBPm"])
@pytest.mark.parametrize("direction", ["nil", "favourable", "adverse"])
def test_published_rounded_zero_is_nil_only(value, unit, direction):
    amount = "£0.00m" if unit == "GBPm" else "£0.00"
    errors = check_published_outputs(
        [variance(value, unit=unit)], f"Variance: {amount} {direction}"
    )
    assert bool(errors) is (direction != "nil")


@pytest.mark.parametrize("unit", ["GBP", "GBPm"])
@pytest.mark.parametrize("amount", ["£0.00", "£0m", "0p", "0 pence"])
@pytest.mark.parametrize("direction", ["nil", "favourable", "adverse"])
def test_zero_alternatives_are_nil_only_after_scale_conversion(unit, amount, direction):
    errors = check_numeric_alternatives(
        [variance("0.004", unit=unit)], [f"Accept {amount} {direction}."]
    )
    assert bool(errors) is (direction != "nil")


@pytest.mark.parametrize(
    "value, magnitude, direction",
    [
        ("0.005", "0.01", "favourable"),
        ("-0.005", "0.01", "adverse"),
        ("1.005", "1.01", "favourable"),
        ("-1.005", "1.01", "adverse"),
    ],
)
def test_nonzero_rounding_direction_and_precision_are_preserved(
    value, magnitude, direction
):
    check = variance(value)
    assert not check_published_outputs([check], f"Variance: £{magnitude} {direction}")
    assert not check_numeric_alternatives([check], [f"£{magnitude} {direction}"])
    assert check_numeric_alternatives([check], [f"£{magnitude} nil"])
    assert check_published_outputs([check], f"Variance: £{magnitude} nil")
    wrong = "adverse" if direction == "favourable" else "favourable"
    assert check_published_outputs([check], f"Variance: £{magnitude} {wrong}")
    assert check_numeric_alternatives([check], [f"£{magnitude} {wrong}"])


@pytest.mark.parametrize(
    "unit, value, quantity",
    [
        ("GBP", "1.004", "100.4p favourable"),
        ("GBPm", "0.004", "£4000 nil"),
        ("GBPm", "1.234", "£1234000 favourable"),
    ],
)
def test_alternatives_do_not_gain_a_new_rounding_step(unit, value, quantity):
    assert check_numeric_alternatives([variance(value, unit=unit)], [quantity])


@pytest.mark.parametrize(
    "quantity", ["-£-1.00", "+£-1.00", "−£−1.00", "-£+1.00", "+£+1.00"]
)
@pytest.mark.parametrize("channel", ["published", "alternative"])
def test_double_signed_currency_is_a_structured_refusal(quantity, channel):
    check = CheckedNumericOutput(
        role="owned",
        unit="GBP",
        decimal_places=2,
        scheme_pattern=rf"^Answer: {MONEY}",
        value="1",
    )
    if channel == "published":
        assert check_published_outputs([check], f"Answer: {quantity}")
    else:
        assert check_numeric_alternatives([check], [quantity])


@pytest.mark.parametrize(
    "quantity, expected",
    [
        ("-£1.00", "-1"),
        ("£-1.00", "-1"),
        ("−£1.00", "-1"),
        ("£−1.00", "-1"),
        ("+£1.00", "1"),
        ("£+1.00", "1"),
    ],
)
def test_one_currency_sign_on_either_side_stays_supported(quantity, expected):
    check = CheckedNumericOutput(
        role="owned",
        unit="GBP",
        decimal_places=2,
        scheme_pattern=rf"^Answer: {MONEY}",
        value=expected,
    )
    assert not check_published_outputs([check], f"Answer: {quantity}")
    assert not check_numeric_alternatives([check], [quantity])


def test_previous_numeric_approval_cannot_be_relabelled_as_current():
    check = variance("0")
    item = {
        "id": "owned",
        "kind": "calculation",
        "prompt": "Calculate the variance.",
        "authoring_context": {
            "calculation_expression": "amount",
            "calculation_variables": {"amount": 0},
            "calculation_input_units": {"amount": "GBP"},
            "calculation_output": check.model_dump(exclude={"value"}),
        },
    }
    solution = IndependentSolver().solve(item, [])
    scheme = {"mark_scheme": ["Variance: £0.00 nil"]}
    assert solution.integrity_version == NUMERIC_INTEGRITY_VERSION
    assert reconcile_solution(solution, scheme).passed
    old = solution.model_copy(update={"integrity_version": OLD_VERSION})
    assert not reconcile_solution(old, scheme).passed


def test_previous_canonical_cannot_trigger_a_new_difficulty_review():
    from Backend.Core.model_review import require_difficulty_review

    class NoModel:
        def generate_json(self, _prompt):
            pytest.fail("stale evidence reached a model")

    with pytest.raises(ValueError, match="incompatible canonical"):
        require_difficulty_review(
            NoModel(),
            item_id="owned",
            subject="Accounting",
            target={},
            candidate={},
            specification={},
            canonical_solution={"integrity_version": OLD_VERSION},
        )


def test_previous_saved_review_cannot_replay_current_numeric_acceptance():
    from Backend.Core import model_review

    source = {
        "id": "owned",
        "marks": 1,
        "kind": "calculation",
        "prompt": "Calculate the supplied variance.",
    }
    evidence = model_review.DifficultyReviewResult(
        approved=True,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=True,
        command_word_fit=True,
        context_fit=True,
        profile_fit=True,
        solution_integrity_version=OLD_VERSION,
        public_task_operation_evidence=model_review._public_task_operation_evidence(
            source
        ),
        candidate_content_identity=model_review.candidate_content_identity(source),
    ).model_dump(mode="json")
    with pytest.raises(ValueError, match="incompatible solution integrity"):
        model_review.validate_saved_difficulty_evidence(
            evidence, {}, item_id="owned", candidate=source
        )


@pytest.mark.parametrize("policy", [OLD_VERSION, NUMERIC_INTEGRITY_VERSION])
def test_previous_checkpoint_version_cannot_reuse_accepted_items(
    tmp_path, monkeypatch, policy
):
    from aqaaccountgen.cli import ADAPTER

    from Backend.Core import family_adapter
    from Backend.Core.ai_assessment import ASSESSMENT_REVIEW_VERSION
    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        CheckpointMismatch,
        identity_for_blueprint,
    )
    from Backend.Core.family_adapter import run_family_adapter

    monkeypatch.setattr(family_adapter, "NUMERIC_INTEGRITY_VERSION", policy)

    syllabus_path = (
        Path(__file__).resolve().parents[1]
        / "Resources/accounting/aqa/generator/data/syllabus.json"
    )
    syllabus = ADAPTER.load_syllabus(syllabus_path)
    paper = ADAPTER.build(ADAPTER.load_rule("paper_2"), syllabus, 26083122)
    identity = identity_for_blueprint(
        paper,
        provider="ollama",
        model="owned",
        prompt_version=f"{ADAPTER.prompt_version}:{OLD_VERSION}:{ASSESSMENT_REVIEW_VERSION}",
    )
    checkpoint = tmp_path / "old.json"
    AssessmentCheckpointStore(checkpoint, identity).save_payload("owned", {})

    class NoModel:
        provider, model = "ollama", "owned"

        def generate_json(self, _prompt):
            pytest.fail("stale checkpoint reached a model")

    class ReachedAuthoring(RuntimeError):
        pass

    def must_not_resume(*_args):
        raise ReachedAuthoring("pre-fix identity reached authoring")

    expected = ReachedAuthoring if policy == OLD_VERSION else CheckpointMismatch
    with pytest.raises(
        expected, match="authoring" if policy == OLD_VERSION else "prompt_version"
    ):
        run_family_adapter(
            replace(ADAPTER, improve=must_not_resume),
            paper="paper_2",
            syllabus_path=syllabus_path,
            output_dir=tmp_path / "output",
            seed=26083122,
            model="owned",
            dry_run=False,
            client=NoModel(),
            checkpoint_path=checkpoint,
        )
