from decimal import Decimal


def test_allocation_sequence_retains_sql_rows_and_complete_credit():
    from Backend.Core.france.allocation_exercise import render_case
    from Backend.Core.france.nsi import NSIExercise

    exercise = NSIExercise.model_validate(render_case(270104))
    assert exercise.credit == Decimal("6")
    assert len(exercise.questions) == 12
    assert sum(question.estimated_minutes for question in exercise.questions) == 70
    assert len(exercise.materials) == 3
    assert "(10, 1), (10, 2), (11, 1), (12, 3)" in exercise.questions[5].answer
    assert "[(10, 2), (11, 1), (12, 3)]" in exercise.questions[7].answer
    assert "__A__" in exercise.questions[7].prompt
    assert "0" in exercise.questions[10].answer
    assert "BDD-SQL-SELECT" in {
        code for question in exercise.questions for code in question.curriculum_codes
    }
