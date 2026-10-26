import re
from decimal import Decimal

import pytest

from Backend.Core.france.expression_stack import compile_tree, execute
from Backend.Core.france.expression_synthesis import build_case
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.postfix_exercise import render_case


@pytest.mark.parametrize("seed", [0, 1, 27, 713, 270103])
def test_complete_postfix_exercise_and_printed_algorithms(seed):
    raw = render_case(seed)
    exercise = NSIExercise.model_validate(raw)
    assert exercise.credit == Decimal("6")
    assert len(exercise.questions) == 10
    case = build_case(seed)
    rows = case["public"]["rows"]
    nodes = {r[0]: r[1:] for r in rows}
    program = compile_tree(rows, "n0")
    namespace = {}
    for index in (6, 7, 8):
        source = re.search(
            r"```python\n(.*?)\n```", raw["questions"][index]["answer"], re.S
        )[1]
        # Fixed app-owned reference solutions only, never model-authored code.
        exec(compile(source, "<postfix-reference>", "exec"), namespace)
    assert namespace["compiler"](nodes, "n0") == program
    assert namespace["calculer"](program) == execute(program)["answer"]
    assert namespace["valide"](program)
    for invalid in ([], ["+"], [1, 2], [1, "*"], ["unknown"], [True]):
        assert not namespace["valide"](invalid)


def test_stack_exercise_differs_from_recursive_evaluation():
    from Backend.Core.france.expression_exercise import render_case as recursive
    from Backend.Core.france.originality import screen_originality
    from Backend.Core.france.pipeline import exercise_candidate_text

    result = screen_originality(
        exercise_candidate_text(NSIExercise.model_validate(render_case(713))),
        [],
        previous_texts=[
            exercise_candidate_text(NSIExercise.model_validate(recursive(713)))
        ],
    )
    assert result["state"] == "passed_calibrated_screen"


def test_correction_keeps_each_prompt_with_its_answer(tmp_path):
    import pymupdf

    from Backend.Core.france.rendering import render_assessment

    exercise = NSIExercise.model_validate(render_case(713))
    output = tmp_path / "postfix.pdf"
    render_assessment(output, [exercise], correction=True, coherent_material_flow=True)
    with pymupdf.open(output) as pdf:
        for question in exercise.questions:
            prompts = [p.number for p in pdf if p.search_for(f"{question.id}.")]
            answers = [
                p.number
                for p in pdf
                if p.search_for(f"Réponse attendue — question {question.id}")
            ]
            assert len(prompts) == 1
            assert prompts == answers
