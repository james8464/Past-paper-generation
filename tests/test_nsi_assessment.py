from copy import deepcopy
from decimal import Decimal

import pytest


def exercise():
    return {
        "id": "1",
        "title": "Données d'un réseau",
        "context": "Un lycée modélise son réseau.",
        "topics": ["architectures-reseaux"],
        "minutes": 60,
        "questions": [
            dict(
                id=str(i),
                prompt=f"Déterminer la valeur du calcul {i}.",
                points="1",
                answer=str(i),
                marking=[{"points": "1", "criterion": f"Valeur {i} justifiée."}],
                verification={"kind": "binary", "input": format(i, "b"), "expected": i},
            )
            for i in range(1, 7)
        ],
    }


def test_exercise_credit_is_exact_and_duplicate_labels_rejected():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    parsed = NSIExercise.model_validate(raw)
    assert parsed.credit == Decimal("6")
    raw["questions"][1]["id"] = "1"
    with pytest.raises(ValueError, match="identifiants"):
        NSIExercise.model_validate(raw)


def test_marking_must_credit_each_question_exactly():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    raw["questions"][0]["marking"][0]["points"] = "0.5"
    with pytest.raises(ValueError, match="barème"):
        NSIExercise.model_validate(raw)


def test_deterministic_verifier_does_not_trust_expected_answer():
    from Backend.Core.france.verification import verify_contract

    assert verify_contract({"kind": "binary", "input": "1101", "expected": 13})[
        "passed"
    ]
    assert not verify_contract({"kind": "binary", "input": "1101", "expected": 12})[
        "passed"
    ]
    assert (
        verify_contract({"kind": "unsupported", "expected": 1})["state"] == "unresolved"
    )


@pytest.mark.parametrize("extension_api_available", [True, False])
def test_sql_verification_checks_results_and_disallows_external_access(
    monkeypatch, extension_api_available
):
    import sqlite3

    from Backend.Core.france.verification import verify_contract

    if not extension_api_available:
        connect = sqlite3.connect

        class ConnectionWithoutExtensions(sqlite3.Connection):
            def __getattribute__(self, name):
                if name == "enable_load_extension":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        monkeypatch.setattr(
            sqlite3, "connect",
            lambda *args, **kwargs: connect(
                *args, **kwargs, factory=ConnectionWithoutExtensions
            ),
        )

    base = {
        "kind": "sql",
        "schema": "CREATE TABLE eleve(id INTEGER, points INTEGER);",
        "rows": {"eleve": [[1, 4], [2, 7]]},
        "query": "SELECT id FROM eleve WHERE points > 5 ORDER BY id",
        "expected": [[2]],
    }
    assert verify_contract(base)["passed"]
    wrong = deepcopy(base)
    wrong["expected"] = [[1]]
    assert not verify_contract(wrong)["passed"]
    for query in (
        "ATTACH DATABASE '/tmp/leak' AS other",
        "SELECT load_extension('/tmp/x')",
    ):
        bad = deepcopy(base)
        bad["query"] = query
        assert not verify_contract(bad)["passed"]


def test_python_trace_has_no_imports_file_access_or_unbounded_loops():
    from Backend.Core.france.verification import verify_contract

    assert verify_contract(
        {
            "kind": "python_trace",
            "code": "s = 0\nfor n in range(4):\n    s = s + n",
            "variable": "s",
            "expected": 6,
        }
    )["passed"]
    for code in (
        "import os",
        "x = open('/tmp/file')",
        "while True:\n    pass",
        "x = 2 ** 999999999",
    ):
        result = verify_contract(
            {"kind": "python_trace", "code": code, "variable": "x", "expected": 0}
        )
        assert not result["passed"]


def test_shortest_path_checks_real_graph_and_missing_nodes():
    from Backend.Core.france.verification import verify_contract

    raw = {
        "kind": "shortest_path",
        "edges": [["a", "b", 2], ["b", "c", 3], ["a", "c", 8]],
        "start": "a",
        "end": "c",
        "expected": 5,
    }
    assert verify_contract(raw)["passed"]
    raw["end"] = "z"
    assert not verify_contract(raw)["passed"]


def test_solver_prompt_does_not_leak_solution_or_marking():
    from Backend.Core.france.nsi import NSIExercise, solver_prompt

    raw = exercise()
    raw["questions"][0]["answer"] = "SOLUTION_SECRET"
    raw["questions"][0]["marking"][0]["criterion"] = "MARKING_SECRET"
    prompt = solver_prompt(NSIExercise.model_validate(raw))
    assert "SOLUTION_SECRET" not in prompt and "MARKING_SECRET" not in prompt
    assert '"expected"' not in prompt
    assert "Un lycée" in prompt
