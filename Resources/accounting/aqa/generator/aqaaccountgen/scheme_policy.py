"""Human-facing, question-owned rows for the opt-in Paper 2 scheme."""

from __future__ import annotations

import re

from aqaaccountgen.marking_policy import MARKING_POLICY_ID, printed_mcq_rows
from Backend.Core.accounting_scheme_content import (
    ACCOUNTING_PAPER_TWO_SCHEME_PAGINATION,
)
from Backend.Core.credit_policy import PERMISSIONS
from Backend.Core.exam_blueprints import GeneratedPaper, GeneratedQuestion

POLICY_KEY = "accounting_marking_policy"
GENERAL_GUIDANCE = (
    (
        "Applying the scheme",
        "Read the complete response. Award marks for the work required by the question, accepting valid equivalent accounting treatments and alternative layouts. Do not reward the same point twice.",
    ),
    (
        "Workings and own figures",
        "Use the question-specific working marks and any dependencies or caps. Where an earlier error is carried through consistently, award the later method marks. Keep full precision in intermediate calculations and round only as the question requires.",
    ),
    (
        "Levels and indicative content",
        "For a levels-based response, use the applicable grid once to judge the response as a whole. Indicative points are examples, not a checklist of compulsory points. Credit other valid, relevant reasoning and conclusions. Require a judgement only where the question asks for one.",
    ),
    (
        "Assessment objectives",
        "AO1: Knowledge and understanding, including accounting techniques; AO2: Application to the given situation; AO3: Analysis and evaluation.",
    ),
    (
        "Question and paper totals",
        "Each 25-mark decision allocates AO2: 5 and AO3: 20. The AO allocation is part of the question's total, not an additional award. Check each question maximum and the 120-mark paper total.",
    ),
)


def paper_two_policy(paper: GeneratedPaper) -> bool:
    questions = [q for s in paper.sections for o in s.options for q in o.questions]
    declared = [
        q.authoring_context[POLICY_KEY]
        for q in questions
        if POLICY_KEY in q.authoring_context
    ]
    if paper.paper_id == "paper_1":
        if any(value != MARKING_POLICY_ID for value in declared):
            raise ValueError(
                "Accounting scheme policy is unknown or misplaced on Paper 1"
            )
        return False
    if not declared:
        return False
    if (
        paper.paper_id != "paper_2"
        or len(declared) != len(questions)
        or any(value != ACCOUNTING_PAPER_TWO_SCHEME_PAGINATION for value in declared)
    ):
        raise ValueError(
            "Accounting Paper 2 has an unknown, misplaced or incomplete scheme policy"
        )
    return True


def question_heading(question: GeneratedQuestion) -> str:
    return f"Question {question.number}: {question.prompt}"


def question_rows(
    question: GeneratedQuestion,
) -> tuple[list[list[str]], list[list[str]]]:
    """Keep each credit/alternative/exclusion; separate one original levels grid."""
    expected_mode = "levels" if len(question.assessment_objectives) > 1 else "points"
    if question.scheme_mode != expected_mode:
        raise ValueError("Accounting Paper 2 marking mode differs from its AO budget")
    if question.kind == "multiple_choice":
        answer = printed_mcq_rows([question])[0][1]
        return [[answer, str(question.marks)]], []
    if sum(point.marks for point in question.structured_mark_scheme) != question.marks:
        raise ValueError(
            "Accounting Paper 2 credit total differs from its question tariff"
        )
    rows: list[list[str]] = []
    levels: list[list[str]] = []
    for point in question.structured_mark_scheme:
        if point.marks and point.text == "Levels-based marking":
            raise ValueError("A reserved levels heading cannot carry an award")
        match = re.fullmatch(r"Level (\d+) \(([^)]+)\):\s*(.+)", point.text, re.DOTALL)
        if match:
            if point.marks:
                raise ValueError("A levels descriptor cannot carry an additional award")
            levels.append([f"Level {match[1]}: {match[3]}", match[2]])
        elif point.text != "Levels-based marking" and not (
            point.marks == 0 and point.text == PERMISSIONS["equivalent-assessed-route"]
        ):
            # This exact host-owned permission is expressed once in the guide.
            # Other question-specific guidance and all attached rules remain.
            rows.append([point.text, str(point.marks) if point.marks else "—"])
        rows.extend([f"Accept: {value}", "—"] for value in point.alternatives)
        rows.extend([f"Allow: {value}", "—"] for value in point.allow)
        rows.extend([f"Do not accept: {value}", "—"] for value in point.do_not_accept)
        rows.extend([f"Ignore: {value}", "—"] for value in point.ignore)
        rows.extend([f"Depends on: {value}", "—"] for value in point.depends_on)
    if question.scheme_mode == "levels":
        bands = [row[1].replace("–", "-") for row in levels]
        expected = (
            ["21-25", "16-20", "11-15", "6-10", "1-5", "0"]
            if question.marks == 25
            else ["5-6", "3-4", "1-2", "0"]
        )
        if bands != expected:
            raise ValueError(
                "Accounting Paper 2 requires one complete applicable levels grid"
            )
    elif levels:
        raise ValueError(
            "Accounting levels grid belongs only to a levels-based question"
        )
    return rows, levels
