from __future__ import annotations

from Backend.Core.subject_plugins import discover_subject_plugin
from Backend.Core.subjects.computer_science import (
    ComputerSciencePlugin,
    normalise_pseudocode,
    pseudocode_equivalent,
    truth_table,
)


def test_computer_science_uses_the_specialised_plugin() -> None:
    assert isinstance(discover_subject_plugin("computer-science"), ComputerSciencePlugin)


def test_pseudocode_normalisation_preserves_tokens_not_formatting() -> None:
    left = "IF Score >= 50 THEN\n  Result ← 'PASS'\nENDIF"
    right = "if score>=50 then result = 'PASS' endif"

    assert normalise_pseudocode(left) == normalise_pseudocode(right)
    assert pseudocode_equivalent(left, right) is True
    assert pseudocode_equivalent(left, right.replace("50", "60")) is False


def test_truth_table_is_recomputed_from_the_expression() -> None:
    rows = truth_table("(A AND NOT B) OR C", variables=("A", "B", "C"))

    assert len(rows) == 8
    assert rows[0] == {"A": False, "B": False, "C": False, "result": False}
    assert rows[-1] == {"A": True, "B": True, "C": True, "result": True}


def test_truth_table_accepts_aqa_symbols_for_all_six_boolean_operations() -> None:
    expressions = {
        "A · B": (False, False),
        "A + B": (False, True),
        "¬A": (True, True),
        "A ⊕ B": (False, True),
        "A ⊼ B": (True, True),
        "A ⊽ B": (True, False),
    }

    for expression, expected in expressions.items():
        rows = truth_table(expression, variables=("A", "B"))
        observed = (rows[0]["result"], rows[1]["result"])
        assert observed == expected

    overbar_rows = truth_table("A̅ + B", variables=("A", "B"))
    assert overbar_rows[0]["result"] is True


def test_programming_paper_accepts_only_declared_languages_and_evidence() -> None:
    plugin = ComputerSciencePlugin()
    invalid = plugin.validate_item(
        {
            "question": "Implement the program.",
            "marks": 12,
            "item_kind": "practical-programming",
            "language": "JavaScript",
            "answer": "program listing",
        }
    )
    valid = plugin.validate_item(
        {
            "question": "Implement the program.",
            "marks": 12,
            "item_kind": "practical-programming",
            "language": "Python",
            "answer": "program listing",
            "test_evidence": ["normal", "boundary", "invalid"],
        }
    )

    assert invalid.passed is False
    assert valid.passed is True
