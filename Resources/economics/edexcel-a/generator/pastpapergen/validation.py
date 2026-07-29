from __future__ import annotations

import re

from pastpapergen.models import PaperBlueprint, PaperConfig, Syllabus


def validate_blueprint(
    blueprint: PaperBlueprint,
    config: PaperConfig,
    syllabus: Syllabus,
) -> None:
    if blueprint.paper_code != config.code:
        raise ValueError(f"Paper code mismatch: {blueprint.paper_code} != {config.code}")
    if blueprint.total_marks != config.total_marks:
        raise ValueError(f"Total marks mismatch: {blueprint.total_marks} != {config.total_marks}")
    if not blueprint.questions:
        raise ValueError("Paper has no questions")
    answer_marks = 0
    seen_choice_groups: set[str] = set()
    seen_prompts: set[str] = set()

    for question in blueprint.questions:
        if question.marks <= 0:
            raise ValueError(f"Question {question.number} has invalid marks")
        _reject_mark_text(question.number, question.prompt)
        prompt_key = " ".join(question.prompt.casefold().split())
        if not prompt_key or prompt_key in seen_prompts:
            raise ValueError(f"Question {question.number} is empty or duplicated")
        seen_prompts.add(prompt_key)
        try:
            topic = syllabus.get_topic(question.topic_id)
        except KeyError as error:
            raise ValueError(f"Question {question.number} uses unknown topic {question.topic_id}") from error
        if topic.theme not in config.allowed_themes:
            raise ValueError(
                f"Question {question.number} topic {topic.id} theme {topic.theme} "
                f"is not allowed for {config.code}"
            )
        if question.choice_group:
            if question.choice_group not in seen_choice_groups:
                seen_choice_groups.add(question.choice_group)
                answer_marks += question.marks
        else:
            answer_marks += question.marks
        if question.parts and sum(part.marks for part in question.parts) != question.marks:
            raise ValueError(
                f"Question {question.number} part marks do not total "
                f"{question.marks}"
            )
        for part in question.parts:
            _reject_mark_text(f"{question.number}({part.label})", part.prompt)
            if part.command_word == "mcq":
                if len(part.options) != 4 or part.correct_option not in {"A", "B", "C", "D"}:
                    raise ValueError(f"Question {question.number} MCQ part {part.label} is not structured")
                option_labels = {option.label for option in part.options}
                if option_labels != {"A", "B", "C", "D"}:
                    raise ValueError(f"Question {question.number} MCQ options must be A-D")
                answer = next(
                    option.text
                    for option in part.options
                    if option.label == part.correct_option
                )
                scheme = " ".join(part.mark_scheme).casefold()
                if (
                    part.correct_option.casefold() not in scheme
                    and answer.casefold() not in scheme
                ):
                    raise ValueError(
                        f"Question {question.number} MCQ scheme does not identify "
                        "the correct option"
                    )
            if not part.mark_scheme and part.marks <= 5:
                raise ValueError(f"Question {question.number} part {part.label} has no mark scheme")
            _validate_scheme(
                f"{question.number}({part.label})",
                part.mark_scheme,
                part.marks,
            )
        if not question.mark_scheme:
            raise ValueError(f"Question {question.number} has no mark scheme")
        _validate_scheme(question.number, question.mark_scheme, question.marks)
    if answer_marks != config.total_marks:
        raise ValueError(f"Answerable marks mismatch: {answer_marks} != {config.total_marks}")


def _reject_mark_text(number: str, prompt: str) -> None:
    if re.search(r"\(\s*\d+\s*marks?\s*\)", prompt, flags=re.IGNORECASE):
        raise ValueError(f"Question {number} prompt contains marks text")


def _validate_scheme(number: str, points: list[str], marks: int) -> None:
    if not points:
        return
    normalised = [
        " ".join(point.casefold().split())
        for point in points
        if point.strip()
    ]
    if len(normalised) != len(set(normalised)):
        raise ValueError(f"Question {number} repeats a mark-scheme point")
    if marks <= 5 and len(normalised) < min(marks, 2):
        raise ValueError(
            f"Question {number} does not provide enough traceable marking points"
        )
