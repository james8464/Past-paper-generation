"""Internal range iteration must not change Python comparison semantics."""

import json

import pytest

from Backend.Core.france.llm_pipeline import validate_authored_exercise
from Backend.Core.france.verification import verify_contract
from tests.test_french_llm_pipeline import raw_exercise
from tests.test_french_trace_bindings import contract


@pytest.mark.parametrize(
    "code",
    [
        "x = range(3) == [0, 1, 2]",
        "r = range(3)\nx = r == [0, 1, 2]",
    ],
)
def test_range_is_not_a_list_in_trace_evidence(code):
    assert verify_contract(contract(code, True))["passed"] is False
    assert verify_contract(contract(code, False)) == {
        "state": "passed",
        "passed": True,
        "actual": False,
    }


def test_public_french_admission_refuses_range_list_false_equivalence():
    raw = raw_exercise()
    code = "x = range(3) == [0, 1, 2]"
    raw["questions"][0].update(
        prompt=f"On exécute ce programme Python.\n```python\n{code}\n```\nDonner x.",
        answer="True",
        verification=contract(code, True),
    )
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "code,expected",
    [
        ("x = range(0) == range(2, 2)", True),
        ("x = range(0, 3, 2) == range(0, 4, 2)", True),
        ("x = range(3) != [0, 1, 2]", True),
        ("r = range(5, 0, -2)\nx = len(r)", 3),
        ("r = range(5, 0, -2)\nx = r[-1]", 1),
        ("r = range(4)\nx = 0\nfor i in r:\n    x = x + i", 6),
        ("x = len(range(256))", 256),
    ],
)
def test_bounded_range_operations_keep_python_results(code, expected):
    assert verify_contract(contract(code, expected)) == {
        "state": "passed",
        "passed": True,
        "actual": expected,
    }


@pytest.mark.parametrize(
    "code,expected",
    [
        ("x = range(3)", [0, 1, 2]),
        ("x = [range(3)]", [[0, 1, 2]]),
        ("x = [[0, 1, 2]]", [[0, 1, 2]]),
        ("x = range(3) < range(4)", True),
        ("x = len(range(257))", 257),
        ("x = len(range(0, 2, 0))", 0),
    ],
)
def test_unsupported_results_and_range_limits_fail_with_serializable_evidence(
    code, expected
):
    result = verify_contract(contract(code, expected))
    assert result["state"] == "failed"
    assert result["passed"] is False
    json.dumps(result, allow_nan=False)
