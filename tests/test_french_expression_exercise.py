# Synthesized cases must produce complete, bound questions, not data alone.

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.expression_exercise import render_case, verify_candidate
from Backend.Core.france.expression_synthesis import build_case
from Backend.Core.france.nsi import NSIExercise


def test_trace_rubric_accepts_either_child_evaluation_order():
    question = render_case(713)["questions"][7]
    assert "autre ordre" in question["answer"]
    assert "fonction proposée" in question["marking"][0]["criterion"]


def test_construction_explicitly_requires_the_assessed_recursion():
    question = render_case(713)["questions"][6]
    assert "fonction récursive" in question["prompt"]


@pytest.mark.parametrize("seed", [0, 1, 27, 270103])
def test_new_tree_data_does_not_claim_original_question_variety(seed):
    from Backend.Core.france.originality import screen_originality
    from Backend.Core.france.pipeline import exercise_candidate_text

    previous = exercise_candidate_text(NSIExercise.model_validate(render_case(713)))
    candidate = exercise_candidate_text(NSIExercise.model_validate(render_case(seed)))
    assert build_case(seed)["sha256"] != build_case(713)["sha256"]
    # Different checked data is not evidence of a different reasoning task.
    # Keep this experimental exercise behind the production originality gate.
    with pytest.raises(ValueError, match="génération précédente"):
        screen_originality(candidate, [], previous_texts=[previous])


@pytest.mark.parametrize("seed", [0, 1, 27, 713, -42, 270103])
@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_complete_exercise_is_bound_to_synthesized_case(seed, total):
    raw = render_case(seed, total=total)
    exercise = NSIExercise.model_validate(raw)
    case = build_case(seed)
    assert exercise.credit == Decimal(total)
    assert exercise.minutes == 70
    assert len(exercise.questions) == 10
    assert verify_candidate(raw, seed, total=total)
    assert all(
        q.verification["case_sha256"] == case["sha256"] for q in exercise.questions
    )
    assert "```python" in exercise.questions[3].prompt
    assert "def combine_erronee(" in exercise.questions[3].prompt
    assert "valeur_erronee(nodes" not in exercise.questions[3].prompt
    for field in ["prompt", "answer", "marking", "verification"]:
        changed = deepcopy(raw)
        changed["questions"][4][field] = "forged"
        assert not verify_candidate(changed, seed, total=total)
    assert all(
        not {"answer", "marking", "verification"} & q.keys()
        for q in exercise.candidate_view()["questions"]
    )


def test_printed_debug_program_reproduces_the_stated_fault():
    import re

    for seed in range(30):
        case = build_case(seed)
        raw = render_case(seed)
        source = re.search(
            r"```python\n(.*?)\n```", raw["questions"][3]["prompt"], re.S
        )[1]
        namespace = {}
        # Fixed app-owned listing only; never run model-authored source.
        exec(compile(source, "<expression-debug-listing>", "exec"), namespace)
        nodes = {row[0]: tuple(row[1:]) for row in case["public"]["rows"]}
        before = deepcopy(nodes)
        values = {}
        for node in case["expected"]["states"][0]["postorder"]:
            value, left, right = nodes[node]
            values[node] = (
                value
                if left is None
                else namespace["combine_erronee"](value, values[left], values[right])
            )
        assert values == case["expected"]["reversed_subtraction"]["values"]
        assert nodes == before


@pytest.mark.parametrize("total", [6, "7", None])
def test_rejects_unsupported_mark_allocation(total):
    with pytest.raises(ValueError):
        render_case(1, total=total)


def test_printed_correct_helpers_match_every_generated_state():
    import re

    for seed in range(30):
        case = build_case(seed)
        raw = render_case(seed)
        namespace = {}
        for index in (6, 8):
            source = re.search(
                r"```python\n(.*?)\n```", raw["questions"][index]["answer"], re.S
            )[1]
            exec(compile(source, "<app-owned-expression-solution>", "exec"), namespace)
        original = {row[0]: tuple(row[1:]) for row in case["public"]["rows"]}
        current = deepcopy(original)
        for index, state in enumerate(case["expected"]["states"]):
            if index:
                change = case["public"]["changes"][index - 1]
                current[change["node"]] = (
                    change["value"],
                    *current[change["node"]][1:],
                )
            before = deepcopy(current)
            assert namespace["expression_value"](current, "n0") == state["answer"]
            assert (
                namespace["variation"](original, current, "n0")
                == state["answer"] - case["expected"]["states"][0]["answer"]
            )
            assert current == before


@pytest.mark.parametrize("seed", [0, 713])
def test_synthesized_correction_keeps_prompt_answer_and_state_table(tmp_path, seed):
    import pymupdf

    from Backend.Core.france.rendering import render_assessment

    exercise = NSIExercise.model_validate(render_case(seed))
    path = tmp_path / "correction.pdf"
    render_assessment(
        path,
        [exercise],
        correction=True,
        human_readable_graph_titles=True,
        coherent_material_flow=True,
    )
    with pymupdf.open(path) as pdf:
        for question in exercise.questions:
            prompt = [p.number for p in pdf if p.search_for(f"{question.id}.")]
            answer = [
                p.number
                for p in pdf
                if p.search_for(f"Réponse attendue — question {question.id}")
            ]
            assert len(prompt) == 1
            assert answer == prompt
        table_pages = [
            p.number
            for p in pdf
            if p.search_for("Tableau de travail pour la question 1e")
        ]
        question_pages = [p.number for p in pdf if p.search_for("1e.")]
        assert table_pages == question_pages


def test_correction_draws_every_tree_branch_with_left_right_orientation():
    import re

    from Backend.Core.france.expression_exercise import render_case
    from Backend.Core.france.expression_synthesis import build_case

    for seed in range(100):
        rows = {row[0]: row[1:] for row in build_case(seed)["public"]["rows"]}
        answer = render_case(seed)["questions"][0]["answer"]
        drawing = answer.split("```\n")[1].split("```")[0]
        lines = drawing.rstrip().splitlines()
        assert lines[0] == f"n0 ({rows['n0'][0]})"
        stack = ["n0"]
        seen = {"n0"}
        for line in lines[1:]:
            match = re.fullmatch(
                r"((?:\|   |    )*)\+-- ([GD]): (n\d+) \((-?\d+|[+*-])\)", line
            )
            assert match, line
            depth = len(match[1]) // 4 + 1
            branch, node, value = match[2], match[3], match[4]
            parent = stack[depth - 1]
            assert rows[parent][1 if branch == "G" else 2] == node
            assert str(rows[node][0]) == value
            assert node not in seen
            seen.add(node)
            stack[depth:] = [node]
        assert seen == set(rows)
