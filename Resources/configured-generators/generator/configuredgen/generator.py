from __future__ import annotations

import random
import secrets

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
        section_topics = [
            topic for topic in topics if topic.id in section_topic_ids
        ]
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
                + "; ".join(point.removeprefix("Records ").removesuffix(".") for point in exact_points[:-1]),
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
            "cambridge-standard-4-level"
            if _uses_levels(rule)
            else None
        ),
    }
    if rule.kind != "multiple_choice":
        authoring_context["valid_alternatives"] = [
            "Accept an equivalent, technically accurate route."
        ]
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
                    credit_type=(
                        "level" if _uses_levels(rule) else "point"
                    ),
                    assessment_objective=objective,
                    alternatives=[
                        "Equivalent accurate terminology or method."
                    ],
                    do_not_accept=[
                        "Unsupported repetition of the question."
                    ],
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
        "extended_response": "extended_response",
    }.get(kind, "constructed_response")


def _uses_levels(rule: QuestionRule) -> bool:
    return rule.kind == "extended_response" or (
        rule.marks >= 8
        and rule.command_word.casefold()
        in {"analyse", "analyze", "assess", "discuss", "evaluate", "justify"}
    )
