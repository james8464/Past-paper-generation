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
from Backend.Core.subjects.computer_science_contracts import SumTrace
from ocrcsgen.configs import SECTION_TOPICS
from ocrcsgen.syllabus import Syllabus, Topic
from ocrcsgen.task_calibration import calibrated_task

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
            f"fetch-decode-execute cycle in {evidence}. Refer to the program counter, memory address "
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
            "Develop a clearly labelled technical design showing how an input request is "
            "processed and stored. Include the processor, main memory, relevant registers, "
            "address/data/control buses, input and output, and the direction of each transfer."
        )
    return (
        f"Develop pseudocode or a clearly labelled technical design that applies {point} "
        f"to {evidence}. Include validation, exceptional-input handling and explanations "
        "of the important design decisions."
    )


def _programming_scheme(point: str, evidence: str) -> list[str]:
    value = point.casefold()
    if any(
        term in value
        for term in ("processor components", "fetch-decode", "processor performance")
    ):
        return [
            "The processor and main memory are identified and connected correctly.",
            "Relevant registers, such as the program counter, memory address register and memory data register, are labelled and used consistently.",
            "The address bus, data bus and control bus are labelled with technically correct roles or transfer directions.",
            "Input, processing, storage and output form a coherent transfer path.",
            "Credit an equivalent technically valid architecture or diagram.",
        ]
    return [
        "Inputs, outputs and identifiers are defined consistently.",
        "Sequence, selection and iteration or an equivalent suitable structure are correct.",
        "Boundary, invalid and exceptional inputs are handled.",
        f"The solution applies {point} to {evidence}.",
        "Award method credit for a coherent alternative design.",
    ]


