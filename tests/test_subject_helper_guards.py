"""Small owned helper regressions; no generator, model or user files."""

from decimal import ROUND_DOWN, Decimal, Rounded, localcontext

import pytest

from Backend.Core.subjects.essay import EssaySubjectPlugin
from Backend.Core.subjects.mathematics import (
    MathematicalAnswer,
    compare_mathematical_answers,
    round_to_significant_figures,
)


@pytest.mark.parametrize(
    "value,figures,expected",
    [
        ("9.99", 2, "10"),
        ("999", 2, "1.0E+3"),
        ("-9.99", 2, "-10"),
        ("-999", 2, "-1.0E+3"),
        ("0.0999", 2, "0.10"),
        ("1.2", 3, "1.20"),
        ("0.012345", 3, "0.0123"),
    ],
)
def test_significant_figure_carry_keeps_the_exact_requested_representation(
    value, figures, expected
):
    assert (
        round_to_significant_figures(Decimal(value), figures).as_tuple()
        == Decimal(expected).as_tuple()
    )


def test_rounding_uses_but_does_not_change_the_ambient_context():
    with localcontext() as context:
        context.prec = 1
        context.rounding = ROUND_DOWN
        context.flags[Rounded] = True
        before = context.copy()
        assert (
            round_to_significant_figures(Decimal("9.99"), 2).as_tuple()
            == Decimal("9.9").as_tuple()
        )
        assert context.prec == before.prec and context.rounding == before.rounding
        assert context.flags == before.flags and context.traps == before.traps


@pytest.mark.parametrize("value", ["NaN", "sNaN", "Infinity", "-Infinity"])
def test_rounding_refuses_nonfinite_inputs_with_a_controlled_error(value):
    with pytest.raises(ValueError):
        round_to_significant_figures(Decimal(value), 2)


@pytest.mark.parametrize(
    "left,right,tolerance,accepted",
    [
        ("sqrt(-1)", "0", "0", False),
        ("sqrt(-1)", "sqrt(-1)", "0", True),
        ("1+sqrt(-1)", "1+2*sqrt(-1)", "1", True),
        ("1+sqrt(-1)", "1+2*sqrt(-1)", "0.9", False),
        ("1/0", "0", "0", False),
        ("9.806", "9.81", "0.01", True),
    ],
)
def test_complex_numeric_magnitudes_and_finite_admission(
    left, right, tolerance, accepted
):
    assert (
        compare_mathematical_answers(
            MathematicalAnswer(left, tolerance=Decimal(tolerance)),
            MathematicalAnswer(right),
        ).equivalent
        is accepted
    )


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity"), Decimal("-1")])
def test_mathematical_comparison_refuses_invalid_tolerances(value):
    assert not compare_mathematical_answers(
        MathematicalAnswer("2", tolerance=value), MathematicalAnswer("1")
    ).equivalent


@pytest.mark.parametrize("marks", ["12", [12], {"marks": 12}, 12.0, True, None])
def test_essay_invalid_marks_return_diagnostics_instead_of_comparing_types(marks):
    result = EssaySubjectPlugin("psychology").validate_item(
        {
            "question": "Owned question",
            "marks": marks,
            "answer": "Owned indicative content",
        }
    )
    assert not result.passed
    assert "marks must be a positive integer" in result.diagnostics


def test_essay_valid_extended_marks_still_require_the_level_policy():
    item = {
        "question": "Owned question",
        "marks": 12,
        "answer": "Owned indicative content",
    }
    plugin = EssaySubjectPlugin("psychology")
    assert not plugin.validate_item(item).passed
    item["level_policy_id"] = "owned-policy"
    assert plugin.validate_item(item).passed
