import re
from decimal import Decimal

import pytest

from Backend.Core.france.expression_stack import compile_tree, execute
from Backend.Core.france.expression_synthesis import build_case
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.postfix_exercise import render_case


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_allocated_marks_match_every_printed_criterion(total):
    exercise = NSIExercise.model_validate(render_case(713, total=total))
    assert exercise.credit == Decimal(total)
    assert exercise.target_points == total
    for question in exercise.questions:
        assert sum(Decimal(item.points) for item in question.marking) == Decimal(
            question.points
        )


@pytest.mark.parametrize("total", [6, "7", None, "6.0"])
def test_unsupported_mark_allocations_are_rejected(total):
    with pytest.raises(ValueError):
        render_case(713, total=total)


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
        # fixed app-owned reference solutions only, never model-authored code
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


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
@pytest.mark.parametrize("family", ["tree", "database", "system"])
def test_postfix_is_distinct_from_existing_whole_case_families(seed, family):
    from Backend.Core.france import (
        database_case_prose,
        system_case_prose,
        tree_case_prose,
    )
    from Backend.Core.france.originality import screen_originality
    from Backend.Core.france.pipeline import exercise_candidate_text

    module = {
        "tree": tree_case_prose,
        "database": database_case_prose,
        "system": system_case_prose,
    }[family]
    screen_originality(
        exercise_candidate_text(NSIExercise.model_validate(render_case(713))),
        [],
        previous_texts=[
            exercise_candidate_text(
                NSIExercise.model_validate(module.render_case(seed))
            )
        ],
    )


def test_evaluation_scaffold_fills_to_the_checked_program():
    raw = render_case(713)
    prompt = raw["questions"][7]["prompt"]
    listing = re.search(r"```python\n(.*?)\n```", prompt, re.S)
    assert listing is not None
    source = listing[1]
    for marker, value in {
        "__A__": "instruction",
        "__B__": "pile.pop()",
        "__C__": "gauche - droite",
        "__D__": "pile[0]",
    }.items():
        assert source.count(marker) == 1
        source = source.replace(marker, value)
    namespace = {}
    exec(compile(source, "<completed-app-owned-scaffold>", "exec"), namespace)
    for seed in range(30):
        case = build_case(seed)
        program = compile_tree(case["public"]["rows"], "n0")
        assert namespace["calculer"](program) == execute(program)["answer"]


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
