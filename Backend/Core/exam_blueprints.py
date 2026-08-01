from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, Field


class QuestionRule(BaseModel):
    id: str
    marks: int = Field(gt=0)
    kind: str
    command_word: str
    assessment_objectives: dict[str, int] = Field(default_factory=dict)
    intended_demand: Literal["low", "standard", "high"] | None = None
    expected_minutes: float | None = Field(default=None, gt=0)


class SectionRule(BaseModel):
    id: str
    title: str
    option_count: int = Field(gt=0)
    answer_options: int = Field(gt=0)
    option_marks: int = Field(gt=0)
    questions: list[QuestionRule]

    @property
    def candidate_marks(self) -> int:
        return self.answer_options * self.option_marks


class PaperRule(BaseModel):
    id: str
    code: str
    title: str
    duration_minutes: int = Field(gt=0)
    total_marks: int = Field(gt=0)
    allowed_topic_ids: set[str]
    sections: list[SectionRule]


class MarkSchemePoint(BaseModel):
    text: str = Field(min_length=1)
    marks: int = Field(ge=0)
    credit_type: Literal["answer", "point", "level", "guidance"] = "point"
    assessment_objective: str | None = None
    alternatives: list[str] = Field(default_factory=list)
    allow: list[str] = Field(default_factory=list)
    do_not_accept: list[str] = Field(default_factory=list)
    ignore: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)


class GeneratedQuestion(BaseModel):
    rule_id: str
    number: str
    marks: int = Field(gt=0)
    kind: str
    command_word: str
    topic_id: str
    prompt: str
    mark_scheme: list[str]
    choices: list[str] = Field(default_factory=list)
    correct_choice: int | None = None
    syllabus_outcomes: list[str] = Field(default_factory=list)
    assessment_objectives: dict[str, int] = Field(default_factory=dict)
    intended_demand: Literal["low", "standard", "high"] = "standard"
    expected_minutes: float | None = Field(default=None, gt=0)
    scheme_mode: Literal["points", "levels"] = "points"
    structured_mark_scheme: list[MarkSchemePoint] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    provenance: str = "built-in"


class GeneratedOption(BaseModel):
    id: str
    title: str
    stimulus: list[str] = Field(default_factory=list)
    chart_title: str = ""
    chart_labels: list[str] = Field(default_factory=list)
    chart_values: list[float] = Field(default_factory=list)
    questions: list[GeneratedQuestion]


class GeneratedSection(BaseModel):
    id: str
    title: str
    instructions: str
    options: list[GeneratedOption]


class GeneratedPaper(BaseModel):
    paper_id: str
    paper_code: str
    title: str
    duration_minutes: int
    total_marks: int
    seed: int
    sections: list[GeneratedSection]


def validate_rule(rule: PaperRule, syllabus_topic_ids: Iterable[str]) -> None:
    syllabus_ids = set(syllabus_topic_ids)
    if not rule.sections:
        raise ValueError(f"{rule.id} has no sections")
    if not rule.allowed_topic_ids:
        raise ValueError(f"{rule.id} has no allowed topics")
    unknown = rule.allowed_topic_ids - syllabus_ids
    if unknown:
        raise ValueError(f"{rule.id} references unknown topics: {sorted(unknown)}")

    section_ids: set[str] = set()
    candidate_total = 0
    for section in rule.sections:
        if section.id in section_ids:
            raise ValueError(f"{rule.id} repeats section {section.id}")
        section_ids.add(section.id)
        if section.answer_options > section.option_count:
            raise ValueError(f"{rule.id} section {section.id} answers more options than printed")
        marks = sum(question.marks for question in section.questions)
        for question in section.questions:
            if not question.assessment_objectives:
                question.assessment_objectives = _objective_allocation(
                    marks=question.marks,
                    kind=question.kind,
                    command_word=question.command_word,
                )
            if sum(question.assessment_objectives.values()) != question.marks:
                raise ValueError(
                    f"{rule.id} question {question.id} AO marks do not total "
                    f"{question.marks}"
                )
            if question.intended_demand is None:
                question.intended_demand = _demand_band(
                    marks=question.marks,
                    command_word=question.command_word,
                )
            if question.expected_minutes is None:
                question.expected_minutes = round(
                    rule.duration_minutes * question.marks / rule.total_marks,
                    2,
                )
        if marks != section.option_marks:
            raise ValueError(
                f"{rule.id} section {section.id} question marks total {marks}, "
                f"expected {section.option_marks}"
            )
        candidate_total += section.candidate_marks
    if candidate_total != rule.total_marks:
        raise ValueError(
            f"{rule.id} candidate marks total {candidate_total}, expected {rule.total_marks}"
        )


