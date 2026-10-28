"""V32 whole-case foundations: SQL and independent list-based evidence."""

from copy import deepcopy

import pytest


@pytest.mark.parametrize("seed", range(270100, 270112))
def test_database_cases_bind_public_source_and_independent_results(seed):
    from Backend.Core.france.database_case_families import build_case, verify_case

    case = build_case(seed)
    assert verify_case(case)
    assert "expected" not in case["public"]
    assert len(case["public"]["tables"]) == 2
    assert case["expected"]["foreign_key_rejected"] is True
    assert case["expected"]["sql_matches_independent"] is True
    altered = deepcopy(case)
    altered["public"]["tables"][0]["rows"][0][1] = "ALTERED"
    assert not verify_case(altered)
    altered = deepcopy(case)
    altered["expected"]["sql_matches_independent"] = 1
    assert not verify_case(altered)
    altered = deepcopy(case)
    altered["expected"]["result"] = []
    assert not verify_case(altered)


def test_three_cases_require_different_relational_and_algorithmic_reasoning():
    from Backend.Core.france.database_case_families import build_case

    sensor, booking, stock = [build_case(s) for s in range(270100, 270103)]
    assert [c["family"] for c in (sensor, booking, stock)] == [
        "sensors",
        "bookings",
        "stock",
    ]
    # Invalid observations do not enter extrema; unobserved sensors remain explicit.
    offset = 270100 % 5
    assert sensor["expected"]["result"] == [
        [1, 18 + offset, 24 + offset],
        [2, 12 + offset, 16 + offset],
        [3, None, None],
    ]
    # Count seats rather than reservation rows, and retain the empty session.
    assert booking["expected"]["result"] == [[1, -1], [2, 2], [3, 5]]
    assert booking["expected"]["overbooked"] == [1]
    # A positive closing balance does not prove that every prefix was feasible.
    assert stock["expected"]["first_invalid"] == 11
    assert stock["expected"]["result"][0] == [1, 2]
    assert stock["expected"]["prefix_balances"][0][1] == -2


def test_case_inputs_are_isolated_and_reject_invalid_seed_types():
    from Backend.Core.france.database_case_families import build_case

    for value in (True, 1.2, "270100", None):
        with pytest.raises(ValueError):
            build_case(value)
    case = build_case(270100)
    case["public"]["tables"][0]["rows"].clear()
    assert len(build_case(270100)["public"]["tables"][0]["rows"]) == 3


def test_single_pass_algorithms_cover_empty_invalid_and_boundary_cases():
    from Backend.Core.france.database_case_families import (
        first_stock_deficit,
        remaining_places,
        sensor_extrema,
    )

    assert sensor_extrema([1, 2], []) == {1: None, 2: None}
    observations = [(1, -8, True), (1, 99, False), (1, -12, True)]
    assert sensor_extrema([1, 2], observations) == {1: (-12, -8), 2: None}
    assert observations == [(1, -8, True), (1, 99, False), (1, -12, True)]
    assert remaining_places({1: 4, 2: 3}, []) == {1: 4, 2: 3}
    capacities = {1: 4, 2: 3}
    assert remaining_places(capacities, [(1, 4, True), (2, 8, False)]) == {1: 0, 2: 3}
    assert remaining_places(capacities, [(1, 5, True)]) == {1: -1, 2: 3}
    assert capacities == {1: 4, 2: 3}
    assert first_stock_deficit(0, []) is None
    assert first_stock_deficit(2, [(11, -2), (12, 1)]) is None
    assert first_stock_deficit(2, [(11, -3), (12, 9)]) == 11
    assert first_stock_deficit(2, [(11, 3), (12, -6)]) == 12


