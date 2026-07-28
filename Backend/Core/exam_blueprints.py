from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, Field


class QuestionRule(BaseModel):
    id: str
    marks: int = Field(gt=0)
    kind: str
    command_word: str


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
                if question.topic_id not in rule.allowed_topic_ids:
                    raise ValueError(f"question {question.number} uses an out-of-scope topic")
                prompt_key = " ".join(question.prompt.casefold().split())
                stimulus_key = " ".join(
                    " ".join(option.stimulus).casefold().split()
                )
                uniqueness_key = (prompt_key, stimulus_key)
                if not prompt_key or uniqueness_key in seen_prompts:
                    raise ValueError(f"question {question.number} is empty or duplicated")
                seen_prompts.add(uniqueness_key)
                if not question.mark_scheme:
                    raise ValueError(f"question {question.number} has no mark scheme")
                if question.kind == "multiple_choice":
                    if len(question.choices) != 4 or question.correct_choice not in range(4):
                        raise ValueError(f"question {question.number} has invalid multiple-choice data")
