from __future__ import annotations

import pytest

from Backend.Core import model_review
from Backend.Core.model_review import (
    ReviewResult,
    independent_review,
    require_independent_review,
)


class ReviewClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.prompt = ""

    def generate_json(self, prompt: str) -> dict[str, object]:
        self.prompt = prompt
        return self.response


def test_independent_review_returns_structured_repair_diagnostics() -> None:
    client = ReviewClient(
        {
            "approved": False,
            "factual_issues": ["The exchange-rate direction is reversed."],
            "marking_issues": [],
            "source_issues": [],
            "difficulty_issues": [],
            "ambiguity_issues": [],
        }
    )
    result = independent_review(
        client,
        item_id="q1",
        subject="Economics",
        blueprint={"marks": 4},
        candidate={"prompt": "Explain the effect."},
        specification={"topic": "exchange rates"},
    )

    assert result == ReviewResult(
        approved=False,
        factual_issues=["The exchange-rate direction is reversed."],
    )
    assert result.issues == ["The exchange-rate direction is reversed."]
    assert "Semantically equivalent original wording is expected" in client.prompt


def test_require_independent_review_preserves_rejecting_wrapper_behavior() -> None:
    client = ReviewClient(
        {
            "approved": False,
            "factual_issues": [],
            "marking_issues": [],
            "source_issues": [],
            "difficulty_issues": [],
            "ambiguity_issues": [],
        }
    )

    with pytest.raises(ValueError, match="not approved"):
        require_independent_review(
            client,
            item_id="q1",
            subject="Economics",
            blueprint={},
            candidate={},
            specification={},
        )


def test_independent_review_rejects_approval_with_reported_issues() -> None:
    result = independent_review(
        ReviewClient(
            {
                "approved": True,
                "factual_issues": [],
                "marking_issues": ["The scheme cannot award all four marks."],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        ),
        item_id="q1",
        subject="Economics",
        blueprint={},
        candidate={},
        specification={},
    )

    assert result.approved is False
    assert result.marking_issues == ["The scheme cannot award all four marks."]


def test_difficulty_review_is_a_separate_structured_judgement() -> None:
    client = ReviewClient(
        {
            "approved": False,
            "estimated_demand": "low",
            "reasoning_steps": 1,
            "tariff_fit": False,
            "command_word_fit": False,
            "context_fit": True,
            "profile_fit": False,
            "issues": ["The response requires recall only, not evaluation."],
        }
    )

    result = model_review.difficulty_review(
        client,
        item_id="q8",
        subject="Economics",
        target={
            "demand_band": "high",
            "minimum_reasoning_steps": 4,
            "requires_judgement": True,
        },
        candidate={"prompt": "State one effect.", "marks": 15},
        specification={"topic": "market failure"},
    )

    assert result == model_review.DifficultyReviewResult(
        approved=False,
        estimated_demand="low",
        reasoning_steps=1,
        tariff_fit=False,
        command_word_fit=False,
        context_fit=True,
        profile_fit=False,
        issues=["The response requires recall only, not evaluation."],
    )
    assert "difficulty calibration specialist" in client.prompt
    assert "factual correctness is reviewed separately" in client.prompt


def test_require_difficulty_review_rejects_under_demanded_item() -> None:
    client = ReviewClient(
        {
            "approved": True,
            "estimated_demand": "standard",
            "reasoning_steps": 2,
            "tariff_fit": True,
            "command_word_fit": True,
            "context_fit": True,
            "profile_fit": True,
            "issues": [],
        }
    )

    with pytest.raises(ValueError, match="minimum 4"):
        model_review.require_difficulty_review(
            client,
            item_id="q8",
            subject="Economics",
            target={
                "demand_band": "high",
                "minimum_reasoning_steps": 4,
                "requires_judgement": True,
            },
            candidate={"prompt": "Evaluate the decision.", "marks": 15},
            specification={"topic": "market failure"},
        )
