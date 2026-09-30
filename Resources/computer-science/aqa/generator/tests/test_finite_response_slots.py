import random

import pytest
from cspapergen.generator import build_paper1_blueprint
from cspapergen.ollama_client import _part_solver_item
from cspapergen.question_bank import QUESTION_STYLES, build_question
from cspapergen.syllabus import load_syllabus

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from tests.support.solver_responses import complete_solver_response


def solve(question, part, answers):
    class Client:
        def generate_json(self, _prompt):
            return complete_solver_response(
                {"answer": answers, "mark_points": answers}
            )

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
            {"route-in-order": "A,C,F", "edges": "2"},
        ),
        (
            "functional_programming",
            0,
            {"output-in-order": "16,36,25"},
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
    assert "complete every cell" in part.prompt.casefold()
    assert "1 for an edge and 0 otherwise" in part.prompt.casefold()
    assert "record only" not in part.prompt.casefold()
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


def test_rle_encoding_checks_both_ordered_sequences_without_fixing_pair_notation():
    style = next(s for s in QUESTION_STYLES if s.id == "rle_compression")
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[0]
    answers = {"run-lengths": "2,4,1,1,3,5", "pixel-values": "3,6,9,10,11,4"}
    assert part.response_slots == list(answers)
    for valid in (answers, {key: f"[{value}]" for key, value in answers.items()}):
        assert reconcile_solution(
            solve(question, part, valid), part.marking.model_dump()
        ).passed
    for wrong in (
        {**answers, "run-lengths": "2,4,1,1,4,4"},
        dict(zip(answers, reversed(list(answers.values())), strict=True)),
        {**answers, "pixel-values": "3,6,9,10,11,11"},
    ):
        assert not reconcile_solution(
            solve(question, part, wrong), part.marking.model_dump()
        ).passed
    with pytest.raises(ValueError, match="every slot"):
        solve(question, part, {"run-lengths": answers["run-lengths"]})


@pytest.mark.parametrize(
    "style_id,part_index,answers,wrong_sequence",
    [
        ("data_structures_graph", 1, {"route-in-order": "A,C,F", "edges": "2"}, "A,F"),
        ("functional_programming", 0, {"output-in-order": "16,36,25"}, "16,36"),
    ],
)
def test_solver_sequence_slots_do_not_disclose_computed_length(
    style_id, part_index, answers, wrong_sequence
):
    import json

    style = next(s for s in QUESTION_STYLES if s.id == style_id)
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[part_index]
    prompts = []

    class Client:
        def generate_json(self, prompt):
            prompts.append(prompt)
            return complete_solver_response(
                {"steps": [], "answer": answers, "mark_points": answers}
            )

    solution = IndependentSolver(Client()).solve(_part_solver_item(question, part), [])
    payload = json.JSONDecoder().raw_decode(prompts[0].split("\n", 1)[1])[0]
    assert payload["item"]["response_slots"] == list(answers)
    assert "closed_answers" not in prompts[0]
    assert "route-3" not in prompts[0] and "output-3" not in prompts[0]
    assert reconcile_solution(solution, part.marking.model_dump()).passed
    sequence_slot = next(iter(answers))
    for value in (
        wrong_sequence,
        ",".join(reversed(answers[sequence_slot].split(","))),
        answers[sequence_slot] + ",0",
    ):
        assert not reconcile_solution(
            solve(question, part, {**answers, sequence_slot: value}),
            part.marking.model_dump(),
        ).passed
    assert reconcile_solution(
        solve(
            question, part, {**answers, sequence_slot: f"[{answers[sequence_slot]}]"}
        ),
        part.marking.model_dump(),
    ).passed


@pytest.mark.parametrize(
    "route",
    ["A,C,F", "A, C, F", "[A,C,F]", '["A", "C", "F"]',
     "A -> C -> F", "A → C → F", "A-C-F"],
)
@pytest.mark.parametrize("same_marking_format", [False, True])
def test_graph_route_accepts_equivalent_ordered_vertex_notation(route, same_marking_format):
    style = next(s for s in QUESTION_STYLES if s.id == "data_structures_graph")
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[1]

    class Client:
        def generate_json(self, _prompt):
            return complete_solver_response({
                "answer": {"route-in-order": route, "edges": "2"},
                "mark_points": {
                    "route-in-order": route if same_marking_format else "A,C,F",
                    "edges": "2",
                },
            })

    solution = IndependentSolver(Client()).solve(_part_solver_item(question, part), [])
    assert reconcile_solution(solution, part.marking.model_dump()).passed


@pytest.mark.parametrize(
    "route,edges",
    [("A,F", "2"), ("A,C,F,E", "2"), ("F,C,A", "2"),
     ("A,F,C", "2"), ("A,B,F", "2"), ("A,B,E,F", "3"),
     ("a,c,f", "2"), ("A,CC,F", "2"), ("A,C,C,F", "2"),
     ("A,C,F", "3"), ("A,C,F", "-2"), ("A,C,F", "2.1")],
)
def test_graph_route_preserves_vertex_identity_order_and_edge_count(route, edges):
    style = next(s for s in QUESTION_STYLES if s.id == "data_structures_graph")
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[1]
    solution = solve(question, part, {"route-in-order": route, "edges": edges})
    assert not reconcile_solution(solution, part.marking.model_dump()).passed


def test_graph_route_comparison_does_not_normalise_other_sequence_slots():
    style = next(s for s in QUESTION_STYLES if s.id == "functional_programming")
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[0]
    solution = solve(question, part, {"output-in-order": "16-36-25"})
    assert not reconcile_solution(solution, part.marking.model_dump()).passed


@pytest.mark.parametrize(
    "route",
    ["A,,C,F", "A-->C->F", "[A,C,F", '[["A", "C", "F"]]',
     '["A", null, "F"]', "A,C,F or A,B,F", "A,C,F,", "[]"],
)
def test_graph_route_rejects_malformed_or_ambiguous_notation(route):
    style = next(s for s in QUESTION_STYLES if s.id == "data_structures_graph")
    question = build_question(style, 1, style.totals[0], random.Random(7))
    with pytest.raises(ValueError, match="answer and mark_points contradict"):
        solve(question, question.parts[1], {"route-in-order": route, "edges": "2"})


@pytest.mark.parametrize(
    "marking",
    [{"route-in-order": "A -> B -> F", "edges": "2"},
     {"route-in-order": "A -> C -> F", "edges": "3"}],
)
def test_graph_route_still_rejects_contradictory_solver_mark_points(marking):
    style = next(s for s in QUESTION_STYLES if s.id == "data_structures_graph")
    question = build_question(style, 1, style.totals[0], random.Random(7))

    class Client:
        def generate_json(self, _prompt):
            return complete_solver_response({
                "answer": {"route-in-order": "A,C,F", "edges": "2"},
                "mark_points": marking,
            })

    with pytest.raises(ValueError, match="answer and mark_points contradict"):
        IndependentSolver(Client()).solve(_part_solver_item(question, question.parts[1]), [])


@pytest.mark.parametrize("route,passed", [("A → C → F", True), ("A → B → F", False)])
def test_graph_route_alternatives_use_the_same_ordered_vertex_comparison(route, passed):
    style = next(s for s in QUESTION_STYLES if s.id == "data_structures_graph")
    question = build_question(style, 1, style.totals[0], random.Random(7))
    part = question.parts[1]
    solution = solve(question, part, {"route-in-order": "A,C,F", "edges": "2"})
    solution = solution.model_copy(update={
        "credit_policy_version": "legacy-unverified",
        "alternatives": [f"route-in-order: {route}"],
    })
    assert reconcile_solution(solution, part.marking.model_dump()).passed is passed
