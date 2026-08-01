from __future__ import annotations

from Backend.Core.ai_assessment import (
    GenerationPolicy,
    _Task,
    _batches_for_client,
    _clean_generated_prompt,
    _effective_batch_size,
    _generation_prompt,
    _normalise_level_allocations,
    _validate_mark_points,
)
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedQuestion,
    MarkSchemePoint,
)


class _Client:
    def __init__(self, *, parallel: bool) -> None:
        self.supports_parallel_generation = parallel


def test_local_generation_uses_smaller_structured_output_batches() -> None:
    policy = GenerationPolicy(batch_size=6)

    assert _effective_batch_size(_Client(parallel=False), policy) == 3
    assert _effective_batch_size(_Client(parallel=True), policy) == 6


def test_generated_prompt_drops_renderer_owned_number_and_mark_label() -> None:
    question = GeneratedQuestion(
        rule_id="q01",
        number="01",
        marks=1,
        kind="multiple_choice",
        command_word="select",
        topic_id="topic",
        prompt="Which source document records a credit purchase?",
        mark_scheme=["Purchase invoice."],
    )

    assert _clean_generated_prompt(
        "Question 01: Which document is evidence of a credit purchase? [1 mark]",
        question=question,
    ) == "Which document is evidence of a credit purchase?"
    assert _clean_generated_prompt(
        "1. Which document is evidence of a credit purchase?",
        question=question,
    ) == "Which document is evidence of a credit purchase?"


def test_local_batches_separate_high_mark_items() -> None:
    option = GeneratedOption(
        id="option",
        title="Option",
        questions=[],
    )

    def task(index: int, marks: int) -> _Task:
        return _Task(
            key=(0, 0, index),
            option=option,
            topic=object(),
            question=GeneratedQuestion(
                rule_id=f"q{index}",
                number=str(index + 1),
                marks=marks,
                kind="essay" if marks > 1 else "multiple_choice",
                command_word="assess" if marks > 1 else "select",
                topic_id="topic",
                prompt="Assess the decision." if marks > 1 else "Select the item.",
                mark_scheme=["Credit a valid response."],
            ),
        )

    tasks = [task(0, 1), task(1, 1), task(2, 1), task(3, 16), task(4, 12)]
    local = _batches_for_client(
        tasks,
        client=_Client(parallel=False),
        policy=GenerationPolicy(),
    )
    remote = _batches_for_client(
        tasks,
        client=_Client(parallel=True),
        policy=GenerationPolicy(),
    )

    assert [len(batch) for batch in local] == [3, 1, 1]
    assert [len(batch) for batch in remote] == [5]


def test_generation_prompt_withholds_planning_draft_content() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=4,
        kind="explain",
        command_word="explain",
        topic_id="topic",
        prompt="Explain the forbidden planning draft phrase.",
        mark_scheme=["Forbidden planning mark point."],
    )
    task = _Task(
        key=(0, 0, 0),
        question=question,
        option=GeneratedOption(id="option", title="Case study", questions=[question]),
        topic=type(
            "Topic",
            (),
            {
                "id": "topic",
                "title": "Topic title",
                "points": ["Specification point"],
            },
        )(),
    )

    prompt = _generation_prompt(
        [task],
        subject="Test subject",
        seed=123,
        attempt=1,
        previous_failure="",
    )

    assert "forbidden planning draft phrase" not in prompt.casefold()
    assert "forbidden planning mark point" not in prompt.casefold()
    assert "draft_to_replace" not in prompt


def test_levels_scheme_uses_ao_allocations_and_descriptors() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    points = [
        MarkSchemePoint(
            text="Accurate knowledge.",
            marks=3,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Applied case evidence.",
            marks=3,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text="Developed chain of reasoning.",
            marks=6,
            assessment_objective="AO3",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level} descriptor.",
                marks=0,
                credit_type="level",
            )
            for level in range(1, 4)
        ],
    ]

    _validate_mark_points(question, points)


def test_levels_scheme_requires_explicit_descriptors() -> None:
    import pytest

    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    points = [
        MarkSchemePoint(
            text="Knowledge.",
            marks=3,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application.",
            marks=3,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text="Analysis.",
            marks=6,
            assessment_objective="AO3",
        ),
    ]

    with pytest.raises(ValueError, match="level descriptors"):
        _validate_mark_points(question, points)


def test_levels_scheme_normalises_model_arithmetic_to_blueprint() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    raw = [
        MarkSchemePoint(
            text="Knowledge.",
            marks=1,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application.",
            marks=1,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text="Analysis.",
            marks=1,
            assessment_objective="AO3",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level}.",
                marks=level,
                credit_type="level",
                assessment_objective="AO3",
            )
            for level in range(1, 4)
        ],
    ]

    normalised = _normalise_level_allocations(question, raw)

    assert [point.marks for point in normalised] == [
        3,
        3,
        6,
        0,
        0,
        0,
        0,
        0,
        0,
    ]
    assert sum(point.marks for point in normalised) == 12
    _validate_mark_points(question, normalised)


def test_levels_scheme_recovers_unlabelled_substantive_ao_content() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    raw = [
        MarkSchemePoint(
            text="Accurate knowledge of the business concept.",
            marks=1,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application to the source evidence and business context.",
            marks=1,
            assessment_objective="AO2",
        ),
        MarkSchemePoint(
            text=(
                "A developed causal chain showing the effect on costs and "
                "therefore the consequence for profit."
            ),
            marks=0,
            assessment_objective=None,
        ),
        MarkSchemePoint(
            text="Additional acceptable indicative content.",
            marks=2,
            assessment_objective="AO2",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level}.",
                marks=level,
                credit_type="level",
                assessment_objective="AO3",
            )
            for level in range(1, 4)
        ],
    ]

    normalised = _normalise_level_allocations(question, raw)

    awarded = [point for point in normalised if point.marks]
    assert [(point.assessment_objective, point.marks) for point in awarded] == [
        ("AO1", 3),
        ("AO2", 3),
        ("AO3", 6),
    ]
    assert next(
        point for point in normalised if point.text.startswith("Additional")
    ).credit_type == "guidance"
    _validate_mark_points(question, normalised)


def test_levels_scheme_adds_missing_objective_rubric_row() -> None:
    question = GeneratedQuestion(
        rule_id="q1",
        number="1",
        marks=12,
        kind="analysis",
        command_word="analyse",
        topic_id="topic",
        prompt="Analyse the decision.",
        mark_scheme=["Levels-based marking."],
        assessment_objectives={"AO1": 3, "AO2": 3, "AO3": 6},
        scheme_mode="levels",
    )
    raw = [
        MarkSchemePoint(
            text="Accurate understanding of the concept.",
            marks=1,
            assessment_objective="AO1",
        ),
        MarkSchemePoint(
            text="Application to the source evidence.",
            marks=1,
            assessment_objective="AO2",
        ),
        *[
            MarkSchemePoint(
                text=f"Level {level}.",
                marks=level,
                credit_type="level",
                assessment_objective="AO3",
            )
            for level in range(1, 4)
        ],
    ]

    normalised = _normalise_level_allocations(question, raw)

    assert [point.assessment_objective for point in normalised[:3]] == [
        "AO1",
        "AO2",
        "AO3",
    ]
    assert "allocation within the levels grid" in normalised[2].text
    assert [point.marks for point in normalised[:3]] == [3, 3, 6]
    _validate_mark_points(question, normalised)