def test_algorithms_match_independent_oracles_on_many_inputs():
    import random

    from Backend.Core.france.database_case_families import (
        first_stock_deficit,
        remaining_places,
        sensor_extrema,
    )

    rng = random.Random(3200)
    for _ in range(200):
        observations = [
            (rng.randrange(3), rng.randrange(-30, 40), rng.choice([True, False]))
            for _ in range(rng.randrange(20))
        ]
        expected = {}
        for key in range(3):
            values = [
                value
                for sensor, value, valid in observations
                if sensor == key and valid
            ]
            expected[key] = (min(values), max(values)) if values else None
        assert sensor_extrema(range(3), iter(observations)) == expected
        capacities = {key: rng.randrange(1, 20) for key in range(3)}
        bookings = [
            (rng.randrange(3), rng.randrange(1, 9), rng.choice([True, False]))
            for _ in range(rng.randrange(20))
        ]
        assert remaining_places(capacities, iter(bookings)) == {
            key: capacity
            - sum(
                seats
                for session, seats, confirmed in bookings
                if session == key and confirmed
            )
            for key, capacity in capacities.items()
        }
        initial = rng.randrange(10)
        movements = [
            (index + 1, rng.choice([-4, -2, 1, 3]))
            for index in range(rng.randrange(20))
        ]
        bad = [
            identifier
            for index, (identifier, _) in enumerate(movements)
            if initial + sum(delta for _, delta in movements[: index + 1]) < 0
        ]
        assert first_stock_deficit(initial, iter(movements)) == (
            bad[0] if bad else None
        )


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_case_requires_algorithm_and_sql_agreement(seed):
    from Backend.Core.france.database_case_families import build_case

    assert build_case(seed)["expected"]["algorithm_matches_independent"] is True


@pytest.mark.parametrize(
    ("seed", "function", "wrong"),
    [
        (270100, "sensor_extrema", {1: (0, 99), 2: None, 3: None}),
        (270101, "remaining_places", {1: 0, 2: 2, 3: 5}),
        (270102, "first_stock_deficit", None),
    ],
)
def test_algorithm_mismatch_blocks_case_publication(monkeypatch, seed, function, wrong):
    from Backend.Core.france import database_case_families as cases

    monkeypatch.setattr(cases, function, lambda *args: wrong)
    with pytest.raises(ValueError, match="Algorithm and independent"):
        cases.build_case(seed)


def test_linked_states_have_distinct_causal_effects():
    from Backend.Core.france.database_case_families import build_case

    sensor, booking, stock = [build_case(seed) for seed in range(270100, 270103)]
    assert [state["result"][0] for state in sensor["expected"]["states"]] == [
        [1, 18, 24],
        [1, 18, 18],
        [1, 18, 21],
    ]
    assert [state["result"] for state in booking["expected"]["states"]] == [
        [[1, -1], [2, 2], [3, 5]],
        [[1, 2], [2, 2], [3, 2]],
        [[1, 2], [2, 0], [3, 2]],
        [[1, 2], [2, 1], [3, 2]],
    ]
    assert [state["first_invalid"] for state in stock["expected"]["states"]] == [
        11,
        None,
        16,
        16,
    ]
    assert [state["result"][0][1] for state in stock["expected"]["states"]] == [
        2,
        2,
        -1,
        4,
    ]


@pytest.mark.parametrize("seed", range(270100, 270112))
def test_each_linked_state_is_verified_by_sql_and_algorithm(seed):
    from Backend.Core.france.database_case_families import build_case

    case = build_case(seed)
    assert case["expected"]["states_sql_matches_independent"] is True
    assert case["expected"]["states_algorithm_matches_independent"] is True
    assert [state["name"] for state in case["expected"]["states"]] == [
        f"S{index}" for index in range(len(case["expected"]["states"]))
    ]


def test_chronology_corruption_cannot_hide_behind_unchanged_totals(monkeypatch):
    from Backend.Core.france import database_case_families as cases

    original = cases.linked_sql

    def corrupt(family, public):
        statements = original(family, public)
        statements[0] = "UPDATE mouvement SET instant=5 WHERE numero=12;"
        return statements

    monkeypatch.setattr(cases, "linked_sql", corrupt)
    with pytest.raises(ValueError, match="wrong source rows"):
        cases.build_case(270102)


def test_case_rejects_tampered_linked_evidence():
    from Backend.Core.france.database_case_families import build_case, verify_case

    case = build_case(270102)
    case["expected"]["states"][-1]["first_invalid"] = None
    assert not verify_case(case)
