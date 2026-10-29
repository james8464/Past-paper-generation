from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from Backend.Core.level_of_response import (
    BoardLevelPolicy,
    LevelDescriptor,
    LevelOfResponseEngine,
    load_level_policies,
    scale_level_policy,
)
from Backend.Core.response_simulation import CandidateResponse

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("tariff", [1, 2, 3])
def test_scaling_refuses_a_tariff_with_fewer_marks_than_positive_bands(tariff):
    policy = load_level_policies(
        ROOT / "Resources" / "level-of-response-policies.json"
    )["aqa-standard-4-level"]
    with pytest.raises(ValueError, match=r"band|level"):
        scale_level_policy(policy, tariff)


def test_level_descriptor_rejects_an_inverted_mark_range():
    with pytest.raises(ValidationError, match="mark"):
        LevelDescriptor(
            level=1,
            minimum_mark=4,
            maximum_mark=3,
            minimum_coverage=0.1,
            descriptor="Invalid range",
        )


@pytest.mark.parametrize(
    "malformation",
    ["duplicate", "overlap", "coverage", "missing_zero", "zero_threshold", "gapped"],
)
def test_level_policy_rejects_inconsistent_bands(malformation):
    policy = load_level_policies(
        ROOT / "Resources" / "level-of-response-policies.json"
    )["aqa-standard-4-level"].model_dump()
    levels = policy["levels"]
    if malformation == "duplicate":
        levels[2]["level"] = levels[1]["level"]
    elif malformation == "overlap":
        levels[2]["minimum_mark"] = levels[1]["maximum_mark"]
    elif malformation == "coverage":
        levels[2]["minimum_coverage"] = levels[1]["minimum_coverage"]
    elif malformation == "missing_zero":
        del levels[0]
    elif malformation == "gapped":
        for index, level in enumerate(levels):
            level["level"] = index * 2
    else:
        levels[0]["minimum_coverage"] = 0.005
    with pytest.raises(ValidationError):
        BoardLevelPolicy.model_validate(policy)


def test_all_current_policies_and_supported_scalings_keep_valid_mark_bands():
    policies = load_level_policies(
        ROOT / "Resources" / "level-of-response-policies.json"
    )
    assert len(policies) == 9
    for policy in policies.values():
        assert BoardLevelPolicy.model_validate(policy.model_dump()) == policy
        assert scale_level_policy(policy, policy.maximum_mark) is policy
        count = sum(level.level > 0 for level in policy.levels)
        for tariff in range(count, 31):
            scaled = scale_level_policy(policy, tariff)
            assert all(
                0 <= level.minimum_mark <= level.maximum_mark <= tariff
                for level in scaled.levels
            )
            assert scaled.levels[-1].maximum_mark == tariff


def test_all_supported_boards_have_data_backed_best_fit_policies() -> None:
    policies = load_level_policies(
        ROOT / "Resources" / "level-of-response-policies.json"
    )

    assert {policy.board for policy in policies.values()} == {
        "aqa",
        "ocr",
        "pearson-edexcel",
        "cambridge-international",
    }
    assert all(
        policy.levels and policy.maximum_mark > 0 for policy in policies.values()
    )


def test_aqa_economics_tariffs_are_registered_with_their_exact_mark_bands() -> None:
    policies = load_level_policies(
        ROOT / "Resources" / "level-of-response-policies.json"
    )

    expected = {
        "aqa-economics-9-mark": [(0, 0), (1, 3), (4, 6), (7, 9)],
        "aqa-economics-10-mark": [(0, 0), (1, 3), (4, 7), (8, 10)],
        "aqa-economics-15-mark": [(0, 0), (1, 5), (6, 10), (11, 15)],
        "aqa-economics-25-mark": [
            (0, 0),
            (1, 5),
            (6, 10),
            (11, 15),
            (16, 20),
            (21, 25),
        ],
    }
    for policy_id, mark_bands in expected.items():
        policy = policies[policy_id]
        assert [
            (level.minimum_mark, level.maximum_mark) for level in policy.levels
        ] == (mark_bands)


def test_level_engine_marks_weak_average_and_excellent_responses_monotonically() -> (
    None
):
    policy = load_level_policies(
        ROOT / "Resources" / "level-of-response-policies.json"
    )["aqa-standard-4-level"]
    responses = [
        CandidateResponse(
            band="weak",
            text="A limited assertion.",
            demonstrated_mark_points=["definition"],
            misconceptions=["unsupported causal claim"],
        ),
        CandidateResponse(
            band="average",
            text="A developed answer.",
            demonstrated_mark_points=["definition", "application", "analysis"],
        ),
        CandidateResponse(
            band="excellent",
            text="A sustained and supported judgement.",
            demonstrated_mark_points=[
                "definition",
                "application",
                "analysis",
                "evaluation",
            ],
        ),
    ]

    decisions = [
        LevelOfResponseEngine().mark(response, policy) for response in responses
    ]

    assert decisions[0].mark < decisions[1].mark < decisions[2].mark
    assert decisions[0].cap_applied is not None
    assert all(
        len(decision.annotations) == policy.maximum_mark for decision in decisions
    )
    assert all(
        annotation.reason
        for decision in decisions
        for annotation in decision.annotations
    )
