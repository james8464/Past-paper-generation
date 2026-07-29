from __future__ import annotations

import pytest

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    SectionRule,
    validate_generated_paper,
    validate_rule,
)


def rule() -> PaperRule:
    return PaperRule(
        id="paper_1",
        code="TEST/1",
        title="Test",
        duration_minutes=60,
        total_marks=10,
        allowed_topic_ids={"a"},
        sections=[
            SectionRule(
                id="A",
                title="Section A",
                option_count=2,
                answer_options=1,
                option_marks=10,
                questions=[QuestionRule(id="q", marks=10, kind="essay", command_word="evaluate")],
            )
        ],
    )


def paper() -> GeneratedPaper:
    question = lambda number: GeneratedQuestion(
        rule_id="q",
        number=number,
        marks=10,
        kind="essay",
        command_word="evaluate",
        topic_id="a",
        prompt=f"Evaluate option {number}.",
        mark_scheme=["Accurate analysis.", "Supported evaluation."],
    )
    return GeneratedPaper(
        paper_id="paper_1",
        paper_code="TEST/1",
        title="Test",
        duration_minutes=60,
        total_marks=10,
        seed=1,
        sections=[
            GeneratedSection(
                id="A",
                title="Section A",
                instructions="Answer one option.",
                options=[
                    GeneratedOption(id="1", title="Option 1", questions=[question("1")]),
                    GeneratedOption(id="2", title="Option 2", questions=[question("2")]),
                ],
            )
        ],
    )


def test_choice_marks_are_candidate_marks_not_all_printed_marks() -> None:
    validate_rule(rule(), {"a"})


def test_rule_rejects_bad_mark_total() -> None:
    value = rule()
    value.sections[0].questions[0].marks = 9
    with pytest.raises(ValueError, match="question marks total"):
        validate_rule(value, {"a"})


def test_generated_paper_rejects_duplicate_prompts() -> None:
    value = paper()
    value.sections[0].options[1].questions[0].prompt = "Evaluate option 1."
    with pytest.raises(ValueError, match="duplicated"):
        validate_generated_paper(value, rule(), {"a"})


def test_generated_paper_matches_contract() -> None:
    generated = paper()
    validate_generated_paper(generated, rule(), {"a"})
    question = generated.sections[0].options[0].questions[0]
    assert question.syllabus_outcomes == ["a"]
    assert sum(question.assessment_objectives.values()) == question.marks
    assert (
        sum(point.marks for point in question.structured_mark_scheme)
        == question.marks
    )
    assert question.expected_minutes == 60
    assert question.provenance == "built-in"
