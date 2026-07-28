from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from Backend.Core.exam_blueprints import (
    GeneratedOption,
    GeneratedPaper,
    GeneratedQuestion,
    GeneratedSection,
)


def enrich_paper(
    paper: GeneratedPaper,
    topics: Iterable[Any],
    *,
    subject: str,
) -> GeneratedPaper:
    """Remove generator artefacts and add examiner-grade indicative guidance."""
    topic_by_id = {topic.id: topic for topic in topics}
    compact_ocr_programming = (
        subject == "computer science" and paper.paper_code == "H446/02"
    )
    sections: list[GeneratedSection] = []
    for section in paper.sections:
        options: list[GeneratedOption] = []
        for option in section.options:
            questions = [
                _enrich_question(
                    question,
                    topic_by_id[question.topic_id],
                    subject,
                    compact=compact_ocr_programming,
                )
                for question in option.questions
            ]
            options.append(
                option.model_copy(
                    update={
                        "title": _clean_text(option.title),
                        "stimulus": [_clean_text(text) for text in option.stimulus],
                        "questions": questions,
                    }
                )
            )
        sections.append(section.model_copy(update={"options": options}))
    return paper.model_copy(update={"sections": sections})


def _enrich_question(
    question: GeneratedQuestion,
    topic: Any,
    subject: str,
    *,
    compact: bool = False,
) -> GeneratedQuestion:
    if question.kind == "multiple_choice":
        return question.model_copy(update={"prompt": _clean_text(question.prompt)})

    points = [str(point).strip() for point in topic.points if str(point).strip()]
    selected = (points * 3)[:6]
    scheme = list(question.mark_scheme)
    if compact:
        scheme.extend(_compact_technical_guidance(question, topic.title, selected))
        return question.model_copy(
            update={
                "prompt": _clean_text(question.prompt),
                "mark_scheme": _deduplicate(scheme),
            }
        )
    scheme.extend(_objective_guidance(question, topic.title, selected, subject))
    if question.marks >= 8:
        scheme.extend(_level_guidance(question.marks, subject))
    scheme.append(
        "Marker check: reward a valid alternative route where it demonstrates the same assessed knowledge or skill."
    )
    if question.marks >= 4:
        scheme.append(
            "Do not award the same developed point twice. Where an early numerical error is carried through consistently, award the later method marks."
        )
    scheme = _deduplicate(scheme)
    return question.model_copy(
        update={
            "prompt": _clean_text(question.prompt),
            "mark_scheme": scheme,
        }
    )


def _compact_technical_guidance(
    question: GeneratedQuestion,
    topic_title: str,
    points: list[str],
) -> list[str]:
    guidance = [
        "Indicative content",
        f"AO1: credit accurate technical knowledge of {topic_title}.",
        f"AO2: apply {points[0]} to the stated data, algorithm or system.",
        "Accept equivalent pseudocode, terminology or a technically valid alternative method.",
    ]
    if question.marks >= 5:
        guidance.extend(
            [
                f"AO3: develop the consequences of {points[1]} rather than merely naming it.",
                "Award only distinct points; do not credit the same explanation twice.",
            ]
        )
    if question.marks >= 8:
        guidance.extend(_level_guidance(question.marks, "computer science"))
    return guidance


