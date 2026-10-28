# Whole E2 cases must differ in reasoning, not just names or numbers

from decimal import Decimal

import pytest


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_complete_case_has_balanced_credit_time_and_bound_sources(seed):
    from Backend.Core.france.database_case_prose import render_case
    from Backend.Core.france.nsi import NSIExercise

    exercise = NSIExercise.model_validate(render_case(seed))
    assert exercise.credit == Decimal("6")
    assert exercise.minutes == 70
    assert [q.id for q in exercise.questions] == [
        f"2{letter}" for letter in "abcdefghijkl"
    ]
    assert len(exercise.materials) == 3
    assert exercise.materials[-1].id == "case_states"
    assert "case_states" in exercise.questions[8].material_ids
    assert all("case_states" not in q.material_ids for q in exercise.questions[:8])
    assert [row[0] for row in exercise.materials[-1].rows] == (
        ["S0", "S1", "S2"]
        if seed == 270100
        else ["S0", "S1", "S2", "S3"]
        if seed == 270101
        else ["S1", "S2", "S3"]
    )
    assert all(q.material_ids for q in exercise.questions)
    assert exercise.questions[7].operation == "design"
    assert exercise.questions[7].difficulty == 4
    assert exercise.questions[7].points == "1"
    assert len(exercise.questions[7].marking) == 4
    public = exercise.candidate_view()
    assert all(
        not {"answer", "marking", "verification"} & q.keys()
        for q in public["questions"]
    )
    assert "def sensor_extrema" not in exercise.context


def test_whole_cases_pass_unchanged_pairwise_originality_screen():
    from Backend.Core.france.database_case_prose import render_case
    from Backend.Core.france.originality import screen_originality

    previous = []
    for seed in range(270100, 270103):
        exercise = render_case(seed)
        text = "\n".join(
            [
                exercise["title"],
                exercise["context"],
                *(q["prompt"] for q in exercise["questions"]),
            ]
        )
        screen_originality(text, [], previous_texts=previous)
        previous.append(text)


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("total", ("5.5", "6", "6.5"))
def test_case_supports_pipeline_allocations_without_dropping_criteria(seed, total):
    from Backend.Core.france.database_case_prose import (
        case_blueprint,
        render_case,
        verify_candidate,
    )
    from Backend.Core.france.nsi import NSIExercise

    raw = render_case(seed, total=total)
    exercise = NSIExercise.model_validate(raw)
    base = NSIExercise.model_validate(render_case(seed))
    assert exercise.credit == Decimal(total)
    assert exercise.minutes == 70
    assert verify_candidate(raw, seed, total=total)
    for question, original, plan in zip(
        exercise.questions, base.questions, case_blueprint(seed, total), strict=True
    ):
        assert plan["id"] == question.id
        assert plan["points"] == question.points
        assert plan["estimated_minutes"] == question.estimated_minutes
        assert plan["required_curriculum_code"] == question.curriculum_codes[0]
        assert all(
            credit.criterion in " ".join(c.criterion for c in question.marking)
            for credit in original.marking
        )
        assert question.answer == original.answer
    for invalid in ("0", "6.25", True, 6, None):
        with pytest.raises(ValueError):
            render_case(seed, total=invalid)


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_pipeline_verification_recomputes_and_rejects_mutated_case(seed):
    from copy import deepcopy

    from Backend.Core.france.database_case_prose import render_case
    from Backend.Core.france.verification import verify_contract

    for question in render_case(seed)["questions"]:
        contract = question["verification"]
        assert verify_contract(contract)["state"] == "passed"
        for key, value in (
            ("seed", True),
            ("version", "v0"),
            ("case_sha256", "0" * 64),
            ("task_id", "1a"),
            ("expected", {}),
        ):
            changed = deepcopy(contract)
            changed[key] = value
            assert verify_contract(changed)["state"] == "failed"
        changed = deepcopy(contract)
        changed["unexpected"] = "ignored?"
        assert verify_contract(changed)["state"] == "failed"


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_case_verifier_rejects_prompt_credit_answer_and_source_changes(seed):
    from copy import deepcopy

    from Backend.Core.france.database_case_prose import render_case, verify_candidate

    exercise = render_case(seed)
    assert verify_candidate(exercise, seed)
    for field in ("prompt", "answer", "points"):
        changed = deepcopy(exercise)
        changed["questions"][7][field] = "incorrect"
        assert not verify_candidate(changed, seed)
    changed = deepcopy(exercise)
    changed["materials"][0]["rows"][0][0] = "999"
    assert not verify_candidate(changed, seed)


