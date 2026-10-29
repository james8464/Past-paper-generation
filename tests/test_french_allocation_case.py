# Relational rows and exhaustive assignment oracles for the new case.

import sqlite3
from copy import deepcopy
from itertools import permutations

import pytest


def test_query_uses_active_eligible_teams_in_task_priority_order():
    from Backend.Core.france.allocation_case import build_case, candidate_query

    case = build_case(270104)
    with sqlite3.connect(":memory:") as database:
        database.executescript(case["schema"])
        database.executemany("INSERT INTO Equipe VALUES (?, ?, ?)", case["teams"])
        database.executemany("INSERT INTO Tache VALUES (?, ?, ?)", case["tasks"])
        database.executemany("INSERT INTO Habilitation VALUES (?, ?)", case["skills"])
        assert database.execute(candidate_query()).fetchall() == [
            (10, 1),
            (10, 2),
            (11, 1),
            (12, 3),
        ]
        database.execute("UPDATE Equipe SET active = 0 WHERE id = 2")
        assert database.execute(candidate_query()).fetchall() == [
            (10, 1),
            (11, 1),
            (12, 3),
        ]


def test_greedy_choice_is_a_counterexample_not_proof_of_infeasibility():
    from Backend.Core.france.allocation_case import affecter, glouton

    choices = [(10, 1), (10, 2), (11, 1), (12, 3)]
    before = deepcopy(choices)
    assert glouton([10, 11, 12], choices) is None
    assert affecter([10, 11, 12], choices) == [(10, 2), (11, 1), (12, 3)]
    assert choices == before


def test_repair_matches_all_small_bipartite_feasibility_cases():
    from Backend.Core.france.allocation_case import affecter

    tasks, teams = [10, 11, 12], [1, 2, 3]
    edges = [(task, team) for task in tasks for team in teams]
    for mask in range(2 ** len(edges)):
        choices = [edge for index, edge in enumerate(edges) if mask & (1 << index)]
        feasible = [
            list(zip(tasks, order, strict=True))
            for order in permutations(teams)
            if all(
                (task, team) in choices for task, team in zip(tasks, order, strict=True)
            )
        ]
        answer = affecter(tasks, choices)
        assert (answer is not None) == bool(feasible)
        if answer is not None:
            assert answer in feasible


def test_failed_search_does_not_pollute_the_next_attempt():
    from Backend.Core.france.allocation_case import affecter

    assert affecter([10, 11], [(10, 1), (11, 1)]) is None
    assert affecter([], []) == []
    assert affecter([10], [(10, 1)]) == [(10, 1)]


def test_sql_schema_enforces_the_keys_and_active_domain_claimed_in_the_paper():
    from Backend.Core.france.allocation_case import build_case

    case = build_case(270104)
    with sqlite3.connect(":memory:") as database:
        database.execute("PRAGMA foreign_keys = ON")
        database.executescript(case["schema"])
        database.executemany("INSERT INTO Equipe VALUES (?, ?, ?)", case["teams"])
        database.executemany("INSERT INTO Habilitation VALUES (?, ?)", case["skills"])
        for team, domain in [(9, "son"), (1, "son"), (None, "son")]:
            with pytest.raises(sqlite3.IntegrityError):
                database.execute(
                    "INSERT INTO Habilitation VALUES (?, ?)", (team, domain)
                )
        with pytest.raises(sqlite3.IntegrityError):
            database.execute("UPDATE Equipe SET active = 2 WHERE id = 1")


@pytest.mark.parametrize("seed", [True, 1.5, "270104", -(2**63) - 1, 2**63])
def test_invalid_seed_is_refused(seed):
    from Backend.Core.france.allocation_case import build_case

    with pytest.raises(ValueError):
        build_case(seed)
