from __future__ import annotations

from types import SimpleNamespace

import pytest

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _candidate_question,
    _generate_item_transaction,
    _Task,
    _validate_checkpoint_item,
)
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedQuestion,
    MarkSchemePoint,
)

CHOICES = [
    "Income is recorded only when cash is received.",
    "Expenses are recognised only when cash is paid.",
    "Income is recorded when it is earned.",
    "Costs are ignored until the period ends.",
]
STEM = "Select the statement that correctly applies the accruals concept."
POLICY = GenerationPolicy(attempts=2, require_model_review=False)


def _task() -> _Task:
    question = GeneratedQuestion(
        rule_id="accounting_concept",
        number="03",
        marks=1,
        kind="multiple_choice",
        command_word="Select",
        topic_id="accounting-5",
        prompt="Which accounting convention matches a transaction to its reporting period?",
        choices=CHOICES,
        correct_choice=2,
        mark_scheme=[CHOICES[2]],
        structured_mark_scheme=[
            MarkSchemePoint(text=CHOICES[2], marks=1, assessment_objective="AO1")
        ],
        assessment_objectives={"AO1": 1},
    )
    return _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="case", title="Accounting", questions=[question]),
        topic=SimpleNamespace(
            id="accounting-5", title="Accounting concepts", points=[]
        ),
    )


def _response(prompt: str) -> dict[str, object]:
    return {
        "id": "0/0/0",
        "prompt": prompt,
        "choices": CHOICES,
        "correct_choice": 2,
        "mark_scheme": [
            {"text": CHOICES[2], "marks": 1, "assessment_objective": "AO1"}
        ],
    }


class Writer:
    provider = "test"
    model = "fixture"

    def __init__(self, prompts: list[str]) -> None:
        self.responses = iter(prompts)
        self.requests: list[str] = []

    def generate_json(self, prompt: str) -> dict[str, object]:
        self.requests.append(prompt)
        return {"questions": [_response(next(self.responses))]}


@pytest.mark.parametrize(
    ("separator", "label_suffix"), [(" ", "."), ("\n", ")"), ("\n", ":")]
)
def test_mcq_writer_cannot_embed_the_structured_choices_in_its_stem(
    separator: str, label_suffix: str
) -> None:
    alternatives = separator.join(
        f"{label}{label_suffix} {choice}"
        for label, choice in zip("ABCD", CHOICES, strict=True)
    )
    with pytest.raises(ValueError, match=r"alternatives.*choices"):
        _candidate_question(
            _task(),
            _response(STEM + separator + alternatives),
            client=Writer([]),
            policy=POLICY,
        )


@pytest.mark.parametrize(
    "label_format",
    ["**{}.**", "**{}**.", "__{}.__", "{} -", "{} \u2013", "{} \u2014", "({})"],
)
def test_formatted_option_labels_cannot_hide_a_duplicate_mcq_list(
    label_format: str,
) -> None:
    prompt = (
        STEM
        + "\n"
        + "\n".join(
            f"{label_format.format(label)} {choice}"
            for label, choice in zip("ABCD", CHOICES, strict=True)
        )
    )
    with pytest.raises(ValueError, match=r"alternatives.*choices"):
        _candidate_question(
            _task(), _response(prompt), client=Writer([]), policy=POLICY
        )


@pytest.mark.parametrize(
    "prompt",
    [
        STEM,
        "A business supplies goods on credit.\nSelect the correct accounting treatment.",
        "Select the correct treatment. Option A and option B refer to cash movements.",
        "A. The business supplies goods on credit.\nB. Its customer pays later.\n"
        "C. Accounts are prepared at year end.\nD. Select the correct treatment.",
    ],
)
def test_mcq_stems_keep_legitimate_references_and_multiline_source(prompt: str) -> None:
    candidate = _candidate_question(
        _task(),
        _response(prompt),
        client=Writer([]),
        policy=POLICY,
    )
    assert candidate.prompt == " ".join(prompt.split())
    assert candidate.choices == CHOICES


def test_non_mcq_labelled_source_is_not_treated_as_a_duplicate_choice_list() -> None:
    task = _task()
    question = task.question.model_copy(
        update={"kind": "analysis", "choices": [], "correct_choice": None}
    )
    task = _Task(key=task.key, question=question, option=task.option, topic=task.topic)
    prompt = (
        STEM
        + "\n"
        + "\n".join(
            f"{label}. {choice}" for label, choice in zip("ABCD", CHOICES, strict=True)
        )
    )
    candidate = _candidate_question(
        task, _response(prompt), client=Writer([]), policy=POLICY
    )
    assert candidate.prompt == " ".join(prompt.split())
    assert candidate.choices == []


def test_embedded_options_trigger_a_writer_retry_not_silent_stem_stripping() -> None:
    invalid = (
        STEM
        + " "
        + " ".join(
            f"{label}. {choice}" for label, choice in zip("ABCD", CHOICES, strict=True)
        )
    )
    client = Writer([invalid, STEM])
    candidate = _generate_item_transaction(
        _task(),
        client=client,
        subject="aqa/accounting",
        seed=270100,
        policy=POLICY,
        progress=None,
        accepted_prompts=[],
    )
    assert len(client.requests) == 2
    assert "alternatives" in client.requests[1]
    assert candidate.prompt == STEM
    assert candidate.choices == CHOICES


def test_existing_checkpoint_validation_keeps_its_historical_contract() -> None:
    task = _task()
    historical = task.question.model_copy(
        update={
            "prompt": STEM
            + " "
            + " ".join(
                f"{label}. {choice}"
                for label, choice in zip("ABCD", CHOICES, strict=True)
            )
        }
    )
    _validate_checkpoint_item(task, historical)
