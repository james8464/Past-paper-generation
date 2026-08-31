from __future__ import annotations

import random
import secrets

from Backend.Core.credit_policy import alternative_permission
from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
    MarkSchemePoint,
    PaperRule,
    QuestionRule,
    SectionRule,
    validate_generated_paper,
    validate_rule,
)
from configuredgen.models import ConfiguredSyllabus, Topic

CONTEXTS = (
    "a regional transport network",
    "an independent renewable-energy cooperative",
    "a public library digital service",
    "a specialist food producer",
    "a community health data project",
    "a cross-border online retailer",
    "a small satellite-monitoring organisation",
    "a municipal recycling programme",
)


def build_paper(
    rule: PaperRule,
    syllabus: ConfiguredSyllabus,
    seed: int | None,
) -> GeneratedPaper:
    run_seed = seed if seed is not None else secrets.randbits(64)
    rng = random.Random(run_seed)
    validate_rule(rule, syllabus.topic_ids)
    topics = [topic for topic in syllabus.topics if topic.id in rule.allowed_topic_ids]
    rng.shuffle(topics)
    cursor = 0
    number = 1
    sections: list[GeneratedSection] = []
    for section_rule in rule.sections:
        section_topic_ids = section_rule.allowed_topic_ids or rule.allowed_topic_ids
        section_topics = [topic for topic in topics if topic.id in section_topic_ids]
        options: list[GeneratedOption] = []
        for option_index in range(section_rule.option_count):
            topic = section_topics[cursor % len(section_topics)]
            cursor += 1
            context = rng.choice(CONTEXTS)
            questions: list[GeneratedQuestion] = []
            for question_rule in section_rule.questions:
                question_topic = section_topics[cursor % len(section_topics)]
                cursor += 1
                questions.append(
                    _question(
                        question_rule,
                        number=number,
                        topic=question_topic,
                        context=context,
                        rng=rng,
                        subject=syllabus.subject_plugin,
                    )
                )
                number += 1
            options.append(
                GeneratedOption(
                    id=f"{section_rule.id}{option_index + 1}",
                    title=(
                        f"{section_rule.title} – option {option_index + 1}"
                        if section_rule.option_count > 1
                        else section_rule.title
                    ),
                    stimulus=(
                        []
                        if not section_rule.stimulus_required
                        else [_stimulus(topic, context, rng)]
                    ),
                    questions=questions,
                )
            )
        sections.append(
            GeneratedSection(
                id=section_rule.id,
                title=section_rule.title,
                instructions=_section_instruction(section_rule),
                options=options,
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


def _question(
    rule: QuestionRule,
    *,
    number: int,
    topic: Topic,
    context: str,
    rng: random.Random,
    subject: str,
) -> GeneratedQuestion:
    if subject == "mathematics":
        return _mathematics_question(
            rule,
            number=number,
            topic=topic,
            rng=rng,
        )
    exact_points: list[str] = []
    if rule.kind == "multiple_choice":
        correct = topic.points[0]
        choices = [correct, *topic.points[1:4]]
        rng.shuffle(choices)
        correct_index = choices.index(correct)
        prompt = (
            f"For scenario {number}, which statement about "
            f"{topic.title.casefold()} is correct in "
            f"the context of {context}?"
        )
        scheme = [f"{chr(65 + correct_index)} – {correct}"]
    else:
        choices = []
        correct_index = None
        focus = rng.choice(topic.points)
        calculation_solution: tuple[int, int, int] | None = None
        if rule.kind == "calculation":
            original = rng.randint(4, 20) * 20
            percentage = rng.choice((5, 10, 15, 20, 25))
            result = original * (100 + percentage) // 100
            calculation_solution = (original, percentage, result)
            exact_points = [
                f"Uses {original} × (100 + {percentage}) ÷ 100.",
                f"Obtains {result} units.",
            ]
            prompt = (
                f"For case {number}, a relevant measure for {context} was "
                f"{original} units and then increased by {percentage}%. "
                f"{rule.command_word} the new value, showing your working."
            )
        elif rule.kind == "trace":
            limit = rng.randint(3, 6)
            trace = []
            total = 0
            for index in range(1, limit + 1):
                total += index
                trace.append(f"index={index}, total={total}")
            prompt = (
                f"For task {number}, {rule.command_word.casefold()} a trace table "
                f"for this original pseudocode using limit = {limit}: "
                "total ← 0; FOR index ← 1 TO limit; "
                "total ← total + index; NEXT index. Record index and total "
                "after each iteration."
            )
            exact_points = [
                *(f"Records {row}." for row in trace),
                f"States the final total as {total}.",
            ]
        else:
            prompt = _prompt(
                rule.command_word,
                focus=focus,
                topic=topic.title,
                context=context,
                kind=rule.kind,
                subject=subject,
                variant=number,
            )
        scheme = _scheme_lines(rule, topic, context)
        if calculation_solution is not None:
            original, percentage, result = calculation_solution
            scheme[0:0] = [
                f"Method: {original} × (100 + {percentage}) ÷ 100.",
                f"Result: {result} units.",
            ]
        if rule.kind == "trace":
            scheme[0:0] = [
                "Expected trace: "
                + "; ".join(
                    point.removeprefix("Records ").removesuffix(".")
                    for point in exact_points[:-1]
                ),
                exact_points[-1],
            ]
    structured = _structured_points(
        rule,
        topic,
        context,
        exact_points=exact_points,
    )
    authoring_context = {
        "expected_answer_form": _answer_form(rule.kind),
        "prerequisite_knowledge": [topic.title],
        "observable_mark_points": [point.text for point in structured],
        "common_errors": [
            "A statement without the requested application or reasoning."
        ],
        "level_policy_id": (
            "cambridge-standard-4-level" if _uses_levels(rule) else None
        ),
    }
    if rule.kind != "multiple_choice":
        authoring_context.update(alternative_permission("equivalent-configured-route"))
    if rule.marks >= 4 and rule.kind != "multiple_choice":
        authoring_context["partial_credit_boundaries"] = [
            "Credit each developed point once only."
        ]
        authoring_context["follow_through_rules"] = [
            "Allow consistent follow-through where the method remains valid."
        ]
        scheme.extend(
            [
                "Credit each developed point once only.",
                "Allow consistent follow-through where the method remains valid.",
            ]
        )
    return GeneratedQuestion(
        rule_id=rule.id,
        number=str(number),
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=scheme,
        choices=choices,
        correct_choice=correct_index,
        syllabus_outcomes=[topic.id],
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "standard",
        expected_minutes=rule.expected_minutes,
        scheme_mode=("levels" if _uses_levels(rule) else "points"),
        structured_mark_scheme=structured,
        authoring_context=authoring_context,
    )


def _mathematics_question(
    rule: QuestionRule,
    *,
    number: int,
    topic: Topic,
    rng: random.Random,
) -> GeneratedQuestion:
    if rule.kind == "multiple_choice":
        coefficient = 2 + number % 5
        solution = (number * 3) % 14 - 5
        constant = (number * 5) % 19 - 9
        result = coefficient * solution + constant
        choices = [solution, solution + 1, solution - 1, -solution or 2]
        choices = list(dict.fromkeys(choices))
        while len(choices) < 4:
            choices.append(choices[-1] + 2)
        rng.shuffle(choices)
        correct_choice = choices.index(solution)
        prompt = (
            f"In a mathematical model concerning {topic.title}, "
            f"{coefficient}x + {constant} = {result}. Select the value of x."
        )
        exact_points = [f"A1: x = {solution}."]
        required_terms = [f"{coefficient}x", str(result)]
    elif topic.id.startswith("mechanics-"):
        mass = 2 + number % 5
        initial_speed = 2 + number % 7
        acceleration = 2 + number % 4
        time = 3 + number % 4
        final_speed = initial_speed + acceleration * time
        displacement = initial_speed * time + acceleration * time**2 / 2
        force = mass * acceleration
        momentum = mass * final_speed
        prompt = (
            f"A particle of mass {mass} kg moves in a straight line with initial "
            f"speed {initial_speed} m s⁻¹ and constant acceleration "
            f"{acceleration} m s⁻² for {time} s. {rule.command_word} its final speed and "
            "displacement."
        )
        points = [
            "M1: uses v = u + at.",
            f"A1: obtains v = {final_speed} m s⁻¹.",
            "M1: uses s = ut + ½at².",
            f"M1: substitutes u = {initial_speed}, a = {acceleration} and t = {time}.",
            f"A1: obtains s = {displacement:g} m.",
            "M1: uses F = ma for the resultant force.",
            f"A1: obtains F = {force} N.",
            "M1: uses momentum = mv at the end of the motion.",
            f"A1: obtains momentum = {momentum} kg m s⁻¹.",
            "B1: states that the positive values use the stated direction of motion.",
        ]
        if rule.marks >= 7:
            prompt += " Hence find the resultant force."
        if rule.marks >= 9:
            prompt += " Also find the particle's final momentum."
        exact_points = points[: rule.marks]
        choices = []
        correct_choice = None
        required_terms = [str(mass), str(initial_speed), str(acceleration), str(time)]
    elif topic.id.startswith("statistics-"):
        start = 3 + number % 11
        values = [start, start + 2, start + 4, start + 6, start + 10]
        total = sum(values)
        mean = total / len(values)
        squared_sum = sum((value - mean) ** 2 for value in values)
        variance = squared_sum / len(values)
        standard_deviation = variance**0.5
        prompt = (
            f"The data values {', '.join(str(value) for value in values)} arise "
            f"in a study of {topic.title}. {rule.command_word} the mean and the population "
            "standard deviation, showing all working."
        )
        points = [
            f"B1: obtains Σx = {total}.",
            f"A1: obtains the mean {mean:g}.",
            "M1: calculates deviations from the mean.",
            "M1: squares the deviations before summing.",
            f"A1: obtains Σ(x − x̄)² = {squared_sum:g}.",
            "M1: divides the squared-deviation total by 5.",
            f"A1: obtains the variance {variance:g}.",
            f"A1: obtains the population standard deviation {standard_deviation:.3f} (3 s.f.).",
            f"B1: identifies the median as {values[2]}.",
            f"B1: identifies the range as {values[-1] - values[0]}.",
        ]
        if rule.marks >= 9:
            prompt += " State the median and range."
        exact_points = points[: rule.marks]
        choices = []
        correct_choice = None
        required_terms = [str(values[0]), str(values[-1]), "standard deviation"]
    elif rule.kind == "mathematical_argument":
        example = 2 + number % 7
        example_value = (2 * example + 1) ** 2
        prompt = (
            f"Let n be an integer. {rule.command_word} that the square of the odd integer "
            f"2n + 1 is odd. Verify your result for n = {example}."
        )
        points = [
            "B1: represents an arbitrary odd integer as 2n + 1.",
            "M1: forms (2n + 1)².",
            "A1: expands to 4n² + 4n + 1.",
            "M1: rewrites this as 2(2n² + 2n) + 1.",
            "A1: concludes it has the form 2k + 1 for integer k.",
            f"B1: for n = {example}, obtains {example_value}.",
            "B1: observes that the verification value is odd.",
            "B1: explains that the argument applies to every integer n.",
            "B1: distinguishes verification of an example from the general proof.",
            "B1: uses implication and integer notation consistently.",
        ]
        exact_points = points[: rule.marks]
        choices = []
        correct_choice = None
        required_terms = ["2n + 1", str(example)]
    else:
        root_one = 1 + number % 7
        root_two = root_one + 2 + number % 4
        coefficient = root_one + root_two
        constant = root_one * root_two
        axis = coefficient / 2
        vertex = axis**2 - coefficient * axis + constant
        prompt = (
            f"In work on {topic.title}, let f(x) = x² − {coefficient}x + {constant}. "
            f"{rule.command_word} "
            "the exact solutions of f(x) = 0 by factorising."
        )
        points = [
            f"M1: seeks two numbers with sum {coefficient} and product {constant}.",
            f"A1: writes f(x) = (x − {root_one})(x − {root_two}).",
            f"A1: obtains x = {root_one}.",
            f"A1: obtains x = {root_two}.",
            "B1: gives both solutions as exact values.",
            f"M1: uses x = {coefficient}/2 for the axis of symmetry.",
            f"A1: obtains the axis x = {axis:g}.",
            f"A1: obtains the vertex value f({axis:g}) = {vertex:g}.",
            f"B1: verifies that the roots sum to {coefficient}.",
            f"B1: verifies that the roots have product {constant}.",
        ]
        if rule.marks >= 7:
            prompt += " Find the equation of the axis of symmetry."
        if rule.marks >= 8:
            prompt += " Hence find the coordinates of the vertex."
        if rule.marks >= 9:
            prompt += " Verify the sum and product of the roots."
        exact_points = points[: rule.marks]
        choices = []
        correct_choice = None
        required_terms = ["f(x)", str(coefficient), str(constant)]

    structured = _structured_points(
        rule,
        topic,
        "the stated mathematical problem",
        exact_points=exact_points,
    )
    authoring_context = {
        "expected_answer_form": _answer_form(rule.kind),
        "prerequisite_knowledge": [topic.title],
        "observable_mark_points": [point.text for point in structured],
        "common_errors": [
            "Uses a correct method but makes an arithmetic or sign error."
        ],
        "preserve_mark_scheme": True,
        "required_prompt_terms": required_terms,
    }
    return GeneratedQuestion(
        rule_id=rule.id,
        number=str(number),
        marks=rule.marks,
        kind=rule.kind,
        command_word=rule.command_word,
        topic_id=topic.id,
        prompt=prompt,
        mark_scheme=exact_points,
        choices=[str(choice) for choice in choices],
        correct_choice=correct_choice,
        syllabus_outcomes=[topic.id],
        assessment_objectives=dict(rule.assessment_objectives),
        intended_demand=rule.intended_demand or "standard",
        expected_minutes=rule.expected_minutes,
        scheme_mode="points",
        structured_mark_scheme=structured,
        authoring_context=authoring_context,
    )


def _prompt(
    command: str,
    *,
    focus: str,
    topic: str,
    context: str,
    kind: str,
    subject: str,
    variant: int,
) -> str:
    if kind == "programming":
        return (
            f"For task {variant}, {command.casefold()} pseudocode or program "
            f"logic that applies {focus} to "
            f"a task used by {context}. Explain any assumptions you make."
        )
    if subject == "economics":
        return (
            f"For case {variant}, using {context} as the context, "
            f"{command.casefold()} how the following economic relationship may "
            f"influence decisions: {focus}. Use relevant reasoning from {topic}."
        )
    return (
        f"For task {variant}, in relation to a system used by {context}, "
        f"{command.casefold()} how the following computing principle applies: "
        f"{focus}. Use relevant reasoning from {topic}."
    )


def _section_instruction(rule: SectionRule) -> str:
    if rule.answer_options == rule.option_count:
        return "Answer all questions in this section."
    noun = "option" if rule.option_count == 1 else "options"
    return (
        f"Answer {rule.answer_options} of the {rule.option_count} "
        f"{noun} in this section."
    )


def _stimulus(topic: Topic, context: str, rng: random.Random) -> str:
    change = rng.randint(6, 24)
    return (
        f"A fictional case concerning {context} reports a {change}% change in "
        f"one relevant measure. Decision-makers are considering {topic.points[0]} "
        f"while recognising {topic.points[1]}. All names and data are original."
    )


def _scheme_lines(
    rule: QuestionRule,
    topic: Topic,
    context: str,
) -> list[str]:
    lines = [
        f"AO guidance: credit accurate use of {point} in relation to {context}."
        for point in topic.points[:4]
    ]
    lines.append("Accept an equivalent, technically accurate route.")
    lines.append("Do not credit the same developed point twice.")
    if rule.kind == "calculation":
        lines.extend(
            [
                "Method mark: selects and applies the relevant relationship.",
                "Accuracy mark: obtains a correctly stated result with units where required.",
            ]
        )
    if _uses_levels(rule):
        lines.extend(
            [
                f"Level 4 ({max(1, rule.marks - 2)}–{rule.marks}): sustained analysis and a supported judgement.",
                f"Level 3 ({max(1, rule.marks - 5)}–{max(1, rule.marks - 3)}): developed reasoning with relevant evaluation.",
                f"Level 2 (3–{max(3, rule.marks - 6)}): some applied reasoning but limited evaluation.",
                "Level 1 (1–2): isolated relevant knowledge.",
                "Level 0 (0): no creditworthy response.",
            ]
        )
    return lines


def _structured_points(
    rule: QuestionRule,
    topic: Topic,
    context: str,
    *,
    exact_points: list[str],
) -> list[MarkSchemePoint]:
    result: list[MarkSchemePoint] = []
    serial = 1
    for objective, marks in rule.assessment_objectives.items():
        for offset in range(marks):
            if exact_points:
                guidance = exact_points[(serial - 1) % len(exact_points)]
            else:
                point = topic.points[(serial - 1) % len(topic.points)]
                guidance = (
                    f"uses {point} accurately for {context}; "
                    f"development step {offset + 1}."
                )
            result.append(
                MarkSchemePoint(
                    text=f"{objective} point {serial}: {guidance}",
                    marks=1,
                    credit_type=("level" if _uses_levels(rule) else "point"),
                    assessment_objective=objective,
                    alternatives=["Equivalent accurate terminology or method."],
                    do_not_accept=["Unsupported repetition of the question."],
                )
            )
            serial += 1
    return result


def _answer_form(kind: str) -> str:
    return {
        "multiple_choice": "selected_response",
        "calculation": "calculation_with_working",
        "programming": "code_or_pseudocode",
        "trace": "trace_table",
        "mathematical_argument": "mathematical_argument",
        "extended_response": "extended_response",
    }.get(kind, "constructed_response")


def _uses_levels(rule: QuestionRule) -> bool:
    return rule.kind == "extended_response" or (
        rule.marks >= 8
        and rule.command_word.casefold()
        in {"analyse", "analyze", "assess", "discuss", "evaluate", "justify"}
    )
