# Bind Accounting award points and printed guidance to one explicit policy.

from __future__ import annotations

import re
from typing import Literal, TypedDict

from Backend.Core.exam_blueprints import GeneratedQuestion, MarkSchemePoint

MARKING_POLICY_ID = "aqa-accounting-explicit-credit-v1"
POINT_COUNTS = {
    "statement_extract": 7,
    "ledger_calculation": 5,
    "accounting_concept": 2,
    "company_statement": 14,
    "partnership_1": 6,
    "partnership_2": 8,
}
EXPLICIT_RULES = frozenset((*POINT_COUNTS, "explain_trade"))
TRADE_REASON_LEVELS = (
    (3, 3, "A clear and thorough explanation showing a benefit to the business."),
    (2, 2, "A partial explanation showing a relevant benefit."),
    (1, 1, "A relevant reason is identified but not developed."),
    (0, 0, "Nothing worthy of credit."),
)


class SourceContent(TypedDict):
    role: Literal["indicative", "level_descriptor", "context"]
    text: str


def _source_content(question: GeneratedQuestion) -> list[SourceContent]:
    content: list[SourceContent] = []
    for index, text in enumerate(question.mark_scheme):
        role: Literal["indicative", "level_descriptor", "context"] = "indicative"
        if re.match(r"^(?:Level [0-5]\b|Levels-based\b)", text, flags=re.IGNORECASE):
            role = "level_descriptor"
        elif question.rule_id == "explain_trade" and index == 0:
            role = "context"
        content.append({"role": role, "text": text})
    return content


def _reason_budget(label: str) -> str:
    return (
        f"{label} distinct reason: award up to 3 marks using the per-reason levels grid. "
        "Credit its identification, development and explained business benefit together."
    )


def _grouped_reason_policy(content: list[SourceContent]) -> dict[str, object]:
    if len(content) != 6:
        raise ValueError(
            "Accounting marking policy requires the two source reasoning chains"
        )
    return {
        "id": "aqa-accounting-two-reasons-v1",
        "schema_version": 1,
        "distinct_reasons_required": True,
        "groups": [
            {
                "id": "first_reason",
                "maximum_mark": 3,
                "assessment_objective": "AO1",
                "observable_mark_points": [
                    content[1]["text"],
                    "Explain how a lower effective unit price can encourage a larger purchase.",
                    "Link the larger purchase to higher revenue or faster inventory turnover.",
                ],
            },
            {
                "id": "second_reason",
                "maximum_mark": 3,
                "assessment_objective": "AO1",
                "observable_mark_points": [
                    content[2]["text"],
                    "Explain how the discount gives the customer an incentive to purchase again.",
                    "Link repeat purchasing to customer retention and more predictable future revenue.",
                ],
            },
        ],
        "levels": [
            {
                "level": level,
                "minimum_mark": marks,
                "maximum_mark": marks,
                "minimum_coverage": {0: 0.0, 1: 0.01, 2: 0.5, 3: 0.75}[level],
                "descriptor": descriptor,
            }
            for level, marks, descriptor in reversed(TRADE_REASON_LEVELS)
        ],
    }


# Capture source content before enrichment and set the supported award routes.
def apply_marking_policy(question: GeneratedQuestion) -> GeneratedQuestion:
    if question.kind == "multiple_choice":
        return question
    content = _source_content(question)
    context = {**question.authoring_context, "accounting_source_content": content}
    if question.rule_id not in EXPLICIT_RULES:
        return question.model_copy(update={"authoring_context": context})
    if len(question.assessment_objectives) != 1:
        raise ValueError(
            f"Accounting marking policy requires one objective for {question.rule_id}"
        )
    objective, marks = next(iter(question.assessment_objectives.items()))
    if marks != question.marks:
        raise ValueError(
            "Accounting marking policy objective allocation differs from the tariff"
        )
    context["accounting_marking_policy"] = MARKING_POLICY_ID
    if question.rule_id == "explain_trade":
        if question.marks != 6:
            raise ValueError(
                "Accounting marking policy requires six marks for two reasons"
            )
        descriptors = [
            f"Level {level} ({marks}): {text}"
            for level, marks, text in TRADE_REASON_LEVELS
        ]
        context["grouped_level_policy"] = _grouped_reason_policy(content)
        context["level_policy_id"] = "aqa-accounting-two-reasons-v1"
        context["observable_mark_points"] = [
            entry["text"] for entry in content if entry["role"] == "indicative"
        ]
        points = [
            MarkSchemePoint(
                text=_reason_budget("First"),
                marks=3,
                credit_type="level",
                assessment_objective=objective,
            ),
            MarkSchemePoint(
                text=_reason_budget("Second"),
                marks=3,
                credit_type="level",
                assessment_objective=objective,
                do_not_accept=[
                    "The first reason repeated without a second distinct reason."
                ],
            ),
            *[
                MarkSchemePoint(text=entry["text"], marks=0, credit_type="guidance")
                for entry in content
            ],
            *[
                MarkSchemePoint(text=text, marks=0, credit_type="level")
                for text in descriptors
            ],
        ]
        return question.model_copy(
            update={
                "scheme_mode": "levels",
                "structured_mark_scheme": points,
                "mark_scheme": [
                    "Apply levels separately to two distinct reasons, with a maximum of 3 marks for each reason.",
                    *question.mark_scheme,
                    *descriptors,
                ],
                "authoring_context": context,
            }
        )
    count = POINT_COUNTS[question.rule_id]
    if len(content) != count or count != question.marks:
        raise ValueError(
            f"Accounting marking policy has the wrong number of source routes for {question.rule_id}"
        )
    return question.model_copy(
        update={
            "structured_mark_scheme": [
                MarkSchemePoint(
                    text=entry["text"],
                    marks=1,
                    credit_type="point",
                    assessment_objective=objective,
                )
                for entry in content
            ],
            "authoring_context": context,
        }
    )


