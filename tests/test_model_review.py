from __future__ import annotations

import pytest

from Backend.Core.model_review import (
    ReviewResult,
    independent_review,
    require_independent_review,
)


class ReviewClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response

    def generate_json(self, _prompt: str) -> dict[str, object]:
        return self.response


def test_independent_review_returns_structured_repair_diagnostics() -> None:
    result = independent_review(
        ReviewClient(
            {
                "approved": False,
                "factual_issues": ["The exchange-rate direction is reversed."],
                "marking_issues": [],
                "source_issues": [],
                "difficulty_issues": [],
                "ambiguity_issues": [],
            }
        ),
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
