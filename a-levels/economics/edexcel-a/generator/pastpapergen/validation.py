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

    for question in blueprint.questions:
        _reject_mark_text(question.number, question.prompt)
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
        for part in question.parts:
            _reject_mark_text(f"{question.number}({part.label})", part.prompt)
            if part.command_word == "mcq":
                if len(part.options) != 4 or part.correct_option not in {"A", "B", "C", "D"}:
                    raise ValueError(f"Question {question.number} MCQ part {part.label} is not structured")
                option_labels = {option.label for option in part.options}
                if option_labels != {"A", "B", "C", "D"}:
                    raise ValueError(f"Question {question.number} MCQ options must be A-D")
            if not part.mark_scheme and part.marks <= 5:
                raise ValueError(f"Question {question.number} part {part.label} has no mark scheme")
        if not question.mark_scheme:
            raise ValueError(f"Question {question.number} has no mark scheme")
    if answer_marks != config.total_marks:
        raise ValueError(f"Answerable marks mismatch: {answer_marks} != {config.total_marks}")


def _reject_mark_text(number: str, prompt: str) -> None:
    if re.search(r"\(\s*\d+\s*marks?\s*\)", prompt, flags=re.IGNORECASE):
        raise ValueError(f"Question {number} prompt contains marks text")
