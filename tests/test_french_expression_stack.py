# Independent stack semantics for synthesized expression reasoning tasks.

from copy import deepcopy

import pytest

from Backend.Core.france.expression_stack import compile_tree, execute
from Backend.Core.france.expression_synthesis import build_case


def test_stack_order_and_trace_are_explicit():
    assert execute([2, 5, "-", -3, "*"]) == {
        "answer": 9,
        "trace": [[2], [2, 5], [-3], [-3, -3], [9]],
        "peak_depth": 2,
    }


def test_trace_snapshots_do_not_alias_and_input_is_unchanged():
    program = [2, 5, "-"]
    result = execute(program)
    result["trace"][0].append(99)
    assert result["trace"][1:] == [[2, 5], [-3]]
    assert program == [2, 5, "-"]


def test_program_and_arithmetic_bounds():
    assert execute([1_000_000])["answer"] == 1_000_000
    assert execute([-1_000_000])["answer"] == -1_000_000
    assert execute([1] * 64 + ["+"] * 63)["answer"] == 64
    for program in ([1] * 65 + ["+"] * 64, [1_000_001], [1000, 1001, "*"]):
        with pytest.raises(ValueError):
            execute(program)


def test_compiler_uses_links_not_row_order():
    rows = [
        ["right", 5, None, None],
        ["root", "-", "left", "right"],
        ["left", 2, None, None],
    ]
    assert compile_tree(rows, "root") == [2, 5, "-"]


def test_compiler_rejects_oversized_tree_before_traversal():
    with pytest.raises(ValueError):
        compile_tree([[str(i), 1, None, None] for i in range(128)], "0")


@pytest.mark.parametrize("seed", range(100))
def test_compiled_execution_matches_independent_tree_states(seed):
    case = build_case(seed)
    rows = deepcopy(case["public"]["rows"])
    for index, state in enumerate(case["expected"]["states"]):
        if index:
            change = case["public"]["changes"][index - 1]
            next(row for row in rows if row[0] == change["node"])[1] = change["value"]
        before = deepcopy(rows)
        program = compile_tree(rows, "n0")
        assert len(program) == len(rows)
        result = execute(program)
        assert result["answer"] == state["answer"]
        assert len(result["trace"]) == len(program)
        assert rows == before


@pytest.mark.parametrize(
    "program", [[], [1, 2], ["+"], [1, "*"], [True], [1.5], ["eval"], ["2"], None]
)
def test_invalid_programs_are_rejected(program):
    with pytest.raises(ValueError):
        execute(program)


@pytest.mark.parametrize(
    "rows,root",
    [
        ([], "r"),
        ([["r", "+", "r", "r"]], "r"),
        ([["r", "+", "a", "a"], ["a", 2, None, None]], "r"),
        ([["r", 2, None, None], ["r", 3, None, None]], "r"),
        ([["r", 2, None, None], ["a", 3, None, None]], "r"),
        ([["r", "+", "a", None], ["a", 2, None, None]], "r"),
        ([["r", True, None, None]], "r"),
        ([["r", 2, None, None]], "missing"),
    ],
)
def test_malformed_trees_are_rejected(rows, root):
    with pytest.raises(ValueError):
        compile_tree(rows, root)
