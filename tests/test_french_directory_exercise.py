from decimal import Decimal


def test_original_directory_sequence_has_complete_credit_and_visible_sources():
    from Backend.Core.france.directory_exercise import render_case
    from Backend.Core.france.nsi import NSIExercise

    exercise = NSIExercise.model_validate(render_case(270104))
    assert exercise.id == "1"
    assert exercise.credit == Decimal("6")
    assert len(exercise.questions) == 12
    assert sum(question.estimated_minutes for question in exercise.questions) == 70
    assert {material.kind for material in exercise.materials} == {
        "table",
        "weighted_graph",
    }
    assert {"SD-POO", "SD-GRAPHE", "ALG-GRAPHES", "LP-RECURSIVITE"} <= {
        code for question in exercise.questions for code in question.curriculum_codes
    }
    assert "r, a, c, d, b" in exercise.questions[6].answer
    assert "None" in exercise.questions[8].answer
    assert "identifiant" in exercise.questions[7].answer
    assert "attente" in exercise.questions[9].prompt
    assert "```python" in exercise.questions[9].answer


def test_distance_counterexample_names_visit_order_without_an_ambiguous_index():
    from Backend.Core.france.directory_exercise import render_case

    answer = render_case(270104)["questions"][8]["answer"]
    assert "cinquième identifiant ajouté" in answer
    assert "chemin d'un arc" in answer
    assert "position de b dans vus vaut 4" not in answer


def test_every_question_has_explicit_tested_case_identity():
    from Backend.Core.france.directory_exercise import render_case

    first, second = render_case(270104), render_case(270104)
    assert first == second
    assert all(
        question["verification"]["seed"] == 270104 for question in first["questions"]
    )
    assert all(
        len(question["verification"]["case_sha256"]) == 64
        for question in first["questions"]
    )
