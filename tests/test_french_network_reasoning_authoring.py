"""Finite V18 wording and replay tests for the deeper written network case."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.network_reasoning_contract import (
    build_network_reasoning_contract,
)
from Backend.Core.france.nsi import NSIExercise

_IDS = [f"3{letter}" for letter in "abcdefghijkl"]
_MINUTES = (4, 7, 6, 8, 5, 6, 6, 6, 5, 5, 6, 6)


def _task(total: str) -> dict:
    if total not in {"5.5", "6", "6.5"}:
        raise ValueError(total)
    points = ["0.5"] * 12
    if total == "5.5":
        points[0] = points[4] = "0.25"
    elif total == "6.5":
        points[3] = points[11] = "0.75"
    return {
        "question_blueprint": [
            {
                "id": task_id,
                "part_id": "AAAABBBBCCCC"[index],
                "points": points[index],
                "estimated_minutes": _MINUTES[index],
                "operation": ("apply", "analyse", "justify", "design")[index % 4],
                "difficulty": min(4, 1 + index // 3),
                "required_curriculum_code": (
                    "ASR-ROUTAGE"
                    if index < 4
                    else "ASR-PROCESSUS"
                    if index < 8
                    else "ASR-CRYPTO"
                ),
            }
            for index, task_id in enumerate(_IDS)
        ]
    }


def _selection():
    return {
        "scene_id": "terrain",
        "question_forms": {task_id: f"{task_id}-q1" for task_id in _IDS},
        "rubric_forms": {task_id: f"{task_id}-r1" for task_id in _IDS},
    }


def _identity():
    return {
        "provider": "ollama",
        "model_digest": "a" * 64,
        "implementation_sha256": "b" * 64,
    }


class SelectionClient:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate_json(self, _prompt):
        return self.responses.pop(0)


@pytest.mark.parametrize("total", ["5.5", "6", "6.5"])
def test_v18_candidate_has_twelve_connected_french_questions_and_exact_credit(total):
    from Backend.Core.france.network_reasoning_prose import (
        render_network_reasoning_candidate,
    )

    raw = render_network_reasoning_candidate(
        build_network_reasoning_contract(270100),
        _selection(),
        _task(total)["question_blueprint"],
    )
    exercise = NSIExercise.model_validate(raw)
    assert exercise.id == "3"
    assert [question.id for question in exercise.questions] == _IDS
    assert "R1–R3" in exercise.context
    assert [item.id for item in exercise.materials] == [
        "links",
        "process_initial",
        "message_cards",
    ]
    assert sum(question.estimated_minutes for question in exercise.questions) == 70
    assert sum(Decimal(question.points) for question in exercise.questions) == Decimal(
        total
    )
    assert all(
        all(credit.points == "0.25" for credit in question.marking)
        for question in exercise.questions
    )
    assert exercise.questions[2].answer.find("18") >= 0
    assert exercise.questions[3].answer.find("20") >= 0
    assert "P1" in exercise.questions[5].answer
    assert "P2" in exercise.questions[5].answer
    assert "M2" in exercise.questions[8].answer
    assert "métadonnées" in exercise.questions[11].answer
    assert "terminal compromis" in exercise.questions[11].answer
    assert all(question.prompt.endswith("?") for question in exercise.questions)


@pytest.mark.parametrize("large_print", [False, True])
def test_v18_correction_keeps_answer_with_its_rubric(tmp_path, large_print):
    import pymupdf

    from Backend.Core.france.network_reasoning_prose import (
        render_network_reasoning_candidate,
    )
    from Backend.Core.france.rendering import render_assessment

    exercise = NSIExercise.model_validate(
        render_network_reasoning_candidate(
            build_network_reasoning_contract(270100),
            _selection(),
            _task("5.5")["question_blueprint"],
        )
    )
    output = tmp_path / "correction.pdf"
    render_assessment(output, [exercise], correction=True, large_print=large_print)
    with pymupdf.open(output) as pdf:
        pages = [" ".join(page.get_text().split()) for page in pdf]

    for question in exercise.questions:
        answer_fragment = " ".join(question.answer.split())[:42]
        answer_pages = [i for i, page in enumerate(pages) if answer_fragment in page]
        rubric_pages = [
            i
            for i, page in enumerate(pages)
            if f"Barème indicatif — question {question.id}" in page
        ]
        assert answer_pages == rubric_pages, question.id


def test_v18_schema_rejects_free_text_and_incomplete_forms():
    from Backend.Core.france.network_reasoning_prose import (
        network_reasoning_selection_schema,
        validate_network_reasoning_selection,
    )

    contract = build_network_reasoning_contract(270100)
    schema = network_reasoning_selection_schema(contract)
    assert set(schema["properties"]["question_forms"]["properties"]) == set(_IDS)
    assert validate_network_reasoning_selection(contract, _selection()) == _selection()
    for field, task_id, bad in (
        ("question_forms", "3a", "route inventée"),
        ("rubric_forms", "3l", "3l-r3"),
    ):
        forged = deepcopy(_selection())
        forged[field][task_id] = bad
        with pytest.raises(ValueError):
            validate_network_reasoning_selection(contract, forged)
    forged = deepcopy(_selection())
    del forged["question_forms"]["3l"]
    with pytest.raises(ValueError):
        validate_network_reasoning_selection(contract, forged)
    forged = {**_selection(), "result": "19"}
    with pytest.raises(ValueError):
        validate_network_reasoning_selection(contract, forged)


def test_v18_candidate_rejects_wrong_credit_and_reordered_part():
    from Backend.Core.france.network_reasoning_prose import (
        render_network_reasoning_candidate,
    )

    contract = build_network_reasoning_contract(270100)
    wrong_credit = _task("6")["question_blueprint"]
    wrong_credit[0]["points"] = "1"
    with pytest.raises(ValueError):
        render_network_reasoning_candidate(contract, _selection(), wrong_credit)
    wrong_part = _task("6")["question_blueprint"]
    wrong_part[4]["part_id"] = "A"
    with pytest.raises(ValueError):
        render_network_reasoning_candidate(contract, _selection(), wrong_part)


def test_v18_variable_credits_cover_every_requested_step():
    from Backend.Core.france.network_reasoning_prose import (
        render_network_reasoning_candidate,
    )

    contract = build_network_reasoning_contract(270100)
    for total in ("5.5", "6", "6.5"):
        questions = render_network_reasoning_candidate(
            contract, _selection(), _task(total)["question_blueprint"]
        )["questions"]
        first, changed, processes = questions[0], questions[3], questions[4]
        if total == "5.5":
            assert "Central" in first["marking"][0]["criterion"]
            assert all(
                name in processes["marking"][0]["criterion"] for name in ("P1", "P2")
            )
        else:
            assert "P1" in processes["marking"][0]["criterion"]
            assert "P2" in processes["marking"][1]["criterion"]
        assert "initial" in changed["prompt"]


def test_v18_authoring_replays_exact_hashes_and_preserves_bad_attempt(tmp_path):
    from Backend.Core.france.network_reasoning_authoring import (
        author_network_reasoning_selection,
        network_reasoning_selection_prompt,
        replay_network_reasoning_selection,
    )
    from Backend.Core.france.network_reasoning_prose import (
        network_reasoning_selection_schema,
    )
    from Backend.Core.france.provider import response_policy

    task = _task("6")
    contract = build_network_reasoning_contract(270100)
    prompt = network_reasoning_selection_prompt(task, contract, [])
    schema, budget = response_policy(prompt)
    assert schema == network_reasoning_selection_schema(contract)
    assert budget <= 2048
    bad = deepcopy(_selection())
    bad["question_forms"]["3d"] = "free text"
    path = tmp_path / "v18-selection.json"
    raw, evidence = author_network_reasoning_selection(
        SelectionClient([bad, _selection()]),
        task,
        contract,
        [],
        path,
        run_identity=_identity(),
    )
    assert raw["id"] == "3"
    assert evidence["failed_attempts"][0]["response"] == bad
    assert (
        replay_network_reasoning_selection(
            task, contract, [], evidence, run_identity=_identity()
        )
        == raw
    )
    forged = deepcopy(evidence)
    forged["accepted"]["response"]["scene_id"] = "campus"
    with pytest.raises(ValueError):
        replay_network_reasoning_selection(
            task, contract, [], forged, run_identity=_identity()
        )
    forged = deepcopy(evidence)
    forged["failed_attempts"][0]["attempt"] = 2
    with pytest.raises(ValueError):
        replay_network_reasoning_selection(
            task, contract, [], forged, run_identity=_identity()
        )
    forged = deepcopy(evidence)
    forged["contract_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        replay_network_reasoning_selection(
            task, contract, [], forged, run_identity=_identity()
        )
    with pytest.raises(ValueError, match="identity"):
        author_network_reasoning_selection(
            SelectionClient([]),
            task,
            contract,
            [],
            path,
            run_identity={**_identity(), "model_digest": "c" * 64},
        )
