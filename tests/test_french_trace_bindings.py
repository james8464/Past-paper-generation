"""Bounded traces must respect assignments to Python builtin names."""

import pytest

from Backend.Core.france.llm_pipeline import validate_authored_exercise
from Backend.Core.france.verification import verify_contract
from tests.test_french_llm_pipeline import raw_exercise

SHADOWED_CALLS = [
    ("len = 7\nx = len([1, 2])", 2),
    ("range = 7\nx = 0\nfor i in range(3):\n    x = x + i", 3),
]


def contract(code, expected):
    return {
        "kind": "python_trace",
        "code": code,
        "variable": "x",
        "expected": expected,
    }


@pytest.mark.parametrize("code,expected", SHADOWED_CALLS)
def test_shadowed_builtin_call_cannot_receive_passed_evidence(code, expected):
    # Real Python raises TypeError instead of calling the original builtin.
    result = verify_contract(contract(code, expected))
    assert not result["passed"]
    assert result["state"] != "passed"


@pytest.mark.parametrize("code,expected", SHADOWED_CALLS)
def test_public_french_admission_refuses_shadowed_builtin_call(code, expected):
    raw = raw_exercise()
    raw["questions"][0].update(
        prompt=f"On exécute ce programme Python.\n```python\n{code}\n```\nDonner x.",
        answer=str(expected),
        verification=contract(code, expected),
    )
    with pytest.raises(ValueError):
        validate_authored_exercise(raw, "1")


@pytest.mark.parametrize(
    "code,expected",
    [
        ("x = len([1, 2])", 2),
        ("x = 0\nfor i in range(3):\n    x = x + i", 3),
        ("len = 7\nx = len + 1", 8),
        ("range = 7\nx = range + 1", 8),
        ("if 0:\n    len = 7\n    range = 7\nx = len(range(3))", 3),
    ],
)
def test_valid_builtin_use_and_uncalled_shadowed_values_remain_supported(
    code, expected
):
    result = verify_contract(contract(code, expected))
    assert result == {"state": "passed", "passed": True, "actual": expected}


@pytest.mark.parametrize("statement", ["return", "break", "continue", "nonlocal x"])
def test_trace_refuses_invalid_module_syntax_even_in_unreached_branch(statement):
    code = f"x = 1\nif False:\n    {statement}"
    with pytest.raises(SyntaxError):
        compile(code, "<test trace>", "exec")
    result = verify_contract(contract(code, 1))
    assert result["state"] == "failed"
    assert not result["passed"]


def test_public_french_admission_refuses_uncompilable_printed_trace():
    raw = raw_exercise()
    code = "x = 1\nif False:\n    return"
    raw["questions"][0].update(
        prompt=f"On exécute ce programme Python.\n```python\n{code}\n```\nDonner x.",
        answer="1",
        verification=contract(code, 1),
    )
    with pytest.raises(ValueError, match="Vérification générique échouée"):
        validate_authored_exercise(raw, "1")


def test_valid_unreached_runtime_error_is_not_executed():
    result = verify_contract(contract("x = 1\nif False:\n    x = 1 // 0", 1))
    assert result == {"state": "passed", "passed": True, "actual": 1}
