from __future__ import annotations

import random
import secrets

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    PaperRule,
    QuestionRule,
    validate_generated_paper,
)

from ocrcsgen.configs import SECTION_TOPICS
from ocrcsgen.syllabus import Syllabus, Topic


CONTEXTS = [
    "a community transport service",
    "a wildlife monitoring network",
    "an independent cinema booking system",
    "a regional recycling centre",
    "a school robotics club",
    "a small medical appointment service",
    "a renewable-energy controller",
    "a multiplayer strategy game",
]
NAMES = ["Ari", "Bao", "Cleo", "Dev", "Esi", "Farah", "Gus", "Hana"]


def build_paper(
    rule: PaperRule, syllabus: Syllabus, seed: int | None = None
) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    topics = {topic.id: topic for topic in syllabus.topics}
    sections: list[GeneratedSection] = []
    for section_index, section_rule in enumerate(rule.sections):
        topic = topics[SECTION_TOPICS[rule.id][section_index]]
        context = rng.choice(CONTEXTS)
        case_id = rng.randint(1000, 9999)
        values = [float(rng.randint(12, 48)) for _ in range(6)]
        option = GeneratedOption(
            id=f"Q{section_rule.id}",
            title=f"Question {section_rule.id}",
            stimulus=_stimulus(topic, context, case_id, rng),
            chart_title=f"Trace data for case {case_id}",
            chart_labels=[f"N{index}" for index in range(1, 7)],
            chart_values=values,
            questions=[
                _question(
                    question_rule,
                    section_rule.id,
                    question_index,
                    topic,
                    context,
                    case_id,
                    rng,
                )
                for question_index, question_rule in enumerate(
                    section_rule.questions, start=1
                )
            ],
        )
        sections.append(
            GeneratedSection(
                id=section_rule.id,
                title=section_rule.title,
                instructions="Answer all parts of this question.",
                options=[option],
            )
        )
    paper = GeneratedPaper(
        paper_id=rule.id,
        paper_code=rule.code,
        title=rule.title,
        duration_minutes=rule.duration_minutes,
        total_marks=rule.total_marks,
        seed=run_seed,
        sections=sections,
    )
    validate_generated_paper(paper, rule, syllabus.topic_ids)
    return paper


def _stimulus(
    topic: Topic, context: str, case_id: int, rng: random.Random
) -> list[str]:
    first = rng.choice(topic.points)
    second = rng.choice([point for point in topic.points if point != first])
    user = rng.choice(NAMES)
    size = rng.randint(120, 980)
    paragraph = (
        f"Independent case {case_id}: {user} is developing {context}. The system handles "
        f"{size} records during its busiest interval and must remain correct if an input is "
        "missing, duplicated or delayed. The team is comparing alternative designs involving "
        f"{first} and {second}. Costs, performance, security, maintainability and effects on "
        "users must all be justified. All names, organisations and data in this practice "
        "scenario are fictional."
    )
    code = (
        f"01 total = {rng.randint(2, 9)}\n"
        f"02 for index = 0 to {rng.randint(4, 9)}\n"
        f"03     if values[index] > {rng.randint(10, 40)} then\n"
        "04         total = total + values[index]\n"
        "05     endif\n"
        "06 next index\n"
        "07 print(total)"
    )
    return [paragraph, code]


