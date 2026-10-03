from dataclasses import replace
from decimal import Decimal

import pytest


def test_french_assessment_rejects_uk_context_and_unknown_session():
    from Backend.Core.education_context import NSI_2027, NSI_CONTEXT

    NSI_2027.validate_context(NSI_CONTEXT)
    with pytest.raises(ValueError, match="context"):
        NSI_2027.validate_context(replace(NSI_CONTEXT, education_system="uk"))
    with pytest.raises(ValueError, match="session"):
        NSI_2027.validate_context(NSI_CONTEXT, session=2026)


@pytest.mark.parametrize("value", [0.25, "NaN", "Infinity", "-1", "", True])
def test_points_reject_inexact_or_invalid_input(value):
    from Backend.Core.education_context import points

    with pytest.raises(ValueError):
        points(value)


def test_fractional_credit_adds_exactly_and_separates_language():
    from Backend.Core.education_context import NSI_2027, points

    assert sum(map(points, ["0.1", "0.2"])) == Decimal("0.3")
    NSI_2027.validate_credit(["5.5", "6.25", "6.25"], "2")
    with pytest.raises(ValueError, match="technical"):
        NSI_2027.validate_credit(["6", "6", "8"], "2")
    with pytest.raises(ValueError, match="three"):
        NSI_2027.validate_credit(["9", "9"], "2")


def test_empty_context_is_not_a_wildcard():
    from Backend.Core.education_context import NSI_CONTEXT

    with pytest.raises(ValueError, match="subject"):
        replace(NSI_CONTEXT, subject="")
