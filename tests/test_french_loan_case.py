# Loan availability must agree with relational and interval-based evidence.

from copy import deepcopy
from itertools import permutations

import pytest

from Backend.Core.france.loan_case import available, build_case, overlaps, sql_available


def test_return_boundary_is_available_but_new_loan_occupies_it():
    case = build_case(270103)
    assert available(case["copies"], case["loans"], 4) == [30]
    assert available(case["copies"], case["loans"], 5) == [20, 30]
    assert available(case["copies"], case["loans"], 6) == [11, 20, 30]
    assert overlaps(case["loans"]) == []
    assert overlaps(case["loans"] + [[105, 11, "Eli", 5, 7]]) == [[103, 105]]


def test_sql_and_python_agree_for_all_source_orders_and_boundaries():
    case = build_case(270103)
    original = deepcopy(case)
    for order in permutations(case["loans"]):
        for time in range(9):
            assert sql_available(case["copies"], order, time) == available(
                case["copies"], order, time
            )
    assert case == original


def test_nested_intervals_and_touching_intervals():
    loans = [
        [1, 10, "A", 0, 10],
        [2, 10, "B", 2, 3],
        [3, 10, "C", 4, 5],
        [4, 20, "D", 0, None],
    ]
    assert overlaps(loans) == [[1, 2], [1, 3]]
    assert overlaps([[1, 10, "A", 0, 4], [2, 10, "B", 4, None]]) == []


def test_correction_then_new_loan_removes_the_previously_rejected_conflict():
    case = build_case(270103)
    assert overlaps(case["revised_loans"]) == []
    for time in (5, 6, 7):
        assert available(case["copies"], case["revised_loans"], time) == [20, 30]
        assert sql_available(case["copies"], case["revised_loans"], time) == [20, 30]


@pytest.mark.parametrize("time", [True, -1, "4", 1.5, 101])
def test_invalid_snapshot_time(time):
    case = build_case(0)
    for function in (available, sql_available):
        with pytest.raises(ValueError):
            function(case["copies"], case["loans"], time)


@pytest.mark.parametrize(
    "loans",
    [
        [[1, 10, "A", 0, 0]],
        [[1, 10, "A", 4, 3]],
        [[1, 99, "A", 0, None]],
        [[1, 10, "A", True, None]],
        [[1, 10, "A", 0, False]],
        [[1, 10, "A", 0, None], [1, 20, "B", 1, None]],
    ],
)
def test_invalid_loan_data_is_rejected(loans):
    copies = [[10, "Atlas"], [20, "Boreal"]]
    for function in (available, sql_available):
        with pytest.raises(ValueError):
            function(copies, loans, 4)


def test_exercise_links_sql_intervals_revisions_and_counterexample():
    from decimal import Decimal

    from Backend.Core.france.loan_exercise import render_case
    from Backend.Core.france.nsi import NSIExercise

    exercise = NSIExercise.model_validate(render_case(270103))
    assert exercise.id == "2"
    assert exercise.minutes == 70
    assert exercise.credit == Decimal("6")
    assert len(exercise.questions) == 12
    assert "JOIN emprunt" in exercise.questions[3].prompt
    assert "__A__" in exercise.questions[5].prompt
    assert "103" in exercise.questions[6].answer
    assert "105" in exercise.questions[6].answer


def test_printed_python_helpers_match_independent_interval_checks():
    from Backend.Core.france.loan_exercise import actifs, conflits

    case = build_case(270103)
    before = deepcopy(case)
    for time in range(9):
        busy = actifs(case["copies"], case["loans"], time)
        assert sorted(code for code, ids in busy.items() if not ids) == available(
            case["copies"], case["loans"], time
        )
    proposed = case["loans"] + [[105, 11, "Eli", 5, 7]]
    assert conflits(proposed) == overlaps(proposed)
    assert case == before
