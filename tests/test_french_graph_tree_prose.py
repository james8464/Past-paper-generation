"""The closed French renderer cannot print model-authored factual prose."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.france.graph_tree_binding import canonical_answer
from Backend.Core.france.graph_tree_contract import build_graph_tree_contract
from Backend.Core.france.graph_tree_prose import (
    PROSE_CONTRACT_VERSION,
    prose_catalogue_digest,
    render_graph_tree_candidate,
    selection_schema,
    validate_selection,
)
from Backend.Core.france.pipeline import _tasks_for_seed


def _selections(contract, *, variant=1):
    data = contract.to_dict()
    return [
        {
            **(
                {"scene_id": "service", "slots": {"activity": "interventions"}}
                if part == "A"
                else {}
            ),
            "questions": [
                {
                    "contract_task_id": task_id,
                    "claimed_result": data["expected"][task_id],
                    "question_form_id": f"{task_id}-q{variant}",
                    "rubric_form_id": f"{task_id}-r{variant}",
                }
                for task_id in data["task_ids"][start : start + 2]
            ],
        }
        for part, start in (("A", 0), ("B", 2), ("C", 4))
    ]


@pytest.mark.parametrize("seed", [270100, 270101, 270102])
@pytest.mark.parametrize("variant", [1, 2])
def test_renderer_uses_locked_facts_and_exact_credit(seed, variant):
    contract = build_graph_tree_contract(seed, "1")
    task = _tasks_for_seed(seed)[0]
    selections = _selections(contract, variant=variant)
    rendered = render_graph_tree_candidate(task, contract, selections)
    expected = contract.to_dict()["expected"]

    assert rendered["id"] == "1"
    assert rendered["materials"] == []
    assert rendered["target_points"] == task["technical_points"]
    assert [question["id"] for question in rendered["questions"]] == [
        "1a",
        "1b",
        "1c",
        "1d",
        "1e",
        "1f",
    ]
    for question, planned in zip(
        rendered["questions"], task["question_blueprint"], strict=True
    ):
        assert question["points"] == planned["points"]
        assert question["answer"] == canonical_answer(
            question["id"], expected[question["id"]]
        )
        assert sum(Decimal(item["points"]) for item in question["marking"]) == Decimal(
            planned["points"]
        )
        assert all(Decimal(item["points"]) > 0 for item in question["marking"])
    for task_id in ("1b", "1c", "1e", "1f"):
        question = next(item for item in rendered["questions"] if item["id"] == task_id)
        assert len(question["marking"]) == 2
    assert contract.to_dict()["debug_case"]["faulty_code"] not in rendered["context"]
    assert PROSE_CONTRACT_VERSION and len(prose_catalogue_digest()) == 64


def test_second_scene_and_wording_change_only_presentation():
    contract = build_graph_tree_contract(270100, "1")
    task = _tasks_for_seed(270100)[0]
    first = render_graph_tree_candidate(task, contract, _selections(contract))
    choices = _selections(contract, variant=2)
    choices[0]["scene_id"] = "collecte"
    choices[0]["slots"] = {"activity": "collectes"}
    second = render_graph_tree_candidate(task, contract, choices)
    assert first["context"] != second["context"]
    assert first["questions"][0]["prompt"] != second["questions"][0]["prompt"]
    assert [q["answer"] for q in first["questions"]] == [
        q["answer"] for q in second["questions"]
    ]
    assert [q["points"] for q in first["questions"]] == [
        q["points"] for q in second["questions"]
    ]


def test_every_schema_advertised_scene_activity_pair_is_renderable():
    contract = build_graph_tree_contract(270100, "1")
    task = _tasks_for_seed(270100)[0]
    schema = selection_schema("A")
    scene_ids = schema["properties"]["scene_id"]["enum"]
    activities = schema["properties"]["slots"]["properties"]["activity"]["enum"]
    for scene_id in scene_ids:
        for activity in activities:
            choices = _selections(contract)
            choices[0]["scene_id"] = scene_id
            choices[0]["slots"]["activity"] = activity
            validate_selection("A", choices[0], task, contract)
            rendered = render_graph_tree_candidate(task, contract, choices)
            assert rendered["context"]


@pytest.mark.parametrize(
    "injection",
    [
        ("title", "A et F sont directement reliés."),
        ("context", "A et F sont directement reliés."),
        ("prompt", "A et F sont directement reliés."),
        ("marking", "A et F sont directement reliés."),
        ("note", "Ce graphe est complet."),
        ("tree_key", "La clé 999 est présente."),
    ],
)
def test_model_prose_has_no_rendered_entry_point(injection):
    contract = build_graph_tree_contract(270100, "1")
    task = _tasks_for_seed(270100)[0]
    choices = _selections(contract)
    key, value = injection
    choices[0][key] = value
    with pytest.raises(ValueError):
        validate_selection("A", choices[0], task, contract)
    with pytest.raises(ValueError):
        render_graph_tree_candidate(task, contract, choices)


def test_schema_and_validator_reject_unknown_or_changed_selections():
    contract = build_graph_tree_contract(270100, "1")
    task = _tasks_for_seed(270100)[0]
    choices = _selections(contract)
    assert selection_schema("A")["additionalProperties"] is False
    for mutation in (
        lambda item: item["questions"][0].update(question_form_id="1a-unknown"),
        lambda item: item.update(scene_id=[]),
        lambda item: item["questions"][0].update(points="99"),
        lambda item: item["questions"][0]["claimed_result"].update(weight=999),
        lambda item: item["slots"].update(activity="colis"),
    ):
        wrong = deepcopy(choices[0])
        mutation(wrong)
        with pytest.raises(ValueError):
            validate_selection("A", wrong, task, contract)
