"""Exact distance admission must not depend on ambient Decimal arithmetic."""

from decimal import (
    MAX_EMAX,
    MIN_ETINY,
    ROUND_UP,
    Decimal,
    Inexact,
    InvalidOperation,
    Rounded,
    Underflow,
    localcontext,
)
from fractions import Fraction
from random import Random

import pytest

from Backend.Core.subjects.physics import compare_physical_answers


@pytest.mark.parametrize(
    ("candidate", "expected", "tolerance", "accepted"),
    [
        ("1e-10000000", "0", "0", False),
        ("-1e-10000000", "0", "0", False),
        ("1e-10000000", "-1e-10000000", "1e-10000000", False),
        ("1e-10000000", "-1e-10000000", "2e-10000000", True),
        ("1e-10000000", "1e-10000000", "0", True),
        ("-0", "0.000", "0", True),
        ("1.0", "1", "0", True),
        ("999", "-1", "1000", True),
        ("999", "-1", "999", False),
        ("1000", "1", "999", True),
        ("1000", "1", "998", False),
        ("1", "1e-10000000", "1", True),
        ("1", "-1e-10000000", "1", False),
        ("-1", "1e-10000000", "1", False),
        ("1.001", "0", "1.000", False),
        ("1.001", "0", "1.001", True),
        (f"1e{MAX_EMAX}", f"-1e{MAX_EMAX}", f"2e{MAX_EMAX}", True),
    ],
)
def test_exact_distance_boundaries(candidate, expected, tolerance, accepted):
    assert (
        compare_physical_answers(
            candidate, expected, "V", "V", tolerance=Decimal(tolerance)
        )
        is accepted
    )


@pytest.mark.parametrize("coefficient,accepted", [(1, True), (2, False), (-2, False)])
def test_smallest_constructible_exponents(coefficient, accepted):
    try:
        tolerance = Decimal(f"1e{MIN_ETINY}")
        candidate = Decimal(f"{coefficient}e{MIN_ETINY}")
    except InvalidOperation:
        pytest.skip("This Decimal implementation cannot construct MIN_ETINY inputs")
    assert (
        compare_physical_answers(str(candidate), "0", "V", "V", tolerance=tolerance)
        is accepted
    )


def test_ambient_precision_rounding_traps_and_flags_are_not_used_or_changed():
    with localcontext() as context:
        context.prec = 1
        context.rounding = ROUND_UP
        for signal in (Inexact, Rounded, Underflow):
            context.traps[signal] = True
        context.flags[Rounded] = True
        before = context.copy()
        assert compare_physical_answers("12.0", "12", "V", "V", significant_figures=3)
        assert not compare_physical_answers(
            "1.001", "0", "V", "V", tolerance=Decimal("1")
        )
        assert compare_physical_answers(
            "1", "1e-10000000", "V", "V", tolerance=Decimal("1")
        )
        assert context.prec == before.prec
        assert context.rounding == before.rounding
        assert context.flags == before.flags
        assert context.traps == before.traps


def test_seeded_moderate_distances_match_exact_fraction_oracle():
    random = Random(27011105)
    for _ in range(250):
        values = [
            Decimal(f"{random.randint(-999999, 999999)}e{random.randint(-30, 30)}")
            for _ in range(3)
        ]
        left, right, raw_tolerance = values
        tolerance = raw_tolerance.copy_abs()
        distance = abs(Fraction(left) - Fraction(right))
        expected = distance <= Fraction(tolerance)
        assert (
            compare_physical_answers(
                str(left), str(right), "V", "V", tolerance=tolerance
            )
            is expected
        ), (left, right, tolerance)


def test_units_and_significant_figures_still_apply_after_exact_distance():
    assert not compare_physical_answers("12.0", "12", "A", "V")
    assert not compare_physical_answers("12", "12", "V", "V", significant_figures=3)
    assert compare_physical_answers("12.0", "12", "V", "V", significant_figures=3)
