"""Private solver reasoning has its own bounded text contract."""

import json

import pytest
from jsonschema import Draft202012Validator

from Backend.Core.generation_requests import OutputContract
from Backend.Core.providers import _ollama_json_schema


@pytest.fixture(params=["open", "multiple_choice", "slots"])
def schema(request):
    item = {"kind": request.param}
    if request.param == "multiple_choice":
        item["choices"] = ["A", "B", "C", "D"]
    if request.param == "slots":
        item["response_slots"] = ["a", "b"]
    prompt = "Independently solve this item.\n" + json.dumps({"item": item})
    legacy = _ollama_json_schema(prompt)
    typed = _ollama_json_schema(
        "Trusted request",
        contract=OutputContract(
            "solver",
            kind=item["kind"],
            choices=tuple(item.get("choices", [])),
            response_slots=tuple(item.get("response_slots", [])),
        ),
    )
    assert legacy == typed
    return typed


@pytest.mark.parametrize("length", [289, 512])
def test_private_reasoning_steps_allow_bounded_complete_explanations(schema, length):
    validator = Draft202012Validator(schema["properties"]["steps"])
    assert validator.is_valid(["x" * length])


def test_reasoning_retains_step_count_and_explicit_513_character_refusal(schema):
    validator = Draft202012Validator(schema["properties"]["steps"])
    assert not validator.is_valid(["x" * 513])
    assert validator.is_valid(["x"] * 16)
    assert not validator.is_valid(["x"] * 17)


@pytest.mark.parametrize(
    "field",
    [
        "evidence_ids",
        "alternatives",
        "partial_credit_boundaries",
        "follow_through_rules",
    ],
)
def test_other_short_text_contracts_stay_at_240(schema, field):
    validator = Draft202012Validator(schema["properties"][field])
    assert validator.is_valid(["x" * 240])
    assert not validator.is_valid(["x" * 241])


def test_reasoning_counts_unicode_codepoints_without_normalisation(schema):
    validator = Draft202012Validator(schema["properties"]["steps"])
    assert validator.is_valid(["e\u0301" * 256])
    assert not validator.is_valid(["e\u0301" * 257])


def test_mark_points_keep_the_original_short_text_limit(schema):
    marking = schema["properties"]["mark_points"]
    if marking["type"] == "object":
        marking = marking["properties"]["a"]
        valid, invalid = "x" * 240, "x" * 241
    elif "enum" in marking["items"]:
        valid, invalid = ["A"], ["Not a supplied choice"]
    else:
        valid, invalid = ["x" * 240], ["x" * 241]
    validator = Draft202012Validator(marking)
    assert validator.is_valid(valid)
    assert not validator.is_valid(invalid)