def source_content(question: GeneratedQuestion) -> list[SourceContent]:
    raw = question.authoring_context.get("accounting_source_content")
    if not isinstance(raw, list) or not raw:
        raise ValueError(
            f"Accounting marking policy source content is missing for {question.number}"
        )
    for entry in raw:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"role", "text"}
            or entry["role"] not in {"indicative", "level_descriptor", "context"}
            or not isinstance(entry["text"], str)
            or not entry["text"].strip()
        ):
            raise ValueError("Accounting marking policy source content is malformed")
    return raw


def finalise_marking_policy(question: GeneratedQuestion) -> GeneratedQuestion:
    if question.authoring_context.get("accounting_marking_policy") != MARKING_POLICY_ID:
        return question
    existing = {point.text for point in question.structured_mark_scheme}
    guidance = [
        MarkSchemePoint(text=text, marks=0, credit_type="guidance")
        for text in question.mark_scheme
        if text not in existing
    ]
    return question.model_copy(
        update={
            "structured_mark_scheme": [*question.structured_mark_scheme, *guidance],
        }
    )


def indicative_content(question: GeneratedQuestion) -> list[str]:
    return [
        entry["text"]
        for entry in source_content(question)
        if entry["role"] == "indicative"
    ]


# Reject allocations that disagree with the declared marking policy.
def explicit_credit_points(question: GeneratedQuestion) -> list[MarkSchemePoint]:
    if (
        question.rule_id not in EXPLICIT_RULES
        or question.authoring_context.get("accounting_marking_policy")
        != MARKING_POLICY_ID
        or len(question.assessment_objectives) != 1
    ):
        raise ValueError(
            f"Accounting marking policy is missing or invalid for {question.number}"
        )
    objective, budget = next(iter(question.assessment_objectives.items()))
    points = [point for point in question.structured_mark_scheme if point.marks > 0]
    if question.rule_id == "explain_trade":
        if question.authoring_context.get(
            "grouped_level_policy"
        ) != _grouped_reason_policy(source_content(question)):
            raise ValueError(
                f"Accounting marking policy reason groups differ for {question.number}"
            )
        weights = [3, 3]
        texts = [_reason_budget("First"), _reason_budget("Second")]
        credit_type = "level"
        mode = "levels"
    else:
        weights = [1] * POINT_COUNTS[question.rule_id]
        texts = [entry["text"] for entry in source_content(question)]
        credit_type = "point"
        mode = "points"
    if (
        budget != question.marks
        or sum(weights) != question.marks
        or question.scheme_mode != mode
        or [point.marks for point in points] != weights
        or [point.text for point in points] != texts
        or any(
            point.credit_type != credit_type or point.assessment_objective != objective
            for point in points
        )
    ):
        raise ValueError(
            f"Accounting marking policy allocation differs for {question.number}"
        )
    return points


def credit_total(question: GeneratedQuestion, *indices: int) -> str:
    points = explicit_credit_points(question)
    return str(sum(points[index].marks for index in indices))


def reason_level_rows(question: GeneratedQuestion) -> list[list[str]]:
    explicit_credit_points(question)
    levels = question.authoring_context["grouped_level_policy"]["levels"]
    return [
        [str(level["level"]), str(level["maximum_mark"]), level["descriptor"]]
        for level in reversed(levels)
    ]
