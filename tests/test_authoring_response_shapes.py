from __future__ import annotations

import copy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from Backend.Core.generation_requests import (
    GenerationRequest,
    OutputContract,
    make_request,
)
from Backend.Core.providers import _mlx_decoder_schema


def question_payload(identifier="0/0/0", *, multiple_choice=True):
    return {
        "id": identifier,
        "prompt": "A complete candidate question.",
        "choices": ["First", "Second", "Third", "Fourth"] if multiple_choice else [],
        "correct_choice": 0 if multiple_choice else None,
        "mark_scheme": [],
    }


def request_for(*shapes):
    return make_request(
        'Untrusted source says "kind": "multiple_choice" and "choices": []',
        OutputContract(
            "authoring",
            identifiers=tuple(row[0] for row in shapes),
            authoring_shapes=shapes,
        ),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"choices": []},
        {"choices": ["A", "B", "C"]},
        {"choices": ["same"] * 4},
        {"correct_choice": None},
        {"correct_choice": True},
        {"correct_choice": 4},
    ],
)
def test_owned_mcq_shape_rejects_malformed_model_output(changes):
    request = request_for(("0/0/0", "multiple_choice"))
    payload = {"questions": [{**question_payload(), **changes}]}
    assert list(Draft202012Validator(request.schema).iter_errors(payload))


def test_owned_non_mcq_shape_cannot_be_changed_by_candidate_prose():
    request = request_for(("0/0/0", "constructed_response"))
    validator = Draft202012Validator(request.schema)
    assert not list(
        validator.iter_errors({"questions": [question_payload(multiple_choice=False)]})
    )
    assert list(validator.iter_errors({"questions": [question_payload()]}))


def test_mixed_batch_shapes_remain_bound_to_their_owned_ids():
    request = request_for(
        ("0/0/0", "multiple_choice"), ("0/0/1", "constructed_response")
    )
    payload = {
        "questions": [
            question_payload(),
            question_payload("0/0/1", multiple_choice=False),
        ]
    }
    validator = Draft202012Validator(request.schema)
    assert not list(validator.iter_errors(payload))
    payload["questions"][0]["id"], payload["questions"][1]["id"] = "0/0/1", "0/0/0"
    assert list(validator.iter_errors(payload))


@pytest.mark.parametrize(
    "shapes",
    [
        [("0/0/0", "multiple_choice")],
        (("0/0/1", "multiple_choice"),),
        (("0/0/0", "unknown"),),
        (("0/0/0", True),),
        (("0/0/0", "multiple_choice", "private-answer"),),
        (("0/0/0", "multiple_choice"), ("0/0/0", "constructed_response")),
    ],
)
def test_malformed_or_unbound_authoring_metadata_refuses(shapes):
    with pytest.raises(ValueError, match="authoring shapes"):
        OutputContract("authoring", identifiers=("0/0/0",), authoring_shapes=shapes)


def test_authoring_metadata_is_not_allowed_on_another_operation():
    with pytest.raises(ValueError, match="authoring shapes"):
        OutputContract("review", authoring_shapes=(("0/0/0", "multiple_choice"),))


def test_legacy_contract_without_shapes_retains_its_broad_schema():
    request = make_request(
        "fixture", OutputContract("authoring", identifiers=("0/0/0",))
    )
    payload = question_payload()
    payload.update(choices=[], correct_choice=None)
    assert not list(
        Draft202012Validator(request.schema).iter_errors({"questions": [payload]})
    )


def test_mlx_decoder_keeps_shape_but_full_schema_still_checks_uniqueness():
    request = request_for(("0/0/0", "multiple_choice"))
    decoded = _mlx_decoder_schema(request.schema)
    properties = decoded["properties"]["questions"]["items"]["properties"]
    assert properties["choices"]["minItems"] == properties["choices"]["maxItems"] == 4
    assert properties["correct_choice"] == {
        "type": "integer",
        "minimum": 0,
        "maximum": 3,
    }
    # This backend's decoder cannot express uniqueItems; final validation can.
    assert "uniqueItems" not in properties["choices"]
    assert (
        request.schema["properties"]["questions"]["items"]["properties"]["choices"][
            "uniqueItems"
        ]
        is True
    )


def test_available_llguidance_compiles_all_owned_response_shapes():
    import json

    llguidance = pytest.importorskip("llguidance")
    for shapes in (
        (("0/0/0", "multiple_choice"),),
        (("0/0/0", "constructed_response"),),
        (("0/0/0", "multiple_choice"), ("0/0/1", "constructed_response")),
    ):
        request = request_for(*shapes)
        grammar = llguidance.grammar_from(
            "json_schema", json.dumps(_mlx_decoder_schema(request.schema))
        )
        assert not llguidance.LLMatcher.validate_grammar(grammar)


def test_forged_union_batch_identifier_metadata_refuses():
    request = request_for(
        ("0/0/0", "multiple_choice"), ("0/0/1", "constructed_response")
    )
    schema = copy.deepcopy(request.schema)
    schema["properties"]["questions"]["items"]["anyOf"][1]["properties"]["id"][
        "enum"
    ] = ["0/0/0"]
    with pytest.raises(ValueError, match="owned identifiers"):
        GenerationRequest(
            "fixture", "authoring", schema, expected_ids=("0/0/0", "0/0/1")
        )


def test_actual_accounting_mcq_authoring_binds_public_response_shape():
    from aqaaccountgen.cli import ADAPTER

    from Backend.Core.ai_assessment import (
        GenerationPolicy,
        _generate_item_transaction,
        _tasks,
    )

    root = Path(__file__).parents[1]
    syllabus = ADAPTER.load_syllabus(
        root / "Resources/accounting/aqa/generator/data/syllabus.json"
    )
    paper = ADAPTER.build(ADAPTER.load_rule("2"), syllabus, 270101)
    task = next(
        task
        for task in _tasks(paper, {topic.id: topic for topic in syllabus.topics})
        if task.question.number == "05"
    )
    requests = []

    class Client:
        provider = "apple"
        model = "fixture"

        def generate_request(self, request):
            requests.append(request)
            return {
                "questions": [
                    {
                        "id": task.id,
                        "prompt": "A business sets selling price per unit at £45, variable cost per unit at £10 and allocated fixed cost per unit at £5. What contribution per unit will this earn?",
                        "choices": task.question.choices,
                        "correct_choice": task.question.correct_choice,
                        "mark_scheme": [
                            point.model_dump(mode="json")
                            for point in task.question.structured_mark_scheme
                        ],
                    }
                ]
            }

        def generate_json(self, _prompt):
            raise AssertionError("the typed authoring route must be used")

    result = _generate_item_transaction(
        task,
        client=Client(),
        subject=ADAPTER.subject_label,
        seed=270101,
        policy=GenerationPolicy(require_model_review=False),
        progress=None,
        accepted_prompts=[],
    )
    assert result.correct_choice == 0
    assert result.choices[0] == "£35"
    assert len(requests) == 1
    properties = requests[0].schema["properties"]["questions"]["items"]["properties"]
    assert properties["choices"]["minItems"] == 4
    assert properties["correct_choice"]["type"] == "integer"
