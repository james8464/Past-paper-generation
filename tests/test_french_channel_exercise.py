from decimal import Decimal


def test_channel_sequence_has_explicit_rules_and_complete_credit():
    from Backend.Core.france.channel_exercise import render_case
    from Backend.Core.france.nsi import NSIExercise

    exercise = NSIExercise.model_validate(render_case(270104))
    assert exercise.credit == Decimal("6")
    assert len(exercise.questions) == 12
    assert sum(question.estimated_minutes for question in exercise.questions) == 70
    assert "P, P, C, C, P, C, P, C" in exercise.context
    assert "__A__" in exercise.questions[5].prompt
    assert "attente" in exercise.questions[5].answer
    assert "ASR-CRYPTO" in exercise.questions[11].curriculum_codes
    assert "clé" in exercise.questions[10].answer
