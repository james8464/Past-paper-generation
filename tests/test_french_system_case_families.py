"""Independent answer checks for substantive E3 families, not renamed incidents."""

from copy import deepcopy

import pytest


@pytest.mark.parametrize(
    "seed,family", [(270100, "routing"), (270101, "locks"), (270102, "delivery")]
)
def test_case_is_fresh_bound_and_has_linked_states(seed, family):
    from Backend.Core.france.system_case_families import build_case, verify_case

    case = build_case(seed)
    assert case["family"] == family
    assert len(case["expected"]["states"]) >= 3
    assert verify_case(case)
    altered = deepcopy(case)
    altered["public"]["title"] = "different"
    assert not verify_case(altered)
    case["expected"]["states"].clear()
    assert len(build_case(seed)["expected"]["states"]) >= 3
    for invalid in (True, "270100", 1.2, None):
        with pytest.raises(ValueError):
            build_case(invalid)


def test_distance_round_uses_previous_round_not_in_place_updates():
    from Backend.Core.france.system_case_families import distance_round

    links = [["A", "B", 1], ["B", "C", 1], ["C", "D", 1]]
    old = {"A": None, "B": None, "C": None, "D": 0}
    before = deepcopy(old)
    assert distance_round(links, old, "D") == {"A": None, "B": None, "C": 1, "D": 0}
    assert old == before
    next_round = distance_round(links, distance_round(links, old, "D"), "D")
    assert next_round == {"A": None, "B": 2, "C": 1, "D": 0}


def test_deadlock_cycle_is_not_the_same_as_all_waiting_processes():
    from Backend.Core.france.system_case_families import deadlocked_processes

    owners = {"X": "P", "Y": "Q", "Z": "R"}
    waiting = {"P": "Y", "Q": "X", "R": "X", "S": "Z", "T": "FREE"}
    before = deepcopy((owners, waiting))
    assert deadlocked_processes(owners, waiting) == ["P", "Q"]
    assert (owners, waiting) == before
    assert deadlocked_processes({}, waiting) == []


def test_delivery_buffers_gaps_and_discards_identical_duplicates():
    from Backend.Core.france.system_case_families import delivery_trace

    events = [[0, 2, "B"], [1, 2, "B"], [3, 1, "A"], [5, 3, "C"], [6, 1, "A"]]
    before = deepcopy(events)
    trace = delivery_trace(events)
    assert [s["emitted"] for s in trace] == [[], [], ["A", "B"], ["C"], []]
    assert [s["next"] for s in trace] == [1, 1, 3, 4, 4]
    assert trace[-1]["buffer"] == []
    assert events == before
    assert delivery_trace([]) == []
    with pytest.raises(ValueError):
        delivery_trace([[0, 1, "A"], [1, 1, "different"]])
    for invalid in ([[2, 1, "A"], [1, 2, "B"]], [[0, True, "A"]], [[0, 0, "A"]]):
        with pytest.raises(ValueError):
            delivery_trace(invalid)


@pytest.mark.parametrize(
    "name,seed,wrong",
    [
        ("distance_round", 270100, {"A": 0, "B": 0, "C": 0, "D": 0}),
        ("deadlocked_processes", 270101, []),
        ("delivery_trace", 270102, []),
        ("fifo_jobs", 270102, []),
    ],
)
def test_independent_oracle_catches_algorithm_regressions(
    monkeypatch, name, seed, wrong
):
    from Backend.Core.france import system_case_families as cases

    monkeypatch.setattr(cases, name, lambda *args: deepcopy(wrong))
    with pytest.raises(ValueError, match="oracle"):
        cases.build_case(seed)


def test_routing_rounds_against_bounded_walk_oracle_on_varied_graphs():
    from random import Random

    from Backend.Core.france.system_case_families import _walk_oracle, distance_round

    random = Random(84)
    for _ in range(100):
        nodes = "ABCDE"
        links = [
            [a, b, random.randint(1, 6)]
            for i, a in enumerate(nodes)
            for b in nodes[i + 1 :]
            if random.random() < 0.45
        ]
        initial = {n: random.choice([None, 2, 3, 8]) for n in nodes}
        initial["E"] = 0
        current = initial
        for rounds in range(1, 5):
            current = distance_round(links, current, "E")
            assert current == _walk_oracle(links, initial, "E", rounds)


def test_wait_graphs_against_independent_transitive_closure():
    from random import Random

    from Backend.Core.france.system_case_families import (
        _cycle_oracle,
        deadlocked_processes,
    )

    random = Random(192)
    for _ in range(200):
        owners = {f"r{i}": p for i, p in enumerate("ABCDE")}
        waits = {
            p: random.choice([*owners, "free"])
            for p in "ABCDE"
            if random.random() < 0.8
        }
        assert deadlocked_processes(owners, waits) == _cycle_oracle(owners, waits)
    assert deadlocked_processes({"r": "A"}, {"A": "r"}) == ["A"]


def test_all_small_delivery_orders_and_duplicates_have_same_final_prefix():
    from itertools import permutations

    from Backend.Core.france.system_case_families import (
        _delivery_oracle,
        delivery_trace,
    )

    for order in permutations(range(1, 5)):
        events = [[i, n, str(n)] for i, n in enumerate(order)]
        events += [[4, order[0], str(order[0])]]
        trace = delivery_trace(events)
        assert trace == _delivery_oracle(events)
        assert [v for state in trace for v in state["emitted"]] == ["1", "2", "3", "4"]
        assert trace[-1]["next"] == 5
        assert trace[-1]["buffer"] == []


def test_fifo_busy_idle_and_equal_arrivals_match_tick_oracle():
    from random import Random

    from Backend.Core.france.system_case_families import _fifo_oracle, fifo_jobs

    random = Random(213)
    for _ in range(100):
        times = sorted(random.randint(0, 20) for _ in range(6))
        arrivals = [[t, str(i), random.randint(1, 5)] for i, t in enumerate(times)]
        before = deepcopy(arrivals)
        assert fifo_jobs(arrivals) == _fifo_oracle(arrivals)
        assert arrivals == before
    assert fifo_jobs([]) == _fifo_oracle([]) == []
    for invalid in ([[0, "a", 0]], [[0, "a", True]], [[2, "a", 1], [1, "b", 1]]):
        with pytest.raises(ValueError):
            fifo_jobs(invalid)


def test_causal_case_answers_are_not_only_locally_consistent():
    from Backend.Core.france.system_case_families import build_case

    route = build_case(270100)["expected"]
    assert [s["distances"] for s in route["states"]] == [
        {"A": 2, "B": 1, "C": 2, "D": 0},
        {"A": 2, "B": 3, "C": 2, "D": 0},
        {"A": 4, "B": 3, "C": 2, "D": 0},
        {"A": 4, "B": 3, "C": 2, "D": 0},
    ]
    assert (route["arrival"], route["process_end"], route["report_arrival"]) == (
        6,
        8,
        9,
    )
    locks = build_case(270101)["expected"]
    assert [s["cycle"] for s in locks["states"]] == [["P", "Q"], [], []]
    assert locks["finishes"] == {"P": 7, "R": 9, "S": 10}
    delivery = build_case(270102)["expected"]
    assert [(j["message"], j["start"], j["end"]) for j in delivery["jobs"]] == [
        ("A", 3, 5),
        ("B", 5, 7),
        ("C", 7, 9),
        ("D", 9, 11),
    ]
    assert delivery["acknowledgement"] == 12
    assert delivery["acknowledged_on_time"] is False
