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
        "target_points": "6",
        "questions": [
            dict(
                id=str(i),
                prompt=f"Déterminer la valeur du calcul {i}.",
                points="1",
                answer=str(i),
                marking=[{"points": "1", "criterion": f"Valeur {i} justifiée."}],
                curriculum_codes=["ASR-ROUTAGE"],
                operation=("apply", "analyse", "design", "debug", "justify", "analyse")[
                    i - 1
                ],
                difficulty=(2, 2, 3, 3, 4, 4)[i - 1],
                estimated_minutes=10,
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


def test_exercise_credit_must_match_its_explicit_blueprint_allocation():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    raw["target_points"] = "5.5"
    with pytest.raises(ValueError, match="allocation"):
        NSIExercise.model_validate(raw)


def test_language_rubric_is_officially_structured_but_numerically_indicative():
    from Backend.Core.france.nsi import LANGUAGE_RUBRIC_2027

    assert LANGUAGE_RUBRIC_2027["points"] == "2"
    assert LANGUAGE_RUBRIC_2027["allocation_status"] == "indicative_product_profile"
    assert set(LANGUAGE_RUBRIC_2027["dimensions"]) == {
        "orthographe",
        "syntaxe",
        "lexique",
        "organisation",
    }
    assert [band["id"] for band in LANGUAGE_RUBRIC_2027["bands"]] == [
        "tres_insuffisant",
        "insuffisant",
        "satisfaisant",
        "tres_satisfaisant",
    ]
    assert sum(
        Decimal(value) for value in LANGUAGE_RUBRIC_2027["indicative_points"].values()
    ) > Decimal("2")


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
            sqlite3,
            "connect",
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


def test_structured_graph_is_bound_to_question_and_deterministic_contract():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    raw["materials"] = [
        {
            "kind": "weighted_graph",
            "id": "reseau",
            "title": "Réseau du lycée",
            "nodes": ["A", "B", "C"],
            "edges": [["A", "B", 2], ["B", "C", 3], ["A", "C", 8]],
            "directed": True,
        }
    ]
    raw["questions"][0]["material_ids"] = ["reseau"]
    raw["questions"][0]["verification"] = {
        "kind": "shortest_path",
        "material_id": "reseau",
        "edges": [["A", "B", 2], ["B", "C", 3], ["A", "C", 8]],
        "directed": True,
        "start": "A",
        "end": "C",
        "expected": 5,
    }
    NSIExercise.model_validate(raw)
    raw["questions"][0]["verification"]["edges"][0][2] = 9
    with pytest.raises(ValueError, match="figure"):
        NSIExercise.model_validate(raw)


def test_app_owned_six_node_graph_renders_without_crossed_edges():
    from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
    from reportlab.lib.styles import ParagraphStyle

    from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
    from Backend.Core.france.nsi import NSIWeightedGraphMaterial
    from Backend.Core.france.rendering import structured_material

    graph = build_graph_tree_contract(270100, "1").to_dict()["graph"]
    material = NSIWeightedGraphMaterial.model_validate(
        {"kind": "weighted_graph", "title": "Réseau", **graph}
    )
    block = structured_material(
        material,
        body=ParagraphStyle("body"),
        bold_font="Helvetica-Bold",
        regular_font="Helvetica",
        available_width=440,
    )
    drawing = next(item for item in block._content if isinstance(item, Drawing))
    lines = [item for item in drawing.contents if isinstance(item, Line)]
    weight_backings = [item for item in drawing.contents if isinstance(item, Rect)]
    weight_labels = [item for item in drawing.contents if isinstance(item, String)][
        : len(material.edges)
    ]

    def crosses(first, second):
        def orient(ax, ay, bx, by, cx, cy):
            return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

        endpoints = ((first.x1, first.y1), (first.x2, first.y2))
        other = ((second.x1, second.y1), (second.x2, second.y2))
        if set(endpoints) & set(other):
            return False
        return (
            orient(*endpoints[0], *endpoints[1], *other[0])
            * orient(*endpoints[0], *endpoints[1], *other[1])
            < 0
            and orient(*other[0], *other[1], *endpoints[0])
            * orient(*other[0], *other[1], *endpoints[1])
            < 0
        )

    assert len(lines) == len(material.edges)
    assert len(weight_backings) == len(material.edges)
    assert all(
        backing.x <= label.x
        and label.x + label.getBounds()[2] - label.getBounds()[0]
        <= backing.x + backing.width
        and backing.y <= label.y <= backing.y + backing.height
        for backing, label in zip(weight_backings, weight_labels, strict=True)
    )
    assert not any(
        crosses(first, second)
        for index, first in enumerate(lines)
        for second in lines[index + 1 :]
    )

    other = material.model_copy(update={"id": "other_graph"})
    other_block = structured_material(
        other,
        body=ParagraphStyle("other"),
        bold_font="Helvetica-Bold",
        regular_font="Helvetica",
        available_width=440,
    )
    other_drawing = next(
        item for item in other_block._content if isinstance(item, Drawing)
    )
    first_node = next(
        item for item in other_drawing.contents if isinstance(item, Circle)
    )
    assert first_node.cy < other_drawing.height / 2


def test_structured_table_requires_rectangular_bounded_data():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    raw["materials"] = [
        {
            "kind": "table",
            "id": "mesures",
            "title": "Mesures relevées",
            "columns": ["id", "valeur"],
            "rows": [["1", "4"], ["2"]],
        }
    ]
    with pytest.raises(ValueError):
        NSIExercise.model_validate(raw)


def test_sql_relation_identifier_is_visible_and_optional_create_clause_is_valid():
    from reportlab.lib.styles import ParagraphStyle

    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import require_declared_relations
    from Backend.Core.france.rendering import structured_material

    raw = exercise()
    raw["materials"] = [
        {
            "kind": "table",
            "id": "technicien",
            "title": "Personnel de maintenance",
            "columns": ["id", "nom"],
            "rows": [["1", "Alice"], ["2", "Bob"]],
        }
    ]
    raw["questions"][0]["prompt"] = "Lire SELECT nom FROM technicien."
    raw["questions"][0]["material_ids"] = ["technicien"]
    raw["questions"][0]["verification"] = {
        "kind": "sql",
        "schema": "CREATE TABLE IF NOT EXISTS technicien (id INTEGER, nom TEXT);",
        "rows": {"technicien": [[1, "Alice"], [2, "Bob"]]},
        "query": "SELECT nom FROM technicien",
        "expected": [["Alice"], ["Bob"]],
    }
    parsed = NSIExercise.model_validate(raw)

    require_declared_relations(parsed)
    block = structured_material(
        parsed.materials[0],
        body=ParagraphStyle("body"),
        bold_font="Helvetica-Bold",
        regular_font="Helvetica",
        available_width=420,
    )
    assert "technicien" in block._content[0].text


def test_question_demand_is_bound_to_official_capabilities_and_time_budget():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    raw["minutes"] = 60
    operations = ["apply", "analyse", "design", "debug", "justify", "analyse"]
    difficulties = [2, 2, 3, 3, 4, 4]
    for index, question in enumerate(raw["questions"]):
        question["curriculum_codes"] = ["ASR-ROUTAGE"]
        question["operation"] = operations[index]
        question["difficulty"] = difficulties[index]
        question["estimated_minutes"] = 10
    parsed = NSIExercise.model_validate(raw)
    assert sum(question.estimated_minutes for question in parsed.questions) == 60

    raw["questions"][0]["curriculum_codes"] = ["BDD-SQL-MUTATION"]
    with pytest.raises(ValueError, match="programme"):
        NSIExercise.model_validate(raw)


def test_exercise_rejects_flat_low_demand_question_sets():
    from Backend.Core.france.nsi import NSIExercise

    raw = exercise()
    for question in raw["questions"]:
        question["curriculum_codes"] = ["ASR-ROUTAGE"]
        question["operation"] = "recall"
        question["difficulty"] = 1
        question["estimated_minutes"] = 10
    with pytest.raises(ValueError, match="demande cognitive"):
        NSIExercise.model_validate(raw)


def test_seeded_question_blueprints_make_marks_and_timing_exact_before_ai():
    from Backend.Core.france.pipeline import _tasks_for_seed

    for seed in range(3):
        for task in _tasks_for_seed(seed):
            questions = task["question_blueprint"]
            assert len(questions) == 6
            assert sum(Decimal(item["points"]) for item in questions) == Decimal(
                task["technical_points"]
            )
            assert (
                sum(item["estimated_minutes"] for item in questions) == task["minutes"]
            )
            assert set(task["required_curriculum_codes"]) <= {
                item["required_curriculum_code"] for item in questions
            }
            assert len({item["operation"] for item in questions}) >= 3
            assert sum(item["operation"] == "recall" for item in questions) <= 1
            assert any(item["difficulty"] == 4 for item in questions)


def test_question_intents_follow_coherent_parts_instead_of_rotating_codes():
    from Backend.Core.france.pipeline import _tasks_for_seed

    expected = (
        (
            "SD-GRAPHE",
            "SD-GRAPHE",
            "ALG-GRAPHES",
            "ALG-GRAPHES",
            "ALG-ARBRES",
            "ALG-ARBRES",
        ),
        (
            "BDD-ANOMALIES",
            "BDD-SQL-SELECT",
            "BDD-SQL-SELECT",
            "BDD-SQL-MUTATION",
            "LP-DEBUG",
            "LP-DEBUG",
        ),
        (
            "ASR-ROUTAGE",
            "ASR-ROUTAGE",
            "ASR-PROCESSUS",
            "ASR-PROCESSUS",
            "ASR-CRYPTO",
            "ASR-CRYPTO",
        ),
    )
    for seed in (270100, 270101, 270102):
        for task, codes in zip(_tasks_for_seed(seed), expected, strict=True):
            questions = task["question_blueprint"]
            assert tuple(q["required_curriculum_code"] for q in questions) == codes
            assert [q["part_id"] for q in questions] == ["A", "A", "B", "B", "C", "C"]
            assert all(q["goal"] and q["response_form"] for q in questions)
            assert task["scenario_brief"]
            assert set(task["required_curriculum_codes"]) == set(codes)
    assert (
        _tasks_for_seed(270100)[0]["scenario_brief"]
        != _tasks_for_seed(270101)[0]["scenario_brief"]
    )


def test_recorded_v6_blueprint_is_not_rewritten_by_new_archetypes():
    from Backend.Core.france.pipeline import _legacy_tasks_for_seed

    legacy = _legacy_tasks_for_seed(270100)
    assert (
        legacy[0]["question_blueprint"][0]["required_curriculum_code"] == "ALG-GRAPHES"
    )
    assert "scenario_brief" not in legacy[0]
