# Complete E1 case demand, rubric alignment and closed-content integrity.

from copy import deepcopy
from decimal import Decimal

import pytest


def test_french_prose_spacing_escapes_markup_without_changing_newlines():
    from Backend.Core.france.rendering import french_prose_markup

    assert french_prose_markup("« a < b » : oui !\nPourquoi ?") == (
        "«\u00a0a &lt; b\u00a0»\u00a0: oui\u00a0!<br/>Pourquoi\u00a0?"
    )
    assert french_prose_markup('x = "a&b";\ny = 2') == 'x = "a&amp;b";<br/>y = 2'


def test_rank_debugging_source_and_marking_agree_on_actual_trace():
    import re

    from Backend.Core.france.tree_case_families import build_case, count_below
    from Backend.Core.france.tree_case_prose import render_case

    case = build_case(270100)
    nodes = {row[0]: tuple(row[1:]) for row in case["public"]["rows"]}
    question = render_case(270100)["questions"][5]
    source = re.search(r"```python\n(.*?)\n```", question["prompt"], re.S)
    assert source, "The candidate must inspect the actual faulty program"
    namespace = {}
    # Fixed app-owned teaching code only, never model output.
    exec(compile(source[1], "<app-owned-faulty-count>", "exec"), namespace)
    visited = []

    class TracedNodes(dict):
        def __getitem__(self, key):
            visited.append(key)
            return super().__getitem__(key)

    before = deepcopy(nodes)
    assert namespace["compte_errone"](TracedNodes(nodes), "r", 70) == 3
    assert visited == ["r", "a", "c"]
    assert namespace["compte_errone"]({}, None, 70) == 0
    assert count_below(nodes, "r", 70) == 5
    assert "renvoie 3" in question["answer"]
    assert "d (35)" in question["answer"] and "e (55)" in question["answer"]
    assert nodes == before


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("total", ("5.5", "6", "6.5"))
def test_case_balances_credit_time_and_has_constructed_reasoning(seed, total):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.tree_case_prose import render_case, verify_candidate

    raw = render_case(seed, total=total)
    exercise = NSIExercise.model_validate(raw)
    assert exercise.credit == Decimal(total)
    assert exercise.minutes == 70
    assert len(exercise.materials) == 2
    state_index = 4 if seed == 270101 else 7
    assert "tree_states" in exercise.questions[state_index].material_ids
    assert all(
        "tree_states" not in q.material_ids for q in exercise.questions[:state_index]
    )
    assert [q.id for q in exercise.questions] == [f"1{c}" for c in "abcdefghij"]
    assert exercise.questions[6].operation == "design"
    assert len(exercise.questions[6].marking) == 4
    assert exercise.questions[8].operation == "design"
    assert verify_candidate(raw, seed, total=total)
    for field in ("prompt", "answer", "points"):
        changed = deepcopy(raw)
        changed["questions"][6][field] = "changed"
        assert not verify_candidate(changed, seed, total=total)
    assert all(
        not {"answer", "marking", "verification"} & set(q)
        for q in exercise.candidate_view()["questions"]
    )


def test_three_whole_cases_pass_originality_with_history_intact():
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _originality, exercise_candidate_text
    from Backend.Core.france.tree_case_prose import render_case

    history = []
    for seed in range(270100, 270103):
        exercise = NSIExercise.model_validate(render_case(seed))
        _originality(exercise, [], history)
        history.append(exercise_candidate_text(exercise))
    assert len(history) == 3


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_printed_algorithm_solutions_execute_against_case_truth(seed):
    import re

    from Backend.Core.france.tree_case_families import build_case
    from Backend.Core.france.tree_case_prose import render_case

    case, raw = build_case(seed), render_case(seed)
    nodes = {r[0]: tuple(r[1:]) for r in case["public"]["rows"]}
    before = deepcopy(nodes)
    namespace = {}
    for index in (6, 8):
        source = re.search(
            r"```python\n(.*?)\n```", raw["questions"][index]["answer"], re.S
        )[1]
        # Only fixed application-owned correction code, never model output.
        exec(compile(source, "<application-tree-solution>", "exec"), namespace)
    if case["family"] == "rank":
        assert namespace["count_below"](nodes, "r", case["public"]["limit"]) == 5
        bounds = case["expected"]["states"][0]["interval_bounds"]
        assert (
            namespace["count_interval"](nodes, "r", *bounds)
            == case["expected"]["states"][0]["interval_count"]
        )
    elif case["family"] == "expression":
        assert namespace["expression_value"](nodes, "r") == 25
        revised = deepcopy(nodes)
        revised["b"] = (7, None, None)
        assert namespace["variation"](nodes, revised, "r") == -9
        revised["m"] = ("-", "d", "e")
        assert namespace["variation"](nodes, revised, "r") == -22
    else:
        bits = case["public"]["bits"]
        assert namespace["decode_message"](nodes, "r", bits) == "ABCD"
        assert (
            namespace["transcode"](
                nodes, "r", bits, {"A": "0", "B": "111", "C": "110", "D": "10"}
            )
            == case["public"]["recoded_bits"]
        )
    assert nodes == before


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("large_print", (False, True))
def test_tree_case_pdf_keeps_prompts_and_marking_legible(tmp_path, seed, large_print):
    import re

    import pymupdf

    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.tree_case_prose import render_case

    exercise = NSIExercise.model_validate(render_case(seed))
    for correction in (False, True):
        path = tmp_path / f"e1-{seed}-{large_print}-{correction}.pdf"
        render_assessment(
            path,
            [exercise],
            correction=correction,
            large_print=large_print,
            coherent_material_flow=True,
        )
        with pymupdf.open(path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)
            if not correction:
                assert "Rédigez vos réponses sur votre copie." in pdf[0].get_text()
                assert (
                    "Recopiez et complétez les tableaux demandés." in pdf[0].get_text()
                )
            assert "tree_nodes" not in text and "tree_states" not in text
            assert ("def " in text) is (correction or seed == 270100)
            assert "```" not in text
            assert not any(
                line.strip() in {"?", "!", ";", ":", "»"} for line in text.splitlines()
            ), "French punctuation must stay attached to the preceding word"
            for page in pdf:
                for x0, y0, x1, y1, *_ in page.get_text("words"):
                    assert 0 <= x0 < x1 <= page.rect.width
                    assert 0 <= y0 < y1 <= page.rect.height
            if not large_print:
                for q in exercise.questions:
                    if correction:
                        assert any(
                            f"Réponse attendue — question {q.id}" in p.get_text()
                            and f"Barème indicatif — question {q.id}" in p.get_text()
                            for p in pdf
                        )
                    else:
                        visible = re.sub(r"```(?:python|sql)?", "", q.prompt)
                        compact = re.sub(r"\s+", "", visible)
                        assert any(
                            compact in re.sub(r"\s+", "", p.get_text()) for p in pdf
                        )
