from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ExamSchedule:
    date: date
    session: str


ECONOMICS_A_9EC0_2026: dict[str, ExamSchedule] = {
    "paper_1": ExamSchedule(date(2026, 5, 11), "Morning"),
    "paper_2": ExamSchedule(date(2026, 5, 18), "Afternoon"),
    "paper_3": ExamSchedule(date(2026, 6, 4), "Morning"),
}


def economics_exam_schedule(paper_id: str) -> ExamSchedule:
    try:
        return ECONOMICS_A_9EC0_2026[paper_id]
    except KeyError as exc:
        raise ValueError(f"Unknown Economics A paper id: {paper_id}") from exc


def formatted_economics_exam_date(paper_id: str, generated_on: date | None = None) -> str:
    economics_exam_schedule(paper_id)
    exam_date = generated_on or date.today()
    return f"{exam_date:%A} {exam_date.day} {exam_date:%B %Y}"