def _task_operation(prompt: str) -> str:
    command = prompt.split(maxsplit=1)[0].casefold().strip(".,:;!?()[]{}")
    operations = {
        "calculate": "transform",
        "complete": "transform",
        "describe": "describe",
        "develop": "program",
        "discuss": "judge",
        "draw": "design",
        "evaluate": "judge",
        "explain": "explain",
        "state": "retrieve",
        "trace": "trace",
    }
    try:
        return operations[command]
    except KeyError as error:
        raise ValueError(f"unsupported OCR task command: {command}") from error


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
        threshold = rng.randint(18, 40)
        values = [threshold - rng.randint(1, 6), threshold, threshold + rng.randint(1, 8)]
        values.extend(rng.randint(12, 48) for _ in range(rng.randint(0, 3)))
        rng.shuffle(values)
        trace = SumTrace(values=values, initial_total=rng.randint(2, 9), threshold=threshold)
        values = [float(value) for value in trace.values]
        option = GeneratedOption(
            id=f"Q{section_rule.id}",
            title=f"Question {section_rule.id}",
            stimulus=_stimulus(topic, context, case_id, rng, trace),
            chart_title="Array values (zero-based)",
            chart_labels=[str(index) for index in range(len(values))],
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
                    trace,
                )
                for question_index, question_rule in enumerate(
                    section_rule.questions, start=1
                )
            ],
        )
        sections.append(
            GeneratedSection(
                id=section_rule.id,
                answer_options=section_rule.answer_options,
                candidate_marks=section_rule.candidate_marks,
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
    topic: Topic, context: str, case_id: int, rng: random.Random, trace: SumTrace
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
    code = trace.code()
    return [paragraph, code]


def _question(
    rule: QuestionRule,
    group: str,
    index: int,
    topic: Topic,
    context: str,
    case_id: int,
    rng: random.Random,
    trace: SumTrace,
) -> GeneratedQuestion:
    letter = chr(96 + index)
    number = f"{group}({letter})"
    point = topic.points[(index - 1) % len(topic.points)]
    evidence = f"the {context.removeprefix('a ').removeprefix('an ')}"
    focus = _technical_focus(point)
    authoring_context: dict[str, object] = (
        {"allow_additional_numeric_values": True}
        if rule.kind in {"analysis", "extended_response", "programming"}
        else {}
    )
    authoring_context["objective_subject"] = "computer science"
    authoring_context["max_prompt_words"] = (
        45
        if rule.kind == "programming"
        else 65
        if rule.kind == "extended_response"
        else 55
    )
    if rule.command_word.casefold() == "state" and rule.marks <= 2:
        authoring_context.update(
            {
                "preserve_prompt": True,
                "preserve_mark_scheme": True,
            }
        )
    if "fetch-decode-execute" in point.casefold():
        authoring_context.update(
            {
                "preserve_prompt": True,
                "preserve_mark_scheme": True,
            }
        )
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
                f"{rule.command_word} {rule.marks} distinct features of {point} "
                "that should be "
                f"considered when developing {evidence}, with particular reference to {focus}."
            )
        scheme = [
            f"One mark for each accurate, distinct point about {point}.",
            f"Accept a technically equivalent answer applied to {evidence}.",
        ]
    elif rule.kind == "analysis":
        prompt = _analysis_prompt(point, evidence, index)
        scheme = [
            f"Accurate knowledge of {point}.",
            "A linked technical chain from design choice to system behaviour.",
            f"Application to the constraints and data for {evidence}.",
            "Credit a correct trace, calculation, diagram or equivalent reasoning.",
        ]
    elif rule.kind == "calculation":
        authoring_context.update(
            {
                "preserve_prompt": True,
                "preserve_mark_scheme": True,
            }
        )
        if topic.id == "systems-5":
            boolean_tasks = {
                2: (
                    "Calculate the output Q when A = 0 and B = 1 for Q = A OR B.",
                    ["Case 1 output: 1."],
                ),
                3: (
                    "Calculate the output R when A = 1 and B = 0 for R = (NOT A) AND B.",
                    ["NOT A = 0.", "Case 1 output: 0."],
                ),
                4: (
                    "Calculate the output of Q = A XOR B for A = 0, B = 0 and for A = 1, B = 1.",
                    [
                        "Case 1 output: 0.",
                        "Case 2 output: 0.",
                    ],
                ),
            }
            prompt, scheme = boolean_tasks[index]
            expression, inputs = {
                2: ("A OR B", [{"A": 0, "B": 1}]),
                3: ("(NOT A) AND B", [{"A": 1, "B": 0}]),
                4: ("A XOR B", [{"A": 0, "B": 0}, {"A": 1, "B": 1}]),
            }[index]
            authoring_context["cs_input_contract"] = {"kind": "boolean-evaluation", "expression": expression, "inputs": inputs}
        else:
            prompt, scheme, source = _representation_calculation(index, marks=rule.marks, rng=rng)
            authoring_context["cs_input_contract"] = source
    elif rule.kind == "trace":
        iterations = len(trace.values)
        prompt = (
            f"Trace all {iterations} iterations of the supplied pseudocode. "
            "Record total after each iteration, then give the single final output. "
            "Array indices start at zero and the loop's upper bound is inclusive."
        )
        total = trace.initial_total
        scheme = []
        for position, value in enumerate(trace.values, 1):
            total += value if value > trace.threshold else 0
            scheme.append(f"After iteration {position}, total: {total:,}.")
        sequence_groups = rule.marks - 1
        groups = [list(range(1, iterations + 1))[i * iterations // sequence_groups:(i + 1) * iterations // sequence_groups]
                  for i in range(sequence_groups)]
        credit = "; ".join(f"1 mark for correct totals in iterations {','.join(map(str, group))}" for group in groups)
        scheme.extend([f"Final output: {total:,}.",
            f"Credit: {credit}; 1 mark for the single final output. Total {rule.marks} marks.",
            "Allow follow-through from one arithmetic error when subsequent control flow is correct."])
        authoring_context.update({"preserve_prompt": True, "preserve_mark_scheme": True,
                                  "cs_input_contract": trace.model_dump(mode="json")})
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
            f"The result is applied to the requirements of {evidence}.",
        ]
    elif rule.kind == "table":
        comparison = topic.points[index % len(topic.points)]
        prompt = (
            f"Complete a comparison table for {point} and {comparison} in the context of "
            f"{evidence}. Include operation, one benefit, one limitation concerning {focus} "
            "and a scenario-specific use."
        )
        scheme = [
            f"Accurate operation of {point}.",
            f"Accurate operation of {comparison}.",
            "A technically valid benefit and limitation.",
            f"A valid use linked to the constraints of {evidence}.",
            "Award one mark per distinct correct table entry up to the maximum.",
        ]
    elif rule.kind == "programming":
        prompt = _programming_prompt(point, evidence)
        scheme = _programming_scheme(point, evidence)
    elif rule.kind == "extended_response":
        prompt = (
            f"Discuss the consequences of using {point} in {evidence}, focusing on {focus}. "
            "Consider technical operation, users, risks, alternatives and the evidence "
            "needed before deployment."
        )
        scheme = _levels(rule.marks, topic, point, evidence)
    else:
        raise ValueError(f"unsupported OCR H446 question kind: {rule.kind}")
    calibrated = calibrated_task(topic.id, group, index)
    if calibrated:
        prompt, scheme = calibrated
        authoring_context.update({"preserve_prompt": True, "preserve_mark_scheme": True})
    task_operation = (
        "analyse"
        if rule.kind == "analysis" and rule.assessment_objectives.get("AO2", 0) > 0
        else _task_operation(prompt)
    )
    authoring_context["task_operation"] = task_operation
    return GeneratedQuestion(
        rule_id=rule.id,
        number=number,
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        assessment_objectives=dict(rule.assessment_objectives),
        expected_minutes=rule.expected_minutes,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=scheme,
        authoring_context=authoring_context,
    )


def _representation_calculation(
    index: int,
    *,
    marks: int,
    rng: random.Random,
) -> tuple[str, list[str], dict]:
    if index == 1:
        value = rng.randint(18, 238)
        return (
            f"Calculate the hexadecimal representation of the denary value {value}.",
            [f"Hexadecimal: {value:02X}."],
            {"kind": "denary-hex", "value": value},
        )
    if index == 3:
        width = rng.choice([64, 128, 256])
        height = rng.choice([32, 64, 128])
        depth = rng.choice([4, 8])
        bits = width * height * depth
        return (
            f"Calculate the uncompressed size in bytes of a {width} by {height} pixel bitmap with a colour depth of {depth} bits. Show your working.",
            [
                f"Method: {width} × {height} × {depth} = {bits} bits.",
                f"File size: {bits // 8:,} bytes.",
            ],
            {"kind": "bitmap-bytes", "width": width, "height": height, "depth": depth},
        )
    if index == 4:
        sample_rate = rng.choice([8_000, 12_000])
        sample_depth = rng.choice([8, 16])
        duration = rng.choice([2, 3])
        size = sample_rate * sample_depth * duration // 8
        return (
            f"Calculate the uncompressed size in bytes of a mono sound sampled at {sample_rate} Hz with a {sample_depth}-bit sample depth for {duration} seconds. Show your working.",
            [
                f"Method: {sample_rate} × {sample_depth} × {duration} bits.",
                "Divide the result by 8 to convert bits to bytes.",
                f"File size: {size:,} bytes.",
            ],
            {"kind": "sound-bytes", "sample_rate": sample_rate, "sample_depth": sample_depth, "duration": duration, "channels": 1},
        )
    if index == 5:
        left = rng.randint(40, 90)
        right = rng.randint(20, 70)
        total = left + right
        return (
            f"Calculate the sum of the two 8-bit unsigned binary values {left:08b} and {right:08b}. Give the 8-bit result and state whether overflow occurs. Show your working.",
            [
                f"Method: align {left:08b} and {right:08b} by place value.",
                "Add corresponding bits from right to left, carrying where required.",
                f"8-bit result: {total:08b}.",
                "Overflow: no.",
                "The unsigned result is no greater than 255.",
            ],
            {"kind": "unsigned-sum", "left": left, "right": right},
        )
    if index == 6:
        return (
            "Calculate the representation of denary 6.5 in an 8-bit normalised floating-point format using a 5-bit two's complement mantissa followed by a 3-bit two's complement exponent. The binary point is after the mantissa sign bit.",
            [
                "6.5 is 110.1 in binary, which normalises to 0.1101 × 2³.",
                "Mantissa 01101 and exponent 011.",
                "Floating representation: 01101011.",
            ],
            {"kind": "floating-encode", "value": "6.5", "mantissa_bits": 5, "exponent_bits": 3},
        )
    raise ValueError(f"unsupported representation calculation {index} ({marks} marks)")


def _levels(marks: int, topic: Topic, point: str, evidence: str) -> list[str]:
    if marks == 12:
        bands = [
            "Level 3 (9–12): thorough technical knowledge, sustained contextual reasoning, balanced discussion and a supported conclusion.",
            "Level 2 (5–8): relevant technical knowledge and developed reasoning, though balance or context may be uneven.",
            "Level 1 (1–4): isolated relevant facts or assertions with limited development or application.",
        ]
    else:
        bands = [
            f"Level 3 ({marks - 2}–{marks}): accurate, developed and contextual reasoning with a supported conclusion.",
            f"Level 2 (4–{marks - 3}): some linked technical reasoning and relevant application, but limited balance.",
            "Level 1 (1–3): isolated correct points or unsupported assertions.",
        ]
    return [
        f"Indicative content: {topic.title}; {point}; application to {evidence}.",
        "Consider correctness, performance, security, maintainability, users and realistic alternatives where relevant.",
        *bands,
        "Level 0 (0): no creditworthy material.",
    ]