def validate_generated_paper(
    paper: GeneratedPaper,
    rule: PaperRule,
    syllabus_topic_ids: Iterable[str],
) -> None:
    validate_rule(rule, syllabus_topic_ids)
    if (
        paper.paper_id,
        paper.paper_code,
        paper.duration_minutes,
        paper.total_marks,
    ) != (rule.id, rule.code, rule.duration_minutes, rule.total_marks):
        raise ValueError("generated paper identity does not match its rule")
    if len(paper.sections) != len(rule.sections):
        raise ValueError("generated paper has the wrong section count")

    seen_prompts: set[tuple[str, str]] = set()
    for generated_section, section_rule in zip(paper.sections, rule.sections, strict=True):
        if generated_section.id != section_rule.id:
            raise ValueError(f"expected section {section_rule.id}, got {generated_section.id}")
        if len(generated_section.options) != section_rule.option_count:
            raise ValueError(
                f"section {section_rule.id} has {len(generated_section.options)} options, "
                f"expected {section_rule.option_count}"
            )
        for option in generated_section.options:
            if len(option.questions) != len(section_rule.questions):
                raise ValueError(f"section {section_rule.id} option {option.id} has wrong question count")
            if option.chart_values and len(option.chart_labels) != len(option.chart_values):
                raise ValueError(f"section {section_rule.id} option {option.id} has invalid chart data")
            for question, question_rule in zip(
                option.questions, section_rule.questions, strict=True
            ):
                _hydrate_assessment_metadata(
                    question,
                    question_rule=question_rule,
                )
                expected = (
                    question_rule.id,
                    question_rule.marks,
                    question_rule.kind,
                    question_rule.command_word,
                )
                actual = (
                    question.rule_id,
                    question.marks,
                    question.kind,
                    question.command_word,
                )
                if actual != expected:
                    raise ValueError(f"question {question.number} does not match rule {question_rule.id}")
                if (
                    question.assessment_objectives
                    != question_rule.assessment_objectives
                    or question.intended_demand != question_rule.intended_demand
                    or question.expected_minutes != question_rule.expected_minutes
                ):
                    raise ValueError(
                        f"question {question.number} assessment metadata does not "
                        f"match rule {question_rule.id}"
                    )
                if question.topic_id not in rule.allowed_topic_ids:
                    raise ValueError(f"question {question.number} uses an out-of-scope topic")
                unknown_outcomes = (
                    set(question.syllabus_outcomes) - rule.allowed_topic_ids
                )
                if unknown_outcomes:
                    raise ValueError(
                        f"question {question.number} uses out-of-scope syllabus "
                        f"outcomes: {sorted(unknown_outcomes)}"
                    )
                prompt_key = " ".join(question.prompt.casefold().split())
                stimulus_key = " ".join(
                    " ".join(option.stimulus).casefold().split()
                )
                uniqueness_key = (prompt_key, stimulus_key)
                if not prompt_key or uniqueness_key in seen_prompts:
                    raise ValueError(f"question {question.number} is empty or duplicated")
                seen_prompts.add(uniqueness_key)
                if (
                    question.kind != "multiple_choice"
                    and not _prompt_uses_command_word(
                        question.prompt,
                        question_rule.command_word,
                    )
                ):
                    raise ValueError(
                        f"question {question.number} prompt does not use command "
                        f"word {question_rule.command_word!r}"
                    )
                if not question.mark_scheme:
                    raise ValueError(f"question {question.number} has no mark scheme")
                if sum(question.assessment_objectives.values()) != question.marks:
                    raise ValueError(
                        f"question {question.number} assessment objectives total "
                        f"{sum(question.assessment_objectives.values())}, "
                        f"expected {question.marks}"
                    )
                if (
                    sum(point.marks for point in question.structured_mark_scheme)
                    != question.marks
                ):
                    raise ValueError(
                        f"question {question.number} structured scheme does not "
                        "trace every mark"
                    )
                awarded_objectives: dict[str, int] = {}
                for point in question.structured_mark_scheme:
                    if point.marks and not point.assessment_objective:
                        raise ValueError(
                            f"question {question.number} has an awarded mark "
                            "without an assessment objective"
                        )
                    if point.assessment_objective:
                        awarded_objectives[point.assessment_objective] = (
                            awarded_objectives.get(point.assessment_objective, 0)
                            + point.marks
                        )
                if awarded_objectives != question.assessment_objectives:
                    raise ValueError(
                        f"question {question.number} structured scheme AO "
                        f"allocation {awarded_objectives} does not match "
                        f"{question.assessment_objectives}"
                    )
                normalised_points = {
                    " ".join(point.text.casefold().split())
                    for point in question.structured_mark_scheme
                }
                if len(normalised_points) != len(question.structured_mark_scheme):
                    raise ValueError(
                        f"question {question.number} repeats a mark-scheme point"
                    )
                if question.kind == "multiple_choice":
                    if len(question.choices) != 4 or question.correct_choice not in range(4):
                        raise ValueError(f"question {question.number} has invalid multiple-choice data")
                    correct = question.choices[question.correct_choice].casefold()
                    scheme = " ".join(question.mark_scheme).casefold()
                    if correct not in scheme:
                        raise ValueError(
                            f"question {question.number} scheme does not identify "
                            "the correct option"
                        )