def _objective_guidance(
    question: GeneratedQuestion,
    topic_title: str,
    points: list[str],
    subject: str,
) -> list[str]:
    prompt = _clean_text(question.prompt)
    application = _application_label(subject)
    if question.marks <= 4:
        concise = [
            "Indicative content",
            f"AO1: credit accurate knowledge of {topic_title}.",
            *[
                f"AO1: accept a correct point about {point}."
                for point in points[: min(question.marks, 2)]
            ],
            f"{application}: apply the answer to the figures, constraints or evidence supplied in the question.",
            f"AO3: where explanation is required, link {points[0]} to a relevant consequence rather than merely naming it.",
        ]
        if subject == "computer science":
            concise.append(
                "Accept equivalent pseudocode or technical terminology only where its meaning and result are unambiguous."
            )
        return concise
    guidance = [
        "Indicative content",
        f"AO1: demonstrate precise knowledge of {topic_title}, using the terminology in the specification accurately.",
        *[
            f"AO1: credit an accurate explanation of {point}, where it is relevant to the question."
            for point in points[:3]
        ],
        f"{application}: select and use the figures, constraints or evidence supplied in the question; unsupported generic statements do not demonstrate application.",
        f"{application}: link each applied point directly to the named organisation, market, system or decision in: “{prompt}”",
        f"AO3: develop a complete chain of reasoning from {points[0]} through an intermediate effect to a supported outcome.",
        f"AO3: a second valid route may use {points[1]} and {points[2]}; reward the reasoning rather than the wording of this guidance.",
    ]
    if subject == "computer science":
        guidance.extend(
            [
                "AO2: where pseudocode, a trace, table or diagram is required, award only internally consistent steps and labels that answer the stated task.",
                "AO3: credit testing of normal, boundary and erroneous data, plus a justified explanation of the observed result.",
                "Accept equivalent technical syntax where its meaning is unambiguous; do not credit prose that merely repeats the question.",
            ]
        )
    elif subject == "accounting":
        guidance.extend(
            [
                "AO2: figures must be labelled, use the correct accounting convention and show enough working to identify the method used.",
                "AO3: reward analysis of the effect on profit, financial position, cash flow and stakeholder decisions where each link is relevant.",
                "Accept an alternative accounting treatment only when it is consistent throughout and supported by the applicable principle.",
            ]
        )
    elif subject == "business":
        guidance.extend(
            [
                "AO2: reward selective use of the quantitative and qualitative case evidence, including correctly interpreted units and trends.",
                "AO3: analysis must explain how the business evidence changes costs, demand, operations, people or strategic risk.",
                "AO4: evaluation should weigh the importance of the evidence, timescale, stakeholder impact and uncertainty before reaching a decision.",
            ]
        )
    else:
        guidance.extend(
            [
                "AO2: reward accurate use of source data, including units, direction and scale; a quotation alone is not application.",
                "AO3: analysis should identify the relevant economic agent, incentive and transmission mechanism before stating the final effect.",
                "AO4: evaluation may consider assumptions, elasticities, magnitude, time period, distributional effects and unintended consequences.",
            ]
        )
    return guidance


def _level_guidance(marks: int, subject: str) -> list[str]:
    if marks >= 20:
        bands = [
            (5, marks - 4, marks, "sustained, well-focused analysis; effective evaluation; and a fully supported conclusion"),
            (4, marks - 9, marks - 5, "developed analysis and relevant evaluation with a supported conclusion"),
            (3, marks - 14, marks - 10, "sound knowledge and some developed analysis; evaluation is partial"),
            (2, max(4, marks - 19), marks - 15, "limited application with short or incomplete analytical chains"),
            (1, 1, max(3, marks - 20), "isolated relevant points with little development"),
        ]
    elif marks >= 12:
        bands = [
            (4, marks - 2, marks, "accurate contextual knowledge, developed analysis, balanced evaluation and a supported judgement"),
            (3, marks - 5, marks - 3, "good knowledge and linked analysis; evaluation is relevant but uneven"),
            (2, max(3, marks - 8), marks - 6, "some accurate knowledge and analysis; evaluation is limited"),
            (1, 1, max(2, marks - 9), "fragmentary knowledge or unsupported assertions"),
        ]
    else:
        bands = [
            (3, marks - 1, marks, "clear application and a developed, logically ordered response"),
            (2, max(2, marks - 3), marks - 2, "some application and a partly developed explanation"),
            (1, 1, max(1, marks - 4), "a limited response containing one or more relevant points"),
        ]
    label = "technical accuracy" if subject == "computer science" else "subject knowledge"
    result = ["Levels-based marking"]
    result.extend(
        f"Level {level} ({low}–{high}): {description}; {label} is secure at the top of the band."
        for level, low, high, description in bands
        if low <= high
    )
    result.append("Level 0 (0): no creditworthy material.")
    return result


def _application_label(subject: str) -> str:
    return "AO2"


def _clean_text(value: str) -> str:
    text = value
    text = re.sub(
        r"\b(?:practice|independent) case (\d+)\b",
        r"case study \1",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\bCase (\d+)\b", r"case study \1", text)
    text = re.sub(r"\bData set \d+\.\s*", "", text)
    text = re.sub(r"\(\d{4}\)$", "", text)
    text = re.sub(r"\bSynoptic theme \d+:", "Theme:", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = " ".join(cleaned.casefold().split())
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
