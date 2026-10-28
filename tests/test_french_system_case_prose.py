# Whole E3 sequences: distinct reasoning, aligned credits and bound facts

from copy import deepcopy
from decimal import Decimal

import pytest


def test_routing_debug_prompt_does_not_claim_a_numerical_difference():
    from Backend.Core.france.system_case_prose import render_case

    question = render_case(270100)["questions"][4]
    assert question["id"] == "3e"
    assert "l'égalité de ces deux nombres" in question["prompt"]
    assert "valeur de A effectivement lue" in question["prompt"]
    assert "B reste 3" in question["answer"]
    assert "A=2" in question["answer"] and "A=4" in question["answer"]


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("total", ("5.5", "6", "6.5"))
def test_e3_whole_case_balances_credit_and_requires_construction(seed, total):
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.system_case_prose import render_case, verify_candidate

    raw = render_case(seed, total=total)
    exercise = NSIExercise.model_validate(raw)
    assert exercise.credit == Decimal(total)
    assert exercise.minutes == 70
    assert [q.id for q in exercise.questions] == [f"3{c}" for c in "abcdefghijkl"]
    assert exercise.questions[3].operation == "design"
    assert len(exercise.questions[3].marking) == 4
    assert verify_candidate(raw, seed, total=total)
    for field in ("prompt", "answer", "points"):
        altered = deepcopy(raw)
        altered["questions"][3][field] = "changed"
        assert not verify_candidate(altered, seed, total=total)
    assert all(
        not {"answer", "marking", "verification"} & q.keys()
        for q in exercise.candidate_view()["questions"]
    )


def test_whole_e3_sequences_pass_originality_without_relaxing_history():
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.pipeline import _originality, exercise_candidate_text
    from Backend.Core.france.system_case_prose import render_case

    history = []
    for seed in range(270100, 270103):
        exercise = NSIExercise.model_validate(render_case(seed))
        _originality(exercise, [], history)
        history.append(exercise_candidate_text(exercise))


def test_lock_deadline_explicitly_accepts_arrival_at_the_boundary():
    from Backend.Core.france.system_case_prose import render_case

    question = render_case(270101)["questions"][7]
    assert question["id"] == "3h"
    assert "t=11 inclus" in question["prompt"]
    assert "une arrivée à 11" in question["answer"]
    assert "réduction minimale : une minute" in question["answer"]


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_printed_system_algorithm_runs_and_preserves_inputs(seed):
    import re

    from Backend.Core.france.system_case_families import build_case
    from Backend.Core.france.system_case_prose import render_case

    case = build_case(seed)
    answer = render_case(seed)["questions"][3]["answer"]
    code = re.search(r"```python\n(.*?)\n```", answer, re.S)[1]
    namespace = {}
    # fixed application-owned correction only, never model-supplied code
    exec(compile(code, "<application-system-solution>", "exec"), namespace)
    public = deepcopy(case["public"])
    if case["family"] == "routing":
        adjacency = {n: [] for n in public["initial"]}
        for a, b, cost in public["links"]:
            if [a, b] != public["failed_link"]:
                adjacency[a].append((b, cost))
                adjacency[b].append((a, cost))
        assert (
            namespace["tour"](adjacency, public["initial"], "D")
            == case["expected"]["states"][1]["distances"]
        )
    elif case["family"] == "locks":
        assert namespace["cycle_depuis"]("R", public["owners"], public["waiting"]) == [
            "P",
            "Q",
        ]
        assert namespace["cycle_depuis"]("T", public["owners"], public["waiting"]) == []
    else:
        assert namespace["reassembler"](public["events"]) == ["A", "B", "C", "D"]
    assert public == case["public"]


def test_correction_helpers_match_independent_foundation_checks():
    from itertools import permutations
    from random import Random

    from Backend.Core.france.system_case_families import (
        _cycle_oracle,
        _delivery_oracle,
        _walk_oracle,
    )
    from Backend.Core.france.system_case_prose import cycle_depuis, reassembler, tour

    random = Random(713)
    for _ in range(100):
        links = [
            [a, b, random.randint(1, 5)]
            for i, a in enumerate("ABCD")
            for b in "ABCD"[i + 1 :]
            if random.random() < 0.5
        ]
        previous = {n: random.choice([None, 1, 5]) for n in "ABCD"}
        previous["D"] = 0
        adjacency = {n: [] for n in previous}
        for a, b, cost in links:
            adjacency[a].append((b, cost))
            adjacency[b].append((a, cost))
        assert tour(adjacency, previous, "D") == _walk_oracle(links, previous, "D", 1)
        owners = {f"r{i}": p for i, p in enumerate("ABCD")}
        waits = {
            p: random.choice([*owners, "free"]) for p in "ABCD" if random.random() < 0.8
        }
        found = {p for start in "ABCD" for p in cycle_depuis(start, owners, waits)}
        assert sorted(found) == _cycle_oracle(owners, waits)
    for order in permutations(range(1, 5)):
        events = [[i, n, str(n)] for i, n in enumerate(order)]
        events.append([4, order[0], str(order[0])])
        assert reassembler(events) == [
            v for s in _delivery_oracle(events) for v in s["emitted"]
        ]
    assert reassembler([]) == []
    assert reassembler([[0, 2, "B"]]) == []


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("large_print", (False, True))
def test_system_pdf_keeps_questions_and_credit_readable(tmp_path, seed, large_print):
    import re

    import pymupdf

    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment
    from Backend.Core.france.system_case_prose import render_case

    exercise = NSIExercise.model_validate(render_case(seed))
    for correction in (False, True):
        path = tmp_path / f"e3-{seed}-{large_print}-{correction}.pdf"
        render_assessment(
            path,
            [exercise],
            correction=correction,
            large_print=large_print,
            coherent_material_flow=True,
        )
        with pymupdf.open(path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)
            assert "system_source" not in text and "system_states" not in text
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
                        compact = re.sub(r"\s+", "", q.prompt)
                        assert any(
                            compact in re.sub(r"\s+", "", p.get_text()) for p in pdf
                        )
