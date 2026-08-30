import random

import pytest
from cspapergen.generator import build_paper1_blueprint
from cspapergen.ollama_client import _part_solver_item
from cspapergen.question_bank import QUESTION_STYLES, build_question
from cspapergen.syllabus import load_syllabus

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution


def solve(question, part, answers):
    class Client:
        def generate_json(self, _prompt):
            return {"answer": answers, "mark_points": answers}

    return IndependentSolver(Client()).solve(_part_solver_item(question, part), [])


@pytest.mark.parametrize(
    "style_id,part_index,answers",
    [
        (
            "data_structures_stack_queue",
            0,
            {"bottom-1": "53", "bottom-2": "62", "bottom-3": "18"},
        ),
        (
            "data_structures_stack_queue",
            1,
            {
                "removed-1": "53",
                "removed-2": "31",
                "removed-3": "62",
                "removed-4": "18",
            },
        ),
        ("data_structures_hash", 0, {"key-4": "4", "key-15": "5", "key-26": "6"}),
        (
            "data_structures_tree",
            0,
            {
                "node-50-parent": "none",
                "node-50-side": "root",
                "node-30-parent": "50",
                "node-30-side": "left",
                "node-70-parent": "50",
                "node-70-side": "right",
                "node-20-parent": "30",
                "node-20-side": "left",
                "node-40-parent": "30",
                "node-40-side": "right",
                "node-60-parent": "70",
                "node-60-side": "left",
            },
        ),
        (
            "data_structures_tree",
            1,
            {
                "visit-1": "20",
                "visit-2": "30",
                "visit-3": "40",
                "visit-4": "50",
                "visit-5": "60",
                "visit-6": "70",
            },
        ),
        (
            "data_structures_graph",
            0,
            {f"visit-{n}": v for n, v in enumerate("ABCDEF", 1)},
        ),
        (
            "data_structures_graph",
            1,
            {"route-1": "A", "route-2": "C", "route-3": "F", "edges": "2"},
        ),
        (
            "functional_programming",
            0,
            {"output-1": "16", "output-2": "36", "output-3": "25"},
        ),
        ("functional_recursion", 1, {"result": "15"}),
        ("erd_keys", 0, {"cardinality": "one-to-many"}),
        ("fibonacci_recursion", 1, {"result": "8"}),
        ("floating_point", 0, {"direction": "right"}),
        ("floating_point", 2, {"normalised": "yes", "leading-mantissa-bits": "10"}),
        ("floating_point", 5, {"error": "underflow"}),
        ("binary_arithmetic_short", 0, {"8-bit-result": "01111111"}),
    ],
)
def test_finite_outputs_are_keyed_and_reject_a_changed_value(
    style_id, part_index, answers
):
    style = next(style for style in QUESTION_STYLES if style.id == style_id)
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[part_index]
    assert set(part.response_slots) == set(answers)
    assert reconcile_solution(
        solve(question, part, answers), part.marking.model_dump()
    ).passed
    wrong = {**answers, next(iter(answers)): "wrong"}
    assert not reconcile_solution(
        solve(question, part, wrong), part.marking.model_dump()
    ).passed


@pytest.mark.parametrize(
    "question_index,part_index,answers",
    [
        (0, 7, {"passes": "79"}),
        (5, 0, {"S2-input-0": "S1", "S2-input-1": "S2"}),
        (5, 4, {"answer": "no"}),
        (4, 0, {"first-call-n": "4", "second-call-n": "3"}),
        (
            2,
            4,
            {
                "called-current-vertices-in-order": "3,2,1,4,5,6",
                "visited-additions-in-order": "3,2,1,4,5",
                "result": "True",
            },
        ),
    ],
)
def test_paper1_finite_outputs_are_checked_exhaustively(
    question_index, part_index, answers
):
    paper, _ = build_paper1_blueprint(load_syllabus(), seed=7)
    question = paper.questions[question_index]
    part = question.parts[part_index]
    assert set(part.response_slots) == set(answers)
    assert reconcile_solution(
        solve(question, part, answers), part.marking.model_dump()
    ).passed
    with pytest.raises(ValueError, match="every slot"):
        solve(question, part, dict(list(answers.items())[1:]))


def test_paper1_matrix_keys_do_not_reveal_which_cells_contain_one():
    paper, _ = build_paper1_blueprint(load_syllabus(), seed=7)
    question = paper.questions[2]
    part = question.parts[2]
    rows = ["010100", "101010", "010001", "100010", "010101", "001010"]
    answers = {
        f"r{r}c{c}": value
        for r, row in enumerate(rows, 1)
        for c, value in enumerate(row, 1)
    }
    assert set(part.response_slots) == set(answers)
    assert reconcile_solution(
        solve(question, part, answers), part.marking.model_dump()
    ).passed
    assert not reconcile_solution(
        solve(question, part, {**answers, "r1c2": "0"}), part.marking.model_dump()
    ).passed


def test_truth_input_combination_preserves_all_valid_rows_without_mixing_them():
    style = next(s for s in QUESTION_STYLES if s.id == "truth_table_completion")
    question = build_question(style, 1, 7, random.Random(5))
    part = question.parts[1]
    assert part.response_slots == ["A,B,C"]
    for value in ("0,1,1", "1,0,1", "A=0, B=1, C=1", "[1, 0, 1]"):
        assert reconcile_solution(
            solve(question, part, {"A,B,C": value}), part.marking.model_dump()
        ).passed
    for value in ("0,0,1", "1,1,1"):
        assert not reconcile_solution(
            solve(question, part, {"A,B,C": value}), part.marking.model_dump()
        ).passed


def test_full_truth_table_requires_every_input_combination():
    style = next(s for s in QUESTION_STYLES if s.id == "logic_truth_table")
    question = build_question(style, 1, 8, random.Random(7))
    part = question.parts[1]
    # Seed 7 chooses (A XOR B) AND C.
    answers = dict(
        zip(
            ["000", "001", "010", "011", "100", "101", "110", "111"],
            "00010100",
            strict=True,
        )
    )
    assert part.response_slots == list(answers)
    assert reconcile_solution(
        solve(question, part, answers), part.marking.model_dump()
    ).passed
    assert not reconcile_solution(
        solve(question, part, {**answers, "011": "0"}), part.marking.model_dump()
    ).passed


def test_assembly_trace_checks_every_register_series_and_stored_value():
    style = next(s for s in QUESTION_STYLES if s.id == "assembly_trace")
    question = build_question(style, 1, 11, random.Random(7))
    part = question.parts[0]
    answers = {
        "R0-initial-and-after-loops": "0,1,2,3,4",
        "R1-initial-and-after-loops": "13,6,3,1,0",
        "R2-initial-and-after-loops": "0,1,1,2,3",
        "R3-after-loops": "1,0,1,1",
        "memory-120": "3",
    }
    assert part.response_slots == list(answers)
    assert reconcile_solution(
        solve(question, part, answers), part.marking.model_dump()
    ).passed
    assert not reconcile_solution(
        solve(question, part, {**answers, "R3-after-loops": "0,0,1,1"}),
        part.marking.model_dump(),
    ).passed
