"""Owned public strategic-change rate admission, without model inference."""

from copy import deepcopy
from decimal import Decimal

import pytest

from Backend.Core.subjects.selected_response import (
    selected_response_contract,
    solve_selected_response,
)


def item(external, strategic):
    return {
        "kind": "multiple_choice",
        "marks": 1,
        "choices": [
            "Strategic fit",
            "Strategic drift",
            "Tactical planning",
            "Diversification",
        ],
        "authoring_context": {
            "selected_response_contract": selected_response_contract(
                "strategic_drift",
                inputs={"external_change": external, "strategic_change": strategic},
            )
        },
    }


@pytest.mark.parametrize(
    "value", ["not-a-rate", "medium", "17", Decimal("17"), "", " high", "low "]
)
@pytest.mark.parametrize("placement", ["both", "external", "strategic"])
def test_unsupported_public_rate_refuses_without_mutating_input(value, placement):
    question = item(
        value if placement in {"both", "external"} else "high",
        value if placement in {"both", "strategic"} else "low",
    )
    original = deepcopy(question)
    with pytest.raises(ValueError, match="unsupported strategic-change classification"):
        solve_selected_response(question)
    assert question == original


@pytest.mark.parametrize(
    "external,strategic,answer",
    [
        ("high", "low", "Strategic drift"),
        ("high", "high", "Strategic fit"),
        ("low", "low", "Strategic fit"),
        ("HIGH", "Low", "Strategic drift"),
        ("HiGh", "HIGH", "Strategic fit"),
        ("LOW", "LoW", "Strategic fit"),
    ],
)
def test_supported_rate_pairs_keep_their_existing_results(external, strategic, answer):
    question = item(external, strategic)
    original = deepcopy(question)
    result = solve_selected_response(question)
    assert result["answer"] == answer
    assert result["mark_points"] == [answer]
    assert result["numeric_results"] == {}
    assert question == original


def test_reverse_supported_movement_still_refuses():
    question = item("low", "high")
    original = deepcopy(question)
    with pytest.raises(ValueError, match="unsupported strategic-change classification"):
        solve_selected_response(question)
    assert question == original


@pytest.mark.parametrize("mutation", ["missing", "extra", "rows", "format"])
def test_existing_contract_shape_refusals_remain(mutation):
    question = item("high", "low")
    contract = question["authoring_context"]["selected_response_contract"]
    if mutation == "missing":
        del contract["inputs"]["external_change"]
    elif mutation == "extra":
        contract["inputs"]["unrelated"] = "high"
    elif mutation == "rows":
        contract["rows"] = [{"label": "Unrelated"}]
    else:
        contract["decimal_places"] = 1
    original = deepcopy(question)
    with pytest.raises(ValueError):
        solve_selected_response(question)
    assert question == original
