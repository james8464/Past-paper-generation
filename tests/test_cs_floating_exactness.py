"""Exact bounded floating encodings must not depend on Decimal rounding."""

from decimal import ROUND_DOWN, Decimal, localcontext
from pathlib import Path

import pytest

from Backend.Core.subjects import computer_science_contracts as subject

ROOT = Path(__file__).resolve().parents[1]
assert Path(subject.__file__).resolve() == (
    ROOT / "Backend/Core/subjects/computer_science_contracts.py"
)


def encode(value, mantissa=8, exponent=4):
    return subject.solve_computer_science_contract(
        {
            "authoring_context": {
                "cs_input_contract": {
                    "kind": "floating-encode",
                    "value": value,
                    "mantissa_bits": mantissa,
                    "exponent_bits": exponent,
                }
            }
        }
    )["answer"]["representation"]


@pytest.mark.parametrize("precision", [6, 28, 50])
def test_near_dyadic_decimal_is_not_silently_rounded_to_a_representable_value(
    precision,
):
    with localcontext() as context:
        context.prec = precision
        with pytest.raises(ValueError, match="exactly representable"):
            encode("0.50000000000000000000000000001")


def test_out_of_range_decimal_refuses_with_a_bounded_operation_budget(monkeypatch):
    operations = []

    class BudgetDecimal(Decimal):
        def __mul__(self, other):
            operations.append("multiply")
            assert len(operations) <= 32, "normalisation exceeded its operation budget"
            return BudgetDecimal(super().__mul__(other))

        def __truediv__(self, other):
            operations.append("divide")
            assert len(operations) <= 32, "normalisation exceeded its operation budget"
            return BudgetDecimal(super().__truediv__(other))

    monkeypatch.setattr(subject, "Decimal", BudgetDecimal)
    # Only 100 decimal places, never an enormous exponent or timing deadline.
    with pytest.raises(ValueError):
        encode("1e-100")
    assert len(operations) <= 32


@pytest.mark.parametrize(
    "value,mantissa,exponent,expected",
    [
        ("0.5", 8, 4, "010000000000"),
        ("6.5", 5, 3, "01101011"),
        ("0.125", 5, 3, "01000110"),
        ("7.5", 5, 3, "01111011"),
        ("0.001953125", 8, 4, "010000001000"),
        ("127", 8, 4, "011111110111"),
        ("0.5" + "0" * 400, 8, 4, "010000000000"),
    ],
)
def test_exact_values_and_signed_exponent_widths_remain_supported(
    value, mantissa, exponent, expected
):
    with localcontext() as context:
        context.prec = 6
        assert encode(value, mantissa, exponent) == expected


@pytest.mark.parametrize("value", ["0", "-0", "-0.5", "NaN", "sNaN", "Infinity", "0.1"])
def test_existing_nonpositive_nonfinite_and_inexact_refusals_remain(value):
    with pytest.raises(ValueError):
        encode(value)


@pytest.mark.parametrize("value", [0.5, True, None, {"value": "0.5"}])
def test_unknown_value_types_refuse(value):
    with pytest.raises(ValueError):
        encode(value)


@pytest.mark.parametrize("mantissa", [2, 5, 8, 16])
@pytest.mark.parametrize("exponent", [2, 3, 4, 8])
def test_exact_width_boundaries_have_the_original_signed_normalised_encoding(
    mantissa, exponent
):
    limit = 2 ** (exponent - 1)
    for power in (-limit, 0, limit - 1):
        for coefficient in (2 ** (mantissa - 2), 2 ** (mantissa - 1) - 1):
            # Decode known bits exactly to a decimal fixture, independently of
            # the production decimal-to-binary encoder and ambient precision.
            with localcontext() as context:
                context.prec = 300
                value = Decimal(coefficient) * Decimal(2) ** (power - mantissa + 1)
            with localcontext() as context:
                context.prec = 2
                assert encode(str(value), mantissa, exponent) == (
                    f"{coefficient:0{mantissa}b}{power % (2**exponent):0{exponent}b}"
                )


@pytest.mark.parametrize("value", ["0.001953124", "128", "1e100", "not a number"])
def test_range_and_invalid_decimal_refusals_remain_controlled(value):
    with pytest.raises(ValueError):
        encode(value)


@pytest.mark.parametrize(
    "mantissa,exponent", [(1, 4), (17, 4), (8, 1), (8, 9), (True, 4)]
)
def test_existing_width_limits_remain_strict(mantissa, exponent):
    with pytest.raises(ValueError):
        encode("0.5", mantissa, exponent)


@pytest.mark.parametrize("value", ["000.5000", "+5e-1", "5.000E-1", "0.0000005e6"])
def test_equivalent_padded_decimal_spellings_preserve_the_value(value):
    assert encode(value) == encode("0.5")


@pytest.mark.parametrize(
    "value", ["1e1000000000", "1e-1000000000", "0.5" + "0" * 500 + "1"]
)
def test_magnitude_and_coefficient_admission_precede_ratio_allocation(
    monkeypatch, value
):
    def forbidden_conversion(*args, **kwargs):
        pytest.fail("unsupported source reached ratio construction")

    # The production int conversion precedes every power/ratio allocation.
    # This trap makes a missing early guard fail without allocating giant powers.
    monkeypatch.setattr(subject, "int", forbidden_conversion, raising=False)
    with pytest.raises(ValueError, match="exactly representable"):
        encode(value)


def test_encoding_does_not_change_the_callers_decimal_context():
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        context.clear_flags()
        before = (
            context.prec,
            context.rounding,
            dict(context.flags),
            dict(context.traps),
        )
        assert encode("6.5", 5, 3) == "01101011"
        for value in ("not a number", "sNaN", "0.50000000000000000000000000001"):
            with pytest.raises(ValueError):
                encode(value)
        assert (
            context.prec,
            context.rounding,
            dict(context.flags),
            dict(context.traps),
        ) == before
