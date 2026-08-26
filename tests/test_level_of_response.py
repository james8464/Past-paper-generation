from __future__ import annotations

from pathlib import Path

from Backend.Core.level_of_response import (
    LevelOfResponseEngine,
    load_level_policies,
)
from Backend.Core.response_simulation import CandidateResponse

ROOT = Path(__file__).resolve().parents[1]


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
