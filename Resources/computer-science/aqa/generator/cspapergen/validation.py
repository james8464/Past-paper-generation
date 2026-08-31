from __future__ import annotations

from collections import Counter
from math import isclose

from Backend.Core.assessment_objectives import objective_policy_for
from cspapergen.models import PaperBlueprint, Syllabus


def validate_blueprint(blueprint: PaperBlueprint, syllabus: Syllabus) -> None:
    objective_policy_for("7517").validate(blueprint)
    if blueprint.assessment_kind not in {"full-paper", "question-bank"}:
        raise ValueError("Unsupported assessment kind")
    if blueprint.assessment_kind == "question-bank":
        _validate_question_bank_identity(blueprint, syllabus)
    elif blueprint.paper_code not in {"7517/1", "7517/2"}:
        raise ValueError("Paper code must be 7517/1 or 7517/2")
    if blueprint.paper_number != blueprint.paper_code.rsplit("/", 1)[-1]:
        raise ValueError("Paper number must match paper code")
    if blueprint.delivery_mode not in {"written", "on-screen"}:
        raise ValueError("Unsupported delivery mode")
    if blueprint.paper_number == "1" and blueprint.delivery_mode != "on-screen":
        raise ValueError("Paper 1 must use on-screen delivery")
    if blueprint.paper_number == "2" and blueprint.delivery_mode != "written":
        raise ValueError("Paper 2 must use written delivery")
    if blueprint.assessment_kind == "full-paper":
        if blueprint.total_marks != 100:
            raise ValueError("Paper total must be 100")
        if len(blueprint.questions) < 8:
            raise ValueError("Paper must contain a full set of questions")
    elif not 3 <= len(blueprint.questions) <= 12:
        raise ValueError("Question bank must contain 3 to 12 questions")

    total = 0
    objective_totals = Counter()
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
        if question.stimulus and any(
            len(line) > 58 for line in question.stimulus.code.splitlines()
        ):
            raise ValueError(
                f"Question {question.number} contains a code line too wide for the page"
            )
        _validate_verified_question_contract(question)
        total += question.total_marks
        for part in question.parts:
            if not part.assessment_objectives or sum(part.assessment_objectives.values()) != part.marks:
                raise ValueError("CS requires explicit assessment objectives matching each tariff")
            if part.marking.assessment_objectives != part.assessment_objectives:
                raise ValueError("CS marking objective allocation differs from the item")
            objective_totals.update(part.assessment_objectives)
            if part.expected_minutes is None or not isclose(
                part.expected_minutes, blueprint.duration_minutes * part.marks / blueprint.total_marks
            ):
                raise ValueError("CS item timing must match the declared component or bank allowance")
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
    if blueprint.assessment_kind == "full-paper":
        expected = {"1": {"AO1": 20, "AO2": 30, "AO3": 50},
                    "2": {"AO1": 56, "AO2": 40, "AO3": 4}}[blueprint.paper_number]
        if dict(objective_totals) != expected:
            raise ValueError("CS full-paper objective budget differs from the calibrated task plan")


def _validate_question_bank_identity(
    blueprint: PaperBlueprint,
    syllabus: Syllabus,
) -> None:
    if blueprint.paper_code != "7517/QB" or blueprint.paper_number != "QB":
        raise ValueError("Question bank must use the 7517/QB document identity")
    if blueprint.delivery_mode != "written":
        raise ValueError("Question bank must use written delivery")
    if blueprint.focus_topic_id not in syllabus.topic_ids:
        raise ValueError("Question bank focus topic is not in the syllabus")
    if not 10 <= blueprint.total_marks <= 60:
        raise ValueError("Question bank total must be between 10 and 60 marks")
    if any(
        question.topic_id != blueprint.focus_topic_id
        for question in blueprint.questions
    ):
        raise ValueError("Question bank contains a question outside its focus topic")


def _validate_verified_question_contract(question) -> None:
    prompts = " ".join(part.prompt for part in question.parts)
    guidance = " ".join(
        point for part in question.parts for point in part.marking.points
    )
    if question.style_id == "sound_sampling" and not any(
        "mib" in point.casefold() and "=" in point
        for point in question.parts[0].marking.points
    ):
        raise ValueError("Sound calculation requires a canonical final answer in MiB")
    if question.style_id == "sql_normalisation":
        required = {"SELECT", "INSERT", "UPDATE", "DELETE", "ERROR"}
        missing = required - set(prompts.upper().replace(".", " ").split())
        if missing:
            raise ValueError(
                f"Database assessment is missing required SQL work: {sorted(missing)}"
            )
    if question.style_id == "stored_program":
        cycle = " ".join(question.parts[1].marking.points).casefold()
        if not all(name in cycle for name in ("address bus", "data bus", "control bus")):
            raise ValueError("Fetch-decode-execute guidance must use all three buses")
    if question.style_id in {"truth_table_completion", "boolean_simplification"}:
        expression_text = " ".join(
            [prompts, question.stimulus.code if question.stimulus else ""]
        )
        if any(
            word in expression_text.upper()
            for word in (" AND ", " OR ", " NOT ", " XOR ", " NAND ", " NOR ")
        ):
            raise ValueError("Boolean expressions must use symbolic AQA notation")
    if question.style_id == "fibonacci_recursion":
        content = f"{question.stem} {prompts} {guidance}".casefold()
        if not all(
            concept in content
            for concept in ("pattern matching", "immutable", "pure function")
        ):
            raise ValueError("Paper 2 functional question lacks functional concepts")
