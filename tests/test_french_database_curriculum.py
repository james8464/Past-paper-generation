# The new edition must not require SQL excluded from the Terminale programme.

import re

import pytest


@pytest.mark.parametrize("seed", range(270100, 270104))
def test_candidate_sql_stays_within_the_required_clauses(seed):
    from Backend.Core.france.extended_pipeline import _source

    _, _, exercises = _source(seed)
    for exercise in exercises:
        for question in exercise["questions"]:
            for text in (question["prompt"], question["answer"]):
                assert not re.search(
                    r"\b(?:GROUP\s+BY|HAVING|LEFT\s+JOIN|COALESCE)\b", text, re.I
                ), question["id"]


@pytest.mark.parametrize("seed", range(270100, 270109))
def test_printed_source_queries_match_independent_row_joins(seed):
    from Backend.Core.france.database_case_families import build_case
    from Backend.Core.france.database_curriculum_prose import source_rows

    case = build_case(seed)
    parents, events = [table["rows"] for table in case["public"]["tables"]]
    family = case["family"]
    if family == "sensors":
        expected = [
            [p[0], r[3]]
            for p in parents
            for r in sorted(events, key=lambda row: row[2])
            if p[0] == r[1] and r[4] == 1
        ]
    elif family == "bookings":
        expected = [
            [p[0], r[2]]
            for p in parents
            for r in sorted(events)
            if p[0] == r[1] and r[3] == 1
        ]
    else:
        expected = [
            [p[0], r[0], r[3]]
            for p in parents
            for r in sorted(events, key=lambda row: row[2])
            if p[0] == r[1]
        ]
    assert source_rows(seed) == expected