def _hydrate_assessment_metadata(
    question: GeneratedQuestion,
    *,
    question_rule: QuestionRule,
) -> None:
    if not question.syllabus_outcomes:
        question.syllabus_outcomes = [question.topic_id]
    if not question.assessment_objectives:
        question.assessment_objectives = dict(
            question_rule.assessment_objectives
        )
    if question.expected_minutes is None:
        question.expected_minutes = question_rule.expected_minutes
    question.intended_demand = (
        question_rule.intended_demand or question.intended_demand
    )
    if any(
        point.casefold().startswith(("level ", "levels-based"))
        for point in question.mark_scheme
    ):
        question.scheme_mode = "levels"
    if not question.structured_mark_scheme:
        question.structured_mark_scheme = _structured_scheme(question)


def _prompt_uses_command_word(prompt: str, command_word: str) -> bool:
    aliases = {
        "analyse": {"analyse", "analyze"},
        "analyze": {"analyse", "analyze"},
    }
    expected = aliases.get(command_word.casefold(), {command_word.casefold()})
    words = {
        word.strip(".,:;!?()[]{}'\"").casefold()
        for word in prompt.split()
    }
    return bool(words & expected)


def _objective_allocation(
    *,
    marks: int,
    kind: str,
    command_word: str,
) -> dict[str, int]:
    if kind == "multiple_choice":
        return {"AO1": marks}
    if kind in {"calculation", "data"}:
        return {"AO2": marks}
    if marks >= 8:
        ao1 = max(1, round(marks * 0.2))
        ao2 = max(1, round(marks * 0.2))
        ao3 = max(1, round(marks * 0.3))
        return {
            "AO1": ao1,
            "AO2": ao2,
            "AO3": ao3,
            "AO4": marks - ao1 - ao2 - ao3,
        }
    if command_word.casefold() in {"explain", "analyse", "analyze"}:
        ao1 = (marks + 1) // 2
        return {"AO1": ao1, "AO2": marks - ao1}
    return {"AO1": marks}


def _demand_band(
    *,
    marks: int,
    command_word: str,
) -> Literal["low", "standard", "high"]:
    command = command_word.casefold()
    if marks >= 12 or command in {"assess", "evaluate", "discuss"}:
        return "high"
    if marks <= 3 or command in {"identify", "select", "state"}:
        return "low"
    return "standard"


def _structured_scheme(question: GeneratedQuestion) -> list[MarkSchemePoint]:
    if question.kind == "multiple_choice":
        return [
            MarkSchemePoint(
                text=question.mark_scheme[0],
                marks=question.marks,
                credit_type="answer",
                assessment_objective=next(
                    iter(question.assessment_objectives),
                    None,
                ),
            )
        ]

    guidance_prefixes = (
        "ao1",
        "ao2",
        "ao3",
        "ao4",
        "level ",
        "levels-based",
        "marker check",
        "do not award",
        "maximum ",
    )
    content_indices = [
        index
        for index, text in enumerate(question.mark_scheme)
        if not text.casefold().startswith(guidance_prefixes)
    ]
    if not content_indices:
        content_indices = [0]
    objectives = [
        objective
        for objective, count in question.assessment_objectives.items()
        for _ in range(count)
    ]
    allocation: dict[tuple[int, str], int] = {}
    for mark, objective in enumerate(objectives):
        index = content_indices[mark % len(content_indices)]
        key = (index, objective)
        allocation[key] = allocation.get(key, 0) + 1

    result: list[MarkSchemePoint] = []
    for index, text in enumerate(question.mark_scheme):
        lowered = text.casefold()
        if lowered.startswith(("level ", "levels-based")):
            credit_type = "level"
        elif index not in content_indices:
            credit_type = "guidance"
        else:
            credit_type = "point"
        entries = [
            (objective, marks)
            for (allocated_index, objective), marks in allocation.items()
            if allocated_index == index
        ]
        if not entries:
            result.append(
                MarkSchemePoint(
                    text=text,
                    marks=0,
                    credit_type=credit_type,
                    assessment_objective=None,
                )
            )
            continue
        for entry_index, (objective, marks) in enumerate(entries):
            result.append(
                MarkSchemePoint(
                    text=(
                        text
                        if len(entries) == 1
                        else f"{text} [{objective} credit]"
                    ),
                    marks=marks,
                    credit_type=credit_type,
                    assessment_objective=objective,
                )
            )
    return result
