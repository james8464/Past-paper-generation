from __future__ import annotations

import math

import pytest

from Backend.Core.assessment_package import (
    _authoring_provenance,
    validate_cross_paper_quality,
)


def _item(identifier: str, prompt: str) -> dict:
    return {
        "id": identifier,
        "prompt": prompt,
        "marks": 4,
        "topic_id": "markets",
        "command_word": "Explain",
        "intended_demand": "standard",
        "assessment_objectives": {"AO1": 1, "AO2": 1, "AO3": 2},
        "context": ["A supplied extract establishes the subject."],
    }


def test_cross_paper_quality_reports_mark_ao_topic_command_and_demand_balance() -> None:
    report = validate_cross_paper_quality(
        [
            _item("q1", "Explain one effect of the change."),
            {
                **_item("q2", "Evaluate whether the policy should continue."),
                "marks": 8,
                "topic_id": "policy",
                "command_word": "Evaluate",
                "intended_demand": "high",
                "assessment_objectives": {"AO1": 2, "AO2": 2, "AO3": 2, "AO4": 2},
            },
        ]
    )

    assert report["total_marks"] == 12
    assert report["assessment_objectives"] == {
        "AO1": 3,
        "AO2": 3,
        "AO3": 4,
        "AO4": 2,
    }
    assert report["command_words"] == {"Evaluate": 1, "Explain": 1}
    assert report["demand"] == {"high": 1, "standard": 1}


@pytest.mark.parametrize(
    ("item", "message"),
    [
        (_item("q1", "The correct answer is lower inflation."), "answer leakage"),
        (
            {**_item("q2", "It causes unemployment."), "context": []},
            "ambiguous opening pronoun",
        ),
        (
            {**_item("q3", "Calculate the result."), "chart_values": [math.inf]},
            "non-finite data",
        ),
    ],
)
def test_cross_paper_quality_fails_closed_on_unintended_clues_and_impossible_data(
    item: dict,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_cross_paper_quality([item])


def test_package_provenance_keeps_stem_edits_distinct_from_authored_questions() -> None:
    report = _authoring_provenance(
        [
            {"provenance": "ai-authored-stem-reviewed-contract"},
            *[
                {"provenance": "reviewed-deterministic-contract"}
                for _ in range(3)
            ],
        ]
    )

    assert report["ai_authored_stem_items"] == 1
    assert report["ai_authored_items"] == 0
    assert report["reviewed_fixed_items"] == 3
    assert report["unknown_items"] == 0
