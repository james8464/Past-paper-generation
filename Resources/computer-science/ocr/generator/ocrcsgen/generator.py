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
from Backend.Core.mark_scheme_enrichment import enrich_paper

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


def _technical_focus(point: str) -> str:
    value = point.casefold()
    if any(term in value for term in ("encryption", "hash", "protocol", "data protection", "computer misuse")):
        return "security"
    if any(term in value for term in ("processor performance", "parallel", "compression", "search", "sort", "complexity")):
        return "performance"
    if any(term in value for term in ("fetch-decode", "boolean", "logic", "representation", "arithmetic")):
        return "correctness"
    if any(term in value for term in ("operating system", "storage", "network", "file handling")):
        return "reliability"
    if any(term in value for term in ("software development", "translator", "paradigm", "object-oriented")):
        return "maintainability"
    return "fitness for purpose"


def _analysis_prompt(point: str, evidence: str, index: int) -> str:
    value = point.casefold()
    if "fetch-decode-execute" in value:
        emphasis = (
            "Show how the program counter changes.",
            "Show how an operand is transferred from memory.",
            "Explain the role of the control unit in decoding the instruction.",
            "Explain when the current instruction register is updated.",
        )[(index - 1) % 4]
        return (
            "Explain how one machine-code instruction is processed during the "
            "fetch-decode-execute cycle. Refer to the program counter, memory address "
            "register, memory data register, current instruction register and control unit. "
            f"{emphasis}"
        )
    if "processor components and buses" in value:
        return (
            "Explain how the address, data and control buses are used when an instruction "
            "and its operand are transferred between memory and the processor."
        )
    if "processor performance" in value or "parallel processing" in value:
        return (
            f"Explain how cache size, clock speed and the number of processor cores could "
            f"affect the performance of {evidence}. Include one reason why a higher value "
            "does not always produce a proportional improvement."
        )
    if "input, output and storage" in value:
        return (
            f"Explain why the choice of input, output and secondary-storage devices for "
            f"{evidence} must consider capacity, speed, durability and accessibility."
        )
    return f"Explain how {point} affects the technical operation of {evidence}. Use the supplied evidence."


def _programming_prompt(point: str, evidence: str) -> str:
    value = point.casefold()
    if any(term in value for term in ("processor components", "fetch-decode", "processor performance")):
        return (
            "Produce a clearly labelled technical design showing how an input request is "
            "processed and stored. Include the processor, main memory, relevant registers, "
            "address/data/control buses, input and output, and the direction of each transfer."
        )
    return (
        f"Develop pseudocode or a clearly labelled technical design that applies {point} "
        f"to {evidence}. Include validation, exceptional-input handling and explanations "
        "of the important design decisions."
    )


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
            chart_title="Trace data for the supplied scenario",
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
    paper = enrich_paper(paper, syllabus.topics, subject="computer science")
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
        f"{user} is developing {context}. During its busiest interval, the system processes "
        f"{size} records. It must continue to behave predictably when data is missing, duplicated "
        f"or delayed. The design uses {first}. The team is also considering {second}."
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
    evidence = f"the {context.removeprefix('a ').removeprefix('an ')}"
    focus = _technical_focus(point)
    if rule.kind == "short_answer":
        if rule.marks == 1:
            aspect = (
                "advantage",
                "limitation",
                "requirement",
                "test condition",
                "implementation risk",
                "precondition",
                "validation check",
                "performance concern",
                "correctness condition",
            )[(index - 1) % 9]
            prompt = (
                f"State one {aspect} associated with {point} when it is used in {evidence}."
            )
        else:
            prompt = (
                f"Describe {rule.marks} distinct features of {point} that should be "
                f"considered when developing {evidence}, with particular reference to {focus}."
            )
        scheme = [
            f"One mark for each accurate, distinct point about {point}.",
            f"Accept a technically equivalent answer applied to case {case_id}.",
        ]
    elif rule.kind == "analysis":
        prompt = _analysis_prompt(point, evidence, index)
        scheme = [
            f"Accurate knowledge of {point}.",
            "A linked technical chain from design choice to system behaviour.",
            f"Application to the constraints and data in case {case_id}.",
            "Credit a correct trace, calculation, diagram or equivalent reasoning.",
        ]
    elif rule.kind == "calculation":
        value = rng.randint(18, 238)
        prompt = (
            f"Convert the denary value {value} "
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
            f"Trace the supplied pseudocode for the first {iterations} iterations. "
            "Record each changed variable and "
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
            f"Draw a clearly labelled logic or data-structure diagram that applies {point} "
            f"to {evidence}, with particular reference to {focus}. Show inputs, processing "
            "relationships and output."
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
            f"Complete a comparison table for {point} and {comparison} in the context of "
            f"{evidence}. Include operation, one benefit, one limitation concerning {focus} "
            "and a justified "
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
        prompt = _programming_prompt(point, evidence)
        scheme = [
            "Inputs, outputs and identifiers are defined consistently.",
            "Sequence, selection and iteration or an equivalent suitable structure are correct.",
            "Boundary, invalid and exceptional inputs are handled.",
            f"The solution applies {point} to case {case_id}.",
            "Award method credit for a coherent alternative design.",
        ]
    elif rule.kind == "extended_response":
        prompt = (
            f"Discuss the consequences of using {point} in {evidence}, focusing on {focus}. "
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
