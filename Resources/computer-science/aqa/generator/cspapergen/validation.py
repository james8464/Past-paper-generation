from __future__ import annotations

from cspapergen.models import PaperBlueprint, Syllabus


def validate_blueprint(blueprint: PaperBlueprint, syllabus: Syllabus) -> None:
    if blueprint.paper_code not in {"7517/1", "7517/2"}:
        raise ValueError("Paper code must be 7517/1 or 7517/2")
    if blueprint.paper_number != blueprint.paper_code.rsplit("/", 1)[-1]:
        raise ValueError("Paper number must match paper code")
    if blueprint.delivery_mode not in {"written", "on-screen"}:
        raise ValueError("Unsupported delivery mode")
    if blueprint.paper_number == "1" and blueprint.delivery_mode != "on-screen":
        raise ValueError("Paper 1 must use on-screen delivery")
    if blueprint.paper_number == "2" and blueprint.delivery_mode != "written":
        raise ValueError("Paper 2 must use written delivery")
    if blueprint.total_marks != 100:
        raise ValueError("Paper total must be 100")
    if len(blueprint.questions) < 8:
        raise ValueError("Paper must contain a full set of questions")

    total = 0
    seen_numbers: set[int] = set()
    seen_prompts: set[str] = set()
    for question in blueprint.questions:
        if question.number in seen_numbers:
            raise ValueError(f"Duplicate question number {question.number}")
        seen_numbers.add(question.number)
        if question.topic_id not in syllabus.topic_ids:
            raise ValueError(f"Question {question.number} uses unknown topic {question.topic_id}")
        if not question.parts:
            raise ValueError(f"Question {question.number} has no parts")
        total += question.total_marks
        for part in question.parts:
            if part.marks <= 0:
                raise ValueError(f"Question {question.number}.{part.label} has invalid marks")
            if not part.prompt.strip():
                raise ValueError(f"Question {question.number}.{part.label} has no prompt")
            prompt_key = " ".join(part.prompt.casefold().split())
            if prompt_key in seen_prompts:
                raise ValueError(
                    f"Question {question.number}.{part.label} duplicates another prompt"
                )
            seen_prompts.add(prompt_key)
            if not part.marking.points:
                raise ValueError(f"Question {question.number}.{part.label} has no marking guidance")
            points = [
                " ".join(point.casefold().split())
                for point in part.marking.points
                if point.strip()
            ]
            if len(points) != len(set(points)):
                raise ValueError(
                    f"Question {question.number}.{part.label} repeats a marking point"
                )
            if part.marks <= 5 and len(points) < min(part.marks, 2):
                raise ValueError(
                    f"Question {question.number}.{part.label} has insufficient "
                    "traceable marking points"
                )
            if not part.marking.ao:
                raise ValueError(f"Question {question.number}.{part.label} has no AO reference")
            if part.options and len(part.options) != 4:
                raise ValueError(f"Question {question.number}.{part.label} must have four options")
            if part.options:
                labels = {option.label for option in part.options}
                if labels != {"A", "B", "C", "D"}:
                    raise ValueError(
                        f"Question {question.number}.{part.label} options must be A-D"
                    )
                if part.correct_option not in labels:
                    raise ValueError(
                        f"Question {question.number}.{part.label} has no valid "
                        "correct option"
                    )
    if total != blueprint.total_marks:
        raise ValueError(f"Question marks total {total}, expected {blueprint.total_marks}")
