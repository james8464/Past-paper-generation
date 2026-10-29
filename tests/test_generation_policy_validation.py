from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict

import pytest

from Backend.Core.ai_assessment import GenerationPolicy
from Backend.Core.assessment_quality import assert_distinct_items


@pytest.mark.parametrize("field", ["batch_size", "attempts", "max_workers"])
@pytest.mark.parametrize("invalid", [True, False, 0, -1, 1.5, "3", None, float("inf")])
def test_generation_counts_require_positive_non_boolean_integers(
    field: str, invalid: object
) -> None:
    with pytest.raises(ValueError, match=field):
        GenerationPolicy(**{field: invalid})


@pytest.mark.parametrize("field", ["draft_similarity_limit", "paper_similarity_limit"])
@pytest.mark.parametrize(
    "invalid",
    [
        True,
        False,
        -0.01,
        1.01,
        float("nan"),
        float("inf"),
        -float("inf"),
        "0.5",
        None,
        10**1000,
    ],
)
def test_similarity_limits_require_finite_numbers_in_the_score_range(
    field: str, invalid: object
) -> None:
    with pytest.raises(ValueError, match=field):
        GenerationPolicy(**{field: invalid})


@pytest.mark.parametrize("value", [0, 0.0, 0.5, 1, 1.0])
def test_similarity_score_boundaries_remain_valid(value: float) -> None:
    policy = GenerationPolicy(
        draft_similarity_limit=value, paper_similarity_limit=value
    )
    assert policy.draft_similarity_limit == value
    assert policy.paper_similarity_limit == value


def test_valid_positive_counts_keep_their_existing_values() -> None:
    policy = GenerationPolicy(batch_size=1, attempts=25, max_workers=100)
    assert (policy.batch_size, policy.attempts, policy.max_workers) == (1, 25, 100)


def test_policy_defaults_and_immutability_are_unchanged() -> None:
    policy = GenerationPolicy()
    assert asdict(policy) == {
        "batch_size": 6,
        "attempts": 3,
        "max_workers": 4,
        "draft_similarity_limit": 0.82,
        "paper_similarity_limit": 0.84,
        "require_model_review": True,
        "require_independent_solution": False,
        "require_difficulty_review": False,
    }
    with pytest.raises(FrozenInstanceError):
        policy.attempts = 0


def test_maximum_similarity_limit_still_rejects_an_identical_item() -> None:
    policy = GenerationPolicy(paper_similarity_limit=1)
    with pytest.raises(ValueError, match="similar"):
        assert_distinct_items(
            [
                {"id": "one", "prompt": "A repeated question."},
                {"id": "two", "prompt": "A repeated question."},
            ],
            threshold=policy.paper_similarity_limit,
        )


def test_zero_similarity_limit_keeps_its_strict_comparison_semantics() -> None:
    policy = GenerationPolicy(paper_similarity_limit=0)
    with pytest.raises(ValueError, match="similar"):
        assert_distinct_items(
            [
                {"id": "one", "prompt": "Completely unrelated vocabulary."},
                {"id": "two", "prompt": "Another distinct sentence."},
            ],
            threshold=policy.paper_similarity_limit,
        )
