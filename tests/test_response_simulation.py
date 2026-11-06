from __future__ import annotations

import json
from copy import deepcopy

import pytest

from Backend.Core.answer_projection import without_private_answer_keys
from Backend.Core.response_simulation import ResponseSimulator


def test_response_simulator_produces_monotonic_candidate_evidence() -> None:
    item = {
        "id": "q1",
        "prompt": "Evaluate the policy.",
        "mark_scheme": ["private drafting content"],
        "authoring_context": {
            "observable_mark_points": [
                "defines the policy",
                "develops a causal chain",
                "uses the source",
                "reaches a supported judgement",
            ],
            "misconception_targets": ["assumes correlation proves causation"],
        },
    }

    responses = ResponseSimulator().responses(item)

    assert [response.band for response in responses] == [
        "weak",
        "average",
        "excellent",
    ]
    assert [len(response.demonstrated_mark_points) for response in responses] == [
        1,
        2,
        4,
    ]
    assert responses[0].misconceptions
    assert not responses[-1].misconceptions
    assert all(
        "private drafting content" not in response.text for response in responses
    )


def test_model_simulation_context_excludes_the_draft_mark_scheme() -> None:
    class Client:
        prompt = ""

        def generate_json(self, prompt: str) -> dict[str, object]:
            self.prompt = prompt
            return {
                "responses": [
                    {
                        "band": band,
                        "text": f"{band} response",
                        "demonstrated_mark_points": [],
                        "evidence_ids": [],
                        "misconceptions": [],
                    }
                    for band in ("weak", "average", "excellent")
                ]
            }

    client = Client()
    ResponseSimulator(client).responses(
        {
            "id": "q2",
            "prompt": "Assess the evidence.",
            "mark_scheme": ["secret answer"],
        }
    )

    assert "secret answer" not in client.prompt


@pytest.mark.parametrize(
    "container", ["direct", "dict", "list", "mixed", "tuple", "mixed_tuple"]
)
def test_model_context_filters_nested_private_keys_without_changing_public_data(
    container,
):
    private = {
        "correct_choice": "PRIVATE_CHOICE_CANARY",
        "marking": {"points": ["PRIVATE_MARKING_CANARY"]},
        "observable_mark_points": ["PRIVATE_OBSERVABLE_CANARY"],
    }
    public = {"prompt": "Use the public table.", "choices": ["North", "South"]}
    payload = {**deepcopy(public), **private}
    nested = {
        "direct": payload,
        "dict": {"part": payload},
        "list": [payload],
        "mixed": [{"parts": [payload]}],
        "tuple": (payload,),
        "mixed_tuple": {"parts": ([payload],)},
    }[container]
    item = {
        "id": "owned",
        "prompt": "Explain the public result.",
        "source_data": {"credit": 7, "observations": [2, 4, 6]},
        "public_context": nested,
        "parts": [{"prompt": "Public subtask", "marking": private["marking"]}],
        "authoring_context": {
            "observable_mark_points": private["observable_mark_points"],
            "public_assumptions": "No inventory changes.",
        },
    }
    before = deepcopy(item)

    class Client:
        prompt = ""

        def generate_json(self, prompt):
            self.prompt = prompt
            return {
                "responses": [{"band": "owned", "text": "Owned diagnostic response"}]
            }

    client = Client()
    responses = ResponseSimulator(client).responses(item, bands=("owned",))
    sent = json.loads(client.prompt.split("\n", 1)[1])["item"]
    assert all(
        canary not in client.prompt
        for canary in (
            "PRIVATE_CHOICE_CANARY",
            "PRIVATE_MARKING_CANARY",
            "PRIVATE_OBSERVABLE_CANARY",
        )
    )
    assert sent["source_data"] == item["source_data"]
    assert sent["authoring_context"] == {"public_assumptions": "No inventory changes."}
    assert sent["parts"] == [{"prompt": "Public subtask"}]
    expected = {
        "direct": public,
        "dict": {"part": public},
        "list": [public],
        "mixed": [{"parts": [public]}],
        "tuple": [public],
        "mixed_tuple": {"parts": [[public]]},
    }[container]
    assert sent["public_context"] == expected
    assert item == before
    assert [response.band for response in responses] == ["owned"]


def test_private_key_filter_preserves_public_tuples_and_does_not_require_json():
    private = object()
    item = {
        "public": (
            {"choices": ("North", "South"), "correct_choice": "PRIVATE_CANARY"},
            [{"source_data": {"credit": 7}, "marking": "PRIVATE_CANARY"}],
        ),
        "mark_scheme": private,
    }
    before = deepcopy(item["public"])
    filtered = without_private_answer_keys(item)
    assert isinstance(filtered["public"], tuple)
    assert isinstance(filtered["public"][0]["choices"], tuple)
    assert filtered == {
        "public": ({"choices": ("North", "South")}, [{"source_data": {"credit": 7}}])
    }
    filtered["public"][1][0]["source_data"]["credit"] = 9
    assert item["public"] == before
    assert item["mark_scheme"] is private


def test_synthetic_path_keeps_raw_observable_points_and_input_unchanged():
    item = {
        "id": "owned-synthetic",
        "prompt": "Evaluate the public case.",
        "authoring_context": {
            "observable_mark_points": ["first", "second", "third", "fourth"],
            "misconception_targets": ["owned misconception"],
        },
    }
    before = deepcopy(item)
    responses = ResponseSimulator().responses(item)
    assert [response.model_dump() for response in responses] == [
        {
            "band": "weak",
            "text": "Candidate response at weak band. first Common error: owned misconception",
            "demonstrated_mark_points": ["first"],
            "evidence_ids": [],
            "misconceptions": ["owned misconception"],
            "available_mark_points": 4,
        },
        {
            "band": "average",
            "text": "Candidate response at average band. first second",
            "demonstrated_mark_points": ["first", "second"],
            "evidence_ids": [],
            "misconceptions": [],
            "available_mark_points": 4,
        },
        {
            "band": "excellent",
            "text": "Candidate response at excellent band. first second third fourth",
            "demonstrated_mark_points": ["first", "second", "third", "fourth"],
            "evidence_ids": [],
            "misconceptions": [],
            "available_mark_points": 4,
        },
    ]
    assert item == before
