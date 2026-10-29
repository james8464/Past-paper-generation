from __future__ import annotations

from types import SimpleNamespace

import pytest

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _candidate_question,
    _Task,
    _validate_checkpoint_item,
)
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedQuestion,
    MarkSchemePoint,
)

PAIR = [
    "The sale increases the asset account and the revenue account.",
    "The sale increases the revenue account and the asset account.",
]


def task(choices):
    point = MarkSchemePoint(text=choices[0], marks=1, assessment_objective="AO1")
    question = GeneratedQuestion(
        rule_id="Q01",
        number="1",
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        topic_id="double_entry",
        prompt="Select the correct effect of the sale.",
        choices=choices,
        correct_choice=0,
        mark_scheme=[point.text],
        structured_mark_scheme=[point],
        assessment_objectives={"AO1": 1},
        authoring_context={"preserve_prompt": True},
    )
    return _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Effect", questions=[question]),
        topic=object(),
    )


def candidate(current):
    return _candidate_question(
        current,
        {
            "prompt": current.question.prompt,
            "choices": current.question.choices,
            "correct_choice": 0,
            "mark_scheme": [
                {
                    "text": current.question.choices[0],
                    "marks": 1,
                    "assessment_objective": "AO1",
                }
            ],
        },
        client=SimpleNamespace(provider="fixture", model="fixture"),
        policy=GenerationPolicy(),
    )


def test_reordered_account_conjunction_cannot_be_accepted():
    current = task([*PAIR, "No accounts change.", "Only the bank account changes."])
    with pytest.raises(ValueError, match="unique choices"):
        candidate(current)


def test_reordered_account_conjunction_is_rejected_when_restoring_checkpoint():
    current = task([*PAIR, "No accounts change.", "Only the bank account changes."])
    with pytest.raises(ValueError, match="unique choices"):
        _validate_checkpoint_item(current, current.question)


@pytest.mark.parametrize(
    "pair",
    [
        [
            "The sale debits the asset account and credits the revenue account.",
            "The sale credits the asset account and debits the revenue account.",
        ],
        [PAIR[0], "The sale decreases the revenue account and the asset account."],
        [
            "The debit account precedes the credit account.",
            "The credit account precedes the debit account.",
        ],
    ],
)
def test_directional_or_different_predicate_options_remain_distinct(pair):
    current = task([*pair, "No accounts change.", "Only the bank account changes."])
    assert candidate(current).choices == current.question.choices
    _validate_checkpoint_item(current, current.question)