def _question(
    rule: QuestionRule,
    group: str,
    index: int,
    topic: Topic,
    context: str,
    case_id: int,
    rng: random.Random,
) -> GeneratedQuestion:
    letter = chr(96 + index)
    number = f"{group}({letter})"
    point = topic.points[(index - 1) % len(topic.points)]
    evidence = f"independent case {case_id} about {context}"
    if rule.kind == "short_answer":
        if rule.marks == 1:
            prompt = (
                f"For part {number}, state one fact about {point} that is relevant "
                f"to {evidence}."
            )
        else:
            prompt = (
                f"For part {number}, describe {rule.marks} distinct features of {point} "
                f"that the developer should consider in {evidence}."
            )
        scheme = [
            f"One mark for each accurate, distinct point about {point}.",
            f"Accept a technically equivalent answer applied to case {case_id}.",
        ]
    elif rule.kind == "analysis":
        prompt = (
            f"For part {number}, explain how {point} could affect the correctness, "
            f"performance or usability of the system in {evidence}. Refer to the supplied "
            "trace or pseudocode."
        )
        scheme = [
            f"Accurate knowledge of {point}.",
            "A linked technical chain from design choice to system behaviour.",
            f"Application to the constraints and data in case {case_id}.",
            "Credit a correct trace, calculation, diagram or equivalent reasoning.",
        ]
    elif rule.kind == "calculation":
        value = rng.randint(18, 238)
        prompt = (
            f"For part {number}, convert the denary value {value} used in {evidence} "
            "to 8-bit unsigned binary and hexadecimal. Show each stage required by "
            "the number of marks available."
        )
        scheme = [
            f"8-bit binary: {value:08b}.",
            f"Hexadecimal: {value:02X}.",
            "Award method marks for correct place values or a valid intermediate conversion.",
        ]
    elif rule.kind == "trace":
        iterations = rng.randint(3, 7)
        prompt = (
            f"For part {number}, trace the supplied pseudocode for the first {iterations} "
            f"iterations using the data from {evidence}. Record each changed variable and "
            "the resulting output in order."
        )
        scheme = [
            "Each iteration uses the correct array index and condition.",
            "Changed values are recorded in execution order.",
            "The final output follows from the completed trace.",
            "Award follow-through for one earlier arithmetic error.",
        ]
    elif rule.kind == "diagram":
        prompt = (
            f"For part {number}, draw a clearly labelled logic or data-structure diagram "
            f"for {point} in {evidence}. Show inputs, processing relationships and output."
        )
        scheme = [
            "Inputs and output are labelled.",
            f"The diagram implements {point} correctly.",
            "Connections, direction or Boolean operators are unambiguous.",
            f"The result is applied to the requirements of case {case_id}.",
        ]
    elif rule.kind == "table":
        comparison = topic.points[index % len(topic.points)]
        prompt = (
            f"For part {number}, complete a comparison table for {point} and {comparison} "
            f"in {evidence}. Include operation, one benefit, one limitation and a justified "
            "choice."
        )
        scheme = [
            f"Accurate operation of {point}.",
            f"Accurate operation of {comparison}.",
            "A technically valid benefit and limitation.",
            f"A justified choice linked to case {case_id}.",
            "Award one mark per distinct correct table entry up to the maximum.",
        ]
    elif rule.kind == "programming":
        prompt = (
            f"For part {number}, develop pseudocode or a clearly labelled technical design "
            f"that uses {point} to meet the requirements of {evidence}. Include validation "
            "and explain the important design decisions."
        )
        scheme = [
            "Inputs, outputs and identifiers are defined consistently.",
            "Sequence, selection and iteration or an equivalent suitable structure are correct.",
            "Boundary, invalid and exceptional inputs are handled.",
            f"The solution applies {point} to case {case_id}.",
            "Award method credit for a coherent alternative design.",
        ]
    elif rule.kind == "extended_response":
        prompt = (
            f"For part {number}, discuss the consequences of using {point} in {evidence}. "
            "Consider technical operation, users, risks, alternatives and the evidence "
            "needed before deployment."
        )
        scheme = _levels(rule.marks, topic, point, case_id)
    else:
        raise ValueError(f"unsupported OCR H446 question kind: {rule.kind}")
    return GeneratedQuestion(
        rule_id=rule.id,
        number=number,
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=scheme,
    )


def _levels(marks: int, topic: Topic, point: str, case_id: int) -> list[str]:
    if marks == 12:
        bands = [
            "Level 4 (10–12): thorough technical knowledge, sustained contextual reasoning, balanced discussion and a supported conclusion.",
            "Level 3 (7–9): good technical knowledge and developed reasoning with relevant discussion, though balance or context may be uneven.",
            "Level 2 (4–6): some correct knowledge and short reasoning chains; discussion is limited or generic.",
            "Level 1 (1–3): isolated relevant facts or assertions with little development.",
        ]
    else:
        bands = [
            f"Level 3 ({marks - 2}–{marks}): accurate, developed and contextual reasoning with a supported conclusion.",
            f"Level 2 (4–{marks - 3}): some linked technical reasoning and relevant application, but limited balance.",
            "Level 1 (1–3): isolated correct points or unsupported assertions.",
        ]
    return [
        f"Indicative content: {topic.title}; {point}; application to case {case_id}.",
        "Consider correctness, performance, security, maintainability, users and realistic alternatives where relevant.",
        *bands,
        "Level 0 (0): no creditworthy material.",
    ]
