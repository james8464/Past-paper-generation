from __future__ import annotations

from decimal import Decimal

import pytest

from Backend.Core.subjects.mathematics import (
    MarkAward,
    MarkingRule,
    MathematicalAnswer,
    MathematicsPlugin,
    compare_mathematical_answers,
    round_to_significant_figures,
)


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        ("(x + 1)**2", "x**2 + 2*x + 1"),
        ("sin(x)**2 + cos(x)**2", "1"),
        ("log(exp(x))", "x"),
        ("2/3", "0.6666666666666667"),
    ],
)
def test_symbolic_and_numeric_equivalence(candidate: str, expected: str) -> None:
    result = compare_mathematical_answers(
        MathematicalAnswer(candidate),
        MathematicalAnswer(expected),
    )

    assert result.equivalent is True


def test_units_and_tolerance_are_checked_independently() -> None:
    close = compare_mathematical_answers(
        MathematicalAnswer("9.806", unit="m s^-2", tolerance=Decimal("0.01")),
        MathematicalAnswer("9.81", unit="m/s^2"),
    )
    wrong_unit = compare_mathematical_answers(
        MathematicalAnswer("9.806", unit="m", tolerance=Decimal("0.01")),
        MathematicalAnswer("9.81", unit="m/s^2"),
    )

    assert close.equivalent is True
    assert wrong_unit.equivalent is False
    assert "unit" in wrong_unit.diagnostics[0]


def test_significant_figure_rounding_handles_zero_and_negative_values() -> None:
    assert round_to_significant_figures(Decimal("0"), 3) == Decimal("0")
    assert round_to_significant_figures(Decimal("0.012345"), 3) == Decimal("0.0123")
    assert round_to_significant_figures(Decimal("-9876"), 2) == Decimal("-9.9E+3")


def test_method_marks_require_declared_dependencies_but_allow_follow_through() -> None:
    rules = (
        MarkingRule("M1", "Chooses the product rule"),
        MarkingRule("A1", "Obtains the derivative", depends_on=("M1",)),
        MarkingRule("FT1", "Uses their derivative consistently", follow_through=True),
    )
    award = MarkAward.from_observed(rules, {"M1", "A1", "FT1"})

    assert award.total == 3
    assert award.awarded == ("M1", "A1", "FT1")
    with pytest.raises(ValueError, match="depends on M1"):
        MarkAward.from_observed(rules, {"A1"})


def test_mathematics_plugin_rejects_unsafe_or_underspecified_items() -> None:
    plugin = MathematicsPlugin()

    unsafe = plugin.validate_item(
        {"question": "Evaluate the expression", "marks": 2, "answer": "__import__('os')"}
    )
    missing = plugin.validate_item({"question": "Solve", "marks": 2})

    assert unsafe.passed is False
    assert missing.passed is False


def test_mathematics_plugin_validates_and_solves_a_typed_item() -> None:
    plugin = MathematicsPlugin()
    item = {
        "question": "Expand (x + 2)^2.",
        "marks": 2,
        "answer": "x**2 + 4*x + 4",
        "variables": ["x"],
        "marking_rules": [
            {"code": "M1", "description": "Uses a valid expansion method"},
            {"code": "A1", "description": "Obtains the correct expression", "depends_on": ["M1"]},
        ],
    }

    assert plugin.validate_item(item).passed is True
    assert str(plugin.solve(item)) == "x**2 + 4*x + 4"