def test_solutions_are_derived_from_tested_application_algorithms():
    from Backend.Core.france.database_case_families import (
        first_stock_deficit,
        remaining_places,
        sensor_extrema,
    )
    from Backend.Core.france.database_case_prose import render_case

    arguments = [
        ([1, 2], [(1, -8, True), (1, 99, False)]),
        ({1: 4}, [(1, 5, True)]),
        (2, [(11, -3), (12, 8)]),
    ]
    for seed, function, args in zip(
        range(270100, 270103),
        (sensor_extrema, remaining_places, first_stock_deficit),
        arguments,
        strict=True,
    ):
        answer = render_case(seed)["questions"][7]["answer"]
        code = answer.split("```python\n", 1)[1].split("```", 1)[0]
        namespace = {}
        # only deterministic application-owned solution text; never model output
        exec(compile(code, "<application-solution>", "exec"), namespace)
        assert namespace[function.__name__](*args) == function(*args)


@pytest.mark.parametrize("seed", range(270100, 270103))
def test_printed_sql_queries_and_state_transitions_execute_as_described(seed):
    import re
    import sqlite3

    from Backend.Core.france.database_case_families import _SCHEMAS, build_case
    from Backend.Core.france.database_case_prose import render_case

    case, exercise = build_case(seed), render_case(seed)
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(_SCHEMAS[case["family"]])
        for table in case["public"]["tables"]:
            connection.executemany(
                f"INSERT INTO {table['name']} VALUES ({','.join('?' for _ in table['columns'])})",
                table["rows"],
            )

        def sql(index):
            # only fixed app-owned corrections, never arbitrary model SQL.
            return re.search(
                r"```sql\n(.*?)\n```", exercise["questions"][index]["answer"], re.S
            )[1]

        query = sql(5)
        assert [list(row) for row in connection.execute(query)] == case["expected"][
            "result"
        ]
        subset = list(connection.execute(sql(2)))
        if case["family"] == "sensors":
            assert subset == [(0, 18 + seed % 5), (10, 24 + seed % 5)]
        elif case["family"] == "bookings":
            assert subset == [(13, 2)]
        else:
            assert subset == [(11, -(6 + seed % 3) - 2), (12, 4)]
        connection.executescript(sql(9))
        updated = list(connection.execute(query))
        if case["family"] == "sensors":
            assert updated[0] == (1, 18 + seed % 5, 21 + seed % 5)
        elif case["family"] == "bookings":
            assert updated == [(1, 2), (2, 1), (3, 2)]
        else:
            assert next(iter(connection.execute(sql(2)))) == (12, 4)
            assert updated == [(1, 4), (2, 4), (3, 6)]
    finally:
        connection.close()


@pytest.mark.parametrize("seed", range(270100, 270103))
@pytest.mark.parametrize("large_print", (False, True))
@pytest.mark.parametrize("total", ("5.5", "6", "6.5"))
def test_complete_case_pdf_keeps_all_questions_and_no_clipped_words(
    tmp_path, seed, large_print, total
):
    import pymupdf

    from Backend.Core.france.database_case_prose import render_case
    from Backend.Core.france.nsi import NSIExercise
    from Backend.Core.france.rendering import render_assessment

    exercise = NSIExercise.model_validate(render_case(seed, total=total))
    for correction in (False, True):
        path = tmp_path / f"e2-{seed}-{large_print}-{correction}.pdf"
        render_assessment(
            path,
            [exercise],
            correction=correction,
            large_print=large_print,
            coherent_material_flow=True,
        )
        with pymupdf.open(path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)
            assert "case_states" not in text
            assert any(
                "Tableau de travail pour la question 2i" in page.get_text()
                and "2i." in page.get_text()
                for page in pdf
            )
            for question in exercise.questions:
                assert question.id in text
            for page in pdf:
                for x0, y0, x1, y1, *_ in page.get_text("words"):
                    assert 0 <= x0 < x1 <= page.rect.width
                    assert 0 <= y0 < y1 <= page.rect.height
            assert ("def sensor_extrema" in text) is (correction and seed == 270100)
            assert ("def remaining_places" in text) is (correction and seed == 270101)
            assert ("def first_stock_deficit" in text) is (
                correction and seed == 270102
            )
            if not large_print:
                if correction:
                    for question in exercise.questions:
                        assert any(
                            f"Réponse attendue — question {question.id}"
                            in page.get_text()
                            and f"Barème indicatif — question {question.id}"
                            in page.get_text()
                            for page in pdf
                        )
                else:
                    import re

                    for question in exercise.questions:
                        compact = re.sub(r"\s+", "", question.prompt)
                        assert any(
                            compact in re.sub(r"\s+", "", page.get_text())
                            for page in pdf
                        )
