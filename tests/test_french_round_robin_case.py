# check the new scheduling case against an independent, one-tick simulator

from copy import deepcopy
from itertools import product

import pytest

from Backend.Core.france.round_robin_case import build_case, schedule


def tick_oracle(jobs, quantum):
    remaining = {name: duration for name, _, duration in jobs}
    finished, ready, slices = {}, [], []
    active, used, start, time = None, 0, 0, 0
    while len(finished) < len(jobs):
        ready.extend(name for name, arrival, _ in jobs if arrival == time)
        if active is not None and (remaining[active] == 0 or used == quantum):
            slices.append([active, start, time])
            if remaining[active] == 0:
                finished[active] = time
            else:
                ready.append(active)
            active = None
        if active is None and ready:
            active, start, used = ready.pop(0), time, 0
        if active is not None:
            remaining[active] -= 1
            used += 1
        time += 1
    return slices, finished


def test_case_has_a_real_preemption_and_boundary_arrival():
    case = build_case(270103)
    result = schedule(case["jobs"], 2)
    assert result["slices"] == [
        ["A", 0, 2],
        ["B", 2, 4],
        ["C", 4, 5],
        ["A", 5, 7],
        ["B", 7, 8],
        ["D", 8, 10],
        ["A", 10, 11],
    ]
    assert result["ready_after"][3] == ["B", "D", "A"]
    assert result["finished"] == {"C": 5, "B": 8, "D": 10, "A": 11}


def test_many_small_schedules_match_tick_oracle_without_mutation():
    for arrivals in product(range(3), repeat=3):
        for durations in product(range(1, 4), repeat=3):
            jobs = sorted(
                zip("ABC", arrivals, durations, strict=True), key=lambda job: job[1]
            )
            original = deepcopy(jobs)
            for quantum in (1, 2, 3):
                expected_slices, expected_finished = tick_oracle(jobs, quantum)
                actual = schedule(jobs, quantum)
                assert actual["slices"] == expected_slices
                assert actual["finished"] == expected_finished
            assert jobs == original


def test_idle_gaps_and_empty_queue():
    assert schedule([], 2) == {"slices": [], "finished": {}, "ready_after": []}
    result = schedule([("A", 3, 1), ("B", 9, 2)], 2)
    assert result["slices"] == [["A", 3, 4], ["B", 9, 11]]
    assert result["ready_after"] == [[], []]


@pytest.mark.parametrize("quantum", [True, 0, -1, 17, 1.5, "2"])
def test_invalid_quantum_is_rejected(quantum):
    with pytest.raises(ValueError):
        schedule([("A", 0, 1)], quantum)


@pytest.mark.parametrize(
    "jobs",
    [
        [("A", True, 1)],
        [("A", 0, False)],
        [("A", -1, 1)],
        [("A", 0, 0)],
        [("A", 0, 101)],
        [("A", 101, 1)],
        [("A", 0, 1), ("A", 0, 2)],
        [("A", 2, 1), ("B", 1, 1)],
        [("", 0, 1)],
        [(1, 0, 1)],
        [("A", 0)],
        "A",
    ],
)
def test_invalid_jobs_are_rejected(jobs):
    with pytest.raises(ValueError):
        schedule(jobs, 2)


@pytest.mark.parametrize("seed", [True, 1.5, 2**63, -(2**63) - 1])
def test_case_rejects_invalid_seed(seed):
    with pytest.raises(ValueError):
        build_case(seed)


def test_exercise_has_linked_construction_and_complete_credit():
    from decimal import Decimal

    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.round_robin_exercise import render_case

    raw = render_case(270103)
    exercise = NSIExercise.model_validate(raw)
    assert exercise.id == "3"
    assert exercise.credit == Decimal("6")
    assert exercise.minutes == 70
    assert len(exercise.questions) == 12
    assert [q.id for q in exercise.questions] == ["3" + c for c in "abcdefghijkl"]
    assert any("__A__" in q.prompt for q in exercise.questions)
    assert "B, D, A" in exercise.questions[3].answer
    assert "13/4" in exercise.questions[2].answer
    assert all(q.marking and q.answer for q in exercise.questions)


def test_slice_helper_uses_partial_final_quantum():
    from Backend.Core.france.round_robin_exercise import tranche

    ready, remaining = ["C", "A"], {"C": 1, "A": 3}
    assert tranche(ready, remaining, 4, 2) == ("C", 5)
    assert ready == ["A"]
    assert remaining == {"C": 0, "A": 3}
